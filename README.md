# Sonic J2ME Map & Object Editor

A full map and object editor for a classic Sonic the Hedgehog J2ME mobile game, built with Python and Pillow.  Reverse-engineered from the decompiled JAR (see `sonic_editor.py` header for full technical writeup).

---

## Features

- Render all 6 zones × 3 acts of map data
- **Block mode** painting (256 × 256 px whole-block replacement)
- **Tile mode** painting (16 × 16 px single-tile editing inside a block)
- Right-panel **Block Editor** for fine tile placement
- Collision mask overlay (semi-transparent red per solid tile)
- **Object Editor** tab — place, move, delete game objects with sprite overlays
- Object properties panel (X, Y, param, type, count)
- 50-step **Undo / Redo** (`Ctrl+Z` / `Ctrl+Y`) per tab
- Export modified **`.bmd`** and **`.act`** binaries
- Zoom levels: 25 %, 50 %, 100 %, 200 %

---

## Requirements

```bash
pip install Pillow
```

Python ≥ 3.8 and tkinter (included in the Python standard library; on some Linux distros: `sudo apt install python3-tk`).

---

## Usage

```bash
python sonic_editor.py [res_dir]
```

`res_dir` — path to the extracted JAR resource folder. Can also be selected at runtime via **File → Open resource folder…**.

The resource folder should contain:

| File | Description |
|------|-------------|
| `zone1.png` … `zone6.png` | Zone tilesets |
| `zone1.bmd` … `zone6.bmd` | Block map data |
| `ZONE1ACT.act` … `ZONE6ACT.act` | Object/act data |
| `blkcol.bct` | Collision data |
| `*.png` | Object sprites |

Extract these files from the game's JAR with any ZIP tool.

---

## Binary Formats

### Block Map Data (`.bmd`)

Each zone file is `N_blocks × 512` bytes.  Every 512-byte block encodes a 16 × 16 tile grid (2 bytes per tile, row-major):

```
Byte 0 — control:  bits [1:0] = image bank (0/1/2 → tiles 0-255/256-511/512-767)
                   bits [4:3] = rotation  (0=0°, 1=90°, 2=180°, 3=270°)
Byte 1 — tile ID:  index 0-255 within the selected image bank
```

### Object/Act Data (`.act`)

```
Bytes 0-7:   four big-endian uint16 lengths (one per act slot)
Bytes 8+:    act data, concatenated
```

Each object record is exactly **7 bytes**:

```
[0-1] X position  (big-endian uint16, pixels)
[2-3] Y position  (big-endian uint16, pixels)
[4]   param
[5]   type index
[6]   count  (ring chains: extra instances − 1)
```

Objects *must* be sorted by X when written back (the game's streaming code requires it).

### Collision Data (`blkcol.bct`)

`256 blocks × 32 bytes = 8192 bytes`.  Each block gets a 16 × 16 bitfield (1 bit = 1 tile, 1 = solid):

```python
byte_idx = block_idx * 32 + tx * 2 + (ty >> 3)
bit      = (data[byte_idx] >> (7 - (ty & 7))) & 1
```

---

## World Map Data

The block grid (`worldMapData[zone][act][row][col]`) is hardcoded in `MainCanvas.java` as a static array.  Extract it by decompiling the JAR and replacing the `WORLD_MAP_DATA` literal at the top of `sonic_editor.py`.

---

## Repository Structure

```
Sonic-Map-Editor-J2me/
├── sonic_editor.py   # Main editor (~700 lines, single file)
├── README.md
└── res/              # Game resources — extract from JAR (not included)
    ├── zone1.png … zone6.png
    ├── zone1.bmd … zone6.bmd
    ├── ZONE1ACT.act … ZONE6ACT.act
    ├── blkcol.bct
    └── *.png
```

---

*Reverse-engineered with patience, a hex editor, and a lot of `print(hex(buf[i]))`.*