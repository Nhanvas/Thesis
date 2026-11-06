# R0_SMOKE outputs (Kaggle version 1, 06/11/2026, r2_core sha 634dc095)

- Files here are the ones downloaded by the author; `inventory.csv`, the PhysioNet `SHA256SUMS` copies and `logs/`
  stay in the Kaggle output of that version.
- `run_meta.json` has no runtime: the END cell did not run (bug in `projection()`, fixed in sha 7191ad11; plan §12
  06/11 18:40). Elapsed time from the last log line: **28.5 min** (notebook start to the end of the PN00 cell).
- `projection.json` holds `"split_R0_CHB": "False"` as a string (same bug); its numbers are computed estimates.
