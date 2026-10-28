#!/usr/bin/env python
"""
v9_eeg_samples.py -- V9-T3 Part B: real-EEG figures of what the final system catches, misses, and
false-alarms on. Read-only on every committed result and on v9_anatomy.py's output; reuses
v9_anatomy.py's contexts, caches and final_events() (same final system, same seed 42, same balanced
point) and raw_eeg_view.py's own filtering (filter_window_mem / read_segment, bit-exact with the
pipeline) -- no new filtering code, no smoothing beyond the pipeline's.

SELECTION RULE (fixed here, BEFORE any panel is drawn; also written to selection.csv):
  CHB-MIT test, per patient (8 patients):
    TP  the true detection (caught=True in v9_anatomy's per_seizure.csv) with the lowest p_need
        (= the highest score: p_need is 1 - the within-patient percentile of its peak smoothed score,
        so lower p_need is a higher score, patient by patient -- v9_anatomy.pneed_fn);
    FN  the missed seizure (caught=False) whose duration is closest to the patient's OWN median
        reference-seizure duration (over every reference seizure of that patient, caught or not);
    FP  the false alarm (false_alarms.csv) with the highest peak_score.
  Siena: the same 3 picks for the 4 patients with the most reference seizures (seed 42, balanced,
    after the localizer: results/x1_external SUMMARY -- PN10=10, PN00=5, PN06=5, PN12=4/PN14=4 tie),
    plus the shortest seizure overall. DEVIATION (forced by data availability, not a choice made after
    looking at any picture): only PN00, PN10, PN11 have their raw EDF in this checkout (v9_anatomy.py's
    SIENA_LOCAL / SIENA_MISSING); PN06, PN12, PN14 cannot be drawn. The rule above is applied to the
    patients that ARE available (PN00, PN10 are 2 of the true top 4; PN11 is substituted as the third
    available patient) and "shortest seizure overall" is computed over the available 3 patients' own
    reference seizures only (not the true Siena-wide shortest, which may be in a missing patient) --
    both facts are printed and written to selection.csv, never silently dropped.

DRAWING: 18 bipolar channels (preprocessing.COMMON_CHANNELS order), real pipeline-filtered signal
(raw_eeg_view.read_segment for CHB-MIT; ext_read_segment below -- same bandpass+notch, same
FILTER_PAD, same zero-phase filtfilt -- for chb24/Siena, reusing x1_external.filters/load_18), one
common microvolt scale per figure, >= 60 s around the event (more if the event itself is longer, same
margin rule as raw_eeg_view: pad to >=60 s total, else +-15 s), grey shading = reference annotation
(TP/FN), teal shading = the system's (localized) event (TP/FP), a one-row strip under the traces of
the unsmoothed ensemble score (the frozen final scalar, v9_anatomy.final_events) per 4 s window, time
axis in seconds from the event's own onset. Title: "<patient>  <file>  <TP|FN|FP>  duration <d> s".
PNG at 200 dpi per panel plus one contact sheet per set (chb-test, siena). No AI drawing; the only
filtering is the pipeline's own (verified bit-exact by raw_eeg_view.py's own --selfcheck and by this
script's reuse of its functions, never reimplemented).

OUTPUT: F:/Study/Thesis/Defense/slides/figs/eeg_samples/ (figures + selection.csv), results/v9_anatomy/
 (nothing else here -- Part B writes no new result CSVs beyond selection.csv, which lives with the figures
 per the task's own output path).

V9-T4 (--siena-full): once all 14 Siena patients are available and v9_anatomy.py --siena-full has run,
re-draws Siena with the ORIGINAL rule (no deviation) -- the true 4 patients with the most reference
seizures (counted directly, not the V9-T3 fallback) plus the true shortest seizure over all 14. Writes
only F:/.../eeg_samples/siena14/; the V9-T3 3-patient figures above are untouched.
Run:  python src/v9_eeg_samples.py --smoke     (1 CHB-MIT test patient only)
      python src/v9_eeg_samples.py             (needs results/v9_anatomy/per_seizure.csv + false_alarms.csv)
      python src/v9_eeg_samples.py --siena-full  (needs results/v9_anatomy/siena14/*.csv)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import filtfilt, sosfiltfilt

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                       # noqa: E402
from matplotlib.gridspec import GridSpec              # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_anatomy as V9                 # noqa: E402
import p2_scalars as PS                 # noqa: E402
import raw_eeg_view as RV               # noqa: E402
import x1_external as X1                # noqa: E402
import preprocessing as P               # noqa: E402

FIGOUT = Path("F:/Study/Thesis/Defense/slides/figs/eeg_samples")
CH = list(P.COMMON_CHANNELS)
WIN = 4
MARGIN_LONG = 15.0
MIN_TOTAL = 60.0
SIENA_TOP4_RANK = ["PN10", "PN00", "PN06", "PN12"]   # from results/x1_external SUMMARY.md (n_ref 10,5,5,4)


# ============================================================================ segment readers
def ext_read_segment(path, kind, notch, t0_s, t1_s):
    """chb24 / Siena analogue of raw_eeg_view.read_segment: same bandpass+notch, same FILTER_PAD,
    reusing x1_external.load_18 / x1_external.filters (no new filtering code)."""
    data = X1.load_18(path, kind)
    if data is None:
        return None
    n_total = data.shape[1]
    s = max(0, int(round(t0_s * P.FS)))
    e = min(n_total, int(round(t1_s * P.FS)))
    ps, pe = max(0, s - P.FILTER_PAD), min(n_total, e + P.FILTER_PAD)
    seg = data[:, ps:pe]
    sos, b, aa = X1.filters(notch)
    bp = sosfiltfilt(sos, seg, axis=1)
    notched = filtfilt(b, aa, bp, axis=1)
    off = s - ps
    filt = notched[:, off:off + (e - s)] * 1e6
    rawf = seg[:, off:off + (e - s)] * 1e6
    return filt, rawf, s / P.FS, e / P.FS


def margin_for(duration_s):
    if duration_s >= MIN_TOTAL:
        return MARGIN_LONG
    return max(MARGIN_LONG, (MIN_TOTAL - duration_s) / 2.0)


# ============================================================================ selection
def pick_three(seiz, fa, patients, setname):
    """the TP / FN / FP rule for one set (chb-test or siena-3of14)."""
    picks = []
    for s in patients:
        d = seiz[(seiz.set == setname) & (seiz.subject == s)]
        if not len(d):
            continue
        med_dur = d.duration_s.median()
        tp = d[d.caught]
        if len(tp):
            r = tp.loc[tp.p_need.idxmin()]
            picks.append(dict(subject=s, kind="TP", file=r.file, onset_s=int(r.onset_s),
                              duration_s=int(r.duration_s), rule="lowest p_need (highest score) true detection"))
        fn = d[~d.caught]
        if len(fn):
            r = fn.loc[(fn.duration_s - med_dur).abs().idxmin()]
            picks.append(dict(subject=s, kind="FN", file=r.file, onset_s=int(r.onset_s),
                              duration_s=int(r.duration_s),
                              rule=f"missed seizure closest to the patient's median duration ({med_dur:.0f} s)"))
        f = fa[(fa.set == setname) & (fa.subject == s)]
        if len(f):
            r = f.loc[f.peak_score.idxmax()]
            picks.append(dict(subject=s, kind="FP", file=r.file, onset_s=int(r.onset_s),
                              duration_s=int(r.duration_s), rule="highest peak-score false alarm"))
    return picks


def pick_chb_test(seiz, fa, patients):
    return pick_three(seiz, fa, patients, "chb-test")


def pick_siena(seiz, fa, patients):
    picks = pick_three(seiz, fa, patients, "siena-3of14")
    for p in picks:
        p["set"] = "siena-3of14"
    d = seiz[seiz.set == "siena-3of14"]
    if len(d):
        r = d.loc[d.duration_s.idxmin()]
        kind = "TP (shortest)" if r.caught else "FN (shortest)"
        picks.append(dict(subject=r.subject, kind=kind, file=r.file, onset_s=int(r.onset_s),
                          duration_s=int(r.duration_s), rule="shortest reference seizure, available patients only",
                          set="siena-3of14"))
    return picks


def pick_siena_full(seiz, fa):
    """V9-T4: the ORIGINAL rule (no deviation) -- the 4 patients with the most reference seizures,
    counted directly from the siena-14 per-seizure rows, plus the shortest seizure over all 14."""
    d14 = seiz[seiz.set == "siena-14"]
    counts = d14.groupby("subject").size().sort_values(ascending=False)
    top4 = list(counts.index[:4])
    picks = pick_three(seiz, fa, top4, "siena-14")
    for p in picks:
        p["set"] = "siena-14"
    if len(d14):
        r = d14.loc[d14.duration_s.idxmin()]
        kind = "TP (shortest)" if r.caught else "FN (shortest)"
        picks.append(dict(subject=r.subject, kind=kind, file=r.file, onset_s=int(r.onset_s),
                          duration_s=int(r.duration_s), rule="shortest reference seizure, all 14 patients",
                          set="siena-14"))
    return picks, top4, counts


# ============================================================================ context / score access
_CTX_CACHE = {}


def ctx_and_res(subj, setname):
    key = (subj, setname)
    if key in _CTX_CACHE:
        return _CTX_CACHE[key]
    if setname == "chb-test":
        ctx = V9.test_ctx(subj)
    elif setname == "chb24":
        ctx, _ = V9.build_or_load_ext(subj, V9.CHB_DATA)
    else:
        ctx, _ = V9.build_or_load_ext(subj, V9.SIENA_DATA)
    res = V9.final_events(ctx, V9.HEAD)
    _CTX_CACHE[key] = (ctx, res)
    return ctx, res


def score_strip(ctx, res, file_id, w0, w1):
    """unsmoothed final scalar, one value per 4 s window, local window indices [w0, w1)."""
    m = np.flatnonzero(ctx["fidx"] == file_id)
    w0, w1 = max(0, w0), min(len(m), w1)
    g = m[w0:w1]
    x = res["x"][g].copy()
    x[~ctx["ok"][g]] = np.nan
    return x, w0, w1


def refs_and_loc(ctx, res, file_id):
    m = np.flatnonzero(ctx["fidx"] == file_id)
    refs = [(a * WIN, b * WIN) for a, b in PS._runs(ctx["ict"][m])]
    loc = res["loc"].get(file_id, [])
    return refs, loc


# ============================================================================ drawing
def draw_panel(ax_eeg, ax_score, filt, t0, t1, title, refs, loc, event_onset, spacing_uV, score_vals, score_t0):
    n = filt.shape[1]
    t = t0 - event_onset + np.arange(n) / P.FS
    offs = np.arange(len(CH))[::-1] * spacing_uV
    lim = 1.2 * spacing_uV
    for ci in range(len(CH)):
        y = np.clip(filt[ci], -lim, lim)
        ax_eeg.plot(t, y + offs[ci], lw=0.35, color="#111111")
    ax_eeg.set_yticks(offs); ax_eeg.set_yticklabels(CH, fontsize=6)
    ax_eeg.set_xlim(t0 - event_onset, t1 - event_onset)
    ax_eeg.set_ylim(-1.4 * spacing_uV, offs[0] + 1.4 * spacing_uV)
    for a, b in refs:
        if b >= t0 and a <= t1:
            ax_eeg.axvspan(a - event_onset, b - event_onset, color="#808080", alpha=0.18, lw=0)
    for a, b in loc:
        if b >= t0 and a <= t1:
            ax_eeg.axvspan(a - event_onset, b - event_onset, color="#008080", alpha=0.18, lw=0)
    ax_eeg.set_title(title, fontsize=8, loc="left")
    ax_eeg.tick_params(axis="x", labelsize=6)
    for s in ("top", "right"):
        ax_eeg.spines[s].set_visible(False)
    xb = (t0 - event_onset) + 0.012 * (t1 - t0)
    yb = -1.25 * spacing_uV
    ax_eeg.plot([xb, xb], [yb, yb + spacing_uV], color="#1f77b4", lw=1.8, solid_capstyle="butt")
    ax_eeg.text(xb + 0.008 * (t1 - t0), yb + spacing_uV * 0.5, f"{spacing_uV:g} uV", fontsize=6,
               color="#1f77b4", va="center", ha="left")

    nb = len(score_vals)
    if nb:
        tb = (score_t0 - event_onset) + WIN * (np.arange(nb) + 0.5)
        ax_score.bar(tb, np.nan_to_num(score_vals, nan=0.0), width=WIN * 0.95, color="#555555")
    ax_score.set_xlim(t0 - event_onset, t1 - event_onset)
    ax_score.set_xlabel("time from event onset (s)", fontsize=6.5)
    ax_score.set_ylabel("score", fontsize=6)
    ax_score.tick_params(labelsize=6)
    for s in ("top", "right"):
        ax_score.spines[s].set_visible(False)


def spacing_for(segments):
    q = float(np.median([np.percentile(np.abs(s), 99.0) for s in segments]))
    target = 2.0 * q
    for v in (25, 50, 75, 100, 150, 200, 250, 300, 400, 500, 600, 800, 1000, 1500, 2000, 3000, 4000, 5000):
        if v >= target:
            return float(v)
    return float(np.ceil(target / 1000.0) * 1000)


def render(picks, setname, outdir):
    outdir.mkdir(parents=True, exist_ok=True)
    loaded = []
    for pk in picks:
        subj, kind, fname, onset, dur = pk["subject"], pk["kind"], pk["file"], pk["onset_s"], pk["duration_s"]
        setkey = pk.get("set", setname)
        ctx, res = ctx_and_res(subj, setkey)
        files = ctx["z"]["files"]
        fid = int(np.flatnonzero(files == fname)[0]) if (files == fname).any() else None
        if fid is None:
            print(f"  SKIP {subj} {kind} {fname}: file not found in this subject's context", flush=True)
            continue
        margin = margin_for(dur)
        t0, t1 = onset - margin, onset + dur + margin
        if setkey == "chb-test":
            seg = RV.read_segment(subj, fname, t0, t1)
            if seg is None:
                continue
            filt, _raw, a, b = seg
        else:
            path = (V9.CHB_DATA / subj / fname) if subj == "chb24" else (V9.SIENA_DATA / subj / fname)
            kind_, notch = ("chb", 60.0) if subj == "chb24" else ("siena", 50.0)
            out = ext_read_segment(path, kind_, notch, t0, t1)
            if out is None:
                continue
            filt, _raw, a, b = out
        refs, loc = refs_and_loc(ctx, res, fid)
        w0, w1 = int(a // WIN), int(np.ceil(b / WIN))
        score_vals, sw0, _sw1 = score_strip(ctx, res, fid, w0, w1)
        score_t0 = sw0 * WIN
        title = f"{subj}  {fname}  {kind}  duration {dur} s"
        loaded.append(dict(pk=pk, filt=filt, t0=a, t1=b, title=title, refs=refs, loc=loc,
                           onset=onset, score_vals=score_vals, score_t0=score_t0))
    if not loaded:
        return [], None
    spacing = spacing_for([d["filt"] for d in loaded])
    written = []
    for d in loaded:
        pk = d["pk"]
        fig = plt.figure(figsize=(8.5, 6.2), dpi=200)
        gs = GridSpec(2, 1, height_ratios=[4.2, 1.0], hspace=0.30, left=0.09, right=0.98, top=0.93, bottom=0.09)
        draw_panel(fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), d["filt"], d["t0"], d["t1"], d["title"],
                  d["refs"], d["loc"], d["onset"], spacing, d["score_vals"], d["score_t0"])
        kind_tag = pk["kind"].replace(" (", "-").replace(")", "").replace(" ", "-")
        tag = f"{pk['subject']}_{pk['file'].replace('.edf', '')}_{kind_tag}_{pk['onset_s']}"
        path = outdir / f"{setname}_{tag}.png"
        fig.savefig(path)
        plt.close(fig)
        written.append(path)
    n = len(loaded)
    ncols = 2
    nrows = int(np.ceil(n / ncols))
    fig = plt.figure(figsize=(ncols * 8.5, nrows * 6.2), dpi=100)
    gs = GridSpec(nrows * 2, ncols, height_ratios=[4.2, 1.0] * nrows, hspace=0.42, wspace=0.22,
                  left=0.05, right=0.98, top=0.97, bottom=0.03)
    for k, d in enumerate(loaded):
        r, c = divmod(k, ncols)
        draw_panel(fig.add_subplot(gs[2 * r, c]), fig.add_subplot(gs[2 * r + 1, c]), d["filt"], d["t0"], d["t1"],
                  d["title"], d["refs"], d["loc"], d["onset"], spacing, d["score_vals"], d["score_t0"])
    sheet = outdir / f"contact_sheet_{setname}.png"
    fig.savefig(sheet)
    plt.close(fig)
    return written, sheet


# ============================================================================ main
def run_siena14():
    t0 = time.time()
    pf = ROOT / "results" / "v9_anatomy" / "siena14" / "per_seizure.csv"
    ff = ROOT / "results" / "v9_anatomy" / "siena14" / "false_alarms.csv"
    if not pf.exists() or not ff.exists():
        raise SystemExit("STOP: results/v9_anatomy/siena14/per_seizure.csv and false_alarms.csv are "
                         "missing -- run `python src/v9_anatomy.py --siena-full` first")
    seiz, fa = pd.read_csv(pf), pd.read_csv(ff)
    picks, top4, counts = pick_siena_full(seiz, fa)
    outdir = FIGOUT / "siena14"
    outdir.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(picks).to_csv(outdir / "selection.csv", index=False)
    print(f"siena-14 selection: top 4 by seizure count = {top4} (counts: {dict(counts)}); "
          f"{len(picks)} picks -> {outdir / 'selection.csv'}", flush=True)
    w, s = render(picks, "siena14", outdir)
    print(f"siena14: {len(w)} panels -> {s}", flush=True)
    print(f"done in {time.time() - t0:.0f}s", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--siena-full", action="store_true",
                    help="V9-T4: re-draw Siena with the original top-4-by-seizure-count rule, all 14 "
                         "patients; writes F:/.../eeg_samples/siena14/ only, keeps the 3-patient set")
    a = ap.parse_args()
    if a.siena_full:
        run_siena14()
        return
    t0 = time.time()
    pf = ROOT / "results" / "v9_anatomy" / "per_seizure.csv"
    ff = ROOT / "results" / "v9_anatomy" / "false_alarms.csv"
    if not pf.exists() or not ff.exists():
        raise SystemExit("STOP: results/v9_anatomy/per_seizure.csv and false_alarms.csv are missing -- "
                         "run src/v9_anatomy.py (Part A) first")
    seiz, fa = pd.read_csv(pf), pd.read_csv(ff)

    chb_patients = sorted(seiz[seiz.set == "chb-test"].subject.unique())
    if a.smoke:
        chb_patients = chb_patients[:1]
    chb_picks = pick_chb_test(seiz, fa, chb_patients)

    siena_available = sorted(seiz[seiz.set == "siena-3of14"].subject.unique())
    top4_available = [s for s in SIENA_TOP4_RANK if s in siena_available]
    siena_patients = top4_available + [s for s in siena_available if s not in top4_available]
    siena_picks = [] if a.smoke else pick_siena(seiz, fa, siena_patients)

    sel = pd.DataFrame(chb_picks + siena_picks)
    FIGOUT.mkdir(parents=True, exist_ok=True)
    sel.to_csv(FIGOUT / "selection.csv", index=False)
    print(f"selection: {len(chb_picks)} chb-test picks, {len(siena_picks)} siena-3of14 picks "
          f"(rule fixed before drawing; see selection.csv and the module docstring)", flush=True)
    print(f"Siena deviation: patients available locally {siena_available}; true top-4 by seizure count "
          f"{SIENA_TOP4_RANK} -> {[s for s in SIENA_TOP4_RANK if s not in siena_available]} unavailable.",
          flush=True)

    w1, s1 = render(chb_picks, "chb-test", FIGOUT)
    print(f"chb-test: {len(w1)} panels -> {s1}", flush=True)
    if not a.smoke:
        w2, s2 = render(siena_picks, "siena", FIGOUT)
        print(f"siena: {len(w2)} panels -> {s2}", flush=True)
    print(f"done in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
