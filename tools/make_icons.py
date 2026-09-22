#!/usr/bin/env python3
"""Generates the PWA/favicon PNGs in pure Python (no Pillow on this machine).

Draws the Tampa Maids mark: a teal rounded square, two wave strokes, and an
amber four-point sparkle.  python3 tools/make_icons.py
"""
import os, zlib, struct, math

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.join(ROOT, "web", "icons")
SS = 2  # supersample factor

TEAL = (11, 110, 143)
LIGHT = (127, 208, 232)
AMBER = (242, 165, 65)
WHITE = (255, 255, 255)


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


def wave(cx_scale, y, amp, n):
    """A gentle sine wave polyline across the canvas."""
    pts = []
    steps = 40
    for i in range(steps + 1):
        t = i / steps
        x = (0.14 + 0.72 * t) * n
        pts.append((x, y + math.sin(t * math.pi * 2.6 + cx_scale) * amp))
    return pts


def draw(size, maskable=False):
    n = size * SS
    c = Canvas(n)
    pad = 0 if maskable else 0
    r = n * (0.30 if maskable else 0.24)
    c.rounded_rect(pad, pad, n - pad, n - pad, r, TEAL)

    # sparkle (four-point star), upper area
    sx, sy, R, w = n * 0.50, n * 0.365, n * 0.175, n * 0.055
    c.polygon([(sx, sy - R), (sx + w, sy - w), (sx + R, sy), (sx + w, sy + w),
               (sx, sy + R), (sx - w, sy + w), (sx - R, sy), (sx - w, sy - w)], AMBER)

    # two waves
    c.stroke_path(wave(0.0, n * 0.655, n * 0.052, n), n * 0.062, WHITE)
    c.stroke_path(wave(0.6, n * 0.795, n * 0.042, n), n * 0.050, LIGHT)

    w2, data = c.downsample(SS)
    return w2, data


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

    svg = '''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 40 40">
  <rect width="40" height="40" rx="11" fill="#0b6e8f"/>
  <path d="M7 26c3.2 0 3.2-3 6.4-3s3.2 3 6.4 3 3.2-3 6.4-3 3.2 3 6.4 3" stroke="#fff" stroke-width="2.2" stroke-linecap="round" fill="none"/>
  <path d="M7 31c3.2 0 3.2-2.4 6.4-2.4S16.6 31 19.8 31s3.2-2.4 6.4-2.4S29.4 31 32.6 31" stroke="#7fd0e8" stroke-width="1.8" stroke-linecap="round" fill="none"/>
  <path d="M20 8.5l1.9 4.4 4.4 1.9-4.4 1.9L20 21.1l-1.9-4.4-4.4-1.9 4.4-1.9z" fill="#f2a541"/>
</svg>'''
    with open(os.path.join(OUT, "favicon.svg"), "w") as f:
        f.write(svg)
    print("  web/icons/favicon.svg")


if __name__ == "__main__":
    main()
