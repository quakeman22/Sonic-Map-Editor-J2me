# Reverse Engineering Sonic J2ME Game: Building a Full Map & Object Editor

> A deep-dive into binary format analysis, Java bytecode reverse engineering, and building a functional level editor for a classic mobile Sonic game using Python and PIL.

---

## Table of Contents

1. [Project Overview](#1-project-overview)
2. [Tools & Stack](#2-tools--stack)
3. [Reverse Engineering the Codebase](#3-reverse-engineering-the-codebase)
4. [Binary Format: Block Map Data (.bmd)](#4-binary-format-block-map-data-bmd)
5. [Binary Format: Object/Act Data (.act)](#5-binary-format-objectact-data-act)
6. [Binary Format: Collision Data (.bct)](#6-binary-format-collision-data-bct)
7. [World Map Structure](#7-world-map-structure)
8. [Coordinate System](#8-coordinate-system)
9. [Object Type Mapping](#9-object-type-mapping)
10. [Editor Architecture](#10-editor-architecture)
11. [Rendering Pipeline](#11-rendering-pipeline)
12. [RGBA Transparency Handling](#12-rgba-transparency-handling)
13. [Incremental Canvas Updates](#13-incremental-canvas-updates)
14. [Undo / Redo System](#14-undo--redo-system)
15. [Exporting Modified Binaries](#15-exporting-modified-binaries)
16. [Lessons Learned](#16-lessons-learned)

---

## 1. Project Overview

This project involved fully reverse engineering the resource format of a Sonic the Hedgehog game developed for J2ME (Java 2 Micro Edition) mobile phones, and building a complete two-tab level editor in Python capable of:

- Rendering all 6 zones × 3 acts of map data
- Editing block placement at both block level (256×256 px) and tile level (16×16 px)
- Visualizing and editing collision masks per block
- Placing, moving and deleting game objects (enemies, rings, platforms, items) with sprite overlays
- Exporting modified `.bmd` and `.act` binaries ready to replace inside the original JAR

The game's Java source was obtained by decompiling the JAR with a standard Java decompiler. All binary formats were reverse engineered by cross-referencing the decompiled `MainCanvas.java` with hex dumps of the resource files.

---

## 2. Tools & Stack

| Tool | Purpose |
|------|---------|
| Java decompiler (Fernflower / CFR) | Decompile the JAR to readable Java source |
| Python 3.12 | Editor implementation |
| Pillow (PIL) | Image loading, compositing, tile rendering |
| tkinter | GUI framework (built into Python stdlib) |
| `struct` module | Big-endian binary parsing |
| Hex editor | Validating binary formats against code |

---

## 3. Reverse Engineering the Codebase

The decompiled `MainCanvas.java` was ~23,600 lines long. The strategy was to search for known anchor points — file names referenced in `getResourceAsStream()` calls — and trace the surrounding parsing code.

Key methods targeted:

```
LoadImages()           → maps object type indices to sprite filenames
objectInit()           → reveals .act file structure and object count logic
addObjectSet()         → shows how 7-byte records are decoded into live objects
blockColChk()          → reveals the exact bit-addressing formula for collision
readStageObject()      → confirms .act header layout
```

For each binary format, the approach was:

1. Find the `DataInputStream.read()` or array indexing code
2. Map each byte/short read to a semantic field
3. Verify by writing a Python parser and comparing rendered output visually

---

## 4. Binary Format: Block Map Data (.bmd)

**File:** `zone1.bmd` … `zone6.bmd`  
**Size:** ~43 KB per zone (84 blocks × 512 bytes)

### Block Structure

Each block is exactly **512 bytes**, representing a 16×16 grid of tiles (256 tiles × 2 bytes each).

```
Block layout (512 bytes):
  [tile_0_ctrl][tile_0_id]  ← tile at (x=0, y=0)
  [tile_1_ctrl][tile_1_id]  ← tile at (x=1, y=0)
  ...
  [tile_255_ctrl][tile_255_id]  ← tile at (x=15, y=15)

Tile ordering: row-major, x varies fastest
  index = tx + ty * 16
```

### Byte 0 — Control Byte

```
Bits 1-0: imageOffset
  00 → use tiles  0–255  (tileset rows 0–15)
  01 → use tiles  256–511  (tileset rows 16–31)
  10 → use tiles  512–767  (tileset rows 32–47)

Bits 4-3: rotation
  00 → no rotation
  01 → 90°
  10 → 180°
  11 → 270°
```

### Byte 1 — Tile ID

Index into the tileset spritesheet row, from 0 to 255. The actual tile index into the sheet is:

```python
effective_tile = tile_id + image_offset * 256
src_x = (effective_tile % 10) * 16   # 10 tiles per row (160px wide sheet)
src_y = (effective_tile // 10) * 16
```

### Python Parser

```python
def read_tile(bmd: bytearray, block_idx: int, tx: int, ty: int):
    offset = block_idx * 512 + (tx + ty * 16) * 2
    ctrl   = bmd[offset]
    tid    = bmd[offset + 1]

    image_offset = 1 if (ctrl & 1) else (2 if (ctrl & 3) == 2 else 0)
    rotation     = (ctrl >> 3) & 3
    effective    = tid + image_offset * 256

    src_x = (effective % 10) * 16
    src_y = (effective // 10) * 16
    return src_x, src_y, rotation
```

---

## 5. Binary Format: Object/Act Data (.act)

**File:** `ZONE1ACT.act` … `ZONE6ACT.act`  
**Size:** 4–5 KB per zone

### File Header

The file opens with 4 big-endian `uint16` values — one per act — each giving the **byte length** of that act's object data:

```
Bytes 0-1:  length of act 0 data  (big-endian uint16)
Bytes 2-3:  length of act 1 data
Bytes 4-5:  length of act 2 data
Bytes 6-7:  length of act 3 data  (usually 0)
Bytes 8+:   act 0 data, act 1 data, act 2 data, act 3 data (concatenated)
```

### Object Record (7 bytes each)

This was the trickiest format to decode. Initial attempts assumed `type` was the first byte — it is not. The correct layout, confirmed from `addObjectSet()` lines 6281–6343:

```
Byte 0-1:  X position  (big-endian uint16, in pixels)
Byte 2-3:  Y position  (big-endian uint16, in pixels)
Byte 4:    param       (extra parameter — direction, behavior variant, etc.)
Byte 5:    type        (object type index — maps to sprite and behavior)
Byte 6:    count       (number of repeated instances - 1, used for ring chains)
```

The critical insight: **objects must be sorted by X position** before writing back, because the game's streaming code (`addObjectChk`) performs a sorted scan to load objects into view as the player scrolls.

### Python Parser

```python
def parse_act(buf: bytearray) -> list[dict]:
    n = len(buf) // 7
    objects = []
    for i in range(n):
        b = i * 7
        objects.append({
            'x':     ((buf[b]   & 0xFF) << 8) | (buf[b+1] & 0xFF),
            'y':     ((buf[b+2] & 0xFF) << 8) | (buf[b+3] & 0xFF),
            'param': buf[b+4] & 0xFF,
            'type':  buf[b+5] & 0xFF,
            'count': buf[b+6] & 0xFF,
        })
    return objects

def serialize_act(objects: list[dict]) -> bytearray:
    sorted_objs = sorted(objects, key=lambda o: o['x'])
    buf = bytearray()
    for o in sorted_objs:
        x, y = o['x'] & 0xFFFF, o['y'] & 0xFFFF
        buf += bytes([
            (x >> 8) & 0xFF, x & 0xFF,
            (y >> 8) & 0xFF, y & 0xFF,
            o['param'] & 0xFF,
            o['type']  & 0xFF,
            o['count'] & 0xFF,
        ])
    return buf
```

### Group Objects

When `byte[5]` (type) is one of `{0, 1, 63, 64, 65, 66, 67, 68, 69}` (ring patterns), `byte[6]` (count) indicates **how many additional instances** to spawn in sequence. For example, `type=0, count=5` spawns 6 rings spaced 24 px apart horizontally.

---

## 6. Binary Format: Collision Data (.bct)

**File:** `blkcol.bct`  
**Size:** 8192 bytes (256 blocks × 32 bytes)

### Structure

Each block gets **32 bytes = 256 bits**, representing a 16×16 binary collision grid — one bit per tile position. A `1` means solid (Sonic is blocked), `0` means passable.

The bit addressing formula was extracted directly from `blockColChk()`:

```java
// From MainCanvas.java line 3073 (rotation 0):
blockColTable[var4 + (x & 15) * 2 + ((y & 15) >> 3)] >> (7 - (y & 7)) & 1
```

Translated to Python:

```python
def is_solid(col_data: bytearray, block_idx: int, tx: int, ty: int) -> bool:
    base     = block_idx * 32
    byte_idx = base + tx * 2 + (ty >> 3)
    bit      = (col_data[byte_idx] >> (7 - (ty & 7))) & 1
    return bool(bit)
```

### Rotation Variants

The function has four code paths for the four rotation states of a tile:

| Rotation | Formula |
|----------|---------|
| 0° | `base + tx*2 + (ty>>3)`, bit `7-(ty&7)` |
| 90° | `base + (15-tx)*2 + (ty>>3)`, bit `7-(ty&7)` |
| 180° | `base + tx*2 + ((15-ty)>>3)`, bit `ty&7` |
| 270° | `base + (15-tx)*2 + ((15-ty)>>3)`, bit `ty&7` |

The editor visualizes collision by overlaying a semi-transparent red rectangle over each solid tile when "Collision" is checked.

---

## 7. World Map Structure

The map grid (which block goes in which cell) is **not stored in any external file** — it is hardcoded as a static multidimensional array inside `MainCanvas.java`:

```java
static int[][][][] worldMapData = { /* zone × act × row × col */ };
```

The array was extracted by parsing the decompiled source with a regex and embedded directly into the editor as a Python literal. Each value is a block index (0 = empty, 1–83 = block from the zone's .bmd).

---

## 8. Coordinate System

The game uses three nested coordinate levels:

| Unit | Size | Description |
|------|------|-------------|
| Tile | 16 × 16 px | Smallest visual unit, one entry in the tileset |
| Block | 256 × 256 px | 16×16 tiles; one entry in worldMapData |
| World pixel | 1 px | Raw pixel coordinate used in object X/Y positions |

Object positions in `.act` files are in **world pixels** — not blocks, not tiles. A ring at `x=1088` is at pixel 1088, which is block column `1088 // 256 = 4`, tile column `(1088 % 256) // 16 = 4`.

---

## 9. Object Type Mapping

Object types were mapped by cross-referencing three sources in `MainCanvas.java`:

1. **`CallObjectDraw()`** — a large `switch(objectData[1])` that calls a draw function per type
2. **`LoadImages()`** — maps `m_imgObj[type_idx]` to a PNG filename
3. **`addObjectSet()`** — reveals grouping logic and spawn offsets per type

Example excerpt from `CallObjectDraw`:

```java
case 9:  this.toge_nflag_draw_ikeshita(var1); break;  // spike
case 40: this.hachi_sflag_draw_arai(var1);    break;  // Hachi enemy
case 57: this.kani_sflag_draw_arai(var1);     break;  // Kani enemy
case 86: this.fish_sflag_draw_arai(var1);     break;  // Fish enemy
```

And from `LoadImages`:

```java
this.m_imgObj[9]  = this.createImage("/toge.png");
this.m_imgObj[40] = this.createImage("/hachi.png");
this.m_imgObj[57] = this.createImage("/kani.png");
this.m_imgObj[86] = this.createImage("/fish2.png");
```

This gave us a complete `type → (name, sprite_filename, hitbox_size, category)` table for all ~60 object types.

---

## 10. Editor Architecture

The editor is a single Python file (~2000 lines) built on **tkinter** with **Pillow** for all image operations.

### Class Structure

```
SonicEditor
├── Data layer
│   ├── tilesets   dict[zone → PIL.Image]
│   ├── bmd_data   dict[zone → bytearray]
│   ├── act_data   dict[zone → list[bytearray]]   # one per act
│   ├── col_data   bytearray (8192 bytes)
│   └── sprites    dict[filename → PIL.Image]
│
├── Tab 1 — Map Editor
│   ├── Left panel:   tileset canvas + tool buttons + brush mode radio
│   ├── Center:       main map canvas (scrollable, zoomable)
│   └── Right panel:  block editor (256×256 px, tile-level editing)
│
└── Tab 2 — Object Editor
    ├── Left panel:   object palette (listbox + category filter)
    ├── Center:       map canvas with object overlay
    └── Right panel:  property fields + object list
```

### Two Brush Modes (Map Editor)

| Mode | Granularity | What changes |
|------|-------------|-------------|
| Block (256 px) | One `worldMapData` cell | Replaces entire 256×256 block |
| Tile (16 px) | One tile within a block | Writes to `bmd_data` at the specific 2-byte offset |

In tile mode, the paint and erase tools write directly to `bmd_data[zone][block_idx * 512 + (tx + ty*16) * 2 + 1]`, updating the tile ID in place.

---

## 11. Rendering Pipeline

### Full Map Render

```
worldMapData[zone][act]
    → for each (row, col) → block_index
        → for each (tx, ty) in 16×16
            → read ctrl_byte, tile_id from bmd_data
            → compute image_offset, rotation
            → crop tile from tileset PIL.Image
            → apply rotation via Image.Transpose
            → paste onto map PIL.Image using alpha mask
    → draw tile/block grid overlays (ImageDraw)
    → draw collision overlay if enabled
    → resize to zoom level (Image.NEAREST for pixel-accurate scaling)
    → convert to ImageTk.PhotoImage
    → place on tk.Canvas
```

### Incremental Block Update

Rerendering the full map (which can be 12000×1700 px) on every brush stroke would be too slow. Instead, the editor maintains a cached full-map `PIL.Image` and updates only the affected block:

```python
def _patch_block_on_canvas(self, bx: int, by: int):
    # 1. Re-render only the 256×256 region for block (bx, by)
    blk_img = self._render_single_block(bx, by)

    # 2. Paste it into the cached full-map image
    self._map_img.paste(blk_img, (bx * BLOCK_PX, by * BLOCK_PX))

    # 3. Apply overlays (collision, grid) for just this block

    # 4. Crop, scale to zoom level, convert to ImageTk
    patch = self._map_img.crop((bx*256, by*256, (bx+1)*256, (by+1)*256))
    patch_scaled = patch.convert('RGB').resize(
        (int(256*zoom), int(256*zoom)), Image.NEAREST)
    tk_patch = ImageTk.PhotoImage(patch_scaled)

    # 5. Place on canvas at the correct pixel position
    self._block_tk_cache[(bx, by)] = tk_patch  # keep reference alive
    canvas.create_image(int(bx*256*zoom), int(by*256*zoom),
                        anchor='nw', image=tk_patch)
```

This makes tile-by-tile painting feel instantaneous even on large maps.

---

## 12. RGBA Transparency Handling

The J2ME tilesets and sprite sheets are PNG files with full alpha channels. A common mistake with Pillow is using `.convert('RGB')` on an RGBA image, which fills transparent pixels with their raw RGB values — often magenta `(255, 0, 255)` — instead of compositing them correctly.

### Wrong approach

```python
img.paste(tile.convert('RGB'), (dx, dy))  # ← transparent areas become pink/magenta
```

### Correct approach

```python
# For pasting onto an opaque RGB background:
if tile.mode == 'RGBA':
    img.paste(tile, (dx, dy), mask=tile.split()[3])  # use alpha channel as mask
else:
    img.paste(tile.convert('RGB'), (dx, dy))

# For object sprites displayed on the tkinter canvas:
# ImageTk.PhotoImage natively supports RGBA — no conversion needed
if sprite.mode != 'RGBA':
    sprite = sprite.convert('RGBA')
tk_img = ImageTk.PhotoImage(sprite)  # transparency renders correctly on Canvas
```

The map base image is kept as `RGBA` throughout the render pipeline and only converted to `RGB` at the final step before creating the `ImageTk.PhotoImage` for display.

---

## 13. Incremental Canvas Updates

The tkinter `Canvas` widget allows stacking multiple `create_image()` calls. When a block is patched, a new image item is placed at the exact canvas coordinates of that block, covering the old image underneath:

```python
canvas.create_image(cx, cy, anchor='nw', image=tk_patch)
```

Because tkinter draws canvas items in creation order, the new item renders on top of the stale background image without needing to redraw the entire canvas. A `dict` cache stores `ImageTk` references keyed by `(bx, by)` to prevent Python's garbage collector from deleting them (a common tkinter pitfall — if the `PhotoImage` object is GC'd, the image disappears from the canvas silently).

---

## 14. Undo / Redo System

Both editor tabs implement independent undo/redo with a 50-step history.

### Map Editor

Because both `worldMapData` (the block grid) and `bmd_data` (tile-level data inside blocks) can be modified, both are snapshotted together:

```python
def _save_map_undo(self):
    state = {
        'grid': [list(row) for row in self.map_grid],  # deep copy of grid
        'bmd':  bytes(self.bmd_data[self.zone]),        # immutable snapshot
    }
    self.map_undo.append(state)
    if len(self.map_undo) > 50:
        self.map_undo.pop(0)
    self.map_redo.clear()
```

### Object Editor

Objects are plain dicts, so `copy.deepcopy()` suffices:

```python
def _save_obj_undo(self):
    self.obj_undo.append(copy.deepcopy(self.objects))
    if len(self.obj_undo) > 50:
        self.obj_undo.pop(0)
    self.obj_redo.clear()
```

Undo is triggered by `Ctrl+Z`, redo by `Ctrl+Y`, routed to the currently active tab.

---

## 15. Exporting Modified Binaries

### BMD Export

The `bmd_data[zone]` bytearray is written directly to disk — no transformation needed since edits are made in-place:

```python
with open(output_path, 'wb') as f:
    f.write(self.bmd_data[zone])
```

### ACT Export

The modified object list for the current act is serialized back to 7-byte records (sorted by X), then the four act buffers are reassembled with the header:

```python
def _export_act_file(self, zone: int) -> bytes:
    acts = self.act_data[zone]
    acts[self.act] = self._serialize_act(self.objects)  # update current act

    sizes = [len(a) for a in acts]
    buf = bytearray()
    for s in sizes:
        buf += bytes([(s >> 8) & 0xFF, s & 0xFF])  # 4× uint16 header
    for a in acts:
        buf += a
    return bytes(buf)
```

---

## 16. Lessons Learned

**Binary format discovery is iterative.** The `.act` field order was initially reversed (type first, then X/Y). The mistake only became obvious when rendered objects appeared at physically impossible positions like `x=65535`. Tracing back through `addObjectSet()` revealed the correct field order.

**Sort order is a hidden contract.** The game's object streaming system assumes objects in `.act` files are sorted by X coordinate. Writing them back in arbitrary order causes objects to either never load or all load at once, crashing the game's object pool. This was discovered by testing a modified file in an emulator.

**Incremental rendering is essential for usability.** Rerendering a 12000×1700 px map image from scratch on every brush stroke took 800–1200 ms. Patching only the modified 256×256 block dropped that to under 30 ms.

**Tkinter's `PhotoImage` GC issue is a classic trap.** Any `ImageTk.PhotoImage` object must be kept alive by a Python reference (stored in a list or dict). If it goes out of scope after being placed on a Canvas, the canvas item turns blank silently with no error.

**Collision data reveals design intent.** Once the `blkcol.bct` overlay was working, it became clear that many visually similar tiles have very different collision shapes — slopes, half-blocks, one-way platforms. This kind of data is invisible in the visual render alone.

---

## Repository Structure

```
sonic-j2me-editor/
├── sonic_editor.py          # Main editor (single-file, ~2000 lines)
├── README.md                # This document
└── res/                     # Game resource folder (not included — extract from JAR)
    ├── zone1.png … zone6.png
    ├── zone1.bmd … zone6.bmd
    ├── ZONE1ACT.act … ZONE6ACT.act
    ├── blkcol.bct
    └── *.png                # Object sprites
```

## Requirements

```bash
pip install Pillow
python sonic_editor.py
```

Tested on Python 3.12, Windows and Linux. Tkinter is included in the Python standard library on all platforms (on some Linux distros: `sudo apt install python3-tk`).

---

*Reverse engineered and documented with patience, a hex editor, and a lot of `print(hex(buf[i]))`.*
