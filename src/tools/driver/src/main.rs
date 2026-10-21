//! Runs the game ROM on the Mil Capivaras core (no window) and obeys commands, one per
//! line, read from standard input:
//!
//!   frames N         lets N frames go by
//!   press B          presses and releases a button: up, down, f1, f2, start
//!   press_raw B      holds it for 3 frames without waiting for the game (like src/tools/test_mame.lua)
//!   choose K         turns the scene's pages and picks the K-th visible option (0 = 1st)
//!                    and prints the state
//!   state            prints the state
//!   memory X         puts X in the seen endings (as if it came from the password)
//!   pause            opens the pause menu (Start) and picks "Continue"
//!   finish           turns the ending's pages until the end screen
//!   screen           prints the tile map: 24 lines of 32 codes in hexadecimal
//!   record FILE N    records N frames of sound (f32, 48 kHz, mono) into FILE
//!   shot FILE.ppm    saves the screen
//!   hw               uses the real console model instead of the MiSTer core
//!
//! The state comes out on one line: scene hum bond items flags holding memory mode dark
//! (fixed RAM addresses, see src/rom/game.asm).
//!
//! Usage:  rom_driver ROM.bin < commands.txt
use std::io::BufRead;

use pv1000_core::machine::{Pv1000, H, W};

const RAM: usize = 0xBB00;
const SCENE: usize = RAM;
const HUM: usize = RAM + 1;
const BOND: usize = RAM + 2;
const ITEMS: usize = RAM + 3;
const FLAGS: usize = RAM + 4;
const HOLDING: usize = RAM + 5;
const MEMORY: usize = RAM + 6;
const DARK: usize = RAM + 7;
const BUSY: usize = RAM + 0x6B;
const M_END: u8 = 2;
const MODE: usize = RAM + 0x1C;
const LAST: usize = RAM + 0x23;
const SPECIAL: usize = RAM + 0x3E;
const M_SCENE: u8 = 1;

fn button(name: &str) -> u32 {
    // joystick bits in the core: 0 right, 1 left, 2 down, 3 up, 4 Fire 1,
    // 5 Fire 2, 6 Select, 7 Start
    match name {
        "up" => 1 << 3,
        "down" => 1 << 2,
        "f1" => 1 << 4,
        "f2" => 1 << 5,
        "start" => 1 << 7,
        _ => panic!("unknown button: {name}"),
    }
}

struct Machine {
    pv: Pv1000,
    sound: Option<Vec<f32>>,
}

impl Machine {
    fn frames(&mut self, j: u32, n: u32) {
        for _ in 0..n {
            self.pv.set_joy(j, 0);
            self.pv.run_frame();
            let a = self.pv.take_audio();
            if let Some(g) = self.sound.as_mut() {
                g.extend(a);
            }
        }
    }
    // waits for the game to be free (unpacking an image takes a few frames, and the game
    // only reads the controller between one task and the next), presses and releases
    fn press(&mut self, b: &str) {
        self.wait();
        self.frames(button(b), 3);
        self.frames(0, 3);
    }
    /// Lets the game finish what it is doing; returns how many frames it took.
    fn wait(&mut self) -> u32 {
        let mut n = 0;
        self.frames(0, 1);
        while self.r(BUSY) != 0 {
            self.frames(0, 1);
            n += 1;
            assert!(n < 600, "the game does not go back to reading the controller");
        }
        n
    }
    fn r(&self, a: usize) -> u8 {
        self.pv.ram()[a]
    }
    fn state(&self) -> String {
        format!("{} {} {} {} {} {} {} {} {}", self.r(SCENE), self.r(HUM), self.r(BOND), self.r(ITEMS),
                self.r(FLAGS), self.r(HOLDING), self.r(MEMORY), self.r(MODE), self.r(DARK))
    }
}

fn main() {
    let rom = std::fs::read(std::env::args().nth(1).expect("usage: rom_driver ROM.bin < commands")).unwrap();
    let mut m = Machine { pv: Pv1000::new(48000), sound: None };
    let mut loaded = false;
    for line in std::io::stdin().lock().lines() {
        let line = line.unwrap();
        let p: Vec<&str> = line.split_whitespace().collect();
        if p.is_empty() || p[0].starts_with('#') {
            continue;
        }
        if p[0] == "hw" {
            m.pv.set_hardware_model(true);
            continue;
        }
        if !loaded {
            m.pv.load(&rom);
            m.frames(0, 30);
            loaded = true;
        }
        match p[0] {
            "frames" => m.frames(0, p[1].parse().unwrap()),
            "press" => m.press(p[1]),
            "press_raw" => m.frames(button(p[1]), 3),
            "state" => {
                m.wait();
                println!("{}", m.state())
            }
            "measure" => {
                // presses Fire 1 and counts the frames until the game reads the controller again
                m.wait();
                m.frames(button("f1"), 1);
                println!("{} frames", m.wait() + 1);
                m.frames(0, 3);
            }
            "memory" => m.pv.ram_mut()[MEMORY] = p[1].parse().unwrap(),
            "choose" => {
                let k: usize = p[1].parse().unwrap();
                let mut turns = 0;
                // waits for the game to finish drawing before looking at the page: with the
                // dithered text and the image, drawing takes a few frames
                while { m.wait(); m.r(MODE) == M_SCENE && m.r(LAST) == 0 } {
                    m.press("f1");
                    turns += 1;
                    assert!(turns < 50, "the scene never reaches its last page");
                }
                if m.r(MODE) == M_SCENE && m.r(SPECIAL) != 2 {
                    for _ in 0..k {
                        m.press("down");
                    }
                    m.press("f1");
                }
                m.wait();
                println!("{}", m.state());
            }
            "pause" => {
                m.press("start");
                m.press("f1");
            }
            "finish" => {
                let mut turns = 0;
                while m.r(MODE) == M_SCENE {
                    m.press("f1");
                    turns += 1;
                    assert!(turns < 50, "never reaches the end screen");
                }
                m.wait();
                assert_eq!(m.r(MODE), M_END);
            }
            "record" => {
                m.sound = Some(Vec::new());
                m.frames(0, p[2].parse().unwrap());
                let a = m.sound.take().unwrap();
                let b: Vec<u8> = a.iter().flat_map(|x| x.to_le_bytes()).collect();
                std::fs::write(p[1], b).unwrap();
            }
            "screen" => {
                m.wait();
                for l in 0..24 {
                    let row: String = (0..32).map(|c| format!("{:02x}", m.r(0xB800 + l * 32 + c))).collect();
                    println!("T {row}");
                }
            }
            "shot" => {
                m.wait();
                m.frames(0, 1); // the frame in which the game finished still came out half drawn
                let mut out = format!("P6\n{W} {H}\n255\n").into_bytes();
                for &px in &m.pv.fb {
                    out.extend_from_slice(&[(px >> 16) as u8, (px >> 8) as u8, px as u8]);
                }
                std::fs::write(p[1], out).unwrap();
            }
            c => panic!("unknown command: {c}"),
        }
    }
}
