#!/usr/bin/env python
"""D12 -- the ensemble anomaly score of this thesis (report Sections 2.5.2-2.5.4, Eqs. 6-9).
Definitions checked in code: E16.rz = (x - median) / MAD (no 1.4826); E17b.member = 6th/9th/12th largest or mean of
18, minus a centred 451-window (+-15 min) running median inside each file; PS.pct = (rank - 0.5) / n; E22.final_scalar
= mean of the 4 percentiles. LedoitWolf().mahalanobis is the SQUARED distance (report Eq. 6).
The three small plots read ONLY the committed file results/figures_v6_data/chb03_score.csv (data of report Fig. 8,
chb03, seed 42, final system); nothing is recomputed."""
import sys
import pandas as pd
from diag_lib import *

REPO = "/home/claude/repo/"
S = pd.read_csv(REPO + "results/figures_v6_data/chb03_score.csv")
assert len(S) == 2700 and sorted(S.file.unique()) == [0, 1, 2], "chb03_score.csv changed"
W_, H_ = 17.28, 6.5
d = D(W_, H_)


def inset(x0, y0, x1, y1):
    a = d.fig.add_axes([x0 / W_, y0 / H_, (x1 - x0) / W_, (y1 - y0) / H_])
    for s in ("top", "right"):
        a.spines[s].set_visible(False)
    a.tick_params(labelsize=12.5, length=3)
    return a


def shade(a, t, ict, lo, hi):
    on = None
    for x, v in zip(list(t) + [None], list(ict) + [False]):
        if v and on is None:
            on = x
        if not v and on is not None:
            a.axvspan(on, x, color="#F2B98A", alpha=0.9, lw=0); on = None


# ======================================================== top row: per channel
d.group(0.12, 3.55, 17.16, 6.42, "Per channel: how far is this window from the patient’s own normal?")
d.matrix(0.45, 3.8, 1.35, 1.75, 14, 16, [(16, O)])
d.txt(1.12, 5.8, r"$z_c(t)$: 16 numbers", 14.5, fontweight="bold")
d.txt(2.42, 4.82, "every\nwindow\nof the\nrecording", 13, color=GREY)
fit = d.box(4.55, 4.82, 2.75, 1.25, r"Fit $\mu_c$ and $\Sigma_c$ on all" + "\nwindows of this patient\n(Ledoit–Wolf), no labels", fs=14.5)
d.badge(fit)
dist = d.box(8.15, 4.82, 3.75, 1.25, "", fs=14.5)
d.txt(8.15, 5.07, r"$D_c(t) = (z_c - \mu_c)^{T}\,\Sigma_c^{-1}\,(z_c - \mu_c)$", 16)
d.txt(8.15, 4.52, "squared Mahalanobis distance", 14)
rz = d.box(11.75, 4.82, 2.85, 1.25, "", fs=14.5)
d.txt(11.75, 5.07, r"$r_c(t) = \dfrac{D_c(t) - \mathrm{median}}{\mathrm{MAD}}$", 16)
d.txt(11.75, 4.42, "robust z per channel", 14)
d.badge(rz)
for a, b in ((fit, dist), (dist, rz)):
    d.arrow([R(a), L(b)])
d.arrow([(2.95, 4.82), L(fit)])
# output grid 18 channels x windows, one window outlined
gx0, gy0, gw, gh, nc = 13.75, 3.85, 3.15, 1.85, 36
d.matrix(gx0, gy0, gw, gh, 18, nc, [(nc, "#C8D3E0")])
d.ax.add_patch(Rectangle((gx0 + 21 * gw / nc, gy0), gw / nc, gh, fill=False, ec=RED, lw=2.2, zorder=4))
d.txt(gx0 + gw / 2, 5.98, "r: 18 channels × all windows", 14.5, fontweight="bold")
d.txt(gx0 + 21.5 * gw / nc, 3.72, "one window t", 13, color=RED)
d.arrow([R(rz), (gx0 - 0.05, 4.82)])

# carriage return: the outlined window goes to the bottom row
d.arrow([(gx0 + 21.5 * gw / nc, 3.6), (gx0 + 21.5 * gw / nc, 3.43), (3.35, 3.43), (3.35, 3.3)])

# ======================================================== bottom row
# members
d.group(0.12, 0.12, 3.62, 3.3, None)
d.txt(1.7, 2.92, "Across the 18 channels:\n4 members", 14.5, fontweight="bold", color=BLUE)
mem = [("6th largest", "≥ 1/3"), ("9th largest", "≥ 1/2"), ("12th largest", "≥ 2/3"), ("mean of 18", "all")]
for i, (a, b) in enumerate(mem):
    y = 2.36 - i * 0.47
    d.box(1.2, y, 1.8, 0.4, a, c=P, fs=14, rounded=True)
    d.txt(2.3, y, b, 13, ha="left", color=GREY)
d.txt(1.87, 0.38, "share of channels that must be high;\none bad electrode raises only one", 12.5, style="italic", color=GREY)

# drift correction with the real chb03 member
d.group(3.85, 0.12, 10.25, 3.3, "Per file: drift correction", c="#F4F7FB")
d.ax.add_patch(Circle((9.95, 3.08), 0.13, fc=W, ec=EC, lw=1.4, zorder=5))
d.txt(9.95, 3.08, "P", 11, fontweight="bold", zorder=6)
d.arrow([(3.62, 1.75), (3.88, 1.75)])
off, t = {}, 0.0
for f in (0, 1, 2):
    off[f] = t; t += S[S.file == f].t_s.max() + 4
S["h"] = (S.t_s + S.file.map(off)) / 3600
bounds = [off[1] / 3600, off[2] / 3600]
for (y0, y1, col, lab) in ((1.78, 2.72, "s9_raw", "before: level jumps between files"),
                           (0.42, 1.36, "s9_corr", "after: member − its ±15 min running median")):
    a = inset(4.55, y0, 10.05, y1)
    shade(a, S.h, S.ictal, 0, 1)
    a.plot(S.h, S[col], color="#0072B2", lw=0.45)
    if col == "s9_raw":
        a.plot(S.h, S.s9_med, color="k", lw=1.8)
        a.set_xticklabels([])
    else:
        a.set_xticklabels([])
    for b in bounds:
        a.axvline(b, color=GREY, ls="--", lw=1.0)
    a.set_xlim(0, 3.0); a.set_ylim(-2.3, 6.0); a.set_yticks([0, 4])
    a.set_xticks([0, 1, 2, 3])
    d.txt(4.55, y1 + 0.13, lab, 13.5, ha="left")
d.txt(10.05, 0.25, "chb03, 9th-largest member, three consecutive 1 h files; orange = seizures", 12, ha="right", style="italic", color=GREY)

# percentile + mean
pc = d.box(11.55, 1.75, 2.1, 1.75, "Percentile rank\nof each member\nin the patient’s\nrecording,\nthen mean of 4", fs=14)
d.badge(pc)
d.arrow([(10.25, 1.75), L(pc)])

# output: ensemble score E(t), real chb03 around the first seizure
e = S[(S.file == 0) & (S.t_s >= 0) & (S.t_s <= 900)]
a = inset(13.35, 0.62, 16.95, 2.62)
shade(a, e.t_s / 60, e.ictal, 0, 1)
a.plot(e.t_s / 60, e.score, color="#0072B2", lw=0.9)
a.set_ylim(0, 1.02); a.set_yticks([0, 0.5, 1]); a.set_xlim(0, 15); a.set_xticks([0, 5, 10, 15])
d.txt(15.15, 2.98, "Ensemble anomaly score E(t)", 14.5, fontweight="bold")
d.txt(15.15, 0.2, "chb03, first 15 min (min)", 12, style="italic", color=GREY)
d.arrow([R(pc), (13.05, 1.75)])
d.save(sys.argv[1])
print("saved")
