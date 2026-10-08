#!/usr/bin/env python
"""
refs_sync_1008.py -- report phase, reference verification (2026-10-08).

Installs the verified reference sheet and the benchmark check, and corrects three statements in the
source-of-truth docs that the verification proved wrong. Run from the repo root (F:/Study/Thesis/Code):

    python src/refs_sync_1008.py --stage ../Agent/refs_1008            # dry run: checks only
    python src/refs_sync_1008.py --stage ../Agent/refs_1008 --apply    # write

Fail-fast: every check runs before any write; nothing is written if one fails.
Inputs (staged): Thesis_Reference_Sheet.md (new), BENCHMARK_CHECK_szcore_c57da2f.md.
Edits:
  docs/Thesis_Reference_Sheet.md      replaced (old content must hash to 7a7d5aea50db..., LF-normalised)
  docs/BENCHMARK_CHECK_szcore_c57da2f.md  added
  docs/PERF_PHASE_RECORD.md           9.9: "SeizureTransformer ... trained on other corpora" corrected
  docs/HANDOFF_REPORT.md              section 7 (unverified leads) replaced by a pointer + corrections
  docs/VERIFIED_CORRECTIONS.md        section 15 appended
"""
import argparse, hashlib, os, re, sys

ap = argparse.ArgumentParser()
ap.add_argument("--stage", required=True)
ap.add_argument("--apply", action="store_true")
a = ap.parse_args()

def rd(p):
    with open(p, "r", encoding="utf-8", newline="") as f:
        return f.read()

def wr(p, s):
    with open(p, "w", encoding="utf-8", newline="") as f:
        f.write(s)

def eol(s):
    return "\r\n" if "\r\n" in s else "\n"

def sha(s):
    return hashlib.sha256(s.replace("\r\n", "\n").encode("utf-8")).hexdigest()

fail = []
def need(cond, msg):
    if not cond:
        fail.append(msg)

SHEET, BENCH = "docs/Thesis_Reference_Sheet.md", "docs/BENCHMARK_CHECK_szcore_c57da2f.md"
REC, HAND, CORR = "docs/PERF_PHASE_RECORD.md", "docs/HANDOFF_REPORT.md", "docs/VERIFIED_CORRECTIONS.md"
new_sheet_p = os.path.join(a.stage, "Thesis_Reference_Sheet.md")
bench_p = os.path.join(a.stage, "BENCHMARK_CHECK_szcore_c57da2f.md")

for p in [SHEET, REC, HAND, CORR, new_sheet_p, bench_p]:
    need(os.path.isfile(p), "missing: " + p)
if fail:
    print("STOP\n" + "\n".join(fail)); sys.exit(1)

old_sheet, new_sheet, bench = rd(SHEET), rd(new_sheet_p), rd(bench_p)
need(sha(old_sheet).startswith("7a7d5aea50db"), "docs sheet is not the expected base (sha %s)" % sha(old_sheet)[:12])
need(sha(new_sheet).startswith("f482a99f1ca2"), "staged sheet is not the delivered file (sha %s)" % sha(new_sheet)[:12])
need("K3" in new_sheet and "Group M (M1" in new_sheet, "staged sheet lacks groups K-M")

# --- record 9.9 ------------------------------------------------------------
rec = rd(REC)
OLD_REC = "SeizureTransformer 0.685 / 1.0, trained on other corpora)"
NEW_REC = ("SeizureTransformer 0.685 / 1.0, which declares Siena among its training data and is therefore not "
           "an out-of-sample comparator; corrected 2026-10-08, VERIFIED_CORRECTIONS 15)")
need(rec.count(OLD_REC) == 1, "record: expected 1 occurrence of the SeizureTransformer sentence, found %d" % rec.count(OLD_REC))

# --- handoff section 7 -----------------------------------------------------
hand = rd(HAND)
m7 = re.search(r"## 7 · Literature leads.*?(?=## 8 · )", hand, re.S)
need(m7 is not None, "handoff: section 7 or 8 header not found")
E = eol(hand)
SEC7 = E.join([
    "## 7 · Literature (verified 2026-10-08)",
    "",
    "The leads that stood here were checked against online full text, abstracts, Crossref and the cloned",
    "benchmark repository; the results are groups K, L and M of `docs/Thesis_Reference_Sheet.md` (flags 6–10).",
    "Corrections to the old leads: Karpov et al. is 2022 and does not say that artifacts and seizures are both",
    "rare high-amplitude peaks (M4); the ICASSP 2024 paper is Hassan et al., metadata only (M5); the Frontiers in",
    "Neuroinformatics 2026 paper (Yin & Yin, M3) excluded chb06, chb12 and chb16; under that exclusion our seed-42",
    "rows would also drop chb12, which is not a test patient, so the computed 33/56 and 22/56 stand; ScoreNet has",
    "one DOI, 10.1109/TNSRE.2021.3129467 (M6); the IRBM 2019 abstract gives 6.3 s onset / −1.17 s offset latency (M7);",
    "the DynaSD preprint (K4) has no CHB-MIT or Siena number — those come from the benchmark (K3).",
    "Benchmark training data (flag 6): SeizureTransformer and five other Siena entries trained on Siena;",
    "DynaSD was tuned on a CHB-MIT subset. Not identified, not cited: NeuroAdapt-Bench 2026, Tress et al. 2021,",
    "the persistent-homology paper, the Sci Rep 2024 chb06-duration paper.",
    "", ""])

# --- corrections section 15 ------------------------------------------------
corr = rd(CORR)
need("## 15 · Reference verification" not in corr, "corrections: section 15 already present")
C = eol(corr)
SEC15 = C.join([
    "",
    "## 15 · Reference verification (2026-10-08; details in `Thesis_Reference_Sheet.md` groups K–M, flags 6–10)",
    "",
    "- **Benchmark training data.** `datasets` in `esl-epfl/szcore` algorithm cards means training data. SeizureTransformer",
    "  (0.685 @ 0.99 on Siena) declares Siena as training data — not \"trained on other corpora\" (record 9.9 and the",
    "  08/10 briefing were wrong). Five more Siena entries are in-sample. DynaSD declares CHB-MIT (hyperparameters tuned",
    "  on a subset), so its CHB-MIT row is not out-of-sample; its Siena row is.",
    "- **DynaSD's paper** (Ojemann et al., medRxiv 2026, method NDD) reports no CHB-MIT, Siena or SzCORE number; its",
    "  threshold is tuned on labelled intracranial data. Benchmark numbers are cited to the repository.",
    "- **The \"RF / Transformer / XGBoost CHB-MIT\" rows** are Table 2 of the SzCORE arXiv preprint (v1–v3), not the",
    "  Epilepsia paper; the Transformer 76.5 % / 40.6 FP/day is TUH.",
    "- **Ingolfsson et al. 2024:** 22.9 → 1.0 FP/h is TUAR artifact data through the CHB-MIT-trained detector, not a",
    "  CHB-MIT false-alarm reduction.",
    "- **Ali et al. 2024** is supervised, leave-one-subject-out, Random Forest, ≥ 70 % coverage, events ≤ 10 s dropped,",
    "  4.79 false detections/h (LOO).",
    "- **Search-lead errors:** Karpov et al. is 2022; the ICASSP 2024 paper is Hassan et al.; the 2026 Frontiers paper",
    "  excluded three cases (chb06, chb12, chb16); the ScoreNet Neural Networks DOI is an unrelated paper; IRBM 2019",
    "  abstract gives 6.3 s / −1.17 s, not 3.9 s / 49.26 s; the CEP 2026 paper's title differs and it is supervised.",
    "- **Siena hours:** PhysioNet states about 128 h; our X1 summary sums to about 140 h (open item).",
    ""])

if fail:
    print("STOP\n" + "\n".join(fail)); sys.exit(1)

print("checks passed")
if not a.apply:
    print("dry run: nothing written (add --apply)"); sys.exit(0)

wr(SHEET, new_sheet)
wr(BENCH, bench)
wr(REC, rec.replace(OLD_REC, NEW_REC))
wr(HAND, hand[:m7.start()] + SEC7 + hand[m7.end():])
wr(CORR, corr.rstrip("\r\n") + C + SEC15)
for p in [SHEET, BENCH, REC, HAND, CORR]:
    print("%-45s %s" % (p, sha(rd(p))[:12]))
print("done")
