"""
fig2_10_changepoint_detection.py -- Fig 2.10, docs/FIGURE_ROUND4.md §3 ("build by
recomputation"), rebuilt as a zoom per docs/FIGURE_ROUND5.md §3.

Fused anomaly score against time in minutes, for one continuous chb13 recording,
recomputed end-to-end (see continuous_rescore.py) rather than read from the committed
score arrays -- those are segment-ordered, half-substituted with bootstrap-resampled
values, and drift by the number of artifact-rejected windows, so they cannot support a
real time axis. Detected change points (cpd_pipeline_v14.detect_changepoints, locked
defaults, "at the reported operating point") as vertical lines; the annotated seizure
shaded in the ictal colour.

docs/FIGURE_ROUND5.md §3: this figure previously showed the same full hour as the bottom
panel of Fig 3.4, differing only in vertical lines vs. shaded bands -- two chapters
printing almost the same picture. Fig 2.10 sits in the methodology chapter and exists to
show what change-point detection DOES, so it is now a ~5 minute zoom centred on one
annotated seizure of the same recording (the mechanism -- pre-shift level, the shift,
the bracketing change points -- is legible at this scale in a way the full hour is not).
Fig 3.4 keeps the full hour.

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
ZOOM_SEIZURE_IDX = 0              # which of chb13_62.edf's three seizures to zoom on
ZOOM_WINDOW_S = 300.0             # ~5 minutes, centred on that seizure's midpoint
OUT = ROOT / "figures" / "fig2_10_changepoint_detection.png"


def main():
    apply_rc()
    calib = CR.fit_calibration()
    result = CR.score_continuous_file(RAW_DIR / SUBJ / EDF_NAME, calib)
    fused = result["fused"]
    t_seconds = result["t_seconds"]

    cps, smoothed = V14.detect_changepoints(fused, PEN_MULT, min_mag_pct=MIN_MAG_PCT,
                                            local_win=15, inter_mask=None)
    cp_seconds = sorted(c * V14.WIN_SEC_DEFAULT for c in cps)

    edfs = E.parse_summary_edf_list(ROOT / "data" / "summaries" / f"{SUBJ}-summary.txt")
    this = next(e for e in edfs if e["fname"] == EDF_NAME)
    seizures = this["seizures"]   # chb13_62.edf carries three annotated seizures

    onset_s, offset_s = seizures[ZOOM_SEIZURE_IDX]
    mid = (onset_s + offset_s) / 2.0
    view_t0 = max(0.0, mid - ZOOM_WINDOW_S / 2.0)
    view_t1 = min(result["n_windows"] * 4, mid + ZOOM_WINDOW_S / 2.0)

    print(f"[Fig 2.10] {SUBJ}/{EDF_NAME}: {result['n_windows']} windows recomputed, "
         f"no artifact rejection")
    print(f"[Fig 2.10] change points detected at the reported operating point over the "
         f"FULL recording (min_mag_pct={MIN_MAG_PCT}, pen_mult={PEN_MULT}): "
         f"{len(cp_seconds)} -- {cp_seconds}")
    print(f"[Fig 2.10] annotated seizures (onset_s, offset_s): {seizures}")
    print(f"[Fig 2.10] zoomed on seizure index {ZOOM_SEIZURE_IDX} "
         f"(onset={onset_s}s, offset={offset_s}s); view window "
         f"[{view_t0:.0f}, {view_t1:.0f}] s (~{ZOOM_WINDOW_S:.0f}s)")
    cp_in_view = [c for c in cp_seconds if view_t0 <= c <= view_t1]
    print(f"[Fig 2.10] change points inside the zoom window: {cp_in_view}")

    mask = (t_seconds >= view_t0) & (t_seconds <= view_t1)
    t_s_view = t_seconds[mask]
    fused_view = fused[mask]

    fig, ax = plt.subplots(figsize=(9.5, 5.0))
    ax.plot(t_s_view, fused_view, color="#4C72B0", lw=1.0, label="Fused anomaly score")
    ax.axvspan(onset_s, offset_s, color=ICTAL, alpha=0.25, label="Annotated seizure")
    for i, cs in enumerate(cp_in_view):
        ax.axvline(cs, color=DETECTED, lw=1.3, ls="--",
                  label="Detected change point" if i == 0 else None)

    ax.set_xlim(view_t0, view_t1)
    ax.set_xlabel("Time (s)")
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
         f"Recording: {SUBJ}/{EDF_NAME}, zoomed to a ~5 minute window "
         f"[{view_t0:.0f}, {view_t1:.0f}] s centred on the annotated seizure at "
         f"[{onset_s},{offset_s}] s. Scores were recomputed on the continuous "
         "recording with every window retained (no artifact rejection), using the "
         "study's fitted checkpoint, z-score statistics, robust-z calibration and "
         "latent-space covariance; they are not the source of any reported number.")


if __name__ == "__main__":
    main()
