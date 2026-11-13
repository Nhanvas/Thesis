#!/usr/bin/env python
"""pipeline.py -- report Fig. 6 (processing pipeline) redrawn horizontally for the 16:9 slide.

Same boxes, shapes, colours and wording as Fig. 6 of the report; one connected serpentine flow:
row 1 left->right (preprocessing, graph), row 2 (node features + graph autoencoder), row 3 right->left
(score), row 4 left->right (events). 1 in = 100 px on the slide (figure 17.28 x 7.3 in), 16 pt = 22 px.
Run: python pipeline.py out/P07_pipeline.png
"""
import sys
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, Polygon, Ellipse, Rectangle, Circle

Y, G, O, P, W = "#F8E6A6", "#D6E8D4", "#F6C9A0", "#DCD3EC", "#FFFFFF"
EC, FS = "#3A3F47", 15
W_, H_ = 1.62, 0.86
fig = plt.figure(figsize=(17.28, 7.3))
ax = fig.add_axes([0, 0, 1, 1]); ax.set_xlim(0, 17.28); ax.set_ylim(0, 7.3); ax.axis("off")


def txt(x, y, s, fs=FS, **k):
    ax.text(x, y, s, ha="center", va="center", fontsize=fs, color="#1E2430", linespacing=1.12, **k)


def rect(x, y, s, c=W, w=W_, h=H_, rounded=False, dash=False):
    bs = "round,pad=0,rounding_size=0.16" if rounded else "square,pad=0"
    ax.add_patch(FancyBboxPatch((x - w / 2, y - h / 2), w, h, boxstyle=bs, fc=c, ec=EC, lw=1.6, ls="--" if dash else "-"))
    txt(x, y, s)
    return (x, y, w, h)


def para(x, y, s, c, w=W_, h=H_, fs=FS):
    k = 0.16
    ax.add_patch(Polygon([(x - w / 2 + k, y + h / 2), (x + w / 2 + k, y + h / 2), (x + w / 2 - k, y - h / 2),
                          (x - w / 2 - k, y - h / 2)], closed=True, fc=c, ec=EC, lw=1.6))
    txt(x, y, s, fs)
    return (x, y, w, h)


def cyl(x, y, s, c=Y, w=W_, h=H_, fs=FS):
    e = 0.14
    ax.add_patch(Rectangle((x - w / 2, y - h / 2 + e / 2), w, h - e, fc=c, ec="none"))
    ax.plot([x - w / 2, x - w / 2], [y - h / 2 + e / 2, y + h / 2 - e / 2], color=EC, lw=1.6)
    ax.plot([x + w / 2, x + w / 2], [y - h / 2 + e / 2, y + h / 2 - e / 2], color=EC, lw=1.6)
    ax.add_patch(Ellipse((x, y - h / 2 + e / 2), w, e * 2, fc=c, ec=EC, lw=1.6))
    ax.add_patch(Ellipse((x, y + h / 2 - e / 2), w, e * 2, fc=c, ec=EC, lw=1.6))
    txt(x, y - 0.03, s, fs)
    return (x, y, w, h)


def trap(x, y, s, c=O, w=W_, h=0.7):
    k = 0.2
    ax.add_patch(Polygon([(x - w / 2, y + h / 2), (x + w / 2, y + h / 2), (x + w / 2 - k, y - h / 2), (x - w / 2 + k, y - h / 2)],
                         closed=True, fc=c, ec=EC, lw=1.6))
    txt(x, y, s)
    return (x, y, w, h)


def badge(b):
    x, y, w, h = b
    ax.add_patch(Circle((x - w / 2 + 0.05, y + h / 2 - 0.02), 0.13, fc="#FFFFFF", ec=EC, lw=1.4, zorder=5))
    ax.text(x - w / 2 + 0.05, y + h / 2 - 0.02, "P", ha="center", va="center", fontsize=11, fontweight="bold", zorder=6)


def arrow(pts, dash=False):
    xs, ys = zip(*pts)
    ax.plot(xs[:-1] + (xs[-1],), ys[:-1] + (ys[-1],), color=EC, lw=1.7, ls="--" if dash else "-", zorder=1)
    ax.annotate("", xy=pts[-1], xytext=pts[-2], arrowprops=dict(arrowstyle="-|>", color=EC, lw=1.7, mutation_scale=18,
                                                                 ls="--" if dash else "-"), zorder=2)


R = lambda b: (b[0] + b[2] / 2, b[1])
L = lambda b: (b[0] - b[2] / 2, b[1])
T = lambda b: (b[0], b[1] + b[3] / 2)
B = lambda b: (b[0], b[1] - b[3] / 2)

# ---------------- row 1: preprocessing and graph (left -> right)
y1 = 6.6
xs = [0.95 + i * 1.925 for i in range(9)]
r1 = [cyl(xs[0], y1, "18-channel\nbipolar EEG", h=1.0, fs=14.5),
      rect(xs[1], y1, "Band-pass\n0.5–60 Hz,\nnotch filter"),
      rect(xs[2], y1, "Segment into\n4 s windows"),
      rect(xs[3], y1, "Channel\nz-score\nper patient"),
      para(xs[4], y1, "Preprocessed\nwindows", Y),
      rect(xs[5], y1, "Common\naverage\nreference"),
      para(xs[6], y1, "wPLI + AEC\nadjacency", G),
      rect(xs[7], y1, "Retain\nstrongest\n20 % of edges"),
      para(xs[8] - 0.05, y1, "Per-window\ngraph: 18 nodes,\n30 edges", G, w=1.7, h=1.0, fs=13.5)]
badge(r1[3])
for a, b in zip(r1[:-1], r1[1:]):
    arrow([R(a), L(b)])

# ---------------- row 2: node features + graph autoencoder
y2 = 4.55
feat = para(xs[4] - 0.08, y2, "Band powers\nand amplitude\nfeatures", G, w=1.85, h=0.95)
arrow([B(r1[4]), T(feat)])
ax.add_patch(FancyBboxPatch((9.78, 3.62), 7.4, 2.02, boxstyle="round,pad=0,rounding_size=0.15", fc="none", ec=EC, lw=1.5, ls=(0, (4, 3))))
ax.text(11.35, 5.42, "Graph autoencoder", fontsize=FS, fontweight="bold", va="center", color="#1E2430")
enc = trap(10.75, 4.55, "Encoder", w=1.55)
lat = rect(12.85, 4.55, "Latent Z\n(18 × 16)", O, w=1.55, h=0.72)
adec = trap(14.75, 5.05, "A decoder", w=1.45, h=0.56)
xdec = trap(14.75, 4.05, "X decoder", w=1.45, h=0.56)
loss = rect(16.4, 4.55, "Loss:\nMSE(A) +\n0.1·MSE(X)", W, w=1.35, h=1.2)
arrow([R(feat), L(enc)])
arrow([B(r1[8]), (r1[8][0], 5.95), (enc[0], 5.95), T(enc)])
arrow([R(enc), L(lat)])
arrow([R(lat), (13.95, 4.55), (13.95, 5.05), L(adec)], dash=True)
arrow([(13.95, 4.55), (13.95, 4.05), L(xdec)], dash=True)
arrow([R(adec), (15.72, 5.05)], dash=True)
arrow([R(xdec), (15.72, 4.05)], dash=True)
ax.text(9.95, 3.82, "decoders and loss: training only", fontsize=13, style="italic", color="#5F6B7A", ha="left")

# ---------------- row 3: anomaly score (right -> left)
y3 = 2.55
maha = rect(12.85, y3, "Mahalanobis\ndistance\nper channel", w=1.75)
rz = rect(10.6, y3, "Robust\nz-score\nper channel")
badge(maha); badge(rz)
arrow([B(lat), T(maha)])
ax.text(13.0, 3.3, "used for scoring", fontsize=13, style="italic", color="#5F6B7A", ha="left")
arrow([L(maha), R(rz)])
mx = 8.15
mem = [rect(mx, y3 + 0.69 - i * 0.46, s, P, w=1.95, h=0.38, rounded=True) for i, s in
       enumerate(["6th largest", "9th largest", "12th largest", "mean of 18"])]
ax.text(mx, y3 + 1.08, "Four ensemble members", fontsize=13.5, ha="center", va="center", color="#1E2430")
for m in mem:
    arrow([(9.55, m[1]), R(m)])
ax.plot([9.55, 9.55], [mem[-1][1], mem[0][1]], color=EC, lw=1.7)
ax.plot([L(rz)[0], 9.55], [y3, y3], color=EC, lw=1.7)
for m in mem:
    ax.plot([L(m)[0], 6.85], [m[1], m[1]], color=EC, lw=1.7)
ax.plot([6.85, 6.85], [mem[-1][1], mem[0][1]], color=EC, lw=1.7)
drift = rect(5.5, y3, "Drift correction:\nminus ±15 min\nrunning median", w=1.9, h=1.0)
badge(drift)
arrow([(6.85, y3), R(drift)])
pct = rect(3.25, y3, "Percentile rank\nper member,\nthen average", w=1.9, h=1.0)
badge(pct)
arrow([L(drift), R(pct)])
ens = para(1.05, y3, "Ensemble\nanomaly score", Y, w=1.6)
arrow([L(pct), R(ens)])

# ---------------- row 4: events (left -> right)
y4 = 0.62
sm = rect(1.05, y4, "Smoothing\n(5 windows,\n20 s)")
arrow([B(ens), T(sm)])
thr = rect(3.3, y4, "Threshold at\nthe patient’s\nalarm budget", w=1.9)
badge(thr)
ev = rect(5.6, y4, "Detected events\n(merge < 90 s)", P, w=1.85)
cpd = rect(7.85, y4, "Kernel change\npoint localizer", w=1.8)
out = rect(10.2, y4, "Seizure events:\nonset and offset", P, w=1.95)
for a, b in ((sm, thr), (thr, ev), (ev, cpd), (cpd, out)):
    arrow([R(a), L(b)])

# ---------------- legend
lx = 12.2
ax.add_patch(Rectangle((lx, 1.25), 0.42, 0.28, fc=O, ec=EC, lw=1.3))
ax.text(lx + 0.6, 1.39, "fitted once on the 12 training patients", fontsize=14, va="center")
ax.add_patch(Circle((lx + 0.21, 0.85), 0.13, fc="#FFFFFF", ec=EC, lw=1.4))
ax.text(lx + 0.21, 0.85, "P", ha="center", va="center", fontsize=11, fontweight="bold")
ax.text(lx + 0.6, 0.85, "estimated per patient from its own recording", fontsize=14, va="center")
ax.plot([lx, lx + 0.42], [0.33, 0.33], color=EC, lw=1.7, ls="--")
ax.text(lx + 0.6, 0.33, "training only", fontsize=14, va="center")
fig.savefig(sys.argv[1], dpi=200)
print("saved")
