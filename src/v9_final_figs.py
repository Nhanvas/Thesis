#!/usr/bin/env python
"""
v9_final_figs.py -- V9-FINAL Part D (docs/prompts/V9_FINAL_VERIFY.md): slide figure pack, items 1-4
and 7 (CHB-MIT detected/missed/false-alarm, Siena detected/missed, model comparison). Items 5 (web
demo screenshot), 6 (hospital EEG) and 8 (ASR, after Part A) are handled separately -- see
FIGURE_INDEX.md's own "pending" rows, written here too so the index is complete even before those
run.

ONE clean style for every event panel (8 of the highest-RMS-channel slide version + an 18-channel
backup): real filtered EEG, grey band = annotated seizure (P3L.refs_of), teal band = system event
(the thesis system's own `loc`, after the localizer), a thin score-trace strip below (the frozen
final scalar `res["x"]`, NOT a bar chart -- v9_eeg_evidence.draw_eeg's existing strips are bars, so
this script draws its own line-trace strip instead of reusing draw_eeg for the strip, though the EEG
panel itself, read_window, top_k_channels and the grey/teal band logic ARE reused verbatim) with the
alarm threshold line (`res["thr"]`, the same per-patient quantile the system itself alarms against),
two vertical ticks at the localized event's own onset/offset, time in seconds from the event's
reference onset, plain-words title, no file paths, no internal labels.

Selection rules (fixed here, before drawing; every rule is also written into FIGURE_INDEX.md):
  1. Detected: the CHB-MIT-test true detection (thesis system, seed 42, after the localizer) whose
     onset error (E18.match_errors(refs, loc), signed, seconds) is closest to the median onset error
     over all CHB-MIT-test true detections. Plus a fixed second pick, chb03's own first seizure
     (earliest onset_s in chb03's own file list) -- the prompt's own fixed choice, not a measured rule.
  2. Missed: the CHB-MIT-test missed seizure (thesis system) whose amplitude ratio (results/v9_v1/
     part1_descriptors.csv) is closest to the median amplitude ratio over all CHB-MIT-test missed
     seizures.
  3. False alarm: among the 8 CHB-MIT-test patients, the one whose own false-alarm COUNT (thesis
     system, localized stage) is closest to the median patient FP count; among that patient's own
     false alarms, the one with the highest peak score (v9_eeg_evidence.event_peak_score).
  4. Siena: detected picked the SAME way as item 1 (closest to the median onset error, over all Siena
     true detections); missed picked the SAME way as item 2 (closest to the median amplitude ratio
     over Siena missed seizures) -- the prompt only gives the detected-seizure rule explicitly for
     Siena, so the missed-seizure rule is this script's own fixed choice, logged here rather than
     picked by hand.
  7. Model comparison: results/v9_x3/sys_sweep.csv's own three arms (GAE-CV, kNN-LOO, GAE+kNN-CV),
     per-case-mean sensitivity vs FP/day, matched grid = the sweep's own k_mult points (NOT just the
     three FP_TARGETS used elsewhere for a table -- a continuous-looking curve needs more points than
     that), 24 cases every arm.

READ-ONLY REUSE: v9_eeg_evidence.py (ctx_and_res_G/read_window/top_k_channels/event_peak_score/
file_index/spacing_for/event_done, CH/FS), v9_anatomy.py (test_ctx/build_or_load_ext/SIENA_ALL_14),
p3_levers.py (refs_of), e18_cpd_localizer.py (match_errors), v9_e1_baselines.py (TEST).

OUTPUT: F:/Study/Thesis/Defense/slides/figs/final/ (one *_slide.png + one *_full18.png per event, plus
model_comparison.png), F:/Study/Thesis/Defense/slides/figs/final/FIGURE_INDEX.md.
Run:  python src/v9_final_figs.py --select     (print the 5 picks + model-comparison data, no drawing)
      python src/v9_final_figs.py --draw       (draw everything selectable from committed data)
      python src/v9_final_figs.py --index      (write/refresh FIGURE_INDEX.md)
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_eeg_evidence as V9V           # noqa: E402 -- read-only reuse
import v9_anatomy as V9A                # noqa: E402
import v9_e1_baselines as V9E1          # noqa: E402
import p3_levers as P3L                 # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402

OUT = Path("F:/Study/Thesis/Defense/slides/figs/final")
PART1 = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
CH, FS = V9V.CH, V9V.FS
TEST = V9E1.TEST
SIENA = V9A.SIENA_ALL_14
MARGIN_S = 20.0   # seconds of context shown either side of the plotted span


def _fname(ctx, f):
    return str(ctx["z"]["files"][int(f)])


# ============================================================================ selection
def _test_detected_table():
    rows = []
    for s in TEST:
        ctx, res = V9V.ctx_and_res_G(s, "chb-test")
        refs = P3L.refs_of(ctx)
        for f, a, b, h0, h1 in E18.match_errors(refs, res["loc"]):
            rows.append(dict(subject=s, setname="chb-test", file=_fname(ctx, f), file_idx=int(f),
                              onset_s=a, offset_s=b, dur_s=b - a, loc_on=h0, loc_off=h1,
                              onset_err=h0 - a))
    return pd.DataFrame(rows)


def _siena_detected_table():
    rows = []
    for s in SIENA:
        ctx, res = V9V.ctx_and_res_G(s, "siena")
        refs = P3L.refs_of(ctx)
        for f, a, b, h0, h1 in E18.match_errors(refs, res["loc"]):
            rows.append(dict(subject=s, setname="siena", file=_fname(ctx, f), file_idx=int(f),
                              onset_s=a, offset_s=b, dur_s=b - a, loc_on=h0, loc_off=h1,
                              onset_err=h0 - a))
    return pd.DataFrame(rows)


def pick_detected_test():
    D = _test_detected_table()
    med = D.onset_err.median()
    pick = D.iloc[(D.onset_err - med).abs().values.argmin()]
    chb03 = D[D.subject == "chb03"].sort_values("onset_s").iloc[0]
    return pick, chb03, D


def pick_missed_test():
    desc = pd.read_csv(PART1)
    test = desc[desc.set == "chb-test"]
    missed = test[~test.caught]
    med = missed.amp_ratio.median()
    pick = missed.iloc[(missed.amp_ratio - med).abs().values.argmin()]
    return pick, missed


def pick_siena_detected_missed():
    D = _siena_detected_table()
    med = D.onset_err.median()
    det_pick = D.iloc[(D.onset_err - med).abs().values.argmin()]
    desc = pd.read_csv(PART1)
    siena = desc[desc.set == "siena"]
    missed = siena[~siena.caught]
    medm = missed.amp_ratio.median()
    miss_pick = missed.iloc[(missed.amp_ratio - medm).abs().values.argmin()]
    return det_pick, miss_pick, D, missed


def pick_false_alarm():
    fp_counts = {}
    fp_rows = {}
    for s in TEST:
        ctx, res = V9V.ctx_and_res_G(s, "chb-test")
        refs = P3L.refs_of(ctx)
        matched_hyp = {(f, h0, h1) for f, a, b, h0, h1 in E18.match_errors(refs, res["loc"])}
        fps = []
        for f, evs in res["loc"].items():
            for h0, h1 in evs:
                if (f, h0, h1) not in matched_hyp:
                    score = V9V.event_peak_score(ctx, res, f, h0, h1)
                    fps.append(dict(subject=s, file=_fname(ctx, f), file_idx=int(f), onset_s=h0,
                                     offset_s=h1, dur_s=h1 - h0, peak_score=score))
        fp_counts[s] = len(fps)
        fp_rows[s] = pd.DataFrame(fps)
    counts = pd.Series(fp_counts)
    med = counts.median()
    med_patient = (counts - med).abs().idxmin()
    d = fp_rows[med_patient]
    if not len(d):
        raise SystemExit(f"STOP: median-FP patient {med_patient} has 0 false alarms -- pick a different rule")
    pick = d.loc[d.peak_score.idxmax()]
    return pick, med_patient, counts


# ============================================================================ drawing (unified style)
def draw_event_panel(outdir, tag, subj, setname, file_idx, span_t0, span_t1, title, ref_band, loc_band,
                      event_onset, score_x, score_t0_s, thr):
    """score_x: the frozen final scalar, per-window, for the WHOLE file (res['x'] sliced to this file's
    windows) -- score_t0_s is the clock time (s) of score_x[0]. Draws a thin LINE trace (not bars, to
    read as a continuous alarm signal) with a dashed horizontal threshold line, plus two vertical ticks
    at the localized event's own onset/offset (loc_band's first entry inside the plotted span)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.gridspec import GridSpec

    out = V9V.read_window(subj, setname, _fname_lookup(subj, setname, file_idx), span_t0, span_t1)
    if out is None:
        return None
    filt, a, b = out
    WIN = 4.0
    n_win = filt.shape[1] // int(WIN * FS)
    sw0 = int(round((a - score_t0_s) / WIN))
    sx = score_x[sw0:sw0 + n_win]

    for fig_kind, k, big, figsize, dpi in (("slide", 8, True, (12.8, 7.2), 150), ("full18", 18, False, (8.5, 6.2), 200)):
        chan_idx, chan_names = V9V.top_k_channels(filt, CH, k=k)
        fig = plt.figure(figsize=figsize, dpi=dpi)
        gs = GridSpec(2, 1, height_ratios=[4.2, 1.1], hspace=0.30, left=0.09, right=0.98, top=0.90, bottom=0.10)
        ax_eeg, ax_sc = fig.add_subplot(gs[0]), fig.add_subplot(gs[1])

        t = a - event_onset + np.arange(filt.shape[1]) / FS
        spacing = V9V.spacing_for([filt])
        offs = np.arange(len(chan_idx))[::-1] * spacing
        lim = 1.2 * spacing
        fs_lbl, fs_tick = (16, 13) if big else (7, 6)
        for row, ci in enumerate(chan_idx):
            y = np.clip(filt[ci], -lim, lim)
            ax_eeg.plot(t, y + offs[row], lw=0.5 if big else 0.35, color="#111111")
        ax_eeg.set_yticks(offs); ax_eeg.set_yticklabels(chan_names, fontsize=fs_tick)
        ax_eeg.set_xlim(span_t0 - event_onset, span_t1 - event_onset)
        ax_eeg.set_ylim(-1.4 * spacing, offs[0] + 1.4 * spacing)
        rb0, rb1 = ref_band
        if rb1 >= span_t0 and rb0 <= span_t1:
            ax_eeg.axvspan(rb0 - event_onset, rb1 - event_onset, color="#808080", alpha=0.20, lw=0)
        lb0, lb1 = loc_band
        if lb1 >= span_t0 and lb0 <= span_t1:
            ax_eeg.axvspan(lb0 - event_onset, lb1 - event_onset, color="#008080", alpha=0.20, lw=0)
        ax_eeg.set_title(title, fontsize=fs_lbl + (2 if big else 0), loc="left")
        ax_eeg.tick_params(axis="x", labelsize=fs_tick)
        for sp in ("top", "right"):
            ax_eeg.spines[sp].set_visible(False)
        xb = (span_t0 - event_onset) + 0.012 * (span_t1 - span_t0)
        yb = -1.25 * spacing
        ax_eeg.plot([xb, xb], [yb, yb + spacing], color="#1f77b4", lw=2.0 if big else 1.4, solid_capstyle="butt")
        ax_eeg.text(xb + 0.008 * (span_t1 - span_t0), yb + spacing * 0.5, f"{spacing:g} uV",
                    fontsize=fs_tick + (2 if big else 0), color="#1f77b4", va="center", ha="left")

        ts = np.arange(len(sx)) * WIN + (a - event_onset)
        ax_sc.plot(ts, sx, lw=1.3 if big else 0.9, color="#333333")
        ax_sc.axhline(thr, color="#c0392b", lw=1.1, ls="--")
        if lb1 > lb0:   # no system event (missed seizure): nothing to mark, draw no ticks
            for vx in (lb0 - event_onset, lb1 - event_onset):
                if span_t0 - event_onset <= vx <= span_t1 - event_onset:
                    ax_sc.axvline(vx, color="#008080", lw=1.4)
        ax_sc.set_xlim(span_t0 - event_onset, span_t1 - event_onset)
        ax_sc.set_ylabel("alarm score", fontsize=fs_tick + (3 if big else 0))
        ax_sc.set_xlabel("time from event onset (s)", fontsize=fs_lbl)
        ax_sc.tick_params(labelsize=fs_tick)
        for sp in ("top", "right"):
            ax_sc.spines[sp].set_visible(False)

        fig.savefig(outdir / f"{tag}_{fig_kind}.png")
        plt.close(fig)
    return outdir / f"{tag}_slide.png"


def _fname_lookup(subj, setname, file_idx):
    ctx, _ = V9V.ctx_and_res_G(subj, setname)
    return _fname(ctx, file_idx)


def draw_from_pick(tag, row, title, margin=MARGIN_S):
    subj, setname = row.subject, row["setname"]
    ctx, res = V9V.ctx_and_res_G(subj, setname)
    f = int(row.file_idx)
    refs = P3L.refs_of(ctx)
    ref_band = next(((a, b) for a, b in refs.get(f, []) if a - 1 <= row.onset_s <= a + 1), (row.onset_s, row.get("offset_s", row.onset_s)))
    loc_band = (row.get("loc_on", row.onset_s), row.get("loc_off", row.get("offset_s", row.onset_s)))
    span_t0 = min(ref_band[0], loc_band[0]) - margin
    span_t1 = max(ref_band[1], loc_band[1]) + margin
    m = np.flatnonzero(ctx["fidx"] == f)
    score_x_full = res["x"][m]
    score_t0_s = 0.0
    OUT.mkdir(parents=True, exist_ok=True)
    if V9V.event_done(OUT, tag):
        return OUT / f"{tag}_slide.png"
    return draw_event_panel(OUT, tag, subj, setname, f, span_t0, span_t1, title, ref_band, loc_band,
                             ref_band[0], score_x_full, score_t0_s, res["thr"])


def draw_missed(tag, row, title, margin=MARGIN_S):
    subj, setname = row.subject, "chb-test" if row.set == "chb-test" else "siena"
    ctx, res = V9V.ctx_and_res_G(subj, setname)
    f = V9V.file_index(ctx, row.file)
    onset_s, dur_s = float(row.onset_s), float(row.duration_s)
    ref_band = (onset_s, onset_s + dur_s)
    loc_band = (onset_s, onset_s)   # missed: no localized event: no teal band, ticks collapse to nothing visible
    span_t0, span_t1 = onset_s - margin, onset_s + dur_s + margin
    m = np.flatnonzero(ctx["fidx"] == f)
    score_x_full = res["x"][m]
    OUT.mkdir(parents=True, exist_ok=True)
    if V9V.event_done(OUT, tag):
        return OUT / f"{tag}_slide.png"
    return draw_event_panel(OUT, tag, subj, setname, f, span_t0, span_t1, title, ref_band, (onset_s, onset_s),
                             onset_s, score_x_full, 0.0, res["thr"])


def draw_false_alarm(tag, row, title, margin=MARGIN_S):
    subj, setname = row.subject, "chb-test"
    ctx, res = V9V.ctx_and_res_G(subj, setname)
    f = int(row.file_idx)
    loc_band = (float(row.onset_s), float(row.offset_s))
    span_t0, span_t1 = loc_band[0] - margin, loc_band[1] + margin
    m = np.flatnonzero(ctx["fidx"] == f)
    score_x_full = res["x"][m]
    OUT.mkdir(parents=True, exist_ok=True)
    if V9V.event_done(OUT, tag):
        return OUT / f"{tag}_slide.png"
    return draw_event_panel(OUT, tag, subj, setname, f, span_t0, span_t1, title, (loc_band[0], loc_band[0]),
                             loc_band, loc_band[0], score_x_full, 0.0, res["thr"])


# ============================================================================ item 5: web demo comparison
def item5_web_demo():
    """V9-FINAL Part D item 5: the already-retaken SzScan screenshot (V9-V1-FIX, chb03_01.edf's
    only seizure, duration 56 s -- matches this pass's own item1_chb03_first pick exactly) next to
    the SAME event drawn in this pass's unified style. No new browser session: V9-V1-FIX already
    retook this screenshot read-only (web_demo untouched, same as here)."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    shot_path = Path("F:/Study/Thesis/Defense/slides/figs/eeg_evidence/part3/szscan_screenshots"
                     "/chb03_TP_event1.jpg")
    panel_path = OUT / "item1_chb03_first_slide.png"
    if not shot_path.exists() or not panel_path.exists():
        raise SystemExit(f"STOP: missing {shot_path} or {panel_path} -- run --draw first")
    shot = plt.imread(shot_path)
    panel = plt.imread(panel_path)
    fig, axes = plt.subplots(2, 1, figsize=(14, 11), dpi=150)
    axes[0].imshow(shot); axes[0].axis("off")
    axes[0].set_title("Web demo (SzScan), 500 uV -- patient chb03, event 1 (duration 0:56)", fontsize=15)
    axes[1].imshow(panel); axes[1].axis("off")
    axes[1].set_title("Same seizure, this pack's style", fontsize=15)
    fig.tight_layout()
    fig.savefig(OUT / "item5_web_demo_comparison.png")
    plt.close(fig)
    print(f"wrote {OUT/'item5_web_demo_comparison.png'}", flush=True)


# ============================================================================ item 7: model comparison
def model_comparison():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    SYS = pd.read_csv(ROOT / "results" / "v9_x3" / "sys_sweep.csv")
    ARM_LABEL = {"GAE-CV": "GAE", "kNN-LOO": "kNN", "GAE+kNN-CV": "GAE + kNN"}
    COLOR = {"GAE-CV": "#1f77b4", "kNN-LOO": "#d62728", "GAE+kNN-CV": "#2ca02c"}
    fig, ax = plt.subplots(figsize=(16, 9), dpi=150)
    for arm in ("GAE-CV", "kNN-LOO", "GAE+kNN-CV"):
        d = SYS[SYS.arm == arm].copy()
        d["sens"] = d.tp / d.n_ref
        d["fa"] = d.fp / d.nonict_h * 24
        pm = d.groupby("k_mult")[["sens", "fa"]].mean().reset_index().sort_values("fa")
        ax.plot(pm.fa, pm.sens, marker="o", ms=5, lw=2.2, color=COLOR[arm], label=ARM_LABEL[arm])
    ax.set_xlabel("false alarms per day (per-case mean)", fontsize=18)
    ax.set_ylabel("sensitivity (per-case mean)", fontsize=18)
    ax.set_title("Model comparison -- 24-case cross-validation", fontsize=20)
    ax.tick_params(labelsize=14)
    ax.legend(fontsize=16)
    ax.set_xlim(0, 60)
    fig.tight_layout()
    OUT.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT / "model_comparison.png")
    plt.close(fig)
    print(f"wrote {OUT/'model_comparison.png'}", flush=True)


# ============================================================================ select / draw / index
def run_select():
    det_pick, chb03_pick, det_tab = pick_detected_test()
    miss_pick, miss_tab = pick_missed_test()
    fa_pick, fa_patient, fa_counts = pick_false_alarm()
    s_det, s_miss, s_det_tab, s_miss_tab = pick_siena_detected_missed()

    print("=== item 1: detected (median onset error) ===")
    print(det_pick); print(f"median onset_err over {len(det_tab)} matches = {det_tab.onset_err.median():.1f}s")
    print("\n=== item 1b: chb03 first seizure ===")
    print(chb03_pick)
    print("\n=== item 2: missed (median amp ratio) ===")
    print(miss_pick); print(f"median amp_ratio over {len(miss_tab)} missed = {miss_tab.amp_ratio.median():.3f}")
    print("\n=== item 3: false alarm (median-FP patient, highest score) ===")
    print(f"per-patient FP counts:\n{fa_counts.to_string()}\nmedian-FP patient = {fa_patient}")
    print(fa_pick)
    print("\n=== item 4: siena detected ===")
    print(s_det); print(f"median onset_err over {len(s_det_tab)} matches = {s_det_tab.onset_err.median():.1f}s")
    print("\n=== item 4: siena missed ===")
    print(s_miss); print(f"median amp_ratio over {len(s_miss_tab)} missed = {s_miss_tab.amp_ratio.median():.3f}")
    return dict(det=det_pick, chb03=chb03_pick, miss=miss_pick, fa=fa_pick, fa_patient=fa_patient,
                s_det=s_det, s_miss=s_miss)


def run_draw():
    t0 = time.time()
    picks = run_select()
    p1a = draw_from_pick("item1_detected_test", picks["det"],
                         f"Detected seizure -- patient {picks['det'].subject}")
    p1b = draw_from_pick("item1_chb03_first", picks["chb03"],
                         "Detected seizure -- patient chb03 (first seizure)")
    p2 = draw_missed("item2_missed_test", picks["miss"], f"Missed seizure -- patient {picks['miss'].subject}")
    p3 = draw_false_alarm("item3_false_alarm", picks["fa"], f"False alarm -- patient {picks['fa'].subject}")
    p4a = draw_from_pick("item4_siena_detected", picks["s_det"],
                         f"Detected seizure -- Siena patient {picks['s_det'].subject}")
    p4b = draw_missed("item4_siena_missed", picks["s_miss"],
                      f"Missed seizure -- Siena patient {picks['s_miss'].subject}")
    model_comparison()
    print(f"\ndraw done in {time.time()-t0:.0f}s: {[p1a, p1b, p2, p3, p4a, p4b]}", flush=True)


def write_index():
    OUT.mkdir(parents=True, exist_ok=True)
    L = ["# FIGURE_INDEX -- V9-FINAL Part D slide figure pack\n",
         "Every row: file, what it shows, the selection rule (fixed before drawing), the numbers printed "
         "on/under it and their source file, a proposed caption. Style (all rows 1-4, 8): 16:9 slide "
         "version (8 highest-RMS channels) + 18-channel backup, real filtered EEG, grey band = annotated "
         "seizure, teal band = system event, thin score trace below with the dashed red alarm threshold "
         "line, two teal vertical ticks at the localizer's own onset/offset, time in seconds from the "
         "event's reference onset, plain-words title, no file paths, no internal labels.\n",
         "| # | file | what it shows | selection rule | numbers (source) | proposed caption |",
         "|---|---|---|---|---|---|"]
    rows = [
        ("1a", "item1_detected_test_slide.png", "A true detection, CHB-MIT test, thesis system after "
         "the localizer", "onset error closest to the median onset error over all CHB-MIT-test true "
         "detections (results/v9_final/hard/ construction reused; onset errors from e18_cpd_localizer."
         "match_errors on results/e23_test_look7-gated loc events)", "onset/offset error (s), seconds "
         "from onset on the x-axis (results/v9_v1/part1_descriptors.csv + this script's own match)",
         "\"Detected seizure -- patient <X>\""),
        ("1b", "item1_chb03_first_slide.png", "chb03's first seizure, detected", "fixed pick (the "
         "prompt's own choice): earliest onset_s in chb03's own CHB-MIT-test file list", "same as above",
         "\"Detected seizure -- patient chb03\""),
        ("2", "item2_missed_test_slide.png", "A missed seizure, CHB-MIT test", "amplitude ratio closest "
         "to the median amplitude ratio over all CHB-MIT-test missed seizures (results/v9_v1/"
         "part1_descriptors.csv)", "amplitude ratio (results/v9_v1/part1_descriptors.csv)",
         "\"Missed seizure -- patient <X>\""),
        ("3", "item3_false_alarm_slide.png", "A false alarm, CHB-MIT test", "the test patient whose own "
         "false-alarm count (thesis system, localized) is closest to the median patient FP count; among "
         "that patient's own false alarms, the highest peak score (v9_eeg_evidence.event_peak_score)",
         "peak alarm score (results/e23_test_look7, this script's own per-patient FP table)",
         "\"False alarm -- patient <X>\""),
        ("4a", "item4_siena_detected_slide.png", "A true detection, Siena", "SAME rule as item 1 "
         "(median onset error), over Siena's 14 patients", "onset error (results/x1_external, this "
         "script's own match)", "\"Detected seizure -- Siena patient <X>\""),
        ("4b", "item4_siena_missed_slide.png", "A missed seizure, Siena", "SAME rule as item 2 (median "
         "amplitude ratio), over Siena's missed seizures -- the prompt gives this rule only for the "
         "detected pick; this script fixes the same rule for missed, logged here rather than picked by "
         "hand", "amplitude ratio (results/v9_v1/part1_descriptors.csv)",
         "\"Missed seizure -- Siena patient <X>\""),
        ("7", "model_comparison.png", "GAE vs kNN vs GAE+kNN, 24-case CV", "every arm's own per-case-mean "
         "sensitivity/FP-day at every sys_sweep k_mult grid point (no cherry-picked points)",
         "results/v9_x3/sys_sweep.csv", "\"Model comparison -- 24-case cross-validation\""),
    ]
    for r in rows:
        L.append("| " + " | ".join(r) + " |")
    L += ["\n## Pending (not drawn by this script)\n",
          "- **Item 5 (web demo)**: the retaken SzScan screenshot of chb03 (500 uV) next to the same "
          "event drawn in this style -- needs a live browser session against web_demo (never touched by "
          "this script per the Rules); run separately, same event-matching approach as V9-V1-FIX.",
          "- **Item 6 (hospital EEG)**: clin02 score timeline + clin01 event panel -- real clinical data "
          "under `F:/Study/Thesis/Defense/clinical/`, privacy rules of V9_C1 apply (neutral captions, no "
          "artifact/seizure claim); not drawn here pending that access/privacy check.",
          "- **Item 8 (ASR before/after)**: needs Part A finished first (median + max share-removed "
          "seizure); drawn after Part A, same style, same uV scale before/after."]
    (OUT / "FIGURE_INDEX.md").write_text("\n".join(L), encoding="utf-8")
    print(f"wrote {OUT/'FIGURE_INDEX.md'}", flush=True)


def main():
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--select", action="store_true")
    ap.add_argument("--draw", action="store_true")
    ap.add_argument("--index", action="store_true")
    a = ap.parse_args()
    if a.select:
        run_select()
    elif a.draw:
        run_draw()
    elif a.index:
        write_index()
    else:
        raise SystemExit("pass --select, --draw or --index")


if __name__ == "__main__":
    main()
