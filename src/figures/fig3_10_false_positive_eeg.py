"""
fig3_10_false_positive_eeg.py -- Fig 3.10, docs/FIGURE_ROUND4.md §3 ("build by
recomputation").

A false positive with the concurrent EEG, on the same recomputed continuous chb13
recording as Fig 2.10 / Fig 3.4. Two stacked panels, shared time axis: the fused score
above, the raw signal below (six channels, labelled amplitude scale). Centred on one
detected-but-unmatched (false-positive) interval with about a minute of context each
side; that interval is shaded. Confirms from the annotation that no seizure overlaps it.

Does NOT import szcore_eval.build_timeline_masked (forbidden for this figure by R4 §3.1).
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import continuous_rescore as CR
import cpd_pipeline_v14 as V14
import szcore_eval as SE
import evaluation_protocol as E
import preprocessing as P
from palette import ICTAL, DETECTED, INTERICTAL, apply_rc

ROOT = Path(_src).parent
RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUBJ = "chb13"
EDF_NAME = "chb13_62.edf"
MIN_MAG_PCT, PEN_MULT = 50, 2.0
CONTEXT_S = 60.0
N_CHANNELS = 6
OUT = ROOT / "figures" / "fig3_10_false_positive_eeg.png"


def main():
    apply_rc()
    calib = CR.fit_calibration()
    result = CR.score_continuous_file(RAW_DIR / SUBJ / EDF_NAME, calib)

    events = V14.detect_events(result["fused"], PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                               local_win=15, inter_mask=None)
    edfs = E.parse_summary_edf_list(ROOT / "data" / "summaries" / f"{SUBJ}-summary.txt")
    this = next(e for e in edfs if e["fname"] == EDF_NAME)
    seizures = this["seizures"]

    sc = SE.score_szcore(seizures, events, result["n_windows"] * 4, n_inter_h=1.0)
    print(f"[Fig 3.10] {SUBJ}/{EDF_NAME}: tp={sc['tp']} fp={sc['fp']} of {sc['n_hyp']} "
         f"detected intervals against {sc['n_ref']} annotated seizures")

    # Identify the false-positive intervals: detected intervals with no overlap, under
    # the SzCORE tolerance (30 s pre / 60 s post), with any annotated seizure -- the
    # same tolerance szcore_eval.score_szcore already applied above, not re-implemented
    # here; this only re-derives WHICH interval was a miss for the caption/selection.
    TOL_PRE, TOL_POST = 30, 60
    fp_events = [ev for ev in events if not any(
        (s0 - TOL_PRE) <= ev[0] <= (s1 + TOL_POST) or (s0 - TOL_PRE) <= ev[1] <= (s1 + TOL_POST)
        for (s0, s1) in seizures)]
    print(f"[Fig 3.10] false-positive intervals (no overlap with any annotated seizure, "
         f"tolerance -30s/+60s): {fp_events}")
    if not fp_events:
        raise SystemExit("Fig 3.10: no false-positive interval found -- stop (brief §3.2)")

    # Prefer a short, isolated FP well clear of any seizure's tolerance window, for a
    # clean +/-60s context view.
    def clearance(ev):
        return min(abs(ev[0] - s1) + abs(ev[1] - s0) for (s0, s1) in seizures)
    fp = max(fp_events, key=clearance)
    fp_on, fp_off = fp
    print(f"[Fig 3.10] chosen false-positive interval: ({fp_on}, {fp_off}) s")

    view_t0 = max(0.0, fp_on - CONTEXT_S)
    view_t1 = min(result["n_windows"] * 4, fp_off + CONTEXT_S)
    print(f"[Fig 3.10] view window: [{view_t0:.0f}, {view_t1:.0f}] s "
         f"(~{CONTEXT_S:.0f}s context each side)")
    overlaps = [(s0, s1) for (s0, s1) in seizures if s0 < fp_off and s1 > fp_on]
    overlaps_msg = overlaps if overlaps else "NONE -- confirmed no seizure overlaps this interval"
    print(f"[Fig 3.10] annotation check: seizures overlapping the false positive "
         f"[{fp_on},{fp_off}]s directly: {overlaps_msg}")

    # ---- panel (a): fused score ----
    t = result["t_seconds"]
    mask = (t >= view_t0) & (t <= view_t1)

    fig, (ax_score, ax_sig) = plt.subplots(2, 1, figsize=(10.5, 8.4),
                                           gridspec_kw={"height_ratios": [1, 1.4]},
                                           sharex=True)
    ax_score.plot(t[mask], result["fused"][mask], color="#4C72B0", lw=1.0)
    ax_score.axvspan(fp_on, fp_off, color=DETECTED, alpha=0.30, label="False-positive interval")
    ax_score.set_ylabel("Fused anomaly score")
    ax_score.legend(fontsize=8, loc="upper right")
    ax_score.grid(alpha=0.2, lw=0.4)

    # ---- panel (b): raw EEG, six channels, concurrent with the score window ----
    raw = P.open_edf(RAW_DIR / SUBJ / EDF_NAME)
    channels = P.COMMON_CHANNELS[:N_CHANNELS]
    ch_idx = [raw.ch_names.index(c) for c in channels]
    s0 = int(view_t0 * P.FS); s1 = int(view_t1 * P.FS)
    seg_uV = raw.get_data(picks=ch_idx, start=s0, stop=s1) * 1e6
    t_axis = view_t0 + np.arange(seg_uV.shape[1]) / P.FS

    offset = 4.0 * np.median(np.std(seg_uV, axis=1))
    for i, ch in enumerate(channels):
        y = seg_uV[N_CHANNELS - 1 - i] + i * offset
        ax_sig.plot(t_axis, y, color=INTERICTAL, lw=0.6)
    ax_sig.set_yticks([i * offset for i in range(N_CHANNELS)])
    ax_sig.set_yticklabels(list(reversed(channels)))
    ax_sig.axvspan(fp_on, fp_off, color=DETECTED, alpha=0.20)
    bar_uv = round(offset / 4.0, -1) or 10.0
    x0, x1 = ax_sig.get_xlim(); y0, y1 = ax_sig.get_ylim()
    bx = x0 + 0.01 * (x1 - x0); by0 = y0 + 0.02 * (y1 - y0); by1 = by0 + bar_uv
    ax_sig.plot([bx, bx], [by0, by1], color="black", lw=1.8, solid_capstyle="butt", clip_on=False)
    ax_sig.text(bx + 0.008 * (x1 - x0), (by0 + by1) / 2, f"{bar_uv:g} µV",
               fontsize=8, va="center", ha="left")
    ax_sig.set_xlabel("Time (s)")
    ax_sig.grid(alpha=0.2, lw=0.4)

    fig.tight_layout()
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")

    print("\n[CAPTION] "
         f"Recording: {SUBJ}/{EDF_NAME}, false-positive interval [{fp_on},{fp_off}] s. "
         "Scores were recomputed on the continuous recording with every window "
         "retained (no artifact rejection), using the study's fitted checkpoint, "
         "z-score statistics, robust-z calibration and latent-space covariance; they "
         "are not the source of any reported number.")


if __name__ == "__main__":
    main()
