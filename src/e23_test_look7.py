#!/usr/bin/env python
"""
e23_test_look7.py -- stage P3, look #7 at the test set. Written 2026-10-07 BEFORE the P3 freeze and before any
P3 number on test. Disclosed as TEST-INFORMED (record 9.2: the levers were triggered by the P3-A anatomy,
tier T-B). Look #6 stays the clean held-out result; this look is reported beside it.

FROZEN P3 SYSTEM = the P2 frozen system (e22) with the two P3 decisions read from
results/p3_levers/calibration.json (written by p3_levers.py from its pre-registered gates):
  budget    "frozen" (top 0.5 %) or "L2" (top-p_i = clip(q_i(k), 0.0025, 0.02), k from the non-test calibration)
  localizer "cpd" (E18) or "hybrid" (L6: CPD onset, contiguous-run offset, events > 300 s keep the detector's)
REPORTED (no gate): per seed and 4-seed mean +- SD (headline seed 42); pooled and official subject-mean
sensitivity, precision, F1 and FP/day from the scorer's counts, for the detector and after the localizer;
onset/offset |error| (detector, CPD, hybrid) with n; short seizures (< 20 s by whole-window runs);
per subject seed 42 next to look #6; patient-level bootstrap (B = 10,000, 4-seed means) of the pooled and
subject-mean difference P3 - look #6 and of FP/day.
EXPECTATION written now: FP/day about 1.2 x the non-test value of the frozen P3 configuration.
REPRODUCTION GATES (stop before reading any P3 result):
  R1 (--repro-only, non-test chb01): this code path reproduces results/p3_levers/per_subject.csv for the
     chosen budget (detector and chosen localizer stage), every seed;
  R2 (test): the configuration frozen budget + CPD reproduces look #6 (results/e22_test_oneshot/
     per_subject_seed.csv, detector and localized tp/fp) for every subject and seed.
GUARD: refuses test subjects unless --confirm-look-7 and the git tag p3-frozen exists; records sha256 of the
code it runs.
Run:  python src/e23_test_look7.py --repro-only           (non-test only, ~1 min, estimated)
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
LEV = ROOT / "results" / "p3_levers"
TAGS = list(E22.TAGS)
TEST = list(E22.TEST)
WIN = 4


def sha(p):
    return hashlib.sha256(Path(p).read_bytes().replace(b"\r\n", b"\n")).hexdigest()[:16]


def evaluate(ctx, tag, cfg, budget, localizer):
    x = E22.final_scalar(ctx, tag)
    if budget == "frozen":
        top = P3L.TOP0
    else:
        q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), cfg["smooth"]), cfg["k"])
        top = float(np.clip(q, cfg["P_MIN"], cfg["P_MAX"]))
    det = PS.d1_events(ctx, x, cfg["smooth"], top)
    thr = np.nanquantile(PS.smoothed(ctx, x, cfg["smooth"]), 1 - top)
    loc, pairs = {}, {}
    for mode in ("cpd", "hybrid"):
        loc[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    out = {}
    shorts = PS.short_refs(ctx)
    for name, ev in (("detector", det), ("localized", loc[localizer]), ("cpd", loc["cpd"]), ("hybrid", loc["hybrid"])):
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(shorts, ev)
        out[name] = dict(tp=tp, fp=fp, n_ref=nr, nonict_h=h, short_tp=k, short_n=ns, top=top)
    errs = []
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(ctx), det):
        c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(ref_dur=rb - ra, det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra, cpd_off=c1 - rb,
                         hyb_on=y0 - ra, hyb_off=y1 - rb))
    return out, errs


def boot(A, B, n=10_000, seed=0):
    """A, B: per-subject 4-seed-mean frames (tp, fp, n_ref, nonict_h); resample subjects."""
    rng = np.random.default_rng(seed); subs = A.index.values; d = []
    for _ in range(n):
        s = rng.choice(subs, len(subs), replace=True)
        a, b = A.loc[s], B.loc[s]
        d.append((a.tp.sum() / a.n_ref.sum() - b.tp.sum() / b.n_ref.sum(),
                  (a.tp / a.n_ref).mean() - (b.tp / b.n_ref).mean(),
                  a.fp.sum() / a.nonict_h.sum() * 24 - b.fp.sum() / b.nonict_h.sum() * 24))
    d = np.array(d)
    return [(np.percentile(d[:, i], 2.5), np.percentile(d[:, i], 97.5)) for i in range(3)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--repro-only", action="store_true")
    ap.add_argument("--confirm-look-7", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    cfg = json.load(open(LEV / "calibration.json"))
    budget, localizer = cfg["budget"], cfg["localizer"]
    stage = "hybrid" if localizer == "hybrid" else "cpd"
    lev = pd.read_csv(LEV / "per_subject.csv")
    ctx = PS.subject_context("chb01")                                  # R1
    for tag in TAGS:
        out, _ = evaluate(ctx, tag, cfg, budget, localizer)
        for st_here, st_lev in (("detector", "detector"), ("localized", stage)):
            r = lev[(lev.subject == "chb01") & (lev.seed == tag) & (lev.budget == budget) & (lev.stage == st_lev)].iloc[0]
            if (out[st_here]["tp"], out[st_here]["fp"]) != (int(r.tp), int(r.fp)):
                raise SystemExit(f"STOP R1 chb01 {tag} {st_here}: {(out[st_here]['tp'], out[st_here]['fp'])} vs {(int(r.tp), int(r.fp))}")
    print(f"R1 OK: budget {budget}, localizer {localizer} reproduce p3_levers on chb01, 4 seeds", flush=True)
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
            r6, _ = evaluate(ctx, tag, cfg, "frozen", "cpd")             # R2: look #6 reproduced
            for st in ("detector", "localized"):
                w = look6[(look6.subject == s) & (look6.seed == tag) & (look6.stage == st)].iloc[0]
                if (r6[st]["tp"], r6[st]["fp"]) != (int(w.tp), int(w.fp)):
                    raise SystemExit(f"STOP R2 {s} {tag} {st}: {(r6[st]['tp'], r6[st]['fp'])} vs look #6 {(int(w.tp), int(w.fp))}")
            out, errs = evaluate(ctx, tag, cfg, budget, localizer)
            for k_, v in out.items():
                rows.append(dict(subject=s, seed=tag, stage=k_, **v))
            erows += [dict(subject=s, seed=tag, **e) for e in errs]
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    OUT.mkdir(parents=True, exist_ok=True)
    R, Er = pd.DataFrame(rows), pd.DataFrame(erows)
    R.to_csv(OUT / "per_subject_seed.csv", index=False); Er.to_csv(OUT / "errors.csv", index=False)

    L = ["# E23 -- look #7 (TEST-INFORMED, record 9.2) of the P3 frozen system, 8 test patients, 4 seeds\n",
         f"Configuration: budget {budget}" + (f" (k = {cfg['k']:.4f})" if budget == "L2" else "") + f", localizer {localizer}. "
         "Gates R1 (non-test path) and R2 (look #6 reproduced on test) passed.",
         "Hashes (sha256/16, LF): " + ", ".join(f"{n} {sha(ROOT / 'src' / n)}" for n in
                                                ("e23_test_look7.py", "p3_levers.py", "p2_scalars.py", "e18_cpd_localizer.py",
                                                 "e17b_latent_family.py", "e22_test_oneshot.py")) + "\n",
         "## Per seed (pooled | subject-mean)\n", "```",
         "stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short"]
    summ = []
    for label, df in (("detector", R[R.stage == "detector"]), ("localized", R[R.stage == "localized"]),
                      ("look #6", look6[look6.stage == "localized"])):
        for tag in TAGS:
            m = E22.metrics(df[df.seed == tag]); summ.append(dict(system=label, seed=tag, **m))
            L.append(f"{label:12s} {tag:13s} {m['tp']:3.0f}/{m['n_ref']:3.0f} {m['fp']:4.0f}  {m['sens']:.3f}  {m['prec']:.3f}  "
                     f"{m['f1']:.3f}  {m['fa_day']:6.2f} | {m['s_sens']:.3f}  {m['s_prec']:.3f}  {m['s_f1']:.3f} {m['s_fa']:6.2f} | {m['short']}")
    L.append("```")
    S = pd.DataFrame(summ); S.to_csv(OUT / "summary_per_seed.csv", index=False)
    L += ["\n## Headline (seed 42) and 4-seed mean +- SD\n", "```"]
    for label, g in S.groupby("system", sort=False):
        h = g[g.seed == "clean_seed42"].iloc[0]
        L.append(f"{label:12s} seed 42: sens {h.sens:.3f} @ {h.fa_day:.2f} FP/day, prec {h.prec:.3f}, F1 {h.f1:.3f} | 4 seeds: "
                 f"sens {g.sens.mean():.3f} +- {g.sens.std(ddof=1):.3f}, FP/day {g.fa_day.mean():.2f} +- {g.fa_day.std(ddof=1):.2f}, "
                 f"subject-mean sens {g.s_sens.mean():.3f} +- {g.s_sens.std(ddof=1):.3f}")
    L.append("```")
    if len(Er):
        L += [f"\n## Onset / offset |error| on matched seizures (n = {len(Er)} pairs)\n", "```"]
        for lab, c in (("detector", "det"), ("CPD", "cpd"), ("hybrid", "hyb")):
            on, off = Er[f"{c}_on"], Er[f"{c}_off"]
            L.append(f"{lab:9s} onset median {on.abs().median():5.1f} s bias {on.median():+5.1f} | offset median "
                     f"{off.abs().median():5.1f} s bias {off.median():+5.1f}")
        L.append("```")
    A = R[R.stage == "localized"].groupby("subject")[["tp", "fp", "n_ref", "nonict_h"]].mean()
    B = look6[look6.stage == "localized"].groupby("subject")[["tp", "fp", "n_ref", "nonict_h"]].mean().loc[A.index]
    ci = boot(A, B)
    L += ["\n## Patient-level bootstrap, P3 (after localizer) - look #6, 4-seed means, B = 10,000\n", "```",
          f"pooled sens diff {A.tp.sum() / A.n_ref.sum() - B.tp.sum() / B.n_ref.sum():+.3f} [{ci[0][0]:+.3f}, {ci[0][1]:+.3f}]",
          f"subject-mean diff {(A.tp / A.n_ref).mean() - (B.tp / B.n_ref).mean():+.3f} [{ci[1][0]:+.3f}, {ci[1][1]:+.3f}]",
          f"FP/day diff {A.fp.sum() / A.nonict_h.sum() * 24 - B.fp.sum() / B.nonict_h.sum() * 24:+.2f} [{ci[2][0]:+.2f}, {ci[2][1]:+.2f}]", "```",
          "\n## Per subject, seed 42: P3 after localizer | look #6 (budget top-p)\n", "```"]
    for s in TEST:
        f_ = R[(R.subject == s) & (R.seed == "clean_seed42") & (R.stage == "localized")].iloc[0]
        e_ = look6[(look6.subject == s) & (look6.seed == "clean_seed42") & (look6.stage == "localized")].iloc[0]
        L.append(f"{s}  {f_.tp}/{f_.n_ref} FP {f_.fp} ({f_.fp / f_.nonict_h * 24:5.1f}/day, top {f_.top:.4f}) | "
                 f"{e_.tp}/{e_.n_ref} FP {e_.fp} ({e_.fp / e_.nonict_h * 24:5.1f}/day)")
    L += ["```", f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
