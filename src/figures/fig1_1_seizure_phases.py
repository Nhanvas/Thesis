"""
fig1_1_seizure_phases.py -- Fig 1.1, Phases of the EEG signal around a seizure
(Figure Round 7, item 2)
================================================================================
Previously listed as an adaptation of a published source (FIGURE_WORK_HANDOFF.md
§5). It is not one any more: the project has the recordings, so this figure is
drawn from real data instead.

Patient chb11, a validation patient, per the illustration policy (Chapters 1
and 2 illustrate on validation data; the running example is the only
exception).

Four labelled regions on a shared time axis, one continuous stretch spanning
one seizure:

    interictal | preictal | ICTAL | postictal | interictal

The corpus provides onset and offset only -- preictal and postictal are FIXED
WINDOWS this script defines, not annotated states. Their lengths are printed
below and must travel into the caption verbatim. This is not a prediction
figure: no forecasting horizon or occurrence period is drawn, and the
preictal region carries no meaning beyond "the fixed window the literature's
vocabulary calls preictal."

Source: the raw EDF recording directly (F:/Study/Thesis/Dataset/CHB-MIT),
bandpass 0.5-60 Hz + 60 Hz notch (preprocessing.py Steps 1-2) but NOT
z-scored, so the vertical scale bar reads in physical units (uV) -- this is
a display choice for readability, not the z-scored pipeline representation
used for scoring.

USAGE
    python src/figures/fig1_1_seizure_phases.py
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from pathlib import Path

import numpy as np
from scipy.signal import sosfiltfilt, filtfilt

import dataprep.preprocessing as P
from palette import INTERICTAL, ICTAL, apply_rc

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

apply_rc()

SUBJECT = "chb11"
EDF_NAME = "chb11_82.edf"
ONSET_S = 298.0
OFFSET_S = 320.0

PREICTAL_LEN_S = 60.0     # fixed window immediately before onset -- NOT annotated
POSTICTAL_LEN_S = 60.0    # fixed window immediately after offset -- NOT annotated
INTERICTAL_MARGIN_S = 90.0  # interictal context shown on each side

N_CHANNELS = 4
NEUTRAL_SHADE = "#DDDDDD"  # non-ictal regions: neutral, never coloured as a detection

RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = Path("F:/Study/Thesis/Code/data/summaries")
OUT = Path("figures/fig1_1_seizure_phases.png")


def _self_check():
    """Confirm the hard-coded onset/offset against the committed summary file --
    stop rather than draw a value that disagrees with the corpus record."""
    summary_path = SUMMARY_DIR / f"{SUBJECT}-summary.txt"
    seizures = P.parse_summary(summary_path)
    found = seizures.get(EDF_NAME, [])
    if not found:
        raise SystemExit(f"[STOP] {EDF_NAME} has no seizure recorded in {summary_path}")
    onset, offset = found[0]
    if onset != ONSET_S or offset != OFFSET_S:
        raise SystemExit(
            f"[STOP] committed summary gives onset={onset}, offset={offset} for "
            f"{EDF_NAME}, disagreeing with the hard-coded {ONSET_S}/{OFFSET_S}"
        )
    print(f"[self-check] {SUBJECT}/{EDF_NAME} seizure onset={onset}s offset={offset}s "
          f"-- matches data/summaries/{SUBJECT}-summary.txt")


def _add_scale_bar(ax, bar_value, label):
    y0, y1 = ax.get_ylim()
    x0, x1 = ax.get_xlim()
    bar_x = x0 + 0.015 * (x1 - x0)
    bar_y0 = y0 + 0.04 * (y1 - y0)
    bar_y1 = bar_y0 + bar_value
    ax.plot([bar_x, bar_x], [bar_y0, bar_y1], color="black", lw=1.6,
            solid_capstyle="butt", clip_on=False, zorder=6)
    ax.text(bar_x + 0.01 * (x1 - x0), (bar_y0 + bar_y1) / 2, label,
            fontsize=8, va="center", ha="left")


def main():
    _self_check()

    edf_path = RAW_DIR / SUBJECT / EDF_NAME
    raw = P.open_edf(edf_path)
    if raw is None:
        raise SystemExit(f"[STOP] {edf_path}: missing one of the 18 common channels")

    # Left-temporal chain: this seizure's amplitude contrast between ictal and
    # interictal is clearest here (ictal/interictal channel s.d. ratio 2.1-3.6x,
    # checked against the other three bipolar chains and the central pair
    # before choosing).
    channels = P.COMMON_CHANNELS[:N_CHANNELS]
    ch_idx = [raw.ch_names.index(c) for c in channels]

    preictal_start = ONSET_S - PREICTAL_LEN_S
    interictal_pre_start = preictal_start - INTERICTAL_MARGIN_S
    postictal_end = OFFSET_S + POSTICTAL_LEN_S
    interictal_post_end = postictal_end + INTERICTAL_MARGIN_S

    if interictal_pre_start < 0:
        raise SystemExit("[STOP] chosen windows run before the start of the recording")

    start_samp = int(round(interictal_pre_start * P.FS))
    stop_samp = int(round(interictal_post_end * P.FS))
    n_total = int(raw.n_times)
    if stop_samp > n_total:
        raise SystemExit("[STOP] chosen windows run past the end of the recording")

    pad = 3 * P.FS
    pad_start = max(0, start_samp - pad)
    pad_end = min(n_total, stop_samp + pad)
    off = start_samp - pad_start
    dur_samp = stop_samp - start_samp

    traces = np.zeros((N_CHANNELS, dur_samp))
    for i, ci in enumerate(ch_idx):
        seg_padded = raw.get_data(picks=[ci], start=pad_start, stop=pad_end)
        bp = sosfiltfilt(P._BP_SOS, seg_padded, axis=1)
        notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
        traces[i] = notched[0, off: off + dur_samp] * 1e6  # uV

    fig, ax = plt.subplots(figsize=(11, 6.2))

    # ---- region shading (drawn first, behind the traces) ----
    def shade(t0, t1, color, alpha):
        ax.axvspan(t0, t1, color=color, alpha=alpha, lw=0, zorder=0)

    shade(interictal_pre_start, preictal_start, NEUTRAL_SHADE, 0.6)
    shade(preictal_start, ONSET_S, NEUTRAL_SHADE, 0.9)
    shade(ONSET_S, OFFSET_S, ICTAL, 0.22)
    shade(OFFSET_S, postictal_end, NEUTRAL_SHADE, 0.9)
    shade(postictal_end, interictal_post_end, NEUTRAL_SHADE, 0.6)

    # ---- boundary lines ----
    for b in (preictal_start, OFFSET_S + POSTICTAL_LEN_S):
        ax.axvline(b, color="#888888", ls=":", lw=1.0, zorder=2)
    ax.axvline(ONSET_S, color=ICTAL, ls="--", lw=1.4, zorder=3)
    ax.axvline(OFFSET_S, color=ICTAL, ls="--", lw=1.4, zorder=3)

    # ---- traces ----
    # The 322 s span at 256 Hz crams ~83k true samples per channel into an axis
    # a few hundred pixels wide; a plain line plot renders as a solid smear
    # rather than a readable trace. Bin into per-pixel-scale windows and draw
    # each bin's true min-to-max range as a vertical segment (the standard
    # envelope rendering for a time-compressed EEG strip) -- every value drawn
    # is a real sample, none are interpolated or filtered away.
    N_BINS = 1600
    bin_edges = np.linspace(0, traces.shape[1], N_BINS + 1).astype(int)
    t_bins = interictal_pre_start + (bin_edges[:-1] + bin_edges[1:]) / 2 / P.FS

    offset_uv = 3.0 * np.median(np.std(traces, axis=1))
    for i, ch in enumerate(channels):
        y = traces[N_CHANNELS - 1 - i] + i * offset_uv
        y_min = np.array([y[a:b].min() for a, b in zip(bin_edges[:-1], bin_edges[1:])])
        y_max = np.array([y[a:b].max() for a, b in zip(bin_edges[:-1], bin_edges[1:])])
        ax.vlines(t_bins, y_min, y_max, color=INTERICTAL, lw=0.8, zorder=4)
    ax.set_yticks([i * offset_uv for i in range(N_CHANNELS)])
    ax.set_yticklabels(list(reversed(channels)))

    bar_uv = round(offset_uv / 3.0, -1) or 10.0
    _add_scale_bar(ax, bar_uv, f"{bar_uv:g} \u00b5V")

    # ---- region labels above the trace ----
    y_top = ax.get_ylim()[1]
    label_y = y_top * 1.04
    regions = [
        ("Interictal", (interictal_pre_start + preictal_start) / 2),
        ("Preictal", (preictal_start + ONSET_S) / 2),
        ("Ictal", (ONSET_S + OFFSET_S) / 2),
        ("Postictal", (OFFSET_S + postictal_end) / 2),
        ("Interictal", (postictal_end + interictal_post_end) / 2),
    ]
    for name, xc in regions:
        ax.text(xc, label_y, name, ha="center", va="bottom", fontsize=9,
                color=(ICTAL if name == "Ictal" else "black"), clip_on=False)

    ax.annotate("onset", xy=(ONSET_S, y_top), xytext=(ONSET_S, y_top * 1.14),
                ha="center", fontsize=7.5, color=ICTAL,
                arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))
    ax.annotate("offset", xy=(OFFSET_S, y_top), xytext=(OFFSET_S, y_top * 1.14),
                ha="center", fontsize=7.5, color=ICTAL,
                arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))

    ax.set_xlim(interictal_pre_start, interictal_post_end)
    ax.set_ylim(top=y_top * 1.22)
    ax.set_xlabel("Time (s)")

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"[recording] {SUBJECT}/{EDF_NAME}")
    print(f"[seizure] onset={ONSET_S:.0f}s offset={OFFSET_S:.0f}s "
          f"(duration {OFFSET_S - ONSET_S:.0f}s)")
    print(f"[windows] preictal length = {PREICTAL_LEN_S:.0f}s (fixed, NOT annotated); "
          f"postictal length = {POSTICTAL_LEN_S:.0f}s (fixed, NOT annotated); "
          f"interictal context margin = {INTERICTAL_MARGIN_S:.0f}s each side")
    print(f"[time span shown] {interictal_pre_start:.0f}s to {interictal_post_end:.0f}s "
          f"into {EDF_NAME} ({interictal_post_end - interictal_pre_start:.0f}s total)")
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
