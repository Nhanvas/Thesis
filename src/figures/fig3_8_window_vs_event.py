"""
fig3_8_window_vs_event.py -- Fig 3.8, Figure Brief Round 2 Task C.

Scatter, one labelled point per held-out patient. x = window-level
discrimination (AUROC). y = event-level F1 at m50/p2.0. Reference lines at
the across-patient window value (0.805) and the pooled event F1 (0.213),
both read from file, not typed.

chb06 has no F1 at this operating point (sensitivity and precision both
zero, so the harmonic mean is undefined, not zero) -- drawn at zero on the
vertical axis with an explicit annotation that F1 is undefined.

The brief expects chb17 to sit just below BOTH reference lines (0.782,
0.207) rather than in the high-discrimination quadrant, contradicting a
claim elsewhere in the project that places chb17 with the decision-limited
group. That is reported here, not adjusted for.

Sources: results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json and
results/phaseB/tier2/rlg_test/final_eval_seed42.csv at m50/p2.0.
"""
import os as _os, sys as _sys
from pathlib import Path
_here = _os.path.dirname(_os.path.abspath(__file__))
_src = _os.path.dirname(_here)
for _p in (_here, _src):
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from palette import INTERICTAL, ICTAL, CHANCE, HEADLINE, apply_rc

ROOT = Path(_src).parent
WINDOW_JSON = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "rlg" / "window_auroc_seed42.json"
GRID_CSV = ROOT / "results" / "phaseB" / "tier2" / "rlg_test" / "final_eval_seed42.csv"
OUT = ROOT / "figures" / "fig3_8_window_vs_event.png"

HELD_OUT = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
MACRO_WINDOW_AUROC = 0.805     # docs/VERIFIED_NUMBERS.md Part 1.2, macro across 8 subjects
POOLED_EVENT_F1 = 0.213        # docs/VERIFIED_NUMBERS.md Part 1.1, headline m50/p2.0


def main():
    apply_rc()
    window_auroc = json.loads(WINDOW_JSON.read_text())
    macro = round(float(np.mean([window_auroc[s] for s in HELD_OUT])), 3)
    print(f"[Fig 3.8] recomputed macro window AUROC = {macro} (expected {MACRO_WINDOW_AUROC})")
    if macro != MACRO_WINDOW_AUROC:
        raise ValueError(f"Fig 3.8: macro window AUROC {macro} != {MACRO_WINDOW_AUROC} -- stop")

    df = pd.read_csv(GRID_CSV)
    d = df[(np.isclose(df.mag_pct, 50.0)) & (np.isclose(df.pen_mult, 2.0))].set_index("subject")

    tp_all, fp_all, nsz_all = 0, 0, 0
    x_vals, y_vals, undefined = {}, {}, set()
    for subj in HELD_OUT:
        r = d.loc[subj]
        tp, fp, nsz = float(r.tp), float(r.fp), float(r.n_seizures)
        tp_all += tp; fp_all += fp; nsz_all += nsz
        sens = tp / nsz if nsz else float("nan")
        prec = tp / (tp + fp) if (tp + fp) else float("nan")
        x_vals[subj] = window_auroc[subj]
        if (sens + prec) == 0:
            y_vals[subj] = 0.0
            undefined.add(subj)
        else:
            y_vals[subj] = 2 * prec * sens / (prec + sens)

    pooled_f1 = round(2 * (tp_all / (tp_all + fp_all)) * (tp_all / nsz_all) /
                      ((tp_all / (tp_all + fp_all)) + (tp_all / nsz_all)), 3)
    print(f"[Fig 3.8] recomputed pooled event F1 = {pooled_f1} (expected {POOLED_EVENT_F1})")
    if pooled_f1 != POOLED_EVENT_F1:
        raise ValueError(f"Fig 3.8: pooled F1 {pooled_f1} != {POOLED_EVENT_F1} -- stop")

    print("\n[Fig 3.8] per-patient values and quadrant "
          f"(x-ref={MACRO_WINDOW_AUROC}, y-ref={POOLED_EVENT_F1}):")
    for subj in HELD_OUT:
        x, y = x_vals[subj], y_vals[subj]
        hi_x = "high" if x >= MACRO_WINDOW_AUROC else "low"
        hi_y = "high" if y >= POOLED_EVENT_F1 else "low"
        note = " (F1 undefined, drawn at 0)" if subj in undefined else ""
        print(f"  {subj}: window_auroc={x:.4f}  event_f1={'undefined' if subj in undefined else round(y,3)}  "
              f"quadrant=({hi_x} window, {hi_y} event){note}")

    chb17_x, chb17_y = round(x_vals["chb17"], 3), round(y_vals["chb17"], 3)
    print(f"\n[Fig 3.8] chb17: window_auroc={chb17_x}, event_f1={chb17_y} "
          f"(brief expects 0.782, 0.207 -- below both reference lines)")

    fig, ax = plt.subplots(figsize=(8, 6.4))
    for subj in HELD_OUT:
        x, y = x_vals[subj], y_vals[subj]
        color = CHANCE if subj in undefined else ICTAL
        marker = "x" if subj in undefined else "o"
        ax.scatter([x], [y], s=90, color=color, marker=marker, edgecolor="black",
                  linewidth=0.6, zorder=4)
        ax.annotate(subj, (x, y), xytext=(6, 6), textcoords="offset points", fontsize=9)

    ax.annotate("F1 undefined at chb06\n(sensitivity = precision = 0)",
               xy=(x_vals["chb06"], 0.0), xytext=(x_vals["chb06"] + 0.01, 0.09),
               fontsize=8, arrowprops=dict(arrowstyle="-", color=CHANCE, lw=0.8))

    ax.axvline(MACRO_WINDOW_AUROC, color=CHANCE, ls="--", lw=1.1,
              label=f"Across-patient window AUROC ({MACRO_WINDOW_AUROC})")
    ax.axhline(POOLED_EVENT_F1, color=HEADLINE, ls="--", lw=1.1,
              label=f"Pooled event F1 at m50/p2.0 ({POOLED_EVENT_F1})")

    ax.set_xlabel("Window-level discrimination (AUROC)")
    ax.set_ylabel("Event-level F1 (m50/p2.0)")
    # No figure number / descriptive title on the image (brief §1 rule 5).
    ax.legend(fontsize=8, loc="upper left")
    ax.grid(alpha=0.25, lw=0.5)

    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\n[saved] {OUT.resolve()}")


if __name__ == "__main__":
    main()
