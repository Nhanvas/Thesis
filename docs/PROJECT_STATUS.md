# PROJECT STATUS — single source of truth for "where are we right now"
**Last updated:** 2026-09-02 (rev. B). **Replaces:** `MASTER_HANDOFF_v2.md`, `PLAN_AND_STATUS.md`,
`NEXT_TASKS_AND_PLAN.md` (all retired). **On any number conflict, `RESULTS_OF_RECORD_phaseB.md` wins
over this file.** On artifact identity, `PROVENANCE.md` wins. On paths, `REPO_MAP.md` wins.

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
Attribution study               → EXECUTED 2026-09-01/02. Machinery verified label-free; results
   ★ DONE (provisional) ★          against labels are PROVISIONAL and blocked by a LABEL limitation,
                                  not by the method. See §6.
        ↓
★ CURRENT PHASE ★
Report writing + Web Demo (SzScan) + Defense prep
```

## 2 · The pipeline of record — rlg

```
per-window graphs (wPLI+AEC, top-k20)
 → Joint GAE (seed 42, canonical; encoder GCNConv 23→64→16, ~8.7k params)
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
- **`REPO_MAP.md` rewritten** with per-file purpose and a **Traps** section (§7) listing the five
  known confusion sources.

## 6 · Attribution — EXECUTED, results PROVISIONAL

Full detail: **`ATTRIBUTION_SPEC.md` v3**. Summary in `RESULTS_OF_RECORD_phaseB.md` §10.
Framing: **XAI for the GAE reconstruction branch — not localization, not SOZ.**

**Done, and not provisional (label-free):**
- Machinery verified by synthetic injection with exact ground truth. Gates G-S1/G-S2/G-S3 and G-S4′
  all PASS; permutation-null mean stayed in **0.4990–0.5013 across all 50 cells**; a +25 % anomaly is
  detected at AUROC ≈ 0.70.
- GAE-seed robustness: channel-ranking Spearman **0.970 ± 0.026** across seeds {42,1,2,3}.
- No global channel bias (across-subject ranking correlation −0.012). Three subjects
  (chb13/chb15/chb16) show top-1 concentration above a random null.

**Done, and provisional (label-scored) — but narrower than the spec intended:**
- ⚠️ **Label-schema caveat.** The label file records the reader's **dominant channel(s), 1–2 per
  seizure** (40 DIFFUSE / 25 one-channel / 11 two-channel; mean |S| = 1.31), **not** the full ictal-set
  schema of `ATTRIBUTION_SPEC.md` §3.2. So the scored question is "does the GAE rank the reader's
  leading channel first?" — the framing the spec had retired. Numbers are correct; the question is
  narrower. State this wherever they appear.
- macro-AUROC **0.6497 [0.5663, 0.7390]**, macro-AUPRC 0.3095 (4.2× the 0.073 prevalence),
  p_perm = 0.001, over the 36 labelled seizures. Stable across seeds and aggregations.

**Two honest negatives that go in the report:**
1. **The D7 control is uninformative** — within-subject label Jaccard is **0.8879**. A 1–2 channel
   dominant label from a patient's fixed focus is almost forced to be constant, so the
   subject-constant control wins by noise-averaging alone. With these labels, per-seizure attribution
   and a subject-level channel prior **cannot be distinguished**, and the §3.2 question is not tested.
   This is a limitation of the LABELS, not a finding about the method.
2. **The spread metric does not work** — normalised entropy is U-shaped in |S| (synthetic) and points
   the wrong way on real labels (focal 0.9693 > generalized 0.9594, p = 0.984). A methodological
   negative.

**Report figures — DONE, `figures/attribution/`** (generated by `src/figures/attribution_figures.py`,
which reads the committed CSVs and recomputes nothing):
`attribution_fig1_synthetic.png` · `fig2_seed_robustness.png` · `fig3_rank_heatmap.png` (all three
LABEL-FREE and final) · `fig4_persubject_forest.png` (PROVISIONAL) · `attribution_top3_channels.csv`.

**Blocked on the supervisor** (four evidence-backed requests in `ATTRIBUTION_SPEC.md` §9.5): §3.2-
conformant labels listing every ictal channel rather than 1–2 lead channels (**primary**); within-patient
variation (target Jaccard < 0.6); channel sets for chb06/chb13 or confirmation they are truly
generalized; acknowledgement that chb15 supplies 20 of 36 annotated seizures.

**Not blocking the report.** The label-free half is a complete, defensible result on its own, and the
label-scored half is reportable as PROVISIONAL with the limitation stated. If the freeze arrives, rerun
`python src/attribution_pipeline.py eval` and replace §9.3 of the spec — nothing else changes.

## 7 · What's left (priority order)

1. **Report writing** — `docs/demo/THESIS_REPORT_WRITING_GUIDE.md` (structure/style),
   `RUBRIC_TRACKING.md` (8-criterion checklist + which number goes where), `Report_format.md`.
   ⚠️ `RUBRIC_TRACKING.md` predates the attribution results — check whether the attribution row needs
   updating before using it as the checklist.
2. **Web demo (SzScan)** — ⚠️ `WEB_DEMO_SPEC_v4.md` predates the attribution results and needs one
   wording change (channel view → "channels with ictal-like reconstruction anomaly", no per-seizure
   localization implied). Not yet made; it is the demo authority so the edit needs an explicit
   decision. `WEB_DEMO_SPEC_v4.md` wins on any conflict; `WEB_DEMO_DESIGN_SYSTEM.md` for
   design. Not yet built. Attribution is now done, so the demo is unblocked.
   Given §6, the channel view must be labelled **"channels with ictal-like reconstruction anomaly"** and
   must not imply per-seizure localization.
3. **Defense prep** — Q&A anchors: why Phase D wasn't run (`PHASE_D_HANDOFF.md` §3); why 0.361/0.426 F1
   is competitive (SzCORE Challenge 2025 realistic band 0.32–0.43); how to frame the 7-lever negative
   program as rigor (`RUBRIC_TRACKING.md` §6); and now, how the attribution chapter reports an
   uninformative control honestly rather than dressing it as a result.
4. **If labels are frozen** — rerun `attribution_pipeline.py eval`, update spec §9.3 and RoR §10.

## 8 · Integrity rules (binding for report/demo work)

- Run `src/verify_provenance.py` before trusting any number or loading any checkpoint.
- Never touch or re-derive TEST-subject numbers. They are locked.
- Any number in the report must trace to `RESULTS_OF_RECORD_phaseB.md` — re-read before quoting, never
  rely on memory across a long chat.
- Attribution and demo must use `gae_joint_seed42.pt`, never the multi-relational checkpoint and never
  anything in `archive/pre_rebuild_s0/`.
- Archive, don't delete. Never reconstruct a source-of-truth file from memory or from chat transcripts.

## 9 · Where to start in a new chat

1. `python src/verify_provenance.py` — must print PASS.
2. This file.
3. `RESULTS_OF_RECORD_phaseB.md` (numbers) and `PROVENANCE.md` (artifact identity).
4. Then whichever matches the task: `THESIS_REPORT_WRITING_GUIDE.md` + `RUBRIC_TRACKING.md` (report),
   `ATTRIBUTION_SPEC.md` (attribution), `WEB_DEMO_SPEC_v4.md` (demo), `PHASE_C_FULL_AUDIT.md`
   (defending an optimization decision), `PHASE_D_HANDOFF.md` (future work).
   `REPO_MAP.md` for any path lookup — read its §7 Traps before touching unfamiliar files.
