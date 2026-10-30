# V9-X3 -- 4-fold patient-wise cross-validation of the GAE: results

Source: docs/prompts/V9_X3_CV_PREP.md. GAE-CV = each fold's own held-out cases, scored by that fold's own GAE (trained on the other 3 folds, seed 42, last epoch kept). kNN-LOO = B4 (12-feature per-channel kNN distance, no trained component), leave-one-case-out k, all 24 cases -- results/v9_x3/b4_loo_*.csv, SAME per-case ctx/inputs as GAE-CV (not results/v9_e4/'s own chb24 inputs, which used a different, label-free z-scoring -- see v9_x3_knn_b4.py's docstring). GAE+kNN-CV = per-fold fusion (F arm), k_F calibrated once per fold on that fold's own training cases, label-free.


## Per-case (localized stage), all 3 arms
```
                fp                     n_ref                      sens                        tp               
arm     GAE+kNN-CV GAE-CV kNN-LOO GAE+kNN-CV GAE-CV kNN-LOO GAE+kNN-CV GAE-CV kNN-LOO GAE+kNN-CV GAE-CV kNN-LOO
subject                                                                                                        
chb01         36.0   39.0    30.0        7.0    7.0     7.0      1.000  1.000   1.000        7.0    7.0     7.0
chb02         34.0   49.0    28.0        3.0    3.0     3.0      1.000  1.000   0.667        3.0    3.0     2.0
chb03         22.0   24.0    17.0        7.0    7.0     7.0      1.000  1.000   1.000        7.0    7.0     7.0
chb04        184.0  169.0   152.0        4.0    4.0     4.0      0.750  0.750   1.000        3.0    3.0     4.0
chb05         21.0   23.0     5.0        5.0    5.0     5.0      1.000  1.000   1.000        5.0    5.0     5.0
chb06        106.0  112.0    44.0       10.0   10.0    10.0      0.200  0.200   0.200        2.0    2.0     2.0
chb07         38.0   60.0    68.0        3.0    3.0     3.0      1.000  1.000   1.000        3.0    3.0     3.0
chb08          7.0    6.0    11.0        5.0    5.0     5.0      1.000  1.000   1.000        5.0    5.0     5.0
chb09         37.0   81.0    33.0        4.0    4.0     4.0      1.000  1.000   1.000        4.0    4.0     4.0
chb10         27.0   37.0    21.0        7.0    7.0     7.0      1.000  1.000   1.000        7.0    7.0     7.0
chb11         25.0   38.0    13.0        5.0    5.0     5.0      0.800  0.800   0.800        4.0    4.0     4.0
chb12         23.0   29.0    13.0       26.0   26.0    26.0      0.154  0.269   0.269        4.0    7.0     7.0
chb13         36.0   41.0    29.0       12.0   12.0    12.0      0.167  0.167   0.083        2.0    2.0     1.0
chb14         28.0   39.0    27.0        8.0    8.0     8.0      1.000  0.750   1.000        8.0    6.0     8.0
chb15         42.0   58.0    25.0       20.0   20.0    20.0      0.450  0.500   0.300        9.0   10.0     6.0
chb16         34.0   18.0    20.0       10.0   10.0    10.0      0.400  0.200   0.100        4.0    2.0     1.0
chb17         26.0   34.0    18.0        3.0    3.0     3.0      1.000  1.000   1.000        3.0    3.0     3.0
chb18         37.0   39.0    42.0        6.0    6.0     6.0      0.833  0.833   0.833        5.0    5.0     5.0
chb19         45.0   58.0    35.0        3.0    3.0     3.0      0.667  0.667   1.000        2.0    2.0     3.0
chb20         16.0   26.0    13.0        8.0    8.0     8.0      0.625  0.375   1.000        5.0    3.0     8.0
chb21         39.0   63.0    29.0        4.0    4.0     4.0      1.000  0.250   0.250        4.0    1.0     1.0
chb22         30.0   32.0    30.0        3.0    3.0     3.0      1.000  1.000   1.000        3.0    3.0     3.0
chb23         20.0   17.0    12.0        7.0    7.0     7.0      1.000  1.000   1.000        7.0    7.0     7.0
chb24         12.0   37.0    16.0       16.0   16.0    16.0      0.938  0.875   0.812       15.0   14.0    13.0
```

## Pooled + subject-mean metrics, by subset (localized stage)


### all24 (n=24)
```
arm              n    tp/ref    FP    sens   prec     F1  FP/day | subj-mean             95% CI
GAE-CV          24  115/186   1129  0.618 0.092 0.161  27.90 |     0.735 [0.605, 0.855]
kNN-LOO         24  116/186    731  0.624 0.137 0.225  18.07 |     0.763 [0.619, 0.888]
GAE+kNN-CV      24  121/186    925  0.651 0.116 0.196  22.86 |     0.791 [0.665, 0.901]
```

### subj23 (n=23)
```
arm              n    tp/ref    FP    sens   prec     F1  FP/day | subj-mean             95% CI
GAE-CV          23  114/182   1066  0.626 0.097 0.167  27.24 |     0.756 [0.630, 0.872]
kNN-LOO         23  115/182    702  0.632 0.141 0.230  17.94 |     0.785 [0.645, 0.909]
GAE+kNN-CV      23  117/182    886  0.643 0.117 0.197  22.64 |     0.782 [0.656, 0.895]
```

### test8 (n=8)
```
arm              n    tp/ref    FP    sens   prec     F1  FP/day | subj-mean             95% CI
GAE-CV           8   37/76     365  0.487 0.092 0.155  31.55 |     0.581 [0.344, 0.812]
kNN-LOO          8   33/76     222  0.434 0.129 0.199  19.19 |     0.565 [0.283, 0.846]
GAE+kNN-CV       8   40/76     331  0.526 0.108 0.179  28.61 |     0.631 [0.388, 0.869]
```

### dev15 (n=15)
```
arm              n    tp/ref    FP    sens   prec     F1  FP/day | subj-mean             95% CI
GAE-CV          15   64/94     727  0.681 0.081 0.145  25.95 |     0.807 [0.657, 0.936]
kNN-LOO         15   70/94     493  0.745 0.124 0.213  17.60 |     0.866 [0.720, 0.978]
GAE+kNN-CV      15   66/94     582  0.702 0.102 0.178  20.78 |     0.866 [0.735, 0.967]
```

## Paired bootstrap (per-case sensitivity, localized stage, 10,000 draws)
```
GAE-CV - kNN-LOO   (all 24 cases):  mean diff -0.028  95% CI [-0.106, +0.039]  P(diff>0) 0.231
GAE+kNN-CV - GAE-CV (n=24 held-out cases): mean diff +0.056  95% CI [+0.001, +0.134]  P(diff>0) 0.977
```

## Duration bins (caught/n, localized stage)


**GAE-CV**
```
  [   0,20  ) s:  11/31  = 0.355
  [  20,40  ) s:  26/51  = 0.510
  [  40,80  ) s:  38/59  = 0.644
  [  80,inf ) s:  39/44  = 0.886
```

**kNN-LOO**
```
  [   0,20  ) s:   9/31  = 0.290
  [  20,40  ) s:  28/51  = 0.549
  [  40,80  ) s:  41/59  = 0.695
  [  80,inf ) s:  37/44  = 0.841
```

**GAE+kNN-CV**
```
  [   0,20  ) s:  15/31  = 0.484
  [  20,40  ) s:  27/51  = 0.529
  [  40,80  ) s:  41/59  = 0.695
  [  80,inf ) s:  37/44  = 0.841
```

## Onset / offset |error| (median [IQR], bias, n), matched seizures
```
GAE-CV       onset  median   8.0 s IQR [4.0, 20.0] bias  +4.0 (n=114)
             offset median  16.0 s IQR [4.0, 52.0] bias  +4.0 (n=114)
kNN-LOO      onset  median   4.0 s IQR [0.0, 8.0] bias  +0.0 (n=115)
             offset median  24.0 s IQR [6.0, 44.0] bias +16.0 (n=115)
GAE+kNN-CV   onset  median   4.0 s IQR [4.0, 12.0] bias  +4.0 (n=120)
             offset median  16.0 s IQR [4.0, 48.0] bias  +8.0 (n=120)
```

## Per fold (localized stage, GAE-CV)
```
fold 1: 5 held-out cases, tp/ref 23/50, fp 344, sens 0.460, FP/day 27.75
fold 2: 6 held-out cases, tp/ref 30/48, fp 187, sens 0.625, FP/day 24.63
fold 3: 6 held-out cases, tp/ref 33/44, fp 327, sens 0.750, FP/day 28.71
fold 4: 7 held-out cases, tp/ref 29/44, fp 271, sens 0.659, FP/day 29.85
```

## Disclosures
(a) The architecture and post-processing (members, correction, smoothing, localizer, SzCORE config) were designed on the 15 original development patients, and the per-patient budget cap partly with the test set in view -- CV numbers on those 15 patients (and, to a lesser extent, the 8 original test patients) may be mildly optimistic for that reason, independent of the CV split itself. The 8 original test patients' numbers are reported as a separate subset above for this reason.
(b) One seed (42) per fold -- no multi-seed averaging, unlike the thesis model's own 4-seed report.
(c) chb24 is inside a fold here (fold 3's held-out case), trained into folds 1/2/4 -- this CV analysis is therefore separate from, and not a replacement for, the external evaluation of the unchanged thesis model on chb24 (results/v9_anatomy, results/x1_external).
