"""
fig3_4_detection_output.py -- Fig 3.4, docs/FIGURE_ROUND4.md §3 ("build by recomputation").

Detection output on one full continuous chb13 recording, recomputed end-to-end (see
continuous_rescore.py). Stacked panels on a shared time axis: the three component scores
(zrecon, zlatent, zgamma), the fused score, detected intervals shaded in the
detected-interval colour, the annotated seizures shaded in the ictal colour.

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
from palette import ICTAL, DETECTED, apply_rc

ROOT = Path(_src).parent
RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUBJ = "chb13"
EDF_NAME = "chb13_62.edf"
MIN_MAG_PCT, PEN_MULT = 50, 2.0   # the reported operating point
OUT = ROOT / "figures" / "fig3_4_detection_output.png"


def main():
    apply_rc()
    calib = CR.fit_calibration()
    result = CR.score_continuous_file(RAW_DIR / SUBJ / EDF_NAME, calib)
    t_min = result["t_seconds"] / 60.0

    events = V14.detect_events(result["fused"], PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                               local_win=15, inter_mask=None)

    edfs = E.parse_summary_edf_list(ROOT / "data" / "summaries" / f"{SUBJ}-summary.txt")
    this = next(e for e in edfs if e["fname"] == EDF_NAME)
    seizures = this["seizures"]

    sc = SE.score_szcore(seizures, events, result["n_windows"] * 4, n_inter_h=1.0)
    print(f"[Fig 3.4] {SUBJ}/{EDF_NAME}: {result['n_windows']} windows recomputed, "
         f"no artifact rejection")
    print(f"[Fig 3.4] detected intervals (onset_s, end_s) at the reported operating point: "
         f"{events}")
    print(f"[Fig 3.4] score vs annotation: tp={sc['tp']} fp={sc['fp']} "
         f"n_ref={sc['n_ref']} n_hyp={sc['n_hyp']}")

    fig, axes = plt.subplots(4, 1, figsize=(11, 10), sharex=True,
                             gridspec_kw={"height_ratios": [1, 1, 1, 1.3]})
    comp_names = [("zrecon", "GAE reconstruction (zrecon)"),
                 ("zlatent", "Latent Mahalanobis (zlatent)"),
                 ("zgamma", "Gamma-band AEC (zgamma)")]
    for ax, (key, label) in zip(axes[:3], comp_names):
        ax.plot(t_min, result[key], color="#4C72B0", lw=0.7)
        ax.set_ylabel(label, fontsize=8.5)

    axes[3].plot(t_min, result["fused"], color="#4C72B0", lw=0.8, label="Fused score")
    axes[3].set_ylabel("Fused score")
    axes[3].set_xlabel("Time (minutes)")

    for ax in axes:
        for i, (onset_s, offset_s) in enumerate(seizures):
            ax.axvspan(onset_s / 60.0, offset_s / 60.0, color=ICTAL, alpha=0.22,
                      label="Annotated seizure" if (i == 0 and ax is axes[3]) else None)
        for i, (a0, a1) in enumerate(events):
            ax.axvspan(a0 / 60.0, a1 / 60.0, color=DETECTED, alpha=0.30,
                      label="Detected interval" if (i == 0 and ax is axes[3]) else None)

    axes[3].legend(fontsize=8, loc="upper right")
    for ax in axes:
        ax.grid(alpha=0.2, lw=0.4)

    fig.tight_layout()
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
