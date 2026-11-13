"""D4g appendix figures (coded; read committed result files only; never recompute a result).

Gates (assert, fail fast) check every drawn count against the report / NUMBERS_LOCK before saving.
  F1  annotation map  <- results/attribution_v7/labels/ictal_channels_FINAL.csv
      gates: 76 seizures; 62 focal + 14 generalized; 282 focal labels; T7-P7 = 45; FP total 116;
             five channels never annotated (C3-P3, C4-P4, P4-O2, FZ-CZ, CZ-PZ).            (NL §7)
  A2  seizure durations per case <- results/p3_seizure_burden/burden.txt
      gates: test seizures 76 (7,10,12,8,20,10,3,6); min 6 s (chb16), max 205 s (chb15);
             test seizures < 20 s by annotation = 23.                                      (NL §2)
Usage: python figs_d4g.py <repo> <outdir>
"""
import sys, csv, re, os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib import font_manager as fm

REPO, OUT = sys.argv[1], sys.argv[2]
os.makedirs(OUT, exist_ok=True)
for f in fm.findSystemFonts():
    if "Carlito" in f:
        fm.fontManager.addfont(f)
plt.rcParams.update({"font.family": "Carlito", "font.size": 15, "axes.edgecolor": "#5F6B7A",
                     "axes.labelcolor": "#1E2430", "xtick.color": "#1E2430", "ytick.color": "#1E2430"})

INK, MUTED, GRID = "#1E2430", "#5F6B7A", "#E3E8EF"
SET_COL = {"training": "#8FB4D9", "validation": "#E69F00", "test": "#1F6FB2"}

# ---------------------------------------------------------------- F1 annotation map
CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
      "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
rows = list(csv.DictReader(open(f"{REPO}/results/attribution_v7/labels/ictal_channels_FINAL.csv")))
assert len(rows) == 76
foc = [r for r in rows if r["focal_generalized"] == "focal"]
gen = [r for r in rows if r["focal_generalized"] == "generalized"]
assert len(foc) == 62 and len(gen) == 14
cnt = {c: 0 for c in CH}
for r in foc:
    for c in r["ictal_channels"].split("|"):
        cnt[c] += 1
assert sum(cnt.values()) == 282 and cnt["T7-P7"] == 45
assert cnt["FP1-F7"] + cnt["FP1-F3"] + cnt["FP2-F4"] + cnt["FP2-F8"] == 116
assert [c for c in CH if cnt[c] == 0] == ["C3-P3", "C4-P4", "P4-O2", "FZ-CZ", "CZ-PZ"]

subj_order = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
rows.sort(key=lambda r: (subj_order.index(r["subject"]), int(r["seizure_idx"])))
import numpy as np
M = np.zeros((18, 76))
for j, r in enumerate(rows):
    if r["focal_generalized"] == "generalized":
        M[:, j] = 1
    else:
        for c in r["ictal_channels"].split("|"):
            M[CH.index(c), j] = 2
from matplotlib.colors import ListedColormap
cmap = ListedColormap(["#EEF2F7", "#B9CCE0", "#1F6FB2"])
fig, ax = plt.subplots(figsize=(14.0, 6.0), dpi=150)
ax.imshow(M, aspect="auto", cmap=cmap, vmin=0, vmax=2, interpolation="nearest")
ax.set_yticks(range(18)); ax.set_yticklabels(CH, fontsize=16)
ax.set_xticks([])
start = 0
for s in subj_order:
    n = sum(1 for r in rows if r["subject"] == s)
    if start > 0:
        ax.axvline(start - 0.5, color="white", lw=3)
    ax.text(start + n / 2 - 0.5, -1.0, f"{s}\n({n})", ha="center", va="bottom", fontsize=16, color=INK)
    start += n
for y in (3.5, 7.5, 11.5, 15.5):
    ax.axhline(y, color="white", lw=1.5)
ax.set_xlabel("76 test seizures in file order, grouped by patient (number of seizures in brackets)", fontsize=17, color=MUTED)
for sp in ax.spines.values():
    sp.set_visible(False)
ax.tick_params(length=0)
from matplotlib.patches import Patch
ax.legend(handles=[Patch(color="#1F6FB2", label="annotated ictal channel (focal seizure)"),
                   Patch(color="#B9CCE0", label="generalized: all 18 channels"),
                   Patch(color="#EEF2F7", label="not annotated")],
          loc="upper center", bbox_to_anchor=(0.5, -0.08), ncol=3, frameon=False, fontsize=17)
fig.tight_layout()
fig.savefig(f"{OUT}/F1_annotation_map.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("F1 ok: 76 seizures, 62 focal, 14 generalized, 282 labels")

# ---------------------------------------------------------------- A2 seizure durations per case
txt = open(f"{REPO}/results/p3_seizure_burden/burden.txt").read().splitlines()
pat = re.compile(r"^(chb\d\d)\s+(test|non-test)\s+(\d+)\s+(\d+)\s+(\d+)/\s*(\d+)/\s*(\d+)\s+(\d+)\s+\S+\s+(\S+)")
recs = []
for line in txt:
    m = pat.match(line)
    if m:
        s, st, nsum, nv2, med, mn, mx, short, rec_h = m.groups()
        recs.append(dict(s=s, set=st, n=int(nsum), nv2=int(nv2), med=int(med), mn=int(mn), mx=int(mx),
                         short=int(short), h=float(rec_h)))
assert len(recs) == 23
VAL = {"chb10", "chb11", "chb22"}
for r in recs:
    r["grp"] = "test" if r["set"] == "test" else ("validation" if r["s"] in VAL else "training")
test = [r for r in recs if r["grp"] == "test"]
assert [r["n"] for r in sorted(test, key=lambda r: r["s"])] == [7, 10, 12, 8, 20, 10, 3, 6]
assert sum(r["short"] for r in test) == 23
assert min(r["mn"] for r in test) == 6 and max(r["mx"] for r in test) == 205
order = sorted(recs, key=lambda r: (["training", "validation", "test"].index(r["grp"]), r["s"]))
fig, ax = plt.subplots(figsize=(13.0, 6.2), dpi=150)
for i, r in enumerate(order):
    c = SET_COL[r["grp"]]
    ax.plot([i, i], [r["mn"], r["mx"]], color=c, lw=7, solid_capstyle="round")
    ax.plot(i, r["med"], "o", ms=10, color="white", mec=INK, mew=1.6)
    ax.text(i, 3.1, f"{r['n']}", ha="center", va="bottom", fontsize=17, color=INK)
ax.axhline(20, color="#C62828", lw=1.4, ls="--")
ax.text(len(order) - 0.4, 21.5, "20 s", color="#C62828", fontsize=18, ha="right", va="bottom")
ax.set_yscale("log"); ax.set_ylim(2.6, 2600)
ax.set_yticks([5, 10, 20, 50, 100, 200, 500]); ax.set_yticklabels(["5", "10", "20", "50", "100", "200", "500"])
ax.set_xticks(range(len(order))); ax.set_xticklabels([r["s"] for r in order], rotation=45, ha="right", fontsize=17)
ax.set_ylabel("Seizure duration (s, log scale)", fontsize=19)
ax.text(-0.9, 3.1, "n =", ha="right", va="bottom", fontsize=17, color=MUTED)
ax.set_xlim(-1.6, len(order) - 0.3)
ax.grid(axis="y", color=GRID, lw=1); ax.set_axisbelow(True)
for sp in ("top", "right"):
    ax.spines[sp].set_visible(False)
from matplotlib.lines import Line2D
ax.legend(handles=[Line2D([], [], color=SET_COL["training"], lw=7, label="training (12)"),
                   Line2D([], [], color=SET_COL["validation"], lw=7, label="validation (3)"),
                   Line2D([], [], color=SET_COL["test"], lw=7, label="test (8)"),
                   Line2D([], [], color="white", marker="o", mec=INK, mew=1.6, ms=10, lw=0, label="median")],
          loc="upper left", ncol=4, frameon=False, fontsize=18)
fig.tight_layout()
fig.savefig(f"{OUT}/A2_durations.png", bbox_inches="tight", facecolor="white")
plt.close(fig)
print("A2 ok: 23 cases; test 76 seizures, 23 < 20 s, 6-205 s")
