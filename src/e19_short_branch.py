#!/usr/bin/env python
"""
e19_short_branch.py -- stage P2, E19 (design approved 2026-10-07, PERF_PHASE_RECORD 6.3).
15 non-test subjects, 4 seeds, cache only.

Problem (P1 diagnosis 4): 23/76 test seizures last < 20 s and E9 caught 0/18 short ones; the non-test
set has 3, so the benefit cannot be gated here. Second detector on the SAME scalar X:
smoothing 3 windows, threshold = the patient's top-p_s, only events <= 30 s kept, union with the main
D1 events (merge 90 s). Main D1 cell of X re-selected by the 4-seed pooled rule (FA/day <= 25).
p_s = the largest of {0.001, 0.002, 0.005} whose ADDED FA/day (4-seed mean, pooled) is <= 3.
ADOPTED if the union's pooled sensitivity is not lower than the main detector's and the added FA/day
<= 3. Short seizures caught (approximate overlap with the SzCORE 30 s / 60 s tolerances) are reported
descriptively, main vs union.
Reproduction: the main D1 events built here must give exactly the tp/fp of e1_normal_definition at
the chosen cell for every subject and seed, else STOP.
If no p_s fits the budget: --short-k 12 (fallback fixed now): the short branch uses the ensemble with C
taken as the 12th largest per-channel anomaly (broader spatial requirement), same budget rule.
Run:  python src/e19_short_branch.py --scalar Eb        (estimated 10-25 min CPU, not measured)
      (--scalar Eb_dt if E16g adopted it; --short-k 12 only as the pre-registered fallback)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import p2_scalars as PS                # noqa: E402
import e16_recording_baseline as E16   # noqa: E402
import e8_gae_v2_eval as E8            # noqa: E402
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]

OUT = ROOT / "results" / "e19_short_branch"
PSET = [0.001, 0.002, 0.005]
PARTS = ("C", "L", "gamma")


def scalar(ctx, tag, a, c_k=9):
    """final scalar from --c-arm / --parts (or the legacy --scalar names)."""
    parts = tuple(a.parts.split(",")) if a.parts else PARTS
    c_arm = a.c_arm
    if a.scalar == "Eb_h":
        c_arm = "e"
    if parts == ("C",):
        v = E16.rz(PS.readout(ctx, tag, "C", c_arm=c_arm, c_k=c_k), ctx["ok"])
    else:
        v = PS.ensemble_scalar(ctx, tag, parts, c_arm=c_arm, c_k=c_k)
    return PS.detrend_file(ctx, v) if a.scalar == "Eb_dt" else v

def main():
    import e1_normal_definition as E1
    ap = argparse.ArgumentParser()
    ap.add_argument("--scalar", default="Eb", choices=["Eb", "Eb_dt", "Eb_h"])
    ap.add_argument("--c-arm", default="S9base", choices=["S9base", "e", "b"], help="C of the final scalar (E21)")
    ap.add_argument("--parts", default=None, help="comma list, e.g. C,L,gamma or C (E21 final scalar)")
    ap.add_argument("--fine", action="store_true", help="E21 fine top-p grid")
    ap.add_argument("--short-k", type=int, default=9, choices=[9, 12])
    ap.add_argument("--total-cap", type=float, default=None,
                    help="also require the union's FA/day <= this cap (proposed 25, author decision)")
    a = ap.parse_args()
    if a.fine:
        E1.TOPS = FINE
    spec = f"{a.scalar}" if not a.parts else f"{a.parts.replace(',', '+')}_C{a.c_arm}"
    spec += "_fine" if a.fine else ""
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ctxs, X, rows = {}, {}, []
    for s in E8.SUBJS:                                   # pass 1: main grid, cell selection
        ctx = PS.subject_context(s); ctxs[s] = ctx
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            X[(s, tag)] = scalar(ctx, tag, a)
            for r_ in E1.event_grid(d, X[(s, tag)]):
                r_.update(subject=s, score=f"{tag}|main", nonict_h=ctx["nh"]); rows.append(r_)
        print(f"{s}: grid ({time.time()-t0:.0f}s)", flush=True)
    gr = pd.DataFrame(rows); gr["kind"] = "main"; gr["seed"] = gr.score.str.split("|").str[0]
    Mn = E16.summarise(gr, "main")
    if Mn["cell"] is None:
        raise SystemExit("STOP: the main scalar never reaches FA/day <= 25")
    sm_, top_ = Mn["cell"][0], Mn["cell"][1]

    out = []                                             # pass 2: main vs union
    for s in E8.SUBJS:
        ctx = ctxs[s]; refs = PS.short_refs(ctx)
        g = gr[(gr.subject == s) & (gr.smooth == sm_) & (gr.top == top_)].set_index("seed")
        for tag in PS.TAGS:
            main = PS.d1_events(ctx, X[(s, tag)], sm_, top_)
            tp, fp, nr, h = PS.score(ctx, main)
            if tp != int(g.loc[tag, "tp"]) or fp != int(g.loc[tag, "fp"]):
                raise SystemExit(f"STOP {s} {tag}: main D1 ({tp},{fp}) differs from event_grid "
                                 f"({int(g.loc[tag, 'tp'])},{int(g.loc[tag, 'fp'])})")
            k0, n0 = PS.caught(refs, main)
            out.append(dict(subject=s, seed=tag, arm="main", p_s=np.nan, tp=tp, fp=fp, n_ref=nr, nonict_h=h,
                            short_caught=k0, short_n=n0))
            xs = X[(s, tag)] if a.short_k == 9 else scalar(ctx, tag, a, c_k=12)
            for p in PSET:
                short = PS.d1_events(ctx, xs, 3, p, keep_max_s=30)
                uni = {f: PS.merge(main.get(f, []) + short.get(f, [])) for f in set(main) | set(short)}
                tp, fp, nr, h = PS.score(ctx, uni)
                k1, n1 = PS.caught(refs, uni)
                out.append(dict(subject=s, seed=tag, arm="union", p_s=p, tp=tp, fp=fp, n_ref=nr, nonict_h=h,
                                short_caught=k1, short_n=n1))
        print(f"{s}: union ({time.time()-t0:.0f}s)", flush=True)
    U = pd.DataFrame(out); U.to_csv(OUT / f"per_subject_{spec}_k{a.short_k}{'_cap' if a.total_cap else ''}.csv", index=False)

    def pooled(df):
        q = df.groupby(["arm", "p_s", "seed"], dropna=False)[["tp", "fp", "n_ref", "nonict_h", "short_caught",
                                                               "short_n"]].sum().reset_index()
        q["sens"] = q.tp / q.n_ref; q["fa_day"] = q.fp / q.nonict_h * 24
        return q.groupby(["arm", "p_s"], dropna=False)[["sens", "fa_day", "short_caught", "short_n"]].mean().reset_index()

    P, V = pooled(U), pooled(U[U.subject.isin(E8.VAL)])
    m0 = P[P.arm == "main"].iloc[0]
    lines = [f"# E19 -- short-seizure branch on {spec} (short branch k = {a.short_k}, total cap {a.total_cap}), 4 seeds, 15 non-test\n",
             f"Main D1 cell (re-selected): smooth {sm_}, top {top_}; reproduction of event_grid exact.\n",
             "```", "arm    p_s     sens   FA/day  added FA  short caught  val sens"]
    lines.append(f"main   -       {m0.sens:.3f}  {m0.fa_day:6.2f}  {0:8.2f}  {m0.short_caught:.2f}/{m0.short_n:.0f}"
                 f"      {V[V.arm == 'main'].sens.iloc[0]:.3f}")
    cand = []
    for p in PSET:
        r = P[(P.arm == "union") & (P.p_s == p)].iloc[0]
        added = r.fa_day - m0.fa_day
        lines.append(f"union  {p:<6}  {r.sens:.3f}  {r.fa_day:6.2f}  {added:8.2f}  {r.short_caught:.2f}/{r.short_n:.0f}"
                     f"      {V[(V.arm == 'union') & (V.p_s == p)].sens.iloc[0]:.3f}")
        if added <= 3 and (a.total_cap is None or r.fa_day <= a.total_cap):
            cand.append((p, r, added))
    lines.append("```")
    if cand:
        p, r, added = max(cand, key=lambda x: x[0])
        ok_ = r.sens >= m0.sens and added <= 3
        verdict = "ADOPTED" if ok_ else "NOT adopted"
        E16.ledger("E19", f"{spec}_k{a.short_k}_p{p}" + ("_cap" if a.total_cap else ""),
                   dict(best=float(r.sens), cell=(3, p, round(float(r.fa_day), 2))),
                   dict(sens_not_lower=r.sens >= m0.sens, added_fa_le3=added <= 3), verdict)
        lines.append(f"\np_s = {p} (largest within the +3 FA/day budget): union sens {r.sens:.3f} vs main {m0.sens:.3f}, "
                     f"added FA/day {added:.2f} -> **{verdict}**")
    else:
        E16.ledger("E19", f"{spec}_k{a.short_k}", dict(best=0.0, cell=None), {}, "no p_s within budget")
        lines.append("\nNo p_s fits the +3 FA/day budget -> describe the short false events; run --short-k 12 "
                     "(pre-registered fallback)" if a.short_k == 9 else "\nNo p_s fits the budget with k = 12 either.")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / f"SUMMARY_{spec}_k{a.short_k}{'_cap' if a.total_cap else ''}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
