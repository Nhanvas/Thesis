# Laboratory evaluation protocol v4 -- event-level evaluation on artifact-free EEG -- SUMMARY

docs/CC_PROMPT_LAB_PROTOCOL_V4.md (pre-registered 2026-10-01, committed alone before this ran). Same code base as src/lab_protocol_eval.py, cached Scope T (A2) scores only. Detector side is v3's (results/lab_protocol/v3/SUMMARY.md): only the signal-loss rule masks windows, no +-5 SD masking. The +-5 SD artifact rule moves entirely to the EVALUATION side here, as a second don't-care region alongside the post-ictal buffer -- computed for every window including ictal ones, from the raw signal, with no annotation used to compute the flag. A hyp event overlapping an annotated seizure is always scored normally (sensitivity unaffected); an unmatched hyp event is a false alarm only if its onset window is outside both don't-care regions. Does not edit the v1, v2 or v3 outputs.

wall-clock time: 44.4 min

## Denominators (all 11 subjects)

Per-patient breakdown of the four disjoint FA/day components (Step 3) in `denominators.csv`.

## Step A -- validation grid + operating-point selection

8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps = 96 cells, scored pooled across chb10, chb11, chb22 (`stepA_grid.csv`, 384 rows).

**Amendment A8 rule (reported result):** maximize pooled validation sensitivity subject to pooled validation FA/day <= 25; ties by lower FA/day, then lower penalty.

- mag_pct = 40, pen_mult = 10, merge_s = 90
- pooled: sensitivity=0.3333 precision=0.1351 f1=0.1923 FA/day=12.75 seizures=15 detected=5 false_alarms=32

**Information only (best F1 cell on validation):**

- mag_pct = 75, pen_mult = 10, merge_s = 300
- pooled: sensitivity=0.2667 precision=0.2500 f1=0.2581 FA/day=4.78

## Step B -- test, scored ONCE at the Amendment A8 point

No other test point is computed or reported. Nothing chosen after this step is seen.

```
        subject  seizures  detected  false_alarms  sensitivity  precision       f1  fp_per_day  median_latency_s  n_latency  recorded_hours  seizure_hours  signal_loss_hours  post_ictal_dontcare_hours  artifact_dontcare_hours  denom_hours
          chb03         7         0            11     0.000000   0.000000 0.000000   13.810742               NaN          0         38.0011         0.1178             0.0000                     4.1111                  14.6567      19.1156
          chb06        10         2            15     0.200000   0.117647 0.148148   16.342177              40.0          2         66.7333         0.0500             0.0000                    13.8800                  30.7744      22.0289
          chb13        12         0             2     0.000000   0.000000 0.000000    3.469322               NaN          0         33.0000         0.1600             0.0000                     4.8133                  14.1911      13.8356
          chb14         8         0            17     0.000000   0.000000 0.000000   26.260459               NaN          0         26.0000         0.0544             0.0000                     3.0000                   7.4089      15.5367
          chb15        20         0            22     0.000000   0.000000 0.000000   27.910255               NaN          0         40.0089         0.5722             0.0000                     9.0211                  11.4978      18.9178
          chb16        10         0             9     0.000000   0.000000 0.000000   30.242688               NaN          0         19.0000         0.0311             0.0000                     3.9356                   7.8911       7.1422
          chb17         3         0             7     0.000000   0.000000 0.000000   17.240593               NaN          0         21.0067         0.0822             0.5933                     0.5800                  10.0067       9.7444
          chb18         6         0             9     0.000000   0.000000 0.000000   13.088265               NaN          0         35.6333         0.0922             0.0000                     2.5767                  16.4611      16.5033
         POOLED        76         2            92     0.026316   0.021277 0.023529   17.976878              40.0          2        279.3833         1.1600             0.5933                    41.9178                 112.8878     122.8244
POOLED_no_chb17        73         2            85     0.027397   0.022989 0.025000   18.040325              40.0          2        258.3767         1.0778             0.0000                    41.3378                 102.8811     113.0800
```

## Step 5 -- false alarms ignored by each don't-care component (test, A8 point)

Counts of unmatched hyp events dropped because their onset window fell in a given don't-care region; the two regions can overlap for a given event (then it counts under both), so `n_dropped_total` (the actual number of events ignored) is not necessarily their sum.

```
        subject  n_dropped_buffer  n_dropped_artifact  n_dropped_total
          chb03                 8                  13               16
          chb06                 4                  24               24
          chb13                 1                   3                3
          chb14                 2                   6                8
          chb15                13                  39               44
          chb16                 0                   4                4
          chb17                 0                   9                9
          chb18                 1                  11               11
         POOLED                29                 109              119
POOLED_no_chb17                29                 100              110
```
