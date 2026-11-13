#!/usr/bin/env python
"""
make_defense_figs.py -- result figures R1-R12 of the defense deck (chat D4c, 2026-10-17; R5 retired in D4d).

Lives OUTSIDE the repository: F:/Study/Thesis/Defense/slides/figs/  (precedent D1b).

Integrity (instructions rule 2b.2, 6.13):
  * every value is READ from a committed result file of github.com/Nhanvas/Thesis (or, for R12, from the
    design table of the report, Table 8); nothing is recomputed from EEG, scores or caches;
  * the repository's own figure module src/figures_v8/make_v8_exhibits.py is IMPORTED for its readers
    (e22/e23/x1 per-patient rows, pooled / per-patient-mean aggregation = the report's Tables 11-17);
  * every figure has a GATE: the values it prints must equal NUMBERS_LOCK.md (written as there); a mismatch
    stops the script before anything is written.

Style (DECK_BRIEF section 5, SLIDE_OUTLINE rev 2 section 3): Inter; teal = this work, orange = limit,
grey = others, purple = the one other label-free method; no title inside a figure (the slide carries it);
ticks >= 12 pt; one muted footer line with set · seed · aggregate; PNG 200 dpi (transparent) + SVG
(text kept as text, font Inter).

Layered exports (Canva "appear" animation, author decision P-D2): R1 and R3 also write
layers/<fig>_L<k>_<name>.png -- same canvas, transparent, each holding only the marks added at that step;
stacking them in order gives the full figure.

Run (laptop, Git Bash):  python make_defense_figs.py --repo F:/Study/Thesis/Code
Run (cloud clone):       python make_defense_figs.py --repo ~/Thesis --out ./out
Runtime: about 20 s (measured in the cloud container, 2026-10-17).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import numpy as np

# ─────────────────────────────── paths, repo module ───────────────────────────────
ap = argparse.ArgumentParser()
ap.add_argument("--repo", default=str(Path(__file__).resolve().parents[3] / "Code"),
                help="root of the Thesis repository (default F:/Study/Thesis/Code)")
ap.add_argument("--out", default=str(Path(__file__).resolve().parent), help="output folder (default: this folder)")
ap.add_argument("--smoke", action="store_true", help="run the gates only, write nothing")
ARGS = ap.parse_args()
REPO = Path(ARGS.repo).expanduser().resolve()
if not (REPO / "src/figures_v8/make_v8_exhibits.py").exists():
    raise SystemExit(f"STOP: {REPO} is not the Thesis repository (src/figures_v8/make_v8_exhibits.py missing)")
sys.path.insert(0, str(REPO / "src/figures_v8"))
import make_v8_exhibits as X  # noqa: E402  (readers + gate of the report's figure script)
import pandas as pd  # noqa: E402
import matplotlib  # noqa: E402
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Ellipse, FancyArrowPatch  # noqa: E402

R = REPO / "results"
OUT = Path(ARGS.out).expanduser().resolve()
TEST = X.TEST
SEEDS = X.SEEDS

# ─────────────────────────────── style (DECK_BRIEF §5) ───────────────────────────────
INK, MUTED, GRID = "#211C29", "#6F6579", "#E6E1EA"
TEAL, TEAL_L = "#146F70", "#E3F1F0"
ORANGE, ORANGE_D, ORANGE_L = "#C8693A", "#A8522A", "#FBEFE8"
PURPLE, GREY, GREY_L = "#8C5AA6", "#8A7F96", "#D9D3DF"
plt.rcParams.update({
    "font.family": "Inter", "font.size": 14, "axes.labelsize": 15, "xtick.labelsize": 13, "ytick.labelsize": 13,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED, "text.color": INK,
    "axes.spines.top": False, "axes.spines.right": False, "axes.linewidth": 1.0, "axes.grid": False,
    "svg.fonttype": "none", "savefig.dpi": 200, "savefig.transparent": True, "legend.frameon": False,
})
FULL, HALF = (12.8, 5.6), (6.4, 5.4)          # inches: 16:9 content area / half width
SHOWN = {}                                    # figure -> list of printed numbers (for HANDBACK_R.md)
SOURCES = {}                                  # figure -> source files


def stop(msg):
    raise SystemExit(f"STOP (gate): {msg}")


def gate(cond, msg):
    if not cond:
        stop(msg)


def footer(fig, text):
    return fig.text(0.012, 0.018, text, fontsize=12, color=MUTED, ha="left", va="bottom")


def grid_y(ax):
    ax.yaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)


def grid_x(ax):
    ax.xaxis.grid(True, color=GRID, lw=0.8); ax.set_axisbelow(True)


class Layers:
    """Register artists per reveal step; export each step on the same transparent canvas."""

    def __init__(self, fig, names):
        self.fig, self.names, self.reg = fig, names, {n: [] for n in names}

    def add(self, name, *artists):
        for a in artists:
            if isinstance(a, (list, tuple)):
                self.add(name, *a)
            elif a is not None:
                self.reg[name].append(a)

    def _all_artists(self):
        out = list(self.fig.texts)
        for ax in self.fig.axes:
            out += list(ax.lines) + list(ax.collections) + list(ax.patches) + list(ax.texts) + list(ax.artists)
        return out

    def export(self, stem):
        registered = {id(a) for v in self.reg.values() for a in v}
        base = self.names[0]
        self.reg[base] += [a for a in self._all_artists() if id(a) not in registered]
        (OUT / "layers").mkdir(parents=True, exist_ok=True)
        for k, name in enumerate(self.names):
            keep = {id(a) for a in self.reg[name]}
            for a in self._all_artists():
                a.set_visible(id(a) in keep)
            for ax in self.fig.axes:
                ax.set_axis_on() if name == base else ax.set_axis_off()
            self.fig.savefig(OUT / "layers" / f"{stem}_L{k}_{name}.png")
        for a in self._all_artists():
            a.set_visible(True)
        for ax in self.fig.axes:
            ax.set_axis_on()


def save(fig, stem, shown, sources):
    SHOWN[stem], SOURCES[stem] = shown, sources
    if ARGS.smoke:
        plt.close(fig); return
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / f"{stem}.png"); fig.savefig(OUT / f"{stem}.svg")
    plt.close(fig)


def rx(path, pattern, cast=float):
    """Read one number (or group tuple) from a committed text file."""
    txt = (R / path).read_text(encoding="utf-8")
    m = re.search(pattern, txt, re.M)
    if not m:
        stop(f"pattern not found in {path}: {pattern}")
    g = m.groups()
    return cast(g[0]) if len(g) == 1 else tuple(cast(v) for v in g)


def ledger(step, arm):
    d = pd.read_csv(R / "p2_ledger.csv")
    r = d[(d.step == step) & (d.arm == arm)]
    gate(len(r) == 1, f"ledger row {step}/{arm}")
    return r.iloc[0]


# ════════════════════════════════════════ R1 ════════════════════════════════════════
def r1_development():
    """Development path, 15 development patients, pooled sensitivity at <= 25 FP/day."""
    v1 = rx("e8_gae_v2/SUMMARY.md", r"V1 \(locked\): best sens FA/day<=25 = ([\d.]+)")
    v2 = rx("p2_bootstrap/SUMMARY_C_Ce.md", r"E pooled ([\d.]+) @ ([\d.]+) FA/day")[0]
    lat = rx("e16_recording_baseline/SUMMARY_a.md", r"^S9base\s+([\d.]+)")
    dr = float(ledger("E21-1", "E16e").best_le25)
    fin, fin_s = rx("p3c_freeze/SUMMARY.md", r"^L2f cpd\s+([\d.]+) @ [\d.]+ \| subject-mean ([\d.]+)")
    e22 = pd.read_csv(R / "e22_test_oneshot/summary_per_seed.csv")
    h4 = e22[e22.system == "final localized"].sens.mean()
    vals = [round(v1, 3), round(v2, 3), round(lat, 3), round(dr, 3), round(fin, 3)]
    gate(vals == [0.330, 0.489, 0.612, 0.681, 0.670] and round(fin_s, 3) == 0.832 and round(h4, 3) == 0.336,
         f"R1 values {vals}, {fin_s}, held-out {h4}")

    fig = plt.figure(figsize=FULL)
    ax = fig.add_axes([0.075, 0.30, 0.90, 0.66])
    L = Layers(fig, ["base", "amplitude", "channel", "drift", "final", "heldout"])
    names = ["Earlier score", "+ amplitude\nfeatures", "Channel-level\nlatent", "+ drift\ncorrection", "Final system"]
    causes = [None, "removes: amplitude\nwas erased", "removes: graph-level\naveraging", "removes:\nfile-level drift",
              "+ ensemble, alarm\nbudget, change points"]
    x = np.arange(5)
    ax.set_xlim(-0.5, 4.6); ax.set_ylim(0, 0.85); ax.set_yticks([0, 0.2, 0.4, 0.6, 0.8])
    ax.set_ylabel("Pooled sensitivity\n(≤ 25 false alarms / day)")
    ax.set_xticks(x, names, fontsize=14, color=INK)
    ax.spines["bottom"].set_color(GREY_L); ax.tick_params(axis="x", length=0, pad=10)
    grid_y(ax)
    layer_of = ["base", "amplitude", "channel", "drift", "final"]
    for i in range(5):
        lay = layer_of[i]
        col = GREY if i == 0 else TEAL
        if i > 0:
            L.add(lay, ax.plot([x[i - 1], x[i]], [vals[i - 1], vals[i]], color=TEAL, lw=2.2, zorder=2))
        face = "white" if i == 0 else (TEAL if i == 4 else TEAL_L)
        L.add(lay, ax.scatter([x[i]], [vals[i]], s=150 if i == 4 else 110, facecolor=face, edgecolor=col, lw=2.2, zorder=3))
        L.add(lay, ax.text(x[i], vals[i] + 0.045, f"{vals[i]:.3f}", ha="center", va="bottom", fontsize=17,
                           fontweight="bold" if i == 4 else "semibold", color=INK if i else MUTED))
        if causes[i]:
            L.add(lay, ax.text(x[i], -0.235, causes[i], ha="center", va="top", fontsize=12.5,
                               color=ORANGE_D if i < 4 else MUTED, transform=ax.get_xaxis_transform()))
    L.add("base", ax.text(x[0], vals[0] - 0.06, "seed 42 only", ha="center", va="top", fontsize=12, color=MUTED))
    L.add("final", ax.text(x[4], vals[4] - 0.07, f"per-patient mean {fin_s:.3f}", ha="center", va="top",
                           fontsize=13, color=TEAL))
    # held-out reference (separate layer): the same final system on the unseen test patients, 4 seeds, pooled
    L.add("heldout", ax.add_patch(FancyArrowPatch((x[4], vals[4] - 0.115), (x[4], h4 + 0.03), arrowstyle="-|>",
                                                  mutation_scale=18, color=ORANGE, lw=2, ls=(0, (4, 3)), zorder=2)))
    L.add("heldout", ax.scatter([x[4]], [h4], s=150, marker="D", facecolor="white", edgecolor=ORANGE, lw=2.2, zorder=3))
    L.add("heldout", ax.text(x[4] - 0.12, h4, f"held-out test\npatients: {h4:.3f}", ha="right", va="center",
                             fontsize=14, color=ORANGE_D, fontweight="semibold"))
    footer(fig, "Development patients (15) · 4 seeds (earlier score: seed 42) · pooled sensitivity, best point "
                "≤ 25 false alarms per day; orange: same system on the test patients")
    if not ARGS.smoke:
        OUT.mkdir(parents=True, exist_ok=True); L.export("R1_development_path")
    save(fig, "R1_development_path",
         ["0.330 (seed 42)", "0.489", "0.612", "0.681", "0.670", "per-patient mean 0.832", "held-out 0.336 (4 seeds)"],
         ["results/e8_gae_v2/SUMMARY.md l.3 (V1 0.330)", "results/p2_bootstrap/SUMMARY_C_Ce.md l.15 (E 0.489 @ 20.06, 4 seeds)",
          "results/e16_recording_baseline/SUMMARY_a.md (S9base 0.612)", "results/p2_ledger.csv E21-1/E16e (0.6809)",
          "results/p3c_freeze/SUMMARY.md (L2f cpd 0.670, subject-mean 0.832)",
          "results/e22_test_oneshot/summary_per_seed.csv (final localized, 4-seed mean 0.336)"])


# ════════════════════════════════════════ R3 ════════════════════════════════════════
def r3_unseen_patients():
    h = X.e22_per_subject(); f = X.e23_per_subject()
    h42 = h[h.seed == "clean_seed42"].set_index("subject").loc[TEST]
    f42 = f[f.seed == "clean_seed42"].set_index("subject").loc[TEST]
    gate((h42.tp.sum(), h42.fp.sum(), f42.tp.sum(), f42.fp.sum()) == (26, 257, 37, 318), "R3 totals")
    hfa = (h42.fp / h42.nonict_h * 24).round(1); ffa = (f42.fp / f42.nonict_h * 24).round(1)   # = Table 12 cells
    gate((int(h42.loc["chb15"].tp), int(f42.loc["chb15"].tp), hfa["chb15"], ffa["chb15"]) == (0, 11, 8.5, 32.3), "R3 chb15")

    fig = plt.figure(figsize=FULL)
    a1 = fig.add_axes([0.075, 0.17, 0.46, 0.75]); a2 = fig.add_axes([0.72, 0.17, 0.26, 0.75])
    L = Layers(fig, ["heldout", "final", "chb15"])
    y = np.arange(len(TEST))[::-1]
    for a in (a1, a2):
        a.set_yticks(y, TEST if a is a1 else [], fontsize=14, color=INK); a.tick_params(axis="y", length=0); a.spines["left"].set_visible(False)
        grid_x(a); a.set_ylim(-0.7, len(TEST) - 0.3)
    a1.set_xlim(0, 1.04); a1.set_xticks([0, 0.25, 0.5, 0.75, 1.0], ["0", "", "50 %", "", "100 %"]); a2.yaxis.grid(False)
    a1.set_xlabel("Seizures detected (share of the patient's seizures)")
    a2.set_xlim(0, 40); a2.set_xticks([0, 10, 20, 30, 40]); a2.set_xlabel("False alarms per day")
    for yi, s in zip(y, TEST):
        n = int(f42.loc[s].n_ref); ht, ft = int(h42.loc[s].tp), int(f42.loc[s].tp)
        L.add("heldout", a1.scatter([ht / n], [yi], s=120, facecolor="white", edgecolor=TEAL, lw=2.2, zorder=3))
        L.add("heldout", a2.scatter([hfa[s]], [yi], s=110, facecolor="white", edgecolor=TEAL, lw=2.2, zorder=3))
        txt_h = a1.text(1.07, yi, f"{ht} / {n}", va="center", ha="left", fontsize=13.5, color=MUTED,
                        transform=a1.get_yaxis_transform())
        L.add("heldout", txt_h)
        if ft != ht:
            L.add("final", a1.add_patch(FancyArrowPatch((ht / n + 0.02, yi), (ft / n - 0.025, yi), arrowstyle="-|>",
                                                        mutation_scale=18, color=TEAL, lw=2.2, zorder=2)))
        if abs(ffa[s] - hfa[s]) > 0.05:
            L.add("final", a2.add_patch(FancyArrowPatch((hfa[s] + 0.6, yi), (ffa[s] - 0.9, yi), arrowstyle="-|>",
                                                        mutation_scale=16, color=ORANGE, lw=1.8, zorder=2)))
        L.add("final", a1.scatter([ft / n], [yi], s=120, color=TEAL, zorder=4))
        L.add("final", a2.scatter([ffa[s]], [yi], s=110, color=ORANGE if abs(ffa[s] - hfa[s]) > 0.05 else TEAL, zorder=4))
        if ft != ht:
            L.add("final", a1.text(1.205, yi, f"→ {ft} / {n}", va="center", ha="left", fontsize=13.5, color=TEAL,
                                   fontweight="bold", transform=a1.get_yaxis_transform()))
    L.add("heldout", a1.text(1.07, 1.01, "detected / seizures", transform=a1.transAxes, ha="left", va="bottom",
                             fontsize=12.5, color=MUTED))
    yc = y[TEST.index("chb15")]
    L.add("chb15", a1.add_patch(Ellipse((0.30, yc), 0.66, 0.95, fill=False, ec=ORANGE, lw=2.2, ls="--", zorder=5)))
    L.add("chb15", a2.text(ffa["chb15"], yc - 0.42, f"{hfa['chb15']:.1f} → {ffa['chb15']:.1f}", ha="right", va="top",
                           fontsize=13, color=ORANGE_D, fontweight="semibold"))
    L.add("chb15", a1.text(0.30, yc + 0.62, "the final gain is one patient", ha="center", va="bottom", fontsize=13.5,
                           color=ORANGE_D, fontweight="semibold"))
    # legend (base layer)
    L.add("heldout", a1.scatter([], [], s=120, facecolor="white", edgecolor=TEAL, lw=2.2, label="held-out evaluation"))
    L.add("final", a1.scatter([], [], s=120, color=TEAL, label="final system (test-informed)"))
    lg = a1.legend(loc="lower left", bbox_to_anchor=(0.30, 0.0), fontsize=13, handletextpad=0.3, borderaxespad=0.2)
    L.add("heldout", lg)
    footer(fig, "Test patients (8, 76 seizures) · seed 42 · counts per patient after the localizer "
                "(totals: held-out 26 / 76 at 22.2 FP/day, final 37 / 76 at 27.5 FP/day)")
    if not ARGS.smoke:
        OUT.mkdir(parents=True, exist_ok=True); L.export("R3_unseen_patients")
    save(fig, "R3_unseen_patients",
         [f"{s}: {int(h42.loc[s].tp)}/{int(f42.loc[s].n_ref)} → {int(f42.loc[s].tp)}" for s in TEST]
         + ["FP/day per patient (Table 12)", "totals 26/76 @ 22.2; 37/76 @ 27.5"],
         ["results/e22_test_oneshot/per_subject_seed.csv (localized, clean_seed42)",
          "results/e23_test_look7/per_subject_seed.csv (balanced, localized, clean_seed42)",
          "read via src/figures_v8/make_v8_exhibits.py e22_per_subject / e23_per_subject"])


# ════════════════════════════════════════ R2 ════════════════════════════════════════
def r2_test_map():
    cont = (R / "continuous_eval/SUMMARY.md").read_text(encoding="utf-8")
    m = re.search(r"T fixed_50_2\.0\s+50\.0\s+2\.0\s+90\s+POOLED\s+(\d+)\s+(\d+)\s+(\d+)\s+\d+\s+([\d.]+)\s+[\d.]+\s+[\d.]+\s+([\d.]+)", cont)
    gate(m is not None, "continuous_eval V1 row")
    v1_tp, _, v1_n, v1_s, v1_fa = int(m[1]), int(m[2]), int(m[3]), float(m[4]), float(m[5])
    e22 = pd.read_csv(R / "e22_test_oneshot/summary_per_seed.csv").set_index(["system", "seed"])
    E = e22.loc[("E (P1 frozen)", "clean_seed42")]; H = e22.loc[("final localized", "clean_seed42")]
    F = X.e23_seed("localized").loc["clean_seed42"]
    pj = json.loads((R / "application_eval_v4/pooled.json").read_text())["pooled"]
    pts = [("Earlier system\n(midterm)", v1_s, v1_fa, f"{v1_tp} / {v1_n}", GREY, "o", "white"),
           ("Earlier score,\ngraph-level", E.sens, E.fa_day, f"{int(E.tp)} / 76", GREY, "o", "white"),
           ("Held-out evaluation", H.sens, H.fa_day, f"{int(H.tp)} / 76", TEAL, "o", "white"),
           ("Final system\n(test-informed)", F.sens, F.fa_day, f"{int(F.tp)} / 76", TEAL, "o", TEAL),
           ("Review application\n(label-free statistics)", pj["sensitivity"], pj["false_alarms_per_day"],
            f"{pj['tp']} / 76", TEAL, "s", TEAL)]
    got = [(round(s, 3), round(fa, 1)) for _, s, fa, *_ in pts]
    gate(got == [(0.303, 73.3), (0.039, 24.1), (0.342, 22.2), (0.487, 27.5), (0.434, 27.9)], f"R2 points {got}")
    fig, ax = plt.subplots(figsize=FULL); fig.subplots_adjust(left=0.08, right=0.97, top=0.96, bottom=0.17)
    ax.set_xlim(0, 85); ax.set_ylim(0, 0.6); ax.set_yticks([0, 0.2, 0.4, 0.6])
    ax.set_xlabel("False alarms per day"); ax.set_ylabel("Pooled sensitivity"); grid_y(ax); grid_x(ax)
    off = [(-12, 14, "right"), (12, 4, "left"), (-14, -30, "right"), (-14, 16, "right"), (14, -26, "left")]
    for (lab, s, fa, cnt, col, mk, face), (dx, dy, ha) in zip(pts, off):
        ax.scatter([fa], [s], s=170, marker=mk, facecolor=face, edgecolor=col, lw=2.4, zorder=3)
        ax.annotate(f"{lab}\n{cnt} at {fa:.1f}", (fa, s), xytext=(dx, dy), textcoords="offset points", ha=ha,
                    va="center", fontsize=13, color=INK if col == TEAL else MUTED, linespacing=1.15)
    footer(fig, "Test patients (8, 76 seizures, continuous recordings) · seed 42 · pooled sensitivity, "
                "false alarms per day of non-seizure time")
    save(fig, "R2_test_map", [f"{lab.splitlines()[0]}: {cnt} at {fa:.1f} (sens {s:.3f})" for lab, s, fa, cnt, *_ in pts],
         ["results/continuous_eval/SUMMARY.md l.306 (V1 continuous 23/76 @ 73.31)",
          "results/e22_test_oneshot/summary_per_seed.csv (E (P1 frozen) and final localized, seed 42)",
          "results/e23_test_look7/summary_per_seed.csv (balanced localized, seed 42)",
          "results/application_eval_v4/pooled.json"])


# ════════════════════════════════════════ R5 ════════════════════════════════════════
def r5_siena_benchmark():
    txt = (REPO / "docs/BENCHMARK_CHECK_szcore_c57da2f.md").read_text(encoding="utf-8").split("### Siena")[1].split("###")[0]
    rows = re.findall(r"^\| ([^|]+?) \| ([^|]+?) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| ([\d.]+) \| (yes|no[^|]*) \|", txt, re.M)
    b = pd.DataFrame(rows, columns=["entry", "train", "sens", "prec", "f1", "fa", "oos"])
    b[["sens", "fa"]] = b[["sens", "fa"]].astype(float)
    b = b[b.oos == "yes"]                         # Table 18: entries trained on Siena excluded
    gate(len(b) == 11, f"R5 out-of-sample entries {len(b)}")
    x = X.x1_rows(); s = x[x.set == "siena"]
    ms = [X.subject_mean(s[s.seed == sd]) for sd in SEEDS]
    ours = (round(np.mean([m["sens"] for m in ms]), 3), round(np.mean([m["fa"] for m in ms]), 1))
    dyn = b[b.entry == "DynaSD"].iloc[0]
    gate(ours == (0.633, 41.0) and (dyn.sens, dyn.fa) == (0.664, 77.74), f"R5 ours {ours}, DynaSD {dyn.sens, dyn.fa}")
    fig, ax = plt.subplots(figsize=FULL); fig.subplots_adjust(left=0.08, right=0.97, top=0.96, bottom=0.17)
    ax.set_xscale("log"); ax.set_xlim(2, 450); ax.set_ylim(0, 1.08)
    ax.set_xticks([3, 10, 30, 100, 300], ["3", "10", "30", "100", "300"]); ax.minorticks_off()
    ax.set_xlabel("False alarms per day (log scale)"); ax.set_ylabel("Sensitivity (per-patient mean)")
    grid_y(ax); grid_x(ax)
    label_sup = {"Zhu Transformer 2023": ("Zhu 2023\n0.674 at 15.3", 10, 10, "left"),
                 "EventNet 2024": ("EventNet\n0.587 at 8.2", -10, -18, "right"),
                 "Gotman 1982": ("rule-based (Gotman)", -12, 20, "right")}
    for _, q in b.iterrows():
        if q.entry == "DynaSD":
            continue
        rule = q.entry.startswith("Gotman")
        ax.scatter([q.fa], [q.sens], s=90, marker="^" if rule else "o", facecolor="white" if rule else GREY_L,
                   edgecolor=GREY, lw=1.6, zorder=2)
        if q.entry in label_sup:
            t, dx, dy, ha = label_sup[q.entry]
            ax.annotate(t, (q.fa, q.sens), xytext=(dx, dy), textcoords="offset points", ha=ha, va="center",
                        fontsize=12.5, color=MUTED)
    ax.scatter([dyn.fa], [dyn.sens], s=170, marker="D", facecolor="white", edgecolor=PURPLE, lw=2.6, zorder=4)
    ax.annotate("DynaSD (label-free)\n0.664 at 77.7", (dyn.fa, dyn.sens), xytext=(14, 18), textcoords="offset points",
                ha="left", va="center", fontsize=14, color=PURPLE, fontweight="semibold")
    ax.scatter([ours[1]], [ours[0]], s=320, marker="*", color=TEAL, zorder=5)
    ax.annotate("This work (label-free)\n0.633 at 41.0", (ours[1], ours[0]), xytext=(-16, -34), textcoords="offset points",
                ha="right", va="center", fontsize=14.5, color=TEAL, fontweight="bold")
    ax.annotate("", xy=(ours[1] * 1.08, ours[0] + 0.012), xytext=(dyn.fa / 1.08, dyn.sens - 0.004),
                arrowprops=dict(arrowstyle="-|>", color=PURPLE, lw=1.6, ls="--", mutation_scale=16), zorder=3)
    ax.text(np.sqrt(ours[1] * dyn.fa), 0.615, "about half\nthe false alarms", ha="center", va="top", fontsize=13.5,
            color=TEAL, fontweight="semibold")
    ax.scatter([], [], s=90, color=GREY_L, edgecolor=GREY, label="supervised, trained on other corpora")
    ax.scatter([], [], s=90, marker="^", facecolor="white", edgecolor=GREY, label="rule-based")
    ax.legend(loc="lower right", fontsize=13)
    footer(fig, "Siena (14 adults, 47 seizures) · SzCORE event scoring · per-patient mean; this work = mean of 4 seeds, "
                "own scorer; entries trained on Siena excluded")
    save(fig, "R5_siena_benchmark", ["this work 0.633 at 41.0 (4 seeds)", "DynaSD 0.664 at 77.7", "Zhu 0.674 at 15.3",
                                     "EventNet 0.587 at 8.2", "9 other entries unlabelled (Table 18)"],
         ["docs/BENCHMARK_CHECK_szcore_c57da2f.md ### Siena (rows marked out-of-sample 'yes' = Table 18)",
          "results/x1_external/rows_PN*.csv via make_v8_exhibits.x1_rows / subject_mean (4 seeds)"])


# ════════════════════════════════════════ R7 ════════════════════════════════════════
def r7_channel():
    sm = pd.read_csv(R / "attribution_v8/attribution_summary.csv")
    p = sm[sm.panel == "ALL focal (primary)"].iloc[0]
    gate((round(p.macro_AUROC, 3), round(p.AUROC_CI_lo, 3), round(p.AUROC_CI_hi, 3), round(p.macro_AUROC_prior, 3),
          int(p.n_seizures)) == (0.547, 0.499, 0.597, 0.739, 62), "R7 primary panel")
    fig, ax = plt.subplots(figsize=HALF); fig.subplots_adjust(left=0.36, right=0.95, top=0.95, bottom=0.25)
    rows = [("Random ranking", 0.500, None, GREY), ("This model", p.macro_AUROC, (p.AUROC_CI_lo, p.AUROC_CI_hi), TEAL),
            ("Anatomical prior\n(fixed rule)", p.macro_AUROC_prior, None, PURPLE)]
    y = np.arange(3)[::-1]
    ax.set_xlim(0.40, 0.85); ax.set_ylim(-0.6, 2.6); ax.set_yticks(y, [r[0] for r in rows], fontsize=14, color=INK)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False); grid_x(ax)
    ax.axvline(0.5, color=GREY, lw=1.2, ls=":")
    for yi, (lab, v, ci, col) in zip(y, rows):
        if ci:
            ax.plot(ci, [yi, yi], color=col, lw=3, solid_capstyle="round")
        ax.scatter([v], [yi], s=170, color=col, zorder=3)
        ax.text(v, yi + 0.28, f"{v:.3f}", ha="center", va="bottom", fontsize=15, fontweight="semibold",
                color=INK if col != TEAL else TEAL)
    ax.set_xlabel("Channel ranking AUROC\nagainst the blind annotation")
    footer(fig, "Test patients, 62 focal seizures · seed 42 · mean AUROC [95 % CI]")
    save(fig, "R7_channel_ranking", ["0.547 [0.499, 0.597] (CI drawn, not printed)", "0.739 prior", "0.500 random"],
         ["results/attribution_v8/attribution_summary.csv (panel 'ALL focal (primary)')"])

    # R7b (backup B21): per patient, model vs prior
    sub = sm[sm.panel.str.startswith("subject ")].copy()
    sub["subject"] = sub.panel.str.replace("subject ", "", regex=False)
    gate(len(sub) == 7 and round(sub.set_index("subject").loc["chb15"].macro_AUROC, 3) == 0.675
         and round(sub.set_index("subject").loc["chb15"].macro_AUROC_prior, 3) == 0.576, "R7b per patient")
    sub = sub.sort_values("subject", ascending=False)
    fig, ax = plt.subplots(figsize=FULL); fig.subplots_adjust(left=0.13, right=0.97, top=0.95, bottom=0.17)
    y = np.arange(len(sub))
    ax.set_yticks(y, [f"{s}  ({int(n)})" for s, n in zip(sub.subject, sub.n_seizures)], fontsize=14, color=INK)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False); ax.set_xlim(0.3, 1.0); grid_x(ax)
    ax.axvline(0.5, color=GREY, lw=1.2, ls=":")
    for yi, (_, q) in zip(y, sub.iterrows()):
        ax.plot([q.macro_AUROC, q.macro_AUROC_prior], [yi, yi], color=GREY_L, lw=2.5, zorder=1)
        ax.scatter([q.macro_AUROC_prior], [yi], s=130, color=PURPLE, zorder=3)
        ax.scatter([q.macro_AUROC], [yi], s=130, color=TEAL, zorder=4)
        if q.subject == "chb15":
            ax.text(q.macro_AUROC + 0.02, yi + 0.3, f"only patient above its prior: {q.macro_AUROC:.3f} vs "
                    f"{q.macro_AUROC_prior:.3f}", fontsize=13, color=TEAL, fontweight="semibold", va="bottom")
    ax.scatter([], [], s=130, color=TEAL, label="this model"); ax.scatter([], [], s=130, color=PURPLE, label="anatomical prior")
    ax.legend(loc="lower right", fontsize=13); ax.set_xlabel("Channel ranking AUROC (patient mean)")
    footer(fig, "Test patients with focal seizures (number of focal seizures) · seed 42 · per-patient mean AUROC; "
                "chb06 has only generalized seizures")
    save(fig, "R7b_channel_per_patient", ["chb15 0.675 vs prior 0.576"],
         ["results/attribution_v8/attribution_summary.csv (panels 'subject chbXX')"])


# ════════════════════════════════════════ R8 ════════════════════════════════════════
def r8_application():
    a = pd.read_csv(R / "application_eval_v4/per_subject.csv").set_index("subject").loc[TEST]
    f = X.e23_per_subject(); f42 = f[f.seed == "clean_seed42"].set_index("subject").loc[TEST]
    gate((a.detected.sum(), a.false_alarms.sum(), f42.tp.sum(), f42.fp.sum()) == (33, 323, 37, 318), "R8 totals")
    less = [s for s in TEST if a.loc[s].detected < f42.loc[s].tp]
    gate(less == ["chb03", "chb06", "chb15", "chb16"] and all(f42.loc[s].tp - a.loc[s].detected == 1 for s in less), "R8 diff")
    fig, ax = plt.subplots(figsize=FULL); fig.subplots_adjust(left=0.10, right=0.80, top=0.95, bottom=0.17)
    y = np.arange(len(TEST))[::-1]
    ax.set_yticks(y, TEST, fontsize=14, color=INK); ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False)
    ax.set_xlim(0, 21); ax.set_xlabel("Seizures detected (count)"); grid_x(ax)
    for yi, s in zip(y, TEST):
        n = int(a.loc[s].seizures)
        ax.barh(yi, n, height=0.62, color=GREY_L, zorder=1)
        ax.scatter([f42.loc[s].tp], [yi + 0.12], s=120, facecolor="white", edgecolor=TEAL, lw=2.2, zorder=3)
        ax.scatter([a.loc[s].detected], [yi - 0.12], s=120, color=TEAL, marker="s", zorder=4)
        col = ORANGE_D if s in less else MUTED
        ax.text(21.4, yi, f"{int(a.loc[s].detected)} vs {int(f42.loc[s].tp)} of {n}", va="center", ha="left",
                fontsize=13.5, color=col, fontweight="semibold" if s in less else "normal")
    ax.scatter([], [], s=120, facecolor="white", edgecolor=TEAL, lw=2.2, label="final system (thesis statistics)")
    ax.scatter([], [], s=120, marker="s", color=TEAL, label="review application (label-free statistics)")
    from matplotlib.patches import Patch
    h, l = ax.get_legend_handles_labels()
    ax.legend(h + [Patch(color=GREY_L)], l + ["seizures of the patient"], loc="lower right", fontsize=13)
    ax.set_xticks([0, 5, 10, 15, 20])
    ax.text(1.005, 1.0, "application vs final", transform=ax.transAxes, ha="left", va="bottom", fontsize=13, color=MUTED)
    footer(fig, "Test patients (8) · seed 42 · counts per patient; totals 33 / 76 (323 false alarms) vs 37 / 76 (318); "
                "one fewer in chb03, chb06, chb15, chb16")
    save(fig, "R8_application_vs_final", [f"{s}: {int(a.loc[s].detected)} vs {int(f42.loc[s].tp)} of {int(a.loc[s].seizures)}"
                                          for s in TEST] + ["33/76, 323 FA vs 37/76, 318 FA"],
         ["results/application_eval_v4/per_subject.csv", "results/e23_test_look7/per_subject_seed.csv (balanced, localized, seed 42)"])


# ════════════════════════════════════════ R9 ════════════════════════════════════════
def r9_normal_reference():
    other, own_feat = rx("e5_patient_density/SUMMARY.md", r"K1: best sens at FA/day <= 25: E5 ([\d.]+) \{'smooth': 15\.0.*?\| A0 ([\d.]+)")[::-1]
    m10 = rx("e16_recording_baseline/SUMMARY_a.md", r"^E16a\s+([\d.]+)")
    m30 = rx("e16_recording_baseline/SUMMARY_bcd.md", r"^E16c\s+([\d.]+)")
    caus = rx("e16_recording_baseline/SUMMARY_bcd.md", r"^E16d\s+([\d.]+)")
    whole = rx("e16_recording_baseline/SUMMARY_a.md", r"^S9base\s+([\d.]+)")
    got = [round(v, 3) for v in (other, own_feat, m10, m30, caus, whole)]
    gate(got == [0.340, 0.596, 0.191, 0.295, 0.487, 0.612], f"R9 {got}")
    fig = plt.figure(figsize=FULL)
    ax1 = fig.add_axes([0.25, 0.53, 0.71, 0.39]); ax2 = fig.add_axes([0.25, 0.20, 0.71, 0.22])
    g1 = [("First 10 min of each file", m10, GREY), ("First 30 min of each file", m30, GREY),
          ("Past 30 min (causal window)", caus, GREY), ("Patient's whole recording", whole, TEAL)]
    g2 = [("Other patients' normal", other, GREY), ("Patient's whole recording", own_feat, TEAL)]
    for ax, g, ttl in ((ax1, g1, "Same latent score (4 seeds)"), (ax2, g2, "Same input features (feature model)")):
        y = np.arange(len(g))[::-1]
        ax.barh(y, [v for _, v, _ in g], height=0.62, color=[c for *_, c in g], zorder=2)
        ax.set_yticks(y, [l for l, *_ in g], fontsize=14, color=INK); ax.tick_params(axis="y", length=0)
        ax.spines["left"].set_visible(False); ax.set_xlim(0, 0.72); grid_x(ax)
        for yi, (_, v, c) in zip(y, g):
            ax.text(v + 0.01, yi, f"{v:.3f}", va="center", ha="left", fontsize=15,
                    fontweight="bold" if c == TEAL else "normal", color=TEAL if c == TEAL else INK)
        ax.text(-0.33, 1.04, ttl, transform=ax.transAxes, fontsize=13.5, color=MUTED, ha="left", va="bottom",
                fontweight="semibold")
    ax1.set_xticklabels([]); ax2.set_xlabel("Pooled sensitivity (≤ 25 false alarms / day)")
    footer(fig, "Development patients (15) · pooled sensitivity at the best operating point ≤ 25 false alarms per day; "
                "each group compares references on the same model")
    save(fig, "R9_normal_reference", ["0.191", "0.295", "0.487", "0.612", "0.340", "0.596"],
         ["results/e16_recording_baseline/SUMMARY_a.md E16a 0.191; SUMMARY_bcd.md E16c 0.295, E16d 0.487 (= p2_ledger E16 a/c/d)", "results/e16_recording_baseline/SUMMARY_a.md S9base 0.612",
          "results/e5_patient_density/SUMMARY.md K1 (E5 0.596 vs A0 0.340)"])


# ════════════════════════════════════════ R10 ═══════════════════════════════════════
def r10_seeds_bootstrap():
    d = pd.read_csv(R / "e23_test_look7/summary_per_seed.csv"); d = d[d.point == "balanced"]
    held = d[d.system == "look #6"].set_index("seed").loc[SEEDS]; fin = d[d.system == "localized"].set_index("seed").loc[SEEDS]
    bt = (R / "e22_test_oneshot/BOOTSTRAP.md").read_text()
    bp = tuple(map(float, re.search(r"all 8\s+final pooled sens\s+\+?([\d.]+)\s+\[\s*\+?([\d.]+),\s*\+?([\d.]+)\]", bt).groups()))
    bm = tuple(map(float, re.search(r"all 8\s+final subject-mean sens\s+\+?([\d.]+)\s+\[\s*\+?([\d.]+),\s*\+?([\d.]+)\]", bt).groups()))
    s7 = (R / "e23_test_look7/SUMMARY.md").read_text().split("## sensitivity")[0]
    dp = tuple(map(float, re.search(r"pooled sens diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()))
    dm = tuple(map(float, re.search(r"subject-mean diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()))
    dfa = tuple(map(float, re.search(r"FP/day diff \+([\d.]+) \[\+([\d.]+), \+([\d.]+)\]", s7).groups()))
    gate(bp == (0.336, 0.133, 0.670) and bm == (0.498, 0.226, 0.770) and dp == (0.141, 0.000, 0.333)
         and dm == (0.070, 0.000, 0.201) and dfa == (5.27, 0.37, 13.60), "R10 bootstrap")
    gate(round(held.loc["clean_seed42"].sens, 3) == 0.342 and round(fin.loc["clean_seed42"].sens, 3) == 0.487, "R10 seed 42")
    fig = plt.figure(figsize=FULL)
    a1 = fig.add_axes([0.25, 0.20, 0.42, 0.70]); a2 = fig.add_axes([0.73, 0.20, 0.25, 0.70])
    rows = [("Held-out, pooled", held.sens, bp), ("Held-out, per-patient mean", held.s_sens, bm),
            ("Final, pooled", fin.sens, None), ("Final, per-patient mean", fin.s_sens, None)]
    y = np.arange(4)[::-1]
    a1.set_yticks(y, [r[0] for r in rows], fontsize=14, color=INK); a1.tick_params(axis="y", length=0)
    a1.spines["left"].set_visible(False); a1.set_xlim(0, 1); a1.set_ylim(-0.6, 3.6); grid_x(a1)
    a1.set_xlabel("Sensitivity")
    rng = np.random.default_rng(0)
    for yi, (lab, seeds, ci) in zip(y, rows):
        if ci:
            a1.plot([ci[1], ci[2]], [yi, yi], color=ORANGE, lw=4, solid_capstyle="round", zorder=1)
            a1.text(ci[2] + 0.02, yi, f"[{ci[1]:.3f}, {ci[2]:.3f}]", va="center", fontsize=13, color=ORANGE_D)
        a1.scatter(seeds.values, yi + rng.uniform(-0.08, 0.08, 4), s=70, color=TEAL, zorder=3, alpha=0.9)
    a1.scatter([], [], s=70, color=TEAL, label="4 seeds (spread from initialisation)")
    a1.plot([], [], color=ORANGE, lw=4, label="95 % patient bootstrap")
    fig.legend(*a1.get_legend_handles_labels(), loc="upper left", bbox_to_anchor=(0.25, 0.995), ncol=2, fontsize=13)
    yy = np.arange(2)[::-1]
    for yi, (lab, dd) in zip(yy, (("pooled", dp), ("per-patient\nmean", dm))):
        a2.plot([dd[1], dd[2]], [yi, yi], color=ORANGE, lw=4, solid_capstyle="round")
        a2.scatter([dd[0]], [yi], s=90, color=INK, zorder=3)
        a2.text(dd[0], yi + 0.18, f"+{dd[0]:.3f}", ha="center", va="bottom", fontsize=13.5, color=INK)
    a2.set_yticks(yy, ["pooled", "per-patient\nmean"], fontsize=13.5, color=INK); a2.tick_params(axis="y", length=0)
    a2.spines["left"].set_visible(False); a2.set_xlim(-0.05, 0.4); a2.set_ylim(-0.7, 1.7); a2.axvline(0, color=GREY, lw=1.2, ls=":")
    a2.set_xlabel("Final − held-out"); grid_x(a2)
    a2.text(0.5, 0.03, f"false alarms per day:\n+{dfa[0]:.2f} [+{dfa[1]:.2f}, +{dfa[2]:.2f}]", transform=a2.transAxes,
            ha="center", va="bottom", fontsize=12.5, color=MUTED)
    footer(fig, "Test patients (8, 76 seizures) · dots: 4 seeds · bars: 95 % patient bootstrap of the 4-seed mean "
                "(B = 10,000)")
    save(fig, "R10_seeds_bootstrap", ["held-out pooled [0.133, 0.670]", "held-out per-patient [0.226, 0.770]",
                                      "diff pooled +0.141 [0.000, 0.333]", "diff per-patient +0.070 [0.000, 0.201]",
                                      "diff FP/day +5.27 [+0.37, +13.60]", "seed dots (Table 11 / Appendix C)"],
         ["results/e23_test_look7/summary_per_seed.csv (balanced: look #6 and localized)",
          "results/e22_test_oneshot/BOOTSTRAP.md", "results/e23_test_look7/SUMMARY.md (balanced bootstrap)"])


# ════════════════════════════════════════ R11 ═══════════════════════════════════════
def r11_siena_patients():
    x = X.x1_rows(); s = x[(x.set == "siena") & (x.seed == "clean_seed42")].set_index("subject").loc[X.SIENA]
    gate((s.tp.sum(), s.n_ref.sum(), s.fp.sum(), round(s.hours.sum(), 1)) == (33, 47, 257, 141.0), "R11 totals")
    fa = (s.fp / s.nonict_h * 24).round(1)                                 # = Table 15 cells
    m42 = X.subject_mean(s.reset_index())
    gate(round(m42["fa"], 1) == 41.5 and round(m42["sens"], 3) == 0.748, f"R11 seed-42 mean {m42}")
    fig = plt.figure(figsize=FULL)
    a1 = fig.add_axes([0.07, 0.56, 0.91, 0.38]); a2 = fig.add_axes([0.07, 0.17, 0.91, 0.30])
    xx = np.arange(len(s))
    a1.bar(xx, s.n_ref, 0.62, color=GREY_L, zorder=1, label="seizures")
    det_col = [ORANGE if t == 0 else TEAL for t in s.tp]
    a1.bar(xx, s.tp, 0.36, color=det_col, zorder=2, label="detected")
    for xi, (t, n) in zip(xx, zip(s.tp, s.n_ref)):
        a1.text(xi, n + 0.25, f"{int(t)}/{int(n)}", ha="center", va="bottom", fontsize=12.5,
                color=ORANGE_D if t == 0 else INK)
    a1.set_xticks(xx, []); a1.set_ylim(0, 12); a1.set_yticks([0, 5, 10]); a1.set_ylabel("Seizures"); grid_y(a1)
    a1.legend(loc="upper right", fontsize=12.5, ncol=2)
    hi = fa > 70
    a2.bar(xx, fa, 0.55, color=[ORANGE if h else GREY for h in hi], zorder=2)
    a2.axhline(m42["fa"], color=TEAL, lw=2, ls=(0, (5, 3)), zorder=3)
    a2.text(7.5, m42["fa"] + 4, f"per-patient mean {m42['fa']:.1f}", ha="center", va="bottom", fontsize=12.5,
            color=TEAL, fontweight="semibold")
    a2.set_xticks(xx, X.SIENA, fontsize=12.5, color=INK); a2.set_ylabel("False alarms\nper day"); a2.set_ylim(0, 120); a2.set_yticks([0, 50, 100])
    grid_y(a2)
    footer(fig, "Siena (14 adults, 47 seizures, 141.0 h) · seed 42 · per patient after the localizer; "
                "orange: missed patient and > 70 false alarms per day")
    save(fig, "R11_siena_patients", [f"{p}: {int(s.loc[p].tp)}/{int(s.loc[p].n_ref)}" for p in X.SIENA]
         + ["FP/day bars unlabelled (Table 15)", "per-patient mean 41.5 (seed 42)"],
         ["results/x1_external/rows_PN*.csv via make_v8_exhibits.x1_rows (balanced, localized, seed 42)"])


# ════════════════════════════════════════ R12 ═══════════════════════════════════════
def r12_deployment():
    """Report Table 8 (a design table, no result file): scores 1-5, weights by engineering judgment."""
    w = np.array([0.30, 0.25, 0.20, 0.15, 0.10])
    scores = {"Cloud service": [2, 3, 5, 2, 5], "On-premise workstation": [5, 4, 4, 4, 3], "Bedside device": [4, 2, 2, 3, 2]}
    tot = {k: round(float(np.dot(w, v)), 2) for k, v in scores.items()}
    gate(tot == {"Cloud service": 3.15, "On-premise workstation": 4.20, "Bedside device": 2.75}, f"R12 {tot}")
    order = ["On-premise workstation", "Cloud service", "Bedside device"]
    fig, ax = plt.subplots(figsize=HALF); fig.subplots_adjust(left=0.40, right=0.93, top=0.95, bottom=0.30)
    y = np.arange(3)[::-1]
    ax.barh(y, [tot[k] for k in order], height=0.58, color=[TEAL, GREY, GREY], zorder=2)
    ax.set_yticks(y, ["On-premise\nworkstation", "Cloud\nservice", "Bedside\ndevice"], fontsize=14, color=INK)
    ax.tick_params(axis="y", length=0); ax.spines["left"].set_visible(False); ax.set_xlim(0, 5); grid_x(ax)
    for yi, k in zip(y, order):
        ax.text(tot[k] + 0.08, yi, f"{tot[k]:.2f}", va="center", fontsize=16, fontweight="bold" if k == order[0] else "normal",
                color=TEAL if k == order[0] else INK)
    ax.set_xlabel("Weighted score (1–5)")
    footer(fig, "Data protection 30 % · cost 25 % · time 20 %\nenergy 15 % · maintenance 10 %; weights by engineering judgment")
    save(fig, "R12_deployment", ["4.20", "3.15", "2.75", "weights 30/25/20/15/10 %"],
         ["Thesis_Final_Report.md Table 8 (design table; totals recomputed and gated)"])


# ════════════════════════════════════════ R13 ═══════════════════════════════════════
def r13_processing_time():
    """Report Table 25: stage times of the median timed run on chb16 (19 files, 19.0 h), laptop CPU."""
    t = pd.read_csv(R / "t1_demo/timing.csv")
    med = t.sort_values("s_per_hour").iloc[1]                      # median of 3 runs (= run 3, 21.68 s/h)
    gate((int(med.run), round(med.s_per_hour, 2), round(med.total_s, 1), med.hours) == (3, 21.68, 411.9, 19.0), "R13 median run")
    stages = [("Reading, filtering,\nwindowing", med.phase_a_s), ("Graphs and features", med.features_s),
              ("Autoencoder", med.gae_s), ("Distances and score", med.distances_and_score_s), ("Events", med.events_s)]
    gate([round(v, 1) for _, v in stages] == [156.2, 250.6, 4.3, 0.3, 0.3], "R13 stages = Table 25 run 3")
    fig, ax = plt.subplots(figsize=FULL); fig.subplots_adjust(left=0.22, right=0.93, top=0.95, bottom=0.2)
    y = np.arange(len(stages))[::-1]
    cols = [GREY, TEAL, TEAL, TEAL, TEAL]
    ax.barh(y, [v for _, v in stages], height=0.6, color=cols, zorder=2)
    for yi, (lab, v) in zip(y, stages):
        ax.text(v + 4, yi, f"{v:.1f} s", va="center", fontsize=15, color=INK)
    ax.set_yticks(y, [l for l, _ in stages], fontsize=14, color=INK); ax.tick_params(axis="y", length=0)
    ax.spines["left"].set_visible(False); ax.set_xlim(0, 300); grid_x(ax); ax.set_xlabel("Seconds for 19.0 h of EEG")
    ax.text(0.98, 0.08, f"total {med.total_s:.1f} s = {med.s_per_hour:.2f} s per hour of EEG", transform=ax.transAxes,
            ha="right", va="bottom", fontsize=15, color=TEAL, fontweight="semibold")
    footer(fig, "chb16, 19 files, 19.0 h · median of 3 timed runs · laptop CPU (i5-8250U, 16 GB), no GPU")
    save(fig, "R13_processing_time", ["156.2", "250.6", "4.3", "0.3", "0.3 s", "total 411.9 s = 21.68 s per hour"],
         ["results/t1_demo/timing.csv (run 3 = median, = report Table 25)"])


# ════════════════════════════════════════ main ══════════════════════════════════════
def main():
    # r5_siena_benchmark is retired (author 17/10, DECK_BRIEF A19): comparisons with other studies are tables, never figures
    for f in (r1_development, r3_unseen_patients, r2_test_map, r7_channel, r8_application,
              r9_normal_reference, r10_seeds_bootstrap, r11_siena_patients, r12_deployment, r13_processing_time):
        f()
        print(f"ok  {f.__name__}")
    if not ARGS.smoke:
        (OUT / "figs_manifest.json").write_text(json.dumps({"shown": SHOWN, "sources": SOURCES}, indent=1, ensure_ascii=False),
                                                encoding="utf-8")
    print("ALL GATES PASSED" + (" (smoke: nothing written)" if ARGS.smoke else f" -> {OUT}"))


if __name__ == "__main__":
    main()
