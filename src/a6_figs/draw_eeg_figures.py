#!/usr/bin/env python
"""
draw_eeg_figures.py -- report figures with real EEG (chat A6, rev 2, 17/11). PLOT ONLY: reads panel files in the
format of src/figures_v8/export_v8_data.py (results/figures_v8_data/gallery/*.npz and results/a6_figs_data/*.npz)
and never recomputes a result.

Style rev 2 (author 17/11 18:55): every trace black; the EEG inside the annotated seizure is red, so the seizure
stands out; the system's event is a light blue band. The same two colours are used in the score strip below
(annotated seizure light red, event light blue, threshold dashed). One small legend line at the top, no titles.
A missed seizure therefore shows red EEG with no blue band, a false alarm a blue band over black EEG.
Figure 13 mode (keys ch_mark / ch_top): red marks the annotated channels inside the seizure, a dot after the trace
marks the channels ranked highest by the model. ASR mode (key eeg_after): before / after with one shared gain.

Page: the 30 s stored in the panel file (10 s before the seizure onset, or before the event start for a false
alarm); the score strip shows the whole +-5 min with the page marked by two grey lines.

Run:  python src/a6_figs/draw_eeg_figures.py --fig 10 --panels a.npz b.npz --out <dir>
"""
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.lines import Line2D  # noqa: E402
from matplotlib.patches import Patch  # noqa: E402

PRE, POST = 10.0, 20.0
RED, BLUE, BLACK = "#C0392B", "#5DADE2", "#1A1A1A"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})


def load(p):
    z = np.load(p, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    d["fs"] = int(d["fs"])
    for k in ("eeg_t0", "thr", "thr_heldout"):
        d[k] = float(d[k])
    if d["eeg"].shape[0] != 18 or len(d["ch"]) != 18:
        raise SystemExit(f"STOP: {p} does not hold 18 derivations")
    return d


def anchor(d):
    # the 30 s page stored by the exporter: 10 s before the seizure onset (detected or missed seizure) or before
    # the event start (false alarm), the rule of export_v8_data.py / export_a6_panels.py
    return d["eeg_t0"] + PRE


def page(d, eeg):
    c = anchor(d)
    t = d["eeg_t0"] + np.arange(eeg.shape[1]) / d["fs"]
    m = (t >= c - PRE) & (t <= c + POST)
    return c, t, m


def gain_for(eeg, m):
    return 0.5 / (float(np.median(np.percentile(np.abs(eeg[:, m]), 95, axis=1))) or 1.0)


def draw_eeg(ax, d, eeg, gain, show_event=True):
    c, t, m = page(d, eeg)
    in_sz = np.zeros(t.shape, bool)
    for a, b in d["ann"]:
        in_sz |= (t >= a) & (t <= b)
    marked = d.get("ch_mark")
    for i in range(18):
        y = np.clip(eeg[i, m] * gain, -1.4, 1.4) - i
        tt = t[m]
        ax.plot(tt, y, color=BLACK, lw=0.3)
        red = in_sz[m] if marked is None else (in_sz[m] & bool(marked[i]))
        if red.any():
            ax.plot(tt, np.where(red, y, np.nan), color=RED, lw=0.45)
    if show_event:
        for a, b in d["loc"]:
            if b >= c - PRE and a <= c + POST:
                ax.axvspan(max(a, c - PRE), min(b, c + POST), color=BLUE, alpha=0.18, lw=0)
    if "ch_top" in d:
        for i, on in enumerate(d["ch_top"]):
            if on:
                ax.plot([c + POST + 0.6], [-i], "o", ms=3, color=BLACK, clip_on=False)
    ax.set_yticks(-np.arange(18), [str(x) for x in d["ch"]], fontsize=6.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(c - PRE, c + POST)
    ax.set_ylim(-18, 1.2)
    ax.set_xlabel("Time (s)", fontsize=7.5)
    ax.tick_params(axis="x", labelsize=7)


def draw_score(ax, d):
    c, _, _ = page(d, d["eeg"])
    st = d["score_t"]
    for a, b in d["ann"]:
        ax.axvspan(a, b, color=RED, alpha=0.25, lw=0)
    for a, b in d["loc"]:
        ax.axvspan(a, b, color=BLUE, alpha=0.35, lw=0)
    ax.plot(st, d["score_sm"], color=BLACK, lw=0.8)
    ax.axhline(d["thr"], color=BLACK, ls="--", lw=0.7)
    if np.isfinite(d["thr_heldout"]):
        ax.axhline(d["thr_heldout"], color="#7F8C8D", ls=":", lw=0.9)
    ax.axvline(c - PRE, color="#7F8C8D", lw=0.5)
    ax.axvline(c + POST, color="#7F8C8D", lw=0.5)
    ax.set_xlim(st.min(), st.max())
    ax.set_ylim(0, 1.05)
    ax.set_yticks([0, 0.5, 1])
    ax.set_ylabel("Score", fontsize=7.5)
    ax.set_xlabel("Time (s)", fontsize=7.5)
    ax.tick_params(labelsize=7)


def legend(fig, channel_mode=False):
    h = [Line2D([], [], color=RED, lw=1.5), Patch(color=BLUE, alpha=0.35)]
    lab = ["Annotated channel in the seizure" if channel_mode else "Annotated seizure", "Detected by the system"]
    if channel_mode:
        h.append(Line2D([], [], marker="o", color=BLACK, lw=0, ms=4))
        lab.append("Ranked highest by the model")
    fig.legend(h, lab, loc="upper center", ncol=len(h), frameon=False, fontsize=7.5)


def label_columns(fig, axes):
    if len(axes) < 2:
        return
    for j, ax in enumerate(axes):
        x = (ax.get_position().x0 + ax.get_position().x1) / 2
        fig.text(x, 0.012, f"({'abcd'[j]})", ha="center", fontsize=9)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig", required=True)
    ap.add_argument("--panels", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ds = [load(p) for p in a.panels]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)

    if "eeg_after" in ds[0]:                                   # ASR before / after
        d = ds[0]
        eb, ea = d["eeg"].astype(np.float32), d["eeg_after"].astype(np.float32)
        _, _, m = page(d, eb)
        g = gain_for(eb, m)
        fig, axs = plt.subplots(1, 2, figsize=(6.8, 4.2),
                                gridspec_kw=dict(wspace=0.3, left=0.12, right=0.98, top=0.93, bottom=0.17))
        for ax, e in zip(axs, (eb, ea)):
            draw_eeg(ax, d, e, g, show_event=False)
        fig.legend([Line2D([], [], color=RED, lw=1.5)], ["Annotated seizure"], loc="upper center", frameon=False,
                   fontsize=7.5)
        label_columns(fig, axs)
    else:
        n = len(ds)
        channel_mode = "ch_mark" in ds[0]
        fig = plt.figure(figsize=(3.4 * n, 5.3))
        gs = fig.add_gridspec(2, n, height_ratios=[3.6, 1.0], hspace=0.42, wspace=0.32,
                              left=0.09 if n > 1 else 0.17, right=0.98, top=0.93, bottom=0.14)
        eax = []
        for j, d in enumerate(ds):
            e = d["eeg"].astype(np.float32)
            _, _, m = page(d, e)
            ax_e = fig.add_subplot(gs[0, j])
            draw_eeg(ax_e, d, e, gain_for(e, m))
            draw_score(fig.add_subplot(gs[1, j]), d)
            eax.append(ax_e)
        legend(fig, channel_mode)
        label_columns(fig, eax)
    fig.savefig(out / f"Figure{a.fig}.png")
    plt.close(fig)
    print(f"Figure {a.fig} -> {out / f'Figure{a.fig}.png'}")


if __name__ == "__main__":
    main()
