#!/usr/bin/env python
"""fig1b_eeg_onset_offset.py -- report Figure 1b (chat A7, 18/11): scalp EEG around one seizure, the 18 bipolar
derivations in black with the annotated onset and offset as red vertical lines.

Selection rule (fixed before drawing): the seizure of the submitted report's Figure 1, chb11 (validation patient),
chb11_82.edf, annotated 298-320 s in chb11-summary.txt (STOP if the summary says otherwise); shown from 20 s before
the onset to 20 s after the offset. Same filtering as the pipeline (0.5-60 Hz band-pass + 60 Hz notch, zero-phase,
3 s padding); not z-scored, so the scale bar is in uV. Style of src/a6_figs/draw_eeg_figures.py rev 2.

Run (laptop, raw EEG):   python src/a6_figs/fig1b_eeg_onset_offset.py
Smoke (no EEG):          python src/a6_figs/fig1b_eeg_onset_offset.py --smoke --out <png>
Runtime: a few seconds (one EDF of 1 h is opened, 70 s of signal are read).
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SRC = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(SRC))

SUBJECT, EDF_NAME = "chb11", "chb11_82.edf"
ONSET_S, OFFSET_S = 298.0, 320.0
PRE, POST = 20.0, 20.0
FS = 256
RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY = SRC.parent / "data" / "summaries" / f"{SUBJECT}-summary.txt"
OUT = Path("F:/Study/Thesis/Reports/A6_figures/Figure1b_eeg_onset_offset.png")
RED, BLACK = "#C0392B", "#1A1A1A"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})
CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4",
      "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]


def load_real(t0, t1):
    from scipy.signal import sosfiltfilt, filtfilt
    import dataprep.preprocessing as P
    if P.FS != FS or list(P.COMMON_CHANNELS) != CH:
        raise SystemExit("STOP: sampling rate or channel order differs from dataprep/preprocessing.py")
    found = P.parse_summary(SUMMARY).get(EDF_NAME, [])
    if not found or tuple(map(float, found[0])) != (ONSET_S, OFFSET_S):
        raise SystemExit(f"STOP: summary gives {found} for {EDF_NAME}, expected ({ONSET_S}, {OFFSET_S})")
    raw = P.open_edf(RAW_DIR / SUBJECT / EDF_NAME)
    if raw is None:
        raise SystemExit("STOP: recording lacks one of the 18 common channels")
    s0, s1 = int(round(t0 * FS)), int(round(t1 * FS))
    if s0 < 0 or s1 > raw.n_times:
        raise SystemExit("STOP: window runs outside the recording")
    pad = 3 * FS
    p0, p1 = max(0, s0 - pad), min(int(raw.n_times), s1 + pad)
    seg = raw.get_data(start=p0, stop=p1)
    seg = filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, seg, axis=1), axis=1)
    return seg[:, s0 - p0: s0 - p0 + (s1 - s0)] * 1e6


def load_smoke(t0, t1):
    rng = np.random.default_rng(0)
    t = t0 + np.arange(int(round((t1 - t0) * FS))) / FS
    x = 25 * rng.standard_normal((18, t.size))
    ict = (t >= ONSET_S) & (t < OFFSET_S)
    x[:, ict] += 150 * np.sin(2 * np.pi * 3 * t[ict])[None, :]
    return x


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(OUT))
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    t0, t1 = ONSET_S - PRE, OFFSET_S + POST
    eeg = (load_smoke if a.smoke else load_real)(t0, t1)
    t = t0 + np.arange(eeg.shape[1]) / FS
    bg = (t < ONSET_S) | (t >= OFFSET_S)
    p95 = float(np.median(np.percentile(np.abs(eeg[:, bg]), 95, axis=1))) or 1.0
    gain = 0.3 / p95                           # one shared gain: background fills about a third of a row
    fig, ax = plt.subplots(figsize=(4.6, 4.0))
    fig.subplots_adjust(left=0.15, right=0.88, top=0.92, bottom=0.11)
    for i in range(18):
        ax.plot(t, np.clip(eeg[i] * gain, -1.2, 1.2) - i, color=BLACK, lw=0.3)
    for x, name in ((ONSET_S, "Onset"), (OFFSET_S, "Offset")):
        ax.axvline(x, color=RED, lw=1.2, zorder=5)
        ax.text(x, 1.35, name, color=RED, ha="center", va="bottom", fontsize=8)
    ax.set_yticks(-np.arange(18), CH, fontsize=6.5)
    ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False)
    ax.set_xlim(t0, t1)
    ax.set_ylim(-18, 1.3)
    ax.set_xlabel("Time (s)", fontsize=7.5)
    ax.tick_params(axis="x", labelsize=7)
    bar = float(np.round(1.0 / gain, -1)) or 10.0      # scale bar of about one row
    xb = t1 + 1.0
    ax.plot([xb, xb], [-17.5, -17.5 + bar * gain], color=BLACK, lw=1.4, clip_on=False, solid_capstyle="butt")
    ax.text(xb + 0.6, -17.5 + bar * gain / 2, f"{bar:g} \u00b5V", fontsize=6.5, va="center", ha="left",
            clip_on=False)
    out = Path(a.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out)
    plt.close(fig)
    print(f"{'SMOKE ' if a.smoke else ''}saved {out}")
    print(f"{SUBJECT}/{EDF_NAME}: seizure {ONSET_S:.0f}-{OFFSET_S:.0f} s, shown {t0:.0f}-{t1:.0f} s, "
          f"scale bar {bar:g} uV")


if __name__ == "__main__":
    main()
