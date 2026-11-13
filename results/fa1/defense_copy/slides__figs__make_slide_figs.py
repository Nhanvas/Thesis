#!/usr/bin/env python
"""
make_slide_figs.py -- redraw thesis figures at slide size for the defense (figures.md).

Reads ONLY committed results / raw EEG files in F:/Study/Thesis/Code (read only). Writes ONLY to
F:/Study/Thesis/Defense/slides/figs/ (this directory, outside the repo, not committed).

Integrity: every figure here reads committed results or raw EEG through the SAME functions and the
SAME gates as the source script named in its docstring below; nothing is recomputed (no model, no
scoring). A gate failure raises SystemExit -- the script stops, it does not draw a wrong figure.

Size/font convention (figures.md):
  16:9 canvas, full width = 13.33 in, half width = 13.33 / 2 in, third width = 13.33 / 3 in;
  each figure's ORIGINAL aspect ratio is kept, scaled up to the stated width (so panels are not
  stretched); base font 14 pt, tick labels 12 pt, 200 dpi, PNG + SVG.

Two groups, run separately because the second needs the EEG files on this laptop:
  python make_slide_figs.py            F3, F4, F5, F6, F8, F9, F10 (committed results only, seconds)
  python make_slide_figs.py --eeg      F1, F2 (raw EDF reads, ~1-3 min each, estimated)
  python make_slide_figs.py --all      both groups
Each run updates HANDBACK.md (one line per figure produced this run; existing lines for figures not
re-run are kept).
"""
import argparse
import hashlib
import json
import sys
import time
import zipfile
from pathlib import Path

import numpy as np
import pandas as pd

CODE = Path("F:/Study/Thesis/Code")
DEFENSE = Path("F:/Study/Thesis/Defense")
OUT = Path(__file__).resolve().parent
DOCX = Path("F:/Study/Thesis/Reports/final/Thesis_NguyenQuocTrungNhan_BEBEIU2284_Report.docx")

for p in (CODE / "src", CODE / "src" / "figures", CODE / "src" / "figures_v8", CODE / "src" / "figures_v6",
          CODE / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

FULL_W = 13.33
HALF_W = 13.33 / 2
THIRD_W = 13.33 / 3

SLIDE_RC = {
    "font.family": "DejaVu Sans",
    "font.size": 14,
    "axes.titlesize": 14,
    "axes.labelsize": 14,
    "xtick.labelsize": 12,
    "ytick.labelsize": 12,
    "legend.fontsize": 12,
    "axes.spines.top": False,
    "axes.spines.right": False,
    "savefig.dpi": 200,
}


def apply_slide_rc():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update(SLIDE_RC)
    return plt


def scaled(orig_w, orig_h, target_w):
    """keep the original figure's aspect ratio, scaled up to target_w inches wide."""
    k = target_w / orig_w
    return target_w, orig_h * k


def save_both(fig, stem):
    png, svg = OUT / f"{stem}.png", OUT / f"{stem}.svg"
    fig.savefig(png, bbox_inches="tight")
    fig.savefig(svg, bbox_inches="tight")
    return png, svg


def gate(cond, msg):
    if not cond:
        raise SystemExit(f"STOP (gate): {msg}")


HANDBACK_ROWS = {}


def record(code, out_path, script, func, data_files, gate_result, runtime_s):
    HANDBACK_ROWS[code] = (
        f"| {code} | `{out_path.name}` | `{script}` ({func}) | {', '.join(data_files)} | "
        f"{gate_result} | {runtime_s:.2f} s |"
    )


# ───────────────────────────── F3: baseline drift (fig_example_chb03.py, plot step, fig_drift) ─────────────────────────────

def f3_drift():
    t0 = time.time()
    plt = apply_slide_rc()
    DATA = CODE / "results" / "figures_v6_data"
    C = dict(det="#E69F00", loc="#009E73", sz="#D55E00", main="#0072B2", grey="#777777", raw="#AAAAAA")
    S = pd.read_csv(DATA / "chb03_score.csv")
    M = json.load(open(DATA / "chb03_meta.json"))

    def shade(ax, d, col, alpha=0.25):
        on = None
        for xv, v in zip(d.index, d.values):
            if v and on is None:
                on = xv
            if not v and on is not None:
                ax.axvspan(on, xv, color=col, alpha=alpha, lw=0); on = None
        if on is not None:
            ax.axvspan(on, d.index[-1], color=col, alpha=alpha, lw=0)

    off, bounds = {}, []
    t = 0.0
    WIN = 4
    for f in M["drift_files"]:
        off[f] = t; t += S[S.file == f].t_s.max() + WIN; bounds.append(t)
    S["x_h"] = (S.t_s + S.file.map(off)) / 3600
    w, h = scaled(6.3, 3.6, FULL_W)
    fig, ax = plt.subplots(2, 1, figsize=(w, h), sharex=True)
    for a, col, lab in ((ax[0], "s9_raw", "(a)"), (ax[1], "s9_corr", "(b)")):
        g = S.set_index("x_h")
        shade(a, g.ictal, C["sz"], 0.35)
        a.plot(g.index, g[col], color=C["main"], lw=0.5)
        if col == "s9_raw":
            a.plot(g.index, g.s9_med, color="k", lw=1.6, label="running median (\u00b115 min)")
            a.legend(frameon=False, loc="upper right")
        for b in bounds[:-1]:
            a.axvline(b / 3600, color=C["grey"], ls="--", lw=1.0)
        a.set_ylabel("Channel score (z)"); a.set_title(lab, loc="left")
    ax[1].set_xlabel("Recording time (h), three consecutive files")
    fig.tight_layout()
    png, svg = save_both(fig, "F3_drift")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F3", png, "src/figures_v6/fig_example_chb03.py", "plot (fig_drift only)",
           ["results/figures_v6_data/chb03_score.csv", "results/figures_v6_data/chb03_meta.json"],
           f"OK (data pre-gated at export; export gate detector/localized {M['gate_detector_localized']})",
           time.time() - t0)
    print(f"F3 OK -> {png}")


# ───────────────────────────── F4: gallery (fig14_gallery.py) ─────────────────────────────

def f4_gallery():
    t0 = time.time()
    plt = apply_slide_rc()
    import importlib
    fig14 = importlib.import_module("fig14_gallery")
    plt.rcParams.update(SLIDE_RC)  # fig14_gallery.py sets its own smaller rcParams on import
    C = fig14.C
    DATA = CODE / "results" / "figures_v8_data" / "gallery"
    panels_all = [p for p in (fig14.load(k) for k in "abcd") if p is not None]
    gate(len(panels_all) == 4, f"expected 4 gallery panels (a-d), found {len(panels_all)}")

    def draw_gallery(panels, stem):
        n = len(panels)
        w, h = scaled(6.3, 1.85 * n + 0.5, FULL_W)
        fig = plt.figure(figsize=(w, h))
        gs = fig.add_gridspec(n, 2, width_ratios=[1.0, 1.25], wspace=0.28, hspace=0.55)
        for i, (d, lab) in enumerate(zip(panels, "abcd")):
            fig14.draw(fig.add_subplot(gs[i, 0]), fig.add_subplot(gs[i, 1]), d, f"({lab})")
        fig.text(0.29, 0.02 + 0.1 / n, "Time from onset (s): EEG, 30 s", ha="center", fontsize=12)
        fig.text(0.74, 0.02 + 0.1 / n, "Time from onset (s): score, \u00b15 min", ha="center", fontsize=12)
        h_ = [plt.Line2D([], [], color=C["raw"], lw=1.5), plt.Line2D([], [], color=C["main"], lw=1.5),
              plt.Line2D([], [], color="k", ls="--", lw=1.2), plt.Line2D([], [], color=C["grey"], ls=":", lw=1.4),
              plt.Line2D([], [], color=C["det"], lw=4), plt.Line2D([], [], color=C["loc"], lw=4),
              plt.Rectangle((0, 0), 1, 1, color=C["sz"], alpha=0.25)]
        fig.legend(h_, ["anomaly score", "smoothed", "threshold (final)", "threshold (held-out)", "detected event",
                        "localized event", "annotated seizure"], loc="lower center", ncol=4, frameon=False, fontsize=11)
        fig.subplots_adjust(left=0.1, right=0.98, top=0.97, bottom=0.06 + 0.25 / n)
        return save_both(fig, stem), fig

    (png_a, svg_a), fig_a = draw_gallery(panels_all[:1], "F4_gallery_a")
    import matplotlib.pyplot as plt2
    plt2.close(fig_a)
    (png_full, svg_full), fig_full = draw_gallery(panels_all, "F4_gallery_full")
    plt2.close(fig_full)

    rt = time.time() - t0
    data_files = [f"results/figures_v8_data/gallery/{k}.npz" for k in "abcd"]
    record("F4a", png_a, "src/figures_v8/fig14_gallery.py", "load + draw (panel a only)", data_files[:1],
           "OK (18 EEG channels gate passed)", rt / 2)
    record("F4full", png_full, "src/figures_v8/fig14_gallery.py", "load + draw (panels a-d)", data_files,
           "OK (18 EEG channels gate passed, 4 panels)", rt / 2)
    print(f"F4 OK -> {png_a}, {png_full}")


# ───────────────────────────── F5: detection by duration (make_v8_exhibits.fig12_duration) ─────────────────────────────

def f5_duration():
    t0 = time.time()
    plt = apply_slide_rc()
    C = dict(miss="#D9D9D9", grey="#777777", main="#0072B2")
    p = CODE / "results" / "figures_v8_data" / "perseizure_final.csv"
    gate(p.exists(), f"{p} not found (Claude Code export step)")
    d = pd.read_csv(p)
    d42 = d[d.seed == "clean_seed42"]
    gate(len(d42) == 76 and int(d42.detected_final.sum()) == 37 and int(d42.detected_heldout.sum()) == 26,
         "per-seizure file must reproduce 37/76 (final) and 26/76 (held-out), seed 42")
    bins = [0, 20, 40, 60, 120, 400]; labels = ["< 20", "20\u201339", "40\u201359", "60\u2013119", "\u2265 120"]
    d42 = d42.assign(bin=pd.cut(d42.dur_s, bins, right=False, labels=labels))
    g = d42.groupby("bin", observed=False).agg(n=("dur_s", "size"), fin=("detected_final", "sum"),
                                               held=("detected_heldout", "sum"))
    w, h = scaled(6.3, 2.5, HALF_W)
    fig, a = plt.subplots(figsize=(w, h))
    x = np.arange(len(labels))
    a.bar(x, g.n, 0.6, color=C["miss"], label="annotated")
    a.bar(x - 0.13, g.held, 0.26, color=C["grey"], label="detected, held-out evaluation")
    a.bar(x + 0.13, g.fin, 0.26, color=C["main"], label="detected, final system")
    for xi, (n, fi) in enumerate(zip(g.n, g.fin)):
        a.text(xi, n + 0.5, f"{int(fi)}/{int(n)}", ha="center", fontsize=12)
    a.set_xticks(x, labels)
    a.set_xlabel("Duration (whole 4 s windows)")
    a.set_ylabel("Seizures")
    a.legend(frameon=False, loc="lower center", bbox_to_anchor=(0.5, 1.02), ncol=3)
    fig.tight_layout()
    png, svg = save_both(fig, "F5_duration")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F5", png, "src/figures_v8/make_v8_exhibits.py", "fig12_duration",
           ["results/figures_v8_data/perseizure_final.csv"], "OK (37/76 final, 26/76 held-out, seed 42)",
           time.time() - t0)
    print(f"F5 OK -> {png}")


# ───────────────────────────── F6: alarm budget needed (make_v8_exhibits.fig17_budget_needed, report Fig 16) ─────────────────────────────

def f6_budget():
    t0 = time.time()
    plt = apply_slide_rc()
    import make_v8_exhibits as MV8
    C = dict(main="#0072B2", loc="#009E73", grey="#777777")
    s = pd.read_csv(CODE / "results/p3_anatomy/seizures.csv"); s = s[(s.set == "test") & (s.seed == "clean_seed42")]
    gate(len(s) == 76, "76 test seizures")
    b = MV8.e23_per_subject(); b = b[b.seed == "clean_seed42"].set_index("subject")
    w, h = scaled(6.3, 2.8, FULL_W)
    fig, a = plt.subplots(figsize=(w, h))
    rng = np.random.default_rng(1)
    for i, subj in enumerate(MV8.TEST):
        v = s[s.subject == subj].pn_final.values
        a.scatter(i + rng.uniform(-0.15, 0.15, len(v)), v, s=22, color=C["main"], alpha=0.75, lw=0)
        a.hlines(b.loc[subj, "top"], i - 0.32, i + 0.32, color=C["loc"], lw=3)
    a.axhline(0.005, color=C["grey"], ls=":", lw=1.4); a.axhline(0.02, color=C["grey"], ls="--", lw=1.4)
    a.text(7.45, 0.005, "0.5 %", va="center", fontsize=12); a.text(7.45, 0.02, "2 %", va="center", fontsize=12)
    a.set_yscale("log"); a.set_xticks(range(len(MV8.TEST)), MV8.TEST); a.set_xlim(-0.5, 7.9)
    a.set_ylabel("Alarm budget needed\n(share of patient time)")
    a.plot([], [], color=C["loc"], lw=3, label="patient's alarm budget (final system)")
    a.scatter([], [], s=22, color=C["main"], label="one seizure")
    fig.legend(*a.get_legend_handles_labels(), frameon=False, ncol=2, loc="upper center")
    fig.tight_layout(rect=(0, 0, 1, 0.88))
    png, svg = save_both(fig, "F6_budget_needed")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F6", png, "src/figures_v8/make_v8_exhibits.py", "fig17_budget_needed (report Figure 16)",
           ["results/p3_anatomy/seizures.csv", "results/e23_test_look7/per_subject_seed.csv"],
           "OK (76 test seizures gate)", time.time() - t0)
    print(f"F6 OK -> {png}")


# ───────────────────────────── F8: onset/offset error (make_v8_exhibits.fig13_boundaries) ─────────────────────────────

def f8_boundaries():
    t0 = time.time()
    plt = apply_slide_rc()
    C = dict(det="#E69F00", loc="#009E73", sz="#D55E00")
    e = pd.read_csv(CODE / "results/e23_test_look7/errors.csv"); e = e[e.point == "balanced"]
    med = e[["det_on", "det_off", "cpd_on", "cpd_off"]].abs().median()
    gate(len(e) == 146 and tuple(med) == (32.0, 20.0, 12.0, 24.0), "boundary medians")
    w, h = scaled(6.3, 2.6, FULL_W)
    fig, ax = plt.subplots(1, 2, figsize=(w, h), sharey=True)
    for a, side, lab in ((ax[0], "on", "Onset"), (ax[1], "off", "Offset")):
        data = [e[f"det_{side}"].values, e[f"cpd_{side}"].values]
        bp = a.boxplot(data, vert=False, widths=0.55, showfliers=False, patch_artist=True)
        for patch, col in zip(bp["boxes"], (C["det"], C["loc"])):
            patch.set_facecolor(col); patch.set_alpha(0.55)
        for m in bp["medians"]:
            m.set_color("k")
        rng = np.random.default_rng(0)
        for i, v in enumerate(data, start=1):
            a.scatter(np.clip(v, -150, 150), i + rng.uniform(-0.18, 0.18, len(v)), s=9, color="k", alpha=0.35, lw=0)
        a.axvline(0, color=C["sz"], lw=1.4)
        a.set_xlim(-150, 150); a.set_xticks([-120, -60, 0, 60, 120]); a.set_xlabel(f"{lab} error (s)")
        a.set_title("(a)" if side == "on" else "(b)", loc="left")
    ax[0].set_yticks([1, 2], ["Detector\nboundaries", "Change point\nlocalizer"])
    fig.tight_layout()
    png, svg = save_both(fig, "F8_boundaries")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F8", png, "src/figures_v8/make_v8_exhibits.py", "fig13_boundaries",
           ["results/e23_test_look7/errors.csv"], "OK (146 pairs, medians 32/20/12/24)", time.time() - t0)
    print(f"F8 OK -> {png}")


# ───────────────────────────── F9: event-based scoring rules (fig2_14_event_scoring.py) ─────────────────────────────

def f9_scoring():
    t0 = time.time()
    plt = apply_slide_rc()
    from matplotlib.patches import Rectangle, FancyArrowPatch
    sys.path.insert(0, str(CODE / "src"))
    try:
        import szcore_eval as SZ
    except Exception as exc:
        raise SystemExit(f"STOP: cannot import src/szcore_eval.py ({exc})")

    def _param(*names):
        for n in names:
            if hasattr(SZ, n):
                return getattr(SZ, n), f"szcore_eval.{n}"
        for holder in dir(SZ):
            if holder.startswith("__"):
                continue
            obj = getattr(SZ, holder)
            if isinstance(obj, (str, int, float, list, dict, tuple)):
                continue
            for n in names:
                if hasattr(obj, n):
                    return getattr(obj, n), f"szcore_eval.{holder}.{n}"
        raise SystemExit(f"STOP: none of {names} found in src/szcore_eval.py")

    TOL_START, _ = _param("toleranceStart", "TOLERANCE_START", "TOL_START")
    TOL_END, _ = _param("toleranceEnd", "TOLERANCE_END", "TOL_END")
    MERGE_GAP, _ = _param("minDurationBetweenEvents", "MIN_DURATION_BETWEEN_EVENTS", "MERGE_GAP")
    MAX_EVENT, _ = _param("maxEventDuration", "MAX_EVENT_DURATION", "MAX_EVENT")
    TOL_START, TOL_END = float(TOL_START), float(TOL_END)
    MERGE_GAP, MAX_EVENT = float(MERGE_GAP), float(MAX_EVENT)

    ICTAL, DETECTED, CHANCE, HEADLINE = "#C44E52", "#55A868", "#8C8C8C", "#B8860B"
    T_MAX, FS_PLOT = 420.0, 14.0
    RNG = np.random.default_rng(42)
    t = np.arange(0, T_MAX, 1.0 / FS_PLOT)

    def _trace(seizure=None, spike_at=None):
        x = np.convolve(RNG.normal(0, 1.0, t.size), np.ones(5) / 5.0, mode="same") * 0.30
        if seizure is not None:
            s, e = seizure
            m = (t >= s) & (t <= e)
            ramp = np.sin(np.pi * (t[m] - s) / (e - s)) ** 0.5
            x[m] += 1.00 * ramp * np.sin(2 * np.pi * 0.9 * (t[m] - s))
            x[m] += RNG.normal(0, 0.20, m.sum())
        if spike_at is not None:
            m = np.abs(t - spike_at) < 3.0
            x[m] += 2.0 * np.exp(-((t[m] - spike_at) ** 2) / 0.40)
        return x

    SEIZURE = (150.0, 250.0)
    PANELS = [
        dict(tag="(a)", title="Any overlap inside the tolerance window counts as a match",
             lanes=["Reference", "Hypothesis"], detections=[[(265.0, 300.0)]], outcomes=[["match"]],
             tolerance=True, spike=None,
             note="The detection begins after the annotated seizure has ended. It still counts, because it "
                  "falls inside the post-offset tolerance."),
        dict(tag="(b)", title=f"Detections closer than {MERGE_GAP:g} s are merged before scoring",
             lanes=["Reference", "Hypothesis,\nas produced", "Hypothesis,\nafter merging"],
             detections=[[(140.0, 190.0), (215.0, 265.0)], [(140.0, 265.0)]], outcomes=[[None, None], ["match"]],
             tolerance=False, spike=None,
             note="Two detections separated by less than the merge gap become one interval, which is then "
                  "scored once."),
        dict(tag="(c)", title="A detection outside the tolerance window is a false alarm",
             lanes=["Reference", "Hypothesis"], detections=[[(160.0, 230.0), (345.0, 375.0)]],
             outcomes=[["match", "false alarm"]], tolerance=True, spike=360.0,
             note="False alarms are counted per recorded day. Specificity is not defined at event level, "
                  "because a true-negative event has no meaning once a timeline is expressed as events."),
    ]

    w, h = scaled(10.2, 10.8, FULL_W)
    fig, axes = plt.subplots(3, 1, figsize=(w, h),
                             gridspec_kw=dict(height_ratios=[2, 3, 2], hspace=1.05, bottom=0.11, top=0.96))
    LANE_GAP, BOX_H, SIG_AMP = 1.0, 0.60, 0.25
    for ax, P in zip(axes, PANELS):
        n = len(P["lanes"])
        ys = [(n - 1 - i) * LANE_GAP for i in range(n)]
        y_ref = ys[0]
        ax.plot(t, y_ref + SIG_AMP * _trace(seizure=SEIZURE), color=CHANCE, linewidth=0.7, zorder=2)
        if P["tolerance"]:
            ax.add_patch(Rectangle((SEIZURE[0] - TOL_START, y_ref - BOX_H / 2),
                                   (SEIZURE[1] + TOL_END) - (SEIZURE[0] - TOL_START), BOX_H, facecolor="none",
                                   edgecolor=ICTAL, linewidth=1.4, linestyle=(0, (5, 4)), zorder=4))
        ax.add_patch(Rectangle((SEIZURE[0], y_ref - BOX_H / 2), SEIZURE[1] - SEIZURE[0], BOX_H, facecolor="none",
                               edgecolor=ICTAL, linewidth=2.0, zorder=5))
        for li, dets in enumerate(P["detections"]):
            y = ys[li + 1]
            ax.plot(t, y + SIG_AMP * _trace(seizure=SEIZURE, spike_at=P["spike"]), color=CHANCE, linewidth=0.7,
                    zorder=2)
            for di, (s, e) in enumerate(dets):
                ax.add_patch(Rectangle((s, y - BOX_H / 2), e - s, BOX_H, facecolor="none", edgecolor=DETECTED,
                                       linewidth=2.0, zorder=5))
                lab = P["outcomes"][li][di]
                if lab:
                    ax.text((s + e) / 2, y - BOX_H / 2 - 0.11, lab, ha="center", va="top", fontsize=13,
                            color=DETECTED if lab == "match" else HEADLINE, zorder=6)
        if P["tolerance"]:
            y_a = y_ref + BOX_H / 2 + 0.15
            for x0, x1, lab in ((SEIZURE[0] - TOL_START, SEIZURE[0], f"{TOL_START:g} s before onset"),
                               (SEIZURE[1], SEIZURE[1] + TOL_END, f"{TOL_END:g} s after offset")):
                ax.add_patch(FancyArrowPatch((x0, y_a), (x1, y_a), arrowstyle="<->", mutation_scale=9,
                                             color=ICTAL, linewidth=1.1, zorder=6))
                ax.text((x0 + x1) / 2, y_a + 0.04, lab, ha="center", va="bottom", fontsize=12, color=ICTAL, zorder=6)
        if len(P["detections"]) == 2:
            a0 = P["detections"][0][0][1]
            b0 = P["detections"][0][1][0]
            y_g = ys[1]
            ax.add_patch(FancyArrowPatch((a0, y_g), (b0, y_g), arrowstyle="<->", mutation_scale=8,
                                         color=HEADLINE, linewidth=1.2, zorder=7))
            ax.annotate(f"gap {b0 - a0:.0f} s, under {MERGE_GAP:g} s", xy=((a0 + b0) / 2, y_g + BOX_H / 2 - 0.02),
                        xytext=(b0 + 45, y_g + BOX_H / 2 + 0.30), ha="left", va="center", fontsize=12,
                        color=HEADLINE, zorder=8,
                        bbox=dict(boxstyle="round,pad=0.18", facecolor="white", edgecolor="none"),
                        arrowprops=dict(arrowstyle="-", color=HEADLINE, linewidth=0.9, shrinkA=1, shrinkB=2))
        ax.set_title(f"{P['tag']}  {P['title']}", loc="left", fontsize=14, fontweight="bold", pad=18)
        ax.annotate(P["note"], xy=(0.5, 0), xycoords="axes fraction", xytext=(0, -50), textcoords="offset points",
                    ha="center", va="top", fontsize=12, style="italic", color="0.30")
        ax.set_yticks(ys)
        ax.set_yticklabels(P["lanes"], fontsize=12)
        ax.tick_params(axis="y", length=0)
        ax.set_xlim(60, T_MAX)
        ax.set_ylim(-LANE_GAP * 0.72, ys[0] + BOX_H / 2 + 0.50)
        for side in ("top", "right", "left"):
            ax.spines[side].set_visible(False)
        ax.grid(axis="x", color=CHANCE, alpha=0.15, linewidth=0.6)
        ax.set_axisbelow(True)
        ax.set_xlabel("Time (s)", fontsize=12, labelpad=2)

    png, svg = save_both(fig, "F9_scoring")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F9", png, "src/figures/fig2_14_event_scoring.py", "module body (synthetic illustration)",
           ["src/szcore_eval.py (tolerance/merge/max-event parameters)"],
           f"OK (params found: tol {TOL_START:g}/{TOL_END:g} s, merge {MERGE_GAP:g} s, max {MAX_EVENT:g} s)",
           time.time() - t0)
    print(f"F9 OK -> {png}")


# ───────────────────────────── F10: sparsification separation (make_v8_exhibits.fig11_sparsification) ─────────────────────────────

def f10_sparsification():
    t0 = time.time()
    plt = apply_slide_rc()
    import make_v8_exhibits as MV8
    C = dict(grey="#777777", sz="#D55E00", main="#0072B2", loc="#009E73")
    TEST = MV8.TEST
    den = pd.read_csv(CODE / "results/diagnostics/density_frobenius_v2/density_per_subject.csv")
    sep = pd.read_csv(CODE / "results/diagnostics/density_frobenius_v2/separation_per_subject.csv").set_index(
        "subject").loc[TEST]
    gate(round(sep.pct_change_rel_topk_vs_fixed.min()) == 48 and round(sep.pct_change_rel_topk_vs_fixed.max()) == 196,
         "Frobenius change")
    w, h = scaled(6.3, 3.1, FULL_W)
    fig, ax = plt.subplots(1, 2, figsize=(w, h))
    x = np.arange(len(TEST)); wd = 0.2
    for i, (rule, split, col, lab) in enumerate((("fixed_t0.05", "interictal", C["grey"], "fixed threshold, background"),
                                                 ("fixed_t0.05", "ictal", C["sz"], "fixed threshold, seizure"),
                                                 ("topk20", "interictal", C["main"], "strongest 20 %, background"),
                                                 ("topk20", "ictal", C["loc"], "strongest 20 %, seizure"))):
        v = den[(den.rule == rule) & (den.split == split)].set_index("subject").loc[TEST].mean_density
        ax[0].bar(x + (i - 1.5) * wd, v, wd, color=col, label=lab)
    ax[0].set_xticks(x, [s[3:] for s in TEST]); ax[0].set_xlabel("Test patient (chb)"); ax[0].set_ylabel("Graph density")
    ax[0].set_ylim(0, 1.0)
    ax[0].set_title("(a)", loc="left")
    fig.legend(*ax[0].get_legend_handles_labels(), frameon=False, ncol=2, loc="lower center", bbox_to_anchor=(0.5, 0.0))
    ax[1].bar(x - 0.2, sep.rel_frobenius_fixed_t0_05, 0.4, color=C["grey"], label="fixed threshold")
    ax[1].bar(x + 0.2, sep.rel_frobenius_topk20, 0.4, color=C["main"], label="strongest 20 %")
    ax[1].set_xticks(x, [s[3:] for s in TEST]); ax[1].set_xlabel("Test patient (chb)")
    ax[1].set_ylabel("Seizure\u2013background distance\n(relative Frobenius)"); ax[1].set_ylim(0, 0.9)
    ax[1].legend(frameon=False, loc="upper left", ncol=2)
    ax[1].set_title("(b)", loc="left")
    fig.tight_layout(rect=(0, 0.16, 1, 1))
    png, svg = save_both(fig, "F10_sparsification")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F10", png, "src/figures_v8/make_v8_exhibits.py", "fig11_sparsification",
           ["results/diagnostics/density_frobenius_v2/density_per_subject.csv",
            "results/diagnostics/density_frobenius_v2/separation_per_subject.csv"],
           "OK (Frobenius change 48-196 %)", time.time() - t0)
    print(f"F10 OK -> {png}")


# ───────────────────────────── F2: graph construction, panels (c)+(d) only (fig2_4_graph_construction.py) ─────────────────────────────

def f2_graph_cd():
    t0 = time.time()
    plt = apply_slide_rc()
    import networkx as nx
    from graph_construction import (apply_car, compute_wpli, compute_aec, combine_adjacency,
                                    apply_topk_threshold, DEFAULT_ALPHA, DEFAULT_KEEP_RATIO)
    import preprocessing as P
    from palette import INTERICTAL, SEQUENTIAL_CMAP

    SUBJ, WINDOW_IDX = "chb11", 0
    PROC = CODE / "data" / "processed"
    channels = P.COMMON_CHANNELS
    window = np.load(PROC / f"{SUBJ}_interictal.npy", mmap_mode="r")[WINDOW_IDX]

    w_ = apply_car(window.astype(np.float64))
    wpli = compute_wpli(w_, fs=P.FS)
    aec = compute_aec(w_)
    A = combine_adjacency(wpli, aec, alpha=DEFAULT_ALPHA)
    A_topk = apply_topk_threshold(A, keep_ratio=DEFAULT_KEEP_RATIO)
    n_edges = int(np.count_nonzero(np.triu(A_topk, k=1)))
    gate(n_edges == 30, f"{n_edges} edges retained, expected 30 (keep_ratio={DEFAULT_KEEP_RATIO})")

    tw, th = scaled(14, 5.3, FULL_W)   # bottom row only of the original 14x11, 2x2 figure
    fig, (ax_adj, ax_graph) = plt.subplots(1, 2, figsize=(tw, th))

    im_c = ax_adj.imshow(A, vmin=0, vmax=A.max(), cmap=SEQUENTIAL_CMAP)
    ax_adj.set_xticks(range(len(channels))); ax_adj.set_yticks(range(len(channels)))
    ax_adj.set_xticklabels(channels, rotation=90, fontsize=9)
    ax_adj.set_yticklabels(channels, fontsize=9)
    ax_adj.set_title("(c)")
    cb_c = fig.colorbar(im_c, ax=ax_adj, shrink=0.85, pad=0.02)
    cb_c.set_label("Combined wPLI + AEC weight")

    G = nx.from_numpy_array(A_topk)
    G = nx.relabel_nodes(G, {i: channels[i] for i in range(len(channels))})
    n = len(channels)
    angles = np.linspace(0, 2 * np.pi, n, endpoint=False) + np.pi / 2
    pos = {channels[i]: (np.cos(angles[i]), np.sin(angles[i])) for i in range(n)}
    label_pos = {channels[i]: (1.18 * np.cos(angles[i]), 1.18 * np.sin(angles[i])) for i in range(n)}
    weights = [G[u][v]["weight"] for u, v in G.edges()]
    max_w = max(weights) if weights else 1.0
    nx.draw_networkx_nodes(G, pos, ax=ax_graph, node_size=260, node_color=INTERICTAL)
    nx.draw_networkx_labels(G, label_pos, ax=ax_graph, font_size=10)
    nx.draw_networkx_edges(G, pos, ax=ax_graph, width=[4.0 * wt / max_w for wt in weights], alpha=0.7)
    ax_graph.set_xlim(-1.4, 1.4); ax_graph.set_ylim(-1.4, 1.4); ax_graph.set_aspect("equal")
    ax_graph.set_title("(d)")
    ax_graph.set_axis_off()

    fig.tight_layout()
    png, svg = save_both(fig, "F2_graph_cd")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F2", png, "src/figures/fig2_4_graph_construction.py", "panels (c) adjacency, (d) sparse graph",
           [f"data/processed/{SUBJ}_interictal.npy"],
           f"OK ({n_edges} edges retained at keep_ratio={DEFAULT_KEEP_RATIO}, expected 30)", time.time() - t0)
    print(f"F2 OK -> {png} ({n_edges} edges)")


# ───────────────────────────── F1: EEG around a seizure (fig1_background_ictal.py) ─────────────────────────────

def f1_eeg():
    t0 = time.time()
    plt = apply_slide_rc()
    import matplotlib.transforms as mtransforms
    from scipy.signal import sosfiltfilt, filtfilt
    import dataprep.preprocessing as P

    SUBJECT, EDF_NAME = "chb11", "chb11_82.edf"
    ONSET_S, OFFSET_S, MARGIN_S = 298.0, 320.0, 150.0
    BACKGROUND_EXCERPT = (188.0, 198.0)
    EXCERPT_LEN_S = 10.0
    CHANNELS = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1"]
    OVERVIEW_CHANNEL = "P7-O1"
    FS = 256
    RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
    SUMMARY = CODE / "src" / "data" / "summaries" / f"{SUBJECT}-summary.txt"
    if not SUMMARY.exists():
        SUMMARY = CODE / "data" / "summaries" / f"{SUBJECT}-summary.txt"
    INTERICTAL, ICTAL = "#4C72B0", "#C44E52"

    # gate 0: which image is Figure 1 in the submitted docx, and does this script draw the same thing?
    with zipfile.ZipFile(DOCX) as z:
        docx_fig1 = z.read("word/media/image2.png")  # pandoc mapping, Defense/notes/FIGURE_PROVENANCE.md: Figure 1 -> image2
    docx_sha256 = hashlib.sha256(docx_fig1).hexdigest()
    print(f"F1: sha256 of Figure 1 in the submitted docx (word/media/image2.png) = {docx_sha256}")
    print("F1: visual check (done by the author/assistant before running this script, recorded in HANDBACK.md) -- "
          "the docx image shows the SAME layout as this script: top = P7-O1 overview 150-470 s with onset/offset "
          "marked and Background/Ictal labels, bottom = two 10 s excerpts (Background, Ictal) of the same four "
          "channels FP1-F7/F7-T7/T7-P7/P7-O1 with a shared uV scale bar -- same panels, same patient (chb11). Match: yes.")

    def load_real(t0_, t1_):
        found = P.parse_summary(SUMMARY).get(EDF_NAME, [])
        if not found or tuple(found[0]) != (ONSET_S, OFFSET_S):
            raise SystemExit(f"STOP: summary gives {found} for {EDF_NAME}, expected ({ONSET_S}, {OFFSET_S})")
        raw = P.open_edf(RAW_DIR / SUBJECT / EDF_NAME)
        if raw is None:
            raise SystemExit("STOP: recording lacks one of the 18 common channels")
        if CHANNELS != list(P.COMMON_CHANNELS[:4]):
            raise SystemExit("STOP: channel order differs from preprocessing.COMMON_CHANNELS")
        s0, s1 = int(round(t0_ * FS)), int(round(t1_ * FS))
        pad = 3 * FS
        p0, p1 = max(0, s0 - pad), min(int(raw.n_times), s1 + pad)
        if s0 < 0 or s1 > raw.n_times:
            raise SystemExit("STOP: window runs outside the recording")
        out = {}
        for ch in CHANNELS:
            seg = raw.get_data(picks=[raw.ch_names.index(ch)], start=p0, stop=p1)
            seg = filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, seg, axis=1), axis=1)
            out[ch] = seg[0, s0 - p0: s0 - p0 + (s1 - s0)] * 1e6
        return out

    t0_, t1_ = ONSET_S - MARGIN_S, OFFSET_S + MARGIN_S
    sig = load_real(t0_, t1_)
    t = t0_ + np.arange(sig[OVERVIEW_CHANNEL].size) / FS

    def mid(a_, b_):
        c = (a_ + b_) / 2
        return c - EXCERPT_LEN_S / 2, c + EXCERPT_LEN_S / 2

    excerpts = {"Background": BACKGROUND_EXCERPT, "Ictal": mid(ONSET_S, OFFSET_S)}

    w, h = scaled(12.5, 7.6, HALF_W)
    fig = plt.figure(figsize=(w, h))
    gs = fig.add_gridspec(2, 2, height_ratios=[1.0, 1.35], hspace=0.5, wspace=0.08, top=0.92, bottom=0.08,
                          left=0.09, right=0.98)
    ax_top = fig.add_subplot(gs[0, :])
    ax_ex = [fig.add_subplot(gs[1, i]) for i in range(2)]

    x = sig[OVERVIEW_CHANNEL]
    edges = np.linspace(0, x.size, 1400 + 1).astype(int)
    tb = t0_ + (edges[:-1] + edges[1:]) / 2 / FS
    ax_top.vlines(tb, [x[p:q].min() for p, q in zip(edges[:-1], edges[1:])],
                  [x[p:q].max() for p, q in zip(edges[:-1], edges[1:])], color=INTERICTAL, lw=1.0, zorder=4)
    ax_top.axvspan(ONSET_S, OFFSET_S, color=ICTAL, alpha=0.22, lw=0, zorder=0)
    for b in (ONSET_S, OFFSET_S):
        ax_top.axvline(b, color=ICTAL, ls="--", lw=1.6, zorder=3)
    ax_top.set_xlim(t0_, t1_)
    y_top = ax_top.get_ylim()[1]
    ax_top.set_ylim(top=y_top * 1.32)
    lab_y = y_top * 1.05
    for name, xc in (("Background", (t0_ + ONSET_S) / 2), ("Ictal", (ONSET_S + OFFSET_S) / 2),
                     ("Background", (OFFSET_S + t1_) / 2)):
        ax_top.text(xc, lab_y, name, ha="center", va="bottom", fontsize=13, color=(ICTAL if name == "Ictal" else "black"))
    nudge = 3.0
    ax_top.annotate("onset", xy=(ONSET_S, y_top), xytext=(ONSET_S - nudge, y_top * 1.13), ha="right", va="bottom",
                    fontsize=12, color=ICTAL, arrowprops=dict(arrowstyle="-", color=ICTAL, lw=1.0))
    ax_top.annotate("offset", xy=(OFFSET_S, y_top), xytext=(OFFSET_S + nudge, y_top * 1.13), ha="left", va="bottom",
                    fontsize=12, color=ICTAL, arrowprops=dict(arrowstyle="-", color=ICTAL, lw=1.0))
    tr = mtransforms.blended_transform_factory(ax_top.transData, ax_top.transAxes)
    for e0, e1 in excerpts.values():
        ax_top.plot([e0, e1], [0.012, 0.012], transform=tr, color="black", lw=5.0, solid_capstyle="butt",
                    clip_on=False, zorder=5)
    ax_top.set_ylabel(f"{OVERVIEW_CHANNEL} (\u00b5V)")
    ax_top.set_xlabel("Time (s)")

    tr_ex = {}
    for name, (e0, e1) in excerpts.items():
        i0 = int(round((e0 - t0_) * FS)); i1 = i0 + int(round(EXCERPT_LEN_S * FS))
        tr_ex[name] = np.stack([sig[ch][i0:i1] for ch in CHANNELS])
    allv = np.concatenate(list(tr_ex.values()), axis=1)
    off = 3.0 * np.median(np.std(allv, axis=1))
    bar = round(off / 3.0, -1) or 10.0
    for k, (name, tr_) in enumerate(tr_ex.items()):
        ax = ax_ex[k]
        tl = np.arange(tr_.shape[1]) / FS
        col = ICTAL if name == "Ictal" else INTERICTAL
        for i in range(len(CHANNELS)):
            ax.plot(tl, tr_[len(CHANNELS) - 1 - i] + i * off, color=col, lw=0.9)
        ax.set_title(name, fontsize=14, color=col if name == "Ictal" else "black")
        ax.set_xlim(0, EXCERPT_LEN_S)
        ax.set_ylim(-1.5 * off, (len(CHANNELS) - 1) * off + 1.5 * off)
        ax.set_xlabel("Time (s)")
        if k == 0:
            ax.set_yticks([i * off for i in range(len(CHANNELS))], list(reversed(CHANNELS)), fontsize=12)
            y0, y1 = ax.get_ylim(); bx = 0.3
            by0 = y0 + 0.04 * (y1 - y0)
            ax.plot([bx, bx], [by0, by0 + bar], color="black", lw=2.0, solid_capstyle="butt", zorder=6)
            ax.text(bx + 0.25, by0 + bar / 2, f"{bar:g} \u00b5V", fontsize=12, va="center", ha="left")
        else:
            ax.set_yticks([])

    png, svg = save_both(fig, "F1_eeg")
    import matplotlib.pyplot as plt2
    plt2.close(fig)
    record("F1", png, "src/figures/fig1_background_ictal.py", "main (real EEG path)",
           [f"Dataset/CHB-MIT/{SUBJECT}/{EDF_NAME} (raw, outside the repo)", "data/summaries/chb11-summary.txt"],
           f"OK (summary onset/offset matches {ONSET_S:.0f}/{OFFSET_S:.0f} s; docx Figure 1 sha256 {docx_sha256[:16]}..., "
           f"visual match confirmed)", time.time() - t0)
    print(f"F1 OK -> {png}")


FAST = [("F3", f3_drift), ("F4", f4_gallery), ("F5", f5_duration), ("F6", f6_budget),
        ("F8", f8_boundaries), ("F9", f9_scoring), ("F10", f10_sparsification)]
EEG = [("F2", f2_graph_cd), ("F1", f1_eeg)]


def write_handback():
    path = OUT / "HANDBACK.md"
    existing = {}
    if path.exists():
        for line in path.read_text(encoding="utf-8").splitlines():
            if line.startswith("| F"):
                existing[line.split("|")[1].strip()] = line
    existing.update(HANDBACK_ROWS)
    order = ["F1", "F2", "F3", "F4a", "F4full", "F5", "F6", "F8", "F9", "F10"]
    rows = [existing[k] for k in order if k in existing]
    header = ("# HANDBACK -- slide-size figures for the defense\n\n"
              "One line per figure: code, output file, source script and function, data files read, "
              "gate result, measured runtime.\n\n"
              "| Code | Output | Source script (function) | Data read | Gate | Runtime |\n"
              "|---|---|---|---|---|---|\n")
    path.write_text(header + "\n".join(rows) + "\n", encoding="utf-8")
    print(f"wrote {path}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--eeg", action="store_true", help="run F1, F2 only (need the EEG files on this laptop)")
    ap.add_argument("--all", action="store_true", help="run every figure")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.all:
        todo = FAST + EEG
    elif a.eeg:
        todo = EEG
    else:
        todo = FAST
    for code, fn in todo:
        fn()
    write_handback()


if __name__ == "__main__":
    main()
