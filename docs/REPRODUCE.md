# REPRODUCE — record of the reproducibility checks (R1, from 2026-10-22)

How to reproduce is in `README.md` section 5. This file records what was actually checked, on which
commit, with which criterion (written before the run) and with what result. Nothing is edited after a
result to make a check pass; a failed check is recorded as it is.

| # | Level (README 5) | Where | Commit | Status |
|---|---|---|---|---|
| 1 | 1 · redraw the report exhibits from committed results | cloud container, fresh clone, new environment | `1638359` | **PASS** (22/10) |
| 2 | 2 · external rerun from raw EDF with the committed checkpoints | author's laptop, fresh clone, new environment | `5cf5fb2` | **FAIL** (23/10) |
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

## Check 2 — external rerun from raw EDF (FAIL)

- **Question:** does a stranger who clones the repository, installs `requirements.txt` and downloads the
  public recordings get the committed external results with the committed checkpoints?
- **Setup:** `git clone https://github.com/Nhanvas/Thesis.git` at `5cf5fb2`; Windows laptop (Intel Core
  i5-8250U @ 1.60 GHz, 4 cores / 8 threads, ~16 GB RAM, Windows 10.0.19045.5737, 285 GB free on F:).
  New venv, Python 3.11.9, `pip install -r requirements.txt`: torch 2.12.0+cpu, torch_geometric 2.7.0,
  mne 1.12.1, ruptures 1.1.10, timescoring 0.0.7, scikit-learn 1.8.0, numpy 2.4.4, pandas 3.0.3,
  scipy 1.17.1. Measured times: clone 1 m 48 s; venv creation 27 s; `pip install -r requirements.txt`
  10 m 29 s; `r1_x1_win.py run` (all 4 subjects, `--procs 2`) 19 m 27 s. (Between the environment setup
  and the run there was an unmeasured pause while the Siena PN00/PN11 folders were downloaded — see
  deviations below; that pause is not part of the runtime estimate.)
- **Subjects (fixed before the run):** chb24 (16 seizures), Siena PN10 (18.72 h, 10), PN00
  (3.24 h, 5), PN11 (2.41 h, 1). PN10 repeats the laptop rebuild of 12/10. Local/downloaded: PN10 was
  already local; chb24's EDF files were already local but its `chb24-summary.txt` was downloaded
  separately (see deviations); PN00 and PN11 were downloaded whole from PhysioNet (the author
  downloaded these two manually after the agent's automated download kept hitting mid-transfer resets
  from the PhysioNet server). Measured runtime per subject (`r1_x1_win.py run`, labelfree statistics +
  scoring): chb24 21 files, 20.3 h, 356 s (18 s/h); PN10 6 files, 18.7 h, 421 s (23 s/h); PN00 5 files,
  3.2 h, 154 s (47 s/h); PN11 1 file, 2.4 h, 85 s (35 s/h). 0 files skipped for every subject.
- **Criterion (fixed 2026-10-22 before the run, in `src/r1_compare_external.py`):** for each subject, all
  16 rows (2 operating points × 4 seeds × 2 stages): tp equal; |fp difference| ≤ 2; number of seizures
  and skipped files equal; hours within 0.01 h. PASS only if every row passes. Precedent: PN10 on the
  laptop, 12/10: tp 7 = 7, fp 17 vs 18 (seed 42, balanced, localized); the likely cause, not proven, is
  a floating-point difference between library versions (the original run was on Kaggle).
- **Result: FAIL.** 44 / 64 rows pass (`results/r1_repro/COMPARE.md`, reproduced in full below).
  PN00 and PN11 pass every one of their 16 rows; PN10 passes 12/16 (hours, seizures and budget equal on all
  16 rows; the 4 failing rows fail on tp: seed 2 detects 6 instead of 5 and seed 3 detects 5 instead of 6,
  at both operating points and both stages, so the four-seed total is unchanged, 24 = 24 after the
  localizer at the balanced point; max |fp diff| 1; seeds 42 and 1 pass every row); **chb24 passes 0/16** — every chb24 row fails because
  `hours` differs from `hours_ref` by ≈1.0000 h (21.2956 h committed vs 20.2956 h rerun; the
  `top_diff`/`fp_diff` terms are small, within or near tolerance on several rows, e.g. the seed-42
  balanced-localized row below has tp 14 = 14).

  ```
  # R1 check 2 -- external rerun from a clean clone vs committed results/x1_external/

  Criterion: tp equal, |fp diff| <= 2, n_ref and skipped equal, hours within 0.01 h, on every row (2 points x 4 seeds x 2 stages per subject).

  Rows compared: 64; rows passing: 44; VERDICT: FAIL

  Seed 42, balanced point, after the localizer:

  subject  n_ref  tp  tp_new  fp  fp_new   hours  hours_new  top_diff
    chb24     16  14      14  26      24 21.2956    20.2956  0.000037
     PN00      5   5       5   1       1  3.2422     3.2422  0.000343
     PN10     10   7       7  18      18 18.7244    18.7244  0.000000
     PN11      1   1       1   3       3  2.4100     2.4100  0.000000

  Per subject (all 16 rows): rows with tp equal, max |fp diff|, max |budget diff|:

           rows  passing  tp_equal  max_abs_fp_diff  max_abs_budget_diff
  subject
  PN00       16       16        16                0             0.000343
  PN10       16       12        12                1             0.000000
  PN11       16       16        16                0             0.000000
  chb24      16        0         4                7             0.000322
  ```

  Descriptive onset/offset error, balanced point (`errors_*.csv`, median |onset|/|offset|, committed vs
  rerun — all equal except chb24's row count, which differs by one error row):

  | subject | n rows (committed / rerun) | median \|onset\| committed / rerun | median \|offset\| committed / rerun |
  |---|---|---|---|
  | chb24 | 53 / 54 | 4.00 s / 4.00 s | 4.00 s / 4.00 s |
  | PN10  | 24 / 24 | 4.00 s / 4.00 s | 16.00 s / 16.00 s |
  | PN00  | 15 / 15 | 32.00 s / 32.00 s | 4.00 s / 4.00 s |
  | PN11  | 4 / 4   | 4.00 s / 4.00 s | 20.00 s / 20.00 s |

- **Reading (added 23/10 after the result, the verdict is unchanged):** on the three Siena patients,
  whose input files were complete, seed 42 is identical (13 of 16 seizures, 22 false
  alarms, committed and rerun) and the four-seed sums are 43 = 43 seizures with 102 vs 103 false alarms
  (balanced point, after the localizer); the only differences are one borderline seizure in each of two
  seeds of PN10. chb24 cannot be judged from this run, because one of its 22 files was missing from the
  input (below). The criterion asked for identical tp on every row, which this run does not meet.
- **Likely cause of the chb24 FAIL (not proven; not fixed, per the ground rules of
  `docs/prompts/CC_R1_REPRO.md`):** `chb24_08.edf` is confirmed present on PhysioNet (`HEAD` request:
  HTTP 200, 42,399,744 bytes — the same size as the other full-hour chb24 files) but is absent from the
  local dataset copy at `F:/Study/Thesis/Dataset/CHB-MIT/chb24/` (21 of the 22 published files are
  present; `chb24_08.edf` is the one gap). The Step 4 inventory check validates only the total parsed
  seizure count (16, which matched) and did not catch the missing file. Its absence would account for
  almost exactly the observed ≈1.0000 h deficit in every chb24 row, which alone fails the fixed 0.01 h
  tolerance on all 16 rows regardless of tp/fp agreement. The missing file was **not** downloaded and the
  subject was **not** rerun — the ground rules forbid changing the input set or rerunning after seeing a
  result; the FAIL stands as recorded.
- **Deviations from `docs/prompts/CC_R1_REPRO.md`:**
  1. `chb24-summary.txt` was absent from the local dataset even though all of chb24's EDF files were
     present; it was downloaded directly from PhysioNet (2,192 bytes) before the Step 4 inventory check.
     This is not literally the "missing subject" case the prompt describes (download the whole folder)
     but was handled in the same spirit (download the one missing file from PhysioNet, report it here).
  2. PN00 and PN11 were entirely absent locally. The agent's own automated `curl` downloads of these two
     Siena folders repeatedly hit mid-transfer connection resets and HTTP 502s from the PhysioNet server;
     at the author's request the agent stopped its automated retry loops and the author downloaded PN00
     and PN11 manually. All 6 EDF files were then verified byte-exact against PhysioNet's published
     sizes; the two `Seizures-list-*.txt` files differ by a few bytes from the PhysioNet index (PN00:
     1,578 vs 1,534 bytes; PN11: 909 vs 897 bytes), consistent with text line-ending conversion rather
     than corrupted content — not independently verified further.
  3. `chb24_08.edf` missing from the local dataset — see above.
  4. Ground rule 5 (close Chrome, Edge and Cursor before the run) was **not** followed: a post-hoc check
     after the run found Edge and Cursor still running throughout. The run still completed within the
     estimated 20–45 min window (19 m 27 s) using `--procs 2` on ~16 GB RAM, so it is not flagged as a
     likely cause of the chb24 FAIL above, but memory headroom during the run was not as the ground
     rules intended, and this was not caught until after Step 8.
  5. No other deviations: ground rules 1 (no edits under `src/`, `data/`, `results/x1_external/`) and 4
     (no EDF or `features/*.npz` staged) were followed.

## Check 3 — retrain one seed (optional, not started)

GPU training is not bit-reproducible; the criterion will be set before the run (expected: the same
detected seizures within a few events, not identical weights).

## Open items

- **Figure 8 (baseline drift correction), searched for in check 2 (23/10):** the drawing script IS in
  the repository: `src/figures_v6/fig_example_chb03.py` (chb03, seed `clean_seed42`, 9th-largest
  channel member before/after its ±15 min running-median drift correction, over the three consecutive
  files starting at chb03's first seizure-containing file; writes `fig_drift.png`). Two pre-rendered
  copies of the figure were also found: `F:/Study/Thesis/Reports/v8/figures/Fig08_drift.png`
  (2026-10-10, 296,994 bytes) and `F:/Study/Thesis/Defense/inputs/report_figs/Fig08.png` (2026-10-20,
  344,658 bytes). The script was copied unchanged into `../fig08_test/` (only its output paths
  redirected there) and run with `export` in the check-2 environment: it imports and reaches its gate
  logic correctly, then fails with `FileNotFoundError` on `data/testset_v2/chb03.npz` — this file and
  `results/p2_test/chb03.npz` are the uncommitted score caches of Level 3 (README 5.3), neither of which
  exists in a clean clone. So the script could not be run to completion and its PNG could not be
  compared against `Fig08_drift.png` in this check; rebuilding Level 3 from EDF to unblock it is a much
  larger task outside this check's scope. Per the prompt, the script is therefore **not** copied to
  `src/figures_v8/fig08_drift.py` (that copy is conditional on the script running and reproducing the
  figure).
- **Level 3:** the test-set scripts stop at reproduction gates that need score caches of earlier
  stages (not committed, several GB). A clean-clone rebuild of the CHB-MIT test results is not done.
