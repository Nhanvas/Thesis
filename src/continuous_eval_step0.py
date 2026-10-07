#!/usr/bin/env python
"""
continuous_eval_step0.py -- Step 0 of docs/CC_PROMPT_CONTINUOUS_EVAL.md: exact correction
of the committed offline result at mag_pct=50, pen_mult=2.0 (rlg, seed as in D0a).

No new scores: reuses the committed ens_seed42_{subj}_{inter,ictal}.npy arrays and the
existing offline harness (szcore_eval.build_timeline_masked, cpd_pipeline_v14.detect_changepoints,
szcore_eval.cps_to_events / score_szcore). Only new computation: which change points
cps_to_events silently drops via its is_buffer rule (away from any seizure), and the FA/day
denominator split into real-interictal hours vs. all-non-ictal hours.

Reuses (never re-implements): szcore_eval.build_timeline_masked / cps_to_events / score_szcore /
_aligned / PEN_MULTS / WIN_SEC / TEST_SUBJS, cpd_pipeline_v14.detect_changepoints.

Usage: python src/continuous_eval_step0.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import szcore_eval as SE          # noqa: E402
import cpd_pipeline_v14 as V14    # noqa: E402

TEST_SUBJS = SE.TEST_SUBJS
WIN_S = SE.WIN_SEC
MAG_PCT = 50.0
PEN_MULT = 2.0
BOOTSTRAP_SEED = 0   # score_ens.py --bootstrap_seed default; same seed D0a used

SUMMARY_DIR = ROOT / "data" / "summaries"
ENS_DIR = ROOT / "results" / "phaseB" / "tier2" / "ens_test_tf" / "rlg"
OUT_DIR = ROOT / "results" / "continuous_eval"

D0A_EXPECTED = dict(tp=47, fn=29, fp=318, sensitivity=0.618, precision=0.129,
                    f1=0.213, fp_per_day=27.4)


def load_offline(subj):
    ei = np.load(ENS_DIR / f"ens_seed42_{subj}_inter.npy")
    ec = np.load(ENS_DIR / f"ens_seed42_{subj}_ictal.npy")
    return ei, ec


def run():
    rows = []
    for subj in TEST_SUBJS:
        ei, ec = load_offline(subj)
        np.random.seed(BOOTSTRAP_SEED)
        signal, is_ictal, is_buffer, real_inter, sz_ranges, n_inter_h = \
            SE.build_timeline_masked(subj, ei, ec, str(SUMMARY_DIR))

        cps, _ = V14.detect_changepoints(signal, PEN_MULT, min_mag_pct=MAG_PCT,
                                         local_win=15, inter_mask=real_inter)
        n_dropped = 0
        for c in cps:
            if not (0 < c < len(signal)):
                continue
            if is_buffer[c] and not SE._aligned(c, sz_ranges):
                n_dropped += 1

        hyp_iv = SE.cps_to_events(cps, is_buffer, len(signal), sz_ranges=sz_ranges)
        ref_iv = [(s * WIN_S, e * WIN_S) for (s, e) in sz_ranges]
        total_dur_s = len(signal) * WIN_S
        sc = SE.score_szcore(ref_iv, hyp_iv, total_dur_s, n_inter_h)

        real_inter_h = float(real_inter.sum()) * WIN_S / 3600.0
        all_noninter_h = float(n_inter_h)   # build_timeline_masked's own denominator (real + buffer)

        fa_real = sc["fp"] / max(real_inter_h, 1e-9) * 24.0
        fa_all = sc["fp"] / max(all_noninter_h, 1e-9) * 24.0

        rows.append(dict(
            subject=subj, tp=sc["tp"], fp=sc["fp"], n_ref=sc["n_ref"], fn=sc["n_ref"] - sc["tp"],
            sensitivity=round(sc["sensitivity"], 4), precision=round(sc["precision"], 4),
            f1=round(sc["f1"], 4),
            hours_real_inter=round(real_inter_h, 3), hours_all_nonictal=round(all_noninter_h, 3),
            fa_per_day_real=round(fa_real, 3), fa_per_day_all_nonictal=round(fa_all, 3),
            n_cps_dropped_by_is_buffer=n_dropped,
        ))
        print(f"  [S0] {subj}: FP={sc['fp']} real_inter_h={real_inter_h:.2f} "
              f"all_nonictal_h={all_noninter_h:.2f} FA/day(real)={fa_real:.2f} "
              f"FA/day(all)={fa_all:.2f} dropped_cps={n_dropped}", flush=True)

    df = pd.DataFrame(rows)
    pooled_tp = int(df.tp.sum()); pooled_fp = int(df.fp.sum()); pooled_ref = int(df.n_ref.sum())
    pooled_fn = pooled_ref - pooled_tp
    pooled_sens = pooled_tp / pooled_ref if pooled_ref else float("nan")
    pooled_prec = pooled_tp / (pooled_tp + pooled_fp) if (pooled_tp + pooled_fp) else float("nan")
    pooled_f1 = (2 * pooled_prec * pooled_sens / (pooled_prec + pooled_sens)
                if (pooled_prec + pooled_sens) else float("nan"))
    pooled_real_h = float(df.hours_real_inter.sum())
    pooled_all_h = float(df.hours_all_nonictal.sum())
    pooled_fa_real = pooled_fp / pooled_real_h * 24.0 if pooled_real_h else float("nan")
    pooled_fa_all = pooled_fp / pooled_all_h * 24.0 if pooled_all_h else float("nan")
    pooled_dropped = int(df.n_cps_dropped_by_is_buffer.sum())

    reproduced = (pooled_tp == D0A_EXPECTED["tp"] and pooled_fn == D0A_EXPECTED["fn"] and
                  pooled_fp == D0A_EXPECTED["fp"] and
                  round(pooled_sens, 3) == D0A_EXPECTED["sensitivity"] and
                  round(pooled_prec, 3) == D0A_EXPECTED["precision"] and
                  round(pooled_f1, 3) == D0A_EXPECTED["f1"] and
                  round(pooled_fa_all, 1) == D0A_EXPECTED["fp_per_day"])

    pooled_row = dict(
        subject="POOLED", tp=pooled_tp, fp=pooled_fp, n_ref=pooled_ref, fn=pooled_fn,
        sensitivity=round(pooled_sens, 4), precision=round(pooled_prec, 4), f1=round(pooled_f1, 4),
        hours_real_inter=round(pooled_real_h, 3), hours_all_nonictal=round(pooled_all_h, 3),
        fa_per_day_real=round(pooled_fa_real, 3), fa_per_day_all_nonictal=round(pooled_fa_all, 3),
        n_cps_dropped_by_is_buffer=pooled_dropped,
    )
    out_df = pd.concat([df, pd.DataFrame([pooled_row])], ignore_index=True)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    out_df.to_csv(OUT_DIR / "step0.csv", index=False)

    print("\n" + "=" * 100)
    print(f"[S0] POOLED: TP={pooled_tp} FP={pooled_fp} FN={pooled_fn} n_ref={pooled_ref} "
          f"sens={pooled_sens:.3f} prec={pooled_prec:.3f} F1={pooled_f1:.3f}")
    print(f"[S0] denominator = all-non-ictal (reported convention): {pooled_all_h:.1f} h -> "
          f"FA/day = {pooled_fa_all:.1f}  (expected 27.4; matches offline D0a reproduction: "
          f"{'PASS' if reproduced else 'FAIL'})")
    print(f"[S0] denominator = real-interictal only (exact correction): {pooled_real_h:.1f} h -> "
          f"FA/day = {pooled_fa_real:.1f}")
    print(f"[S0] change points dropped by the is_buffer rule (away from any seizure): "
          f"{pooled_dropped} pooled across all 8 test patients")
    print("=" * 100)
    print(f"Wrote {OUT_DIR / 'step0.csv'}")
    return reproduced


if __name__ == "__main__":
    t0 = time.perf_counter()
    ok = run()
    print(f"\n[S0] D0a offline reproduction check (sanity, not this step's own gate): "
          f"{'PASS' if ok else 'FAIL'}")
    print(f"[S0] elapsed: {time.perf_counter() - t0:.1f} s")
