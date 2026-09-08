"""
fig2_2_seizure_durations.py -- Fig 2.2, Figure Brief Round 2 Task C.

Histogram of annotated seizure durations, log-scale horizontal axis. All 182
seizures across the 23 subjects, with the 76 held-out seizures drawn as a
distinguishable series on the same axes (the brief's own §4 rationale: this
figure sits beside two tables describing the whole corpus, so a histogram of
the held-out subset alone would be an internal inconsistency).

Source: data/summaries/*.txt, parsed with evaluation_protocol.parse_summary_edf_list
(the same parser results/report_tables/table_A1 uses).

Self-check against docs/VERIFIED_NUMBERS.md Part 3, held-out set (n=76):
minimum 6 s, median 45 s, mean 51.9 s, maximum 205 s, 23 shorter than 20 s,
31 shorter than 30 s.
"""
import os as _os, sys as _sys
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

import evaluation_protocol as E
from palette import INTERICTAL, ICTAL, apply_rc

ROOT = Path(_src).parent
SUMMARY_DIR = ROOT / "data" / "summaries"
HELD_OUT = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ALL_SUBJECTS = [f"chb{i:02d}" for i in range(1, 24)]
OUT = ROOT / "figures" / "fig2_2_seizure_durations.png"


def all_durations(subj):
    edfs = E.parse_summary_edf_list(SUMMARY_DIR / f"{subj}-summary.txt")
    return [off - on for e in edfs for (on, off) in e["seizures"]]


def main():
    apply_rc()
    all_dur, held_dur = [], []
    for subj in ALL_SUBJECTS:
        d = all_durations(subj)
        all_dur.extend(d)
        if subj in HELD_OUT:
            held_dur.extend(d)

    all_dur = np.array(all_dur, dtype=float)
    held_dur = np.array(held_dur, dtype=float)
    print(f"[Fig 2.2] all subjects: n={len(all_dur)} (brief: 182)")
    print(f"[Fig 2.2] held-out: n={len(held_dur)} min={held_dur.min():.0f} "
          f"median={np.median(held_dur):.0f} mean={held_dur.mean():.1f} "
          f"max={held_dur.max():.0f} <20s={(held_dur < 20).sum()} <30s={(held_dur < 30).sum()}")

    if len(all_dur) != 182:
        raise ValueError(f"all-subject seizure count = {len(all_dur)}, expected 182 -- stop")
    checks = dict(n=(len(held_dur), 76), minimum=(held_dur.min(), 6),
                  median=(np.median(held_dur), 45), mean=(round(held_dur.mean(), 1), 51.9),
                  maximum=(held_dur.max(), 205), lt20=((held_dur < 20).sum(), 23),
                  lt30=((held_dur < 30).sum(), 31))
    for name, (got, exp) in checks.items():
        if got != exp:
            raise ValueError(f"Fig 2.2 self-check failed: {name}={got}, expected {exp} -- stop")
    print("[Fig 2.2] self-check OK against docs/VERIFIED_NUMBERS.md Part 3")

    bins = np.logspace(np.log10(all_dur.min()), np.log10(all_dur.max()), 24)

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    ax.hist(all_dur, bins=bins, color=INTERICTAL, alpha=0.55, edgecolor="black",
           linewidth=0.4, label=f"All 23 subjects (n={len(all_dur)})")
    ax.hist(held_dur, bins=bins, color=ICTAL, alpha=0.75, edgecolor="black",
           linewidth=0.4, label=f"Held-out subjects (n={len(held_dur)})")

    ax.set_xscale("log")
    ax.axvline(4.0, color="black", ls="--", lw=1.2, label="4 s analysis window")
    n_short = int((held_dur < 20).sum())
    ax.annotate(f"{n_short}/{len(held_dur)} held-out seizures < 20 s",
               xy=(20, ax.get_ylim()[1] * 0.0), xycoords=("data", "axes fraction"),
               xytext=(0.02, 0.92), textcoords="axes fraction", fontsize=9)

    ax.set_xlabel("Seizure duration (s, log scale)")
    ax.set_ylabel("Count")
    ax.legend(fontsize=9, loc="upper right")
    ax.grid(axis="y", alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
