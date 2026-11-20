# DIAG_PC1 — diagnostics of the PC1 reading (D33-F, 20/11)

Read only, from the committed PC1 outputs (`src/eur_pc1_diag.py`; gate D0 = the per-patient means equal the aggregate's: PASS, 912 rows). CPD stage; every seed pooled for counts.

## 1 · Why 10a has more false alarms (H10a predicted fewer)

Share of windows flagged at the own label-free point (mean over patients and seeds, %):

- development: V0 0.64, R0 0.59, 10a 0.62, 10b 0.60
- test: V0 0.73, R0 0.70, 10a 0.81, 10b 0.68

| set | budget | variant | events | seizures found | false alarms | s per event | flagged time % |
|---|---|---|---|---|---|---|---|
| development | fixed | 10a | 4745 | 142 / 376 | 4603 | 42.0 | 2.05 |
| development | fixed | 10b | 2530 | 238 / 376 | 2292 | 55.1 | 1.44 |
| development | fixed | R0 | 2628 | 234 / 376 | 2394 | 56.0 | 1.51 |
| development | fixed | V0 | 2440 | 249 / 376 | 2191 | 55.9 | 1.41 |
| development | own | 10a | 5859 | 151 / 376 | 5708 | 43.4 | 2.62 |
| development | own | 10b | 2777 | 241 / 376 | 2536 | 55.4 | 1.59 |
| development | own | R0 | 2897 | 240 / 376 | 2657 | 55.5 | 1.66 |
| development | own | V0 | 2857 | 252 / 376 | 2605 | 55.1 | 1.62 |
| test | fixed | 10a | 2009 | 75 / 304 | 1934 | 40.0 | 2.00 |
| test | fixed | 10b | 1207 | 88 / 304 | 1119 | 54.0 | 1.62 |
| test | fixed | R0 | 1284 | 87 / 304 | 1197 | 54.5 | 1.74 |
| test | fixed | V0 | 1207 | 102 / 304 | 1105 | 54.0 | 1.62 |
| test | own | 10a | 2677 | 109 / 304 | 2568 | 44.0 | 2.93 |
| test | own | 10b | 1407 | 129 / 304 | 1278 | 57.9 | 2.02 |
| test | own | R0 | 1543 | 131 / 304 | 1412 | 57.0 | 2.19 |
| test | own | V0 | 1494 | 145 / 304 | 1349 | 57.0 | 2.12 |

## 2 · Training of the retrained arms

| arm | seed | parameters | training windows | first loss | last loss | validation loss |
|---|---|---|---|---|---|---|
| 10a | 1 | 3285 | 270190 | 0.01957 | 0.01729 | 0.02305 |
| 10a | 2 | 3285 | 270190 | 0.01947 | 0.01716 | 0.02296 |
| 10a | 3 | 3285 | 270190 | 0.01934 | 0.01732 | 0.02306 |
| 10a | 42 | 3285 | 270190 | 0.01977 | 0.01734 | 0.02310 |
| 10b | 1 | 3770 | 270190 | 0.01776 | 0.01575 | 0.02114 |
| 10b | 2 | 3770 | 270190 | 0.01763 | 0.01574 | 0.02115 |
| 10b | 3 | 3770 | 270190 | 0.01759 | 0.01575 | 0.02111 |
| 10b | 42 | 3770 | 270190 | 0.01733 | 0.01572 | 0.02106 |
| R0 | 1 | 3964 | 270190 | 0.01815 | 0.01582 | 0.02121 |
| R0 | 2 | 3964 | 270190 | 0.01835 | 0.01583 | 0.02124 |
| R0 | 3 | 3964 | 270190 | 0.01809 | 0.01583 | 0.02122 |
| R0 | 42 | 3964 | 270190 | 0.01796 | 0.01587 | 0.02133 |

## 3 · Sensitivity per seed (per-patient mean, own point, CPD) and without seed 2

| set | variant | seed 42 | seed 1 | seed 2 | seed 3 | all 4 | without seed 2 |
|---|---|---|---|---|---|---|---|
| development | V0 | 0.847 | 0.826 | 0.816 | 0.838 | 0.832 | 0.837 |
| development | R0 | 0.817 | 0.821 | 0.680 | 0.841 | 0.790 | 0.826 |
| development | 10a | 0.516 | 0.503 | 0.536 | 0.495 | 0.513 | 0.505 |
| development | 10b | 0.808 | 0.827 | 0.775 | 0.796 | 0.802 | 0.810 |
| test | V0 | 0.577 | 0.559 | 0.545 | 0.588 | 0.567 | 0.575 |
| test | R0 | 0.495 | 0.562 | 0.408 | 0.511 | 0.494 | 0.523 |
| test | 10a | 0.329 | 0.326 | 0.374 | 0.307 | 0.334 | 0.320 |
| test | 10b | 0.553 | 0.501 | 0.460 | 0.532 | 0.512 | 0.529 |
| chb24 | V0 | 0.875 | 0.812 | 0.812 | 0.875 | 0.844 | 0.854 |
| chb24 | R0 | 0.812 | 0.875 | 0.812 | 0.812 | 0.828 | 0.833 |
| chb24 | 10a | 0.312 | 0.188 | 0.250 | 0.188 | 0.234 | 0.229 |
| chb24 | 10b | 0.812 | 0.875 | 0.438 | 0.688 | 0.703 | 0.792 |
| siena | V0 | 0.771 | 0.569 | 0.655 | 0.586 | 0.645 | 0.642 |
| siena | R0 | 0.669 | 0.664 | 0.583 | 0.767 | 0.671 | 0.700 |
| siena | 10a | 0.535 | 0.535 | 0.539 | 0.665 | 0.568 | 0.578 |
| siena | 10b | 0.663 | 0.548 | 0.515 | 0.568 | 0.574 | 0.593 |
