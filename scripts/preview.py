#!/usr/bin/env python3
"""preview.png: every size at 1:1 on light and dark, zoomed pixel detail of the
small sizes, and the platform variants (macOS slots, web icons as masked)."""
import os
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = f"{ROOT}/png/robosapiens-monitor"
FONT = ImageFont.load_default(size=13)
LIGHT, DARK = (242, 242, 242), (30, 30, 30)

def label(img, xy, text, fill): ImageDraw.Draw(img).text(xy, text, font=FONT, fill=fill)

def row(sizes, bg, fg, width=1400, height=300, src=lambda n: f"{P}-{n}.png"):
    img = Image.new("RGB", (width, height), bg); x = 16
    for n in sizes:
        icon = Image.open(src(n)).convert("RGBA")
        img.paste(icon, (x, height - 30 - icon.height), icon)
        label(img, (x, height - 24), str(n), fg)
        x += icon.width + 18
    return img

def zoom_row(sizes, bg=LIGHT, target=176):
    img = Image.new("RGB", (1400, target + 40), bg); x = 16
    for n in sizes:
        z = max(1, target // n)
        icon = Image.open(f"{P}-{n}.png").convert("RGBA").resize((n * z, n * z), Image.NEAREST)
        img.paste(icon, (x, 26), icon)
        label(img, (x, 6), f"{n} px ({z}x)", (0, 0, 0))
        x += icon.width + 14
    return img

def platform_row():
    img = Image.new("RGB", (1400, 330), LIGHT)
    label(img, (16, 6), "macOS .icns slots (padded to Apple's grid), on light and dark", (0, 0, 0))
    x = 16
    for n in (16, 32, 64, 128, 256):
        icon = Image.open(f"{ROOT}/macos/png/robosapiens-monitor-{n}.png").convert("RGBA")
        for i, bg in enumerate((LIGHT, DARK)):
            tile = Image.new("RGB", (n, n), bg); tile.paste(icon, (0, 0), icon)
            img.paste(tile, (x, 30 + i * (n + 8) if n < 256 else 30))
            if n == 256: break
        x += n + 16
    label(img, (x, 6), "web: touch icon as iOS masks it, maskable as a circle", (0, 0, 0))
    for name, shape in (("apple-touch-icon.png", "rounded"), ("icon-maskable-192.png", "circle"), ("icon-192.png", None)):
        icon = Image.open(f"{ROOT}/web/{name}").convert("RGBA")
        if shape:
            m = Image.new("L", icon.size, 0); d = ImageDraw.Draw(m); s = icon.width
            if shape == "rounded": d.rounded_rectangle((0, 0, s - 1, s - 1), radius=int(s * .225), fill=255)
            else: d.ellipse((0, 0, s - 1, s - 1), fill=255)
            icon.putalpha(m)
        img.paste(icon, (x, 30), icon); label(img, (x, 30 + icon.height + 4), name, (0, 0, 0))
        x += icon.width + 16
    return img

sizes = [256, 128, 96, 64, 48, 40, 32, 24, 22, 20, 16]
parts = [row(sizes, LIGHT, (0, 0, 0)), row(sizes, DARK, (220, 220, 220)),
         zoom_row([64, 48, 40, 32, 24, 22, 20, 16]), platform_row()]
out = Image.new("RGB", (1400, sum(p.height for p in parts)), LIGHT); y = 0
for p in parts: out.paste(p, (0, y)); y += p.height
out.save(f"{ROOT}/preview.png")
