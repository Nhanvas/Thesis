#!/usr/bin/env python
"""
p3_levers.py -- stage P3, the levers triggered by P3-A (record 9.5, decision table fixed before P3-A).
15 non-test subjects, 4 seeds, cache only. Written 2026-10-07 after P3-A, before any lever result.

Triggers read from results/p3_anatomy/SUMMARY.md (P3-A):
  L1 focal member      test resc_S3e - loss_S3e = 1.50 - 5.25 < 3            -> NOT triggered (H6 not supported)
  L2 per-patient budget missed test seizures (seed 42) with p_need in (0.005, 0.02] = 16 >= 3 -> TRIGGERED
  L3 guarded correction test resc_final_nodt - loss = 0.50 - 13.25 < 3      -> NOT triggered (the correction helps)
  L4 trimmed fit        non-test resc_trim - loss = 0.25 - 2.00 < 2         -> NOT triggered (H2 not supported)
  L5 input normalisation no test patient beyond the training range (clip share <= 0.012, |shift| <= 1.56 SD;
                        training patients reach 0.077 and 1.54)              -> NOT triggered (H7 not supported)
  L6 localizer hybrid   always                                               -> RUN
  Non-test analogue of L2's mechanism: chb12 caught 4.75/27 at p_need <= 0.005, 12.5 at <= 0.02.

L2 (one construction, fixed in record 9.5): m(t) = mean over the four frozen members (S6e, S9e, S12e,
  Smean_e; e17b_latent_family.member) of their patient robust-z; smoothed as D1 (5 windows); q_i(k) =
  share of the patient's smoothed values above k; k calibrated ONCE on the 15 non-test patients, seed 42,
  so that the median q_i(k) = 0.005 (the frozen budget redistributed, not enlarged); every seed uses that
  k; top-p_i = clip(q_i, 0.0025, 0.02); D1 on the frozen scalar with smoothing 5 and top-p_i.
L6 (one construction): per detector event, onset = kernel-CPD onset (e18 cpd_event, if CPD accepted,
  else the detector's), offset = control 2 (e18 run_event: contiguous run containing the event peak);
  events longer than 300 s keep the detector's boundaries; re-merged (90 s).

GATE L2 (vs the P2 frozen detector E17b, cell 5/0.005: 0.668 @ 19.98, subject-mean 0.828, val 0.983):
  pooled sensitivity (4-seed mean) >= 0.648, subject-mean >= 0.808, validation pooled sensitivity
  >= 0.916, pooled FA/day <= 25; MECHANISM chb12 TP (4-seed mean) >= the frozen detector's.
  (L2 has no grid cell: its budget is the construction; validation is read at the construction.)
GATE L6 (vs the current localizer E18 CPD on the same detector): post-localizer pooled sensitivity >=
  detector - 0.005; median |onset| and |offset| errors each not worse than CPD's, one better by >= 4 s.
  Scored on the frozen detector and, if L2 passes, on the L2 detector (L6 must pass on the detector used).
If not met: L2 -> the per-subject TP/FP table shows where the budget moved (which patients paid in FA);
  the frozen budget stands. L6 -> CPD stays the localizer.
REPRODUCTION (STOP before any result): frozen detector 4-seed pooled = 0.668 @ 19.98 (+-0.0015 /
  +-0.02) and E18 CPD post-localizer = 0.662 @ 19.55 (same tolerances).
OUTPUT results/p3_levers/: SUMMARY.md, per_subject.csv, errors.csv, calibration.json (k and the
  non-test q_i, for look #7); one ledger row per lever in results/p2_ledger.csv.
--include-test prints the label-free budget p_i of the 8 test patients (tier T-A: no annotation read
  for it); nothing else on test.
Run:  python src/p3_levers.py --smoke    (chb01 + chb10, seed 42; no gates, ~1 min, estimated)
      python src/p3_levers.py --include-test   (estimated 4-10 min CPU, not measured)
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
import e17b_latent_family as F17       # noqa: E402
import e18_cpd_localizer as E18        # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
import e22_test_oneshot as E22         # noqa: E402

OUT = ROOT / "results" / "p3_levers"
TAGS = list(E16.TAGS)
SMOOTH, TOP0, MARGIN, WIN = 5, 0.005, 15, 4
P_MIN, P_MAX = 0.0025, 0.02
REF_DET, REF_CPD = (0.668, 19.98), (0.662, 19.55)
GATE = dict(pooled=0.648, subj=0.808, val=0.916, fa=25.0)
LONG_S = 300


# ----------------------------------------------------------------------------- builders
def member_mean_z(ctx, tag):
    """m(t): mean over the four frozen members of their patient robust-z (full window axis)."""
    zs = [E16.rz(PS._full(ctx, F17.member(ctx["D"][tag], ctx["wf"], kk)), ctx["ok"]) for kk in F17.MEMBERS.values()]
    return np.mean(zs, axis=0)


def q_of(sm_m, k):
    v = sm_m[np.isfinite(sm_m)]
    return float((v > k).mean())


def calibrate(sms):
    """k such that the median over patients of q_i(k) = TOP0 (bisection; q is non-increasing in k)."""
    lo, hi = 0.0, float(max(np.nanmax(s) for s in sms))
    for _ in range(80):
        k = (lo + hi) / 2
        if np.median([q_of(s, k) for s in sms]) > TOP0:
            lo = k
        else:
            hi = k
    return (lo + hi) / 2


def refs_of(ctx):
    out = {}
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        out[f] = [(i * WIN, j * WIN) for i, j in PS._runs(ctx["ict"][m])]
    return out


def localize(ctx, x, det, thr, mode):
    """mode 'cpd' = E18 (frozen localizer); 'hybrid' = L6. Returns events (s) and per-event boundaries."""
    loc, pair = {}, {}
    for f, evs in det.items():
        m = np.flatnonzero(ctx["fidx"] == f)
        xf, okf = x[m], ctx["ok"][m]
        new = []
        for e0, e1 in evs:
            aw, bw = e0 // WIN, e1 // WIN
            ca, cb, used = E18.cpd_event(xf, okf, aw, bw, MARGIN)
            if mode == "cpd":
                a_, b_ = ca, cb
            elif e1 - e0 > LONG_S:
                a_, b_ = aw, bw
            else:
                _, rb = E18.run_event(xf, okf, aw, bw, MARGIN, thr)
                a_ = ca if used else aw
                b_ = rb
                if b_ <= a_:
                    a_, b_ = aw, bw
            new.append((a_ * WIN, b_ * WIN)); pair[(f, e0, e1)] = (a_ * WIN, b_ * WIN)
        loc[f] = PS.merge(new)
    return loc, pair


# ----------------------------------------------------------------------------- aggregation
def agg(R, subjects=None):
    q = R if subjects is None else R[R.subject.isin(subjects)]
    p = q.groupby("seed")[["tp", "fp", "n_ref", "nonict_h"]].sum()
    sens = (p.tp / p.n_ref); fa = p.fp / p.nonict_h * 24
    s = q.assign(se=q.tp / q.n_ref, fd=q.fp / q.nonict_h * 24).groupby("seed")[["se", "fd"]].mean()
    return dict(sens=float(sens.mean()), fa=float(fa.mean()), seeds={t: float(sens.get(t, np.nan)) for t in TAGS},
                subj=float(s.se.mean()), subj_fa=float(s.fd.mean()))


def summary_row(R, label):
    a = agg(R); v = agg(R, E8.VAL); x = agg(R, [s for s in R.subject.unique() if s != "chb12"])
    tp12 = float(R[R.subject == "chb12"].tp.mean()) if (R.subject == "chb12").any() else np.nan
    sh = R.groupby("seed")[["short_tp", "short_n"]].sum().mean()
    return dict(label=label, **a, val=v["sens"], val_fa=v["fa"], x12=x["sens"], chb12_tp=tp12,
                short=f"{sh.short_tp:.2f}/{sh.short_n:.0f}")


def fmt(r):
    return (f"{r['label']:24s} {r['sens']:.3f} @ {r['fa']:5.2f} | subject-mean {r['subj']:.3f} @ {r['subj_fa']:5.2f} | "
            f"val {r['val']:.3f} @ {r['val_fa']:5.2f} | no-chb12 {r['x12']:.3f} | chb12 TP {r['chb12_tp']:.2f} | "
            f"short {r['short']} | seeds " + ", ".join(f"{v:.3f}" for v in r["seeds"].values()))


def err_stats(E, col):
    v = E[col].abs()
    return float(v.median()), f"median {v.median():5.1f} s IQR [{v.quantile(.25):.1f}, {v.quantile(.75):.1f}] bias {E[col].median():+5.1f}"


# ----------------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--include-test", action="store_true")
    a = ap.parse_args()
    t0 = time.time()
    subjects = ["chb01", "chb10"] if a.smoke else list(E8.SUBJS)
    tags = ["clean_seed42"] if a.smoke else TAGS
    if set(subjects) & set(E22.TEST):
        raise SystemExit("TEST GUARD")
    ctxs, X, SMM = {}, {}, {}
    for s in subjects:
        ctx = PS.subject_context(s); ctxs[s] = ctx
        for tag in tags:
            X[(s, tag)] = E22.final_scalar(ctx, tag)
            SMM[(s, tag)] = PS.smoothed(ctx, member_mean_z(ctx, tag), SMOOTH)
    k = calibrate([SMM[(s, "clean_seed42")] for s in subjects])
    q = {(s, t): q_of(SMM[(s, t)], k) for s in subjects for t in tags}
    p_i = {key: float(np.clip(v, P_MIN, P_MAX)) for key, v in q.items()}
    print(f"k = {k:.4f} (median q_i on seed 42 = {np.median([q[(s, 'clean_seed42')] for s in subjects]):.4f})", flush=True)

    rows, errs = [], []
    for s in subjects:
        ctx = ctxs[s]; refs = refs_of(ctx); shorts = PS.short_refs(ctx)
        for tag in tags:
            x = X[(s, tag)]
            for budget in ("frozen", "L2"):
                top = TOP0 if budget == "frozen" else p_i[(s, tag)]
                det = PS.d1_events(ctx, x, SMOOTH, top)
                thr = np.nanquantile(PS.smoothed(ctx, x, SMOOTH), 1 - top)
                stages = {"detector": det}
                pairs = {}
                for mode in ("cpd", "hybrid"):
                    stages[mode], pairs[mode] = localize(ctx, x, det, thr, mode)
                for st, ev in stages.items():
                    tp, fp, nr, h = PS.score(ctx, ev)
                    kk, ns = PS.caught(shorts, ev)
                    rows.append(dict(subject=s, seed=tag, budget=budget, stage=st, top=top, tp=tp, fp=fp, n_ref=nr,
                                     nonict_h=h, short_tp=kk, short_n=ns))
                for f, ra, rb, h0, h1 in E18.match_errors(refs, det):
                    c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
                    errs.append(dict(subject=s, seed=tag, budget=budget, ref_dur=rb - ra, ev_dur=h1 - h0,
                                     det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra, cpd_off=c1 - rb,
                                     hyb_on=y0 - ra, hyb_off=y1 - rb))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    R, E = pd.DataFrame(rows), pd.DataFrame(errs)
    od = OUT / "smoke" if a.smoke else OUT
    od.mkdir(parents=True, exist_ok=True)
    R.to_csv(od / "per_subject.csv", index=False); E.to_csv(od / "errors.csv", index=False)

    S = {(b, st): summary_row(R[(R.budget == b) & (R.stage == st)], f"{b} {st}")
         for b in ("frozen", "L2") for st in ("detector", "cpd", "hybrid")}
    if not a.smoke:                                                        # reproduction
        d0, c0 = S[("frozen", "detector")], S[("frozen", "cpd")]
        if abs(d0["sens"] - REF_DET[0]) > 0.0015 or abs(d0["fa"] - REF_DET[1]) > 0.02:
            raise SystemExit(f"STOP: frozen detector {d0['sens']:.4f} @ {d0['fa']:.3f}, record {REF_DET}")
        if abs(c0["sens"] - REF_CPD[0]) > 0.0015 or abs(c0["fa"] - REF_CPD[1]) > 0.02:
            raise SystemExit(f"STOP: frozen CPD {c0['sens']:.4f} @ {c0['fa']:.3f}, record {REF_CPD}")

    L = ["# P3 levers -- L2 per-patient budget and L6 localizer hybrid, 15 non-test, 4 seeds\n",
         "Reproduction: frozen detector and E18 CPD match the record." if not a.smoke else "SMOKE (no gates).",
         f"\nL2 calibration (seed 42, non-test): k = {k:.4f} robust-z units; median q_i = 0.005.\n",
         "## Detection and localization (pooled sens @ FA/day, 4-seed mean)\n", "```"]
    L += [fmt(S[key]) for key in S] + ["```"]
    pt = R[R.stage == "detector"].pivot_table(index="subject", columns="budget", values=["tp", "fp", "top"], aggfunc="mean")
    pt[("n_ref", "")] = R[R.stage == "detector"].groupby("subject").n_ref.first()
    L += ["\n## Per subject, detector (4-seed mean): budget top-p, TP, FP\n", "```", pt.round(4).to_string(), "```"]

    verdicts = {}
    fz, l2 = S[("frozen", "detector")], S[("L2", "detector")]
    g = dict(pooled=l2["sens"] >= GATE["pooled"], subj=l2["subj"] >= GATE["subj"], val=l2["val"] >= GATE["val"],
             fa=l2["fa"] <= GATE["fa"], mech_chb12=(l2["chb12_tp"] >= fz["chb12_tp"]) if np.isfinite(fz["chb12_tp"]) else False)
    verdicts["L2"] = all(g.values())
    L += ["\n## L2 gate\n", "- " + " ".join(f"{kk} {'pass' if v else 'FAIL'}" for kk, v in g.items()),
          f"\n**L2 {'ADOPTED' if verdicts['L2'] else 'NOT adopted'}**"]
    for b in ("frozen", "L2"):
        if b == "L2" and not verdicts["L2"]:
            continue
        Eb, det, hyb, cpd = E[E.budget == b], S[(b, "detector")], S[(b, "hybrid")], S[(b, "cpd")]
        con, con_s = err_stats(Eb, "cpd_on"); coff, coff_s = err_stats(Eb, "cpd_off")
        hon, hon_s = err_stats(Eb, "hyb_on"); hoff, hoff_s = err_stats(Eb, "hyb_off")
        _, don_s = err_stats(Eb, "det_on"); _, doff_s = err_stats(Eb, "det_off")
        gs = hyb["sens"] >= det["sens"] - 0.005
        gl = hon <= con and hoff <= coff and (hon <= con - 4 or hoff <= coff - 4)
        verdicts[f"L6_{b}"] = bool(gs and gl)
        L += [f"\n## L6 on the {b} detector (matched pairs n = {len(Eb)})\n", "```",
              f"onset   detector {don_s} | CPD {con_s} | hybrid {hon_s}",
              f"offset  detector {doff_s} | CPD {coff_s} | hybrid {hoff_s}",
              f"sens    detector {det['sens']:.3f} | CPD {cpd['sens']:.3f} | hybrid {hyb['sens']:.3f}", "```",
              f"- sensitivity >= detector - 0.005 -> {'pass' if gs else 'FAIL'}; errors -> {'pass' if gl else 'FAIL'}",
              f"\n**L6 on {b}: {'ADOPTED (hybrid localizer)' if verdicts[f'L6_{b}'] else 'NOT adopted (CPD stays)'}**"]
    if not a.smoke:
        E16.ledger("P3-L2", "per-patient budget k-calibrated", dict(best=l2["sens"], cell=("5", "p_i"), val=l2["val"],
                   x12=l2["x12"], subj=l2["subj"], subj_fa=l2["subj_fa"], seeds=l2["seeds"]),
                   {kk: v for kk, v in g.items()}, "ADOPTED" if verdicts["L2"] else "NOT adopted")
        b = "L2" if verdicts["L2"] else "frozen"
        E16.ledger("P3-L6", f"hybrid localizer on {b}", dict(best=S[(b, "hybrid")]["sens"], cell=("5", b)),
                   {"rule": verdicts.get(f"L6_{b}", False)}, "ADOPTED" if verdicts.get(f"L6_{b}") else "NOT adopted")
    final_b = "L2" if verdicts["L2"] else "frozen"
    final_l = "hybrid" if verdicts.get(f"L6_{final_b}") else "cpd"
    L.append(f"\n**P3 configuration for the freeze: budget = {final_b}, localizer = {final_l}**")

    if a.include_test:                                                    # tier T-A, label-free
        tq = {}
        for s in E22.TEST:
            ctx = E22.test_context(s)
            tq[s] = [float(np.clip(q_of(PS.smoothed(ctx, member_mean_z(ctx, t), SMOOTH), k), P_MIN, P_MAX)) for t in TAGS]
        L += ["\n## Label-free budget p_i of the test patients under L2 (tier T-A, no annotation read; 4 seeds)\n", "```"]
        L += [f"{s}  " + ", ".join(f"{v:.4f}" for v in tq[s]) for s in E22.TEST] + ["```"]
    json.dump(dict(k=k, P_MIN=P_MIN, P_MAX=P_MAX, smooth=SMOOTH, budget=final_b, localizer=final_l,
                   q_nontest={f"{s}|{t}": q[(s, t)] for s, t in q}), open(od / "calibration.json", "w"), indent=1)
    L.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (od / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
