# RUBRIC TRACKING — thesis scoring checklist (v3, post-Phase-C)

Maps the 8 rubric criteria (`Thesis_Rubric.pdf`, total 100) to where each is covered and what still
needs writing. Update the Status column as chapters get drafted.
Legend: ✅ evidence exists / 🟡 partial / 🔴 to write.

> **v3 CORRECTION (2026-09-01).** v1 of this file cited **0.750/39.77, 0.829/71.25, AUROC 0.791** and
> pointed at `docs/RESULTS_OF_RECORD.md` + `src/thesis_repro_lock.py`. Those are **pre-rebuild numbers
> that were never reproduced** (they depended on lost components + test-selection) and both of those
> files are now retired/archived. **Never cite them.** The numbers below come from
> `docs/RESULTS_OF_RECORD_phaseB.md`, which wins over this file on any conflict.

---

## 0 · The numbers to cite (single source: `RESULTS_OF_RECORD_phaseB.md`)

| what | value | where |
|---|---|---|
| Pipeline of record | **rlg** = recon-MSE + latent-Mahalanobis + gamma-AEC, equal 1/3, temporal-free | §1 |
| Honest headline (VAL-derived OP, m50/p2.0) | sens 0.618 · prec 0.129 · **F1 0.213** · **27.4 FP/day** | §3 |
| Matched-cell vs §0 baseline (m70/p0.5) | sens 0.645 · prec 0.099 · F1 0.172 · 38.4 FP/day (§0: 0.632/0.097/0.168/38.6) | §3 |
| Pooled TEST Pareto peak | **F1 0.426 @ 4.9 FP/day** (sens 0.474, prec 0.387) — reported as a curve, not a selected OP | §3 |
| Phase-C event headline | F1 0.361 @ 3.6 FP/day | §9 |
| GAE seed-stability (VAL, 4 seeds) | window macro AUROC **0.929 ± 0.002**; event F1@3.6 **0.51 ± 0.034** | §7 |
| Noise floors (gate thresholds) | window seed-SD 0.002 · event seed-SD 0.034 | §7 |
| TEST set | 8 subjects, 76 seizures, 278.2 interictal h, one-shot | §3 |

⚠ **Open item:** the TEST **window macro AUROC** is not recorded in `RESULTS_OF_RECORD_phaseB.md`
(only the VAL 0.929). The figure 0.805 circulates in handoffs/memory without a cited row. **Verify it
from `results/phaseB/tier2/` before it enters the report**, then add it to §3 of the RoR.

---

## 1 · Criteria

| # | Criterion (pts) | Status | Covered by | What's still needed |
|---|---|---|---|---|
| 1 | **Literature review + knowledge gap** (PI 7C, 15) | 🟡 | Ch.1 Intro + Related Work; `Literature_Review...md`; `Spatial_Localization...md` | Write Related Work prose; complete the comparison table + pending DOIs; state the unsupervised graph-attribution gap explicitly. Use Yildiz = 0.68. **Never cite the Transformer sens 0.765/40.6 as CHB-MIT — it is a TUH result.** |
| 2 | **Research problem + realistic constraints** (10) | 🟡 | Ch.1 Problem statement | Write problem/constraints: label-free, patient-independent, no per-channel SOZ ground truth, **post-hoc review triage (not a real-time alarm)**. Frame FP/day as review burden. |
| 3 | **Appropriate principles / methods / tools** (PI 1A, 10) | ✅ | Ch.2/3 Methodology; `src/` | Methods prose with named equations: wPLI, AEC, top-k20, GAE loss `MSE(A) + 0.1·MSE(X)`, robust-z (median/MAD), latent Mahalanobis (LedoitWolf, per-subject interictal fit), PELT + penalty, SzCORE. Disclose that the original GAE training loop was reconstructed under PREREG_01 and validated by Gate R-GAE. |
| 4 | **Design considers impacts** (PI 4C, 10) | ✅ | `docs/archive/Proposed_solution_updated_v5.md` §XIII **DM6** | Fold DM6 (deployment strategy) into the report's Decision-Matrix section so it is visible in the report, not only in the solution doc. |
| 5 | **Result meets/exceeds objectives** (20) | ✅ | Ch.4 Results; `RESULTS_OF_RECORD_phaseB.md` §1–§9; `results/phaseB/tier2/` | Write Results using §0 above. Frame honestly: the defensible win is **precision/F1 at matched-or-lower FP/day + full reproducibility**, not a sensitivity gain (0.632→0.645 is within CI). Report the Pareto frontier as dominance evidence. |
| 6 | **Evaluation of validity / reliability / performance** (10) | ✅ | Ch.4 Evaluation | SzCORE-exact scoring (`timescoring`), Wilson CIs (sens/prec) + Poisson CIs (FP/day), **4-seed GAE robustness (§7)**, branch ablation (E1/E2), and the **Phase-C negatives (§8–§9) as an honest reliability probe** — seven pre-registered VAL-gated levers, none Pareto-improved rlg. The slope-gate false positive caught by multi-seed is the strongest rigor exhibit. |
| 7 | **Significance + impacts + applicability** (PI 4C, 10) | 🟡 | Ch.5 Discussion | Clinical review-triage value; channel attribution as XAI differentiator; honest limitations: FP/day is structural to label-free anomaly detection, chb06/chb14 are representation-limited, attribution ≠ SOZ, single-dataset (no external validation). |
| 8 | **Written report: format + graphics + statistics + references** (15) | 🔴 | whole report; `src/fig_*`, `src/fig5_eight_subjects.py`, `src/plot_event_level.py`; `Report_format.md` | Figures: pipeline diagram, CPD mechanism, connectivity, per-subject panel, attribution head-maps. Correct citations; format compliance; Grammarly + AI/plagiarism check. |

---

## 2 · Highest-leverage reminders

- **#4 + #7 = 20 pts on ABET PI 4C** (impact + applicability) — commonly under-served. DM6 + the
  attribution/XAI differentiator feed these directly; make them prominent.
- **#5 (20) is locked** — the numbers exist and are reproducible. Just write them clearly and cite §3.
- **#1 + #8 (30)** are the biggest *writing* lifts — front-load Related Work and start figures early.
- **Report the Phase-C negatives as a strength** (falsification with a documented mechanism), not as a
  hidden failure. It is worth real points under #6 and is the intellectual core of the Discussion.
- Sensitivity, precision, and FP/day are always reported **together**; never optimize or headline a
  single metric in isolation.

---

## 3 · Report-writing hazards (checked before submission)

1. No pre-rebuild number (0.750 / 0.829 / 0.791 / 39.77 / 71.25) appears anywhere.
2. No number is cited from `docs/archive/` or `results/history_superseded/`.
3. The TEST window macro AUROC is either verified from CSV or omitted (see §0 open item).
4. Every cited figure traces to a file under `results/phaseB/tier2/`, `results/retrain_v3p1/`, or
   `results/phaseC/`.
5. The temporal/LSTM branch is described as **dropped** (PREREG_TIER2 Amendment A1) — not as part of
   the final system.
6. Phase D is described as **Future Work, deliberately not executed** — a time-boxed decision, not an
   oversight.
