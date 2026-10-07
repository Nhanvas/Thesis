#!/usr/bin/env python
"""
e21_fine_grid.py -- stage P2, E21 (approved by the author 2026-10-07 with the reviewer's conditions).
15 non-test subjects, 4 seeds, cache only.

Mechanism (record 6.4): the D1 top-p grid {0.05, 0.02, 0.01, 0.005, 0.002, 0.001} moves FA/day in
factor-2 steps, so arms that lower FA cannot spend the 25 FA/day budget (E16e best cell 22.3, Eb_h 15.2).
Fix of the construction (threshold calibration, the form's literature focus): add 0.03, 0.015, 0.0075
to the grid for EVERY score, reference and arms alike. NOTE FOR THE LEDGER: this change was decided
after seeing E16e and Eb_h.
GATES UNCHANGED. Stage 1 (vs S9 base): G1 4-seed mean best <= 25 >= S9 + 0.05 and >= 3/4 seeds not
lower; G2 subject-mean; G3 without chb12; G4 validation; G5 >= 9/15 subjects; M seizure z not > 10 %
lower. Arms re-scored in one pass: E16e, E16b, E15 (TTA 2,000 steps; gated only if all 4 seeds are
adapted, else characterisation). C' = the passing arm with the highest pooled best (exact ties within
0.005: lower FA/day); S9 base if none passes.
Stage 2 (E17 construction with C'): Ea = C'+recon+gamma, Eb = C'+L+gamma, Ec = C'+L, non-inferiority
vs C' (pooled >= -0.02, subject-mean >= -0.02, validation >= -0.067). Choice: highest pooled best;
within 0.02 prefer a combination containing gamma; exact ties (0.005) -> lower FA/day.
(If C' = E16e, stage-2 Eb is Eb_h of E16g; it is counted once.)
Descriptive: FA/day, <= 15, <= 10, subject-mean. Diagnostics: per-component drift (S9 base, L, gamma,
recon): per-file median IQR / patient MAD and the share of the final scalar's top-2 % non-ictal
windows inside that component's top-quartile files; per subject, flagged share in top vs other files
(check of the 0.459 / 0.459 coincidence) and share of top-quartile files with a seizure vs share of
all files with a seizure (check of 8.3 %).
Run:  python src/e21_fine_grid.py        (estimated 30-70 min CPU, not measured)
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
import e11_tail_anatomy as E11         # noqa: E402

OUT = ROOT / "results" / "e21_fine_grid"
FINE = [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001]
E1.TOPS = FINE                          # every score, reference and arms alike
NOTE = "grid changed after seeing E16e and Eb_h"


def tta_d(s, tag):
    for folder in ("pernode", "pernode_s23"):
        f = ROOT / "results" / "e15_patient_adaptation" / folder / f"{s}.npz"
        if f.exists():
            z = np.load(f)
            if f"{tag}_s2000_d" in z.files:
                return z[f"{tag}_s2000_d"].astype(np.float64)
    return None


def grid_rows(ctx, d, v, label, tag, rows):
    for r_ in E1.event_grid(d, v):
        r_.update(subject=ctx["s"], score=f"{tag}|{label}", nonict_h=ctx["nh"]); rows.append(r_)


def frame(rows):
    gr = pd.DataFrame(rows)
    gr["kind"] = gr.score.str.split("|").str[1]; gr["seed"] = gr.score.str.split("|").str[0]
    return gr


def fmt(k, R):
    if R["cell"] is None:
        return f"{k:7s} never reaches FA/day <= 25"
    return (f"{k:7s} {R['best']:.3f} {R['cell']} | {R['le15']:.3f} | {R['le10']:.3f} | val {R['val']:.3f} | "
            f"{R['x12']:.3f} | {R['subj']:.3f} @ {R['subj_fa']:.1f} | "
            f"{', '.join(f'{v:.3f}' for v in R['seeds'].values())} | {R['short']}")


def pick(cands, res, prefer=None):
    top = max(res[k]["best"] for k in cands)
    pool = [k for k in cands if top - res[k]["best"] <= 0.02]
    if prefer:
        pref = [k for k in pool if prefer(k)]
        pool = pref or [k for k in pool if res[k]["best"] == top]
    best_v = max(res[k]["best"] for k in pool)
    tied = [k for k in pool if best_v - res[k]["best"] <= 0.005]
    return min(tied, key=lambda k: res[k]["cell"][2])


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    ctxs, rows1, mech1, tta_seeds = {}, [], [], set()
    for s in E8.SUBJS:                                              # stage 1
        ctx = PS.subject_context(s); ctxs[s] = ctx
        d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            sc = {"S9base": E16.c_scalar("S9base", ctx["D"][tag], ctx["Z"][tag], ctx["wf"])[0],
                  "E16e": E16.c_scalar("e", ctx["D"][tag], ctx["Z"][tag], ctx["wf"])[0],
                  "E16b": E16.c_scalar("b", ctx["D"][tag], ctx["Z"][tag], ctx["wf"])[0]}
            dt = tta_d(s, tag)
            if dt is not None:
                sc["E15tta"] = E16.s_from_d(dt); tta_seeds.add(tag)
            for k, v in sc.items():
                vv = E16.rz(PS._full(ctx, v), ctx["ok"])
                grid_rows(ctx, d, vv, k, tag, rows1)
                mech1.append(dict(subject=s, seed=tag, kind=k, sz_median_z=float(np.nanmedian(vv[ctx["ict_ok"]]))))
        print(f"{s}: stage 1 ({time.time()-t0:.0f}s)", flush=True)
    g1 = frame(rows1); g1.to_csv(OUT / "stage1_grid_per_subject.csv", index=False)
    med1 = pd.DataFrame(mech1).groupby(["kind", "subject"]).sz_median_z.mean().groupby("kind").median()
    B = E16.summarise(g1, "S9base")
    lines = [f"# E21 -- finer top-p grid {FINE}, gates unchanged, 4 seeds, 15 non-test\n",
             f"Ledger note: {NOTE}.\n", "## Stage 1 (reference S9 base)\n",
             "Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short\n", "```"]
    res1 = {"S9base": B}
    arms = ["E16e", "E16b"] + (["E15tta"] if "E15tta" in set(g1.kind) else [])
    for k in ["S9base"] + arms:
        res1[k] = B if k == "S9base" else E16.summarise(g1, k)
        lines.append(fmt(k, res1[k]))
    lines.append("```")
    passing = []
    for k in arms:
        R = res1[k]
        gated = not (k == "E15tta" and len(tta_seeds) < 4)
        if R["cell"] is None:
            E16.ledger("E21-1", k, dict(best=0.0, cell=None), {}, f"no cell; {NOTE}"); continue
        if not gated:
            lines.append(f"- {k}: {len(tta_seeds)} seeds adapted -> characterisation only")
            E16.ledger("E21-1", k, R, {}, f"characterisation ({len(tta_seeds)} seeds); {NOTE}"); continue
        g, ok_ = E16.gate(R, B, med1[k], med1["S9base"])
        E16.ledger("E21-1", k, R, g, ("ADOPTED" if ok_ else "NOT adopted") + f"; {NOTE}")
        lines.append(f"- {k}: " + " ".join(f"{a} {'pass' if v else 'FAIL'}" for a, v in g.items() if a != "n_ok")
                     + f" (subjects {g['n_ok']}/15) -> **{'ADOPTED' if ok_ else 'NOT adopted'}**")
        if ok_:
            passing.append(k)
    cprime = pick(passing, res1) if passing else "S9base"
    c_arm = {"S9base": "S9base", "E16e": "e", "E16b": "b"}.get(cprime)
    if c_arm is None:
        raise SystemExit("C' = E15tta: stage 2 needs the adapted node distances wired into p2_scalars; stop and report")
    lines.append(f"\n**C' = {cprime}**\n")

    rows2, comp = [], []                                            # stage 2
    combos = {"Ea": ("C", "recon", "gamma"), "Eb": ("C", "L", "gamma"), "Ec": ("C", "L")}
    diag = []
    for s in E8.SUBJS:
        ctx = ctxs[s]; d = E8.d_for_grid(ctx["z"])
        for tag in PS.TAGS:
            C = E16.rz(PS.readout(ctx, tag, "C", c_arm=c_arm), ctx["ok"])
            grid_rows(ctx, d, C, "C", tag, rows2)
            for k, parts in combos.items():
                grid_rows(ctx, d, PS.ensemble_scalar(ctx, tag, parts, c_arm=c_arm), k, tag, rows2)
            # diagnostics on the base readouts (drift per component)
            eb = PS.ensemble_scalar(ctx, tag, combos["Eb"], c_arm=c_arm)
            sm = PS.smoothed(ctx, eb, 15)
            T = (sm > np.nanquantile(sm, 0.98)) & ctx["nonict"]
            for comp_name in ("S9base", "L", "gamma", "recon"):
                v = PS.readout(ctx, tag, "C" if comp_name == "S9base" else comp_name)
                ni = ctx["nonict"]
                meds = pd.Series(v[ni]).groupby(ctx["fidx"][ni]).median()
                mad = np.median(np.abs(v[ni] - np.median(v[ni]))) + 1e-9
                topf = meds[meds >= meds.quantile(0.75)].index
                in_top = np.isin(ctx["fidx"], topf)
                sz_files = np.unique(ctx["fidx"][ctx["ict"]]); allf = np.unique(ctx["fidx"])
                diag.append(dict(subject=s, seed=tag, component=comp_name,
                                 drift_iqr_over_mad=float((meds.quantile(.75) - meds.quantile(.25)) / mad),
                                 final_tail_in_top_files=float(in_top[T].mean()) if T.any() else np.nan,
                                 flag_top=float(ctx["fl5"][ni & in_top].mean()) if (ni & in_top).any() else np.nan,
                                 flag_other=float(ctx["fl5"][ni & ~in_top].mean()) if (ni & ~in_top).any() else np.nan,
                                 top_files_with_sz=float(np.isin(topf, sz_files).mean()) if len(topf) else np.nan,
                                 all_files_with_sz=float(np.isin(allf, sz_files).mean()),
                                 n_files=len(allf)))
        print(f"{s}: stage 2 ({time.time()-t0:.0f}s)", flush=True)
    g2 = frame(rows2); g2.to_csv(OUT / "stage2_grid_per_subject.csv", index=False)
    Dg = pd.DataFrame(diag); Dg.to_csv(OUT / "diagnostics_per_subject_seed.csv", index=False)
    RC = E16.summarise(g2, "C")
    res2 = {"C": RC}
    lines += [f"## Stage 2 (rank ensembles with C' = {cprime})\n", "```", fmt("C", RC)]
    for k in combos:
        res2[k] = E16.summarise(g2, k); lines.append(fmt(k, res2[k]) + f"   {'+'.join(combos[k])}")
    lines.append("```")
    ni_pass = []
    for k in combos:
        R = res2[k]
        if R["cell"] is None:
            E16.ledger("E21-2", k, dict(best=0.0, cell=None), {}, f"no cell; {NOTE}"); continue
        n1 = R["best"] >= RC["best"] - 0.02; n2 = R["subj"] >= RC["subj"] - 0.02; n3 = R["val"] >= RC["val"] - 0.067
        ok_ = n1 and n2 and n3
        E16.ledger("E21-2", f"{k}(C={cprime})", R, dict(NI_pooled=n1, NI_subj=n2, NI_val=n3),
                   ("non-inferior" if ok_ else "inferior") + f"; {NOTE}")
        lines.append(f"- {k}: pooled {'pass' if n1 else 'FAIL'}, subject-mean {'pass' if n2 else 'FAIL'}, "
                     f"validation {'pass' if n3 else 'FAIL'} (val {R['val']:.3f} vs floor {RC['val'] - 0.067:.3f})")
        if ok_:
            ni_pass.append(k)
    final = pick(ni_pass, res2, prefer=lambda k: "gamma" in combos[k]) if ni_pass else "C"
    lines.append(f"\n**Final scalar after E21: {final} with C' = {cprime}, D1 cell {res2[final]['cell']}**")
    lines += ["\n## Diagnostics (median over subjects of seed means)\n", "```"]
    for cname, gq in Dg.groupby("component"):
        m = gq.drop(columns=["seed", "component"]).groupby("subject").mean().median()
        lines.append(f"{cname:7s} drift IQR/MAD {m.drift_iqr_over_mad:.3f} | final-tail share in its top files "
                     f"{m.final_tail_in_top_files:.3f} | flag top/other {m.flag_top:.3f}/{m.flag_other:.3f} | "
                     f"top files with seizure {m.top_files_with_sz:.3f} vs all files {m.all_files_with_sz:.3f}")
    lines += ["```", "\nPer subject (S9base, seed mean): flag share top/other, files with seizure top/all\n", "```"]
    q = Dg[Dg.component == "S9base"].drop(columns=["seed", "component"]).groupby("subject").mean()
    lines += [f"{s_}  {r.flag_top:.3f}/{r.flag_other:.3f}   {r.top_files_with_sz:.3f}/{r.all_files_with_sz:.3f}  files {r.n_files:.0f}"
              for s_, r in q.iterrows()]
    lines += ["```", f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
