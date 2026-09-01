#!/usr/bin/env python
"""
attribution_synthetic_check.py — ATTRIBUTION_SPEC §4.6 + A2/D6.

Injects synthetic per-channel anomalies into interictal per-node recon error, where ground truth
is exact, and asks whether the scoring machinery recovers it. Runs BEFORE any real label is scored.

Gate = VAL subjects. TEST is a confirmatory panel only; nothing is selected on it.

Usage (from repo ROOT):
    python src/attribution_synthetic_check.py
"""
import sys, csv
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "retrain"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
from scipy.stats import mannwhitneyu

PN    = ROOT / "data" / "pernode_v2" / "seed42"
OUT   = ROOT / "results" / "attribution_v6"
BLK   = OUT / "seizure_blocks.csv"
VAL   = ["chb10", "chb11", "chb22"]
TEST  = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ALPHAS = [1.0, 1.25, 1.5, 2.0, 3.0]
SIZES  = [1, 2, 4, 8, 12]
R, NPERM, SEED, NCH = 200, 1000, 42, 18


def die(m):
    print(f"\n[FATAL] {m}\n", file=sys.stderr); sys.exit(1)


def macro_auroc(S, Y):
    """S,Y: [R,18]. No ties expected in S (float recon error)."""
    Rn, C = S.shape
    order = np.argsort(S, axis=1)
    ranks = np.empty_like(order)
    ranks[np.arange(Rn)[:, None], order] = np.arange(1, C + 1)[None, :]
    npos = Y.sum(1); nneg = C - npos
    sr = (ranks * Y).sum(1)
    return float(np.mean((sr - npos * (npos + 1) / 2) / (npos * nneg)))


def macro_ap(S, Y):
    aps = []
    for s, y in zip(S, Y):
        o = np.argsort(-s, kind="mergesort"); yy = y[o]
        tp = np.cumsum(yy)
        prec = tp / np.arange(1, len(yy) + 1)
        aps.append((prec * yy).sum() / max(yy.sum(), 1))
    return float(np.mean(aps))


def macro_recall_at_S(S, Y):
    rec = []
    for s, y in zip(S, Y):
        k = int(y.sum())
        top = np.argsort(-s)[:k]
        rec.append(y[top].sum() / k)
    return float(np.mean(rec))


def spreads(S):
    """Normalised entropy of the non-negative score vector; 1 = fully diffuse."""
    P = np.clip(S, 1e-12, None)
    P = P / P.sum(1, keepdims=True)
    return -(P * np.log(P)).sum(1) / np.log(S.shape[1])


def perm_null(S, Y, rng):
    """Permute s across channels within each pseudo-seizure, keeping y."""
    out = np.empty(NPERM)
    for t in range(NPERM):
        idx = np.argsort(rng.random(S.shape), axis=1)
        out[t] = macro_auroc(np.take_along_axis(S, idx, axis=1), Y)
    return out


def load_len_distribution():
    if not BLK.is_file():
        die(f"missing {BLK} — run src/build_seizure_blocks.py first")
    lens = []
    with open(BLK) as f:
        for row in csv.DictReader(f):
            if row["subject"] in TEST:
                lens.append(int(row["n_windows"]))
    if len(lens) != 76:
        die(f"expected 76 TEST seizures in {BLK}, got {len(lens)}")
    return np.array(lens)


def run(subjects, lens, tag):
    rng = np.random.default_rng(SEED)
    inter = {}
    for s in subjects:
        f = PN / f"{s}_interictal_pernode.npy"
        if not f.is_file():
            die(f"missing {f}")
        inter[s] = np.load(f)

    rows = []
    store = {}
    for alpha in ALPHAS:
        for k in SIZES:
            S = np.zeros((R, NCH)); Y = np.zeros((R, NCH), dtype=int)
            for r in range(R):
                subj = subjects[rng.integers(len(subjects))]
                A = inter[subj]
                L = int(lens[rng.integers(len(lens))])
                L = min(L, A.shape[0] // 4)
                st = int(rng.integers(0, A.shape[0] - L))
                blk = A[st:st + L].copy()
                base = np.delete(A, np.arange(st, st + L), axis=0)   # baseline excludes the block

                inj = rng.choice(NCH, size=k, replace=False)
                blk[:, inj] *= alpha

                med = np.median(base, axis=0)
                mad = np.median(np.abs(base - med), axis=0) + 1e-9
                z = np.abs((blk - med) / mad)
                S[r] = np.percentile(z, 95, axis=0)                  # PRIMARY aggregation (p95)
                Y[r, inj] = 1

            auroc, ap = macro_auroc(S, Y), macro_ap(S, Y)
            rec, spr = macro_recall_at_S(S, Y), spreads(S)
            null = perm_null(S, Y, rng)
            pval = (np.sum(null >= auroc) + 1) / (NPERM + 1)
            rows.append({"panel": tag, "alpha": alpha, "n_injected": k,
                         "macro_AUROC": round(auroc, 4), "macro_AUPRC": round(ap, 4),
                         "recall_at_S": round(rec, 4),
                         "null_mean": round(float(null.mean()), 4),
                         "null_p95": round(float(np.percentile(null, 95)), 4),
                         "p_perm": round(float(pval), 4),
                         "spread_mean": round(float(spr.mean()), 4)})
            store[(alpha, k)] = spr
            print(f"  {tag:<4} a={alpha:<5} |S|={k:<3} AUROC={auroc:.4f} AUPRC={ap:.4f} "
                  f"R@S={rec:.4f} null={null.mean():.4f} p={pval:.4f} spread={spr.mean():.4f}")
    return rows, store


def main():
    lens = load_len_distribution()
    print(f"seizure-length distribution from 76 TEST seizures: "
          f"min={lens.min()} median={int(np.median(lens))} max={lens.max()}\n")

    all_rows = {}
    store_val = None
    for tag, subs in [("VAL", VAL), ("TEST", TEST)]:
        print(f"--- {tag} ---")
        rows, store = run(subs, lens, tag)
        all_rows[tag] = rows
        if tag == "VAL":
            store_val = store
        print()

    flat = all_rows["VAL"] + all_rows["TEST"]
    with open(OUT / "synthetic_sanity.csv", "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(flat[0].keys())); w.writeheader(); w.writerows(flat)
    print(f"wrote {OUT / 'synthetic_sanity.csv'}")

    g = {r["alpha"]: r for r in all_rows["VAL"] if r["n_injected"] == 1}
    gs1 = 0.45 <= g[1.0]["macro_AUROC"] <= 0.55
    gs2 = g[3.0]["macro_AUROC"] >= 0.95
    gs3 = all(
        all(next(r for r in all_rows["VAL"] if r["alpha"] == a and r["n_injected"] == k)["macro_AUROC"]
            <= next(r for r in all_rows["VAL"] if r["alpha"] == b and r["n_injected"] == k)["macro_AUROC"]
            + 1e-9 for a, b in zip(ALPHAS, ALPHAS[1:]))
        for k in SIZES)
    u, p4 = mannwhitneyu(store_val[(2.0, 12)], store_val[(2.0, 1)], alternative="greater")
    gs4 = p4 < 0.05

    print("\n=== PRE-REGISTERED GATES (VAL) ===")
    print(f"  G-S1 negative control  a=1.0,|S|=1 AUROC={g[1.0]['macro_AUROC']:.4f} in [0.45,0.55]"
          f"  -> {'PASS' if gs1 else 'FAIL'}")
    print(f"  G-S2 upper bound       a=3.0,|S|=1 AUROC={g[3.0]['macro_AUROC']:.4f} >= 0.95"
          f"  -> {'PASS' if gs2 else 'FAIL'}")
    print(f"  G-S3 monotone in alpha -> {'PASS' if gs3 else 'FAIL'}")
    print(f"  G-S4 spread(|S|=12) > spread(|S|=1) at a=2.0, p={p4:.2e}"
          f"  -> {'PASS' if gs4 else 'FAIL'}")
    print("\nVERDICT:", "PASS — machinery verified, proceed to real labels"
          if all([gs1, gs2, gs3, gs4]) else "FAIL — DO NOT score real labels; diagnose first")


if __name__ == "__main__":
    main()