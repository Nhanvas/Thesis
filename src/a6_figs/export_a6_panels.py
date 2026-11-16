#!/usr/bin/env python
"""
export_a6_panels.py -- A6 panel export (docs/prompts/A6_FIGURES.md, chat A6 17/11). EXPORT ONLY: writes
results/a6_figs_data/<key>.npz in the panel format of src/figures_v8/export_v8_data.py so that
src/a6_figs/draw_eeg_figures.py can draw the report's real-EEG figures without recomputing anything.

READ-ONLY REUSE of the thesis code -- no result, no model and no frozen file is changed, and every event
drawn is the thesis system's own (seed 42 / clean_seed42, final system after the localizer):
  v9_eeg_evidence.py  -- ctx_and_res_G (frozen final system per subject), read_window (the real
                         pipeline-filtered EEG reader), file_index, _parse_channel_labels.
  v9_final_figs.py    -- pick_missed_test, pick_false_alarm, pick_siena_detected_missed (the selection
                         rules of FIGURE_INDEX.md items 2, 3 and 4a, called, not retyped).
  p3_levers.refs_of / p2_scalars.smoothed / v9_anatomy.SMOOTH -- the annotations and the system's own
                         smoothed alarm series (the series its threshold is a quantile of).
  e18_cpd_localizer.match_errors -- the detection/reference matching of the chb24 rule.
  results/attribution_v6/seizure_blocks.csv + attribution_v8/attribution_perseizure.csv +
  attribution_v8/attribution_scores.csv + attribution_v7/labels/source/Channel_label_approved.md
                      -- the Part 6 focal picks, their blind channel annotation and the model's own
                         channel-level latent-anomaly ranking (read, never recomputed).
  results/v9_x6/seizures.csv + v9_x6_asr.py (_get_trace / --extract-trace, cutoff 20)
                      -- the ASR before/after page of item 8a. aggregate() is NOT called: it would
                         rewrite the committed results/v9_x6/*.csv, so the committed seizures.csv is
                         read and the median-share rule applied to it.

PANELS (one .npz each; the figure each belongs to is in the table of A6_FIGURES.md):
  f16a  chb06/chb06_18.edf  seizure 7796 s, 16 s     -- missed test seizure, median amplitude ratio
  f17b  chb14/chb14_29.edf  false alarm 1476 s, 32 s -- highest-peak FA of the median-FP patient
  f10a  chb24/chb24_01.edf  seizure 480 s, 28 s      -- detection with the median onset error (chb24)
  f10b  PN09/PN09-2.edf     seizure 7124 s, 64 s     -- Siena detection with the median onset error
  f12a  chb15/chb15_15.edf  seizure 1591 s, 157 s    -- highest channel-ranking AUROC (chb15 seizure 2)
  f12b  chb16/chb16_17.edf  seizure 3290 s, 8 s      -- lowest channel-ranking AUROC (chb16 seizure 7)
  f18   chb15/chb15_40.edf  seizure 3362 s, 63 s     -- median share of power removed by ASR (cutoff 20)

GATE (per panel, before anything is written): the listed annotated seizure and/or localized event must
be present in the system's own output for that file. The system works on 4 s windows, so an annotation
appears in `refs_of` quantized to the window grid; a listed event therefore passes only if it matches
either its own times or its own times on that grid (floor of the onset, ceiling of the offset), each
within 1 s. Anything else STOPs that panel -- nothing is written and nothing is drawn for it. Every
selection rule is also re-checked against the event listed in the prompt, and STOPs if it differs.

OUTPUT KEYS (exactly draw_eeg_figures.py's): eeg [18, n] float16 (the real filtered EEG in uV,
decimated 256 -> 128 Hz for display, as export_v8_data.py does), fs, eeg_t0 (s in the file; the page is
anchor -10 s .. +20 s, the anchor being ann[0] else loc[0] else det[0]), ch, score_t/score/score_sm
(the system's own unsmoothed and smoothed alarm series of that file over anchor +-300 s), thr (the
patient's own final threshold), thr_heldout (NaN), ann/det/loc (s in the file, the listed event first),
title. f12a/f12b add ch_mark/ch_top bool[18]; f18 adds eeg_after (the same page after ASR).

Run:  python src/a6_figs/export_a6_panels.py              (all 7 panels)
      python src/a6_figs/export_a6_panels.py --only f16a f18
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import decimate

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import v9_eeg_evidence as V9V           # noqa: E402 -- read-only reuse
import v9_final_figs as V9F             # noqa: E402
import v9_anatomy as V9A                # noqa: E402
import p2_scalars as PS                 # noqa: E402
import p3_levers as P3L                 # noqa: E402
import e18_cpd_localizer as E18         # noqa: E402
import preprocessing as P               # noqa: E402

OUT = ROOT / "results" / "a6_figs_data"
CH = list(P.COMMON_CHANNELS)
WIN = V9A.WIN                            # 4 s
SMOOTH = V9A.SMOOTH
PRE, POST, PAD = 10.0, 20.0, 5.0         # EEG page: anchor -10 .. +20 s; +-5 s edge padding for decimate
SCORE_HALF = 300.0                       # score series: anchor +-5 min
DEC = 2                                  # 256 -> 128 Hz for display (export_v8_data.py's own choice)
TOL = 1.0                                # gate tolerance, seconds

BLOCKS = ROOT / "results" / "attribution_v6" / "seizure_blocks.csv"
PERSEIZ = ROOT / "results" / "attribution_v8" / "attribution_perseizure.csv"
CHSCORES = ROOT / "results" / "attribution_v8" / "attribution_scores.csv"
X6_SEIZ = ROOT / "results" / "v9_x6" / "seizures.csv"


# ----------------------------------------------------------------------------- gate
def _quantized(on, off):
    """how the pipeline's own 4 s windowing sees an annotation (p3_levers.refs_of on ctx['ict'])."""
    return float(np.floor(on / WIN) * WIN), float(np.ceil(off / WIN) * WIN)


def gate(key, what, on, off, have, fname):
    """STOP unless `have` (the system's own refs/loc list for that file) holds the listed event, either
    at its own times or at its own times on the 4 s window grid, each within TOL."""
    qon, qoff = _quantized(on, off)
    for ha, hb in have:
        for wa, wb, how in ((on, off, "exact"), (qon, qoff, "window-quantized")):
            if abs(ha - wa) <= TOL and abs(hb - wb) <= TOL:
                print(f"  gate OK [{key}] {what} {on:g}-{off:g} s in {fname}: the system has "
                      f"{ha:g}-{hb:g} s ({how})", flush=True)
                return float(ha), float(hb), how
    raise SystemExit(f"STOP [{key}]: {what} {on:g}-{off:g} s (window grid {qon:g}-{qoff:g}) is NOT in "
                     f"the system's own output for {fname}; it has "
                     f"{[(float(a), float(b)) for a, b in have]}. Nothing written for this panel.")


def gate_missed(key, on, off, loc_f, fname):
    """a missed seizure must have NO system event inside the SzCORE tolerance (p2_scalars.caught's own
    overlap rule: onset -30 s, offset +60 s)."""
    hit = [(a, b) for a, b in loc_f if b >= on - 30 and a <= off + 60]
    if hit:
        raise SystemExit(f"STOP [{key}]: seizure {on:g}-{off:g} s of {fname} is NOT missed by the final "
                         f"system -- events {hit} fall inside the tolerance. Nothing written.")
    print(f"  gate OK [{key}]: no system event within the SzCORE tolerance of {on:g}-{off:g} s "
          f"({len(loc_f)} event(s) elsewhere in {fname})", flush=True)


# ----------------------------------------------------------------------------- shared panel pieces
_SM_CACHE = {}


def smoothed_of(subj, setname, ctx, res):
    key = (subj, setname)
    if key not in _SM_CACHE:
        _SM_CACHE[key] = PS.smoothed(ctx, res["x"], SMOOTH)
    return _SM_CACHE[key]


def score_series(subj, setname, ctx, res, f, anchor):
    """the system's own alarm series of that file over anchor +-5 min: score = the frozen final scalar
    per 4 s window, score_sm = its own smoothed version (the series res['thr'] is a quantile of)."""
    sm = smoothed_of(subj, setname, ctx, res)
    m = np.flatnonzero(ctx["fidx"] == f)
    t = np.arange(len(m)) * float(WIN)
    sel = (t >= max(0.0, anchor - SCORE_HALF)) & (t <= anchor + SCORE_HALF)
    g = m[sel]
    return t[sel].astype(float), res["x"][g].astype(float), sm[g].astype(float)


def _decimate_page(filt, a, anchor, fs_in=None):
    """decimate the padded segment 256 -> 128 Hz (zero-phase, scipy.signal.decimate) and cut the page
    anchor -10 .. +20 s out of it; `a` is the clock time (s in the file) of filt[:, 0]."""
    fs_in = P.FS if fs_in is None else fs_in
    fs = fs_in // DEC
    dec = decimate(np.asarray(filt, np.float64), DEC, zero_phase=True, axis=1)
    k0 = int(round((max(a, anchor - PRE) - a) * fs))
    k1 = int(round((min(a + dec.shape[1] / fs, anchor + POST) - a) * fs))
    return dec[:, k0:k1].astype(np.float16), float(a + k0 / fs), int(fs)


def page(subj, setname, fname, anchor):
    """the real pipeline-filtered EEG of the page anchor -10 .. +20 s, uV, decimated to 128 Hz
    (v9_eeg_evidence.read_window + the display path of export_v8_data.py)."""
    out = V9V.read_window(subj, setname, fname, anchor - PRE - PAD, anchor + POST + PAD)
    if out is None:
        raise SystemExit(f"STOP: read_window failed for {subj}/{fname} around {anchor:g} s")
    filt, a, _b = out
    return _decimate_page(filt, a, anchor)


def _listed_first(arr, on, off):
    """export_v8_data._anchor_first: the listed event must be entry 0, since draw_eeg_figures.anchor()
    reads time 0 off ann[0] else loc[0] else det[0]."""
    arr = np.asarray(arr, dtype=float).reshape(-1, 2)
    if not len(arr):
        return arr
    eq = (np.abs(arr[:, 0] - on) <= TOL) & (np.abs(arr[:, 1] - off) <= TOL)
    if not eq.any():
        return arr
    i = int(np.argmax(eq))
    return arr if i == 0 else arr[[i] + [j for j in range(len(arr)) if j != i]]


def save(key, d):
    OUT.mkdir(parents=True, exist_ok=True)
    p = OUT / f"{key}.npz"
    np.savez(p, **d)
    sz = p.stat().st_size
    if sz > 3 * 1024 * 1024:
        raise SystemExit(f"STOP: panel {key}.npz is {sz} bytes, over the 3 MB gate")
    print(f"  wrote {p} ({sz / 1024:.0f} KB): {str(d['title'])}", flush=True)
    return p


def build(key, subj, setname, fname, anchor, ann, title, extra=None):
    """the common body: the page EEG plus the file's own score series, events and threshold."""
    ctx, res = V9V.ctx_and_res_G(subj, setname)
    f = V9V.file_index(ctx, fname)
    if f is None:
        raise SystemExit(f"STOP [{key}]: {fname} is not a file of {subj}'s own context")
    eeg, eeg_t0, fs = page(subj, setname, fname, anchor)
    st, sc, scsm = score_series(subj, setname, ctx, res, f, anchor)
    d = dict(eeg=eeg, fs=fs, eeg_t0=eeg_t0, ch=np.array(CH), score_t=st, score=sc, score_sm=scsm,
             thr=float(res["thr"]), thr_heldout=float(np.nan),
             ann=np.asarray(ann, float).reshape(-1, 2),
             det=np.asarray(res["det"].get(f, []), float).reshape(-1, 2),
             loc=np.asarray(res["loc"].get(f, []), float).reshape(-1, 2), title=title)
    d.update(extra or {})
    return d, ctx, res, f


# ----------------------------------------------------------------------------- f16a: missed test seizure
def panel_f16a():
    pick, missed = V9F.pick_missed_test()
    subj, fname = str(pick.subject), str(pick.file)
    on, off = float(pick.onset_s), float(pick.onset_s) + float(pick.duration_s)
    print(f"  rule (FIGURE_INDEX item 2, v9_final_figs.pick_missed_test): amplitude ratio closest to "
          f"the median over the {len(missed)} missed CHB-MIT-test seizures (median "
          f"{missed.amp_ratio.median():.4f}); pick {subj}/{fname} {on:g} s, {off - on:g} s, amp_ratio "
          f"{float(pick.amp_ratio):.4f}", flush=True)
    if (subj, fname, on, off - on) != ("chb06", "chb06_18.edf", 7796.0, 16.0):
        raise SystemExit(f"STOP [f16a]: the rule gives {subj}/{fname} {on:g} s / {off - on:g} s, not the "
                         f"listed chb06/chb06_18.edf 7796 s / 16 s. Nothing written.")
    ctx, res = V9V.ctx_and_res_G(subj, "chb-test")
    f = V9V.file_index(ctx, fname)
    gate("f16a", "annotated seizure", on, off, P3L.refs_of(ctx).get(f, []), fname)
    gate_missed("f16a", on, off, res["loc"].get(f, []), fname)
    d, *_ = build("f16a", subj, "chb-test", fname, on, [[on, off]], f"{subj}: missed seizure")
    return save("f16a", d)


# ----------------------------------------------------------------------------- f17b: false alarm
def panel_f17b():
    pick, patient, counts = V9F.pick_false_alarm()
    subj, fname = str(pick.subject), str(pick.file)
    on, off = float(pick.onset_s), float(pick.offset_s)
    print(f"  rule (FIGURE_INDEX item 3, v9_final_figs.pick_false_alarm): median-FP patient over the "
          f"{len(counts)} test patients (counts {counts.to_dict()}, median {counts.median():g}) = "
          f"{patient}; its highest-peak false alarm = {fname} {on:g}-{off:g} s, peak score "
          f"{float(pick.peak_score):.4f}", flush=True)
    if (subj, fname, on, off - on) != ("chb14", "chb14_29.edf", 1476.0, 32.0):
        raise SystemExit(f"STOP [f17b]: the rule gives {subj}/{fname} {on:g} s / {off - on:g} s, not the "
                         f"listed chb14/chb14_29.edf 1476 s / 32 s. Nothing written.")
    ctx, res = V9V.ctx_and_res_G(subj, "chb-test")
    f = V9V.file_index(ctx, fname)
    gate("f17b", "localized event", on, off, res["loc"].get(f, []), fname)
    refs_f = P3L.refs_of(ctx).get(f, [])
    if refs_f:
        raise SystemExit(f"STOP [f17b]: {fname} carries annotated seizures {refs_f}; a false-alarm "
                         f"panel's `ann` must be empty. Nothing written.")
    d, *_ = build("f17b", subj, "chb-test", fname, on, np.zeros((0, 2)), f"{subj}: false alarm")
    d["det"] = _listed_first(d["det"], on, off)
    d["loc"] = _listed_first(d["loc"], on, off)
    return save("f17b", d)


# ----------------------------------------------------------------------------- f10a: chb24 detection
def panel_f10a():
    """the rule and the gate of Defense/slides/gen/d9c/d9c_eeg_figs.py::chb24 (16 annotated seizures,
    14 detected, seed 42): the detection whose onset error is closest to the median onset error."""
    ctx, res = V9V.ctx_and_res_G("chb24", "chb24")
    refs = P3L.refs_of(ctx)
    D = pd.DataFrame([dict(file_idx=int(f), file=str(ctx["z"]["files"][int(f)]), onset_s=a, offset_s=b,
                           loc_on=h0, loc_off=h1, onset_err=h0 - a)
                      for f, a, b, h0, h1 in E18.match_errors(refs, res["loc"])])
    n_ref = sum(len(v) for v in refs.values())
    if not 13 <= len(D) <= 16 or n_ref != 16:
        raise SystemExit(f"STOP [f10a]: chb24 counts differ from the report ({n_ref} annotated seizures, "
                         f"{len(D)} detected; the report says 16 and 14) -- nothing written.")
    med = D.onset_err.median()
    pick = D.iloc[(D.onset_err - med).abs().values.argmin()]
    fname = str(pick.file)
    on, off = float(pick.onset_s), float(pick.offset_s)
    lon, loff = float(pick.loc_on), float(pick.loc_off)
    print(f"  rule (d9c_eeg_figs.chb24): {n_ref} annotated seizures, {len(D)} matched detections, onset "
          f"error closest to the median ({med:g} s): {fname} {on:g}-{off:g} s, localized {lon:g}-{loff:g} "
          f"s, onset error {float(pick.onset_err):g} s", flush=True)
    f = int(pick.file_idx)
    gate("f10a", "annotated seizure", on, off, refs.get(f, []), fname)
    gate("f10a", "localized event", lon, loff, res["loc"].get(f, []), fname)
    d, *_ = build("f10a", "chb24", "chb24", fname, on, [[on, off]], "chb24: detected (unseen patient)")
    d["det"] = _listed_first(d["det"], lon, loff)
    d["loc"] = _listed_first(d["loc"], lon, loff)
    return save("f10a", d)


# ----------------------------------------------------------------------------- f10b: Siena detection
def panel_f10b():
    det_pick, _miss, D, _mt = V9F.pick_siena_detected_missed()
    subj, fname = str(det_pick.subject), str(det_pick.file)
    on, off = float(det_pick.onset_s), float(det_pick.offset_s)
    lon, loff = float(det_pick.loc_on), float(det_pick.loc_off)
    print(f"  rule (FIGURE_INDEX item 4a, v9_final_figs.pick_siena_detected_missed): onset error "
          f"closest to the median over the {len(D)} Siena true detections (median "
          f"{D.onset_err.median():g} s): {subj}/{fname} {on:g}-{off:g} s, localized {lon:g}-{loff:g} s, "
          f"onset error {float(det_pick.onset_err):g} s", flush=True)
    if (subj, fname, on, off - on, lon, loff) != ("PN09", "PN09-2.edf", 7124.0, 64.0, 7144.0, 7196.0):
        raise SystemExit(f"STOP [f10b]: the rule gives {subj}/{fname} {on:g} s / {off - on:g} s, "
                         f"localized {lon:g}-{loff:g} s, not the listed PN09/PN09-2.edf 7124 s / 64 s, "
                         f"localized 7144-7196 s. Nothing written.")
    ctx, res = V9V.ctx_and_res_G(subj, "siena")
    f = V9V.file_index(ctx, fname)
    gate("f10b", "annotated seizure", on, off, P3L.refs_of(ctx).get(f, []), fname)
    gate("f10b", "localized event", lon, loff, res["loc"].get(f, []), fname)
    d, *_ = build("f10b", subj, "siena", fname, on, [[on, off]], f"{subj} (Siena): detected")
    d["det"] = _listed_first(d["det"], lon, loff)
    d["loc"] = _listed_first(d["loc"], lon, loff)
    return save("f10b", d)


# ----------------------------------------------------------------------------- f12a / f12b: channel ranking
def _focal_picks():
    """the two picks of Defense/slides/figs/eeg_evidence/part6/selection.csv, from their own rule
    (v9_eeg_evidence.part6): the highest and lowest channel-ranking AUROC among the focal seizures."""
    PPS = pd.read_csv(PERSEIZ)
    return PPS.loc[PPS.AUROC.idxmax()], PPS.loc[PPS.AUROC.idxmin()], len(PPS)


def _channel_masks(subj, seiz_idx):
    """ch_mark = the blind annotation's own channels (Channel_label_approved.md, read through
    v9_eeg_evidence._parse_channel_labels); ch_top = the SAME number of channels ranked highest by the
    model's channel-level latent anomaly (attribution_scores.csv, seed 42, agg p95 -- the construction
    behind the part6 figure's own heat column)."""
    labels = V9V._parse_channel_labels()
    ann_ch = labels.get(subj, {}).get(seiz_idx, [])
    marked = set(CH) if ann_ch == "diffuse" else set(ann_ch)
    unknown = marked - set(CH)
    if unknown:
        raise SystemExit(f"STOP: the annotation of {subj} seizure {seiz_idx} names unknown channels "
                         f"{sorted(unknown)}")
    if not marked:
        raise SystemExit(f"STOP: no channel annotation found for {subj} seizure {seiz_idx}")
    ch_mark = np.array([c in marked for c in CH], bool)
    S = pd.read_csv(CHSCORES)
    S = S[(S.seed == 42) & (S["agg"] == "p95") & (S.subject == subj) & (S.seizure_idx == seiz_idx)]
    if len(S) != len(CH):
        raise SystemExit(f"STOP: {len(S)} channel scores for {subj} seizure {seiz_idx}, expected "
                         f"{len(CH)} (seed 42, agg p95)")
    sc = np.array([float(S[S.ch_name == c].score.iloc[0]) for c in CH])
    k = int(ch_mark.sum())
    top = np.argsort(-sc, kind="stable")[:k]
    ch_top = np.zeros(len(CH), bool)
    ch_top[top] = True
    print(f"  {subj} seizure {seiz_idx}: annotated {k} channel(s) "
          f"{[c for c, m in zip(CH, ch_mark) if m]}; the model's own top {k} "
          f"{[CH[i] for i in top]} ({int((ch_mark & ch_top).sum())} shared)", flush=True)
    return ch_mark, ch_top


def _panel_focal(key, pick, kind, expect):
    B = pd.read_csv(BLOCKS)
    subj, idx = str(pick.subject), int(pick.seizure_idx)
    b = B[(B.subject == subj) & (B.seizure_idx == idx)]
    if not len(b):
        raise SystemExit(f"STOP [{key}]: {subj} seizure {idx} is not in {BLOCKS.name}")
    b = b.iloc[0]
    fname, on, off = str(b.edf_file), float(b.onset_s), float(b.offset_s)
    print(f"  rule (part6/selection.csv): {kind} channel-ranking AUROC among the focal test seizures = "
          f"{subj} seizure {idx} (AUROC {float(pick.AUROC):.4f}) -> {fname} {on:g}-{off:g} s", flush=True)
    if (subj, idx, fname, on, off) != expect:
        raise SystemExit(f"STOP [{key}]: the rule gives {subj} seizure {idx} ({fname} {on:g}-{off:g} s), "
                         f"not the listed {expect}. Nothing written.")
    ctx, _res = V9V.ctx_and_res_G(subj, "chb-test")
    f = V9V.file_index(ctx, fname)
    gate(key, "annotated seizure", on, off, P3L.refs_of(ctx).get(f, []), fname)
    ch_mark, ch_top = _channel_masks(subj, idx)
    d, *_ = build(key, subj, "chb-test", fname, on, [[on, off]],
                  f"{subj}: channel ranking, {kind} AUROC",
                  extra=dict(ch_mark=ch_mark, ch_top=ch_top))
    return save(key, d)


def panel_f12a():
    best, _worst, n = _focal_picks()
    print(f"  ({n} focal test seizures with an AUROC)", flush=True)
    return _panel_focal("f12a", best, "highest", ("chb15", 2, "chb15_15.edf", 1591.0, 1748.0))


def panel_f12b():
    _best, worst, n = _focal_picks()
    print(f"  ({n} focal test seizures with an AUROC)", flush=True)
    return _panel_focal("f12b", worst, "lowest", ("chb16", 7, "chb16_17.edf", 3290.0, 3298.0))


# ----------------------------------------------------------------------------- f18: ASR before / after
def panel_f18():
    """item 8a's own pick and its own before/after traces: v9_x6_asr.py --item8 sorts the cutoff=20
    seizure rows by share_seizure and takes iloc[n // 2]; its traces come from --extract-trace
    (whole_file_filtered + run_asr(cutoff=20), asrpy 0.0.8, per-file calibration). aggregate() is not
    called -- it would rewrite the committed results/v9_x6/*.csv -- so the committed seizures.csv is
    read and the same rule applied to it."""
    import v9_x6_asr as X6
    SZ = pd.read_csv(X6_SEIZ)
    s20 = SZ[SZ.cutoff == 20].dropna(subset=["share_seizure"]).sort_values("share_seizure")
    if not len(s20):
        raise SystemExit("STOP [f18]: no cutoff=20 seizure rows in results/v9_x6/seizures.csv")
    r = s20.iloc[len(s20) // 2]
    subj, fname = str(r.subject), str(r.file)
    on, off = float(r.onset_s), float(r.offset_s)
    print(f"  rule (FIGURE_INDEX item 8a, v9_x6_asr.item8_median_max): the median share of power "
          f"removed at cutoff 20 over the {len(s20)} seizure rows (median "
          f"{s20.share_seizure.median():+.4f}); pick {subj}/{fname} {on:g} s, {off - on:g} s, share "
          f"{float(r.share_seizure):+.4f}", flush=True)
    if (subj, fname, on, off - on) != ("chb15", "chb15_40.edf", 3362.0, 63.0):
        raise SystemExit(f"STOP [f18]: the rule gives {subj}/{fname} {on:g} s / {off - on:g} s, not the "
                         f"listed chb15/chb15_40.edf 3362 s / 63 s. Nothing written.")
    ctx, res = V9V.ctx_and_res_G(subj, "chb-test")
    f = V9V.file_index(ctx, fname)
    gate("f18", "annotated seizure", on, off, P3L.refs_of(ctx).get(f, []), fname)

    tmp = X6.PARTS / "_trace_cache"
    tmp.mkdir(parents=True, exist_ok=True)
    cached = tmp / f"{subj}__{fname.replace('.edf', '')}__c20_trace.npz"
    print(f"  ASR traces: {'cached' if cached.exists() else 'running --extract-trace (cutoff 20)'} "
          f"-> {cached.name}", flush=True)
    X_raw, X_clean, n_total = X6._get_trace(subj, fname, 20, {}, tmp)
    lo = max(0.0, on - PRE - PAD)
    hi = min(n_total / P.FS, on + POST + PAD)
    a0, a1 = int(round(lo * P.FS)), int(round(hi * P.FS))
    eeg, eeg_t0, fs = _decimate_page(X_raw[:, a0:a1] * 1e6, lo, on)
    eeg_after, t0b, _fs = _decimate_page(X_clean[:, a0:a1] * 1e6, lo, on)
    if eeg.shape != eeg_after.shape or abs(t0b - eeg_t0) > 1e-9:
        raise SystemExit(f"STOP [f18]: the before/after pages differ ({eeg.shape} at {eeg_t0} vs "
                         f"{eeg_after.shape} at {t0b})")
    st, sc, scsm = score_series(subj, "chb-test", ctx, res, f, on)
    d = dict(eeg=eeg, eeg_after=eeg_after, fs=fs, eeg_t0=eeg_t0, ch=np.array(CH), score_t=st, score=sc,
             score_sm=scsm, thr=float(res["thr"]), thr_heldout=float(np.nan),
             ann=np.array([[on, off]], float),
             det=np.asarray(res["det"].get(f, []), float).reshape(-1, 2),
             loc=np.asarray(res["loc"].get(f, []), float).reshape(-1, 2),
             title=f"{subj}: before / after ASR (cutoff 20)")
    return save("f18", d)


# ----------------------------------------------------------------------------- main
PANELS = dict(f16a=panel_f16a, f17b=panel_f17b, f10a=panel_f10a, f10b=panel_f10b, f12a=panel_f12a,
              f12b=panel_f12b, f18=panel_f18)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--only", nargs="+", choices=sorted(PANELS), default=None)
    a = ap.parse_args()
    keys = a.only or list(PANELS)
    t_all = time.time()
    times = {}
    for k in keys:
        t0 = time.time()
        print(f"\n=== panel {k} ===", flush=True)
        PANELS[k]()
        times[k] = time.time() - t0
        print(f"  panel {k} done in {times[k]:.0f}s", flush=True)
    print(f"\nexport OK: {len(keys)} panel(s) -> {OUT}", flush=True)
    for k, v in times.items():
        print(f"  {k}: {v:.0f}s", flush=True)
    print(f"total {time.time() - t_all:.0f}s", flush=True)


if __name__ == "__main__":
    main()
