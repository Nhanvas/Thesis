#!/usr/bin/env python
"""
e19b_short_branch_fine.py -- stage P2, E19 re-run on the E21 final scalar (author decisions 2026-10-07).
15 non-test subjects, 4 seeds, cache only, fine top-p grid of E21.

Why a re-run: E19 on Eb (coarse grid) was adopted with +0.011 pooled sensitivity (about ONE seizure of
94), short seizures caught unchanged (1/3 at every p_s), and a union at 25.7 FA/day, above the budget.
Its rule only asked "not lower"; a union adds alarms and so gains sensitivity mechanically, and the
main detector had been chosen on the coarse grid at 22.8 FA/day.
RULE (fixed now):
  * main-only reference = the best main D1 cell of the final scalar on the fine grid at FA/day <= 25
    (4-seed mean, pooled);
  * union(c, p_s) = main D1 at cell c + short branch (smoothing 3, patient top-p_s, events <= 30 s),
    merged at 90 s; c ranges over the fine-grid cells, p_s over {0.001, 0.002, 0.005};
  * a union is eligible if its total FA/day <= 25 AND it adds <= 3 FA/day over its own main cell;
  * ADOPTED only if the best eligible union has pooled sensitivity STRICTLY HIGHER than the main-only
    reference (ties -> lower FA/day among unions).
Reported: both validation quantities (best re-selected on the 3 validation subjects = the gate
definition; and sensitivity of the 3 validation subjects at the selected cell, descriptive).
Short-seizure diagnostics (the 3 short seizures of the selection set, every seed): percentile of the
peak of the 3-window-smoothed score inside the patient; for each p_s, the reason it is or is not caught
by the short branch: below threshold / supra-threshold run > 30 s / run <= 30 s but merged into an
event > 30 s and then dropped / kept. Also whether the main detector catches it.
Reproduction: main D1 at every cell used must equal event_grid tp/fp, else STOP.
Run:  python src/e19b_short_branch_fine.py --c-arm S9base --parts C,L,gamma   (E21 final scalar)
      (estimated 30-90 min CPU, not measured)
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
import e1_normal_definition as E1      # noqa: E402

OUT = ROOT / "results" / "e19_short_branch"
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
E1.TOPS = FINE
PSET = [0.001, 0.002, 0.005]
CAP, ADD = 25.0, 3.0


def build(ctx, tag, a):
    parts = tuple(a.parts.split(","))
    if parts == ("C",):
        return E16.rz(PS.readout(ctx, tag, "C", c_arm=a.c_arm), ctx["ok"])
    return PS.ensemble_scalar(ctx, tag, parts, c_arm=a.c_arm)


def short_diag(ctx, x, p_list, main_ev):
    sm3 = PS.smoothed(ctx, x, 3)
    vals = sm3[np.isfinite(sm3)]
    out = []
    for f in np.unique(ctx["fidx"]):
        m = np.flatnonzero(ctx["fidx"] == f)
        for i0, i1 in PS._runs(ctx["ict"][m]):
            if (i1 - i0) * PS.WIN >= 20:
                continue
            pk = np.nanmax(sm3[m[i0:i1]])
            a_s, b_s = i0 * PS.WIN, i1 * PS.WIN
            row = dict(file=int(f), onset_s=a_s, dur_s=b_s - a_s, peak_pct=float((vals <= pk).mean()),
                       main_caught=any(h1 >= a_s - 30 and h0 <= b_s + 60 for h0, h1 in main_ev.get(f, [])))
            for p in p_list:
                thr = np.nanquantile(sm3, 1 - p)
                above = np.nan_to_num(sm3[m], nan=-np.inf) > thr
                if not above[i0:i1].any():
                    row[f"p{p}"] = "below threshold"; continue
                j = i0 + int(np.argmax(above[i0:i1]))
                r = [(u, v) for u, v in PS._runs(above) if u <= j < v][0]
                run_s = (r[1] - r[0]) * PS.WIN
                merged = PS.merge([(u * PS.WIN, v * PS.WIN) for u, v in PS._runs(above)])
                mlen = [e1 - e0 for e0, e1 in merged if e0 <= j * PS.WIN < e1][0]
                row[f"p{p}"] = ("run > 30 s" if run_s > 30 else
                                "merged into > 30 s, dropped" if mlen > 30 else "kept")
            out.append(row)
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--c-arm", default="S9base", choices=["S9base", "e", "b"])
    ap.add_argument("--parts", default="C,L,gamma")
    a = ap.parse_args()
    spec = f"{a.parts.replace(',', '+')}_C{a.c_arm}_fine_cap25"
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ctxs, X, rows = {}, {}, []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s); ctxs[s] = ctx
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            X[(s, tag)] = build(ctx, tag, a)
            for r_ in E1.event_grid(d, X[(s, tag)]):
                r_.update(subject=s, score=f"{tag}|main", nonict_h=ctx["nh"]); rows.append(r_)
        print(f"{s}: grid ({time.time()-t0:.0f}s)", flush=True)
    gr = pd.DataFrame(rows); gr["kind"] = "main"; gr["seed"] = gr.score.str.split("|").str[0]
    Mn = E16.summarise(gr, "main")
    if Mn["cell"] is None:
        raise SystemExit("STOP: the final scalar never reaches FA/day <= 25")
    P, A = E16.pooled_tables(gr)
    cells = A[(A.kind == "main") & (A.fa_day <= CAP)][["smooth", "top", "sens", "fa_day"]].values.tolist()

    out, sdiag = [], []
    for s in E8.SUBJS:
        ctx = ctxs[s]
        for tag in PS.TAGS:
            x = X[(s, tag)]
            main_ref = PS.d1_events(ctx, x, Mn["cell"][0], Mn["cell"][1])
            sdiag += [dict(subject=s, seed=tag, **r) for r in short_diag(ctx, x, PSET, main_ref)]
            for sm_, top_, _, _ in cells:
                sm_ = int(sm_)
                g = gr[(gr.subject == s) & (gr.seed == tag) & (gr.smooth == sm_) & (gr.top == top_)].iloc[0]
                main = PS.d1_events(ctx, x, sm_, top_)
                tp, fp, nr, h = PS.score(ctx, main)
                if tp != int(g.tp) or fp != int(g.fp):
                    raise SystemExit(f"STOP {s} {tag} cell {sm_}/{top_}: D1 ({tp},{fp}) vs event_grid ({int(g.tp)},{int(g.fp)})")
                for p in PSET:
                    short = PS.d1_events(ctx, x, 3, p, keep_max_s=30)
                    uni = {f: PS.merge(main.get(f, []) + short.get(f, [])) for f in set(main) | set(short)}
                    tpu, fpu, nru, hu = PS.score(ctx, uni)
                    out.append(dict(subject=s, seed=tag, smooth=sm_, top=top_, p_s=p, tp=tpu, fp=fpu,
                                    n_ref=nru, nonict_h=hu, main_fp=fp))
        print(f"{s}: unions ({time.time()-t0:.0f}s)", flush=True)
    U = pd.DataFrame(out); U.to_csv(OUT / f"unions_{spec}.csv", index=False)
    Sd = pd.DataFrame(sdiag); Sd.to_csv(OUT / f"short_diag_{spec}.csv", index=False)

    q = U.groupby(["smooth", "top", "p_s", "seed"])[["tp", "fp", "n_ref", "nonict_h", "main_fp"]].sum().reset_index()
    q["sens"] = q.tp / q.n_ref; q["fa_day"] = q.fp / q.nonict_h * 24; q["main_fa"] = q.main_fp / q.nonict_h * 24
    Q = q.groupby(["smooth", "top", "p_s"])[["sens", "fa_day", "main_fa"]].mean().reset_index()
    Q["added"] = Q.fa_day - Q.main_fa
    elig = Q[(Q.fa_day <= CAP) & (Q.added <= ADD)]
    lines = [f"# E19b -- short branch on {spec}, fine grid, total cap 25, 4 seeds, 15 non-test\n",
             f"Main-only reference (fine grid, <= 25): {Mn['best']:.3f} @ {Mn['cell']} | val (gate definition) "
             f"{Mn['val']:.3f} | val at the cell {Mn['val_at_cell']:.3f} | subject-mean {Mn['subj']:.3f} @ {Mn['subj_fa']:.1f}\n"]
    if len(elig):
        top_sens = elig.sens.max()
        b = elig[elig.sens == top_sens].sort_values("fa_day").iloc[0]
        adopted = bool(b.sens > Mn["best"])
        lines += ["Best eligible union:", "```",
                  f"main cell {int(b.smooth)}/{b.top}  p_s {b.p_s}  sens {b.sens:.3f}  FA/day {b.fa_day:.2f} "
                  f"(main {b.main_fa:.2f}, added {b.added:.2f})", "```",
                  f"Union {b.sens:.3f} vs main-only {Mn['best']:.3f} -> **{'ADOPTED' if adopted else 'NOT adopted'}** "
                  f"(difference {b.sens - Mn['best']:+.3f} = {(b.sens - Mn['best']) * 94:+.1f} seizures of 94)"]
        E16.ledger("E19b", f"{spec}_main{int(b.smooth)}/{b.top}_p{b.p_s}",
                   dict(best=float(b.sens), cell=(int(b.smooth), float(b.top), round(float(b.fa_day), 2))),
                   dict(strictly_higher=adopted, total_le25=True, added_le3=True),
                   "ADOPTED" if adopted else "NOT adopted")
    else:
        lines.append("No eligible union (total <= 25 and added <= 3) -> **NOT adopted**")
        E16.ledger("E19b", spec, dict(best=0.0, cell=None), {}, "no eligible union")
    lines += ["\n## The 3 short seizures of the selection set (per seed)\n", "```",
              Sd.to_string(index=False) if len(Sd) else "none", "```"]
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / f"SUMMARY_{spec}.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
