#!/usr/bin/env python
"""figs_backup.py -- coded figures for the backup slides (D4 rebuild, 19/10/2026).

Reads committed files of github.com/Nhanvas/Thesis; recomputes nothing from EEG or score caches. Every figure has a
gate against the numbers of the report (NUMBERS_LOCK). Values that exist only in the experiment record (no file in
results/) are transcribed from report Table 10 and marked REC below; every ledger value is read from the ledger.

  B04_not_adopted.png   designs evaluated and not adopted (report Table 10)        ledger + REC
  B06_budgets.png       label-free budget per test patient, final system (Table 12) e23 per_subject_seed.csv
  B07_cpd.png           detector boundaries vs change-point localizer, chb03     figures_v8_data/gallery/a.npz
  B12_uncertainty.png   seeds vs patient bootstrap, held-out and final (Table 11) e22/e23 csv + BOOTSTRAP.md + SUMMARY.md
  B16_labelstep.png     application (label-free statistics) vs final system (Table 17) application_eval_v4, e23
  B18_siena_budget.png  Siena: false alarms per day vs label-free budget (Table 15) x1_external rows
  B20_channels.png      blind channel annotation: labels per channel (App D)     attribution_v7 labels
  B22_timing.png        processing time per stage, chb16, 3 runs (Table 25)     t1_demo/timing.csv
Run: python figs_backup.py --repo /home/claude/repo --out out
"""
import argparse
import re
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ap = argparse.ArgumentParser(); ap.add_argument("--repo", required=True); ap.add_argument("--out", required=True)
a = ap.parse_args()
R = Path(a.repo); RES = R / "results"; OUT = Path(a.out); OUT.mkdir(parents=True, exist_ok=True)
sys.path.insert(0, str(R / "src" / "figures_v8"))
import make_v8_exhibits as M  # noqa: E402
C, TEST = M.C, M.TEST
plt.rcParams.update({"font.family": "DejaVu Sans", "axes.spines.top": False, "axes.spines.right": False,
                     "font.size": 16, "axes.labelsize": 16, "xtick.labelsize": 15, "ytick.labelsize": 15,
                     "legend.fontsize": 15, "axes.titlesize": 16})
RED, BLUE, GREY, NAVY = "#C62828", "#0072B2", "#8A949F", "#1B2A4A"


def gate(c, m):
    if not c:
        raise SystemExit("STOP (gate): " + m)


def save(fig, name):
    fig.savefig(OUT / name, dpi=200, bbox_inches="tight"); plt.close(fig)


# ------------------------------------------------------------------ B04 designs not adopted (Table 10)
led = pd.read_csv(RES / "p2_ledger.csv")
def L(step, arm):
    r = led[(led.step == step) & (led.arm == arm)]; gate(len(r) >= 1, f"ledger {step} {arm}"); return round(float(r.best_le25.iloc[-1]), 3)
# (stage, design, value, reference, reference label, note)
rows = [("Normal reference", "Normal from other patients (feature model)", 0.340, 0.596, "own recording", ""),        # REC E1/E5
        ("Normal reference", "Artifact model on the high-amplitude flag", 0.096, 0.351, "without it", "earlier score"),  # REC E4
        ("Normal reference", "First 10 min of each file", L("E16", "a"), L("E16", "e"), "", ""),
        ("Normal reference", "First 30 min of each file", L("E16", "c"), 0.612, "whole recording", ""),
        ("Normal reference", "Causal 30-min window", L("E16", "d"), 0.612, "", ""),
        ("Normal reference", "GAE fine-tuned per patient (2 seeds)", 0.628, 0.622, "", "no fall in non-seizure scores"),  # REC E15
        ("Readout", "Graph-level latent distance (2 seeds)", 0.553, 0.622, "channel-level", ""),                  # REC E14
        ("Readout", "+ reconstruction error + gamma coupling", L("E21-2", "Eb(C=E16e)"), L("E21-1", "E16e"), "channel score alone", ""),
        ("Drift", "Level and spread corrected per file", L("E21-1", "E16b"), L("E21-1", "E16e"), "level only", ""),
        ("Drift", "Per-file median instead of running", L("E16", "f"), L("E16", "e"), "running median", ""),
        ("Detection", "Change points as the detector", 0.213, 0.479, "threshold detector", "earlier score"),     # REC E7
        ("Detection", "Kernel detector of local bumps", 0.250, 0.489, "", "5.8 vs 19.8 FA/day"),                  # REC E10
        ("Detection", "One 2 % budget for every patient", 0.803, L("P3-L2f", "budget clip(q, 0.005, 0.02)"), "per-patient budget", "95.1 vs 23.8 FA/day"),  # REC 9.7
        ("Detection", "Budget floor 0.25 % instead of 0.5 %", 0.657, L("P3-L2f", "budget clip(q, 0.005, 0.02)"), "", "chb21 1.75 → 0.50"),  # REC 9.7
        ("Localization", "Change points on the 18-channel trajectory", L("E20a", "family_Ce_fine_raw_m15_multi"), L("E18", "family_Ce_fine_raw_m15"), "1-D localizer", "offset 8 vs 16 s")]
# the ledger value of 'first 10 min' reference is the per-file grid; Table 10 compares with whole recording 0.612
rows[2] = (rows[2][0], rows[2][1], rows[2][2], 0.612, "whole recording", "")
gate(all(abs(v - e) <= 0.0015 for v, e in ((rows[2][2], 0.191), (rows[3][2], 0.295), (rows[4][2], 0.487))), "E16 a/c/d = 0.191/0.295/0.487")
rows[2] = rows[2][:2] + (0.191,) + rows[2][3:]  # report value (ledger 0.1915)
ap_ = lambda v, e: abs(v - e) <= 0.0015
gate(ap_(rows[7][2], 0.636) and ap_(rows[7][3], 0.681) and ap_(rows[8][2], 0.596), "E21 = 0.636/0.681/0.596")
gate(ap_(rows[9][2], 0.559) and ap_(rows[9][3], 0.628), "E16 f/e = 0.559/0.628")
gate(ap_(rows[12][3], 0.678) and ap_(rows[14][2], 0.657) and ap_(rows[14][3], 0.662), "P3-L2f 0.678; E20a 0.657; E18 0.662")
fig, ax = plt.subplots(figsize=(10.5, 8.2))
n = len(rows); ys = np.arange(n)[::-1]
stage_prev = None
for y, (st, de, v, r, rl, note) in zip(ys, rows):
    ax.plot([min(v, r), max(v, r)], [y, y], color="#C9D3E0", lw=5, zorder=1, solid_capstyle="round")
    ax.scatter([r], [y], s=150, color=BLUE, zorder=3, label="design kept (same rule)" if y == ys[0] else None)
    ax.scatter([v], [y], s=150, color=RED, zorder=3, marker="D", label="design not adopted" if y == ys[0] else None)
    ax.text(-0.02, y, de, ha="right", va="center", fontsize=15)
    if note:
        ax.text(max(v, r) + 0.02, y, note, ha="left", va="center", fontsize=13, color=GREY, style="italic")
    if st != stage_prev:
        gy = [yy for yy, rr in zip(ys, rows) if rr[0] == st]
        ax.text(-1.22, (max(gy) + min(gy)) / 2, st.replace(" ", "\n"), ha="left", va="center", fontsize=15, fontweight="bold", color=NAVY)
        if stage_prev is not None:
            ax.plot([-1.22, 1.0], [y + 0.5, y + 0.5], color="#D5DCE5", lw=1.2, clip_on=False)
        stage_prev = st
ax.set_xlim(0, 1.0); ax.set_ylim(-0.6, n - 0.2); ax.set_yticks([])
ax.spines["left"].set_visible(False)
ax.set_xlabel("Pooled sensitivity, development patients (≤ 25 false alarms per day unless noted)")
ax.legend(frameon=False, loc="lower left", fontsize=15)
save(fig, "B04_not_adopted.png")

# ------------------------------------------------------------------ B06 budgets per test patient (final, seed 42)
e23 = pd.read_csv(RES / "e23_test_look7" / "per_subject_seed.csv")
b = e23[(e23.point == "balanced") & (e23.seed == "clean_seed42") & (e23.stage == "localized")].set_index("subject").loc[TEST]
exp = {"chb03": 0.0052, "chb06": 0.005, "chb13": 0.005, "chb14": 0.0065, "chb15": 0.02, "chb16": 0.005, "chb17": 0.005, "chb18": 0.0082}
gate(all(abs(round(b.top[s], 4) - v) < 1e-9 for s, v in exp.items()), "Table 12 budgets")
fig, ax = plt.subplots(figsize=(10.5, 4.8))
cols = [RED if t >= 0.02 - 1e-9 else (BLUE if t > 0.005 + 1e-9 else GREY) for t in b.top]
ax.bar([s[3:] for s in TEST], 100 * b.top, color=cols, width=0.6)
for i, t in enumerate(b.top):
    ax.text(i, 100 * t + 0.05, f"{100 * t:.2f}", ha="center", fontsize=14)
ax.axhline(0.5, color="k", ls="--", lw=1.3); ax.text(7.45, 0.5, "floor 0.5 %\n(held-out budget)", va="center", fontsize=13)
ax.axhline(2.0, color=RED, ls="--", lw=1.3); ax.text(7.45, 2.0, "cap 2 %", va="center", fontsize=13, color=RED)
ax.axhline(1.1, color=GREY, ls=":", lw=1.3); ax.text(7.45, 1.1, "largest\ndevelopment 1.1 %", va="center", fontsize=13, color=GREY)
ax.set_ylim(0, 2.4); ax.set_xlabel("Test patient (chb)"); ax.set_ylabel("Alarm budget (% of time)")
save(fig, "B06_budgets.png")

# ------------------------------------------------------------------ B07 detector vs localizer (chb03 seizure, data of report Fig. 14a)
g = np.load(RES / "figures_v8_data" / "gallery" / "a.npz", allow_pickle=True)
gate(str(g["title"]).startswith("chb03") and tuple(g["ann"][0]) == (360.0, 416.0) and tuple(g["loc"][0]) == (372.0, 460.0), "gallery a")
t, sc, sm = g["score_t"], g["score"], g["score_sm"]
d0, d1 = g["det"][0]; l0, l1 = g["loc"][0]; a0, a1 = g["ann"][0]
fig, ax = plt.subplots(figsize=(11, 5.0))
ax.axvspan(a0, a1, color="#F4C7C3", alpha=0.7, lw=0, label="annotated seizure")
ax.axvspan(d0 - 60, d1 + 60, color="#EEF2F7", lw=0, zorder=0, label="search window: event ± 60 s")
ax.plot(t, sc, color="#9AA5B1", lw=1.2, label="unsmoothed score (localizer input)")
ax.plot(t, sm, color=C["main"], lw=2.4, label="smoothed score (detector input)")
ax.axhline(float(g["thr"]), color="k", ls="--", lw=1.3)
ax.hlines(-0.07, d0, d1, color=C["det"], lw=9, label="detector event")
ax.hlines(-0.17, l0, l1, color=C["loc"], lw=9, label="after the 2 change points")
for x in (l0, l1):
    ax.axvline(x, color=C["loc"], lw=2, ls=":")
ax.set_xlim(240, 600); ax.set_ylim(-0.25, 1.08); ax.set_yticks([0, 0.5, 1])
ax.set_xlabel("Time in the recording (s), chb03"); ax.set_ylabel("Score (percentile)")
ax.legend(frameon=False, fontsize=13.5, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.2))
save(fig, "B07_cpd.png")

# ------------------------------------------------------------------ B12 seeds vs bootstrap
s22 = pd.read_csv(RES / "e22_test_oneshot" / "summary_per_seed.csv")
s23 = pd.read_csv(RES / "e23_test_look7" / "summary_per_seed.csv")
h = s22[s22.system.str.contains("local")] if s22.system.str.contains("local").any() else s22
f = s23[(s23.point == "balanced") & (s23.system.str.contains("local"))]
gate(len(h) == 4 and len(f) == 4, f"4 seeds each ({len(h)}, {len(f)}); systems {s22.system.unique()} {s23.system.unique()}")
gate(round(h[h.seed == "clean_seed42"].sens.iloc[0], 3) == 0.342 and round(f[f.seed == "clean_seed42"].sens.iloc[0], 3) == 0.487, "seed 42 0.342 / 0.487")
gate(round(h.sens.mean(), 3) == 0.336 and round(f.sens.mean(), 3) == 0.477, "4-seed 0.336 / 0.477")
bt = (RES / "e22_test_oneshot" / "BOOTSTRAP.md").read_text()
m = re.search(r"all 8\s+final pooled sens\s+\+([\d.]+)\s+\[\s*\+([\d.]+),\s*\+([\d.]+)\]", bt)
gate(m and m.groups() == ("0.336", "0.133", "0.670"), "held-out bootstrap 0.336 [0.133, 0.670]")
sm23 = (RES / "e23_test_look7" / "SUMMARY.md").read_text()
dm = re.search(r"pooled sens diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", sm23)
gate(dm and dm.groups() == ("0.141", "0.000", "0.333"), "diff +0.141 [0.000, 0.333]")
fig, ax = plt.subplots(1, 2, figsize=(14, 4.4), gridspec_kw={"width_ratios": [1.35, 1]})
for y, (name, df, col) in enumerate([("final (test-informed)", f, C["loc"]), ("held-out", h, C["main"])]):
    ax[0].scatter(df.sens, [y] * 4, s=110, color=col, zorder=3, edgecolor="white")
    ax[0].text(df.sens.max() + 0.02, y, f"4 seeds: {df.sens.min():.3f}–{df.sens.max():.3f}", va="center", fontsize=14)
lo, hi = float(m.group(2)), float(m.group(3))
ax[0].plot([lo, hi], [1.28, 1.28], color=C["main"], lw=4, solid_capstyle="round")
ax[0].text((lo + hi) / 2, 1.5, f"patient bootstrap 95 %: [{lo:.3f}, {hi:.3f}]", ha="center", fontsize=14, color=C["main"])
ax[0].set_yticks([0, 1], ["final", "held-out"]); ax[0].set_ylim(-0.6, 1.9); ax[0].set_xlim(0, 0.85)
ax[0].set_xlabel("Pooled sensitivity, 8 test patients"); ax[0].set_title("(a) seed spread vs patient uncertainty", loc="left")
dv, dlo, dhi = map(float, dm.groups())
ax[1].plot([dlo, dhi], [0, 0], color=C["loc"], lw=4, solid_capstyle="round"); ax[1].scatter([dv], [0], s=120, color=C["loc"], zorder=3)
ax[1].axvline(0, color="k", lw=1.2, ls="--")
ax[1].text(dv, 0.25, f"+{dv:.3f} [{dlo:.3f}, {dhi:.3f}]", ha="center", fontsize=14)
ax[1].set_ylim(-0.6, 0.8); ax[1].set_yticks([]); ax[1].spines["left"].set_visible(False); ax[1].set_xlim(-0.1, 0.45)
ax[1].set_xlabel("Final − held-out, pooled sensitivity"); ax[1].set_title("(b) gain of the final system", loc="left")
fig.tight_layout(); save(fig, "B12_uncertainty.png")

# ------------------------------------------------------------------ B16 label-dependent step: application vs final
app = pd.read_csv(RES / "application_eval_v4" / "per_subject.csv").set_index("subject").loc[TEST]
gate(app.detected.sum() == 33 and app.false_alarms.sum() == 323 and b.tp.sum() == 37 and b.fp.sum() == 318, "33/323 vs 37/318")
fig, ax = plt.subplots(1, 2, figsize=(14, 4.6))
x = np.arange(len(TEST)); w = 0.38
ax[0].bar(x - w / 2, b.tp, w, color=C["main"], label="final system (thesis statistics)")
ax[0].bar(x + w / 2, app.detected, w, color="#E69F00", label="application (label-free statistics)")
for i, s in enumerate(TEST):
    if app.detected[s] != b.tp[s]:
        ax[0].text(i + w / 2, app.detected[s] + 0.3, "−1", ha="center", fontsize=14, color=RED, fontweight="bold")
ax[0].set_xticks(x, [s[3:] for s in TEST]); ax[0].set_ylabel("Seizures detected"); ax[0].set_xlabel("Test patient (chb)")
ax[0].set_title("(a) detected: 37 → 33 of 76", loc="left"); ax[0].set_ylim(0, 13)
ax[1].bar(x - w / 2, b.fp, w, color=C["main"]); ax[1].bar(x + w / 2, app.false_alarms, w, color="#E69F00")
ax[1].set_xticks(x, [s[3:] for s in TEST]); ax[1].set_ylabel("False alarms"); ax[1].set_xlabel("Test patient (chb)")
ax[1].set_title("(b) false alarms: 318 → 323", loc="left")
fig.legend(*ax[0].get_legend_handles_labels(), frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, -0.02))
fig.tight_layout(); save(fig, "B16_labelstep.png")

# ------------------------------------------------------------------ B18 Siena: FA/day vs budget
SI = ["PN00", "PN01", "PN03", "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12", "PN13", "PN14", "PN16", "PN17"]
xr = pd.concat([pd.read_csv(RES / "x1_external" / f"rows_{p}.csv") for p in SI])
xr = xr[(xr.seed == "clean_seed42") & (xr.stage == "localized") & (xr.point == "balanced")].set_index("subject").loc[SI]
fpd = xr.fp / xr.nonict_h * 24
gate(xr.tp.sum() == 33 and xr.fp.sum() == 257 and round(fpd["PN07"], 1) == 90.9 and round(fpd["PN11"], 1) == 30.1, "Siena 33/257; PN07 90.9; PN11 30.1")
big = xr.top > 0.017
gate(xr.fp[big].sum() == 197 and big.sum() == 7, "7 patients > 1.7 % hold 197 FA")
fig, ax = plt.subplots(figsize=(10.5, 5.6))
ax.scatter(100 * xr.top, fpd, s=40 + 25 * xr.n_ref, color=[RED if v else C["main"] for v in big], alpha=0.85, edgecolor="white", zorder=3)
OFF = {"PN01": (0.05, -3.5), "PN05": (-0.19, 4.0), "PN10": (0.05, 3.0), "PN09": (0.06, -2.5), "PN07": (-0.27, -1.5), "PN14": (-0.2, 3.5)}
for p in SI:
    dx, dy = OFF.get(p, (0.04, 1.5))
    ax.text(100 * xr.top[p] + dx, fpd[p] + dy, p, fontsize=12.5)
ax.axvline(1.7, color=GREY, ls=":", lw=1.3)
ax.text(1.74, 22, "7 patients > 1.7 %:\n197 of 257 false alarms", fontsize=14, color=RED, va="top")
ax.set_xlabel("Label-free alarm budget (% of time)"); ax.set_ylabel("False alarms per day")
ax.set_xlim(0.3, 2.35); ax.set_ylim(0, 100)
save(fig, "B18_siena_budget.png")

# ------------------------------------------------------------------ B20 channel annotation frequency
lab = pd.read_csv(RES / "attribution_v7" / "labels" / "ictal_channels_FINAL.csv")
foc = lab[lab.focal_generalized == "focal"]
gate(len(foc) == 62 and (lab.focal_generalized == "generalized").sum() == 14, "62 focal + 14 generalized")
cnt = pd.Series([c for s in foc.ictal_channels for c in s.split("|")]).value_counts()
CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
      "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
cnt = cnt.reindex(CH).fillna(0).astype(int)
FP = ["FP1-F7", "FP1-F3", "FP2-F4", "FP2-F8"]
gate(cnt.sum() == 282 and cnt[FP].sum() == 116, "282 labels; frontopolar 116")
gate(set(cnt[cnt == 0].index) == {"C3-P3", "C4-P4", "P4-O2", "FZ-CZ", "CZ-PZ"}, "5 never annotated")
o = cnt.sort_values(ascending=False)
fig, ax = plt.subplots(figsize=(13, 4.8))
ax.bar(range(18), o.values, color=[RED if c in FP else (GREY if v == 0 else C["main"]) for c, v in o.items()], width=0.7)
ax.set_xticks(range(18), o.index, rotation=55, ha="right", fontsize=13)
for i, v in enumerate(o.values):
    if v == 0:
        ax.text(i, 0.8, "0", ha="center", fontsize=13, color=GREY)
ax.set_ylabel("Times annotated\n(62 focal seizures)")
ax.text(17.4, o.values.max() * 0.95, "red: frontopolar, 116 of 282 labels (41 %)\ngrey: never annotated (5 channels)", ha="right", va="top", fontsize=14)
save(fig, "B20_channels.png")

# ------------------------------------------------------------------ B22 processing time per stage
tm = pd.read_csv(RES / "t1_demo" / "timing.csv")
gate(list(tm.s_per_hour) == [24.41, 21.6, 21.68] and float(np.median(tm.s_per_hour)) == 21.68, "timing 24.41/21.60/21.68")
st = [("phase_a_s", "reading, filtering, windowing", "#9CC3E6"), ("features_s", "graphs and features", C["main"]),
      ("gae_s", "autoencoder", "#E69F00"), ("distances_and_score_s", "distances and score", "#56B4E9"), ("events_s", "events", "#009E73")]
fig, ax = plt.subplots(figsize=(12, 3.8))
left = np.zeros(3)
for c, lbl, col in st:
    ax.barh([f"run {r}" for r in tm.run], tm[c], left=left, color=col, label=lbl, height=0.55)
    left += tm[c].values
for i, (tot, sph) in enumerate(zip(tm.total_s, tm.s_per_hour)):
    ax.text(tot + 6, i, f"{tot:.1f} s · {sph:.2f} s per hour", va="center", fontsize=14)
ax.invert_yaxis(); ax.set_xlim(0, 640); ax.set_xlabel("Seconds for chb16 (19 files, 19.0 h), laptop CPU, no GPU")
ax.legend(frameon=False, ncol=3, fontsize=13.5, loc="upper center", bbox_to_anchor=(0.45, -0.3))
save(fig, "B22_timing.png")

# ------------------------------------------------------------------ B11 why the metrics are low (held-out and final, seed 42)
h22 = pd.read_csv(RES / "e22_test_oneshot" / "per_subject_seed.csv")
h22 = h22[(h22.seed == "clean_seed42") & (h22.stage == "localized")].set_index("subject").loc[TEST]
gate(h22.tp.sum() == 26 and h22.fp.sum() == 257 and h22.n_ref.sum() == 76, "held-out 26/257/76")
tail = pd.read_csv(RES / "p3b_diag" / "tail.csv")
tail = tail[(tail.set == "test") & (tail.tier == "top0.5%")].set_index("subject").loc[TEST]
gate(round(tail.flagged["chb06"], 2) == 0.30 and round(tail.flagged["chb13"], 2) == 0.89
     and round(tail.drop("chb06").flagged.min(), 2) == 0.62 and round(tail.drop("chb06").flagged.max(), 2) == 0.91
     and tail.peri_10min.max() <= 0.11, "tail flagged chb06 30 %, others 62-91 %, chb13 89 %, peri <= 11 %")
fig, ax = plt.subplots(1, 2, figsize=(16, 4.9), gridspec_kw={"width_ratios": [1.15, 1], "wspace": 0.35})
for y, (lab, tp, fn, fp) in enumerate([("final\n(test-informed)", b.tp.sum(), b.n_ref.sum() - b.tp.sum(), b.fp.sum()),
                                       ("held-out", h22.tp.sum(), h22.n_ref.sum() - h22.tp.sum(), h22.fp.sum())]):
    ax[0].barh(y, tp, color=C["loc"], height=0.55, label="detected seizures" if y == 0 else None)
    ax[0].barh(y, fn, left=tp, color="#C9D3E0", height=0.55, label="missed seizures" if y == 0 else None)
    ax[0].barh(y, fp, left=tp + fn, color=RED, height=0.55, alpha=0.85, label="false alarms" if y == 0 else None)
    for x0, v in ((0, tp), (tp, fn), (tp + fn, fp)):
        ax[0].text(x0 + v / 2, y, str(int(v)), ha="center", va="center", fontsize=15, color="white" if v != fn else NAVY, fontweight="bold")
    prec = tp / (tp + fp); f1 = 2 * tp / (2 * tp + fp + fn)
    ax[0].text(tp + fn + fp + 8, y, f"precision {prec:.3f}\nF1 {f1:.3f}", va="center", fontsize=14)
gate(abs(26 / 283 - 0.092) < 5e-4 and abs(52 / 359 - 0.145) < 5e-4, "precision/F1 held-out 0.092/0.145")
ax[0].set_yticks([0, 1], ["final\n(test-informed)", "held-out"]); ax[0].set_xlim(0, 520)
ax[0].set_xlabel("Count, 8 test patients (279.39 h), seed 42")
ax[0].legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.45, -0.2), fontsize=14)
ax[0].set_title("(a) false alarms outnumber seizures", loc="left", fontsize=16)
x = np.arange(len(TEST))
ax[1].bar(x, 100 * tail.flagged, color=[GREY if s == "chb06" else C["main"] for s in TEST], width=0.6)
ax[1].axhline(46, color="k", ls="--", lw=1.3); ax[1].text(7.45, 46, "all non-seizure\ntraining windows: 46 %", va="center", fontsize=13)
ax[1].set_xticks(x, [s[3:] for s in TEST]); ax[1].set_ylim(0, 100); ax[1].set_xlabel("Test patient (chb)")
ax[1].set_ylabel("High-amplitude share (%)")
ax[1].set_title("(b) top 0.5 % non-seizure windows: high-amplitude share", loc="left", fontsize=16)
save(fig, "B11_metrics_low.png")

# ------------------------------------------------------------------ B14 a missed seizure and a false alarm (data of report Fig. 14c, 14d)
fig = plt.figure(figsize=(16, 6.4))
gs = fig.add_gridspec(2, 2, height_ratios=[1.55, 1], hspace=0.38, wspace=0.12)
for col, k, ttl in ((0, "c", "(a) missed: shortest seizure of chb16 (8 s)"), (1, "d", "(b) false alarm: highest-scoring, > 10 min from any seizure, chb03")):
    g = np.load(RES / "figures_v8_data" / "gallery" / f"{k}.npz", allow_pickle=True)
    gate(str(g["title"]).startswith("chb16" if k == "c" else "chb03"), f"gallery {k}")
    eeg = g["eeg"].astype(float); fs = int(g["fs"]); t0 = float(g["eeg_t0"]); te = t0 + np.arange(eeg.shape[1]) / fs
    a = fig.add_subplot(gs[0, col])
    for i in range(18):
        a.plot(te, eeg[i] / (4 * np.nanstd(eeg)) - i, color="#1F3A5F", lw=0.5)
    for s0, s1 in g["ann"]:
        a.axvspan(s0, s1, color="#F4C7C3", alpha=0.7, lw=0)
    for s0, s1 in g["loc"]:
        a.axvspan(max(s0, te[0]), min(s1, te[-1]), color="#CFE8DD", alpha=0.6, lw=0) if s1 > te[0] and s0 < te[-1] else None
    a.set_yticks(-np.arange(18), list(g["ch"]), fontsize=9); a.set_xlim(te[0], te[-1]); a.set_ylim(-18, 1)
    a.set_title(ttl, loc="left", fontsize=15); a.tick_params(axis="x", labelsize=12)
    b2 = fig.add_subplot(gs[1, col])
    for s0, s1 in g["ann"]:
        b2.axvspan(s0, s1, color="#F4C7C3", alpha=0.8, lw=0)
    for s0, s1 in g["loc"]:
        b2.axvspan(s0, s1, color="#CFE8DD", alpha=0.8, lw=0)
    b2.plot(g["score_t"], g["score_sm"], color=C["main"], lw=1.8)
    b2.axhline(float(g["thr"]), color="k", ls="--", lw=1.2)
    b2.axvspan(te[0], te[-1], color="none", ec=GREY, lw=1.0, ls=":")
    b2.set_xlim(g["score_t"][0], g["score_t"][-1]); b2.set_ylim(0, 1.05); b2.set_yticks([0, 0.5, 1])
    b2.set_xlabel("Time in the recording (s)", fontsize=13); b2.tick_params(labelsize=12)
    if col == 0:
        b2.set_ylabel("Smoothed\nscore", fontsize=13)
fig.legend(handles=[plt.Rectangle((0, 0), 1, 1, color="#F4C7C3"), plt.Rectangle((0, 0), 1, 1, color="#CFE8DD"),
                    plt.Line2D([], [], color=C["main"], lw=2), plt.Line2D([], [], color="k", ls="--")],
           labels=["annotated seizure", "event of the system", "smoothed score (20 s)", "patient threshold"],
           frameon=False, ncol=4, loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=14)
save(fig, "B14_miss_fa.png")

# ------------------------------------------------------------------ B15 boundaries on every set (Table 13)
med = lambda s: float(np.median(np.abs(s)))
e22 = pd.read_csv(RES / "e22_test_oneshot" / "errors.csv")
e23 = pd.read_csv(RES / "e23_test_look7" / "errors.csv"); e23 = e23[e23.point == "balanced"]
dev = pd.read_csv(RES / "p3c_freeze" / "errors.csv"); dev = dev[dev.budget == "L2f"]
c24 = pd.read_csv(RES / "x1_external" / "errors_chb24.csv"); c24 = c24[c24.point == "balanced"]
sie = pd.concat([pd.read_csv(f) for f in sorted((RES / "x1_external").glob("errors_PN*.csv")) if f.stat().st_size > 5]); sie = sie[sie.point == "balanced"]
sets = [("Development", dev, "det", "cpd", 247), ("Held-out test", e22, "det", "loc", 103), ("Final test", e23, "det", "cpd", 146),
        ("chb24", c24, "det", "cpd", 53), ("Siena", sie, "det", "cpd", 116)]
exp = {"Development": (16, 24, 4, 16), "Held-out test": (28, 16, 8, 20), "Final test": (32, 20, 12, 24), "chb24": (12, 8, 4, 4), "Siena": (36, 28, 20, 28)}
vals = {}
for nm, df, d, l, n in sets:
    v = (med(df[d + "_on"]), med(df[d + "_off"]), med(df[l + "_on"]), med(df[l + "_off"]))
    gate(tuple(round(x) for x in v) == exp[nm], f"Table 13 {nm}: {v}")
    gate(len(df) == n or nm == "Held-out test", f"n {nm} {len(df)}")
    vals[nm] = v
fig, ax = plt.subplots(1, 2, figsize=(15, 4.6), sharey=True)
names = [s[0] for s in sets][::-1]
for j, (lab, i0, i1) in enumerate((("(a) onset", 0, 2), ("(b) offset", 1, 3))):
    for y, nm in enumerate(names):
        d0, l0 = vals[nm][i0], vals[nm][i1]
        col = C["loc"] if l0 < d0 else (RED if l0 > d0 else GREY)
        ax[j].annotate("", xy=(l0, y), xytext=(d0, y), arrowprops=dict(arrowstyle="-|>", color=col, lw=2.4, mutation_scale=20)) if l0 != d0 else None
        ax[j].scatter([d0], [y], s=120, color="#E69F00", zorder=3, label="detector boundary" if y == 0 else None)
        ax[j].scatter([l0], [y], s=120, color=C["loc"], zorder=4, marker="D", label="change point localizer" if y == 0 else None)
        ax[j].text(max(d0, l0) + 1.5, y, f"{d0:.0f} → {l0:.0f} s", va="center", fontsize=14)
    ax[j].set_xlim(0, 48); ax[j].set_title(lab, loc="left", fontsize=16); ax[j].set_xlabel("Median absolute error (s)")
ax[0].set_yticks(range(len(names)), names)
fig.legend(*ax[0].get_legend_handles_labels(), frameon=False, ncol=2, loc="upper center", bbox_to_anchor=(0.5, 0.0), fontsize=14)
fig.tight_layout(); save(fig, "B15_boundaries.png")

# ------------------------------------------------------------------ B05 window view vs event view (chb03, first hour, data of report Fig. 8)
S = pd.read_csv(RES / "figures_v6_data" / "chb03_score.csv"); E = pd.read_csv(RES / "figures_v6_data" / "chb03_events.csv")
gate(len(S) == 2700 and int(S[S.file == 0].ictal.sum()) == 14, "chb03 file 0: 900 windows, 14 seizure windows")
s0 = S[S.file == 0]; ev = E[(E.file == 0) & (E.kind == "localized")]
fig, ax = plt.subplots(2, 1, figsize=(15, 5.6), gridspec_kw={"height_ratios": [1.25, 1], "hspace": 0.55})
ax[0].bar(s0.t_s / 60, s0.score, width=4 / 60, color=np.where(s0.ictal, RED, "#9AB3CC"))
ax[0].set_xlim(0, 60); ax[0].set_ylim(0, 1.02); ax[0].set_yticks([0, 0.5, 1]); ax[0].set_ylabel("Score")
ax[0].set_title("(a) window view: 900 separate 4 s scores, 14 of them in the seizure (red); a ranking metric such as AUROC is computed here",
                loc="left", fontsize=14)
ax[1].axvspan(*(s0[s0.ictal].t_s.agg(["min", "max"]) / 60 + np.array([0, 4 / 60])), color="#F4C7C3", alpha=0.9, lw=0, label="annotated seizure")
ax[1].axvspan((s0[s0.ictal].t_s.min() - 30) / 60, (s0[s0.ictal].t_s.max() + 4 + 60) / 60, color="#EEF2F7", lw=0, zorder=0, label="tolerance −30 s / +60 s")
for _, r in ev.iterrows():
    ax[1].hlines(0.5, r.t0_s / 60, r.t1_s / 60, color=C["loc"], lw=14, label="event of the system")
ax[1].set_xlim(0, 60); ax[1].set_ylim(0, 1); ax[1].set_yticks([]); ax[1].spines["left"].set_visible(False)
ax[1].set_xlabel("Time in the first file of chb03 (min)")
ax[1].set_title("(b) event view (SzCORE): one seizure, one event → 1 detected, onset and offset errors, false alarms per day", loc="left", fontsize=14)
ax[1].legend(frameon=False, ncol=3, loc="upper center", bbox_to_anchor=(0.5, -0.45), fontsize=13.5)
save(fig, "B05_event_view.png")

print("ALL GATES PASSED")
