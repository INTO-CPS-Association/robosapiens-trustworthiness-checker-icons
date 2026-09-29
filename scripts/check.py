#!/usr/bin/env python3
"""Verifies the built icon set; exits with status 1 if anything is wrong.

Checks every PNG (app sizes, macOS slots, web icons) for:
  - no anti-aliased pulse pixels (no red/white blends below the head)
  - at least one clear row between the head and the pulse
  - head outline and pulse widths matching the table in README.md
and that the .ico/.icns entries are exactly the per-size PNGs, the macOS
padding and web safe zones are right, and the glyph SVGs and icon font load.
Run by build.py; can also be run on its own: python3 scripts/check.py
"""
import glob, os, struct, sys
import xml.dom.minidom
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
NAME = "robosapiens-monitor"
SIZES = [16, 20, 22, 24, 32, 40, 48, 64, 96, 128, 256, 512, 1024]
# expected widths in px: head outline (top edge) and pulse
OUTLINE = {16: 1, 20: 2, 22: 2, 24: 2, 32: 2, 40: 2, 48: 2, 64: 2, 96: 3, 128: 4, 256: 6, 512: 12, 1024: 24}
PULSE_W = {16: 1, 20: 2, 22: 2, 24: 2, 32: 2, 40: 3, 48: 3, 64: 3, 96: 5, 128: 6, 256: 10, 512: 20, 1024: 40}
EYE_COL = {16: 5, 20: 7, 22: 8, 24: 8, 32: 11, 40: 14, 48: 16, 64: 22, 96: 34, 128: 46, 256: 96, 512: 192, 1024: 384}

failures = []
def fail(msg): failures.append(msg)

def load(path): return Image.open(path).convert("RGBA")

def darkness(p):                     # 1 for outline black, 0 for any fill colour (all have a channel > 220)
    return 0 if p[3] < 128 else max(0.0, min(1.0, (230 - max(p[:3])) / (230 - 17)))

def is_white(p): return p[3] == 255 and min(p[:3]) > 245

def pulse_checks(label, im):
    n = im.width; px = im.load()
    head_bottom = max((y for y in range(n) for x in range(n) if px[x, y][3] == 255 and max(px[x, y][:3]) < 60), default=-1)
    blended = [(x, y) for y in range(head_bottom + 1, n) for x in range(n)
               if px[x, y][3] == 255 and not is_white(px[x, y]) and px[x, y][0] > 230 and px[x, y][1] > 60]
    if blended: fail(f"{label}: {len(blended)} anti-aliased pulse pixels, e.g. {blended[:3]}")
    top = min((y for y in range(head_bottom + 1, n) for x in range(n) if is_white(px[x, y])), default=None)
    if top is None: fail(f"{label}: no pulse found below the head")
    elif top - head_bottom < 2: fail(f"{label}: pulse touches the head (head ends row {head_bottom}, pulse starts row {top})")

def run_length(col, pred):
    run = 0.0
    for v in col:
        w = pred(v)
        if w > 0.05: run += w
        elif run: return round(run, 2)
    return round(run, 2)

def app_icons():
    for n in SIZES:
        path = f"{ROOT}/png/{NAME}-{n}.png"
        if not os.path.exists(path): fail(f"missing {path}"); continue
        im = load(path)
        if im.size != (n, n): fail(f"{n}: wrong size {im.size}"); continue
        pulse_checks(f"png {n}", im)
        px = im.load()
        ol = run_length([px[EYE_COL[n], y] for y in range(n)], darkness)
        if abs(ol - OUTLINE[n]) > 0.15: fail(f"{n}: head outline {ol} px, expected {OUTLINE[n]}")
        pw = run_length([px[int(n * .12), y] for y in range(n)], lambda p: 1 if is_white(p) else 0)
        if pw != PULSE_W[n]: fail(f"{n}: pulse {pw} px wide, expected {PULSE_W[n]}")

def ico():
    im = Image.open(f"{ROOT}/windows/{NAME}.ico")
    for s in sorted(im.info["sizes"]):
        im.size = s
        if im.convert("RGBA").tobytes() != load(f"{ROOT}/png/{NAME}-{s[0]}.png").tobytes():
            fail(f"ico: {s} entry differs from png/{NAME}-{s[0]}.png")
    want = {(n, n) for n in (16, 20, 24, 32, 40, 48, 64, 128, 256)}
    if set(im.info["sizes"]) != want: fail(f"ico: sizes {sorted(im.info['sizes'])}, expected {sorted(want)}")

def icns():
    data = open(f"{ROOT}/macos/{NAME}.icns", "rb").read()
    if data[:4] != b"icns" or struct.unpack(">I", data[4:8])[0] != len(data): fail("icns: bad header"); return
    slots = {"icp4": 16, "icp5": 32, "icp6": 64, "ic07": 128, "ic08": 256, "ic09": 512, "ic10": 1024,
             "ic11": 32, "ic12": 64, "ic13": 256, "ic14": 512}
    i, seen = 8, set()
    while i < len(data):
        t, ln = data[i:i + 4].decode(), struct.unpack(">I", data[i + 4:i + 8])[0]
        if data[i + 8:i + ln] != open(f"{ROOT}/macos/png/{NAME}-{slots[t]}.png", "rb").read():
            fail(f"icns: {t} is not macos/png/{NAME}-{slots[t]}.png")
        seen.add(t); i += ln
    if seen != set(slots): fail(f"icns: missing chunks {set(slots) - seen}")
    # padding: small slots hold a native design at 75%, large ones the 824/1024 tile
    inner = {16: 12, 32: 24, 64: 48, 128: 96, 256: 206, 512: 412, 1024: 824}
    for slot, size in inner.items():
        im = load(f"{ROOT}/macos/png/{NAME}-{slot}.png")
        bbox = im.getchannel("A").point(lambda a: 255 if a >= 250 else 0).getbbox()
        w = bbox[2] - bbox[0]
        if abs(w - size) > 1: fail(f"macOS {slot}: tile is {w} px wide, expected {size}")
        pulse_checks(f"macOS {slot}", im)

def web():
    for name, n in {"apple-touch-icon.png": 180, "icon-192.png": 192, "icon-512.png": 512,
                    "icon-maskable-192.png": 192, "icon-maskable-512.png": 512}.items():
        im = load(f"{ROOT}/web/{name}")
        if im.size != (n, n): fail(f"web {name}: size {im.size}"); continue
        pulse_checks(f"web {name}", im)
        if name.startswith(("apple", "icon-maskable")) and im.getchannel("A").getextrema()[0] < 255:
            fail(f"web {name}: must be fully opaque")
        if "maskable" in name:      # everything but the tile and the pulse flats inside the 40% safe circle
            px = im.load(); c = n / 2
            out = [(x, y) for y in range(n) for x in range(n)
                   if (x + .5 - c) ** 2 + (y + .5 - c) ** 2 > (0.4 * n) ** 2
                   and not is_white(px[x, y]) and max(abs(a - b) for a, b in zip(px[x, y][:3], (237, 52, 26))) > 12]
            if out: fail(f"web {name}: {len(out)} drawing pixels outside the maskable safe zone")

def glyphs():
    for path in glob.glob(f"{ROOT}/vscode/**/*.svg", recursive=True):
        try: xml.dom.minidom.parse(path)
        except Exception as e: fail(f"glyph {path}: {e}")
    order = ["robosapiens", "robot", "robot-fleet", "robot-live", "robot-offline", "robot-ok", "robot-warning", "robot-error"]
    for name in order:
        for d, sizes in (("macos", ("Template", "Template@2x")), ("white", ("-16", "-24", "-32", "-48")), ("black", ("-16", "-24", "-32", "-48"))):
            for sfx in sizes:
                if not os.path.exists(f"{ROOT}/tray/{d}/{name}{sfx}.png"): fail(f"tray: missing {d}/{name}{sfx}.png")
    ttf = f"{ROOT}/vscode/font/robosapiens-glyphs.ttf"
    if not os.path.exists(ttf): fail("glyph font missing"); return
    from fontTools.ttLib import TTFont
    from PIL import ImageDraw, ImageFont
    cmap = TTFont(f"{ROOT}/vscode/font/robosapiens-glyphs.woff").getBestCmap()
    if len(cmap) != 8: fail(f"glyph font: {len(cmap)} glyphs mapped, expected 8")
    # at 16 px the font must render exactly the 16 px drawings, with no anti-aliasing
    ft = ImageFont.truetype(ttf, 16)
    for i, name in enumerate(order):
        im = Image.new("L", (16, 16), 0)
        ImageDraw.Draw(im).text((0, 0), chr(0xE001 + i), font=ft, fill=255, anchor="la")
        want = Image.open(f"{ROOT}/tray/black/{name}-16.png").getchannel("A").point(lambda a: 255 if a >= 128 else 0)
        if im.tobytes() != want.tobytes(): fail(f"glyph font: {name} at 16 px differs from the 16 px drawing")

if __name__ == "__main__":
    for step in (app_icons, ico, icns, web, glyphs): step()
    if failures:
        print("check.py: FAILED"); print("\n".join("  - " + f for f in failures)); sys.exit(1)
    print("check.py: all checks passed")
