# Synthetic tests of delivery D37F1 (chat D37-F, 21/11/2026)

Run in the build container from a frozen copy of the repository (main `69bb08a` + the D37F1 files; the copy was compared
file by file with the delivered files after the runs: identical). Library versions as Kaggle's PC7 runs: python 3.13.18,
torch 2.11.0, torch_geometric 2.7.0, numpy 2.1.3, scipy 1.16.3, scikit-learn 1.6.1, pandas 2.3.3, mne 1.13.2; 2 CPU
cores. Notebooks pin `eur_abl.py` sha256 `428c16c0456333db`.

| test | result | measured |
|---|---|---|
| `src/eur_pc8_synthetic_test.py` (new) | **ALL PASS** — U (two-level bootstrap on a known world, wording rule); P0 reference EUR_PC1_R0; C control EUR_PC7_A / _B + the PC7 reading; P1 EUR_PC8_a / _b / _c: every gate PASS incl. G-pc8cols, G-pc7reuse (R0 seed 42 only), G-pc7plat, G-pc7rep, G-guard (2 chunks), G-pc7k, G-pc7r0; V0 × 4, R0 × seed 42, arm × 3 seeds on 26 cases; arm dimensions 25 / 7, 28 / 10, 7 / 7; CPU model in `run_meta`; N1 (non-circular) P8a seed 1 re-trained with columns chosen by name = the worker's checkpoint exactly, P8c scalar recomputed from the training construction (max abs diff 0.0), parameter counts; R reader gates M0 / M1 / M2 / M4 and every table, merged control rows = the control runs' rows; negative paths NEG1 (columns, seed 42), NEG2 (M1), NEG3 (M0), NEG4 (M4), NEG5 (edited module), NEG6 (one run per arm) | 1,638 s |
| `src/eur_pc7_synthetic_test.py` (unchanged test, changed `eur_abl.py`) | **ALL PASS** (PC7 behaviour unchanged) | 986 s |
| `src/eur_pc1_synthetic_test.py` (unchanged test, changed `eur_abl.py`) | **ALL PASS** (PC1 behaviour unchanged; its A0 is "reported only" in test mode by design) | 931 s |

Found and fixed during development (before the final runs): the reader used `DataFrame.diff` (a method) instead of the
column `"diff"`; gate M4 compared against PC7's q5 with a control seed set that differed from PC7's primary set in a
pooled world — the control is now PC7's primary seed list (`pc7/gates.json`), on the real data the 16 new seeds.
