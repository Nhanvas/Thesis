#!/usr/bin/env python
"""
fig_example_chb03.py -- two report figures on test patient chb03, final system (tag p3-frozen), seed 42,
balanced point. Runs in two steps so that the plot never recomputes (integrity rule 13):

  export  uses the frozen code path of e23_test_look7.evaluate (E22.final_scalar, P3L budget,
          PS.d1_events, P3L.localize "cpd") and writes small CSV files to results/figures_v6_data/:
            chb03_score.csv    one row per window of the plotted files: file, t_s (seconds in the file),
                               ok, ictal, s9_raw (9th-largest channel robust-z, before drift correction),
                               s9_med (its +-15 min running median), s9_corr, score (ensemble),
                               score_sm (5-window smoothed)
            chb03_events.csv   kind (detector / localized), file, t0_s, t1_s
            chb03_meta.json    threshold, budget, files plotted, gate counts
          GATES (stop on mismatch): the whole of chb03 gives detector tp/fp 7/23 and localized 7/22
          (results/e23_test_look7/per_subject_seed.csv); s9_corr equals e17b_latent_family.member(...,9).
          No label is used to build any score; labels are read only for the shading and the gate.
  plot    reads only the CSV files and draws
            fig_drift.png      (a) 9th-largest channel score over three consecutive files with its
                               running median, (b) after the correction; file boundaries, seizures shaded
            fig_example.png    (a) one file: ensemble score, smoothed score, patient threshold,
                               annotated seizure, detector event, localized event; (b) +-4 min zoom

Run:  python src/figures_v6/fig_example_chb03.py export   (estimated 1-3 min, not measured)
      python src/figures_v6/fig_example_chb03.py plot     (~5 s)
"""
import json
import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

DATA = ROOT / "results" / "figures_v6_data"
FIG = ROOT / "results" / "figures_v6"
SUBJ, TAG, WIN = "chb03", "clean_seed42", 4
C = dict(det="#E69F00", loc="#009E73", sz="#D55E00", main="#0072B2", grey="#777777", raw="#AAAAAA")


def export():
    import p2_scalars as PS
    import e16_recording_baseline as E16
    import e17b_latent_family as F17
    import e22_test_oneshot as E22
    import p3_levers as P3L
    cfg = json.load(open(ROOT / "results" / "p3c_freeze" / "freeze.json"))
    floor, cap = cfg["points"]["balanced"]
    ctx = E22.test_context(SUBJ)
    x = E22.final_scalar(ctx, TAG)
    q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, TAG), cfg["smooth"]), cfg["k"])
    top = float(np.clip(q, floor, max(cap, floor)))
    det = PS.d1_events(ctx, x, cfg["smooth"], top)
    sm = PS.smoothed(ctx, x, cfg["smooth"])
    thr = float(np.nanquantile(sm, 1 - top))
    loc, _ = P3L.localize(ctx, x, det, thr, "cpd")
    got = (*PS.score(ctx, det)[:2], *PS.score(ctx, loc)[:2])
    ref = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
    ref = ref[(ref.point == "balanced") & (ref.subject == SUBJ) & (ref.seed == TAG)].set_index("stage")
    want = (int(ref.loc["detector", "tp"]), int(ref.loc["detector", "fp"]),
            int(ref.loc["localized", "tp"]), int(ref.loc["localized", "fp"]))
    if got != want:
        raise SystemExit(f"STOP gate: tp/fp detector, localized {got} vs e23 {want}")
    D = ctx["D"][TAG]; okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    s9 = -np.sort(-Zc, axis=1)[:, 8]
    med = np.empty_like(s9)
    for f in np.unique(ctx["wf"]):
        w = np.flatnonzero(ctx["wf"] == f)
        med[w] = pd.Series(s9[w]).rolling(451, min_periods=1, center=True).median().values
    if not np.allclose(s9 - med, F17.member(D, ctx["wf"], 9)):
        raise SystemExit("STOP gate: corrected 9th-largest member differs from e17b_latent_family.member")
    full = lambda v: (lambda o: (o.__setitem__(ctx["idx"], v), o)[1])(np.full(ctx["n"], np.nan))
    s9f, medf = full(s9), full(med)
    files = list(np.unique(ctx["fidx"]))
    sz_files = [f for f in files if ctx["ict"][ctx["fidx"] == f].any()]
    f0 = sz_files[0]
    i0 = files.index(f0)
    drift_files = files[i0:i0 + 3]
    rows = []
    for f in drift_files:
        m = np.flatnonzero(ctx["fidx"] == f)
        for j, w in enumerate(m):
            rows.append(dict(file=int(f), t_s=j * WIN, ok=bool(ctx["ok"][w]), ictal=bool(ctx["ict"][w]),
                             s9_raw=s9f[w], s9_med=medf[w], s9_corr=s9f[w] - medf[w], score=x[w], score_sm=sm[w]))
    DATA.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(rows).to_csv(DATA / "chb03_score.csv", index=False)
    ev = [dict(kind=k, file=int(f), t0_s=a, t1_s=b) for k, E in (("detector", det), ("localized", loc))
          for f in drift_files for a, b in E.get(f, [])]
    pd.DataFrame(ev, columns=["kind", "file", "t0_s", "t1_s"]).to_csv(DATA / "chb03_events.csv", index=False)
    json.dump(dict(threshold=thr, budget=top, example_file=int(f0), drift_files=[int(f) for f in drift_files],
                   gate_detector_localized=list(got)), open(DATA / "chb03_meta.json", "w"), indent=1)
    print(f"export OK: gate {got}; budget {top:.4f}; files {drift_files}; wrote {DATA}")


def shade(ax, d, y0, y1, col, alpha=0.25):
    """shade contiguous runs where d is True (d indexed by plotting x in minutes)."""
    on = None
    for xv, v in zip(d.index, d.values):
        if v and on is None:
            on = xv
        if not v and on is not None:
            ax.axvspan(on, xv, color=col, alpha=alpha, lw=0); on = None
    if on is not None:
        ax.axvspan(on, d.index[-1], color=col, alpha=alpha, lw=0)


def plot():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 9, "axes.spines.top": False,
                         "axes.spines.right": False, "savefig.dpi": 300})
    S = pd.read_csv(DATA / "chb03_score.csv"); E = pd.read_csv(DATA / "chb03_events.csv")
    M = json.load(open(DATA / "chb03_meta.json"))
    FIG.mkdir(parents=True, exist_ok=True)

    # drift: three consecutive files placed end to end
    off, bounds = {}, []
    t = 0.0
    for f in M["drift_files"]:
        off[f] = t; t += S[S.file == f].t_s.max() + WIN; bounds.append(t)
    S["x_h"] = (S.t_s + S.file.map(off)) / 3600
    fig, ax = plt.subplots(2, 1, figsize=(6.3, 3.6), sharex=True)
    for a, col, lab in ((ax[0], "s9_raw", "(a)"), (ax[1], "s9_corr", "(b)")):
        g = S.set_index("x_h")
        shade(a, g.ictal, 0, 1, C["sz"], 0.35)
        a.plot(g.index, g[col], color=C["main"], lw=0.4)
        if col == "s9_raw":
            a.plot(g.index, g.s9_med, color="k", lw=1.2, label="running median (±15 min)")
            a.legend(frameon=False, fontsize=8, loc="upper right")
        for b in bounds[:-1]:
            a.axvline(b / 3600, color=C["grey"], ls="--", lw=0.8)
        a.set_ylabel("Channel score (z)"); a.set_title(lab, loc="left")
    ax[1].set_xlabel("Recording time (h), three consecutive files")
    fig.tight_layout(); fig.savefig(FIG / "fig_drift.png"); plt.close(fig)

    # example: one file with a seizure
    f0 = M["example_file"]; s = S[S.file == f0].copy(); s["m"] = s.t_s / 60
    e = E[E.file == f0]
    sz = s[s.ictal]; c = (sz.t_s.min() + sz.t_s.max()) / 2 / 60
    fig, ax = plt.subplots(2, 1, figsize=(6.3, 4.3))
    for a, (lo, hi), lab in ((ax[0], (0, s.m.max()), "(a)"), (ax[1], (c - 4, c + 4), "(b)")):
        w = s[(s.m >= lo) & (s.m <= hi)].set_index("m")
        shade(a, w.ictal, 0, 1, C["sz"], 0.30)
        a.plot(w.index, w.score, color=C["raw"], lw=0.6, label="anomaly score")
        a.plot(w.index, w.score_sm, color=C["main"], lw=1.0, label="smoothed score")
        a.axhline(M["threshold"], color="k", ls="--", lw=0.8, label="patient threshold")
        for kind, y, col in (("detector", 1.04, C["det"]), ("localized", 1.10, C["loc"])):
            for _, r in e[e.kind == kind].iterrows():
                a.hlines(y, max(r.t0_s / 60, lo), min(r.t1_s / 60, hi), color=col, lw=4)
        a.set_xlim(lo, hi); a.set_ylim(0, 1.14); a.set_ylabel("Score (0–1)"); a.set_title(lab, loc="left")
    ax[1].set_xlabel("Time in the file (min)")
    h = [plt.Line2D([], [], color=C["raw"], lw=1), plt.Line2D([], [], color=C["main"], lw=1),
         plt.Line2D([], [], color="k", ls="--", lw=0.8), plt.Line2D([], [], color=C["det"], lw=4),
         plt.Line2D([], [], color=C["loc"], lw=4), plt.Rectangle((0, 0), 1, 1, color=C["sz"], alpha=0.3)]
    fig.legend(h, ["anomaly score", "smoothed", "threshold", "detected event", "localized event",
                   "annotated seizure"], loc="lower center", ncol=3, frameon=False, fontsize=8)
    fig.tight_layout(rect=(0, 0.09, 1, 1)); fig.savefig(FIG / "fig_example.png"); plt.close(fig)
    print(f"plot OK: {FIG / 'fig_drift.png'}, {FIG / 'fig_example.png'} (file index {f0})")


if __name__ == "__main__":
    if len(sys.argv) != 2 or sys.argv[1] not in ("export", "plot"):
        raise SystemExit("usage: fig_example_chb03.py export|plot")
    export() if sys.argv[1] == "export" else plot()
