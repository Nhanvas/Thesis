#!/usr/bin/env python
"""
p3_record_97b.py -- append record section 9.7b (freeze step results, decisions and reading rule before look #7),
2026-10-07. Numbers copied from results/p3c_freeze/SUMMARY.md. Idempotent; keeps CRLF/LF.
Run:  python src/p3_record_97b.py      (seconds)
"""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs" / "PERF_PHASE_RECORD.md"
MARK = "### 9.7b Freeze step results"
TEXT = r"""
### 9.7b Freeze step results and the rules for look #7 (fixed before the look)

**p3c_freeze (non-test, 4 seeds; reproductions of L2 and of the frozen detector exact; 76 s).**
L2f detector 0.678 @ 23.81 FA/day, subject-mean 0.842, validation 0.983, without chb12 0.868, every
subject's TP ≥ frozen (chb21 back to 1.75, chb20 to 3.0) → gate passed, pooled ≥ L2 (0.657) → **L2f
replaces L2**. L2f's +0.010 over the frozen detector costs +3.8 FA/day: it lies on the frozen detector's own
curve (0.668 @ 20.0 → 0.705 @ 32.3), so L2f wins nothing on non-test; its expected benefit on test is the
budget given to chb15. Localizer (L6 rule on L2f): hybrid onset 8 s vs CPD 4 s (worse: events > 300 s and
fallbacks keep detector onsets) → **CPD stays**. After CPD: 0.670 @ 23.25, subject-mean 0.832.
Sensitivity-priority point (floor 0.0075 = best smoothing-5 top-p at ≤ 40 FA/day): 0.697 @ 32.73 after CPD
→ kept, **descriptive only**. Review fraction (event time / recorded time) after CPD: L2f 0.0162, S 0.0219.
Label-free test budgets (balanced): chb15 0.0200 on all seeds (raw q 0.0231–0.0250, above the cap); chb14
0.0055–0.0065, chb18 0.0063–0.0082, chb03 0.0050–0.0052; chb06, chb13, chb16, chb17 at 0.0050 (raw q below 0.005).

**Disclosures.** (1) The cap 0.02 binds for chb15 (raw q above it on every seed) and for no non-test patient
(non-test maximum 0.011): the cap decides chb15's result and is untested on non-test. It was fixed in the
decision table (9.5) after look #6 and the burden table, before the per-seizure anatomy — test-informed in
the broad sense. (2) L2 / L2f have no measured benefit on non-test (chb12, the seizure-rich analogue, gets
0.0051 and stays at 4.75). (3) The label-free test budgets were seen before L2f was designed; the reason for
L2f is the non-test chb21/chb20 loss. (4) "A representation change is needed for chb06/chb13/chb16" is an
untested hypothesis, not a finding: patient fine-tuning (E15), more capacity (E1) and input normalisation
(H7) all lacked support.
**Correction (Claude 1).** The earlier forecast of 27–32 FA/day on test for the balanced point was too low.
Computed from the label-free test budgets: budget-weighted mean top-p ≈ 0.0076, which on the non-test
curve is ≈ 32 FA/day; × 1.2 ≈ 38. Expectation: balanced ≈ 35–40 FA/day, sensitivity point ≈ 45–50.

**Frozen P3 system (tag `p3-frozen`).** P2 frozen scalar and D1 (smoothing 5, merge 90 s) with top-p_i =
clip(q_i(k = 4.0677), 0.005, 0.02); kernel CPD localizer (E18). Second, descriptive operating point:
clip(q_i, 0.0075, 0.02). `results/p3c_freeze/freeze.json`, read by `src/e23_test_look7.py`.
**Reading rule for look #7.** The target (pooled ≥ 0.50; seed-42 headline with the 4-seed mean) is judged
on the balanced point only. Every result is reported as is: ≥ 0.50 → target reached; < 0.50 → not reached,
reported with the subject-mean and the bootstrap difference to look #6; balanced FP/day > 40 → flagged as
above the acceptable level. Look #6 stays the clean held-out result; look #7 is labelled test-informed.
No look #8. After look #7: record 9.8 and handoff; performance work closes.
"""


def main():
    s = P.read_bytes().decode("utf-8")
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    if MARK in s:
        print("record: 9.7b already present"); return
    if "### 9.7 Levers, P3-B diagnostics" not in s:
        raise SystemExit("STOP: section 9.7 missing")
    s = s.rstrip("\n") + "\n" + TEXT
    P.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")
    print("record: 9.7b appended")


if __name__ == "__main__":
    main()
