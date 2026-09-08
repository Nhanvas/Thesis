"""
fig2_10_changepoint_detection.py -- Fig 2.10, docs/FIGURE_ROUND4.md §3 ("build by
recomputation").

Fused anomaly score against time in minutes, for one continuous chb13 recording,
recomputed end-to-end (see continuous_rescore.py) rather than read from the committed
score arrays -- those are segment-ordered, half-substituted with bootstrap-resampled
values, and drift by the number of artifact-rejected windows, so they cannot support a
real time axis. Detected change points (cpd_pipeline_v14.detect_changepoints, locked
defaults, "at the reported operating point") as vertical lines; the annotated seizure
shaded in the ictal colour.

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
import evaluation_protocol as E
from palette import ICTAL, DETECTED, apply_rc

ROOT = Path(_src).parent
RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUBJ = "chb13"
EDF_NAME = "chb13_62.edf"
MIN_MAG_PCT, PEN_MULT = 50, 2.0   # the reported operating point
OUT = ROOT / "figures" / "fig2_10_changepoint_detection.png"


def main():
    apply_rc()
    calib = CR.fit_calibration()
    result = CR.score_continuous_file(RAW_DIR / SUBJ / EDF_NAME, calib)
    fused = result["fused"]
    t_min = result["t_seconds"] / 60.0

    cps, smoothed = V14.detect_changepoints(fused, PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                                            local_win=15, inter_mask=None)
    cp_seconds = sorted(c * V14.WIN_SEC_DEFAULT for c in cps)

    edfs = E.parse_summary_edf_list(ROOT / "data" / "summaries" / f"{SUBJ}-summary.txt")
    this = next(e for e in edfs if e["fname"] == EDF_NAME)
    seizures = this["seizures"]   # chb13_62.edf carries three annotated seizures

    print(f"[Fig 2.10] {SUBJ}/{EDF_NAME}: {result['n_windows']} windows recomputed, "
         f"no artifact rejection")
    print(f"[Fig 2.10] change points detected at the reported operating point "
         f"(min_mag_pct={MIN_MAG_PCT}, pen_mult={PEN_MULT}): {len(cp_seconds)}")
    print(f"[Fig 2.10] change point times (s): {cp_seconds}")
    print(f"[Fig 2.10] annotated seizures (onset_s, offset_s): {seizures}")

    fig, ax = plt.subplots(figsize=(11, 5.2))
    ax.plot(t_min, fused, color="#4C72B0", lw=0.8, label="Fused anomaly score (recomputed)")
    for i, (onset_s, offset_s) in enumerate(seizures):
        ax.axvspan(onset_s / 60.0, offset_s / 60.0, color=ICTAL, alpha=0.25,
                  label="Annotated seizure" if i == 0 else None)
    for i, cs in enumerate(cp_seconds):
        ax.axvline(cs / 60.0, color=DETECTED, lw=1.1, ls="--",
                  label="Detected change point" if i == 0 else None)

    ax.set_xlabel("Time (minutes)")
    ax.set_ylabel("Fused anomaly score")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(alpha=0.25, lw=0.5)
    # No figure number / descriptive title inside the image (standing rule); caption text
    # for the report is printed below, not baked into the PNG.
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")

    print("\n[CAPTION] "
         f"Recording: {SUBJ}/{EDF_NAME}. Scores were recomputed on the continuous "
         "recording with every window retained (no artifact rejection), using the "
         "study's fitted checkpoint, z-score statistics, robust-z calibration and "
         "latent-space covariance; they are not the source of any reported number.")


if __name__ == "__main__":
    main()
