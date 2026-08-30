# PHASE B — RE-OPTIMIZED ROADMAP v2 (2026-08)

**Goal (unchanged, restated):** push **every** metric up *proportionally vs SOTA* — event
{sensitivity, precision, F1, FP/day} **and** window {AUROC, AUPRC, precision, recall, F1}. No single-metric
headline. Trade-offs allowed, never lopsided below the SOTA floor on any axis.

---

## 1. WHERE WE ARE — numbers of record after Phase-0 (all VAL-derived, one-shot test, reproduce §0)

**Event level (reportable, test-clean):**
| Point | rule | sens | prec | F1 | FP/day | use |
|---|---|---|---|---|---|---|
| Triage (§0 high-sens) | VAL, ~high recall | 0.776 | 0.065 | 0.121 | 72.7 | catch-most for review |
| **Balanced / SOTA-comparison** | **VAL FP-budget → mag80/pen5** | **0.395** | **0.316** | **0.351** | **5.6** | **headline vs SzCORE** |
| (retired) argmax-F1 mag80/pen10 | — | 0.276 | 0.362 | 0.313 | 3.2 | lopsided; not headline |

Balanced point matches the SOTA event band (SzCORE top F1 0.43 / EPFL 0.32; sens ~0.37; prec 0.29–0.45)
on **all four axes**, unsupervised, on CHB-MIT. Window macro-AUROC 0.775 (beats unsupervised scalp ~0.68).

**What Phase-0 established (banked):**
- Operating-point placement was the first big honest fix: §0 balanced F1 0.168 → 0.351 by reporting at
  the right FP rate (decision-layer only, no retraining).
- **Decision-layer levers are now EXHAUSTED.** Shared re-selection (PREREG_06) and per-subject label-free
  FP-budget (PREREG_07) both fail to beat mag80/pen5. Per-subject recovers **only chb17** (0→0.667);
  chb06/chb14 uncatchable at any budget; **chb16 corrected from "cheap Phase-1" to representation-limited
  at usable FP.**
- The remaining ceiling (~sens 0.40 / F1 0.35 @ 5 FP/day) is **representational**, set by chb06 (AUROC
  0.437, below chance), chb14 (0.626), chb16 (fires only at very high FP). T3 oracle F1 ≤ 0.09 for
  chb06/chb14 confirms no operating point rescues them.

## 2. WHY the wall is representational (the defensible diagnosis)
For chb06/chb14/chb16 the ictal windows do not separate from the interictal score distribution → no
threshold (label-free, or even the per-subject oracle) converts them to events. Lifting them requires
better *features/graphs*, not better *thresholds*. This is exactly the failure mode the graph-structure-
learning literature targets (IRENE/GraphS4mer for below-chance connectivity subjects).

---

## 3. WHAT'S NEXT — three tiers, ordered by ROI and by the timeline (submit Oct 15)

### TIER 0 — reporting completeness (free / CPU, no model change) — **do first**
Fills the *other half* of the mandate and hardens the defense.
- **W1 · Window-metric suite:** AUPRC, window precision/recall/F1 at a VAL-derived window threshold, per
  subject + macro, vs window SOTA (CSBrain AUPRC 0.516, foundation-model AUROC band). Needs
  `ens_seed42_{subj}_{inter,ictal}.npy` (confirmed present). *Closes "all metrics" at window level.*
- **W2 · Consolidate RESULTS_OF_RECORD §0**: full Pareto + both operating points + per-subject table +
  the honest negative results (per-subject, argmax-F1). After cô sign-off.

### TIER 1 — cheap levers that lift event metrics WITHOUT retraining — **highest remaining ROI**
- **A1 · Inference-time artifact / signal-quality gate** before PELT (amplitude, line-length, cross-channel
  similarity, or a light artifact classifier). Literature precedent: 22.9→1.0 FP/h (Ingolfsson 2024).
  **Target: ≥50% FP/day cut at equal sensitivity** → directly raises precision + F1 at fixed sens = the
  "all metrics up proportionally" move. CPU. Falsification: if FP/day at fixed sens doesn't drop, revert.
- **A2 · T4 chb06 sign-flip / rolling-z probe** — gates Phase 2. Files confirmed
  (`ens_seed42_chb06_*` + branch components `{zrecon,ztemp,zgamma}_chb06_*`). If chb06's anomaly signal is
  merely **inverted** in one branch, it recovers for *free* — and chb06 has 10 seizures, the single biggest
  representational block. If not inverted → chb06 is genuinely rep-limited → Phase 2 or Future Work.

### TIER 2 — representation (GPU, gated by A2 + probes) — the only lever that lifts hard-subject AUROC
Prioritized; each gated by a pre-registered pass bar. Given the Oct-15 timeline, treat as **stretch /
likely partial**; SSL branch is already GVHD-scoped to Future Work.
- **R1 · Learned sparse graph structure** (IB/self-expressive or Gumbel-softmax GSL layer on the GCN
  encoder, trained by existing reconstruction loss — no labels). Direct fix for chb06's inverted/noisy
  connectivity; literature's largest AUROC gains. **Gate: chb06 window AUROC > 0.5 (chance), ideally
  > 0.7; macro AUROC > 0.80.** Highest Phase-2 priority.
- **R2 · Multi-band features** (beyond gamma-AEC) — cheap-ish representational add.
- **R3 · Masked/contrastive SSL 4th branch** (EEG2Rep/IRENE-style) — **Future Work** (scoped out).
- **R4 · Foundation-model transfer** — lowest priority, exploratory, Future Work.

---

## 4. SEQUENCING vs the calendar
1. **Now → next few sessions (CPU, safe):** W1 window-suite → A2 (T4 chb06) → A1 artifact gate. These are
   the realistic, bankable Phase-B gains before Oct 15, and they move event *and* window metrics.
2. **If A2 says chb06 is a cheap fix:** apply it (free representational win) before submission.
3. **Phase 2 (R1) GPU:** only if time remains after Tier 0/1 and A2 justifies it; otherwise R1 becomes the
   headline Future-Work direction with a small proof-of-concept if possible.

## 5. DECISIONS needing cô ratification before Phase 2 (D1–D3)
- **D1** stay fully unsupervised (yes — core thesis identity).
- **D2** do not open external unlabeled data unless in-domain SSL underperforms.
- **D3** report the **full Pareto** headlining both the triage (0.776) and the balanced (mag80/pen5) points
  — not a single number. *(This roadmap already assumes D3.)*
- **New for cô:** the honest reframe — decision-layer optimization is complete and delivered mag80/pen5;
  further gains are representational; per-subject calibration was tried and did not beat the shared point.

## 6. What is DONE vs OPEN
DONE: T1 (superseded by RESELECT), RESELECT/PREREG_06 (balanced headline), T2 (SOTA table draft),
T3 (oracle split), per-subject FP-budget (PREREG_07, negative), denominator audit.
OPEN: W1 window-suite · A2 (T4 chb06) · A1 artifact gate · (gated) R1 learned graph · thesis write-up.
