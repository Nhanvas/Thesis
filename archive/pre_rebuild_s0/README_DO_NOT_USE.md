# PRE-REBUILD §0 ARTIFACTS — DO NOT USE, DO NOT CITE

Everything in this directory belongs to the **§0 pre-rebuild** joint GAE, which is **not** part of
the rlg pipeline of record. Kept for provenance per PREREG_01 ("kept and archived, never deleted").

| artifact | what it is |
|---|---|
| `best_model_joint_lambda01.pt` | §0 joint GAE. bias fingerprint **0.8676**, chb13 recon AUROC **0.8360** |
| `pernode/` | per-node recon dumps generated from the §0 model above |

## Why this is a trap

These artifacts correlate **0.987–0.999** with the canonical ones. That is close enough to look
identical in any spot check, and close enough to reproduce RoR's headline shape — but they come from
different weights. On 2026-09-01 this nearly caused the attribution chapter to be written about the
wrong model, and briefly caused the canonical checkpoint to be misidentified as corrupt.

## The canonical checkpoint

`data/models_retrain/gae_joint_seed42.pt` — bias fingerprint **1.1597**, chb13 recon AUROC **0.8319**.
Verified against the committed one-shot TEST components
(`results/phaseB/tier2/ens_test_tf/components/zrecon_*`): Pearson **corr = 1.0000000 on 16/16 arrays**,
via `src/verify_ckpt_vs_components.py`. The §0 model scores 0.987–0.999 on that same test.

**Identity test, not a name test.** Never identify a checkpoint by filename or by the 0.8676 / 0.836
constants — those are §0 values. Run `src/verify_provenance.py`. See `docs/PROVENANCE.md`.