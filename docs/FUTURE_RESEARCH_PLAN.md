# FUTURE_RESEARCH_PLAN — Track F: validation and limits after the model comparison (rev 1 FIXED, 2026-11-05, chat D12-F)

*Repo: `docs/FUTURE_RESEARCH_PLAN.md` + project file. **Rev 1 = fixed with the author (05/11, 11:12).** Every
assumption of rev 0 was checked in the code (§10). Any change from now on is logged in §9 **before** results are seen.
Replaces rev 0 in full. Replaces `V10_PLAN.md` (suspended 02/11; its B2, B3, B4 are carried here; B0/B1 (kNN) stay
dropped, R88).*

---

## 0 · Why, and what Track F is (and is not)

The defense is on **09/11**; the slides were submitted on 04/11. Track F is an **independent research track** that runs
on Kaggle (cloud) from now, through the defense day and after it. It never changes the submitted slides, the thesis
system or the demo before the defense (R93, R98); verified results may enter Q&A answers only. It answers what the
review and the model comparison left open: (1) **cô 04/11:** one fixed split or one fixed CV partition can be lucky or
unlucky → repeat training and testing on **several random patient partitions**, each with its own training seed, and
report the average and the spread; (2) **the model comparison (04/11):** an autoencoder identical to the GAE but without
message passing (MLP-AE) found the same seizures with 27 % fewer false alarms on one partition and one seed — is that
stable, and why?; (3) **limits named in the thesis:** offset error, weak/short seizures missed by every model, and
what the graph adds (R91).

**Working rules (author 05/11):** nothing is believed until it has run and passed verification; every new failure
analysis or improvement idea is put to the author with a proposal and runs only after approval; an improvement that
survives verification is recorded and may become the next system version **after the defense** (author decision; a
change of the scoring method touches the registered title — registration-form question). The author's laptop runs
nothing in Track F.

## 1 · What we already know (verified, do not rediscover)

| fact | source |
|---|---|
| GAE 4-fold CV (24 cases / 23 subjects; folds by a fixed stratified rule): 0.735 / F1 0.203 @ 28.4 FP/day; on the 8 thesis test patients 0.581 (37/76) | `results/v9_x3/`, S18 §18.4, §18.6 |
| the 4 seeds 42/1/2/3 of the thesis system share **one split** (training randomness only) | record; instructions §3 |
| six single models on that CV: only the MLP-AE differs from the GAE in F1 (+0.070 [+0.026, +0.117]); same 115 seizures, 827 vs 1,129 false alarms; SVM lower sensitivity; every model misses the same weak, short seizures (≈ 1.3× own background, ≈ 30 s) | `results/model_cmp/`, `MODEL_CMP_ANALYSIS.md` |
| both autoencoders rebuild the graph (inner-product decoder); only the GAE propagates along edges | `src/model_cmp_core.py`, `src/retrain/gae_joint.py` |
| measured Kaggle times (committed runs): GAE fold training (PyG loader, T4) 10,985–14,171 s for 1.74–2.28 M steps (≈ 6.3 ms/step, computed); MLP-AE 3,899–5,088 s per fold incl. scoring (≈ 2 ms/step, computed); GAE scoring only 66–72 s per fold (CPU) | `results/v9_x3/models/fold*/*.json`; `results/model_cmp/raw/*/jobs.json` |
| **new (05/11):** the tensor-batch GAE training loop equals the PyG DataLoader loop of `v9_x3_train_fold.py` **bit for bit on CPU** (max weight difference 0; synthetic windows, torch 2.15 / PyG 2.7.0); re-checked on real windows by gate G-vec in every notebook | this chat, `src/f1_core.py` |
| **new (05/11):** single-thread CPU speed in the build container: GAE 3.1 ms/step, MLP-AE 1.4 ms/step; 2 threads are not faster (launch-bound) → a GPU is not needed for speed; Kaggle's own speed is measured by the smoke | this chat (container, measured there; not a Kaggle number) |
| CPD helps the onset (median 32 → 12 s) but not the offset (20 → 24 s); a contiguous-run rule gives 16 s | HANDOFF rev 2 (record), board rev 40 §3 |
| committed results contain **no score arrays or event lists** of the thesis system (only error tables, e.g. `results/e23_test_look7/errors.csv`) → F5 needs a recomputation run, not a container-only analysis | repo check 05/11 |
| the MLP-AE checkpoints of the comparison are **not committed** (only on the laptop, `data/models_cmp/`) | repo check 05/11 |

## 2 · Questions (only these)

| id | question | answer comes from | when |
|---|---|---|---|
| **F1** | How much do the GAE's CV results depend on **which patients fall in which fold** (and on the training seed)? → average and spread over random partitions (cô 04/11) | repeated random 4-fold CV (§3) | now |
| **F2** | Is the MLP-AE's advantage over the GAE **stable** across partitions and seeds? | same runs, paired (§3) | now |
| **F3** | **Why** does message passing add false alarms? (hypothesis: neighbour mixing spreads one channel's local event into several channels' latents and raises the 6th/9th/12th-largest order statistics) | per-channel distances of both models, from committed checkpoints (§4) | after F1/F2 |
| **F4** | What does the graph show that a non-graph model cannot? (R91) | I1–I3 on both autoencoders (§5) | after F3 |
| **F5** | Can the offset error be reduced without changing detections? (B2) | recomputation on Kaggle, CHB-MIT + Siena (§6) | after F1/F2 are launched |
| **F6** | Can new input features catch the weak, short seizures every model misses? (B3) | new feature extraction (§7) | after the defense |

Not questions here: more model families (closed, instructions §10); kNN (R88); combined scores (R89); raw-EEG deep
models (future work); LOSO (future work beside F1).

## 3 · F1 + F2 — repeated random patient-wise 4-fold CV (the main run) — FIXED

**Partitions** (`src/f1_build_partitions.py` → `results/f1_repcv/partitions.json`, **committed before any training**):
- unit = subject (23 groups; chb01 + chb21 one group); seizure counts per group from `results/v9_x3/folds.json` (no new
  annotation reading);
- partition r uses `numpy.random.default_rng(r)`: random tie-break key per group → groups sorted by seizure count
  (descending, ties by the key) → consecutive **blocks of 4** → each block dealt to the 4 folds by a random permutation
  ("rank blocks of 4"; stratified: every fold gets one group of each size class);
- **partition 0** = the committed CV (`folds.json`); it is a member of the same family (each of its blocks of 4 is dealt
  to all four folds — checked); it keeps its committed results (GAE and MLP-AE, seed 42);
- 10 random partitions generated now (r = 1 … 10); checks passed: every case held out exactly once per partition,
  chb01/chb21 together, no partition equal to another or to partition 0; seizures per fold 36–58 (partition 0: 42–51);
  adjusted Rand index vs partition 0 −0.02 … 0.23, between random partitions mean 0.03 (max 0.21). A literal reading of
  rev 0 (sort + serpentine with random ties) was rejected: it reproduces partition 0's fold totals (ARI 0.21–0.49);
- **R = 5 now** (partitions 1–5); partitions 6–10 may run **after the defense** as a separate, later report; the R = 5
  reading below is the one reported first and is not replaced by a selection.

**Seeds:** partition r trains with seed r (GAE and MLP-AE share it → paired); partition and seed are confounded by
design (cô: "mỗi seed 1 split"); stated as such.

**Models:** GAE and MLP-AE only (O4). Recipe = the thesis fold recipe, unchanged: clean windows of the fold's training
cases; f7 constants **recomputed for each fold** from its training cases; node input 30; Adam 1e-3, cosine T_max 200,
batch 32, **200 epochs, last kept**, no validation subset, no early stopping; 3,964 parameters each.

**Training loop:** tensor batches whose window order reproduces `DataLoader(shuffle=True, generator=seed)` exactly
(gate G-vec). **Device:** Kaggle cloud; the same notebook runs with Accelerator **None** (CPU: W = min(4, cores,
RAM / 6 GB) worker processes, 1 thread each, deterministic) **or GPU T4 x2** (4 workers on cuda:0 / cuda:1). Rule fixed
now: the smoke is run once in each mode; **GPU is used unless CPU's projected wall time is shorter by ≥ 10 %** (author
preference for GPU; CPU is bit-deterministic, GPU is not because of atomic scatter — not a design difference). The
device is not a design variable; it is recorded per job.

**Chain:** frozen and unchanged (`v9_e1_baselines.evaluate_arm` through the model comparison's construction); k
calibrated per fold on that fold's training cases (median q_i = 0.005, label-free); SzCORE.

**Gates (every notebook; STOP on failure):**
| gate | check |
|---|---|
| D0 | n_ref and non-ictal hours of the 24 cases = `results/v9_x3`; clean training-window counts = the committed fold models (`model_cmp_core.gate_D0`) |
| G-const | partition 0's f7 constants recomputed by the new code = the committed fold models' constants (relative ≤ 1e-9) |
| G-vec | GAE tensor loop = the PyG loop of `v9_x3_train_fold.py` (CPU, 2,000 real windows, 2 epochs, seed 42): max weight difference ≤ 1e-6 (exact 0 expected) |
| G-mlp | the new MLP-AE loop = `model_cmp_core.mlp_train` (CPU, smoke subset): max weight difference ≤ 1e-6 |
| GG0 | the new chain on partition 0 with the committed GAE fold checkpoints reproduces `results/v9_x3` (tp/fp of 48 rows and the 185 caught flags exactly; k within 1e-6 relative) |
| smoke | 2-epoch end-to-end job of each model + speed of W concurrent workers → `projection.json`; the full run is refused if the projection exceeds 10.5 h; a job starts only if its projected end is before 11.3 h |
| per job | training windows = committed clean counts of the training cases; 3,964 parameters; G2 (last-epoch loss < first) |
| aggregate | all gates PASS; 200 epochs; identical code and partitions sha in every notebook (= the committed `partitions.json`); 8 jobs per partition; 24 cases × 2 models × 2 points × 2 stages; n_ref / non-ictal hours identical across partitions; each case scored in the fold `partitions.json` assigns it |

**Outputs per partition** (`/kaggle/working/f1_repcv/p{r}/` → downloaded to `results/f1_repcv/raw/p{r}/`): per job
tp, fp, n_ref, non-ictal hours at the own point and at the fixed 0.005 point (detector + localized), detector curve,
window AUROC, per-seizure caught, training log, checkpoint + meta (≈ 20 KB each; **committed**, O5), `fit.json`
(ms/step, peak RAM, device); per notebook `run_meta.json`, `gates.json`, `projection.json`, `jobs.json`.

**Pre-registered reading** (`src/f1_aggregate.py`, written before any result; per-case means over the 24 cases, own
label-free point, after CPD; P = 6 partitions incl. partition 0; random-only = sensitivity analysis):
- **F1:** per partition, sensitivity / precision / F1 / FP/day / window AUROC of each model, also on the 8 thesis test
  patients and on the other 16 cases; across partitions **mean ± SD and range** — the SD is the sensitivity to the
  partition and seed, **not** uncertainty (training sets overlap; there is no unbiased variance estimator for k-fold
  CV, Bengio & Grandvalet, JMLR 2004); uncertainty = **paired-subject bootstrap** (23 units, B = 10,000) of the
  across-partition mean (each case first averaged over partitions). Statement form: *"over P patient partitions (each
  with its own training seed), the GAE's 4-fold CV per-case mean sensitivity is m ± s (range a–b) at f ± g FP/day; 95 %
  CI of the mean over subjects [lo, hi]."*
- **F2:** per partition, paired subject bootstrap of ΔF1 = MLP-AE − GAE; across partitions n_pos = partitions with
  ΔF1 > 0 and the bootstrap CI of the across-partition mean ΔF1. **"Stable advantage of the MLP-AE" iff n_pos ≥ ⌈0.8 P⌉
  (= 5 of 6) AND the CI's lower bound > 0**; "stable advantage of the GAE" symmetrically; otherwise **"not stable"**.
- **Secondary (pre-registered now, never decisive):** ΔF1 at the fixed 0.005 budget; each model's sensitivity on its
  detector curve at the GAE's own FP/day (same alarm rate); ΔFP/day at the own point; Δwindow AUROC; seizures caught and
  false alarms (counts) per partition.
- No model selection on these results; the thesis system stays as is before the defense.

**Budget (estimate; the smoke measures):** per fold 1.74–2.28 M training steps → at the container's single-thread
speed GAE ≈ 1.5–2.0 h, MLP-AE ≈ 0.7–0.9 h per job; one partition = 8 jobs on 4 workers ≈ 3–4 h wall (computed
estimate). R = 5 → 5 notebooks on the 4 existing accounts, about one night. CPU sessions use no GPU quota; **no new
Kaggle accounts** (Kaggle allows one account per person).

## 4 · F3 — mechanism of the MLP-AE gain (after F1/F2)

- Inputs: per-channel distances D of both models, recomputed from **committed checkpoints** (partition 0: GAE folds in
  the repo + MLP-AE folds copied from the laptop, O5; partitions 1–5: Track F checkpoints).
- Test (to be fixed in a plan revision **before** it runs, with the author): in each model's false-alarm events vs true
  detections, the number of channels whose robust-z exceeds a fixed threshold and their spread over graph neighbours;
  prediction of the hypothesis: GAE false alarms recruit more channels than MLP-AE false alarms at the same windows;
  checked in more than one partition.

## 5 · F4 — graph insight analyses (R91)

I1 edge reconstruction map during seizures · I2 learned network (Z·Zᵀ) background vs seizure vs anatomy · I3 spread over
the graph. Both autoencoders have the inner-product decoder, so every analysis is run on **both**; only what differs is
attributed to message passing. Rule for every figure fixed before drawing; real EEG; a number.

## 6 · F5 — offset rule (B2)

Onset from CPD, offset from the contiguous-run rule; detections and false alarms unchanged by construction (check).
**Not container-only** (no committed score arrays): a Kaggle recomputation with the committed thesis checkpoints
(`data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt`) on CHB-MIT (development + test + chb24, from `v9-x3-fold1/3`) and on
**Siena** (the public Kaggle dataset "Combined Siena Scalp and CHB MIT EEG Datasets" (Ryan Clarke) used in the original
runs — its contents and preprocessing identity to the thesis pipeline are verified first, by a gate reproducing the
committed Siena counts). Designed in its own plan revision after F1/F2 are launched; median absolute onset/offset
errors per set; adoption is an after-defense decision.

## 7 · F6 — features for weak, short seizures (B3; after the defense)

Rhythm / morphology features (periodicity, spectral-peak stability, line-length slope) on the raw EEG; needs a new
feature extraction (Kaggle with the raw EDF datasets). Designed after F1–F3.

## 8 · Decisions (author 05/11, 11:12)

| # | item | decision |
|---|---|---|
| O1 | number of random partitions | **R = 5 now**; 10 generated and committed; 6–10 after the defense, reported separately |
| O2 | partition type | repeated stratified group 4-fold, **"rank blocks of 4"** rule (verified: valid, random, balanced; partition 0 in the same family) |
| O3 | seeds | seed r for partition r, both models; partition 0 seed 42; nothing hard-coded to one partition (author: "random split trên từng seed") |
| O4 | optional models | **none** (GAE + MLP-AE only) |
| O5 | checkpoints | commit all Track F checkpoints; the author copies the 4 MLP-AE checkpoints of partition 0 from the laptop when convenient (`results/model_cmp/ckpt/`) |
| O6 | order | F1/F2 now; F5 next (Kaggle, CHB-MIT + Siena); F3, F4, F6 after |
| O7 | use before 09/11 | verified F1/F2 results may enter **Q&A answers only**; never slides; otherwise future work. Track F does not depend on the defense date |
| O8 | device | Kaggle cloud only (the laptop runs nothing); GPU T4 x2 unless the measured smoke shows CPU ≥ 10 % faster (rule in §3) |
| O9 | secondary readings | pre-registered in §3 |
| O10 | packing | one notebook = one partition × both models (8 jobs, 4 workers); `F1_SMOKE` + `F1_p1 … F1_p5` |

## 9 · Change log

| when | change | reason | seen results? |
|---|---|---|---|
| 05/11 08:45 | rev 0 draft | author: future research track after slides submitted; cô 04/11 | no |
| 05/11 12:30 | **rev 1 fixed**: partition rule "rank blocks of 4" (rev 0 wording ambiguous; literal reading near-copies partition 0); R = 5 now / 10 committed; seed r; GAE + MLP-AE only; Kaggle GPU or CPU by measured smoke (tensor training loop, verified equal to the PyG loop); gates D0, G-const, G-vec, G-mlp, GG0, smoke, per-job, aggregate; F2 rule as a count (5 of 6); secondary readings pre-registered; SD vs CI wording; F5 needs a Kaggle recomputation (no committed score arrays) incl. Siena; F3 needs MLP-AE checkpoints (O5) | chat D12-F: rev 0 verified against the code; author decisions 05/11 11:12 | no (no Track F run exists; synthetic tests only) |

## 10 · Rev 0 assumptions checked in the code (05/11)

| rev 0 assumption | finding |
|---|---|
| vectorised GCN training loop exists and equals `train_gae_v2.py` | **not in the repo** (only the vectorised inference `gae_D` and the MLP-AE loop); written in `src/f1_core.py`, equal bit for bit (synthetic, CPU), gated on real data |
| GPU needed; 50–95 GPU hours | **no**: training is launch-bound; CPU single thread is faster per step than the committed T4 runs; budget re-estimated (§3) |
| partitions "binned, shuffled, assigned to balance" | ambiguous; literal reading near-copies partition 0 → rule fixed as "rank blocks of 4" |
| reuse `model_cmp_core` for the chain | its fold lists, metas and k are tied to the committed CV → partition-aware wrapper `src/f1_core.py` (closed code untouched) + gate GG0 |
| partition-0 retrain needed as a gate | not needed: partition 0 keeps its committed results; GG0 + G-vec + G-mlp cover equivalence |
| "≥ 80 % of partitions" | ambiguous with few partitions → count rule ⌈0.8 P⌉ |
| F5 container-only from saved events | **no** score arrays committed → Kaggle recomputation (CHB-MIT + Siena) |
| F3 MLP-AE checkpoints | not committed → O5 |
