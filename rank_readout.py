"""Rank readout for the channel-attribution section (Chapter 3 §3.6.3, Appendix A.2).

Reconstructs the per-channel score of every focal test seizure exactly as the attribution pipeline
does, then reports where the annotated ictal channels sit in the model's ranking.

It writes nothing until it has reproduced the per-seizure AUROC already stored in
results/attribution_v7/attribution_perseizure.csv to within 1e-9 on every focal seizure. If the
reproduction fails, the script stops and prints the worst mismatch, and no number is reported.

Run from the repository root:
    python rank_readout.py
Outputs:
    results/attribution_v7/rank_readout_perseizure.csv   one row per focal seizure
    results/attribution_v7/rank_readout_summary.txt      the sentences for the report
"""

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parent
PERNODE = ROOT / "data" / "pernode_v2" / "seed42"
V7 = ROOT / "results" / "attribution_v7"
BLOCKS = ROOT / "results" / "attribution_v6" / "seizure_blocks.csv"
LABELS = V7 / "labels" / "ictal_channels_FINAL.csv"
STORED = V7 / "attribution_perseizure.csv"
P95 = 95


def die(msg):
    print("STOP:", msg)
    sys.exit(1)


for p in (PERNODE, BLOCKS, LABELS, STORED):
    if not p.exists():
        die(f"missing {p}")

blocks = pd.read_csv(BLOCKS)
labels = pd.read_csv(LABELS)
stored = pd.read_csv(STORED)

# channel order of the per-node dumps, fixed in the pipeline
ORDER = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
         "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
         "FZ-CZ", "CZ-PZ"]
IDX = {c: i for i, c in enumerate(ORDER)}


def auroc18(y, s):
    """AUROC over 18 channels with ties averaged, as in the pipeline."""
    pos, neg = s[y == 1], s[y == 0]
    if len(pos) == 0 or len(neg) == 0:
        return np.nan
    gt = (pos[:, None] > neg[None, :]).sum()
    eq = (pos[:, None] == neg[None, :]).sum()
    return (gt + 0.5 * eq) / (len(pos) * len(neg))


rows = []
for subj, g in labels.groupby("subject"):
    inter = np.load(PERNODE / f"{subj}_interictal_pernode.npy")
    ictal = np.load(PERNODE / f"{subj}_ictal_pernode.npy")
    med = np.median(inter, axis=0)
    mad = np.median(np.abs(inter - med), axis=0)
    mad[mad == 0] = np.nan
    b = blocks[blocks.subject == subj].set_index("seizure_idx")
    for _, r in g.iterrows():
        k = int(r.seizure_idx)
        if r.focal_generalized != "focal":
            continue
        blk = b.loc[k]
        seg = ictal[int(blk.row_start): int(blk.row_end) + 1]
        z = np.abs((seg - med) / mad)
        score = np.percentile(z, P95, axis=0)           # one value per channel
        y = np.zeros(18, dtype=int)
        for ch in str(r.ictal_channels).split("|"):
            if ch not in IDX:
                die(f"unknown channel {ch!r} in {subj} seizure {k}")
            y[IDX[ch]] = 1
        order = np.argsort(-score)                       # rank 1 = most anomalous
        rank = np.empty(18, dtype=int)
        rank[order] = np.arange(1, 19)
        annotated = rank[y == 1]
        n_s = int(y.sum())
        rows.append(dict(
            subject=subj, seizure_idx=k, n_annotated=n_s,
            auroc=auroc18(y, score),
            median_rank=float(np.median(annotated)),
            best_rank=int(annotated.min()),
            top1_is_annotated=int(y[order[0]] == 1),
            recall_at_S=float(y[order[:n_s]].sum() / n_s),
            in_top3=int((annotated <= 3).sum()),
            ranks="|".join(str(int(x)) for x in np.sort(annotated)),
        ))

out = pd.DataFrame(rows)
if len(out) != 62:
    die(f"expected 62 focal seizures, built {len(out)}")

# --- reproduction gate: our AUROC must equal the stored one
chk = out.merge(stored[["subject", "seizure_idx", "AUROC"]], on=["subject", "seizure_idx"], how="left")
if chk.AUROC.isna().any():
    die("some focal seizures are missing from attribution_perseizure.csv")
diff = (chk.auroc - chk.AUROC).abs()
TOL = 1e-4  # the stored file carries four decimals
if diff.max() > TOL:
    worst = chk.loc[diff.idxmax()]
    die(f"AUROC reproduction failed: {worst.subject} seizure {worst.seizure_idx}, "
        f"{worst.auroc:.6f} vs stored {worst.AUROC:.6f} (max diff {diff.max():.2e}, tolerance {TOL:.0e})")
print(f"reproduction OK on {len(out)} focal seizures "
      f"(max diff {diff.max():.2e}, within the four-decimal rounding of the stored file)")

out.to_csv(V7 / "rank_readout_perseizure.csv", index=False)

# --- summary, with the chance value beside every number
n = len(out)
med_rank = out.median_rank.median()
chance_rank = 9.5
top1 = out.top1_is_annotated.mean()
chance_top1 = (out.n_annotated / 18).mean()
recall = out.recall_at_S.mean()
chance_recall = (out.n_annotated / 18).mean()
best = out.best_rank.median()

lines = [
    f"focal seizures                          {n}",
    f"median rank of annotated channels       {med_rank:.1f}   (chance 9.5)",
    f"median rank of the best-ranked one      {best:.1f}",
    f"top-ranked channel is annotated         {top1:.3f}  ({out.top1_is_annotated.sum()} of {n}; chance {chance_top1:.3f})",
    f"recall at |S|                           {recall:.3f}  (chance {chance_recall:.3f})",
    f"seizures with >=1 annotated in top 3    {(out.in_top3 > 0).mean():.3f}",
    "",
    "per patient (median rank of annotated channels, top-1 hit rate):",
]
for subj, g in out.groupby("subject"):
    lines.append(f"  {subj}  n={len(g):2d}  median rank {g.median_rank.median():4.1f}   top-1 {g.top1_is_annotated.mean():.2f}")
txt = "\n".join(lines)
(V7 / "rank_readout_summary.txt").write_text(txt, encoding="utf-8")
print(txt)
