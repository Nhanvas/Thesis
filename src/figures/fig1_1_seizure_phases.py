"""
fig1_1_seizure_phases.py -- Fig 1.1, Phases of the EEG signal around a seizure
(Figure Round 7 item 2; rebuilt in Figure Round 8 item 1 -- the single-panel
layout did not work at print size: four channels crammed into 322 s of
256 Hz data render as a solid block with no separable waveform, and the
2.1-3.6x ictal/background amplitude contrast the Round 7 script measured is
real but invisible at that compression.)
================================================================================
Drawn from real data (the project has the recordings), patient chb11, a
validation patient, per the illustration policy (Chapters 1 and 2 illustrate
on validation data; the running example is the only exception).

NEW TWO-ROW LAYOUT (Round 8)
-----------------------------
Top row, full width: a compressed ONE-CHANNEL overview of the same 322 s,
with the four regions shaded and labelled, onset/offset marked, and four
tick brackets beneath it marking where each excerpt below was taken from.
Its job is temporal context, not morphology.

Bottom row: four excerpts, side by side, equal width, 10 s each, same four
channels, one per region, stacked with a shared vertical offset and ONE
shared amplitude scale bar (drawn once, on the leftmost panel) so the four
are directly comparable.

TERMINOLOGY (Round 8): the two background stretches are labelled
`Background`, not `Interictal`. In this thesis "interictal" names the
defined, artifact-rejected training set (4 h excluded after each seizure);
the region shown here either side of this seizure is not that set, so the
figure uses the neutral word instead. `Preictal`, `Ictal` and `Postictal`
are unchanged.

Preictal and postictal remain FIXED WINDOWS this script defines, not
annotated states -- lengths are printed below and must travel into the
caption text verbatim. No prediction horizon and no seizure-occurrence
period: this thesis is post-hoc review triage, not prediction.

Source: the raw EDF recording directly (F:/Study/Thesis/Dataset/CHB-MIT),
bandpass 0.5-60 Hz + 60 Hz notch (preprocessing.py Steps 1-2) but NOT
z-scored, so the vertical scale bar reads in physical units (uV) -- a
display choice for readability, not the z-scored pipeline representation
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
import matplotlib.transforms as mtransforms

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
BACKGROUND_MARGIN_S = 90.0  # background context shown on each side

N_CHANNELS = 4
EXCERPT_LEN_S = 10.0
NEUTRAL_SHADE = "#DDDDDD"  # non-ictal regions: neutral, never coloured as a detection

# Overview channel: of the four left-temporal-chain channels, P7-O1 shows the
# clearest ictal/background amplitude contrast for this seizure (checked in
# Round 7: ictal/background s.d. ratio 3.6x, the highest of the four).
OVERVIEW_CHANNEL = "P7-O1"

RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = Path("F:/Study/Thesis/Code/data/summaries")
OUT = Path("figures/fig1_1_seizure_phases.png")


def _self_check():
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
    bar_x = x0 + 0.06 * (x1 - x0)
    bar_y0 = y0 + 0.04 * (y1 - y0)
    bar_y1 = bar_y0 + bar_value
    ax.plot([bar_x, bar_x], [bar_y0, bar_y1], color="black", lw=1.6,
            solid_capstyle="butt", clip_on=False, zorder=6)
    ax.text(bar_x + 0.05 * (x1 - x0), (bar_y0 + bar_y1) / 2, label,
            fontsize=8, va="center", ha="left")


def _load_channels(raw, ch_names, start_samp, stop_samp):
    """Bandpass + notch filtered signal, in uV, for [start_samp, stop_samp)."""
    n_total = int(raw.n_times)
    pad = 3 * P.FS
    pad_start = max(0, start_samp - pad)
    pad_end = min(n_total, stop_samp + pad)
    off = start_samp - pad_start
    dur_samp = stop_samp - start_samp
    out = np.zeros((len(ch_names), dur_samp))
    for i, ch in enumerate(ch_names):
        ci = raw.ch_names.index(ch)
        seg_padded = raw.get_data(picks=[ci], start=pad_start, stop=pad_end)
        bp = sosfiltfilt(P._BP_SOS, seg_padded, axis=1)
        notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
        out[i] = notched[0, off: off + dur_samp] * 1e6  # uV
    return out


def main():
    _self_check()

    edf_path = RAW_DIR / SUBJECT / EDF_NAME
    raw = P.open_edf(edf_path)
    if raw is None:
        raise SystemExit(f"[STOP] {edf_path}: missing one of the 18 common channels")

    channels = P.COMMON_CHANNELS[:N_CHANNELS]

    preictal_start = ONSET_S - PREICTAL_LEN_S
    background_pre_start = preictal_start - BACKGROUND_MARGIN_S
    postictal_end = OFFSET_S + POSTICTAL_LEN_S
    background_post_end = postictal_end + BACKGROUND_MARGIN_S

    if background_pre_start < 0:
        raise SystemExit("[STOP] chosen windows run before the start of the recording")

    overview_start_samp = int(round(background_pre_start * P.FS))
    overview_stop_samp = int(round(background_post_end * P.FS))
    n_total = int(raw.n_times)
    if overview_stop_samp > n_total:
        raise SystemExit("[STOP] chosen windows run past the end of the recording")

    # ---- excerpt time ranges: the middle EXCERPT_LEN_S of each region ----
    def middle_window(t0, t1, length=EXCERPT_LEN_S):
        c = (t0 + t1) / 2.0
        return c - length / 2.0, c + length / 2.0

    excerpts = {
        "Background": middle_window(background_pre_start, preictal_start),
        "Preictal": middle_window(preictal_start, ONSET_S),
        "Ictal": middle_window(ONSET_S, OFFSET_S),
        "Postictal": middle_window(OFFSET_S, postictal_end),
    }

    # ---- top row: one-channel compressed overview ----
    overview = _load_channels(raw, [OVERVIEW_CHANNEL], overview_start_samp, overview_stop_samp)[0]

    fig = plt.figure(figsize=(12.5, 8.5))
    gs = fig.add_gridspec(2, 4, height_ratios=[1.0, 1.35], hspace=0.55, wspace=0.12,
                          top=0.90, bottom=0.08, left=0.06, right=0.98)
    ax_top = fig.add_subplot(gs[0, :])
    ax_ex = [fig.add_subplot(gs[1, i]) for i in range(4)]

    def shade(ax, t0, t1, color, alpha):
        ax.axvspan(t0, t1, color=color, alpha=alpha, lw=0, zorder=0)

    shade(ax_top, background_pre_start, preictal_start, NEUTRAL_SHADE, 0.6)
    shade(ax_top, preictal_start, ONSET_S, NEUTRAL_SHADE, 0.9)
    shade(ax_top, ONSET_S, OFFSET_S, ICTAL, 0.22)
    shade(ax_top, OFFSET_S, postictal_end, NEUTRAL_SHADE, 0.9)
    shade(ax_top, postictal_end, background_post_end, NEUTRAL_SHADE, 0.6)

    for b in (preictal_start, postictal_end):
        ax_top.axvline(b, color="#888888", ls=":", lw=1.0, zorder=2)
    ax_top.axvline(ONSET_S, color=ICTAL, ls="--", lw=1.4, zorder=3)
    ax_top.axvline(OFFSET_S, color=ICTAL, ls="--", lw=1.4, zorder=3)

    # Envelope rendering (min/max per bin): 322 s at 256 Hz is ~83k true
    # samples across an axis a few hundred pixels wide; every value drawn is
    # a real sample, none interpolated or filtered away.
    N_BINS = 1400
    bin_edges = np.linspace(0, overview.shape[0], N_BINS + 1).astype(int)
    t_bins = background_pre_start + (bin_edges[:-1] + bin_edges[1:]) / 2 / P.FS
    y_min = np.array([overview[a:b].min() for a, b in zip(bin_edges[:-1], bin_edges[1:])])
    y_max = np.array([overview[a:b].max() for a, b in zip(bin_edges[:-1], bin_edges[1:])])
    ax_top.vlines(t_bins, y_min, y_max, color=INTERICTAL, lw=0.8, zorder=4)
    ax_top.set_ylabel(f"{OVERVIEW_CHANNEL} (\u00b5V)")

    y_top = ax_top.get_ylim()[1]
    label_y = y_top * 1.05
    region_labels = [
        ("Background", (background_pre_start + preictal_start) / 2),
        ("Preictal", (preictal_start + ONSET_S) / 2),
        ("Ictal", (ONSET_S + OFFSET_S) / 2),
        ("Postictal", (OFFSET_S + postictal_end) / 2),
        ("Background", (postictal_end + background_post_end) / 2),
    ]
    for name, xc in region_labels:
        ax_top.text(xc, label_y, name, ha="center", va="bottom", fontsize=9,
                    color=(ICTAL if name == "Ictal" else "black"), clip_on=False)

    ax_top.annotate("onset", xy=(ONSET_S, y_top), xytext=(ONSET_S, y_top * 1.20),
                    ha="center", fontsize=7.5, color=ICTAL,
                    arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))
    ax_top.annotate("offset", xy=(OFFSET_S, y_top), xytext=(OFFSET_S, y_top * 1.20),
                    ha="center", fontsize=7.5, color=ICTAL,
                    arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))

    # Brackets beneath the overview marking where each excerpt was taken from.
    trans = mtransforms.blended_transform_factory(ax_top.transData, ax_top.transAxes)
    for name, (t0, t1) in excerpts.items():
        ax_top.plot([t0, t1], [-0.08, -0.08], transform=trans, color="black", lw=4.0,
                    solid_capstyle="butt", clip_on=False, zorder=5)

    ax_top.set_xlim(background_pre_start, background_post_end)
    ax_top.set_ylim(top=y_top * 1.32)
    ax_top.set_xlabel("Time (s)")

    # ---- bottom row: four 10 s excerpts, same four channels, shared scale ----
    excerpt_traces = {}
    for name, (t0, t1) in excerpts.items():
        s0 = int(round(t0 * P.FS))
        s1 = int(round(t1 * P.FS))
        excerpt_traces[name] = _load_channels(raw, channels, s0, s1)

    # One shared offset/scale across all four excerpts and all four channels,
    # so the panels are directly comparable -- printed below for the caption.
    all_vals = np.concatenate([v for v in excerpt_traces.values()], axis=1)
    offset_uv = 3.0 * np.median(np.std(all_vals, axis=1))
    bar_uv = round(offset_uv / 3.0, -1) or 10.0

    for panel_i, (name, (t0, t1)) in enumerate(excerpts.items()):
        ax = ax_ex[panel_i]
        traces = excerpt_traces[name]
        t_local = np.linspace(0, EXCERPT_LEN_S, traces.shape[1])
        for i, ch in enumerate(channels):
            y = traces[N_CHANNELS - 1 - i] + i * offset_uv
            ax.plot(t_local, y, color=(ICTAL if name == "Ictal" else INTERICTAL), lw=0.7)
        ax.set_title(name, fontsize=10,
                    color=(ICTAL if name == "Ictal" else "black"))
        ax.set_xlim(0, EXCERPT_LEN_S)
        ax.set_ylim(-1.5 * offset_uv, (N_CHANNELS - 1) * offset_uv + 1.5 * offset_uv)
        ax.set_xlabel("Time (s)")
        if panel_i == 0:
            ax.set_yticks([i * offset_uv for i in range(N_CHANNELS)])
            ax.set_yticklabels(list(reversed(channels)), fontsize=8)
            _add_scale_bar(ax, bar_uv, f"{bar_uv:g} \u00b5V")
        else:
            ax.set_yticks([])

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)

    print(f"[recording] {SUBJECT}/{EDF_NAME}")
    print(f"[seizure] onset={ONSET_S:.0f}s offset={OFFSET_S:.0f}s "
          f"(duration {OFFSET_S - ONSET_S:.0f}s)")
    print(f"[windows] preictal length = {PREICTAL_LEN_S:.0f}s (fixed, NOT annotated); "
          f"postictal length = {POSTICTAL_LEN_S:.0f}s (fixed, NOT annotated); "
          f"background context margin = {BACKGROUND_MARGIN_S:.0f}s each side")
    print(f"[overview span] {background_pre_start:.0f}s to {background_post_end:.0f}s "
          f"into {EDF_NAME} ({background_post_end - background_pre_start:.0f}s total), "
          f"channel {OVERVIEW_CHANNEL}")
    print(f"[excerpts] {EXCERPT_LEN_S:.0f}s each, one per region, same four channels "
          f"({', '.join(channels)}), sharing ONE amplitude scale bar "
          f"({bar_uv:g} uV, shown on the leftmost panel):")
    for name, (t0, t1) in excerpts.items():
        print(f"    {name}: {t0:.1f}s - {t1:.1f}s")
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
