# Laboratory evaluation protocol v3 -- no amplitude masking -- SUMMARY

docs/CC_PROMPT_LAB_PROTOCOL_V3.md (pre-registered 2026-10-01, committed alone before this ran). Same code base as src/lab_protocol_eval.py (results/lab_protocol/SUMMARY.md = v1, SUMMARY_v2.md = v2), cached scores only. v2 found the +-5 SD rule masks 86% of ictal windows (32/76 test seizures entirely) and collapses the lab-protocol window AUROC to 0.4532 -- amplitude masking cannot separate artifact from seizure, so it is dropped from the detector here: only the signal-loss rule (Amendment A2) masks windows. Does not edit the v1 or v2 outputs.

wall-clock time (Steps A-C): 39.5 min

## Step A -- validation grid + operating-point selection

8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = 96 cells, scored pooled across chb10, chb11, chb22 (`stepA_grid.csv`, 384 rows).

**Amendment A8 rule (reported result):** maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; ties by lower FA/day, then lower penalty.

- mag_pct = 40, pen_mult = 10, merge_s = 300
- pooled: sensitivity=0.3333 precision=0.0685 f1=0.1136 FA/day=15.80 seizures=15 detected=5 false_alarms=68

**Information only (sensitivity == precision):**

- mag_pct = 80, pen_mult = 10, merge_s = 300
- pooled: sensitivity=0.2000 precision=0.1154 f1=0.1463 FA/day=5.34

## Step B -- test, scored ONCE at the Amendment A8 point

No other test point is computed or reported. Nothing chosen after this step is seen.

(`masked_hours` here is exactly signal-loss time -- v3 has no +-5 SD masking, so `masked` reduces to `is_signal_loss`.)

```
        subject  seizures  detected  false_alarms  sensitivity  precision       f1  fp_per_day  median_latency_s  n_latency  recorded_hours  seizure_hours  dontcare_hours  masked_hours  denom_hours
          chb03         7         0            19     0.000000   0.000000 0.000000   13.502221               NaN          0         38.0011         0.1178          4.1111        0.0000      33.7722
          chb06        10         2            33     0.200000   0.057143 0.088889   14.999053              40.0          2         66.7333         0.0500         13.8800        0.0000      52.8033
          chb13        12         0             4     0.000000   0.000000 0.000000    3.425309               NaN          0         33.0000         0.1600          4.8133        0.0000      28.0267
          chb14         8         0            18     0.000000   0.000000 0.000000   18.827175               NaN          0         26.0000         0.0544          3.0000        0.0000      22.9456
          chb15        20         0            38     0.000000   0.000000 0.000000   29.984657               NaN          0         40.0089         0.5722          9.0211        0.0000      30.4156
          chb16        10         0            13     0.000000   0.000000 0.000000   20.753880               NaN          0         19.0000         0.0311          3.9356        0.0000      15.0333
          chb17         3         0            15     0.000000   0.000000 0.000000   18.226823               NaN          0         21.0067         0.0822          0.5800        0.5933      19.7511
          chb18         6         0            18     0.000000   0.000000 0.000000   13.105029               NaN          0         35.6333         0.0922          2.5767        0.0000      32.9644
         POOLED        76         2           158     0.026316   0.012500 0.016949   16.087414              40.0          2        279.3833         1.1600         41.9178        0.5933     235.7122
POOLED_no_chb17        73         2           143     0.027397   0.013793 0.018349   15.891750              40.0          2        258.3767         1.0778         41.3378        0.0000     215.9611
```

## Step C -- window-level macro AUROC on test

- lab-protocol v3 conventions (negatives = non-ictal, outside the don't-care region, not signal-loss): **0.6261**
- all windows (no exclusions, recomputed fresh from the same cache): **0.6208** (docs cite 0.621)
- artifact-free background, the offline definition (src/diag_application_windows.py's `OFFLINE_MACRO_AUROC`, report Table 3.1 -- a different, label-based offline pipeline; cited here, never recomputed): **0.805**

Per subject in `stepC_auroc.csv`.

## For the record of v2 (no rerun)

Of the 47 test seizures detected in v2 at its own A8 point (mag=80, pen=10, merge=90 -- taken from `results/lab_protocol/SUMMARY_v2.md`, not re-derived; reproduced here via v2's own deterministic ictal-artifact correction as a cross-check against `stepB_v2.csv`'s POOLED `detected=47`), **26** were entirely masked (fused score 0 on every one of their windows). For those, the matching hypothesis event's onset position relative to the seizure's own mask boundary `[seizure_start_win, seizure_end_win)`:

```
subject  seizure_start_win  seizure_end_win  n_seizure_windows  onset_win  offset_win onset_pos_vs_mask_boundary
  chb03                 90              104                 14        105         106      after mask end (se+1)
  chb03               1082             1099                 17       1100        1101      after mask end (se+1)
  chb03               1908             1926                 18       1925        1926        inside mask (ss+17)
  chb03               3240             3254                 14       3255        3256      after mask end (se+1)
  chb03              30196            30209                 13      30210       30211      after mask end (se+1)
  chb03              31249            31265                 16      31265       31266                at mask end
  chb03              31932            31946                 14      31945       31946        inside mask (ss+13)
  chb06              39447            39451                  4      39455       39456      after mask end (se+4)
  chb13              14919            14931                 12      14930       14946        inside mask (ss+11)
  chb13              15533            15551                 18      15545       15556        inside mask (ss+12)
  chb13              29206            29223                 17      29220       29221        inside mask (ss+14)
  chb15              28730            28758                 28      28760       28761      after mask end (se+2)
  chb15              29077            29112                 35      29105       29151        inside mask (ss+28)
  chb15              31700            31719                 19      31715       31716        inside mask (ss+15)
  chb16               8672             8675                  3       8675        8676                at mask end
  chb16              13803            13805                  2      13805       13806                at mask end
  chb16              14456            14459                  3      14460       14461      after mask end (se+1)
  chb16              14823            14825                  2      14825       14841                at mask end
  chb16              15222            15225                  3      15235       15251     after mask end (se+10)
  chb16              15456            15459                  3      15460       15496      after mask end (se+1)
  chb17               8884             8906                 22       8905        8906        inside mask (ss+21)
  chb18              26071            26084                 13      26085       26106      after mask end (se+1)
  chb18              27523            27541                 18      27540       27541        inside mask (ss+17)
  chb18              28047            28061                 14      28060       28061        inside mask (ss+13)
  chb18              30819            30836                 17      30840       30841      after mask end (se+4)
  chb18              31285            31298                 13      31300       31301      after mask end (se+2)
```

Full per-seizure detail (all seizures detected in v2, not just the entirely-masked ones) in `v2_detected_seizures_full.csv`; the entirely-masked subset alone in `v2_entirely_masked_detected_seizures.csv`.
