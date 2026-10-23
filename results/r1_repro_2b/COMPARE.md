# R1 check 2 -- external rerun from a clean clone vs committed results/x1_external/

Criterion: tp equal, |fp diff| <= 2, n_ref and skipped equal, hours within 0.01 h, on every row (2 points x 4 seeds x 2 stages per subject).

Rows compared: 16; rows passing: 16; VERDICT: PASS

Seed 42, balanced point, after the localizer:

```
subject  n_ref  tp  tp_new  fp  fp_new   hours  hours_new  top_diff
  chb24     16  14      14  26      25 21.2956    21.2956       0.0
```

Per subject (all 16 rows): rows with tp equal, max |fp diff|, max |budget diff|:

```
         rows  passing  tp_equal  max_abs_fp_diff  max_abs_budget_diff
subject                                                               
chb24      16       16        16                1             0.000052
```
