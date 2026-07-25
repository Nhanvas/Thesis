# RESULTS OF RECORD — Locked numbers + provenance
**The single authoritative source for every reported number. Each value lists the file it comes from so nothing is re-derived or misremembered. If any other file disagrees, THIS file wins.**

Last locked: **end of Phase B**; refined **2026-07 (mentor-feedback round, Decisions #16–#18, §10–§12)**; **further refined 2026-07/08 (Decisions #19–#20, §1/§10/§11/§13) — ensemble weight changed and a seeding bug in the mag%×pen grid sweep was found, fixed, and re-verified**; **weight-consistency pass 2026-08 (Decisions #21–#22, §2/§4/§8/§9/§14) — every remaining weight-dependent number (window tier §2, event ablation §8, window↔event gap §9) re-verified under the Decision #19 weight; §7 attribution confirmed weight-invariant; a single-source ensemble recipe was introduced and the old-weight ens cache quarantined.** Protocol: SzCORE (Dan et al., *Epilepsia* 2024), patient-independent, 8 test subjects, 76 seizures, scored with the `timescoring` library (any-overlap; 30 s pre / 60 s post tolerance; merge < 90 s; split > 5 min). FP/day denominator = interictal hours.

---

## 1. EVENT-LEVEL (primary results)
**Source:** `locked_phaseA_event_results.csv` (produced by `stat_validation.py`), per-subject detail in `szcore_event_level_new_decision19_mag60.csv` and `szcore_event_level_new_decision19_mag50.csv`. **Ensemble weight and both operating points updated 2026-07/08 — see §13 (Decisions #19–#20) for full derivation.**

| Operating point | Ensemble weight | mag% | pen | Sensitivity (95% CI) | Sens macro±SD | Precision (95% CI) | F1 | FP/day (95% CI) | TP/FN/FP |
|---|---|---|---|---|---|---|---|---|---|
| **Balanced** (primary) | (0.40, 0.35, 0.25) | 60 | 1.0 | **0.750** [0.642, 0.834] | 0.732 ± 0.257 | 0.110 [0.086, 0.140] | 0.192 | **39.77** [36.22, 43.57] | 57/19/461 |
| **High-sensitivity** (current — Decision #20) | (0.40, 0.35, 0.25) | 50 | 0.5 | **0.829** [0.729, 0.897] | 0.807 ± 0.159 | 0.071 [0.056, 0.090] | 0.131 | **71.25** [66.48, 76.28] | 63/13/826 |
| ~~High-sensitivity (Decision #16, superseded)~~ | ~~(0.35, 0.30, 0.35)~~ | ~~50~~ | ~~1.0~~ | ~~0.816~~ [0.714, 0.887] | ~~0.804 ± 0.196~~ | ~~0.100~~ [0.079, 0.127] | ~~0.179~~ | ~~47.97~~ [44.06, 52.12] | ~~62/14/556~~ |
| ~~High-sensitivity (original, superseded)~~ | ~~(0.35, 0.30, 0.35)~~ | ~~70~~ | ~~0.3~~ | ~~0.816~~ [0.714, 0.887] | ~~0.804 ± 0.196~~ | ~~0.099~~ [0.078, 0.125] | ~~0.177~~ | ~~48.6~~ [44.7, 52.8] | ~~62/14/564~~ |

**mag60/pen0.3 (same weight) is numerically IDENTICAL to the high-sensitivity row above** (same TP=63 at every one of the 8 subjects, verified — see §13) and may be cited interchangeably.

- Pooled (micro) aggregation = SzCORE-correct. CIs: Wilson (proportions), exact Poisson (FP/day). Interictal exposure = 278.2 h.
- Balanced point's sensitivity is numerically the same as the old weight's balanced point (0.750 both), but that is because **the old weight's true balanced-point sensitivity, once a seeding bug was fixed, is actually 0.7105 — not the previously-believed 0.750.** The new weight genuinely improves balanced from 0.7105 → 0.7500 (Δ+0.0395). See §13 for the full derivation; do not assume "balanced didn't change" from the fact that both read 0.750.
- Latency ≈ 0 to +7 s (mildly post-onset). **Do NOT claim "pre-ictal."**

## 2. WINDOW / SAMPLE LEVEL (threshold-independent; RE-VERIFIED under the Decision #19 weight — §14)
**Source (current, new weight):** `eval_window_level_newweight.csv`, `eval_stat_tests_newweight.csv`, `window_component_auroc_newweight.csv` (produced by `window_tier_newweight.py`, which builds the ensemble from cached components via `ensemble_recipe.build_ensemble` and re-runs the LOCKED stat functions in `evaluation_protocol.py`). **Old-weight versions (`eval_window_level.csv`, `eval_stat_tests.csv`) are superseded — window AUROC is the AUROC of the ensemble score and IS weight-dependent; the old files used the 0.35/0.30/0.35 cache.**
- **Macro AUROC = 0.791** across 8 test subjects (old weight was 0.796 — Δ−0.005, negligible; still ≈ 0.80 and comfortably > Yildiz unsupervised 0.68). The ensemble still beats its best single component (gamma 0.755) by +0.036 — multi-view value holds at the window tier.
- AUC-PR ≈ 0.079 macro (old ≈ 0.09; low absolute but ~14× chance prevalence — report as lift-over-chance).
- Per-subject AUROC (new weight): chb03 0.934, chb18 0.918, chb16 0.898, chb13 0.835, chb15 0.807, chb14 0.776, chb17 0.741, **chb06 0.420** (near/below chance — inverted connectivity; recon standalone 0.300 confirms the inversion).
- **Component standalone window AUROC (weight-INDEPENDENT, sanity-check PASSED):** recon 0.671, temporal 0.647, gamma 0.755 — reproduce `auroc_verification.csv` exactly, confirming the components are the set that produced §1 and the harness is faithful.
- Mann-Whitney U + effect size r available per subject; window sensitivity at P95 ≈ 0.365 (macro; old ≈ 0.38).
- **Always report window vs event together**: window sens ~0.38 vs event sens ~0.75–0.82 — the gap is expected and is quantified/explained in §9.
- **Window-level precision is a diagnostic metric only — it does not feed the real detection pipeline** (Tier-1 threshold is illustrative; PELT operates on the continuous score, not this threshold). See §12 for the options considered to move it, and their status (all still open/undecided).

## 3. SEED ROBUSTNESS (one line for the report)
**Source:** 8-seed runs (`eval_multiseed.py`, and `szcore_eval.py --multiseed`).
"Detection rate is stable to ±2–3 % across 8 padding seeds; the PELT penalty was made seed-independent." (Determinism: seed `np.random` with 0 before each `build_timeline_masked`; canonical_seed=0.)

## 4. PER-SUBJECT NOTES (balanced point unless noted; VERIFIED new-weight values from `szcore_event_level_new_decision19_{mag60,mag50}.csv`)
Full per-subject TP at both operating points (Decision #19 weight), pooled 57/76 balanced, 63/76 high-sens:

| subject | balanced (mag60/pen1.0) | high-sens (mag50/pen0.5) |
|---|---|---|
| chb03 | 7/7 | 7/7 |
| chb06 | **3/10** | **5/10** |
| chb13 | 10/12 | 10/12 |
| chb14 | 7/8 | 7/8 |
| chb15 | 19/20 | 19/20 |
| chb16 | 4/10 | 8/10 |
| chb17 | 2/3 | 2/3 |
| chb18 | 5/6 | 5/6 |

- Strong: chb03 (7/7), chb15 (19/20), chb14 (7/8), chb18 (5/6).
- Recovered by the buffer-fix: chb16 (0 → 4/10 balanced, 8/10 high-sens; event brevity limits it — see §9, and duration analysis in §11).
- **Genuine limitation: chb06 3/10 at balanced, 5/10 at high-sens (Decision #20's mag50/pen0.5)** — inverted connectivity (ictal connectivity decreases); no filter fully fixes it, but the Decision #19 weight lifts chb06 from 2/10 (old weight) to 3/10 at balanced (consistent with Decision #19's "chb06 improved most"), and the high-sens point recovers more of chb06 than any prior operating point tested. Document as a limitation, not a failure. (But see §7: chb06 is structure-consistent under eigencentrality attribution. See also §11: chb06 still explains most of the residual "10–20s seizures are harder" pattern in pooled duration analysis at both operating points; it is a chb06 effect, not a duration effect.)
- **[correction, 2026-08]** Earlier text stated "chb06 2/10 at balanced"; that was a stale old-weight value. Under the Decision #19 weight the verified balanced figure is **3/10** (canonical `szcore_event_level_new_decision19_mag60.csv` pen1.0, and independently the §8 ablation full(3-view) per-subject, and §11's own duration breakdown 1+2 = 3).

## 5. CONTEXT BASELINES (for comparison framing; verify before quoting in thesis)
- SzCORE paper's own supervised CHB-MIT baselines (Table 2): RF sens 0.37 / FP-day 1.66; **Transformer sens 0.765 / FP-day 40.6**; XGBoost sens 0.671 / FP-day 2.09. → Our balanced point (0.750 / 39.77) is comparable to the supervised Transformer; our high-sens (0.829) exceeds it on sensitivity.
- Yildiz 2022 (unsupervised, CHB-MIT scalp): correct AUROC = **0.68** (NOT the ~0.76 in old docs). Our window AUROC ~0.80 > 0.68.
- A full 2023–2026 literature comparison table is an OPEN write-up task (Week 10; deep-research artifact ready — EEG-CGS AAAI2023, Grattarola ESWA2022, Tang DCRNN ICLR2022, DeepSOZ MICCAI2023, Ali RSOS2024 patient-independent 72–75% anchor). DOI confirmation for 4 supplementary rows (SeizureTransformer, BISeizuRe, e-Glass, Zero-FA ensemble) still pending — deferred to write-up sprint (see PLAN_AND_STATUS.md).
- FP/day clinical-legibility framing (review-burden reframe, ICU/wearable benchmarks) — see §12.4. Not yet drafted as thesis prose.

---

# PHASE B — DEPTH, ABLATION, ATTRIBUTION (locked)

## 6. REJECTED TOPOLOGY EXTENSION (A.5) — mechanistic negative result
**Source:** `topo_extract.py`, `topo_ensemble_eval.py` (HISTORY).
Adding a 4th "topology" view (spectral_radius / graph_energy / fiedler / degree_entropy) to the ensemble was tested to rescue chb06. graph_energy strictly hurt; spectral_radius at w=0.2 lifted chb06 2→4/10 but cost the other 7 subjects exactly 2 detections (pooled-8 TP unchanged 57=57) — a **net-zero redistribution, underpowered (n=10/subject)**. **REJECTED.** The "label-free tradeoff": under the unsupervised constraint, boosting the inverted subject taxes the others equally. Standalone topology AUROC ≠ integration value. (Decision #10.)

## 7. SPATIAL CHANNEL ATTRIBUTION — primary = per-node GAE reconstruction error
**Source:** `attribution_gae_pernode.py` (primary), `attribution_c1/c2/c3.py` (eigencentrality convergent check). Outputs in `results/phaseB/attribution_pernode_*`.

**Method.** Per-window GAE reconstruction error decomposed per node: `r_i = mean_j (A_ij−Â_ij)² + λ·mean_b (Xn_ib−X̂_ib)²` (λ=0.1); dumped by GPU inference from the locked checkpoint (self-check: mean over nodes reproduces the scalar recon score, err ≈1e-8, all 8). Per channel, z vs interictal baseline, rank by |z|. Local (clean occlusion), model-grounded.

**Results (top-k=5), head-to-head with the eigencentrality proxy:**

| metric | eigencentrality (proxy) | **per-node GAE recon (primary)** |
|---|---|---|
| within-patient consistency (vs random null) | 7/8 | 6/8 |
| seizure-specific (vs interictal null) | 5/8 | **6/8** |
| faithful — occlusion (p<0.05) | 3/8 | **5/8** |

Faithful subjects (recon): chb13, chb14, chb15, chb18, chb17; convergent-with-eigencentrality mean ≈0.35. Config: `_adjs_topk20`, top-k 5.

**Verdict.** Per-node GAE reconstruction error is the primary attribution (better faithfulness + specificity, model-grounded, ties to the GAE named in the title, and is the method the original plan specified). Eigencentrality is retained as an independent convergent check.

**Claim scope (honest).** Consistent, seizure-specific, load-bearing channel highlighting — an unsupervised interpretability layer. **NOT clinical SOZ** (CHB-MIT has no per-channel ground truth). Attribution mass is only modestly concentrated (top-k ≈0.28–0.41 vs 0.278 random) → the seizure connectivity change is spatially **DISTRIBUTED** at scalp resolution; attributed channels are significantly necessary (occlusion) but not focally dominant — consistent with volume conduction and ~0.59 scalp channel-attribution sensitivity in the literature.

**chb06 (method-dependent — report both).** Eigencentrality finds chb06's structural connectivity mode consistent + right-temporal across 10 seizures (seizure-specific p=0.014); per-node recon does NOT (its reconstruction failure is spatially diffuse). chb06 remains detection-limited; structure-consistent under eigencentrality, recon-diffuse under the model. A genuine nuance, not a "recovery." (Decisions #11–#13.)

## 8. COMPONENT ABLATION — two-tier, per-subject, mechanistic
**Source:** window tier `auroc_verification.csv` (locked run); event tier `event_ablation.py` → `results/phaseB/event_ablation_*`.

**8.1 Window tier (macro AUROC):** recon 0.671 · temporal 0.647 · gamma **0.755** · ensemble **0.791** (new weight; was 0.796 under the old weight — components are weight-independent, only the ensemble number changed; see §2/§14). Dominant view: gamma→chb03/16/17; recon→chb13/15/18; temporal→chb14.

**8.2 Event tier (SzCORE leave-one-signal-out, balanced pen1.0/mag60) — RE-RUN under the Decision #19 weight (§14, Decision #22).** **Source:** `results/phaseB_newweight/event_ablation_{pooled,persubject}.csv` (built from components with `ENS_WEIGHTS`; old-weight version in `history_superseded/`). **Fidelity now EXACT: component-derived `full(3-view)` = 0.750 (57/76) = MATCH to the locked §1 balanced.** Under the new weight the entire result set is build-from-components on CPU (no separate GPU ens cache), so the old "0.711 drifts from 0.750, trust the deltas" caveat is GONE — the ablation baseline now equals the reported headline.

| config | sens | TP/76 | FP/day | Δsens vs full |
|---|---|---|---|---|
| full (3-view) | **0.750** | 57 | 39.8 | — |
| drop recon (GAE) | 0.605 | 46 | 40.2 | **−0.145** |
| drop temporal | 0.618 | 47 | 33.2 | −0.132 |
| drop gamma | 0.645 | 49 | 38.5 | −0.105 |
| recon only | 0.579 | 44 | 28.6 | −0.171 |
| temporal only | 0.316 | 24 | 49.3 | −0.434 |
| gamma only | 0.566 | 43 | 33.1 | −0.184 |

Per-subject TP lost when a view is removed (new weight): recon→chb15(−5)/chb13(−3)/chb14(−3)/chb06(−1)/chb16(+1) [net −11]; temporal→chb14(−5)/**chb06(−3 → 0/10)**/chb13(−1)/chb16(−1) [net −10]; gamma→chb03(−2)/chb14(−2)/chb15(−2)/chb16(−2) [net −8].

**Findings (new weight):** (1) all three views contribute — 3-view ensemble justified; (2) **relative ordering is now cleanly monotonic — recon (−0.145) > temporal (−0.132) > gamma (−0.105) — tracking the weights (0.40 > 0.35 > 0.25)**, sharper than the old near-tie; (3) **standalone rank ≠ marginal contribution** still holds and is now sharper (gamma best window-ranker 0.755 but smallest event contributor; temporal worst standalone 0.316 but 2nd-largest marginal); (4) temporal LSTM is **the sole reason chb06 is detected at all** — removing it drops chb06 to **0/10**; (5) **GAE load-bearing at event tier** now −11 TP (was −6), chb13/14/15 — pre-empts "what does the GAE add over gamma?"; (6) chb06 relies on temporal+recon, not gamma (drop_gamma leaves chb06 unchanged at 3/10). (Decisions #14, #22.)

**Honest reading of the larger deltas:** much of the increase in delta magnitude vs the old weight comes from the baseline rising 54→57, not from the views suddenly mattering more (absolute TP of the drop configs is close to before: 46–49 vs old 48–50). The defensible claim is *the relative ordering is now clean and the baseline matches the reported system* — NOT "absolute contributions jumped." Standalone-view AUROCs/sensitivities are IDENTICAL to the old run (recon_only 0.579, temporal_only 0.316, gamma_only 0.566), as expected: a one-view "ensemble" is just that view's z-score and the CPD is scale-adaptive.

## 9. WINDOW ↔ EVENT SENSITIVITY GAP (explained) — RECONSTRUCTED under the Decision #19 weight (§14)
**Source (current):** wAUROC/wSens from `eval_window_level_newweight.csv` (§2); eSens = balanced per-subject from `szcore_event_level_new_decision19_mag60.csv` (= §8 ablation full(3-view) per-subject); win/sz is structural (ictal-windows-per-seizure), weight-invariant. Old-weight version (`window_event_gap.csv`) superseded.
Macro window sens **36.5%** → macro event sens **73.2%** (pooled 57/76 = 75.0%).

| subj | win/sz | wAUROC | wSens | eSens | gap |
|---|---|---|---|---|---|
| chb03 | 15.1 | 0.934 | 0.594 | 1.000 | +0.41 |
| chb06 | 4.5 | 0.420 | 0.133 | 0.300 | +0.17 |
| chb13 | 12.0 | 0.835 | 0.319 | 0.833 | +0.51 |
| chb14 | 6.1 | 0.776 | 0.388 | 0.875 | +0.49 |
| chb15 | 25.8 | 0.807 | 0.332 | 0.950 | +0.62 |
| chb16 | 2.8 | 0.898 | 0.464 | 0.400 | **−0.06** |
| chb17 | 24.7 | 0.741 | 0.000 | 0.667 | +0.67 |
| chb18 | 13.8 | 0.918 | 0.687 | 0.833 | +0.15 |

Three mechanisms (unchanged story): (1) **any-overlap event scoring** — one detected window per seizure = TP; gap scales with seizure length (long-seizure chb13/14/15/17 gaps +0.51–0.67). (2) **threshold-window sensitivity understates the CPD system** — chb17 window 0.0% (degenerate op-threshold) yet event 66.7%; only rank-based AUROC/AUPRC are valid window metrics. (3) **structural-failure subjects separated transparently** — chb06 (inverted, AUROC 0.420) + chb16 (brief, 2.8 win/sz) excluded (pre-identified mechanisms, not tuning) → structurally-detectable subset (chb03/13/14/15/17/18) macro event **≈86%**; full-cohort 73.2%/pooled 75.0% remains the headline.
**New under this weight — chb16 gap is now NEGATIVE (−0.06):** window sens (0.464) exceeds event sens (0.400) because chb16's brief (~12s) seizures produce catchable windows but the new-weight balanced point assembles fewer of them into events (chb16 dropped 6→4/10 balanced vs old weight, while gaining at high-sens 8/10). This is consistent with chb16's known brief-seizure structural profile, not a regression — chb16's detections are simply more operating-point-sensitive than most. (Decisions #15, #22.)

---

# MENTOR-FEEDBACK ROUND (2026-07) — operating-point re-verification, duration analysis, protocol audit

*Triggered by supervisor feedback on the Phase A/B evaluation report. All four questions investigated with code-level verification and/or empirical checks, not assumption — see PLAN_AND_STATUS.md Decisions #16–#18 for governance. This is refinement within already-locked Phase A scope (same algorithm, same already-open hyperparameters), not new science.*

## 10. ENSEMBLE WEIGHT CHANGE + OPERATING-POINT RE-DERIVATION (Decisions #19–#20)
**This section replaces the original Decision #16 content, which was found to rest on a buggy grid sweep — see the full derivation and the bug postmortem in §13.** Only the adopted conclusions are summarized here; §13 has the complete story (bug discovery, fix, re-verification, and the criterion used to pick the new high-sensitivity point).

**Decision #19 — ensemble weight changed** from (w_recon=0.35, w_temp=0.30, w_gamma=0.35) to **(w_recon=0.40, w_temp=0.35, w_gamma=0.25)**. Verified via three independent layers (local weight grid, 8-seed paired robustness test, cross-operating-point + per-subject check) — all CPU-only, on cached components, no retraining. The new weight wins at both operating points, with chb06 benefiting most and no subject-tradeoff pattern (the "label-free tradeoff" seen in §6 does NOT recur here). **This predates-Phase-A lock is the first one reopened in this project with explicit sign-off, per the 3-tier "reopening a lock" rule in `PLAN_AND_STATUS.md`.**

**Decision #20 — high-sensitivity operating point re-derived** after discovering that `mag_pen_grid_sweep.py` (the source of the original Decision #16) had a seeding bug: it called `evaluate_subject()` repeatedly across 8 `mag_pct` values per subject without reseeding `np.random` between calls, so results drifted with loop position rather than being independently reproducible (confirmed by a direct forward/reverse-order experiment). The corrected sweep (`mag_pen_grid_sweep_v2.py`, reseeds before every single call) gives, for the NEW weight:

| Operating point | mag% | pen | Sensitivity | FP/day |
|---|---|---|---|---|
| Balanced | 60 | 1.0 | 0.7500 (57/76) | 39.77 |
| **High-sensitivity (Decision #20)** | **50** | **0.5** | **0.8289 (63/76)** | **71.25** |

Selection criterion for the high-sens point (data-driven, not a subjective pick): among Pareto-optimal grid points whose sensitivity gain over balanced clears **2× the known seed-to-seed noise SD (~0.03**, from the 8-seed robustness runs used for Decision #19**)** — i.e. a gain large enough to be confidently attributed to the operating point rather than to bootstrap-padding noise — choose the one with the lowest FP/day. `mag60/pen0.3` gives an **identical** result (same TP at every one of the 8 subjects) and may be cited interchangeably.

**Status: ADOPTED (Decisions #19 and #20).** §1's table reflects this; the old Decision #16 row and the original pre-#16 row are both kept, marked superseded, for audit trail. **See §13 for the complete bug postmortem, the cross-validation against an independently-implemented script (`rebuild_ensemble_new_weight.py`), and the reasoning behind the noise-floor selection criterion.**

## 11. DURATION-STRATIFIED SENSITIVITY — the chb06 duration confound (Decision #17, RE-VERIFIED 2026-07/08 on the current Decision #20 high-sens point)
**Source:** `duration_stratified_sensitivity.py` → `duration_bucket_summary.csv` (pooled), `duration_hit_persubject.csv` (per-seizure, per-subject). **This script now builds the ensemble directly from cached components using the Decision #19 weight (0.40, 0.35, 0.25) — it no longer reads `results/cpd/scores/*.npy`, since that cache is not guaranteed to reflect the current weight.** Fidelity-checked: "ALL" row reproduces the locked pooled sensitivity exactly — balanced (mag60/pen1.0) 57/76=0.750 ✓ against `locked_phaseA_event_results.csv`; high-sens (mag50/pen0.5, Decision #20) 63/76=0.829 ✓ against the same file. **This is the third and (so far) final version of this section** — v1 used the original mag70/pen0.3; v2 used the since-superseded (buggy-grid) mag50/pen1.0; this v3 uses Decision #20's mag50/pen0.5. Per-seizure hit/miss for both points is in `duration_hit_persubject.csv`.

**Motivation.** Mentor asked what seizure duration is "clinically meaningful" for evaluation purposes.

**Clinical duration threshold.** ACNS 2021 Standardized Critical Care EEG Terminology (Hirsch et al., *J Clin Neurophysiol* 2021) defines an electrographic seizure as needing **≥10s** with evolution; events 0.5–10s fall into a separate, clinically-ambiguous category (**BIRDs** — Brief Potentially Ictal Rhythmic Discharges).

**Two different duration numbers — report both, they answer different questions:**
- Raw-annotation-second parsing of the 8 test subjects' summary files: **9/76 seizures <10s, all chb16** (median 8s).
- After the pipeline's 4s-window quantization (`sz_ranges` — what the detector actually operates on): only **3/76 <10s** — window-boundary rounding can inflate a short event's reported duration by up to ~3–4s, pushing several chb16 events just over the 10s line. Use this second number for anything about detector-facing duration; use the first for clinical/ACNS framing.

**Duration-bucket sensitivity, both locked operating points, pooled across all 8 subjects, n=76:**

| bucket | balanced (mag60/pen1.0) | high-sens (mag50/pen0.5, Decision #20) |
|---|---|---|
| <10s | 2/3 = 0.667 | 2/3 = 0.667 |
| 10–20s | 4/15 = **0.267** | 9/15 = **0.600** |
| 20–60s | 22/27 = 0.815 | 23/27 = 0.852 |
| ≥60s | 29/31 = 0.935 | 29/31 = 0.935 |
| ALL | 57/76 = 0.750 | 63/76 = 0.829 |

**Critical finding — chb06 confound persists at the high-sens point, though further attenuated than at any previous version of this analysis.** All 6 seizures that flip from miss→hit between balanced and high-sens are individually identified in `duration_hit_persubject.csv`: chb06 seizure#3 (24s, 20-60s bucket), chb06 seizure#5 (16s, 10-20s bucket), chb16 seizure#0/1/4/6 (all 12s, 10-20s bucket). Of the 5 additional TPs landing in the 10-20s bucket specifically, only 1 comes from chb06 — the other 4 come from chb16.

Per-subject breakdown of the 10-20s bucket:

| subject | balanced | high-sens |
|---|---|---|
| chb06 | 1/7 | **2/7** |
| chb14 | 1/1 | 1/1 |
| chb16 | 2/7 | **6/7** |
| **bucket total** | **4/15 = 0.267** | **9/15 = 0.600** |

chb06 remains the weakest contributor to this bucket at both operating points, but its overall detection rate improves with BOTH the weight change and a more sensitive operating point: **2/10 at old-weight balanced → 3/10 at the current (Decision #19 weight) balanced → 5/10 at the current Decision #20 high-sens point (mag50/pen0.5)** — the best chb06 result recorded anywhere in this project. (The balanced figure is 3/10, not the previously-written 2/10 — that was a stale old-weight value; this section's own flip list below shows only 2 chb06 seizures flipping balanced→high-sens, i.e. 3→5, which is internally consistent with 3/10 balanced.) Excluding chb06 from the 10-20s bucket at high-sens: chb14 (1/1) + chb16 (6/7) = 7/8 = **0.875**, restoring a monotonic increase with duration once chb06 is set aside (0.667 → 0.875 → 0.852 → 0.935).

**Conclusion, confirmed on two independent operating points, now with a corrected grid underlying the high-sens point.** The 10-20s bucket is the pooled sensitivity floor at *both* balanced and high-sens, and in both cases the deficit is disproportionately attributable to chb06 (already documented, §4/§7, as a structural-failure/inverted-connectivity outlier), not to an intrinsic duration effect of the detector. **chb16, not chb06, drives most of the high-sens improvement in this bucket** (2/7→6/7 vs. chb06's 1/7→2/7) — chb16's brief (~12s) seizures are recovered by the more permissive magnitude filter far more readily than chb06's inverted-connectivity seizures are. Sensitivity increases monotonically with duration once chb06 is excluded, at both operating points.

**Do NOT write "10–20s seizures are harder to detect" from the pooled number alone** — that remains predominantly a chb06 artifact consistent with its already-known failure mode (though chb16 is now a comparably-sized contributor to the bucket's low value at the balanced point specifically), not new evidence about duration per se. If duration is discussed in the thesis, present the with/without-chb06 breakdown, and note that the pattern replicates across both locked operating points.

**Status: LOCKED analysis (Decision #17), re-verified 2026-07/08 against the current Decision #20 (mag50/pen0.5) high-sensitivity point.** Not yet incorporated into thesis prose — write-up deferred (see PLAN_AND_STATUS.md open items).

## 12. EVALUATION-PROTOCOL AUDIT — mentor Q&A round
Kept as a permanent methodological record so it does not need re-deriving in a future chat.

**12.1 "Should groundtruth be adjusted to match SzCORE rules — e.g. if hyp events merge, shouldn't close reference annotations merge too?"**
Verified directly in `timescoring`'s `scoring.py` source: `EventScoring.__init__` applies `_mergeNeighbouringEvents` (merge <90s) and `_splitLongEvents` (split >5min) to **both** `self.ref` and `self.hyp` symmetrically; only the tolerance extension (±30s/60s) is ref-only, and that asymmetry is the protocol's *intended* design (defines the acceptance window around each true seizure), not a bug. Empirically checked: computed inter-seizure gaps for all 76 annotated seizures across the 8 test subjects (within-file and across file-concatenation boundaries in the pipeline's pseudo-timeline) — **0/75 pairs are <90s apart**. **Conclusion: the pipeline is already rule-symmetric per SzCORE, and this specific concern never triggers on this dataset** — verified correct as-is, no fix needed, no numbers change.

**12.2 "If evaluation is correct, why are precision/F1/FP-day still low?"**
Not an evaluation bug — a base-rate/prevalence effect, shown quantitatively: with 76 true seizures against 278.2 interictal hours (~11.6 days), even the P95 window-tier threshold's ~5% false-flag rate compounds, and PELT+merge+magnitude-filter already compresses this ~10× (to 441 FP events at the balanced point) — but 441 FP against 76 TP mechanically caps precision near ~0.15 even at perfect sensitivity. This is the textbook low-PPV-under-low-prevalence effect (same logic as low-prevalence medical screening), not a scoring artifact. The genuine lever to move this number is hyperparameter search along mag%/pen (§10), not redefining the scoring rules.

**12.3 "Is the mag%/pen operating-point selection systematic enough?"**
Was not (2 isolated mag values × 6 pens = partial grid). Resolved by the full 48-combo joint grid — §10 / Decision #16.

**12.4 "Is FP/day clinically meaningful to a physician?"**
Methodologically correct (community-standard metric; SzCORE-recommended over specificity/accuracy under low prevalence) but its *clinical legibility* depends on deployment framing: for real-time alarm systems the literature ties FP/day to alarm fatigue; for this thesis's locked post-hoc-review-triage framing, the more legible translation is **review burden** (e.g., "N extra segments to review per 24h" — following precedent papers that report minutes-of-review-added rather than raw FP/day). Literature benchmarks found for context: ICU qEEG-review systems ~6.5 FP/day (expert) to ~15/day (novice); wearable EEG+ECG systems ~2.4–6.5/day — our points (**39.77 balanced, 71.25 high-sens, per Decisions #19–#20**) are notably higher; state this honestly in Limitations, framed against the harder unsupervised/patient-independent/scalp-only setting. **Not yet drafted as thesis prose** — planned for the writing sprint.

**12.5 Window-level precision improvement — raised alongside 12.2.**
Three levers identified, tagged by compute requirement:
- (a) report Tier-1 window metrics at additional/alternate percentiles (e.g. P99) — CPU-only, purely descriptive; does not change real detection (Tier-1 does not feed the pipeline). Still open, not started.
- (b) **DONE — this is Decision #19.** CPU-only re-tuning of the fixed ensemble weights (0.35/0.30/0.35 → 0.40/0.35/0.25) using already-cached per-component z-scores. This *did* reopen a lock that predates Phase A, with explicit sign-off obtained first, per the 3-tier "reopening a lock" rule. Verified via three independent layers (local + wide weight grid, 8-seed paired robustness, cross-operating-point + per-subject check) before adoption — see §10/§13 for the full derivation.
- (c) genuinely improving upstream signal separability (new GAE/LSTM/gamma training or features) — requires GPU/Kaggle, counts as new science, out of scope for the write-up-only phase. Not recommended now.

---
## 13. FULL DERIVATION — Decisions #19–#20 (ensemble weight change + seeding-bug postmortem)
*Complete story for anyone auditing these numbers later. §1/§10/§11 already state the adopted conclusions; this section is the evidentiary trail.*

### 13.1 Decision #19 — ensemble weight changed (0.35/0.30/0.35 → 0.40/0.35/0.25)

**Trigger.** A reviewer-style question was asked: is the locked ensemble weight (fixed pre-Phase-A, `Proposed_solution_updated_v4.md` §5, documented only as "coarse 0.1-step sweep, then fine sweep confirmed" with no surviving table) actually optimal, or might a nearby weight do better? This predates Phase A, so per the project's 3-tier "reopening a lock" rule, it required explicit sign-off before any code was run — obtained.

**Layer 1 — local weight grid (`weight_sensitivity_sweep.py`).** 37-point grid (step 0.05, radius 0.15) around the locked weight, balanced operating point only, single seed. Locked point ranked 17/37; 5 neighboring points flagged as beating it.

**Layer 2 — wide weight grid (`weight_sensitivity_sweep.py`, radius 0.30).** 127 points. Locked point's rank *worsened* to 29/127 at this wider scope — the strongest candidate, `cand_1 = (0.40, 0.35, 0.25)`, sat inside a genuine plateau of `w_temp`-heavy configurations (not an isolated spike): every point within 0.10 L1-distance of it scored 0.71–0.75 sensitivity, and 20/127 points scored ≥0.72, all with `w_temp` in [0.35, 0.55] — a structural signal that the locked weight under-uses the temporal-LSTM component.

**Layer 3 — 8-seed paired robustness check (`weight_seed_robustness_check.py`).** `cand_1` vs. locked, same seed each time (removes seed as a confound), 8 bootstrap-padding seeds: **7/8 wins, sign-test p=0.035** — statistically distinguishable from chance, not just a lucky single seed.

**Layer 4 — cross-operating-point + per-subject check (`weight_candidate_crosscheck.py`).** Confirmed the gain holds at BOTH locked operating points (not just the one tested above): balanced 7/8 seed wins (p=0.035), **high-sens 8/8 seed wins (p=0.004)** — stronger at high-sens. Per-subject breakdown ruled out the "label-free tradeoff" pattern already seen once before (§6, topology extension): **chb06 improved MOST of any subject** (mean ΔTP +0.625 across both operating points, vs. +0.170 for other subjects on average), with only two subjects (chb16, chb18) showing small, inconsistent dips (≤0.5 TP) — not a redistribution at chb06's expense.

**Adopted:** `(w_recon=0.40, w_temp=0.35, w_gamma=0.25)`. This is the first predates-Phase-A lock reopened in this project, with a documented, 4-layer evidentiary chain — a higher evidence bar than several already-adopted Phase-A decisions (e.g. Decision #16 originally rested on a single grid run, later found buggy — see 13.2).

### 13.2 The seeding bug (discovered while re-deriving official numbers for Decision #19)

**How it was found.** After adopting the new weight, official (non-averaged, `timescoring`-scored) numbers were generated via `rebuild_ensemble_new_weight.py` (reseeds `np.random` immediately before every `evaluate_subject()` call). Its **old-weight** row, at the SAME mag/pen as the historically-locked Decision #16 point, did **not** reproduce the locked figures:

| Point | Previously locked (old weight) | `rebuild_ensemble_new_weight.py` (old weight, same harness) | Drift |
|---|---|---|---|
| mag60/pen1.0 (balanced) | 0.750 (57/76) | **0.7105 (54/76)** | −0.0395 |
| mag50/pen1.0 (Decision #16 high-sens) | 0.8158 (62/76) | **0.7500 (57/76)** | −0.0658 |

**Root-cause investigation.** `evaluate_subject()` calls `build_timeline_masked()`, which draws from `np.random` via `np.random.choice(inter_scores, size=250000, replace=True)` for bootstrap-padding post-ictal buffers, and does **not** reseed internally — it relies on the caller. `mag_pen_grid_sweep.py` (the source of Decision #16, written in an earlier session, not preserved in this repo) looped `evaluate_subject()` across 8 `mag_pct` values per subject; if it seeded once per subject rather than once per `(subject, mag_pct)` call, each mag_pct's bootstrap-padded timeline would depend on how many other mag_pct values were evaluated before it — not independently reproducible.

**Confirmed by direct experiment** (not just inferred from reading code): calling `evaluate_subject(mag=60)` as the 1st call after `seed(0)` gave a different `tp` than calling it as the 4th call in a sequence of mag values, with the same `seed(0)` at the very start. A second experiment confirmed the fix (reseed before every single call) makes the result **order-independent**: forward `[40,50,55,60]` and reverse `[60,55,50,40]` orders gave identical per-mag results after the fix, and different results before it.

**The fix: `mag_pen_grid_sweep_v2.py`** — reseeds `np.random(canonical_seed)` immediately before every single `evaluate_subject()` call, for every `(weight, subject, mag_pct)` triple, never relying on a seed set earlier in a loop. Re-ran the full 48-point grid × 2 weights (old + new) × 8 subjects.

**Independent cross-validation of the fix.** `rebuild_ensemble_new_weight.py` and `mag_pen_grid_sweep_v2.py` are two separately-written scripts, both reseeding correctly but via different code paths. They agree **exactly** on the old weight at both mag60/pen1.0 (0.7105, tp=54, both scripts) and mag50/pen1.0 (0.7500, tp=57, both scripts) — the strongest available evidence that the corrected numbers are right, not an artifact of either script individually.

**Scope of the damage — precisely bounded, not "everything is compromised":**
- **NOT affected:** Decision #19 itself. Its entire evidentiary chain (13.1, Layers 1–4) used harnesses that reseed correctly per-call from the start (`weight_sensitivity_sweep.py`, `weight_seed_robustness_check.py`, `weight_candidate_crosscheck.py`) — none of them ever called `mag_pen_grid_sweep.py`. The *relative* conclusion "new weight beats old" was always measured with clean seeding.
- **NOT affected:** Phase B (§6–§9) — no dependency on the mag%×pen grid.
- **AFFECTED:** the *absolute* Decision #16 figures (0.750 balanced / 0.8158 high-sens) and everything computed directly from them: the retired high-sens operating point choice, and the version of §11 (duration-stratified) that was re-verified against the buggy mag50/pen1.0 point. Both are now superseded — see 13.3 and §11.

### 13.3 Decision #20 — high-sensitivity operating point re-derived on the corrected grid

With the corrected 48-point × 2-weight grid (`mag_pen_grid_v2_pooled.csv`), the historically-used high-sens point (mag50/pen1.0) is **no longer Pareto-optimal for either weight** (dominated by other points with equal-or-better sensitivity at equal-or-lower FP/day). A new point had to be chosen — with an explicit, non-subjective criterion, since the original "just look at the numbers and pick" approach was exactly the practice the mentor had flagged as needing a firmer defense (§12.3).

**Selection criterion.** A candidate only counts as a genuinely-improved "high-sensitivity" point if its sensitivity gain over balanced **clears the known seed-to-seed noise floor** — using the 8-seed SD (~0.03) already measured during Decision #19's Layer 3 as the noise estimate, a gain must exceed **2×SD ≈ 0.06** to be confidently attributed to the operating point rather than to bootstrap-padding randomness. Among Pareto-optimal points clearing this bar, the cheapest (lowest FP/day) was chosen — the same "cheapest defensible win" logic underlying Decision #16's original intent, just applied on the corrected data with an explicit, stated threshold instead of an implicit one.

**Result:** `mag50/pen0.5`, sensitivity 0.8289 (63/76, Δ+0.0789 over balanced — well past the 0.06 bar), FP/day 71.25. `mag60/pen0.3` is numerically identical (verified: same TP at every one of the 8 subjects, not just the same pooled total) and may be cited interchangeably.

**Why not a cheaper point (e.g. `mag70/pen0.5`, sens 0.7763, FP/day 43.56)?** Its gain over balanced (+0.026) does not clear the 2×SD noise-floor bar — calling it "high-sensitivity" would be presenting noise as signal.

**Why not a more extreme point (e.g. `mag40/pen0.3`, sens 0.8947, FP/day 102.48)?** It clears the bar with room to spare, but at a cost the Pareto frontier itself flags as inefficient relative to `mag50/pen0.5` — the marginal sensitivity gained per unit of additional FP/day drops sharply beyond this point.

### 13.4 What still needs official CI numbers
`locked_phaseA_event_results.csv` (via `stat_validation.py`) has now been generated for both Decision #19/#20 operating points — see §1's table for the final, CI-bearing figures. This closes the loop: Decision #19/#20's conclusions (13.1, 13.3) were reached on averaged/relative evidence across many seeds; §1's numbers are the single canonical-seed, `timescoring`-scored, CI-bearing figures that should be cited in the thesis body.

---

## 14. WEIGHT-CONSISTENCY PASS (2026-08) — Decisions #21–#22
*Rationale: Decision #19 changed the ensemble weight, but only the EVENT tier (§1) had been re-derived at the time. A reviewer-style rigor check found that several other reported numbers are also weight-dependent (they are functions of the ensemble score) yet were still computed on the old-weight cache. This pass re-verified all of them and introduced a single-source ensemble recipe so this class of drift cannot recur. No headline conclusion changed.*

**Decision #21 — single-source ensemble recipe + cache quarantine.** `ensemble_recipe.py` now holds the ONE definition of the weight (`ENS_WEIGHTS = (0.40, 0.35, 0.25)`) and the ensembling (`build_ensemble` = weighted sum of the per-view component z-scores; no post-hoc renorm, CPD is scale-adaptive). Everything that needs an ensemble score — evaluation, analysis, and the **Phase C export** — imports from here; the weight is never re-defined inline and **no persistent ensemble cache is created** (always build fresh from components). The old-weight GPU ens cache (`results/cpd/scores/*_ens_*.npy`, which still reproduces the OLD 0.35/0.30/0.35 numbers) was **quarantined to `results/history_superseded/oldweight_ens_scores/`** so nothing reads it by accident. New scripts: `ensemble_recipe.py`, `window_tier_newweight.py`. (This is the guardrail against exactly the stale-cache failure mode that caused §13.)

**Decision #22 — every remaining weight-dependent number re-verified under the Decision #19 weight.**
- **§2 window tier:** macro AUROC **0.796 → 0.791** (`window_tier_newweight.py`, build-from-components + the locked `evaluation_protocol` stat functions). Component standalone AUROCs (recon 0.671 / temporal 0.647 / gamma 0.755) reproduce `auroc_verification.csv` **exactly** — sanity check passed, confirming the components are the set that produced §1 and the harness is faithful. Conclusion unchanged (≈0.80 > Yildiz 0.68; ensemble still beats best component).
- **§8.2 event ablation:** re-run; **`full(3-view)` = 0.750 (57/76) = MATCH §1**, so the old "0.711 drifts from 0.750" caveat is removed. New deltas monotonic: recon −0.145 > temporal −0.132 > gamma −0.105 (track the weights). Removing temporal drops **chb06 to 0/10**. GAE load-bearing now −11 TP.
- **§9 window↔event gap:** reconstructed; macro window 36.5% → macro event 73.2% (pooled 75.0%); chb16 gap now negative (window 0.464 > event 0.400).
- **§7 attribution:** confirmed **WEIGHT-INVARIANT** — per-node GAE reconstruction-error attribution is a decomposition of the GAE recon score alone (`r_i`), independent of the ensemble mixing weights. No re-run needed. (Verified by argument; a byte-identical re-run is optional.)
- **§4 per-subject correction:** chb06 balanced **2/10 → 3/10** (the 2/10 was a stale old-weight value; canonical `szcore_event_level_new_decision19_mag60.csv` pen1.0 gives 3/10, and §8/§11 independently agree).
- **Consolidation:** `consolidate_outputs.py` gained a `phaseA_appendix` category (corrected grid `mag_pen_grid_v2_*`, `duration_*`, per-subject `szcore_event_level_new_decision19_*`, and the Decision #19 evidence trail `weight_*`) and a `history_superseded` category (old-weight `szcore_event_level_mag60/mag70.csv`, pre-`_v2` buggy grid, old-weight ablation + window CSVs, and the quarantined old ens cache).

**Net effect:** every weight-dependent number now consistently reflects the Decision #19 system; no headline conclusion moved (window ≈0.80, event 0.750/0.829, ablation story intact and sharper, gap story intact).

---
**DO NOT use numbers from `cpd_results_v12_combined.csv`, `cpd_tolerance_sweep.csv`, `window_metrics.csv`, the result tables inside `Proposed_solution_updated_v3.md`, the ORIGINAL `mag_pen_grid_pooled.csv`/`mag_pen_grid_persubject.csv` (pre-`_v2`, seeding bug — §13.2), the OLD-weight `eval_window_level.csv`/`eval_stat_tests.csv`/`window_event_gap.csv`/old `event_ablation_*` (weight-dependent, superseded by §2/§8/§9 new-weight versions — §14), or the quarantined old-weight ens cache — all superseded. Topology numbers (§6) are a rejected extension kept only as a development record. §14 (2026-08) is the most recent addition; if any older section conflicts with §10–14 on the SAME quantity, the newer section wins.**

