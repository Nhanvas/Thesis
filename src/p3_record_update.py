#!/usr/bin/env python
"""
p3_record_update.py -- append record section 9.6 (P3-A results and lever triggers), 2026-10-07.
Numbers are copied from results/p3_anatomy/SUMMARY.md (P3-A, 4-seed means). Idempotent; keeps CRLF/LF.
Run:  python src/p3_record_update.py      (seconds)
"""
from pathlib import Path

P = Path(__file__).resolve().parents[1] / "docs" / "PERF_PHASE_RECORD.md"
MARK = "### 9.6 P3-A results"
TEXT = r"""
### 9.6 P3-A results (`results/p3_anatomy/`, 436 s; gates R0, R2, R3, R4 passed)

**T-A, label-free.** f7 clip share ≤ 0.012 on every test patient (non-test up to 0.077, chb09); median
shift ≤ 1.56 training SD (chb14 1.562 vs the non-test maximum 1.540, chb10 — marginally above). Only the
7 added node features were checked, not the adjacency. No (file, channel) pair has a median per-channel
z > 3 anywhere. After the ±15 min correction the file drift is 0.02–0.05 MAD on every patient. **H7 not
supported by this check; L5 not triggered.** Two label-free clues (reviewer): after the correction the
tail still sits in top-quartile files in chb16 (0.706), chb03 (0.645) and chb06 (0.257 → 0.515; also
chb04 0.629, chb11 0.683 on non-test); the 4-seed mean index of the tail-owning channel is 14.5–16 in 5/8
test patients vs 3/15 non-test (a mean of indices; to be read per channel against the montage order, P3-B D3).

**T-B, per seizure** (p_need = top-p a threshold needs to touch the seizure; frozen budget 0.005):

| seizures with p_need ≤ | 0.005 | 0.01 | 0.02 | 0.05 | 0.10 |
|---|---|---|---|---|---|
| test (76) | 25.75 | 27.5 | 45.5 | 62.25 | 71.25 |
| non-test (93) | 60.5 | 66.5 | 74.25 | 85.25 | 90.0 |

An upper bound (no false alarms, no merging), not an operating curve. chb15: 0/20 at ≤ 0.01 but 10.5/20
at ≤ 0.02 (median p_need 0.019) — its seizures sit just below the budget, a near miss. Non-test analogue
chb12: 4.75 → 12.5 of 27 between 0.005 and 0.02. chb06, chb13, chb16: mostly 0.02–0.10 (chb16 in-seizure
peaks median 0.185: short seizures). Missed test seizures, seed 42: 16 near (0.005–0.02; chb15 11),
28 mid (0.02–0.10), 5 deep (> 0.10).

**Members.** Seizures at ≤ 0.005 (test / non-test): S9e 25.0 / 61.0, S12e 24.0 / 61.0, Smean_e 24.75 /
59.75, S6e 23.0 / 58.25, S3e 22.0 / 59.0, S1e 19.25 / 54.25. Focal members rescue 1.5 (S3e) and lose
5.25 on test; chb15's seizure peaks recruit 8 channels (median) with z > 3. **H6 not supported in this
configuration; L1 not triggered.** Without the ±15 min correction: 13.0 test / 47.25 non-test (vs 25.75 /
60.5) — removing the correction hurts; the guarded variant (L3) was not tested. **H8 not supported by this
check; L3 not triggered.** Trimmed refit, 5 % (non-test): rescues 0.25, loses 2.0. **H2 not supported in
this configuration; L4 not triggered.** chb15's channels with median z > 2 over the whole seizure: 0.5
(peaks 8) — bursty anomaly, possibly diluted by the 20-s smoothing (H9, P3-B D1); chb12 shows the same
pattern (5.25 / 0).

**Triggered (decision table 9.5): L2** (16 ≥ 3 near misses) **and L6** (always) → `src/p3_levers.py`
(gates as in 9.5, reproduction of the frozen detector and of E18 first). Look #7 script
`src/e23_test_look7.py` written before any P3 result on test; it runs only if p3_levers changes the
frozen configuration, after tag `p3-frozen`.

**Headline rule (fixed 2026-10-07, before look #7; reviewer audit 3).** Look #6 remains the clean held-out
result. The thesis's final system is the P3-frozen configuration chosen on the non-test gates before look
#7; look #7 reports it on test, labelled test-informed, at two operating points declared before the look:
**balanced** (D1 cell re-selected at ≤ 25 FA/day on non-test) and **sensitivity-priority** (≤ 40 FA/day on
non-test). No look #8. The headline is never chosen by a test result. Hard stop for P3: 23:30, 07/10.
`p3_levers.py --include-test` prints only the label-free budget p_i on test; `e23 --repro-only` reads
non-test chb01 only.

**P3-B (reviewer audit 3).** Diagnostics first (`src/p3b_diag.py`): D1 smoothing scales {1, 2, 3, 5, 9}
(per-seizure p_need, non-test operating curve, short-seizure proxy = first 3 windows of each non-test
seizure without tolerance); D2 where the top non-ictal windows lie relative to seizures (peri-ictal
share, flagged share, files); D3 tail-owning channel per channel index vs the montage. Then levers L7
(multi-scale smoothing union, only if D1 supports it), L8 (4-seed average of the scalar), L11 (±5 min
running median), each designed after D1–D3 and before its own result; every lever must also move its
mechanism on chb12 (non-test analogue), never on chb15 alone.
"""


def main():
    s = P.read_bytes().decode("utf-8")
    crlf = "\r\n" in s
    s = s.replace("\r\n", "\n")
    if MARK in s:
        print("record: 9.6 already present"); return
    if "### 9.5 Decision table" not in s:
        raise SystemExit("STOP: section 9.5 missing (run p3_open_docs.py first)")
    s = s.rstrip("\n") + "\n" + TEXT
    P.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")
    print("record: 9.6 appended")


if __name__ == "__main__":
    main()
