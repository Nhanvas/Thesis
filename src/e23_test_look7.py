#!/usr/bin/env python
"""
e23_test_look7.py -- stage P3, look #7 at the test set (record 9.7). Rewritten 2026-10-07 for the freeze
candidate of p3c_freeze.py, BEFORE any P3 number on test. Disclosed as TEST-INFORMED (record 9.2): the
budget lever was triggered by the P3-A per-seizure anatomy (tier T-B). Look #6 stays the clean held-out
result; this look is reported beside it. No look #8.

FROZEN P3 SYSTEM = the P2 frozen scalar and detector (e22) with the per-patient budget and the localizer of
results/p3c_freeze/freeze.json:
  top-p_i = clip(q_i(k), floor, cap), q_i = label-free share of the patient's smoothed member-mean robust-z
  above k (p3_levers); two operating points declared before the look: "balanced" and, if kept on non-test
  (FA/day <= 40), "sensitivity"; localizer "cpd" (E18) or "hybrid" (L6).
REPORTED (no gate): per operating point, per seed and 4-seed mean +- SD (headline seed 42): pooled and
official subject-mean sensitivity, precision, F1, FP/day from the scorer's counts, detector and after the
localizer; review fraction (event time / recorded time); onset/offset |error| (detector, CPD, hybrid) with n;
short seizures (< 20 s by whole-window runs); per subject seed 42 next to look #6; patient-level bootstrap
(B = 10,000, 4-seed means) of P3 - look #6 (pooled, subject-mean, FP/day).
READING RULE (fixed before the look, record 9.7b): the target (pooled sensitivity >= 0.50, seed 42 headline
with the 4-seed mean) is judged on the BALANCED point only; the sensitivity point is descriptive. Every
result is reported as is: >= 0.50 = target reached; < 0.50 = target not reached, reported with the
subject-mean and the bootstrap difference to look #6; balanced FP/day > 40 is flagged as above the
acceptable false-alarm level. No look #8.
EXPECTATION written now (computed from the non-test curve and the label-free test budgets): balanced
FP/day about 35-40 (budget-weighted mean top-p 0.0076); sensitivity point about 45-50.
REPRODUCTION GATES (stop before any P3 result):
  R1 (--repro-only, non-test chb01): this path reproduces results/p3c_freeze/per_subject.csv for every point
     (detector and localizer stage), every seed;
  R2 (test): floor = cap = 0.005 with the CPD localizer reproduces look #6 (results/e22_test_oneshot/
     per_subject_seed.csv, detector and localized tp/fp) for every subject and seed.
GUARD: refuses test subjects unless --confirm-look-7 and the git tag p3-frozen exists; records sha256.
Run:  python src/e23_test_look7.py --repro-only           (non-test chb01 only, ~1 min, estimated)
      python src/e23_test_look7.py --confirm-look-7       (estimated 5-15 min, not measured)
"""
import argparse
import hashlib
import json
import subprocess
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
import p2_scalars as PS                # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402
import e22_test_oneshot as E22         # noqa: E402
import p3_levers as P3L                # noqa: E402

OUT = ROOT / "results" / "e23_test_look7"
FRZ = ROOT / "results" / "p3c_freeze"
TAGS = list(E22.TAGS)
TEST = list(E22.TEST)
NAME = {"balanced": None, "sensitivity": "S"}


def sha(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def evaluate(ctx, tag, cfg, floor, cap, localizer):
    x = E22.final_scalar(ctx, tag)
    q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), cfg["smooth"]), cfg["k"])
    top = float(np.clip(q, floor, max(cap, floor)))
    det = PS.d1_events(ctx, x, cfg["smooth"], top)
    thr = np.nanquantile(PS.smoothed(ctx, x, cfg["smooth"]), 1 - top)
    loc, pairs = {}, {}
    for mode in ("cpd", "hybrid"):
        loc[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    out, shorts, rec_s = {}, PS.short_refs(ctx), ctx["n"] * PS.WIN
    for name, ev in (("detector", det), ("localized", loc[localizer])):
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(shorts, ev)
        out[name] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=k, short_n=ns, top=top, q_raw=q,
                         review_s=float(sum(b - a for v in ev.values() for a, b in v)), rec_s=rec_s)
    errs = []
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(ctx), det):
        c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra, cpd_off=c1 - rb, hyb_on=y0 - ra, hyb_off=y1 - rb))
    return out, errs


def boot(A, B, n=10_000, seed=0):
    rng = np.random.default_rng(seed); subs = A.index.values; d = []
    for _ in range(n):
        s = rng.choice(subs, len(subs), replace=True)
        a, b = A.loc[s], B.loc[s]
        d.append((a.tp.sum() / a.n_ref.sum() - b.tp.sum() / b.n_ref.sum(), (a.tp / a.n_ref).mean() - (b.tp / b.n_ref).mean(),
                  a.fp.sum() / a.nonict_h.sum() * 24 - b.fp.sum() / b.nonict_h.sum() * 24))
    d = np.array(d)
    return [(np.percentile(d[:, i], 2.5), np.percentile(d[:, i], 97.5)) for i in range(3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repro-only", action="store_true")
    ap.add_argument("--confirm-look-7", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    cfg = json.load(open(FRZ / "freeze.json"))
    loc, points = cfg["localizer"], cfg["points"]
    stage = "hybrid" if loc == "hybrid" else "cpd"
    ref = pd.read_csv(FRZ / "per_subject.csv")
    bal_name = "L2f" if abs(points["balanced"][0] - 0.005) < 1e-12 else "L2"
    ctx = PS.subject_context("chb01")                                       # R1
    for pt, (fl, cp) in points.items():
        bname = bal_name if pt == "balanced" else "S"
        for tag in TAGS:
            out, _ = evaluate(ctx, tag, cfg, fl, cp, loc)
            for st_here, st_ref in (("detector", "detector"), ("localized", stage)):
                r = ref[(ref.subject == "chb01") & (ref.seed == tag) & (ref.budget == bname) & (ref.stage == st_ref)].iloc[0]
                if (out[st_here]["tp"], out[st_here]["fp"]) != (int(r.tp), int(r.fp)):
                    raise SystemExit(f"STOP R1 chb01 {pt} {tag} {st_here}: {(out[st_here]['tp'], out[st_here]['fp'])} vs {(int(r.tp), int(r.fp))}")
    print(f"R1 OK: points {list(points)} with localizer {loc} reproduce p3c_freeze on chb01, 4 seeds", flush=True)
    if a.repro_only:
        return
    if not a.confirm_look_7:
        raise SystemExit("refusing to touch test labels without --confirm-look-7")
    if subprocess.run(["git", "rev-parse", "-q", "--verify", "refs/tags/p3-frozen"], capture_output=True).returncode:
        raise SystemExit("refusing: git tag p3-frozen does not exist")
    look6 = pd.read_csv(ROOT / "results" / "e22_test_oneshot" / "per_subject_seed.csv")
    rows, erows = [], []
    for s in TEST:
        ctx = E22.test_context(s)
        for tag in TAGS:
            r6, _ = evaluate(ctx, tag, cfg, 0.005, 0.005, "cpd")              # R2
            for st in ("detector", "localized"):
                w = look6[(look6.subject == s) & (look6.seed == tag) & (look6.stage == st)].iloc[0]
                if (r6[st]["tp"], r6[st]["fp"]) != (int(w.tp), int(w.fp)):
                    raise SystemExit(f"STOP R2 {s} {tag} {st}: {(r6[st]['tp'], r6[st]['fp'])} vs look #6 {(int(w.tp), int(w.fp))}")
            for pt, (fl, cp) in points.items():
                out, errs = evaluate(ctx, tag, cfg, fl, cp, loc)
                for k_, v in out.items():
                    rows.append(dict(point=pt, subject=s, seed=tag, stage=k_, **v))
                erows += [dict(point=pt, subject=s, seed=tag, **e) for e in errs]
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    R, Er = pd.DataFrame(rows), pd.DataFrame(erows)
    R.to_csv(OUT / "per_subject_seed.csv", index=False); Er.to_csv(OUT / "errors.csv", index=False)

    L = ["# E23 -- look #7 (TEST-INFORMED, record 9.2) of the P3 frozen system, 8 test patients, 4 seeds\n",
         f"Points {json.dumps(points)}, k = {cfg['k']:.4f}, localizer {loc}. Non-test reference: {json.dumps(cfg.get('nontest', {}))}.",
         "Gates R1 (non-test path) and R2 (look #6 reproduced on test) passed.",
         "Hashes (sha256/16, LF): " + ", ".join(f"{n} {sha(ROOT / 'src' / n)}" for n in
                                                ("e23_test_look7.py", "p3c_freeze.py", "p3_levers.py", "p2_scalars.py",
                                                 "e18_cpd_localizer.py", "e17b_latent_family.py", "e22_test_oneshot.py")) + "\n"]
    summ = []
    B6 = look6[look6.stage == "localized"]
    for pt in points:
        L += [f"## Point: {pt} -- per seed (pooled | subject-mean)\n", "```",
              "stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short | review"]
        for label, df in (("detector", R[(R.point == pt) & (R.stage == "detector")]),
                          ("localized", R[(R.point == pt) & (R.stage == "localized")]), ("look #6", B6)):
            for tag in TAGS:
                d = df[df.seed == tag]; m = E22.metrics(d)
                rv = (d.review_s.sum() / d.rec_s.sum()) if "review_s" in d else np.nan
                summ.append(dict(point=pt, system=label, seed=tag, review=rv, **m))
                L.append(f"{label:12s} {tag:13s} {m['tp']:3.0f}/{m['n_ref']:3.0f} {m['fp']:4.0f}  {m['sens']:.3f}  {m['prec']:.3f}  "
                         f"{m['f1']:.3f}  {m['fa_day']:6.2f} | {m['s_sens']:.3f}  {m['s_prec']:.3f}  {m['s_f1']:.3f} {m['s_fa']:6.2f} | "
                         f"{m['short']} | {rv:.4f}")
        L.append("```")
    S = pd.DataFrame(summ); S.to_csv(OUT / "summary_per_seed.csv", index=False)
    L += ["\n## Headline (seed 42) and 4-seed mean +- SD\n", "```"]
    for (pt, label), g in S.groupby(["point", "system"], sort=False):
        h = g[g.seed == "clean_seed42"].iloc[0]
        L.append(f"{pt:11s} {label:10s} seed 42: sens {h.sens:.3f} @ {h.fa_day:.2f}, prec {h.prec:.3f}, F1 {h.f1:.3f}, "
                 f"subject-mean {h.s_sens:.3f} | 4 seeds: sens {g.sens.mean():.3f} +- {g.sens.std(ddof=1):.3f}, FP/day "
                 f"{g.fa_day.mean():.2f} +- {g.fa_day.std(ddof=1):.2f}, subject-mean {g.s_sens.mean():.3f} +- {g.s_sens.std(ddof=1):.3f}")
    L.append("```")
    for pt in points:
        e = Er[Er.point == pt]
        if len(e):
            L += [f"\n## {pt}: onset / offset |error| on matched seizures (n = {len(e)} pairs)\n", "```"]
            for lab, c in (("detector", "det"), ("CPD", "cpd"), ("hybrid", "hyb")):
                L.append(f"{lab:9s} onset median {e[c + '_on'].abs().median():5.1f} s bias {e[c + '_on'].median():+5.1f} | "
                         f"offset median {e[c + '_off'].abs().median():5.1f} s bias {e[c + '_off'].median():+5.1f}")
            L.append("```")
        A = R[(R.point == pt) & (R.stage == "localized")].groupby("subject")[["tp", "fp", "n_ref", "nonict_h"]].mean()
        Bm = B6.groupby("subject")[["tp", "fp", "n_ref", "nonict_h"]].mean().loc[A.index]
        ci = boot(A, Bm)
        L += [f"\n## {pt}: patient-level bootstrap, P3 (after localizer) - look #6, 4-seed means, B = 10,000\n", "```",
              f"pooled sens diff {A.tp.sum() / A.n_ref.sum() - Bm.tp.sum() / Bm.n_ref.sum():+.3f} [{ci[0][0]:+.3f}, {ci[0][1]:+.3f}]",
              f"subject-mean diff {(A.tp / A.n_ref).mean() - (Bm.tp / Bm.n_ref).mean():+.3f} [{ci[1][0]:+.3f}, {ci[1][1]:+.3f}]",
              f"FP/day diff {A.fp.sum() / A.nonict_h.sum() * 24 - Bm.fp.sum() / Bm.nonict_h.sum() * 24:+.2f} [{ci[2][0]:+.2f}, {ci[2][1]:+.2f}]",
              "```", f"\n## {pt}: per subject, seed 42: P3 after localizer | look #6\n", "```"]
        for s in TEST:
            f_ = R[(R.point == pt) & (R.subject == s) & (R.seed == "clean_seed42") & (R.stage == "localized")].iloc[0]
            e_ = B6[(B6.subject == s) & (B6.seed == "clean_seed42")].iloc[0]
            L.append(f"{s}  {f_.tp}/{f_.n_ref} FP {f_.fp} ({f_.fp / f_.nonict_h * 24:5.1f}/day, top {f_.top:.4f}, q {f_.q_raw:.4f}) | "
                     f"{e_.tp}/{e_.n_ref} FP {e_.fp} ({e_.fp / e_.nonict_h * 24:5.1f}/day)")
        L.append("```")
    L.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
