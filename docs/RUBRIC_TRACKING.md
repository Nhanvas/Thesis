# RUBRIC TRACKING — thesis scoring checklist
*Maps each of the 8 rubric criteria (from `Thesis_Rubric.pdf`, total 100) to where it is covered in the
report and what still needs writing. Update the Status column as chapters get drafted.
Legend: ✅ evidence exists / 🟡 partial / 🔴 to write.*

| # | Criterion (pts) | Status | Covered by (chapter / file) | What's still needed |
|---|---|---|---|---|
| 1 | **Literature review + knowledge gap** (PI 7C, 15) | 🟡 | Ch.1 Intro + Related Work; `docs/Proposed_solution_updated_v5.md` §II; the two research memos (Literature_Review, Spatial_Localization) | Write Related Work prose; **complete literature comparison table** + the 4 pending DOIs; state the unsupervised-graph-attribution gap explicitly (Layer-3 is novel — no product has it). Use Yildiz=0.68; Transformer=TUH not CHB-MIT. |
| 2 | **Research problem + realistic constraints** (10) | 🟡 | Ch.1 Problem statement; post-hoc-triage framing; patient-independent constraint | Write the problem/constraint section; state label-free + no per-channel SOZ ground truth + patient-independence as design constraints. |
| 3 | **Appropriate principles / methods / tools** (PI 1A, 10) | ✅ | Ch.2/3 Methodology; `docs/Proposed_solution_updated_v5.md` §III (named equations); `src/` code | Write Methods prose with **named equations** (wPLI, AEC, GAE loss MSE(A)+0.1·MSE(X), robust z-norm, PELT + BIC penalty, SzCORE). Note training-script gap honestly. |
| 4 | **Design considers impacts — global/economic/environmental/societal** (PI 4C, 10) | ✅ | `docs/Proposed_solution_updated_v5.md` §XIII **DM6 (Deployment Strategy)** | Fold DM6 into the report (Decision-Matrix section). This closed the one real rubric gap — make sure it's visible in the written report, not just the solution doc. |
| 5 | **Result meets/exceeds objectives** (20) | ✅ | Ch.4 Results; `docs/RESULTS_OF_RECORD.md` §1–§2; `results/` CITED CSVs | Write Results prose: 0.750/39.77 balanced, 0.829/71.25 high-sens, AUROC 0.791, ablation, duration, attribution. Reproduces bit-exact (`src/thesis_repro_lock.py`). |
| 6 | **Evaluation of validity / reliability / performance** (10) | ✅ | Ch.4 Evaluation; SzCORE protocol; CIs (`stat_validation`); multi-seed robustness; ablation | Write Evaluation prose: SzCORE-exact scoring, CIs, seed-robustness, leave-one-view-out ablation, **#24 filter tested & rejected** as an honest reliability probe (ROR §15). |
| 7 | **Significance + positive/negative impacts + applicability** (PI 4C, 10) | 🟡 | Ch.5 Discussion/Significance; market research (Layer-3 differentiator); FP/day→review-burden reframe | Write Significance: clinical review-triage value, Layer-3 AI attribution as market differentiator, honest limitations (FP/day, chb06, attribution≠SOZ), proof-of-concept for the larger product. |
| 8 | **Written report: format + graphics + statistics + references** (15) | 🔴 | whole report; figures (pipeline, CPD mechanism, connectivity, attribution head-maps); `Thesis_report_format` | **Figures** (rebuild on `src/szcore_eval.build_timeline_masked` + `parse_summary_edf_list`; scaffolds in `src/fig_*`). Correct citations; statistically-justified interpretation; format compliance; Grammarly + AI/plagiarism check. |

## Highest-leverage reminders
- **#4 + #7 = 20 pts on ABET PI 4C** (impact + applicability) — commonly under-served by engineering
  students. DM6 + the Layer-3 market gap directly feed these; make them prominent.
- **#5 (20) is strong and locked** — just write it clearly and cite the reproducible numbers.
- **#1 + #8 (30)** are the biggest *writing* lifts — front-load Related Work + start figures early.
- Report the **#24 rejection as a strength** (falsification with a mechanism), not a hidden negative —
  it earns rigor points under #6.
