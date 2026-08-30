# PROJECT HANDOFF — Unsupervised Seizure Temporal Localization (GAE + CPD)
*Single onboarding doc for the next session. Written after the provenance/consolidation phase closed.*

---

## 0. How to use this doc
You are picking up a biomedical-engineering thesis mid-project. This doc gives you the full picture:
identity, locked results, repo layout, what's done, what's left. **For any NUMBER, the authoritative
source is `docs/RESULTS_OF_RECORD.md` (ROR) — it wins over this doc.** For status/decisions,
`docs/PLAN_AND_STATUS.md`. Don't re-derive or re-run locked results unless asked.

The student is **Boti (Nguyen Quoc Trung Nhan, BEBEIU22184)**. Work conversationally in **Vietnamese**;
code/deliverables/governance files in **English**. Boti is the final decision-maker and executes locally
(Windows, Cursor, `F:\Study\Thesis\Code`); the assistant acts as research director — issue commands /
scripts, Boti runs and returns output. **The real filesystem on Boti's machine is the source of truth**,
not any uploaded copy. Never work from stale copies; verify against the machine.

---

## 1. Thesis identity (immutable)
- **Title:** *Unsupervised Epileptic Seizure Temporal Localization in Scalp EEG using Graph Autoencoder and Change Point Detection.*
- **Supervisor:** Hà Thị Thanh Hương (Assoc. Prof.), Biomedical Engineering, International University VNU-HCM (ABET).
- **Dataset:** CHB-MIT scalp EEG, 18-ch bipolar, 256 Hz. **Test = 8 subjects** (chb03, 06, 13, 14, 15, 16, 17, 18), **76 seizures**. Split permanent (seed 42).
- **Framing (locked):** POST-HOC EEG review triage, NOT real-time alarm. Higher FP/day is acceptable.
- **Method (locked):** per-window connectivity graphs (wPLI+AEC, top-k 20%) → Joint GAE (GCNConv 23→64→16, MSE(A)+0.1·MSE(X)) + temporal LSTM + gamma AEC → ensemble anomaly z-score (weighted sum, weights `(0.40, 0.35, 0.25)`, defined ONCE in `src/ensemble_recipe.py`) → PELT change-point detection (`src/cpd_pipeline_v14.py`) for onset/offset. Unsupervised, patient-independent. Interpretability: per-node GAE reconstruction-error channel attribution (claimed as attribution, NOT clinical SOZ).
- **This thesis is a proof-of-concept** for a larger clinical-software project (hospital deployment: onset time + onset channel + propagation). Reproducibility/provenance matter beyond the defense.
- **Timeline:** work/experiments end ~27 Sep; report writing 28 Sep–11 Oct; **IELTS exam 9 Oct** (target 6.0); **submission 15 Oct**; defense Nov 2–3.

---

## 2. Locked headline numbers (verify via `python src/thesis_repro_lock.py`)
- Ensemble weight: `(recon, temporal, gamma) = (0.40, 0.35, 0.25)` (Decision #19).
- **Balanced (primary):** sensitivity **0.750** [0.642, 0.834], FP/day **39.77** [36.22, 43.57] — mag60/pen1.0, TP/FN/FP = 57/19/461.
- **High-sensitivity:** sensitivity **0.829** [0.729, 0.897], FP/day **71.25** — mag50/pen0.5, TP/FN/FP = 63/13/826.
- Window tier: macro AUROC **0.791**; component standalone AUROC recon 0.671 / temporal 0.647 / gamma 0.755.
- **FP-reduction filter (Decision #24): TESTED and REJECTED** — pipeline unchanged; FP/day is an accepted limitation.
- Baselines: Yildiz 2022 unsupervised CHB-MIT AUROC = **0.68** (not 0.76). The 0.765/40.6 SzCORE Transformer is **TUH**, never a CHB-MIT baseline.

`thesis_repro_lock.py` reproduces BOTH operating points **bit-exact** (per-subject + pooled) from committed components, no GPU, no cache. Verified before AND after the repo reorganization.

---

## 3. Current repo structure (github.com/Nhanvas/Thesis, branch `main`)
```
Code/
├── src/                      # ACTIVE code, flat. Run everything as `python src/<name>.py` FROM REPO ROOT.
│   ├── ensemble_recipe.py    #   SINGLE SOURCE: weight + build_ensemble
│   ├── cpd_pipeline_v14.py   #   SINGLE SOURCE: detection (PELT + magnitude filter)
│   ├── szcore_eval.py · evaluation_protocol.py · window_tier_newweight.py
│   ├── thesis_repro_lock.py  #   reproduces locked points bit-exact
│   ├── stat_validation.py · event_ablation.py · duration_stratified_sensitivity.py
│   ├── mag_pen_grid_sweep_v2.py · rebuild_ensemble_new_weight.py · weight_*.py  (provenance one-offs)
│   ├── eval_multiseed.py · window_event_gap.py · consolidate_outputs.py
│   ├── diagnose_fp_mechanism.py · edf_index.py
│   ├── attribution_gae_pernode.py · attribution_v3.py · attribution_tpfp.py · attribution_headmap.py
│   ├── visualize_channel_attribution.py · visualize_chb06_inversion.py
│   ├── fig5_eight_subjects.py · fig_A_three_scores.py · fig_B_raw_eeg_pelt.py   (figure scaffolds)
│   ├── dataprep/             #   upstream prep (preprocessing, graph_construction, feature_extraction, gamma, splits)
│   ├── fp_reduction_prior/   #   efix/efix_v2 (CUSUM/EMA prior-art) + fp_filter_step2*.py (#24 REJECTED record)
│   └── README.md             #   per-script map (active / provenance / etc.)
├── docs/                     # AUTHORITATIVE governance + reference
│   ├── RESULTS_OF_RECORD.md  #   ★ locked numbers §1–§15 (§15 = Decision #24 rejected)
│   ├── PLAN_AND_STATUS.md    #   ★ phase + decision log #1–#24 — read first
│   ├── PROVENANCE_MAP.md     #   upstream→locked chain + model provenance
│   ├── Proposed_solution_updated_v5.md   #   methodology master (Ch.2/3 source; DM1–DM6, DM6=impact 4C)
│   ├── PHASE_C_PLAN_v2.md    #   demo plan (confidence = continuous magnitude; split-screen)
│   └── PHASE_A_AUDIT_handoff.md · PHASE_B_AUDIT_handoff.md
├── notebooks/kaggle_gpu/     # thesis-cpd-final.ipynb (components+pernode; 5B/5D old-weight DEMOTED),
│                             #   thesis-threshold-final.ipynb (rejected baseline record)
├── demo/                     # Phase-C: wireframe_v2_grounded.html, ai_studio_brief.md, 5 mock JSON, PRD
├── archive/                  # superseded code: cpd_history/ rejected/ scaffolding/ probes_old/ attribution_superseded/
├── data/                     # models/best_model_joint_lambda01.pt (JOINT, verified), processed/components/,
│                             #   pernode/, splits/  (all small, COMMITTED); 34GB graphs gitignored
├── results/
│   ├── locked/ · phaseA_appendix/ · phaseB_newweight/ · attribution/ · attribution_v3/   (CITED)
│   ├── phaseB/fp_diagnosis/ · cross_view_consensus/ · fp_filter_*   (records; fp_filter_* = #24 rejection)
│   ├── cpd/evaluation/*_newweight.csv · multiseed/ · szcore_event_level_new_decision19_*   (CITED)
│   ├── history_superseded/   (old-weight caches, buggy grids, old lineage — DO NOT cite)
│   └── README.md             #   maps each result → ROR section
├── README.md · requirements.txt · requirements-kaggle.txt · Dockerfile · Makefile · entry.sh
```
Docker/Makefile/entry.sh are from the original PyTorch template (kept). Session/audit scripts are gitignored.

---

## 4. What's DONE (this consolidation phase)
1. **Full provenance audit + repo reorganization (B1–B7):** inventoried every file, built the provenance map, reorganized loose root files into `src/` (flat, import-safe) + `src/dataprep` + `src/fp_reduction_prior` + `archive/*`, quarantined old-weight artifacts to `results/history_superseded/`, integrated the two Kaggle notebooks, consolidated governance into `docs/`. Committed + pushed. Repo **self-reproduces** from a clean clone.
2. **Reproducibility proven twice:** locked headline reproduces bit-exact before AND after reorg (`thesis_repro_lock.py`).
3. **Model provenance verified:** the authoritative model is the JOINT model `data/models/best_model_joint_lambda01.pt` (has `x_decoder`); the 10 A-only checkpoints in `archive/scaffolding/` are superseded experiments; the joint-training notebook was NOT retained (architecture documented; artifact + components reproduce results).
4. **Decision #24 — FP-reduction filter TESTED and REJECTED.** Pre-registered CUSUM persistence post-filter. Discrete cliff at P=34 (0 seizures lost / 9.3% FP-day cut below it; 3 lost / 21.3% at it). No P clears the pre-registered ≥20%-FP/day-at-≤2-loss bar. Mechanism: short seizures lost first (chb06/chb16), fixed 60s CUSUM window dilutes brief ictal elevation. Pipeline UNCHANGED. Duration-adaptive window = future work. Landed in ROR §15.
5. **Rubric gap closed:** the one real gap (Criterion #4 / ABET PI 4C, impact decision matrix) closed via DM6 (Deployment Strategy) added to `Proposed_solution_updated_v5.md`.
6. **Phase-C demo framing done (not built):** confidence schema = continuous magnitude (not tiers); split-screen wireframe grounded on real Persyst layout; AI-Studio brief + 5 mock JSON; market research → Layer-3 AI attribution is the differentiator (feeds Significance / PI 4C).

---

## 5. What's NOT done yet (next phases — writing + demo build)
**Report writing (the ~80/100 rubric points; front-load Methods first, it's unblocked):**
- Methodology (bám `Proposed_solution_updated_v5.md` §III; named equations for rubric #3; DM6 for #4)
- Introduction / Related Work / Literature
- Results / Evaluation / Significance (PI 4C: impact + Layer-3 differentiator)
- Limitations (FP/day; chb06 detection-limited; attribution ≠ SOZ; #24 rejected as honest negative)
- Abstract, then Grammarly + AI/plagiarism check, then format to `Thesis_report_format`.

**Phase-C web demo (framed, not built):** offline JSON export from `cpd_pipeline_v14` + `edf_reader.py` + FastAPI backend + static frontend from `wireframe_v2_grounded.html`. **Post-hoc, test-subjects-only, read-only.** Feedback panel (D1/D2/D3) + patient metadata were CUT to future work — keep the demo minimal (3 layers, 8 subjects).

**Supporting:** publication-quality figures (pipeline diagram, CPD mechanism, connectivity, attribution head-maps); literature comparison table + complete the 4 pending DOIs; slides + defense script + Q&A (post-submission).

**Small consolidation remainders (optional; do at writing-phase start):**
- Update `PROJECT_INSTRUCTIONS.md` FILE USAGE MAP (still references old weight + root paths → should reflect flat `src/` + Decision #24).
- Create `docs/RUBRIC_TRACKING.md` (8-criteria checklist → chapter/file that covers each).
- Confirm `docs/PROVENANCE_MAP.md` has the #24-rejected line + model-provenance subsection.

---

## 6. Known caveats / not-fully-verified
- Only the **core detection→scoring path** was re-verified post-reorg (`thesis_repro_lock.py`). Other analysis scripts (`window_tier_newweight`, `event_ablation`, `attribution_*`) should run (same flat-`src/` import structure) but weren't individually re-run. Quick check: `python -c "import sys; sys.path.insert(0,'src'); import window_tier_newweight, event_ablation, attribution_v3, attribution_gae_pernode; print('imports OK')"`.
- **GPU (Kaggle) is not bit-reproducible.** Never re-train to "match" locked numbers; the released model + components are authoritative. LSTM training code was not retained (documented as a provenance gap).
- Upstream GAE/LSTM/gamma were not audited (cached components taken as given, but proven to reproduce the locked numbers).
- `results/phaseB/fp_filter_*` are the REJECTION record for #24 — never cite as a result or wire into the pipeline.

---

## 7. Reproduce / verify (commands, from repo root, CPU-only)
```bash
python -m venv .venv && source .venv/bin/activate   # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python src/thesis_repro_lock.py     # must print: LOCKED HEADLINE REPRODUCES (0.750/39.77 + 0.829/71.25)
```
Governance docs may live in `docs/` (in the git repo) and/or `F:\Study\Thesis\Agent\`. Summaries/EDF
files are outside the repo (a CHB-MIT dataset folder); pass the path when a script needs it.

---

## 8. Where to start next
The consolidation/"chốt" phase is CLOSED. The next move is **report writing, Methods first** (it is
unblocked and stable). Open a new conversation and say "bắt đầu viết Methodology"; read `docs/` for
full context. Writing takes priority over the demo when bandwidth is tight (IELTS 9 Oct + submission
15 Oct). Keep the demo minimal and treat it as source material for the report and defense.
