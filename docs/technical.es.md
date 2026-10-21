# Técnico

[English](technical.md) · [Português](technical.pt-BR.md) · **Español**

Para quien quiera hacer su propia versión del juego: corregirlo, traducirlo, cambiar las
reglas o contar otra historia. Para jugar, basta con el [README](../README.es.md).
Actualizado el 2026-10-19.

- [Haga su propia versión](#haga-su-propia-versión): qué instalar, cómo armar la ROM, dónde tocar
- [Mecánica](#mecánica): humanidad, lazo e ítems con los números; disposición de la pantalla
- [Formato del guion](#formato-del-guion): escenas, opciones, condiciones, efectos, interfaz
- [Idiomas](#idiomas): las tres versiones y el espacio de cada una; simulación de otros 10 idiomas
- [Consola, ROM y motor](#consola-rom-y-motor): la consola, el mapa de la ROM, la compresión de imágenes y texto, el motor, el sonido, las pruebas, el release

## Haga su propia versión

Todo se genera a partir de archivos de texto: el guion en YAML, las imágenes dibujadas por
código y las músicas escritas en notas. Puede corregir el texto, traducirlo a otro idioma
o cambiar toda la historia y armar una ROM nueva.

**Necesita:** Python 3 con PyYAML, Pillow y NumPy; y `z80asm` (el ensamblador GNU, paquete
`z80asm` en Debian, Fedora y Arch).

```sh
make validate        # revisa el guion sin ensamblar nada
make roms           # ensambla las tres ROMs en build/
make rom GAME_LANG=en  # un solo idioma (pt, en o es)
make play          # ensambla y abre en MAME (EMULATOR=... para usar otro)
make gallery        # una ROM que muestra las 18 imágenes, una por una
```

| Para… | Edite | Vea |
|---|---|---|
| corregir o cambiar el texto | `src/script/demonios.yaml` (y las traducciones `.en`, `.es`) | [formato del guion](#formato-del-guion) |
| traducir a otro idioma | crear `src/script/demonios.<lang>.yaml` | [idiomas](#idiomas) |
| cambiar las reglas | el guion (condiciones y efectos) | [mecánica](#mecánica) |
| cambiar las imágenes | `src/tools/art.py` | [consola, ROM y motor](#consola-rom-y-motor) |
| cambiar las músicas | `src/tools/music.py` | [consola, ROM y motor](#consola-rom-y-motor) |

`make rom` valida el guion antes (destinos, ítems, anchos de línea, finales alcanzables)
y muestra cuánto espacio queda en los 32 KB.

### Pruebas (opcionales)

Para quien toque el motor:

```sh
make mame [GAME_LANG=en]   # la ROM en MAME × en el núcleo de Mil Capivaras, pantalla a pantalla
```

Necesita Rust (cargo), MAME en Flatpak (`org.mamedev.MAME`) y el código de Mil Capivaras
en `../mil_capivaras`. Mil Capivaras es un emulador aún no publicado: por ahora, solo el
autor ejecuta esta prueba.

## Mecánica

Las reglas con los números reales (**contiene spoilers leves**: qué lleva a cada ruta y final).
Para jugar sin spoilers: el [README](../README.es.md#cómo-funciona).

### La escena es la unidad de todo

Cada escena tiene:

- **imagen:** una de las ilustraciones (varias escenas comparten la misma) o ninguna;
- **texto:** una o más páginas (Fire 1 avanza), con variantes que dependen del estado;
- **opciones:** de 1 a 4, cada una con destino y, si se quiere, condición y efecto; o
  "Continuar" (escena que sigue sola) o "Fin" (escena de final);
- **al entrar:** efectos automáticos (ganar un ítem, marcar una flag, cambiar humanidad o lazo).

### Estado del juego

Vive solo en la RAM de la consola (sin contraseña ni batería):

| Campo | Rango | Notas |
|---|---|---|
| humanidad (H) | 0–7, empieza en 7 | aparece en la barra junto al separador (roja con 2 o menos) |
| lazo (L) | 0–7, empieza en 2 | el afecto entre el narrador y Laura; **oculto** |
| ítems | 6 (1 bit cada uno) | reloj, manuscrito, farol, llave, retrato, pan |
| flags | 8 (1 bit cada una) | releyó el manuscrito, se acabó el aceite, vio la iglesia... |
| contadores | 2 | cuántas veces esperó el día, cuántas veces buscó a alguien |
| finales vistos | 7 bits | se conservan entre partidas mientras la consola sigue encendida |

### Humanidad

Lo que queda del narrador. Es el reloj de la historia.

- **Baja** con decisiones de huida o egoístas (esperar, buscar a otros, callar), con la
  oscuridad sin farol (solo hasta que se acaba el aceite), en momentos fijos de la historia
  (llegar a la casa de Laura, acabarse el aceite sin farol, el muelle, el nombre olvidado)
  y al quitarle la llave de la mano al portero.
- **"Protege"** (la próxima pérdida no ocurre): releer el manuscrito, recordar en la iglesia,
  compartir el pan, recordar con Laura, contarle una historia, recordar el nombre por ella.
- **Decide finales:** la ruta C pide H ≥ 4 en la traba; el FA1 pide H ≥ 3 al final; con H = 0
  el juego corta a un final (FB2, o FA2 en la ruta A, o FC en la ruta C).
- **Borra ítems:** con H ≤ 2 el narrador olvida el reloj y la llave; con H ≤ 1, el retrato y
  el manuscrito.
- **Degrada el texto:**
  - H 5–7: texto completo;
  - H 3–4: solo la primera frase de cada página;
  - H 1–2: sin puntuación y sin palabras vacías (artículos, preposiciones, conjunciones); las
    opciones también.
  La ruta C (el relato se está escribiendo) y la pantalla del autor no se degradan.

### Lazo

El afecto entre el narrador y Laura, oculto como en una novela visual.

- **Sube:** ir directo a su casa, entrar por la puerta con la llave, escuchar y responder con
  calma, compartir el pan, darle el retrato, recordar el pasado.
- **Baja:** desviarse por la iglesia, entrar por la ventana, mentir ("mañana amanece"), comerse
  el pan solo, arrastrarla sin parar, fingir que no lo notó.
- **Decide las rutas:** "Nos quedamos" (ruta A) pide L ≥ 5; "Escribimos" (ruta C) pide L ≥ 5,
  haber releído el manuscrito y H ≥ 4; con L bajo, "Nos quedamos" se vuelve pelea y lleva a la ruta B.
- **Decide finales:** FA1 pide L ≥ 6; en la ruta B, L < 3 en el muelle lleva al FB2.
- **Laura calla antes que el narrador:** con lazo bajo (L ≤ 2 en la conversación del pan, L ≤ 5 al
  olvidar el nombre en la ruta A, L ≤ 3 en el muelle en la ruta B), ella pierde el pensamiento que
  pasaba de frente a frente. Las escenas siguientes cambian (el retrato, la traba, la pelea, el
  ensayo de las palabras, el monte, el dictado de la ruta C). Es el aviso de lo que le espera al
  narrador; con lazo alto, ella habla hasta más tarde. Solo cambia el texto, no los finales.

### Decisiones sobre ítems

- **Retrato** (en la puerta del cuarto): llevarlo o dejarlo. Dárselo a Laura vale lazo +2.
- **Llave** (en la mano del portero muerto): quitársela cuesta humanidad −1; sin ella, la entrada
  a la casa de Laura es por la ventana (lazo −1 en lugar de +1).
- **Botica:** llevar el pan o el farol, no los dos. El pan sirve para Laura; el farol
  evita el costo de la oscuridad y ahorra humanidad cuando se acaba el aceite.

### Disposición de la pantalla (32 × 24 tiles; la TV muestra las columnas 2–29)

```
 0 ┌──────────────────────────────┐
   │      imagem 20 x 11 tiles    │   filas 0–10 (columnas 6–25)
11 │                              │
12 ├───────────────────── ▮▮▮▯▯▯▯ ┤   separador + humanidad
13 │ A VELA SE APAGOU NO PRIMEIRO │
   │ PASSO. TREVA, SÓ TREVA:      │   filas 13–19: texto (7 x 28)
19 │ NENHUM LAMPIÃO...          ▼ │   ▼ = hay más página
20 ├──────────────────────────────┤
21 │ ▶ IR DIRETO À CASA DE LAURA  │
22 │   CORTAR PELO LARGO DA SÉ    │   filas 21–23: hasta 3 opciones
23 │                              │   (con 4 opciones, el texto pierde una fila)
   └──────────────────────────────┘
```

- **Escena sin imagen:** el texto empieza en la fila 1.
- **Título y fin:** la imagen ocupa 10 filas y el texto empieza en la fila 12.

## Formato del guion

El guion está en `src/script/*.yaml`: es la única fuente de la ROM. Después de editarlo,
ejecute `make validate` (o directamente `make rom`, que valida antes de ensamblar).

Las claves (los comandos) están en inglés, para quien vaya a traducir o escribir otra
historia; el texto y los nombres de escenas, ítems, flags y finales son libres.

### Encabezado

```yaml
game:
  title: DEMÔNIOS
  subtitle: ...
  about: |                       # la pantalla "Sobre el autor" (páginas separadas por ---)
  start: quarto                  # primera escena
  humanity: 7                    # humanidad inicial (0–7)
  bond: 2                        # lazo inicial (0–7)
  on_zero: { common: x, A: y }   # humanidad 0: va a esta escena, según la ruta
  forget:                        # ítems que desaparecen con poca humanidad
    - { item: RELOGIO, hum_max: 2 }
  light: { has: LAMPIAO, no_flag: OLEO_ACABOU }   # condición de "tiene luz"
  dark_costs: { no_flag: OLEO_ACABOU }            # cuándo la oscuridad cuesta humanidad

items:   { RELOGIO: relógio parado, ... }     # máx. 8
flags:   [LEMBROU, ...]                       # máx. 8
endings: { F1: { name: A Vela, type: bad } }  # máx. 8; type: good, normal, bad, true_end
```

Los límites vienen de la RAM de la ROM: ítems, flags y finales vistos ocupan un byte cada
uno. El juego no tiene contraseña (decisión del 2026-10-18).

### Escena

```yaml
  nome_da_cena:          # el nombre es libre (scenes:)
    act: 2                # acto
    route: A              # A, B, C; sin route = común (decide el destino de on_zero)
    image: rua            # src/art/rua.png; "none" = escena solo de texto
    dark: true            # sin luz: imagen en contornos azules y, si dark_costs, −1 hum
    light: true           # la escena tiene luz propia (vela), ignora la oscuridad
    on_enter: { ... }     # efecto al entrar
    text: |               # texto por defecto (obligatorio)
      Parágrafo. Quebra de linha simples é respeitada.
      ---
      Página nova.
    variants:             # variantes: la primera cuya condición se cumple reemplaza el texto
      - if: { hum_max: 2 }
        effect: { ... }   # opcional: se aplica si se elige esta variante
        text: |
          ...
    # y exactamente UNO de estos tres:
    options: [ ... ]      # hasta 4
    auto: proxima_cena    # sin elección: "Continuar"
    ending: F1            # pantalla de fin
```

### Opción

```yaml
      - text: Abrir o portão      # hasta 26 columnas (cursor + espacio + 26 = 28 visibles)
        if: { has: CHAVE }        # desaparece si la condición falla
        effect: { bond: +1 }
        goto: outra_cena
      - text: Abrir o portão
        else: true                # aparece solo si la opción anterior desapareció
        goto: outra_cena
```

### Condiciones (`if`)

Todas las claves tienen que cumplirse a la vez.

| Clave | Ejemplo | Se cumple cuando |
|---|---|---|
| `has` / `lacks` | `has: [CHAVE, PAO]` | tiene todos / no tiene ninguno |
| `flag` / `no_flag` | `flag: LEMBROU` | todas activadas / ninguna activada |
| `hum_min` / `hum_max` | `hum_min: 3` | humanidad ≥ / ≤ |
| `bond_min` / `bond_max` | `bond_min: 5` | lazo ≥ / ≤ |
| `count_min` / `count_max` | `count_min: { ESPERA: 2 }` | contador ≥ / ≤ |
| `endings_min` | `endings_min: 2` | finales ya vistos (memoria) ≥ |

### Efectos (`effect`, `on_enter`)

| Clave | Ejemplo | Hace |
|---|---|---|
| `gain` / `lose` | `gain: [PAO]` | añade / quita ítems |
| `flag` / `unflag` | `flag: [BRIGA]` | activa / desactiva flags |
| `hum` | `hum: -1` | cambia la humanidad (0–7) |
| `bond` | `bond: +2` | cambia el lazo (0–7) |
| `protect` | `protect: true` | anula la próxima pérdida de humanidad |
| `add` | `add: { ESPERA: 1 }` | suma a un contador |

### Texto que se degrada

Con humanidad 3–4, solo aparece la primera frase de cada página; con 1–2, el texto pierde la
puntuación y las palabras de `stopwords` (artículos, preposiciones, conjunciones). Las
opciones siguen la misma regla en el nivel 1–2. La ruta C y la pantalla del autor no se degradan.

```yaml
stopwords: ["o", "a", "de", "no", ...]   # siempre entre comillas: en YAML, no/on se vuelven booleanos
```

Escriba teniéndolo en cuenta: la primera frase de cada página debe sostenerse sola, y las
palabras que cargan sentido no deben estar en la lista.

### Textos de la interfaz y otros idiomas

La sección `interface:` del guion contiene los textos fijos de la ROM:

| Clave | Texto en pt |
|---|---|
| `start` | Iniciar |
| `credits` | Péricles S. - 2026 |
| `continue` | Continuar |
| `end` / `end_big` | Fim / F I M |
| `no_exit` | (sem saída) |
| `inventory` / `nothing` | Inventário / (nada) |
| `closes` | Fire 1 ou 2 fecha |
| `pause` / `back_to_title` | Pausa / Voltar ao título |
| `endings_seen` | Finais vistos |
| `about` / `back` | Sobre o autor / Voltar |

El título de la pantalla es `game.title` con espacios entre las letras.

Los otros idiomas están en `src/script/demonios.<lang>.yaml`, solo con los textos, en el
mismo orden del guion base (formato al comienzo de `src/tools/languages.py`):

```yaml
game:      { title: DEMÔNIOS, subtitle: after the story by ..., about: ... }
interface: { start: Start, ... }
stopwords: ["the", "a", ...]
items:     { RELOGIO: pocket watch, ... }
endings:   { F1: The Candle, ... }
scenes:
  quarto:
    text: |
      I woke without knowing...
    options: [Reread what I wrote, Go to the window]
```

¿Cambió una escena en el guion base (opción nueva, variante nueva)? El validador señala la
traducción hasta que tenga el texto correspondiente: `make validate GAME_LANG=en`.

### Qué revisa el validador

Destinos existentes, ítems y flags declarados, límites de la RAM, número de opciones,
ancho de las opciones y de las palabras, y un aviso para escena
inalcanzable o final sin escena. No prueba las condiciones: para eso, juegue la ROM.

También revisa las traducciones (mismas escenas, variantes y opciones que el guion base), las
palabras vacías (tienen que ser texto) y el ancho de los textos de la interfaz, y avisa de
caracteres sin dibujo en la fuente. Al final, muestra cuánto ocupa el texto comprimido.

**Espacio:** el límite real es el espacio libre de la ROM, que solo el build conoce: `make rom` (o
`make roms`) muestra los bytes libres de cada idioma. Hoy quedan unos 600 a 700 bytes.
`make stats` lista el tamaño de cada escena.

## Idiomas

Una ROM de 32 KB por idioma, sin mapper (vea [Consola, ROM y motor](#consola-rom-y-motor)). Para añadir un
idioma: crear `src/script/demonios.<lang>.yaml` (formato en
[Textos de la interfaz y otros idiomas](#textos-de-la-interfaz-y-otros-idiomas)) y ejecutar
`make rom GAME_LANG=<lang>`.

### Las versiones que existen

| Idioma | Archivo (No-Intro) | Texto bruto | Comprimido | Libre en la ROM |
|---|---|---|---|---|
| Portugués | `Demonios (World) (Pt) (Aftermarket) (Unl).bin` | 10 554 bytes | 5 801 bytes | **614 bytes** |
| Inglés | `Demonios (World) (En) (Aftermarket) (Unl).bin` | 11 173 bytes | 5 893 bytes (+1,6%) | **551 bytes** |
| Español | `Demonios (World) (Es) (Aftermarket) (Unl).bin` | 10 997 bytes | 5 982 bytes (+3,1%) | **477 bytes** |

Los números ya incluyen los cinco cambios de imagen del 2026-10-19 (pantalla de fin con pared
negra, casa de Laura sin el poste, monte simplificado, gruta más grande, agua del muelle sin punteado), que ya están en las ROMs.

"Libre" es el núcleo de la ROM (0x4000–0x7FFF), que `make rom` muestra. Además, los tiles
de la fuente sin dibujo aún guardan unos 600 bytes, pero solo de textos cortos (hasta 32 bytes
comprimidos cada uno).

### Simulación: otros 10 idiomas

Límites de cada ROM: **94 dibujos de letra** (códigos de fuente 0x02–0x5F; el resto de los
tiles es de las imágenes), texto escrito de izquierda a derecha en tiles de 8 × 8, y el
espacio libre de arriba. Un idioma cabe sin recortes si el texto comprimido crece hasta un
**+11%** respecto al portugués (614 bytes sobre 5 801).

| Idioma | Letras distintas | ¿Cabe en los 94? | Texto vs. portugués | ¿Cabe en el espacio? | Veredicto |
|---|---|---|---|---|---|
| Japonés | solo kana: ~70 | sí | ~ −20% | sí, con ~1,8 KB de margen | **viable**, como en los juegos de Famicom; las partículas (は が を に の) pasan a ser las palabras vacías |
| Italiano | latinas + 6 acentos | sí | ~ +5% | sí (~311 bytes de margen) | **viable** |
| Ruso | cirílico, 33 letras | sí (en lugar de las latinas) | ~ +5% | sí (~311 bytes de margen) | **viable**, con fuente propia |
| Indonesio | latinas, sin acentos | sí | ~ +10% | sí, al límite (~21 bytes de margen) | **viable** |
| Francés | latinas + ~14 (é è ê ç œ…) | sí | ~ +12% | casi: recortar ~1,5% del texto | viable con un recorte mínimo |
| Alemán | latinas + Ä Ö Ü ß | sí | ~ +18% | no: recortar ~7% | viable con recortes; las palabras largas aprietan las 28 columnas |
| Árabe | 28 letras × hasta 4 formas ≈ 110 | **no** | ~ −5% | sí | **difícil**: de derecha a izquierda (cambiar el motor) y letras ligadas que no caben en los 94 dibujos |
| Hindi | devanagari, cientos de combinaciones | **no** | — | — | **inviable**; solo romanizado |
| Coreano | 300–500 sílabas distintas | **no** | — | — | **inviable**; las sílabas armadas por partes quedan ilegibles |
| Mandarín | 600–800 caracteres distintos | **no** | — | — | **inviable**: ilegible en 8 × 8 y sin espacio; solo en pinyin |

Notas:

- Los porcentajes de tamaño son estimaciones de una traducción típica, no mediciones. Las
  mediciones (inglés +1,6%, español +3,1%) muestran que las estimaciones tienden a ser
  pesimistas para este texto, que es corto y directo.
- Cada idioma nuevo necesita una **fuente propia** (solo con sus letras). Hoy las tres
  ROMs usan la misma fuente, con los acentos del portugués y del español.
- Para los idiomas que no caben, la alternativa a recortar texto es quitar la pantalla "Sobre el
  autor" de esa versión: libera unos 900 bytes (el retrato y la biografía), lo que basta
  para todos los de alfabeto latino, alemán incluido.

## Consola, ROM y motor

### La consola

La **Casio PV-1000** (1983) tiene un Z80 a 3,58 MHz, ninguna BIOS (el cartucho empieza a
ejecutarse en `0x0000`), 1 KB de RAM y un chip de video que solo dibuja tiles de 8 × 8.

| Dirección / puerto | Qué es |
|---|---|
| `0x0000–0x7FFF` | cartucho (ROM), 32 KB |
| `0xB800–0xBAFF` | mapa de tiles 32 × 24 (768 bytes) |
| `0xBB00–0xBBFF` | RAM de trabajo (256 bytes) |
| `0xBC00–0xBFFF` | PCG: patrones de los tiles `0xE0–0xFF` (32 tiles), definidos por el programa |
| `0xF8–0xFA` | 3 canales de onda cuadrada: frecuencia = 8739 Hz / (63 − n); 63 = silencio |
| `0xFB` | activa el sonido |
| `0xFC` | bit 0 = empezó un cuadro nuevo; se lee solo en la interrupción (consultarlo en bucle pierde cuadros en el core de MiSTer) |
| `0xFD` | matriz del joystick: se escribe la fila (1, 2, 4 u 8) y se leen los bits |
| `0xFE` | dirección del PCG (el juego escribe `0xB8`) |
| `0xFF` | bit 5 = banco de patrones, bit 4 = patrones solo de la ROM, bits 2–0 = color del borde |

**Tiles.** Cada patrón tiene 32 bytes: 8 de un plano sin uso y 8 para cada plano
(rojo, verde, azul). Cada píxel puede tener cualquiera de los 8 colores. Un tile `N < 0xE0`
viene de la ROM, en `N × 32` (más `0x2000` con el bit 5 del puerto FF activado): son 2 bancos de
224 patrones. El banco vale para toda la pantalla, por eso la fuente y la imagen están en el mismo
banco.

**Área visible.** La TV muestra las columnas 2 a 29 del mapa (224 píxeles). El texto usa esas
28 columnas.

**Control.** Fila 8 de la matriz: bit 1 = Fire 1, bit 0 = Fire 2 (nombres del núcleo de
MiSTer). El control tiene un interruptor que intercambia los dos botones, y MAME llama al bit 0
"Button 1".

### Por qué 32 KB, sin mapper, una ROM por idioma

El juego tiene que funcionar en todo: MAME, MiSTer, cualquier otro emulador además de la consola
original. Ningún juego de la Casio PV-1000 usa cambio de bancos y ningún emulador lo conoce,
así que la ROM se queda en los 32 KB que el Z80 ve directamente.
Cada idioma (pt, en, es) es una ROM con la misma estructura; solo cambia el texto.

### Mapa de la ROM

| Rango | Contenido |
|---|---|
| `0x0000–0x003F` | encabezado, salto al motor y vector de interrupción (`0x0038`) |
| `0x0040–0x0BFF` | banco 0: fuente e interfaz (tiles `0x02–0x5F`) |
| `0x0C00–0x1BFF` | banco 0: 128 patrones compartidos por las imágenes (tiles `0x60–0xDF`) |
| `0x1C00–0x1FFF` | imágenes comprimidas (los tiles ≥ `0xE0` nunca vienen de aquí, el espacio está libre) |
| `0x2040–0x3BFF` | banco 1: la misma fuente y otros 128 patrones |
| `0x3C00–0x3FFF` | imágenes comprimidas |
| `0x4000–0x7FFF` | motor (~2,9 KB), guion y texto (~6,3 KB), músicas (~0,3 KB), descompresor, resto de las imágenes |

Espacio libre en el núcleo: **614 bytes (pt), 551 (en), 477 (es)**. `make rom` muestra la
cuenta. Los 20 tiles de la fuente que no tienen dibujo guardan otros ~700 bytes de textos cortos
(nombres de ítems, interfaz), hasta 32 bytes cada uno (`font.free_codes()`).

### Imágenes

`src/tools/art.py` dibuja las 18 imágenes en `src/art/` (160 × 88 píxeles, 8 colores; el retrato del
autor es más pequeño). `src/tools/tiles.py` las convierte para el hardware:

1. Cada imagen tiene 20 × 11 tiles. Los tiles que se repiten entre las imágenes de un banco
   forman los **128 patrones compartidos** de la ROM.
2. Los tiles exclusivos que más desentonan van al **PCG** (hasta 32 por imagen),
   cargados en la RAM al entrar en la escena.
3. Lo que sobra se cambia por el patrón más parecido (altera de 0 a ~1,5 % de los píxeles).
4. **Compresión:** el mapa en RLE con "copiar de la fila de arriba" (lee de la propia VRAM, sin
   buffer); el PCG en LZSS (distancia de 12 bits, longitud de 4 bits, 24 bytes útiles por
   tile). Cerca de un 53 % menos que en crudo.
5. Los bloques comprimidos se encajan en las áreas libres de 1 KB (`0x1C00`, `0x3C00`) por la
   mejor suma de subconjuntos; el resto va al núcleo.

Cambiar a una escena con imagen tarda unos 6 cuadros (0,1 s). Las escenas seguidas con la misma
imagen no la vuelven a dibujar.

### Fuente

`src/tools/font.py`: letras de 5 × 7 en tiles de 8 × 8, solo mayúsculas.

| Códigos | Qué es |
|---|---|
| `0x01` | ninguno: en el banco 0, sus bytes guardan el vector de interrupción (`0x0038`) |
| `0x02–0x0C`, `0x19` | mayúsculas acentuadas del portugués (la Á es `0x19`): acento en 2 filas, 1 de separación y la letra en 4 |
| `0x0D–0x10` | español: Ñ Ü ¿ ¡ |
| `0x11–0x17` | interfaz: separador, barra de humanidad, cursor, "hay más", corazón |
| `0x18` | raya (—) |
| `0x20–0x5F` | ASCII |

`0x1E` y `0x1F` son, en el texto comprimido, "nueva línea" y "nueva página".

### Texto

`src/tools/rom.py` genera `src/rom/generated/script.asm` a partir del guion (el formato de los datos está
al comienzo del archivo):

- las líneas ya vienen cortadas en 28 columnas; la paginación se hace en el momento, porque la altura
  del área de texto depende del número de opciones;
- **compresión BPE:** los bytes `0x60–0xFF` son pares de bytes (2 bytes por código en el
  diccionario), expandidos de forma recursiva, una letra a la vez, directo en la pantalla. Los
  códigos de control nunca entran en un par. En portugués: 10 554 → 5 801 bytes;
- **texto que se degrada** (humanidad baja): el motor quita frases, puntuación y palabras
  vacías en el momento y vuelve a cortar las líneas en 28 columnas (`dt_degraded`).

### Motor

`src/rom/game.asm` interpreta el guion: escenas, variantes de texto, opciones con condición y efecto,
humanidad, lazo, ítems, flags, contadores, oscuridad, inventario, pausa, título, "Sobre el
autor" y la pantalla de fin. Las reglas están en [Mecánica](#mecánica).

La RAM del juego (`0xBB00–0xBBFF`) tiene direcciones fijas, descritas al comienzo de
`game.asm`: la prueba automática lee el estado de ahí.

### Sonido

`src/tools/music.py` escribe las músicas en notas y genera `src/rom/generated/music.asm`. Hay música
solo en el título y en las pantallas de fin (una por tipo de final), en los canales 2 y 3; la historia
transcurre en silencio, que es el tema del cuento. El canal 1 queda para los pitidos. Las notas van
del do# 3 al la 4, donde la afinación de la consola se desvía como máximo ~28 cents, y cada música
se transpone al tono en que menos desafina.

### Pruebas

| Herramienta | Qué revisa |
|---|---|
| `src/tools/script.py` | el guion: destinos, ítems, flags, anchos, finales alcanzables |
| `src/tools/languages.py` | las traducciones tienen las mismas escenas, variantes y opciones que el portugués |
| `src/tools/test_mame.py` | ROM en MAME × en Mil Capivaras (modelo "hw"): la pantalla después de cada botón, píxel a píxel |

El robot que maneja la ROM está en `src/tools/driver/` (Rust). Usa el núcleo de
Mil Capivaras (aún no publicado) y espera encontrarlo en `../mil_capivaras`. El mismo robot
toma las capturas del README (`make screenshots`).

Resultado del 2026-10-19 con MAME 0.289: 3 918 pantallas, ninguna diferencia. MAME muestra 10
filas más de borde arriba. Las capturas del propio MAME (F12) estiran la imagen a la
proporción de la TV y cortan algunos píxeles de la primera y la última columna; el cuadro del juego no.

### Release

Una tag `v*` dispara `.github/workflows/release.yml`, que ejecuta `make check dist` y
adjunta los zips al release. `make check` compara el CRC32 de las ROMs con los del Makefile.

El build es reproducible: las distancias entre tiles (`tiles.py`) se calculan con enteros.

### Pendiente de verificar en la consola real

- El overscan de la TV: si corta la columna 2 o la 29, pasar el texto a 26 columnas.
- El tiempo de dibujo de las imágenes y el sonido, en un cartucho de 32 KB.
