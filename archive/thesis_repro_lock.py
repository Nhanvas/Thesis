#!/usr/bin/env python3
"""
thesis_repro_lock.py -- Reproduce the TWO locked operating points end-to-end on THIS
machine, via the authoritative component path (ensemble_recipe.build_ensemble under the
Decision #19 weight). It NEVER reads any *_ens_*.npy cache. Writes nothing but stdout.

Run from the repo root:   python thesis_repro_lock.py
If summaries/components aren't auto-found:
    python thesis_repro_lock.py <summary_dir> <components_dir>
"""
import os, sys, glob
import numpy as np

sys.path.insert(0, os.path.abspath("."))
import ensemble_recipe as ER
import evaluation_protocol as E
import szcore_eval as SZ

print("THESIS_REPRO_LOCK v1  (component path, no ens cache)")
print("ENS_WEIGHTS on disk:", ER.ENS_WEIGHTS)
assert tuple(round(float(w), 3) for w in ER.ENS_WEIGHTS) == (0.40, 0.35, 0.25), \
    "STOP: ENS_WEIGHTS on disk is NOT (0.40,0.35,0.25) -- weight drift, fix before trusting anything."

# ---- locate components dir ----
comp_arg = sys.argv[2] if len(sys.argv) > 2 else None
CAND = [comp_arg, "data/processed/components", "data/components", "components"]
comp_dir = next((d for d in CAND if d and os.path.isdir(d)), None)
if not comp_dir:
    sys.exit("ERROR: components dir not found. Pass it: python thesis_repro_lock.py <summary_dir> <components_dir>")

# ---- locate summary dir (holds chbXX-summary.txt) ----
def find_summary_dir():
    if len(sys.argv) > 1 and os.path.isdir(sys.argv[1]) and \
       glob.glob(os.path.join(sys.argv[1], "chb03-summary.txt")):
        return sys.argv[1]
    for pat in ("chb03-summary.txt", "**/chb03-summary.txt", "../**/chb03-summary.txt"):
        h = glob.glob(pat, recursive=True)
        if h:
            return os.path.dirname(h[0]) or "."
    return None
summary_dir = find_summary_dir()
if not summary_dir:
    sys.exit("ERROR: chb03-summary.txt not found. Pass summary dir: python thesis_repro_lock.py <summary_dir>")

print("comp_dir   :", comp_dir)
print("summary_dir:", summary_dir)
print("TEST_SUBJS :", E.TEST_SUBJS)

# ---- LOCKED expected values (from RESULTS_OF_RECORD / new_decision19 CSVs) ----
EXP = {
    "balanced (mag60/pen1.0)": dict(mag=60, pen=1.0, TP=57, FP=461, sens=0.7500, fpday=39.77,
        subj={"chb03": (7, 49), "chb06": (3, 90), "chb13": (10, 55), "chb14": (7, 86),
              "chb15": (19, 59), "chb16": (4, 24), "chb17": (2, 30), "chb18": (5, 68)}),
    "highsens (mag50/pen0.5)": dict(mag=50, pen=0.5, TP=63, FP=826, sens=0.8289, fpday=71.25,
        subj={"chb03": (7, 94), "chb06": (5, 163), "chb13": (10, 87), "chb14": (7, 138),
              "chb15": (19, 113), "chb16": (8, 48), "chb17": (2, 58), "chb18": (5, 125)}),
}

overall_ok = True
for name, cfg in EXP.items():
    mag, pen = cfg["mag"], cfg["pen"]
    print("\n" + "=" * 66 + f"\n{name}\n" + "=" * 66)
    print(f"{'subj':7} {'tp/exp':>8} {'fp/exp':>10}  status")
    TP = FP = NSZ = 0
    INTER_H = 0.0
    allmatch = True
    for subj in E.TEST_SUBJS:
        ens_i, ens_c = ER.ensemble_for_subject(comp_dir, subj)  # build fresh, no cache
        np.random.seed(0)                                       # canonical seed
        rows = SZ.evaluate_subject(subj, ens_i, ens_c, summary_dir, min_mag_pct=mag)
        r = next(x for x in rows if abs(x["pen_mult"] - pen) < 1e-9)
        tp, fp = int(r["tp"]), int(r["fp"])
        etp, efp = cfg["subj"][subj]
        ok = (tp == etp and fp == efp)
        allmatch &= ok
        print(f"{subj:7} {tp:>4}/{etp:<3} {fp:>5}/{efp:<4}  {'OK' if ok else '*** MISMATCH'}")
        TP += tp; FP += fp; NSZ += int(r["n_seizures"]); INTER_H += float(r["n_inter_h"])
    sens = TP / NSZ if NSZ else float("nan")
    fpday = FP / INTER_H * 24 if INTER_H else float("nan")
    print("-" * 66)
    print(f"POOLED  TP={TP} (exp {cfg['TP']})   FP={FP} (exp {cfg['FP']})")
    print(f"        sens={sens:.4f} (exp {cfg['sens']})   FP/day={fpday:.2f} (exp {cfg['fpday']})")
    pooled_ok = (TP == cfg["TP"] and FP == cfg["FP"])
    verdict = "FULL MATCH (per-subject + pooled) -- reproducible" if (allmatch and pooled_ok) \
        else ("POOLED MATCH, per-subject differs -- residual seed sensitivity" if pooled_ok
              else "MISMATCH -- investigate")
    print("VERDICT:", verdict)
    overall_ok &= pooled_ok

print("\n" + "#" * 66)
print("OVERALL:", "LOCKED HEADLINE REPRODUCES on this machine." if overall_ok
      else "LOCKED HEADLINE DID NOT REPRODUCE -- five-alarm, stop and investigate.")
print("#" * 66)