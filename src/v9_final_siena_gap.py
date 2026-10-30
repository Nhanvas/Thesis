#!/usr/bin/env python
"""
v9_final_siena_gap.py -- V9-FINAL Part C (docs/prompts/V9_FINAL_VERIFY.md): Siena gap decomposition,
formally.

Reweights CHB-MIT-test's own per-bin detection rate to Siena's bin mix (duration bins <=20/21-40/
41-80/>80 s, the thesis system, seed 42, after the localizer, SAME overlap rule for both sets -- i.e.
both CHB-MIT-test and Siena per-seizure caught/duration/amp_ratio come from the SAME source,
results/v9_v1/part1_descriptors.csv, built by the SAME v9_eeg_evidence.part1() call, so "same overlap
rule for both sets" is true by construction, not asserted). Answers: how much of the raw CHB-MIT-test
vs Siena sensitivity gap is explained by Siena simply having a different duration (or amplitude-ratio)
mix of seizures, holding CHB-MIT-test's own per-bin detection rate fixed.

  reweighted_sens  = sum_b w_b(siena) * p_b(chb-test)             (b = duration or amp-ratio-quartile bin)
  share_explained  = (test_actual_sens - reweighted_sens) / (test_actual_sens - siena_actual_sens)

Amplitude-ratio bins: quartiles of the POOLED (CHB-MIT-test + Siena) amp_ratio distribution (so both
sets are binned on a common scale; computed once on the point estimate and used for every bootstrap
replicate too, to avoid quartile boundaries moving as noisily as the bins they define).

Patient bootstrap (B=2000, percentile CI): resample CHB-MIT-test patients with replacement (gives a new
p_b(chb-test) each time, seizures stay with their own patient) AND, independently, resample Siena
patients with replacement (gives a new w_b(siena) each time) -- jointly, every replicate. A replicate is
dropped (counted, not silently) if the Siena resample puts weight on a bin that has zero CHB-MIT-test
seizures in that same replicate (p_b undefined).

READ-ONLY REUSE: results/v9_v1/part1_descriptors.csv (chb-test + siena rows only); v9_e1_baselines.
DUR_BINS (bin edges, SAME boundary convention as v9_e1_baselines.duration_bins: lo < dur <= hi, except
the first bin dur <= hi).

OUTPUT: results/v9_final/siena_gap/ (duration_gap.csv, amp_gap.csv, SUMMARY.md).
Run:  python src/v9_final_siena_gap.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import v9_e1_baselines as V9E1          # noqa: E402 -- read-only reuse (DUR_BINS only)

OUT = ROOT / "results" / "v9_final" / "siena_gap"
PART1 = ROOT / "results" / "v9_v1" / "part1_descriptors.csv"
DUR_BINS = V9E1.DUR_BINS
N_BOOT = 2000
RNG_SEED = 42


def _bin_of_dur(dur):
    for lo, hi in DUR_BINS:
        if (lo == 0 and dur <= hi) or (lo < dur <= hi):
            return (lo, hi)
    return DUR_BINS[-1]


def load():
    D = pd.read_csv(PART1)
    test = D[D.set == "chb-test"].copy()
    siena = D[D.set == "siena"].copy()
    test["dur_bin"] = test.duration_s.map(_bin_of_dur)
    siena["dur_bin"] = siena.duration_s.map(_bin_of_dur)
    return test, siena


def per_bin_rate(df, bin_col):
    g = df.groupby(bin_col).caught.agg(["sum", "count"])
    return {b: (int(r["sum"]), int(r["count"])) for b, r in g.iterrows()}


def reweight(test_rates, siena_counts):
    """weighted sensitivity: sum_b w_b(siena) * p_b(test); p_b undefined (0 test seizures in that bin)
    makes the whole reweight undefined for that replicate -- caller decides whether to drop it."""
    n_siena = sum(c for c in siena_counts.values())
    if n_siena == 0:
        return np.nan, False
    num, bad = 0.0, False
    for b, n_s in siena_counts.items():
        if n_s == 0:
            continue
        tp_t, n_t = test_rates.get(b, (0, 0))
        if n_t == 0:
            bad = True
            continue
        num += (n_s / n_siena) * (tp_t / n_t)
    return (np.nan if bad else num), (not bad)


def point_estimate(test, siena, bin_col):
    test_rates = per_bin_rate(test, bin_col)
    siena_counts = {b: c for b, (tp, c) in per_bin_rate(siena, bin_col).items()}
    reweighted, ok = reweight(test_rates, siena_counts)
    test_sens = test.caught.sum() / len(test)
    siena_sens = siena.caught.sum() / len(siena)
    share = (test_sens - reweighted) / (test_sens - siena_sens) if ok and test_sens != siena_sens else np.nan
    return dict(test_sens=test_sens, siena_sens=siena_sens, reweighted_sens=reweighted, share_explained=share,
                test_rates=test_rates, siena_counts=siena_counts)


def bootstrap(test, siena, bin_col, rng):
    test_subs = test.subject.unique()
    siena_subs = siena.subject.unique()
    rew_list, share_list = [], []
    n_dropped = 0
    for _ in range(N_BOOT):
        t_pick = rng.choice(test_subs, size=len(test_subs), replace=True)
        s_pick = rng.choice(siena_subs, size=len(siena_subs), replace=True)
        bt = pd.concat([test[test.subject == p] for p in t_pick], ignore_index=True)
        bs = pd.concat([siena[siena.subject == p] for p in s_pick], ignore_index=True)
        test_rates = per_bin_rate(bt, bin_col)
        siena_counts = {b: c for b, (tp, c) in per_bin_rate(bs, bin_col).items()}
        reweighted, ok = reweight(test_rates, siena_counts)
        if not ok or len(bt) == 0 or len(bs) == 0:
            n_dropped += 1
            continue
        test_sens = bt.caught.sum() / len(bt)
        siena_sens = bs.caught.sum() / len(bs)
        if test_sens == siena_sens:
            n_dropped += 1
            continue
        rew_list.append(reweighted)
        share_list.append((test_sens - reweighted) / (test_sens - siena_sens))
    return rew_list, share_list, n_dropped


def ci(vals):
    if not vals:
        return (np.nan, np.nan)
    return (float(np.percentile(vals, 2.5)), float(np.percentile(vals, 97.5)))


def run():
    t0 = time.time()
    OUT.mkdir(parents=True, exist_ok=True)
    test, siena = load()
    rng = np.random.RandomState(RNG_SEED)

    # ---- duration mix ----
    pe_dur = point_estimate(test, siena, "dur_bin")
    rew_d, share_d, drop_d = bootstrap(test, siena, "dur_bin", rng)
    ci_rew_d, ci_share_d = ci(rew_d), ci(share_d)

    rows = []
    for b in DUR_BINS:
        tp_t, n_t = pe_dur["test_rates"].get(b, (0, 0))
        n_s = pe_dur["siena_counts"].get(b, 0)
        rows.append(dict(bin=f"{b[0]}-{b[1]}", test_tp=tp_t, test_n=n_t,
                          test_rate=tp_t / n_t if n_t else np.nan, siena_n=n_s,
                          siena_weight=n_s / len(siena) if len(siena) else np.nan))
    pd.DataFrame(rows).to_csv(OUT / "duration_gap.csv", index=False)

    # ---- amplitude-ratio mix: quartiles of the POOLED distribution ----
    pooled_amp = pd.concat([test.amp_ratio, siena.amp_ratio], ignore_index=True)
    edges = np.nanpercentile(pooled_amp, [0, 25, 50, 75, 100])
    edges[0] -= 1e-9  # include the minimum in the first bin
    amp_bins = list(zip(edges[:-1], edges[1:]))

    def _bin_of_amp(v):
        for i, (lo, hi) in enumerate(amp_bins):
            if lo < v <= hi:
                return i
        return len(amp_bins) - 1

    test = test.copy(); siena = siena.copy()
    test["amp_bin"] = test.amp_ratio.map(_bin_of_amp)
    siena["amp_bin"] = siena.amp_ratio.map(_bin_of_amp)
    pe_amp = point_estimate(test, siena, "amp_bin")
    rew_a, share_a, drop_a = bootstrap(test, siena, "amp_bin", rng)
    ci_rew_a, ci_share_a = ci(rew_a), ci(share_a)

    rows = []
    for i, (lo, hi) in enumerate(amp_bins):
        tp_t, n_t = pe_amp["test_rates"].get(i, (0, 0))
        n_s = pe_amp["siena_counts"].get(i, 0)
        rows.append(dict(bin=f"Q{i+1} ({lo:.2f},{hi:.2f}]", test_tp=tp_t, test_n=n_t,
                          test_rate=tp_t / n_t if n_t else np.nan, siena_n=n_s,
                          siena_weight=n_s / len(siena) if len(siena) else np.nan))
    pd.DataFrame(rows).to_csv(OUT / "amp_gap.csv", index=False)

    L = ["# V9-FINAL Part C -- Siena gap decomposition, formally\n",
         f"CHB-MIT test: {len(test)} seizures ({test.subject.nunique()} patients), thesis system seed 42 "
         f"after the localizer, actual sensitivity {pe_dur['test_sens']:.3f}. Siena: {len(siena)} seizures "
         f"({siena.subject.nunique()} patients), actual sensitivity {pe_dur['siena_sens']:.3f}. Raw gap "
         f"{pe_dur['test_sens']-pe_dur['siena_sens']:+.3f}.\n",
         "## Duration-bin reweighting (CHB-MIT-test per-bin rate, Siena's own bin mix)\n", "```",
          pd.read_csv(OUT / "duration_gap.csv").to_string(index=False), "```",
          f"\nReweighted sensitivity (test's own per-bin rate, Siena's duration mix): "
          f"{pe_dur['reweighted_sens']:.3f}  [{ci_rew_d[0]:.3f}, {ci_rew_d[1]:.3f}] "
          f"(patient bootstrap, B={N_BOOT}, {drop_d} replicates dropped for undefined support)",
          f"Share of the test-vs-Siena gap explained by the duration mix alone: "
          f"{pe_dur['share_explained']:.3f}  [{ci_share_d[0]:.3f}, {ci_share_d[1]:.3f}]\n",
          "## Amplitude-ratio-bin reweighting (quartiles of the pooled test+Siena distribution)\n", "```",
          pd.read_csv(OUT / "amp_gap.csv").to_string(index=False), "```",
          f"\nReweighted sensitivity (test's own per-bin rate, Siena's amplitude-ratio mix): "
          f"{pe_amp['reweighted_sens']:.3f}  [{ci_rew_a[0]:.3f}, {ci_rew_a[1]:.3f}] "
          f"(patient bootstrap, B={N_BOOT}, {drop_a} replicates dropped)",
          f"Share of the test-vs-Siena gap explained by the amplitude-ratio mix alone: "
          f"{pe_amp['share_explained']:.3f}  [{ci_share_a[0]:.3f}, {ci_share_a[1]:.3f}]",
          f"\nElapsed {time.time()-t0:.0f}s."]

    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L), flush=True)
    print(f"\nWrote {OUT/'SUMMARY.md'}", flush=True)


if __name__ == "__main__":
    run()
