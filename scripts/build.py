#!/usr/bin/env python3
"""RoboSAPIENS Monitor icon set (concept C: brand-red tile, mascot head, pulse line).

Each size has its own drawing rather than a rescaled master:
  large  (256-1024)  512-unit master, full detail
  medium (96, 128)   thicker outline, bigger pupils
  small  (48, 64)    drawn on the native pixel grid, ear tabs
  tiny   (12-40)     pixel-drawn, schematic head with dot eyes (12 is only used
                     inside the padded macOS 16 px slot)
From 32 px up every eye has a highlight at its upper left.

The pulse has one shape at every size (flat, up A, down 2A, up A, flat; all
diagonals at 45 degrees). In every PNG it is drawn into whole pixels on that
PNG's own grid, so it is never anti-aliased. Only the scalable master SVG keeps
a vector pulse.

Writes, relative to the release folder: png/, svg/, windows/, macos/, linux/, web/,
and (via build_glyphs.py) vscode/ and tray/; then runs check.py and preview.py.
Run: python3 scripts/build.py  (needs Inkscape, ImageMagick, Pillow and fontTools)
"""
import math, os, struct, subprocess, shutil, sys

SCRIPTS = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(SCRIPTS)                  # the release folder; outputs are written here
NAME = "robosapiens-monitor"
CY, OR, RD, PL, K, W = "#5EC8E0", "#F4AD3B", "#ED341A", "#DAF5FB", "#111111", "#FFFFFF"
SIZES = [16, 20, 22, 24, 32, 40, 48, 64, 96, 128, 256, 512, 1024]

def svg(n, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {n} {n}" '
            f'width="{n}" height="{n}">\n<title>RoboSAPIENS Monitor</title>\n{body}\n</svg>\n')

def f(v): return f"{round(v, 4):g}"

# ----------------------------------------------------------------------- pulse
SQRT2 = 2 ** .5

# Per native size: (line width w, baseline centre y0, amplitude A, rise start x1).
# The dip is centred at ~46% of the width and A is 6-12% of the tile at every size.
# Up to 3 px wide the pulse is drawn as fixed-height column runs (exact at that
# width); from 5 px it is an exact round-join stroke (see stroke_pixels).
PULSE = {12: (1, 9.5, 1, 3), 16: (1, 13.5, 2, 3), 20: (2, 17, 2, 5), 22: (2, 19, 2, 6),
         24: (2, 20, 3, 5), 32: (2, 27, 3, 9), 40: (3, 33.5, 3, 12), 48: (3, 41.5, 3, 16),
         64: (3, 54.5, 5, 20), 96: (5, 81.5, 7, 30), 128: (6, 108, 11, 37),
         256: (10, 204, 17, 84), 512: (20, 408, 34, 168), 1024: (40, 816, 68, 336)}

def pulse_points(n, x1_off=0.0, reach=2):
    w, y0, A, x1 = PULSE[n]
    x = x1 + x1_off
    return [(-reach, y0), (x, y0), (x + A, y0 - A), (x + 3 * A, y0 + A), (x + 4 * A, y0), (n + reach, y0)]

def pulse_pixels(n, inside):
    """Rasterise the size-n pulse on its own grid. Up to 3 px wide, each column
    gets a fixed-height run: w rows on the flats and round(w*sqrt2) rows on the
    45-degree parts, so diagonals weigh the same as flats and every stair step
    is one pixel. Vertices shift by half a pixel when needed so each run starts
    on a whole row (no rounding ties)."""
    w, y0 = PULSE[n][0], PULSE[n][1]
    if w >= 5:
        return stroke_pixels(n, pulse_points(n), w / 2, inside)
    hd = round(w * SQRT2)
    want = .5 if hd % 2 else 0.0
    off = 0.0 if abs((y0 + .5) % 1 - want) < 1e-9 else .5
    pts = pulse_points(n, off)
    out = set()
    for c in range(n):
        xc = c + .5
        for (xa, ya), (xb, yb) in zip(pts, pts[1:]):
            if xa <= xc <= xb:
                y = ya + (yb - ya) * (xc - xa) / (xb - xa)
                h = w if ya == yb else hd
                r0 = math.ceil(y - h / 2 - .5); r1 = math.ceil(y + h / 2 - .5)   # rows whose centre is in [y-h/2, y+h/2)
                out.update((c, r) for r in range(r0, r1) if inside(c, r))
    return out

def stroke_pixels(n, pts, half, inside):
    """Pixels whose centre lies within `half` of the polyline: an exact stroke with
    round joins. Used from 5 px wide, where fixed-height column runs would poke
    below the flat at each flat/diagonal join, and for any render that is not on
    a size's native grid. Along a 45-degree segment the line moves exactly one
    row per column, so every column gets the same run length."""
    ys = [y for _, y in pts]
    rlo, rhi = max(0, int(min(ys) - half) - 1), min(n, int(max(ys) + half) + 2)
    segs = list(zip(pts, pts[1:]))
    out = set()
    for r in range(rlo, rhi):
        py = r + .5
        for c in range(n):
            px = c + .5
            for (xa, ya), (xb, yb) in segs:
                dx, dy = xb - xa, yb - ya
                t = max(0, min(1, ((px - xa) * dx + (py - ya) * dy) / (dx * dx + dy * dy)))
                if (px - xa - t * dx) ** 2 + (py - ya - t * dy) ** 2 <= half * half:
                    if inside(c, r): out.add((c, r))
                    break
    return out

def in_rrect(t0, t1, rx):
    def inside(c, r):
        x, y = c + .5, r + .5
        if not (t0 <= x <= t1 and t0 <= y <= t1): return False
        cx = min(max(x, t0 + rx), t1 - rx); cy = min(max(y, t0 + rx), t1 - rx)
        return (x - cx) ** 2 + (y - cy) ** 2 <= rx ** 2
    return inside

def pixel_rects(pixels, fill):
    rows = {}
    for c, r in pixels: rows.setdefault(r, []).append(c)
    out = []
    for r, cs in sorted(rows.items()):
        cs.sort(); start = prev = cs[0]
        for c in cs[1:] + [None]:
            if c is not None and c == prev + 1: prev = c; continue
            out.append(f'<rect x="{start}" y="{r}" width="{prev-start+1}" height="1" fill="{fill}"/>')
            if c is not None: start = prev = c
    return "\n".join(out)

# ---------------------------------------------------------------- vector tiers
def vector(p, N=None, place=None, bleed=False, vector_pulse=False):
    """Body of a vector-tier icon rendered at N px.
    place=(k, o) maps design units to output px (X = o + x*k); default is a plain
    scale to N. bleed=True fills the whole canvas with the tile (web touch and
    maskable icons). The pulse is always rasterised on the N px output grid,
    except for the scalable source (vector_pulse=True)."""
    n, sw = p["n"], p["sw"]
    N = N or n
    k, o = place or (N / n, 0)
    t0, t1 = p["inset"], n - p["inset"]
    cx = n / 2
    s = []
    tile = f'<rect x="{t0}" y="{t0}" width="{t1-t0}" height="{t1-t0}" rx="{p["rx"]}" fill="{RD}"/>'
    # pulse, clipped to the tile so it runs off both edges
    if vector_pulse:
        d = " ".join(f"{'M' if i == 0 else 'L'}{f(x)},{f(y)}" for i, (x, y) in enumerate(pulse_points(n)))
        tile += (f'<clipPath id="tile"><rect x="{t0}" y="{t0}" width="{t1-t0}" height="{t1-t0}" rx="{p["rx"]}"/></clipPath>'
                 f'<path clip-path="url(#tile)" d="{d}" fill="none" stroke="{W}" stroke-width="{PULSE[n][0]}" '
                 f'stroke-linejoin="round" stroke-linecap="butt"/>')
        pulse_out = ""
    else:
        inside = in_rrect(0, N, 0) if bleed else in_rrect(o + t0 * k, o + t1 * k, p["rx"] * k)
        if place is None and N in PULSE:
            px = pulse_pixels(N, inside)
        else:
            pts = [(o + x * k, o + y * k) for x, y in pulse_points(n, reach=n)]
            px = stroke_pixels(N, pts, PULSE[n][0] * k / 2, inside)
        pulse_out = f'<g shape-rendering="crispEdges">{pixel_rects(px, W)}</g>'
    hx0, hy0, hw, hh = cx - p["hw"] / 2, p["hy"], p["hw"], p["hh"]
    ecy = hy0 + hh / 2 + p.get("eye_dy", 0)
    # antenna: orange ball + stalk, cyan trapezoid base
    ball_cy, ball_r = p["ball_cy"], p["ball_r"]
    sw2 = p["stem_w"] / 2
    if p.get("stem_black"):     # small sizes: a plain black stalk reads better than an outlined one
        s.append(f'<rect x="{f(cx-sw2)}" y="{f(ball_cy)}" width="{f(2*sw2)}" height="{f(hy0-ball_cy)}" fill="{K}"/>')
    else:
        s.append(f'<rect x="{f(cx-sw2)}" y="{f(ball_cy)}" width="{f(2*sw2)}" height="{f(p["base_y"]-ball_cy+sw)}" '
                 f'fill="{OR}" stroke="{K}" stroke-width="{sw}"/>')
    bt, bb, by = p["base_top"] / 2, p["base_bot"] / 2, p["base_y"]
    if p.get("base", True):
        s.append(f'<path d="M{f(cx-bb)},{f(hy0)} L{f(cx-bt)},{f(by)} L{f(cx+bt)},{f(by)} L{f(cx+bb)},{f(hy0)} Z" '
                 f'fill="{CY}" stroke="{K}" stroke-width="{sw}" stroke-linejoin="round"/>')
    s.append(f'<circle cx="{f(cx)}" cy="{f(ball_cy)}" r="{f(ball_r)}" fill="{OR}" stroke="{K}" stroke-width="{sw}"/>')
    # ears sit behind the head
    if p.get("ear_tab"):        # 48/64: pale rounded tab, left side; mirrored for the right
        tab = f'<path d="{p["ear_tab"]}" fill="{PL}" stroke="{K}" stroke-width="{sw}"/>'
        s.append(tab + f'<g transform="translate({n} 0) scale(-1 1)">{tab}</g>')
    for dx in ((-1, 1) if p["ear_r"] else ()):
        s.append(f'<circle cx="{f(cx + dx*(hw/2 - p["ear_in"]))}" cy="{f(hy0 + hh/2)}" r="{f(p["ear_r"])}" '
                 f'fill="{PL}" stroke="{K}" stroke-width="{sw}"/>')
    s.append(f'<rect x="{f(hx0)}" y="{f(hy0)}" width="{f(hw)}" height="{f(hh)}" rx="{f(p["hr"])}" '
             f'fill="{CY}" stroke="{K}" stroke-width="{sw}"/>')
    for dx in (-1, 1):
        ex = cx + dx * p["eye_dx"]
        s.append(f'<circle cx="{f(ex)}" cy="{f(ecy)}" r="{f(p["eye_r"])}" fill="{W}" stroke="{K}" stroke-width="{sw}"/>')
        s.append(f'<circle cx="{f(ex)}" cy="{f(ecy)}" r="{f(p["pupil_r"])}" fill="{K}"/>')
        # highlight at the upper left of each pupil (not mirrored, like the mascot)
        if p.get("hl_r"):
            s.append(f'<circle cx="{f(ex - p["hl_off"])}" cy="{f(ecy - p["hl_off"])}" r="{f(p["hl_r"])}" fill="{W}"/>')
        if p.get("hl_px"):      # 48/64: a whole-pixel square keeps the highlight crisp
            x, y, a = p["hl_px"]
            x += (dx + 1) * p["eye_dx"]
            s.append(f'<rect x="{f(x)}" y="{y}" width="{a}" height="{a}" fill="{W}" shape-rendering="crispEdges"/>')
    # tile, then the pulse (already in output px), then the drawing
    rest = "\n".join(s)
    if (k, o) == (1, 0) and not bleed:
        return f"{tile}\n{pulse_out}\n{rest}"
    g = lambda x: f'<g transform="translate({f(o)} {f(o)}) scale({f(k)})">{x}</g>'
    back = f'<rect width="{N}" height="{N}" fill="{RD}"/>' if bleed else g(tile)
    return f"{back}\n{pulse_out}\n{g(rest)}"

# Hand-picked per-size parameters. Relative to the master, smaller sizes get a
# bigger head, heavier outline, bigger pupils and a shorter antenna.
TIERS = {
    "large": dict(n=512, inset=16, rx=108, sw=12, hw=264, hh=196, hy=146, hr=41,
                  ear_r=46, ear_in=8, eye_dx=64, eye_r=46, pupil_r=28, hl_r=9, hl_off=11,
                  ball_cy=59, ball_r=25, stem_w=20, base_y=104, base_top=40, base_bot=76),
    "128":   dict(n=128, inset=4, rx=27, sw=4, hw=74, hh=54, hy=35, hr=12,
                  ear_r=12, ear_in=2, eye_dx=18, eye_r=13, pupil_r=8.5, hl_r=3, hl_off=3.4,
                  ball_cy=14, ball_r=7, stem_w=5, base_y=25, base_top=11, base_bot=22),
    "96":    dict(n=96, inset=3, rx=20, sw=3, hw=57, hh=42, hy=26.5, hr=9,
                  ear_r=9, ear_in=1.5, eye_dx=14, eye_r=10.5, pupil_r=7, hl_r=2.4, hl_off=2.8,
                  ball_cy=10.5, ball_r=5.5, stem_w=4, base_y=19, base_top=9, base_bot=17),
    # 64 and 48: 4:3 head, pale ear tabs, black stalk, white eye ring >= 2 px.
    # Odd-diameter circles sit on pixel centres and even ones on pixel edges.
    "64":    dict(n=64, inset=2, rx=13, sw=2, hw=40, hh=30, hy=16, hr=7,
                  ear_r=0, ear_in=0, ear_tab="M12 26H9a3 3 0 0 0-3 3v5a3 3 0 0 0 3 3H12",
                  eye_dx=9.5, eye_r=7.5, pupil_r=4, eye_dy=0.5, hl_px=(20, 29, 2),
                  ball_cy=8, ball_r=4, stem_w=2, stem_black=True, base_y=13, base_top=6, base_bot=12),
    "48":    dict(n=48, inset=1, rx=10, sw=2, hw=32, hh=24, hy=11, hr=6,
                  ear_r=0, ear_in=0, ear_tab="M8 18H6a2 2 0 0 0-2 2v6a2 2 0 0 0 2 2H8",
                  eye_dx=7.5, eye_r=5.5, pupil_r=2.8, hl_px=(15, 21, 1),
                  ball_cy=5, ball_r=3, stem_w=2, stem_black=True, base=False, base_y=9, base_top=5, base_bot=9),
}

# ----------------------------------------------------------------- pixel tiers
PIX = {"K": K, "C": CY, "P": PL, "W": W, "O": OR}

class Grid:
    def __init__(self, n): self.n, self.g = n, [[None] * n for _ in range(n)]
    def put(self, x, y, c):
        if 0 <= x < self.n and 0 <= y < self.n: self.g[y][x] = c
    def rect(self, x0, y0, x1, y1, c):          # inclusive
        for y in range(y0, y1 + 1):
            for x in range(x0, x1 + 1): self.put(x, y, c)
    def sprite(self, x0, y0, rows):              # ' ' = leave as is
        for dy, row in enumerate(rows):
            for dx, ch in enumerate(row):
                if ch in PIX: self.put(x0 + dx, y0 + dy, ch)
    def mirror(self):                            # copy left half onto right
        for row in self.g:
            for x in range(self.n // 2): row[self.n - 1 - x] = row[x]
    def rects(self):                             # merge horizontal runs
        out = []
        for y, row in enumerate(self.g):
            x = 0
            while x < self.n:
                c = row[x]
                if c is None: x += 1; continue
                x1 = x
                while x1 + 1 < self.n and row[x1 + 1] == c: x1 += 1
                out.append(f'<rect x="{x}" y="{y}" width="{x1-x+1}" height="1" fill="{PIX[c]}"/>')
                x = x1 + 1
        return "\n".join(out)

def rounded_head(g, x0, y0, x1, y1, cut, t=1):
    """Black outline `t` px thick, cyan fill; `cut` px stair-step corners."""
    g.rect(x0, y0, x1, y1, "K")
    g.rect(x0 + t, y0 + t, x1 - t, y1 - t, "C")
    for (cx, sx) in ((x0, 1), (x1, -1)):
        for (cy, sy) in ((y0, 1), (y1, -1)):
            for i in range(cut + t):
                for j in range(cut + t - i):
                    g.put(cx + sx * i, cy + sy * j, None if i + j < cut else "K")

def pixel_icon(n, rx, g):
    for c, r in pulse_pixels(n, in_rrect(0, n, rx)): g.put(c, r, "W")
    return f'<rect width="{n}" height="{n}" rx="{rx}" fill="{RD}"/>\n<g shape-rendering="crispEdges">\n{g.rects()}\n</g>'

# 12-40: the schematic style of the `robosapiens` outline glyph: compact head,
# solid ear nubs, solid dot eyes, pulse beneath. Line weight is 2 px from 20 up.
BALL4 = [" OO ", "OOOO", "OOOO", " OO "]                        # plain orange ball, 16-20
BALL4K = [" KK ", "KOOK", "KOOK", " KK "]                       # outlined ball, 22-24
BALL6K = [" KKKK ", "KKOOKK", "KOOOOK", "KOOOOK", "KKOOKK", " KKKK "]   # outlined ball, 32-40

def px12():     # only used inside the padded macOS 16 px slot
    g = Grid(12)
    g.rect(5, 0, 6, 0, "O")
    rounded_head(g, 2, 1, 9, 6, 1)                             # 8 x 6
    g.put(1, 3, "K"); g.put(1, 4, "K")                         # ear nub
    g.rect(3, 3, 4, 4, "K")                                    # dot eye
    g.mirror()
    return pixel_icon(12, 2, g)

def px16():
    g = Grid(16)
    g.sprite(6, 0, BALL4)                                      # round ball sitting on the head
    rounded_head(g, 3, 4, 12, 9, 1)                            # 10 x 6
    g.rect(2, 6, 2, 7, "K")                                    # ear nub
    g.rect(5, 6, 6, 7, "K")                                    # dot eye
    g.mirror()
    return pixel_icon(16, 3, g)

def px20():
    g = Grid(20)
    g.sprite(8, 0, BALL4)
    rounded_head(g, 3, 4, 16, 12, 2, t=2)                      # 14 x 9
    g.rect(1, 7, 2, 9, "K")
    g.rect(6, 7, 8, 9, "K")
    g.mirror()
    return pixel_icon(20, 4, g)

def px22():
    g = Grid(22)
    g.sprite(9, 0, BALL4K)
    rounded_head(g, 3, 4, 18, 14, 2, t=2)                      # 16 x 11
    g.rect(1, 8, 2, 10, "K")
    g.rect(7, 8, 9, 10, "K")
    g.mirror()
    return pixel_icon(22, 4, g)

def px24():
    g = Grid(24)
    g.sprite(10, 0, BALL4K)                                    # outlined ball sitting on the head
    rounded_head(g, 4, 4, 19, 14, 2, t=2)                      # 16 x 11 (1 row higher than before: room for A=3)
    g.rect(2, 8, 3, 10, "K")
    g.rect(7, 8, 9, 10, "K")
    g.mirror()
    return pixel_icon(24, 5, g)

def px32():
    g = Grid(32)
    g.sprite(13, 0, BALL6K)
    g.rect(15, 6, 16, 6, "K")                                  # stalk
    rounded_head(g, 5, 7, 26, 21, 2, t=2)                      # 22 x 15
    g.rect(3, 12, 4, 16, "K")
    g.sprite(9, 12, [" KKK ", "KKKKK", "KKKKK", "KKKKK", " KKK "])  # 5x5 dot: odd size reads round
    g.mirror()
    g.put(10, 13, "W"); g.put(19, 13, "W")                    # highlight, upper-left of each eye
    return pixel_icon(32, 6, g)

def px40():
    g = Grid(40)
    g.sprite(17, 0, BALL6K)
    g.rect(19, 6, 20, 7, "K")
    rounded_head(g, 6, 8, 33, 26, 3, t=2)                      # 28 x 19
    g.rect(4, 14, 5, 20, "K")
    g.sprite(11, 14, ["  KKK  ", " KKKKK ", "KKKKKKK", "KKKKKKK", "KKKKKKK", " KKKKK ", "  KKK  "])
    g.mirror()
    g.put(13, 16, "W"); g.put(24, 16, "W")
    return pixel_icon(40, 8, g)

# ----------------------------------------------------------------------- build
def run(*a): subprocess.run(a, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)

MAC_R = 824 / 1024          # Apple's app-icon grid: 824 px tile on a 1024 canvas

def mac_shadow(N, x0, size, rx):
    """Soft shadow under the tile, as on Apple's template (256 px slots and up)."""
    sd, dy = N * 0.012, N * 0.012
    return (f'<filter id="sh" x="-20%" y="-20%" width="140%" height="140%"><feGaussianBlur stdDeviation="{f(sd)}"/></filter>'
            f'<rect x="{f(x0)}" y="{f(x0 + dy)}" width="{f(size)}" height="{f(size)}" rx="{f(rx)}" fill="#000" '
            f'opacity=".3" filter="url(#sh)"/>')

def main():
    # the outline glyphs, tray icons and icon font come first: check.py covers them too
    subprocess.run([sys.executable, f"{SCRIPTS}/build_glyphs.py"], check=True)
    svgd, pngd, macd, webd = f"{ROOT}/svg", f"{ROOT}/png", f"{ROOT}/macos/png", f"{ROOT}/web"
    for d in (svgd, pngd, f"{ROOT}/macos", webd, f"{ROOT}/linux", f"{ROOT}/windows"): shutil.rmtree(d, ignore_errors=True)
    for d in (svgd, f"{svgd}/macos", pngd, macd, webd, f"{ROOT}/windows"): os.makedirs(d)
    L = TIERS["large"]
    bodies = {16: px16(), 20: px20(), 22: px22(), 24: px24(), 32: px32(), 40: px40(),
              48: vector(TIERS["48"]), 64: vector(TIERS["64"]), 96: vector(TIERS["96"]), 128: vector(TIERS["128"]),
              256: vector(L, 256), 512: vector(L, 512), 1024: vector(L, 1024)}
    open(f"{svgd}/{NAME}-master.svg", "w").write(svg(512, vector(L, vector_pulse=True)))
    for n in SIZES:
        open(f"{svgd}/{NAME}-{n}.svg", "w").write(svg(n, bodies[n]))
        run("inkscape", f"{svgd}/{NAME}-{n}.svg", "-w", str(n), "-h", str(n), "-o", f"{pngd}/{NAME}-{n}.png")
    # Linux: standard hicolor sizes
    for n in (16, 22, 24, 32, 48, 64, 96, 128, 256, 512):
        hd = f"{ROOT}/linux/hicolor/{n}x{n}/apps"; os.makedirs(hd)
        shutil.copy(f"{pngd}/{NAME}-{n}.png", f"{hd}/{NAME}.png")
    os.makedirs(f"{ROOT}/linux/hicolor/scalable/apps")
    shutil.copy(f"{svgd}/{NAME}-master.svg", f"{ROOT}/linux/hicolor/scalable/apps/{NAME}.svg")
    # Windows .ico, including the 125%/250% sizes (20, 40); every entry is its own drawing
    from PIL import Image
    ico = [Image.open(f"{pngd}/{NAME}-{n}.png") for n in (256, 128, 64, 48, 40, 32, 24, 20, 16)]
    ico[0].save(f"{ROOT}/windows/{NAME}.ico", sizes=[i.size for i in ico], append_images=ico[1:])

    # macOS: padded to Apple's grid. Small slots place a native design at 75% on
    # whole pixels (12 in 16, 24 in 32, 48 in 64, 96 in 128); from 256 the master
    # is placed at 824/1024 with a shadow, and the pulse is rasterised in place.
    mac = {}
    # (48 and 96 drop their own tile margin here, so every small slot's tile is 75% of it)
    small = {16: (12, px12()), 32: (24, bodies[24]),
             64: (48, vector(dict(TIERS["48"], inset=0))), 128: (96, vector(dict(TIERS["96"], inset=0)))}
    for slot, (inner, body) in small.items():
        d = (slot - inner) // 2
        mac[slot] = svg(slot, f'<g transform="translate({d} {d})">{body}</g>')
    for slot in (256, 512, 1024):
        tile = MAC_R * slot; k = tile / (512 - 2 * L["inset"]); o = slot / 2 - 256 * k
        x0 = o + L["inset"] * k
        mac[slot] = svg(slot, mac_shadow(slot, x0, tile, L["rx"] * k) + vector(L, slot, place=(k, o)))
    for slot, s in mac.items():
        open(f"{svgd}/macos/{NAME}-{slot}.svg", "w").write(s)
        run("inkscape", f"{svgd}/macos/{NAME}-{slot}.svg", "-w", str(slot), "-h", str(slot), "-o", f"{macd}/{NAME}-{slot}.png")
    chunks = [("icp4", 16), ("icp5", 32), ("icp6", 64), ("ic07", 128), ("ic08", 256),
              ("ic09", 512), ("ic10", 1024), ("ic11", 32), ("ic12", 64), ("ic13", 256), ("ic14", 512)]
    icns = b""
    for ost, n in chunks:
        data = open(f"{macd}/{NAME}-{n}.png", "rb").read()
        icns += ost.encode() + struct.pack(">I", len(data) + 8) + data
    open(f"{ROOT}/macos/{NAME}.icns", "wb").write(b"icns" + struct.pack(">I", len(icns) + 8) + icns)

    # Web
    ico = [Image.open(f"{pngd}/{NAME}-{n}.png") for n in (48, 32, 16)]
    ico[0].save(f"{webd}/favicon.ico", sizes=[i.size for i in ico], append_images=ico[1:])
    web = {"apple-touch-icon.png": (180, dict(bleed=True, place=(180 / 512, 0))),     # iOS rounds the corners itself
           "icon-192.png": (192, {}),
           "icon-maskable-192.png": (192, dict(bleed=True, place=(0.8 * 192 / 512, 0.1 * 192))),
           "icon-maskable-512.png": (512, dict(bleed=True, place=(0.8 * 512 / 512, 0.1 * 512)))}
    for name, (n, kw) in web.items():
        open(f"{webd}/{name[:-4]}.svg", "w").write(svg(n, vector(L, n, **kw)))
        run("inkscape", f"{webd}/{name[:-4]}.svg", "-w", str(n), "-h", str(n), "-o", f"{webd}/{name}")
        os.remove(f"{webd}/{name[:-4]}.svg")
    shutil.copy(f"{pngd}/{NAME}-512.png", f"{webd}/icon-512.png")
    open(f"{webd}/site.webmanifest", "w").write("""{
  "name": "RoboSAPIENS Monitor",
  "short_name": "RoboSAPIENS",
  "icons": [
    { "src": "icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "icon-512.png", "sizes": "512x512", "type": "image/png" },
    { "src": "icon-maskable-192.png", "sizes": "192x192", "type": "image/png", "purpose": "maskable" },
    { "src": "icon-maskable-512.png", "sizes": "512x512", "type": "image/png", "purpose": "maskable" }
  ],
  "theme_color": "#ED341A",
  "background_color": "#ED341A",
  "display": "standalone"
}
""")
    # verify everything (a failure stops here), then redraw the previews
    subprocess.run([sys.executable, f"{SCRIPTS}/check.py"], check=True)
    subprocess.run([sys.executable, f"{SCRIPTS}/preview.py"], check=True)

if __name__ == "__main__":
    main()
