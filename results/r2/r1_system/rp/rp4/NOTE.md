# rp/rp4 — RP4 on the path-2 model (D21-F 12/11; completed D25-F 14/11)

Missed-seizure / false-alarm analysis of the main model of path 2 (board R190: complete CHB-MIT data without
chb12_27–29; seeds 1–3 = R1 checkpoints, seed 4 = RP1; k per seed), read from `rp/rp2/scores`; no model is run.
Rules: `docs/FUTURE_RESEARCH_PLAN.md` §12 rows 12/11 09:40 and 10:05; first reading row 10:43; completion row 14/11.

- **First run (12/11, D21-F):** `src/r2_rp4.py` (sha16 `df08595b2f550d2d`), container, 279.7 s; the flagged-share part
  did not run because `flags/` arrived afterwards (laptop export of `data/testset_v2/*.npz`, commit `5e9ae8b`; it
  depends on the test data only).
- **Completion (14/11, D25-F):** the same script, unchanged, re-run with `flags/` present (container, 317.1 s; numpy
  2.5.3, pandas 3.0.5, scikit-learn 1.8.0, timescoring 0.0.7). Gate R4.0 PASS again; every table of the first run is
  reproduced byte for byte (`false_alarms.csv` gains the columns `flag_share`, `high_amp`; `fa_summary.csv` gains the
  flag rows; `fa_flags_per_patient_{L2f,frozen}.csv` are new).
- **Secondary analysis of board R175 (14/11, D25-F):** `bw/` — between–within decomposition of the missed-seizure
  association, `src/r2_rp4b.py` (synthetic test `src/r2_rp4b_synthetic_test.py`, 13 / 13 PASS; gates G1, G2 PASS),
  container, 206.9 s.

With R190 (13/11) these are the RP4 numbers of path 2 (report version A2); they enter the report only through
`REPORT_NUMBERS.md` (RP10). The earlier note "history, re-run on the rebuilt model" is void: the rebuild is postponed.
