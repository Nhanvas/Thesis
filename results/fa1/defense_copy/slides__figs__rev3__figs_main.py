#!/usr/bin/env python
"""figs_main.py -- slide-size versions of the result figures, report style (rev 3).

Reads committed files of github.com/Nhanvas/Thesis only; recomputes nothing from EEG or score caches.
Each figure has a gate against the numbers of record (NUMBERS_LOCK). Fonts are large (16 pt base) because
every figure is shown at 800-1000 px on a 1920 x 1080 slide.

  P11_example.png      one detected seizure, chb03 (report Fig. 14a data: results/figures_v8_data/gallery/a.npz)
  P13_sparsity.png     graph density and seizure-background separation (report Fig. 11 data)
  P14_development.png  (a) normal reference, (b) contribution of each component (report Tables 6, 9)
  P16_boundaries.png   onset / offset error, detector vs localizer (report Fig. 13 data)
  P17_siena.png        Siena per patient: detected / seizures and false alarms per day (Table 15 data)
  P18_channel.png      channel ranking AUROC per test patient: model vs anatomical prior (Table 24 data)
  P20_budget.png       alarm budget needed per test seizure (report Fig. 16 data)
  P20_duration.png     detection by seizure duration (report Fig. 12 data)
Run: python figs_main.py --repo /home/claude/repo --out out
"""
import argparse
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
R = Path(a.repo); OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(R / "src" / "figures_v8"))
import make_v8_exhibits as M  # noqa: E402
C, TEST = M.C, M.TEST
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 16, "axes.labelsize": 16, "xtick.labelsize": 15, "ytick.labelsize": 15,
                     "legend.fontsize": 15, "axes.titlesize": 16})
RED = "#C62828"


def gate(c, m):
    if not c:
        raise SystemExit("STOP (gate): " + m)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight"); plt.close(fig)


# ---------------------------------------------------------------- P11 detection example (chb03)
g = np.load(R / "results/figures_v8_data/gallery/a.npz", allow_pickle=True)
gate(str(g["title"]).startswith("chb03") and tuple(g["ann"][0]) == (360.0, 416.0), "gallery a = chb03 seizure 360-416 s")
fig, ax1 = plt.subplots(figsize=(10, 4.3))
ax1.axvspan(*g["ann"][0], color="#F4C7C3", alpha=0.7, lw=0, label="annotated seizure")
ax1.plot(g["score_t"], g["score"], color="#9AA5B1", lw=1.2, label="ensemble anomaly score")
ax1.plot(g["score_t"], g["score_sm"], color=C["main"], lw=2.4, label="smoothed (20 s)")
ax1.axhline(float(g["thr"]), color="k", ls="--", lw=1.4, label="patient threshold (alarm budget)")
ax1.hlines(-0.06, *g["det"][0], color=C["det"], lw=9, label="detector event")
ax1.hlines(-0.15, *g["loc"][0], color=C["loc"], lw=9, label="after change point localizer")
ax1.set_ylim(-0.22, 1.08); ax1.set_yticks([0, 0.5, 1.0])
ax1.set_xlim(g["score_t"][0], g["score_t"][-1])
ax1.set_xlabel("Time in the recording (s)"); ax1.set_ylabel("Score (percentile)")
ax1.legend(frameon=False, fontsize=14, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.22))
save(fig, "P11_example.png")

# ---------------------------------------------------------------- P13 sparsification
den = pd.read_csv(R / "results/diagnostics/density_frobenius_v2/density_per_subject.csv")
sep = pd.read_csv(R / "results/diagnostics/density_frobenius_v2/separation_per_subject.csv").set_index("subject").loc[TEST]
gate(round(sep.pct_change_rel_topk_vs_fixed.min()) == 48 and round(sep.pct_change_rel_topk_vs_fixed.max()) == 196, "Frobenius")
fig, ax = plt.subplots(1, 2, figsize=(11, 4.4))
x = np.arange(len(TEST)); w = 0.2
for i, (rule, split, col, lab) in enumerate((("fixed_t0.05", "interictal", C["grey"], "fixed threshold, background"),
                                             ("fixed_t0.05", "ictal", C["sz"], "fixed threshold, seizure"),
                                             ("topk20", "interictal", C["main"], "strongest 20 %, background"),
                                             ("topk20", "ictal", C["loc"], "strongest 20 %, seizure"))):
    v = den[(den.rule == rule) & (den.split == split)].set_index("subject").loc[TEST].mean_density
    ax[0].bar(x + (i - 1.5) * w, v, w, color=col, label=lab)
ax[0].set_xticks(x, [s[3:] for s in TEST]); ax[0].set_xlabel("Test patient (chb)"); ax[0].set_ylabel("Graph density")
ax[0].set_ylim(0, 1.0); ax[0].set_title("(a) density", loc="left")
ax[0].legend(frameon=False, fontsize=12.5, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2))
ax[1].bar(x - 0.2, sep.rel_frobenius_fixed_t0_05, 0.4, color=C["grey"], label="fixed threshold")
ax[1].bar(x + 0.2, sep.rel_frobenius_topk20, 0.4, color=C["main"], label="strongest 20 %")
ax[1].set_xticks(x, [s[3:] for s in TEST]); ax[1].set_xlabel("Test patient (chb)")
ax[1].set_ylabel("Seizure–background\ndistance"); ax[1].set_ylim(0, 0.9)
ax[1].legend(frameon=False, fontsize=13, loc="upper left"); ax[1].set_title("(b) separation", loc="left")
fig.tight_layout(); save(fig, "P13_sparsity.png")

# ---------------------------------------------------------------- P14 development (Tables 6 and 9)
led = pd.read_csv(R / "results/p2_ledger.csv")
def L(step, arm):
    r = led[(led.step == step) & (led.arm == arm)]; gate(len(r) >= 1, f"ledger {step} {arm}"); return float(r.best_le25.iloc[-1])
gate(abs(L("E16", "a") - 0.1915) < 1e-4 and abs(L("E16", "c") - 0.2952) < 1e-4 and abs(L("E16", "d") - 0.4867) < 1e-4, "E16 a c d")
gate(abs(L("E21-1", "E16e") - 0.6809) < 1e-4 and abs(L("E17b", "latent family (E16e)") - 0.6676) < 1e-4, "E16e E17b")
gate(abs(L("P3-L2f", "budget clip(q, 0.005, 0.02)") - 0.6782) < 1e-4, "L2f")
fz = (R / "results/p3c_freeze/SUMMARY.md").read_text()
gate("0.670" in fz or "0.6702" in fz or "0.6702" in fz, "p3c_freeze final 0.670")
fig, ax = plt.subplots(1, 2, figsize=(13, 5.0), gridspec_kw=dict(width_ratios=[1, 1.45], wspace=0.55))
ref = [("other patients\n(feature model)", 0.340, C["grey"]), ("first 10 min\nof each file", 0.191, C["grey"]),
       ("first 30 min\nof each file", 0.295, C["grey"]), ("causal 30-min\nwindow", 0.487, C["grey"]),
       ("own whole\nrecording", 0.612, C["main"])]
y = np.arange(len(ref))[::-1]
ax[0].barh(y, [v for _, v, _ in ref], color=[c for *_, c in ref], height=0.62)
for yi, (_, v, _) in zip(y, ref):
    ax[0].text(v + 0.01, yi, f"{v:.3f}", va="center", fontsize=15)
ax[0].set_yticks(y, [n for n, *_ in ref], fontsize=14); ax[0].set_xlim(0, 0.8)
ax[0].set_xlabel("Pooled sensitivity"); ax[0].set_title("(a) normal reference", loc="left")
steps = [("earlier score\n(seed 42)", 0.330), ("+ 7 absolute\nfeatures", 0.489), ("channel-level\nlatent", 0.612),
         ("+ drift\ncorrection", 0.681), ("+ 4 spatial\nscales", 0.668), ("+ per-patient\nbudget", 0.678),
         ("+ localizer\n(final)", 0.670)]
ys = np.arange(len(steps))[::-1]
ax[1].plot([v for _, v in steps], ys, color=C["main"], lw=2.2, marker="o", ms=10, zorder=3)
for yi, (_, v) in zip(ys, steps):
    ax[1].text(v + 0.015, yi + 0.12, f"{v:.3f}", fontsize=15)
ax[1].set_yticks(ys, [n.replace("\n", " ") for n, _ in steps], fontsize=14); ax[1].set_xlim(0.25, 0.8)
ax[1].set_xlabel("Pooled sensitivity"); ax[1].set_title("(b) contribution of each component", loc="left")
save(fig, "P14_development.png")

# ---------------------------------------------------------------- P16 boundaries
e = pd.read_csv(R / "results/e23_test_look7/errors.csv"); e = e[e.point == "balanced"]
med = e[["det_on", "det_off", "cpd_on", "cpd_off"]].abs().median()
gate(len(e) == 146 and tuple(med) == (32.0, 20.0, 12.0, 24.0), "boundary medians")
fig, ax = plt.subplots(1, 2, figsize=(12, 4.0), sharey=True)
for axx, side, lab in ((ax[0], "on", "Onset"), (ax[1], "off", "Offset")):
    data = [e[f"det_{side}"].values, e[f"cpd_{side}"].values]
    bp = axx.boxplot(data, vert=False, widths=0.55, showfliers=False, patch_artist=True)
    for p_, col in zip(bp["boxes"], (C["det"], C["loc"])):
        p_.set_facecolor(col); p_.set_alpha(0.55)
    for m in bp["medians"]:
        m.set_color("k"); m.set_linewidth(2)
    rng = np.random.default_rng(0)
    for i, v in enumerate(data, start=1):
        axx.scatter(np.clip(v, -150, 150), i + rng.uniform(-0.18, 0.18, len(v)), s=10, color="k", alpha=0.3, lw=0)
    axx.axvline(0, color=C["sz"], lw=1.5)
    axx.set_xlim(-150, 150); axx.set_xticks([-120, -60, 0, 60, 120]); axx.set_xlabel(f"{lab} error (s), negative = early")
ax[0].set_yticks([1, 2], ["Detector\nboundaries", "Change point\nlocalizer"])
fig.tight_layout(); save(fig, "P16_boundaries.png")

# ---------------------------------------------------------------- P17 Siena per patient (seed 42)
rows = pd.concat([pd.read_csv(p) for p in sorted((R / "results/x1_external").glob("rows_PN*.csv"))])
s42 = rows[(rows.point == "balanced") & (rows.seed == "clean_seed42") & (rows.stage == "localized")].set_index("subject").loc[M.SIENA]
gate(s42.tp.sum() == 33 and s42.n_ref.sum() == 47 and s42.fp.sum() == 257, "Siena 33/47, 257 FA")
fpd = s42.fp / s42.nonict_h * 24
fig, (a1, a2) = plt.subplots(2, 1, figsize=(12, 5.6), sharex=True, gridspec_kw=dict(height_ratios=[1.2, 1], hspace=0.12))
x = np.arange(len(M.SIENA))
a1.bar(x, s42.n_ref, 0.75, color=C["miss"], label="annotated seizures")
a1.bar(x, s42.tp, 0.42, color=C["main"], label="detected")
for i, s in enumerate(M.SIENA):
    a1.text(i, s42.n_ref[s] + 0.2, f"{int(s42.tp[s])}/{int(s42.n_ref[s])}", ha="center", fontsize=13,
            color=RED if s42.tp[s] == 0 else "black")
a1.set_ylabel("Seizures"); a1.set_ylim(0, 12); a1.set_yticks([0, 5, 10]); a1.legend(frameon=False, loc="upper left", ncol=2, fontsize=14)
a2.bar(x, fpd, 0.6, color=[RED if v > 70 else C["grey"] for v in fpd])
a2.axhline(41.0, color=C["main"], ls="--", lw=1.5)
a2.text(9.0, 58, "per-patient mean, 4 seeds: 41.0", ha="center", fontsize=13, color=C["main"])
a2.set_ylabel("False alarms\nper day"); a2.set_xticks(x, M.SIENA, fontsize=13)
save(fig, "P17_siena.png")

# ---------------------------------------------------------------- P18 channel ranking per test patient
ps = pd.read_csv(R / "results/attribution_v8/attribution_perseizure.csv")
summ = pd.read_csv(R / "results/attribution_v8/attribution_summary.csv")
gate(abs(summ.iloc[0].macro_AUROC - 0.5473) < 1e-4 and abs(summ.iloc[0].macro_AUROC_prior - 0.7387) < 1e-4, "0.547 / 0.739")
gate(len(ps) == 62, "62 focal seizures")
pp = ps.groupby("subject").agg(model=("AUROC", "mean"), prior=("AUROC_prior", "mean"), n=("AUROC", "size"))
pp = pp.loc[[s for s in TEST if s in pp.index]]
gate(abs(pp.loc["chb15", "model"] - 0.675) < 0.001, "chb15 0.675")
fig, axx = plt.subplots(figsize=(9.5, 5.4))
yy = np.arange(len(pp))[::-1]
for yi, (s, r) in zip(yy, pp.iterrows()):
    axx.plot([r.model, r.prior], [yi, yi], color="#C9D3E0", lw=3, zorder=1)
axx.scatter(pp.model, yy, s=130, color=C["main"], zorder=3, label="this model (channel-level latent anomaly)")
axx.scatter(pp.prior, yy, s=130, color=C["uns"], zorder=3, label="anatomical prior (ignores the EEG)")
axx.axvline(0.5, color=C["grey"], ls=":", lw=1.5); axx.text(0.5, len(pp) - 0.35, "random 0.5", ha="center", fontsize=13, color=C["grey"])
axx.set_yticks(yy, [f"{s} ({int(r.n)})" for s, r in pp.iterrows()])
axx.set_xlim(0.15, 1.0); axx.set_xlabel("Channel ranking AUROC vs blind annotation (mean per patient)")
axx.legend(frameon=False, loc="upper center", bbox_to_anchor=(0.45, -0.17), ncol=1, fontsize=14)
save(fig, "P18_channel.png")

# ---------------------------------------------------------------- P20 budget needed + duration
sz = pd.read_csv(R / "results/p3_anatomy/seizures.csv"); sz = sz[(sz.set == "test") & (sz.seed == "clean_seed42")]
gate(len(sz) == 76, "76 test seizures")
b = M.e23_per_subject(); b = b[b.seed == "clean_seed42"].set_index("subject")
fig, axb = plt.subplots(figsize=(10, 4.6))
rng = np.random.default_rng(1)
for i, subj in enumerate(TEST):
    v = sz[sz.subject == subj].pn_final.values
    axb.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=40, color=C["main"], alpha=0.8, lw=0)
    axb.hlines(b.loc[subj, "top"], i - 0.32, i + 0.32, color=C["loc"], lw=3)
axb.axhline(0.005, color=C["grey"], ls=":", lw=1.5); axb.axhline(0.02, color=C["grey"], ls="--", lw=1.5)
axb.text(7.5, 0.005, "0.5 %", va="center", fontsize=14); axb.text(7.5, 0.02, "2 % cap", va="center", fontsize=14)
axb.set_yscale("log"); axb.set_xticks(range(len(TEST)), TEST); axb.set_xlim(-0.5, 8.2)
axb.set_ylabel("Budget needed\n(share of time)")
for s in ("chb06", "chb13", "chb16"):
    i = TEST.index(s); axb.add_patch(plt.Rectangle((i - 0.42, 0.0025), 0.84, 0.25, fill=False, ec=RED, lw=2.2))
axb.plot([], [], color=C["loc"], lw=3, label="patient's alarm budget"); axb.scatter([], [], s=40, color=C["main"], label="one seizure")
axb.legend(frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 1.16))
save(fig, "P20_budget.png")

d = pd.read_csv(R / "results/figures_v8_data/perseizure_final.csv"); d42 = d[d.seed == "clean_seed42"]
gate(len(d42) == 76 and int(d42.detected_final.sum()) == 37 and int(d42.detected_heldout.sum()) == 26, "per-seizure 37/26")
bins = [0, 20, 40, 60, 120, 400]; labels = ["< 20", "20–39", "40–59", "60–119", "≥ 120"]
d42 = d42.assign(bin=pd.cut(d42.dur_s, bins, right=False, labels=labels))
gg = d42.groupby("bin", observed=False).agg(n=("dur_s", "size"), fin=("detected_final", "sum"), held=("detected_heldout", "sum"))
gate(list(gg.n) == [18, 18, 9, 23, 8] and int(gg.fin.iloc[0]) == 4, "duration bins")
fig, axd = plt.subplots(figsize=(8.5, 4.6))
x = np.arange(len(labels))
axd.bar(x, gg.n, 0.62, color=C["miss"], label="annotated")
axd.bar(x - 0.14, gg.held, 0.28, color=C["grey"], label="held-out")
axd.bar(x + 0.14, gg.fin, 0.28, color=C["main"], label="final")
for xi, (n, fi) in enumerate(zip(gg.n, gg.fin)):
    axd.text(xi, n + 0.4, f"{int(fi)}/{int(n)}", ha="center", fontsize=15, color=RED if xi == 0 else "black")
axd.set_xticks(x, labels); axd.set_xlabel("Seizure duration, whole 4 s windows (s)"); axd.set_ylabel("Seizures")
axd.set_ylim(0, 31); axd.legend(frameon=False, ncol=3, loc="upper left", fontsize=14)
save(fig, "P20_duration.png")
print("ALL GATES PASSED")
