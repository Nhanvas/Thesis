#!/usr/bin/env python
"""
p3_record_97.py -- append record section 9.7 (p3_levers, P3-B diagnostics, freeze step, stop plan), 2026-10-07.
Numbers copied from results/p3_levers/SUMMARY.md and results/p3b_diag/SUMMARY.md. Idempotent; keeps CRLF/LF.
Run:  python src/p3_record_97.py      (seconds)
"""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs" / "PERF_PHASE_RECORD.md"
MARK = "### 9.7 Levers, P3-B diagnostics, freeze step"
TEXT = r"""
### 9.7 Levers, P3-B diagnostics, freeze step and stop plan (2026-10-07 evening)

**p3_levers (non-test, 4 seeds; reproduction of the frozen detector and E18 exact).** k = 4.0677.
L2 0.657 @ 20.53 FA/day, subject-mean 0.814, validation 0.983, chb12 TP 4.75 = frozen → gate passed (no
gain over the frozen 0.668 @ 19.98; non-inferior). L6 hybrid on L2: sensitivity 0.654 (detector 0.657), onset
8 s = CPD, offset 12 s vs CPD 16 s → adopted; on the frozen detector it failed only the margin (0.662 vs
0.663; CPD 0.662 as well). Label-free test budgets (T-A): chb15 0.0200 (cap) on all 4 seeds; chb06 and
chb17 at the 0.0025 floor; others 0.0028–0.0082.
**Measured harm of the L2 floor (non-test):** chb21 at 0.0025 TP 1.75 → 0.50; chb20 at 0.0041 3.0 → 2.5.
L2 passed only because other patients compensated. Fix → L2f (budget never below 0.005), `src/p3c_freeze.py`.

**D1 smoothing (H9).** Not supported: chb15 median p_need 0.0234 at 1 window vs 0.0191 at 5; test
seizures at p_need ≤ 0.005: 22.75 (1) / 25.75 (5) / 18.25 (9). Non-test curve at ≤ 25 FA/day: smoothing 5
0.668 @ 20.0, smoothing 9 0.697 @ 19.9 (top 0.0075) — the two sets disagree (rule 19); smoothing stays 5,
L7 is not run. A uniform 2 % budget costs 95.1 FA/day on non-test (sensitivity 0.803): only per-patient
budgets are affordable.
**D2.** The top non-ictal windows are mostly flagged (typically 0.45–1.0) and rarely peri-ictal (within 10 min,
outside the tolerance: mostly < 0.2; exceptions chb08 top 0.5 % 1.00, non-flagged — a post-ictal state that
still left 4.25/5 caught — and chb09 0.30); chb15 0.785 flagged, 0.05 peri-ictal. Exception chb06:
flagged 0.27–0.30 — its tail is not high-amplitude activity (its readout is inverted; limitation). The
`median_dist_min` column is void (np.median over NaN; script bug; `peri_10min` is unaffected).
**D3.** No dominant channel (top share typically 0.09–0.20, max 0.44 chb08). Montage order (code):
FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, F3-C3, C3-P3, P3-O1, FP2-F4, F4-C4, C4-P4, P4-O2, FP2-F8, F8-T8,
T8-P8 (14), P8-O2 (15), FZ-CZ (16), CZ-PZ (17); T8-P8 is never dominant. No channel defect.

**Reading (the core).** The remaining test failure is a ranking problem: in chb06, chb13 and chb16 the
seizures sit at the 2–5 % level below the patient's own high-amplitude non-seizure states — the P1 core
(record §4) that the representation still carries. No cache-only lever measured tonight targets it; it
needs a representation change (Future Work). L8 (seed average) and L11 (±5 min median) are not run: no
measured mechanism points to them. chb15 is the one near miss a label-free budget can reach.

**Freeze step (p3c_freeze, before its result).** L2f gate = the L2 gate + monotonicity (every subject's TP ≥
frozen); L2f replaces L2 if it passes and its pooled ≥ L2's. Localizer by the L6 rule on the chosen budget.
Sensitivity-priority point: floor = the best smoothing-5 top-p at ≤ 40 FA/day on non-test, kept if ≤ 40.
`e23_test_look7.py` reads `results/p3c_freeze/freeze.json`.

**Stop plan.** No new arm after p3c_freeze. Sequence: p3c_freeze → author approval → tag `p3-frozen` →
look #7 (both points) → record 9.8 + handoff → performance work closed. 23:30 is reserved for fixing a
script error and re-running the same configuration, never for changing it.
"""


def main():
    s = P.read_bytes().decode("utf-8")
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    if MARK in s:
        print("record: 9.7 already present"); return
    if "### 9.6 P3-A results" not in s:
        raise SystemExit("STOP: section 9.6 missing")
    s = s.rstrip("\n") + "\n" + TEXT
    P.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")
    print("record: 9.7 appended")


if __name__ == "__main__":
    main()
