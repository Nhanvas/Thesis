#!/usr/bin/env python
"""
e12_readout_composition.py -- stage P2, step 2. Cache only, 15 non-test subjects, no training.

Mechanism (E11, results/e11_tail_anatomy/SUMMARY.md, v2 clean, both seeds):
  * the top-2 % tail of the frozen ensemble is 95-96 % flagged (high-amplitude) non-ictal windows;
  * the GAMMA readout owns that tail in 12/15 subjects: mean robust-z 6.2-6.3 in the tail vs 3.29 in
    seizures; seizure-vs-flagged AUROC 0.762;
  * the RECON readout is uninformative against flagged windows: AUROC 0.527-0.534, tail z 1.90 vs
    seizure 0.68-0.71, exceedance 0.34;
  * the v2 LATENT readout (per-patient LedoitWolf Mahalanobis of the mean node latent) separates
    seizures from flagged windows: AUROC 0.966, seizure z 3.15-3.50 vs tail z 1.50-1.59.
  Two of the three equally weighted readouts therefore rank the patient's own high-amplitude states
  above seizures. This is a composition defect, not a weight-tuning question.
Hypothesis: the v2 latent readout alone (L) gives higher event sensitivity at <= 25 FA/day than the
frozen ensemble (E = recon + latent + gamma, E8 V2_LW).
PRIMARY configuration (one, fixed now): L = robust-z of the per-patient LedoitWolf Mahalanobis of the
v2 clean mean node latent, i.e. exactly the zlatent term of E, nothing re-fitted, nothing weighted.
Detector and selection procedure IDENTICAL to E8: D1 grid of e1_normal_definition.event_grid
(per-file moving average, patient's own top-p threshold, merge 90 s, SzCORE), seed-mean per cell,
best cell at FA/day <= 25.
Characterisation only (printed, never used to choose): RL = mean(r, l), LG = mean(l, g),
L2 = mean over seeds 42 and 1 of l (a two-model ensemble of the latent readout).
REPRODUCTION GATE (before anything is read): E must reproduce E8 at the frozen cell (smooth 15,
top 0.02): seed-mean sensitivity 0.489 and FA/day 19.78 within 0.002 / 0.05, else STOP.
ADOPTION GATE (all three):
  G1 best seed-mean pooled sensitivity of L at FA/day <= 25  >=  E's (0.489) + 0.10
  G2 validation-only (chb10, chb11, chb22) value of L  >=  E's validation-only value (0.733)
  G3 per subject, seed-mean TP of L at its chosen cell >= E's at the frozen cell in >= 9 of 15
Mechanism check (reported, required to read a pass as a pass): share of flagged windows among the
non-ictal windows in the top 2 % of the smoothed score falls from E to L.
Reported beside the pooled values: the official SzCORE aggregation (mean over subjects of
sensitivity, precision = tp/(tp+fp), F1 = 2tp/(2tp+fp+fn), FP/day) at the chosen cell.
If adopted -> frozen configuration for at most one disclosed test look (PERF_PHASE_RECORD section 3).
TEST GUARD: E8.SUBJS only.
Run:  python src/e12_readout_composition.py [--smoke]     (estimated 20-60 min CPU, not measured)
"""
import argparse
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain", ROOT / "src" / "dataprep",
          ROOT / "src" / "phaseB", ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import e8_gae_v2_eval as E8            # noqa: E402
import e1_normal_definition as E1      # noqa: E402
import ensemble_recipe as ER           # noqa: E402

TEST = {"chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"}
OUT = ROOT / "results" / "e12_readout_composition"
TAGS = ["clean_seed42", "clean_seed1"]
FROZEN = (15, 0.02)
E8_REF = (0.489, 19.78)


def rz(x, ok):
    m = np.median(x[ok]); s = np.median(np.abs(x[ok] - m)) + 1e-9
    return (x - m) / s


def tail_flag_share(v, z, ok):
    """share of flagged among non-ictal windows in the top 2 % of the 15-window smoothed score."""
    fidx = z["file_idx"].astype(int)
    sm = np.full(len(v), np.nan)
    for f in np.unique(fidx):
        m = fidx == f
        sm[m] = pd.Series(np.where(ok[m], v[m], np.nan)).rolling(15, min_periods=1, center=True).mean().values
    thr = np.nanquantile(sm[ok], 0.98)
    T = (sm > thr) & ~z["is_ictal"].astype(bool) & ~z["is_buffer"].astype(bool) & ok
    return float(z["is_flag5sd"].astype(bool)[T].mean()) if T.any() else np.nan


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true", help="first two subjects only, no gates")
    a = ap.parse_args()
    subs = E8.SUBJS[:2] if a.smoke else E8.SUBJS
    if set(subs) & TEST:
        raise SystemExit("TEST GUARD")
    OUT.mkdir(parents=True, exist_ok=True)
    t0 = time.time()
    rows, mech = [], []
    for s in subs:
        z = np.load(E8.DATA / f"{s}.npz", allow_pickle=True)
        c = np.load(E8.OUT / "scores" / f"{s}.npz")
        d = E8.d_for_grid(z)
        n = len(d["is_ictal"]); ok = ~d["is_signal_loss"]; idx = c["idx"]

        def full(v):
            o = np.full(n, np.nan); o[idx] = v; o[~ok] = np.nanmedian(v); return o

        g = rz(full(z["zgamma_raw"][idx].astype(float)), ok)
        nh = float((~d["is_ictal"] & ok).sum()) * E8.WIN / 3600
        scores, lat_by_seed = {}, []
        for tag in TAGS:
            r = rz(full(c[f"{tag}_recon"]), ok)
            lat = c[f"{tag}_lat"]
            l = rz(full(LedoitWolf().fit(lat).mahalanobis(lat)), ok)
            lat_by_seed.append(l)
            scores[f"{tag}|E"] = np.asarray(ER.build_ensemble_subset(
                {"zrecon": r, "zlatent": l, "zgamma": g}, ER.CANDIDATES["rlg"]), float)
            scores[f"{tag}|L"] = l
            scores[f"{tag}|RL"] = (r + l) / 2
            scores[f"{tag}|LG"] = (l + g) / 2
        scores["seeds42+1|L2"] = np.mean(lat_by_seed, axis=0)
        for name, v in scores.items():
            for r_ in E1.event_grid(d, v):
                r_.update(subject=s, score=name, nonict_h=nh); rows.append(r_)
            mech.append(dict(subject=s, score=name, tail_flag_share=tail_flag_share(v, z, ok)))
        print(f"{s}: done ({time.time()-t0:.0f}s)", flush=True)

    gr = pd.DataFrame(rows); gr.to_csv(OUT / "grid_per_subject.csv", index=False)
    M = pd.DataFrame(mech); M.to_csv(OUT / "mechanism_tail_flag_share.csv", index=False)
    gr["kind"] = gr.score.str.split("|").str[1]
    gr["seed"] = gr.score.str.split("|").str[0]

    def pooled(df):
        p = df.groupby(["kind", "seed", "smooth", "top"])[["tp", "fp", "n_ref", "nonict_h", "tp_short",
                                                           "n_ref_short"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
        return (p.groupby(["kind", "smooth", "top"])
                 .agg(sens=("sens", "mean"), sens_sd=("sens", "std"), fa_day=("fa_day", "mean"),
                      n_seeds=("sens", "size"), tp_short=("tp_short", "mean"), n_short=("n_ref_short", "max"))
                 .reset_index())

    A, V = pooled(gr), pooled(gr[gr.subject.isin(E8.VAL)])
    A.to_csv(OUT / "grid_seed_mean.csv", index=False)

    def best(T, kind, cap=25.0):
        q = T[(T.kind == kind) & (T.fa_day <= cap)]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), (int(r.smooth), float(r.top), round(float(r.fa_day), 2))

    def cell(T, kind, sm, top):
        q = T[(T.kind == kind) & (T.smooth == sm) & (T.top == top)]
        return (float(q.sens.iloc[0]), float(q.fa_day.iloc[0])) if len(q) else (np.nan, np.nan)

    def official(kind, sm, top):
        q = gr[(gr.kind == kind) & (gr.smooth == sm) & (gr.top == top)]
        q = q.groupby(["seed", "subject"])[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        q["sens"] = q.tp / q.n_ref
        q["prec"] = np.where(q.tp + q.fp > 0, q.tp / (q.tp + q.fp).where(q.tp + q.fp > 0, 1), np.nan)
        q["f1"] = 2 * q.tp / (2 * q.tp + q.fp + (q.n_ref - q.tp))
        q["fa_day"] = q.fp / q.nonict_h * 24
        s_ = q.groupby("seed")[["sens", "prec", "f1", "fa_day"]].mean().mean()
        tot = q.groupby("seed")[["tp", "fp", "n_ref"]].sum().mean()
        return dict(subj_sens=s_.sens, subj_prec=s_.prec, subj_f1=s_.f1, subj_fa=s_.fa_day,
                    pooled_prec=tot.tp / (tot.tp + tot.fp), pooled_f1=2 * tot.tp / (2 * tot.tp + tot.fp + tot.n_ref - tot.tp))

    lines = ["# E12 -- readout composition (latent-only L vs frozen ensemble E), 15 non-test subjects\n"]
    e_s, e_fa = cell(A, "E", *FROZEN)
    rep = abs(e_s - E8_REF[0]) <= 0.002 and abs(e_fa - E8_REF[1]) <= 0.05
    lines.append(f"Reproduction of E8 frozen cell: E {e_s:.3f} @ {e_fa:.2f} FA/day vs {E8_REF} -> "
                 f"{'OK' if rep else 'FAILED'}")
    if not rep and not a.smoke:
        (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8"); print("\n".join(lines))
        raise SystemExit("STOP: reproduction failed; nothing below is valid")

    lines += ["\n## Best cell at FA/day <= 25 (pooled, seed mean) | <= 15 | <= 10 | validation-only <= 25\n", "```"]
    res = {}
    for k in ("E", "L", "RL", "LG", "L2"):
        b, cfg = best(A, k); bv, _ = best(V, k)
        res[k] = (b, cfg, bv)
        lines.append(f"{k:3s} {b:.3f} {cfg} | {best(A, k, 15)[0]:.3f} | {best(A, k, 10)[0]:.3f} | val {bv:.3f}"
                     + ("   <- PRIMARY" if k == "L" else "   (reference)" if k == "E" else "   (characterisation)"))
    lines.append("```")

    bL, cL, bvL = res["L"]; bE, _, bvE = res["E"]
    if cL is None:
        lines.append("L never reaches FA/day <= 25 -> NOT adopted")
        adopted = False
    else:
        tpL = gr[(gr.kind == "L") & (gr.smooth == cL[0]) & (gr.top == cL[1])].groupby("subject").tp.mean()
        tpE = gr[(gr.kind == "E") & (gr.smooth == FROZEN[0]) & (gr.top == FROZEN[1])].groupby("subject").tp.mean()
        n_ok = int((tpL >= tpE).sum())
        g1, g2, g3 = bL >= bE + 0.10, bvL >= bvE, n_ok >= 9
        adopted = g1 and g2 and g3 and not a.smoke
        lines += [f"\n- G1 {bL:.3f} vs E {bE:.3f} + 0.10 -> {'pass' if g1 else 'FAIL'}",
                  f"- G2 validation-only {bvL:.3f} vs {bvE:.3f} -> {'pass' if g2 else 'FAIL'}",
                  f"- G3 subjects with TP(L) >= TP(E): {n_ok}/{len(tpE)} -> {'pass' if g3 else 'FAIL'}"]
        mE = M[M.score.str.endswith("|E")].tail_flag_share.median()
        mL = M[M.score.str.endswith("|L")].tail_flag_share.median()
        lines.append(f"- mechanism: flagged share in the top-2 % non-ictal tail, median over subjects and seeds: "
                     f"E {mE:.2f} -> L {mL:.2f}")
        oE, oL = official("E", *FROZEN), official("L", cL[0], cL[1])
        lines += ["\n## Official SzCORE aggregation (mean over subjects) beside pooled\n", "```"]
        for k, o, cfg in (("E", oE, FROZEN), ("L", oL, cL[:2])):
            lines.append(f"{k} cell {cfg}: subject-mean sens {o['subj_sens']:.3f} prec {o['subj_prec']:.3f} "
                         f"F1 {o['subj_f1']:.3f} FP/day {o['subj_fa']:.1f} | pooled prec {o['pooled_prec']:.3f} "
                         f"F1 {o['pooled_f1']:.3f}")
        lines.append("```")
        lines += ["\n## Per subject, seed-mean TP (L at its cell | E frozen) / n_ref\n", "```"]
        nref = gr[(gr.kind == "E") & (gr.smooth == FROZEN[0]) & (gr.top == FROZEN[1])].groupby("subject").n_ref.max()
        for s in tpE.index:
            lines.append(f"{s}  {tpL.get(s, np.nan):4.1f} | {tpE[s]:4.1f} / {int(nref[s])}")
        lines.append("```")
        sh = A[(A.kind == "L") & (A.smooth == cL[0]) & (A.top == cL[1])]
        lines.append(f"\nShort seizures (< 20 s) detected by L at its cell: {float(sh.tp_short.iloc[0]):.1f} "
                     f"of {int(sh.n_short.iloc[0])}")
    lines.append(f"\n**{'ADOPTED' if adopted else 'NOT adopted'}**"
                 + (f" -> FROZEN for one disclosed test look: GAE v2 clean, score L, D1 smooth {cL[0]}, top {cL[1]}"
                    if adopted else ""))
    lines.append(f"\nElapsed {time.time()-t0:.0f} s.")
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines))


if __name__ == "__main__":
    main()
