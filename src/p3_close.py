#!/usr/bin/env python
"""
p3_close.py -- close stage P3 in the canonical docs (2026-10-07). Text only; numbers copied from
results/e23_test_look7/SUMMARY.md (look #7). Idempotent; keeps CRLF/LF; every anchor must occur once.
  docs/PERF_PHASE_RECORD.md   -> section 3 row "7", section 9.8 (look #7 and the close of P3)
  docs/PROJECT_INSTRUCTIONS.md -> header, P3 frozen system in section 4, status in section 5, tags
Run:  python src/p3_close.py      (seconds)
"""
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

ROW7 = ("| 7 | P3 frozen system (tag `p3-frozen`), `e23_test_look7.py`, 2026-10-07 — **TEST-INFORMED** (record 9.2) | "
        "balanced point, seed 42 after the localizer **37/76 (0.487) @ 27.5 FP/day**, precision 0.104, F1 0.172, subject-mean "
        "0.577; 4 seeds 0.477 ± 0.022 @ 29.2 ± 1.3, subject-mean 0.567; detector stage 38/76 (0.500) @ 28.4. Look #6 reproduced "
        "exactly (R2). No look #8 |")

SEC98 = r"""
### 9.8 Look #7 (test-informed) and the close of P3

**Balanced point (the target point), seed 42 after the CPD localizer: 37/76 = 0.487 @ 27.49 FP/day**, precision
0.104, F1 0.172, subject-mean 0.577. 4 seeds: 0.477 ± 0.022 @ 29.15 ± 1.26, subject-mean 0.567 ± 0.019.
Detector stage (before the localizer): seed 42 38/76 = 0.500 @ 28.35, 4 seeds 0.480 ± 0.025.
**By the reading rule (9.7b) the target is not reached:** the frozen system's output is after the localizer,
one seizure short on seed 42. FP/day stayed below the pre-registered expectation (35–40) and below 40.
Per subject (seed 42): **only chb15 changed (0 → 11/20)**; FP rose in chb15 (14 → 53), chb14 (27 → 34) and
chb18 (23 → 38); every other patient is identical to look #6 (budget 0.005). chb06 2/10, chb13 1/12,
chb16 2/10 unchanged (32 seizures, 5 caught).
Patient-level bootstrap vs look #6 (4-seed means, B = 10,000): pooled +0.141 [0.000, 0.333], subject-mean
+0.070 [0.000, 0.201], FP/day +5.27 [+0.37, +13.60]. The gain rests on one patient and on the cap 0.02,
which binds only on test (disclosure 9.7b).
Sensitivity-priority point (descriptive): seed 42 0.487 @ 36.83; 4 seeds 0.490 ± 0.022 @ 38.12 — about +9
FP/day for no material gain.
Localization (balanced, n = 146 matched pairs): onset |error| detector 32 s, CPD 12 s (bias +8), offset
detector 20 s, CPD 24 s (bias +16), contiguous-run (hybrid) offset 16 s. CPD's role on test is the onset
(32 → 12 s); its offset is late, as on non-test (9.7, 6.1). The hybrid was not adopted (non-test rule) and is
not switched after the look.

**How the report presents the test results (fixed).** Look #6 (P2 frozen, 0.342 @ 22.2, subject-mean
0.498) is the clean held-out evaluation. Look #7 (P3 frozen, 0.487 @ 27.5, subject-mean 0.577) is the
final system, labelled test-informed, with the bootstrap interval and the statement that its gain is
chb15 at a budget cap that binds only on test. Both are reported; neither replaces the other.

**What remains unsolved (Future Work, hypotheses, not findings).** chb06 (10 generalized seizures of
12–20 s; inverted readout; its non-ictal tail is not high-amplitude, flagged 0.27–0.30), chb16 (10 seizures
of 6–14 s, below the 4-s window with 20-s smoothing) and chb13 (12 seizures at the 2–5 % level under its own
high-amplitude states, flagged 0.89 in its tail). Candidate directions, none tested: shorter or overlapping
windows for short seizures (rebuild of graphs and retraining), a two-sided readout for seizures that are
more regular than the background, and a representation that separates seizures from the patient's own
high-amplitude states. Patient fine-tuning (E15), capacity (E1) and input normalisation (H7) lacked support.
Any test of these would need a new evaluation set; the CHB-MIT test set is used up (looks 1–7).

**P3 closed (tag `perf-p3-closed`).** Performance work stops here; next: report Chapters 2–5 and the demo
(`docs/HANDOFF_REPORT.md`).
"""

INSTR = [
    ("> **Rev. 2026-10-07 evening (P3 opened).**",
     "> **Rev. 2026-10-07 night (P3 CLOSED).** Final system = P3 frozen (tag `p3-frozen`, record §9.7b–9.8).\n"
     "> Look #7 (test-informed): 0.487 (37/76) @ 27.5 FP/day, subject-mean 0.577 (seed 42); look #6 stays the clean\n"
     "> held-out result. Performance work is closed; next = report and demo, start from `docs/HANDOFF_REPORT.md`.\n>\n"
     "> **Rev. 2026-10-07 evening (P3 opened).**", "header"),
    ("4 seeds 0.336 ± 0.008, subject-mean 0.498, onset/offset 8/20 s**.",
     "4 seeds 0.336 ± 0.008, subject-mean 0.498, onset/offset 8/20 s**.\n\n"
     "### P3 frozen system (tag `p3-frozen`, record §9.7b) — FINAL\n"
     "The P2 scalar and D1 (smooth 5, merge 90 s) with a label-free per-patient budget top-p_i = clip(q_i, 0.005,\n"
     "0.02), q_i = share of the patient's smoothed member-mean robust-z above k = 4.0677 (calibrated on non-test);\n"
     "kernel CPD localizer. Non-test 0.670 @ 23.3 after CPD. **Look #7 (test-informed): 0.487 (37/76) @ 27.5,\n"
     "4 seeds 0.477 ± 0.022 @ 29.2, subject-mean 0.577 / 0.567; gain = chb15 0 → 11/20 at the cap; onset/offset\n"
     "12/24 s.** Descriptive sensitivity point clip(q_i, 0.0075, 0.02): 0.487 @ 36.8.", "section 4"),
    ("**Performance phase — current (2026-10-07).** P1 (E1–E10) and P2 (E11–E22) closed.",
     "**Performance phase — CLOSED (2026-10-07 night).** P1–P3 closed; final system and the two test looks to\n"
     "report: record §9.8. Next: report Chapters 2–5 and the demo (`docs/HANDOFF_REPORT.md`). History follows.\n"
     "P1 (E1–E10) and P2 (E11–E22) closed.", "section 5"),
    ("`perf-p1-closed` · `p2-frozen` · `perf-p2-closed`.",
     "`perf-p1-closed` · `p2-frozen` · `perf-p2-closed` · `p3-frozen` · `perf-p3-closed`.", "tags"),
]


def load(p):
    s = p.read_bytes().decode("utf-8")
    return s.replace("\r\n", "\n"), "\r\n" in s


def save(p, s, crlf):
    p.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")


def main():
    p = DOCS / "PERF_PHASE_RECORD.md"; s, c = load(p)
    if "### 9.8 Look #7" in s:
        print("record: 9.8 already present")
    else:
        if "### 9.7b Freeze step results" not in s:
            raise SystemExit("STOP: record 9.7b missing")
        lines = s.split("\n")
        hit = [i for i, l in enumerate(lines) if l.startswith("| P3-T |")]
        if len(hit) != 1:
            raise SystemExit(f"STOP: section 3 row P3-T found {len(hit)} times")
        lines.insert(hit[0] + 1, ROW7)
        s = "\n".join(lines).rstrip("\n") + "\n" + SEC98
        save(p, s, c); print("record: row 7 and 9.8 written")
    p = DOCS / "PROJECT_INSTRUCTIONS.md"; s, c = load(p)
    if "Rev. 2026-10-07 night (P3 CLOSED)" in s:
        print("instructions: already updated")
    else:
        for old, new, label in INSTR:
            n = s.count(old)
            if n != 1:
                raise SystemExit(f"STOP instructions {label}: anchor found {n} times")
            s = s.replace(old, new)
        save(p, s, c); print("instructions: updated")


if __name__ == "__main__":
    main()
