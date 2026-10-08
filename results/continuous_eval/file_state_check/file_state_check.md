# File-state check

## 1. Share of windows flagged by the +-5 SD rule, per file

| subject | files | median share | files > 50 % | files > 90 % | files < 10 % |
|---|---|---|---|---|---|
| chb10 | 25 | 0.24 | 4 | 0 | 7 |
| chb11 | 31 | 0.48 | 14 | 0 | 1 |
| chb22 | 31 | 0.66 | 19 | 2 | 1 |
| chb03 | 38 | 0.38 | 14 | 2 | 6 |
| chb06 | 18 | 0.59 | 13 | 0 | 0 |
| chb13 | 33 | 0.40 | 14 | 6 | 0 |
| chb14 | 26 | 0.32 | 4 | 0 | 1 |
| chb15 | 40 | 0.35 | 15 | 1 | 2 |
| chb16 | 19 | 0.59 | 11 | 0 | 1 |
| chb17 | 21 | 0.46 | 9 | 0 | 0 |
| chb18 | 36 | 0.55 | 18 | 1 | 3 |

## 2. Fused score (equal weights), validation, non-ictal and non-buffer windows

| subject | eta^2 between files | corr(file mean score, file flagged share) |
|---|---|---|
| chb10 | 0.181 | 0.880 |
| chb11 | 0.158 | 0.741 |
| chb22 | 0.228 | 0.763 |

## 3. Rolling baseline (450 windows, centered), validation

         variant  window_auroc_all  a8_tp  a8_sens  a8_fa_day         a8_cell  fixed_tp  fixed_fa_day
           equal             0.816      5    0.333     24.991  m75/p5.0/mg300        11        96.518
   equal_detrend             0.728      4    0.267     17.235 m65/p10.0/mg300         9        90.270
no_recon_detrend             0.756      4    0.267     17.451 m65/p10.0/mg300         7        84.238

A8 rule: highest pooled sensitivity with pooled FA/day <= 25. 15 reference events: one or two matched events is within noise. Nothing here is selected on a test patient.