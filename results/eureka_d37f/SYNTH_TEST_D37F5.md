# Synthetic tests of delivery D37F5 (chat D37-F, 22/11/2026)

Delivery D37F5 = PC8b (`DESIGN_PC8B.md`): `src/eur_abl.py` (arms P8d / P8e in `PC1_ARMS`, `VARIANTS`, `PC8_DROP`), the
notebook builder entry `--only EUR_PC8B`, the notebooks `EUR_PC8_d` / `EUR_PC8_e`, the reader `src/eur_pc8b_read.py` and
its synthetic test. Run in the build container from a frozen copy of the repository (main `a16df8a` + the D37F5 files;
the copy was compared file by file with the delivered files after the runs: identical). Library versions as the earlier
D37-F tests (python 3.13, torch CPU, numpy 2.1.3, pandas 2.3.3).

| test | result | measured |
|---|---|---|
| `src/eur_pc8b_synthetic_test.py` (new) | **ALL PASS** — U (unseen / validation sets; the split read with ast; missing VAL → STOP); step 0 = `src/eur_pc8_synthetic_test.py` ALL PASS on the changed `eur_abl.py` (PC8 behaviour unchanged; 2,244 s inside); P1 `EUR_PC8_d` / `_e`: every gate PASS incl. G-pc8cols (kept columns by name = the design), G-pc7reuse (R0 seed 42 only), G-pc7plat, G-pc7rep, G-guard (2 chunks), G-pc7k, G-pc7r0; V0 × 4, R0 × seed 42, arm × 3 seeds on 26 cases; arm dimensions 25 / 7 (P8d) and 12 / 12 (P8e); CPU model in `run_meta`; N1 (non-circular) P8e seed 1 re-trained in the main process with columns chosen by name = the worker's checkpoint exactly, the P8e scalar of chb03 recomputed from `model_cmp_core.node_input` with columns 18–29 cut by numpy and a per-window forward (max abs diff 0.0), parameter counts 3,479 / 2,812 = the formula; R reader gates M-gates, M0, M1, M2, M4, M5, M6, M7 and every table (R1, R5, R6, R1m, R3, R4), the P8c rows = the PC8 run's rows, unseen = 11 patients, R0 − P8c = −(P8c − R0); negative paths NEG1 (G-pc8cols with other P8e columns), NEGB2 (M6), NEGB3 (M7), NEGB4 (M5, another validation set), NEGB5 (edited module → `EUR_PC8_d` refuses to start), NEGB6 (`--p8c` given the P8a run), NEGB7 (M1), NEGB8 (one run twice) | 2,925 s |
| `src/eur_pc6_synthetic_test.py` | **ALL PASS** (PC6 behaviour unchanged) | 1,916 s |
| `src/eur_pc7_synthetic_test.py` | **ALL PASS** (PC7 behaviour unchanged) | 1,374 s |
| `src/eur_pc1_synthetic_test.py` | **ALL PASS** (PC1 behaviour unchanged) | 1,257 s |

**Real-data check of the reader before the runs** (not a test of the synthetic world): `src/eur_pc8b_read.py` on the
committed PC8 runs, with P8a / P8b standing in for P8d / P8e. The first try stopped at M6: the PC8 reading's
`per_subject.csv` differs from the run's by ≤ 3.6e-15 in `nonict_h` (96 of 1,824 P8c rows) — pandas' default csv parser
is not exact on a round trip. M6 now compares float columns to a relative 1e-12 (text and integer columns exactly); then
M-gates, M0, M1, M2, M4, M5, M6, M7 PASS (30 s). The only number used from that check is the premise of `DESIGN_PC8B.md`
§1 (P8c − R0 on the 11 unseen patients, computed).

The three regression tests ran as one chain; the chain reached the container's 2-h limit during the PC1 test (after PC6
and PC7 had passed), so the PC1 test was re-run alone (row above).
