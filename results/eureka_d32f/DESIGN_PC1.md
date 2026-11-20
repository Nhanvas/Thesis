# DESIGN_PC1 — retraining ablations 10a and 10b (Track F, chat D32-F, 20/11/2026)

Approved by the author 20/11 16:17 ("duyệt": PC1 before the number freeze of 22/11 evening). Written and committed
**before any run**; nothing below is a result.

## 1 · Question and why it matters for the final

The node input of the GAE has three blocks: the connectivity row (18), the relative band powers (5, delta–gamma) and
**seven absolute, amplitude-preserving features** (log band powers delta–gamma, log line length, kurtosis). Two
measured findings point at the node features:

- Adding the seven absolute features (model V1 → v2) raised the development sensitivity from 0.330 to 0.489 at the
  same false-alarm level (`results/eureka_d31f/T_past_ablations.md` row A1; older readout, micro mean) — but the false
  alarms of V5 are the patient's own high-amplitude non-seizure activity, the same activity that outranks the missed
  seizures (V5 Figure 18; one root cause for both, R215). Whether the amplitude features now *create* those false alarms
  in the V5 chain has never been measured.
- Gamma carried the heavy tail of false alarms when it was a separate readout (E11: owner of the top-2 % tail in 12 of
  15 patients; E21 / E21b: adding gamma lowered sensitivity). Gamma is also where muscle artefact lives. Whether the
  gamma powers inside the node input matter has never been measured.

The council will ask which input carries the detection. Both arms answer it with the thesis model and recipe only (GAE
kept, no change of direction — author 12:58).

## 2 · Arms (one factor each)

| arm | node input kept | reconstruction target kept | parameters (computed) |
|---|---|---|---|
| **R0** (control) | all 30 | all 12 (relative powers 5 + absolute 7) | 3,964 |
| **10a** | 23: connectivity 18 + relative powers 5 (no absolute features) | 5 relative powers | 3,285 (the size of V1, the model before the absolute features) |
| **10b** | 28: without relative gamma (column 22) and absolute gamma (column 27) | 10: without the two gamma targets | 3,770 |

Everything else is V5: the record training data (the 12 training patients' clean windows of the defense-time `.npz`,
270,190 windows; validation loss on the 3 validation patients), V5's feature constants (gate G-pc1const), the
architecture (two GCN layers 64 → 16, latent 16; decoder widths follow the kept columns), loss = adjacency MSE + 0.1 ×
feature MSE, Adam 1e-3, cosine schedule, batch 32, **200 epochs, last epoch, seeds 42 / 1 / 2 / 3**, window order of
torch's DataLoader (the thesis recipe, f1_core's tensor loop, bit-equal to `train_gae_v2.py` by the earlier gate G-vec).
The arm's input columns are cut from the same 30-value node input at training and at inference (`node_x` then
`keep_in`), so the inference construction is the record's. Then the V5 chain unchanged (per-channel Ledoit–Wolf
Mahalanobis → members → drift → ensemble → smoothing → budget with k recalibrated per variant by the label-free rule on
the development patients → localizer).

**Why R0.** The V5 checkpoints were trained on another machine and library version; a retrained model differs by its
platform even with the same seed. R0 is trained in the same notebook, on the same CPU, with the same code as 10a / 10b,
so **arm − R0 isolates the feature effect** (the practice of the remove-and-retrain literature, which retrains the
control too and repeats training over seeds, Hooker et al., 2019; variance from initialisation and data order can be as
large as the effect studied, Bouthillier et al., 2021). R0 − V0 is the size of that retraining variation (descriptive).

## 3 · Hypotheses (fixed before the run)

- **H10a:** without the absolute features the detector loses sensitivity (the V1 → v2 gain) **and** has fewer false
  alarms (amplitude no longer reaches the latent). Development 10a − R0: Δsensitivity < 0, ΔFP/day < 0.
- **H10b:** the gamma powers inside the node input do not carry the detection: development 10b − R0 ≈ 0 in sensitivity
  and F1 (CI containing 0), FP/day not higher.
- No pass / fail threshold beyond the R214 rule below; the paired differences with CIs are reported and the author
  decides how to use them.

## 4 · Readings and the R214 rule (written before the run)

1. **Feature effect (primary):** development, 4-seed per-patient means, own label-free point after the localizer, paired
   patient bootstrap (B = 10,000, chb01 + chb21 one unit) of **10a − R0** and **10b − R0** (`src/eur_pc1_merge.py`,
   `T_PC1.md`). Test, chb24 and Siena: the same differences, descriptive.
2. **Replacement (R214):** an arm (R0, 10a or 10b) replaces V5 only if, on development, **arm − V0** has F1 CI lower
   bound > 0 **and** Δsensitivity ≥ 0 (the aggregate's rule, unchanged: `src/eur_abl_aggregate.py`, `candidates.csv`);
   then scored once on test. Otherwise it is reported as an ablation with all arms shown. Three arms are tried; this is
   disclosed.
3. Every gate below must PASS; a failed gate stops the run and nothing is read.

## 5 · Gates (in the notebook)

| gate | what it checks |
|---|---|
| G-pc1const | V5's feature constants = `train_gae_v2.norm_constants` on the record training windows (relative ≤ 1e-9) |
| G-pc1vec | the arm training loop with every column kept = `f1_core.train` (chb01, 2,000 windows, 2 epochs, seed 42): max weight difference **0**; each arm trains 2 epochs with a falling loss |
| training | window count = V5's `n_train` (270,190) and validation counts = V5's `n_val`, else STOP; G2 (last loss < first) per seed |
| record gates | G-self, G-data, SMOKE, R1.0-dev / -test, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker (as EUR_ABL) |
| M0 (merge) | the three runs' V0 rows identical (`per_subject`, `errors`, `curve`), else STOP |
| A0 / A1 | the aggregate's gates (record metric; every case × variant × seed × arm × stage present) |

Synthetic test `src/eur_pc1_synthetic_test.py` (container only): the three notebooks end to end (2 epochs), and
non-circular checks — R0 = `f1_core.train` on the training cases exactly; an arm re-trained in the main process = the
pool worker's checkpoint exactly; the 10b scalar recomputed from the *training* construction of the node input
(`model_cmp_core.node_input`), columns dropped by index, a per-window forward and Ledoit–Wolf per channel = the stored
scalar; negative paths (edited module, changed V0 rows at merge, wrong window count).

## 6 · Cost (measured basis)

Three notebooks, one arm each (`EUR_PC1_R0`, `EUR_PC1_10a`, `EUR_PC1_10b`), three verified Kaggle CPU accounts in
parallel. Training: 4 seeds in parallel took 14,030 s (3.9 h) in the R1 rerun (`results/r2/r1_system/run/models/
*_DONE.json`, 8.26 ms per step, 1,692,400 steps per seed, 3.2 GB peak per worker); 10a / 10b have fewer columns, so
they are not slower (computed). Scoring V0 + one arm ≈ 0.4–0.7 h (EUR_ABL8B 0.378 h with two variants; computed).
Total ≈ 4.5–5 h per notebook, inside Kaggle's 12-h limit. Outputs ≈ 20 KB per checkpoint (12 checkpoints committed with
the run folders, as the V5 checkpoints are).

## 7 · Literature

- Hooker, S., Erhan, D., Kindermans, P.-J., & Kim, B. (2019). A benchmark for interpretability methods in deep neural
  networks. *NeurIPS 32*, 9737–9748. arXiv:1806.10758 — removing inputs without retraining confounds information loss
  with distribution shift; remove **and retrain**, repeat training (5 times there). Applied: the arms are retrained, the
  control is retrained, 4 seeds.
- Bouthillier, X., et al. (2021). Accounting for variance in machine learning benchmarks. *MLSys 3*.
  https://doi.org/10.48550/arXiv.2103.03098 — initialisation and data order change results markedly; compare under the
  same sources of variation. Applied: R0 as the same-platform control; paired patient bootstrap.
- Hossain, M. S., Sadi, M. A. A., & Al Azad, A. K. (2026). Multi-domain feature engineering and stacked ensemble
  learning for epileptic seizure detection. *Neuroscience Informatics*. https://doi.org/10.1016/j.neuri.2026.100302 —
  paired feature-family ablations on CHB-MIT under patient-level protocols; the amplitude (time-domain) family carried
  most of the transferable information (supervised; context for H10a, not a comparison).

## 8 · What this design does not do

No new feature, no architecture search, no change of the readout; 11a / 11b (edge type) stay for after the freeze
(graph rebuild). If no arm meets R214, the deliverables keep V5's numbers and the arms answer the Q&A question "which
input carries the detection" with the measured differences.
