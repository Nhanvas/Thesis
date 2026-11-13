"""D9 coded figures (after the review). Reads committed result files of the repository only (tag v9-results);
never recomputes a result. Every plotted value is gated against NUMBERS_LOCK §17 before drawing.

Usage: python -I d9_figs.py <repo_root> <out_dir>
"""
import re
import sys
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from matplotlib import font_manager

REPO = Path(sys.argv[1])
OUT = Path(sys.argv[2])
OUT.mkdir(parents=True, exist_ok=True)
R = REPO / "results"

for f in font_manager.findSystemFonts():
    if "Carlito" in f:
        font_manager.fontManager.addfont(f)
plt.rcParams.update({
    "font.family": "Carlito", "font.size": 17, "axes.spines.top": False, "axes.spines.right": False,
    "axes.edgecolor": "#5F6B7A", "axes.labelcolor": "#1E2430", "xtick.color": "#1E2430",
    "ytick.color": "#1E2430", "axes.grid": True, "grid.color": "#E3E8EE", "grid.linewidth": 0.8,
    "axes.axisbelow": True, "savefig.dpi": 200, "savefig.bbox": "tight", "savefig.facecolor": "white",
})
BLUE, ORANGE, TEAL, INK, MUTED = "#1F6FB2", "#C8641E", "#2F9A78", "#1E2430", "#5F6B7A"


def gate(name, got, want, tol=0.0005):
    if abs(got - want) > tol:
        raise SystemExit(f"GATE FAIL {name}: file {got} vs lock {want}")
    print(f"gate ok  {name}: {got:.3f}")


def curve_block(summary_text, section_title):
    """Per-patient-mean sensitivity at 20 / 27.5 / 44 FP/day (system stage) for G, B4, F in one section."""
    sec = summary_text.split(section_title, 1)[1]
    blk = sec.split("System-stage curve", 1)[1].split("```")[1]
    out = {}
    for arm in ("G", "B4", "F"):
        line = [l for l in blk.splitlines() if l.startswith(arm + " ")][0]
        vals = dict(re.findall(r"(\d+\.?\d*):(NA|\d\.\d+)", line))
        out[arm] = {k: (np.nan if v == "NA" else float(v)) for k, v in vals.items()}
    return out


# ---------------------------------------------------------------- 1 · model comparison (p18)
s = (R / "v9_e1b/SUMMARY.md").read_text(encoding="utf-8")
sets = [("Development (15)", "## Development"), ("CHB-MIT test (8)", "## CHB-MIT held-out test"),
        ("chb24", "## chb24"), ("Siena (14)", "## Siena")]
heads = [h for h in re.findall(r"^## .*$", s, flags=re.M)]
vals = {}
for label, key in sets:
    title = [h for h in heads if h.startswith(key)][0]
    c = curve_block(s, title)
    vals[label] = [c["G"]["27.5"], c["F"]["27.5"], c["B4"]["27.5"]]
lock = {"Development (15)": (0.837, 0.902, 0.919), "CHB-MIT test (8)": (0.554, 0.601, 0.607),
        "chb24": (0.820, 0.913, 0.830), "Siena (14)": (0.492, 0.553, 0.595)}
for k, v in vals.items():
    for nm, a, b in zip(("GAE", "GAE+kNN", "kNN"), v, lock[k]):
        gate(f"model {k} {nm}", a, b)
pd_ = pd.read_csv(R / "v9_e2/paired/paired_sens.csv")
row = pd_[(pd_.set == "test") & (pd_.pair == "F-G") & (pd_.fa_target == 27.5)].iloc[0]
gate("paired F-G test diff", row.mean_diff, 0.047); gate("paired lo", row.ci_lo, 0.013); gate("paired hi", row.ci_hi, 0.086)

fig, ax = plt.subplots(figsize=(10.5, 5.6))
x = np.arange(len(sets)); w = 0.26
names = ["GAE (thesis system)", "GAE + kNN", "kNN on the same channel features"]
for i, (nm, col) in enumerate(zip(names, (BLUE, ORANGE, TEAL))):
    ys = [vals[l][i] for l, _ in sets]
    bars = ax.bar(x + (i - 1) * w, ys, w - 0.03, color=col, label=nm, zorder=3)
    for b, y in zip(bars, ys):
        ax.text(b.get_x() + b.get_width() / 2, y + 0.012, f"{y:.3f}", ha="center", va="bottom", fontsize=13.5, color=INK)
ax.set_xticks(x, [l for l, _ in sets])
ax.set_ylim(0, 1.05)
ax.set_ylabel("Per-patient mean sensitivity\nat 27.5 false alarms per day")
ax.grid(axis="x", visible=False)
ax.legend(loc="upper center", bbox_to_anchor=(0.5, -0.1), ncol=3, frameon=False, fontsize=15)
ax.text(1, 0.70, "GAE + kNN − GAE:\n+0.047 [+0.013, +0.086]", fontsize=14, color=INK, ha="center")
fig.savefig(OUT / "d9_model_comparison.png")
plt.close(fig)

# ---------------------------------------------------------------- 2 · Siena explained (p20)
a14 = (R / "v9_anatomy/siena14/SUMMARY.md").read_text(encoding="utf-8")
curves = {}
for key in ("chb-test", "chb24", "siena-14"):
    line = [l for l in a14.splitlines() if l.startswith(f"- {key}: sensitivity")][0]
    curves[key] = [float(v) for v in re.findall(r"=(\d\.\d+)", line)]
gate("siena 27.5", curves["siena-14"][1], 0.534); gate("test 27.5", curves["chb-test"][1], 0.355)
gate("chb24 27.5", curves["chb24"][1], 0.875)
gate("siena 20", curves["siena-14"][0], 0.481); gate("siena 44", curves["siena-14"][2], 0.673)
gate("test 20", curves["chb-test"][0], 0.318); gate("test 44", curves["chb-test"][2], 0.366)
db = pd.concat([pd.read_csv(R / "v9_anatomy/duration_bins.csv"), pd.read_csv(R / "v9_anatomy/siena14/duration_bins.csv")])
t = db[db.set == "chb-test"].set_index("bin"); sn = db[db.set == "siena-14"].set_index("bin")
bins = ["<=20s", "21-40s", "41-80s", ">80s"]
gate("test <=20 n", t.loc["<=20s", "n"], 24, 0); gate("siena <=20 n", sn.loc["<=20s", "n"], 5, 0)
gate("test total", t.n.sum(), 76, 0); gate("siena total", sn.n.sum(), 47, 0)
gate("test caught", t.caught.sum(), 38, 0)  # detector stage, overlap count: 7+4+16+11
fig, (a1, a2) = plt.subplots(1, 2, figsize=(12.5, 5.0), gridspec_kw={"width_ratios": [1, 1.15]})
fa = [20, 27.5, 44]
for key, lab, col in (("chb-test", "CHB-MIT test (8)", BLUE), ("chb24", "chb24", TEAL), ("siena-14", "Siena (14)", ORANGE)):
    a1.plot(fa, curves[key], "-o", color=col, lw=2.2, ms=8, label=lab, zorder=3)
    a1.text(44.8, curves[key][2], lab, va="center", fontsize=14, color=INK)
a1.axvline(27.5, color=MUTED, lw=1, ls="--")
a1.set_xlim(17, 58); a1.set_ylim(0, 1.0)
a1.set_xticks(fa, ["20", "27.5", "44"])
a1.set_xlabel("False alarms per day (matched)"); a1.set_ylabel("Pooled sensitivity (seed 42)")
a1.set_title("(a) same false-alarm rate", loc="left", fontsize=17)
a1.text(28.2, curves["siena-14"][1] + 0.04, f"{curves['siena-14'][1]:.3f}", fontsize=14, color=INK)
a1.text(28.2, curves["chb-test"][1] - 0.08, f"{curves['chb-test'][1]:.3f}", fontsize=14, color=INK)
xb = np.arange(4); w = 0.38
lab_bins = ["≤ 20 s", "21–40 s", "41–80 s", "> 80 s"]
for i, (df, lab, col) in enumerate(((t, "CHB-MIT test", BLUE), (sn, "Siena", ORANGE))):
    share = df.loc[bins, "n"].values / df.n.sum()
    bars = a2.bar(xb + (i - 0.5) * w, share, w - 0.04, color=col, label=lab, zorder=3)
    for b, (n, c) in zip(bars, zip(df.loc[bins, "n"], df.loc[bins, "caught"])):
        a2.text(b.get_x() + b.get_width() / 2, b.get_height() + 0.012, f"{c}/{n}", ha="center", fontsize=13, color=INK)
a2.set_xticks(xb, lab_bins); a2.set_ylim(0, 0.68)
a2.set_ylabel("Share of seizures"); a2.set_xlabel("Seizure duration (annotation)")
a2.set_title("(b) duration mix · caught / total per bin", loc="left", fontsize=17)
a2.grid(axis="x", visible=False); a2.legend(frameon=False, fontsize=14, loc="upper left")
fig.tight_layout(w_pad=3)
fig.savefig(OUT / "d9_siena_explained.png")
plt.close(fig)

# ---------------------------------------------------------------- 3 · hard patients (p19)
d = pd.read_csv(R / "v9_v1/part1_descriptors.csv")
low = {"chb06", "chb12", "chb13", "chb15", "chb16", "chb21"}
c = d[d.subject.str.startswith("chb")].copy()
c["low"] = c.subject.isin(low)
med = c.groupby("low")[["spatial_extent", "amp_ratio", "duration_s"]].median()
gate("hard channels", med.loc[True, "spatial_extent"], 1, 0); gate("other channels", med.loc[False, "spatial_extent"], 13, 0)
gate("hard amp", med.loc[True, "amp_ratio"], 1.27, 0.005); gate("other amp", med.loc[False, "amp_ratio"], 2.58, 0.005)
gate("hard dur", med.loc[True, "duration_s"], 36, 0); gate("other dur", med.loc[False, "duration_s"], 62, 0)
rng = np.random.default_rng(0)
fig, ax = plt.subplots(figsize=(9.6, 6.0))
for is_low, col, lab in ((False, BLUE, "other 18 cases"), (True, ORANGE, "6 hard cases (chb06, 12, 13, 15, 16, 21)")):
    g = c[c.low == is_low]
    xj = g.spatial_extent + rng.uniform(-0.28, 0.28, len(g))
    ax.scatter(xj[g.caught], g.amp_ratio[g.caught], s=46, color=col, edgecolor="white", lw=0.8, zorder=3, label=f"{lab}, detected")
    ax.scatter(xj[~g.caught], g.amp_ratio[~g.caught], s=46, facecolor="white", edgecolor=col, lw=1.6, zorder=3, label=f"{lab}, missed")
    ax.scatter([med.loc[is_low, "spatial_extent"]], [med.loc[is_low, "amp_ratio"]], marker="D", s=170, color=col,
               edgecolor=INK, lw=1.4, zorder=4)
ax.annotate("median: 1 channel, 1.27×", (1, 1.27), xytext=(3.2, 0.62), fontsize=15, color=INK,
            arrowprops=dict(arrowstyle="-", color=MUTED))
ax.annotate("median: 13 channels, 2.58×", (13, 2.58), xytext=(7.0, 6.2), fontsize=15, color=INK,
            arrowprops=dict(arrowstyle="-", color=MUTED))
ax.set_yscale("log"); ax.set_yticks([0.5, 1, 2, 4, 8], ["0.5×", "1×", "2×", "4×", "8×"])
ax.set_xticks([0, 1, 3, 6, 9, 12, 15, 18]); ax.set_xlim(-0.6, 18.8)
ax.set_xlabel("Channels involved (of 18)"); ax.set_ylabel("Amplitude vs the minute before")
ax.legend(frameon=False, fontsize=12.5, loc="upper left", ncol=1)
fig.savefig(OUT / "d9_hard_patients.png")
plt.close(fig)
print("hard-patient seizures plotted:", len(c), "(hard", int(c.low.sum()), ")")

# ---------------------------------------------------------------- 4 · five representations (I2)
s1 = (R / "v9_e1/SUMMARY.md").read_text(encoding="utf-8")
blk = s1.split("## CHB-MIT held-out test", 1)[1].split("### Matched operating point", 1)[1].split("```")[1]
rep = {}
for key in ("G ", "B1 ", "B2 ", "B3 ", "B4 ", "F "):
    line = [l for l in blk.splitlines() if l.startswith(key)][0]
    rep[key.strip()] = float(re.search(r"27\.5:(\d\.\d+)", line).group(1))
for k, v in {"G": 0.342, "B2": 0.106, "B4": 0.467, "F": 0.396, "B1": 0.242, "B3": 0.301}.items():
    gate(f"rep {k}", rep[k], v)
order = [("B2", "Connectivity only (adjacency + Mahalanobis)"), ("B1", "Channel features + Mahalanobis"),
         ("B3", "Channel features + Isolation Forest"), ("G", "GAE (thesis system)"),
         ("F", "GAE + kNN"), ("B4", "Channel features + kNN")]
cols = {"G": BLUE, "F": ORANGE, "B4": TEAL}
fig, ax = plt.subplots(figsize=(10.5, 4.6))
ys = np.arange(len(order))
for y, (k, lab) in zip(ys, order):
    ax.barh(y, rep[k], 0.62, color=cols.get(k, "#9AA5B4"), zorder=3)
    ax.text(rep[k] + 0.008, y, f"{rep[k]:.3f}", va="center", fontsize=15, color=INK)
ax.set_yticks(ys, [l for _, l in order]); ax.set_xlim(0, 0.56)
ax.set_xlabel("Pooled sensitivity at 27.5 false alarms per day")
ax.grid(axis="y", visible=False)
fig.savefig(OUT / "d9_five_representations.png")
plt.close(fig)

# ---------------------------------------------------------------- 5 · kNN on all 24 cases (I4)
e4 = pd.read_csv(R / "v9_e4/per_subject.csv")
e4 = e4[(e4.arm == "loo") & (e4.stage == "localized")].copy()
e4["sens"] = e4.tp / e4.n_ref
gate("knn 24 per-case mean", e4.sens.mean(), 0.763, 0.001)
test8 = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
gate("knn test-group mean", e4[e4.subject.isin(test8)].sens.mean(), 0.565, 0.001)
e4["grp"] = np.where(e4.subject.isin(test8), "test", np.where(e4.subject == "chb24", "chb24", "dev"))
e4 = e4.sort_values(["grp", "subject"], key=lambda s: s.map({"dev": 0, "test": 1, "chb24": 2}) if s.name == "grp" else s)
fig, ax = plt.subplots(figsize=(13.5, 4.8))
xs = np.arange(len(e4))
colr = [ORANGE if v < 0.35 else BLUE for v in e4.sens]
ax.bar(xs, e4.sens, 0.72, color=colr, zorder=3)
ax.set_xticks(xs, [s.replace("chb", "") for s in e4.subject], fontsize=14)
ax.axhline(0.35, color=MUTED, lw=1, ls="--"); ax.text(-0.45, 0.37, "0.35", fontsize=13, color=MUTED, ha="left")
nd = int((e4.grp == "dev").sum())
ax.axvline(nd - 0.5, color=INK, lw=1); ax.axvline(nd + 7.5, color=INK, lw=1)
ax.text((nd - 1) / 2, 1.07, "former development (15): 0.866", ha="center", fontsize=15)
ax.text(nd + 3.5, 1.07, "former test (8): 0.565", ha="center", fontsize=15)
ax.set_ylim(0, 1.15); ax.set_ylabel("Sensitivity per case")
ax.set_xlabel("CHB-MIT case (chb…); orange = below 0.35")
ax.grid(axis="x", visible=False)
fig.savefig(OUT / "d9_knn_24_cases.png")
plt.close(fig)
gate("knn dev mean", e4[e4.grp == "dev"].sens.mean(), 0.866, 0.001)
print("ALL GATES PASSED")
