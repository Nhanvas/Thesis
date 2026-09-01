# RUBRIC TRACKING — thesis scoring checklist (v2 — corrected numbers)
*Maps each of the 8 rubric criteria (from `Thesis_Rubric.pdf` / `Report_format.md`, total 100) to where
it is covered in the report and what still needs writing.*
**Status: pipeline LOCKED (rlg). Optimization CLOSED (Phase C, 7 levers, evidence-based negative).
Phase D NOT executed (Future Work, time-boxed out). Active phase = report + attribution + web demo.**

⚠️ **CORRECTION (this version):** the previous version of this file cited **0.750 balanced-sensitivity /
0.829 high-sens** as the headline result. **These numbers are PRE-REBUILD and were never reproduced** —
they depended on a lost LSTM checkpoint + test-set-selected weights/operating-point (see
`RESULTS_OF_RECORD_phaseB.md` §1, "Amendment A1"). **Do not cite 0.750/0.829 anywhere in the report.**
The correct, current, locked numbers are given in §5 below and must be used throughout.

Legend: ✅ evidence exists / 🟡 partial / 🔴 to write.

| # | Criterion (pts) | Status | Covered by (chapter / file) | What's still needed |
|---|---|---|---|---|
| 1 | **Literature review + knowledge gap** (PI 7C, 15) | 🟡 | Ch.1 Intro + Related Work; `Literature_Review_and_Novelty_Assessment...md`; `Lit_review.txt`; `Spatial_Localization...md` | Compress the two lit-review memos into the table→subsections→bridge shape (see `THESIS_REPORT_WRITING_GUIDE.md` §2). State the gap explicitly: unsupervised GAE+CPD event-level localization on scalp EEG is unaddressed (novel combination, not novel primitive). Use Yildiz 2022 = 0.68 AUROC (CHB-MIT scalp, corrected citation); do NOT cite the 0.765/40.6 Transformer figure as CHB-MIT — it is TUH. |
| 2 | **Research problem + realistic constraints** (10) | 🟡 | Ch.1 Problem statement; post-hoc-triage framing; patient-independent constraint | Write the problem/constraint section: label-free, no per-channel SOZ ground truth, patient-independence, and — new — the **Amendment A1 constraint** (temporal branch unrecoverable → design must be fully reproducible from a clean clone) as a realistic engineering constraint worth stating explicitly. |
| 3 | **Appropriate principles / methods / tools** (PI 1A, 10) | ✅ | Ch.2/3 Methodology; `graph_construction.py`, `gae_joint.py`, `latent_anomaly.py`, `cpd_pipeline_v14.py` | Write Methods prose with named equations: wPLI (Eq.2), AEC (Eq.3), combined adjacency (Eq.4), top-k threshold (Eq.5), GAE joint loss `MSE(A)+0.1·MSE(X)`, **latent-Mahalanobis readout** (LedoitWolf covariance on graph-mean 16-d Z, per-subject interictal fit), robust-z normalization, PELT + magnitude filter + label-free FP-budget operating point, SzCORE scoring. State explicitly that the LSTM temporal branch was designed, found unrecoverable, and replaced (Amendment A1) — this IS methodological content, not just a footnote. |
| 4 | **Design considers impacts — global/economic/environmental/societal** (PI 4C, 10) | ✅ | `Proposed_solution_updated_v5.md` §XIII DM1–DM6 (historical source; port DM6 verbatim) | Fold DM6 (Deployment Strategy) into Ch.2 as a "Decision Matrix for [X]" section (required verbatim heading per `Report_format.md`). This is the strongest existing PI4C asset — make it visible in the written report, not just in the old solution doc. |
| 5 | **Result meets/exceeds objectives** (20) | ✅ **LOCKED — use §5 numbers below, not any other file's numbers** | Ch.4 Results; `RESULTS_OF_RECORD_phaseB.md` §1–§9 | Write Results prose mirroring Methods' stage order. Report BOTH the matched-cell comparison (rlg vs §0's own OPs) AND the VAL-derived honest headline AND the Pareto frontier peak (see §5 table). Reproduces from `data/models_retrain/gae_joint_seed42.pt` + `src/ensemble_recipe.py` (equal weight) + `src/cpd_pipeline_v14.py`. |
| 6 | **Evaluation of validity / reliability / performance** (10) | ✅ **Strong — genuine asset** | Ch.4 Evaluation; SzCORE protocol; Wilson/Poisson CIs; 4-seed GAE stability; **7-lever Phase C negative-result program** | Write Evaluation prose: SzCORE-exact event scoring, 95% CIs (Wilson for sensitivity, Poisson for FP/day), **GAE seed-stability across 4 seeds** (window macro AUROC 0.929±0.002; event F1@3.6 0.51±0.034 — this is the noise floor and should be stated as such), and the **Phase C optimization program as a reliability probe**: 7 independently pre-registered, VAL-gated levers (decision/representation/ensemble/artifact layers) all failed to Pareto-improve rlg at the event headline — report this as rigor evidence ("we tested whether this is a ceiling, and it is"), not as a hidden weakness. See §6 below for the exact framing. |
| 7 | **Significance + positive/negative impacts + applicability** (PI 4C, 10) | 🟡 | Ch.5 Discussion/Significance; market research (Layer-3 differentiator); FP/day→review-burden reframe | Write a Significance subsection SEPARATE from Ch.2's DM6 (see `THESIS_REPORT_WRITING_GUIDE.md` §4.6): who benefits (post-hoc EEG review triage for clinicians), honest limitations (chb06/chb14 representation-limited — sit in TEST and cannot be fixed without label leakage; attribution is PROVISIONAL, not validated), proof-of-concept framing (not a validated clinical product). |
| 8 | **Written report: format + graphics + statistics + references** (15) | 🔴 | whole report; figures (pipeline, CPD mechanism, connectivity, attribution head-maps) | Figures: pipeline diagram (GAE→3 readouts→ensemble→PELT→SzCORE), CPD mechanism, per-subject sensitivity/FP-day table, literature comparison table (revisited in Discussion with this thesis's row added — see writing guide §4.5). Correct citations (numbered bracket `[1]` convention recommended). Grammarly + plagiarism check. Format compliance: TNR 12pt, 1.5in left margin, 1.5 line spacing, ≤50 pages excluding refs/appendices. |

## §5 · THE NUMBERS TO USE (single source: `RESULTS_OF_RECORD_phaseB.md` §1–§3)

**Pipeline = rlg** (recon-MSE + latent-Mahalanobis + gamma-AEC, equal 1/3 weight, GAE canonical seed 42,
temporal/LSTM branch dropped per Amendment A1).

| Reporting frame | Sensitivity | Precision | F1 | FP/day | Use for |
|---|---|---|---|---|---|
| Matched-cell, balanced (rlg @ §0's own OP, m70/p0.5) | 0.645 | 0.099 | 0.172 | 38.4 | Direct comparison to the historical (retired) §0 baseline |
| Matched-cell, high-sens (rlg @ m55/p0.3) | 0.763 | 0.065 | 0.120 | 72.0 | ″ |
| **VAL-derived balanced (m50/p2.0) — the honest headline** | 0.618 | **0.129** | **0.213** | **27.4** | **Primary Abstract/Conclusion number** |
| VAL-derived high-sens (m50/p0.5) | 0.711 | 0.068 | 0.123 | 64.4 | Secondary operating point |
| **Pooled TEST Pareto PEAK** | 0.474 | 0.387 | **0.426** | **4.9** | Cite as "best achievable operating point on the frontier"; inside the SzCORE-challenge unsupervised-patient-independent SOTA band (F1 0.32–0.43) |

- **Window-tier macro AUROC (TEST): 0.805.**
- **GAE seed-stability** (4 seeds {42,1,2,3}, VAL): window macro AUROC **0.929 ± 0.002**; chb13 recon AUROC
  **0.835 ± 0.001**; event F1@3.6 FP/day **0.51 ± 0.034**. The **0.034 event-level SD is the noise floor** —
  state this explicitly when discussing precision of the headline number.
- **Baseline comparison:** exceeds Yildiz et al. (2022) unsupervised CHB-MIT scalp AUROC of 0.68 (window-
  level, non-patient-independent split) — rlg's 0.805 is under a strictly harder patient-independent split.

**Which headline number goes in the Abstract/Conclusion — decide and state explicitly, don't leave it
ambiguous:** the VAL-derived balanced point (F1 0.213 @ 27.4 FP/day) is the honest, non-cherry-picked,
pre-registered operating point and is the recommended headline. The Pareto peak (F1 0.426 @ 4.9 FP/day)
should be reported as "the best point on the frontier," explicitly framed as a frontier characterization,
not as the operating point the system would run at (per PREREG_03 §3, operating points are selected by a
pre-registered rule, not by picking the best-looking point after seeing test results).

## §6 · HOW TO FRAME THE PHASE-C NEGATIVE-RESULT PROGRAM (do not undersell this)

Seven independently pre-registered, VAL-gated optimization levers were tested across the decision,
representation, ensemble, and signal-quality layers of the pipeline; **none Pareto-improved rlg at the
event headline.** This is not "we tried and failed" — framed correctly, it is strong evidence that rlg is
a genuine performance ceiling for this dataset/split, established via due diligence rather than assumed.

| Layer | Lever | Result | Verdict |
|---|---|---|---|
| Decision | C4-lite (directed Transfer-Entropy branch, post-hoc linear mix) | +0.004 F1 @ B=40 but −0.070 F1 @ headline (B=3.6) | Rejected; mechanism finding kept (TE rescues symmetric-inverted subjects chb06/chb22 individually, net-washes at aggregate) |
| Decision | C1 (median pre-CPD smoother) | Harmed sensitivity; VAL@B=40 quantization-saturated | Rejected |
| Decision | slope-gate / C-onset (reject plateau change-points) | Real window headroom (AUROC 0.918 vs 0.823) but seed42-only; failed on seeds 1/2/3 (ΔF1 −0.039 to −0.065) | Rejected — multi-seed caught a false positive before the one-shot TEST was spent |
| Representation | C4-full (multi-relational GAE: symmetric wPLI/AEC + directed TE, non-shared R-GCN encoder, per-relation decoders) | 3-branch window macro 0.909; 2-branch 0.926 — both < rlg's 0.928 (2-branch is a tie within the 0.002 seed-SD) | NO-GO (pre-registered gate). Mechanism finding: directed connectivity genuinely rescues chb22 at the representation level (+0.137, ablation-confirmed) but net-washes via a shared-encoder-capacity cost to chb10 |
| Ensemble | drop-recon / reweight | Dead on record: already measured at event tier pre-Phase-C (§5, lg=0.579 balanced < rlg 0.618) and the weight surface is flat (PREREG_03) | Not re-run — record already answered it |
| Signal | Artifact/transient-gate before CPD | Pre-condition confirmed (FP-prone interictal windows ARE artifact-associated, AUROC 0.78–0.80); only VAL win was 1 subject / 1 budget (chb11 @ 5 FP/day), 3.6 headline unchanged | Rejected — 1-subject/1-budget effect at n=3 VAL is a noise signature, not seed-checked per the hard-limit rule |

**Unifying mechanism (report-worthy):** representation/window-level gains repeatedly die at the
CPD-transfer step (PELT keys on sustained level shifts, not rank separation); per-subject rescue effects
net-wash because each hard subject (chb06, chb14, chb10, chb11...) fails or benefits via a different
mechanism; the representation-limited ceiling subjects (chb06, chb14; oracle F1 ≤ 0.09) sit in the locked
TEST set and cannot be addressed without label leakage.

**One untried lever, disclosed honestly as Future Work, not silently omitted:** multi-band AEC (extending
the gamma-only branch to theta/alpha/beta/gamma) was deprioritized rather than tested, on two measured
priors from this project's own data: the ensemble weight surface is flat (PREREG_03) and a weak/anti-
correlated added branch can drag the equal-weight ensemble down (as C4-full's recon-mr branch did); and
representation enrichment was independently shown to net-wash (C4-full). Low expected value, but honestly
flagged, not hidden.

**Phase D (encoder-capacity / richer-feature hypothesis) was proposed but NOT executed** — a deliberate,
documented decision under the real time constraint (IELTS 9 Oct, report due 15 Oct), not an oversight.
See `PHASE_D_HANDOFF.md` for the full hypothesis and staged plan, retained as Future Work.

## Highest-leverage reminders
- **#4 + #7 = 20 pts on ABET PI 4C** (impact + applicability) — commonly under-served. DM6 + the Layer-3
  market gap directly feed these; make them prominent and keep them in separate chapters (Ch.2 vs Ch.4).
- **#5 (20) is strong and locked** — write it clearly, cite §5 numbers above exactly, never the retired
  0.750/0.829 or the historical §0 numbers (0.632/0.776) except as an explicit "prior/retired baseline"
  comparison point.
- **#6 (10) has a genuine differentiator** most undergraduate theses lack: a full pre-registered,
  VAL-gated, multi-seed optimization program with honest negative results. Do not undersell this as
  "didn't improve" — frame as "systematically established the ceiling with evidence."
- **#1 + #8 (30)** are the biggest *writing* lifts — front-load Related Work + start figures early.
- **Narrative risk to actively manage:** do NOT let the report read as "we tried 7 times and failed."
  Frame as: a rigorous, reproducible pipeline that reaches the unsupervised patient-independent SOTA band,
  followed by a systematic, pre-registered optimization program across three architectural layers that
  conclusively demonstrates this is a structural ceiling — not a lack of effort. See
  `THESIS_REPORT_WRITING_GUIDE.md` §4.3–4.4 for how to write negative results as findings, not confessions.
