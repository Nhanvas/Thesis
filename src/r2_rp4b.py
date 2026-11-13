#!/usr/bin/env python
"""
r2_rp4b.py -- research track, stage RP, step RP4, secondary analysis of board R175 (D21-F, 12/11; design fixed in chat
D25-F on 14/11 00:35 and written here before any output of this script; FUTURE_RESEARCH_PLAN.md §12 row 14/11).

QUESTION. Missed seizures are of lower amplitude relative to the patient's own background and shorter (primary RP4
analysis: pooled logistic, patient-cluster bootstrap). Does the association hold WITHIN patients (a seizure that is
smaller / shorter than the patient's other seizures is more often missed), or does it come only from BETWEEN patients
(patients whose seizures are small are hard as a whole)? The between-within decomposition answers this
(Neuhaus & Kalbfleisch 1998, Biometrics 54:638-645, DOI 10.2307/3109770; Begg & Parides 2003, Stat Med 22:2591-2602,
DOI 10.1002/sim.1524).

MODEL (per analysed set; a = log amplitude ratio, d = log duration; bar = mean over the patient's seizures in that set):
    logit P(caught) = b0 + bW_amp (a - a_bar) + bB_amp a_bar + bW_dur (d - d_bar) + bB_dur d_bar
  unpenalized maximum likelihood (sklearn LogisticRegression, penalty None, lbfgs, max_iter 2000 -- the primary
  analysis' estimator, v9_final_hard.logreg_cluster_boot). Inference: patient-cluster bootstrap, B = 2,000,
  numpy RandomState(42) (the primary analysis' B and seed), patients resampled with replacement, patient means recomputed
  in each resample, percentile 95 % intervals; resamples with one class only or a failed fit are skipped and counted.
  Also reported: bW - bB per variable (bootstrap interval; 0 = equal within and between effects, i.e. the pooled
  coefficient of the primary analysis is then a fair summary).
  Robustness: conditional logistic regression stratified by patient (statsmodels ConditionalLogit; estimates the within
  effects only; patients whose seizures are all caught or all missed carry no information and are counted), Wald 95 %.
  No pass / fail threshold (plan P2): coefficients and intervals are reported as they are.

SETS (R175):
  (i)  all 23 patients of RP4 = 8 test + chb24 + 14 Siena (139 seizures), main model of path 2, seeds 1-4, after CPD;
       arm L2f (final, per-patient budget) primary, arm frozen (held-out, 0.5 %) beside.
       Input: results/r2/r1_system/rp/rp4/seizures_per_seed.csv (caught by the E1 rule, amplitude ratio joined from
       results/v9_v1/part1_descriptors.csv by RP4).
  (ii) the R2 per-seizure tables (R175 named R2b; R2b is postponed by R190, so R2 as it is = the path-2 data):
       24 CHB-MIT cases, 185 seizures, 6 models (one seed per fold, own label-free point, after CPD), from
       results/r2/r2_cv/{a,b,c}/model_cmp/seizures.csv; amplitude ratio joined from part1_descriptors.csv.

GATES (STOP on failure, nothing written):
  G1 (i): the pooled coefficients of rp4/logistic.csv (point estimates, 24 rows) are re-fitted from the input table
      with the primary estimator and equal within 1e-6 -- the input is the table the primary analysis used.
  G2 (ii): every seizure joins exactly one descriptor row by (subject, file, onset_s, duration_s); 185 seizures per model;
      caught per model = caught_rerun of results/r2/r2_cv/aggregate/seizures.csv.
  Reported, not gated: caught per (model, case) vs the scorer's tp (rerun, own, localized) of r2_cv/aggregate/per_subject.csv.

OUTPUT: results/r2/r1_system/rp/rp4/bw/ (bw.csv, clogit.csv, checks.csv, gates.json, SUMMARY.md, run_meta.json).
Run:  python src/r2_rp4b.py            (container; minutes)
      python src/r2_rp4b.py --smoke    (B = 50, no output written)
"""
import argparse
import hashlib
import json
import sys
import time
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")

ROOT = Path(__file__).resolve().parents[1]
RP4 = ROOT / "results" / "r2" / "r1_system" / "rp" / "rp4"
R2 = ROOT / "results" / "r2" / "r2_cv"
DESC = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
OUT = RP4 / "bw"
B, RNG = 2000, 42
KEY = ["subject", "file", "onset_s", "duration_s"]


def log(m):
    print(m, flush=True)


# ----------------------------------------------------------------------------- estimators
def _fit(X, y):
    from sklearn.linear_model import LogisticRegression
    return LogisticRegression(penalty=None, solver="lbfgs", max_iter=2000).fit(X, y)


def design_bw(d):
    a, du = np.log(d.amp_ratio.values), np.log(d.duration_s.values)
    g = d.subject.values
    ab = pd.Series(a).groupby(g).transform("mean").values
    db = pd.Series(du).groupby(g).transform("mean").values
    return np.column_stack([a - ab, ab, du - db, db])


NAMES = ["W_amp", "B_amp", "W_dur", "B_dur"]


def bw_fit(d, b=B, seed=RNG):
    d = d[np.isfinite(d.amp_ratio) & (d.amp_ratio > 0) & (d.duration_s > 0)].reset_index(drop=True)
    y = d.caught.values.astype(int)
    out = dict(n=len(d), n_caught=int(y.sum()), n_patients=int(d.subject.nunique()))
    if len(np.unique(y)) < 2:
        return out | {k: np.nan for k in NAMES} | dict(n_boot_ok=0)
    coef = _fit(design_bw(d), y).coef_[0]
    out.update({k: float(v) for k, v in zip(NAMES, coef)})
    subs = d.subject.unique()
    groups = {s: d[d.subject == s] for s in subs}
    rng = np.random.RandomState(seed)
    boots = []
    for _ in range(b):
        pick = rng.choice(subs, size=len(subs), replace=True)
        parts = []
        for i, p in enumerate(pick):
            g = groups[p].copy()
            g["subject"] = f"{p}#{i}"                    # a resampled copy is its own cluster (own mean = same values)
            parts.append(g)
        bd = pd.concat(parts, ignore_index=True)
        yb = bd.caught.values.astype(int)
        if len(np.unique(yb)) < 2:
            continue
        try:
            boots.append(_fit(design_bw(bd), yb).coef_[0])
        except Exception:
            continue
    Bt = np.array(boots)
    out["n_boot_ok"] = len(Bt)
    for j, k in enumerate(NAMES):
        out[f"{k}_lo"], out[f"{k}_hi"] = (float(np.percentile(Bt[:, j], 2.5)), float(np.percentile(Bt[:, j], 97.5))) \
            if len(Bt) else (np.nan, np.nan)
    for v, (w, bb) in {"amp": (0, 1), "dur": (2, 3)}.items():
        out[f"WminusB_{v}"] = float(coef[w] - coef[bb])
        diff = Bt[:, w] - Bt[:, bb] if len(Bt) else np.array([])
        out[f"WminusB_{v}_lo"], out[f"WminusB_{v}_hi"] = (float(np.percentile(diff, 2.5)),
                                                         float(np.percentile(diff, 97.5))) if len(diff) else (np.nan, np.nan)
    return out


def clogit(d):
    from statsmodels.discrete.conditional_models import ConditionalLogit
    d = d[np.isfinite(d.amp_ratio) & (d.amp_ratio > 0) & (d.duration_s > 0)].reset_index(drop=True)
    inf = d.groupby("subject").caught.transform(lambda s: 0 < s.sum() < len(s))
    di = d[inf].reset_index(drop=True)
    out = dict(n=len(d), n_informative_seizures=len(di), n_informative_patients=int(di.subject.nunique()),
               n_patients=int(d.subject.nunique()))
    if di.subject.nunique() < 2:
        return out | dict(W_amp=np.nan, W_dur=np.nan)
    X = np.column_stack([np.log(di.amp_ratio.values), np.log(di.duration_s.values)])
    r = ConditionalLogit(di.caught.values.astype(int), X, groups=di.subject.values).fit(disp=False)
    ci = np.asarray(r.conf_int())
    return out | dict(W_amp=float(r.params[0]), W_amp_lo=float(ci[0, 0]), W_amp_hi=float(ci[0, 1]),
                      W_dur=float(r.params[1]), W_dur_lo=float(ci[1, 0]), W_dur_hi=float(ci[1, 1]))


# ----------------------------------------------------------------------------- inputs and gates
def set_i():
    S = pd.read_csv(RP4 / "seizures_per_seed.csv")
    L = pd.read_csv(RP4 / "logistic.csv")
    groups = {"test": ["test"], "chb24+siena": ["chb24", "siena"], "all23": ["test", "chb24", "siena"]}
    worst = 0.0
    for _, r in L.iterrows():
        d = S[(S.arm == r.arm) & (S.seed == r.seed) & S.set2.isin(groups[r.group])]
        d = d[np.isfinite(d.amp_ratio) & (d.amp_ratio > 0) & (d.duration_s > 0)]
        c = _fit(np.column_stack([np.log(d.amp_ratio), np.log(d.duration_s)]), d.caught.astype(int)).coef_[0]
        worst = max(worst, abs(c[0] - r.coef_amp), abs(c[1] - r.coef_dur))
        if len(d) != r.n:
            raise SystemExit(f"STOP G1: {r.arm} {r.group} seed {r.seed}: n {len(d)} vs {r.n}")
    if worst > 1e-6:
        raise SystemExit(f"STOP G1: pooled coefficients differ from rp4/logistic.csv by {worst:.3g}")
    log(f"G1 PASS: {len(L)} pooled fits re-fitted, max |diff| {worst:.2e}")
    return S[S.set2.isin(["test", "chb24", "siena"])], dict(G1="PASS", G1_rows=len(L), G1_max_abs_diff=float(worst))


def set_ii():
    parts = [pd.read_csv(R2 / p / "model_cmp" / "seizures.csv") for p in ("a", "b", "c")]
    T = pd.concat(parts, ignore_index=True)
    desc = pd.read_csv(DESC)
    dk = desc[KEY + ["amp_ratio"]]
    if dk.duplicated(KEY).any():
        raise SystemExit("STOP G2: duplicated descriptor keys")
    J = T.merge(dk, on=KEY, how="left", validate="many_to_one")
    if J.amp_ratio.isna().any():
        raise SystemExit(f"STOP G2: {int(J.amp_ratio.isna().sum())} seizure rows without a descriptor\n"
                         f"{J[J.amp_ratio.isna()].head(10)}")
    n = J.groupby("model").size()
    if not (n == 185).all() or len(n) != 6:
        raise SystemExit(f"STOP G2: seizures per model {n.to_dict()} (expected 6 x 185)")
    agg = pd.read_csv(R2 / "aggregate" / "seizures.csv").set_index("model")
    c = J.groupby("model").caught.sum()
    bad = {m: (int(c[m]), int(agg.loc[m, "caught_rerun"])) for m in c.index if int(c[m]) != int(agg.loc[m, "caught_rerun"])}
    if bad:
        raise SystemExit(f"STOP G2: caught per model differs from the R2 aggregate {bad}")
    ps = pd.read_csv(R2 / "aggregate" / "per_subject.csv")
    ps = ps[(ps.system == "rerun") & (ps.point == "own") & (ps.stage == "localized")]
    chk = J.groupby(["model", "subject"]).agg(runs=("caught", "size"), caught=("caught", "sum")).reset_index() \
        .merge(ps[["model", "subject", "tp", "n_ref"]], on=["model", "subject"], how="left")
    chk["equal"] = chk.caught == chk.tp
    log(f"G2 PASS: 6 models x 185 seizures joined; caught = R2 aggregate; caught vs scorer tp equal in "
        f"{int(chk.equal.sum())} / {len(chk)} (model, case) rows (reported)")
    return J, chk, dict(G2="PASS", G2_rows_equal_tp=int(chk.equal.sum()), G2_rows=len(chk))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    b = 50 if a.smoke else B
    t0 = time.time()
    S, g1 = set_i()
    J, chk, g2 = set_ii()
    rows, cl = [], []
    for arm in ("L2f", "frozen"):
        for s in (1, 2, 3, 4):
            d = S[(S.arm == arm) & (S.seed == s)]
            r = bw_fit(d, b)
            rows.append(dict(set="all23", arm=arm, seed=s, model="gae (path 2)") | r)
            cl.append(dict(set="all23", arm=arm, seed=s, model="gae (path 2)") | clogit(d))
            log(f"  all23 {arm} seed {s}: W_amp {r['W_amp']:+.2f} [{r.get('W_amp_lo', np.nan):+.2f}, "
                f"{r.get('W_amp_hi', np.nan):+.2f}] B_amp {r['B_amp']:+.2f}  W_dur {r['W_dur']:+.2f} "
                f"[{r.get('W_dur_lo', np.nan):+.2f}, {r.get('W_dur_hi', np.nan):+.2f}] B_dur {r['B_dur']:+.2f}")
    for m in ["gae", "mlp", "if", "svm", "hgb", "cnn"]:
        d = J[J.model == m]
        r = bw_fit(d, b)
        rows.append(dict(set="r2_24cases", arm="final (own point)", seed=np.nan, model=m) | r)
        cl.append(dict(set="r2_24cases", arm="final (own point)", seed=np.nan, model=m) | clogit(d))
        log(f"  R2 {m}: W_amp {r['W_amp']:+.2f} [{r.get('W_amp_lo', np.nan):+.2f}, {r.get('W_amp_hi', np.nan):+.2f}] "
            f"B_amp {r['B_amp']:+.2f}  W_dur {r['W_dur']:+.2f} [{r.get('W_dur_lo', np.nan):+.2f}, "
            f"{r.get('W_dur_hi', np.nan):+.2f}] B_dur {r['B_dur']:+.2f}")
    BW, CL = pd.DataFrame(rows), pd.DataFrame(cl)
    if a.smoke:
        log(f"SMOKE done in {time.time() - t0:.1f} s (nothing written)")
        return
    OUT.mkdir(parents=True, exist_ok=True)
    BW.to_csv(OUT / "bw.csv", index=False)
    CL.to_csv(OUT / "clogit.csv", index=False)
    chk.to_csv(OUT / "checks.csv", index=False)
    (OUT / "gates.json").write_text(json.dumps(g1 | g2, indent=1))
    f = lambda r, k: f"{r[k]:+.2f} [{r[k + '_lo']:+.2f}, {r[k + '_hi']:+.2f}]"  # noqa: E731
    L = ["# RP4 secondary analysis (R175): between-within decomposition of the missed-seizure association\n",
         "Descriptive (no threshold). Coefficients per unit of log amplitude ratio / log duration; positive = more often "
         "caught. W = within patients (deviation from the patient's mean), B = between patients (patient mean); "
         f"patient-cluster bootstrap B = {b}, rng {RNG}, percentile 95 %. Gates: {g1 | g2}.\n",
         "| set | arm / model | seed | n (patients) | W amp | B amp | W dur | B dur | W-B amp | W-B dur | boot ok |",
         "|---|---|---|---|---|---|---|---|---|---|---|"]
    for _, r in BW.iterrows():
        L.append(f"| {r.set} | {r.arm if r.set == 'all23' else r.model} | {'' if pd.isna(r.seed) else int(r.seed)} | "
                 f"{r.n} ({r.n_patients}) | {f(r, 'W_amp')} | {r.B_amp:+.2f} [{r.B_amp_lo:+.2f}, {r.B_amp_hi:+.2f}] | "
                 f"{f(r, 'W_dur')} | {r.B_dur:+.2f} [{r.B_dur_lo:+.2f}, {r.B_dur_hi:+.2f}] | {f(r, 'WminusB_amp')} | "
                 f"{f(r, 'WminusB_dur')} | {r.n_boot_ok} |")
    L += ["\n## Conditional logistic regression (within effects only; Wald 95 %)\n",
          "| set | arm / model | seed | informative patients / seizures | W amp | W dur |", "|---|---|---|---|---|---|"]
    for _, r in CL.iterrows():
        L.append(f"| {r.set} | {r.arm if r.set == 'all23' else r.model} | {'' if pd.isna(r.seed) else int(r.seed)} | "
                 f"{r.n_informative_patients} / {r.n_informative_seizures} | {f(r, 'W_amp')} | {f(r, 'W_dur')} |")
    (OUT / "SUMMARY.md").write_text("\n".join(L) + "\n", encoding="utf-8")
    import sklearn
    import statsmodels
    (OUT / "run_meta.json").write_text(json.dumps(dict(
        script_sha16=hashlib.sha256(Path(__file__).read_bytes()).hexdigest()[:16], B=b, rng=RNG,
        elapsed_s=round(time.time() - t0, 1), numpy=np.__version__, pandas=pd.__version__,
        sklearn=sklearn.__version__, statsmodels=statsmodels.__version__), indent=1))
    log(f"done in {time.time() - t0:.1f} s -> {OUT}")


if __name__ == "__main__":
    main()
