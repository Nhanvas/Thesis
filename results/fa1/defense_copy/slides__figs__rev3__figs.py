#!/usr/bin/env python
"""figs.py -- defense-slide figures in the REPORT's figure style (rev 3 pilot).

Reads committed result files of github.com/Nhanvas/Thesis only (integrity rule 13); nothing recomputed
from EEG or score caches. Style constants are imported from src/figures_v8/make_v8_exhibits.py so the
slides look like the report's figures. Every figure has a gate against NUMBERS_LOCK values.

  P15_test_per_patient.png  seizures detected and false alarms per day per test patient,
                            held-out vs final (test-informed), seed 42, after the localizer
                            (results/e22_test_oneshot/per_subject_seed.csv, results/e23_test_look7/...)
  P13_gae_loss.png          GAE v2 training / validation loss per epoch, 4 seeds
                            (data/models_v2/gae_v2_clean_seed{42,1,2,3}_loss.npz; seed-42 checkpoint
                            sha256 6e3103...c590f = the frozen model)

Run: python figs.py --repo /home/claude/repo --out /home/claude/slidegen/out
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch

ap = argparse.ArgumentParser()
ap.add_argument("--repo", required=True)
ap.add_argument("--out", required=True)
a = ap.parse_args()
REPO = Path(a.repo)
OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(REPO / "src" / "figures_v8"))
import make_v8_exhibits as M  # noqa: E402  (style + constants of the report)

C = M.C
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 16, "axes.labelsize": 16, "xtick.labelsize": 15, "ytick.labelsize": 15,
                     "legend.fontsize": 15})


def gate(cond, msg):
    if not cond:
        raise SystemExit(f"STOP (gate): {msg}")


# ---------------------------------------------------------------- P15 per test patient
e22 = pd.read_csv(REPO / "results/e22_test_oneshot/per_subject_seed.csv")
e23 = pd.read_csv(REPO / "results/e23_test_look7/per_subject_seed.csv")
h = e22[(e22.seed == "clean_seed42") & (e22.stage == "localized")].set_index("subject")
f = e23[(e23.point == "balanced") & (e23.seed == "clean_seed42") & (e23.stage == "localized")].set_index("subject")
T = M.TEST
h, f = h.loc[T], f.loc[T]
gate(h.tp.sum() == 26 and h.fp.sum() == 257 and h.n_ref.sum() == 76, "held-out totals != 26/76, 257 FA")
gate(f.tp.sum() == 37 and f.fp.sum() == 318, "final totals != 37/76, 318 FA")
fpd_h = h.fp / h.nonict_h * 24
fpd_f = f.fp / f.nonict_h * 24
gate(abs(h.fp.sum() / h.nonict_h.sum() * 24 - 22.2) < 0.05, "held-out FP/day != 22.2")
gate(abs(f.fp.sum() / f.nonict_h.sum() * 24 - 27.5) < 0.05, "final FP/day != 27.5")
gate(abs(fpd_f["chb15"] - 32.3) < 0.05 and abs(fpd_h["chb15"] - 8.5) < 0.05, "chb15 FP/day != 8.5 / 32.3")

fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(9.0, 6.4), sharex=True,
                               gridspec_kw=dict(height_ratios=[1.35, 1], hspace=0.12))
x = np.arange(len(T)); w = 0.34
ax1.bar(x, h.n_ref, 0.8, color=C["miss"], label="annotated seizures", zorder=1)
ax1.bar(x - w / 2, h.tp, w, color=C["grey"], label="detected, held-out evaluation", zorder=2)
ax1.bar(x + w / 2, f.tp, w, color=C["main"], label="detected, final system (test-informed)", zorder=2)
for i, s in enumerate(T):
    ax1.text(i, h.n_ref[s] + (1.6 if s == "chb15" else 0.4), f"{int(h.tp[s])} → {int(f.tp[s])} / {int(h.n_ref[s])}"
             if h.tp[s] != f.tp[s] else f"{int(f.tp[s])} / {int(h.n_ref[s])}",
             ha="center", va="bottom", fontsize=14.5, color="#C62828" if s == "chb15" else "black")
ax1.set_ylabel("Seizures")
ax1.set_ylim(0, 24)
fig.legend(loc="upper center", bbox_to_anchor=(0.5, 1.02), frameon=False, ncol=2, fontsize=15)
ax2.bar(x - w / 2, fpd_h, w, color=C["grey"])
ax2.bar(x + w / 2, fpd_f, w, color=C["main"])
ax2.set_ylabel("False alarms\nper day")
ax2.set_xticks(x, T)
ax2.set_ylim(0, 40)
# highlight chb15 (the only patient that changed in detections) -- red box over both panels
i15 = T.index("chb15")
for ax, top in ((ax1, 21.0), (ax2, 39)):
    ax.add_patch(FancyBboxPatch((i15 - 0.46, 0.2), 0.92, top - 0.4, boxstyle="round,pad=0.02",
                                fill=False, ec="#C62828", lw=2.4, zorder=5, clip_on=False))
fig.savefig(OUT / "P15_test_per_patient.png", dpi=200, bbox_inches="tight")
plt.close(fig)

# ---------------------------------------------------------------- P13 GAE loss curves
fig, ax = plt.subplots(figsize=(8.0, 4.4))
for k, s in enumerate([42, 1, 2, 3]):
    d = np.load(REPO / f"data/models_v2/gae_v2_clean_seed{s}_loss.npz")
    tr, va = d["train"], d["val"]
    gate(len(tr) == 200 and len(va) == 200, f"seed {s}: not 200 epochs")
    ep = np.arange(1, 201)
    ax.plot(ep, tr, color=C["main"], lw=2.0 if s == 42 else 1.0, alpha=1 if s == 42 else 0.6,
            label="training (12 patients)" if k == 0 else None)
    ax.plot(ep, va, color=C["det"], lw=2.0 if s == 42 else 1.0, alpha=1 if s == 42 else 0.6,
            label="validation (3 patients)" if k == 0 else None)
ax.set_xlabel("Epoch")
ax.set_ylabel("Training loss")
ax.set_xlim(0, 200)
ax.legend(frameon=False, loc="upper right")
fig.savefig(OUT / "P13_gae_loss.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print("ALL GATES PASSED")
