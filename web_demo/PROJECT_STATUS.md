# PROJECT STATUS — single source of truth for "where are we right now"
**Last updated:** 2026-09-28 (rev. F — web-demo entries only). **Replaces:** `MASTER_HANDOFF_v2.md`, `PLAN_AND_STATUS.md`,
`NEXT_TASKS_AND_PLAN.md` (all retired). **On any number conflict, `RESULTS_OF_RECORD_phaseB.md` wins
over this file.** On artifact identity, `PROVENANCE.md` wins. On paths, `REPO_MAP.md` wins. On any
statement that was inferred rather than measured, `VERIFIED_CORRECTIONS.md` wins over this file.

**Changes in rev. F (2026-09-28) — web-demo entries only (§1 last line, §7 items 1–2, §9).** The demo build
is complete and is in a test-and-lock phase. §7 item 2 is rewritten: build state, the eight subjects with
their full file sets, the three numbered divergences (the earlier "four steps" wording was wrong about
robust-z), pre-freeze timing figures, and one new methodological point for cô about the operating point.
Nothing about thesis numbers, attribution results or the report chapters was touched; those entries are
as of rev. E2 and are owned by this project.

**Changes in rev. E (2026-09-18).** The channel annotation is FINAL: a human, model-blind,
supervisor-approved annotation of every ictal channel replaces the machine-generated dominant-channel
draft. The attribution method is re-locked as `ATTRIBUTION_SPEC.md` v4 (Amendment A4), every
draft-label number is retired, and the label-scored rerun is in progress (§6, §7 item 4).

**Changes in rev. D.** The five report chapters and the front matter are written. The parameter count
and the processing-time figure below were both wrong in rev. C and are corrected. §7 item 1 is rewritten
because report writing is no longer the open task it describes. Four findings settled during the writing
phase are recorded in `docs/VERIFIED_CORRECTIONS.md` and summarised in §7a.

> **FIRST COMMAND IN ANY SESSION THAT TOUCHES THE GAE:**
> ```bash
> python src/verify_provenance.py      # ~20 s, must print "VERDICT: PASS"
> ```

---

## 0 · Deadlines (hard constraints)

| Date | Event |
|---|---|
| **09/10/2026** | IELTS exam |
| **15/10/2026** | Thesis report submission |
| **05–06/11/2026** | Thesis defense |

> ⚠️ The defense date in the Claude project instructions reads **02–03/11**. This file says 05–06/11.
> Unresolved — confirm with the department and correct whichever is wrong.

September is IELTS-dominant (near-zero research bandwidth). The working window for anything beyond
report / demo / attribution is closed.

---

## 1 · Phase timeline

```
Phase A (pre-rebuild)          → RETIRED. Numbers (0.750/0.829, weight 0.40/0.35/0.25) never
                                  reproduced (lost LSTM checkpoint + test-set-selected OP).
                                  Do not cite. Historical only, in docs/archive/RESULTS_OF_RECORD.md.
        ↓
Rebuild (§0 baseline)          → RETIRED as the reported result, superseded by rlg. Fixed a
                                  train/eval normalization bug in the LSTM branch, removed test-set
                                  tuning of weight/OP. Numbers: sens 0.632 @ 38.6 FP/day (balanced).
        ↓
Phase B (representation search) → S2 (learned graph) REJECTED — collapse. S3 (Deep-SVDD) REJECTED.
                                  S5 (multiband adjacency) REJECTED.
                                  E1/E2 (latent-Mahalanobis readout) — WIN.
        ↓
Tier-2 / Amendment A1          → LSTM temporal branch UNRECOVERABLE (corr 0.10–0.44 vs committed
                                  components, up to 218σ; training code lost). DROPPED.
                                  Replaced by latent-Mahalanobis on the SAME GAE.
                                  → PIPELINE = rlg. This is THE thesis pipeline.
        ↓
Phase C (optimization program)  → 7 pre-registered, VAL-gated levers across decision / representation /
   ★ CLOSED, evidence-based        ensemble / signal layers. NONE Pareto-improved rlg at the event
     negative ★                    headline. rlg confirmed as the ceiling.
        ↓
Phase D (capacity hypothesis)   → PRE-REGISTERED, NOT EXECUTED. Deliberate time-boxed decision.
   ★ Future Work, not run ★        See PHASE_D_HANDOFF.md.
        ↓
Attribution study               → Machinery verified label-free (FINAL). Final blind annotation
   ★ DONE — pre-registered ★       scored 2026-09-19: L1 weak pass (0.569), L2 FAIL (below the
     negative at L2/L3            anatomical prior), L3 FAIL. See §6.
        ↓
★ CURRENT PHASE ★
Report writing + Web Demo (SzScan — built, in test-and-lock) + Defense prep
```

## 2 · The pipeline of record — rlg

```
per-window graphs (wPLI+AEC, top-k20)
 → Joint GAE (seed 42, canonical; encoder GCNConv 23→64→16, 3,285 trainable params)
 → 3 readouts: zrecon (recon-MSE), zlatent (latent-Mahalanobis, LedoitWolf on graph-mean 16-d Z,
               per-subject interictal fit, label-free), zgamma (gamma-band AEC anomaly)
 → per-branch robust-z (median/MAD) → EQUAL-weight ensemble (1/3 each)
 → PELT CPD (src/cpd_pipeline_v14.py) → label-free per-subject FP-budget OP (PREREG_04)
 → SzCORE event scoring (timescoring)
```

**Canonical checkpoint:** `data/models_retrain/gae_joint_seed42.pt`
sha256 `dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108` · 15258 B ·
bias fingerprint **1.1597** · chb13 recon AUROC **0.8319** ·
verified **corr = 1.0000000 on 16/16** committed TEST `zrecon` arrays (2026-09-01).

**Never identify a checkpoint by filename.** The pre-rebuild §0 model
(`archive/pre_rebuild_s0/best_model_joint_lambda01.pt`, bias 0.8676, chb13 0.8360) reproduces the same
components at corr 0.987–0.999 — close enough to pass a careless check and be wrong. It did exactly
that on 2026-09-01. Run `verify_provenance.py`.

**Do NOT use:** `gae_multirel_seed42.pt` (Phase-C C4-full, killed) · the five LSTM files in
`src/retrain/` (dropped branch, kept as provenance only).

## 3 · The locked numbers (full detail + CIs in `RESULTS_OF_RECORD_phaseB.md`)

| Metric | Value |
|---|---|
| Window-tier macro AUROC (TEST) | **0.805** |
| **VAL-derived balanced headline** — sens/prec/F1/FP-day | 0.618 / 0.129 / **0.213** / **27.4** |
| Pooled TEST Pareto peak — sens/prec/F1/FP-day | 0.474 / 0.387 / **0.426** / **4.9** |
| Phase-C event headline | F1 **0.361** @ 3.6 FP/day |
| GAE seed-stability (4 seeds), window macro AUROC (VAL) | 0.929 ± 0.002 |
| GAE seed-stability (4 seeds), event F1 @ 3.6 FP/day | 0.51 ± 0.034 (**the noise floor**) |
| chb13 recon AUROC, re-measured (RoR §7 errata) | 0.8319 / 0.8349 / 0.8326 / 0.8339 → 0.833 ± 0.001 |

⚠️ **Never cite 0.750 / 0.829 / 0.791 / 39.77 / 71.25** (pre-rebuild, never reproduced) or
0.632 / 0.776 (historical §0) as the thesis result.

## 4 · Phase C — one line each (full detail in `PHASE_C_FULL_AUDIT.md`)

| # | Lever | Verdict |
|---|---|---|
| 1 | C4-lite (post-hoc directed-TE branch) | Net-wash at headline; mechanism finding kept (chb06/chb22 rescue) |
| 2 | C1 (median pre-CPD smoother) | Rejected — harmed sensitivity |
| 3 | slope-gate / C-onset | Rejected — seed42-only false positive, caught by multi-seed |
| 4 | C4-full (multi-relational GAE) | NO-GO — 3-branch 0.909, 2-branch 0.926, both ≤ rlg 0.928 |
| 5 | Ensemble reweight / drop-recon | Dead on record — lg = 0.579 event + PREREG_03 flat weight surface |
| 6 | Artifact/transient gate before CPD | Rejected — 1-subject/1-budget win, headline unchanged |
| 7 | Multi-band AEC | NOT tried — deprioritized on measured priors, disclosed as Future Work |

**Unifying mechanism:** window/representation gains die at the CPD-transfer step (PELT keys on
sustained level shifts, not rank separation); per-subject rescue effects net-wash; the
representation-limited subjects (chb06, chb14) sit in the locked TEST set.

## 5 · Repository state (cleanup completed 2026-09-01/02)

- **Provenance hardened.** `docs/PROVENANCE.md` (machine-generated) + `src/verify_provenance.py`
  (session gate). §0 artifacts quarantined in `archive/pre_rebuild_s0/` with a README explaining the
  0.99-correlation trap. The stale §0 constants in `src/retrain/gae_joint.py` were corrected.
- **`src/` consolidated.** 47 top-level scripts → 5 canonical modules
  (`cpd_pipeline_v14`, `ensemble_recipe`, `szcore_eval`, `verify_provenance`, `attribution_pipeline`)
  + `figures/`, `labeling/`, and the existing `dataprep/`, `retrain/`, `phaseB/`, `phaseC/`.
  Superseded scripts → `archive/src_superseded/`.
- **Duplicates removed** after byte-level verification: duplicate `topo_features/`, duplicate label
  PNG/zip under `attribution_v6/labels/`, unpacked torch-archive directories under
  `models_retrain/_archive/` (the mechanism behind the checkpoint confusion).
- **`REPO_MAP.md` rewritten** with per-file purpose and a **Traps** section (§7) listing the known
  confusion sources.
- ⚠️ **Cleanup regression, found and fixed 2026-09-03.** The consolidation archived two modules that
  were still imported: `evaluation_protocol.py` (needed by `src/szcore_eval.py`) and
  `stat_validation.py` (needed by `retrain/final_eval.py` → `retrain/fp_budget_operating_point.py`).
  Neither SzCORE event scoring nor the PREREG_04 operating point could be re-run. **Committed results
  were never affected** — they predate the cleanup — but reproducibility was broken for about a day.
  Both restored to `src/`; the canonical module count is now **7**, not 5. A third file, `edf_index.py`,
  was deleted in the same pass and is genuinely not needed (see §7 item 2). Tag: `repo-deps-fixed`.
  A standing import-scan is recorded in `REPO_MAP.md` §7.7 — run it after any file move.

## 6 · Attribution — FINAL (label-free half 2026-09-02; label-scored half 2026-09-19)

Full detail: **`ATTRIBUTION_SPEC.md` v4** (method locked by Amendment A4, 2026-09-18). Summary in
`RESULTS_OF_RECORD_phaseB.md` §10. Report material: `ATTRIBUTION_REPORT_PACK.md` v2.
Framing: **XAI for the GAE reconstruction branch — not localization, not SOZ; concordance, not accuracy.**

**Done, final, label-free (unchanged):**
- Machinery verified by synthetic injection with exact ground truth. Gates G-S1/G-S2/G-S3 and G-S4′
  all PASS; permutation-null mean stayed in **0.4990–0.5013 across all 50 cells**; a +25 % anomaly is
  detected at AUROC ≈ 0.70. No p-value on G-S4′ (8.9e-11 is untraced).
- GAE-seed robustness: channel-ranking Spearman **0.970 ± 0.026** across seeds {42,1,2,3}.
- No global channel bias (across-subject ranking correlation −0.012).
- Spread (normalised entropy) is U-shaped in |S|: a methodological negative, synthetic only.

**Ground truth — FINAL (2026-09-18).** Annotated by the author from the raw 18-channel EEG, **blind to
every model output**, listing every channel with clear ictal discharge; protocol and result approved by
the supervisor. 62 focal seizures (|S| 1–10, mean 4.55) + 14 generalized (chb06 ×10, chb03 ×3, chb13 ×1).
Within-subject Jaccard 0.5144. Anatomical prior (label-only) macro-AUROC 0.7387.

**Retired — never quote:** everything scored against the machine-generated draft (0.6497, 0.3095,
0.7758, 0.8879, −0.1261, 0.2672, +0.3578, p = 0.984). Restore point `git tag attribution-v6-draft`.

**Result (spec §9.3, RoR §10.3, tag `attribution-v7-results`):** L1 macro-AUROC **0.5694**
[0.5097, 0.6321], p = 0.001 — PASS, weak; **0.5011 without chb15**. L2 Δ vs prior **−0.1694**
[−0.2553, −0.0804] — FAIL, significantly below a fixed anatomical rule. L3 T = +0.0064, p_holm 0.68 —
FAIL. D7 control higher. Stable across seeds (0.572–0.577) and aggregation (0.585). Per subject: chb15
0.713 and chb13 0.676 agree; chb16 0.260 and chb18 0.365 are inverted.
**Reading:** a pre-registered negative. The machinery is sound (synthetic); the reconstruction anomaly
simply does not sit where a reader sees the discharge. The demo panel stays as a neutral anomaly view
(title unchanged, UI frozen); the report must not present it as a guide to ictal channels.

**Figures affected:** Figure 3.9 (rank heat map) is regenerated with the final labels overlaid; Figure
3.10 becomes synthetic-only. Figure 3.8 and Table 3.6 are unchanged. Tables 3.7 and 3.8 are refilled.

## 7 · What's left (priority order)

1. **Report writing — the five chapters and the front matter are WRITTEN (2026-09-16).** All five were
   rewritten against `EXHIBIT_SET_FINAL.md` and `CAPTIONS.md` rev 6, in the house style of
   `PROSE_STYLE_SPEC.md`. The exhibit set is 21 figures plus Figure 3.11 pending the application, and
   29 tables across 4 / 8 / 9 / 2 / 6. Every cross-chapter number was checked by command.

   What is left on the report:

   - **Typesetting.** Word assembly, the reference list and the citation numbers. **No one has checked
     `[1]` to `[68]` against a bibliography**; the numbers were carried forward from the earlier drafts.
   - **Three cross-chapter pairs that must be edited together if either side changes.** The
     directed-connectivity values, 0.710 / 0.674 / 0.888 and +0.137 / +0.052 / −0.059 and 0.928 to
     0.909, live only in the prose of Chapter 3 §3.5.2 and Chapter 4 §4.3 because their table was cut.
     The processing-time sentence appears in Chapter 2 §2.6.2, Chapter 4 §4.7 and `tables_ch4.md`. The
     ten design-requirement rows are word-identical in Table 1.2 and Table 3.9.
   - **Waiting on the application.** Figure 3.11, §3.7 in full, and four rows of Table 3.9. The application
     is now built (§7 item 2), but screenshots and final timing figures stay pending until the author
     declares the demo tested and locked (`web_demo/BUILD_PROGRESS.md` §14). Anything the committee sees
     about the demo is described by what the system does and outputs — never by build-step, phase or
     prompt labels.
   - **Goal 1 is quoted verbatim from the registration form**, "spatial-temporal features", in
     Chapter 1 §1.5, Table 3.9 and Chapter 5. Never reword it; qualify it in a sentence beside it, as
     §1.5 does.

   Style and checklist docs: `THESIS_REPORT_WRITING_GUIDE.md`, `PROSE_STYLE_SPEC.md`,
   `RUBRIC_TRACKING.md`, `Report_format.md`. ⚠️ `RUBRIC_TRACKING.md` predates the attribution results
   and carries the retired 16.9 ms figure at its line 121.
2. **Web demo (SzScan)** — **BUILD COMPLETE (all nine build steps closed); now in a test-and-lock phase
   before freeze + tag.** Authority lives in `web_demo/`: `SZSCAN_SPEC_v5.md` (behaviour/logic/data
   boundary) > `SZSCAN_DESIGN_v2.md` (visual tokens, measured from the locked PNGs) >
   `DEMO_BUILD_HANDOFF.md` (stack/build order), with `UI/` (29 author-frozen PNGs) winning on anything
   visible. Running state and the open list: `web_demo/BUILD_PROGRESS.md` §14 and §16. The four old
   `WEB_DEMO_*` docs are in `docs/archive/demo_v4/` — **do not cite them**; the v4 spec still describes
   an LSTM branch and a cache-replay architecture, both wrong. Tag: `demo-spec-v5`.

   **State (2026-09-28).**

   - All eight held-out TEST subjects are processed through the real Create-New → Process flow with their
     **full real file sets**: chb03 38, chb06 18, chb13 33, chb14 26, chb15 40, chb16 19, chb17 21,
     chb18 36 files. A file-count audit on 2026-09-27 found chb13 holding only 2 of its 33 files; it was
     deleted and re-uploaded in full. The subject allowlist is enforced (anything else is rejected).
   - Live-upload subject for the defense: **chb16**, chosen on measured end-to-end time (~5.7 min, the
     fastest of the eight), not on file count; pre-built copies of all eight are the insurance.
   - The integrity guards (§8) are enforced by an automated test that stays green after every change.
   - One deliberate deviation from the locked mockups, decided by the author: the EEG filter control is a
     single "Preprocessed (0.5-60 Hz + 60 Hz notch)" toggle instead of three buttons, because the
     pipeline has only one real filtered signal (`SZSCAN_SPEC_v5.md` §6.4, C24).

   **Settled.**

   - **The attribution wording is DECIDED.** The panel is titled
     `Channel-level reconstruction anomaly — Event N`. The mockup's "Channel contribute to …" is
     retired — it implies causal localization. No attribution evaluation metric appears in the UI. The
     panel's score is the 95th percentile of |robust-z| per channel over an event's windows, against a
     per-subject baseline — the same formula as `src/attribution_pipeline.py`, differing only in baseline
     scope (whole recording, not interictal-only).
   - **The architecture is settled by measurement.** The committed `ens_seed42_*` arrays are
     segment-ordered with no window→second index, and `szcore_eval.build_timeline_masked()` rebuilds a
     timeline *from the ground-truth annotations*, bootstrap-filling buffer and artifact-rejected gaps
     (`src/szcore_eval.py:90, 98–109, 111–113, 120–123`). Positional information was destroyed at
     preprocessing, so **cache-replay of thesis scores is impossible**. The demo recomputes label-free
     on the continuous recording, CPU only. Three hard guards enforce the label-free claim
     (`SZSCAN_SPEC_v5.md` §1.2).
   - **Timing — two different quantities, never interchangeable, both still pre-freeze.** (a) Algorithm-only
     cost, files processed one after another: **10.83 s per hour of EEG** (median; range 10.69–12.47;
     subject chb16, 19 h, five runs). By stage, in s/h: adjacency + band powers 4.9, change-point
     detection incl. operating-point calibration 2.6, gamma-band AEC 1.7, ingest + filter 1.2, subject-wide
     fits 0.4, GAE scoring 0.2 (`web_demo/BUILD_PROGRESS.md` §16.5). (b) What a user waits for through the
     real upload flow: 10.9–27.3 s/h for the first processing stage across subjects, plus change-point
     detection at 3.2–10.9 s/h. The earlier single-point 9.76 s/h (one four-hour recording) and the
     16.9 ms/window ⇒ ~15 s/h component benchmark are superseded and must not be quoted. Run-to-run
     variation on this machine is real (about fivefold on individual stages). **Final figures are
     re-measured on the frozen build.**
   - **Approved methodological divergences — three numbered items** (`SZSCAN_SPEC_v5.md` §1.6,
     restructured 2026-09-25 to match this report's own enumeration). A new patient has no labels, so:
     (1) z-score statistics, the LedoitWolf covariance for `zlatent` and the attribution baseline are fit
     on **all windows** of the subject instead of the interictal array, and artifact rejection is dropped
     to preserve time alignment; (2) the 4 h post-seizure buffer cannot be excluded, so post-ictal EEG
     goes straight into change-point detection; (3) the change-point penalty variance and magnitude
     threshold are estimated on the whole recording. **Per-branch robust-z is NOT a divergence** —
     `retrain_io.robust_z` already fits median/MAD on the concatenated interictal + ictal scores (checked
     2026-09-28 against `src/retrain/retrain_io.py`); the earlier "four steps" wording listed it wrongly.
     **Scope decided 2026-09-12: per subject, not per file** (the thesis normalises per subject; a
     per-file fit loses comparability between the files of one patient). Justified by measured ictal
     prevalence **0.23 %** (chb06: 45/19871); the LedoitWolf change was measured harmless
     (Spearman ≥ 0.9999, |ΔAUROC| ≤ 0.0085 on chb06/chb13). Items 2 and 3 have not been measured
     against such a criterion. **Consequence: demo numbers will differ from thesis numbers and must not be
     made to match.**

   **To decide / report to cô (methodological, not implementation).**

   - ⚠️ **Divergences (1)–(3) above** were already flagged for cô.
   - ⚠️ **NEW — the demo's operating point.** It uses the thesis's own target (the "balanced" budget of
     40 per day, read from `fp_budget_operating_point.py`) and the thesis's own penalty grid
     (`final_eval.DEFAULT_PENS`), but what it calibrates is the **total detected-event rate per day over
     the whole recording**, choosing the penalty whose rate is closest to the target. The thesis matches
     *false-alarm* rate on interictal data; a new patient has no labels to separate true from false, so
     total event rate is the label-free proxy. Confirmed by reading `pipeline_demo.calibrate_operating_
     point()` on 2026-09-28. Open question: does this sit under divergence (3) or is it a fourth item?
     Chosen penalties so far: chb16 1.0, chb17 2.0, chb14 5.0, chb13 2.0, chb18 2.0, chb03 2.0,
     chb15 5.0, chb06 2.0.

   **Open on the demo** (details: `web_demo/BUILD_PROGRESS.md` §14): SPEC edits recording the operating
   point exactly; an Analysis-screen check on chb06's long recordings (up to ~4 h); a network-off full-flow
   run as the evidence that no data leaves the machine; the extent of post-ictal flagging (O4b, human
   visual review only); freeze + tag, then final per-stage timing and the one-pass Tier 2 run per
   `web_demo/STEP8_9_PREDEFENSE_CHECKLIST.md`; screenshots for the report after lock.
3. **Defense prep** — Q&A anchors: why Phase D wasn't run (`PHASE_D_HANDOFF.md` §3); why 0.361/0.426 F1
   is competitive (SzCORE Challenge 2025 realistic band 0.32–0.43); how to frame the 7-lever negative
   program as rigor (`RUBRIC_TRACKING.md` §6); and the attribution defense questions prepared in
   `ATTRIBUTION_REPORT_PACK.md` v2 PART 4 §4.3 (self-annotation, generalized exclusion, anatomical prior).
4. **Attribution rerun on the final annotation — results FINAL (2026-09-19).** Remaining: regenerate
   Figures 3.9 and 3.10; rewrite the attribution material of the report per
   `ATTRIBUTION_REPORT_PACK.md` v2 PART 1 (Ch.1–5, front matter, Tables 3.7–3.8, captions, Table 3.9
   rows); then update the project instructions §7 once. Must finish before report assembly.

## 7a · Findings settled during the writing phase

Full detail with evidence in `docs/VERIFIED_CORRECTIONS.md`. The four that reverse a statement still
carried elsewhere:

| Finding | What it replaces |
|---|---|
| **CAR exists.** `apply_car` at `src/dataprep/graph_construction.py:84`, called inside the adjacency builders. It is a graph-construction step, not a preprocessing step, so the stored signals are not CAR-referenced | An empty grep over `preprocessing.py` and `build_graphs.py` was read as proof CAR did not exist, and two chapter paragraphs were cut on that basis |
| **Post-seizure exclusion precedes artifact rejection.** `compute_subject_stats` skips ictal and buffered windows before accumulating the mean and standard deviation, and the artifact threshold is five times that standard deviation | A table numbered from the file's own docstring, which calls artifact rejection "Step 4" |
| **`STATS_SUBSAMPLE = 10`.** The background statistics come from a one-in-ten subsample | First asserted from a planning document, then wrongly withdrawn on seeing Welford's algorithm named |
| **The weight surface is not flat.** Optimum 0.9405 against 0.9283 at equal weights, gap 0.0122 on a cross-model spread of 0.0025, equal weighting outside the 29 points within tolerance | "Flat weight surface", which has resurfaced five times. Equal weights are still used; justify them as inherited, never as measured |

Do not credit CAR with resistance to volume conduction. That is wPLI's own property by construction;
AEC is the branch the reference serves.

## 8 · Integrity rules (binding for report/demo work)

- Run `src/verify_provenance.py` before trusting any number or loading any checkpoint.
- Never touch or re-derive TEST-subject numbers. They are locked.
- Any number in the report must trace to `RESULTS_OF_RECORD_phaseB.md` — re-read before quoting, never
  rely on memory across a long chat.
- Attribution and demo must use `gae_joint_seed42.pt`, never the multi-relational checkpoint and never
  anything in `archive/pre_rebuild_s0/`.
- Archive, don't delete. Never reconstruct a source-of-truth file from memory or from chat transcripts.
- **After any file move, run the import scan in `REPO_MAP.md` §7.7 before committing.** Archiving a
  still-imported module breaks reproducibility silently — it happened twice in one cleanup pass.
- **The demo must never touch ground-truth labels** (`SZSCAN_SPEC_v5.md` §1.2). Violating those three
  guards turns a label-free claim into a false one.

## 9 · Where to start in a new chat

1. `python src/verify_provenance.py` — must print PASS.
2. This file.
3. `RESULTS_OF_RECORD_phaseB.md` (numbers), `PROVENANCE.md` (artifact identity), and
   `VERIFIED_CORRECTIONS.md` (statements that were inferred and turned out wrong).
4. Then whichever matches the task: `THESIS_REPORT_WRITING_GUIDE.md` + `RUBRIC_TRACKING.md` (report),
   `ATTRIBUTION_SPEC.md` (attribution), `web_demo/SZSCAN_SPEC_v5.md` (demo — §1 in full before any
   backend reasoning; current build state in `web_demo/BUILD_PROGRESS.md` §14 and §16), `PHASE_C_FULL_AUDIT.md`
   (defending an optimization decision), `PHASE_D_HANDOFF.md` (future work).
   `REPO_MAP.md` for any path lookup — read its §7 Traps before touching unfamiliar files.
