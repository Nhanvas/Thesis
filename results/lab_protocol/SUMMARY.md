# Laboratory evaluation protocol -- SUMMARY

docs/CC_PROMPT_LAB_PROTOCOL.md (pre-registered 2026-10-01, committed alone before this ran). Real continuous timeline, no reconstruction, no resampling; two declared conventions (detector-side masking, evaluation-side post-ictal don't-care) on top of the cached Scope T (Amendment A2) fused scores -- separate from, and never merged with, the application's deployment evaluation (src/app_val_op.py).

wall-clock time: 11.3 min

## Step A -- validation grid + operating-point selection

8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = 96 cells, scored pooled across chb10, chb11, chb22 (`stepA_grid.csv`, 384 rows).

**Amendment A8 rule (reported result):** maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; ties by lower FA/day, then lower penalty.

- mag_pct = 80, pen_mult = 10, merge_s = 90
- pooled: sensitivity=1.0000 precision=0.4412 f1=0.6122 FA/day=7.57 seizures=15 detected=15 false_alarms=19

**Information only (sensitivity == precision):**

- mag_pct = 80, pen_mult = 10, merge_s = 90
- pooled: sensitivity=1.0000 precision=0.4412 f1=0.6122 FA/day=7.57

## Step B -- test, scored ONCE at the Amendment A8 point

No other test point is computed or reported. Nothing chosen after this step is seen.

```
        subject  seizures  detected  false_alarms  sensitivity  precision       f1  fp_per_day  median_latency_s  n_latency  recorded_hours  seizure_hours  dontcare_hours  masked_hours  denom_hours
          chb03         7         7             6     1.000000   0.538462 0.700000    7.533132              -8.0          7         38.0011         0.1178          4.1111       14.6567      19.1156
          chb06        10         9             7     0.900000   0.562500 0.692308    7.626349              32.0          9         66.7333         0.0500         13.8800       30.7744      22.0289
          chb13        12         6             8     0.500000   0.428571 0.461538   13.877289              -4.0          6         33.0000         0.1600          4.8133       14.1911      13.8356
          chb14         8         1             4     0.125000   0.200000 0.153846    6.178932             -12.0          1         26.0000         0.0544          3.0000        7.4089      15.5367
          chb15        20        15             7     0.750000   0.681818 0.714286    8.880536               8.0         15         40.0089         0.5722          9.0211       11.4978      18.9178
          chb16        10         7             6     0.700000   0.538462 0.608696   20.161792               0.0          7         19.0000         0.0311          3.9356        7.8911       7.1422
          chb17         3         3             4     1.000000   0.428571 0.600000    9.851767              20.0          3         21.0067         0.0822          0.5800       10.6000       9.7444
          chb18         6         5             6     0.833333   0.454545 0.588235    8.725510              -8.0          5         35.6333         0.0922          2.5767       16.4611      16.5033
         POOLED        76        53            48     0.697368   0.524752 0.598870    9.379240               4.0         53        279.3833         1.1600         41.9178      113.4811     122.8244
POOLED_no_chb17        73        50            44     0.684932   0.531915 0.598802    9.338521               4.0         50        258.3767         1.0778         41.3378      102.8811     113.0800
```

## Step C -- window-level macro AUROC on test

- lab-protocol conventions (negatives = non-ictal, not masked, not don't-care): **0.8109**
- all-windows (no exclusions, recomputed fresh from the same cache): **0.6208** (docs cite 0.621)

Per subject in `stepC_auroc.csv`.

## Step D -- cost of masking (test)

0/76 test seizures have at least one masked window; 0/76 are entirely masked.

```
subject  n_seizures  n_any_masked_window  n_entirely_masked
  chb03           7                    0                  0
  chb06          10                    0                  0
  chb13          12                    0                  0
  chb14           8                    0                  0
  chb15          20                    0                  0
  chb16          10                    0                  0
  chb17           3                    0                  0
  chb18           6                    0                  0
 POOLED          76                    0                  0
```
