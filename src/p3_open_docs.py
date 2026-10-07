#!/usr/bin/env python
"""
p3_open_docs.py -- open stage P3 in the canonical docs (2026-10-07). Text edits only, no numbers computed.
  docs/PERF_PHASE_RECORD.md   -> rev. Q: header line, section 3 row "P3-T", new section 9 (check of the two
                                 closing P2 results, test-information policy, hypotheses H6-H8, P3-A, decision table)
  docs/VERIFIED_CORRECTIONS.md -> appended section "Stage P2 findings (2026-10-07)"
  docs/PROJECT_INSTRUCTIONS.md -> P3 header, first actions, status pointer, rule 20, files, tags, findings rows
Every edit asserts that its anchor occurs exactly once; the script is idempotent (re-running changes nothing).
Line endings of each file are preserved (CRLF or LF).
Run:  python src/p3_open_docs.py      (seconds)
"""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"


def load(p):
    s = p.read_bytes().decode("utf-8")          # read_text would translate CRLF and hide it
    crlf = "\r\n" in s
    return s.replace("\r\n", "\n"), crlf


def save(p, s, crlf):
    p.write_text(s.replace("\n", "\r\n") if crlf else s, encoding="utf-8", newline="")


def once(s, anchor, new, label):
    n = s.count(anchor)
    if n != 1:
        raise SystemExit(f"STOP {label}: anchor found {n} times: {anchor[:70]!r}")
    return s.replace(anchor, new)


# ----------------------------------------------------------------------------- record rev. Q
REV_Q = (" Rev. Q: stage P3 opened -- checks of the burden table and the 4-seed bootstrap, test-information\n"
         "policy (two tiers), hypotheses H6-H8, P3-A anatomy script, decision table (section 9).")

ROW_P3T = ("| P3-T | 2026-10-07, stage P3, test **information** (not a look at results): (a) `p3_seizure_burden.py` read "
           "the test summaries (counts, durations, ictal minutes); (b) `p3_anatomy.py --include-test`: tier T-A "
           "(label-free test EEG and model outputs) and tier T-B (per-seizure anatomy joined to test annotations), "
           "section 9 | any P3 design motivated by (b) makes look #7 test-informed; it is reported as such |")

SEC9 = r"""
## 9 · Stage P3 (opened 2026-10-07)

Target (author): pooled test sensitivity ≥ 0.50 (38/76, +12 seizures over look #6) at the best FP/day
achievable; sensitivity first. Thesis shape kept: GAE → one scalar ensemble anomaly score → non-parametric
CPD with a measured localization role.

### 9.1 Check of the two closing P2 results

**Burden table** (`results/p3_seizure_burden/burden.txt`; CHB-MIT summaries only, no model output).
- Counts reconcile with the scorer (computed): test 76 annotated = 76 references. Non-test 93 annotated →
  scorer 94 per seed: chb11's 752-s seizure is split into 3 pieces (+2) and two chb12 seizures less than
  90 s apart are merged (−1). This explains the "95 split pieces vs 94" of the E18 diagnostics (that table
  split but did not merge). chb12's summary lists 40 seizures; 13 lie in the skipped files chb12_27/28/29.
  The chb11 seizure is 752 s by annotation; "756 s" elsewhere is its 189 windows.
- Short seizures: < 20 s by annotation — test 23 (chb06 8, chb13 2, chb14 3, chb16 10), non-test 3. The
  scripts' count (`p2_scalars.short_refs`: run of ictal windows × 4 s < 20 s) gives 18 on test because a
  seizure is rounded up to whole windows. Both are reported, labelled.
- Ictal minutes / top-0.5 % budget: chb12 2.91, chb15 2.86, chb08 2.60, chb11 1.47, every other ≤ 0.97.
  H1 is **not confirmed by this table alone**: a seizure is caught by one supra-threshold window inside its
  tolerance span, so ictal time above the budget does not cap sensitivity by itself (chb08, ratio 2.60 with
  5 long seizures, was caught 5/5 even by E — E12 table). The two seizure-rich patients (chb12 26
  references, chb15 20) are the two that fail; budget vs ranking is measured per seizure in P3-A.

**Bootstrap of look #6, 4 seeds** (`results/e22_test_oneshot/BOOTSTRAP.md`): final pooled 0.336
[0.133, 0.670], subject-mean 0.498 [0.226, 0.770]; final − E pooled +0.293 [0.100, 0.609], subject-mean
+0.455 [0.187, 0.724], FP/day −0.95 [−12.0, +5.1]; without chb15 pooled 0.455 [0.240, 0.750].
Consistent with the seed-42 values of §6.1. Reading: with 8 patients the interval of the current system
already contains 0.50; chb15 (20) and chb13 (12) hold 42 % of the test seizures (computed), so the pooled
target is mostly a statement about two patients. The official SzCORE aggregate (subject-mean) of look #6
is 0.498.

### 9.2 Test-information policy for P3 (author decision 2026-10-07)

The author asked to study the test EEG itself (not results), because the 8 test patients are markedly
harder (Part B: seizure peaks out-ranked by 20–50 % of non-ictal spans on test vs ~4 % on non-test).
Two tiers, both logged in §3:
- **T-A, label-free:** test EEG features and model outputs without annotations (input distribution vs the
  training set, flagged share, file drift, the channel owning the score tail). The system is label-free and
  fits each patient on its whole recording, so this is information the system itself sees; it is disclosed.
- **T-B, annotation-guided:** test seizure times joined to scores (per-seizure miss anatomy). Test-informed.

Not done: no sensitivity-vs-FA curve and no threshold choice on test; operating points and gates stay on
the 15 non-test subjects. Any design motivated by T-B makes look #7 test-informed. **Look #6 remains the
clean held-out result in the report; look #7 is reported beside it, labelled test-informed.**
Test facts already known from the attribution study (Chapter 3; the author's blind channel annotation of
the 76 test seizures), counted as T-B: all ten chb06 seizures were annotated generalized; chb15's twenty
are focal (focal test seizures carry 4.55 annotated channels on average), with V1's channel ranking
concentrated on P3-O1.

### 9.3 Hypotheses (extending HANDOFF_P3 §3; H1–H5 unchanged)

- **H6 spatial scale.** The frozen family uses order statistics 6, 9, 12 and the channel mean; a large
  value needs ≥ 6 anomalous channels. Focal seizures with few involved channels (chb15) may stay low.
  Non-test characterisation (E14, before drift correction): S3 0.537, max 0.457, below S9 — but the
  non-test seizures may be broader.
- **H7 input domain shift.** If a test patient's node features fall outside the training distribution,
  the training-set standardisation clips them at ±4 and information is lost.
- **H8 the drift correction absorbs clustered or long seizures.** The ±15 min running median may subtract
  part of a seizure when seizures cluster in time (chb15) or when a file is short.

### 9.4 P3-A — failure anatomy (`src/p3_anatomy.py`, descriptive, no gate)

Part A label-free (T-A) on all 23 subjects: f7 clip share and median shift in training-SD units
(constants recomputed as `train_gae_v2.norm_constants`), flagged share, file drift before/after the
correction, tail share in top-quartile files, channel owning the tail, files with an odd channel.
Part B per seizure (T-B on test): p_need = share of the patient's smoothed values ≥ the seizure's peak over
its SzCORE tolerance span (the top-p a threshold must reach to touch it), for the frozen scalar, the scalar
without the correction, each member and the focal members S1e, S3e; spatial extent; gap to the nearest
seizure; caught or not. Part C (non-test, H2): one LedoitWolf refit per channel without the 5 % most
distant windows. Reproduction gates R0 (scalar = e22), R2 (non-test detector = E17b grid), R3 (test
detector = look #6), R4 (untrimmed refit vs cached distances). Results: §9.6 (written after the run).

### 9.5 Decision table (fixed before any P3-A result)

One construction per lever; a lever runs only if its trigger holds. Counts are 4-seed means.

| lever | hyp. | trigger (from P3-A) | construction |
|---|---|---|---|
| L1 focal member | H6 | test: rescued by S3e at top 0.5 % minus lost ≥ 3 | rank ensemble {S3e, S6e, S9e, S12e, Smean_e}; S3 chosen over S1 a priori (one bad channel owns the max; 3 channels ≈ the mean focal extent) |
| L2 per-patient budget | H1, H3 | ≥ 3 missed test seizures with p_need in (0.005, 0.02] | top-p_i = clip(q_i, 0.0025, 0.02); q_i = share of the patient's smoothed windows where the mean robust-z of the four E16e-corrected members exceeds k; k calibrated once on the 15 non-test patients (seed 42) so that the median q_i = 0.005 — the frozen budget redistributed, not enlarged |
| L3 guarded correction | H8 | test: rescued without the correction minus lost ≥ 3 | running median over ±15 min that ignores values above the file's 90th percentile of that member |
| L4 trimmed fit | H2 | non-test: rescued minus lost ≥ 2, with ≥ 1 on chb12 | per-channel LedoitWolf refit without the 5 % most distant windows; needs a test dump of node latents (`p2_test_dump.py` + latents, est. 15–45 min CPU) |
| L5 per-patient input normalisation | H7 | a test patient with clip share > 5 % on a feature, or median shift > 2 training SD, beyond every training patient | retraining (Kaggle ≈ 3.5 h per seed, 4 accounts in parallel, then dumps); not feasible on 07/10; recorded as a finding, author decides |
| L6 localizer hybrid | H4 | always (non-test evidence exists) | CPD onset + control-2 offset (contiguous run; non-test offset 12 s vs CPD 16 s); events > 300 s keep the detector boundaries |

**Gate for L1–L4** (non-test, 4 seeds, fine grid, D1 cell re-selected at ≤ 25 FA/day; reference = P2
frozen detector E17b 0.668, subject-mean 0.828, `val` 0.983): non-inferiority — pooled ≥ 0.648,
subject-mean ≥ 0.808, `val` ≥ 0.916 — and FA/day ≤ 25. Reason: the non-test set is near its ceiling and
easier (rule 19); a lever aimed at the test failure mechanism can only be required not to damage it there.
L2 has no grid (its budget is the construction): FA/day ≤ 25 and the same non-inferiority. **L6 gate:**
post-localizer sensitivity ≥ detector − 0.005 and median onset/offset errors not worse, one better by ≥ 4 s.
**Combination:** passing levers are combined in table order and the combination re-passes the same gate
once. Then freeze (tag `p3-frozen`) → look #7: 4 seeds, the look-#6 report set, disclosed as
test-informed; expected FP/day ≈ 1.2 × non-test. If no lever triggers or passes, the P2 frozen system stands
(author: the best number is accepted).
**Time arithmetic (estimated, not measured):** P3-A 10–25 min; each cache-only lever 2–6 min; L4 adds a test
latent dump of 15–45 min; look #7 5–15 min. L5 is excluded on 07/10 by its retraining time.
"""

# ----------------------------------------------------------------------------- corrections section
CORR = r"""

## Stage P2 findings (2026-10-07; details in PERF_PHASE_RECORD rev. P–Q)

| correct | what it replaces |
|---|---|
| E14 was **not adopted**: its pre-registered mechanism check failed; the "ADOPTED" line was a coding error (`results/e14_spatial_recruitment/ERRATUM.md`) | "S9 adopted at E14" |
| two validation quantities: `val` (cell re-selected on the 3 validation subjects; every gate G4) and `val_at_cell` (descriptive) — same Eb: 0.800 vs 0.933 | comparing the two as one number |
| the D1 threshold is the quantile over every non-NaN smoothed value (`event_grid`), not over non-signal-loss positions only | the first `p2_scalars` rebuild (stopped E19 by 1 FP) |
| file-level drift is a shift of the latent readout per file (top files carry no more flagged windows and rarely seizures); location-only correction helps, scale correction and short baselines hurt | "drift = more high-amplitude activity" |
| E15 patient fine-tuning is negative in **one** configuration (lr 1e-4, 2,000 steps, all parameters) | "fine-tuning does not work" |
| E19's +0.011 is about one seizure; it caught no extra short seizure | "the short branch works" |
| on E17b, CPD halves the **onset** error; on offset the contiguous-run control (12 s) and multivariate CPD (8 s) beat 1-D CPD (16 s) | "CPD improves both boundaries" |
| non-test: 93 annotated seizures, scorer 94 (chb11 split +2, a chb12 merge −1); the E18 table's 95 pieces lacked the merge | "one-piece mismatch unexplained" |
| "short" (< 20 s) is 23 test seizures by annotation, 18 by whole-window runs (`short_refs`) | mixing the two counts |
| a seizure is caught by one supra-threshold window, so ictal minutes above the top-p budget do not cap sensitivity by themselves (chb08 2.60, caught 5/5 by E) | "chb15 fails because its ictal time exceeds the budget" |
| cache-only steps took 44–317 s on 4 seeds | estimates of 10–70 min (3–10× too high) |
"""

# ----------------------------------------------------------------------------- instructions edits
INSTR = [
    ("> **Rev. 2026-10-07 (P3).** Stage P2 closed;",
     "> **Rev. 2026-10-07 evening (P3 opened).** Record rev. Q §9: checks of the two closing P2 results, the\n"
     "> two-tier test-information policy, hypotheses H6–H8, the failure-anatomy step P3-A and the decision table.\n"
     ">\n> **Rev. 2026-10-07 (P3).** Stage P2 closed;", "header"),
    ("the P2 log (§6) and the ledger `results/p2_ledger.csv`.",
     "the P2 log (§6), the P3 log and decision table (§9) and the ledger `results/p2_ledger.csv`.", "first actions"),
    ("Starting hypotheses H1–H5 and the test-information rule are in `HANDOFF_P3.md` §3.",
     "Hypotheses H1–H8, the two-tier test-information policy and the P3 decision table are in record §9\n"
     "(they extend `HANDOFF_P3.md` §3).", "status"),
    ("the next look is then reported as test-informed.",
     "the next look is then reported as test-informed.\n    In P3, label-free reads of test EEG (tier T-A) and "
     "annotation-guided anatomy (tier T-B) are logged\n    separately (record §9.2); look #6 stays the clean "
     "held-out result in the report.", "rule 20"),
    ("**Performance phase:** `docs/PERF_PHASE_RECORD.md` ·",
     "**Performance phase:** `docs/PERF_PHASE_RECORD.md` · `docs/HANDOFF_P3.md` (P2 code map §5) ·\n"
     "`results/p2_ledger.csv` (every P2/P3 arm) ·", "files"),
    ("`demo-spec-v5` · `e9-test-oneshot` · `perf-p1-closed`.",
     "`demo-spec-v5` · `e9-test-oneshot` · `perf-p1-closed` · `p2-frozen` · `perf-p2-closed`.", "tags"),
    ("| \"CPD improves both boundaries\" |",
     "| \"CPD improves both boundaries\" |\n"
     "| non-test has 93 annotated seizures, the scorer counts 94 (chb11 split +2, a chb12 merge −1) | \"95 pieces vs 94, one unexplained\" |\n"
     "| \"short\" is 23 test seizures by annotation, 18 by whole-window runs | mixing the two counts |\n"
     "| one supra-threshold window catches a seizure; ictal minutes above the top-p budget do not cap sensitivity (chb08 2.60, 5/5 by E) | \"chb15 fails because its ictal time exceeds the budget\" |",
     "findings"),
]


def main():
    p = DOCS / "PERF_PHASE_RECORD.md"; s, c = load(p)
    if "Rev. Q:" in s:
        print("record: rev. Q already present")
    else:
        s = once(s, "); handoff in `docs/HANDOFF_P3.md`.", "); handoff in `docs/HANDOFF_P3.md`." + REV_Q, "record header")
        lines = s.split("\n")
        hit = [i for i, l in enumerate(lines) if l.startswith("| 6 | P2 frozen system (tag `p2-frozen`)")]
        if len(hit) != 1:
            raise SystemExit(f"STOP record section 3: row 6 found {len(hit)} times")
        lines.insert(hit[0] + 1, ROW_P3T)
        s = "\n".join(lines).rstrip("\n") + "\n" + SEC9
        save(p, s, c); print("record: rev. Q written")

    p = DOCS / "VERIFIED_CORRECTIONS.md"; s, c = load(p)
    if "Stage P2 findings (2026-10-07" in s:
        print("corrections: already present")
    else:
        save(p, s.rstrip("\n") + CORR, c); print("corrections: section appended")

    p = DOCS / "PROJECT_INSTRUCTIONS.md"; s, c = load(p)
    if "Rev. 2026-10-07 evening (P3 opened)" in s:
        print("instructions: already updated")
    else:
        for old, new, label in INSTR:
            s = once(s, old, new, f"instructions {label}")
        save(p, s, c); print("instructions: updated")


if __name__ == "__main__":
    main()
