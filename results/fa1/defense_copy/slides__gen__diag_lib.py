"""diag_lib.py -- shared drawing helpers for the method diagrams (same visual language as report Fig. 6
and the horizontal pipeline P07). Coordinates in inches; 1 in = 100 px on the slide."""
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Circle, Rectangle
from PIL import Image
import numpy as np

Y, G, O, P, W = "#F8E6A6", "#D6E8D4", "#F6C9A0", "#DCD3EC", "#FFFFFF"
EC, TX, GREY, RED, BLUE = "#3A3F47", "#1E2430", "#5F6B7A", "#C62828", "#1F6FB2"
FS = 15


class D:
    def __init__(self, w, h):
        self.fig = plt.figure(figsize=(w, h))
        self.ax = self.fig.add_axes([0, 0, 1, 1]); self.ax.set_xlim(0, w); self.ax.set_ylim(0, h); self.ax.axis("off")

    def txt(self, x, y, s, fs=FS, ha="center", va="center", **k):
        self.ax.text(x, y, s, ha=ha, va=va, fontsize=fs, color=k.pop("color", TX), linespacing=1.15, **k)

    def box(self, x, y, w, h, s="", c=W, fs=FS, rounded=False, dash=False, lw=1.6, ec=EC, title=None, tfs=14.5, **k):
        bs = "round,pad=0,rounding_size=0.14" if rounded else "square,pad=0"
        self.ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=bs, fc=c, ec=ec, lw=lw,
                                         ls=(0, (4, 3)) if dash else "-", zorder=k.pop("z", 1)))
        if s:
            self.txt(x, y, s, fs, **k)
        if title:
            self.txt(x - w / 2 + 0.12, y + h / 2 - 0.2, title, tfs, ha="left", fontweight="bold")
        return (x, y, w, h)

    def group(self, x0, y0, x1, y1, title, c="#F4F7FB", ec="#9AA5B1", tfs=15, below=None):
        self.ax.add_patch(FancyBboxPatch((x0, y0), x1 - x0, y1 - y0, boxstyle="round,pad=0,rounding_size=0.15",
                                         fc=c, ec=ec, lw=1.4, zorder=0))
        if title:
            self.txt(x0 + 0.15, y1 - 0.22, title, tfs, ha="left", fontweight="bold", color=BLUE)
        if below:
            self.txt((x0 + x1) / 2, y0 - 0.25, below, 14, style="italic", color=GREY)

    def para(self, x, y, w, h, s, c=G, fs=FS):
        k = 0.15
        self.ax.add_patch(Polygon([(x - w / 2 + k, y + h / 2), (x + w / 2 + k, y + h / 2), (x + w / 2 - k, y - h / 2),
                                   (x - w / 2 - k, y - h / 2)], closed=True, fc=c, ec=EC, lw=1.6, zorder=1))
        self.txt(x, y, s, fs)
        return (x, y, w, h)

    def badge(self, b, dx=0.05):
        x, y, w, h = b
        self.ax.add_patch(Circle((x - w / 2 + dx, y + h / 2 - 0.02), 0.13, fc=W, ec=EC, lw=1.4, zorder=5))
        self.ax.text(x - w / 2 + dx, y + h / 2 - 0.02, "P", ha="center", va="center", fontsize=11, fontweight="bold", zorder=6)

    def arrow(self, pts, dash=False, c=EC, lw=1.7):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=c, lw=lw, ls="--" if dash else "-", zorder=2)
        self.ax.annotate("", xy=pts[-1], xytext=pts[-2],
                         arrowprops=dict(arrowstyle="-|>", color=c, lw=lw, mutation_scale=18), zorder=3)

    def line(self, pts, dash=False, c=EC, lw=1.7):
        xs, ys = zip(*pts)
        self.ax.plot(xs, ys, color=c, lw=lw, ls="--" if dash else "-", zorder=2)

    def image(self, path, x0, y0, x1, y1, frame=True):
        im = np.asarray(Image.open(path).convert("RGBA"))
        self.ax.imshow(im, extent=(x0, x1, y0, y1), aspect="auto", zorder=2, interpolation="lanczos")
        if frame:
            self.ax.add_patch(Rectangle((x0, y0), x1 - x0, y1 - y0, fill=False, ec="#9AA5B1", lw=1.0, zorder=3))

    def matrix(self, x0, y0, w, h, rows, cols, blocks, label=None, lfs=14):
        """schematic matrix: rows x cols cells; blocks = [(ncols, colour)]; dimension only, no values."""
        cw, rh = w / cols, h / rows
        c0 = 0
        for n, c in blocks:
            self.ax.add_patch(Rectangle((x0 + c0 * cw, y0), n * cw, h, fc=c, ec="none", zorder=1))
            c0 += n
        for i in range(rows + 1):
            self.ax.plot([x0, x0 + w], [y0 + i * rh] * 2, color="#FFFFFF", lw=0.6, zorder=2)
        for j in range(cols + 1):
            self.ax.plot([x0 + j * cw] * 2, [y0, y0 + h], color="#FFFFFF", lw=0.6, zorder=2)
        self.ax.add_patch(Rectangle((x0, y0), w, h, fill=False, ec=EC, lw=1.4, zorder=3))
        if label:
            self.txt(x0 + w / 2, y0 - 0.25, label, lfs)

    def save(self, path):
        self.fig.savefig(path, dpi=200)
        plt.close(self.fig)


R = lambda b: (b[0] + b[2] / 2, b[1])
L = lambda b: (b[0] - b[2] / 2, b[1])
T = lambda b: (b[0], b[1] + b[3] / 2)
B = lambda b: (b[0], b[1] - b[3] / 2)
