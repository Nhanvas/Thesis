"""D9b coded figures for the defense deck (main pages 17 and 18 of Canva v7, page map rev 10).

Reads only committed result files of github.com/Nhanvas/Thesis (tag v9-final / HEAD 597289a):
  results/v9_x3/sys_sweep.csv            -> fig17_model_comparison.png
  results/v9_v1/part1_descriptors.csv    -> fig18_missed_amplitude.png (thesis system)
  results/v9_final/hard/knn_loo_seizures.csv, gae_cv_seizures.csv (joined on subject, file, onset_s)
Every number printed on a figure is gated against NUMBERS_LOCK.md section 17 (rev 2) before saving.
Usage: python d9b_figs.py <repo_root> <out_dir>
"""
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from scipy.stats import mannwhitneyu

ROOT, OUT = Path(sys.argv[1]), Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)

C_GAE, C_FUS, C_KNN = "#1F6FB2", "#C8641E", "#2F9A78"
C_TXT, C_GRID, C_GREY = "#1E2A38", "#E3E8EF", "#5F6B7A"
C_CAUGHT, C_MISSED = "#1F6FB2", "#DC433A"
plt.rcParams.update({"font.family": "Carlito", "font.size": 15, "axes.edgecolor": "#9AA5B1",
                     "axes.labelcolor": C_TXT, "xtick.color": C_TXT, "ytick.color": C_TXT,
                     "axes.spines.top": False, "axes.spines.right": False})


def gate(name, got, want, tol):
    if abs(got - want) > tol:
        raise SystemExit(f"GATE FAIL {name}: got {got:.4f}, want {want}")
    print(f"gate ok  {name}: {got:.4f} ~ {want}")


# ---------------------------------------------------------------- page 17 (v8): model comparison (24 cases), per-case means
d = pd.read_csv(ROOT / "results/v9_x3/sys_sweep.csv")
assert d.subject.nunique() == 24
d["sens"] = d.tp / d.n_ref
d["fpd"] = d.fp / d.nonict_h * 24
g = d.groupby(["arm", "k_mult"]).agg(sens=("sens", "mean"), fpd=("fpd", "mean")).reset_index()
own = g[g.k_mult == 1.0].set_index("arm")
# per-case means at each arm's own calibrated point (k_mult 1.0); sensitivity = NUMBERS_LOCK 17.3,
# FP/day per-case mean = NUMBERS_LOCK 17c (D9b v8): 28.4 / 17.7 / 22.7
gate("GAE own sens", own.loc["GAE-CV", "sens"], 0.735, 0.0006)
gate("GAE own FP/day (per-case mean)", own.loc["GAE-CV", "fpd"], 28.4, 0.051)
gate("kNN own sens", own.loc["kNN-LOO", "sens"], 0.763, 0.0006)
gate("kNN own FP/day (per-case mean)", own.loc["kNN-LOO", "fpd"], 17.7, 0.051)
gate("GAE+kNN own sens", own.loc["GAE+kNN-CV", "sens"], 0.791, 0.0006)
gate("GAE+kNN own FP/day (per-case mean)", own.loc["GAE+kNN-CV", "fpd"], 22.7, 0.051)

arms = [("GAE-CV", "GAE (thesis model)", C_GAE, "o"),
        ("GAE+kNN-CV", "GAE + kNN", C_FUS, "s"),
        ("kNN-LOO", "kNN on the same channel features", C_KNN, "D")]
fig, ax = plt.subplots(figsize=(10.5, 6.0), dpi=200)
for arm, lab, col, mk in arms:
    s_ = g[g.arm == arm].drop_duplicates(["sens", "fpd"]).sort_values("fpd")
    ax.plot(s_.fpd, s_.sens, color=col, lw=2.4, marker=mk, ms=5, alpha=0.9, label=lab, zorder=3)
    o = own.loc[arm]
    ax.scatter([o.fpd], [o.sens], s=210, marker=mk, facecolor=col, edgecolor="white", lw=2, zorder=5)
offs = {"GAE-CV": (1.2, -0.022), "GAE+kNN-CV": (-1.0, 0.018), "kNN-LOO": (-1.0, -0.030)}
for arm, lab, col, mk in arms:
    o = own.loc[arm]
    dx, dy = offs[arm]
    ax.text(o.fpd + dx, o.sens + dy, f"{o.sens:.3f} at {o.fpd:.1f}", color=col, fontsize=14,
            fontweight="bold", ha="left" if dx > 0 else "right", va="center", zorder=6)
ax.set_xlim(10, 90)
ax.set_ylim(0.66, 0.94)
ax.set_xlabel("False alarms per day (per-case mean)")
ax.set_ylabel("Sensitivity (per-case mean)")
ax.grid(color=C_GRID, lw=0.8)
ax.legend(loc="lower right", frameon=False, fontsize=14)
fig.tight_layout()
fig.savefig(OUT / "fig17_model_comparison.png")
plt.close(fig)
print("wrote fig17_model_comparison.png")

# ---------------------------------------------------------------- page 18 (v8): missed seizures, three detectors
th = pd.read_csv(ROOT / "results/v9_v1/part1_descriptors.csv")
th = th[th.subject.str.startswith("chb")][["subject", "file", "onset_s", "duration_s", "caught", "amp_ratio"]]
assert len(th) == 185, len(th)
desc = th[["subject", "file", "onset_s", "amp_ratio"]].drop_duplicates()
kn = pd.read_csv(ROOT / "results/v9_final/hard/knn_loo_seizures.csv").merge(desc, on=["subject", "file", "onset_s"], how="left")
gc = pd.read_csv(ROOT / "results/v9_final/hard/gae_cv_seizures.csv").merge(desc, on=["subject", "file", "onset_s"], how="left")
assert kn.amp_ratio.notna().all() and gc.amp_ratio.notna().all()
# medians gated at 3 decimals (results/v9_final/hard/SUMMARY.md); labels use NUMBERS_LOCK 17.4 wording
panels = [("Thesis system (GAE)", th, (2.294, 1.288, 115, 70), ("2.29×", "1.29×")),
          ("kNN on the same\nchannel features", kn, (2.147, 1.244, 115, 70), ("2.15×", "1.24×")),
          ("GAE, cross-validated", gc, (2.220, 1.285, 114, 71), ("2.22×", "1.29×"))]
fig, axes = plt.subplots(1, 3, figsize=(11.5, 6.0), dpi=200, sharey=True)
rng = np.random.default_rng(0)
for ax, (title, df, (mc, mm, nc, nm), labs) in zip(axes, panels):
    c, m = df[df.caught.astype(bool)].amp_ratio, df[~df.caught.astype(bool)].amp_ratio
    gate(f"{title!r} caught median", c.median(), mc, 0.0006)
    gate(f"{title!r} missed median", m.median(), mm, 0.0006)
    assert (len(c), len(m)) == (nc, nm), (len(c), len(m))
    p = mannwhitneyu(c, m).pvalue
    assert p < 1e-4, p
    for x, vals, col, lab in [(0, c, C_CAUGHT, labs[0]), (1, m, C_MISSED, labs[1])]:
        ax.scatter(x + rng.uniform(-0.22, 0.22, len(vals)), vals, s=22, color=col, alpha=0.55, lw=0)
        med = vals.median()
        ax.plot([x - 0.3, x + 0.3], [med, med], color=C_TXT, lw=3)
        ax.text(x + 0.33, med, lab, va="center", fontsize=15, fontweight="bold", color=C_TXT)
    ax.set_xticks([0, 1], [f"caught\n(n = {nc})", f"missed\n(n = {nm})"])
    ax.set_xlim(-0.5, 1.75)
    ax.set_title(title, fontsize=15, color=C_TXT)
    ax.text(0.5, 0.97, "p < 0.0001", transform=ax.transAxes, ha="center", va="top", fontsize=13, color=C_GREY)
    ax.grid(axis="y", color=C_GRID, lw=0.8)
axes[0].set_yscale("log")
axes[0].set_ylim(0.4, 25)
axes[0].set_yticks([0.5, 1, 2, 4, 8, 16], ["0.5×", "1×", "2×", "4×", "8×", "16×"])
axes[0].minorticks_off()
axes[0].set_ylabel("Seizure amplitude vs the minute before (RMS ratio)")
fig.tight_layout()
fig.savefig(OUT / "fig18_missed_amplitude.png")
plt.close(fig)
print("wrote fig18_missed_amplitude.png")
print("ALL GATES PASSED")
