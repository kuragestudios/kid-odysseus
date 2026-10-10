#!/usr/bin/env python3
"""Export 4x palette-coloured sprites from the Unity project for the website.

    scripts/sprites.py [path/to/kid_odysseus] [--all-cells]

The game draws every sprite from a grey-index sheet: the Palette shader maps the red channel
to the four palette colours (< 51 -> colour 0, < 128 -> colour 1, < 204 -> colour 2, else
colour 3). This script does the same in Pillow, crops the frame and scales it with nearest
neighbour. Output: public/images/sprites/<name>.png (palette 0) and
public/images/sprites/palette-<n>.png (Odysseus in each palette, for the swatch row) and palettes.json.
Run with --all-cells to also dump every frame of every sheet (cell-<sheet>-<col>-<row>.png) to pick from.
"""
import re
import sys
from pathlib import Path

from PIL import Image

HERE = Path(__file__).resolve().parent
SITE = HERE.parent
PROJECT = Path(sys.argv[1]) if len(sys.argv) > 1 and not sys.argv[1].startswith("--") else Path.home() / "ghq/github.com/aureliendrouet/kid_odysseus"
IMAGES = PROJECT / "Assets/App/Images"
OUT = SITE / "public/images/sprites"
SCALE = 4

# sheet -> cell size (w, h). Frames sit on a regular grid in every sheet.
SHEETS = {
    "Characters/player.png": (32, 32),
    "Characters/ghost.png": (32, 32),
    "Characters/frog.png": (32, 44),
    "Characters/knight.png": (16, 32),
    "Characters/skull.png": (32, 32),
    "Characters/slime.png": (32, 16),
    "Characters/eye.png": (32, 32),
    "Characters/spectrum.png": (16, 32),
    "Props/items.png": (32, 16),
    "Props/block.png": (32, 32),
    "Props/trigger.png": (32, 16),          # lever, 3 positions
    "Props/moving walkway.png": (32, 4),    # conveyor belt, 4 frames
}

# name -> (sheet, column, row) of the frame shown on the site
PICKS = {
    "odysseus": ("Characters/player.png", 0, 0),  # body only: the head is composited from Hats/default.png, see kid()
    "ghost": ("Characters/ghost.png", 0, 2),
    "frog": ("Characters/frog.png", 0, 0),
    "knight": ("Characters/knight.png", 0, 0),
    "skull": ("Characters/skull.png", 0, 0),
    "slime": ("Characters/slime.png", 0, 0),
    "eye": ("Characters/eye.png", 0, 0),
    "spectrum": ("Characters/spectrum.png", 0, 0),
    "block": ("Props/block.png", 0, 0),
    "pearl": ("Props/items.png", 0, 2),
    "coin": ("Props/items.png", 0, 3),
    "heart": ("Props/items.png", 0, 5),
    "magnet": ("Props/items.png", 1, 2),
    "boots": ("Props/items.png", 0, 1),
    "feather": ("Props/items.png", 1, 6),
    "spikes": ("Props/items.png", 0, 6),
    "hammer": ("Props/items.png", 0, 4),
    "spring": ("Props/items.png", 3, 0),
    "platform": ("Props/items.png", 0, 0),
    "bridge": ("Props/items.png", 1, 0),
    "walkway": ("Props/moving walkway.png", 0, 0),
    "lever": ("Props/trigger.png", 0, 0),
}


def palettes():
    """Parse Palettes.cs so the site always matches the game."""
    src = (PROJECT / "Assets/App/Scripts/Contants/Palettes.cs").read_text()
    result = []
    for line in src.splitlines():
        if "new Palette (" not in line:
            continue
        colours = re.findall(r"new Color \(([^)]*)\)", line)
        result.append([tuple(round(float(v.rstrip("f")) * 255) for v in c.split(",")) for c in colours])
    assert len(result) == 16, len(result)
    return result


def colourise(frame, palette):
    out = Image.new("RGBA", frame.size, (0, 0, 0, 0))
    src = frame.load()
    dst = out.load()
    for y in range(frame.height):
        for x in range(frame.width):
            r, _, _, a = src[x, y]
            if a == 0:
                continue
            c = palette[0] if r < 51 else palette[1] if r < 128 else palette[2] if r < 204 else palette[3]
            dst[x, y] = (*c, a)
    return out


def cell(sheet, col, row):
    img = Image.open(IMAGES / sheet).convert("RGBA")
    w, h = SHEETS[sheet]
    box = (col * w, row * h, (col + 1) * w, (row + 1) * h)
    frame = img.crop(box)
    bbox = frame.getbbox()
    return frame.crop(bbox) if bbox else frame


def kid(col, row, hat="default"):
    """player.png holds the body, the hat sheets hold the head on the same grid: overlay them."""
    body = Image.open(IMAGES / "Characters/player.png").convert("RGBA")
    head = Image.open(IMAGES / f"Hats/{hat}.png").convert("RGBA")
    w, h = SHEETS["Characters/player.png"]
    box = (col * w, row * h, (col + 1) * w, (row + 1) * h)
    frame = Image.alpha_composite(body.crop(box), head.crop(box))
    return frame.crop(frame.getbbox())


def export(frame, palette, path):
    big = colourise(frame, palette).resize((frame.width * SCALE, frame.height * SCALE), Image.NEAREST)
    big.save(path, optimize=True)
    return big


def main():
    pal = palettes()
    OUT.mkdir(parents=True, exist_ok=True)

    for name, (sheet, col, row) in PICKS.items():
        frame = kid(col, row) if sheet == "Characters/player.png" else cell(sheet, col, row)
        export(frame, pal[0], OUT / f"{name}.png")

    # the 16 hats are full player sheets drawn with the hat on; export the standing frame of each
    for hat in sorted((IMAGES / "Hats").glob("*.png")):
        SHEETS[f"Hats/{hat.name}"] = (32, 32)
        export(cell(f"Hats/{hat.name}", 4, 0), pal[0], OUT / f"hat-{hat.stem}.png")

    # stage selector thumbnails: 36x36 maps of each maze, black = wall (colour 0), white = floor (colour 3).
    # Style 0 ("bone") is the default tile set in the game; each maze gets its own palette so the grid shows both.
    thumbs = sorted((PROJECT / "Assets/Tilemaps/screenshots").glob("*_bone.png"))
    for i, thumb in enumerate(thumbs):
        frame = Image.open(thumb).convert("RGBA")
        export(frame, pal[i % len(pal)], OUT / f"maze-{i:02d}.png")
        if i == 0:
            export(frame, pal[0], OUT / "maze.png")

    hero = cell("Hats/default.png", 4, 0)  # Odysseus face with his cap, one per palette
    for i, p in enumerate(pal):
        export(hero, p, OUT / f"palette-{i:02d}.png")

    # palette data for the site (CSS swatches)
    (OUT / "palettes.json").write_text(
        "[\n" + ",\n".join("  [" + ", ".join('"#%02x%02x%02x"' % c for c in p) + "]" for p in pal) + "\n]\n"
    )

    if "--all-cells" in sys.argv:
        # contact sheet of every cell of every sheet, to choose frames from
        for sheet, (w, h) in SHEETS.items():
            img = Image.open(IMAGES / sheet)
            for row in range(img.height // h):
                for col in range(img.width // w):
                    frame = cell(sheet, col, row)
                    if frame.getbbox():
                        export(frame, pal[0], OUT / f"cell-{Path(sheet).stem}-{col}-{row}.png")
    print(f"wrote {len(list(OUT.iterdir()))} files to {OUT}")


if __name__ == "__main__":
    main()
