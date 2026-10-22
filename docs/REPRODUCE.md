# REPRODUCE — record of the reproducibility checks (R1, from 2026-10-22)

How to reproduce is in `README.md` section 5. This file records what was actually checked, on which
commit, with which criterion (written before the run) and with what result. Nothing is edited after a
result to make a check pass; a failed check is recorded as it is.

| # | Level (README 5) | Where | Commit | Status |
|---|---|---|---|---|
| 1 | 1 · redraw the report exhibits from committed results | cloud container, fresh clone, new environment | `1638359` | **PASS** (22/10) |
| 2 | 2 · external rerun from raw EDF with the committed checkpoints | author's laptop, fresh clone, new environment | — | pending (prompt `docs/prompts/CC_R1_REPRO.md`) |
| 3 | 4 · retrain one seed from scratch | Kaggle GPU | — | optional, not started |
| — | 3 · rebuild the CHB-MIT test results from EDF | — | — | not done (gates need uncommitted caches, README 5.3) |

---

## Check 1 — redraw the report exhibits from committed results (PASS)

- **Setup:** `git clone https://github.com/Nhanvas/Thesis.git` at `1638359`; new virtual environment with
  only `numpy 2.5.4`, `pandas 3.1.0`, `matplotlib 3.11.2` (Python 3.13.16, Linux cloud container).
  No EEG, no PyTorch, no cache.
- **Criterion (written 2026-10-22T14:26Z, before running):**
  C1 both scripts exit 0 (`ALL GATES PASSED`, `fig14 OK: 4 panels`); C2 every value of the regenerated
  Tables 4, 11–17, 19, 22, 23 (and the chb24 seed line) equals the report's table at the report's
  precision; C3 Figures 11, 12, 13, 14, 16 are written and looked at.
- **Commands and measured runtime:**
  `python src/figures_v8/make_v8_exhibits.py --out ../out` (3.9 s) and
  `python src/figures_v8/fig14_gallery.py --out ../out` (1.8 s).
- **Result:** C1 pass; C3 pass (Figure 12: 4/18, 6/18, 8/9, 13/23, 6/8 by duration bin; Figure 16: chb15
  seizures around the 2 % cap). C2 pass, every value equal, with one display-rounding note:
  chb04 "hours listed" in Table 19 is 156.065 h computed from the summary file; the script prints
  156.06 (round half to even) and the report prints 156.07. Same data; the total 566.43 h is equal in both.

## Check 2 — external rerun from raw EDF (pending)

- **Question:** does a stranger who clones the repository, installs `requirements.txt` and downloads the
  public recordings get the committed external results with the committed checkpoints?
- **Subjects (fixed before the run):** chb24 (21.3 h, 16 seizures), Siena PN10 (18.72 h, 10), PN00
  (3.24 h, 5), PN11 (2.41 h, 1). PN10 repeats the laptop rebuild of 12/10.
- **Criterion (fixed 2026-10-22 before the run, in `src/r1_compare_external.py`):** for each subject, all
  16 rows (2 operating points × 4 seeds × 2 stages): tp equal; |fp difference| ≤ 2; number of seizures
  and skipped files equal; hours within 0.01 h. PASS only if every row passes. Precedent: PN10 on the
  laptop, 12/10: tp 7 = 7, fp 17 vs 18 (seed 42, balanced, localized); the likely cause, not proven, is
  a floating-point difference between library versions (the original run was on Kaggle).
- **Result:** to be written by the laptop run (section below).

## Check 3 — retrain one seed (optional, not started)

GPU training is not bit-reproducible; the criterion will be set before the run (expected: the same
detected seizures within a few events, not identical weights).

## Open items

- **Figure 8 (baseline drift correction):** the script that drew `fig08_drift.png` is not in the
  repository; searched for on the laptop in check 2.
- **Level 3:** the test-set scripts stop at reproduction gates that need score caches of earlier
  stages (not committed, several GB). A clean-clone rebuild of the CHB-MIT test results is not done.
