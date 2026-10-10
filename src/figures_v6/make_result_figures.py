#!/usr/bin/env python
"""
make_result_figures.py -- three report figures drawn from committed result files only (no recomputation
of any score; integrity rule 13). Final system (tag p3-frozen), balanced point, after the localizer.

  fig_per_patient.png   (a) detected / annotated seizures and (b) false alarms per day, per test patient,
                        seed 42, from results/e23_test_look7/per_subject_seed.csv.
                        GATE: pooled 37/76 and 318 false alarms, subject-mean sensitivity 0.577,
                        subject-mean FP/day 26.84 (SUMMARY of e23).
  fig_boundaries.png    signed onset / offset error of matched seizures, detector boundaries vs the
                        change point localizer, 4 seeds pooled, from results/e23_test_look7/errors.csv.
                        GATE: n = 146; median |error| detector 32 / 20 s, localizer 12 / 24 s.
  fig_peak_share.png    per test seizure, the alarm budget (share of the patient's time flagged) needed to
                        detect it (results/p3_anatomy/seizures.csv, column pn_final, seed 42),
                        with each patient's budget (column top of per_subject_seed.csv) and the 0.005 /
                        0.02 limits. GATE: 76 test seizures.

Run:  python src/figures_v6/make_result_figures.py [--root .] [--out results/figures_v6]   (~10 s)
"""
import argparse
import warnings
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
C = dict(det="#E69F00", loc="#009E73", sz="#D55E00", miss="#D9D9D9", main="#0072B2", grey="#777777")
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                     "axes.spines.right": False, "savefig.dpi": 300})


def stop(msg):
    raise SystemExit(f"STOP: {msg}")


def per_patient(root, out):
    d = pd.read_csv(root / "results/e23_test_look7/per_subject_seed.csv")
    d = d[(d.point == "balanced") & (d.seed == "clean_seed42") & (d.stage == "localized")].set_index("subject").loc[TEST]
    d["fa"] = d.fp / d.nonict_h * 24
    if (d.tp.sum(), d.n_ref.sum(), d.fp.sum()) != (37, 76, 318):
        stop(f"pooled counts {d.tp.sum()}/{d.n_ref.sum()}, fp {d.fp.sum()}")
    if round((d.tp / d.n_ref).mean(), 3) != 0.577 or round(d.fa.mean(), 2) != 26.84:
        stop("subject-mean values differ from the e23 SUMMARY")
    fig, ax = plt.subplots(1, 2, figsize=(6.3, 2.7))
    y = np.arange(len(TEST))[::-1]
    ax[0].barh(y, d.n_ref, color=C["miss"], label="missed")
    ax[0].barh(y, d.tp, color=C["main"], label="detected")
    for yi, (t, n) in zip(y, zip(d.tp, d.n_ref)):
        ax[0].text(n + 0.3, yi, f"{t}/{n}", va="center", fontsize=8)
    ax[0].set_yticks(y, TEST); ax[0].set_xlabel("Seizures"); ax[0].set_xlim(0, 23)
    ax[0].legend(frameon=False, loc="lower right", fontsize=8); ax[0].set_title("(a)", loc="left")
    ax[1].barh(y, d.fa, color=C["grey"])
    ax[1].axvline(d.fa.mean(), color="k", ls="--", lw=0.8)
    ax[1].text(d.fa.mean() + 0.5, y[0] + 0.45, f"mean {d.fa.mean():.1f}", fontsize=8)
    ax[1].set_yticks(y, TEST); ax[1].set_xlabel("False alarms per day"); ax[1].set_title("(b)", loc="left")
    fig.tight_layout(); fig.savefig(out / "fig_per_patient.png"); plt.close(fig)
    return d[["tp", "n_ref", "fp", "fa", "top"]]


def boundaries(root, out):
    e = pd.read_csv(root / "results/e23_test_look7/errors.csv")
    e = e[e.point == "balanced"]
    med = e[["det_on", "det_off", "cpd_on", "cpd_off"]].abs().median()
    if len(e) != 146 or tuple(med) != (32.0, 20.0, 12.0, 24.0):
        stop(f"n {len(e)}, medians {tuple(med)}")
    fig, ax = plt.subplots(1, 2, figsize=(6.3, 2.6), sharey=True)
    for a, side, lab in ((ax[0], "on", "Onset"), (ax[1], "off", "Offset")):
        data = [e[f"det_{side}"].values, e[f"cpd_{side}"].values]
        bp = a.boxplot(data, vert=False, widths=0.55, showfliers=False, patch_artist=True)
        for patch, col in zip(bp["boxes"], (C["det"], C["loc"])):
            patch.set_facecolor(col); patch.set_alpha(0.55)
        for med_line in bp["medians"]:
            med_line.set_color("k")
        rng = np.random.default_rng(0)
        for i, v in enumerate(data, start=1):
            a.scatter(np.clip(v, -150, 150), i + rng.uniform(-0.18, 0.18, len(v)), s=5, color="k", alpha=0.35, lw=0)
        a.axvline(0, color=C["sz"], lw=1)
        a.set_xlim(-150, 150); a.set_xticks([-120, -60, 0, 60, 120]); a.set_xlabel(f"{lab} error (s)")
        a.set_title("(a)" if side == "on" else "(b)", loc="left")
    ax[0].set_yticks([1, 2], ["Threshold\nboundaries", "Change point\nlocalizer"])
    fig.tight_layout(); fig.savefig(out / "fig_boundaries.png"); plt.close(fig)
    return med


def peak_share(root, out, budgets):
    s = pd.read_csv(root / "results/p3_anatomy/seizures.csv")
    s = s[(s.set == "test") & (s.seed == "clean_seed42")]
    if len(s) != 76:
        stop(f"{len(s)} test seizures")
    fig, a = plt.subplots(figsize=(6.3, 2.8))
    rng = np.random.default_rng(1)
    for i, subj in enumerate(TEST):
        v = s[s.subject == subj].pn_final.values
        a.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=12, color=C["main"], alpha=0.75, lw=0)
        a.hlines(budgets.loc[subj, "top"], i - 0.32, i + 0.32, color=C["loc"], lw=2)
    a.axhline(0.005, color=C["grey"], ls=":", lw=1); a.axhline(0.02, color=C["grey"], ls="--", lw=1)
    a.text(7.45, 0.005, "0.5 %", va="center", fontsize=8); a.text(7.45, 0.02, "2 %", va="center", fontsize=8)
    a.set_yscale("log"); a.set_xticks(range(len(TEST)), TEST); a.set_xlim(-0.5, 7.9)
    a.set_ylabel("Alarm budget needed\n(share of patient time)")
    a.plot([], [], color=C["loc"], lw=2, label="patient's alarm budget")
    a.scatter([], [], s=12, color=C["main"], label="one seizure")
    a.legend(frameon=False, fontsize=8, loc="upper left")
    fig.tight_layout(); fig.savefig(out / "fig_peak_share.png"); plt.close(fig)
    return s.groupby("subject").pn_final.median()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=str(Path(__file__).resolve().parents[2]))
    ap.add_argument("--out", default=None)
    a = ap.parse_args()
    warnings.filterwarnings("ignore", category=matplotlib.MatplotlibDeprecationWarning)
    root = Path(a.root)
    out = Path(a.out) if a.out else root / "results" / "figures_v6"
    out.mkdir(parents=True, exist_ok=True)
    pp = per_patient(root, out)
    med = boundaries(root, out)
    pk = peak_share(root, out, pp)
    print("per patient (seed 42):\n", pp.round(4).to_string())
    print("boundary median |error| (s):", med.to_dict())
    print("median peak share per patient (seed 42):", pk.round(4).to_dict())
    print("GATES PASSED; figures in", out)


if __name__ == "__main__":
    sys.exit(main())
