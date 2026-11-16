#!/usr/bin/env python
"""fig_per_patient.py -- report figure (chat A6): detection per test patient, held-out vs final system.
Reads the committed per-patient, per-seed counts (localized stage) and plots the four-seed mean with the range
over seeds. Held-out: results/e22_test_oneshot/per_subject_seed.csv; final: results/e23_test_look7/
per_subject_seed.csv (point 'balanced'). Gate: per-patient means reproduce the report's 0.498 and 0.567.
Run: python src/a6_figs/fig_per_patient.py --out <dir>"""
import argparse
from pathlib import Path
import numpy as np, pandas as pd
import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[2]


def table():
    h = pd.read_csv(ROOT / "results/e22_test_oneshot/per_subject_seed.csv")
    f = pd.read_csv(ROOT / "results/e23_test_look7/per_subject_seed.csv")
    f = f[f.point == "balanced"]
    out = {}
    for name, d in (("held-out", h), ("final", f)):
        d = d[d.stage == "localized"].copy()
        d["sens"] = d.tp / d.n_ref
        d["fpd"] = d.fp / d.nonict_h * 24
        out[name] = d
    return out


def main():
    ap = argparse.ArgumentParser(); ap.add_argument("--out", required=True); a = ap.parse_args()
    T = table()
    subj = sorted(T["final"].subject.unique())
    g = {k: v.groupby("subject") for k, v in T.items()}
    for k, want in (("held-out", 0.498), ("final", 0.567)):
        got = T[k].groupby("seed").sens.mean().mean()
        if abs(got - want) > 0.0015:
            raise SystemExit(f"STOP gate: {k} per-patient mean {got:.4f} != report {want}")
    nref = g["final"].n_ref.first()
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 8, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 300})
    fig, axs = plt.subplots(1, 2, figsize=(6.8, 2.6), gridspec_kw=dict(wspace=0.3, left=0.08, right=0.99,
                                                                       bottom=0.27, top=0.86))
    x = np.arange(len(subj)); w = 0.38
    for j, (col, ylab) in enumerate((("sens", "Sensitivity"), ("fpd", "False alarms per day"))):
        ax = axs[j]
        for i, (k, c) in enumerate((("held-out", "#95A5A6"), ("final", "#1F4E9C"))):
            m = g[k][col].mean().reindex(subj); lo = g[k][col].min().reindex(subj); hi = g[k][col].max().reindex(subj)
            ax.bar(x + (i - 0.5) * w, m, w, color=c, label="Held-out" if k == "held-out" else "Final system")
            ax.errorbar(x + (i - 0.5) * w, m, yerr=[m - lo, hi - m], fmt="none", ecolor="black", lw=0.7, capsize=1.5)
        ax.set_xticks(x, [f"{s}\n({nref[s]})" for s in subj], fontsize=7)
        ax.set_ylabel(ylab)
        if col == "sens":
            ax.set_ylim(0, 1.05)
        x0 = (ax.get_position().x0 + ax.get_position().x1) / 2
        fig.text(x0, 0.01, f"({'ab'[j]})", ha="center", fontsize=9)
    h, l = axs[0].get_legend_handles_labels()
    fig.legend(h, l, frameon=False, fontsize=7.5, loc="upper center", ncol=2)
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    fig.savefig(out / "Figure_per_patient.png"); plt.close(fig)
    for k in ("held-out", "final"):
        print(k, {s: round(float(v), 3) for s, v in g[k].sens.mean().items()})


if __name__ == "__main__":
    main()
