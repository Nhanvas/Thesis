# Laboratory evaluation protocol -- SUMMARY v2

docs/CC_PROMPT_LAB_PROTOCOL.md (pre-registered 2026-10-01, committed alone before this ran). Real continuous timeline, no reconstruction, no resampling; two declared conventions (detector-side masking, evaluation-side post-ictal don't-care) on top of the cached Scope T (Amendment A2) fused scores -- separate from, and never merged with, the application's deployment evaluation (src/app_val_op.py).

**Correction applied (see `step_d_verification.csv`):** the first run's cached is_artifact mask exempted every ictal window from the +-5 SD check -- src/continuous_eval.py's `compute_artifact_flags` skips the test entirely (`if wl[i] or wb[i]: continue`) for any ictal or buffer window, leaving its flag at the array default `False` regardless of true amplitude. This run recomputes that flag for every ictal window (same rule, threshold, and per-window filtering, read directly from the EDFs) and reruns Steps A-D with it folded into is_artifact. The original `SUMMARY.md` and its CSVs are unchanged.

Ictal windows flagged: 1220 (`step_d_verification.csv` has the per-subject breakdown). FA/day denominators are identical to v1 -- ictal windows are always subtracted via seizure time regardless of masking status (see `load_subject_data`'s own comment), so `denominators.csv` is not rerun.

wall-clock time: 11.7 min

## Step A -- validation grid + operating-point selection

8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = 96 cells, scored pooled across chb10, chb11, chb22 (`stepA_grid_v2.csv`, 384 rows).

**Amendment A8 rule (reported result):** maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; ties by lower FA/day, then lower penalty.

- mag_pct = 80, pen_mult = 10, merge_s = 90
- pooled: sensitivity=0.7333 precision=0.3143 f1=0.4400 FA/day=9.56 seizures=15 detected=11 false_alarms=24

**Information only (sensitivity == precision):**

- mag_pct = 80, pen_mult = 10, merge_s = 300
- pooled: sensitivity=0.6667 precision=0.2857 f1=0.4000 FA/day=9.96

## Step B -- test, scored ONCE at the Amendment A8 point

No other test point is computed or reported. Nothing chosen after this step is seen.

```
        subject  seizures  detected  false_alarms  sensitivity  precision       f1  fp_per_day  median_latency_s  n_latency  recorded_hours  seizure_hours  dontcare_hours  masked_hours  denom_hours
          chb03         7         7             9     1.000000   0.437500 0.608696   11.299698              60.0          7         38.0011         0.1178          4.1111       14.6567      19.1156
          chb06        10         9             7     0.900000   0.562500 0.692308    7.626349              32.0          9         66.7333         0.0500         13.8800       30.7744      22.0289
          chb13        12         5            11     0.416667   0.312500 0.357143   19.081272              48.0          5         33.0000         0.1600          4.8133       14.1911      13.8356
          chb14         8         0             4     0.000000   0.000000 0.000000    6.178932               NaN          0         26.0000         0.0544          3.0000        7.4089      15.5367
          chb15        20        10             7     0.500000   0.588235 0.540541    8.880536             116.0         10         40.0089         0.5722          9.0211       11.4978      18.9178
          chb16        10         8             6     0.800000   0.571429 0.666667   20.161792              14.0          8         19.0000         0.0311          3.9356        7.8911       7.1422
          chb17         3         3             4     1.000000   0.428571 0.600000    9.851767             100.0          3         21.0067         0.0822          0.5800       10.6000       9.7444
          chb18         6         5             6     0.833333   0.454545 0.588235    8.725510              60.0          5         35.6333         0.0922          2.5767       16.4611      16.5033
         POOLED        76        47            54     0.618421   0.465347 0.531073   10.551646              56.0         47        279.3833         1.1600         41.9178      113.4811     122.8244
POOLED_no_chb17        73        44            50     0.602740   0.468085 0.526946   10.611956              52.0         44        258.3767         1.0778         41.3378      102.8811     113.0800
```

## Step C -- window-level macro AUROC on test

- lab-protocol conventions (negatives = non-ictal, not masked, not don't-care): **0.4532**
- all-windows (no exclusions, recomputed fresh from the same cache): **0.6208** (docs cite 0.621)

Per subject in `stepC_auroc_v2.csv`.

## Step D -- cost of masking (test)

73/76 test seizures have at least one masked window; 32/76 are entirely masked.

```
subject  n_seizures  n_any_masked_window  n_entirely_masked
  chb03           7                    7                  7
  chb06          10                   10                  1
  chb13          12                   11                  4
  chb14           8                    7                  1
  chb15          20                   19                  5
  chb16          10                   10                  8
  chb17           3                    3                  1
  chb18           6                    6                  5
 POOLED          76                   73                 32
```
