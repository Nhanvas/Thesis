#!/usr/bin/env python
"""
x1_record.py -- log the external validation X1 (chb24, Siena) in the canonical docs, 2026-10-07.
Numbers copied from results/x1_external/SUMMARY.md and computed from results/x1_external/rows_*.csv
(4-seed means, subject-level bootstrap B = 10,000); comparator rows read from github.com/esl-epfl/szcore
results/<algorithm>/siena.json at commit c57da2f. Idempotent; keeps CRLF/LF.
  docs/PERF_PHASE_RECORD.md  -> section 3 row "X1", section 9.9
  docs/HANDOFF_REPORT.md     -> section 2b (external validation)
Run:  python src/x1_record.py      (seconds)
"""
from pathlib import Path

DOCS = Path(__file__).resolve().parents[1] / "docs"

ROW = ("| X1 | 2026-10-07, external validation of the P3 frozen system on data never used by the thesis: chb24 and "
       "Siena (14 patients), `x1_external.py` (tags `x1-prereg`, `x1-prereg-v2`), one run, no tuning | chb24 seed 42 "
       "14/16 @ 29.5 FP/day; Siena seed 42 33/47 (0.702) @ 44.0, subject-mean 0.748; 4 seeds Siena pooled 0.617, "
       "subject-mean 0.633 @ 41.0. Not a look at the CHB-MIT test set |")

SEC = r"""
### 9.9 External validation X1 (chb24 and Siena; clean, never used before)

**Design.** The P3 frozen system unchanged (code path = `e23_test_look7.evaluate`), run once on CHB-MIT chb24
(outside the 23-subject splits) and the Siena Scalp EEG database (14 adult patients, 47 seizures, 140 h),
pre-registered in `src/x1_external.py` before any of these recordings was processed. Declared, label-free
adaptations: z-score statistics from every 10th window of the whole recording; Siena: 18 bipolar channels
derived from the referential montage, 512 → 256 Hz, notch at 50 Hz. Label sources fixed after a label-only
inventory and before any scoring: chb24 every present file, 21.3 h (its summary lists only the 12 seizure files); Siena
annotations from the SzCORE benchmark's own converter (`esl-epfl/epilepsy2bids` d3fb175, verbatim), which
corrects the published typos (the first parser missed 6 seizures and read PN00-3 as 3,660 s). Gates before
scoring: R-feat (chb03 file rebuilt on Kaggle: f7/bp5 exact, 0.045 % adjacency entries differ) and R-model
(distances within 3e-6 relative; look #7 reproduced for chb03, 4 seeds). Runtime 29 min (Kaggle CPU).

**Results (balanced point, after the CPD localizer).**

| set | seed 42 | 4 seeds pooled | 4 seeds subject-mean (official) | onset / offset (CPD) |
|---|---|---|---|---|
| chb24 (16 seizures, 21.1 h) | 14/16 = 0.875 @ 29.5 FP/day, precision 0.350, F1 0.500 | 0.828 ± 0.060 @ 28.4 | (one subject) | 4 / 4 s (n = 53) |
| Siena (47 seizures, 140 h) | 33/47 = 0.702 @ 44.0, subject-mean 0.748 @ 41.5 | 0.617 ± 0.060 @ 43.8 | sens 0.633 ± 0.079, precision 0.160, F1 0.226, 41.0 FP/day | 20 / 28 s (n = 116) |

Siena subject-level bootstrap (4-seed means): subject-mean sensitivity [0.477, 0.777], pooled [0.495, 0.726],
FP/day [32.3, 53.9] (computed). The descriptive sensitivity point adds no seizure on chb24 (budget 0.0107 above
its floor) and +1 on Siena seed 42 at +2.7 FP/day. Siena per patient (seed 42): 0/3 PN05, 1/3 PN09, 1/3 PN13;
FP/day above 70 in PN06, PN07, PN16.

**Comparator on the same data (SzCORE benchmark, `esl-epfl/szcore` results/*/siena.json, commit c57da2f,
subject-mean).** DynaSD (the only unsupervised entry): sensitivity 0.664, precision 0.126, F1 0.170, 77.7
FP/day. Ours (4-seed mean): 0.633, 0.160, 0.226, 41.0 FP/day — similar sensitivity at about half the false
alarms. Supervised entries range from 0.29 to 1.00 sensitivity (e.g. Zhu 2023 0.674 / 15.3 FP/day; EventNet
0.587 / 8.2; SeizureTransformer 0.685 / 1.0, trained on other corpora). Caveats: same annotations and the
same scoring definitions, but our own scorer implementation and our own signal path (the benchmark feeds the
BIDS-converted recordings to each algorithm); not run inside the benchmark.

**Reading.** On data never seen during any design step, the frozen system detects 83 % of chb24's and 62–70 %
of Siena's seizures (adult patients; the GAE was trained on children), at 28 and 41–44 FP/day. The CHB-MIT
test patients are the hard case (look #6 0.342, look #7 0.487); the external sets indicate that the method
generalises, while the false-alarm rate on Siena is above the 40 FP/day level flagged for the test look.
This is the clean held-out evidence for the final system; it does not replace looks #6 and #7.
"""

HAND = r"""
## 2b · External validation (clean; record 9.9)

| set | seed 42 | 4 seeds | comparator, same data (SzCORE benchmark) |
|---|---|---|---|
| chb24 (16 seizures) | 14/16 (0.875) @ 29.5 FP/day | 0.828 @ 28.4 | — |
| Siena (14 patients, 47 seizures) | 33/47 (0.702) @ 44.0; subject-mean 0.748 | subject-mean 0.633, F1 0.226 @ 41.0 | DynaSD (unsupervised) 0.664, F1 0.170 @ 77.7 |

Report it as external validation of the final system on unseen patients (adults for Siena), with the
caveats of record 9.9 (own scorer implementation and signal path; label-free z-score statistics).
"""


def load(p):
    s = p.read_bytes().decode("utf-8")
    return s.replace("\r\n", "\n"), "\r\n" in s


def save(p, s, crlf):
    p.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")


def main():
    p = DOCS / "PERF_PHASE_RECORD.md"; s, c = load(p)
    if "### 9.9 External validation X1" in s:
        print("record: 9.9 already present")
    else:
        lines = s.split("\n")
        hit = [i for i, l in enumerate(lines) if l.startswith("| 7 | P3 frozen system")]
        if len(hit) != 1:
            raise SystemExit(f"STOP: section 3 row 7 found {len(hit)} times")
        lines.insert(hit[0] + 1, ROW)
        save(p, "\n".join(lines).rstrip("\n") + "\n" + SEC, c); print("record: row X1 and 9.9 written")
    p = DOCS / "HANDOFF_REPORT.md"; s, c = load(p)
    if "## 2b · External validation" in s:
        print("handoff: already present")
    else:
        anchor = "## 3 · Disclosures the report must carry"
        if s.count(anchor) != 1:
            raise SystemExit("STOP: handoff anchor missing")
        save(p, s.replace(anchor, HAND.strip("\n") + "\n\n" + anchor), c); print("handoff: 2b written")


if __name__ == "__main__":
    main()
