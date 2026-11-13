"""D11-A backup figures from committed results (read-only clone). Gates must pass before saving."""
import sys, numpy as np, pandas as pd, matplotlib
matplotlib.use("Agg"); import matplotlib.pyplot as plt
R = sys.argv[1] + "/results"; OUT = sys.argv[2]
from decimal import Decimal, ROUND_HALF_UP
hu = lambda v: Decimal(str(round(v, 3))).quantize(Decimal('0.01'), ROUND_HALF_UP)
BLUE, RED, GREY, INK = "#1F6FB2", "#DC433A", "#9AA3AD", "#222222"
plt.rcParams.update({"font.size": 15, "axes.spines.top": False, "axes.spines.right": False,
                     "font.family": "DejaVu Sans", "axes.edgecolor": "#555", "axes.labelcolor": INK})

# ---------- A: seeds & intervals, per-patient ----------
h = pd.read_csv(f"{R}/e22_test_oneshot/summary_per_seed.csv"); h = h[h.system == "final localized"]
f = pd.read_csv(f"{R}/e23_test_look7/summary_per_seed.csv"); f = f[(f.point == "balanced") & (f.system == "localized")]
hs, fs = h.s_sens.values, f.s_sens.values
assert round(hs.mean(), 3) == 0.498 and round(fs.mean(), 3) == 0.567, (hs.mean(), fs.mean())
assert round(h[h.seed == "clean_seed42"].s_sens.item(), 3) == 0.508 and round(f[f.seed == "clean_seed42"].s_sens.item(), 3) == 0.577
assert "+0.070 [+0.000, +0.201]" in open(f"{R}/e23_test_look7/SUMMARY.md").read()
assert "+0.498  [ +0.226,  +0.770]" in open(f"{R}/e22_test_oneshot/BOOTSTRAP.md").read()
fig, ax = plt.subplots(1, 2, figsize=(16, 5.2), gridspec_kw={"width_ratios": [1.6, 1]})
a = ax[0]
a.plot([0.226, 0.770], [1, 1], color=BLUE, lw=4, solid_capstyle="butt")
a.text(0.498, 1.13, "patient bootstrap 95 %: [0.226, 0.770]", ha="center", color=BLUE, fontsize=14)
a.scatter(hs, [1]*4, s=70, color=BLUE, zorder=3, edgecolor="white")
a.text(0.80, 1, f"4 seeds {hs.min():.3f}–{hs.max():.3f}", va="center", fontsize=13)
a.scatter(fs, [0]*4, s=70, color=GREY, zorder=3, edgecolor="white")
a.text(0.62, 0, f"4 seeds {fs.min():.3f}–{fs.max():.3f}", va="center", fontsize=13)
a.set_yticks([1, 0]); a.set_yticklabels(["held-out", "final\n(test-informed)"]); a.set_ylim(-0.6, 1.5)
a.set_xlim(0, 1); a.set_xlabel("Sensitivity, per-patient mean (8 test patients)")
a.set_title("(a) seed spread vs patient uncertainty", loc="left", fontsize=15)
b = ax[1]
b.axvline(0, color="#555", ls="--", lw=1)
b.plot([0.000, 0.201], [0, 0], color=BLUE, lw=4); b.scatter([0.070], [0], s=90, color=BLUE, zorder=3)
b.text(0.10, 0.25, "+0.070 [0.000, 0.201]", ha="center", fontsize=14)
b.set_yticks([]); b.set_ylim(-1, 1); b.set_xlim(-0.1, 0.35)
b.set_xlabel("Final − held-out, per-patient mean"); b.set_title("(b) gain of the final system", loc="left", fontsize=15)
fig.tight_layout(); fig.savefig(f"{OUT}/backup_seeds_intervals_perpatient.png", dpi=150); plt.close(fig)

# ---------- B: GAE-only 24-case cross-validation curve ----------
s = pd.read_csv(f"{R}/v9_x3/sys_sweep.csv"); s = s[s.arm == "GAE-CV"].copy()
assert s.subject.nunique() == 24
s["sens"] = s.tp / s.n_ref; s["fa"] = s.fp / s.nonict_h * 24
c = s.groupby("k_mult")[["sens", "fa"]].mean().sort_values("fa")
own = c.loc[1.0]
assert round(own.sens, 3) == 0.735 and round(own.fa, 1) == 28.4, own
test8 = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
tp8 = s[(s.k_mult == 1.0) & s.subject.isin(test8)].tp.sum(); assert tp8 == 37, tp8
fig, a = plt.subplots(figsize=(10, 5.6))
a.plot(c.fa, c.sens, "-o", color=BLUE, lw=2.5, ms=5)
a.scatter([own.fa], [own.sens], s=180, color=BLUE, edgecolor="black", zorder=4)
a.annotate(f"own label-free point\n{own.sens:.3f} at {own.fa:.1f} FA/day", (own.fa, own.sens),
           xytext=(own.fa + 15, own.sens - 0.18), fontsize=14, arrowprops=dict(arrowstyle="->", color="#555"))
a.set_xlim(0, c.fa.max() * 1.05); a.set_ylim(0, 1)
a.set_xlabel("False alarms per day (per-case mean)"); a.set_ylabel("Sensitivity (per-case mean)")
a.set_title("GAE, 4-fold patient-wise cross-validation, 24 cases (seed 42)", loc="left", fontsize=15)
a.text(0.99, 0.04, "each GAE trained on 17–19 patients;\nthe 8 original test patients: 37/76 found",
       transform=a.transAxes, ha="right", fontsize=13, color="#444")
fig.tight_layout(); fig.savefig(f"{OUT}/backup_gae_cv24.png", dpi=150); plt.close(fig)

# ---------- C: missed vs caught, two GAE detectors (no kNN) ----------
d = pd.read_csv(f"{R}/v9_v1/part1_descriptors.csv"); d = d[d.set != "siena"] if "siena" in d.set.unique() else d
d = d[d.subject.str.startswith("chb")]
assert len(d) == 185, len(d)
cg, mg = d[d.caught].amp_ratio, d[~d.caught].amp_ratio
assert (len(cg), len(mg)) == (115, 70) and round(cg.median(), 3) == 2.294 and round(mg.median(), 3) == 1.288
cv = pd.read_csv(f"{R}/v9_final/hard/gae_cv_seizures.csv")
cv = cv.merge(d[["subject", "file", "onset_s", "amp_ratio"]], on=["subject", "file", "onset_s"], how="inner")
assert len(cv) == 185
cvc, cvm = cv[cv.caught].amp_ratio, cv[~cv.caught].amp_ratio
assert round(cvc.median(), 3) == 2.220 and round(cvm.median(), 3) == 1.285, (cvc.median(), cvm.median())
fig, ax = plt.subplots(1, 2, figsize=(16, 5.6))
rng = np.random.default_rng(0)
for a, (name, cc, mm, dc, dm) in zip(ax, [
        ("Thesis GAE (seed 42)", cg, mg, d[d.caught].duration_s, d[~d.caught].duration_s),
        ("GAE, cross-validated", cvc, cvm, cv[cv.caught].duration_s, cv[~cv.caught].duration_s)]):
    for x, v, col in [(0, cc, BLUE), (1, mm, RED)]:
        a.scatter(x + rng.uniform(-0.18, 0.18, len(v)), v, s=14, color=col, alpha=0.5)
        a.plot([x - 0.28, x + 0.28], [v.median()] * 2, color="black", lw=3)
        a.text(x + 0.32, v.median(), f"{hu(v.median())}×", va="center", fontsize=14)
    a.set_yscale("log"); a.set_yticks([0.5, 1, 2, 4, 8, 16]); a.set_yticklabels(["0.5", "1", "2", "4", "8", "16"])
    a.set_xticks([0, 1]); a.set_xticklabels([f"caught (n={len(cc)})\nmedian {dc.median():.0f} s",
                                              f"missed (n={len(mm)})\nmedian {dm.median():.0f} s"])
    a.set_xlim(-0.5, 1.7); a.set_title(name, loc="left", fontsize=15)
ax[0].set_ylabel("Amplitude ratio\n(seizure RMS / minute before)")
fig.suptitle("185 CHB-MIT seizures — missed seizures barely rise above the patient's own background (p < 0.0001)",
             x=0.01, ha="left", fontsize=15)
fig.tight_layout(); fig.savefig(f"{OUT}/backup_missed_amplitude_2gae.png", dpi=150); plt.close(fig)
print("ALL GATES PASSED", own.sens, own.fa, tp8, hs.mean(), fs.mean())
