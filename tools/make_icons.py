#!/usr/bin/env python3
"""Generates the PWA/favicon PNGs in pure Python (no Pillow on this machine).

Draws the Tampa Maids mark: a cream arched doorway on a deep-teal tile, a gold
sunrise at its threshold and a four-point sparkle.  python3 tools/make_icons.py
"""
import os, zlib, struct, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "icons")
SS = 2  # supersample factor

DEEP = (12, 74, 92)      # #0c4a5c
CREAM = (247, 243, 236)  # #f7f3ec
GOLD = (227, 155, 54)    # #e39b36


def write_png(path, w, h, rgba):
    """rgba: flat bytearray of w*h*4."""
    raw = bytearray()
    stride = w * 4
    for y in range(h):
        raw.append(0)                      # filter type 0
        raw += rgba[y * stride:(y + 1) * stride]
    comp = zlib.compress(bytes(raw), 9)

    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        return c + struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)

    png = (b"\x89PNG\r\n\x1a\n"
           + chunk(b"IHDR", struct.pack(">IIBBBBB", w, h, 8, 6, 0, 0, 0))
           + chunk(b"IDAT", comp)
           + chunk(b"IEND", b""))
    with open(path, "wb") as f:
        f.write(png)


class Canvas:
    def __init__(self, size):
        self.n = size
        self.px = [[0.0, 0.0, 0.0, 0.0] for _ in range(size * size)]

    def blend(self, x, y, color, a):
        if a <= 0 or x < 0 or y < 0 or x >= self.n or y >= self.n:
            return
        p = self.px[y * self.n + x]
        r, g, b = color
        na = a + p[3] * (1 - a)
        if na <= 0:
            return
        p[0] = (r * a + p[0] * p[3] * (1 - a)) / na
        p[1] = (g * a + p[1] * p[3] * (1 - a)) / na
        p[2] = (b * a + p[2] * p[3] * (1 - a)) / na
        p[3] = na

    def rounded_rect(self, x0, y0, x1, y1, r, color, alpha=1.0):
        for y in range(int(y0), int(math.ceil(y1))):
            for x in range(int(x0), int(math.ceil(x1))):
                cx = min(max(x + .5, x0 + r), x1 - r)
                cy = min(max(y + .5, y0 + r), y1 - r)
                d = math.hypot(x + .5 - cx, y + .5 - cy)
                if d <= r:
                    self.blend(x, y, color, alpha)

    def stroke_path(self, pts, width, color, alpha=1.0):
        hw = width / 2.0
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        x0 = int(max(0, min(xs) - hw - 1)); x1 = int(min(self.n, max(xs) + hw + 2))
        y0 = int(max(0, min(ys) - hw - 1)); y1 = int(min(self.n, max(ys) + hw + 2))
        segs = list(zip(pts, pts[1:]))
        for y in range(y0, y1):
            py = y + .5
            for x in range(x0, x1):
                px = x + .5
                best = 1e9
                for (ax, ay), (bx, by) in segs:
                    dx, dy = bx - ax, by - ay
                    L2 = dx * dx + dy * dy
                    t = 0.0 if L2 == 0 else max(0.0, min(1.0, ((px - ax) * dx + (py - ay) * dy) / L2))
                    d = math.hypot(px - (ax + t * dx), py - (ay + t * dy))
                    if d < best:
                        best = d
                        if best <= hw - 1:
                            break
                if best <= hw:
                    self.blend(x, y, color, alpha)

    def polygon(self, pts, color, alpha=1.0):
        xs = [p[0] for p in pts]; ys = [p[1] for p in pts]
        y0 = int(max(0, min(ys))); y1 = int(min(self.n, max(ys) + 1))
        x0 = int(max(0, min(xs))); x1 = int(min(self.n, max(xs) + 1))
        for y in range(y0, y1):
            py = y + .5
            nodes = []
            j = len(pts) - 1
            for i in range(len(pts)):
                yi, yj = pts[i][1], pts[j][1]
                if (yi < py <= yj) or (yj < py <= yi):
                    nodes.append(pts[i][0] + (py - yi) / (yj - yi) * (pts[j][0] - pts[i][0]))
                j = i
            nodes.sort()
            for k in range(0, len(nodes) - 1, 2):
                for x in range(max(x0, int(nodes[k])), min(x1, int(nodes[k + 1]) + 1)):
                    if nodes[k] <= x + .5 <= nodes[k + 1]:
                        self.blend(x, y, color, alpha)

    def downsample(self, factor):
        n = self.n // factor
        out = bytearray(n * n * 4)
        f2 = factor * factor
        for y in range(n):
            for x in range(n):
                r = g = b = a = 0.0
                for dy in range(factor):
                    row = (y * factor + dy) * self.n
                    for dx in range(factor):
                        p = self.px[row + x * factor + dx]
                        r += p[0] * p[3]; g += p[1] * p[3]; b += p[2] * p[3]; a += p[3]
                i = (y * n + x) * 4
                if a > 0:
                    out[i] = int(min(255, r / a)); out[i+1] = int(min(255, g / a))
                    out[i+2] = int(min(255, b / a))
                out[i+3] = int(min(255, a / f2 * 255))
        return n, out


MARK_SVG = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <rect width="40" height="40" rx="10" fill="#0c4a5c"/>
  <path d="M11 33V19.5a9 9 0 0 1 18 0V33z" fill="#f7f3ec"/>
  <path d="M14.2 33a5.8 5.8 0 0 1 11.6 0z" fill="#e39b36"/>
  <path d="M20 14.6l1.4 3.4 3.4 1.4-3.4 1.4-1.4 3.4-1.4-3.4-3.4-1.4 3.4-1.4z" fill="#0c4a5c"/>
</svg>"""


def arc(cx, cy, r, a0, a1, steps=48):
    return [(cx + r * math.cos(math.radians(a0 + (a1 - a0) * i / steps)),
             cy - r * math.sin(math.radians(a0 + (a1 - a0) * i / steps))) for i in range(steps + 1)]


def draw(size, maskable=False):
    """The Tampa Maids mark: a cream arched doorway (home) on a deep-teal tile,
    a gold sunrise at its threshold (Tampa), and a sparkle above (clean).
    Coordinates are the 40x40 grid of MARK_SVG."""
    n = size * SS
    c = Canvas(n)
    c.rounded_rect(0, 0, n, n, n * (0.30 if maskable else 0.25), DEEP)
    k = 0.80 if maskable else 1.0          # maskable: keep the mark inside the safe zone
    def P(x, y):
        return (n / 2 + (x - 20) * n / 40 * k, n / 2 + (y - 20) * n / 40 * k)
    arch = [P(11, 33)] + [P(*q) for q in arc(20, 19.5, 9, 180, 0)] + [P(29, 33)]
    c.polygon(arch, CREAM)
    c.polygon([P(*q) for q in arc(20, 33, 5.8, 0, 180)], GOLD)
    sx, sy, R, w = 20, 19.4, 4.8, 1.4
    c.polygon([P(sx, sy - R), P(sx + w, sy - w), P(sx + R, sy), P(sx + w, sy + w),
               P(sx, sy + R), P(sx - w, sy + w), P(sx - R, sy), P(sx - w, sy - w)], DEEP)
    return c.downsample(SS)


def main():
    os.makedirs(OUT, exist_ok=True)
    for size, name, mask in [(512, "icon-512.png", False),
                             (512, "icon-512-maskable.png", True),
                             (192, "icon-192.png", False),
                             (180, "icon-180.png", False),
                             (32,  "favicon-32.png", False)]:
        w, data = draw(size, mask)
        write_png(os.path.join(OUT, name), w, w, data)
        print("  web/icons/%-24s %dx%d" % (name, w, w))

    svg = MARK_SVG
    with open(os.path.join(OUT, "favicon.svg"), "w") as f:
        f.write(svg)
    print("  web/icons/favicon.svg")


if __name__ == "__main__":
    main()
