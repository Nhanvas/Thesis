# PHASE D — MASTER HANDOFF (read this FIRST, in full)
**Purpose:** start the Phase-D chat clean with the ENTIRE audit in hand — every lever tried,
every result, every conclusion, my (Claude's) reasoning, and Boti's decisions. Phase D runs
**independently** and must **never overwrite or alter Phase C / rlg**. rlg is the backup baseline.

> **On ANY number conflict, `docs/RESULTS_OF_RECORD_phaseB.md` WINS over this handoff and over memory.**
> **TEST is UNTOUCHED and stays one-shot. Never tune on the 8 TEST subjects.**
> **Backup point: git tag `phase-c-final` — if Phase D fails or runs out of time, `git checkout phase-c-final` restores the locked rlg thesis.**

---

## 0 · WHO / ROLE / OPERATING RULES (unchanged across the project)
- **Claude = senior Stanford/MIT-style research mentor.** Independent scientific judgment,
  proactive root-cause finding, honest negative results, never rationalizing low numbers.
  **Boti (Nguyen Quoc Trung Nhan, BEBEIU22184) is the final decision-maker.** Propose → he
  approves → he executes locally/Kaggle. **No autonomous substantive changes.**
- Communicate in **Vietnamese**; code/deliverables in **English**.
- **State hypothesis + falsification + stop-condition BEFORE any experiment.** Reproduce before
  trusting a number. Null-check every evaluation (null AUROC ~0.5). Archive-don't-delete. Commit same day.
- **Read before you build.** Read the relevant source file / RESULTS_OF_RECORD / prior negatives
  BEFORE writing code or proposing a lever. (This rule repeatedly saved whole experiment cycles in
  Phase C — e.g. the reweight lever was already dead on the record.)
- **Anti-rationalization:** never reframe a failed prediction as expected post-hoc; never move the
  goalpost after seeing a number. If you catch yourself mentally rewriting the criterion to pass, STOP.
- **Anti-fishing / hard limit:** each lever gets ONE pre-registered config + one shot. A "win" counts
  only if it's at the **event headline** (not a side budget), on **≥2/3 VAL subjects** (not 1), and
  survives **≥3/4 seeds**. A 1-subject/1-budget effect at n=3 VAL is a noise signature → reject without
  seed-burning. Do not sweep thresholds/weights to find a passing variant.
- **Gate on EVENT, not window.** The single most important Phase-C lesson: window/representation gains
  repeatedly die at the CPD-transfer. Test event-level early and cheaply; kill fast.
- If Claude drifts to diagnosis-only / long-no-code, Boti says **"build"** to cut to code.
- **Cursor (local Windows, CPU) for CPU work; Kaggle (notebooks, GPU) for training.** Kaggle = cells not
  bash; `/kaggle/working` writable only via code; datasets mount at non-standard nested paths — auto-discover
  with `rglob`, never hardcode. 4 Kaggle accounts run in parallel (`nhn2mm`, `norncreades`, +2). ~3.2 h/GAE-seed
  for the small rlg-class model; larger Phase-D models will be slower (measure GPU ETA before committing).
- **Timeline:** IELTS 9 Oct; thesis report due 15 Oct; defense Nov 2–3. Phase D has a *finite* window
  before the report/web-demo must take priority. Web demo (SzScan) can proceed in parallel and does not
  depend on Phase D succeeding.

---

## 1 · PROJECT OVERVIEW
- **Thesis:** "Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder
  and Change Point Detection." Biomedical Engineering, International University VNU-HCM. Supervisor
  Assoc. Prof. Hà Thị Thanh Hương ("cô" — methodological authority; document divergences for her review).
- **Goal:** fully unsupervised, patient-independent, event-level seizure detection; publishable (Q3 solid,
  Q2 ambitious); eventual clinical web demo (SzScan) for Vietnamese hospitals. Application framing =
  **post-hoc EEG review triage, NOT a real-time alarm.**
- **Dataset:** CHB-MIT Scalp EEG (PhysioNet), 18-channel bipolar montage, 4 s windows @ 256 Hz (1024 samp),
  bandpass 0.5–60 Hz + 60 Hz notch, z-scored per subject.
  - **Splits (LOCKED):** TRAIN = chb01,02,04,05,07,08,09,12,19,20,21,23 (12). VAL = chb10,11,22 (3).
    TEST = chb03,06,13,14,15,16,17,18 (8 subjects, 76 seizures, 278.2 interictal h).
  - **Preprocessing already artifact-rejects interictal** (±5 SD amplitude → drop); **ictal is NOT
    artifact-rejected** (seizure EEG is naturally high-amplitude; rejecting it would bias sensitivity).
- **Evaluation = SzCORE** (Dan et al., Epilepsia 2024), via the `timescoring` library. FP/day replaces
  specificity. Macro AUROC/AUPRC are the only valid cross-subject window metrics (rank-based, scale-
  invariant); threshold-dependent pooled window metrics are INVALID (unbounded per-subject score scales).

---

## 2 · THE LOCKED PIPELINE — rlg (system-of-record, the Phase-D bar)
**Source of truth: `docs/RESULTS_OF_RECORD_phaseB.md` §1–§6 (LOCKED).**

```
per-window graphs (wPLI+AEC, top-k20)
  → Joint GAE (seed 42; encoder 23→64→16 GCN, ~8.7k params)
  → 3 readouts: zrecon (recon-MSE), zlatent (latent-Mahalanobis, LedoitWolf on graph-mean 16-d Z,
                per-subject interictal fit — label-free), zgamma (gamma-AEC)
  → per-branch robust-z → EQUAL-weight ensemble (1/3 each)
  → PELT CPD (cpd_pipeline_v14, PELT on 15-win MA-smoothed ensemble)
  → label-free per-subject FP-budget operating point (PREREG_04)
  → SzCORE (timescoring)
```
- LSTM temporal branch **DROPPED** (unreproducible, code lost — PREREG_TIER2 Amendment A1). Its
  removal + the latent-Mahalanobis readout replacing it is the core Phase-B contribution.
- **Node features = `[An1 (18, R1 adjacency row, per-window max-norm) | Xn (5 band-powers)]` = 23-d.**
- **Ensemble weights: `src/ensemble_recipe.py` is the single source of truth** (equal 1/3; PREREG_03
  found the weight surface flat → equal weights as anti-overfit tie-break).
- **CPD algorithm: `src/cpd_pipeline_v14.py` is the locked source of truth** (has default-OFF, byte-exact
  hooks for a swappable SMOOTHER and a slope-gate — both tested-negative, kept as documentation).

### rlg LOCKED TEST numbers (seed 42, one-shot; quote from RESULTS_OF_RECORD §3)
| operating point | sens | prec | F1 | FP/day |
|---|---|---|---|---|
| rlg @ §0 balanced cell (m70/p0.5) | 0.645 | 0.099 | 0.172 | 38.4 |
| rlg @ §0 high-sens cell (m55/p0.3) | 0.763 | 0.065 | 0.120 | 72.0 |
| **rlg VAL-derived balanced (m50/p2.0) — honest headline** | 0.618 | **0.129** | **0.213** | **27.4** |
| rlg VAL-derived high-sens (m50/p0.5) | 0.711 | 0.068 | 0.123 | 64.4 |
| **Pooled TEST Pareto PEAK** | 0.474 | 0.387 | **0.426** | **4.9** |

- Frontier is reported as a **curve** (dominance vs §0, which peaked ~0.351), NOT a cherry-picked point.
  Inside the unsupervised patient-independent SOTA band (F1 0.32–0.43). (The "F1 0.361 @ 3.6 FP/day"
  figure used loosely in chat is a low-FP point on this same frontier — **confirm the exact headline
  point from RESULTS_OF_RECORD before quoting in the report; the record wins.**)
- **Window macro AUROC (TEST): 0.805.**
- **GAE seed-stability (VAL, 4 seeds {42,1,2,3}): window macro AUROC 0.929 ± 0.002; chb13 recon AUROC
  0.835 ± 0.001; event F1@3.6 VAL 0.51 ± 0.034. The event seed-SD (0.034) and window seed-SD (0.002)
  are the NOISE FLOORS any challenger must beat.**

---

## 3 · COMPLETE PHASE C AUDIT — every lever, result, reasoning, decision
Phase C goal was to **Pareto-improve rlg's metric** (Boti was previously critiqued on performance, so the
mandate was explicitly "optimize the number"). **Outcome: 0 levers improved the event headline. rlg is the
ceiling.** Full detail below so Phase D never re-treads settled ground.

### 3.1 Levers tried, in order (all VAL-gated, pre-registered)
| # | Lever (layer) | What it changed | VAL result | Verdict + Boti's decision |
|---|---|---|---|---|
| 1 | **C4-lite / TE ensemble branch** (decision) | rltg_te = 0.75·rlg + 0.25·zTE (directed Transfer-Entropy anomaly branch; PCA-12 + LedoitWolf readout) | +0.004 F1 @ B=40 but **−0.070 F1 @ B=3.6 headline** | Rejected as lever; kept as mechanism finding. Boti: banked as analysis contribution. |
| 2 | **C1 / median pre-CPD smoother** (decision) | median15 / median9 vs locked MA-15 | median15 −sens; median9 +0.004 @ B=40 but harmed headline; VAL@B=40 quantization-saturated (15 events/3 subj) | Rejected. |
| 3 | **slope-gate / C-onset** (decision) | reject high-level interictal PLATEAU change-points, keep rising onsets (MIN_SLOPE_PCT=75) | real WINDOW headroom (slope AUROC 0.918 vs level 0.823) but **seed42-specific**: seed42 +0.023 (< seed-SD 0.034); seeds 1/2/3 FAIL (ΔF1 −0.039…−0.065, sens −0.133) | Rejected — multi-seed caught a false-positive before one-shot. **This is why Phase D must multi-seed from the first round.** |
| 4 | **line-length / Hjorth node features** (feature) | per-channel scalar time-domain features | not built | Rejected a priori (Boti agreed): same class as band-powers, doesn't address directed-relationship failure, weak to defend. **NOTE: this is NOT the same as a genuine capacity/architecture change — see Phase D.** |
| 5 | **C4-full / multi-relational GAE** (representation) | joint R-GCN AE fusing symmetric R1 (wPLI+AEC) + directed R2 (TE) as two relations, non-shared encoder weights, per-relation decoders | 3-branch window macro **0.909**; 2-branch (latent+gamma) **0.926**; both < rlg 0.928 (2-branch = tie within seed-SD 0.002). No collapse (gate_R2 1.01–1.03). | NO-GO (pre-registered). Boti: KILL after the rlg-lg diagnostic confirmed the story. |
| 6 | **ensemble reweight / drop-recon** (ensemble) | drop recon → latent+gamma (lg) | **DEAD ON RECORD** — lg already measured worse at EVENT tier (§5: 0.579 balanced < rlg 0.618, VAL+TEST grids exist in `lg/`,`lg_test/`); PREREG_03 weight surface flat | Not re-run. Boti: confirmed skip after reading §5. |
| 7 | **artifact / signal-quality gate** (signal) | label-free grad_max gate suppressing FP-driving transient-artifact windows before CPD | pre-condition PASS (FP-prone interictal artifact-associated, AUROC 0.78–0.80, grad_max dominant); per-window gate flagged 85% ictal (unusable); **isolation gate** (spare sustained seizures) → ictal-flag 3.5%, VAL win **only @ 5 FP/day, 1 subject (chb11), headline 3.6 UNCHANGED** | Rejected — 1-subject/1-budget = noise signature; not seed-checked (hard-limit rule). Boti: agreed, no seed-burn. |

### 3.2 Mechanism findings (report-worthy positives extracted from the negatives)
- **Directed connectivity (TE) is complementary-but-insufficient.** It genuinely rescues symmetric-inverted
  subjects at the representation level: chb22 latent-mr 0.736→0.873 (**+0.137, ablation-confirmed**
  ΔR2=+0.126; C0: chb22 sym AUROC 0.22→TE 0.83, chb06 0.37→0.73). BUT it net-washes: ΔR2(chb11)=−0.049
  (TE hurts symmetric-good subjects), and the joint 2-relation encoder loses chb10 latent (0.816→0.757,
  **shared-capacity cost, NOT caused by R2**: ΔR2(chb10)=+0.040). This chb10 capacity loss is the seed
  of the Phase-D hypothesis (§5).
- **FP false-positives ARE artifact-associated** (grad_max jumps/pops the ±5-SD preproc lets through,
  AUROC 0.78–0.80), but seizures share high gradient, so per-window artifact gating can't separate them;
  only a duration-isolation gate spares seizures, and even then the FP gain doesn't reach the headline.
- **Window ≠ event, repeatedly.** rlg-lg (drop recon) is BETTER at window-macro (0.9386 > 0.928) yet WORSE
  at the event tier (lg 0.579 < rlg 0.618). PELT/CPD keys on sustained level shifts / onset sharpness, not
  rank separation — this is the CPD-transfer bottleneck that killed nearly every window-level gain.
- **Ceiling subjects chb06, chb14 are representation-limited** (oracle F1 ≤ 0.09) and sit in the LOCKED TEST
  set — they cannot be addressed without label leakage. chb16/chb17 are decision-limited.

### 3.3 Rejected earlier (pre-Phase-C, for completeness — do NOT re-propose)
CCM (no convergence at 4 s windows), learned graph structure / S2 GSL (residual gate → 0 by epoch 40 —
recon-interictal gives no signal to learn a discriminative graph; see `S2_S3_negatives.md`), Deep-SVDD /
compactness retrain (S2/S3 — small variants on the SAME small GAE, net-wash), Transformer baseline cited
earlier was a TUH result, NOT CHB-MIT (must not be cited as a CHB-MIT comparison).

### 3.4 Integrity self-corrections logged (so they're not misread later)
- Stage-0 input-fidelity band [0.78,0.88] for chb22 zTE was mis-specified too tight; measured 0.888
  (= 0.83 ± 0.058, reproduces C0 direction MORE strongly) — a band error, not an R2-input bug.
- At one point Claude over-generalized "TE-levers exhausted" into "all optimization exhausted" from an
  incomplete list, and defaulted toward closing prematurely; Boti + a second reviewer correctly forced a
  full sweep, which surfaced the artifact-gate lever and the capacity gap. **Phase D lesson: enumerate the
  WHOLE lever space with evidence before ever proposing to close.**

---

## 4 · KEY LEARNINGS / PRINCIPLES (accumulated — carry into Phase D)
1. **Gate on EVENT, early and cheap.** Window/representation wins die at CPD-transfer. Base-rate of window→event
   transfer in Phase C ≈ 0/7. Do not spend a week on a window win.
2. **Pre-register everything; one config per lever; no threshold/weight sweeps** (PREREG_03 already showed the
   weight surface is flat — sweeping it is fishing).
3. **Multi-seed from the first VAL round** (slope-gate seed42-win died on seeds 1/2/3). Seed-SD: window 0.002,
   event 0.034.
4. **A 1-subject/1-budget win at n=3 VAL is noise** — reject, don't seed-burn.
5. **Reproduce before trusting; null-check (AUROC ~0.5); watch for degenerate nulls** (dim≫n Mahalanobis gave
   spurious all-1.0 AUROC before — hence PCA-12 before LedoitWolf for high-dim readouts).
6. **Read the record before building** — reweight was dead-on-record; reading saved a cycle.
7. **Archive-don't-delete; parallel modules; rlg untouched.** Every Phase-C script had a TEST guard and lived
   in a parallel path.
8. **Attribution is an UNVALIDATED visual** (Gini 0/8 significant after BH-FDR; Test D TP-vs-FP AUROC 0.530 n.s.).
   Mark PROVISIONAL in the demo; it's coarse spatial plausibility, not validated localization.

---

## 5 · PHASE D — THE NEW DIRECTION (hypothesis + plan)
**Phase C kept two pillars FIXED and only changed things around the latent/score, or added a 2nd graph
relation to the SAME tiny encoder: (i) input features = 5 band-powers, (ii) encoder = 2-layer GCN ~8.7k
params. Phase D questions the pillars themselves — a genuinely different direction, not another lever around
the baseline.**

### 5.1 Core hypothesis
**H_D: the representational bottleneck is the encoder's capacity (and/or the input feature set), NOT the
graph-relation type or any post-latent processing.** Evidence motivating it: an ~8.7k-param encoder is tiny
by modern graph-DL standards; C4-full's chb10 harm was explicitly a *shared-capacity* cost (adding a 2nd
relation to an encoder too small to exploit even one). If true, a higher-capacity / different-architecture
encoder (or a richer feature set) could lift the representation enough to *transfer* to the event headline —
the one thing no Phase-C lever achieved.

### 5.2 Recommended Stage-0 (Boti to confirm the order; Claude leans capacity-first)
- **Stage 0A — CAPACITY (recommended first; cleanest isolation):** keep input features fixed (23-d) and the
  single symmetric relation, but *scale the encoder* — deeper GCN, wider hidden dim, or a different
  architecture (GAT with attention, VGAE, GraphSAGE, or a graph-transformer encoder). Test directly whether
  "encoder too small" is the bottleneck. **Watch overfit hard** (12 train subjects is small — S2 collapsed
  for a related reason); regularize, and monitor a held-out capacity/overfit signal per epoch.
- **Stage 0B — FEATURES (if capacity alone doesn't transfer):** enrich node features beyond 5 band-powers
  (spectral entropy, Hjorth, connectivity-derived node stats, learned features) — but only if 0A suggests
  the encoder *can* use more.
- Either way: **Stage-0 = cheap window check on VAL (esp. chb22 rescue + no chb10 harm), then EVENT gate
  early.** GO to multi-seed only on a window signal that plausibly transfers; **kill on event-transfer
  failure fast** (the Phase-C base rate demands it).

### 5.3 Pre-registered gates (bake in from the start)
- **Multi-seed from the first VAL event round.** GO iff event-F1 improvement is at the **3.6 FP/day headline**,
  **≥2/3 VAL subjects**, **≥3/4 seeds**, mean ΔF1 above the event seed-SD (0.034). Window macro is a pre-screen
  only, never the gate.
- **Falsification:** no event-headline Pareto-win over rlg at matched FP/day → clean negative → rlg stands.
- **Dominant risk (state honestly every time): CPD-transfer.** A window/latent win must survive PELT→event.
  Test event early. Also: bigger model + 12-subject train = overfit risk → hold-out / regularize / seed-check.
- **Hard limit:** enumerate the capacity/feature/architecture sub-space up front; don't drift into an
  unbounded search. If the genuinely-distinct architecture directions are tried and net-wash at the event
  headline, close Phase D and ship the rlg thesis.

### 5.4 Staged plan (mirror Phase-C-final's discipline)
- Stage 0: cheap prototype (1 seed, small/quick), window + early-event check on VAL, KILL fast. (Smoke-first,
  always: synthetic → 1-subject → full run; measure GPU ETA before committing an overnight run.)
- Stage 1: multi-seed {42,1,2,3}, EVENT gate at the 3.6 headline (≥2/3 subj, ≥3/4 seeds).
- Stage 2: one-shot TEST — ONLY on Stage-1 GO, ONLY after Boti signs off. `tier2_oneshot_compare`-style vs rlg.
- Stage 3: close either way; write up (win or negative) into `docs/RESULTS_OF_RECORD_phaseD.md`.

---

## 6 · FILE / PATH LAYOUT (local + Kaggle) — verified through Phase C

### 6.1 LOCAL (Windows, `F:/Study/Thesis/Code`, Git Bash + Cursor, CPU)
Repo: github.com/Nhanvas/Thesis, branch `main`. **Backup tag: `phase-c-final`.**
```
data/processed/            (32.9 GB, gitignored but present — the CPU source for everything)
   {subj}_{interictal,ictal}.npy            raw windows [N,18,1024], z-scored per subject
   {subj}_{split}_adjs_topk20.npy           R1 symmetric adjacency (wPLI+AEC, top-k20)  [split ∈ interictal,ictal]
   {subj}_{split}_features.npy              node features [N,18,5] band-powers
   {subj}_{split}_te_topk20.npy             R2 directed-TE top-k20 [N,18,18] (built in Phase C)
   gamma_aec_{subj}_{inter,ictal}.npy       gamma-AEC branch scores
data/models_retrain/
   gae_joint_seed{42,1,2,3}.pt              rlg GAE checkpoints (zip-dir format; Windows re-zip needs `touch`
                                            to fix pre-1980 timestamps before torch.load)
   gae_multirel_seed42.pt                   C4-full checkpoint (Phase C; state_dict, ~8.7k params)
results/phaseB/tier2/ens_val_tf/rlg/        rlg VAL ensemble arrays: ens_seed{S}_{subj}_{inter,ictal}.npy
results/phaseB/tier2/ens_test_tf/           rlg TEST ens (+components) — DO NOT TOUCH (one-shot)
results/phaseC/                             all Phase-C outputs (c4full/, artifact_probe/, artifact_gate/)
docs/RESULTS_OF_RECORD_phaseB.md            SINGLE SOURCE OF TRUTH for all locked numbers
docs/PHASE_C_FINAL_HANDOFF.md               Phase-C-final handoff (C4-full)
docs/PHASE_D_HANDOFF.md                     THIS FILE
```
CHB-MIT seizure-annotation summaries (for SzCORE ground truth), needed by score_ens/szcore_eval:
`--summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"`.

### 6.2 KAGGLE (notebooks, GPU; accounts `nhn2mm`, `norncreades`, +2)
Datasets mount under `/kaggle/input/datasets/<user>/<slug>/` (nested — auto-discover with rglob):
```
nhn2mm/chbmit-topk20        {subj}_{split}_adjs_topk20.npy   (R1 adjacency)
nhn2mm/chbmit-processed     {subj}_{split}_{adjs,features}.npy  (features + dense adjs; NO raw windows!)
nhn2mm/gamma-aec-scores     gamma_aec_{subj}_{inter,ictal}.npy
nhn2mm/chbmit-te-topk20     {subj}_{split}_te_topk20.npy   (R2 — created in Phase C; ~350 MB)
nhn2mm/chb10-te-topk20-smoke  (chb10 TE smoke subset)
nhn2mm/phase-c              Phase-C code (gae_joint_multirel.py, train_gae_multirel.py, encode_multirel_val.py,
                            build_te_branch.py, connectivity_probe.py, retrain_io.py, align_check*.py, ...)
norncreades/thesis-c-onset-code  rlg code (gae_joint.py, train_gae_joint.py, build_ens_tier2.py, ensemble_recipe.py, retrain_io.py)
norncreades/gae-s5          rlg + S2/S3 code + gae_joint_seed42 unpacked ckpt + lstm/gsl variants
```
**CRITICAL: raw windows `[N,18,1024]` are NOT on Kaggle** (too large; local-only). Anything that needs raw
(TE computation, artifact metrics, any new raw-derived feature) is built LOCALLY on CPU, then the small
derived arrays are uploaded as a Kaggle dataset for GPU training. Kaggle GPU is for training only.

### 6.3 Kaggle workflow rules (learned the hard way)
- Notebooks need **full cell code, top to bottom** (not snippets) — Save Version reruns from scratch, so a
  mid-run error loses the whole run. **Fail-fast pre-flight in Cell 1/2** (assert paths, GPU, code-freshness).
- Auto-discover paths with `rglob`, never hardcode the nested mount path.
- Re-upload the code dataset whenever a module changes; a pre-flight assert (e.g.
  `hasattr(M,'build_batch_fast')`) catches a stale upload before burning GPU time.
- Measure real GPU ms/window on a short run (exclude epoch-0 warmup) BEFORE committing a full training run.

---

## 7 · PHASE-C FILES CREATED (manifest — all committed under `phase-c-final`)
All smoke-tested; all TEST-guarded; all in parallel paths (rlg untouched).
```
src/dataprep/build_te_adj.py         R2 directed-TE top-k20 precompute (reuses validated te_matrix; resumable)
src/phaseC/gae_joint_multirel.py     C4-full model (non-shared R-GCN encoder, bilinear R2 decoder, fast batch path)
src/phaseC/train_gae_multirel.py     C4-full training (R2-collapse monitor + mid-train kill; fast path)
src/phaseC/encode_multirel_val.py    Stage-0 VAL window check + GO/KILL verdict + collapse-ablation + fidelity
src/phaseC/stage0_lg_variant.py      C4-full 2-branch (latent+gamma) variant test
src/phaseC/rlg_lg_diagnostic.py      rlg latent+gamma matched-ablation (window) diagnostic
src/phaseC/artifact_fp_diagnostic.py FP-are-artifacts pre-condition test (grad_max etc.)
src/phaseC/artifact_gate.py          label-free artifact gate (per-window + isolation) → gated ens
src/phaseC/compare_gate.py           VAL Pareto A/B from two score_ens CSVs
```
Evidence JSONs under `results/phaseC/{c4full,artifact_probe,artifact_gate}/…`, C4-full train log under
`results/phaseC/c4full/train_logs/train_multirel_seed42.csv`. See `PHASE_C_CLOSEOUT_provenance.md` for the
exact commit manifest + the RESULTS_OF_RECORD §9 text.
**Reusable for Phase D:** `retrain_io.py` (robust_z, window_auroc), `latent_anomaly.latent_pool`, the
score_ens → g2_val_gate/compare_gate VAL-gate pattern, the smoke-first + GPU-ETA-measure discipline, and the
fast block-diagonal batch construction pattern (if a bigger GNN needs speed).

---

## 8 · WHAT THE PHASE-D CHAT DOES FIRST
1. Read THIS file in full, then `docs/RESULTS_OF_RECORD_phaseB.md` §1–§9 and `docs/S2_S3_negatives.md`
   (so the S2 capacity/collapse precedent is fresh before proposing a bigger encoder).
2. Confirm the Stage-0 direction with Boti (capacity-first recommended; §5.2). Ground any architecture choice
   in literature (searched, recent) and in the S2 overfit precedent.
3. Build in a PARALLEL namespace: `src/phaseD/`, `data/models_phaseD/`, `results/phaseD/`,
   `docs/RESULTS_OF_RECORD_phaseD.md`. **rlg / Phase-C paths are read-only.** Every new script carries a
   TEST guard. Smoke-first (synthetic → 1-subject → full); measure GPU ETA before the overnight run.
4. Pre-register Stage-0 (H + falsification + kill) and the multi-seed EVENT gate BEFORE running.
5. Keep TEST untouched until a Stage-2 one-shot that Boti signs off.
6. If Phase D nets out negative or time runs short: `git checkout phase-c-final` — the rlg thesis is intact.
