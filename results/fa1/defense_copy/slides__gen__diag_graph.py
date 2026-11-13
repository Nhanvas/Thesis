#!/usr/bin/env python
"""D10 -- graph construction and node features of ONE 4 s window (report Sections 2.3.1-2.3.2, Fig. 7).
Thumbnails are cropped from report Fig. 7 (chb11, one window); everything else is the thesis's own procedure.
Note (report 2.3.1): the common average reference is applied ONLY before the coupling, not to the features."""
import sys
from diag_lib import *

TH = "/home/claude/slidegen/thumb/"
d = D(17.28, 6.5)

# input window
d.txt(1.45, 4.45, "One preprocessed\n4 s window, 18 channels", 15, fontweight="bold")
d.image(TH + "eeg.png", 0.15, 1.75, 2.75, 3.95)
d.txt(1.45, 1.5, "chb11 (report Fig. 7a)", 13, style="italic", color=GREY)

# ---- top group: coupling
d.group(3.25, 3.45, 17.15, 6.42, "Edges: coupling between every pair of channels")
car = d.box(4.35, 4.8, 1.75, 1.0, "Common\naverage\nreference")
wpli = d.box(6.75, 5.35, 2.35, 0.8, "wPLI: consistent\nphase lag", fs=14.5)
aec = d.box(6.75, 4.25, 2.35, 0.8, "AEC: envelopes\nrise and fall together", fs=14.5)
d.line([R(car), (5.4, 4.8)]); d.arrow([(5.4, 4.8), (5.4, 5.35), L(wpli)]); d.arrow([(5.4, 4.8), (5.4, 4.25), L(aec)])
comb = d.box(9.35, 4.8, 2.0, 1.0, "A = 0.5 wPLI\n+ 0.5 AEC\n(153 pairs)", fs=14.5)
d.line([R(wpli), (8.1, 5.35), (8.1, 4.25)]); d.line([R(aec), (8.1, 4.25)]); d.arrow([(8.1, 4.8), L(comb)])
d.image(TH + "adj.png", 10.6, 3.75, 12.45, 5.85)
d.arrow([R(comb), (10.55, 4.8)])
keep = d.box(13.55, 4.8, 1.75, 1.0, "Keep the\nstrongest 20 %\n(30 edges)", fs=14.5)
d.arrow([(12.5, 4.8), L(keep)])
d.image(TH + "graph.png", 14.65, 3.6, 16.95, 6.05, frame=False)
d.arrow([R(keep), (14.7, 4.8)])

# ---- bottom group: node features (no CAR)
d.group(3.25, 0.12, 17.15, 3.2, None)
d.txt(17.0, 2.95, "Node features: 30 numbers per channel", 15, ha="right", fontweight="bold", color=BLUE)
f1 = d.box(4.95, 1.6, 3.0, 1.5, "18 · adjacency row\nrow of A ÷ largest\nedge weight", c="#D7E6F4", fs=14.5)
f2 = d.box(8.6, 1.6, 4.3, 1.5, "", c="#D7E6F4")
d.txt(7.75, 1.6, "5 · relative band\npower δ θ α β γ\n(Welch 2 s), scaled\nacross channels", 14.5)
d.image(TH + "bp.png", 9.65, 0.98, 10.6, 2.22)
f3 = d.box(12.4, 1.6, 3.3, 1.5, "+7 · absolute features\n5 log band powers,\nline length, kurtosis", c=O, fs=14.5)
d.txt(12.4, 0.5, "added: keep amplitude and waveform", 13, style="italic", color="#A8522A")
d.txt(15.6, 1.6, "X = [18 | 5 | 7]\n18 channels × 30", 16, fontweight="bold")
d.arrow([R(f3), (14.3, 1.6)])
# adjacency row comes from A
d.arrow([(11.5, 3.75), (11.5, 3.35), (4.95, 3.35), T(f1)], dash=True)

# window -> both branches
d.arrow([(2.75, 3.35), (3.1, 3.35), (3.1, 4.8), L(car)])
d.arrow([(2.75, 2.35), (3.1, 2.35), (3.1, 1.55), L(f1)])
d.txt(1.45, 0.6, "CAR only before\ncoupling, not features", 13, style="italic", color=GREY)
d.save(sys.argv[1])
print("saved")
