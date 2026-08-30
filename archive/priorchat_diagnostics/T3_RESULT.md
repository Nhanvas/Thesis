# T3 RESULT — Per-subject grid-oracle ceiling (Phase-B diagnostic)

**Nature:** DIAGNOSTIC. The grid-oracle PEEKS at per-subject labels to find each subject's best
(mag,pen) cell. It is an **oracle, never a reportable operating point**. Purpose: separate
representation-limited from decision-limited subjects **before** spending GPU on Phase 2.
**Grid-oracle = best F1 over the 48 grid cells = a LOWER bound on the true continuous-threshold oracle.**
Uses the scorer's own `sensitivity`/`precision` columns (authoritative SzCORE; not tp/n_seizures).

---

## TEST — the §3.2 split is CONFIRMED empirically

| Subject | Window AUROC | Oracle F1 | Oracle cell | F1 @ shared OP (mag80/pen10) | Gap | Route |
|---|---|---|---|---|---|---|
| chb06 | 0.437 | **0.087** | mag40/pen10 | 0.000 | 0.09 | **REPRESENTATION → Phase 2** |
| chb14 | 0.626 | **0.083** | mag65/pen2 | 0.000 | 0.08 | **REPRESENTATION → Phase 2** |
| chb17 | 0.747 | 0.444 | mag50/pen10 | 0.000 | 0.44 | **DECISION → Phase 1** |
| chb13 | 0.805 | 0.367 | mag80/pen0.3 | 0.111 | 0.26 | DECISION → Phase 1 |
| chb15 | 0.826 | 0.727 | mag80/pen5 | 0.514 | 0.21 | DECISION → Phase 1 |
| chb16 | 0.871 | 0.265 | mag55/pen0.3 | 0.000 | 0.27 | DECISION (high AUROC, loose-OP recovery) → Phase 1 |
| chb18 | 0.938 | 0.471 | mag80/pen10 | 0.471 | 0.00 | near ceiling at shared OP |
| chb03 | 0.954 | 0.737 | mag80/pen10 | 0.737 | 0.00 | near ceiling at shared OP |

## The three findings that gate Phase 2 spend

**1. Only chb06 and chb14 are representation-limited.** Even peeking at labels across the entire grid,
their best achievable F1 is ≤ 0.09. **No operating point rescues them** — this is a signal/representation
problem, exactly the §3.2 prediction. These are the *only* two subjects that justify GPU / Phase-2
graph-structure work. (chb06 still needs T4 — sign-flip/rolling-z — to rule out a cheap polarity/norm bug
before it is written to Future Work; the plan mandates T4 before write-off.)

**2. chb16 and chb17 are decision-limited — cheap Phase-1 wins.** chb17 is the sharpest case:
oracle F1 **0.444** but **0.000** at the shared OP (gap 0.44). chb16: AUROC 0.871 (representation is
fine) but 0.000 at the shared OP. Their signal exists; the single tight shared operating point strangles
it. Per-subject event-conversion recovery (P1.2, CPU-only) is the right tool — no retraining.

**3. chb03/chb18 are already at their ceiling** at mag80/pen10; chb13/chb15 have moderate decision-layer
headroom. So of the 76 seizures, the *recoverable-without-GPU* mass sits in chb13/15/16/17.

## Strategic implication (diagnose-before-intervene)
**Do NOT spend GPU broadly.** Phase 2 is justified for **2 subjects** (chb06, chb14) only, and only
after T4 clears chb06 of a cheap fix. Everything else moves at the decision layer (Phase 1, CPU). This is
the empirical gate the plan asked for — it prevents wasting the pre-Oct-15 window on GPU that the data
says won't pay off for 6 of 8 subjects.

## Note — a denominator bug caught and contained
chb11 (VAL) exposed that SzCORE splits seizures > 5 min, so its reference-event count (5) exceeds
`n_seizures` (3). **Impact audit:** all 8 TEST subjects have `sensitivity == tp/n_seizures` exactly
(0/48 mismatches each) → the T1 test headline (0.276 / F1 0.313) and §0 are unaffected. On VAL, only
chb11 is affected; re-deriving T1 with the correct denominator (VAL total 15, not 13) **still selects
mag80/pen10** for both OP-F1 and OP-5 → the T1 selection is invariant. Scripts now read the scorer's
`sensitivity` column directly. Logged per the "evaluation bugs masquerade as model failures" principle.

*Artifact: `t3_oracle_ceiling.csv`.*
