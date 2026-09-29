#!/usr/bin/env python3
"""Monochrome outline glyphs for VS Code (Codicon conventions).

Two optical sizes, each drawn on its own grid rather than scaled:
  16/  1 px strokes: commands, tree items, status bar, editor/title actions
  24/  1.5 px strokes: Activity Bar (view container) icons
Straight edges sit on the pixel grid (1 px strokes on half pixels; 1.5 px strokes
with their outer edge on a whole pixel). Everything paints with currentColor,
so VS Code (which uses these as masks) and themes recolour them.

Writes vscode/16, vscode/24 and vscode/font (icon font), tray/ (menu-bar and
system-tray PNGs) and preview-glyphs.png. Run by build.py.
"""
import os, subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GLYPHS, TRAY = f"{ROOT}/vscode", f"{ROOT}/tray"

def svg(n, sw, body, defs=""):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" width="{n}" height="{n}" '
            f'fill="none" stroke="currentColor" stroke-width="{sw}" stroke-linecap="round" stroke-linejoin="round">\n'
            + (f"<defs>{defs}</defs>\n" if defs else "") + body + "\n</svg>\n")

def dot(cx, cy, r): return f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="currentColor" stroke="none"/>'

def masked(mask_id, keep_out, body):
    """Wrap body in a mask that removes keep_out (black shapes) plus a margin."""
    defs = (f'<mask id="{mask_id}" maskUnits="userSpaceOnUse" x="0" y="0" width="100%" height="100%">'
            f'<rect width="100%" height="100%" fill="#fff" stroke="none"/>{keep_out}</mask>')
    return defs, f'<g mask="url(#{mask_id})">{body}</g>'

# --------------------------------------------------------------------- parts
# Every size gets hand-placed coordinates; nothing is derived by scaling.
def sq(x, y, w, h): return f'<rect x="{x}" y="{y}" width="{w}" height="{h}" fill="currentColor" stroke="none"/>'

def stair(*pts):
    """Pixels of a polyline through integer pixel coords (45-degree or straight runs)."""
    px = []
    for (x0, y0), (x1, y1) in zip(pts, pts[1:]):
        n = max(abs(x1 - x0), abs(y1 - y0))
        px += [(x0 + round((x1 - x0) * i / n), y0 + round((y1 - y0) * i / n)) for i in range(n + 1)]
    return sorted(set(px))

def pix(pixels, fill="currentColor", grow=0):
    return "".join(f'<rect x="{x-grow}" y="{y-grow}" width="{1+2*grow}" height="{1+2*grow}" fill="{fill}" stroke="none"/>'
                   for x, y in pixels)

# 16 px is an even grid, so a centred 1 px line would straddle two pixel columns and
# a 1 px diagonal drawn as a vector is always anti-aliased. So at 16 the antenna,
# eyes and every diagonal (pulse, check, cross, slash, signal arcs) are drawn as
# pixels; only the head outline and ears stay vector (they sit on half pixels).
# The antenna is a round 4x4 ball sitting on the head, as on the 16 px app icon.
def ball16(x, y):
    return [(x + 1, y), (x + 2, y)] + [(x + i, y + j) for j in (1, 2) for i in range(4)] + [(x + 1, y + 3), (x + 2, y + 3)]

G = {
    16: dict(
        sw=1,
        robot=(pix(ball16(6, 1)) + '<rect x="2.5" y="5.5" width="11" height="7" rx="2"/>'
               '<path d="M2.5 7.5h-1v3h1M13.5 7.5h1v3h-1"/>' + sq(5, 8, 2, 2) + sq(9, 8, 2, 2)),
        brand=(pix(ball16(6, 0)) + '<rect x="3.5" y="4.5" width="9" height="5" rx="1.5"/>'
               '<path d="M3.5 6h-1v2h1M12.5 6h1v2h-1"/>' + sq(5, 6, 2, 2) + sq(9, 6, 2, 2) +
               pix(stair((0, 13), (4, 13), (6, 11), (9, 14), (10, 13), (15, 13)))),
        live=(pix(ball16(6, 2) + [(4, 2), (3, 3), (3, 4), (4, 5), (11, 2), (12, 3), (12, 4), (11, 5)]) +
              '<rect x="2.5" y="6.5" width="11" height="7" rx="2"/>'
              '<path d="M2.5 8.5h-1v3h1M13.5 8.5h1v3h-1"/>' + sq(5, 9, 2, 2) + sq(9, 9, 2, 2)),
        fleet=(pix(ball16(9, 0)) + '<rect x="6.5" y="4.5" width="8" height="5" rx="1.5"/>',
               '<rect x="1.5" y="7.5" width="9" height="6" rx="1.5"/>' + sq(3, 10, 2, 2) + sq(7, 10, 2, 2),
               '<rect x="1.5" y="7.5" width="9" height="6" rx="1.5" fill="#000" stroke="#000" stroke-width="3"/>'),
        # badges at 16 are bare 1 px symbols; filled discs this small turn to mush
        badge="bare",
        check=stair((9, 12), (11, 14), (15, 10)), cross=stair((11, 11), (15, 15)) + stair((15, 11), (11, 15)),
        bang=sq(13, 9, 2, 4) + sq(13, 14, 2, 2), bang_cut='<rect x="12" y="8" width="4" height="8" fill="#000"/>',
        slash=stair((1, 1), (14, 14)), slash_cut=3,
    ),
    24: dict(
        sw=1.5,
        robot=(dot(12, 3.75, 1.75) + '<path d="M12 5.5V8.75"/>'
               '<rect x="3.75" y="8.75" width="16.5" height="12.5" rx="3"/>'
               '<path d="M3.75 12.75h-1a.75.75 0 0 0-.75.75v3a.75.75 0 0 0 .75.75h1'
               'M20.25 12.75h1a.75.75 0 0 1 .75.75v3a.75.75 0 0 1-.75.75h-1"/>'
               + dot(8, 15, 2) + dot(16, 15, 2)),
        brand=(dot(12, 2.25, 1.75) + '<path d="M12 3.5V5.75"/>'
               '<rect x="4.75" y="5.75" width="14.5" height="9.5" rx="2.5"/>'
               '<path d="M4.75 8.75h-1a.75.75 0 0 0-.75.75v2a.75.75 0 0 0 .75.75h1'
               'M19.25 8.75h1a.75.75 0 0 1 .75.75v2a.75.75 0 0 1-.75.75h-1"/>'
               + dot(8.5, 10.5, 1.5) + dot(15.5, 10.5, 1.5) +
               '<path d="M1 20.5H7.5L10 18L13 23L15.5 20.5H23"/>'),
        live=(dot(12, 5, 1.75) + '<path d="M12 6.5V9.75"/>'
              '<path d="M8.25 2a4 4 0 0 0 0 6M15.75 2a4 4 0 0 1 0 6"/>'
              '<rect x="3.75" y="9.75" width="16.5" height="11.5" rx="3"/>'
              '<path d="M3.75 13.5h-1a.75.75 0 0 0-.75.75v2.5a.75.75 0 0 0 .75.75h1'
              'M20.25 13.5h1a.75.75 0 0 1 .75.75v2.5a.75.75 0 0 1-.75.75h-1"/>'
              + dot(8, 15.5, 2) + dot(16, 15.5, 2)),
        fleet=(dot(15, 2.25, 1.5) + '<path d="M15 3.75V5.75"/><rect x="8.75" y="5.75" width="12.5" height="8.5" rx="2.5"/>',
               '<rect x="2.75" y="10.75" width="13.5" height="10.5" rx="2.5"/>' + dot(6.5, 16, 1.75) + dot(12.5, 16, 1.75),
               '<rect x="2.75" y="10.75" width="13.5" height="10.5" rx="2.5" fill="#000" stroke="#000" stroke-width="4.5"/>'),
        badge="filled", badge_c=(18, 18), badge_r=5, cut_r=6.5,
        check="M15.6 18.2l1.7 1.7 3.2-3.5", cross="M16.1 16.1l3.8 3.8M19.9 16.1l-3.8 3.8",
        tri="M18 12.25L23.25 22.25H12.75Z", bang=("M18 15.5V18.5", (18, 20.4), .85), tri_cut=3.5,
        slash="M2.25 2.25L21.75 21.75", slash_cut=4.5,
    ),
}

def glyphs(n):
    p = G[n]; sw = p["sw"]; out = {}
    robot = p["robot"]
    out["robosapiens"] = svg(n, sw, p["brand"])
    out["robot"] = svg(n, sw, robot)
    out["robot-live"] = svg(n, sw, p["live"])
    back, front, front_cut = p["fleet"]
    d, b = masked("m", front_cut, back)
    out["robot-fleet"] = svg(n, sw, b + front, d)
    if isinstance(p["slash"], list):
        d, b = masked("m", pix(p["slash"], "#000", 1), robot)
        out["robot-offline"] = svg(n, sw, b + pix(p["slash"]), d)
    else:
        d, b = masked("m", f'<path d="{p["slash"]}" stroke="#000" stroke-width="{p["slash_cut"]}"/>', robot)
        out["robot-offline"] = svg(n, sw, b + f'<path d="{p["slash"]}"/>', d)
    # status badges, bottom-right; the head is cut away around them
    if p["badge"] == "bare":
        for name, sym in (("robot-ok", p["check"]), ("robot-error", p["cross"])):
            d, b = masked("m", pix(sym, "#000", 1), robot)
            out[name] = svg(n, sw, b + pix(sym), d)
        d, b = masked("m", p["bang_cut"], robot)
        out["robot-warning"] = svg(n, sw, b + p["bang"], d)
        return out
    bx, by = p["badge_c"]
    circle_cut = f'<circle cx="{bx}" cy="{by}" r="{p["cut_r"]}" fill="#000" stroke="none"/>'
    for name, sym in (("robot-ok", p["check"]), ("robot-error", p["cross"])):
        d1, b1 = masked("m", circle_cut, robot)
        d2, b2 = masked("k", f'<path d="{sym}" stroke="#000"/>',
                        f'<circle cx="{bx}" cy="{by}" r="{p["badge_r"]}" fill="currentColor" stroke="none"/>')
        out[name] = svg(n, sw, b1 + b2, d1 + d2)
    tri_cut = f'<path d="{p["tri"]}" fill="#000" stroke="#000" stroke-width="{p["tri_cut"]}"/>'
    line, (dx, dy), r = p["bang"]
    d1, b1 = masked("m", tri_cut, robot)
    d2, b2 = masked("k", f'<path d="{line}" stroke="#000"/><circle cx="{dx}" cy="{dy}" r="{r}" fill="#000" stroke="none"/>',
                    f'<path d="{p["tri"]}" fill="currentColor"/>')
    out["robot-warning"] = svg(n, sw, b1 + b2, d1 + d2)
    return out

ORDER = ["robosapiens", "robot", "robot-fleet", "robot-live", "robot-offline", "robot-ok", "robot-warning", "robot-error"]

# VS Code recolours only Activity Bar icons (it uses them as masks). Command,
# menu and tree-item icons are drawn as-is, so they need fixed-colour light/dark
# copies; these use the Codicon default foregrounds.
THEMED = {"light": "#424242", "dark": "#C5C5C5"}

# ------------------------------------------------------------------ tray icons
def render_png(svg_text, n, out):
    tmp = out + ".svg"; open(tmp, "w").write(svg_text)
    subprocess.run(["inkscape", tmp, "-w", str(n), "-h", str(n), "-o", out], check=True, capture_output=True)
    os.remove(tmp)

def tray():
    """macOS menu-bar template images (black + alpha; macOS recolours them) and
    plain white/black copies for Windows and Linux trays. The 2x images are exact
    pixel doublings of the 16/24 drawings, which is what a 2x screen should show."""
    import shutil
    shutil.rmtree(TRAY, ignore_errors=True)
    for d in ("macos", "white", "black"): os.makedirs(f"{TRAY}/{d}")
    for name in ORDER:
        for n in (16, 24):
            src = open(f"{GLYPHS}/{n}/{name}.svg").read()
            for col, d in (("#000000", "black"), ("#FFFFFF", "white")):
                out = f"{TRAY}/{d}/{name}-{n}.png"
                render_png(src.replace("currentColor", col), n, out)
                subprocess.run(["magick", out, "-filter", "point", "-resize", "200%", f"{TRAY}/{d}/{name}-{2*n}.png"], check=True)
        shutil.copy(f"{TRAY}/black/{name}-16.png", f"{TRAY}/macos/{name}Template.png")
        shutil.copy(f"{TRAY}/black/{name}-32.png", f"{TRAY}/macos/{name}Template@2x.png")

# ------------------------------------------------------------------- icon font
FONT = "robosapiens-glyphs"
FIRST_CP = 0xE001           # private-use code points, in ORDER
UPM, ASC, PX = 1024, 896, 64

def trace(mask):
    """Outline a pixel mask as TrueType contours: clockwise outers, counter-
    clockwise holes, collinear points removed. At every vertex the walk turns
    right first, so pixels touching only at a corner become separate contours."""
    n = len(mask)
    filled = lambda x, y: 0 <= x < n and 0 <= y < n and mask[y][x]
    P = lambda x, y: (x * PX, ASC - y * PX)
    edges = {}
    for y in range(n):
        for x in range(n):
            if not mask[y][x]: continue
            if not filled(x, y - 1): edges.setdefault(P(x, y), []).append(P(x + 1, y))
            if not filled(x + 1, y): edges.setdefault(P(x + 1, y), []).append(P(x + 1, y + 1))
            if not filled(x, y + 1): edges.setdefault(P(x + 1, y + 1), []).append(P(x, y + 1))
            if not filled(x - 1, y): edges.setdefault(P(x, y + 1), []).append(P(x, y))
    contours = []
    while edges:
        start = next(iter(edges)); a = start; b = edges[a].pop()
        if not edges[a]: del edges[a]
        pts = [a]
        while b != start:
            d = (b[0] - a[0], b[1] - a[1])
            cands = edges[b]
            def turn(c):            # right turn (clockwise in y-up) first, then straight, then left
                e = (c[0] - b[0], c[1] - b[1]); cross = d[0] * e[1] - d[1] * e[0]
                return 0 if cross < 0 else (1 if cross == 0 else 2)
            c = min(cands, key=turn); cands.remove(c)
            if not cands: del edges[b]
            pts.append(b); a, b = b, c
        simple = [p for i, p in enumerate(pts)
                  if (pts[i - 1][0] - p[0]) * (pts[(i + 1) % len(pts)][1] - p[1])
                  != (pts[i - 1][1] - p[1]) * (pts[(i + 1) % len(pts)][0] - p[0])]
        contours.append(simple)
    return contours

def font():
    """Icon font for VS Code's `icons` contribution point, so glyphs can be used
    as $(robosapiens-robot-ok) in labels and the status bar and follow theme
    colours. Built from the pixel-exact 16 px drawings: 1 px = 64 units and the
    baseline sits 14 px down the em, so at 16 px it renders pixel for pixel."""
    from PIL import Image
    from fontTools.fontBuilder import FontBuilder
    from fontTools.pens.ttGlyphPen import TTGlyphPen
    from fontTools.ttLib import TTFont
    names = [n.replace("-", "_") for n in ORDER]
    glyphs, metrics = {}, {}
    pen = TTGlyphPen(None); glyphs[".notdef"] = pen.glyph(); metrics[".notdef"] = (UPM, 0)
    for name, gname in zip(ORDER, names):
        a = Image.open(f"{TRAY}/black/{name}-16.png").getchannel("A")
        mask = [[a.getpixel((x, y)) >= 128 for x in range(16)] for y in range(16)]
        pen = TTGlyphPen(None)
        cs = trace(mask)
        for c in cs:
            pen.moveTo(c[0])
            for p in c[1:]: pen.lineTo(p)
            pen.closePath()
        glyphs[gname] = pen.glyph()
        metrics[gname] = (UPM, min(p[0] for c in cs for p in c))
    fb = FontBuilder(UPM, isTTF=True)
    fb.setupGlyphOrder([".notdef"] + names)
    fb.setupCharacterMap({FIRST_CP + i: g for i, g in enumerate(names)})
    fb.setupGlyf(glyphs)
    fb.setupHorizontalMetrics(metrics)
    fb.setupHorizontalHeader(ascent=ASC, descent=ASC - UPM)
    fb.setupNameTable({"familyName": "RoboSAPIENS Glyphs", "styleName": "Regular"})
    fb.setupOS2(sTypoAscender=ASC, sTypoDescender=ASC - UPM, sTypoLineGap=0,
                usWinAscent=ASC, usWinDescent=UPM - ASC)
    fb.setupPost()
    os.makedirs(f"{GLYPHS}/font", exist_ok=True)
    ttf = f"{GLYPHS}/font/{FONT}.ttf"
    fb.save(ttf)
    for flavor in ("woff", "woff2"):
        t = TTFont(ttf); t.flavor = flavor; t.save(f"{GLYPHS}/font/{FONT}.{flavor}")

def main():
    import shutil
    shutil.rmtree(GLYPHS, ignore_errors=True)
    for n in (16, 24):
        for sub in ("", *THEMED):
            os.makedirs(f"{GLYPHS}/{n}/{sub}".rstrip("/"), exist_ok=True)
        for name, s in glyphs(n).items():
            open(f"{GLYPHS}/{n}/{name}.svg", "w").write(s)
            for theme, col in THEMED.items():
                open(f"{GLYPHS}/{n}/{theme}/{name}.svg", "w").write(s.replace("currentColor", col))
    tray()
    font()
    preview()

def preview():
    """preview.png: both sizes at 1x and zoomed, on VS Code Dark+ and Light+ colours."""
    tmp = f"{ROOT}/.preview"; os.makedirs(tmp, exist_ok=True)
    themes = [("dark", "#181818", "#cccccc"), ("light", "#f8f8f8", "#3b3b3b")]
    rows = []
    for theme, bg, fg in themes:
        for n in (24, 16):
            tiles = []
            for name in ORDER:
                src = open(f"{GLYPHS}/{n}/{name}.svg").read().replace("currentColor", fg)
                open(f"{tmp}/g.svg", "w").write(src)
                subprocess.run(["inkscape", f"{tmp}/g.svg", "-o", f"{tmp}/g.png"], check=True, capture_output=True)
                z = 192 // n
                t = f"{tmp}/{theme}-{n}-{name}.png"
                subprocess.run(["magick", "-size", f"{n}x{n}", f"xc:{bg}", f"{tmp}/g.png", "-composite", "(", "+clone", "-filter",
                                "point", "-resize", f"{z*100}%", ")", "-swap", "0,1", "-background", bg, "-gravity", "center",
                                "(", "-clone", "0", "-extent", "200x200", ")", "(", "-size", "200x18", f"xc:{bg}", "-fill", fg,
                                "-pointsize", "12", "-gravity", "center", "-annotate", "+0+0", name, ")",
                                "(", "-clone", "1", "-extent", "200x36", ")",
                                "-delete", "0,1", "-append", t], check=True)
                tiles.append(t)
            r = f"{tmp}/{theme}-{n}.png"
            subprocess.run(["magick", *tiles, "+append", "-gravity", "northwest", "-fill", fg, "-pointsize", "14",
                            "-annotate", "+8+4", f"{n}px — {theme}", "-bordercolor", bg, "-border", "0x6", r], check=True)
            rows.append(r)
    subprocess.run(["magick", *rows, "-append", f"{ROOT}/preview-glyphs.png"], check=True)
    subprocess.run(["rm", "-rf", tmp])

if __name__ == "__main__":
    main()
