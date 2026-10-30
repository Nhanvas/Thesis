# V9-FINAL Part B -- hard patients, three detectors, all cases

CHB-MIT: 185 seizures (development 93 + chb-test 76 + chb24 16). Siena: 47 seizures, thesis system only -- V9-E4 (kNN) and V9-X3 (GAE-CV) are both CHB-MIT-only builds (see their own module docstrings), so Siena has no kNN-LOO or GAE-CV per-seizure table; not silently skipped, just unavailable from committed results.

kNN-LOO / GAE-CV join to the thesis descriptor table (amp_ratio) by (subject, file, onset_s): 0 unmatched (kNN), 0 unmatched (GAE-CV) -- should be 0 since the window grid and annotations are detector-independent; STOP if not.


## Thesis system (seed 42, after the localizer)

n = 185 seizures, 115 caught, 70 missed.

```
amplitude ratio   caught median 2.294 (n=115) vs missed median 1.288 (n=70), Mann-Whitney p=0.0000
duration (s)      caught median 68.0 (n=115) vs missed median 32.0 (n=70), Mann-Whitney p=0.0000
channel count     caught median 5.0 (n=38) vs missed median 5.5 (n=38), Mann-Whitney p=0.8460  (test only)
```

Logistic regression caught ~ log(amp_ratio) + log(duration_s) (n=185, 0 dropped, patient-cluster bootstrap B=2000, 2000 resamples converged):

```
log(amp_ratio)   coef +2.090   95% CI [+0.847, +4.551]
log(duration_s)  coef +0.787   95% CI [+0.158, +1.747]
```

### Siena (Thesis system (seed 42, after the localizer), 47 seizures, 33 caught) -- reported separately per the prompt

```
amplitude ratio   caught median 2.131 (n=33) vs missed median 1.322 (n=14), p=0.0063
duration (s)      caught median 68.0 (n=33) vs missed median 46.0 (n=14), p=0.0803
```
Logistic regression (Siena, n=47, 2000 resamples converged): log(amp_ratio) coef +1.998 CI [+0.875, +7.301], log(duration_s) coef +0.736 CI [-4.755, +3.104]

## kNN leave-one-case-out

n = 185 seizures, 115 caught, 70 missed.

```
amplitude ratio   caught median 2.147 (n=115) vs missed median 1.244 (n=70), Mann-Whitney p=0.0000
duration (s)      caught median 64.0 (n=115) vs missed median 30.0 (n=70), Mann-Whitney p=0.0000
channel count     caught median 5.0 (n=33) vs missed median 5.0 (n=43), Mann-Whitney p=0.3246  (test only)
```

Logistic regression caught ~ log(amp_ratio) + log(duration_s) (n=185, 0 dropped, patient-cluster bootstrap B=2000, 2000 resamples converged):

```
log(amp_ratio)   coef +2.153   95% CI [+0.107, +8.144]
log(duration_s)  coef +0.686   95% CI [-0.151, +2.665]
```

## GAE-CV

n = 185 seizures, 114 caught, 71 missed.

```
amplitude ratio   caught median 2.220 (n=114) vs missed median 1.285 (n=71), Mann-Whitney p=0.0000
duration (s)      caught median 68.0 (n=114) vs missed median 32.0 (n=71), Mann-Whitney p=0.0000
channel count     caught median 5.0 (n=37) vs missed median 5.0 (n=39), Mann-Whitney p=0.9163  (test only)
```

Logistic regression caught ~ log(amp_ratio) + log(duration_s) (n=185, 0 dropped, patient-cluster bootstrap B=2000, 2000 resamples converged):

```
log(amp_ratio)   coef +1.845   95% CI [+0.467, +4.427]
log(duration_s)  coef +0.728   95% CI [+0.200, +1.591]
```

## Which descriptor survives (p<0.05, Mann-Whitney) in all three detectors

```
descriptor       thesis   knn-loo   gae-cv   survives-all-3
amplitude ratio  True     True      True     True
duration         True     True      True     True
channel count (test only) False    False     False    False
```

Figure: `F:\Study\Thesis\Defense\slides\figs\final\hard_patients_amp_ratio.png`.

Elapsed 263s.