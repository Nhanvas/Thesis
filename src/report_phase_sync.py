#!/usr/bin/env python
"""
report_phase_sync.py -- open the report phase in the repo docs (2026-10-08). Idempotent, fail-fast.

  docs/PERF_PHASE_RECORD.md   rev R: header, look-#6 subject-mean by seed, A5 row in section 3, section 7
                              resolved, X1 hours, new section 10 (author decisions, A5, ledger note,
                              normalisation disclosure, repo state)
  docs/VERIFIED_CORRECTIONS.md section 14 + a superseded note on entry 6
  docs/ATTRIBUTION_SPEC.md     header + A5 result block (after the A5 amendment written by attribution_v8.py)
Every anchored edit must match exactly once (or already be applied), else STOP. Numbers in the added text
are read from results/attribution_v8/attribution_tests.csv and results/e22_test_oneshot/SUMMARY.md and
checked before writing.
"""
import csv
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REC = ROOT / "docs" / "PERF_PHASE_RECORD.md"
COR = ROOT / "docs" / "VERIFIED_CORRECTIONS.md"
SPEC = ROOT / "docs" / "ATTRIBUTION_SPEC.md"
MARK = "<!-- report-phase-2026-10-08 -->"


def stop(msg):
    print(f"STOP: {msg}"); sys.exit(1)


def read(p):
    return p.read_text(encoding="utf-8").replace("\r\n", "\n")


def sub1(s, pattern, repl, label):
    new, n = re.subn(pattern, repl, s, count=1, flags=re.S)
    if n != 1:
        stop(f"anchor not found: {label}")
    return new


def check_numbers():
    t = {r["test"]: r for r in csv.DictReader(open(ROOT / "results" / "attribution_v8" / "attribution_tests.csv"))}
    l1, l2 = t["L1 chance"], t["L2 anatomical prior"]
    want = [(l1["value"], "0.5473"), (l1["p"], "0.018"), (l2["value"], "-0.1914"), (l2["CI_lo"], "-0.2618")]
    for got, exp in want:
        if abs(float(got) - float(exp)) > 1e-4:
            stop(f"A5 file value {got} != {exp}")
    e22 = read(ROOT / "results" / "e22_test_oneshot" / "SUMMARY.md")
    if "0.342  0.092  0.145   22.22 | 0.508" not in e22:
        stop("e22 SUMMARY does not show seed-42 localized subject-mean 0.508")


SEC10 = f"""
{MARK}
## 10 · Report phase (opened 2026-10-08)

### 10.1 Author decisions (08/10; the supervisor reviewed the briefing and asked for the report with the current numbers)

1. **Offline protocol.** Not reported as a result (no table, no figure). One short paragraph (Methods,
   evaluation, or Discussion) states that an earlier evaluation rebuilt the timeline from the annotations
   and filled it with resampled windows from which high-amplitude windows had been removed, and that on
   the continuous recording the same earlier system at the same operating point fell from 0.618 @ 27.4
   FP/day to 23/76 (0.303) @ 73.3 FP/day. The continuous timeline is the protocol of record.
2. Label-free per-patient fitting on the whole recording is part of the unsupervised system (P2 decision;
   DynaSD as precedent).
3. Kernel CPD is the onset/offset localizer on the scalar ensemble anomaly score (decision 2026-10-07);
   the onset gain is measured, the offset is not better than a contiguous-run rule, and both are stated.
4. Test results: look #6 is the clean held-out evaluation, look #7 the final system labelled
   test-informed, side by side (9.8); X1 is the clean external evidence for the final system.
5. Aggregation: pooled and subject-mean side by side (subject-mean = SzCORE's official aggregate);
   headline seed 42 with the 4-seed mean ± SD and the patient-level bootstrap. Look #6 subject-mean:
   **seed 42 0.508, 4 seeds 0.498 ± 0.010** (`results/e22_test_oneshot/SUMMARY.md`); earlier text that
   paired 0.342 with 0.498 mixed the two.
6. The web demo is rebuilt on the final system (seed 42) and its application tier re-run:
   `docs/DEMO_REBUILD_BRIEF.md`.
7. Channel attribution re-run on the final system (A5, 10.2); A4 stays as the attribution of the earlier
   reconstruction readout.
Order of work and fallback: `docs/HANDOFF_REPORT.md` section 0.

### 10.2 Attribution A5 — final system (`src/attribution_v8.py`, `results/attribution_v8/`)

Pre-registered in `ATTRIBUTION_SPEC.md` A5 and committed with tag `attribution-a5-prereg` before scoring;
one run (70 s), gates G1 (alignment of the 76 annotations to the v2 test windows), G2 (cache), G3 (A4
order confirmation) passed. Score: per-channel robust-z of the per-channel latent distance (the system's
own per-channel quantity), p95 of |z| over the seizure. Method, labels and tests of A4.

| test | value | interval / p | verdict |
|---|---|---|---|
| L1 macro-AUROC, 62 focal | 0.5473 | [0.4992, 0.5971], permutation p 0.018 | pass (the registered criterion is the permutation p; the bootstrap lower bound touches 0.5) |
| L2 Δ vs anatomical prior (0.7387) | −0.1914 | [−0.2618, −0.1182] | fail, significantly below the prior |
| L3 matched − swapped | −0.0017 | p 0.53 | fail |
| D7 subject-constant control | −0.0754 | — | control higher |

Descriptive: without chb15 0.4864 (p 0.71); seeds 1/2/3 0.543 / 0.588 / 0.545; mean aggregation 0.556;
n_win ≥ 3 0.549; per subject only chb15 above chance (0.675, p 0.001). Reading (spec 4.7, "L1 passes,
L2 fails"): weak concentration on annotated channels, far below a fixed anatomical rule, no
seizure-specific information — the same pre-registered negative as A4 (0.5694, L2 −0.1694), now on a
second readout. The demo panel becomes `Channel-level latent anomaly — Event N`, neutral.

### 10.3 Ledger note

`results/p2_ledger.csv` `verdict` records the outcome of each step's own gate, not the final selection:
E20a, E18 (`_ovl`) and P3-L6 read "ADOPTED" but were not chosen (E20a lost on sensitivity, E18d tied →
E18, L6 was not adopted on L2f). This record (6.1, 9.7, 9.7b) is the selection of record.

### 10.4 Normalisation statistics (disclosure)

CHB-MIT inputs of the v2 system (`c1b_build_trainset`, `c1t_build_testset`) are z-scored with
`data/processed/{{subj}}_stats.json`, computed by the inherited preprocessing after excluding annotated
seizure windows and the 4-h post-seizure buffer — for every subject, test included. The detection
system uses no labels, but this normalisation step does. X1 and the web demo use label-free statistics
(every 10th window of the whole recording). Effect on CHB-MIT not measured; a descriptive comparison of
the two sets of statistics on the 8 test patients is an open item (HANDOFF section 9).

### 10.5 Repo state (08/10)

Commit `e13e629`: continuous-evaluation results (look #2 evidence) and the v2 checkpoints; v2 inputs and
large caches gitignored. `results/x1_external/SUMMARY.md` restored from git (it had been deleted in the
working tree). Look #4 evidence (`results/veto_screen*`, `results/oracle_gate_bound/`) committed by
`report_phase_sync` follow-up command. `web_demo/*` changes belong to Project 2.
"""

COR14 = f"""
{MARK}
## 14 · Report phase (2026-10-08; details in PERF_PHASE_RECORD rev. R, section 10)

| correct | what it replaces |
|---|---|
| look #6 subject-mean: seed 42 **0.508**, 4 seeds 0.498 ± 0.010 (`e22_test_oneshot/SUMMARY.md`) | "0.342 (seed 42), subject-mean 0.498" in the record, the instructions, HANDOFF rev 1 and the 08/10 briefing |
| the ledger `verdict` column is each step's gate outcome; E20a, E18 `_ovl` and P3-L6 say ADOPTED but were not chosen | reading the ledger as the final selection |
| the L2 floor 0.0025 cut chb21 (1.75 → 0.50) and chb20 (3.0 → 2.5) on non-test; L2f never lowers a budget below 0.005; the cap 0.02 binds only chb15, on test | "the per-patient budget helps generally" |
| chb24's summary lists only its seizure files; X1 scored every present file (21.3 h). Siena labels come from the SzCORE converter (`epilepsy2bids` d3fb175), which fixes the published typos; a first parser missed 6 seizures and read PN00-3 as 3,660 s | "chb24 = 12 files"; "Siena 40 seizures" |
| CHB-MIT z-score statistics (`stats.json`) exclude annotated seizure and buffer windows, test included; X1 and the demo use label-free statistics | "no label anywhere in the pipeline" |
| both GAE readouts fail the anatomical-prior test of channel attribution (A4 reconstruction 0.5694 / −0.1694; A5 latent 0.5473 / −0.1914) | "the negative is specific to the reconstruction readout" |
| processing time: 9.76 s/h (entry 6) was superseded by 10.83 s/h (earlier demo); the final system's time is measured on the rebuilt demo | quoting 9.76 or 10.83 s/h for the final system |
"""

SPEC_RES = f"""
{MARK}
#### A5 result (2026-10-08, `results/attribution_v8/`, tag `attribution-a5-results`)

L1 macro-AUROC 0.5473 [0.4992, 0.5971], p = 0.018 (pass, weak) · L2 Δ vs prior −0.1914 [−0.2618, −0.1182]
(fail, significantly below) · L3 T = −0.0017, p = 0.53 (fail) · D7 −0.0754 · without chb15 0.4864.
Interpretation row of 4.7: "L1 passes, L2 fails", with "latent anomaly" for "reconstruction anomaly".
The A4 result (section 9.3) stands as the attribution of the earlier reconstruction readout.
"""


def main():
    check_numbers()
    # ---------------- record
    s = read(REC)
    if MARK not in s:
        s = sub1(s, r"\*\*Stage P2 CLOSED; stage P3 opens\.\*\*",
                 "**Performance phase CLOSED (P1–P3, X1); report phase since 2026-10-08 (rev. R, section 10).**", "header")
        s = sub1(s, r"Stage \*\*P1\*\* \(E1–E10\) is CLOSED\. Stage \*\*P2\*\* \(E11 onward\) is running; its log and queue are in §6\.",
                 "Stages **P1** (E1–E10), **P2** (E11–E22) and **P3** (section 9) are CLOSED; external validation X1 in 9.9; "
                 "report-phase decisions and the final-system attribution (A5) in section 10.", "stage line")
        s = sub1(s, r"(decision table \(section 9\)\.)",
                 r"\1 Rev. R (2026-10-08): look-#6 subject-mean by seed (0.508 seed 42, 0.498 4 seeds); X1 hours; "
                 r"section 7 resolved; section 10 (report phase, A5).", "rev Q line")
        s = sub1(s, r"subject-mean 0\.498; short 4/18\. E on the same look",
                 "subject-mean 0.508 (seed 42; 4 seeds 0.498 ± 0.010); short 4/18. E on the same look", "look 6 row")
        lines = s.split("\n")
        ix = [i for i, l in enumerate(lines) if l.startswith("| X1 |")]
        if len(ix) != 1:
            stop("X1 row in section 3")
        lines.insert(ix[0] + 1, "| A5 | 2026-10-08, channel attribution of the final system (`src/attribution_v8.py`, tags "
                     "`attribution-a5-prereg`, `attribution-a5-results`): per-channel latent anomaly against the 76 test "
                     "channel annotations already used by A4; no event metric | section 10.2 |")
        s = "\n".join(lines)
        s = sub1(s, r"## 7 · Decisions open for the supervisor \(08/10\)\n",
                 "## 7 · Decisions for the supervisor meeting (08/10) — RESOLVED, see section 10.1\n\n"
                 "The list below is kept as it was asked.\n", "section 7")
        s = sub1(s, r"of look #6\s+is 0\.498\.", "of look #6 is 0.498 (4-seed mean; seed 42 0.508).", "9.1 look 6")
        s = sub1(s, r"Look #6 \(P2 frozen, 0\.342 @ 22\.2, subject-mean\s+0\.498\)",
                 "Look #6 (P2 frozen, 0.342 @ 22.2, subject-mean 0.508 seed 42; 4 seeds 0.336 / 0.498)", "9.8 look 6")
        s = sub1(s, r"chb24 \(16 seizures, 21\.1 h\)", "chb24 (16 seizures, 21.3 h)", "9.9 chb24 hours")
        s = sub1(s, r"\(14 adult patients, 47 seizures, 140 h\)",
                 "(14 adult patients, 47 seizures, ~141 h by the per-patient hours of the X1 summary)", "9.9 Siena hours")
        s = s.rstrip("\n") + "\n" + SEC10
        s = s.replace("**Rev. P, 2026-10-07**", "**Rev. R, 2026-10-08** (rev. P–Q 2026-10-07)", 1)
        REC.write_text(s, encoding="utf-8"); print("record: rev R written")
    else:
        print("record: already rev R")
    # ---------------- corrections
    c = read(COR)
    if MARK not in c:
        c = sub1(c, r"(## 6 · Processing time is 9\.76 s per hour, and the variance belongs to one stage\n)",
                 r"\1\n> **Superseded (2026-10-08):** the end-to-end figure of record became 10.83 s/h (earlier demo, "
                 r"median of 5 runs); neither applies to the final system (section 14).\n", "entry 6")
        c = c.rstrip("\n") + "\n" + COR14
        COR.write_text(c, encoding="utf-8"); print("corrections: section 14 written")
    else:
        print("corrections: already done")
    # ---------------- spec
    p = read(SPEC)
    if "### A5 (2026-10-08)" not in p:
        stop("A5 amendment missing in ATTRIBUTION_SPEC.md (run attribution_v8.py --write-amendment first)")
    if MARK not in p:
        p = sub1(p, r"(# ATTRIBUTION_SPEC — Channel Attribution \(v4 rev\. B, 2026-09-19 — method LOCKED, results FINAL\))",
                 r"\1 · A5 (final system) 2026-10-08", "spec title")
        p = p.rstrip("\n") + "\n" + SPEC_RES
        SPEC.write_text(p, encoding="utf-8"); print("spec: A5 result written")
    else:
        print("spec: already done")


if __name__ == "__main__":
    main()
