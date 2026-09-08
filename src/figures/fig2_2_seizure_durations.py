"""
fig2_2_seizure_durations.py -- Fig 2.2, Figure Brief Round 2 Task C, redrawn per
docs/FIGURE_FIXES_R3.md §1 ("Fig 2.2 -- the overlay cannot be read").

Histogram of annotated seizure durations, log-scale horizontal axis. All 182 seizures across
the 23 subjects, drawn as a STACKED histogram: held-out subjects at the bottom, training and
validation subjects stacked above, summing to 182 in every bin. The two series were previously
drawn overlaid with transparency, which made it impossible to tell whether the held-out set was
a subset of the 182 (it is) or a separate group, and in at least one bin the held-out bar
appeared to exceed the total -- an artefact of the overlay, not the data.

Source: data/summaries/*.txt, parsed with evaluation_protocol.parse_summary_edf_list
(the same parser tables/csv/table_A1 uses).

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
    all_dur, held_dur, other_dur = [], [], []
    for subj in ALL_SUBJECTS:
        d = all_durations(subj)
        all_dur.extend(d)
        if subj in HELD_OUT:
            held_dur.extend(d)
        else:
            other_dur.extend(d)

    all_dur = np.array(all_dur, dtype=float)
    held_dur = np.array(held_dur, dtype=float)
    other_dur = np.array(other_dur, dtype=float)
    print(f"[Fig 2.2] all subjects: n={len(all_dur)} (brief: 182)")
    print(f"[Fig 2.2] held-out: n={len(held_dur)}, training+validation: n={len(other_dur)} "
          f"(legend states both counts, {len(held_dur)} and {len(other_dur)})")
    print(f"[Fig 2.2] held-out: min={held_dur.min():.0f} "
          f"median={np.median(held_dur):.0f} mean={held_dur.mean():.1f} "
          f"max={held_dur.max():.0f} <20s={(held_dur < 20).sum()} <30s={(held_dur < 30).sum()}")

    if len(all_dur) != 182:
        raise ValueError(f"all-subject seizure count = {len(all_dur)}, expected 182 -- stop")
    if len(held_dur) + len(other_dur) != len(all_dur):
        raise ValueError("Fig 2.2: held-out + training/validation counts do not sum to the "
                         "all-subject total -- stop")
    checks = dict(n=(len(held_dur), 76), minimum=(held_dur.min(), 6),
                  median=(np.median(held_dur), 45), mean=(round(held_dur.mean(), 1), 51.9),
                  maximum=(held_dur.max(), 205), lt20=((held_dur < 20).sum(), 23),
                  lt30=((held_dur < 30).sum(), 31))
    for name, (got, exp) in checks.items():
        if got != exp:
            raise ValueError(f"Fig 2.2 self-check failed: {name}={got}, expected {exp} -- stop")
    print("[Fig 2.2] self-check OK against docs/VERIFIED_NUMBERS.md Part 3")

    # Clip the horizontal (log) axis to the data range -- docs/FIGURE_FIXES_R3.md §1:
    # bins span exactly [min(all_dur), max(all_dur)], and xlim is pinned explicitly rather
    # than left to matplotlib's default padding, which was letting the axis run past 500 s
    # when the true maximum is 205 s.
    bins = np.logspace(np.log10(all_dur.min()), np.log10(all_dur.max()), 24)

    fig, ax = plt.subplots(figsize=(8.5, 5.4))
    ax.hist([held_dur, other_dur], bins=bins, stacked=True,
           color=[ICTAL, INTERICTAL], edgecolor="black", linewidth=0.4,
           label=[f"Held-out subjects (n={len(held_dur)})",
                  f"Training + validation subjects (n={len(other_dur)})"])

    ax.set_xscale("log")
    # docs/FIGURE_ROUND5.md §6: the axis previously started at all_dur.min()*0.9 = 5.4 s,
    # so the "4 s analysis window" legend entry fell outside the plotted range and never
    # appeared -- a meaningful reference (the shortest annotated seizure is barely longer
    # than one and a half analysis windows) silently dropped. Lower limit extended to
    # 3.5 s so the line is drawn; upper limit clipped to just past the longest seizure
    # (205 s) rather than the previous *1.1 padding, which ran well past the last bar.
    ax.set_xlim(3.5, 215.0)
    ax.axvline(4.0, color="black", ls="--", lw=1.2, label="4 s analysis window")
    n_short = int((held_dur < 20).sum())
    # Moved clear of the 4 s line (docs/FIGURE_FIXES_R3.md §1): the previous placement sat
    # at the top-left corner, overlapping the 4 s vertical line near the left edge of a
    # log-scale axis whose data starts at 6 s. Placed instead near the top-right, away from
    # both the 4 s line and the bin at 20 s it describes.
    ax.annotate(f"{n_short}/{len(held_dur)} held-out seizures < 20 s",
               xy=(0.98, 0.92), xycoords="axes fraction", ha="right", fontsize=9)

    ax.set_xlabel("Seizure duration (s, log scale)")
    ax.set_ylabel("Count")
    ax.legend(fontsize=9, loc="upper left")
    ax.grid(axis="y", alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
