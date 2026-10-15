#!/usr/bin/env python
"""
fig1_background_ictal.py -- Figure 1 of the v8 report, "EEG around a seizure".
Replaces the layout of fig1_1_seizure_phases.py: only the two states the thesis uses are shown,
background and ictal, with the annotated onset and offset. No preictal or postictal window is
drawn, because the thesis never uses those states.

Same recording, same seizure, same filtering as before:
  chb11 (validation patient), chb11_82.edf, annotated seizure 298-320 s
  (checked against data/summaries/chb11-summary.txt; STOP on mismatch),
  0.5-60 Hz band-pass + 60 Hz notch (dataprep/preprocessing.py), NOT z-scored, so the scale bar is in uV.

Layout
  top:    one channel (P7-O1), 148-470 s (150 s of background on each side, as before), ictal interval shaded,
          onset and offset marked; two black bars under the trace mark where the excerpts come from
  bottom: two 10 s excerpts, same four channels (FP1-F7, F7-T7, T7-P7, P7-O1), one shared uV scale:
          background (188-198 s, as before) and ictal (middle of the seizure, 304-314 s)

Run (laptop):  python src/figures/fig1_background_ictal.py [--out ../Reports/v8/figures/fig01_eeg_seizure.png]
Smoke (no EEG, synthetic signal, layout only):  python src/figures/fig1_background_ictal.py --smoke --out <png>
Runtime: a few seconds (estimated, not measured).
"""
import argparse
import os as _os
import sys as _sys

_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.transforms as mtransforms

from palette import INTERICTAL, ICTAL, apply_rc

SUBJECT = "chb11"
EDF_NAME = "chb11_82.edf"
ONSET_S = 298.0
OFFSET_S = 320.0
MARGIN_S = 150.0                # background shown on each side (same 148-470 s span as the earlier figure)
BACKGROUND_EXCERPT = (188.0, 198.0)   # the background excerpt of the earlier figure, unchanged
EXCERPT_LEN_S = 10.0
CHANNELS = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1"]   # first four of the 18 common derivations
OVERVIEW_CHANNEL = "P7-O1"
FS = 256
RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY = Path(_src).parent / "data" / "summaries" / f"{SUBJECT}-summary.txt"


def load_real(t0, t1):
    """Band-pass + notch filtered uV signal of CHANNELS (+ overview) for [t0, t1) s, with 3 s padding."""
    from scipy.signal import sosfiltfilt, filtfilt
    import dataprep.preprocessing as P
    assert P.FS == FS
    found = P.parse_summary(SUMMARY).get(EDF_NAME, [])
    if not found or tuple(found[0]) != (ONSET_S, OFFSET_S):
        raise SystemExit(f"STOP: summary gives {found} for {EDF_NAME}, expected ({ONSET_S}, {OFFSET_S})")
    raw = P.open_edf(RAW_DIR / SUBJECT / EDF_NAME)
    if raw is None:
        raise SystemExit("STOP: recording lacks one of the 18 common channels")
    if CHANNELS != list(P.COMMON_CHANNELS[:4]):
        raise SystemExit("STOP: channel order differs from preprocessing.COMMON_CHANNELS")
    s0, s1 = int(round(t0 * FS)), int(round(t1 * FS))
    pad = 3 * FS
    p0, p1 = max(0, s0 - pad), min(int(raw.n_times), s1 + pad)
    if s0 < 0 or s1 > raw.n_times:
        raise SystemExit("STOP: window runs outside the recording")
    out = {}
    for ch in CHANNELS:
        seg = raw.get_data(picks=[raw.ch_names.index(ch)], start=p0, stop=p1)
        seg = filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, seg, axis=1), axis=1)
        out[ch] = seg[0, s0 - p0: s0 - p0 + (s1 - s0)] * 1e6
    return out


def load_smoke(t0, t1):
    rng = np.random.default_rng(0)
    t = np.arange(int(round((t1 - t0) * FS))) / FS + t0
    out = {}
    for k, ch in enumerate(CHANNELS):
        x = 25 * rng.standard_normal(t.size)
        ict = (t >= ONSET_S) & (t < OFFSET_S)
        x[ict] += 120 * np.sin(2 * np.pi * 4 * t[ict] + k)
        out[ch] = x
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../Reports/v8/figures/fig01_eeg_seizure.png")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    apply_rc()
    load = load_smoke if a.smoke else load_real

    t0, t1 = ONSET_S - MARGIN_S, OFFSET_S + MARGIN_S
    sig = load(t0, t1)
    t = t0 + np.arange(sig[OVERVIEW_CHANNEL].size) / FS

    def mid(a_, b_):
        c = (a_ + b_) / 2
        return c - EXCERPT_LEN_S / 2, c + EXCERPT_LEN_S / 2

    excerpts = {"Background": BACKGROUND_EXCERPT, "Ictal": mid(ONSET_S, OFFSET_S)}

    fig = plt.figure(figsize=(12.5, 7.6))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.35], hspace=0.5, wspace=0.08,
                          top=0.92, bottom=0.08, left=0.07, right=0.98)
    ax_top = fig.add_subplot(gs[0, :])
    ax_ex = [fig.add_subplot(gs[1, i]) for i in range(2)]

    # top: min/max envelope per bin (every value drawn is a real sample)
    x = sig[OVERVIEW_CHANNEL]
    edges = np.linspace(0, x.size, 1400 + 1).astype(int)
    tb = t0 + (edges[:-1] + edges[1:]) / 2 / FS
    ax_top.vlines(tb, [x[p:q].min() for p, q in zip(edges[:-1], edges[1:])],
                  [x[p:q].max() for p, q in zip(edges[:-1], edges[1:])], color=INTERICTAL, lw=0.8, zorder=4)
    ax_top.axvspan(ONSET_S, OFFSET_S, color=ICTAL, alpha=0.22, lw=0, zorder=0)
    for b in (ONSET_S, OFFSET_S):
        ax_top.axvline(b, color=ICTAL, ls="--", lw=1.4, zorder=3)
    ax_top.set_xlim(t0, t1)
    y_top = ax_top.get_ylim()[1]
    ax_top.set_ylim(top=y_top * 1.32)
    lab_y = y_top * 1.05
    for name, xc in (("Background", (t0 + ONSET_S) / 2), ("Ictal", (ONSET_S + OFFSET_S) / 2),
                     ("Background", (OFFSET_S + t1) / 2)):
        ax_top.text(xc, lab_y, name, ha="center", va="bottom", fontsize=9,
                    color=(ICTAL if name == "Ictal" else "black"))
    nudge = 3.0
    ax_top.annotate("onset", xy=(ONSET_S, y_top), xytext=(ONSET_S - nudge, y_top * 1.13), ha="right",
                    va="bottom", fontsize=8, color=ICTAL, arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))
    ax_top.annotate("offset", xy=(OFFSET_S, y_top), xytext=(OFFSET_S + nudge, y_top * 1.13), ha="left",
                    va="bottom", fontsize=8, color=ICTAL, arrowprops=dict(arrowstyle="-", color=ICTAL, lw=0.8))
    tr = mtransforms.blended_transform_factory(ax_top.transData, ax_top.transAxes)
    for e0, e1 in excerpts.values():
        ax_top.plot([e0, e1], [0.012, 0.012], transform=tr, color="black", lw=4.0,
                    solid_capstyle="butt", clip_on=False, zorder=5)
    ax_top.set_ylabel(f"{OVERVIEW_CHANNEL} (\u00b5V)")
    ax_top.set_xlabel("Time (s)")

    # bottom: two excerpts, one shared offset and scale bar
    tr_ex = {}
    for name, (e0, e1) in excerpts.items():
        i0 = int(round((e0 - t0) * FS)); i1 = i0 + int(round(EXCERPT_LEN_S * FS))
        tr_ex[name] = np.stack([sig[ch][i0:i1] for ch in CHANNELS])
    allv = np.concatenate(list(tr_ex.values()), axis=1)
    off = 3.0 * np.median(np.std(allv, axis=1))
    bar = round(off / 3.0, -1) or 10.0
    for k, (name, tr_) in enumerate(tr_ex.items()):
        ax = ax_ex[k]
        tl = np.arange(tr_.shape[1]) / FS
        col = ICTAL if name == "Ictal" else INTERICTAL
        for i in range(len(CHANNELS)):
            ax.plot(tl, tr_[len(CHANNELS) - 1 - i] + i * off, color=col, lw=0.7)
        ax.set_title(name, fontsize=10, color=col if name == "Ictal" else "black")
        ax.set_xlim(0, EXCERPT_LEN_S)
        ax.set_ylim(-1.5 * off, (len(CHANNELS) - 1) * off + 1.5 * off)
        ax.set_xlabel("Time (s)")
        if k == 0:
            ax.set_yticks([i * off for i in range(len(CHANNELS))], list(reversed(CHANNELS)), fontsize=8)
            y0, y1 = ax.get_ylim(); bx = 0.3
            by0 = y0 + 0.04 * (y1 - y0)
            ax.plot([bx, bx], [by0, by0 + bar], color="black", lw=1.6, solid_capstyle="butt", zorder=6)
            ax.text(bx + 0.25, by0 + bar / 2, f"{bar:g} \u00b5V", fontsize=8, va="center", ha="left")
        else:
            ax.set_yticks([])

    out = Path(a.out); out.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out, dpi=200, bbox_inches="tight"); plt.close(fig)
    print(f"{'SMOKE ' if a.smoke else ''}saved {out.resolve()}")
    print(f"recording {SUBJECT}/{EDF_NAME}, seizure {ONSET_S:.0f}-{OFFSET_S:.0f} s, overview {t0:.0f}-{t1:.0f} s")
    for name, (e0, e1) in excerpts.items():
        print(f"  excerpt {name}: {e0:.1f}-{e1:.1f} s")
    print(f"  shared scale bar {bar:g} uV")


if __name__ == "__main__":
    main()
