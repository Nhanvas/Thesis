# Alert-budget per-patient operating point -- EXPLORATORY, POST-HOC

**This analysis is exploratory and post-hoc: it was not pre-registered in docs/CC_PROMPT_CONTINUOUS_EVAL.md and is not one of Steps A/B/C's results of record.**

Computed from the same grid as Step C's full Scope T test grid (`grid_for_subject`, on the already-cached Scope T score arrays -- no new GAE/connectivity scoring run, only change-point detection, identical to what `stepC_full_test_grid_scopeT.csv` pools). For each test patient, among the 96 grid cells (8 magnitude percentiles x 6 penalty multipliers x 2 merge gaps), the cell chosen is the one whose raw alert rate -- hypothesized event count divided by the patient's recorded days, excluding signal-loss time only (no seizure annotation used in this selection) -- is the largest value not above 25/day; ties by lower `pen_mult`, then lower `mag_pct`, then `merge_s` == 300. Sensitivity, precision and FA/day (which DO use the seizure annotation, same as the rest of Step C) are then read off for the selected cell, per patient and pooled.

## Per patient

subject  mag_pct  pen_mult  merge_s  n_hyp_events  recorded_days_excl_sigloss  alert_rate_per_day  within_budget  n_seizures  detected  false_alarms  sensitivity  precision     f1  fp_per_day
  chb03     80.0       2.0      300            39                      1.5834             24.6309           True           7         0            42       0.0000     0.0000 0.0000      26.608
  chb06     70.0       2.0       90            66                      2.7806             23.7363           True          10         1            65       0.1000     0.0152 0.0263      23.394
  chb13     50.0      10.0      300            34                      1.3750             24.7273           True          12         1            34       0.0833     0.0286 0.0426      24.848
  chb14     70.0       5.0       90            26                      1.0833             24.0000           True           8         1            25       0.1250     0.0385 0.0588      23.125
  chb15     80.0      10.0      300            36                      1.6670             21.5952           True          20         0            40       0.0000     0.0000 0.0000      24.343
  chb16     40.0       1.0      300            19                      0.7917             24.0000           True          10         0            25       0.0000     0.0000 0.0000      31.631
  chb17     70.0       5.0      300            21                      0.8506             24.6897           True           3         0            23       0.0000     0.0000 0.0000      27.151
  chb18     65.0       5.0      300            37                      1.4847             24.9205           True           6         2            37       0.3333     0.0513 0.0889      24.985

## Pooled (all 8 test patients)

TP=5 FP=291 n_ref=76 sensitivity=0.0658 precision=0.0169 FA/day=25.156
