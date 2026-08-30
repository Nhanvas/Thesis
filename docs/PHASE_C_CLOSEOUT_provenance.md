# PHASE C — CLOSEOUT PROVENANCE (paste each block into the named file)
Written 2026-08 after the Phase-C optimization round closed. Optimization is CLOSED
with converging evidence across decision / representation / ensemble / signal layers.
**rlg remains system-of-record. TEST untouched. No numbers below change the locked TEST results.**

Four things to apply:
  (1) `docs/RESULTS_OF_RECORD_phaseB.md` — replace the §8 tail line, then append §9.
  (2) Project custom instructions — replace the CURRENT STATUS Phase-C block.
  (3) Report Future-Work note (keep for the write-up / defense Q&A).
  (4) Commit manifest — force-add the artifacts below.

================================================================================
(1a) RESULTS_OF_RECORD_phaseB.md — REPLACE the current §8 closing paragraph
     ("**Phase C-final (in progress, staged-gated, ~1 week):** ...rlg remains
      system-of-record until a one-shot TEST replaces it.")
     WITH this line:
================================================================================

**Phase C-final (RESOLVED — negative, see §9).** C4-full (multi-relational GAE) was
built, trained, and VAL-gated; it did not beat rlg. Phase-C optimization is closed.

================================================================================
(1b) RESULTS_OF_RECORD_phaseB.md — APPEND as a new section §9
================================================================================

## 9 · Phase-C optimization — CLOSED (added 2026-08)

Phase C is closed. Seven independent levers across the decision, representation, ensemble,
and signal-quality layers were evaluated (pre-registered, VAL-gated); **none Pareto-improved
rlg at the event headline (F1 0.361 @ 3.6 FP/day). rlg is the ceiling and stays
system-of-record.** This is a convergent, evidence-based negative — not an untested closure.

### 9.1 C4-full — multi-relational GAE (representation layer)
Joint R-GCN-style autoencoder fusing symmetric R1 (wPLI+AEC top-k20) + directed R2 (TE
top-k20), NON-SHARED per-relation encoder weights, per-relation decoders (R1 inner-product,
R2 asymmetric bilinear), node features identical to rlg. Trained seed42, PREREG_01 recipe,
270,187 interictal windows. **No collapse** (gate_R2 = ‖grad R2‖/‖grad R1‖ held 1.01–1.03 all
200 epochs — R2 fully used, cf. the S2 residual-gate→0 failure it was designed to detect;
converged r2_recon 0.069→0.051). VAL window-macro AUROC (seed42):

| front-end | window macro AUROC | vs rlg-full 0.928 |
|---|---|---|
| rlg-full (recon+latent+gamma) — incumbent | **0.928** | — |
| C4-full 3-branch (recon-mr+latent-mr+gamma) | 0.909 | −0.019 (recon-mr anti-discriminative, 0.439 < 0.5, drags ensemble) |
| C4-full 2-branch (latent-mr+gamma, drop anti-disc. recon) | 0.926 | −0.002 = **tie within seed-SD (0.002)** |
| rlg-lg diagnostic (rlg latent+gamma, NO TE) | **0.9386** | matched-ablation control |

**Verdict: NO-GO (pre-registered).** The 2-branch tie (0.926 vs 0.928) is within the measured
window seed-SD → multi-seed cannot rescue a noise-floor tie. Diagnostic: rlg-lg (0.9386) >
C4-full-lg (0.926) → **plain latent+gamma without TE already beats the directed variant at
2-branch** → adding the directed relation is net-negative overall despite a real per-subject win.

**Mechanism finding (report-worthy positive):** directed connectivity genuinely rescues the
symmetric-inverted subject at the representation level — chb22 latent-mr 0.736→0.873 (+0.137),
**ablation-confirmed** (zeroing R2 messages: ΔR2(chb22) = +0.126). But it is per-subject and
net-washes: ΔR2(chb11) = −0.049 (TE hurts the symmetric-good subject), and the joint 2-relation
encoder loses chb10 latent (0.816→0.757, shared-capacity cost, not caused by R2: ΔR2(chb10) =
+0.040). This is the same directed-connectivity trade-off C0/C4-lite showed at the decision
layer, now confirmed at the **representation** layer — the strongest evidence in the thesis that
TE is complementary-but-insufficient.

*Self-correction (integrity note):* the Stage-0 input-fidelity band [0.78, 0.88] for chb22 zTE
was mis-specified too tightly; measured 0.888 (0.83 ± 0.058), which REPRODUCES C0's direction
more strongly, not a failure. Recorded so the 4a flag is not misread as an R2-input bug.

### 9.2 Ensemble reweight / drop-recon (ensemble layer) — DEAD ON RECORD, not re-run
The window-macro observation (rlg-lg 0.9386 > rlg-full 0.928) suggested dropping recon. But
this was **already measured at the event tier and rejected**: §5 — "lg (latent+gamma, drop
recon) underperforms rlg at §0 cells (0.579 balanced) → recon retained" (VAL grids in `lg/`,
TEST grids in `lg_test/`). And PREREG_03 already found the weight surface flat (24 triples within
0.005 of argmax; equal weights adopted as anti-overfit). Window≠event again: drop-recon helps
window-macro, hurts the event headline. **Not re-run — the record already answers it.**

### 9.3 Artifact / signal-quality gate (signal layer)
Pre-condition diagnostic (label-free): rlg's FP-prone interictal windows ARE artifact-associated
(best-AUROC 0.78–0.80 across all 3 VAL subjects; null ~0.51; `grad_max` = max first-difference
dominant → sudden jumps/pops that the ±5-SD amplitude preproc rejection lets through). A
per-window grad_max score-suppression gate flagged 85% of ictal windows (seizures share high
gradient) → unusable. A duration/isolation gate (suppress only isolated ≤2-window spikes, spare
sustained seizures) reduced ictal-flag to 3.5% macro and produced a VAL Pareto win — but **only at
5 FP/day, driven entirely by one subject (chb11), with the headline 3.6 FP/day unchanged**. A
1-subject/1-budget effect at n=3 is a noise signature (cf. slope-gate); **rejected** without
seed-check (per the hard-limit rule: a win must be at the 3.6 headline, ≥2/3 subjects, ≥3/4 seeds).
Signal-quality FP-reduction is thus addressed (partly already in preprocessing) and does not lift
the headline.

### 9.4 Unifying conclusion
rlg is the performance ceiling for this dataset/split. Every lever — directed connectivity
(C4-lite decision, C4-full representation), temporal smoothing (C1), plateau/slope gating,
ensemble reweighting (measured), and artifact gating — net-washes at the event headline. The
mechanism is understood: (a) window/representation gains die at the CPD-transfer (PELT keys on
sustained level shifts, not rank separation); (b) per-subject rescue levers net-wash (each hard
subject fails on a different mechanism); (c) the representation-limited ceiling subjects
(chb06/chb14, oracle F1 ≤ 0.09) sit in the locked TEST set and cannot be addressed without
label leakage. The negative is convergent across four layers and pre-registered throughout.

================================================================================
(2) PROJECT CUSTOM INSTRUCTIONS — REPLACE the CURRENT STATUS Phase-C block with:
================================================================================

> - **Phase C (optimization) — CLOSED with converging evidence.** rlg remains the optimized
>   pipeline of record (event F1 0.361 @ 3.6 FP/day, TEST, one-shot; window macro AUROC 0.805;
>   GAE seed-stable 0.929 ± 0.002). Seven pre-registered, VAL-gated levers across decision /
>   representation / ensemble / signal layers **none Pareto-improved rlg at the event headline**:
>   C4-lite (TE branch), C1 (smoothing), slope-gate (seed42-only), C4-full (multi-relational GAE —
>   3-branch 0.909 & 2-branch 0.926 both < rlg 0.928; directed latent rescues chb22 +0.137
>   ablation-confirmed but net-washes), ensemble drop-recon (dead on record: §5 lg 0.579 event +
>   PREREG_03 flat weight surface), artifact gate (1-subject/5-FP local win, headline unchanged).
>   **rlg is the ceiling; directed/reweight/artifact levers net-wash at the event headline;
>   ceiling subjects chb06/chb14 sit in TEST.** Source: `docs/RESULTS_OF_RECORD_phaseB.md` §9.
>   Next phase = report / attribution / web demo / defense. Do NOT re-propose any rejected lever.

================================================================================
(3) REPORT — Future Work paragraph (multi-band AEC: the one lever NOT tried, so the
    answer is ready for defense Q&A)
================================================================================

**Multi-band amplitude-envelope coupling (not evaluated — Future Work).** The only optimization
lever left untried is extending the gamma-AEC branch to a multi-band AEC representation (theta /
alpha / beta / gamma). It was deprioritized rather than tested, on measured priors from this
project's own data: (i) as an added ensemble branch, PREREG_03 showed the ensemble weight surface
is flat and a weak/anti-correlated branch drags the equal-weight ensemble (recon-mr did exactly
this in C4-full); (ii) as a representation change, C4-full established that enriching the graph
representation net-washes at the event headline. Its expected value is therefore low, but it is a
clean, label-free candidate for future work if a richer connectivity view is pursued — ideally
validated on an external dataset (e.g. TUH) rather than the locked CHB-MIT split.

================================================================================
(4) COMMIT MANIFEST — force-add (evidence for the closeout)
================================================================================

# code (src/phaseC/, src/dataprep/) — all smoke-tested, TEST-guarded, rlg untouched
  src/dataprep/build_te_adj.py
  src/phaseC/gae_joint_multirel.py
  src/phaseC/train_gae_multirel.py
  src/phaseC/encode_multirel_val.py
  src/phaseC/stage0_lg_variant.py
  src/phaseC/rlg_lg_diagnostic.py
  src/phaseC/artifact_fp_diagnostic.py
  src/phaseC/artifact_gate.py
  src/phaseC/compare_gate.py
# checkpoints / logs (force-add; gitignored dirs)
  data/models_retrain/gae_multirel_seed42.pt
  results/phaseC/c4full/train_logs/train_multirel_seed42.csv
# verdict / evidence JSONs
  results/phaseC/c4full/stage0_verdict_seed42.json
  results/phaseC/c4full/stage0_lg_variant_seed42.json
  results/phaseC/c4full/rlg_lg_diagnostic_seed42.json
  results/phaseC/artifact_probe/artifact_fp_diagnostic_seed42.json
  results/phaseC/artifact_gate/ens_val_gated_iso2/artifact_gate_report.json
# docs
  docs/RESULTS_OF_RECORD_phaseB.md   (§8 tail replaced, §9 appended)

  git commit -m "Phase C CLOSED: C4-full negative + mechanism finding; artifact-gate negative; \
reweight dead-on-record. rlg stands, TEST untouched. Optimization exhausted with evidence (7 levers)."

# Optional cleanup: move the failed per-window gated ens (results/phaseC/artifact_gate/ens_val_gated/)
# to results/history_superseded/ (archive-don't-delete); keep the iso2 dir + reports as evidence.
