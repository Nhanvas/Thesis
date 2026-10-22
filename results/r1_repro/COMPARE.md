# R1 check 2 -- external rerun from a clean clone vs committed results/x1_external/

Criterion: tp equal, |fp diff| <= 2, n_ref and skipped equal, hours within 0.01 h, on every row (2 points x 4 seeds x 2 stages per subject).

Rows compared: 64; rows passing: 44; VERDICT: FAIL

Seed 42, balanced point, after the localizer:

```
subject  n_ref  tp  tp_new  fp  fp_new   hours  hours_new  top_diff
  chb24     16  14      14  26      24 21.2956    20.2956  0.000037
   PN00      5   5       5   1       1  3.2422     3.2422  0.000343
   PN10     10   7       7  18      18 18.7244    18.7244  0.000000
   PN11      1   1       1   3       3  2.4100     2.4100  0.000000
```

Per subject (all 16 rows): rows with tp equal, max |fp diff|, max |budget diff|:

```
         rows  passing  tp_equal  max_abs_fp_diff  max_abs_budget_diff
subject                                                               
PN00       16       16        16                0             0.000343
PN10       16       12        12                1             0.000000
PN11       16       16        16                0             0.000000
chb24      16        0         4                7             0.000322
```
