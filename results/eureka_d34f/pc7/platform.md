# PC7 — machine check (descriptive, added after the reading)

Written after G-pc7rep of EUR_PC7_B came back DIFF (same library versions, different training arithmetic); not part of the reading rule of `DESIGN_PC7.md`. Two-sided permutation test of the difference of group means (20,000 relabellings).

Training speed (ms per step, from the checkpoints' _DONE.json):

| machine group | seeds | ms per step |
|---|---|---|
| A + PC1 (G-pc7rep PASS) | 12 | 5.14–5.74 |
| B (G-pc7rep DIFF) | 8 | 7.87–8.12 |

| set | metric | A + PC1 mean (n) | B mean (n) | B − (A + PC1) | permutation p |
|---|---|---|---|---|---|
| development | sens | 0.807 (12) | 0.790 (8) | -0.017 | 0.378 |
| development | f1 | 0.227 (12) | 0.220 (8) | -0.006 | 0.400 |
| development | fa | 22.9 (12) | 22.9 (8) | -0.001 | 0.999 |
| test | sens | 0.522 (12) | 0.510 (8) | -0.012 | 0.621 |
| test | f1 | 0.162 (12) | 0.159 (8) | -0.003 | 0.696 |
| test | fa | 29.7 (12) | 29.6 (8) | -0.120 | 0.848 |
| chb24 | sens | 0.823 (12) | 0.781 (8) | -0.042 | 0.393 |
| chb24 | f1 | 0.496 (12) | 0.490 (8) | -0.006 | 0.768 |
| chb24 | fa | 27.3 (12) | 25.3 (8) | -2.081 | 0.207 |
| siena | sens | 0.650 (12) | 0.646 (8) | -0.003 | 0.915 |
| siena | f1 | 0.221 (12) | 0.229 (8) | +0.008 | 0.326 |
| siena | fa | 41.6 (12) | 39.4 (8) | -2.193 | 0.098 |
