#!/usr/bin/env python
"""eur_diag_check.py -- read-only checks of the EUR_DIAG rerun output (Track F, chat D32-F, 20/11/2026). No model, no
EEG: only the committed files results/eureka_d31f/diag/{ev_events.csv, d1_rows.csv}.

(1) EV scale check. eur_diag.event_values scores each window feature as a robust z against the patient's background
    with MAD + 1e-9 in the denominator; when a feature's background MAD is 0 (contiguity, flat-run fraction, ...) the
    values reach ~1e9 and the POOLED AUROC of the EV rule mixes patients on incomparable scales. The within-patient
    (stratified) AUROC compares only seizure / false-alarm pairs of the same patient and seed, so it does not depend on
    any per-patient monotone rescaling. Reported per feature: share of development events with |value| > 1e6, the
    stratified AUROC oriented by its own direction, and a patient-cluster bootstrap 95 % interval (B = 2,000, rng 0,
    chb01 + chb21 one unit, every resampled copy a separate stratum); test / chb24 / Siena stratified AUROC
    (descriptive). The EV rule (lower bound >= 0.80) is applied to this reading as a check of the committed decision.
(2) D1 margin. The budget each short seizure needs (need_q: share of the patient's smoothed V5 values above the seizure
    peak) at shift 0 and at the best shift, against the patient's budget (top), median over seeds.
Outputs (--out, default results/eureka_d32f/diag_check): ev_stratified.csv, d1_margin.csv, CHECK.md.
  python src/eur_diag_check.py
"""
import argparse
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.stats import rankdata

ROOT = Path(__file__).resolve().parents[1]
DIAG = ROOT / "results" / "eureka_d31f" / "diag"
UNIT = {"chb21": "chb01"}
B, RNG = 2000, 0


def strat_auc(g, f, key="stratum"):
    num = den = 0.0
    for _, h in g.groupby([key, "seed"]):
        y = (h.label == "seizure").values
        x = h[f].values.astype(float)
        k = np.isfinite(x)
        y, x = y[k], x[k]
        n1 = int(y.sum()); n0 = len(y) - n1
        if n1 == 0 or n0 == 0:
            continue
        r = rankdata(x)
        num += r[y].sum() - n1 * (n1 + 1) / 2
        den += n1 * n0
    return num / den if den else np.nan


def ev_check(E):
    feats = [c for c in E.columns if c.endswith("_med")] + ["line_length_max", "evo_dfreq", "evo_amp", "duration"]
    E = E[E.label.isin(["seizure", "false_alarm"])].copy()
    E["stratum"] = E.subject
    d = E[E.set == "development"].reset_index(drop=True)
    unit = d.subject.map(lambda s: UNIT.get(s, s)).values
    units = sorted(set(unit))
    rows_of = {u: np.flatnonzero(unit == u) for u in units}
    rng = np.random.default_rng(RNG)
    boots = {f: [] for f in feats}
    for _ in range(B):
        pick = rng.choice(units, size=len(units), replace=True)
        parts = []
        for j, u in enumerate(pick):
            h = d.iloc[rows_of[u]].copy()
            h["stratum"] = h.subject + f"#{j}"
            parts.append(h)
        dd = pd.concat(parts, ignore_index=True)
        for f in feats:
            boots[f].append(strat_auc(dd, f))
    out = []
    for f in feats:
        a = strat_auc(d, f)
        o = 1 if a >= 0.5 else -1
        bs = np.asarray(boots[f]); bs = bs if o > 0 else 1 - bs
        r = dict(feature=f, direction="higher in seizures" if o > 0 else "lower in seizures",
                 dev_share_abs_gt_1e6=float((d[f].abs() > 1e6).mean()),
                 dev_strat_auroc=a if o > 0 else 1 - a, ci_lo=float(np.percentile(bs, 2.5)),
                 ci_hi=float(np.percentile(bs, 97.5)))
        for st in ("test", "chb24", "siena"):
            v = strat_auc(E[E.set == st], f)
            r[f"{st}_strat_auroc"] = (v if o > 0 else 1 - v) if np.isfinite(v) else np.nan
        r["rule_met"] = bool(r["ci_lo"] >= 0.80)
        out.append(r)
    return pd.DataFrame(out).sort_values("dev_strat_auroc", ascending=False)


def d1_margin(D):
    g = D.groupby(["set", "subject", "onset_s", "seed"])
    x = g.apply(lambda h: pd.Series(dict(top=h.top.iloc[0], dur_s=h.dur_s.iloc[0],
                                          need_s0=h.loc[h.shift_s == 0, "need_q"].iloc[0],
                                          need_best=h.need_q.min()))).reset_index()
    return x.groupby(["set", "subject"]).agg(seizures=("onset_s", "nunique"), top=("top", "median"),
                                             need_s0=("need_s0", "median"), need_best=("need_best", "median")).reset_index()


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default=str(ROOT / "results" / "eureka_d32f" / "diag_check"))
    a = ap.parse_args()
    out = Path(a.out); out.mkdir(parents=True, exist_ok=True)
    ev = ev_check(pd.read_csv(DIAG / "ev_events.csv"))
    ev.to_csv(out / "ev_stratified.csv", index=False)
    dm = d1_margin(pd.read_csv(DIAG / "d1_rows.csv"))
    dm.to_csv(out / "d1_margin.csv", index=False)
    L = ["# Checks of the EUR_DIAG rerun (D32-F, read only; src/eur_diag_check.py)", "",
         "## EV — within-patient (stratified) AUROC, seizure vs false-alarm events, development", "",
         "Pairs compared only within the same patient and seed, so the reading does not depend on the per-patient robust-z",
         "scale (which reaches ~1e9 where the background MAD is 0). Patient-cluster bootstrap, B = 2,000. Rule as EV:",
         "lower bound ≥ 0.80.", "",
         "| feature | direction | dev events with |value| > 1e6 | dev stratified AUROC [95 % CI] | test | chb24 | Siena | rule |",
         "|---|---|---|---|---|---|---|---|"]
    for _, r in ev.iterrows():
        L.append(f"| {r.feature} | {r.direction} | {r.dev_share_abs_gt_1e6:.1%} | {r.dev_strat_auroc:.3f} "
                 f"[{r.ci_lo:.3f}, {r.ci_hi:.3f}] | {r.test_strat_auroc:.2f} | {r.chb24_strat_auroc:.2f} | "
                 f"{r.siena_strat_auroc:.2f} | {'met' if r.rule_met else 'not met'} |")
    L += ["", "## D1 — budget the short seizures need (median over seeds)", "",
          "| set | subject | short seizures | budget (top) | needed at shift 0 | needed at best shift |", "|---|---|---|---|---|---|"]
    for _, r in dm.iterrows():
        L.append(f"| {r.set} | {r.subject} | {r.seizures} | {r.top:.2%} | {r.need_s0:.2%} | {r.need_best:.2%} |")
    (out / "CHECK.md").write_text("\n".join(L) + "\n")
    print("\n".join(L))


if __name__ == "__main__":
    main()
