#!/usr/bin/env python
"""D11 -- the graph autoencoder of this thesis (report Section 2.4, Eqs. 4-5, Table 21, Appendix B).
Matrices are drawn to their true sizes (rows x columns), with no values: dimensions only."""
import sys
from diag_lib import *

TH = "/home/claude/slidegen/thumb/"
d = D(17.28, 6.3)
cB, cR, cA = "#9CC3E6", "#7FB3DC", "#E8A35F"   # feature blocks: adjacency row, relative bp, absolute

# ---- inputs
d.txt(1.3, 6.05, "Input: one window", 15.5, fontweight="bold")
d.image(TH + "graph.png", 0.2, 3.5, 2.4, 5.75, frame=False)
d.txt(1.3, 3.3, "A: sparse adjacency\n18 × 18 (30 edges)", 14)
d.matrix(0.25, 0.75, 2.1, 1.6, 18, 30, [(18, cB), (5, cR), (7, cA)])
d.txt(1.3, 0.42, "X: node features 18 × 30", 14)

# ---- encoder
d.group(2.95, 0.15, 8.75, 6.25, "Encoder (graph convolution)", c="#FDF3EA", ec="#D9A574")
l1 = d.box(5.85, 4.65, 5.3, 1.05, "Layer 1:  H = ReLU( Ã X W₁ )\nW₁: 30 × 64  ·  1,984 parameters", c=O, fs=15)
l2 = d.box(5.85, 3.1, 5.3, 1.05, "Layer 2:  Z = Ã H W₂\nW₂: 64 × 16  ·  1,040 parameters", c=O, fs=15)
d.arrow([B(l1), T(l2)])
d.txt(5.85, 1.95, r"$\tilde{A} = \tilde{D}^{-1/2}\,(A + I)\,\tilde{D}^{-1/2}$", 17)
d.txt(5.85, 1.15, "each channel is updated from its\ngraph neighbours along weighted edges", 14)
d.arrow([(2.45, 4.65), L(l1)])
d.arrow([(2.4, 1.55), (2.75, 1.55), (2.75, 4.35), (3.2, 4.35)])

# ---- latent
d.matrix(9.25, 2.35, 1.4, 1.95, 18, 16, [(16, O)])
d.txt(9.95, 4.7, "Latent Z\n18 × 16", 15.5, fontweight="bold")
d.txt(9.9, 1.9, "one 16-number\nvector per\nchannel", 14)
d.arrow([R(l2), (9.2, 3.1)])

# ---- decoders + loss (training only)
d.group(11.1, 0.95, 17.15, 6.25, "Decoders and loss: training only", c="#FFFFFF", ec="#9AA5B1")
dA = d.box(12.75, 4.9, 2.7, 0.95, "Â = clamp(Z Zᵀ, 0, 1)\nno parameters", c=W, fs=14.5, dash=True)
dX = d.box(12.75, 3.0, 2.7, 0.95, "MLP 16 → 32 → 12\n940 parameters", c=W, fs=14.5, dash=True)
d.matrix(14.45, 4.35, 1.1, 1.1, 18, 18, [(18, "#C8D3E0")])
d.txt(15.0, 5.7, "Â: 18 × 18", 14)
d.matrix(14.45, 2.4, 0.75, 1.1, 18, 12, [(5, cR), (7, cA)])
d.txt(15.0, 2.1, "X̂: 18 × 12\n(blocks 2 + 3)", 14)
d.arrow([(10.7, 3.6), (11.35, 3.6), (11.35, 4.9), L(dA)], dash=True)
d.arrow([(11.35, 3.6), (11.35, 3.0), L(dX)], dash=True)
d.arrow([R(dA), (14.4, 4.9)], dash=True)
d.arrow([R(dX), (14.4, 2.95)], dash=True)
loss = d.box(14.1, 1.45, 5.6, 0.62, "Loss = MSE(A, Â) + 0.1 · MSE(X, X̂)", c="#F2F6FB", fs=15)
d.line([(15.65, 4.35), (16.6, 4.35), (16.6, 1.76), (16.3, 1.76)], dash=True)
d.line([(15.25, 2.95), (16.6, 2.95)], dash=True)

# ---- after training
d.arrow([(10.65, 2.6), (10.88, 2.6), (10.88, 0.55), (11.1, 0.55)])
d.txt(11.25, 0.55, "after training: Z of every channel → anomaly score", 15, ha="left", fontweight="bold", color=BLUE)
d.save(sys.argv[1])
print("saved")
