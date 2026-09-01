#!/usr/bin/env python
"""
attribution_score_seizures.py — ATTRIBUTION_SPEC §2 + A2 (D1/D3/D4/D5).

Per seizure, produces the 18-channel score vector s and its ranking. LABEL-FREE: this is the
method's output, independent of any ground truth. Scoring against labels happens downstream.

s_i = p95_w |z_i(w)|  (PRIMARY)   |   s_i = mean_w |z_i(w)|  (sensitivity)
z from robust-z against the subject's own interictal per-node baseline.

Usage:  python src/attribution_score_seizures.py            # seeds 42,1,2,3
"""
import csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
import numpy as np

PNR  = ROOT / "data" / "pernode_v2"
OUT  = ROOT / "results" / "attribution_v6"
MAP  = OUT / "ictal_row_to_seizure.csv"
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
SEEDS = [42, 1, 2, 3]
CH = ["FP1-F7","F7-T7","T7-P7","P7-O1","FP1-F3","F3-C3","C3-P3","P3-O1",
      "FP2-F4","F4-C4","C4-P4","P4-O2","FP2-F8","F8-T8","T8-P8","P8-O2","FZ-CZ","CZ-PZ"]


def die(m):
    print(f"\n[FATAL] {m}\n", file=sys.stderr); sys.exit(1)


def main():
    if not MAP.is_file():
        die(f"missing {MAP}")
    rowmap = {}
    for r in csv.DictReader(open(MAP)):
        if r["subject"] in TEST:
            rowmap.setdefault((r["subject"], int(r["seizure_idx"])), []).append(int(r["row"]))
    if len(rowmap) != 76:
        die(f"expected 76 TEST seizures in map, got {len(rowmap)}")

    out = []
    for seed in SEEDS:
        d = PNR / f"seed{seed}"
        if not d.is_dir():
            die(f"missing {d} — run: python src/dump_pernode_recon.py --seed {seed}")
        for subj in TEST:
            ict = np.load(d / f"{subj}_ictal_pernode.npy")
            base = np.load(d / f"{subj}_interictal_pernode.npy")
            med = np.median(base, axis=0)
            mad = np.median(np.abs(base - med), axis=0) + 1e-9
            for (s, k), rows in sorted(rowmap.items()):
                if s != subj:
                    continue
                z = np.abs((ict[np.array(rows)] - med) / mad)      # [n_win, 18]
                for agg, vec in [("p95", np.percentile(z, 95, axis=0)),
                                 ("mean", z.mean(axis=0))]:
                    order = np.argsort(-vec)
                    rank = np.empty(18, dtype=int); rank[order] = np.arange(1, 19)
                    for i in range(18):
                        out.append({"seed": seed, "subject": subj, "seizure_idx": k,
                                    "n_windows": len(rows), "agg": agg,
                                    "ch_idx": i, "ch_name": CH[i],
                                    "score": round(float(vec[i]), 6), "rank": int(rank[i])})
            print(f"  seed{seed} {subj}: scored {sum(1 for a,_ in rowmap if a==subj)} seizures")

    f = OUT / "attribution_scores.csv"
    with open(f, "w", newline="") as fh:
        w = csv.DictWriter(fh, fieldnames=list(out[0].keys())); w.writeheader(); w.writerows(out)
    exp = len(SEEDS) * 76 * 2 * 18
    print(f"\nwrote {f}  ({len(out)} rows, expected {exp})")
    if len(out) != exp:
        die("row count mismatch")

    p95 = [r for r in out if r["seed"] == 42 and r["agg"] == "p95"]
    top = {}
    for r in p95:
        if r["rank"] == 1:
            top[r["ch_name"]] = top.get(r["ch_name"], 0) + 1
    print("\nseed42/p95 — top-1 channel frequency across 76 seizures:")
    for k, v in sorted(top.items(), key=lambda x: -x[1]):
        print(f"  {k:<8} {v}")


if __name__ == "__main__":
    main()