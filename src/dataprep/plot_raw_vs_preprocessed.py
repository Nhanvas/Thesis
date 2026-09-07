"""
plot_raw_vs_preprocessed.py
============================
Illustrative figure: a raw EEG segment vs. the SAME segment after the locked
preprocessing pipeline (bandpass 0.5-60 Hz -> notch 60 Hz -> z-score), reusing
the filter design, `open_edf`, and summary parser DIRECTLY from `preprocessing.py`
so this figure is guaranteed to match what the real pipeline computes (no logic
duplicated). ONE combined figure, 2 stacked panels (Raw / Preprocessed), same
subject / time window / channel. No seizure label is drawn on the plot.

By default the segment is auto-picked to AVOID seizure windows (uses
`preprocessing.parse_summary` + `build_labels`), so the figure demonstrates
general preprocessing quality on ordinary background EEG, not seizure-specific
amplitude. Pass --include_seizure to lift that restriction, or --start to pick
an exact timestamp yourself once you've looked at a subject's data.

Note on scope: Step 3 (CAR) is applied later in graph_construction.py across
the full 18-channel set before wPLI -- it is NOT part of what preprocessing.py
writes to `{subj}_interictal.npy`. So "Preprocessed" here = Steps 1+2+5
(bandpass -> notch -> z-score), matching the saved arrays exactly.

USAGE (run from the folder containing preprocessing.py, or add it to PYTHONPATH)
  python plot_raw_vs_preprocessed.py --subject chb10 --channel "P7-O1"
  python plot_raw_vs_preprocessed.py --subject chb10 --channel "T7-P7" \
      --start 1245.0 --duration 3.0        # manual segment instead of auto-pick
  python plot_raw_vs_preprocessed.py --subject chb03 --channel "F7-T7" \
      --edf chb03_04.edf --duration 4.0

Requires: mne, numpy, scipy, matplotlib (same stack as preprocessing.py).
"""
import argparse
import json
from pathlib import Path

import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import sosfiltfilt, filtfilt

import preprocessing as P   # the locked pipeline module -- single source of truth

plt.rcParams.update({
    "font.family": "serif",
    "font.size": 10,
    "axes.spines.top": False,
    "axes.spines.right": False,
})


def find_denoising_demo_segment(raw, ch_idx, seizure_list, duration_s=1.5,
                                stride_s=0.25, skip_edges_s=30.0,
                                avoid_seizures=True, artifact_thresh_V=None,
                                top_k_candidates=30, flat_frac=0.3,
                                flat_eps_uV=0.5):
    """Pick a `duration_s` window where bandpass+notch filtering visibly
    reduces noise, so 'Raw' vs 'Preprocessed' actually look different --
    NOT simply the window with the single biggest raw amplitude.

    A window with the largest raw peak-to-peak is very often an electrode
    lead-off / saturation artifact: flat near-zero signal, then one huge
    spike as the electrode reconnects. Such broadband transients pass
    through the 0.5-60Hz bandpass almost unchanged in SHAPE (only Step 5's
    linear z-score rescales it), so before/after look identical apart from
    the y-axis units -- exactly what happens if the naive picker is used.
    These windows would ALSO be dropped by the pipeline's own Step-4
    artifact rejection (>5x per-channel SD), so they are not representative
    of what the model ever trains on either.

    Two-stage search:
      1. Cheap scan on RAW samples only: reject windows that overlap a
         seizure (if avoid_seizures), look near-flatline (lead-off), or
         exceed `artifact_thresh_V` (mirrors Step 4 exactly if it was loaded
         from {subj}_stats.json; otherwise a self-calibrated 5xSD proxy).
         Keep the `top_k_candidates` most "active" (highest raw std) survivors.
      2. Among those, actually bandpass+notch-filter each one and keep the
         one where filtering removes the most RELATIVE noise
         (std(raw-filtered) / std(filtered)) -- i.e. the one that will look
         most visibly cleaned up, the same effect the reference figure shows.
    Returns (start_sample, artifact_thresh_V_used).
    """
    n_total = int(raw.n_times)
    n_seconds = n_total // P.FS
    labels = P.build_labels(n_seconds, seizure_list) if avoid_seizures else None
    dur_samp = int(duration_s * P.FS)
    stride_samp = max(1, int(stride_s * P.FS))
    skip = int(skip_edges_s * P.FS)
    data = raw.get_data(picks=[ch_idx])[0]          # Volts

    if artifact_thresh_V is None:
        sample = data[skip: max(skip + 1, n_total - skip): max(1, P.FS)]
        artifact_thresh_V = 5.0 * float(np.std(sample))

    shortlist = []
    for s in range(skip, max(skip + 1, n_total - dur_samp - skip), stride_samp):
        if avoid_seizures:
            s0, s1 = s // P.FS, (s + dur_samp) // P.FS
            if labels[s0:s1].max() == 1:
                continue
        seg = data[s:s + dur_samp]
        ptp = seg.max() - seg.min()
        if ptp > artifact_thresh_V:
            continue                                  # Step-4 would drop this
        d = np.abs(np.diff(seg))
        if (d < flat_eps_uV * 1e-6).mean() > flat_frac:
            continue                                  # near-flatline -> uninformative
        shortlist.append((s, float(seg.std())))

    if not shortlist:
        raise RuntimeError(
            "no clean, non-artifact segment found on this channel/file -- "
            "try another --channel or --edf, loosen the search (larger "
            "--skip_edges is unlikely to help; the channel may be mostly "
            "flat or heavily contaminated), or pass --start manually.")

    shortlist.sort(key=lambda x: -x[1])               # most "active" first
    best_start, best_ratio = shortlist[0][0], -1.0
    for s, _ in shortlist[:top_k_candidates]:
        pad_start = max(0, s - P.FILTER_PAD)
        pad_end = min(n_total, s + dur_samp + P.FILTER_PAD)
        raw_pad = data[pad_start:pad_end]
        bp = sosfiltfilt(P._BP_SOS, raw_pad)
        filt_pad = filtfilt(P._NOTCH_B, P._NOTCH_A, bp)
        off = s - pad_start
        filt_seg = filt_pad[off: off + dur_samp]
        raw_seg = data[s: s + dur_samp]
        ratio = np.std(raw_seg - filt_seg) / (np.std(filt_seg) + 1e-12)
        if ratio > best_ratio:
            best_ratio, best_start = ratio, s

    return best_start, artifact_thresh_V


def load_subject_stats(processed_dir, subject_id, ch_name):
    """Reuse the ALREADY-computed per-channel mean/std (Step 5 params) from
    {subj}_stats.json, so this figure z-scores EXACTLY like the real pipeline.
    Returns (None, None) if the stats file isn't there yet."""
    p = Path(processed_dir) / f"{subject_id}_stats.json"
    if not p.exists():
        return None, None
    stats = json.loads(p.read_text())
    idx = P.COMMON_CHANNELS.index(ch_name)
    return (stats["ch_mean_uV"][idx] * 1e-6,     # back to Volts (MNE units)
            stats["ch_std_uV"][idx] * 1e-6)


def build_figure(raw, seizure_list, subject_id, channel, start_samp, dur_samp,
                 processed_dir, out_path):
    ch_idx = raw.ch_names.index(channel)
    t0 = start_samp / P.FS
    t_axis = t0 + np.arange(dur_samp) / P.FS

    # ---- RAW: exactly as read from the EDF, no processing ----
    raw_uV = raw.get_data(picks=[ch_idx], start=start_samp,
                          stop=start_samp + dur_samp)[0] * 1e6

    # ---- PREPROCESSED: Steps 1+2 (bandpass -> notch, same padding/zero-phase
    #      convention as preprocessing.filter_window) then Step 5 (z-score) ----
    n_total = int(raw.n_times)
    pad_start = max(0, start_samp - P.FILTER_PAD)
    pad_end = min(n_total, start_samp + dur_samp + P.FILTER_PAD)
    seg = raw.get_data(picks=[ch_idx], start=pad_start, stop=pad_end)
    bp = sosfiltfilt(P._BP_SOS, seg, axis=1)
    notched = filtfilt(P._NOTCH_B, P._NOTCH_A, bp, axis=1)
    off = start_samp - pad_start
    filt = notched[0, off: off + dur_samp]          # Volts

    mean_V, std_V = load_subject_stats(processed_dir, subject_id, channel)
    if mean_V is None:
        print(f"[warn] {subject_id}_stats.json not found under {processed_dir} -- "
              f"normalizing from THIS segment only (illustrative fallback, "
              f"not the pipeline's real per-subject stats)")
        mean_V, std_V = filt.mean(), (filt.std() or 1.0)
    z = (filt - mean_V) / std_V

    # ---- ONE combined figure, 2 stacked panels ----
    subj_no = subject_id.replace("chb", "").lstrip("0") or "0"
    fig, axes = plt.subplots(2, 1, figsize=(7, 5.2), sharex=True)

    axes[0].plot(t_axis, raw_uV, color="#1f77b4", lw=0.8)
    axes[0].set_title(f"Raw EEG signal - CH. {channel}, SUBJECT {subj_no}")
    axes[0].set_ylabel("Amplitude (\u00b5V)")

    axes[1].plot(t_axis, z, color="#1f77b4", lw=0.8)
    axes[1].set_title(f"Preprocessed EEG signal - CH. {channel}, SUBJECT {subj_no}")
    axes[1].set_ylabel("Amplitude (z-score)")
    axes[1].set_xlabel("Time (s)")

    fig.tight_layout()
    out_path.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_path, dpi=200, bbox_inches="tight")
    plt.close(fig)
    return out_path


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw_dir", default="F:/Study/Thesis/Dataset/CHB-MIT")
    ap.add_argument("--processed_dir", default="F:/Study/Thesis/Code/data/processed")
    ap.add_argument("--subject", default="chb10")
    ap.add_argument("--edf", default=None, help="EDF filename; default = first file for the subject")
    ap.add_argument("--channel", default="P7-O1", choices=P.COMMON_CHANNELS)
    ap.add_argument("--start", type=float, default=None,
                    help="segment start (s) into the EDF file; omit for auto-pick")
    ap.add_argument("--duration", type=float, default=3.0)
    ap.add_argument("--include_seizure", action="store_true",
                    help="allow the auto-picker to land inside a seizure window (off by default)")
    ap.add_argument("--out", default=None)
    args = ap.parse_args()

    raw_dir = Path(args.raw_dir)
    edf_files = sorted((raw_dir / args.subject).glob("*.edf"))
    if not edf_files:
        raise SystemExit(f"No EDF files found for {args.subject} under {raw_dir}")
    edf_path = (raw_dir / args.subject / args.edf) if args.edf else edf_files[0]
    print(f"[load] {edf_path}")

    summary_path = raw_dir / "CHB info" / "summary" / f"{args.subject}-summary.txt"
    seizure_map = P.parse_summary(summary_path) if summary_path.exists() else {}
    seizure_list = seizure_map.get(edf_path.name, [])

    raw = P.open_edf(edf_path)
    if raw is None:
        raise SystemExit(f"{edf_path.name}: missing one of the 18 common channels")

    dur_samp = int(args.duration * P.FS)
    if args.start is None:
        ch_idx = raw.ch_names.index(args.channel)
        start_samp, _ = find_denoising_demo_segment(raw, ch_idx, seizure_list, args.duration,
                                                    avoid_seizures=not args.include_seizure)
        print(f"[auto] most eventful {args.duration:g}s segment (channel {args.channel}) "
              f"starts at t={start_samp / P.FS:.2f}s")
    else:
        start_samp = int(args.start * P.FS)

    out = Path(args.out) if args.out else Path(
        f"figures/raw_vs_preprocessed_{args.subject}_{args.channel}.png")
    saved = build_figure(raw, seizure_list, args.subject, args.channel,
                         start_samp, dur_samp, args.processed_dir, out)
    print(f"[saved] {saved.resolve()}")


if __name__ == "__main__":
    main()