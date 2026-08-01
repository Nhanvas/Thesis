# PLAN & STATUS — Thesis CPD/GAE Seizure Detection
**Living document: where we are, what is done, what is next, and why. Read this first in any new chat. Update it as work progresses.**

---

## CURRENT STATUS: Phase A + A.5 + B CLOSED. Mentor-feedback round (#16–#18) + weight change (#19–#20) + weight-consistency pass (#21–#22) CLOSED. All technical + governance loose ends resolved; every weight-dependent number now on the Decision #19 weight. **Decision #23/#24 (CUSUM FP filter) TESTED and REJECTED — pipeline unchanged. Repo reorganized (flat `src/`) + pushed + self-reproduces bit-exact. ACTIVE phase = REPORT WRITING (Methods first, unblocked); the Phase-C demo is built in parallel, kept minimal, and treated as source material. WRITING TAKES PRIORITY when bandwidth is tight (IELTS 9 Oct). See `PROJECT_HANDOFF.md`.**
Algorithm locked in `cpd_pipeline_v14.py`; all numbers locked in `RESULTS_OF_RECORD.md` (authoritative — if this file ever disagrees with it on a number, RESULTS_OF_RECORD wins). No new science is planned before the Oct-1 technical lock — only consolidation, the literature table (Week 10), and the thesis chapters. See `PHASE_B_AUDIT_handoff.md` for the full Phase-B audit.

**2026-07 addendum — mentor-feedback round (Decisions #16–#18):** supervisor reviewed the Phase A/B evaluation report and raised 4 questions (groundtruth/SzCORE-rule symmetry, why precision/FP-day still look low, mag%/pen selection rigor, FP/day clinical meaningfulness). All 4 investigated and resolved/answered with code-level verification — see `RESULTS_OF_RECORD.md` §10–12. **This is refinement within already-locked Phase A scope — same algorithm, same hyperparameters that were always open for tuning (mag%, pen) — not new science.** See the clarified rule under KEY LEARNINGS on what counts as "reopening a lock" vs. "finishing an already-open search."

**2026-07/08 addendum — ensemble-weight change + seeding-bug postmortem (Decisions #19–#20):** a reviewer-style question about whether the pre-Phase-A ensemble weight was optimal led to (a) **Decision #19** — the ensemble weight was changed from (0.35, 0.30, 0.35) to **(0.40, 0.35, 0.25)** after a 4-layer evidentiary chain, and (b) the discovery of a **seeding bug** in the original mag%×pen grid sweep (`mag_pen_grid_sweep.py`) that had inflated the old absolute numbers. Fixing the bug (`mag_pen_grid_sweep_v2.py`, cross-validated against `rebuild_ensemble_new_weight.py`) and re-deriving the high-sensitivity point on the corrected grid gave **Decision #20** — new high-sens point `mag50/pen0.5`. **This superseded Decision #16.** Full derivation + bug postmortem: `RESULTS_OF_RECORD.md` §13. Since the weight was a lock predating Phase A, this was the first such lock reopened in the project, with explicit sign-off obtained first (3-tier rule below).

**2026-08 addendum — weight-consistency pass (Decisions #21–#22):** Decision #19 changed the weight but only the EVENT tier (§1) had been re-derived. A rigor check found other reported numbers are also weight-dependent (functions of the ensemble score) but were still on the old-weight cache. **Decision #21** introduced a single-source ensemble recipe (`ensemble_recipe.py`: `ENS_WEIGHTS` + `build_ensemble`) as the ONE place the weight/ensembling live — imported by evaluation, analysis, and the Phase C export; the old-weight ens cache was quarantined. **Decision #22** re-verified every remaining weight-dependent number under the Decision #19 weight: §2 window AUROC 0.796→0.791 (component AUROCs reproduce `auroc_verification.csv` exactly — sanity check passed); §8 event ablation re-run (`full`=0.750 = MATCH §1, drift caveat removed, deltas now monotonic); §9 gap reconstructed (36.5%→73.2%, pooled 75.0%); §7 attribution confirmed weight-invariant; §4 chb06 balanced corrected 2/10→3/10. **No headline conclusion changed.** Full detail: `RESULTS_OF_RECORD.md` §14. **All weight-dependent numbers now consistently reflect the Decision #19 system — the weight-consistency loop is closed.**

---

## PHASE A — Evaluation rigor + CPD optimization  ✅ DONE
Goal: turn a working CPD pipeline into publication-grade, SzCORE-compliant, statistically-validated results.

| Week | Task | Status |
|---|---|---|
| 1 | Seed robustness of bootstrap padding | ✅ ±2–3% DR; made PELT penalty seed-independent |
| 2 | SzCORE-exact event scoring (`timescoring`) | ✅ adopted; fixed a bad CP→interval bridge (segment-mean gate) |
| 3 | Over-segmentation diagnosis + fix | ✅ found buffer-drop eval bug (chb16=0), added SzCORE don't-care + magnitude filter |
| 4 | Extra FP interventions | ⏭️ SKIPPED by decision — magnitude filter met the goal; residuals → future work |
| 5 | Operating-point selection + statistical validation + single-source consolidation | ✅ Pareto sweep; 2 operating points; built `cpd_pipeline_v14.py`; event-tier CIs |

## PHASE A.5 — Detector soundness gate  ✅ DONE
Decision gate before Phase B: is the detector good enough or should it be rebuilt/swapped? **Confirmed sound, no rebuild.** Window AUROC 0.80 > Yildiz unsupervised 0.68; event 0.75/0.83 ≈ supervised SzCORE Transformer 0.765; "low" F1/precision is by-design under the triage framing. Topology upgrade tested and rejected (see Decision #10).

## PHASE B — Depth + contribution  ✅ DONE
| Week | Task | Status |
|---|---|---|
| 6 | Window-sensitivity per-subject + window↔event gap | ✅ §9 — 37.6%→74.8%, 3 mechanisms, subset 86.4% |
| 7 | Event-tier leave-one-signal-out ablation | ✅ §8 — all views contribute; GAE load-bearing at event tier |
| 8 | Spatial attribution (which channels) | ✅ §7 — per-node GAE recon error primary; eigencentrality convergent |
| 9 | chb06 topology (as open problem) | ✅ §6 — rejected, label-free tradeoff |
| 10 | Latency + literature table + Yildiz→0.68 | ⏭️ deferred to writing sprint |
| 11 | Consolidation + cross-check | ✅ RESULTS_OF_RECORD consolidated; results/ tree via consolidate_outputs.py (2nd pass still pending — see REMAINING #2) |

> **Note on §8 event-tier ablation:** computed under the OLD ensemble weight (0.35/0.30/0.35). The ablation DELTAS (drop-recon/temporal/gamma, standalone-view ranks) are robust conclusions and do not change with the weight. Only re-verify the absolute component-`full` baseline against the new weight IF §8's absolute numbers are cited in the thesis body — flagged, not yet actioned (see OPEN ITEMS).
> **Note on §7 attribution:** per-node GAE reconstruction-error attribution is derived from the GAE recon score alone, independent of the ensemble mixing weights → weight-invariant, no re-run needed. (Verify this assumption once before final lock if any doubt.)

## MENTOR-FEEDBACK ROUND (2026-07) — post-lock refinement  ✅ DONE (analysis); ⏭️ write-up pending
| Task | Status |
|---|---|
| SzCORE merge/split rule symmetry audit (ref vs hyp) | ✅ verified in `timescoring` source + empirically (0/75 pairs <90s) — no fix needed (#18) |
| Base-rate explanation for low precision/FP-day | ✅ quantified (§12.2) — not an evaluation bug |
| Full mag%×pen Pareto grid (was: 2 isolated mag spot-checks) | ✅ done, but the FIRST grid (`mag_pen_grid_sweep.py`) had a seeding bug → **superseded by the corrected grid, Decision #20** |
| Duration-stratified sensitivity + ACNS 10s threshold | ✅ `duration_stratified_sensitivity.py` — chb06 duration-confound caught (Decision #17); **RE-VERIFIED on the current mag50/pen0.5 point (§11 v3)** |
| FP/day clinical-meaningfulness literature framing | ✅ researched (§12.4) — review-burden reframe + ICU/wearable benchmarks; ⏭️ NOT yet drafted as thesis prose |
| Window-level precision improvement options | ✅ lever (b) — ensemble-weight re-tune — **DONE = Decision #19**; levers (a) descriptive percentiles and (c) upstream retrain remain out of scope / not started (§12.5) |
| Incorporate §10/§11 findings into thesis Results/Discussion prose | ⏭️ deferred — not yet at write-up stage |

## WEIGHT-CHANGE ROUND (2026-07/08) — Decisions #19–#20  ✅ DONE (analysis + governance); ⏭️ prose pending
| Task | Status |
|---|---|
| Ensemble-weight optimality re-check (local + wide weight grid) | ✅ `weight_sensitivity_sweep.py` — locked weight ranked 17/37 then 29/127; cand_1=(0.40,0.35,0.25) sits in a `w_temp`-heavy plateau |
| 8-seed paired robustness of the candidate weight | ✅ `weight_seed_robustness_check.py` — 7/8 wins, sign-test p=0.035 |
| Cross-operating-point + per-subject check | ✅ `weight_candidate_crosscheck.py` — balanced 7/8 (p=0.035), high-sens 8/8 (p=0.004); chb06 improves MOST, no label-free tradeoff |
| **Decision #19 — adopt weight (0.40, 0.35, 0.25)** | ✅ ADOPTED with explicit sign-off (first predates-Phase-A lock reopened) |
| Seeding-bug discovery in `mag_pen_grid_sweep.py` | ✅ found (old-weight numbers didn't reproduce), root-caused (no reseed between per-mag `evaluate_subject()` calls), confirmed by forward/reverse-order experiment |
| Bug fix + cross-validation | ✅ `mag_pen_grid_sweep_v2.py` (reseed before every call); agrees exactly with independently-written `rebuild_ensemble_new_weight.py` on old-weight at mag60/pen1.0 (0.7105) and mag50/pen1.0 (0.7500) |
| **Decision #20 — high-sens point re-derived on corrected grid** | ✅ ADOPTED — `mag50/pen0.5` (0.829/71.25), 2×SD noise-floor selection criterion; mag60/pen0.3 identical |
| Official CI numbers for both points (`stat_validation.py`) | ✅ `locked_phaseA_event_results.csv` regenerated — §1 table now CI-bearing |
| §11 duration re-verify on mag50/pen0.5 | ✅ v3 (§11) — fidelity-checked, chb06 confound persists but attenuated |

## WEIGHT-CONSISTENCY PASS (2026-08) — Decisions #21–#22  ✅ DONE
| Task | Status |
|---|---|
| Single-source ensemble recipe (`ensemble_recipe.py`: `ENS_WEIGHTS`+`build_ensemble`) | ✅ #21 — the ONE place the weight/ensembling live; Phase C imports it |
| Quarantine old-weight ens cache → `results/history_superseded/oldweight_ens_scores/` | ✅ #21 — nothing reads a stale cache by accident |
| §2 window tier re-verify (`window_tier_newweight.py`) | ✅ #22 — macro AUROC 0.796→0.791; component AUROCs reproduce `auroc_verification.csv` exactly (sanity PASS) |
| §8.2 event ablation re-run under new weight | ✅ #22 — `full`=0.750 = MATCH §1 (drift caveat gone); deltas monotonic recon>temporal>gamma; temporal removal → chb06 0/10 |
| §9 window↔event gap reconstruction | ✅ #22 — 36.5%→73.2% (pooled 75.0%); chb16 gap now negative |
| §7 attribution weight-invariance | ✅ #22 — confirmed by argument (per-node recon = GAE decomposition, independent of mix); no re-run |
| §4 chb06 balanced correction 2/10→3/10 | ✅ #22 — stale old-weight value; canonical CSV + §8 + §11 agree on 3/10 |
| `consolidate_outputs.py` 2nd pass (phaseA_appendix + history_superseded) | ✅ 0 MISSING / 0 MISPLACED; repro package consistent with #19/#20 |

---

## DECISIONS LOG (with rationale)
1. **SzCORE = evaluation backbone.** CHB-MIT bipolar montage is SzCORE-exempt/compliant. Drop specificity/accuracy (TN-based). FP/day primary.
2. **Seed-independent PELT penalty** (s² from interictal only) — deterministic.
3. **Magnitude filter** (prune CPs below interictal-percentile magnitude) — label-free precision fix.
4. **Buffer "don't-care"** (eval-only, label-aware) — fixed the offset-CP loss that zeroed chb16.
5. **Change-point→event mapping** (not segment-mean gating).
6. **`cpd_pipeline_v14.py` = single source of truth** for detection; eval + demo share it.
7. **Operating points:** balanced (mag60/pen1.0) + high-sensitivity (originally mag70/pen0.3 → mag50/pen1.0 → **now mag50/pen0.5**, see #16→#20).
8. **Skip Week-4 interventions** (diminishing returns).
9. **Yildiz baseline correction:** CHB-MIT scalp AUROC = 0.68 (not 0.76).
10. **Topology extension REJECTED** (A.5). spectral_radius lifts chb06 2→4/10 but costs the other 7 exactly 2 (pooled 57=57) — net-zero, underpowered. The "label-free tradeoff": boosting the inverted subject taxes the rest. Standalone AUROC ≠ integration value.
11. **Phase-B attribution C1–C2 (eigencentrality) validated** — consistency 7/8, seizure-specific 5/8, convergent ~0.45, lateralization 4/8. (Superseded as PRIMARY by #13.)
12. **Faithfulness C3 (eigencentrality) weak** — 3/8 occlusion-significant; connectivity change spatially distributed; eigencentrality is holistic → weak occlusion.
13. **Per-node GAE recon error adopted as PRIMARY attribution** (original-plan Priority-1). Faithful 5/8 (vs 3/8), specific 6/8, consistent 6/8; convergent with eigencentrality ≈0.35; model-based, ties to GAE. Signal distributed → interpretability, not SOZ. chb06 structure-consistent (eigcent) but recon-diffuse (method-dependent).
14. **Event-tier ablation done.** All 3 views contribute (recon/temporal −0.079, gamma −0.053 pooled). Standalone≠marginal reconfirmed at event tier. Temporal weakest alone (0.316) but complementary (chb06/chb14). GAE load-bearing (−6 TP, chb13/14/15). Harness fidelity confirmed (locked 0.750/38.0 under OLD weight); component `full` drifts to 0.711 (GPU non-repro), deltas valid.
15. **Window↔event gap explained.** 37.6%→74.8%. Any-overlap scaling with seizure length + threshold-window degeneracy (chb17). Structural-failure chb06/chb16 separated → subset 86.4% (headline 74.8%).
16. **[2026-07] ~~High-sensitivity operating point re-selected from a full mag%×pen Pareto grid~~ — SUPERSEDED by #19/#20.** The grid that produced this (`mag_pen_grid_sweep.py`) was later found to have a seeding bug (§13.2); its absolute numbers (mag50/pen1.0 = 0.816/47.97) do not survive the corrected grid. The *intent* (pick a defensible high-sens point from a systematic grid) carries forward into #20; the *number* is retired. Kept in the log only for audit trail.
17. **[2026-07] Duration-stratified sensitivity reveals a chb06 confound, not a duration effect.** Pooled 10–20s bucket is the sensitivity floor at both operating points; the deficit is disproportionately chb06 (inverted-connectivity outlier), not an intrinsic duration effect. Excluding chb06, sensitivity increases monotonically with duration. Report raw-annotation duration (9/76 <10s) vs window-quantized (3/76 <10s) both. RE-VERIFIED on the #20 point (§11 v3): at high-sens, chb16 (not chb06) drives most of the bucket's improvement (2/7→6/7). Do NOT write "10–20s seizures are harder" from the pooled number alone.
18. **[2026-07] SzCORE merge/split rule symmetry confirmed correct as-is; no evaluation-protocol fix needed.** `_mergeNeighbouringEvents`/`_splitLongEvents` apply to both `ref` and `hyp` (only tolerance extension is ref-only, by design). 0/75 annotated-seizure pairs across the 8 test subjects are <90s apart → rule never triggers here regardless. Persistently low precision/FP-day is a base-rate effect (§12.2), not a scoring bug.
19. **[2026-07/08] Ensemble weight changed** from (0.35, 0.30, 0.35) to **(0.40, 0.35, 0.25)**. Evidence: local + wide weight grid (locked weight ranked 17/37 → 29/127; candidate in a `w_temp`-heavy plateau), 8-seed paired sign-test (7/8, p=0.035), cross-operating-point + per-subject check (balanced p=0.035, high-sens p=0.004; chb06 improves most; no label-free tradeoff). All CPU-only on cached components, no retraining. **First predates-Phase-A lock reopened — explicit sign-off obtained first** (3-tier rule). New weight genuinely lifts balanced 0.7105→0.750 (the old weight's *true* balanced, post-bug-fix). Full derivation: `RESULTS_OF_RECORD.md` §13.1.
20. **[2026-07/08] High-sensitivity operating point re-derived** to **mag50/pen0.5** (0.829/71.25) after a seeding bug was found in the original grid (`mag_pen_grid_sweep.py` did not reseed `np.random` between per-mag `evaluate_subject()` calls → results drifted with loop position). Corrected grid (`mag_pen_grid_sweep_v2.py`), cross-validated against `rebuild_ensemble_new_weight.py`. Selection criterion: among Pareto-optimal points whose sensitivity gain over balanced clears 2×SD (≈0.06, from 8-seed noise), pick the lowest FP/day. mag60/pen0.3 is identical (same per-subject TP). Bug scope precisely bounded: NOT affecting Decision #19 or Phase B; affecting only the absolute Decision #16 numbers + the prior §11 version. Full postmortem: `RESULTS_OF_RECORD.md` §13.2–13.4.
21. **[2026-08] Single-source ensemble recipe + old-cache quarantine.** `ensemble_recipe.py` holds the ONE definition of the weight (`ENS_WEIGHTS = (0.40, 0.35, 0.25)`) and the ensembling (`build_ensemble` = weighted sum of per-view component z-scores; no post-hoc renorm, CPD is scale-adaptive). Evaluation, analysis, and the **Phase C export** all import from here — the weight is never re-defined inline and NO persistent ensemble cache is created (always build fresh from components). The old-weight GPU ens cache (`results/cpd/scores/*_ens_*.npy`) was quarantined to `results/history_superseded/oldweight_ens_scores/`. This is the guardrail against the stale-cache failure mode behind §13. New scripts: `ensemble_recipe.py`, `window_tier_newweight.py`. Full detail: `RESULTS_OF_RECORD.md` §14.
22. **[2026-08] Every remaining weight-dependent number re-verified under the Decision #19 weight.** §2 window AUROC 0.796→0.791 (component AUROCs reproduce `auroc_verification.csv` exactly — sanity PASS); §8.2 event ablation re-run (`full`=0.750 = MATCH §1, drift caveat removed, deltas monotonic recon −0.145 > temporal −0.132 > gamma −0.105, temporal removal → chb06 0/10); §9 gap reconstructed (36.5%→73.2%, pooled 75.0%, chb16 gap now negative); §7 attribution confirmed weight-invariant (no re-run); §4 chb06 balanced corrected 2/10→3/10 (stale old-weight value). No headline conclusion changed. `RESULTS_OF_RECORD.md` §14.
23. **[renumbered] Phase C (web demo) — ACTIVE, targeted for completion by Oct 1** (per mentor: build it so it can be written into the report; not an optional bonus). Gate A passed (science solid). Build: static frontend + offline JSON from `cpd_pipeline_v14.detect_events`, sourcing the ensemble via `ensemble_recipe.build_ensemble` (Decision #21) — build-from-components, never a cache — post-hoc, test-subjects only, CPU, 3 layers. Do NOT add a second dataset for localization (breaks methodological cleanliness; attribution IS the detector's internal signal). *(Note: this decision carried #19 then #21 in earlier versions; renumbered to #23 to keep decision numbering consistent with `RESULTS_OF_RECORD.md`'s #19/#20 (weight/operating-point) and #21/#22 (recipe/re-verify).)*
24. **[2026-08] CUSUM persistence FP-reduction post-filter (the Decision #23 experiment) — TESTED and REJECTED.** Baseline reproduced (57/461/0.750/39.67). Continuous P-sweep locates a discrete cliff at P=34: 0 seizures lost / 9.3% FP-day cut just below it, 3 lost / 21.3% cut at it; no P clears the pre-registered ≥20%-FP/day-at-≤2-loss bar. Duration diagnostic + chb06/chb16 being the first casualties confirm an intrinsic fixed-60s-window CUSUM limitation, not a calibration gap. NOT adopted; pipeline unchanged; duration-adaptive window = future work, out of thesis scope. See `RESULTS_OF_RECORD.md` §15.

## KEY LEARNINGS
- **Evaluation bugs masquerade as model failures.** Two sensitivity collapses (84%→38%, chb16→0) were eval-layer design errors, not model bugs. Verify each stage first.
- **Scoring rules change the story.** Old onset-match "FCP/h" ≠ SzCORE FP/day.
- **Separate algorithm (label-free) from evaluation (label-aware).**
- **Standalone rank ≠ integration/marginal value.** First seen in the topology tradeoff (A.5), reconfirmed at the event-tier ablation: gamma is the best window-ranker but the smallest event-tier contributor; temporal is the worst standalone but a top complementary contributor.
- **GPU is not bit-reproducible.** Re-exported components do not reconstruct the locked ensemble (closure ≈2). Use one self-consistent set per analysis; verify any harness reproduces the locked balanced point first; seed np.random(0) before build_timeline_masked.
- **Attribution on scalp EEG is distributed.** Two independent attributions (recon, eigencentrality) both show only modest mass concentration → claim highlighting/interpretability, never SOZ, on CHB-MIT.
- **[2026-07] Three tiers of "reopening a lock" — don't conflate them.** (i) Hyperparameters explicitly left open for Phase A tuning (mag%, pen_mult) — deepening the search here is finishing already-open work, not new science; adopt validated improvements immediately. (ii) Decisions that predate Phase A / were locked before the current phase (e.g. ensemble weights 0.35/0.30/0.35) — reopening these needs explicit user sign-off first, even though it's still CPU-only (this is exactly what Decision #19 did). (iii) New architecture/features/training/data — genuinely new science, needs GPU/Kaggle, out of scope until told otherwise.
- **[2026-07] PELT's `.fit()` is ~free; `.predict(pen=beta)` is the real cost and must be called once per `pen_mult`.** A first version of the mag×pen grid script looped full `detect_changepoints()` once per (mag, pen) combo — 48×/subject instead of 6×/subject, since `min_mag_pct` only affects a cheap post-hoc filter. Caused a 4+ hour runtime before being caught (~8× speedup, bit-identical output). Identify which parameters affect the expensive step vs. which are cheap post-filters.
- **[2026-07/08] A shared RNG that isn't reseeded per-call makes loop results order-dependent — a silent correctness bug.** `evaluate_subject()` draws from `np.random` for bootstrap buffer padding and relies on the caller to seed. The original `mag_pen_grid_sweep.py` seeded once per subject, not once per (subject, mag_pct) call, so each mag_pct's result depended on how many others ran before it — confirmed by a forward-vs-reverse-order experiment giving different numbers. This inflated the old absolute figures (balanced *looked* 0.750 but was truly 0.7105). **Lesson: any harness that reuses a caller-seeded RNG inside a loop must reseed immediately before every single call; cross-validate the fix with a second, independently-written script.**
- **[2026-07] Window-boundary quantization (4s windows) can inflate a short real seizure's reported duration by several seconds.** Raw-annotation-second duration and what-the-detector-actually-sees duration disagree near threshold boundaries (e.g., ACNS 10s cutoff) — report both.
- **[2026-07] Always check subject-level confounds before attributing a pooled effect to the variable of interest.** The apparent "10–20s seizures are hardest" pattern was a chb06 (already-known outlier) effect, caught only by breaking the pooled bucket down per-subject.

- **[2026-08] Falsification WITH a mechanism beats a bare null.** The FP filter's failure was traced to short seizures (chb06/chb16 first to die), showing a fixed-window CUSUM structurally dilutes brief ictal elevation — a specific, defensible reason rather than "it didn't work." Reported as a finding plus a concrete future-work direction (duration-adaptive window), which strengthens the thesis rather than hiding a negative.
## OPEN ITEMS / KNOWN LIMITATIONS
- Upstream GAE/LSTM/gamma not audited (cached scores taken as given).
- **Upstream component flags — status (answers a common cross-session question):**
  - (a) `src/gae/model.py` A-only vs the joint model — **RESOLVED.** `data/models/best_model_joint_lambda01.pt` verified JOINT (contains `x_decoder`) by checkpoint forensics; the A-only harness + its 10 checkpoints are archived under `archive/scaffolding/`. See `PROVENANCE_MAP.md` §4b.
  - (b) LSTM warm-up fill-values (first ~15 ictal windows; chb16 ~57%, chb06 ~33% contamination) and (c) chb17 518-window constant-fill block — **NOT separately re-audited; accepted under the "upstream taken as given" scope.** The locked results reproduce bit-exact regardless, so these are non-blocking; they are candidates to DISCLOSE in the thesis Limitations, not open experiments.
  - (d) Decision #19 weight robustness is **modest** (+3 TP vs a ~7 TP seed-variance swing). The weight choice is defensible but its margin is thin — disclose honestly rather than overclaim.
- **chb06 (inverted connectivity) ≈ 2/10 balanced, 5/10 high-sens — genuine detection limitation; but structure-consistent under eigencentrality attribution (method-dependent). Frame as the thesis's most instructive subject, not merely a failure.** Also drives the apparent (spurious) 10–20s duration-bucket dip — see #17.
- FP/day now **39.77 balanced / 71.25 high-sens** at the reported points (updated by #19/#20; was 38–49). Fine for post-hoc triage, NOT real-time alarm; state whenever FP/day is discussed. Review-burden reframe + ICU/wearable literature benchmarks researched (§12.4) but not yet written into thesis prose. *(Note: the high-sens FP/day rose substantially with #20 — 71.25 vs the old 48.6 — because the new point is genuinely more permissive; be honest about this tradeoff in Limitations.)*
- Attribution is spatially distributed (5/8 faithful) — an interpretability layer, not focal localization.
- Literature comparison table + latency quantification NOT done (Week 10; deferred to writing). DOI confirmation still pending for 4 supplementary rows (SeizureTransformer, BISeizuRe, e-Glass, Zero-FA ensemble). Note: the Transformer sens 0.765/FP-day 40.6 is a TUH result, NOT CHB-MIT — must not be cited as a CHB-MIT baseline.
- Web demo NOT built (optional; will wrap `cpd_pipeline_v14.detect_events`).
- **[write-up stage — deferred by decision, keep in view:]**
  1. Results/Discussion prose for the new weight + operating point (§10/§13) and the duration-bucket/chb06-confound finding (§11).
  2. Week-10 latency quantification (`mean_lat_s`, already in the event CSVs) + honest annotation-lag caveat.
  3. DOI confirmation for the 4 literature-table supplementary rows.
  4. FP/day → review-burden reframe (§12.4) into Discussion/Limitations prose.
- **[resolved since last update — no longer open]:**
  - ~~Re-run `duration_stratified_sensitivity.py` on the new high-sens point~~ → DONE (§11 v3, mag50/pen0.5).
  - ~~Recompute §10 CIs through `stat_validation.py`~~ → DONE (`locked_phaseA_event_results.csv` regenerated, §1 CI-bearing).
  - ~~Decide whether to open lever (b) ensemble-weight re-tune~~ → DONE = Decision #19 (opened with sign-off, adopted).
  - ~~2nd pass of `consolidate_outputs.py` (phaseA_appendix category)~~ → DONE (Decision #22 round; 0 MISSING / 0 MISPLACED; also added `history_superseded`).
  - ~~Verify §8 event-ablation baseline + §7 attribution under the new weight~~ → DONE (Decision #22): §8 re-run (`full`=0.750 MATCH); §7 confirmed weight-invariant.
  - ~~Re-verify §2 window tier + §9 gap under the new weight~~ → DONE (Decision #22): §2 AUROC 0.796→0.791, §9 reconstructed.
- **[still open — write-up only, deferred to sprint]:** the 4 write-up items above; optional mentor-facing briefing memo summarizing how each of the 4 mentor questions + the weight change + the weight-consistency pass were resolved.

---

## REMAINING BEFORE OCT-15 SUBMISSION (Phase C demo → then report; all detection science + governance closed)

**UPDATE [2026-08]:** #23/#24 (FP-reduction filter) CLOSED — REJECTED; the single reopened lock is now shut and NO detection-science experiments remain. Repo reorganized (flat `src/` + `src/dataprep` + `src/fp_reduction_prior` + `archive/*`), committed + pushed to github.com/Nhanvas/Thesis, and self-reproduces the two locked operating points bit-exact from committed components (`src/thesis_repro_lock.py`). `edf_index.py` verified 89/89. Rubric gap #4 (Decision-Matrix impact 4C) closed via DM6 (`Proposed_solution_updated_v5.md`). Active phase = report writing + Phase-C demo build over locked results.

> **PRECEDENCE NOTE [2026-08]:** any older "Phase C is the priority until Oct 1, then write" language further down (REMAINING / PHASE C sections) is SUPERSEDED. The current decision is **writing first (Methods), demo in parallel and minimal.** The demo references `docs/PHASE_C_PLAN_v2.md` (not the older `PHASE_C_PLAN.md`), with a CONTINUOUS confidence schema and the feedback panel cut to future work.

1. `RESULTS_OF_RECORD.md` — DONE (sections 1–14; #19–#22 incorporated; every weight-dependent number on the Decision #19 weight).
2. `consolidate_outputs.py` 2nd pass — DONE (phaseA_appendix + history_superseded; 0 MISSING / 0 MISPLACED).
3. **Technical/governance state fully consistent** — weight-consistency loop closed (#21–#22); Phase C has a clean single-source contract (`ensemble_recipe.build_ensemble`); stale ens cache quarantined. **No further detection science or re-verification needed.**
4. **NOW → Oct 1: build the Phase C web demo** (active priority). Start from the data contract + JSON schema in `PHASE_C_PLAN.md` before any frontend code. Decide up front: which operating point(s) the demo shows; that it runs label-free (`detect_events`, no `inter_mask`) so on-screen counts are qualitative and may not exactly equal the masked §1 event counts (a designed property, document it); attribution heatmap sources per-node recon error (data exists, §7 weight-invariant).
5. **Oct 1 → Oct 15: write the report** — demo is source material. 5 key findings ready: complementary multi-view (GAE load-bearing both tiers; −11 TP at event tier); structural FP ceiling of unsupervised; topology label-free tradeoff (A.5); attribution consistent+specific but distributed; chb06 detection-limited/structure-consistent. Fold in the mentor-feedback round (§10/§13), the weight-consistency pass (§14), duration/chb06 confound (§11), protocol audit (§12). Plus: latency quantification (mean_lat_s in event CSVs), literature table + 4 DOI confirmations, Yildiz→0.68, FP/day→review-burden reframe (§12.4).
5. Optional Phase C demo (only with bandwidth) — see below.

## PHASE C — Translation & web demo (ACTIVE — priority until Oct 1)
The active work item now (Gate A passed). Static frontend + offline JSON export produced by `cpd_pipeline_v14.detect_events`; post-hoc, test-subjects only, CPU; 3 layers (timeline of suspicion / per-channel attribution heatmap / clinical context). NOT real-time. Design-thinking spec + data contract before any code. See `PHASE_C_PLAN.md`. **Prerequisite — satisfied:** the ensemble source is settled (Decision #21) — the export imports `ensemble_recipe.build_ensemble` and builds from components under the current weight (0.40, 0.35, 0.25); it must NEVER read the quarantined old-weight ens cache. Any locked number the demo surfaces must be the current #19/#20/§2 figures. Scaffolding as built: `edf_index.py` (time map, reuses the locked summary parser). The demo feeds directly into the report (Oct 1–15).

---
*Update this file at the end of each working session: tick completed items, append decisions, and revise the "next" list.*
*Note: the project's custom-instructions FILE USAGE MAP (maintained separately in Claude Project settings, not a file in this repo) still lists the OLD weight (0.35/0.30/0.35) and OLD operating points — it should be updated to reflect Decisions #19/#20, and to list `mag_pen_grid_sweep_v2.py`, `rebuild_ensemble_new_weight.py`, `weight_*_sweep/check.py`, `duration_stratified_sensitivity.py` and their output CSVs as AUTHORITATIVE. Claude cannot edit that document directly.*
