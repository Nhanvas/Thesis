# WINDOW SUITE (W1) + T4 CLOSURE — results of record (2026-08)

## W1 — Window-metric suite (PREREG_08; seed 42, equal weights; macro AUROC gate PASS = 0.775)

| subj | prev | AUROC | AUPRC | lift | w_prec | w_rec | w_F1 |
|---|---|---|---|---|---|---|---|
| chb03 | 0.006 | 0.954 | 0.171 | 28.0 | 0.168 | 0.349 | 0.227 |
| chb06 | 0.002 | 0.437 | 0.004 | 1.6 | 0.000 | 0.000 | 0.000 |
| chb13 | 0.011 | 0.805 | 0.038 | 3.3 | 0.043 | 0.104 | 0.061 |
| chb14 | 0.003 | 0.626 | 0.021 | 5.9 | 0.000 | 0.000 | 0.000 |
| chb15 | 0.029 | 0.826 | 0.218 | 7.4 | 0.436 | 0.126 | 0.196 |
| chb16 | 0.004 | 0.871 | 0.104 | 24.0 | 0.063 | 0.429 | 0.110 |
| chb17 | 0.008 | 0.747 | 0.016 | 2.1 | 0.003 | 0.027 | 0.006 |
| chb18 | 0.006 | 0.938 | 0.201 | 36.2 | 0.333 | 0.181 | 0.234 |
| **MACRO** | | **0.775** | **0.097** | **13.6×** | 0.131 | 0.152 | 0.104 |
| POOLED | 0.009 | 0.817 | 0.051 | | | | |

Window threshold t\* = 4.85 (VAL F1-optimal, frozen). AUROC/AUPRC are threshold-free.

**Honest SOTA framing (window level):** macro AUROC 0.775 beats the unsupervised scalp field (Yildiz
~0.68). Macro AUPRC 0.097 is far below supervised foundation-model AUC-PR (CSBram ~0.52, CBraMod 0.37),
but those are **supervised, segment-level, higher-prevalence** — not comparable. The prevalence-invariant
**AUPRC lift (13.6× macro; 24–36× on chb03/16/18)** is the honest cross-setting statement. Strong subjects
carry real precision; the hard subjects (chb06 1.6×, chb17 2.1×, chb14 5.9×) sit near chance and pull the
macro down — consistent with the representation ceiling.

## T4 — chb06 sign/normalization probe: CLOSED → representation-limited (no free fix)

Per-branch AUROC (test subjects; VAL components absent but not required for the conclusion):

| subj | zrecon | ztemp | zgamma | ensemble | reading |
|---|---|---|---|---|---|
| chb03 | 0.659 | 0.662 | 0.969 | 0.954 | healthy |
| chb14 | 0.662 | 0.823 | **0.401** | 0.626 | **zgamma inverted** (subject-specific) |
| chb06 | **0.300** | 0.488 | 0.578 | 0.437 | **zrecon inverted** (subject-specific) |

**Verdict:** zrecon is correctly signed for chb03/chb14 → no global sign bug. chb06's inversion is
**subject-specific**; correcting it needs chb06's labels → **test leakage → forbidden**. The auto-gate in
`t4_chb06_probe.py` that read "free fix" was **too optimistic** (it did not check that the flip decision
uses test labels); the globality check overrides it. chb06 (zrecon) and chb14 (zgamma) each have a
different branch pathologically inverted — idiosyncratic, not systematic.

**Scientific implication (Phase-2 justification):** different subjects fail on different branches under a
fixed top-k graph → motivates **learned/adaptive graph structure** (R1, IRENE/GraphS4mer). chb06 & chb14
are confirmed **representation-limited → Phase 2 / Future Work**. Consistent with T3 (oracle F1 ≤ 0.09).

**T4 status: CLOSED.** No reportable-number change. Diagnostic only.

## Roadmap deltas
- Decision-layer optimization: DONE (headline mag80/pen5). Per-subject FP-budget: negative. T4: closed.
- chb06, chb14 → Phase 2 / Future Work (representation).
- Next ROI lever = A1 inference-time artifact gate (global precision/F1 at fixed sensitivity).
