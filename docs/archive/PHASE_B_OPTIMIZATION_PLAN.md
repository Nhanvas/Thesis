# PHASE B — OPTIMIZATION PLAN (Unsupervised Seizure Detection, GAE + CPD)

**Status:** DRAFT FOR EXECUTION · **Owner:** Nguyen Quoc Trung Nhan (BEBEIU22184) · **Supervisor (cô):** Assoc. Prof. Hà Thị Thanh Hương
**Purpose of this file:** Single self-contained handoff to bootstrap the next chat and drive the Phase-B optimization. It consolidates every problem, decision, research finding, plan, goal, and condition established in the planning session.
**Authority:** This plan SUPPLEMENTS, and does NOT override, `docs/RESULTS_OF_RECORD.md` §0 (the locked baseline-of-record). Where this plan and §0 disagree on a *baseline* number, §0 wins. This plan defines the *forward* work.

---

## 0. HOW TO USE THIS FILE (for the next chat)
**Scope boundary:** THIS plan is the *input* produced in the planning chat. **Execution begins in the NEXT chat.** The first execution action (Step 0) is: **Boti sends `results/retrain_v3p1/val/final_eval_seed42.csv`** → then write PREREG_05 + the T1 derivation script → run T1. Nothing is executed in the planning chat.

**Primary success criterion:** PERFORMANCE. The committee and cô weight it heavily (paper-comparison + future publication). The mandate (§4) is to push event- and window-level performance as high as legitimately possible — reconsidering the whole pipeline — while every gain stays VALID (VAL-derived, test-clean). Rigor is the vehicle for defensible performance, not a brake.

1. Read §1 (context) → §2 (baseline of record) → §3 (diagnosis) → §4 (goals/mandate) → §5 (plan) in order. Do NOT re-derive locked baselines.
2. Before running ANY experiment, check the input/compute status in §10 (T1 is already unblocked, CPU-only).
3. Every experiment is pre-registered with a falsification criterion (§5). Report negative results as falsified predictions — do not reframe them.
4. All derivation happens on VAL / non-test subjects. The 8 test subjects are touched **once**, as-is. This discipline is the entire reason the pre-rebuild headline was retired; it is non-negotiable (§8).

---

## 1. IMMUTABLE CONTEXT
- **Thesis:** *Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection.* BME, International University VNU-HCM (ABET).
- **Dataset:** CHB-MIT scalp EEG, 18-ch bipolar, 256 Hz. **Test = 8 subjects** (chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18), **76 seizures**, **278.2 interictal hours**. Split permanent (seed 42).
- **VAL = chb10, chb11, chb22** — CONFIRMED from `retrain_io.py` (`VAL_SUBJS`, the single source). TRAIN = the other 12 subjects.
- **Framing (locked):** POST-HOC EEG review triage, NOT real-time alarm.
- **Method (locked pipeline):** per-window functional-connectivity graphs (wPLI + AEC, top-k 20% edges) → Joint GAE (GCN encoder, reconstruction error) + predictive LSTM (temporal prediction error) + gamma-band AEC → per-branch robust-z → **equal-weight (1/3 each) ensemble** → PELT change-point detection → label-free per-subject FP-budget operating point → SzCORE event scoring (`timescoring`). Unsupervised, patient-independent.
- **Model checkpoints:** `gae_joint_seed42.pt`, `lstm_temporal_seed{42,1,2,3,4}.pt` (canonical = seed 42).
- **Timeline:** IELTS **Oct 9**; thesis submit **Oct 15**; defense **Nov 2–3**.

---

## 2. BASELINE OF RECORD (the floor — cite from RESULTS_OF_RECORD §0)
| Tier | Metric | Value |
|---|---|---|
| Window | macro AUROC | **0.775** |
| Window | 5-seed VAL AUROC | 0.648 ± 0.011 (Gate PASS) |
| Event · balanced (mag70/pen0.5) | Sensitivity | **0.632** [0.519, 0.731] |
| Event · balanced | FP/day | **38.6**; TP/FN/FP = 48/28/447; precision 0.097 |
| Event · high-sensitivity (mag55/pen0.3) | Sensitivity | **0.776** [0.671, 0.855] |
| Event · high-sensitivity | FP/day | **72.7**; TP/FN/FP = 59/17/843; precision 0.065 |

**Locked design choices (do not re-litigate):** equal weights (flat non-test surface); canonical seed 42 (deep 5-seed mean DROPPED — dilutes anomaly peaks at event level); label-free per-subject FP-budget operating point.

**Per-subject reality (source of the whole problem):**
| Subject | Window AUROC | Event sens (bal) | Event prec (bal) | FP (bal) |
|---|---|---|---|---|
| chb03 | 0.954 | 1.00 | 0.117 | 53 |
| **chb06** | **0.437 (BELOW CHANCE)** | 0.10 | 0.014 | 71 |
| chb13 | 0.805 | 0.833 | 0.192 | 42 |
| **chb14** | **0.626 (weak)** | 0.25 | 0.021 | 94 |
| chb15 | 0.826 | 0.90 | 0.225 | 62 |
| chb16 | 0.871 | 0.30 | 0.097 | 28 |
| chb17 | 0.747 | 0.667 | 0.065 | 29 |
| chb18 | 0.938 | 0.833 | 0.069 | 68 |

---

## 3. DIAGNOSIS — WHY THE REPORTED NUMBERS LOOK LOW (three separable causes)

### 3.1 Cause A — Operating-point placement (fixable for FREE)
The reported precision (~10%) is measured at **38.6 FP/day**. SOTA event-level papers report precision at **1.3–14 FP/day**. We have been reporting the wrong point on our own curve. Re-pooling the existing mag×pen grid (seed 42, 8 test subjects) gives the full Pareto frontier:

| Operating point | Sens | Prec | F1 | FP/day | TP/FP |
|---|---|---|---|---|---|
| high-sens (reported) mag55/pen0.3 | 0.776 | 0.065 | 0.121 | 72.7 | 59/843 |
| balanced (reported) mag70/pen0.5 | 0.632 | 0.097 | 0.168 | 48/447 |
| mag65/pen5 | 0.461 | 0.243 | 0.318 | 9.4 | 35/109 |
| **F1-optimal mag80/pen5** | **0.395** | **0.316** | **0.351** | **5.6** | **30/65** |
| high-precision mag80/pen10 | 0.276 | 0.362 | 0.313 | 3.2 | 21/37 |

The F1-optimal region is a **broad, stable ridge** (pen=5 across mag 65→80 all give F1 0.31–0.35), not a lucky cell → a VAL-derived operating point will land in it and transfer. **NOTE:** the mag80/pen5 selection above was made by inspecting test (diagnosis only). The reportable operating point MUST be derived on VAL and applied to test once (see T1).

### 3.2 Cause B — Two subjects with broken representation (needs model work)
Per-subject at the F1-optimal point (mag80/pen5): chb06, chb14, chb16, chb17 all collapse to **0 TP**. But they fail for **different reasons**:
- **chb06** (window AUROC 0.437, below chance) + **chb14** (0.626, weak): **representation is broken** (suspected noisy/"inverted" functional connectivity). → Phase 2 (graph-structure learning) target.
- **chb16** (window AUROC 0.871, strong) + **chb17** (0.747, decent): **representation is fine**; the event-conversion (PELT → event) loses the signal at tight thresholds. → Phase 1 (decision-layer) target — cheap, no retraining.

Concentration: chb06 + chb14 = **37% of all FP (165/447) but only 6% of TP (3/48)** at the balanced point.

### 3.3 Cause C — Comparison-protocol mismatch (fixable by an honest table)
CHB-MIT papers reporting 90–99% precision/F1 are almost universally **segment/window-level, and/or patient-specific, and/or supervised, and/or leakage-prone** (random-split reuses same-subject segments). SzCORE — the field's standardized event-level benchmark — explicitly rejects accuracy/specificity as clinically meaningless for rare events. Our comparable metric is window AUROC 0.775 (which beats the unsupervised baseline Yildiz ~0.68) and event-level F1 at matched FP/day.

**Realistic patient-independent event-level SOTA (the correct ceiling):** SzCORE 2025 challenge top event F1 = **0.43** (sens 0.37 / prec 0.45); the 28-algorithm EPFL benchmark top F1 = **0.32** (sens 0.37 / prec 0.29), on a held-out 65-subject / 4,360-hour EMU set — all **supervised**. Our F1-optimal point (F1 0.351, prec 0.316 @ 5.6 FP/day) is already **inside that band, unsupervised** — on a different dataset (CHB-MIT), so it is a reference band, not a head-to-head. A like-for-like CHB-MIT event-level table is still required.

---

## 4. GOALS (quantified, honest)

**PERFORMANCE MANDATE (first-class success criterion — repeatedly emphasised by Boti).** The committee AND the supervisor (cô) weight *performance* heavily: it is the basis for comparison against other papers and for a possible future paper submission. Therefore the objective of Phase B is to **actively maximise event-level performance (primary: sensitivity, FP/day, F1) and window-level performance (AUROC/AUPRC) through scientifically valid means** — aiming to reach and, where possible, exceed the patient-independent unsupervised SOTA band — NOT merely to reach a defensible floor. "Think out of the box, like a top-lab researcher": reconsider the whole pipeline (features, preprocessing, graph construction, encoder, objective), not only the locked components. The performance push and scientific honesty are NOT in tension: we push as hard as possible, and the ONLY things off-limits are *invalid* means (test-set tuning, leakage, tricks). Every gain must come from a method that is correct (§8).

**Staged targets (an ambitious path, not a ceiling):**
1. **Immediate (Phase 0, free):** move the *reported* headline from event F1 0.168 to **~0.32–0.35** (precision ~0.30) by reporting a VAL-derived F1-oriented operating point + the full Pareto curve. Enter the SzCORE SOTA band without touching the unsupervised claim.
2. **Cheap (Phase 1):** meaningfully cut FP/day at fixed sensitivity (artifact gating) and recover chb16/chb17 events (decision-layer) → push F1 further.
3. **Model (Phase 2):** fix chb06/chb14 representation → window macro AUROC **> 0.80**, event F1 toward **0.40+**, still unsupervised & patient-independent.
4. **Framing:** deliver a defensible like-for-like comparison so the committee compares event-level unsupervised patient-independent to the same, not to segment-level supervised numbers.

**Honesty condition (how the mandate and rigor coexist):** we exhaust the *valid* method space first — think broadly, revisit every pipeline stage, try each promising lever — and only accept a plateau after genuinely trying. A plateau reached that way is reported honestly (a systematic, pre-registered falsification with mechanisms + a corrected comparison is itself a defensible contribution; cf. ICML 2024 "Quo Vadis, Unsupervised TSAD": bigger models do not reliably beat simple baselines). What we never do is manufacture a number by invalid means (test-set tuning, leakage, tricks). Maximise hard; stay honest about how the maximum was reached.

---

## 5. THE PLAN — three phases, diagnose-before-intervene, each gated

### PHASE 0 — Diagnose + bank the free wins (this week; CPU-only; no test-tuning)
**T1 · VAL-derived operating point (biggest, cheapest lever).**
- Run the mag×pen grid on VAL. Pre-register the selection rule BEFORE looking at test: (a) F1-optimal on VAL, and (b) a fixed-budget point at ~5 FP/day (to report in SzCORE convention). Apply the chosen (mag,pen) to test **once**.
- Deliverable: full test Pareto curve + the two new operating points, added alongside (not replacing) the §0 points.
- **Falsification:** success = reported test event F1 ≥ **0.30** (from 0.168) with no test-tuning. If the VAL-derived point lands far off the ridge on test, report as-is and investigate transfer.

**T2 · Like-for-like comparison table.** Classify every baseline the committee cites by (segment vs event) × (patient-specific vs independent) × (supervised vs unsupervised) × (curated vs full-continuous). Deliverable for the supervisor conversation.

**T3 · Oracle-ceiling per subject (VAL + test-diagnostic).** For each subject, best achievable event-F1 under an oracle threshold. Separates representation-limited (low oracle) from decision-limited (high oracle). **Expected:** chb16/chb17 high oracle (→ Phase 1); chb06/chb14 low oracle (→ Phase 2). Confirms the §3.2 split before any GPU is spent.

**T4 · chb06 sign-flip / rolling-z probe (free).** Test whether chb06's below-chance AUROC recovers under score sign-inversion or local (rolling) normalization.
- **Falsification:** success = chb06 window AUROC > 0.5 (ideally > 0.6). If yes → a normalization/polarity bug, cheap fix. If no → genuinely representation-limited → Phase 2 graph-structure-learning target (do not write off to Future Work without this test).

### PHASE 1 — Cheap fixes (next; little/no GPU; VAL-derived)
**P1.1 · Inference-time artifact / signal-quality gate** before PELT (amplitude, line-length, cross-channel similarity thresholds, or a small artifact classifier).
- **Falsification:** success = ≥ **50%** FP/day reduction at equal sensitivity on VAL. Literature precedent up to 96% FP/h reduction (Ingolfsson et al., Sci. Rep. 2024, 22.9→1.0 FP/h). If FP/day does not drop meaningfully at fixed sensitivity, revert.

**P1.2 · Event-conversion recovery for chb16/chb17** (per-subject PELT/persistence calibration; representation already good).
- **Falsification:** success = chb16 & chb17 event sensitivity > 0 at the F1-optimal operating point (currently 0).

**P1.3 · chb14 standalone-branch diagnostic.** Measure each branch's standalone AUROC on chb14 to localize the weakness (GAE vs LSTM vs gamma-AEC) before Phase 2. Diagnostic only; routes chb14 into the Phase 2 representation track.

### PHASE 2 — Representation / architecture upgrade (weeks; GPU; GATED by Phase 0/1 probes)
Enter ONLY for the subjects/axes that Phase 0/1 proved are representation-limited (expected: chb06, chb14). Each track is a VAL-only probe with a stated criterion; only winners graduate to a full build + one-shot test. Priority order is set by the literature ROI assessment (§6).

**P2.1 · Learned sparse graph structure (highest priority).** Replace fixed top-k with a lightweight differentiable adjacency (Information-Bottleneck / self-expressive, à la IRENE; or Gumbel-softmax GTS-style), trained by the existing reconstruction loss (no labels).
- **Falsification:** success = chb06 window AUROC > 0.5 (chance), ideally > 0.7; VAL macro AUROC > 0.80. If chb06 still < 0.5, suspect montage/polarity/reference artifact rather than graph structure → pivot to preprocessing.

**P2.2 · Masked-graph / contrastive SSL objective** as a fourth ensemble branch (IRENE-style masked graph autoencoder, or EEG-CGS-style contrastive; both label-free).
- **Falsification:** success = event F1 improvement ≥ **0.03** on VAL held-out.

**P2.3 · Multi-band connectivity + richer node features** (δ/θ/α/β/γ graphs; band-power, Hjorth, spectral-entropy nodes; L1 feature selection).
- **Falsification:** success = improvement on chb14 without increasing per-subject variance. Drop if variance rises.

**P2.4 · Foundation-model transfer (exploratory, lowest priority).** Frozen LaBraM/CBraMod as a feature extractor feeding the anomaly scorer — only after resolving the 18-ch-bipolar → foundation-model montage mismatch.
- **Falsification:** must beat the P2.1+P2.2 pipeline on event F1; abandon if it merely matches at higher cost. High domain-shift risk; out-of-domain foundation-model AUROC drops toward ~0.79.

---

## 6. RESEARCH EVIDENCE (condensed from the Phase-B literature review; directions, not locked benchmarks)
| Upgrade axis | Key evidence | Expected benefit | Cost | Data need | Overfit risk |
|---|---|---|---|---|---|
| **Learned sparse graph** (P2.1) | IRENE (IB + graph MAE) AUROC 0.908/0.916 vs GraphS4mer 0.882/0.885 on TUSZ; edge density 0.16 vs 0.72; EvoBrain dynamic graphs 0.94 CHB-MIT | **High** (targets chb06 directly) | Moderate | Low–moderate (unsupervised) | Moderate (sparsity prior mitigates) |
| **Inference artifact gate** (P1.1) | Ingolfsson 2024: 22.9→1.0 FP/h (96% cut) | **High** (FP problem) | Low | Very low | Very low |
| **Masked/contrastive SSL** (P2.2) | Tang 2022 (0.875 AUROC TUSZ, next-window); EEG2Rep (KDD'24, masked); EEG-CGS (AAAI'23, no seizure labels) | Moderate–high | Moderate | Low | Low |
| **Multi-band features** (P2.3) | Band-resolved FC + Hjorth/entropy standard; DynSeizureGAT multi-band | Moderate | Low–moderate | Low | Moderate (12 subjects) |
| **Foundation model** (P2.4) | CBraMod 0.889 / LaBraM 0.868 CHB-MIT segment (barely > EEGNet 0.805); out-of-domain ≈ 0.79 | Low–moderate, uncertain | High | High | High (domain shift) |

**Evaluation-norm evidence:** SzCORE (Epilepsia) + EPFL 28-algorithm benchmark confirm event-level, patient-independent, full-continuous scoring is correct and that segment/patient-specific numbers are inflated. The "overlooked perspectives on CHB-MIT" critique confirms random-split leakage. Our protocol is already the rigorous one.

**Caveats:** IRENE is a very recent (2026) preprint with minor internal inconsistencies — treat as strong evidence of *direction*, not a locked target. All graph-SSL SOTA numbers are supervised/fine-tuned and mostly on TUSZ/SEEG, not CHB-MIT event-level; they indicate representation quality, not a promise of equal event-level gains in our unsupervised pipeline.

---

## 7. STRATEGIC DECISIONS
**Made (locked for Phase B):**
- **Performance is a first-class success criterion** (committee + cô weight it heavily; basis for cross-paper comparison and future publication). Maximise event-level (primary) and window-level performance through valid means; aim to reach/exceed the patient-independent unsupervised SOTA band (§4).
- Diagnose-before-intervene; each Phase 2 track gated by a VAL probe with a falsification criterion. (Gating serves *efficiency* — spend compute where it pays — not timidity; Phase 2 is pursued seriously as the main performance-push vehicle.)
- Bank the free/cheap wins (Phase 0/1) first; spend GPU only where diagnosis proves a representation bottleneck.
- §0 remains the floor-of-record; new operating points are added alongside, not silently swapped.

**Boti-approved (2026-08; defaults accepted — D1–D3 still to be RATIFIED by cô before Phase 2, since they touch the thesis claim):**
- **D1 · Fork 1 — Unsupervised purity → A (stay fully unsupervised).** The operating-point finding makes the SOTA band reachable without supervision. Nhánh B (VAL-supervised candidate-gate) only as optional upside if precision is still short after Phase 2.
- **D2 · Fork 2 — External unlabeled data → NOT opened yet.** SSL pretraining on external interictal (e.g., TUH) only if in-domain SSL (P2.2) underperforms; if opened it must be declared loudly (scope was CUT).
- **D3 · Fork 3 — Headline operating point → report the FULL Pareto curve, headline BOTH** the high-sensitivity point (triage use-case) and the F1-optimal point (SOTA comparison).
- **D4 · T1 operating-point selection rule → derive on VAL BOTH (i) F1-optimal and (ii) a fixed ~5 FP/day point; ADD them alongside §0, never replace §0.** §0 stays the floor-of-record. (Pure technical decision, Boti-locked.)

---

## 8. INTEGRITY GUARDRAILS (non-negotiable)
1. Derive operating points / weights / thresholds on VAL / non-test ONLY. Touch the 8 test subjects once, as-is. (Root cause of the retired pre-rebuild headline.)
2. Pre-register hypothesis + falsification criterion before each experiment. Report negatives as falsified predictions.
3. Diagnose before intervening; verify each stage — many "model failures" are evaluation bugs.
4. Authoritative scorer = `timescoring`; any harness must reproduce §0.
5. Single-source: ensemble weight only in `src/ensemble_recipe.py`; detection algorithm only in `src/cpd_pipeline_v14.py`.
6. Archive, don't delete → `results/history_superseded/<date>/` via `git mv`.
7. Attribution = interpretability (XAI), never seizure-onset-zone on CHB-MIT.
8. Use "demonstrates / suggests / is consistent with" precisely; report scope honestly.

---

## 9. TIMELINE & FALLBACK
- **Phase 0** (this week, free) → banks the SOTA-floor headline for submission.
- **Phase 1** (following, cheap) → FP reduction + chb16/17 recovery.
- **Phase 2** (weeks, GPU) → may or may not land before Oct 15.
- **Fallback rule:** if Phase 2 is not conclusive by ~mid-September, freeze Phase 0/1 results as the submission headline and present Phase 2 diagnostics as systematic, mechanism-backed future work. **The submission is never hostage to Phase 2.** Report Intro + Methods writing can proceed now (independent of these numbers).

---

## 10. INPUT / COMPUTE STATUS (resolution log)
1. **VAL subject IDs — RESOLVED.** chb10, chb11, chb22 (from `retrain_io.py`).
2. **VAL grid CSV — EXISTS: `results/retrain_v3p1/val/final_eval_seed42.csv`.** Therefore **T1 is CPU-only (scenario a): no Kaggle, no component rebuild needed.** Test grid = `results/retrain_v3p1/final_eval_seed42.csv` (already verified: 8 test subjects × 8 mag × 6 pen). Existing OP-derivation machinery: `fp_budget_operating_point.py` (`--stage val`/`--stage test`) + `retrain_io.select_operating_points_optionA`; T1 reuses it with an F1/low-FP objective instead of `target_fp≈40`.
   - *To finalize the T1 script first-try:* view `results/retrain_v3p1/val/final_eval_seed42.csv` (confirm it holds the full 3×8×6 grid with columns `subject,mag_pct,pen_mult,tp,fp,n_seizures,n_inter_h,sensitivity,precision,fp_per_day,window_auroc`).
3. **Compute — Phase 0/1 are fully local/CPU (no Kaggle dependency).** Phase 2 retraining will need Kaggle GPU (`nhn2mm`, `norncreades`); some ensemble-component score arrays from the rebuild may live on Kaggle rather than locally — to be located only when Phase 2 starts, NOT a blocker for Phase 0.
4. **Fork decisions — RESOLVED (Boti-approved defaults, see §7 D1–D4).** D1–D3 to be ratified by cô before Phase 2.

## 11. OPEN QUESTIONS FOR THE SUPERVISOR (cô)
- Approve Fork 1/2/3 decisions (§7).
- Approve the like-for-like comparison framing (§3.3 / T2) as the way to present results.
- Channel-attribution ground-truth blind labels (separate track, unaffected by detection rebuild) — still pending; MAP@K results remain PROVISIONAL until then.

## 12. FILE / ARTIFACT MAP
- **This file** = master plan for Phase B. Self-contained bootstrap for the next chat.
- Supplements `docs/RESULTS_OF_RECORD.md` §0 (floor) — does not override it.
- Full literature review = the "Phase-2 Pipeline Upgrades" report artifact (evidence source; key points embedded in §6 here).
- **At execution (next chat), spin out per-experiment pre-registrations** following existing convention: `PREREG_05` (operating point / T1), `PREREG_06` (artifact gate / P1.1), `PREREG_07` (learned graph / P2.1), etc.
- After any Phase-B result: update `RESULTS_OF_RECORD.md` §0 ONLY after VAL-gated derivation + a single one-shot test, with a provenance banner. Archive superseded artifacts, never delete.

---
*End of Phase B optimization plan. Status: VAL confirmed, D1–D4 locked (D1–D3 pending cô), VAL grid CSV located → T1 unblocked as a CPU-only task. Next action: verify the VAL grid CSV, write PREREG_05 + the T1 derivation script (derive F1-optimal & ~5 FP/day on VAL, apply to test once), then execute.*
