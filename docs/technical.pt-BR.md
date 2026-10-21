# Técnico

[English](technical.md) · **Português** · [Español](technical.es.md)

Para quem quer fazer a sua própria versão do jogo: corrigir, traduzir, mudar as regras
ou contar outra história. Para jogar, basta o [README](../README.pt-BR.md). Atualizado em
2026-10-19.

- [Fazer a sua versão](#fazer-a-sua-versão): o que instalar, como montar a ROM, onde mexer
- [Mecânica](#mecânica): humanidade, laço e itens com os números; layout da tela
- [Formato do roteiro](#formato-do-roteiro): cenas, opções, condições, efeitos, interface
- [Línguas](#línguas): as três versões e o espaço de cada uma; simulação de outras 10 línguas
- [Console, ROM e motor](#console-rom-e-motor): o console, o mapa da ROM, a compressão de imagens e texto, o motor, o som, os testes, o release

## Fazer a sua versão

Tudo é gerado a partir de arquivos de texto: o roteiro em YAML, as imagens desenhadas por
código e as músicas escritas em notas. Dá para corrigir o texto, traduzir para outra
língua ou trocar a história inteira e montar uma ROM nova.

**Precisa de:** Python 3 com PyYAML, Pillow e NumPy; e o `z80asm` (o montador GNU, pacote
`z80asm` no Debian, Fedora e Arch).

```sh
make validate        # confere o roteiro sem montar nada
make roms           # monta as três ROMs em build/
make rom GAME_LANG=en  # uma língua só (pt, en ou es)
make play          # monta e abre no MAME (EMULATOR=... para usar outro)
make gallery        # uma ROM que mostra as 18 imagens, uma por uma
```

| Para… | Mexa em | Veja |
|---|---|---|
| corrigir ou mudar o texto | `src/script/demonios.yaml` (e as traduções `.en`, `.es`) | [formato do roteiro](#formato-do-roteiro) |
| traduzir para outra língua | criar `src/script/demonios.<lang>.yaml` | [línguas](#línguas) |
| mudar as regras | o roteiro (condições e efeitos) | [mecânica](#mecânica) |
| mudar as imagens | `src/tools/art.py` | [console, ROM e motor](#console-rom-e-motor) |
| mudar as músicas | `src/tools/music.py` | [console, ROM e motor](#console-rom-e-motor) |

O `make rom` valida o roteiro antes (destinos, itens, larguras de linha, finais
alcançáveis) e mostra quanto espaço sobra nos 32 KB.

### Testes (opcionais)

Para quem mexer no motor:

```sh
make mame [GAME_LANG=en]   # a ROM no MAME × no núcleo do Mil Capivaras, tela a tela
```

Precisa do Rust (cargo), do MAME em Flatpak (`org.mamedev.MAME`) e do código do Mil
Capivaras em `../mil_capivaras`. O Mil Capivaras é um emulador ainda não publicado: por
enquanto, só o autor roda este teste.

## Mecânica

As regras com os números de verdade (**tem spoilers leves**: o que leva a cada rota e final).
Para quem joga, sem spoilers: o [README](../README.pt-BR.md#como-funciona).

### Cena = unidade de tudo

Cada cena tem:

- **imagem:** uma das ilustrações (várias cenas compartilham a mesma) ou nenhuma;
- **texto:** uma ou mais páginas (Fire 1 avança), com variantes que dependem do estado;
- **opções:** de 1 a 4, cada uma com destino e, se quiser, condição e efeito; ou
  "Continuar" (cena que segue sozinha) ou "Fim" (cena de final);
- **ao entrar:** efeitos automáticos (ganhar item, marcar flag, mudar humanidade ou laço).

### Estado do jogo

Vive só na RAM do console (sem senha nem bateria):

| Campo | Faixa | Notas |
|---|---|---|
| humanidade (H) | 0–7, começa em 7 | aparece na barra ao lado do separador (vermelha com 2 ou menos) |
| laço (L) | 0–7, começa em 2 | o afeto entre o narrador e Laura; **escondido** |
| itens | 6 (1 bit cada) | relógio, manuscrito, lampião, chave, retrato, pão |
| flags | 8 (1 bit cada) | releu o manuscrito, o óleo acabou, viu a igreja... |
| contadores | 2 | quantas vezes esperou o dia, quantas vezes procurou alguém |
| finais vistos | 7 bits | atravessam partidas enquanto o console fica ligado |

### Humanidade

O quanto resta do narrador. É o relógio da história.

- **Cai** com escolhas de fuga ou egoístas (esperar, procurar outros, calar), com o
  escuro sem lampião (só até o óleo acabar), em momentos fixos da história (chegar à
  casa de Laura, o óleo acabar sem lampião, o cais, o nome esquecido) e ao tirar a chave
  da mão do porteiro.
- **"Protege"** (a próxima perda não acontece): reler o manuscrito, lembrar na igreja,
  repartir o pão, lembrar com Laura, contar uma história a ela, lembrar o nome por ela.
- **Decide finais:** a rota C pede H ≥ 4 na trava; o FA1 pede H ≥ 3 no fim; com H = 0 o
  jogo corta para um final (FB2, ou FA2 na rota A, ou FC na rota C).
- **Apaga itens:** com H ≤ 2 o narrador esquece o relógio e a chave; com H ≤ 1, o retrato e
  o manuscrito.
- **Degrada o texto:**
  - H 5–7: texto inteiro;
  - H 3–4: só a primeira frase de cada página;
  - H 1–2: sem pontuação e sem palavras vazias (artigos, preposições, conjunções); as
    opções também.
  A rota C (o relato está sendo escrito) e a tela do autor não degradam.

### Laço

O afeto entre o narrador e Laura, escondido como numa visual novel.

- **Sobe:** ir direto à casa dela, entrar pela porta com a chave, ouvir e responder com
  calma, repartir o pão, dar o retrato, lembrar do passado.
- **Desce:** desviar pela igreja, entrar pela janela, mentir ("amanhã amanhece"), comer
  o pão sozinho, puxá-la sem parar, fingir que não notou.
- **Decide as rotas:** "Ficamos" (rota A) pede L ≥ 5; "Escrevemos" (rota C) pede L ≥ 5,
  ter relido o manuscrito e H ≥ 4; com L baixo, "Ficamos" vira briga e leva à rota B.
- **Decide finais:** FA1 pede L ≥ 6; na rota B, L < 3 no cais leva ao FB2.
- **Laura cala antes do narrador:** com laço baixo (L ≤ 2 na conversa do pão, L ≤ 5 ao
  esquecer o nome na rota A, L ≤ 3 no cais na rota B), ela perde o pensamento que passava
  de testa a testa. As cenas seguintes mudam (o retrato, a trava, a briga, o ensaio das
  palavras, a mata, o ditado da rota C). É o aviso do que vem para o narrador; com laço
  alto, ela fala até mais tarde. Só muda o texto, não os finais.

### Escolhas de itens

- **Retrato** (à porta do quarto): levar ou deixar. Dá-lo a Laura vale laço +2.
- **Chave** (na mão do porteiro morto): tirá-la custa humanidade −1; sem ela, a entrada
  na casa de Laura é pela janela (laço −1 em vez de +1).
- **Botica:** levar o pão ou o lampião, não os dois. O pão serve para Laura; o lampião
  evita o custo do escuro e poupa a humanidade quando o óleo acaba.

### Layout da tela (32 × 24 tiles; a TV mostra as colunas 2–29)

```
 0 ┌──────────────────────────────┐
   │      imagem 20 x 11 tiles    │   linhas 0–10 (colunas 6–25)
11 │                              │
12 ├───────────────────── ▮▮▮▯▯▯▯ ┤   separador + humanidade
13 │ A VELA SE APAGOU NO PRIMEIRO │
   │ PASSO. TREVA, SÓ TREVA:      │   linhas 13–19: texto (7 x 28)
19 │ NENHUM LAMPIÃO...          ▼ │   ▼ = há mais página
20 ├──────────────────────────────┤
21 │ ▶ IR DIRETO À CASA DE LAURA  │
22 │   CORTAR PELO LARGO DA SÉ    │   linhas 21–23: até 3 opções
23 │                              │   (com 4 opções, o texto perde uma linha)
   └──────────────────────────────┘
```

- **Cena sem imagem:** o texto começa na linha 1.
- **Título e fim:** a imagem ocupa 10 linhas e o texto começa na linha 12.

## Formato do roteiro

O roteiro fica em `src/script/*.yaml`: é a fonte única da ROM. Depois de editar, rode
`make validate` (ou direto `make rom`, que valida antes de montar).

As chaves (os comandos) são em inglês, para quem for traduzir ou escrever outra história;
o texto e os nomes de cenas, itens, flags e finais são livres.

### Cabeçalho

```yaml
game:
  title: DEMÔNIOS
  subtitle: ...
  about: |                       # a tela "Sobre o autor" (páginas separadas por ---)
  start: quarto                  # primeira cena
  humanity: 7                    # humanidade inicial (0–7)
  bond: 2                        # laço inicial (0–7)
  on_zero: { common: x, A: y }   # humanidade 0: vai para esta cena, conforme a rota
  forget:                        # itens que somem com pouca humanidade
    - { item: RELOGIO, hum_max: 2 }
  light: { has: LAMPIAO, no_flag: OLEO_ACABOU }   # condição de "tem luz"
  dark_costs: { no_flag: OLEO_ACABOU }            # quando o escuro custa humanidade

items:   { RELOGIO: relógio parado, ... }     # máx. 8
flags:   [LEMBROU, ...]                       # máx. 8
endings: { F1: { name: A Vela, type: bad } }  # máx. 8; type: good, normal, bad, true_end
```

Os limites vêm da RAM da ROM: itens, flags e finais vistos ocupam um byte cada. O jogo
não tem senha (decisão de 2026-10-18).

### Cena

```yaml
  nome_da_cena:          # o nome é livre (scenes:)
    act: 2                # ato
    route: A              # A, B, C; sem route = comum (decide o destino de on_zero)
    image: rua            # src/art/rua.png; "none" = cena só de texto
    dark: true            # sem luz: imagem em contornos azuis e, se dark_costs, −1 hum
    light: true           # a cena tem luz própria (vela), ignora o escuro
    on_enter: { ... }     # efeito ao entrar
    text: |               # texto padrão (obrigatório)
      Parágrafo. Quebra de linha simples é respeitada.
      ---
      Página nova.
    variants:             # variantes: a primeira cuja condição vale substitui o texto
      - if: { hum_max: 2 }
        effect: { ... }   # opcional: aplicado se esta variante for a escolhida
        text: |
          ...
    # e exatamente UM destes três:
    options: [ ... ]      # até 4
    auto: proxima_cena    # sem escolha: "Continuar"
    ending: F1            # tela de fim
```

### Opção

```yaml
      - text: Abrir o portão      # até 26 colunas (cursor + espaço + 26 = 28 visíveis)
        if: { has: CHAVE }        # some se a condição falhar
        effect: { bond: +1 }
        goto: outra_cena
      - text: Abrir o portão
        else: true                # aparece só se a opção anterior sumiu
        goto: outra_cena
```

### Condições (`if`)

Todas as chaves precisam valer ao mesmo tempo.

| Chave | Exemplo | Vale quando |
|---|---|---|
| `has` / `lacks` | `has: [CHAVE, PAO]` | tem todos / não tem nenhum |
| `flag` / `no_flag` | `flag: LEMBROU` | todas ligadas / nenhuma ligada |
| `hum_min` / `hum_max` | `hum_min: 3` | humanidade ≥ / ≤ |
| `bond_min` / `bond_max` | `bond_min: 5` | laço ≥ / ≤ |
| `count_min` / `count_max` | `count_min: { ESPERA: 2 }` | contador ≥ / ≤ |
| `endings_min` | `endings_min: 2` | finais já vistos (memória) ≥ |

### Efeitos (`effect`, `on_enter`)

| Chave | Exemplo | Faz |
|---|---|---|
| `gain` / `lose` | `gain: [PAO]` | põe / tira itens |
| `flag` / `unflag` | `flag: [BRIGA]` | liga / desliga flags |
| `hum` | `hum: -1` | muda a humanidade (0–7) |
| `bond` | `bond: +2` | muda o laço (0–7) |
| `protect` | `protect: true` | anula a próxima perda de humanidade |
| `add` | `add: { ESPERA: 1 }` | soma num contador |

### Texto que degrada

Com humanidade 3–4, só a primeira frase de cada página aparece; com 1–2, o texto perde a
pontuação e as palavras de `stopwords` (artigos, preposições, conjunções). As
opções seguem a mesma regra no nível 1–2. A rota C e a tela do autor não degradam.

```yaml
stopwords: ["o", "a", "de", "no", ...]   # sempre entre aspas: no YAML, no/on viram booleano
```

Escreva pensando nisso: a primeira frase de cada página deve se sustentar sozinha, e as
palavras que carregam sentido não devem estar na lista.

### Textos da interface e outras línguas

A seção `interface:` do roteiro tem os textos fixos da ROM:

| Chave | Texto em pt |
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

O título da tela é `game.title` com espaços entre as letras.

As outras línguas ficam em `src/script/demonios.<lang>.yaml`, só com os textos, na mesma
ordem do roteiro base (formato no começo de `src/tools/languages.py`):

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

Mudou uma cena no roteiro base (opção nova, variante nova)? O validador acusa a
tradução até ela ter o texto correspondente: `make validate GAME_LANG=en`.

### O que o validador confere

Destinos existentes, itens e flags declarados, limites da RAM, número de opções,
largura das opções e das palavras, e um aviso para cena
inalcançável ou final sem cena. Não testa as condições: para isso, jogue a ROM.

Também confere as traduções (mesmas cenas, variantes e opções do roteiro base), as
palavras vazias (têm de ser texto) e a largura dos textos da interface, e avisa sobre
caracteres sem desenho na fonte. No fim, mostra quanto o texto ocupa comprimido.

**Espaço:** o limite real é o espaço livre da ROM, que só o build sabe: `make rom` (ou
`make roms`) mostra os bytes livres de cada língua. Hoje sobram uns 600 a 700 bytes.
`make stats` lista o tamanho de cada cena.

## Línguas

Uma ROM de 32 KB por língua, sem mapper (ver [Console, ROM e motor](#console-rom-e-motor)). Para acrescentar uma
língua: criar `src/script/demonios.<lang>.yaml` (formato em
[Textos da interface e outras línguas](#textos-da-interface-e-outras-línguas)) e rodar
`make rom GAME_LANG=<lang>`.

### As versões que existem

| Língua | Arquivo (No-Intro) | Texto bruto | Comprimido | Livre na ROM |
|---|---|---|---|---|
| Português | `Demonios (World) (Pt) (Aftermarket) (Unl).bin` | 10 554 bytes | 5 801 bytes | **614 bytes** |
| Inglês | `Demonios (World) (En) (Aftermarket) (Unl).bin` | 11 173 bytes | 5 893 bytes (+1,6%) | **551 bytes** |
| Espanhol | `Demonios (World) (Es) (Aftermarket) (Unl).bin` | 10 997 bytes | 5 982 bytes (+3,1%) | **477 bytes** |

Os números já contam as cinco mudanças de imagem de 2026-10-19 (tela de fim com parede
preta, casa de Laura sem o poste, mata simplificada, gruta maior, água do cais sem pontilhado), que estão nas ROMs.

"Livre" é o miolo da ROM (0x4000–0x7FFF), que o `make rom` mostra. Além dele, os tiles
da fonte sem desenho ainda guardam uns 600 bytes, mas só de textos curtos (até 32 bytes
comprimidos cada).

### Simulação: outras 10 línguas

Limites de cada ROM: **94 desenhos de letra** (códigos de fonte 0x02–0x5F; o resto dos
tiles é das imagens), texto escrito da esquerda para a direita em tiles de 8 × 8, e o
espaço livre acima. Uma língua cabe sem cortes se o texto comprimido crescer até uns
**+11%** em relação ao português (614 bytes sobre 5 801).

| Língua | Letras diferentes | Cabe nos 94? | Texto vs. português | Cabe no espaço? | Veredito |
|---|---|---|---|---|---|
| Japonês | só kana: ~70 | sim | ~ −20% | sim, com ~1,8 KB de folga | **viável**, como nos jogos de Famicom; as partículas (は が を に の) viram as palavras vazias |
| Italiano | latinas + 6 acentos | sim | ~ +5% | sim (~311 bytes de folga) | **viável** |
| Russo | cirílico, 33 letras | sim (no lugar das latinas) | ~ +5% | sim (~311 bytes de folga) | **viável**, com fonte própria |
| Indonésio | latinas, sem acentos | sim | ~ +10% | sim, no limite (~21 bytes de folga) | **viável** |
| Francês | latinas + ~14 (é è ê ç œ…) | sim | ~ +12% | quase: cortar ~1,5% do texto | viável com um corte mínimo |
| Alemão | latinas + Ä Ö Ü ß | sim | ~ +18% | não: cortar ~7% | viável com cortes; palavras longas apertam as 28 colunas |
| Árabe | 28 letras × até 4 formas ≈ 110 | **não** | ~ −5% | sim | **difícil**: da direita para a esquerda (mudar o motor) e letras ligadas que não cabem nos 94 desenhos |
| Hindi | devanágari, centenas de combinações | **não** | — | — | **inviável**; só romanizado |
| Coreano | 300–500 sílabas diferentes | **não** | — | — | **inviável**; sílabas montadas por partes ficam ilegíveis |
| Mandarim | 600–800 caracteres diferentes | **não** | — | — | **inviável**: ilegível em 8 × 8 e sem espaço; só em pinyin |

Notas:

- As porcentagens de tamanho são estimativas de tradução típica, não medidas. As
  medidas (inglês +1,6%, espanhol +3,1%) mostram que as estimativas tendem a ser
  pessimistas para este texto, que é curto e direto.
- Cada língua nova precisa de uma **fonte própria** (só as letras dela). Hoje as três
  ROMs usam a mesma fonte, com os acentos do português e do espanhol.
- Para as línguas que não cabem, a alternativa a cortar texto é tirar a tela "Sobre o
  autor" daquela versão: libera uns 900 bytes (o retrato e a biografia), o que basta
  para todas as latinas, alemão incluído.

## Console, ROM e motor

### O console

O **Casio PV-1000** (1983) tem um Z80 a 3,58 MHz, nenhuma BIOS (o cartucho começa a
rodar em `0x0000`), 1 KB de RAM e um chip de vídeo que só desenha tiles de 8 × 8.

| Endereço / porta | O quê |
|---|---|
| `0x0000–0x7FFF` | cartucho (ROM), 32 KB |
| `0xB800–0xBAFF` | mapa de tiles 32 × 24 (768 bytes) |
| `0xBB00–0xBBFF` | RAM de trabalho (256 bytes) |
| `0xBC00–0xBFFF` | PCG: padrões dos tiles `0xE0–0xFF` (32 tiles), definidos pelo programa |
| `0xF8–0xFA` | 3 canais de onda quadrada: frequência = 8739 Hz / (63 − n); 63 = mudo |
| `0xFB` | liga o som |
| `0xFC` | bit 0 = começou um quadro novo; lida só na interrupção (consultá-la em laço perde quadros no core do MiSTer) |
| `0xFD` | matriz do joystick: escreve a linha (1, 2, 4 ou 8) e lê os bits |
| `0xFE` | endereço do PCG (o jogo escreve `0xB8`) |
| `0xFF` | bit 5 = banco de padrões, bit 4 = padrões só da ROM, bits 2–0 = cor da borda |

**Tiles.** Cada padrão tem 32 bytes: 8 de um plano sem uso e 8 para cada plano
(vermelho, verde, azul). Cada pixel pode ter qualquer uma das 8 cores. Um tile `N < 0xE0`
vem da ROM, em `N × 32` (mais `0x2000` com o bit 5 da porta FF ligado): são 2 bancos de
224 padrões. O banco vale para a tela inteira, por isso fonte e imagem ficam no mesmo
banco.

**Área visível.** A TV mostra as colunas 2 a 29 do mapa (224 pixels). O texto usa essas
28 colunas.

**Controle.** Linha 8 da matriz: bit 1 = Fire 1, bit 0 = Fire 2 (nomes do núcleo do
MiSTer). O controle tem uma chave que troca os dois botões, e o MAME chama o bit 0 de
"Button 1".

### Por que 32 KB, sem mapper, uma ROM por língua

O jogo tem de rodar em tudo: MAME, MiSTer, qualquer outro emulador além do console
original. Nenhum jogo de Casio PV-1000 usa troca de bancos e nenhum emulador a conhece,
então a ROM fica nos 32 KB que o Z80 enxerga direto.
Cada língua (pt, en, es) é uma ROM com a mesma estrutura; muda só o texto.

### Mapa da ROM

| Faixa | Conteúdo |
|---|---|
| `0x0000–0x003F` | cabeçalho, salto para o motor e vetor de interrupção (`0x0038`) |
| `0x0040–0x0BFF` | banco 0: fonte e interface (tiles `0x02–0x5F`) |
| `0x0C00–0x1BFF` | banco 0: 128 padrões compartilhados pelas imagens (tiles `0x60–0xDF`) |
| `0x1C00–0x1FFF` | imagens comprimidas (tiles ≥ `0xE0` nunca vêm daqui, o espaço é livre) |
| `0x2040–0x3BFF` | banco 1: a mesma fonte e outros 128 padrões |
| `0x3C00–0x3FFF` | imagens comprimidas |
| `0x4000–0x7FFF` | motor (~2,9 KB), roteiro e texto (~6,3 KB), músicas (~0,3 KB), descompressor, resto das imagens |

Espaço livre no miolo: **614 bytes (pt), 551 (en), 477 (es)**. O `make rom` mostra a
conta. Os 20 tiles da fonte que não têm desenho guardam mais ~700 bytes de textos curtos
(nomes de itens, interface), até 32 bytes cada (`font.free_codes()`).

### Imagens

`src/tools/art.py` desenha as 18 imagens em `src/art/` (160 × 88 pixels, 8 cores; o retrato do
autor é menor). `src/tools/tiles.py` as converte para o hardware:

1. Cada imagem tem 20 × 11 tiles. Os tiles que se repetem entre as imagens de um banco
   formam os **128 padrões compartilhados** da ROM.
2. Os tiles exclusivos que mais destoam vão para o **PCG** (até 32 por imagem),
   carregados na RAM ao entrar na cena.
3. O que sobra é trocado pelo padrão mais parecido (altera de 0 a ~1,5 % dos pixels).
4. **Compressão:** o mapa em RLE com "copiar da linha de cima" (lê da própria VRAM, sem
   buffer); o PCG em LZSS (distância de 12 bits, tamanho de 4 bits, 24 bytes úteis por
   tile). Cerca de 53 % menor que o cru.
5. Os blocos comprimidos são encaixados nas áreas livres de 1 KB (`0x1C00`, `0x3C00`) pela
   melhor soma de subconjuntos; o resto vai no miolo.

Trocar de cena com imagem leva uns 6 quadros (0,1 s). Cenas seguidas com a mesma imagem
não a redesenham.

### Fonte

`src/tools/font.py`: letras de 5 × 7 em tiles de 8 × 8, só maiúsculas.

| Códigos | O quê |
|---|---|
| `0x01` | nenhum: no banco 0, os bytes dele guardam o vetor de interrupção (`0x0038`) |
| `0x02–0x0C`, `0x19` | maiúsculas acentuadas do português (o Á é `0x19`): acento em 2 linhas, 1 de folga e a letra em 4 |
| `0x0D–0x10` | espanhol: Ñ Ü ¿ ¡ |
| `0x11–0x17` | interface: separador, barra de humanidade, cursor, "tem mais", coração |
| `0x18` | travessão (—) |
| `0x20–0x5F` | ASCII |

`0x1E` e `0x1F` são, no texto comprimido, "nova linha" e "nova página".

### Texto

`src/tools/rom.py` gera `src/rom/generated/script.asm` a partir do roteiro (o formato dos dados está
no começo do arquivo):

- as linhas já vêm quebradas em 28 colunas; a paginação é feita na hora, porque a altura
  da área de texto depende do número de opções;
- **compressão BPE:** os bytes `0x60–0xFF` são pares de bytes (2 bytes por código no
  dicionário), expandidos de forma recursiva, uma letra por vez, direto na tela. Os
  códigos de controle nunca entram num par. Em português: 10 554 → 5 801 bytes;
- **texto que degrada** (humanidade baixa): o motor tira frases, pontuação e palavras
  vazias na hora e requebra as linhas em 28 colunas (`dt_degraded`).

### Motor

`src/rom/game.asm` interpreta o roteiro: cenas, variantes de texto, opções com condição e efeito,
humanidade, laço, itens, flags, contadores, escuro, inventário, pausa, título, "Sobre o
autor" e a tela de fim. As regras estão em [Mecânica](#mecânica).

A RAM do jogo (`0xBB00–0xBBFF`) tem endereços fixos, descritos no começo do
`game.asm`: o teste automático lê o estado dali.

### Som

`src/tools/music.py` escreve as músicas em notas e gera `src/rom/generated/music.asm`. Há música
só no título e nas telas de fim (uma por tipo de final), nos canais 2 e 3; a história é em
silêncio, que é o tema do conto. O canal 1 fica para os bipes. As notas vão do dó# 3 ao lá
4, onde a afinação do console desvia no máximo ~28 cents, e cada música é transposta para
o tom em que desafina menos.

### Testes

| Ferramenta | O que confere |
|---|---|
| `src/tools/script.py` | o roteiro: destinos, itens, flags, larguras, finais alcançáveis |
| `src/tools/languages.py` | as traduções têm as mesmas cenas, variantes e opções do português |
| `src/tools/test_mame.py` | ROM no MAME × no Mil Capivaras (modelo "hw"): a tela depois de cada botão, pixel a pixel |

O robô que comanda a ROM fica em `src/tools/driver/` (Rust). Ele usa o núcleo do
Mil Capivaras (ainda não publicado) e espera encontrá-lo em `../mil_capivaras`. O mesmo robô
tira as capturas do README (`make screenshots`).

Resultado em 2026-10-19 com o MAME 0.289: 3 918 telas, nenhuma diferença. O MAME mostra 10
linhas a mais de borda em cima. As fotos do próprio MAME (F12) esticam a imagem para a
proporção da TV e cortam uns pixels da primeira e da última coluna; o quadro do jogo não.

### Release

Uma tag `v*` dispara o `.github/workflows/release.yml`, que roda `make check dist` e
anexa os zips ao release. O `make check` confere o CRC32 das ROMs com os do Makefile.

O build é reproduzível: as distâncias entre tiles (`tiles.py`) são calculadas em inteiros.

### A conferir no console de verdade

- O overscan da TV: se cortar a coluna 2 ou a 29, passar o texto para 26 colunas.
- O tempo de desenho das imagens e o som, num cartucho de 32 KB.
