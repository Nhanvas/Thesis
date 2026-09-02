# PROVENANCE — checkpoint identity (MACHINE-GENERATED, DO NOT EDIT BY HAND)

Generated `2026-09-02 10:43` local by `src/verify_provenance.py --full`.
Every number below was measured at generation time. Regenerate rather than edit.

## Identity test

A checkpoint is canonical **iff** it reproduces the committed one-shot TEST components
`results/phaseB/tier2/ens_test_tf/components/zrecon_*` at Pearson corr = 1.0000000.
Filenames and the legacy constants 0.8676 / 0.836 are **not** identity evidence — they are
pre-rebuild §0 values.

## Canonical checkpoint

- path: `data/models_retrain/gae_joint_seed42.pt`
- size: 15258 B
- sha256: `dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108`
- bias fingerprint: **1.1597**
- chb13 recon AUROC: **0.8319**
- zrecon vs committed TEST components: **corr = 1.0000000 (worst of 16/16)**

## GAE seeds (RoR §7 robustness set)

| file | sha256 (16) | bias_fp | chb13 recon AUROC |
|---|---|---|---|
| `gae_joint_seed1.pt` | `6ffb9f5aa505178d` | 1.3705 | 0.8349 |
| `gae_joint_seed2.pt` | `a32e390063b01028` | 1.5801 | 0.8326 |
| `gae_joint_seed3.pt` | `33f350e22a162229` | 1.6370 | 0.8339 |

## Quarantined pre-rebuild §0 artifacts — DO NOT USE

`archive/pre_rebuild_s0/` — the §0 joint GAE and its per-node dumps. They correlate
0.987–0.999 with canonical output, close enough to pass any spot check. See the README there.

## Session gate

```bash
python src/verify_provenance.py        # ~20 s, exit 0 = canonical
```
