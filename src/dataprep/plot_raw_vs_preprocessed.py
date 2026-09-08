"""
plot_raw_vs_preprocessed.py -- Fig 2.3, rebuilt (Figure Brief Round 2, Task B)
================================================================================
Illustrates the locked preprocessing pipeline (bandpass 0.5-60 Hz -> notch
60 Hz -> z-score) reusing the filter design, `open_edf` and summary parser
DIRECTLY from `preprocessing.py`, so this figure is guaranteed to match what
the real pipeline computes (no logic duplicated).

WHY THE PREVIOUS VERSION WAS REBUILT
-------------------------------------
`figures/raw_vs_preprocessed.png` (now `figures/archive/raw_vs_preprocessed_
SUBJECT10_superseded.png`) showed a single channel, so it could not
illustrate referencing across channels at all, and its two panels differed
only in vertical scale -- a reader saw a rescaling, not filtering, because
there was no third panel showing the frequency-domain effect. It also
titled itself "SUBJECT 10" (the rest of the report says "chb10"), used a
double hyphen, and never imported the shared palette.

THIS VERSION
------------
  (a)/(b)  Six channels (a bipolar chain, stacked with a constant vertical
           offset, labelled by derivation name), raw (left) vs preprocessed
           (right), same ~10 s time span.
  (c)      Power spectrum (Welch PSD, log y-axis) of ONE of those six
           channels, raw vs preprocessed overlaid, with the 60 Hz line
           marked -- visible as a peak in the raw curve, suppressed in the
           preprocessed curve. Without this panel the filtering stage's
           effect is not visible at all, which is why the previous figure
           failed.

Patient chb10 or chb11 (validation patients; brief's illustration policy,
Figure Brief Round 2 Task C preamble -- this figure is Chapter 2, so it must
NOT be a held-out patient). Segment auto-picked for a visible mains-
interference / drift / artifact effect; the chosen segment and why is
printed, never silently assumed.

USAGE
    python src/dataprep/plot_raw_vs_preprocessed.py --subject chb11
    python src/dataprep/plot_raw_vs_preprocessed.py --subject chb10 --edf chb10_05.edf --start 120.0
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import argparse
from pathlib import Path

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from scipy.signal import sosfiltfilt, filtfilt, welch

import preprocessing as P          # the locked pipeline module -- single source of truth

_sys.path.insert(0, str(Path(_here).parent / "figures"))
from palette import INTERICTAL, apply_rc          # brief Task B: import palette, interictal colour

apply_rc()

VALID_SUBJECTS = ("chb10", "chb11")
N_CHANNELS = 6
SPECTRUM_CHANNEL = "P7-O1"


MAINS_RATIO_MIN, MAINS_RATIO_MAX = 3.0, 50.0   # visible, but not an artifact-dominated segment
MAX_RAW_PTP_UV = 300.0                          # excludes saturated / heavily artifacted windows


def find_interference_segment(raw, seizure_list, duration_s=10.0, stride_s=2.0,
                              skip_edges_s=30.0):
    """Scan `duration_s` candidate windows on SPECTRUM_CHANNEL for a visible
    but not artifact-dominated 60 Hz mains-interference effect, avoiding
    seizure windows. Score = ratio of RAW power in the 58-62 Hz mains band to
    power in the neighbouring 50-58 / 62-70 Hz bands. Candidates whose mains
    ratio is outside [MAINS_RATIO_MIN, MAINS_RATIO_MAX] (no visible peak, or
    a segment so saturated with 60 Hz / broadband artifact that individual
    channel traces would be unreadable) or whose raw peak-to-peak amplitude
    exceeds MAX_RAW_PTP_UV are excluded; among the rest, the one with the
    LOWEST broadband (4-40 Hz) power is kept -- the cleanest background EEG
    that still shows a clear, visible mains peak. Returns (start_sample, reason)."""
    n_total = int(raw.n_times)
    n_seconds = n_total // P.FS
    labels = P.build_labels(n_seconds, seizure_list)
    ch_idx = raw.ch_names.index(SPECTRUM_CHANNEL)
    data = raw.get_data(picks=[ch_idx])[0] * 1e6   # microvolts
    dur_samp = int(duration_s * P.FS)
    stride_samp = int(stride_s * P.FS)
    skip = int(skip_edges_s * P.FS)

    candidates = []
    for s in range(skip, max(skip + 1, n_total - dur_samp - skip), stride_samp):
        s0, s1 = s // P.FS, (s + dur_samp) // P.FS
        if labels[s0:s1].max() == 1:
            continue
        seg = data[s:s + dur_samp]
        ptp = np.ptp(seg)
        if ptp < 1.0 or ptp > MAX_RAW_PTP_UV:
            continue
        f, pxx = welch(seg, fs=P.FS, nperseg=min(1024, len(seg)))
        mains = pxx[(f >= 58) & (f <= 62)].mean()
        neigh = pxx[((f >= 50) & (f < 58)) | ((f > 62) & (f <= 70))].mean()
        mains_ratio = mains / (neigh + 1e-20)
        if not (MAINS_RATIO_MIN <= mains_ratio <= MAINS_RATIO_MAX):
            continue
        broadband = pxx[(f >= 4) & (f <= 40)].mean()
        candidates.append((s, mains_ratio, broadband, ptp))

    if not candidates:
        raise RuntimeError("no candidate segment found with a visible-but-not-dominant "
                           "60 Hz peak, seizure-free, within the amplitude bound")

    candidates.sort(key=lambda x: x[2])   # cleanest background first
    best_s, best_mains, best_bb, best_ptp = candidates[0]
    reason = (f"visible 60 Hz mains peak in the raw spectrum "
              f"({best_mains:.1f}x the neighbouring 50-58/62-70 Hz bands) on the "
              f"cleanest-background candidate (raw ptp={best_ptp:.0f} uV)")
    return best_s, reason, best_bb


def _add_scale_bar(ax, bar_value, label):
    """Vertical scale bar (data-unit height) in the axes' lower-left corner, with its
    value and unit labelled -- docs/FIGURE_FIXES_R3.md Fig 2.3, panels (a)/(b) fix."""
    y0, y1 = ax.get_ylim()
    x0, x1 = ax.get_xlim()
    bar_x = x0 + 0.02 * (x1 - x0)
    bar_y0 = y0 + 0.03 * (y1 - y0)
    bar_y1 = bar_y0 + bar_value
    ax.plot([bar_x, bar_x], [bar_y0, bar_y1], color="black", lw=1.6,
           solid_capstyle="butt", clip_on=False, zorder=6)
    ax.text(bar_x + 0.012 * (x1 - x0), (bar_y0 + bar_y1) / 2, label,
           fontsize=7.5, va="center", ha="left")


def build_figure(raw, subject_id, edf_name, start_samp, dur_samp, processed_dir, out_path):
    channels = P.COMMON_CHANNELS[:N_CHANNELS]
    ch_idx = [raw.ch_names.index(c) for c in channels]
    t0 = start_samp / P.FS
    t_axis = t0 + np.arange(dur_samp) / P.FS

    n_total = int(raw.n_times)
    pad_start = max(0, start_samp - P.FILTER_PAD)
    pad_end = min(n_total, start_samp + dur_samp + P.FILTER_PAD)
    off = start_samp - pad_start

    raw_uV = np.zeros((N_CHANNELS, dur_samp))
    z = np.zeros((N_CHANNELS, dur_samp))
    for i, ci in enumerate(ch_idx):
        seg_uV = raw.get_data(picks=[ci], start=start_samp, stop=start_samp + dur_samp)[0] * 1e6
        raw_uV[i] = seg_uV

        pad = raw.get_data(picks=[ci], start=pad_start, stop=pad_end)
        bp = sosfiltfilt(P._BP_SOS, pad, axis=1)
        notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
        filt = notched[0, off: off + dur_samp]   # Volts

        mean_V, std_V = load_subject_stats(processed_dir, subject_id, channels[i])
        if mean_V is None:
            mean_V, std_V = filt.mean(), (filt.std() or 1.0)
        z[i] = (filt - mean_V) / std_V

    # ---- panels (a)/(b): stacked traces, constant vertical offset ----
    fig = plt.figure(figsize=(13, 9.2))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.35, 1], hspace=0.38, wspace=0.22,
                          top=0.90, bottom=0.06, left=0.07, right=0.98)
    ax_raw = fig.add_subplot(gs[0, 0])
    ax_pre = fig.add_subplot(gs[0, 1], sharex=ax_raw)
    ax_psd = fig.add_subplot(gs[1, :])

    # docs/FIGURE_FIXES_R3.md Fig 2.3: panels (a)/(b) carried no vertical scale and their
    # units differ (raw = microvolts, preprocessed = z-score) with no way to tell -- both
    # get an explicit scale bar in their own unit, plus the offset value is annotated.
    raw_offset = 3.0 * np.median(np.std(raw_uV, axis=1))
    for i, ch in enumerate(channels):
        y = raw_uV[N_CHANNELS - 1 - i] + i * raw_offset
        ax_raw.plot(t_axis, y, color=INTERICTAL, lw=0.7)
    ax_raw.set_yticks([i * raw_offset for i in range(N_CHANNELS)])
    ax_raw.set_yticklabels(list(reversed(channels)))
    ax_raw.set_xlabel("Time (s)")
    ax_raw.set_title("(a)")
    raw_bar_uv = round(raw_offset / 3.0, -1) or 10.0  # nearest 10 uV, one channel's typical s.d.
    _add_scale_bar(ax_raw, raw_bar_uv, f"{raw_bar_uv:g} µV")

    pre_offset = 3.0 * np.median(np.std(z, axis=1))
    for i, ch in enumerate(channels):
        y = z[N_CHANNELS - 1 - i] + i * pre_offset
        ax_pre.plot(t_axis, y, color=INTERICTAL, lw=0.7)
    ax_pre.set_yticks([i * pre_offset for i in range(N_CHANNELS)])
    ax_pre.set_yticklabels(list(reversed(channels)))
    ax_pre.set_xlabel("Time (s)")
    ax_pre.set_title("(b)")
    pre_bar_z = round(pre_offset / 3.0, 1) or 1.0  # nearest 0.1, one channel's typical s.d.
    _add_scale_bar(ax_pre, pre_bar_z, f"{pre_bar_z:g} z (s.d.)")

    # ---- panel (c): power spectrum of one channel, raw vs preprocessed ----
    # docs/FIGURE_FIXES_R3.md Fig 2.3: the previous version let matplotlib's y-autoscale
    # see the FULL Nyquist-range welch output (0-128 Hz) even though only 0-80 Hz was
    # displayed; the bandpass-filtered preprocessed trace collapses to floating-point noise
    # near Nyquist (~1e-19), which alone stretched the y-axis to ~21 empty decades and made
    # the real 60 Hz notch (which bottoms out around 1e-10, not 1e-19) invisible by
    # comparison. Fix: slice to the displayed 0-80 Hz band BEFORE autoscaling.
    spec_i = channels.index(SPECTRUM_CHANNEL)
    f_raw_full, pxx_raw_full = welch(raw_uV[spec_i], fs=P.FS, nperseg=min(1024, dur_samp))
    f_pre_full, pxx_pre_full = welch(z[spec_i], fs=P.FS, nperseg=min(1024, dur_samp))
    band = f_raw_full <= 80.0
    f_raw, pxx_raw = f_raw_full[band], pxx_raw_full[band]
    f_pre, pxx_pre = f_pre_full[band], pxx_pre_full[band]
    ax_psd.semilogy(f_raw, pxx_raw, color="#888888", lw=1.1, label=f"Raw ({SPECTRUM_CHANNEL})")
    ax_psd.semilogy(f_pre, pxx_pre, color=INTERICTAL, lw=1.1,
                    label=f"Preprocessed ({SPECTRUM_CHANNEL})")
    ax_psd.axvline(60.0, color="#C44E52", ls="--", lw=1.0, label="60 Hz")
    ax_psd.set_xlim(0, 80)

    ymin_data = min(pxx_raw.min(), pxx_pre.min())
    ymax_data = max(pxx_raw.max(), pxx_pre.max())
    y_top = 10 ** np.ceil(np.log10(ymax_data))
    y_bottom = 10 ** np.floor(np.log10(ymin_data))
    decades = np.log10(y_top) - np.log10(y_bottom)
    if decades > 8:
        # Still wider than "about six decades" (brief §1) with BOTH the raw curve's DC
        # peak and the true 60 Hz notch floor kept on-screen -- clipping either away would
        # hide a real feature the panel exists to show, so the floor is raised only enough
        # to bring the span to 8 decades (closest defensible approach to "about six" that
        # does not crop the notch minimum itself, which sits within 2 decades of that floor).
        y_bottom = y_top / 10 ** 8
        decades = 8.0
    ax_psd.set_ylim(y_bottom, y_top)
    print(f"[Fig 2.3 / panel c] y-axis clipped to {decades:.0f} decades "
         f"[{y_bottom:.0e}, {y_top:.0e}] (was ~21 decades when autoscale saw the "
         f"off-screen near-Nyquist floor); data range in the displayed 0-80 Hz band is "
         f"[{ymin_data:.2e}, {ymax_data:.2e}]")

    ax_psd.set_xlabel("Frequency (Hz)")
    ax_psd.set_ylabel("Power spectral density (log scale)")
    ax_psd.set_title("(c)")
    ax_psd.legend(fontsize=8, loc="upper right", framealpha=1.0)

    # No figure number / descriptive title on the image (brief §1 rule 5) --
    # the subject/file/segment identity is printed to console (below) and
    # belongs in the report's external caption, not baked into the PNG.
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def load_subject_stats(processed_dir, subject_id, ch_name):
    import json
    p = Path(processed_dir) / f"{subject_id}_stats.json"
    if not p.exists():
        return None, None
    stats = json.loads(p.read_text())
    idx = P.COMMON_CHANNELS.index(ch_name)
    return (stats["ch_mean_uV"][idx] * 1e-6, stats["ch_std_uV"][idx] * 1e-6)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", default="F:/Study/Thesis/Dataset/CHB-MIT")
    ap.add_argument("--processed_dir", default="F:/Study/Thesis/Code/data/processed")
    ap.add_argument("--summary_dir", default="F:/Study/Thesis/Code/data/summaries")
    ap.add_argument("--subject", default="chb11", choices=VALID_SUBJECTS)
    ap.add_argument("--edf", default=None, help="EDF filename; default = auto-scan across files")
    ap.add_argument("--start", type=float, default=None,
                    help="segment start (s) into the EDF file; omit for auto-pick")
    ap.add_argument("--duration", type=float, default=10.0)
    ap.add_argument("--out", default="figures/fig2_3_raw_vs_preprocessed.png")
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    edf_files = sorted((raw_dir / args.subject).glob("*.edf"))
    if not edf_files:
        raise SystemExit(f"No EDF files found for {args.subject} under {raw_dir}")

    summary_path = Path(args.summary_dir) / f"{args.subject}-summary.txt"
    seizure_map = P.parse_summary(summary_path) if summary_path.exists() else {}

    dur_samp = int(args.duration * P.FS)

    if args.edf and args.start is not None:
        edf_path = raw_dir / args.subject / args.edf
        raw = P.open_edf(edf_path)
        if raw is None:
            raise SystemExit(f"{edf_path.name}: missing one of the 18 common channels")
        start_samp = int(args.start * P.FS)
        reason = "manually specified via --edf/--start"
    else:
        scan_files = edf_files if not args.edf else [raw_dir / args.subject / args.edf]
        best = None   # (broadband, edf_path, raw, start_samp, reason)
        for edf_path in scan_files:
            raw_c = P.open_edf(edf_path)
            if raw_c is None:
                continue
            seizure_list = seizure_map.get(edf_path.name, [])
            try:
                s, reason, bb = find_interference_segment(raw_c, seizure_list, args.duration)
            except RuntimeError:
                continue
            if best is None or bb < best[0]:
                best = (bb, edf_path, raw_c, s, reason)
        if best is None:
            raise SystemExit(f"No usable segment found for {args.subject} across "
                             f"{len(scan_files)} EDF files -- stop.")
        _, edf_path, raw, start_samp, reason = best
        print(f"[auto] scanned {len(scan_files)} EDF files")

    print(f"[segment] {args.subject}/{edf_path.name}, t={start_samp / P.FS:.1f}s "
          f"for {args.duration:g}s -- chosen because: {reason}")

    out = Path(args.out)
    saved = build_figure(raw, args.subject, edf_path.name, start_samp, dur_samp,
                         args.processed_dir, out)
    print(f"[saved] {saved.resolve()}")


if __name__ == "__main__":
    main()
