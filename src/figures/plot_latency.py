"""
================================================================================
 plot_latency.py -- Fig 3.5 detection latency
================================================================================
Histogram of matched-seizure detection latency at the headline operating point.
Source: results/phaseB/tier2/latency/latency_per_seizure.csv, rows where
operating_point == 'val_derived_balanced' and matched == True.

Vertical lines at -30 s and +60 s mark the latency matcher's tolerance window.
The distribution is truncated exactly at -28 s because of that tolerance (4 s
window quantisation on top of the 30 s allowance) -- this is what the figure is
for: showing the negative values come from the matching rule, not detection
before onset (docs/VERIFIED_NUMBERS.md Part 8, item 1).
"""
import argparse
from pathlib import Path
import sys

HEADLINE_MAG_PCT, HEADLINE_PEN_MULT = 50.0, 2.0
ENS_DIR = "results/phaseB/tier2/ens_test_tf/rlg"
SUMMARY_DIR = "data/summaries"

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from timescoring.annotations import Annotation

_here = str(Path(__file__).parent)
_src = str(Path(__file__).parent.parent)
for _p in (_here, _src):
    if _p not in sys.path:
        sys.path.insert(0, _p)
from palette import DETECTED, CHANCE, apply_rc
import szcore_eval as SE
import cpd_pipeline_v14 as V14


def _identify_extra_match(csv_path, grid_csv_path):
    """Read-only diagnostic (docs/VERIFIED_NUMBERS.md Part 8, item 1; Chapter 3 SS3.3.1;
    Chapter 4): the latency procedure's match count exceeds the SzCORE scorer's true-
    positive count by exactly one at every operating point. Identify which seizure that
    is, from committed sources only (latency_per_seizure.csv + the raw grid CSV for the
    subject-level count; committed ens_test_tf/rlg arrays + locked mag50/pen2.0 for the
    per-seizure pinpoint). No retraining, no writes."""
    lat = pd.read_csv(csv_path)
    d = lat[lat.operating_point == "val_derived_balanced"]
    per_subj_matched = d[d.matched == True].groupby("subject").size()

    grid = pd.read_csv(grid_csv_path)
    hd = grid[(np.isclose(grid.mag_pct, HEADLINE_MAG_PCT)) & (np.isclose(grid.pen_mult, HEADLINE_PEN_MULT))]
    per_subj_tp = hd.groupby("subject").tp.sum()

    cmp = pd.concat([per_subj_matched.rename("n_matched"), per_subj_tp.rename("tp")], axis=1).fillna(0)
    cmp["diff"] = cmp.n_matched - cmp.tp
    extra = cmp[cmp["diff"] > 0]
    print(f"[Fig 3.5] per-subject latency-matched vs SzCORE TP: "
         f"{cmp[['n_matched', 'tp']].astype(int).to_dict('index')}")
    if len(extra) != 1:
        print(f"[Fig 3.5] extra match not uniquely attributable to one subject from committed "
             f"aggregates alone: {extra.to_dict('index')} -- stopping identification here.")
        return
    subj = extra.index[0]

    ei = np.load(f"{ENS_DIR}/ens_seed42_{subj}_inter.npy")
    ec = np.load(f"{ENS_DIR}/ens_seed42_{subj}_ictal.npy")
    np.random.seed(0)
    signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
        SE.build_timeline_masked(subj, ei, ec, SUMMARY_DIR)
    ref_iv = [(s * SE.WIN_SEC, e * SE.WIN_SEC) for (s, e) in sz_ranges]
    total_dur_s = len(signal) * SE.WIN_SEC
    cps, _ = V14.detect_changepoints(signal, HEADLINE_PEN_MULT, min_mag_pct=HEADLINE_MAG_PCT,
                                     local_win=15, inter_mask=real_inter)
    hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)

    ref = Annotation(list(ref_iv), 1, max(int(total_dur_s), 1))
    hyp = Annotation(list(hyp_iv), 1, max(int(total_dur_s), 1))
    s = SE.scoring.EventScoring(ref, hyp, SE.SZ_PARAM)
    if len(s.ref.events) != len(ref_iv):
        print(f"[Fig 3.5] {subj}: minDurationBetweenEvents merging changed the reference event "
             f"count ({len(s.ref.events)} vs {len(ref_iv)} raw) -- cannot align per-seizure, "
             f"stopping identification here.")
        return
    extended = SE.scoring.EventScoring._extendEvents(s.ref, SE.SZ_PARAM.toleranceStart,
                                                       SE.SZ_PARAM.toleranceEnd)
    szcore_matched = []
    for (e0, e1) in extended.events:
        rel = (np.sum(s.hyp.mask[round(e0 * s.fs):round(e1 * s.fs)]) / s.fs) / (e1 - e0)
        szcore_matched.append(rel > SE.SZ_PARAM.minOverlap + 1e-6)

    lat_subj = d[(d.subject == subj) & (d.matched == True)].set_index("ref_onset_s")
    for (r0, r1), szc in zip(ref_iv, szcore_matched):
        if r0 in lat_subj.index and not szc:
            print(f"[Fig 3.5] extra match identified: subject={subj}, seizure onset={r0:.0f}s "
                 f"end={r1:.0f}s, latency-procedure latency_s={lat_subj.loc[r0, 'latency_s']:.0f}s "
                 f"(matched by the latency procedure's h0 <= ref_end + {SE.SZ_PARAM.toleranceEnd:g}s "
                 f"containment rule) but NOT a SzCORE true positive (its extended-tolerance window "
                 f"requires strictly positive overlap; a hypothesis starting at/after the window's "
                 f"right edge contributes none) -- a boundary-inclusivity difference between the "
                 f"two independent implementations, not a data error.")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--csv", default="results/phaseB/tier2/latency/latency_per_seizure.csv")
    ap.add_argument("--grid_csv", default="results/phaseB/tier2/rlg_test/final_eval_seed42.csv")
    ap.add_argument("--out_dir", default="figures")
    a = ap.parse_args()

    apply_rc()
    df = pd.read_csv(a.csv)
    d = df[(df.operating_point == "val_derived_balanced") & (df.matched == True)]

    n = len(d)
    lat = d["latency_s"].values
    med = np.median(lat)
    n_neg = int((lat < 0).sum())
    print(f"[Fig 3.5] n={n} (brief: 48), median={med:.1f}s (brief: -4s), "
         f"negative={n_neg}/{n} (brief: 25/48), min={lat.min():.1f}s (brief: truncated at -28s)")
    # n == 48, not TP == 47: the latency procedure is a separate implementation from the
    # SzCORE scoring framework's own matcher and its match count exceeds the true-positive
    # count by exactly one at every operating point -- a disclosed, expected offset, not a
    # bug (docs/VERIFIED_NUMBERS.md Part 8, item 1; thesis Chapter 3 SS3.3.1; Chapter 4).
    if n != 48:
        raise ValueError(f"n={n}, expected 48 (latency-procedure match count, "
                         f"docs/VERIFIED_NUMBERS.md Part 8 item 1) -- stop, do not force")
    if med != -4.0:
        raise ValueError(f"median={med}, expected -4 -- stop")
    if n_neg != 25:
        raise ValueError(f"negative count={n_neg}, expected 25 -- stop")
    if lat.min() != -28.0:
        raise ValueError(f"min={lat.min()}, expected exactly -28 -- stop")

    _identify_extra_match(a.csv, a.grid_csv)

    fig, ax = plt.subplots(figsize=(8, 5.2))
    bin_width = 4  # matches the 4 s window quantisation
    bins = np.arange(lat.min() - bin_width / 2, lat.max() + bin_width, bin_width)
    ax.hist(lat, bins=bins, color=DETECTED, edgecolor="black", linewidth=0.5, alpha=0.85)

    ax.axvline(-30, color=CHANCE, ls="--", lw=1.3, label="-30 s before onset (matching tolerance)")
    ax.axvline(med, color="black", ls="-", lw=1.3, label=f"median = {med:.0f} s")
    ax.plot([], [], " ", label=f"n = {n} matched (latency procedure)")

    ax.set_xlabel("Latency of detected interval relative to annotated onset (s)")
    ax.set_ylabel("Matched seizures")
    ax.legend(fontsize=8, loc="upper right")
    ax.grid(axis="y", alpha=0.25, lw=0.5)

    out_dir = Path(a.out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    fig.savefig(out_dir / "fig3_4_detection_latency.png", dpi=300, bbox_inches="tight")
    plt.close(fig)
    print(f"  [saved] {(out_dir / 'fig3_4_detection_latency.png').resolve()}")


if __name__ == "__main__":
    main()
