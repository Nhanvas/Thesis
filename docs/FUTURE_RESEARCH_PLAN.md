# FUTURE_RESEARCH_PLAN — Track F: validation and limits after the model comparison (rev 0 DRAFT, 2026-11-05, chat D11-M)

*Repo: `docs/FUTURE_RESEARCH_PLAN.md` + project file. **DRAFT** — the next chat (F1) verifies every assumption in the
code, completes the open design items (§8) with the author, and only then marks it rev 1 "fixed". Nothing runs before
rev 1. Any change after rev 1 is logged in §9 before results are seen. Replaces `V10_PLAN.md` (suspended 02/11; its
B2, B3, B4 are carried here; B0/B1 (kNN) stay dropped, R88).*

---

## 0 · Why (one paragraph)

The defense moved to **09/11**; the slides were submitted on 04/11. This track runs **in parallel on Kaggle** and does
not change the thesis system or the demo before the defense (R93). It answers what the review and the model
comparison left open: (1) **cô 04/11:** one fixed split or one fixed CV partition can be lucky or unlucky — repeat
training and testing on **several random patient partitions** and report the average and spread; (2) **the model
comparison (04/11):** an autoencoder identical to the GAE but without message passing (MLP-AE) found the same
seizures with 27 % fewer false alarms on one partition and one seed — is that stable across partitions and seeds, and
why does it happen?; (3) **limits named in the thesis:** offset error, weak/short seizures missed by every model, and
the open question of what the graph adds (R91).

## 1 · What we already know (do not rediscover)

| fact | source |
|---|---|
| GAE 4-fold CV (24 cases / 23 subjects; folds by a fixed stratified rule): 0.735 / F1 0.203 @ 28.4 FP/day; on the 8 thesis test patients 0.581 (37/76) | `results/v9_x3/`, S18 §18.4, §18.6 |
| the 4 seeds 42/1/2/3 of the thesis system share **one split** (training randomness only) | record; instructions §3 |
| six single models on that CV: only the MLP-AE differs from the GAE in F1 (+0.070 [+0.026, +0.117]); same 115 seizures, 827 vs 1,129 false alarms; SVM lower sensitivity; every model misses the same weak, short seizures (≈ 1.3× own background, ≈ 30 s) | `results/model_cmp/`, `MODEL_CMP_ANALYSIS.md` |
| both autoencoders rebuild the graph (inner-product decoder); only the GAE propagates along edges | `src/model_cmp_core.py`, `src/retrain/gae_joint.py` |
| measured Kaggle times: GAE fold training 3.05–3.94 h (PyG loader, 200 epochs); MLP-AE 1.06–1.40 h (vectorised loop); CNN 2.5–2.8 min per fold; trees 5–6 min per fold; IF < 10 min for 24 cases; linear SVM 1.0–2.2 h per fold | fold jsons; `results/model_cmp/raw/*/jobs.json` |
| the vectorised GCN training loop equals `train_gae_v2.py` bit for bit on CPU (3 epochs, max abs. weight difference 0); not yet timed on a T4 | chat D11-M, rev 1 tests |
| CPD helps the onset (median 32 → 12 s) but not the offset (20 → 24 s); a contiguous-run rule gives 16 s | NUMBERS_LOCK, board rev 40 §3 |

## 2 · Questions (only these)

| id | question | answer comes from |
|---|---|---|
| **F1** | How much do the CV results of the GAE depend on **which patients fall in which fold** (and on the training seed)? → average and spread over random partitions (cô 04/11) | repeated random 4-fold CV |
| **F2** | Is the MLP-AE's advantage over the GAE **stable** across partitions and seeds? | same runs as F1 (paired, same partitions) |
| **F3** | **Why** does message passing add false alarms? (hypothesis: neighbour mixing spreads one channel's local event into several channels' latents and raises the 6th/9th/12th-largest order statistics) | analysis of saved per-channel distances on false-alarm windows, both models |
| **F4** | What does the graph show that a non-graph model cannot? (R91 graph insight analyses) | I1–I3 on saved latents / reconstructions |
| **F5** | Can the offset error be reduced without changing detections? (B2) | recomputation from saved events (container) |
| **F6** | Can new input features catch the weak, short seizures every model misses? (B3) | new feature extraction — **after the defense**, designed after F1–F3 |

Not questions here: more model families (closed, instructions §10); kNN (R88); combined scores (R89); LOSO (23 trainings
per model; listed as future work beside F1); raw-EEG deep models (future work).

## 3 · F1 + F2 — repeated random patient-wise 4-fold CV (the main run)

**Design (proposed; F1 chat confirms):**
- **Partitions:** R new random partitions, r = 1 … R, each a **stratified group 4-fold split** of the 23 subjects
  (24 cases; chb01 + chb21 one group): groups binned by seizure count (counts from `results/v9_x3/folds.json`, no new
  annotation reading), shuffled with `random_state = r`, assigned to balance seizures per fold. The existing
  partition (`folds.json`, rule-based) is kept as **partition 0** with its committed results. Partitions are generated
  and **committed before any training** (`results/f1_repcv/partitions.json`), with a check that no two partitions are
  identical and that every case is held out exactly once per partition.
- **Seeds:** partition r trains with seed r (new split **and** new initialisation per repetition — "mỗi seed 1 split",
  cô 04/11). Partition 0 keeps seed 42.
- **Models:** **GAE** (thesis recipe: `v9_x3_train_fold.py` constants per fold, 200 epochs, last kept, no early stopping)
  and **MLP-AE** (`model_cmp_core.mlp_train`, same recipe) — required. Optional, cheap (author decides, §8):
  Isolation Forest (no training; partition-independent scores, only k changes), gradient-boosted trees, 1-D CNN.
  Linear SVM excluded (1–2 h per fold, worst row).
- **Chain:** unchanged frozen chain (`v9_e1_baselines.evaluate_arm`; k calibrated per fold on that fold's training cases
  by `p3_levers.calibrate`), SzCORE.
- **Training loop:** the vectorised loop (needed for the time budget). Gate before use: on fold 1 of partition 0, a GAE
  trained by the vectorised loop on Kaggle GPU for 2 epochs must match a `v9_x3_train_fold.py` run of 2 epochs on the
  same device within float tolerance (weights) — and the full 200-epoch retrain of partition-0 fold 1 is **not**
  required to equal the committed checkpoint (GPU non-determinism), only to give the committed fold's events within
  the documented tolerance (tp exact or ±1 per case; reported, not gated).

**Outputs:** per partition × model × case: tp, fp, n_ref, nonict_h (own point, fixed 0.005, both stages), curves, window
AUROC, per-seizure caught; training logs; checkpoints (`data/models_f1/`, not committed).

**Pre-registered reading (fixed at rev 1):**
- F1: report per partition the per-case mean sensitivity, precision, F1, FP/day of the GAE; the **mean ± SD across
  partitions** (split + seed variability) **and** the patient bootstrap of the across-partition mean (uncertainty).
  Statement: "over R + 1 random partitions, the GAE's CV sensitivity is m ± s".
- F2: per partition the paired subject bootstrap of ΔF1 (MLP-AE − GAE); the advantage is called **stable** if ΔF1 > 0 in
  ≥ 80 % of partitions **and** the CI of the across-partition mean ΔF1 excludes 0; otherwise "not stable".
- No model selection on these results; the thesis system stays as is.

**Budget (estimate; the smoke measures and the notebook refuses to start what does not fit):** with R = 5: GAE 20 fold
trainings × ≈ 1.5–3.5 h + MLP-AE 20 × ≈ 1.1–1.4 h ≈ **50–95 GPU hours**; 4 accounts × 30 h per week. One notebook = one
model × one partition (4 folds; GAE ≈ 6–14 h → may need 2 notebooks per partition). With R = 3: ≈ 30–57 GPU hours.

## 4 · F3 — mechanism of the MLP-AE gain (container + one Kaggle CPU pass)

- Inputs: per-channel distances D of both models on partition 0 (re-dump with the committed GAE fold checkpoints and the
  MLP-AE checkpoints of the comparison — tiny files; commit them or put them in a Kaggle dataset, §8).
- Test (to fix at rev 1): in each model's false-alarm events vs true detections, the number of channels whose robust-z
  exceeds a fixed threshold and the spatial spread over graph neighbours; prediction of the hypothesis: GAE false alarms
  recruit more channels than MLP-AE false alarms at the same windows; checked on more than one subject group.

## 5 · F4 — graph insight analyses (R91; board rev 40 §4)

I1 edge reconstruction map during seizures · I2 learned network (Z·Zᵀ) background vs seizure vs anatomy · I3 spread over
the graph. **Honest constraint found in the comparison:** the MLP-AE also has the inner-product decoder, so I1/I2
"graph reconstruction" is not unique to the GAE; each analysis is run on **both** models and only what differs is
attributed to message passing. Rule for every figure fixed before drawing; real EEG; a number.

## 6 · F5 — offset rule (B2; container, any time)

Onset from CPD, offset from the contiguous-run rule; recompute from saved events (development, test 4 seeds, chb24,
Siena where available); median absolute errors; confirm detections and false alarms unchanged. Analysis only before the
defense; adoption is an after-defense decision.

## 7 · F6 — features for weak, short seizures (B3; after the defense)

Rhythm / morphology features (periodicity, spectral-peak stability, line-length slope) on the raw EEG; needs a new
feature extraction (Kaggle with the CHB-MIT EDF dataset, or the laptop after the defense). Designed after F1–F3.

## 8 · Open design items for the F1 chat (author decides; nothing runs before)

| # | item | proposal |
|---|---|---|
| O1 | number of random partitions R | 5 (fallback 3 if the smoke projects > 90 GPU h) |
| O2 | partition type | repeated stratified group 4-fold (recommended) vs repeated random 12/3/8 split |
| O3 | seeds | new seed per partition (recommended) |
| O4 | optional models in F1 | IF + trees + CNN (cheap) yes / no |
| O5 | MLP-AE checkpoints for F3 | commit to the repo (`results/model_cmp/ckpt/`, 8 files × ~20 KB) |
| O6 | order | F1/F2 runs start first (long); F5 and F3 in the container while they run; F4 after F3; F6 after the defense |
| O7 | use before 09/11 | verified F1/F5 results may enter **Q&A answers only** (not the submitted slides); otherwise future work |

## 9 · Change log

| when | change | reason | seen results? |
|---|---|---|---|
| 05/11 08:45 | rev 0 draft | author: future research track after slides submitted; cô 04/11 | no |
