#!/usr/bin/env python
"""
fig14_gallery.py -- Figure 14 "Detected and missed seizures": up to five panels, each = 18-channel EEG
around the event (top) and the ensemble anomaly score over +-5 min (bottom). PLOT ONLY: it reads the
files written by src/figures_v8/export_v8_data.py (Claude Code, docs/prompts/CC_FIGURES_V8.md) and never
recomputes anything (integrity rule 13).

Input  results/figures_v8_data/gallery/{a,b,c,d,e}.npz, each with keys
  eeg          float16 [18, n]   (covers onset-10 s .. onset+20 s) bipolar EEG after the system's filters and z-score (display only)
  fs           int               sampling rate of `eeg` (128)
  eeg_t0       float             time in the file (s) of eeg[:, 0]
  ch           str [18]          derivation names in montage order
  score_t      float [m]         window start times in the file (s), +-5 min around the event
  score        float [m]         ensemble anomaly score (0-1)
  score_sm     float [m]         5-window smoothed score
  thr          float             the patient's threshold of the final system
  thr_heldout  float             threshold of the held-out evaluation (budget 0.005); NaN if not shown
  ann          float [k, 2]      annotated seizures (s in the file), may be empty
  det          float [j, 2]      detector events;  loc  float [j, 2]  localized events
  title        str               short panel title, e.g. "chb03: detected"
Output <out>/figures/fig14_gallery.png (6.3 x up to 9.5 in, 300 dpi)

Run:  python src/figures_v8/fig14_gallery.py [--out ../Reports/v8]        (~5 s)
      python src/figures_v8/fig14_gallery.py --smoke                     (synthetic data, layout check only)
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "results" / "figures_v8_data" / "gallery"
C = dict(det="#E69F00", loc="#009E73", sz="#D55E00", main="#0072B2", grey="#777777", raw="#AAAAAA", eeg="#222222")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})
PRE, POST = 10.0, 20.0    # EEG shown from 10 s before to 20 s after the onset (a 30 s page)
EEG_HALF = 15.0          # half-width used by the synthetic smoke data only


def smoke_panel(seed, title, short=False, fa=False):
    """synthetic, smoothed noise with a 4 Hz burst on 6 channels -- layout check only, never a result."""
    rng = np.random.default_rng(seed)
    fs = 128
    on, off = (1010.0, 1018.0) if short else (1005.0, 1040.0)
    c = (on + off) / 2
    t0 = c - EEG_HALF
    n = int(2 * EEG_HALF * fs)
    w = rng.normal(0, 1, (18, n + 64))
    eeg = np.stack([np.convolve(r, np.hanning(24), "valid")[:n] for r in w])
    eeg = eeg / eeg.std()
    if not fa:
        t = t0 + np.arange(n) / fs
        k = (t >= on) & (t <= off)
        eeg[:6, k] += 3 * np.sin(2 * np.pi * 4 * t[k])
    st = np.arange(c - 300, c + 300, 4.0)
    sc = np.clip(rng.uniform(0.2, 0.8, len(st)) + (0.0 if fa else 0.3) * ((st > on) & (st < off)), 0, 1)
    sm = np.convolve(sc, np.ones(5) / 5, mode="same")
    ann = np.zeros((0, 2)) if fa else np.array([[on, off]])
    det = np.zeros((0, 2)) if short else np.array([[on + 8, off + 4]])
    loc = det - [4, 0] if len(det) else det
    return dict(eeg=eeg.astype(np.float16), fs=fs, eeg_t0=t0, ch=np.array([f"CH{i}" for i in range(18)]),
                score_t=st, score=sc, score_sm=sm, thr=0.9, thr_heldout=0.95 if seed == 2 else np.nan,
                ann=ann, det=det, loc=loc, title=title)


def load(panel):
    p = DATA / f"{panel}.npz"
    if not p.exists():
        return None
    z = np.load(p, allow_pickle=False)
    d = {k: z[k] for k in z.files}
    d["title"] = str(d["title"]); d["fs"] = int(d["fs"])
    for k in ("eeg_t0", "thr", "thr_heldout"):
        d[k] = float(d[k])
    gate = {"eeg": 18, "ch": 18}
    if d["eeg"].shape[0] != gate["eeg"] or len(d["ch"]) != gate["ch"]:
        raise SystemExit(f"STOP: panel {panel} has {d['eeg'].shape[0]} EEG channels")
    return d


def anchor(d):
    """time 0 of a panel = onset of the first annotated seizure, else onset of the first localized/detected event."""
    for k in ("ann", "loc", "det"):
        if len(d[k]):
            return float(d[k][0][0])
    return d["eeg_t0"] + PRE


def draw(ax_e, ax_s, d, lab):
    c = anchor(d)
    fs, t0, eeg = d["fs"], d["eeg_t0"], d["eeg"].astype(np.float32)
    t = t0 + np.arange(eeg.shape[1]) / fs
    m = (t >= c - PRE) & (t <= c + POST)
    for i in range(18):
        ax_e.plot(t[m] - c, np.clip(eeg[i, m], -5, 5) * 0.22 - i, color=C["eeg"], lw=0.3)
    for a, b in d["ann"]:
        ax_e.axvspan(a - c, b - c, color=C["sz"], alpha=0.18, lw=0)
    ax_e.set_yticks(-np.arange(18)[::3], [str(x) for x in d["ch"][::3]], fontsize=5.5)
    ax_e.set_xlim(-PRE, POST); ax_e.set_ylim(-18.5, 1.2)
    ax_e.set_title(f"{lab} {d['title']}", loc="left", fontsize=8)
    ax_e.tick_params(axis="x", labelsize=6)
    st = d["score_t"]
    ax_s.plot(st - c, d["score"], color=C["raw"], lw=0.5)
    ax_s.plot(st - c, d["score_sm"], color=C["main"], lw=0.9)
    ax_s.axhline(d["thr"], color="k", ls="--", lw=0.7)
    if np.isfinite(d["thr_heldout"]):
        ax_s.axhline(d["thr_heldout"], color=C["grey"], ls=":", lw=0.9)
    for a, b in d["ann"]:
        ax_s.axvspan(a - c, b - c, color=C["sz"], alpha=0.25, lw=0)
    for k, y, col in (("det", 1.05, C["det"]), ("loc", 1.12, C["loc"])):
        for a, b in d[k]:
            ax_s.hlines(y, a - c, b - c, color=col, lw=3)
    ax_s.axvspan(-PRE, POST, color="k", alpha=0.04, lw=0)
    ax_s.set_xlim(st.min() - c, st.max() - c); ax_s.set_ylim(0, 1.17); ax_s.set_yticks([0, 0.5, 1])
    ax_s.tick_params(labelsize=6); ax_s.set_ylabel("Score", fontsize=7)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT.parent / "Reports" / "v8"))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        panels = [smoke_panel(1, "detected"), smoke_panel(2, "detected only with the per-patient budget"),
                  smoke_panel(3, "short seizure, missed", short=True), smoke_panel(4, "false alarm", fa=True),
                  smoke_panel(5, "Siena, detected")]
        out = Path(a.out) / "smoke"
    else:
        panels = [p for p in (load(k) for k in "abcde") if p is not None]
        if not panels:
            raise SystemExit("STOP: no gallery data in results/figures_v8_data/gallery/ (run the Claude Code export)")
        out = Path(a.out)
    (out / "figures").mkdir(parents=True, exist_ok=True)
    n = len(panels)
    fig = plt.figure(figsize=(6.3, 1.85 * n + 0.5))
    gs = fig.add_gridspec(n, 2, width_ratios=[1.0, 1.25], wspace=0.28, hspace=0.55)
    for i, (d, lab) in enumerate(zip(panels, "abcde")):
        draw(fig.add_subplot(gs[i, 0]), fig.add_subplot(gs[i, 1]), d, f"({lab})")
    fig.text(0.29, 0.02 + 0.1 / n, "Time from onset (s): EEG, 30 s", ha="center", fontsize=7)
    fig.text(0.74, 0.02 + 0.1 / n, "Time from onset (s): score, ±5 min", ha="center", fontsize=7)
    h = [plt.Line2D([], [], color=C["raw"], lw=1), plt.Line2D([], [], color=C["main"], lw=1),
         plt.Line2D([], [], color="k", ls="--", lw=0.8), plt.Line2D([], [], color=C["grey"], ls=":", lw=0.9),
         plt.Line2D([], [], color=C["det"], lw=3), plt.Line2D([], [], color=C["loc"], lw=3),
         plt.Rectangle((0, 0), 1, 1, color=C["sz"], alpha=0.25)]
    fig.legend(h, ["anomaly score", "smoothed", "threshold (final)", "threshold (held-out)", "detected event",
                   "localized event", "annotated seizure"], loc="lower center", ncol=4, frameon=False, fontsize=6.5)
    fig.subplots_adjust(left=0.1, right=0.98, top=0.97, bottom=0.06 + 0.25 / n)
    fig.savefig(out / "figures" / "fig14_gallery.png"); plt.close(fig)
    print(f"fig14 OK: {n} panels -> {out / 'figures' / 'fig14_gallery.png'}")


if __name__ == "__main__":
    sys.exit(main())
