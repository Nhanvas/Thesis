#!/usr/bin/env python
"""
p3c_freeze.py -- stage P3, last design step before the freeze (record 9.7). 15 non-test subjects, 4 seeds,
cache only. Written 2026-10-07 after p3_levers and p3b_diag, before any result of this script.

WHY (measured on non-test, results/p3_levers/SUMMARY.md): the L2 floor 0.0025 cuts the budget of patients
whose seizures already sit near the frozen threshold -- chb21 at 0.0025 lost 1.25 of 4 seizures (TP 1.75 ->
0.50), chb20 at 0.0041 lost 0.5. L2 passed its non-inferiority gate only because other patients
compensated (pooled 0.657 vs 0.668). Fix of the construction, gate unchanged:
  L2f  top-p_i = clip(q_i(k), 0.005, 0.02): the label-free budget only RAISES a patient above the frozen
       0.005, never cuts below it (same k = 4.0677 from p3_levers/calibration.json, no recalibration).
       Raising a threshold budget is monotone: every seizure caught at 0.005 stays caught.
  (Disclosure: the label-free test budgets printed by p3_levers -- chb06 and chb17 at the 0.0025 floor --
  were seen before this design; the reason for the change is the non-test chb21/chb20 loss.)
GATE L2f (record 9.5, unchanged): pooled >= 0.648, subject-mean >= 0.808, validation pooled >= 0.916,
  pooled FA/day <= 25 (4-seed means); MECHANISM: every subject's 4-seed-mean TP >= the frozen detector's.
CHOICE (fixed now): L2f replaces L2 if it passes the gate and its pooled sensitivity >= L2's (0.657);
  otherwise L2 stays (already adopted).
LOCALIZER: the L6 rule of p3_levers on the chosen budget (hybrid if post-localizer sensitivity >= detector
  - 0.005 and onset/offset not worse than CPD with one better by >= 4 s; else CPD).
SENSITIVITY-PRIORITY POINT (headline rule, record 9.6): floor t_s = the top-p at smoothing 5 with the best
  pooled non-test sensitivity at FA/day <= 40 on the fine grid of p3b_diag (results/p3b_diag/grid.csv; ties
  -> lower FA); budget clip(q_i, t_s, max(0.02, t_s)); kept only if its non-test pooled FA/day <= 40.
REPRODUCTION (STOP first): floor 0.0025 reproduces the p3_levers L2 detector tp/fp, and floor = cap = 0.005
  reproduces the frozen detector, for every subject and seed.
ALSO REPORTED: review fraction = detected event time / recorded time (a triage reading-load measure).
--include-test: raw q_i and the budgets of the 8 test patients (label-free, tier T-A).
OUTPUT results/p3c_freeze/: SUMMARY.md, per_subject.csv, errors.csv, freeze.json (read by e23_test_look7);
one ledger row per arm.
Run:  python src/p3c_freeze.py --include-test     (estimated 4-10 min CPU, not measured)
"""
import argparse
import json
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
import e16_recording_baseline as E16   # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402
import p3_levers as P3L                # noqa: E402

OUT = ROOT / "results" / "p3c_freeze"
TAGS = list(E16.TAGS)
SMOOTH, CAP = 5, 0.02
GATE = dict(pooled=0.648, subj=0.808, val=0.916, fa=25.0)


def budget(q, floor, cap):
    return float(np.clip(q, floor, max(cap, floor)))


def run_budget(ctx, s, tag, x, q, floor, cap, name, rows, errs):
    top = budget(q, floor, cap)
    det = PS.d1_events(ctx, x, SMOOTH, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
    stages, pairs = {"detector": det}, {}
    for mode in ("cpd", "hybrid"):
        stages[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    rec_s = ctx["n"] * PS.WIN
    for st, ev in stages.items():
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(PS.short_refs(ctx), ev)
        rows.append(dict(subject=s, seed=tag, budget=name, stage=st, top=top, tp=tp, fp=fp, n_ref=nr, nonict_h=h,
                         short_tp=k, short_n=ns, review_s=float(sum(b - a for v in ev.values() for a, b in v)), rec_s=rec_s))
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(ctx), det):
        c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(subject=s, seed=tag, budget=name, det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra,
                         cpd_off=c1 - rb, hyb_on=y0 - ra, hyb_off=y1 - rb))


def sens_floor():
    g = pd.read_csv(ROOT / "results" / "p3b_diag" / "grid.csv")
    g = g[g.smooth == SMOOTH]
    p = g.groupby(["seed", "top"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
    p["sens"] = p.tp / p.n_ref; p["fa"] = p.fp / p.nonict_h * 24
    m = p.groupby("top")[["sens", "fa"]].mean().reset_index()
    q = m[m.fa <= 40].sort_values(["sens", "fa"], ascending=[False, True])
    return float(q.top.iloc[0]), float(q.sens.iloc[0]), float(q.fa.iloc[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--include-test", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    k = json.load(open(ROOT / "results" / "p3_levers" / "calibration.json"))["k"]
    t_s, s_grid, fa_grid = sens_floor()
    arms = {"frozen": (0.005, 0.005), "L2": (P3L.P_MIN, CAP), "L2f": (0.005, CAP), "S": (t_s, CAP)}
    lev = pd.read_csv(ROOT / "results" / "p3_levers" / "per_subject.csv")
    rows, errs, qtab = [], [], []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s)
        for tag in TAGS:
            x = E22.final_scalar(ctx, tag)
            q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), SMOOTH), k)
            qtab.append(dict(subject=s, set="non-test", seed=tag, q_raw=q))
            for name, (fl, cp) in arms.items():
                run_budget(ctx, s, tag, x, q, fl, cp, name, rows, errs)
            for name, lb in (("frozen", "frozen"), ("L2", "L2")):          # reproduction
                mine = [r for r in rows if r["subject"] == s and r["seed"] == tag and r["budget"] == name and r["stage"] == "detector"][0]
                ref = lev[(lev.subject == s) & (lev.seed == tag) & (lev.budget == lb) & (lev.stage == "detector")].iloc[0]
                if (mine["tp"], mine["fp"]) != (int(ref.tp), int(ref.fp)):
                    raise SystemExit(f"STOP reproduction {s} {tag} {name}: {(mine['tp'], mine['fp'])} vs p3_levers {(int(ref.tp), int(ref.fp))}")
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    R, E = pd.DataFrame(rows), pd.DataFrame(errs)
    OUT.mkdir(parents=True, exist_ok=True)
    R.to_csv(OUT / "per_subject.csv", index=False); E.to_csv(OUT / "errors.csv", index=False)

    def row(b, st):
        q = R[(R.budget == b) & (R.stage == st)]
        r = P3L.summary_row(q, f"{b} {st}")
        r["review"] = float(q.groupby("seed").apply(lambda d: d.review_s.sum() / d.rec_s.sum()).mean())
        return r
    S = {(b, st): row(b, st) for b in arms for st in ("detector", "cpd", "hybrid")}
    L = ["# P3 freeze step -- L2f (budget never below 0.005) and the sensitivity-priority point, 15 non-test, 4 seeds\n",
         "Reproduction: floor 0.0025 = p3_levers L2 and floor = cap = 0.005 = frozen detector, every subject and seed.\n",
         f"k = {k:.4f} (p3_levers); sensitivity-priority floor t_s = {t_s} (grid at smoothing 5: {s_grid:.3f} @ {fa_grid:.1f} FA/day).\n",
         "## Pooled sens @ FA/day (4-seed mean), subject-mean, validation, review fraction\n", "```"]
    L += [P3L.fmt(S[key]) + f" | review {S[key]['review']:.4f}" for key in S] + ["```"]
    tp_t = R[R.stage == "detector"].groupby(["budget", "subject"]).tp.mean().unstack(0)
    top_t = R[R.stage == "detector"].groupby(["budget", "subject"]).top.mean().unstack(0)
    L += ["\n## Per subject, detector (4-seed mean): TP | top-p\n", "```",
          pd.concat({"TP": tp_t, "top": top_t}, axis=1).round(4).to_string(), "```"]

    f2, l2 = S[("L2f", "detector")], S[("L2", "detector")]
    mono = bool((tp_t["L2f"] >= tp_t["frozen"] - 1e-9).all())
    g = dict(pooled=f2["sens"] >= GATE["pooled"], subj=f2["subj"] >= GATE["subj"], val=f2["val"] >= GATE["val"],
             fa=f2["fa"] <= GATE["fa"], mech_monotone=mono)
    adopt = all(g.values()) and f2["sens"] >= l2["sens"]
    bal = "L2f" if adopt else "L2"
    L += ["\n## L2f gate\n", "- " + " ".join(f"{kk} {'pass' if v else 'FAIL'}" for kk, v in g.items())
          + f"; pooled {f2['sens']:.3f} vs L2 {l2['sens']:.3f}",
          f"\n**Balanced budget: {bal}{' (L2f replaces L2)' if adopt else ' (L2 stays)'}**"]
    Eb = E[E.budget == bal]; det, hyb = S[(bal, "detector")], S[(bal, "hybrid")]
    con, coff = Eb.cpd_on.abs().median(), Eb.cpd_off.abs().median()
    hon, hoff = Eb.hyb_on.abs().median(), Eb.hyb_off.abs().median()
    gl = hon <= con and hoff <= coff and (hon <= con - 4 or hoff <= coff - 4)
    gs = hyb["sens"] >= det["sens"] - 0.005
    loc = "hybrid" if (gl and gs) else "cpd"
    L += [f"\nL6 on {bal}: onset CPD {con:.1f} / hybrid {hon:.1f} s, offset CPD {coff:.1f} / hybrid {hoff:.1f} s; "
          f"sens detector {det['sens']:.3f}, hybrid {hyb['sens']:.3f} -> **localizer {loc}**"]
    sp = S[("S", loc)]
    s_ok = sp["fa"] <= 40
    L.append(f"\nSensitivity-priority point (floor {t_s}): {sp['sens']:.3f} @ {sp['fa']:.2f} FA/day after the localizer -> "
             f"**{'kept' if s_ok else 'dropped (FA > 40)'}**")
    E16.ledger("P3-L2f", "budget clip(q, 0.005, 0.02)", dict(best=f2["sens"], cell=("5", "p_i"), val=f2["val"], x12=f2["x12"],
               subj=f2["subj"], subj_fa=f2["subj_fa"], seeds=f2["seeds"]), g, "ADOPTED" if adopt else "NOT adopted")
    E16.ledger("P3-S", f"sensitivity point clip(q, {t_s}, 0.02)", dict(best=sp["sens"], cell=("5", "p_i"), val=sp["val"],
               x12=sp["x12"], subj=sp["subj"], subj_fa=sp["subj_fa"], seeds=sp["seeds"]), {"fa_le_40": s_ok},
               "kept" if s_ok else "dropped")
    if a.include_test:
        L += ["\n## Test patients, label-free (tier T-A): raw q_i and budgets (balanced | sensitivity), 4 seeds\n", "```"]
        for s in E22.TEST:
            ctx = E22.test_context(s)
            qs = [P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, t), SMOOTH), k) for t in TAGS]
            fl_b = 0.005 if bal == "L2f" else P3L.P_MIN
            L.append(f"{s}  q_raw " + ", ".join(f"{v:.4f}" for v in qs) + " | " + ", ".join(f"{budget(v, fl_b, CAP):.4f}" for v in qs)
                     + " | " + ", ".join(f"{budget(v, t_s, CAP):.4f}" for v in qs))
        L.append("```")
    fr = dict(k=k, smooth=SMOOTH, cap=CAP, localizer=loc, points={"balanced": [0.005 if bal == "L2f" else P3L.P_MIN, CAP]})
    if s_ok:
        fr["points"]["sensitivity"] = [t_s, CAP]
    fr["nontest"] = {pt: dict(sens=S[(("L2f" if pt == "balanced" and bal == "L2f" else ("L2" if pt == "balanced" else "S")), loc)]["sens"],
                              fa=S[(("L2f" if pt == "balanced" and bal == "L2f" else ("L2" if pt == "balanced" else "S")), loc)]["fa"])
                     for pt in fr["points"]}
    json.dump(fr, open(OUT / "freeze.json", "w"), indent=1)
    L += [f"\n**Freeze candidate: {json.dumps({kk: fr[kk] for kk in ('localizer', 'points')})}**", f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
