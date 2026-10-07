#!/usr/bin/env python
"""
e22_test_oneshot.py -- stage P2, the single disclosed test look (#6 in PERF_PHASE_RECORD section 3).
Written 2026-10-07 BEFORE the freeze and before any P2 number on test exists.

FROZEN SYSTEM (record 6.6; nothing here is selected on test):
  GAE v2 clean, seeds 42, 1, 2, 3. Per patient, label-free: per-channel LedoitWolf distance of the
  node latent; per-channel robust-z; order statistics 6, 9, 12 of 18 and the channel mean; each minus
  its centred +-15 min running median inside each file; each -> patient percentile; equal mean = the
  ensemble anomaly score. Detection D1: per-file centred moving average of 5 windows, threshold = the
  patient's top 0.5 % of time, merge 90 s. Localization: kernel CPD with exactly 2 change points over
  the event +- 15 windows (--localizer kernel1d: on the scalar; multi: on the 18-channel trajectory,
  only if E20a replaced E18 before the freeze).
REPORTED (no gate; reported as is):
  * per seed and 4-seed mean +- SD; HEADLINE = seed 42. Pooled and official subject-mean
    sensitivity, precision = tp/(tp+fp), F1 = 2tp/(2tp+fp+fn) from the scorer's counts, FP/day;
    for the detector events and after the localizer;
  * onset / offset |error| (median, IQR, signed bias, n) on matched seizures: detector boundaries,
    localizer, no-CPD control 1 (first/last supra-threshold window), control 2 (contiguous run);
  * short seizures (< 20 s) caught (E1 overlap rule), detector and after the localizer;
  * reference E (the P1 frozen system, E9 code path and E9 cache) on the same patients.
PRE-REGISTERED EXPECTATION (record 6.6, 6.2 item 6): FA/day about 1.2 x the non-test 19.6 (~ 23.5);
sensitivity at most a moderate improvement over E9 (seed 42: 3/76). No tuning after this look; any
later change is a new, disclosed look.
REPRODUCTION GATES (all must hold or the script stops before reading any test label):
  R1 (--repro-only, non-test chb01) the evaluate() path used for test reproduces E17b's detector
     tp/fp at cell 5/0.005 (results/e17b_latent_family/grid_per_subject.csv) and the post-localizer
     tp/fp of the E18 / E20a run (results/e18_cpd_localizer/detection_<arm>.csv), every seed;
  R2 E on test reproduces E9's per-subject tp/fp for every clean seed (results/e9_test_oneshot/
     per_subject.csv).
GUARD: refuses test subjects unless --confirm-look-6 and the git tag p2-frozen exists; records the
sha256 of this script, p2_scalars.py, e18_cpd_localizer.py and e17b_latent_family.py in the SUMMARY.
Run:  python src/e22_test_oneshot.py --repro-only --localizer kernel1d        (non-test only, ~1 min)
      python src/e22_test_oneshot.py --confirm-look-6 --localizer kernel1d    (estimated 5-15 min)
"""
import argparse
import hashlib
import subprocess
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e17b_latent_family as F17       # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402

TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
DATA = ROOT / "data" / "testset_v2"
DUMP = ROOT / "results" / "p2_test"
E9DIR = ROOT / "results" / "e9_test_oneshot"
OUT = ROOT / "results" / "e22_test_oneshot"
TAGS = ["clean_seed42", "clean_seed1", "clean_seed2", "clean_seed3"]
CELL, MARGIN, WIN = (5, 0.005), 15, 4


def sha(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def test_context(s):
    if s not in TEST:
        raise SystemExit("test_context is for test subjects only")
    z = np.load(DATA / f"{s}.npz", allow_pickle=True)
    dmp = np.load(DUMP / f"{s}.npz")
    ok = ~z["is_signal_loss"].astype(bool); idx = dmp["idx"]
    if not np.array_equal(idx, np.flatnonzero(ok)):
        raise SystemExit(f"{s}: dump index differs from the test set")
    ict = z["is_ictal"].astype(bool); fidx = z["file_idx"].astype(int)
    fl5 = z["is_flag5sd"].astype(bool) if "is_flag5sd" in z.files else np.zeros(len(ict), bool)
    return dict(s=s, z=z, idx=idx, D={t: dmp[f"{t}_d"].astype(np.float64) for t in TAGS},
                Z={t: None for t in TAGS}, c8=dmp, p2=dmp, n=len(ict), ok=ok, fidx=fidx, wf=fidx[idx],
                ict=ict, ict_ok=ict & ok, fl5=fl5, nonict=~ict & ~z["is_buffer"].astype(bool) & ok,
                nh=float((~ict & ok).sum()) * WIN / 3600)


def final_scalar(ctx, tag):
    raw = [PS._full(ctx, F17.member(ctx["D"][tag], ctx["wf"], kk)) for kk in F17.MEMBERS.values()]
    return np.mean([PS.pct(v, ctx["ok"]) for v in raw], axis=0)


def evaluate(ctx, tag, localizer):
    """the one code path used for test and for the non-test reproduction."""
    x = final_scalar(ctx, tag)
    det = PS.d1_events(ctx, x, CELL[0], CELL[1])
    thr = np.nanquantile(PS.smoothed(ctx, x, CELL[0]), 1 - CELL[1])
    XM = E18.channel_trajectory(ctx, tag) if localizer == "multi" else None

    def loc_one(f, aw, bw):
        m = np.flatnonzero(ctx["fidx"] == f)
        if localizer == "multi":
            return E18.cpd_event_multi(XM[m], x[m], ctx["ok"][m], aw, bw, MARGIN)
        return E18.cpd_event(x[m], ctx["ok"][m], aw, bw, MARGIN)

    loc = {}
    for f, evs in det.items():
        loc[f] = PS.merge([tuple(v * WIN for v in loc_one(f, e0 // WIN, e1 // WIN)[:2]) for e0, e1 in evs])
    out = {}
    for name, ev in (("detector", det), ("localized", loc)):
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(PS.short_refs(ctx), ev)
        out[name] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=k, short_n=ns)
    refs = {f: [(i * WIN, j * WIN) for i, j in PS._runs(ctx["ict"][np.flatnonzero(ctx["fidx"] == f)])]
            for f in np.unique(ctx["fidx"])}
    errs = []
    for f, ra, rb, h0, h1 in E18.match_errors(refs, det):
        m = np.flatnonzero(ctx["fidx"] == f)
        a_w, b_w, used = loc_one(f, h0 // WIN, h1 // WIN)
        t_a, t_b = E18.thr_event(x[m], ctx["ok"][m], h0 // WIN, h1 // WIN, MARGIN, thr)
        r_a, r_b = E18.run_event(x[m], ctx["ok"][m], h0 // WIN, h1 // WIN, MARGIN, thr)
        errs.append(dict(ref_dur=rb - ra, ev_dur=h1 - h0, used=used, det_on=h0 - ra, det_off=h1 - rb,
                         loc_on=a_w * WIN - ra, loc_off=b_w * WIN - rb, c1_on=t_a * WIN - ra,
                         c1_off=t_b * WIN - rb, c2_on=r_a * WIN - ra, c2_off=r_b * WIN - rb))
    return out, errs


def metrics(df):
    """pooled and subject-mean metrics from scorer counts; df: one row per subject."""
    tp, fp, nr, h = df.tp.sum(), df.fp.sum(), df.n_ref.sum(), df.nonict_h.sum()
    sm = df.assign(sens=df.tp / df.n_ref, prec=df.tp / (df.tp + df.fp).where(df.tp + df.fp > 0),
                   f1=2 * df.tp / (2 * df.tp + df.fp + (df.n_ref - df.tp)), fa=df.fp / df.nonict_h * 24)
    return dict(tp=tp, n_ref=nr, fp=fp, sens=tp / nr, prec=tp / (tp + fp) if tp + fp else np.nan,
                f1=2 * tp / (2 * tp + fp + (nr - tp)), fa_day=fp / h * 24, s_sens=sm.sens.mean(),
                s_prec=sm.prec.mean(), s_f1=sm.f1.mean(), s_fa=sm.fa.mean(), short=f"{df.short_tp.sum()}/{df.short_n.sum()}")


def repro_nontest(localizer):
    ctx = PS.subject_context("chb01")
    g = pd.read_csv(ROOT / "results" / "e17b_latent_family" / "grid_per_subject.csv")
    arm = "family_Ce_fine_raw_m15" + ("_multi" if localizer == "multi" else "")
    dd = pd.read_csv(ROOT / "results" / "e18_cpd_localizer" / f"detection_{arm}.csv")
    for tag in TAGS:
        out, _ = evaluate(ctx, tag, localizer)
        r = g[(g.subject == "chb01") & (g.score == f"{tag}|E17b") & (g.smooth == CELL[0]) & (g.top == CELL[1])].iloc[0]
        c = dd[(dd.subject == "chb01") & (dd.seed == tag) & (dd.arm == "cpd")].iloc[0]
        got = (out["detector"]["tp"], out["detector"]["fp"], out["localized"]["tp"], out["localized"]["fp"])
        want = (int(r.tp), int(r.fp), int(c.tp), int(c.fp))
        if got != want:
            raise SystemExit(f"STOP R1 chb01 {tag}: evaluate() gives {got}, stored {want}")
    print("R1 OK: the test code path reproduces E17b (detector) and the localizer run on chb01, 4 seeds")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--localizer", required=True, choices=["kernel1d", "multi"])
    ap.add_argument("--repro-only", action="store_true")
    ap.add_argument("--confirm-look-6", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    repro_nontest(a.localizer)
    if a.repro_only:
        return
    if not a.confirm_look_6:
        raise SystemExit("refusing to touch test labels without --confirm-look-6")
    if subprocess.run(["git", "rev-parse", "-q", "--verify", "refs/tags/p2-frozen"], capture_output=True).returncode:
        raise SystemExit("refusing: git tag p2-frozen does not exist")
    import e9_test_oneshot as E9
    e9 = pd.read_csv(E9DIR / "per_subject.csv")
    OUT.mkdir(parents=True, exist_ok=True)
    rows, erows, erow = [], [], []
    for s in TEST:
        ctx = test_context(s)
        for tag in TAGS:                                   # R2: reference E reproduces E9
            q = np.load(E9DIR / "scores" / f"{s}__{tag}.npz")
            from sklearn.covariance import LedoitWolf
            okk = ctx["ok"]
            e = np.mean([E16.rz(PS._full(ctx, q["recon"].astype(float)), okk),
                         E16.rz(PS._full(ctx, LedoitWolf().fit(q["lat"]).mahalanobis(q["lat"])), okk),
                         E16.rz(PS._full(ctx, ctx["z"]["zgamma_raw"][ctx["idx"]].astype(float)), okk)], axis=0)
            r = E9.detect_and_score(ctx["z"], e, 0.02)
            w = e9[(e9.subject == s) & (e9.model == tag)].iloc[0]
            if (int(r["tp"]), int(r["fp"])) != (int(w.tp), int(w.fp)):
                raise SystemExit(f"STOP R2 {s} {tag}: E gives {(int(r['tp']), int(r['fp']))}, E9 stored {(int(w.tp), int(w.fp))}")
            erow.append(dict(subject=s, seed=tag, tp=int(r["tp"]), fp=int(r["fp"]), n_ref=int(r["n_ref"]),
                             nonict_h=r["nonict_h"], short_tp=r["tp_short"], short_n=r["n_short"]))
        for tag in TAGS:
            out, errs = evaluate(ctx, tag, a.localizer)
            for k, v in out.items():
                rows.append(dict(subject=s, seed=tag, stage=k, **v))
            erows += [dict(subject=s, seed=tag, **e_) for e_ in errs]
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    R, Er, Ee = pd.DataFrame(rows), pd.DataFrame(erows), pd.DataFrame(erow)
    R.to_csv(OUT / "per_subject_seed.csv", index=False); Er.to_csv(OUT / "errors.csv", index=False)
    Ee.to_csv(OUT / "reference_E.csv", index=False)

    lines = ["# E22 -- single test look (#6) of the P2 frozen system, 8 test patients, 4 seeds\n",
             f"Localizer: {a.localizer}. Reproduction gates R1 (non-test path) and R2 (E = E9) passed.",
             "Hashes (sha256/16, LF): " + ", ".join(f"{n} {sha(ROOT / 'src' / n)}" for n in
                                                    ("e22_test_oneshot.py", "p2_scalars.py", "e18_cpd_localizer.py",
                                                     "e17b_latent_family.py")) + "\n",
             "## Per seed (pooled | subject-mean)\n", "```",
             "system/stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short"]
    summ = []
    for label, df in (("final detector", R[R.stage == "detector"]), ("final localized", R[R.stage == "localized"]),
                      ("E (P1 frozen)", Ee)):
        for tag in TAGS:
            m = metrics(df[df.seed == tag]); summ.append(dict(system=label, seed=tag, **m))
            lines.append(f"{label:18s} {tag:13s} {m['tp']:3.0f}/{m['n_ref']:3.0f} {m['fp']:4.0f}  {m['sens']:.3f}  "
                         f"{m['prec']:.3f}  {m['f1']:.3f}  {m['fa_day']:6.2f} | {m['s_sens']:.3f}  {m['s_prec']:.3f}  "
                         f"{m['s_f1']:.3f} {m['s_fa']:6.2f} | {m['short']}")
    lines.append("```")
    S = pd.DataFrame(summ); S.to_csv(OUT / "summary_per_seed.csv", index=False)
    lines += ["\n## Headline (seed 42) and 4-seed mean +- SD\n", "```"]
    for label, g in S.groupby("system", sort=False):
        h = g[g.seed == "clean_seed42"].iloc[0]
        lines.append(f"{label:18s} seed 42: sens {h.sens:.3f} @ {h.fa_day:.2f} FP/day, prec {h.prec:.3f}, F1 {h.f1:.3f} | "
                     f"4 seeds: sens {g.sens.mean():.3f} +- {g.sens.std(ddof=1):.3f}, FP/day {g.fa_day.mean():.2f} +- "
                     f"{g.fa_day.std(ddof=1):.2f}, subject-mean sens {g.s_sens.mean():.3f} +- {g.s_sens.std(ddof=1):.3f}")
    lines.append("```")

    def st(col, df):
        v = df[col].abs()
        return f"median {v.median():5.1f} s IQR [{v.quantile(.25):.1f}, {v.quantile(.75):.1f}] bias {df[col].median():+5.1f}"
    lines += [f"\n## Onset / offset |error| on matched seizures (n = {len(Er)} seizure-seed pairs; "
              f"{Er.groupby('seed').size().mean() if len(Er) else 0:.1f} per seed)\n", "```"]
    if len(Er):
        for lab, c in (("detector", "det"), ("localizer", "loc"), ("control 1", "c1"), ("control 2", "c2")):
            lines.append(f"{lab:10s} onset {st(c + '_on', Er)} | offset {st(c + '_off', Er)}")
    lines += ["```", "\n## Per subject (seed 42, after the localizer | E)\n", "```"]
    for s in TEST:
        f_ = R[(R.subject == s) & (R.seed == "clean_seed42") & (R.stage == "localized")].iloc[0]
        e_ = Ee[(Ee.subject == s) & (Ee.seed == "clean_seed42")].iloc[0]
        lines.append(f"{s}  {f_.tp}/{f_.n_ref} FP {f_.fp} ({f_.fp / f_.nonict_h * 24:5.1f}/day) | "
                     f"{e_.tp}/{e_.n_ref} FP {e_.fp} ({e_.fp / e_.nonict_h * 24:5.1f}/day)")
    lines += ["```", "\nPre-registered expectation: FP/day ~ 23.5; sensitivity at most a moderate improvement over E9.",
              f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
