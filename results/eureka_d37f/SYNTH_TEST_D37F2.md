# Synthetic test of delivery D37F2 (chat D37-F, 22/11/2026)

Delivery D37F2 = the PC8 reading addendum R1m (`DESIGN_PC8.md` §9, written after the runs and before any reading) and
the PC6 design (`DESIGN_PC6.md`). Run in the build container from a frozen copy of the repository (main `e32902b` + the
D37F2 files; compared file by file with the delivered files after the run: identical); library versions as in
`SYNTH_TEST_D37F1.md`; 2 CPU cores.

| test | result | measured |
|---|---|---|
| `src/eur_pc8_synthetic_test.py` (with the R1m check added) | **ALL PASS** — every check of D37F1 plus R1m: in one container every run has G-pc7rep PASS, so the machine-matched control = the control runs' trained seeds (4 here); `r1_machine.csv` holds P8a / P8b / P8c, marked secondary | 2,111 s |

Reader check on the real PC8 outputs (`e32902b`) before delivery, tables not read (output deleted unread): M-gates, M0,
M1, M2, M4 PASS; control N = 16; machine-matched control = the 8 seeds of `pc7_B` for each arm (all three arm runs
G-pc7rep DIFF).
