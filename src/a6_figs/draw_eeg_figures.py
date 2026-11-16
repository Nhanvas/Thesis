#!/usr/bin/env python
"""
draw_eeg_figures.py -- report figures with real EEG (chat A6, 17/11). PLOT ONLY: reads panel files in the
format of src/figures_v8/export_v8_data.py (results/figures_v8_data/gallery/*.npz and the A6 export
results/a6_figs_data/*.npz) and never recomputes a result.

Style (author 17/11): the EEG as recorded after the system's filters, all 18 derivations named, colour by
chain (left red, right blue, midline green), the annotated seizure as a light band, the system's event as a
bar; below it the anomaly score over +-5 min with the patient's threshold. No titles or legends inside the
figure (the caption explains), panel letters under each column.

Panel file keys: eeg [18, n] (display units), fs, eeg_t0 (s in file), ch [18], score_t, score, score_sm,
thr, thr_heldout (NaN if not shown), ann [k, 2], det [j, 2], loc [j, 2], title (not drawn).

Optional keys: ch_mark bool[18] (annotated channels, bold label), ch_top bool[18] (channels ranked highest by
the model, dot after the trace), eeg_after [18, n] (ASR: the same page after reconstruction -> two EEG columns,
before / after, one shared gain, no score panel).

Run:  python src/a6_figs/draw_eeg_figures.py --fig 9  --panels results/figures_v8_data/gallery/a.npz results/figures_v8_data/gallery/b.npz --out <dir>
      (one column per panel file; output <out>/Figure<fig>.png, 300 dpi)
"""
import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

PRE, POST = 10.0, 20.0          # EEG page: 10 s before to 20 s after the anchor (30 s)
LEFT = {"FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1"}
RIGHT = {"FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2"}
COL = dict(left="#C0392B", right="#1F4E9C", mid="#1E8449", sz="#F5B041", ev="#117A65", sc="#2C3E50")
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
    for k in ("ann", "loc", "det"):
        if len(d[k]):
            return float(d[k][0][0])
    return d["eeg_t0"] + PRE


def chan_colour(name):
    return COL["left"] if name in LEFT else COL["right"] if name in RIGHT else COL["mid"]


def draw_eeg_only(ax, d, eeg, gain):
    c = anchor(d)
    t = d["eeg_t0"] + np.arange(eeg.shape[1]) / d["fs"]
    m = (t >= c - PRE) & (t <= c + POST)
    for i, name in enumerate(d["ch"]):
        ax.plot(t[m], np.clip(eeg[i, m] * gain, -1.4, 1.4) - i, color=chan_colour(str(name)), lw=0.28)
    for a, b in d["ann"]:
        ax.axvspan(max(a, c - PRE), min(b, c + POST), color=COL["sz"], alpha=0.22, lw=0)
    ax.set_yticks(-np.arange(18), [str(x) for x in d["ch"]], fontsize=6.5)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlim(c - PRE, c + POST); ax.set_ylim(-18, 1.2)
    ax.set_xlabel("Time (s)", fontsize=7.5); ax.tick_params(axis="x", labelsize=7)


def draw_before_after(d, out, fig_id):
    """ASR panels: key eeg_after holds the same page after artifact subspace reconstruction; both
    columns share one gain (set on the signal before ASR) so the loss of amplitude is visible."""
    eb, ea = d["eeg"].astype(np.float32), d["eeg_after"].astype(np.float32)
    c = anchor(d); t = d["eeg_t0"] + np.arange(eb.shape[1]) / d["fs"]
    m = (t >= c - PRE) & (t <= c + POST)
    gain = 0.5 / (float(np.median(np.percentile(np.abs(eb[:, m]), 95, axis=1))) or 1.0)
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 4.2), gridspec_kw=dict(wspace=0.3, left=0.12, right=0.98,
                                                                       top=0.98, bottom=0.17))
    for ax, e in zip(axs, (eb, ea)):
        draw_eeg_only(ax, d, e, gain)
    for j, ax in enumerate(axs):
        x = (ax.get_position().x0 + ax.get_position().x1) / 2
        fig.text(x, 0.015, f"({'ab'[j]})", ha="center", fontsize=9)
    fig.savefig(out / f"Figure{fig_id}.png"); plt.close(fig)


def draw_column(ax_e, ax_s, d):
    c = anchor(d)
    eeg = d["eeg"].astype(np.float32)
    t = d["eeg_t0"] + np.arange(eeg.shape[1]) / d["fs"]
    m = (t >= c - PRE) & (t <= c + POST)
    # one gain per panel: the median over channels of the 95th percentile of |EEG| on the page fills
    # about half the spacing, so both background and seizure stay readable (same gain for every channel)
    amp = float(np.median(np.percentile(np.abs(eeg[:, m]), 95, axis=1))) or 1.0
    gain = 0.5 / amp
    for i, name in enumerate(d["ch"]):
        ax_e.plot(t[m], np.clip(eeg[i, m] * gain, -1.4, 1.4) - i, color=chan_colour(str(name)), lw=0.28)
    for a, b in d["ann"]:
        ax_e.axvspan(max(a, c - PRE), min(b, c + POST), color=COL["sz"], alpha=0.22, lw=0)
    for a, b in d["loc"]:
        if b >= c - PRE and a <= c + POST:
            ax_e.hlines(1.0, max(a, c - PRE), min(b, c + POST), color=COL["ev"], lw=4)
    ax_e.set_yticks(-np.arange(18), [str(x) for x in d["ch"]], fontsize=6.5)
    if "ch_mark" in d:                      # annotated channels: bold label
        for lab, on in zip(ax_e.get_yticklabels(), d["ch_mark"]):
            lab.set_fontweight("bold" if on else "normal")
    if "ch_top" in d:                       # channels ranked highest by the model: dot after the trace
        for i, on in enumerate(d["ch_top"]):
            if on:
                ax_e.plot([c + POST + 0.6], [-i], "o", ms=3.2, color="black", clip_on=False)
    ax_e.tick_params(axis="y", length=0)
    ax_e.spines["left"].set_visible(False)
    ax_e.set_xlim(c - PRE, c + POST)
    ax_e.set_ylim(-18, 1.6)
    ax_e.set_xlabel("Time (s)", fontsize=7.5)
    ax_e.tick_params(axis="x", labelsize=7)

    st = d["score_t"]
    ax_s.plot(st, d["score_sm"], color=COL["sc"], lw=0.9)
    ax_s.axhline(d["thr"], color="black", ls="--", lw=0.8)
    if np.isfinite(d["thr_heldout"]):
        ax_s.axhline(d["thr_heldout"], color="#7F8C8D", ls=":", lw=1.0)
    for a, b in d["ann"]:
        ax_s.axvspan(a, b, color=COL["sz"], alpha=0.35, lw=0)
    for a, b in d["loc"]:
        ax_s.hlines(1.08, a, b, color=COL["ev"], lw=3)
    ax_s.axvspan(c - PRE, c + POST, color="black", alpha=0.06, lw=0)
    ax_s.set_xlim(st.min(), st.max())
    ax_s.set_ylim(0, 1.15)
    ax_s.set_yticks([0, 0.5, 1])
    ax_s.set_ylabel("Score", fontsize=7.5)
    ax_s.set_xlabel("Time (s)", fontsize=7.5)
    ax_s.tick_params(labelsize=7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--fig", required=True)
    ap.add_argument("--panels", nargs="+", required=True)
    ap.add_argument("--out", required=True)
    a = ap.parse_args()
    ds = [load(p) for p in a.panels]
    out = Path(a.out)
    out.mkdir(parents=True, exist_ok=True)
    if "eeg_after" in ds[0]:
        draw_before_after(ds[0], out, a.fig)
        print(f"Figure {a.fig}: before / after -> {out / f'Figure{a.fig}.png'}")
        return
    n = len(ds)
    fig = plt.figure(figsize=(3.4 * n, 5.2))
    gs = fig.add_gridspec(2, n, height_ratios=[3.6, 1.0], hspace=0.42, wspace=0.32,
                          left=0.09 if n > 1 else 0.17, right=0.98, top=0.98, bottom=0.14)
    for j, d in enumerate(ds):
        draw_column(fig.add_subplot(gs[0, j]), fig.add_subplot(gs[1, j]), d)
        if n > 1:
            x = (gs[1, j].get_position(fig).x0 + gs[1, j].get_position(fig).x1) / 2
            fig.text(x, 0.015, f"({'abcd'[j]})", ha="center", fontsize=9)
    fig.savefig(out / f"Figure{a.fig}.png")
    plt.close(fig)
    print(f"Figure {a.fig}: {n} panel(s) -> {out / f'Figure{a.fig}.png'}")


if __name__ == "__main__":
    main()
