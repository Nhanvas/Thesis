#!/usr/bin/env python
"""
e21b_gamma_detrend.py -- stage P2, E21b (proposed by the author 2026-10-07 from the E21 diagnostics).
15 non-test subjects, 4 seeds, cache only, fine top-p grid of E21.

Mechanism (E21 diagnostics, median over subjects): gamma drifts most of all readouts (per-file median
IQR / patient MAD 1.54 vs 0.69-0.85 for L, S9, recon); 57.5 % of the final ensemble's top-2 % non-ictal
windows sit in gamma's top-quartile files (0.18-0.19 for the other readouts); gamma's top files carry
more flagged windows (0.660 vs 0.395). In E21 stage 2 the rank ensemble Eb = C + L + gamma (C = E16e)
lost to C alone at <= 25 FA/day (0.636 vs 0.681). Hypothesis: the file-level drift of gamma, not gamma
itself, is what drags the ensemble; correcting gamma the same way E16e corrected S9 restores it.
ARM (one): E21b = percentile mean of C (E16e), L, gamma_dt (gamma minus its +-15 min running median
inside each file; p2_scalars readout "gamma_dt").
Reference: C = E16e alone (the E21 final scalar). GATE = E17 stage-2 non-inferiority, unchanged:
pooled best >= C - 0.02, subject-mean sensitivity at the cell >= C's - 0.02, validation (`val`, the gate
definition) >= C's - 0.067. CHOICE (E17 rule, written before the run): if E21b is non-inferior it
becomes the final scalar (it restores the ensemble of readouts; the rule prefers a combination with
gamma within 0.02); otherwise the final scalar stays C.
Reproduction: C must reproduce E21 (0.681 @ cell 5/0.0075) within 0.002, else STOP.
Mechanism reported (not gated): share of the ensemble's top-2 % non-ictal windows inside gamma's
top-quartile files (raw gamma), for Eb (C+L+gamma) and E21b; flagged share in that tail.
Run:  python src/e21b_gamma_detrend.py        (estimated 10-25 min CPU, not measured)
"""
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

OUT = ROOT / "results" / "e21b_gamma_detrend"
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
E1.TOPS = FINE
E21_C = (0.681, (5, 0.0075))


def fmt(k, R):
    if R["cell"] is None:
        return f"{k:7s} never reaches FA/day <= 25"
    return (f"{k:7s} {R['best']:.3f} {R['cell']} | {R['le15']:.3f} | {R['le10']:.3f} | val {R['val']:.3f} "
            f"(at cell {R['val_at_cell']:.3f}) | {R['x12']:.3f} | {R['subj']:.3f} @ {R['subj_fa']:.1f} | "
            f"{', '.join(f'{v:.3f}' for v in R['seeds'].values())} | {R['short']}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, mech = [], []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s); d = E8.d_for_grid(ctx["z"])
        g_raw = PS.readout(ctx, "clean_seed42", "gamma")
        ni = ctx["nonict"]
        meds = pd.Series(g_raw[ni]).groupby(ctx["fidx"][ni]).median()
        in_top = np.isin(ctx["fidx"], meds[meds >= meds.quantile(0.75)].index)
        for tag in PS.TAGS:
            sc = {"C": E16.rz(PS.readout(ctx, tag, "C", c_arm="e"), ctx["ok"]),
                  "Eb": PS.ensemble_scalar(ctx, tag, ("C", "L", "gamma"), c_arm="e"),
                  "E21b": PS.ensemble_scalar(ctx, tag, ("C", "L", "gamma_dt"), c_arm="e")}
            for k, v in sc.items():
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=f"{tag}|{k}", nonict_h=ctx["nh"]); rows.append(r_)
                sm = PS.smoothed(ctx, v, 15)
                T = (sm > np.nanquantile(sm, 0.98)) & ni
                mech.append(dict(subject=s, seed=tag, kind=k,
                                 tail_in_gamma_top_files=float(in_top[T].mean()) if T.any() else np.nan,
                                 tail_flagged=float(ctx["fl5"][T].mean()) if T.any() else np.nan))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism.csv", index=False)
    R = {k: E16.summarise(gr, k) for k in ("C", "Eb", "E21b")}
    lines = ["# E21b -- rank ensemble C(E16e) + L + gamma_dt vs C alone, fine grid, 4 seeds, 15 non-test\n"]
    if abs(R["C"]["best"] - E21_C[0]) > 0.002 or R["C"]["cell"][:2] != E21_C[1]:
        lines.append(f"STOP: C reproduces {R['C']['best']:.3f} {R['C']['cell']}, E21 gave {E21_C}")
        (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8"); print("\n".join(lines)); sys.exit(1)
    lines += [f"Reproduction of E21 C: {R['C']['best']:.3f} {R['C']['cell']} OK\n",
              "Best <= 25 | <= 15 | <= 10 | val (gate) (val at cell) | no-chb12 | subject-mean @ FP/day | per seed | short\n",
              "```"] + [fmt(k, R[k]) for k in R] + ["```"]
    mm = M.groupby(["kind", "subject"])[["tail_in_gamma_top_files", "tail_flagged"]].mean().groupby("kind").median()
    lines += ["\nMechanism (median over subjects): share of the top-2 % non-ictal tail in gamma's top-quartile "
              "files | flagged share in that tail\n", "```"]
    lines += [f"{k:5s} {mm.loc[k, 'tail_in_gamma_top_files']:.3f} | {mm.loc[k, 'tail_flagged']:.3f}" for k in mm.index]
    lines.append("```")
    X, C = R["E21b"], R["C"]
    if X["cell"] is None:
        verdict = "inferior (no cell)"; ok_ = False
        E16.ledger("E21b", "C+L+gamma_dt", dict(best=0.0, cell=None), {}, verdict)
    else:
        n1 = X["best"] >= C["best"] - 0.02; n2 = X["subj"] >= C["subj"] - 0.02; n3 = X["val"] >= C["val"] - 0.067
        ok_ = n1 and n2 and n3
        verdict = "non-inferior" if ok_ else "inferior"
        E16.ledger("E21b", "C+L+gamma_dt", X, dict(NI_pooled=n1, NI_subj=n2, NI_val=n3), verdict)
        lines.append(f"\n- pooled {X['best']:.3f} vs floor {C['best'] - 0.02:.3f} -> {'pass' if n1 else 'FAIL'}; "
                     f"subject-mean {X['subj']:.3f} vs {C['subj'] - 0.02:.3f} -> {'pass' if n2 else 'FAIL'}; "
                     f"validation {X['val']:.3f} vs {C['val'] - 0.067:.3f} -> {'pass' if n3 else 'FAIL'}")
    lines.append(f"\n**{verdict}: final scalar = {'E21b (C+L+gamma_dt), cell ' + str(X['cell']) if ok_ else 'C (E16e), cell ' + str(C['cell'])}**")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
