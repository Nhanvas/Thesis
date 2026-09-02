# RUBRIC TRACKING — thesis scoring checklist (v4, post-attribution, rev. B)

Maps the 8 rubric criteria (`Thesis_Rubric.pdf`, total 100) to where each is covered and what still
needs writing. Update the Status column as chapters get drafted.
Legend: ✅ evidence exists / 🟡 partial / 🔴 to write.

> **v3 CORRECTION (2026-09-01), still binding.** v1 of this file cited **0.750/39.77, 0.829/71.25,
> AUROC 0.791** and pointed at `docs/RESULTS_OF_RECORD.md` + `src/thesis_repro_lock.py`. Those are
> **pre-rebuild numbers that were never reproduced** (they depended on lost components +
> test-selection) and both files are now retired/archived. **Never cite them.**
>
> **v4 UPDATE (2026-09-02).** Three changes: (a) the §0 open item on TEST window macro AUROC is
> **RESOLVED** — 0.805 is verified and recorded in `RESULTS_OF_RECORD_phaseB.md` §3 with a per-subject
> table; (b) `src/` was reorganised, so the figure paths in criterion #8 changed; (c) the attribution
> study has been **executed** — criteria #7 and #8 now have real evidence and a real limitation.
>
> `RESULTS_OF_RECORD_phaseB.md` wins over this file on any number conflict.

---

## 0 · The numbers to cite (single source: `RESULTS_OF_RECORD_phaseB.md`)

### 0.1 Detection (the thesis headline)

| what | value | where |
|---|---|---|
| Pipeline of record | **rlg** = recon-MSE + latent-Mahalanobis + gamma-AEC, equal 1/3, temporal-free | §1 |
| Honest headline (VAL-derived OP, m50/p2.0) | sens 0.618 · prec 0.129 · **F1 0.213** · **27.4 FP/day** | §3 |
| Matched-cell vs §0 baseline (m70/p0.5) | sens 0.645 · prec 0.099 · F1 0.172 · 38.4 FP/day (§0: 0.632/0.097/0.168/38.6) | §3 |
| Pooled TEST Pareto peak | **F1 0.426 @ 4.9 FP/day** (sens 0.474, prec 0.387) — a curve, not a selected OP | §3 |
| Phase-C event headline | F1 0.361 @ 3.6 FP/day | §9 |
| **TEST window macro AUROC** | **0.805** (per-subject: 0.964 / 0.501 / 0.822 / 0.698 / 0.879 / 0.876 / 0.782 / 0.920) | §3 |
| GAE seed-stability (VAL, 4 seeds) | window macro AUROC **0.929 ± 0.002**; event F1@3.6 **0.51 ± 0.034** | §7 |
| Noise floors (gate thresholds) | window seed-SD 0.002 · event seed-SD 0.034 | §7 |
| TEST set | 8 subjects, 76 seizures, 278.2 interictal h, one-shot | §3 |

✅ **v3's open item is CLOSED.** TEST window macro AUROC = 0.805 was verified 2026-09-01 from
`results/phaseB/tier2/rlg_test/final_eval_seed42.csv` and is now a cited row in RoR §3.

### 0.2 Attribution (PROVISIONAL — source: `ATTRIBUTION_SPEC.md` §9, summary in RoR §10)

| what | value | provisional? |
|---|---|---|
| Framing | **XAI for the GAE reconstruction branch** — not localization, not SOZ | — |
| Synthetic gates G-S1 / G-S2 / G-S3 / G-S4′ | all **PASS**; null 0.4912, ceiling 0.9818 | **no** |
| Permutation-null mean, all 50 synthetic cells | 0.4990–0.5013 | **no** |
| Detection sensitivity of the machinery | +25 % anomaly → AUROC ≈ 0.70 | **no** |
| Channel-ranking seed robustness (4 GAE seeds) | Spearman **0.970 ± 0.026** | **no** |
| Label schema actually on disk | **dominant-channel, 1–2 per seizure** (mean \|S\| = 1.31) — NOT the ictal-channel set | yes |
| macro-AUROC, 36 annotated seizures | **0.6497** [0.5663, 0.7390], p_perm = 0.001 | yes |
| macro-AUPRC | **0.3095** = 4.2 × prevalence (0.073) | yes |
| Within-subject label Jaccard | **0.8879** — the reason the D7 control is uninformative | yes |
| Spread metric (focal vs generalized) | **methodological negative** — U-shaped in \|S\|; real labels p = 0.984 | yes |

⚠ **Word the label-scored half as the dominant-channel question.** The labels name 1–2 leading
channels, so those numbers do not measure per-channel binary classification. Say what was measured.

⚠ **The two sentences that decide this chapter.**
(1) The label file is **dominant-channel (1–2 per seizure), not the §3.2 ictal set**, so every
label-scored number answers a narrower question than the spec poses. Say so wherever they appear.
(2) The subject-constant control (0.7758) scores higher than the per-seizure score (0.6497). That is
**not** "attribution failed". A 1–2 channel label from a patient's fixed focus is almost forced to be
constant within a subject (Jaccard 0.8879), so the control wins by noise-averaging alone. The correct
claim is: **with these labels, per-seizure attribution and a subject-level channel prior cannot be
distinguished.** Write it that way, or a reviewer will read the Δ and reach the wrong conclusion — and
so will you, six weeks from now.

---

## 1 · Criteria

| # | Criterion (pts) | Status | Covered by | What's still needed |
|---|---|---|---|---|
| 1 | **Literature review + knowledge gap** (PI 7C, 15) | 🟡 | Ch.1 Intro + Related Work; `docs/archive/Spatial_Localization...md` (field survey); `Thesis_Reference_Sheet.md` | Write Related Work prose; complete the comparison table + pending DOIs; state the unsupervised graph-attribution gap explicitly. Use Yildiz = 0.68. **Never cite the Transformer sens 0.765/40.6 as CHB-MIT — it is a TUH result.** For the attribution chapter, EEG-CGS (AAAI 2023) is the framework comparator (bar 0.70/0.55/0.43/0.78, TUSZ). |
| 2 | **Research problem + realistic constraints** (10) | 🟡 | Ch.1 Problem statement | Write problem/constraints: label-free, patient-independent, no per-channel SOZ ground truth, **post-hoc review triage (not a real-time alarm)**. Frame FP/day as review burden. |
| 3 | **Appropriate principles / methods / tools** (PI 1A, 10) | ✅ | Ch.2/3 Methodology; `src/` | Methods prose with named equations: wPLI, AEC, top-k20, GAE loss `MSE(A) + 0.1·MSE(X)`, robust-z (median/MAD), latent Mahalanobis (LedoitWolf, per-subject interictal fit), PELT + penalty, SzCORE. Disclose that the original GAE training loop was reconstructed under PREREG_01 and validated by Gate R-GAE. For attribution, state the p95 aggregation and that it was pre-registered. |
| 4 | **Design considers impacts** (PI 4C, 10) | ✅ | `docs/archive/Proposed_solution_updated_v5.md` §XIII **DM6** | Fold DM6 (deployment strategy) into the report's Decision-Matrix section so it is visible in the report, not only in the solution doc. |
| 5 | **Result meets/exceeds objectives** (20) | ✅ | Ch.4 Results; `RESULTS_OF_RECORD_phaseB.md` §1–§9; `results/phaseB/tier2/` | Write Results using §0.1. Frame honestly: the defensible win is **precision/F1 at matched-or-lower FP/day + full reproducibility**, not a sensitivity gain (0.632→0.645 is within CI). Report the Pareto frontier as dominance evidence. |
| 6 | **Evaluation of validity / reliability / performance** (10) | ✅ | Ch.4 Evaluation | SzCORE-exact scoring (`timescoring`), Wilson CIs (sens/prec) + Poisson CIs (FP/day), **4-seed GAE robustness (§7)**, branch ablation (E1/E2), the **Phase-C negatives (§8–§9) as an honest reliability probe**, and now two more rigor exhibits: the **synthetic attribution sanity check** (exact ground truth, clean null on 50/50 cells) and the **machine-verified checkpoint provenance** (corr 1.0000000 on 16/16 committed TEST arrays, `docs/PROVENANCE.md`). The slope-gate false positive caught by multi-seed remains the strongest single exhibit. |
| 7 | **Significance + impacts + applicability** (PI 4C, 10) | ✅ | Ch.5 Discussion; `ATTRIBUTION_SPEC.md` §9 | Clinical review-triage value; **channel attribution as the XAI differentiator, now with measured evidence** (§0.2), not a promise. Honest limitations: FP/day is structural to label-free anomaly detection; chb06/chb14 are representation-limited; attribution ≠ SOZ; the label file is dominant-channel not ictal-set (§3.3), so it cannot test per-seizure attribution (Jaccard 0.8879); the spread metric is a negative; single dataset, no external validation. |
| 8 | **Written report: format + graphics + statistics + references** (15) | 🔴 | whole report; `src/figures/`; `Report_format.md` | Figures: pipeline diagram, CPD mechanism, connectivity, per-subject panel, attribution head-maps, synthetic AUROC-vs-α curve, AUROC-vs-\|S\| scatter. Correct citations; format compliance; Grammarly + AI/plagiarism check. Attribution figures are **already generated**: `src/figures/attribution_figures.py` → `figures/attribution/` (`fig1_synthetic`, `fig2_seed_robustness`, `fig3_rank_heatmap` — label-free and final; `fig4_persubject_forest` — PROVISIONAL; plus `attribution_top3_channels.csv` for the appendix). **Path update:** figure scripts now live in `src/figures/` (`fig5_eight_subjects.py`, `fig_B_raw_eeg_pelt.py`, `plot_event_level.py`, `attribution_headmap.py`, `visualize_channel_attribution.py`, `visualize_chb06_inversion.py`). `fig_A_three_scores.py` was **deleted** — it plotted the dropped `z_temporal` branch; recover from `git show phase-c-final:src/fig_A_three_scores.py` and retarget to zrecon/zlatent/zgamma if that figure is wanted. |

---

## 2 · Highest-leverage reminders

- **#4 + #7 = 20 pts on ABET PI 4C** (impact + applicability) — commonly under-served. DM6 + the
  attribution/XAI differentiator feed these directly; make them prominent.
- **#5 (20) is locked** — the numbers exist and are reproducible. Just write them clearly.
- **#1 + #8 (30)** are the biggest *writing* lifts — front-load Related Work and start figures early.
- **Report every negative as a strength** (falsification with a documented mechanism), not as a hidden
  failure. There are now three: the Phase-C 7-lever program, the attribution spread metric, and the
  uninformative D7 control. Together they are the intellectual core of the Discussion.
- Sensitivity, precision, and FP/day are always reported **together**; never headline a single metric.
- The attribution chapter has a **complete label-free half** (machinery + seed robustness) that does not
  depend on the supervisor's freeze. Write that half now; the label-scored half is PROVISIONAL and only
  §9.3 of the spec changes if the freeze arrives.

---

## 3 · Report-writing hazards (checked before submission)

1. No pre-rebuild number (0.750 / 0.829 / 0.791 / 39.77 / 71.25) appears anywhere.
2. No number is cited from `docs/archive/` or `results/history_superseded/`.
3. ~~TEST window macro AUROC unverified~~ — **RESOLVED**; 0.805 is in RoR §3 with a per-subject table.
4. Every cited figure traces to a file under `results/phaseB/tier2/`, `results/retrain_v3p1/`,
   `results/phaseC/`, or `results/attribution_v6/`.
5. The temporal/LSTM branch is described as **dropped** (PREREG_TIER2 Amendment A1) — not as part of
   the final system.
6. Phase D is described as **Future Work, deliberately not executed** — a time-boxed decision.
7. **Attribution is never called localization or SOZ**, and every label-scored number carries the
   PROVISIONAL qualifier.
8. **The D7 control is described as uninformative, not as a negative result about the method** (§0.2).
8b. **The label file is described as dominant-channel, not as the §3.2 ictal set** — no sentence claims
    per-channel binary classification over the full ictal field was evaluated.
9. **The spread metric is reported as a methodological negative** — it is not used to classify
   focal vs generalized anywhere in the report.
10. No checkpoint is identified by filename. The constants **0.8676 / 0.836** are pre-rebuild §0 values
    and must not appear as the canonical model's fingerprint. Canonical = bias 1.1597, chb13 0.8319
    (`docs/PROVENANCE.md`).
