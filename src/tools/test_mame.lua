-- Used by src/tools/test_mame.py: reads the steps from steps.txt (one per line: "button frames",
-- button = f1, f2, up, down, start or "-"), holds each button for 3 frames, waits and
-- writes the raw screen frame (224 × 244, 32 bits per pixel) to frames.raw.
local dir = os.getenv("HOME") .. "/.cache/demonios_mame/"
local ports = manager.machine.ioport.ports
-- MAME calls "Button 1" the bit that MiSTer (and the game) calls Fire 2
local fields = {
  f1 = ports[":IN3"].fields["P1 Button 2"], f2 = ports[":IN3"].fields["P1 Button 1"],
  up = ports[":IN2"].fields["P1 Up"], down = ports[":IN1"].fields["P1 Down"],
  start = ports[":IN0"].fields["P1 Start"],
}
local steps = {}
for l in io.lines(dir .. "steps.txt") do
  local b, q = l:match("(%S+)%s+(%d+)")
  steps[#steps + 1] = {fields[b], tonumber(q)}
end
local out = io.open(dir .. "frames.raw", "wb")
local i, wait, hold, current = 0, 0, 0, nil
emu.register_frame_done(function()
  if hold > 0 then
    hold = hold - 1
    if hold == 0 then current:set_value(0) end
    return
  end
  if wait > 0 then wait = wait - 1; return end
  if i > 0 then out:write((manager.machine.screens[":screen"]:pixels())) end
  i = i + 1
  if i > #steps then out:close(); manager.machine:exit(); return end
  current = steps[i][1]
  if current then current:set_value(1); hold = 3 end
  wait = steps[i][2]
end)
