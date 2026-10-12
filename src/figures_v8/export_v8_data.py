#!/usr/bin/env python
"""
export_v8_data.py -- Claude Code export for Figures 12 (per-seizure detection) and 14 (gallery panels),
docs/prompts/CC_FIGURES_V8.md. FROZEN SYSTEM ONLY (tag p3-frozen): builds the final system (balanced
point, results/p3c_freeze/freeze.json) and the held-out evaluation (floor = cap = 0.005) with the same
construction as src/figures_v6/fig_example_chb03.py export() -- e22_test_oneshot.test_context/
final_scalar, p2_scalars.smoothed/d1_events/score, p3_levers.q_of/member_mean_z/refs_of/localize. For
Siena (panel e) the frozen external path is used instead: x1_external.build_subject/model_outputs/
make_ctx, label-free statistics, 50 Hz notch. Writes data only; figures never recompute (rule 13).

perseizure  one row per annotated test seizure x seed (76 x 4): results/figures_v8_data/perseizure_final.csv.
            GATED against results/e23_test_look7/per_subject_seed.csv (point balanced, stage localized,
            tp/fp) and results/e22_test_oneshot/per_subject_seed.csv (stage localized, tp/fp). The
            per-seizure hit flag is first the overlap rule of p2_scalars.caught (pre 30 s / post 60 s);
            for any subject/seed where the summed hits disagree with the scorer's tp, every reference of
            that subject/seed is re-scored one at a time with the exact scorer (p2_scalars.score on a
            context whose is_ictal mask holds only that one reference).
gallery     one .npz per panel a-d always, e only if --siena points at a directory holding PN10's EDF
            files: results/figures_v8_data/gallery/. Requires perseizure_final.csv (panels a/b/c are
            picked from it). Seed 42, final system (balanced point).

Run:  python src/figures_v8/export_v8_data.py perseizure                 (estimated 10-30 min)
      python src/figures_v8/export_v8_data.py gallery --siena <dir>      (estimated 2-15 min; Siena
                                                                            needs its own 5-15 min if run)
      python src/figures_v8/export_v8_data.py perseizure --smoke          (chb03 seed 42 only, no write)
"""
import argparse
import json
import sys
import tempfile
import time
import time as _time_mod
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import decimate, filtfilt, sosfiltfilt

ROOT = Path(__file__).resolve().parents[2]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC",
          ROOT / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e22_test_oneshot as E22         # noqa: E402
import p3_levers as P3L                # noqa: E402
import preprocessing as PP             # noqa: E402

OUT = ROOT / "results" / "figures_v8_data"
GALLERY = OUT / "gallery"
FRZ = ROOT / "results" / "p3c_freeze"
TEST = list(E22.TEST)
TAGS = list(E22.TAGS)
WIN = PS.WIN
PRE, POST, PAD = 10.0, 20.0, 5.0       # EEG window: onset -10..+20 s, +-5 s edge padding for decimate
SCORE_HALF = 300.0                     # score window: +-5 min


# ----------------------------------------------------------------------------- frozen construction
def system_eval(ctx, tag, cfg, floor, cap):
    """balanced point (floor,cap = cfg['points']['balanced']) or held-out (floor=cap=0.005); the exact
    construction of src/figures_v6/fig_example_chb03.py export() (tag p3-frozen)."""
    x = E22.final_scalar(ctx, tag)
    q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), cfg["smooth"]), cfg["k"])
    top = float(np.clip(q, floor, max(cap, floor)))
    det = PS.d1_events(ctx, x, cfg["smooth"], top)
    thr = float(np.nanquantile(PS.smoothed(ctx, x, cfg["smooth"]), 1 - top))
    loc, _ = P3L.localize(ctx, x, det, thr, "cpd")
    return x, det, thr, top, loc


def overlap_hit(ev, a, b, pre=30, post=60):
    """the overlap rule of p2_scalars.caught, applied to one reference (a, b) against hypotheses ev."""
    return any(h1 >= a - pre and h0 <= b + post for h0, h1 in ev)


class _ZView:
    """ctx['z'] look-alike with is_ictal replaced -- lets p2_scalars.score grade one reference alone."""
    def __init__(self, z, ict):
        self._z, self._ict = z, ict

    def __getitem__(self, k):
        return self._ict if k == "is_ictal" else self._z[k]


def scorer_hit(ctx, per_file, f, a, b):
    """exact SzCORE verdict for one reference (f, a, b): p2_scalars.score on a context whose is_ictal
    mask holds only that reference (ground rule: 'score that file's references one at a time with the
    scorer')."""
    m = np.flatnonzero(ctx["fidx"] == f)
    ict1 = np.zeros(ctx["n"], bool)
    ict1[m[a // WIN: b // WIN]] = True
    ctx1 = dict(ctx); ctx1["z"] = _ZView(ctx["z"], ict1)
    tp, fp, nr, h = PS.score(ctx1, per_file)
    return tp >= 1


# ----------------------------------------------------------------------------- step 1: perseizure
def perseizure(smoke=False):
    t0 = time.time()
    cfg = json.load(open(FRZ / "freeze.json"))
    floor, cap = cfg["points"]["balanced"]
    e23 = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")
    e22 = pd.read_csv(ROOT / "results" / "e22_test_oneshot" / "per_subject_seed.csv")
    subjects = ["chb03"] if smoke else TEST
    tags = ["clean_seed42"] if smoke else TAGS
    rows = []
    for s in subjects:
        ctx = E22.test_context(s)
        refs = P3L.refs_of(ctx)
        fnames = ctx["z"]["files"]
        for tag in tags:
            _, _, _, _, loc_f = system_eval(ctx, tag, cfg, floor, cap)
            _, _, _, _, loc_h = system_eval(ctx, tag, cfg, 0.005, 0.005)

            got_f = PS.score(ctx, loc_f)[:2]
            w = e23[(e23.point == "balanced") & (e23.subject == s) & (e23.seed == tag) &
                    (e23.stage == "localized")].iloc[0]
            want_f = (int(w.tp), int(w.fp))
            if got_f != want_f:
                raise SystemExit(f"STOP gate (final) {s} {tag}: got {got_f} vs e23 {want_f}")

            got_h = PS.score(ctx, loc_h)[:2]
            w = e22[(e22.subject == s) & (e22.seed == tag) & (e22.stage == "localized")].iloc[0]
            want_h = (int(w.tp), int(w.fp))
            if got_h != want_h:
                raise SystemExit(f"STOP gate (held-out) {s} {tag}: got {got_h} vs e22 {want_h}")

            local = []
            for f in sorted(refs):
                for a, b in refs[f]:
                    local.append(dict(subject=s, seed=tag, file=str(fnames[f]), onset_s=a, offset_s=b,
                                      dur_s=b - a, _f=f,
                                      detected_final=int(overlap_hit(loc_f.get(f, []), a, b)),
                                      detected_heldout=int(overlap_hit(loc_h.get(f, []), a, b))))
            sum_f = sum(r["detected_final"] for r in local)
            if sum_f != got_f[0]:
                for r in local:
                    r["detected_final"] = int(scorer_hit(ctx, loc_f, r["_f"], r["onset_s"], r["offset_s"]))
                sum_f = sum(r["detected_final"] for r in local)
                if sum_f != got_f[0]:
                    raise SystemExit(f"STOP: per-reference scorer fallback still mismatches final tp "
                                     f"{s} {tag}: {sum_f} vs {got_f[0]}")
            sum_h = sum(r["detected_heldout"] for r in local)
            if sum_h != got_h[0]:
                for r in local:
                    r["detected_heldout"] = int(scorer_hit(ctx, loc_h, r["_f"], r["onset_s"], r["offset_s"]))
                sum_h = sum(r["detected_heldout"] for r in local)
                if sum_h != got_h[0]:
                    raise SystemExit(f"STOP: per-reference scorer fallback still mismatches held-out tp "
                                     f"{s} {tag}: {sum_h} vs {got_h[0]}")
            for r in local:
                r.pop("_f")
            rows += local
        print(f"{s}: done ({time.time() - t0:.0f}s)", flush=True)

    df = pd.DataFrame(rows, columns=["subject", "seed", "file", "onset_s", "offset_s", "dur_s",
                                      "detected_final", "detected_heldout"])
    if smoke:
        print(f"SMOKE OK: {len(df)} rows (no gate, no write); elapsed {time.time() - t0:.0f}s")
        return df
    for tag in TAGS:
        g = df[df.seed == tag]
        if len(g) != 76:
            raise SystemExit(f"STOP gate: {tag} has {len(g)} rows, expected 76")
    tot42 = df[df.seed == "clean_seed42"]
    got_tot = (int(tot42.detected_final.sum()), int(tot42.detected_heldout.sum()))
    if got_tot != (37, 26):
        raise SystemExit(f"STOP gate: seed-42 totals {got_tot}, expected (37, 26)")
    OUT.mkdir(parents=True, exist_ok=True)
    df.to_csv(OUT / "perseizure_final.csv", index=False)
    print(f"perseizure OK: {len(df)} rows, seed-42 totals {got_tot} -> {OUT / 'perseizure_final.csv'}; "
          f"elapsed {time.time() - t0:.0f}s")
    return df


# ----------------------------------------------------------------------------- step 2: gallery
def score_window(ctx, x, sm, f, anchor_s, half=SCORE_HALF):
    m = np.flatnonzero(ctx["fidx"] == f)
    t = np.arange(len(m)) * WIN
    sel = (t >= max(0.0, anchor_s - half)) & (t <= anchor_s + half)
    idx = m[sel]
    return t[sel].astype(float), x[idx].astype(float), sm[idx].astype(float)


def build_eeg_chb(subj, fname, anchor_s):
    """the evaluation's own filtered, z-scored EEG (continuous_eval.filter_file/zscore, thesis
    statistics), decimated 256 -> 128 Hz (scipy.signal.decimate, q=2, zero-phase), clipped to the file."""
    import continuous_eval as CE
    path = CE.DATASET_DIR / subj / fname
    filtered, n_windows = CE.filter_file(path)                       # [n_windows, 18, 1024] f32, 256 Hz
    stats = json.loads((ROOT / "data" / "processed" / f"{subj}_stats.json").read_text())
    ch_mean = np.asarray(stats["ch_mean_uV"], np.float64) * 1e-6
    ch_std = np.asarray(stats["ch_std_uV"], np.float64) * 1e-6
    file_s = n_windows * PP.WIN_SAMPLES / PP.FS
    lo = max(0.0, anchor_s - PRE - PAD)
    hi = min(file_s, anchor_s + POST + PAD)
    s0, s1 = int(round(lo * PP.FS)), int(round(hi * PP.FS))
    w0, w1 = s0 // PP.WIN_SAMPLES, -(-s1 // PP.WIN_SAMPLES)
    seg = CE.zscore(filtered[w0:w1], ch_mean, ch_std)
    sig = seg.transpose(1, 0, 2).reshape(18, -1)
    t0_seg = w0 * PP.WIN_SAMPLES / PP.FS
    i0, i1 = s0 - int(round(t0_seg * PP.FS)), s1 - int(round(t0_seg * PP.FS))
    sig = sig[:, max(i0, 0):min(i1, sig.shape[1])]
    dec = decimate(sig, 2, zero_phase=True, axis=1)                  # 128 Hz
    want_lo, want_hi = max(0.0, anchor_s - PRE), min(file_s, anchor_s + POST)
    k0, k1 = int(round((want_lo - lo) * 128)), int(round((want_hi - lo) * 128))
    eeg = dec[:, k0:k1].astype(np.float16)
    return eeg, float(lo + k0 / 128.0), 128


def build_eeg_siena(path, mu, sd, anchor_s):
    """same display path for Siena: x1_external.load_18 (referential->bipolar, resample to 256 Hz) +
    filtfilt/notch 50 Hz, z-scored with the label-free statistics, decimated to 128 Hz."""
    import x1_external as X1
    data = X1.load_18(path, "siena")
    n_samp = data.shape[1]; file_s = n_samp / PP.FS
    lo = max(0.0, anchor_s - PRE - PAD); hi = min(file_s, anchor_s + POST + PAD)
    s0, s1 = int(round(lo * PP.FS)), int(round(hi * PP.FS))
    edge = 3 * PP.FS
    p0, p1 = max(0, s0 - edge), min(n_samp, s1 + edge)
    sos, b, a = X1.filters(50.0)
    filt = filtfilt(b, a, sosfiltfilt(sos, data[:, p0:p1], axis=1), axis=1)
    seg = filt[:, s0 - p0: s0 - p0 + (s1 - s0)]
    z = (seg - mu[:, None]) / sd[:, None]
    dec = decimate(z, 2, zero_phase=True, axis=1)
    want_lo, want_hi = max(0.0, anchor_s - PRE), min(file_s, anchor_s + POST)
    k0, k1 = int(round((want_lo - lo) * 128)), int(round((want_hi - lo) * 128))
    eeg = dec[:, k0:k1].astype(np.float16)
    return eeg, float(lo + k0 / 128.0), 128


def _anchor_first(arr, onset, offset):
    """fig14_gallery.py's anchor() takes time 0 from ann[0], else loc[0], else det[0] -- when ann is
    empty (the false-alarm panel) the chosen event must be that first entry, not just any event of the
    file, so move it to the front if present."""
    if len(arr) == 0:
        return arr
    eq = np.isclose(arr[:, 0], onset) & np.isclose(arr[:, 1], offset)
    if not eq.any():
        return arr
    i = int(np.argmax(eq))
    return arr if i == 0 else arr[[i] + [j for j in range(len(arr)) if j != i]]


def make_panel(fmap, sysd_entry, fname, onset, offset, title, thr_heldout=np.nan, is_fa=False):
    ctx, x, det, thr, loc, sm = (sysd_entry[k] for k in ("ctx", "x", "det", "thr", "loc", "sm"))
    f = fmap[fname]
    t, sc, scsm = score_window(ctx, x, sm, f, onset)
    eeg, eeg_t0, fs = build_eeg_chb(sysd_entry["subj"], fname, onset)
    ann = np.zeros((0, 2)) if is_fa else np.array([[onset, offset]], dtype=float)
    det_f = _anchor_first(np.array(det.get(f, []), dtype=float).reshape(-1, 2), onset, offset)
    loc_f = _anchor_first(np.array(loc.get(f, []), dtype=float).reshape(-1, 2), onset, offset)
    return dict(eeg=eeg, fs=fs, eeg_t0=eeg_t0, ch=np.array(PP.COMMON_CHANNELS), score_t=t, score=sc,
                score_sm=scsm, thr=float(thr), thr_heldout=float(thr_heldout), ann=ann, det=det_f,
                loc=loc_f, title=title)


def save_panel(key, d):
    GALLERY.mkdir(parents=True, exist_ok=True)
    p = GALLERY / f"{key}.npz"
    np.savez(p, **d)
    sz = p.stat().st_size
    if sz > 3 * 1024 * 1024:
        raise SystemExit(f"STOP: panel {key}.npz is {sz} bytes, over the 3 MB gate")
    print(f"panel {key}: {d['title']!r} -> {p} ({sz / 1024:.0f} KB)")


def gallery(siena_dir=None):
    t0 = time.time()
    cfg = json.load(open(FRZ / "freeze.json"))
    floor, cap = cfg["points"]["balanced"]
    pf_path = OUT / "perseizure_final.csv"
    if not pf_path.exists():
        raise SystemExit(f"STOP: run `perseizure` first ({pf_path} missing)")
    PF42 = pd.read_csv(pf_path).pipe(lambda d: d[d.seed == "clean_seed42"])
    e23 = pd.read_csv(ROOT / "results" / "e23_test_look7" / "per_subject_seed.csv")

    sysd, fmaps = {}, {}
    for s in TEST:
        ctx = E22.test_context(s)
        x, det, thr, top, loc = system_eval(ctx, "clean_seed42", cfg, floor, cap)
        got = PS.score(ctx, loc)[:2]
        w = e23[(e23.point == "balanced") & (e23.subject == s) & (e23.seed == "clean_seed42") &
                (e23.stage == "localized")].iloc[0]
        want = (int(w.tp), int(w.fp))
        if got != want:
            raise SystemExit(f"STOP gate (gallery, final) {s}: got {got} vs e23 {want}")
        sm = PS.smoothed(ctx, x, cfg["smooth"])
        refs = P3L.refs_of(ctx)
        fnames = ctx["z"]["files"]
        sysd[s] = dict(subj=s, ctx=ctx, x=x, det=det, thr=thr, loc=loc, sm=sm, refs=refs, fnames=fnames)
        fmaps[s] = {str(n): i for i, n in enumerate(fnames)}
        print(f"{s}: final-system seed-42 gate OK ({time.time() - t0:.0f}s)", flush=True)

    # panel a -- chb03 first annotated seizure (file order, then onset)
    row = PF42[PF42.subject == "chb03"].iloc[0]
    save_panel("a", make_panel(fmaps["chb03"], sysd["chb03"], row.file, float(row.onset_s),
                               float(row.offset_s), "chb03: detected"))

    # panel b -- chb15 first seizure detected_final=1, detected_heldout=0
    cand = PF42[(PF42.subject == "chb15") & (PF42.detected_final == 1) & (PF42.detected_heldout == 0)]
    if not len(cand):
        raise SystemExit("STOP: no chb15 seed-42 seizure with detected_final=1, detected_heldout=0")
    row = cand.iloc[0]
    ctx15, x15 = sysd["chb15"]["ctx"], sysd["chb15"]["x"]
    thr_h = float(np.nanquantile(PS.smoothed(ctx15, x15, cfg["smooth"]), 1 - 0.005))
    save_panel("b", make_panel(fmaps["chb15"], sysd["chb15"], row.file, float(row.onset_s),
                               float(row.offset_s), "chb15: detected with the per-patient budget",
                               thr_heldout=thr_h))

    # panel c -- chb16 shortest seizure with detected_final=0 (ties: first)
    cand = PF42[(PF42.subject == "chb16") & (PF42.detected_final == 0)]
    if not len(cand):
        raise SystemExit("STOP: no chb16 seed-42 missed seizure")
    row = cand.loc[cand.dur_s.idxmin()]
    save_panel("c", make_panel(fmaps["chb16"], sysd["chb16"], row.file, float(row.onset_s),
                               float(row.offset_s), "chb16: short seizure, missed"))

    # panel d -- highest-peak false alarm, no annotated seizure within +-10 min, any test subject
    best = None
    for s in TEST:
        d = sysd[s]; ctx = d["ctx"]
        for f in sorted(d["loc"]):
            refs_f = d["refs"].get(f, [])
            for a, b in d["loc"][f]:
                if any(ra - 600 <= b and rb + 600 >= a for ra, rb in refs_f):
                    continue
                m = np.flatnonzero(ctx["fidx"] == f)
                ia, ib = int(a // WIN), int(b // WIN)
                peak = float(np.nanmax(d["sm"][m[ia:ib]])) if ib > ia else -np.inf
                if best is None or peak > best[0]:
                    best = (peak, s, f, a, b)
    if best is None:
        raise SystemExit("STOP: no qualifying false alarm found for panel d")
    _, s_fa, f_fa, a_fa, b_fa = best
    fname_fa = str(sysd[s_fa]["fnames"][f_fa])
    save_panel("d", make_panel(fmaps[s_fa], sysd[s_fa], fname_fa, float(a_fa), float(b_fa),
                               f"{s_fa}: false alarm", is_fa=True))
    print(f"panel d: peak smoothed score {best[0]:.3f} ({s_fa}, file {f_fa}, "
          f"{a_fa:.0f}-{b_fa:.0f} s)")

    siena_ok = siena_dir is not None and any(Path(siena_dir).glob("PN10/PN10*.edf"))
    if not siena_ok:
        print(f"panel e skipped: Siena EDF files not found under {siena_dir}")
    else:
        build_panel_e(Path(siena_dir), cfg, floor, cap, t0)
    print(f"gallery OK; elapsed {time.time() - t0:.0f}s")


def _mktime_time_of_day(struct):
    """Windows' mktime raises OverflowError on strptime's default 1900 date (epilepsy2bids' Siena
    annotation parser, verbatim in x1_external.py, was written for Linux/Kaggle). _substractTimeStamps
    only uses mktime's return value as HH:MM:SS seconds-of-day (then wraps a day-boundary diff mod 24h),
    so this is numerically identical and platform-independent -- scoped to this call only, never left
    patched in, and never touches anything in the frozen pipeline itself (feature/model/scoring code)."""
    return struct.tm_hour * 3600 + struct.tm_min * 60 + struct.tm_sec


def build_panel_e(siena_dir, cfg, floor, cap, t0):
    import x1_external as X1
    orig_mktime = _time_mod.mktime
    _time_mod.mktime = _mktime_time_of_day
    try:
        files, meta = X1.subject_files(str(siena_dir), "PN10")
        mu, sd = X1.labelfree_stats(files, meta["kind"], meta["notch"])
        print(f"PN10: label-free statistics done ({time.time() - t0:.0f}s)", flush=True)
        fd, tmp_path = tempfile.mkstemp(suffix=".json")
        try:
            with open(fd, "w") as fh:
                json.dump(dict(ch_mean_uV=(mu * 1e6).tolist(), ch_std_uV=(sd * 1e6).tolist()), fh)
            z, _ = X1.build_subject(str(siena_dir), "PN10", stats_mode="json", stats_json=tmp_path, procs=2)
        finally:
            Path(tmp_path).unlink(missing_ok=True)
    finally:
        _time_mod.mktime = orig_mktime
    if z is None:
        print("panel e skipped: PN10 has no file with every electrode present"); return
    print(f"PN10: features built ({time.time() - t0:.0f}s)", flush=True)
    idx, D = X1.model_outputs(z)
    ctx = X1.make_ctx(z, idx, D)
    x, det, thr, top, loc = system_eval(ctx, "clean_seed42", cfg, floor, cap)
    got = PS.score(ctx, loc)[:2]
    ext = pd.read_csv(ROOT / "results" / "x1_external" / "rows_PN10.csv")
    w = ext[(ext.point == "balanced") & (ext.seed == "clean_seed42") & (ext.stage == "localized")].iloc[0]
    want = (int(w.tp), int(w.fp))
    if got != want:
        raise SystemExit(f"STOP gate (panel e) PN10: got {got} vs rows_PN10.csv {want}")
    refs = P3L.refs_of(ctx)
    fnames = z["files"]
    hit = None
    for f in sorted(refs):
        for a, b in refs[f]:
            if overlap_hit(loc.get(f, []), a, b):
                hit = (f, a, b); break
        if hit:
            break
    if hit is None:
        raise SystemExit("STOP: no detected PN10 seizure found for panel e")
    f, a, b = hit
    sm = PS.smoothed(ctx, x, cfg["smooth"])
    t, sc, scsm = score_window(ctx, x, sm, f, a)
    path = Path(siena_dir) / "PN10" / str(fnames[f])
    eeg, eeg_t0, fs = build_eeg_siena(path, mu, sd, a)
    det_f = np.array(det.get(f, []), dtype=float).reshape(-1, 2)
    loc_f = np.array(loc.get(f, []), dtype=float).reshape(-1, 2)
    d = dict(eeg=eeg, fs=fs, eeg_t0=eeg_t0, ch=np.array(PP.COMMON_CHANNELS), score_t=t, score=sc,
             score_sm=scsm, thr=float(thr), thr_heldout=float(np.nan), ann=np.array([[a, b]], dtype=float),
             det=det_f, loc=loc_f, title="PN10 (Siena): detected")
    save_panel("e", d)


def main():
    ap = argparse.ArgumentParser()
    sp = ap.add_subparsers(dest="cmd", required=True)
    p1 = sp.add_parser("perseizure"); p1.add_argument("--smoke", action="store_true")
    p2 = sp.add_parser("gallery"); p2.add_argument("--siena", default=None)
    a = ap.parse_args()
    if a.cmd == "perseizure":
        perseizure(smoke=a.smoke)
    else:
        gallery(siena_dir=a.siena)


if __name__ == "__main__":
    main()
