#!/usr/bin/env python3
"""
Sonic J2ME Map & Object Editor
================================
Single-file editor for Sonic the Hedgehog J2ME game resources.

Supports:
  - Rendering all 6 zones x 3 acts of map data
  - Editing block placement (block mode: 256x256 px) and tile placement
    (tile mode: 16x16 px)
  - Visualising and editing collision masks per block
  - Placing, moving and deleting game objects with sprite overlays
  - Exporting modified .bmd and .act binaries

Requirements:
    pip install Pillow
    python sonic_editor.py [res_dir]

  res_dir  Path to the extracted JAR resource folder containing:
             zone1.png ... zone6.png   (tilesets)
             zone1.bmd ... zone6.bmd   (block map data)
             ZONE1ACT.act ... ZONE6ACT.act  (object/act data)
             blkcol.bct                (collision data)
             *.png                     (object sprites)

  If res_dir is omitted the editor starts without game data and asks
  you to select the folder via the menu.
"""

import copy
import os
import struct
import sys
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

try:
    from PIL import Image, ImageDraw, ImageTk
except ImportError:
    print("Pillow is required.  Install with:  pip install Pillow")
    sys.exit(1)

# ---------------------------------------------------------------------------
# Constants
# ---------------------------------------------------------------------------

TILE_PX          = 16     # pixels per tile
BLOCK_PX         = 256    # pixels per block  (16 tiles * 16 px)
TILES_PER_ROW_TS = 10     # tiles per row in the tileset PNG
TILES_PER_SIDE   = 16     # tiles per side of a block (16 * 16 = 256 tiles)
BYTES_PER_BLOCK_BMD = 512  # 256 tiles * 2 bytes each
BYTES_PER_BLOCK_BCT = 32   # 256 bits
NUM_ZONES        = 6
NUM_ACTS         = 3
MAX_UNDO         = 50

ZOOM_LEVELS = [0.25, 0.5, 1.0, 2.0]

# PIL Transpose operations for the four rotation codes (clockwise degrees)
_ROT_XPOSE = {
    0: None,
    1: Image.Transpose.ROTATE_270,   # 90 deg clockwise
    2: Image.Transpose.ROTATE_180,   # 180 deg
    3: Image.Transpose.ROTATE_90,    # 270 deg clockwise
}

# ---------------------------------------------------------------------------
# Placeholder world-map data
# ---------------------------------------------------------------------------
# Format: WORLD_MAP_DATA[zone_idx][act_idx] = list-of-rows,
#         each row is a list of block indices (0 = empty, 1-83 = block).
#
# Replace the placeholder below with the actual array extracted from the
# decompiled MainCanvas.java "static int[][][][] worldMapData" literal.
# ---------------------------------------------------------------------------

def _flat_row(width, ground_block=1, sky_block=0, ground_rows=2):
    """Helper: build a list-of-rows representing a flat ground."""
    rows = []
    for r in range(7):
        if r >= (7 - ground_rows):
            rows.append([ground_block] * width)
        else:
            rows.append([sky_block] * width)
    return rows


WORLD_MAP_DATA = [
    [_flat_row(32, ground_block=i * 3 + 1) for _ in range(NUM_ACTS)]
    for i in range(NUM_ZONES)
]

# ---------------------------------------------------------------------------
# Object type table
# ---------------------------------------------------------------------------
# Each entry:  (display_name, sprite_filename, hitbox_w, hitbox_h, category)
#
# Categories: 'ring', 'enemy', 'item', 'platform', 'hazard', 'goal', 'misc'
# ---------------------------------------------------------------------------

OBJECT_TYPES = {
    0:  ("Ring (H-chain)",    "ring.png",      16, 16, "ring"),
    1:  ("Ring (V-chain)",    "ring.png",      16, 16, "ring"),
    2:  ("10-Ring",           "ring10.png",    16, 16, "ring"),
    3:  ("Spring (Up)",       "spring.png",    32, 16, "item"),
    4:  ("Spring (Fwd)",      "spring.png",    16, 32, "item"),
    5:  ("Shield",            "shield.png",    24, 24, "item"),
    6:  ("Invincibility",     "star.png",      24, 24, "item"),
    7:  ("Speed Shoes",       "shoes.png",     24, 24, "item"),
    8:  ("Extra Life",        "1up.png",       24, 24, "item"),
    9:  ("Spike",             "toge.png",      32, 16, "hazard"),
    10: ("Spike (Ceil)",      "toge.png",      32, 16, "hazard"),
    11: ("Moving Platform",   "platform.png",  64, 16, "platform"),
    12: ("Falling Platform",  "platform.png",  64, 16, "platform"),
    13: ("Bumper",            "bumper.png",    32, 32, "item"),
    14: ("Exploding Block",   "blk_ex.png",    32, 32, "misc"),
    15: ("Checkpoint",        "checkpoint.png",16, 32, "goal"),
    16: ("Signpost",          "sign.png",      16, 40, "goal"),
    17: ("Capsule",           "capsule.png",   40, 40, "goal"),
    18: ("Motobug",           "motobug.png",   28, 24, "enemy"),
    19: ("Caterkiller",       "cater.png",     48, 24, "enemy"),
    20: ("Buzz Bomber",       "buzz.png",      32, 24, "enemy"),
    21: ("Crabmeat",          "crab.png",      28, 28, "enemy"),
    22: ("Chopper",           "chopper.png",   24, 28, "enemy"),
    23: ("Bat",               "bat.png",       28, 24, "enemy"),
    24: ("Uni-Uni",           "uni.png",       24, 24, "enemy"),
    25: ("Burrobot",          "burro.png",     28, 28, "enemy"),
    26: ("Roller",            "roller.png",    28, 28, "enemy"),
    27: ("Bomb",              "bomb.png",      24, 24, "hazard"),
    28: ("Fire",              "fire.png",      16, 32, "hazard"),
    29: ("Lava Pool",         "lava.png",      32, 16, "hazard"),
    30: ("Swinging Platform", "swing.png",     48, 16, "platform"),
    31: ("Lift (Vertical)",   "lift.png",      48, 16, "platform"),
    32: ("Lift (Horizontal)", "lift.png",      48, 16, "platform"),
    33: ("Pushable Block",    "push_blk.png",  32, 32, "misc"),
    34: ("Warp Gate",         "warp.png",      32, 48, "misc"),
    35: ("Super Ring (20)",   "ring20.png",    16, 16, "ring"),
    36: ("S Monitor",         "monitor_s.png", 32, 32, "item"),
    37: ("R Monitor",         "monitor_r.png", 32, 32, "item"),
    38: ("I Monitor",         "monitor_i.png", 32, 32, "item"),
    39: ("1UP Monitor",       "monitor_1.png", 32, 32, "item"),
    40: ("Hachi",             "hachi.png",     28, 28, "enemy"),
    41: ("Nezu",              "nezu.png",      24, 24, "enemy"),
    42: ("Pata-Pata",         "pata.png",      32, 28, "enemy"),
    43: ("Jaws",              "jaws.png",      32, 28, "enemy"),
    44: ("Spiny",             "spiny.png",     24, 24, "enemy"),
    45: ("Sandworm",          "worm.png",      48, 24, "enemy"),
    46: ("Bata-Bata",         "bata.png",      32, 24, "enemy"),
    47: ("Rhinobot",          "rhino.png",     40, 32, "enemy"),
    48: ("Coconuts",          "coconuts.png",  28, 28, "enemy"),
    49: ("Asteron",           "asteron.png",   32, 32, "enemy"),
    50: ("Grabber",           "grabber.png",   32, 48, "enemy"),
    51: ("Shellcracker",      "shellcr.png",   32, 32, "enemy"),
    52: ("Slicer",            "slicer.png",    28, 28, "enemy"),
    53: ("Turtloid",          "turtloid.png",  32, 32, "enemy"),
    54: ("Balkiry",           "balkiry.png",   28, 24, "enemy"),
    55: ("Penguinator",       "penguin.png",   24, 32, "enemy"),
    56: ("Snowbot",           "snowbot.png",   32, 32, "enemy"),
    57: ("Kani",              "kani.png",      28, 28, "enemy"),
    58: ("Spike Trap",        "spike_t.png",   16, 32, "hazard"),
    59: ("Rolling Rock",      "rock.png",      32, 32, "hazard"),
    60: ("Icicle",            "icicle.png",    16, 32, "hazard"),
    61: ("Bubbles",           "bubbles.png",   24, 24, "item"),
    62: ("Flame Shield",      "flmshld.png",   24, 24, "item"),
    63: ("Ring (pattern A)",  "ring.png",      16, 16, "ring"),
    64: ("Ring (pattern B)",  "ring.png",      16, 16, "ring"),
    65: ("Ring (pattern C)",  "ring.png",      16, 16, "ring"),
    66: ("Ring (pattern D)",  "ring.png",      16, 16, "ring"),
    67: ("Ring (pattern E)",  "ring.png",      16, 16, "ring"),
    68: ("Ring (pattern F)",  "ring.png",      16, 16, "ring"),
    69: ("Ring (pattern G)",  "ring.png",      16, 16, "ring"),
    86: ("Fish",              "fish2.png",     28, 28, "enemy"),
}

# Types whose 'count' byte spawns additional instances (ring chains)
RING_GROUP_TYPES = {0, 1, 63, 64, 65, 66, 67, 68, 69}

# Object category display colours (R, G, B)
CATEGORY_COLOURS = {
    "ring":     (255, 220,  50),
    "enemy":    (220,  80,  80),
    "item":     ( 80, 200,  80),
    "platform": ( 80, 160, 220),
    "hazard":   (220, 150,  50),
    "goal":     (200,  80, 200),
    "misc":     (180, 180, 180),
}

# ---------------------------------------------------------------------------
# Binary format helpers
# ---------------------------------------------------------------------------

def read_tile_info(bmd: bytearray, block_idx: int, tx: int, ty: int):
    """Return (src_x, src_y, rotation) for a tile inside a block.

    src_x / src_y are pixel coordinates inside the zone tileset PNG.
    rotation is 0-3 (clockwise 0°/90°/180°/270°).
    """
    offset      = block_idx * BYTES_PER_BLOCK_BMD + (tx + ty * TILES_PER_SIDE) * 2
    ctrl        = bmd[offset]
    tile_id     = bmd[offset + 1]
    raw_offset  = ctrl & 3          # bits 1-0
    image_off   = 1 if (ctrl & 1) else (2 if raw_offset == 2 else 0)
    rotation    = (ctrl >> 3) & 3
    effective   = tile_id + image_off * 256
    src_x       = (effective % TILES_PER_ROW_TS) * TILE_PX
    src_y       = (effective // TILES_PER_ROW_TS) * TILE_PX
    return src_x, src_y, rotation


def write_tile_info(bmd: bytearray, block_idx: int, tx: int, ty: int,
                    tile_id: int, image_off: int, rotation: int):
    """Write a single tile's ctrl+id bytes back into bmd."""
    offset = block_idx * BYTES_PER_BLOCK_BMD + (tx + ty * TILES_PER_SIDE) * 2
    ctrl = (image_off & 3) | ((rotation & 3) << 3)
    bmd[offset]     = ctrl
    bmd[offset + 1] = tile_id & 0xFF


def is_solid(col_data: bytearray, block_idx: int, tx: int, ty: int,
             rotation: int = 0) -> bool:
    """Return True if the tile at (tx, ty) inside block_idx is solid.

    Implements the four rotation variants of blockColChk() from MainCanvas.java.
    """
    base = block_idx * BYTES_PER_BLOCK_BCT
    if rotation == 0:
        byte_idx = base + tx * 2 + (ty >> 3)
        bit      = (col_data[byte_idx] >> (7 - (ty & 7))) & 1
    elif rotation == 1:   # 90°
        byte_idx = base + (15 - tx) * 2 + (ty >> 3)
        bit      = (col_data[byte_idx] >> (7 - (ty & 7))) & 1
    elif rotation == 2:   # 180°
        byte_idx = base + tx * 2 + ((15 - ty) >> 3)
        bit      = (col_data[byte_idx] >> (ty & 7)) & 1
    else:                 # 270°
        byte_idx = base + (15 - tx) * 2 + ((15 - ty) >> 3)
        bit      = (col_data[byte_idx] >> (ty & 7)) & 1
    return bool(bit)


def parse_act_buf(buf: (bytes, bytearray)) -> list:
    """Parse a raw act buffer into a list of object dicts (7 bytes each)."""
    n = len(buf) // 7
    objects = []
    for i in range(n):
        b = i * 7
        objects.append({
            'x':     ((buf[b]     & 0xFF) << 8) | (buf[b + 1] & 0xFF),
            'y':     ((buf[b + 2] & 0xFF) << 8) | (buf[b + 3] & 0xFF),
            'param': buf[b + 4] & 0xFF,
            'type':  buf[b + 5] & 0xFF,
            'count': buf[b + 6] & 0xFF,
        })
    return objects


def serialize_act_buf(objects: list) -> bytearray:
    """Serialize object list to raw bytes, sorted by X (game requirement)."""
    sorted_objs = sorted(objects, key=lambda o: o['x'])
    buf = bytearray()
    for o in sorted_objs:
        x = o['x'] & 0xFFFF
        y = o['y'] & 0xFFFF
        buf += bytes([
            (x >> 8) & 0xFF, x & 0xFF,
            (y >> 8) & 0xFF, y & 0xFF,
            o['param'] & 0xFF,
            o['type']  & 0xFF,
            o['count'] & 0xFF,
        ])
    return buf


def parse_act_file(data: (bytes, bytearray)):
    """Parse a full .act file.

    Returns (raw_act_bufs, parsed_acts) where raw_act_bufs is a list of
    bytearrays (one per act slot, up to 4) and parsed_acts is a list of
    lists-of-dicts.
    """
    if len(data) < 8:
        empty = [bytearray(), bytearray(), bytearray(), bytearray()]
        return empty, [[], [], [], []]
    sizes = [((data[i * 2] & 0xFF) << 8) | (data[i * 2 + 1] & 0xFF)
             for i in range(4)]
    pos = 8
    raw_bufs = []
    for s in sizes:
        raw_bufs.append(bytearray(data[pos:pos + s]))
        pos += s
    parsed = [parse_act_buf(b) for b in raw_bufs]
    return raw_bufs, parsed


def export_act_file(raw_bufs: list, current_act: int,
                    new_objects: list) -> bytes:
    """Re-assemble an .act file after editing one act.

    raw_bufs    : list of bytearrays (original 4 acts)
    current_act : which act was edited (0-2)
    new_objects : the modified object list for current_act
    Returns the complete file as bytes.
    """
    updated = list(raw_bufs)
    updated[current_act] = serialize_act_buf(new_objects)
    buf = bytearray()
    for b in updated:
        size = len(b)
        buf += bytes([(size >> 8) & 0xFF, size & 0xFF])
    for b in updated:
        buf += b
    return bytes(buf)


# ---------------------------------------------------------------------------
# Rendering helpers
# ---------------------------------------------------------------------------

def _make_checker(w: int, h: int) -> Image.Image:
    """Create a grey/dark-grey checkerboard (missing-tile placeholder)."""
    img = Image.new("RGBA", (w, h), (100, 100, 100, 255))
    draw = ImageDraw.Draw(img)
    cs = 8
    for ty in range(0, h, cs):
        for tx in range(0, w, cs):
            if (tx // cs + ty // cs) % 2 == 0:
                draw.rectangle([tx, ty, tx + cs - 1, ty + cs - 1],
                                fill=(80, 80, 80, 255))
    return img


def render_block(bmd: bytearray, block_idx: int,
                 tileset: Image.Image) -> Image.Image:
    """Render a single 256x256 px block image from bmd data and the tileset."""
    out = Image.new("RGBA", (BLOCK_PX, BLOCK_PX), (0, 0, 0, 0))
    if tileset is None:
        return _make_checker(BLOCK_PX, BLOCK_PX)
    for ty in range(TILES_PER_SIDE):
        for tx in range(TILES_PER_SIDE):
            sx, sy, rot = read_tile_info(bmd, block_idx, tx, ty)
            # guard against out-of-bounds tileset coords
            tw = tileset.width
            th = tileset.height
            if sx + TILE_PX > tw or sy + TILE_PX > th:
                tile = _make_checker(TILE_PX, TILE_PX)
            else:
                tile = tileset.crop((sx, sy, sx + TILE_PX, sy + TILE_PX))
            if tile.mode != "RGBA":
                tile = tile.convert("RGBA")
            xform = _ROT_XPOSE.get(rot)
            if xform is not None:
                tile = tile.transpose(xform)
            out.paste(tile, (tx * TILE_PX, ty * TILE_PX), mask=tile.split()[3])
    return out


def render_block_collision(col_data: bytearray,
                           block_idx: int,
                           bmd: bytearray) -> Image.Image:
    """Render a 256x256 collision overlay (semi-transparent red squares)."""
    img = Image.new("RGBA", (BLOCK_PX, BLOCK_PX), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)
    for ty in range(TILES_PER_SIDE):
        for tx in range(TILES_PER_SIDE):
            _, _, rot = read_tile_info(bmd, block_idx, tx, ty)
            if is_solid(col_data, block_idx, tx, ty, rot):
                x0, y0 = tx * TILE_PX, ty * TILE_PX
                draw.rectangle([x0, y0, x0 + TILE_PX - 1, y0 + TILE_PX - 1],
                                fill=(255, 0, 0, 100))
    return img


def render_map(world_map_act: list, bmd: bytearray,
               tileset: Image.Image,
               col_data: bytearray = None,
               show_collision: bool = False,
               show_tile_grid: bool = False,
               show_block_grid: bool = False) -> Image.Image:
    """Render the full map for one act.

    world_map_act  : list of rows, each row is a list of block indices
    """
    if not world_map_act:
        return Image.new("RGBA", (BLOCK_PX, BLOCK_PX), (30, 30, 30, 255))
    rows = len(world_map_act)
    cols = max(len(r) for r in world_map_act)
    w = cols * BLOCK_PX
    h = rows * BLOCK_PX
    out = Image.new("RGBA", (w, h), (30, 30, 30, 255))
    for row_idx, row in enumerate(world_map_act):
        for col_idx, blk in enumerate(row):
            if blk == 0:
                continue
            px = col_idx * BLOCK_PX
            py = row_idx * BLOCK_PX
            blk_img = render_block(bmd, blk, tileset)
            out.paste(blk_img, (px, py), mask=blk_img.split()[3])
            if show_collision and col_data:
                col_img = render_block_collision(col_data, blk, bmd)
                out.paste(col_img, (px, py), mask=col_img.split()[3])
    if show_tile_grid:
        draw = ImageDraw.Draw(out)
        for x in range(0, w, TILE_PX):
            draw.line([(x, 0), (x, h - 1)], fill=(60, 60, 60, 100))
        for y in range(0, h, TILE_PX):
            draw.line([(0, y), (w - 1, y)], fill=(60, 60, 60, 100))
    if show_block_grid:
        draw = ImageDraw.Draw(out)
        for x in range(0, w, BLOCK_PX):
            draw.line([(x, 0), (x, h - 1)], fill=(0, 200, 200, 160))
        for y in range(0, h, BLOCK_PX):
            draw.line([(0, y), (w - 1, y)], fill=(0, 200, 200, 160))
    return out


def _apply_zoom(img: Image.Image, zoom: float) -> Image.Image:
    if zoom == 1.0:
        return img
    new_w = max(1, int(img.width * zoom))
    new_h = max(1, int(img.height * zoom))
    return img.resize((new_w, new_h), Image.NEAREST)


# ---------------------------------------------------------------------------
# Main Editor class
# ---------------------------------------------------------------------------

class SonicEditor:
    """Two-tab tkinter editor for Sonic J2ME game resources."""

    # ------------------------------------------------------------------
    # Construction / setup
    # ------------------------------------------------------------------

    def __init__(self, root: tk.Tk, res_dir: str = ""):
        self.root = root
        self.root.title("Sonic J2ME Map & Object Editor")
        self.root.geometry("1280x800")

        # Resource directory
        self.res_dir = res_dir

        # Per-zone data
        self.tilesets:   dict = {}   # zone → PIL.Image (RGBA)
        self.bmd_data:   dict = {}   # zone → bytearray
        self.act_raw:    dict = {}   # zone → list[bytearray]  (4 act slots)
        self.act_parsed: dict = {}   # zone → list[list[dict]]
        self.col_data:   bytearray = bytearray(8192)
        self.sprites:    dict = {}   # filename → PIL.Image (RGBA)

        # Current editor state
        self.zone = 0
        self.act  = 0
        self.zoom_idx = 2  # index into ZOOM_LEVELS (default 1.0)

        # Map-editor state
        self.brush_mode = tk.StringVar(value="block")  # "block" or "tile"
        self.tool       = tk.StringVar(value="paint")  # "paint" or "erase"
        self.selected_block  = 1        # block index to paint
        self.selected_tile_x = 0       # tile coords for tileset palette
        self.selected_tile_y = 0
        self.show_collision  = tk.BooleanVar(value=False)
        self.show_tile_grid  = tk.BooleanVar(value=False)
        self.show_block_grid = tk.BooleanVar(value=True)
        self.active_block_edit = None  # (bx, by) – block open in right panel
        self._map_img: Image.Image = None   # cached full-map PIL image
        self._block_tk_cache: dict = {}     # (bx, by) → ImageTk.PhotoImage
        self._ts_tk: ImageTk.PhotoImage = None
        self._block_edit_tk: ImageTk.PhotoImage = None
        self.map_undo: list = []
        self.map_redo: list = []

        # Object-editor state
        self.obj_selected_type = 0
        self.obj_filter_cat    = tk.StringVar(value="all")
        self.objects:   list = []         # list of dicts for current act
        self.selected_obj_idx  = None
        self._obj_map_tk: ImageTk.PhotoImage = None
        self._obj_sprite_tks:  list = []  # keep refs alive
        self.obj_undo: list = []
        self.obj_redo: list = []
        self._drag_start = None
        self._drag_orig  = None

        self._build_ui()
        if res_dir and os.path.isdir(res_dir):
            self._load_resources()
        else:
            self._refresh_map()
            self._refresh_obj_map()

    # ------------------------------------------------------------------
    # UI construction
    # ------------------------------------------------------------------

    def _build_ui(self):
        """Build the entire GUI."""
        # Menu bar
        menubar = tk.Menu(self.root)
        file_menu = tk.Menu(menubar, tearoff=0)
        file_menu.add_command(label="Open resource folder…",
                              command=self._open_res_dir)
        file_menu.add_separator()
        file_menu.add_command(label="Export BMD…", command=self._export_bmd)
        file_menu.add_command(label="Export ACT…", command=self._export_act)
        file_menu.add_separator()
        file_menu.add_command(label="Quit", command=self.root.quit)
        menubar.add_cascade(label="File", menu=file_menu)
        self.root.config(menu=menubar)

        # Zone / act selectors (top bar)
        top = tk.Frame(self.root, bd=1, relief=tk.RAISED)
        top.pack(side=tk.TOP, fill=tk.X)
        tk.Label(top, text="Zone:").pack(side=tk.LEFT, padx=4)
        self.zone_var = tk.IntVar(value=1)
        for z in range(1, NUM_ZONES + 1):
            tk.Radiobutton(top, text=str(z), variable=self.zone_var,
                           value=z,
                           command=self._on_zone_act_change).pack(side=tk.LEFT)
        tk.Label(top, text="  Act:").pack(side=tk.LEFT, padx=4)
        self.act_var = tk.IntVar(value=1)
        for a in range(1, NUM_ACTS + 1):
            tk.Radiobutton(top, text=str(a), variable=self.act_var,
                           value=a,
                           command=self._on_zone_act_change).pack(side=tk.LEFT)
        tk.Label(top, text="  Zoom:").pack(side=tk.LEFT, padx=8)
        self.zoom_var = tk.StringVar(value="100%")
        zoom_cb = ttk.Combobox(top, textvariable=self.zoom_var, width=7,
                               values=["25%", "50%", "100%", "200%"],
                               state="readonly")
        zoom_cb.pack(side=tk.LEFT)
        zoom_cb.bind("<<ComboboxSelected>>", self._on_zoom_change)

        # Notebook tabs
        self.notebook = ttk.Notebook(self.root)
        self.notebook.pack(fill=tk.BOTH, expand=True)
        self.tab_map = tk.Frame(self.notebook)
        self.tab_obj = tk.Frame(self.notebook)
        self.notebook.add(self.tab_map, text="Map Editor")
        self.notebook.add(self.tab_obj, text="Object Editor")
        self.notebook.bind("<<NotebookTabChanged>>", self._on_tab_change)

        self._build_map_tab()
        self._build_obj_tab()

        # Keyboard shortcuts
        self.root.bind("<Control-z>", self._on_undo)
        self.root.bind("<Control-y>", self._on_redo)

    # ------------------------------------------------------------------
    # Map Editor Tab
    # ------------------------------------------------------------------

    def _build_map_tab(self):
        tab = self.tab_map

        # ---- Left panel: tileset palette + options ------------------
        left = tk.Frame(tab, width=200, bd=1, relief=tk.SUNKEN)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        tk.Label(left, text="Tileset Palette", font=("", 9, "bold")).pack(pady=2)
        ts_frame = tk.Frame(left)
        ts_frame.pack(fill=tk.BOTH, expand=True)
        ts_sb_v = tk.Scrollbar(ts_frame, orient=tk.VERTICAL)
        ts_sb_h = tk.Scrollbar(ts_frame, orient=tk.HORIZONTAL)
        self.ts_canvas = tk.Canvas(ts_frame, bg="#222",
                                   xscrollcommand=ts_sb_h.set,
                                   yscrollcommand=ts_sb_v.set,
                                   cursor="crosshair")
        ts_sb_v.config(command=self.ts_canvas.yview)
        ts_sb_h.config(command=self.ts_canvas.xview)
        ts_sb_v.pack(side=tk.RIGHT, fill=tk.Y)
        ts_sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.ts_canvas.pack(fill=tk.BOTH, expand=True)
        self.ts_canvas.bind("<Button-1>", self._on_ts_click)
        self._ts_sel_rect = None  # selection rectangle item id

        tk.Label(left, text="Brush:").pack()
        tk.Radiobutton(left, text="Block (256 px)", variable=self.brush_mode,
                       value="block").pack(anchor=tk.W)
        tk.Radiobutton(left, text="Tile (16 px)", variable=self.brush_mode,
                       value="tile").pack(anchor=tk.W)
        tk.Label(left, text="Tool:").pack()
        tk.Radiobutton(left, text="Paint", variable=self.tool,
                       value="paint").pack(anchor=tk.W)
        tk.Radiobutton(left, text="Erase", variable=self.tool,
                       value="erase").pack(anchor=tk.W)

        tk.Checkbutton(left, text="Collision",
                       variable=self.show_collision,
                       command=self._refresh_map).pack(anchor=tk.W)
        tk.Checkbutton(left, text="Tile grid",
                       variable=self.show_tile_grid,
                       command=self._refresh_map).pack(anchor=tk.W)
        tk.Checkbutton(left, text="Block grid",
                       variable=self.show_block_grid,
                       command=self._refresh_map).pack(anchor=tk.W)

        # ---- Centre: scrollable map canvas --------------------------
        centre = tk.Frame(tab)
        centre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        map_sb_v = tk.Scrollbar(centre, orient=tk.VERTICAL)
        map_sb_h = tk.Scrollbar(centre, orient=tk.HORIZONTAL)
        self.map_canvas = tk.Canvas(centre, bg="#111", cursor="crosshair",
                                    xscrollcommand=map_sb_h.set,
                                    yscrollcommand=map_sb_v.set)
        map_sb_v.config(command=self.map_canvas.yview)
        map_sb_h.config(command=self.map_canvas.xview)
        map_sb_v.pack(side=tk.RIGHT, fill=tk.Y)
        map_sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.map_canvas.pack(fill=tk.BOTH, expand=True)
        self.map_canvas.bind("<Button-1>",        self._on_map_click)
        self.map_canvas.bind("<B1-Motion>",       self._on_map_drag)
        self.map_canvas.bind("<Button-3>",        self._on_map_right_click)

        # Status bar below map canvas
        self.map_status = tk.StringVar(value="Ready")
        tk.Label(centre, textvariable=self.map_status, anchor=tk.W,
                 relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

        # ---- Right panel: block editor ------------------------------
        right = tk.Frame(tab, width=290, bd=1, relief=tk.SUNKEN)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)
        tk.Label(right, text="Block Editor", font=("", 9, "bold")).pack(pady=2)
        tk.Label(right,
                 text="Right-click map to open block,\nLeft-click here to paint tiles.",
                 justify=tk.LEFT).pack(padx=4, anchor=tk.W)
        be_frame = tk.Frame(right)
        be_frame.pack(fill=tk.BOTH, expand=True)
        be_sb_v = tk.Scrollbar(be_frame, orient=tk.VERTICAL)
        be_sb_h = tk.Scrollbar(be_frame, orient=tk.HORIZONTAL)
        self.block_edit_canvas = tk.Canvas(be_frame, bg="#333",
                                           width=256, height=256,
                                           xscrollcommand=be_sb_h.set,
                                           yscrollcommand=be_sb_v.set,
                                           cursor="crosshair")
        be_sb_v.config(command=self.block_edit_canvas.yview)
        be_sb_h.config(command=self.block_edit_canvas.xview)
        be_sb_v.pack(side=tk.RIGHT, fill=tk.Y)
        be_sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.block_edit_canvas.pack(fill=tk.BOTH, expand=True)
        self.block_edit_canvas.bind("<Button-1>", self._on_block_edit_click)

        self.block_info_var = tk.StringVar(value="No block selected")
        tk.Label(right, textvariable=self.block_info_var,
                 anchor=tk.W).pack(fill=tk.X, padx=4)

    # ------------------------------------------------------------------
    # Object Editor Tab
    # ------------------------------------------------------------------

    def _build_obj_tab(self):
        tab = self.tab_obj

        # ---- Left panel: object palette --------------------------------
        left = tk.Frame(tab, width=220, bd=1, relief=tk.SUNKEN)
        left.pack(side=tk.LEFT, fill=tk.Y)
        left.pack_propagate(False)

        tk.Label(left, text="Object Palette", font=("", 9, "bold")).pack(pady=2)
        tk.Label(left, text="Category filter:").pack(anchor=tk.W, padx=4)
        cats = ["all"] + sorted(set(v[4] for v in OBJECT_TYPES.values()))
        cat_cb = ttk.Combobox(left, textvariable=self.obj_filter_cat,
                              values=cats, state="readonly")
        cat_cb.pack(fill=tk.X, padx=4)
        cat_cb.bind("<<ComboboxSelected>>", self._on_cat_filter_change)

        list_frame = tk.Frame(left)
        list_frame.pack(fill=tk.BOTH, expand=True)
        obj_sb = tk.Scrollbar(list_frame)
        self.obj_listbox = tk.Listbox(list_frame,
                                      yscrollcommand=obj_sb.set,
                                      exportselection=False)
        obj_sb.config(command=self.obj_listbox.yview)
        obj_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.obj_listbox.pack(fill=tk.BOTH, expand=True)
        self.obj_listbox.bind("<<ListboxSelect>>", self._on_obj_type_select)
        self._populate_obj_listbox()

        # ---- Centre: scrollable map canvas with object overlay ---------
        centre = tk.Frame(tab)
        centre.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        obj_map_sb_v = tk.Scrollbar(centre, orient=tk.VERTICAL)
        obj_map_sb_h = tk.Scrollbar(centre, orient=tk.HORIZONTAL)
        self.obj_map_canvas = tk.Canvas(centre, bg="#111",
                                        cursor="crosshair",
                                        xscrollcommand=obj_map_sb_h.set,
                                        yscrollcommand=obj_map_sb_v.set)
        obj_map_sb_v.config(command=self.obj_map_canvas.yview)
        obj_map_sb_h.config(command=self.obj_map_canvas.xview)
        obj_map_sb_v.pack(side=tk.RIGHT, fill=tk.Y)
        obj_map_sb_h.pack(side=tk.BOTTOM, fill=tk.X)
        self.obj_map_canvas.pack(fill=tk.BOTH, expand=True)
        self.obj_map_canvas.bind("<Button-1>",  self._on_obj_canvas_click)
        self.obj_map_canvas.bind("<B1-Motion>", self._on_obj_canvas_drag)
        self.obj_map_canvas.bind("<ButtonRelease-1>",
                                 self._on_obj_canvas_release)
        self.obj_map_canvas.bind("<Button-3>",  self._on_obj_canvas_right)

        self.obj_map_status = tk.StringVar(value="Click to place object")
        tk.Label(centre, textvariable=self.obj_map_status, anchor=tk.W,
                 relief=tk.SUNKEN).pack(side=tk.BOTTOM, fill=tk.X)

        # ---- Right panel: object properties + instance list -----------
        right = tk.Frame(tab, width=240, bd=1, relief=tk.SUNKEN)
        right.pack(side=tk.RIGHT, fill=tk.Y)
        right.pack_propagate(False)

        tk.Label(right, text="Selected Object",
                 font=("", 9, "bold")).pack(pady=2)

        prop_frame = tk.LabelFrame(right, text="Properties")
        prop_frame.pack(fill=tk.X, padx=4, pady=2)

        fields = [("X", "prop_x"), ("Y", "prop_y"),
                  ("Param", "prop_param"), ("Type", "prop_type"),
                  ("Count", "prop_count")]
        self._prop_vars = {}
        for label, key in fields:
            row = tk.Frame(prop_frame)
            row.pack(fill=tk.X)
            tk.Label(row, text=label + ":", width=6,
                     anchor=tk.E).pack(side=tk.LEFT)
            var = tk.StringVar()
            entry = tk.Entry(row, textvariable=var, width=10)
            entry.pack(side=tk.LEFT)
            self._prop_vars[key] = var

        tk.Button(right, text="Apply changes",
                  command=self._apply_obj_props).pack(pady=2)
        tk.Button(right, text="Delete selected",
                  command=self._delete_selected_obj).pack(pady=2)

        tk.Label(right, text="Objects in act:",
                 font=("", 9, "bold")).pack(pady=(8, 0))
        inst_frame = tk.Frame(right)
        inst_frame.pack(fill=tk.BOTH, expand=True, padx=4, pady=4)
        inst_sb = tk.Scrollbar(inst_frame)
        self.inst_listbox = tk.Listbox(inst_frame,
                                       yscrollcommand=inst_sb.set,
                                       exportselection=False,
                                       width=28)
        inst_sb.config(command=self.inst_listbox.yview)
        inst_sb.pack(side=tk.RIGHT, fill=tk.Y)
        self.inst_listbox.pack(fill=tk.BOTH, expand=True)
        self.inst_listbox.bind("<<ListboxSelect>>",
                               self._on_inst_listbox_select)

    # ------------------------------------------------------------------
    # Resource loading
    # ------------------------------------------------------------------

    def _open_res_dir(self):
        d = filedialog.askdirectory(title="Select resource folder",
                                    initialdir=self.res_dir or ".")
        if d:
            self.res_dir = d
            self._load_resources()

    def _load_resources(self):
        """Load all tilesets, BMD, ACT and BCT files from self.res_dir."""
        d = self.res_dir
        for z in range(1, NUM_ZONES + 1):
            # Tileset
            ts_path = os.path.join(d, f"zone{z}.png")
            if os.path.isfile(ts_path):
                try:
                    img = Image.open(ts_path)
                    if img.mode != "RGBA":
                        img = img.convert("RGBA")
                    self.tilesets[z] = img
                except Exception as e:
                    print(f"[WARN] Cannot load {ts_path}: {e}")
            # BMD
            bmd_path = os.path.join(d, f"zone{z}.bmd")
            if os.path.isfile(bmd_path):
                try:
                    with open(bmd_path, "rb") as f:
                        self.bmd_data[z] = bytearray(f.read())
                except Exception as e:
                    print(f"[WARN] Cannot load {bmd_path}: {e}")
            else:
                # Stub: 84 empty blocks
                self.bmd_data[z] = bytearray(84 * BYTES_PER_BLOCK_BMD)
            # ACT
            act_path = os.path.join(d, f"ZONE{z}ACT.act")
            if not os.path.isfile(act_path):
                act_path = os.path.join(d, f"zone{z}act.act")
            if os.path.isfile(act_path):
                try:
                    with open(act_path, "rb") as f:
                        raw_bufs, parsed = parse_act_file(f.read())
                    self.act_raw[z]    = raw_bufs
                    self.act_parsed[z] = parsed
                except Exception as e:
                    print(f"[WARN] Cannot load {act_path}: {e}")
                    self.act_raw[z]    = [bytearray()] * 4
                    self.act_parsed[z] = [[] for _ in range(4)]
            else:
                self.act_raw[z]    = [bytearray()] * 4
                self.act_parsed[z] = [[] for _ in range(4)]

        # Collision data
        bct_path = os.path.join(d, "blkcol.bct")
        if os.path.isfile(bct_path):
            try:
                with open(bct_path, "rb") as f:
                    self.col_data = bytearray(f.read())
            except Exception as e:
                print(f"[WARN] Cannot load {bct_path}: {e}")

        # Object sprites (best-effort)
        for type_idx, info in OBJECT_TYPES.items():
            fname = info[1]
            if fname not in self.sprites:
                sp_path = os.path.join(d, fname)
                if os.path.isfile(sp_path):
                    try:
                        img = Image.open(sp_path)
                        if img.mode != "RGBA":
                            img = img.convert("RGBA")
                        self.sprites[fname] = img
                    except Exception as e:
                        print(f"[WARN] Cannot load {sp_path}: {e}")

        self._on_zone_act_change()

    # ------------------------------------------------------------------
    # Zone / act switching
    # ------------------------------------------------------------------

    def _on_zone_act_change(self, *_):
        self.zone = self.zone_var.get()
        self.act  = self.act_var.get() - 1  # internal 0-based index
        self._ensure_bmd()
        self._load_current_objects()
        self._map_img = None
        self._block_tk_cache.clear()
        self.map_undo.clear()
        self.map_redo.clear()
        self.obj_undo.clear()
        self.obj_redo.clear()
        self.active_block_edit = None
        self.block_info_var.set("No block selected")
        self._refresh_tileset_palette()
        self._refresh_map()
        self._refresh_obj_map()

    def _ensure_bmd(self):
        z = self.zone
        if z not in self.bmd_data:
            self.bmd_data[z] = bytearray(84 * BYTES_PER_BLOCK_BMD)
        if z not in self.tilesets:
            pass  # handled in render via checker

    def _load_current_objects(self):
        z = self.zone
        if z in self.act_parsed:
            self.objects = copy.deepcopy(self.act_parsed[z][self.act])
        else:
            self.objects = []
        self._refresh_inst_listbox()

    # ------------------------------------------------------------------
    # Zoom
    # ------------------------------------------------------------------

    def _on_zoom_change(self, *_):
        mapping = {"25%": 0, "50%": 1, "100%": 2, "200%": 3}
        self.zoom_idx = mapping.get(self.zoom_var.get(), 2)
        self._map_img = None
        self._block_tk_cache.clear()
        self._refresh_map()
        self._refresh_obj_map()

    @property
    def zoom(self) -> float:
        return ZOOM_LEVELS[self.zoom_idx]

    # ------------------------------------------------------------------
    # Tab change
    # ------------------------------------------------------------------

    def _on_tab_change(self, *_):
        tab = self.notebook.index("current")
        if tab == 0:
            self._refresh_map()
        else:
            self._refresh_obj_map()

    # ------------------------------------------------------------------
    # Tileset palette
    # ------------------------------------------------------------------

    def _refresh_tileset_palette(self):
        """Redraw the tileset palette in the left panel."""
        c = self.ts_canvas
        c.delete("all")
        ts = self.tilesets.get(self.zone)
        if ts is None:
            c.create_text(10, 10, text="No tileset loaded",
                          fill="white", anchor=tk.NW)
            self._ts_tk = None
            return
        self._ts_tk = ImageTk.PhotoImage(ts)
        c.create_image(0, 0, anchor=tk.NW, image=self._ts_tk)
        c.config(scrollregion=(0, 0, ts.width, ts.height))
        self._draw_ts_selection()

    def _draw_ts_selection(self):
        c = self.ts_canvas
        if self._ts_sel_rect is not None:
            c.delete(self._ts_sel_rect)
        sx = self.selected_tile_x * TILE_PX
        sy = self.selected_tile_y * TILE_PX
        self._ts_sel_rect = c.create_rectangle(
            sx, sy, sx + TILE_PX - 1, sy + TILE_PX - 1,
            outline="yellow", width=2)

    def _on_ts_click(self, event):
        cx = self.ts_canvas.canvasx(event.x)
        cy = self.ts_canvas.canvasy(event.y)
        self.selected_tile_x = int(cx) // TILE_PX
        self.selected_tile_y = int(cy) // TILE_PX
        self._draw_ts_selection()

    # ------------------------------------------------------------------
    # Map rendering
    # ------------------------------------------------------------------

    def _current_world_map(self) -> list:
        z = self.zone - 1
        a = self.act
        wm = WORLD_MAP_DATA
        if z < len(wm) and a < len(wm[z]):
            return wm[z][a]
        return []

    def _map_grid(self):
        return self._current_world_map()

    def _refresh_map(self):
        """Full rerender of the map canvas."""
        wm = self._current_world_map()
        z  = self.zone
        bmd = self.bmd_data.get(z, bytearray(84 * BYTES_PER_BLOCK_BMD))
        ts  = self.tilesets.get(z)
        col = self.col_data if self.show_collision.get() else None
        self._map_img = render_map(
            wm, bmd, ts, col,
            show_collision=self.show_collision.get(),
            show_tile_grid=self.show_tile_grid.get(),
            show_block_grid=self.show_block_grid.get(),
        )
        scaled = _apply_zoom(self._map_img, self.zoom)
        tk_img = ImageTk.PhotoImage(scaled.convert("RGB"))
        self._map_main_tk = tk_img
        c = self.map_canvas
        c.delete("all")
        c.create_image(0, 0, anchor=tk.NW, image=tk_img)
        c.config(scrollregion=(0, 0, scaled.width, scaled.height))
        self._block_tk_cache.clear()

    def _patch_block_on_canvas(self, bx: int, by: int):
        """Re-render only one 256x256 block and update the canvas."""
        wm = self._current_world_map()
        if by >= len(wm) or bx >= len(wm[by]):
            return
        block_idx = wm[by][bx]
        z   = self.zone
        bmd = self.bmd_data.get(z, bytearray(84 * BYTES_PER_BLOCK_BMD))
        ts  = self.tilesets.get(z)
        if block_idx == 0 or ts is None:
            blk_img = Image.new("RGBA", (BLOCK_PX, BLOCK_PX), (30, 30, 30, 255))
        else:
            blk_img = render_block(bmd, block_idx, ts)
            if self.show_collision.get():
                col_ov = render_block_collision(self.col_data, block_idx, bmd)
                blk_img.paste(col_ov, (0, 0), mask=col_ov.split()[3])
        if self.show_block_grid.get():
            draw = ImageDraw.Draw(blk_img)
            draw.rectangle([0, 0, BLOCK_PX - 1, BLOCK_PX - 1],
                            outline=(0, 200, 200, 160))
        if self.show_tile_grid.get():
            draw = ImageDraw.Draw(blk_img)
            for t in range(0, BLOCK_PX, TILE_PX):
                draw.line([(t, 0), (t, BLOCK_PX - 1)],
                          fill=(60, 60, 60, 100))
                draw.line([(0, t), (BLOCK_PX - 1, t)],
                          fill=(60, 60, 60, 100))

        # Paste into the cached full-map image
        if self._map_img is not None:
            self._map_img.paste(blk_img, (bx * BLOCK_PX, by * BLOCK_PX))

        # Scale and place on canvas
        patch = blk_img.convert("RGB")
        scaled_size = (max(1, int(BLOCK_PX * self.zoom)),
                       max(1, int(BLOCK_PX * self.zoom)))
        patch_scaled = patch.resize(scaled_size, Image.NEAREST)
        tk_patch = ImageTk.PhotoImage(patch_scaled)
        self._block_tk_cache[(bx, by)] = tk_patch
        cx = int(bx * BLOCK_PX * self.zoom)
        cy = int(by * BLOCK_PX * self.zoom)
        self.map_canvas.create_image(cx, cy, anchor=tk.NW, image=tk_patch)

    # ------------------------------------------------------------------
    # Map editor events
    # ------------------------------------------------------------------

    def _canvas_to_block(self, cx: float, cy: float):
        """Convert canvas pixel coords to (bx, by) block indices."""
        bx = int(cx / self.zoom / BLOCK_PX)
        by = int(cy / self.zoom / BLOCK_PX)
        return bx, by

    def _canvas_to_tile(self, cx: float, cy: float):
        """Convert canvas pixel coords to (bx, by, tx, ty)."""
        px = cx / self.zoom
        py = cy / self.zoom
        bx = int(px / BLOCK_PX)
        by = int(py / BLOCK_PX)
        tx = int((px % BLOCK_PX) / TILE_PX)
        ty = int((py % BLOCK_PX) / TILE_PX)
        return bx, by, tx, ty

    def _on_map_click(self, event):
        cx = self.map_canvas.canvasx(event.x)
        cy = self.map_canvas.canvasy(event.y)
        self._paint_at(cx, cy)

    def _on_map_drag(self, event):
        cx = self.map_canvas.canvasx(event.x)
        cy = self.map_canvas.canvasy(event.y)
        self._paint_at(cx, cy)

    def _paint_at(self, cx: float, cy: float):
        wm = self._current_world_map()
        if not wm:
            return
        mode = self.brush_mode.get()
        tool = self.tool.get()
        if mode == "block":
            bx, by = self._canvas_to_block(cx, cy)
            if by < 0 or by >= len(wm):
                return
            row = wm[by]
            if bx < 0 or bx >= len(row):
                return
            new_val = 0 if tool == "erase" else self.selected_block
            if row[bx] == new_val:
                return
            self._save_map_undo()
            row[bx] = new_val
            self._patch_block_on_canvas(bx, by)
            self.map_status.set(f"Block ({bx},{by}) → {new_val}")
        else:  # tile mode
            bx, by, tx, ty = self._canvas_to_tile(cx, cy)
            if by < 0 or by >= len(wm):
                return
            row = wm[by]
            if bx < 0 or bx >= len(row):
                return
            block_idx = row[bx]
            if block_idx == 0:
                return
            z   = self.zone
            bmd = self.bmd_data.get(z)
            if bmd is None:
                return
            self._save_map_undo()
            if tool == "erase":
                write_tile_info(bmd, block_idx, tx, ty, 0, 0, 0)
            else:
                eff = (self.selected_tile_y * TILES_PER_ROW_TS
                       + self.selected_tile_x)
                img_off = eff // 256
                tile_id = eff % 256
                write_tile_info(bmd, block_idx, tx, ty, tile_id, img_off, 0)
            self._patch_block_on_canvas(bx, by)
            self._refresh_block_editor()

    def _on_map_right_click(self, event):
        """Right-click: open block in block editor (right panel)."""
        cx = self.map_canvas.canvasx(event.x)
        cy = self.map_canvas.canvasy(event.y)
        bx, by = self._canvas_to_block(cx, cy)
        wm = self._current_world_map()
        if by < 0 or by >= len(wm):
            return
        row = wm[by]
        if bx < 0 or bx >= len(row):
            return
        block_idx = row[bx]
        self.active_block_edit = (bx, by)
        self.block_info_var.set(f"Block ({bx},{by}) index={block_idx}")
        self._refresh_block_editor()

    # ------------------------------------------------------------------
    # Block editor (right panel of Map tab)
    # ------------------------------------------------------------------

    def _refresh_block_editor(self):
        if self.active_block_edit is None:
            return
        bx, by = self.active_block_edit
        wm = self._current_world_map()
        if by >= len(wm) or bx >= len(wm[by]):
            return
        block_idx = wm[by][bx]
        z   = self.zone
        bmd = self.bmd_data.get(z, bytearray(84 * BYTES_PER_BLOCK_BMD))
        ts  = self.tilesets.get(z)
        blk_img = render_block(bmd, block_idx, ts) if block_idx > 0 else \
            Image.new("RGBA", (BLOCK_PX, BLOCK_PX), (30, 30, 30, 255))
        # Tile grid overlay
        draw = ImageDraw.Draw(blk_img)
        for t in range(0, BLOCK_PX, TILE_PX):
            draw.line([(t, 0), (t, BLOCK_PX - 1)], fill=(80, 80, 80, 200))
            draw.line([(0, t), (BLOCK_PX - 1, t)], fill=(80, 80, 80, 200))
        self._block_edit_tk = ImageTk.PhotoImage(blk_img.convert("RGB"))
        c = self.block_edit_canvas
        c.delete("all")
        c.create_image(0, 0, anchor=tk.NW, image=self._block_edit_tk)
        c.config(scrollregion=(0, 0, BLOCK_PX, BLOCK_PX))

    def _on_block_edit_click(self, event):
        """Paint the selected tile into the block at the clicked position."""
        if self.active_block_edit is None:
            return
        bx, by = self.active_block_edit
        wm = self._current_world_map()
        if by >= len(wm) or bx >= len(wm[by]):
            return
        block_idx = wm[by][bx]
        if block_idx == 0:
            return
        cx = self.block_edit_canvas.canvasx(event.x)
        cy = self.block_edit_canvas.canvasy(event.y)
        tx = int(cx) // TILE_PX
        ty = int(cy) // TILE_PX
        if not (0 <= tx < TILES_PER_SIDE and 0 <= ty < TILES_PER_SIDE):
            return
        z   = self.zone
        bmd = self.bmd_data.get(z)
        if bmd is None:
            return
        self._save_map_undo()
        tool = self.tool.get()
        if tool == "erase":
            write_tile_info(bmd, block_idx, tx, ty, 0, 0, 0)
        else:
            eff = (self.selected_tile_y * TILES_PER_ROW_TS
                   + self.selected_tile_x)
            img_off = eff // 256
            tile_id = eff % 256
            write_tile_info(bmd, block_idx, tx, ty, tile_id, img_off, 0)
        self._refresh_block_editor()
        self._patch_block_on_canvas(bx, by)

    # ------------------------------------------------------------------
    # Object editor rendering
    # ------------------------------------------------------------------

    def _refresh_obj_map(self):
        """Render the background map + all objects onto the object canvas."""
        wm   = self._current_world_map()
        z    = self.zone
        bmd  = self.bmd_data.get(z, bytearray(84 * BYTES_PER_BLOCK_BMD))
        ts   = self.tilesets.get(z)
        base = render_map(wm, bmd, ts,
                          show_block_grid=False,
                          show_tile_grid=False)
        scaled_base = _apply_zoom(base, self.zoom)
        # Convert to RGB for display but keep RGBA for compositing
        self._obj_map_tk = ImageTk.PhotoImage(scaled_base.convert("RGB"))
        c = self.obj_map_canvas
        c.delete("all")
        c.create_image(0, 0, anchor=tk.NW, image=self._obj_map_tk)
        c.config(scrollregion=(0, 0, scaled_base.width, scaled_base.height))
        # Draw objects on top
        self._obj_sprite_tks = []
        for idx, obj in enumerate(self.objects):
            self._draw_obj_on_canvas(idx, obj)

    def _draw_obj_on_canvas(self, obj_idx: int, obj: dict):
        type_idx = obj['type']
        info     = OBJECT_TYPES.get(type_idx,
                                    (f"Type {type_idx}", "", 24, 24, "misc"))
        name, fname, hw, hh, cat = info
        colour = CATEGORY_COLOURS.get(cat, (180, 180, 180))
        cx = int(obj['x'] * self.zoom)
        cy = int(obj['y'] * self.zoom)
        w  = int(hw * self.zoom)
        h  = int(hh * self.zoom)
        is_sel = (obj_idx == self.selected_obj_idx)
        sprite = self.sprites.get(fname)
        if sprite:
            sw = max(1, int(sprite.width  * self.zoom))
            sh = max(1, int(sprite.height * self.zoom))
            scaled_sp = sprite.resize((sw, sh), Image.NEAREST)
            tk_sp = ImageTk.PhotoImage(scaled_sp)
            self._obj_sprite_tks.append(tk_sp)
            tag = f"obj_{obj_idx}"
            self.obj_map_canvas.create_image(
                cx, cy, anchor=tk.CENTER, image=tk_sp, tags=(tag,))
        else:
            # Draw a coloured rectangle as fallback
            r, g, b = colour
            fill_hex = f"#{r:02x}{g:02x}{b:02x}"
            tag = f"obj_{obj_idx}"
            self.obj_map_canvas.create_rectangle(
                cx - w // 2, cy - h // 2, cx + w // 2, cy + h // 2,
                fill=fill_hex, outline="black", tags=(tag,))
        # Name label
        self.obj_map_canvas.create_text(
            cx, cy - int(hh * self.zoom // 2) - 4,
            text=name, fill="white",
            font=("", max(6, int(8 * self.zoom))),
            anchor=tk.S)
        if is_sel:
            self.obj_map_canvas.create_rectangle(
                cx - w // 2 - 2, cy - h // 2 - 2,
                cx + w // 2 + 2, cy + h // 2 + 2,
                outline="yellow", width=2)

    # ------------------------------------------------------------------
    # Object editor events
    # ------------------------------------------------------------------

    def _populate_obj_listbox(self):
        self.obj_listbox.delete(0, tk.END)
        cat_filter = self.obj_filter_cat.get()
        self._obj_listbox_ids = []
        for type_idx in sorted(OBJECT_TYPES.keys()):
            info = OBJECT_TYPES[type_idx]
            if cat_filter != "all" and info[4] != cat_filter:
                continue
            self.obj_listbox.insert(tk.END,
                                    f"{type_idx:3d}  {info[0]}")
            self._obj_listbox_ids.append(type_idx)

    def _on_cat_filter_change(self, *_):
        self._populate_obj_listbox()

    def _on_obj_type_select(self, event):
        sel = self.obj_listbox.curselection()
        if sel:
            self.obj_selected_type = self._obj_listbox_ids[sel[0]]

    def _on_obj_canvas_click(self, event):
        cx = self.obj_map_canvas.canvasx(event.x)
        cy = self.obj_map_canvas.canvasy(event.y)
        wx = int(cx / self.zoom)
        wy = int(cy / self.zoom)
        # Try to select an existing object first
        hit = self._hit_test_obj(wx, wy)
        if hit is not None:
            self.selected_obj_idx = hit
            self._drag_start  = (cx, cy)
            self._drag_orig   = (self.objects[hit]['x'],
                                 self.objects[hit]['y'])
            self._update_prop_fields()
            self._refresh_obj_map()
            return
        # Place new object
        self._save_obj_undo()
        new_obj = {
            'x':     wx,
            'y':     wy,
            'param': 0,
            'type':  self.obj_selected_type,
            'count': 0,
        }
        self.objects.append(new_obj)
        self.selected_obj_idx = len(self.objects) - 1
        self._update_prop_fields()
        self._refresh_obj_map()
        self._refresh_inst_listbox()
        self.obj_map_status.set(
            f"Placed {OBJECT_TYPES.get(new_obj['type'], ('?',))[0]} "
            f"at ({wx},{wy})")

    def _on_obj_canvas_drag(self, event):
        if self.selected_obj_idx is None or self._drag_start is None:
            return
        cx = self.obj_map_canvas.canvasx(event.x)
        cy = self.obj_map_canvas.canvasy(event.y)
        dx = int((cx - self._drag_start[0]) / self.zoom)
        dy = int((cy - self._drag_start[1]) / self.zoom)
        ox, oy = self._drag_orig
        self.objects[self.selected_obj_idx]['x'] = max(0, ox + dx)
        self.objects[self.selected_obj_idx]['y'] = max(0, oy + dy)
        self._refresh_obj_map()
        self._update_prop_fields()

    def _on_obj_canvas_release(self, event):
        if self._drag_start is not None and self.selected_obj_idx is not None:
            # Record undo only if position actually changed
            orig = self._drag_orig
            cur  = (self.objects[self.selected_obj_idx]['x'],
                    self.objects[self.selected_obj_idx]['y'])
            if orig != cur:
                self._save_obj_undo()
        self._drag_start = None
        self._drag_orig  = None
        self._refresh_inst_listbox()

    def _on_obj_canvas_right(self, event):
        """Right-click: delete object under cursor."""
        cx = self.obj_map_canvas.canvasx(event.x)
        cy = self.obj_map_canvas.canvasy(event.y)
        wx = int(cx / self.zoom)
        wy = int(cy / self.zoom)
        hit = self._hit_test_obj(wx, wy)
        if hit is not None:
            self._save_obj_undo()
            del self.objects[hit]
            if self.selected_obj_idx == hit:
                self.selected_obj_idx = None
            elif (self.selected_obj_idx is not None
                  and self.selected_obj_idx > hit):
                self.selected_obj_idx -= 1
            self._refresh_obj_map()
            self._refresh_inst_listbox()

    def _hit_test_obj(self, wx: int, wy: int):
        """Return index of object hit at world coords (wx, wy) or None."""
        for idx in reversed(range(len(self.objects))):
            obj  = self.objects[idx]
            info = OBJECT_TYPES.get(obj['type'],
                                    ("", "", 24, 24, "misc"))
            hw   = info[2] // 2
            hh   = info[3] // 2
            if (obj['x'] - hw <= wx <= obj['x'] + hw and
                    obj['y'] - hh <= wy <= obj['y'] + hh):
                return idx
        return None

    def _update_prop_fields(self):
        if self.selected_obj_idx is None:
            return
        obj = self.objects[self.selected_obj_idx]
        self._prop_vars["prop_x"].set(str(obj['x']))
        self._prop_vars["prop_y"].set(str(obj['y']))
        self._prop_vars["prop_param"].set(str(obj['param']))
        self._prop_vars["prop_type"].set(str(obj['type']))
        self._prop_vars["prop_count"].set(str(obj['count']))

    def _apply_obj_props(self):
        if self.selected_obj_idx is None:
            return
        try:
            obj = self.objects[self.selected_obj_idx]
            self._save_obj_undo()
            obj['x']     = int(self._prop_vars["prop_x"].get())
            obj['y']     = int(self._prop_vars["prop_y"].get())
            obj['param'] = int(self._prop_vars["prop_param"].get())
            obj['type']  = int(self._prop_vars["prop_type"].get())
            obj['count'] = int(self._prop_vars["prop_count"].get())
            self._refresh_obj_map()
            self._refresh_inst_listbox()
        except ValueError as e:
            messagebox.showerror("Invalid input", str(e))

    def _delete_selected_obj(self):
        if self.selected_obj_idx is None:
            return
        self._save_obj_undo()
        del self.objects[self.selected_obj_idx]
        self.selected_obj_idx = None
        self._refresh_obj_map()
        self._refresh_inst_listbox()

    def _refresh_inst_listbox(self):
        self.inst_listbox.delete(0, tk.END)
        for idx, obj in enumerate(self.objects):
            info = OBJECT_TYPES.get(obj['type'],
                                    (f"Type {obj['type']}",))
            marker = "►" if idx == self.selected_obj_idx else " "
            self.inst_listbox.insert(
                tk.END,
                f"{marker}{idx:3d} {info[0][:12]:12s} "
                f"({obj['x']},{obj['y']})")

    def _on_inst_listbox_select(self, event):
        sel = self.inst_listbox.curselection()
        if sel:
            self.selected_obj_idx = sel[0]
            self._update_prop_fields()
            self._refresh_obj_map()

    # ------------------------------------------------------------------
    # Undo / Redo
    # ------------------------------------------------------------------

    def _save_map_undo(self):
        wm  = self._current_world_map()
        z   = self.zone
        bmd = self.bmd_data.get(z, bytearray())
        state = {
            'grid': [list(r) for r in wm],
            'bmd':  bytes(bmd),
        }
        self.map_undo.append(state)
        if len(self.map_undo) > MAX_UNDO:
            self.map_undo.pop(0)
        self.map_redo.clear()

    def _restore_map_state(self, state: dict):
        wm  = self._current_world_map()
        z   = self.zone
        src = state['grid']
        for r in range(min(len(wm), len(src))):
            for c in range(min(len(wm[r]), len(src[r]))):
                wm[r][c] = src[r][c]
        self.bmd_data[z] = bytearray(state['bmd'])
        self._map_img = None
        self._block_tk_cache.clear()
        self._refresh_map()
        self._refresh_block_editor()

    def _save_obj_undo(self):
        self.obj_undo.append(copy.deepcopy(self.objects))
        if len(self.obj_undo) > MAX_UNDO:
            self.obj_undo.pop(0)
        self.obj_redo.clear()

    def _on_undo(self, event=None):
        tab = self.notebook.index("current")
        if tab == 0:  # map editor
            if not self.map_undo:
                return
            self.map_redo.append({
                'grid': [list(r) for r in self._current_world_map()],
                'bmd':  bytes(self.bmd_data.get(self.zone, bytearray())),
            })
            self._restore_map_state(self.map_undo.pop())
        else:          # object editor
            if not self.obj_undo:
                return
            self.obj_redo.append(copy.deepcopy(self.objects))
            self.objects = self.obj_undo.pop()
            self._refresh_obj_map()
            self._refresh_inst_listbox()

    def _on_redo(self, event=None):
        tab = self.notebook.index("current")
        if tab == 0:
            if not self.map_redo:
                return
            self.map_undo.append({
                'grid': [list(r) for r in self._current_world_map()],
                'bmd':  bytes(self.bmd_data.get(self.zone, bytearray())),
            })
            self._restore_map_state(self.map_redo.pop())
        else:
            if not self.obj_redo:
                return
            self.obj_undo.append(copy.deepcopy(self.objects))
            self.objects = self.obj_redo.pop()
            self._refresh_obj_map()
            self._refresh_inst_listbox()

    # ------------------------------------------------------------------
    # Export
    # ------------------------------------------------------------------

    def _export_bmd(self):
        z   = self.zone
        bmd = self.bmd_data.get(z)
        if bmd is None:
            messagebox.showinfo("No data", "No BMD data loaded for this zone.")
            return
        path = filedialog.asksaveasfilename(
            title=f"Export zone{z}.bmd",
            initialfile=f"zone{z}.bmd",
            filetypes=[("BMD files", "*.bmd"), ("All files", "*.*")])
        if not path:
            return
        with open(path, "wb") as f:
            f.write(bmd)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")

    def _export_act(self):
        z = self.zone
        if z not in self.act_raw:
            messagebox.showinfo("No data", "No ACT data loaded for this zone.")
            return
        raw_bufs = self.act_raw[z]
        data     = export_act_file(raw_bufs, self.act, self.objects)
        default  = f"ZONE{z}ACT.act"
        path = filedialog.asksaveasfilename(
            title=f"Export {default}",
            initialfile=default,
            filetypes=[("ACT files", "*.act"), ("All files", "*.*")])
        if not path:
            return
        with open(path, "wb") as f:
            f.write(data)
        messagebox.showinfo("Exported", f"Saved to:\n{path}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

def main():
    res_dir = sys.argv[1] if len(sys.argv) > 1 else ""
    root = tk.Tk()
    app = SonicEditor(root, res_dir=res_dir)
    root.mainloop()


if __name__ == "__main__":
    main()
