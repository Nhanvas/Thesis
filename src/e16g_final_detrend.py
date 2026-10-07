#!/usr/bin/env python
"""
e16g_final_detrend.py -- stage P2, E16g (mechanism-driven fix, proposed 2026-10-07, author approval
required before the run). 15 non-test subjects, 4 seeds, cache only.

Mechanism (E16): under S9 base 84.5 % of the top-2 % non-ictal windows lie in the patient's
top-quartile files; those files rarely contain seizures (8.3 %) and are NOT more often flagged
(0.459 vs 0.459) -> a file-level shift of the latent readout, not more high-amplitude activity.
E16e (S9 minus its +-15 min running median inside each file) moved the whole curve: <= 15 FA/day
0.513 -> 0.614, <= 10 0.423 -> 0.487, subject-mean 0.742 @ 25.7 -> 0.766 @ 22.2, all 4 seeds up,
seizure z 4.72 -> 4.62, but missed G1 at <= 25 (+0.016). E17 then chose the rank ensemble
Eb = C(S9 base) + L + gamma (non-inferior; 0.617 @ 22.8, subject-mean 0.791 @ 24.3).
Drift affects every readout, so the correction belongs on the final scalar.
ARM (one): Eb_dt = Eb minus its centred running median over 451 windows inside each file.
Reference: Eb (current candidate). Same gate as E16 (G1 4-seed mean >= Eb + 0.05 and >= 3/4 seeds
not lower; G2 subject-mean; G3 without chb12; G4 validation; G5 >= 9/15 subjects; M seizure z of the
robust-z-scaled scalar not more than 10 % lower). Reproduction: Eb here must reproduce E17's Eb best
cell value within 0.002, else STOP.
If not adopted: the candidate stays Eb; record the curve at <= 15 / <= 10 as characterisation.
Run:  python src/e16g_final_detrend.py        (estimated 10-25 min CPU, not measured)
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

OUT = ROOT / "results" / "e16g_final_detrend"
E17_EB = 0.617


def main():
    import e1_normal_definition as E1
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, mech = [], []
    for s in E8.SUBJS:
        ctx = PS.subject_context(s)
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            eb = PS.ensemble_scalar(ctx, tag, ("C", "L", "gamma"))
            for kind, v in (("Eb", eb), ("Eb_dt", PS.detrend_file(ctx, eb))):
                for r_ in E1.event_grid(d, v):
                    r_.update(subject=s, score=f"{tag}|{kind}", nonict_h=ctx["nh"]); rows.append(r_)
                zz = E16.rz(v, ctx["ok"])
                mech.append(dict(subject=s, seed=tag, kind=kind, sz_median_z=float(np.nanmedian(zz[ctx["ict_ok"]])),
                                 flag_median_z=float(np.nanmedian(zz[ctx["nonict"] & ctx["fl5"]]))))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)
    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism.csv", index=False)
    med = M.groupby(["kind", "subject"])[["sz_median_z", "flag_median_z"]].mean().groupby("kind").median()
    B, R = E16.summarise(gr, "Eb"), E16.summarise(gr, "Eb_dt")
    lines = ["# E16g -- drift correction of the final ensemble scalar (Eb_dt vs Eb), 4 seeds, 15 non-test\n"]
    if abs(B["best"] - E17_EB) > 0.002:
        lines.append(f"STOP: Eb reproduces {B['best']:.3f}, E17 gave {E17_EB}")
        (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8"); print("\n".join(lines)); sys.exit(1)
    lines += [f"Reproduction of E17 Eb: {B['best']:.3f} (E17 {E17_EB}) OK\n",
              "## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short\n", "```"]
    for k, X in (("Eb", B), ("Eb_dt", R)):
        if X["cell"] is None:
            lines.append(f"{k} never reaches FA/day <= 25"); continue
        lines.append(f"{k:6s} {X['best']:.3f} {X['cell']} | {X['le15']:.3f} | {X['le10']:.3f} | val {X['val']:.3f} | "
                     f"{X['x12']:.3f} | {X['subj']:.3f} @ {X['subj_fa']:.1f} | "
                     f"{', '.join(f'{v:.3f}' for v in X['seeds'].values())} | {X['short']}")
    lines += ["```", "", "```"] + [f"{k:6s} seizure z {med.loc[k, 'sz_median_z']:.2f}  flagged z {med.loc[k, 'flag_median_z']:.2f}"
                                    for k in med.index] + ["```"]
    if R["cell"] is None:
        E16.ledger("E16g", "Eb_dt", dict(best=0.0, cell=None), {}, "NOT adopted"); verdict = "NOT adopted"
    else:
        g, ok_ = E16.gate(R, B, med.loc["Eb_dt", "sz_median_z"], med.loc["Eb", "sz_median_z"])
        verdict = "ADOPTED" if ok_ else "NOT adopted"
        E16.ledger("E16g", "Eb_dt", R, g, verdict)
        lines.append("\n- " + " ".join(f"{k} {'pass' if v else 'FAIL'}" for k, v in g.items() if k != "n_ok")
                     + f" (subjects {g['n_ok']}/15)")
        lines.append("  per subject 4-seed-mean TP (Eb_dt | Eb): " +
                     ", ".join(f"{s_} {R['tp'].get(s_, np.nan):.2f}|{B['tp'][s_]:.2f}" for s_ in B["tp"].index))
    lines.append(f"\n**{verdict}: candidate scalar = {'Eb_dt' if verdict == 'ADOPTED' else 'Eb'}**")
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
