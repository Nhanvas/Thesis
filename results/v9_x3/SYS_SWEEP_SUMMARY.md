# V9-X3 -- system-stage k-sweep: matched FP/day sensitivity + paired F1/precision

No training; reuses the cached GAE/B4 distance dumps from the main V9-X3 run. K_MULT = v9_e1b_calibrate.K_MULT (13 log-spaced multipliers of each case's OWN already-calibrated k); matched FP/day = pooled-curve bracket (v9_e2_veto.per_patient_sens_at_fa's construction), 24 cases.


## Per-case-mean sensitivity at matched FP/day (all 24 cases)
```
fa_target   20.0   27.5
arm                    
GAE+kNN-CV  0.77  0.800
GAE-CV       NaN  0.733
kNN-LOO     0.77  0.800
```

## Paired bootstrap, per-case sensitivity at matched FP/day (10,000 draws, all 24 cases)
```
FP/day  20.0  GAE-kNN        mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
FP/day  20.0  GAE+kNN-GAE    mean diff +nan  95% CI [+nan, +nan]  P(diff>0) nan  (n=0)
FP/day  20.0  GAE+kNN-kNN    mean diff -0.000  95% CI [-0.086, +0.097]  P(diff>0) 0.481  (n=24)
FP/day  27.5  GAE-kNN        mean diff -0.066  95% CI [-0.140, +0.001]  P(diff>0) 0.027  (n=24)
FP/day  27.5  GAE+kNN-GAE    mean diff +0.067  95% CI [+0.010, +0.143]  P(diff>0) 0.996  (n=24)
FP/day  27.5  GAE+kNN-kNN    mean diff +0.001  95% CI [-0.079, +0.092]  P(diff>0) 0.485  (n=24)
```

## Paired bootstrap, per-case F1 and precision at each arm's OWN calibrated point (10,000 draws, all 24 cases)
```
f1         GAE-kNN        mean diff -0.076  95% CI [-0.125, -0.031]  P(diff>0) 0.000  (n=24)
f1         GAE+kNN-GAE    mean diff +0.045  95% CI [+0.018, +0.077]  P(diff>0) 1.000  (n=24)
f1         GAE+kNN-kNN    mean diff -0.030  95% CI [-0.075, +0.010]  P(diff>0) 0.078  (n=24)
precision  GAE-kNN        mean diff -0.062  95% CI [-0.103, -0.025]  P(diff>0) 0.000  (n=24)
precision  GAE+kNN-GAE    mean diff +0.032  95% CI [+0.010, +0.061]  P(diff>0) 1.000  (n=24)
precision  GAE+kNN-kNN    mean diff -0.030  95% CI [-0.068, +0.004]  P(diff>0) 0.045  (n=24)
```