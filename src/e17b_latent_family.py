#!/usr/bin/env python
"""
e17b_latent_family.py -- stage P2, E17b (pre-registered in record 6.3 as the step to run when no
cross-readout combination is non-inferior; that condition holds after E21 stage 2 and E21b).
15 non-test subjects, 4 seeds, cache only, fine top-p grid of E21.

ARM (one): rank ensemble of the latent family at several spatial scales of the same GAE node latent,
each with the E16e correction (minus its +-15 min running median inside each file, on the dumped
windows, exactly as C): {S6_e, S9_e (= C), S12_e, Smean_e}; each -> patient percentile; equal mean.
(L is left out: its graph-mean latent is already the channel mean at the latent level and, being a
patient-level Mahalanobis, has no E16e analogue that E21 tested; adding it would be a second arm.)
Reference: C = E16e alone, cell 5/0.0075 (0.681). Reproduction: S9_e built here must reproduce C
within 0.002 and the same cell, else STOP.
GATE = E17 non-inferiority, unchanged: pooled best >= C - 0.02, subject-mean sensitivity at the cell
>= C's - 0.02, validation (`val`) >= C's - 0.067. CHOICE (E17 rule, before the run): if non-inferior,
the family ensemble becomes the final scalar; otherwise the final scalar stays C.
Descriptive: each member alone (best <= 25, val) and flagged share in the ensemble's top-2 % tail.
Run:  python src/e17b_latent_family.py        (estimated 2-6 min CPU, not measured)
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

OUT = ROOT / "results" / "e17b_latent_family"
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
E1.TOPS = FINE
C_REF = (0.681, (5, 0.0075))
MEMBERS = {"S6e": 6, "S9e": 9, "S12e": 12, "Smean_e": "mean"}


def member(D, wf, k):
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    v = Zc.mean(axis=1) if k == "mean" else -np.sort(-Zc, axis=1)[:, k - 1]
    out = v.copy()
    for f in np.unique(wf):                       # identical to E16.c_scalar("e")
        w = np.flatnonzero(wf == f)
        out[w] = v[w] - pd.Series(v[w]).rolling(451, min_periods=1, center=True).median().values
    return out


def fmt(k, R):
    if R["cell"] is None:
        return f"{k:8s} never reaches FA/day <= 25"
    return (f"{k:8s} {R['best']:.3f} {R['cell']} | {R['le15']:.3f} | {R['le10']:.3f} | val {R['val']:.3f} "
            f"(at cell {R['val_at_cell']:.3f}) | {R['x12']:.3f} | {R['subj']:.3f} @ {R['subj_fa']:.1f} | "
            f"{', '.join(f'{v:.3f}' for v in R['seeds'].values())} | {R['short']}")


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, mech = [], []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s); d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            raw = {k: PS._full(ctx, member(ctx["D"][tag], ctx["wf"], kk)) for k, kk in MEMBERS.items()}
            sc = {"C": E16.rz(raw["S9e"], ctx["ok"])}
            for k in ("S6e", "S12e", "Smean_e"):
                sc[k] = E16.rz(raw[k], ctx["ok"])
            sc["E17b"] = np.mean([PS.pct(v, ctx["ok"]) for v in raw.values()], axis=0)
            for k, v in sc.items():
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=f"{tag}|{k}", nonict_h=ctx["nh"]); rows.append(r_)
                if k in ("C", "E17b"):
                    sm = PS.smoothed(ctx, v, 15)
                    T = (sm > np.nanquantile(sm, 0.98)) & ctx["nonict"]
                    mech.append(dict(subject=s, seed=tag, kind=k,
                                     tail_flagged=float(ctx["fl5"][T].mean()) if T.any() else np.nan))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism.csv", index=False)
    R = {k: E16.summarise(gr, k) for k in ("C", "S6e", "S12e", "Smean_e", "E17b")}
    lines = ["# E17b -- latent-family rank ensemble {S6e, S9e, S12e, Smean_e} vs C (E16e), fine grid, 4 seeds\n"]
    C = R["C"]
    if C["cell"] is None or abs(C["best"] - C_REF[0]) > 0.002 or C["cell"][:2] != C_REF[1]:
        lines.append(f"STOP: S9e reproduces {C['best']:.3f} {C['cell']}, E21 C gave {C_REF}")
        (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8"); print("\n".join(lines)); sys.exit(1)
    lines += [f"Reproduction of E21 C by S9e: {C['best']:.3f} {C['cell']} OK\n",
              "Best <= 25 | <= 15 | <= 10 | val (gate) (val at cell) | no-chb12 | subject-mean @ FP/day | per seed | short\n",
              "```"] + [fmt(k, R[k]) for k in R] + ["```"]
    mm = M.groupby(["kind", "subject"]).tail_flagged.mean().groupby("kind").median()
    lines.append("\nFlagged share in the top-2 % non-ictal tail (median over subjects): "
                 + ", ".join(f"{k} {v:.3f}" for k, v in mm.items()))
    X = R["E17b"]
    if X["cell"] is None:
        ok_ = False; E16.ledger("E17b", "latent family (E16e)", dict(best=0.0, cell=None), {}, "inferior (no cell)")
    else:
        n1 = X["best"] >= C["best"] - 0.02; n2 = X["subj"] >= C["subj"] - 0.02; n3 = X["val"] >= C["val"] - 0.067
        ok_ = n1 and n2 and n3
        E16.ledger("E17b", "latent family (E16e)", X, dict(NI_pooled=n1, NI_subj=n2, NI_val=n3),
                   "non-inferior" if ok_ else "inferior")
        lines.append(f"\n- pooled {X['best']:.3f} vs floor {C['best'] - 0.02:.3f} -> {'pass' if n1 else 'FAIL'}; "
                     f"subject-mean {X['subj']:.3f} vs {C['subj'] - 0.02:.3f} -> {'pass' if n2 else 'FAIL'}; "
                     f"validation {X['val']:.3f} vs {C['val'] - 0.067:.3f} -> {'pass' if n3 else 'FAIL'}")
    lines.append(f"\n**{'non-inferior: final scalar = E17b (latent family), cell ' + str(X['cell']) if ok_ else 'inferior: final scalar = C (E16e), cell ' + str(C['cell'])}**")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
