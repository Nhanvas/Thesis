#!/usr/bin/env python
"""
e5_patient_density.py -- is a window anomalous relative to the SAME patient's own recording?

Rationale (measured, not assumed): high-amplitude non-seizure windows are ~40 % of each
patient's recording, seizures ~0.2-0.7 %. A density model fitted on the patient's own windows
should therefore treat that patient's recurring artifacts as common and its seizures as rare.
E1 fitted "normal" on OTHER patients, where a given patient's artifacts are not represented.

Label-free by construction: the model is fitted on every window of the patient being scored
(no label, no other patient), exactly the transductive setting the application already uses for
its per-subject statistics (whole-recording fit).

Fixed before the run (one configuration):
  GaussianMixture(k = 8, full covariance, reg_covar 1e-3, random_state 0), fitted on up to
  20,000 randomly drawn non-signal-loss windows of the patient; score = -log-likelihood.
  Reference A0 = E1 'clean', k = 8 (results/e1_normal_definition).
GATE:
  K1  best pooled sensitivity with FA/day <= 25:  E5 >= A0 + 0.10   (A0 = 0.340)
  K2  mean AUROC(seizure vs flagged): E5 >= A0 + 0.08, and E5 > A0 in >= 10 of 15 subjects
  K3  mean AUROC(seizure vs clean background): E5 >= A0 - 0.03
  E5 PASSES only if K1, K2 and K3 all pass.
Known bias, stated before the run: for the 12 training subjects the cache holds the seizure
files plus 2 random files, so seizure prevalence there is 1.5-3.7 % instead of ~0.2-0.7 %;
this makes seizures look LESS rare and works AGAINST E5. The 3 validation subjects (all files)
are reported separately as descriptive. k = 32 is descriptive.
TEST GUARD inherited from e1_normal_definition. Writes only results/e5_patient_density/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1  # noqa: E402

OUT = ROOT / "results" / "e5_patient_density"
OUT.mkdir(parents=True, exist_ok=True)
E1_DIR = ROOT / "results" / "e1_normal_definition"
VAL = ["chb10", "chb11", "chb22"]
FIT_MAX = 20000
RNG = np.random.default_rng(0)


def main():
    t0 = time.time()
    ref_ps = pd.read_csv(E1_DIR / "per_subject_auroc.csv")
    ref_ps = ref_ps[(ref_ps.k == 8) & (ref_ps.variant == "clean")].set_index("subject")
    ref_pool = pd.read_csv(E1_DIR / "event_grid_pooled.csv")
    ref_pool = ref_pool[(ref_pool.k == 8) & (ref_pool.variant == "clean")]
    ref_grid = pd.read_csv(E1_DIR / "event_grid_per_subject.csv")
    ref_grid = ref_grid[(ref_grid.k == 8) & (ref_grid.variant == "clean")]

    data = {s: E1.load(s) for s in E1.SUBJS}
    per, grid = [], []
    for k in (8, 32):
        for s in E1.SUBJS:
            d = data[s]
            ok = ~d["is_signal_loss"]
            idx = np.flatnonzero(ok)
            if len(idx) > FIT_MAX:
                idx = RNG.choice(idx, FIT_MAX, replace=False)
            g = GaussianMixture(n_components=k, covariance_type="full", reg_covar=1e-3,
                                max_iter=300, random_state=0).fit(d["X"][idx])
            score = -g.score_samples(d["X"])
            ict = d["is_ictal"] & ok
            base = ~d["is_ictal"] & ~d["is_buffer"] & ok
            flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
            perm = RNG.permutation(ict[ok])
            per.append(dict(k=k, subject=s, sz_flag=E1.auc(score, ict, flag),
                            sz_bg=E1.auc(score, ict, bg), flag_bg=E1.auc(score, flag, bg),
                            null=E1.auc(score[ok], perm, ~perm),
                            A0_sz_flag=float(ref_ps.loc[s, "auc_sz_vs_flagged"]),
                            A0_sz_bg=float(ref_ps.loc[s, "auc_sz_vs_bg"]),
                            ictal_share=float(ict.sum() / ok.sum())))
            nh = float((~d["is_ictal"] & ok).sum()) * E1.WIN / 3600
            for r in E1.event_grid(d, score):
                r.update(k=k, subject=s, nonict_h=nh); grid.append(r)
            print(f"k={k} {s}: sz/flag {per[-1]['sz_flag']:.3f} (A0 {per[-1]['A0_sz_flag']:.3f}) "
                  f"sz/bg {per[-1]['sz_bg']:.3f} ({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per)
    gr = pd.DataFrame(grid)
    ps.to_csv(OUT / "per_subject.csv", index=False)
    gr.to_csv(OUT / "event_grid_per_subject.csv", index=False)

    def pool(df, keys):
        p = df.groupby(keys)[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref
        p["fa_day"] = p.fp / p.nonict_h * 24
        return p

    pooled = pool(gr, ["k", "smooth", "top"])
    pooled.to_csv(OUT / "event_grid_pooled.csv", index=False)

    def best(p, cap):
        q = p[p.fa_day <= cap]
        return (float(q.sens.max()), q.loc[q.sens.idxmax()][["smooth", "top", "tp", "fp", "fa_day"]].to_dict()) \
            if len(q) else (0.0, None)

    lines = ["# E5 -- per-patient (transductive, label-free) density, k = 8 gated\n"]
    for k in (8, 32):
        a = ps[ps.k == k].set_index("subject")
        dflag = a.sz_flag - a.A0_sz_flag
        b5, r5 = best(pooled[pooled.k == k], 25)
        bA, rA = best(ref_pool, 25)
        k1 = b5 >= bA + 0.10
        k2 = dflag.mean() >= 0.08 and (dflag > 0).sum() >= 10
        k3 = a.sz_bg.mean() >= a.A0_sz_bg.mean() - 0.03
        vp = pool(gr[(gr.k == k) & gr.subject.isin(VAL)], ["smooth", "top"])
        vA = pool(ref_grid[ref_grid.subject.isin(VAL)], ["smooth", "top"])
        tag = "PRIMARY (gated)" if k == 8 else "descriptive"
        lines += [f"## k = {k} -- {tag}\n", "```",
                  a[["sz_flag", "A0_sz_flag", "sz_bg", "A0_sz_bg", "flag_bg", "null", "ictal_share"]]
                  .round(4).to_string(), "```",
                  f"- K1: best sens at FA/day <= 25: E5 {b5:.3f} {r5} | A0 {bA:.3f} {rA} -> {'PASS' if k1 else 'FAIL'}",
                  f"- K2: mean diff sz/flag {dflag.mean():+.4f}, improved {(dflag > 0).sum()}/15 -> {'PASS' if k2 else 'FAIL'}",
                  f"- K3: sz/bg E5 {a.sz_bg.mean():.4f} vs A0 {a.A0_sz_bg.mean():.4f} -> {'PASS' if k3 else 'FAIL'}",
                  f"- (info) best at <= 15: E5 {best(pooled[pooled.k == k], 15)[0]:.3f} | A0 {best(ref_pool, 15)[0]:.3f}",
                  f"- (descriptive, validation subjects only, all files) best sens at FA/day <= 25: "
                  f"E5 {best(vp, 25)[0]:.3f} {best(vp, 25)[1]} | A0 {best(vA, 25)[0]:.3f}"]
        if k == 8:
            lines.append(f"\n**E5 VERDICT: {'PASS' if (k1 and k2 and k3) else 'FAIL'}**\n")
    lines += ["## Pooled event grid\n", "```", pooled.round(4).to_string(index=False), "```",
              f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:60]))


if __name__ == "__main__":
    main()
