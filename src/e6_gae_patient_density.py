#!/usr/bin/env python
"""
e6_gae_patient_density.py -- E5's per-patient (transductive, label-free) density, applied to
the REAL GAE outputs dumped by e6_dump_gae.py. Same 15 subjects, files, windows, threshold
detector and SzCORE scoring as E1-E5.

Scores (all fitted per patient on every non-signal-loss window of that patient, no label):
  G0  the locked rlg ensemble as the application builds it: LedoitWolf Mahalanobis on the
      16-d graph-mean latent + robust-z of recon, latent, gamma; equal weights.
  G1  as G0, but the latent readout is a GaussianMixture (k = 8, full) negative
      log-likelihood instead of the single-Gaussian Mahalanobis. One readout changed.
  G2  one GaussianMixture (k = 8) on the joint per-window GAE output vector
      [latent 16, log recon, gamma, log per-node recon 18 if available], robust-standardised.
GATE (event level only, fixed before the run):
  M1  best pooled sensitivity with FA/day <= 25 over the E1 detector grid: Gx >= G0 + 0.10
  M2  on the 3 validation subjects (all files): Gx best sensitivity with FA/day <= 25 >= G0's
  A candidate passes if M1 and M2 pass. If both pass, the one with the higher M1 value is
  carried forward. The carried-forward score and its detector cell (smooth, top = best M1 cell)
  are then frozen for the one-shot test run.
Known bias: training subjects' clean windows were seen by the GAE in training (lower recon
error there -> fewer false alarms for every score alike); the seizure and flagged windows were
never seen. Training-subject caches are seizure-enriched (works against density scores).
TEST GUARD inherited. Writes only results/e6_gae_patient_density/.
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.covariance import LedoitWolf
from sklearn.mixture import GaussianMixture

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import e1_normal_definition as E1  # noqa: E402
import ensemble_recipe as ER       # noqa: E402

DUMP = ROOT / "results" / "e6_gae_dump"
OUT = ROOT / "results" / "e6_gae_patient_density"
OUT.mkdir(parents=True, exist_ok=True)
VAL = ["chb10", "chb11", "chb22"]
FIT_MAX = 20000
RNG = np.random.default_rng(0)


def med_mad(x):
    m = float(np.median(x)); return m, float(np.median(np.abs(x - m))) + 1e-9


def rz(x, ok):
    m, s = med_mad(x[ok]); return (x - m) / s


def gmm_nll(V, ok):
    idx = np.flatnonzero(ok)
    if len(idx) > FIT_MAX:
        idx = RNG.choice(idx, FIT_MAX, replace=False)
    g = GaussianMixture(n_components=8, covariance_type="full", reg_covar=1e-3,
                        max_iter=300, random_state=0).fit(V[idx])
    return -g.score_samples(V)


def robust_std(V, ok):
    c = np.median(V[ok], axis=0)
    s = np.subtract(*np.percentile(V[ok], [75, 25], axis=0)); s[s < 1e-9] = 1.0
    return np.clip((V - c) / s, -10, 10)


def main():
    t0 = time.time()
    per, grid = [], []
    for s in E1.SUBJS:
        d = E1.load(s)
        z = np.load(DUMP / f"{s}.npz")
        gz, zr_raw, zg_raw, pn = z["graph_z"], z["zrecon_raw"], z["zgamma_raw"], z["pernode"]
        if len(zr_raw) != len(d["is_ictal"]):
            raise SystemExit(f"{s}: dump {len(zr_raw)} windows vs cache {len(d['is_ictal'])}")
        ok = ~d["is_signal_loss"]
        zr, zg = rz(zr_raw, ok), rz(zg_raw, ok)
        lw = LedoitWolf().fit(gz[ok])
        zl0 = rz(lw.mahalanobis(gz), ok)
        G0 = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl0, "zgamma": zg}, ER.CANDIDATES["rlg"])
        zl1 = rz(gmm_nll(gz, ok), ok)
        G1 = ER.build_ensemble_subset({"zrecon": zr, "zlatent": zl1, "zgamma": zg}, ER.CANDIDATES["rlg"])
        parts = [gz, np.log(np.maximum(zr_raw, 1e-12))[:, None], zg_raw[:, None]]
        has_pn = not np.isnan(pn).all()
        if has_pn:
            parts.append(np.log(np.maximum(pn, 1e-12)))
        G2 = gmm_nll(robust_std(np.hstack(parts), ok), ok)
        ict = d["is_ictal"] & ok
        base = ~d["is_ictal"] & ~d["is_buffer"] & ok
        flag, bg = base & d["is_artifact"], base & ~d["is_artifact"]
        nh = float((~d["is_ictal"] & ok).sum()) * E1.WIN / 3600
        row = dict(subject=s, pernode=has_pn)
        for name, sc in (("G0", G0), ("G1", G1), ("G2", G2)):
            sc = np.asarray(sc, dtype=float)
            row[f"{name}_sz_flag"] = E1.auc(sc, ict, flag)
            row[f"{name}_sz_bg"] = E1.auc(sc, ict, bg)
            for r in E1.event_grid(d, sc):
                r.update(subject=s, score=name, nonict_h=nh); grid.append(r)
        per.append(row)
        print(f"{s}: sz/flag G0 {row['G0_sz_flag']:.3f} G1 {row['G1_sz_flag']:.3f} G2 {row['G2_sz_flag']:.3f} "
              f"({time.time()-t0:.0f}s)", flush=True)

    ps = pd.DataFrame(per).set_index("subject")
    gr = pd.DataFrame(grid)
    ps.to_csv(OUT / "per_subject.csv")
    gr.to_csv(OUT / "event_grid_per_subject.csv", index=False)

    def pool(df, keys):
        p = df.groupby(keys)[["tp", "fp", "n_ref", "nonict_h"]].sum().reset_index()
        p["sens"] = p.tp / p.n_ref; p["fa_day"] = p.fp / p.nonict_h * 24
        return p

    pooled = pool(gr, ["score", "smooth", "top"]); pooled.to_csv(OUT / "event_grid_pooled.csv", index=False)
    valp = pool(gr[gr.subject.isin(VAL)], ["score", "smooth", "top"])

    def best(p, name, cap=25):
        q = p[(p.score == name) & (p.fa_day <= cap)]
        if not len(q):
            return 0.0, None
        r = q.loc[q.sens.idxmax()]
        return float(r.sens), dict(smooth=int(r.smooth), top=float(r.top), tp=int(r.tp), fp=int(r.fp),
                                   fa_day=round(float(r.fa_day), 2))

    b0, c0 = best(pooled, "G0"); v0, _ = best(valp, "G0")
    lines = ["# E6 -- per-patient density on the real GAE outputs (15 non-test subjects)\n",
             "```", ps.round(4).to_string(), "```\n",
             f"G0 (locked readouts): best sens FA/day<=25 = {b0:.3f} {c0}; validation-only {v0:.3f}"]
    passed = {}
    for name in ("G1", "G2"):
        b, c = best(pooled, name); v, cv = best(valp, name)
        m1, m2 = b >= b0 + 0.10, v >= v0
        lines.append(f"- {name}: best {b:.3f} {c} (M1 {'PASS' if m1 else 'FAIL'}); validation-only {v:.3f} "
                     f"(M2 {'PASS' if m2 else 'FAIL'}); at FA/day<=15: {best(pooled, name, 15)[0]:.3f} "
                     f"vs G0 {best(pooled, 'G0', 15)[0]:.3f}")
        if m1 and m2:
            passed[name] = (b, c)
    if passed:
        win = max(passed, key=lambda k: passed[k][0])
        lines.append(f"\n**E6 VERDICT: PASS -- carried forward: {win}, frozen detector cell {passed[win][1]}**\n")
    else:
        lines.append("\n**E6 VERDICT: FAIL**\n")
    lines += ["## Pooled event grid\n", "```", pooled.round(4).to_string(index=False), "```",
              f"\nElapsed {time.time()-t0:.0f} s."]
    (OUT / "SUMMARY.md").write_text("\n".join(lines), encoding="utf-8")
    print("\n".join(lines[:30]))


if __name__ == "__main__":
    main()
