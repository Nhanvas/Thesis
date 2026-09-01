# PROJECT STATUS — single source of truth for "where are we right now"
**Last updated:** 2026-08-31. **Replaces:** `MASTER_HANDOFF_v2.md`, `PLAN_AND_STATUS.md`,
`NEXT_TASKS_AND_PLAN.md` (all retired — their content is superseded by this file + the phase-specific
handoffs below). **On any number conflict, `RESULTS_OF_RECORD_phaseB.md` §1–§9 wins over this file.**

---

## 0 · Deadlines (hard constraints — everything is planned around these)

| Date | Event |
|---|---|
| **09/10/2026** | IELTS exam |
| **15/10/2026** | Thesis report submission |
| **05–06/11/2026** | Thesis defense |

September is IELTS-dominant (near-zero research bandwidth expected). The real working window for
anything beyond report/demo/attribution is effectively closed as of this file's date.

---

## 1 · Where we are: phase timeline

```
Phase A (pre-rebuild)          → RETIRED. Numbers (0.750/0.829, weight 0.40/0.35/0.25) never
                                  reproduced (lost LSTM checkpoint + test-set-selected OP).
                                  Do not cite. Historical only, in old RESULTS_OF_RECORD.md.
        ↓
Rebuild (§0 baseline)          → RETIRED as the reported result, superseded by rlg below. Fixed a
                                  train/eval normalization bug in the LSTM branch, removed test-set
                                  tuning of weight/OP. Numbers: sens 0.632 @ 38.6 FP/day (balanced).
        ↓
Phase B (representation search) → S2 (learned graph) REJECTED — collapse. S3 (Deep-SVDD compactness)
                                  REJECTED — no signal to learn. S5 (multiband adjacency) REJECTED.
                                  E1/E2 (latent-Mahalanobis readout) — WIN. See PHASE_C_FULL_AUDIT.md §1.
        ↓
Tier-2 / Amendment A1          → LSTM temporal branch found UNRECOVERABLE (corr 0.10–0.44 vs committed
                                  components, up to 218σ outliers — training code lost). DROPPED.
                                  Replaced by latent-Mahalanobis readout on the SAME GAE.
                                  → PIPELINE = rlg (recon-MSE + latent-Mahalanobis + gamma-AEC,
                                  equal 1/3 weight, GAE canonical seed 42). This is THE thesis pipeline.
        ↓
Phase C (optimization program)  → 7 independently pre-registered, VAL-gated levers across decision /
   ★ CLOSED, evidence-based        representation / ensemble / signal layers. NONE Pareto-improved rlg
     negative ★                    at the event headline. rlg confirmed as the performance ceiling.
                                  Full audit: PHASE_C_FULL_AUDIT.md. Closeout: PHASE_C_CLOSEOUT_provenance.md.
        ↓
Phase D (capacity hypothesis)   → PRE-REGISTERED, NOT EXECUTED. Deliberate time-boxed decision (not an
   ★ Future Work, not run ★        oversight) — see PHASE_D_HANDOFF.md. rlg stands as final.
        ↓
★ CURRENT PHASE ★
Report + Attribution + Web Demo (SzScan) + Defense prep
```

## 2 · The pipeline of record — rlg (do not confuse with anything else)

```
per-window graphs (wPLI+AEC, top-k20)
 → Joint GAE (seed 42, canonical; encoder GCNConv 23→64→16, ~8.7k params)
 → 3 readouts: zrecon (recon-MSE), zlatent (latent-Mahalanobis, LedoitWolf on graph-mean 16-d Z,
               per-subject interictal fit, label-free), zgamma (gamma-band AEC anomaly)
 → per-branch robust-z (median/MAD) → EQUAL-weight ensemble (1/3 each)
 → PELT CPD (cpd_pipeline_v14.py) → label-free per-subject FP-budget operating point (PREREG_04)
 → SzCORE event-based scoring (timescoring library)
```

**Checkpoint:** `data/models_retrain/gae_joint_seed42.pt` (single-relation GAE — this is the ONE to use
for anything downstream, including attribution). **Do NOT confuse with** `gae_multirel_seed42.pt`
(the Phase-C C4-full multi-relational variant — tested, KILLED, not part of the thesis pipeline).

**LSTM temporal branch is DROPPED** (Amendment A1) — kept in the repo (`lstm_temporal.py`,
`train_lstm_temporal_v3.py`) only as historical/methodological documentation of why it was replaced.

## 3 · The locked numbers (see `RESULTS_OF_RECORD_phaseB.md` §1–§9 for full detail + CIs)

| Metric | Value |
|---|---|
| Window-tier macro AUROC (TEST) | **0.805** |
| **VAL-derived balanced headline** — sens/prec/F1/FP-day | 0.618 / 0.129 / **0.213** / **27.4** |
| Pooled TEST Pareto peak — sens/prec/F1/FP-day | 0.474 / 0.387 / **0.426** / **4.9** |
| GAE seed-stability (4 seeds), window macro AUROC | 0.929 ± 0.002 |
| GAE seed-stability (4 seeds), event F1 @ 3.6 FP/day | 0.51 ± 0.034 (= the noise floor) |

⚠️ **Never cite 0.750/0.829 (pre-rebuild) or 0.632/0.776 (historical §0) as the thesis result** — they
are retired/historical comparators only. See `RUBRIC_TRACKING.md` §5 for the full reporting-frame table
and which number goes in the Abstract.

## 4 · Phase C — what was tried, in one line each (full detail in PHASE_C_FULL_AUDIT.md)

| # | Lever | Verdict |
|---|---|---|
| 1 | C4-lite (post-hoc directed-TE branch) | Net-wash at headline; mechanism finding kept (chb06/chb22 rescue, individually) |
| 2 | C1 (median pre-CPD smoother) | Rejected — harmed sensitivity |
| 3 | slope-gate / C-onset | Rejected — seed42-only false positive, caught by multi-seed |
| 4 | C4-full (multi-relational GAE, joint TE+symmetric) | NO-GO — 3-branch 0.909, 2-branch 0.926, both < rlg 0.928 (tie within seed-SD) |
| 5 | Ensemble reweight / drop-recon | Dead on record — already measured worse pre-Phase-C (lg=0.579 event) + PREREG_03 flat weight surface |
| 6 | Artifact/transient gate before CPD | Rejected — 1-subject/1-budget win, headline (3.6 FP/day) unchanged |
| 7 | Multi-band AEC | NOT tried — deprioritized on measured priors (flat weight surface + representation-change net-wash), disclosed as Future Work |

**Unifying mechanism:** window/representation gains repeatedly die at the CPD-transfer step (PELT keys
on sustained level shifts, not rank separation); per-subject rescue effects net-wash (each hard subject
fails/benefits via a different mechanism); representation-limited subjects (chb06, chb14) sit in the
locked TEST set and cannot be fixed without label leakage.

## 5 · What's left to do (active work, in priority order)

1. **Report writing** — see `THESIS_REPORT_WRITING_GUIDE.md` for structure/style, `RUBRIC_TRACKING.md`
   for the 8-criterion checklist and exact numbers to cite, `Report_format.md` for formatting rules.
2. **Attribution** — spec is locked (`ATTRIBUTION_SPEC.md`), execution NOT yet run against frozen
   labels (waiting on supervisor's channel-set review). A separate earlier probe (Gini-based) gave a
   negative result (0/8 subjects significant) — report honestly as PROVISIONAL.
3. **Web demo (SzScan)** — spec locked (`WEB_DEMO_SPEC_v4.md` wins on any conflict), design system
   locked (`WEB_DEMO_DESIGN_SYSTEM.md`). Not yet built. Sequencing: Phase C done → attribution → demo
   (do not build in parallel with attribution, to avoid two diverging numbers).
4. **Defense prep** — Q&A anchors: why Phase D wasn't run (`PHASE_D_HANDOFF.md` §3), why 0.361/0.426 F1
   is competitive (SzCORE Challenge 2025 realistic ceiling is 0.32–0.43 on a harder held-out set), how
   to frame the 7-lever negative program as rigor not failure (`RUBRIC_TRACKING.md` §6).

## 6 · Integrity rules carried forward from Phase B/C (still binding for report/demo work)

- Never touch or re-derive TEST-subject numbers. They are locked and reported as-is.
- Any number quoted in the report must trace to `RESULTS_OF_RECORD_phaseB.md` §1–§9 — re-read before
  quoting, don't rely on memory across a long chat.
- Attribution and demo work must use the `rlg` checkpoint (`gae_joint_seed42.pt`), never the C4-full
  multi-relational checkpoint.
- Archive, don't delete, when superseding a file — provenance matters for defense Q&A.

## 7 · Where to start in a new chat

Read, in this order: this file (`PROJECT_STATUS.md`) → `RESULTS_OF_RECORD_phaseB.md` §1–§9 (numbers) →
whichever of the following matches the task: `THESIS_REPORT_WRITING_GUIDE.md` + `RUBRIC_TRACKING.md`
(report), `ATTRIBUTION_SPEC.md` (attribution), `WEB_DEMO_SPEC_v4.md` (demo), `PHASE_C_FULL_AUDIT.md`
(if asked to explain/defend a specific optimization decision), `PHASE_D_HANDOFF.md` (if asked about
future work / why Phase D didn't run). `REPO_MAP.md` for file/path lookup.
