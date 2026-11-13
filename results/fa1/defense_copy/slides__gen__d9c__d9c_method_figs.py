#!/usr/bin/env python
"""d9c_method_figs.py -- simplified Method schematics for the defense deck (chat D9b, 01/11/2026).

Keyword-and-icon style (like the BME11 oral sample): no formulas, no notes. Real data where a curve or a
trace is shown:
  * EEG traces: results/figures_v8_data/gallery/a.npz (chb03 first seizure file, report Fig. 14a data;
    the 4 s window is the first 4 s of the snippet, before the seizure).
  * Graph edges: computed on that same window with src/dataprep/graph_construction.py (CAR, wPLI + AEC,
    alpha 0.5), then the strongest 30 of 153 pairs (the thesis rule). The snippet is stored at 128 Hz,
    so this is an illustration of the rule on real EEG, not a file of the pipeline.
  * Drift and score traces: results/figures_v6_data/chb03_score.csv (data of report Fig. 8).
Pure schematics (no data): feature and latent grids, the distance cloud, the sorted channel bars.

Writes SVG + PNG (2x) for: m1_pipeline (p6), m2_window_to_summary (p9), m3_score (p10).
Usage: python d9c_method_figs.py <repo_root> <out_dir>
"""
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(ROOT / "src" / "dataprep"))
import graph_construction as GC  # noqa: E402

INK, GREY, LINE, PANEL = "#1E2A38", "#5F6B7A", "#C9D3DF", "#F3F7FB"
BLUE, ORANGE, RED, GREEN, TEAL = "#1F6FB2", "#C8641E", "#DC433A", "#1B7F5B", "#2F9A78"
FONT = "Carlito, Calibri, Arial, sans-serif"

# ----------------------------------------------------------------------------- data
Z = np.load(ROOT / "results/figures_v8_data/gallery/a.npz")
EEG = Z["eeg"].astype(np.float64)                   # 18 x 3840 at 128 Hz, from 350 s
FSG = int(Z["fs"])
WIN = EEG[:, : 4 * FSG]                              # 350-354 s: before the seizure (annotation 360 s)
assert float(Z["eeg_t0"]) + 4 <= float(Z["ann"][0][0]), "window must end before the seizure"
CH = [str(c) for c in Z["ch"]]
A = GC.build_adjacency(WIN, alpha=0.5, fs=FSG)
iu = np.triu_indices(18, 1)
order = np.argsort(A[iu])[::-1][:30]
EDGES = [(iu[0][k], iu[1][k], float(A[iu][k])) for k in order]
assert len(EDGES) == 30 and len(iu[0]) == 153

S = pd.read_csv(ROOT / "results/figures_v6_data/chb03_score.csv")

POS = {"FP1": (-.30, .86), "FP2": (.30, .86), "F7": (-.72, .50), "F3": (-.36, .46), "FZ": (0, .43),
       "F4": (.36, .46), "F8": (.72, .50), "T7": (-.90, 0), "C3": (-.44, 0), "CZ": (0, 0), "C4": (.44, 0),
       "T8": (.90, 0), "P7": (-.72, -.50), "P3": (-.36, -.46), "PZ": (0, -.43), "P4": (.36, -.46),
       "P8": (.72, -.50), "O1": (-.30, -.86), "O2": (.30, -.86)}
NODE = [((POS[c.split("-")[0]][0] + POS[c.split("-")[1]][0]) / 2,
         (POS[c.split("-")[0]][1] + POS[c.split("-")[1]][1]) / 2) for c in CH]


# ----------------------------------------------------------------------------- svg helpers
def text(x, y, s, size=22, color=INK, anchor="middle", weight="normal", italic=False):
    st = ' font-style="italic"' if italic else ""
    return (f'<text x="{x:.1f}" y="{y:.1f}" font-family="{FONT}" font-size="{size}" fill="{color}" '
            f'text-anchor="{anchor}" font-weight="{weight}"{st}>{s}</text>')


def card(x, y, w, h, n, title, border=LINE, fill=PANEL):
    return (f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="22" fill="{fill}" stroke="{border}" stroke-width="3"/>'
            f'<circle cx="{x + 34}" cy="{y + 34}" r="18" fill="{border if border != LINE else GREY}"/>'
            + text(x + 34, y + 42, str(n), 22, "#FFFFFF", weight="bold")
            + text(x + 62, y + 43, title, 27, INK, anchor="start", weight="bold"))


def arrow(x0, x1, y, color=GREY):
    return (f'<line x1="{x0}" y1="{y}" x2="{x1 - 14}" y2="{y}" stroke="{color}" stroke-width="5"/>'
            f'<polygon points="{x1},{y} {x1 - 18},{y - 11} {x1 - 18},{y + 11}" fill="{color}"/>')


def polyline(xs, ys, color=INK, w=1.4, op=1.0):
    pts = " ".join(f"{a:.1f},{b:.1f}" for a, b in zip(xs, ys))
    return f'<polyline points="{pts}" fill="none" stroke="{color}" stroke-width="{w}" stroke-opacity="{op}" stroke-linejoin="round"/>'


def eeg_block(x, y, w, h, data, rows=None, color=INK, lw=1.2):
    rows = rows if rows is not None else range(data.shape[0])
    rows = list(rows)
    gap = h / (len(rows) + 0.5)
    out = []
    sc = np.percentile(np.abs(data[rows]), 99) or 1
    xs = x + np.linspace(0, w, data.shape[1])
    for k, r in enumerate(rows):
        yy = y + gap * (k + 0.75) - np.clip(data[r] / sc, -1.2, 1.2) * gap * 0.45
        out.append(polyline(xs, yy, color, lw))
    return "".join(out)


def head_graph(cx, cy, R, node_r=9, show_edges=True, edge_color=BLUE):
    o = [f'<circle cx="{cx}" cy="{cy}" r="{R}" fill="#FFFFFF" stroke="{GREY}" stroke-width="2.5"/>',
         f'<polygon points="{cx - 14},{cy - R + 2} {cx},{cy - R - 18} {cx + 14},{cy - R + 2}" fill="#FFFFFF" stroke="{GREY}" stroke-width="2.5"/>']
    P = [(cx + px * R * 0.92, cy - py * R * 0.92) for px, py in NODE]
    if show_edges:
        wmax = max(e[2] for e in EDGES)
        for i, j, wgt in EDGES:
            o.append(f'<line x1="{P[i][0]:.1f}" y1="{P[i][1]:.1f}" x2="{P[j][0]:.1f}" y2="{P[j][1]:.1f}" '
                     f'stroke="{edge_color}" stroke-width="{1.2 + 4.0 * wgt / wmax:.1f}" stroke-opacity="0.75"/>')
    for px, py in P:
        o.append(f'<circle cx="{px:.1f}" cy="{py:.1f}" r="{node_r}" fill="{INK}" stroke="#FFFFFF" stroke-width="2"/>')
    return "".join(o)


def grid(x, y, cols, rows, cw, rh, blocks):
    """blocks: list of (n_cols, color)"""
    o, cx = [], x
    for n, col in blocks:
        o.append(f'<rect x="{cx}" y="{y}" width="{n * cw}" height="{rows * rh}" fill="{col}" fill-opacity="0.85"/>')
        cx += n * cw
    for r in range(rows + 1):
        o.append(f'<line x1="{x}" y1="{y + r * rh}" x2="{x + cols * cw}" y2="{y + r * rh}" stroke="#FFFFFF" stroke-width="1.2"/>')
    for c in range(cols + 1):
        o.append(f'<line x1="{x + c * cw}" y1="{y}" x2="{x + c * cw}" y2="{y + rows * rh}" stroke="#FFFFFF" stroke-width="1.2"/>')
    return "".join(o)


def encoder(x, y, w, h, color=ORANGE):
    return (f'<polygon points="{x},{y} {x + w},{y + h * 0.28} {x + w},{y + h * 0.72} {x},{y + h}" '
            f'fill="{color}" fill-opacity="0.9" stroke="{color}" stroke-width="2"/>')


def svg(w, h, body):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" width="{w}" height="{h}" viewBox="0 0 {w} {h}">'
            f'<rect width="{w}" height="{h}" fill="#FFFFFF"/>{body}</svg>')


# ----------------------------------------------------------------------------- M2: window -> 16 numbers (p9)
def m2():
    W, H = 1840, 520
    b = []
    cy, ch = 20, 400
    xs = [0, 380, 760, 1140, 1480]
    ws = [330, 330, 330, 290, 360]
    titles = ["One 4 s window", "Graph", "Node features", "Autoencoder", "Channel summary"]
    borders = [LINE, LINE, LINE, ORANGE, BLUE]
    for k in range(5):
        b.append(card(xs[k], cy, ws[k], ch, k + 1, titles[k], borders[k]))
        if k < 4:
            b.append(arrow(xs[k] + ws[k] + 6, xs[k + 1] - 6, cy + ch / 2))
    # 1 EEG
    b.append(eeg_block(30, 80, 270, 300, WIN, color=INK, lw=1.1))
    # 2 graph
    b.append(head_graph(545, 245, 135))
    # 3 features grid 18 x 30
    cw, rh = 9.0, 14.0
    gx, gy = 805, 112
    b.append(grid(gx, gy, 30, 18, cw, rh, [(18, BLUE), (5, TEAL), (7, ORANGE)]))
    for lx, ly, lab, col in ((gx, 0, "links 18", BLUE), (gx + 140, 0, "band power 5", TEAL), (gx + 70, 1, "amplitude, sharpness 7", ORANGE)):
        yy = gy + 18 * rh + 10 + ly * 24
        b.append(f'<rect x="{lx}" y="{yy}" width="15" height="15" fill="{col}"/>')
        b.append(text(lx + 21, yy + 14, lab, 18, col, anchor="start", weight="bold"))
    b.append(text(gx - 12, gy + 9 * rh + 7, "18", 20, GREY, anchor="end"))
    b.append(text(gx + 15 * cw, gy - 12, "30 per channel", 20, GREY))
    # 4 encoder
    b.append(encoder(1185, 120, 200, 230))
    b.append(text(1285, 245, "GAE", 34, "#FFFFFF", weight="bold"))
    # 5 latent 18 x 16
    b.append(grid(1560, 112, 16, 18, 13.0, 14.0, [(16, BLUE)]))
    b.append(text(1560 + 8 * 13, 112 - 12, "16 per channel", 20, GREY))
    b.append(text(1548, 112 + 9 * 14 + 7, "18", 20, GREY, anchor="end"))
    # keywords under cards
    kw = [("18 channels, real EEG", ""), ("edge = two channels move together", "keep the strongest 30 of 153"),
          ("links · band power · amplitude", ""), ("trained once,", "seizure-free EEG only"),
          ("16 numbers per channel", "→ anomaly score")]
    for k, (l1, l2) in enumerate(kw):
        x = xs[k] + ws[k] / 2
        b.append(text(x, cy + ch + 40, l1, 23, INK))
        if l2:
            b.append(text(x, cy + ch + 70, l2, 23, INK))
    return svg(W, H + 20, "".join(b))


# ----------------------------------------------------------------------------- M1: pipeline (p6)
def m1():
    W, H = 1840, 470
    b = []
    cy, ch, cw = 20, 300, 270
    gapx = (W - 6 * cw) / 5
    titles = ["EEG recording", "Clean + cut", "Graph", "Autoencoder", "Anomaly score", "Events"]
    kws = [("hours to days", "18 channels"), ("filter, scale per patient", "4 s windows"),
           ("one graph per window", "channels = nodes"), ("16 numbers per channel", "trained once"),
           ("vs the patient's own", "whole recording"), ("onset and offset", "for the reader")]
    borders = [LINE, LINE, LINE, ORANGE, BLUE, BLUE]
    X = [k * (cw + gapx) for k in range(6)]
    for k in range(6):
        b.append(card(X[k], cy, cw, ch, k + 1, titles[k], borders[k]))
        if k < 5:
            b.append(arrow(X[k] + cw + 6, X[k + 1] - 6, cy + ch / 2))
        b.append(text(X[k] + cw / 2, cy + ch + 38, kws[k][0], 22, INK))
        b.append(text(X[k] + cw / 2, cy + ch + 66, kws[k][1], 22, INK))
    # icons
    long = EEG[:, ::4]                                   # 30 s at 32 Hz for the "recording" look
    b.append(eeg_block(X[0] + 25, 85, cw - 50, 200, long, rows=[0, 3, 7, 11, 15], lw=1.3))
    w1 = WIN[[2, 7, 12]]
    b.append(eeg_block(X[1] + 25, 85, cw - 50, 140, w1, lw=1.4))
    for k in range(4):                                   # window brackets
        xx = X[1] + 25 + k * (cw - 50) / 3
        b.append(f'<line x1="{xx:.1f}" y1="80" x2="{xx:.1f}" y2="240" stroke="{RED}" stroke-width="2.5" stroke-dasharray="6,5"/>')
    b.append(text(X[1] + cw / 2, 275, "4 s | 4 s | 4 s", 21, RED, weight="bold"))
    b.append(head_graph(X[2] + cw / 2, 185, 95, node_r=7))
    b.append(encoder(X[3] + 55, 95, 160, 170))
    b.append(text(X[3] + 135, 188, "GAE", 30, "#FFFFFF", weight="bold"))
    d = S[S.file == 0].sort_values("t_s")
    d = d[d.t_s < 900]
    sx = X[4] + 25 + (d.t_s.values / 900) * (cw - 50)
    sy = 260 - d.score_sm.values * 160
    ict = d[d.ictal]
    if len(ict):
        a0 = X[4] + 25 + ict.t_s.min() / 900 * (cw - 50); a1 = X[4] + 25 + (ict.t_s.max() + 4) / 900 * (cw - 50)
        b.append(f'<rect x="{a0:.1f}" y="95" width="{a1 - a0:.1f}" height="170" fill="{RED}" fill-opacity="0.15"/>')
    b.append(polyline(sx, sy, BLUE, 2.2))
    # events icon: timeline with one event and two ticks
    ex0, ex1, ey = X[5] + 30, X[5] + cw - 30, 190
    b.append(f'<line x1="{ex0}" y1="{ey}" x2="{ex1}" y2="{ey}" stroke="{GREY}" stroke-width="4"/>')
    b.append(f'<rect x="{ex0 + 70}" y="{ey - 30}" width="80" height="60" rx="6" fill="{TEAL}" fill-opacity="0.85"/>')
    for xx, lab in ((ex0 + 70, "onset"), (ex0 + 150, "offset")):
        b.append(f'<line x1="{xx}" y1="{ey - 55}" x2="{xx}" y2="{ey + 45}" stroke="{INK}" stroke-width="3"/>')
        b.append(text(xx, ey - 62, lab, 20, INK, weight="bold"))
    # legend
    ly = H - 22
    b.append(f'<rect x="{W / 2 - 520}" y="{ly - 20}" width="26" height="26" rx="5" fill="{PANEL}" stroke="{ORANGE}" stroke-width="3"/>')
    b.append(text(W / 2 - 484, ly, "trained once on the training patients", 22, INK, anchor="start"))
    b.append(f'<rect x="{W / 2 + 40}" y="{ly - 20}" width="26" height="26" rx="5" fill="{PANEL}" stroke="{BLUE}" stroke-width="3"/>')
    b.append(text(W / 2 + 76, ly, "set for each patient from its own recording, no labels", 22, INK, anchor="start"))
    return svg(W, H, "".join(b))


# ----------------------------------------------------------------------------- M3: score (p10)
def m3():
    W, H = 1840, 500
    b = []
    cy, ch = 20, 360
    xs = [0, 470, 940, 1400]
    ws = [420, 420, 410, 440]
    titles = ["Channel vs its own history", "How many channels?", "Remove slow drift", "One score per window"]
    borders = [BLUE, BLUE, BLUE, BLUE]
    for k in range(4):
        b.append(card(xs[k], cy, ws[k], ch, k + 1, titles[k], borders[k]))
        if k < 3:
            b.append(arrow(xs[k] + ws[k] + 6, xs[k + 1] - 6, cy + ch / 2))
    # 1: schematic cloud + far point
    rng = np.random.default_rng(3)
    pts = rng.multivariate_normal([0, 0], [[1, .6], [.6, 1]], 160)
    cx0, cy0 = 190, 225
    for px, py in pts:
        b.append(f'<circle cx="{cx0 + px * 42:.1f}" cy="{cy0 - py * 42:.1f}" r="4.5" fill="{GREY}" fill-opacity="0.55"/>')
    fx, fy = cx0 + 150, cy0 - 115
    b.append(f'<line x1="{cx0}" y1="{cy0}" x2="{fx}" y2="{fy}" stroke="{RED}" stroke-width="3" stroke-dasharray="8,6"/>')
    b.append(f'<circle cx="{fx}" cy="{fy}" r="10" fill="{RED}"/>')
    b.append(text(fx + 18, fy + 40, "far =", 21, RED, anchor="start", weight="bold"))
    b.append(text(fx + 18, fy + 64, "unusual", 21, RED, anchor="start", weight="bold"))
    b.append(text(cx0 - 60, cy0 + 120, "all windows of this patient", 20, GREY))
    # 2: schematic sorted bars with members
    vals = np.sort(np.concatenate([np.linspace(3.8, 1.2, 9), np.linspace(1.0, 0.2, 9)]))[::-1]
    bx, by, bw = 505, 330, 18
    for k, v in enumerate(vals):
        col = BLUE if k in (5, 8, 11) else "#AFC3D9"
        b.append(f'<rect x="{bx + k * (bw + 1.5):.1f}" y="{by - v * 55:.1f}" width="{bw}" height="{v * 55:.1f}" fill="{col}"/>')
    for k, lab in ((5, "6th"), (8, "9th"), (11, "12th")):
        b.append(text(bx + k * (bw + 1.5) + bw / 2, by + 24, lab, 19, BLUE, weight="bold"))
    mv = vals.mean()
    b.append(f'<line x1="{bx}" y1="{by - mv * 55:.1f}" x2="{bx + 18 * (bw + 1.5)}" y2="{by - mv * 55:.1f}" stroke="{ORANGE}" stroke-width="3" stroke-dasharray="7,5"/>')
    b.append(text(bx + 18 * (bw + 1.5) + 4, by - mv * 55 + 6, "mean", 19, ORANGE, anchor="start", weight="bold"))
    b.append(text(xs[1] + ws[1] / 2, 112, "18 channels, sorted by distance", 20, GREY))
    # 3: real drift before/after (chb03, 9th member, first three files)
    d = S[S.file.isin([0, 1, 2])].copy()
    d["g"] = d.file * 3600 + d.t_s
    gx0, gw = 975, 345
    g = (d.g.values - d.g.min()) / (d.g.max() - d.g.min())
    def tr(y, base, amp):
        y = np.clip(y, -2, 5)
        return base - y * amp
    b.append(text(gx0, 98, "before", 19, GREY, anchor="start"))
    b.append(polyline(gx0 + g * gw, tr(d.s9_raw.values, 190, 13), "#7FA7CC", 1.0))
    b.append(polyline(gx0 + g * gw, tr(d.s9_med.values, 190, 13), INK, 3.0))
    b.append(text(gx0, 248, "after", 19, GREY, anchor="start"))
    b.append(polyline(gx0 + g * gw, tr(d.s9_corr.values, 318, 13), BLUE, 1.0))
    for fb in (1, 2):
        xx = gx0 + (fb * 3600 - d.g.min()) / (d.g.max() - d.g.min()) * gw
        b.append(f'<line x1="{xx:.1f}" y1="105" x2="{xx:.1f}" y2="330" stroke="{GREY}" stroke-width="1.5" stroke-dasharray="4,4"/>')
    b.append(text(xs[2] + ws[2] / 2, cy + ch - 12, "three 1 h files", 19, GREY))
    # 4: real ensemble score, first 15 min of file 0
    d = S[(S.file == 0) & (S.t_s < 900)].sort_values("t_s")
    px0, pw, py0, ph = 1440, 360, 330, 220
    sx = px0 + d.t_s.values / 900 * pw
    ict = d[d.ictal]
    a0 = px0 + ict.t_s.min() / 900 * pw; a1 = px0 + (ict.t_s.max() + 4) / 900 * pw
    b.append(f'<rect x="{a0:.1f}" y="{py0 - ph}" width="{a1 - a0:.1f}" height="{ph}" fill="{RED}" fill-opacity="0.18"/>')
    b.append(polyline(sx, py0 - d.score.values * ph, "#AFC3D9", 1.0))
    b.append(polyline(sx, py0 - d.score_sm.values * ph, BLUE, 2.4))
    b.append(f'<line x1="{px0}" y1="{py0}" x2="{px0 + pw}" y2="{py0}" stroke="{GREY}" stroke-width="1.5"/>')
    b.append(text((a0 + a1) / 2, py0 - ph - 8, "seizure", 19, RED, weight="bold"))
    b.append(text(px0 + pw / 2, py0 + 26, "15 min", 19, GREY))
    kw = [("16 numbers vs all windows", "of the same patient"), ("a third · a half · two thirds · all", ""),
          ("±15 min running median", "inside each file"), ("high = unusual", "for this patient")]
    for k, (l1, l2) in enumerate(kw):
        x = xs[k] + ws[k] / 2
        b.append(text(x, cy + ch + 40, l1, 23, INK))
        if l2:
            b.append(text(x, cy + ch + 70, l2, 23, INK))
    return svg(W, H, "".join(b))


for name, fn in (("m1_pipeline", m1), ("m2_window_to_summary", m2), ("m3_score", m3)):
    (OUT / f"{name}.svg").write_text(fn(), encoding="utf-8")
print("edges kept:", len(EDGES), "of", len(iu[0]), "; strongest", round(EDGES[0][2], 3), "weakest kept", round(EDGES[-1][2], 3))
print("wrote", [p.name for p in sorted(OUT.glob("m*.svg"))])
