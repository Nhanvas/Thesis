# CC_R1_CHECK2B — chb24 with its complete input (R1, written 2026-10-23)

You are Claude Code on the author's laptop. Check 2 (`docs/REPRODUCE.md`) FAILED; chb24 could not be
judged because `chb24_08.edf` was missing from the input (20.2956 h instead of 21.2956 h). This is
**check 2b**: the same subject, the same code and the same criterion, with the complete input. Check 2
stays recorded as FAIL; check 2b is a separate record. Nothing else is rerun.

**Estimated runtime (not measured):** download 42 MB, then about 6–8 min for the run (chb24 took 356 s in
check 2 with 21 files). Close Edge, Chrome and Cursor before step 3.

## Pre-registration (fixed now, before the run; never changed after)

- Subject: chb24 only, all 22 files. Code: the clone at `F:/Study/Thesis/repro_R1/Thesis`, after
  `git pull --ff-only` (no file under `src/`, `data/` or `results/x1_external/` is edited).
- Criterion: unchanged, `src/r1_compare_external.py` (16 rows; tp equal; |fp diff| ≤ 2; seizures and
  skipped equal; hours within 0.01 h). PASS only if all 16 rows pass.
- A FAIL is recorded as it is. No further rerun.

## Steps

1. `cd /f/Study/Thesis/repro_R1/Thesis && source ../venv/Scripts/activate && git pull --ff-only`
   (STOP if the pull is not a fast-forward).
2. Download `https://physionet.org/files/chbmit/1.0.0/chb24/chb24_08.edf` into the chb24 folder used in
   check 2 (the one under `--data`). Check its size is 42,399,744 bytes; if PhysioNet's `SHA256SUMS.txt`
   for chbmit can be fetched, check its sha256 too. Then list the folder: there must be 22
   `chb24_*.edf` files plus `chb24-summary.txt`; else STOP.
3. Set the committed chb24 rows aside, run, keep the rerun, restore:
   ```bash
   mkdir -p results/r1_repro_2b/committed results/r1_repro_2b/rerun
   cp results/x1_external/rows_chb24.csv results/x1_external/errors_chb24.csv results/r1_repro_2b/committed/
   rm results/x1_external/rows_chb24.csv results/x1_external/errors_chb24.csv
   rm -f results/x1_external/features/chb24.npz      # the 21-file feature cache of check 2 must not be reused
   ( time python src/r1_x1_win.py run --data <same --data folder as check 2> --subjects chb24 --procs 2 ) 2>&1 | tee results/r1_repro_2b/run.log
   cp results/x1_external/rows_chb24.csv results/x1_external/errors_chb24.csv results/r1_repro_2b/rerun/
   git checkout -- results/x1_external/
   python src/r1_compare_external.py --ref results/r1_repro_2b/committed --new results/r1_repro_2b/rerun --out results/r1_repro_2b
   ```
   The log must show `chb24: 22 files (0 skipped`; else STOP.
4. Record in `docs/REPRODUCE.md`: add a row `2b` to the status table and a section "Check 2b — chb24 with
   its complete input" after check 2 (download, file count, measured runtime, the whole COMPARE.md,
   verdict). Do not change the text of check 2.
5. Commit with explicit paths and push, then update the working copy:
   ```bash
   git add docs/REPRODUCE.md results/r1_repro_2b/COMPARE.md results/r1_repro_2b/compare.csv results/r1_repro_2b/run.log \
     results/r1_repro_2b/committed/*.csv results/r1_repro_2b/rerun/*.csv
   git commit -m "R1 check 2b: chb24 rerun with its complete input (22 files) vs committed results"
   git push origin main && git -C /f/Study/Thesis/Code pull --ff-only
   ```
6. Print the verdict line, the seed-42 table and the commit hash. No handback file needed.
