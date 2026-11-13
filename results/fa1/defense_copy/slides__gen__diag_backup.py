#!/usr/bin/env python
"""Self-drawn diagrams for the backup slides (same visual language as D10-D13).
Every number printed here is in NUMBERS_LOCK (report) unless the diagram says "from the experiment record".
Run: python diag_backup.py out"""
import sys
import numpy as np
from diag_lib import *
from matplotlib.patches import Rectangle

OUT = sys.argv[1]
TH = "/home/claude/slidegen/thumb/"


# ---------------------------------------------------------------- B02 why the latent distance of a GAE
def b02():
    d = D(17.28, 6.0)
    d.image(TH + "graph.png", 0.15, 2.0, 2.15, 4.3, frame=False)
    d.txt(1.15, 1.75, "graph of one window", 14)
    enc = d.box(3.5, 3.15, 1.8, 1.1, "GAE encoder\n(trained on\nseizure-free EEG)", c=O, fs=14)
    d.arrow([(2.2, 3.15), L(enc)])
    z = d.box(5.75, 3.15, 1.5, 1.1, "Latent Z\n18 × 16", c=O, fs=15)
    d.arrow([R(enc), L(z)])
    rows = [(5.15, "Reconstruction error", "decoder output vs input", "0.527–0.534", "AUROC, seizure vs\nhigh-amplitude windows", RED),
            (3.15, "Latent distance", "Mahalanobis of Z from the patient", "0.966", "AUROC, same windows", BLUE),
            (1.15, "Read per channel", "instead of the graph-mean latent", "0.622 vs 0.553", "pooled sensitivity\n(2 seeds)", BLUE)]
    for y, t, s, v, u, c in rows:
        b = d.box(9.35, y, 3.7, 1.25, "", c=W)
        d.txt(9.35, y + 0.22, t, 15.5, fontweight="bold")
        d.txt(9.35, y - 0.25, s, 13.5, color=GREY)
        d.arrow([(6.55, 3.15), (7.05, 3.15), (7.05, y), L(b)])
        d.txt(11.6, y + 0.2, v, 24, ha="left", fontweight="bold", color=c)
        d.txt(11.6, y - 0.38, u.replace("\n", " "), 13.5, ha="left", color=GREY)
    d.txt(0.2, 0.2, "Same own-recording reference with a density on the input features: 0.596 vs 0.612 for the channel latent (development)",
          13.5, ha="left", style="italic", color=GREY)
    d.save(f"{OUT}/B02_latent.png")


# ---------------------------------------------------------------- B03 earlier systems (experiment record)
def b03():
    d = D(17.28, 5.6)
    steps = [("1 · First pipeline", "GAE + LSTM temporal branch\n+ gamma coupling\n+ change points (PELT)",
              "LSTM branch dropped:\ntraining code lost,\nnot reproducible", "#F4F7FB"),
             ("2 · Earlier system", "GAE v1, three readouts:\nreconstruction, graph latent,\ngamma coupling; PELT",
              "rebuilt timeline 0.618 @ 27.4\ncontinuous 0.303 @ 73.3\n→ protocol not used", "#F4F7FB"),
             ("3 · Levers tried", "directed transfer-entropy branch,\nmulti-relational GAE, slope gate,\nmedian smoother",
              "none improved the event\nresult at its gate\n→ not adopted", "#F4F7FB"),
             ("4 · Rebuild (this thesis)", "continuous timeline; +7 amplitude\nfeatures; channel latent; drift;\nensemble; budget; localizer",
              "held-out 26 / 76 @ 22.2\nfinal 37 / 76 @ 27.5\n(seed 42)", "#E3F1E8")]
    for i, (t, a, r, c) in enumerate(steps):
        x = 2.1 + i * 4.35
        d.box(x, 3.75, 3.95, 2.4, "", c=c, rounded=True)
        d.txt(x, 4.65, t, 16, fontweight="bold", color=BLUE)
        d.txt(x, 3.6, a, 14)
        d.box(x, 1.15, 3.95, 1.45, r, c=W, fs=14, dash=i < 3)
        d.arrow([(x, 2.55), (x, 1.9)])
        if i:
            d.arrow([(x - 4.35 + 1.98, 3.75), (x - 1.98, 3.75)])
    d.save(f"{OUT}/B03_history.png")


# ---------------------------------------------------------------- B09 why event metrics
def b09():
    d = D(17.28, 5.4)
    rng = np.random.default_rng(3)
    n = 90
    x0, w = 0.4, 16.4
    cw = w / n
    seiz = range(40, 47)
    fa = range(70, 73)
    for k, (y, title) in enumerate([(3.6, "Window metric: every 4 s window is one sample"), (1.0, "Event metric (SzCORE): what the reviewer sees")]):
        d.txt(x0, y + 1.05, title, 16, ha="left", fontweight="bold", color=BLUE)
        for i in range(n):
            c = "#F2B98A" if i in seiz else "#DCE6F2"
            if k == 0:
                d.ax.add_patch(Rectangle((x0 + i * cw, y - 0.3), cw * 0.9, 0.6, fc=c, ec="none"))
            else:
                d.ax.add_patch(Rectangle((x0 + i * cw, y - 0.3), cw, 0.6, fc=c, ec="none"))
        if k == 1:
            d.ax.add_patch(Rectangle((x0 + 38 * cw, y - 0.45), 11 * cw, 0.9, fill=False, ec="#009E73", lw=3))
            d.txt(x0 + 43.5 * cw, y - 0.75, "1 detected seizure (onset, offset)", 14, color="#009E73")
            d.ax.add_patch(Rectangle((x0 + 69 * cw, y - 0.45), 5 * cw, 0.9, fill=False, ec=RED, lw=3))
            d.txt(x0 + 71.5 * cw, y - 0.75, "1 false alarm", 14, color=RED)
    d.txt(x0, 2.65, "a long recording is > 99 % background windows (seizures = 0.4 % of test time), so window scores look good while"
          " events are missed; they give no onset, offset or false alarms per day", 13.5, ha="left", color=GREY, style="italic")
    d.save(f"{OUT}/B09_event.png")


# ---------------------------------------------------------------- B10 old evaluation protocol
def b10():
    d = D(17.28, 5.3)
    rng = np.random.default_rng(7)
    n = 80; x0, w = 0.4, 11.4; cw = w / n
    hi = set(rng.choice(range(n), 14, replace=False)) - set(range(36, 42))
    for k, (y, title) in enumerate([(3.75, "Continuous recording (protocol of record): every window, in time order"),
                                     (1.05, "Earlier protocol: timeline rebuilt from the annotations")]):
        d.txt(x0, y + 0.95, title, 16, ha="left", fontweight="bold", color=BLUE if k == 0 else RED)
        for i in range(n):
            if 36 <= i < 42:
                c = "#F2B98A"
            elif i in hi:
                c = "#7F8C9C" if k == 0 else "#FFFFFF"
            else:
                c = "#DCE6F2"
            ec = "#C9D3E0" if (k == 1 and i in hi) else "none"
            d.ax.add_patch(Rectangle((x0 + i * cw, y - 0.3), cw * 0.92, 0.6, fc=c, ec=ec, ls="--"))
        if k == 1:
            d.txt(x0, y - 0.65, "high-amplitude windows removed; gaps filled with resampled clean windows", 13.5, ha="left", color=GREY, style="italic")
    d.txt(x0 + 0.1, 0.2, "orange = seizure · dark grey = high-amplitude non-seizure window (source of most false alarms)", 13, ha="left", color=GREY)
    r1 = d.box(14.55, 3.75, 4.6, 1.25, "", c="#E8F1FA")
    d.txt(14.55, 3.95, "0.303 (23 / 76)", 22, fontweight="bold", color=BLUE)
    d.txt(14.55, 3.45, "at 73.3 false alarms per day", 14)
    r2 = d.box(14.55, 1.05, 4.6, 1.25, "", c="#FDECEA")
    d.txt(14.55, 1.25, "0.618", 22, fontweight="bold", color=RED)
    d.txt(14.55, 0.75, "at 27.4 false alarms per day", 14)
    d.txt(14.55, 2.4, "same earlier system,\nsame operating point", 14, color=GREY)
    d.arrow([(12.0, 3.75), L(r1)]); d.arrow([(12.0, 1.05), L(r2)])
    d.save(f"{OUT}/B10_protocol.png")


# ---------------------------------------------------------------- B21 application without labels
def b21():
    d = D(17.28, 5.6)
    e = d.box(1.4, 3.5, 2.3, 1.1, "Raw EDF files\nof one patient", c=Y, fs=15)
    p = d.box(5.6, 3.5, 4.4, 1.5, "Frozen thesis pipeline\nz-score statistics from the whole\nrecording (every 10th window)", c="#FFF6DD", fs=14.5)
    v = d.box(9.95, 3.5, 2.6, 1.1, "AI events\n→ reviewer", c=P, fs=15)
    d.arrow([R(e), L(p)]); d.arrow([R(p), L(v)])
    nr = d.box(5.6, 1.1, 4.4, 1.6, "", c="#FDECEA", dash=True, ec=RED)
    d.txt(5.6, 1.62, "Never read at run time", 15, fontweight="bold", color=RED)
    d.txt(5.6, 0.95, "seizure annotations · seizure fields of the\nsummary files · label-split arrays · thesis scores", 13.5)
    d.line([(5.6, 1.9), (5.6, 2.75)], dash=True, c=RED)
    d.txt(5.75, 2.35, "✗", 18, color=RED, ha="left")
    t = d.box(14.75, 4.15, 4.6, 1.75, "", c=W)
    d.txt(14.75, 4.7, "15 automated tests passed", 15.5, fontweight="bold")
    d.txt(14.75, 3.9, "4 guards against label use\n7 final-system equivalence\n4 file matching", 14)
    s = d.box(14.75, 1.45, 4.6, 2.0, "", c="#E3F1E8")
    d.txt(14.75, 2.1, "Identity on chb03", 15.5, fontweight="bold")
    d.txt(14.75, 1.25, "thesis statistics: 7 / 7, 22 false alarms\nsame budget 0.005175\nscore difference ≤ 7.31 × 10⁻⁶", 14)
    d.save(f"{OUT}/B21_labelfree.png")


for f in (b02, b03, b09, b10, b21):
    f()
print("saved")
