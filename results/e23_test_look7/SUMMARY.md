# E23 -- look #7 (TEST-INFORMED, record 9.2) of the P3 frozen system, 8 test patients, 4 seeds

Points {"balanced": [0.005, 0.02], "sensitivity": [0.0075, 0.02]}, k = 4.0677, localizer cpd. Non-test reference: {"balanced": {"sens": 0.6702127659574468, "fa": 23.24981777973909}, "sensitivity": {"sens": 0.696808510638298, "fa": 32.728246371709496}}.
Gates R1 (non-test path) and R2 (look #6 reproduced on test) passed.
Hashes (sha256/16, LF): e23_test_look7.py 88587668baf12a64, p3c_freeze.py dabe4139f6005fd2, p3_levers.py feb247d2d08c52ba, p2_scalars.py 11feeaf3ba95ced4, e18_cpd_localizer.py e18c0ffe37f78e77, e17b_latent_family.py 3b4f034dca00eaf3, e22_test_oneshot.py 669350bbfaaf0f4e

## Point: balanced -- per seed (pooled | subject-mean)

```
stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short | review
detector     clean_seed42   38/ 76  328  0.500  0.104  0.172   28.35 | 0.588  0.117  0.189  27.85 | 4/18 | 0.0126
detector     clean_seed1    36/ 76  345  0.474  0.094  0.158   29.82 | 0.559  0.107  0.174  29.80 | 3/18 | 0.0121
detector     clean_seed2    34/ 76  359  0.447  0.087  0.145   31.03 | 0.545  0.102  0.167  30.42 | 3/18 | 0.0131
detector     clean_seed3    38/ 76  352  0.500  0.097  0.163   30.43 | 0.588  0.109  0.178  30.24 | 4/18 | 0.0114
localized    clean_seed42   37/ 76  318  0.487  0.104  0.172   27.49 | 0.577  0.118  0.190  26.84 | 4/18 | 0.0215
localized    clean_seed1    36/ 76  337  0.474  0.097  0.160   29.13 | 0.559  0.110  0.178  28.93 | 3/18 | 0.0213
localized    clean_seed2    34/ 76  353  0.447  0.088  0.147   30.52 | 0.545  0.104  0.169  29.89 | 3/18 | 0.0215
localized    clean_seed3    38/ 76  341  0.500  0.100  0.167   29.48 | 0.588  0.113  0.183  29.26 | 4/18 | 0.0204
look #6      clean_seed42   26/ 76  257  0.342  0.092  0.145   22.22 | 0.508  0.108  0.174  21.79 | 4/18 | nan
look #6      clean_seed1    25/ 76  277  0.329  0.083  0.132   23.95 | 0.491  0.098  0.158  24.12 | 3/18 | nan
look #6      clean_seed2    25/ 76  289  0.329  0.080  0.128   24.98 | 0.488  0.096  0.156  24.73 | 3/18 | nan
look #6      clean_seed3    26/ 76  282  0.342  0.084  0.135   24.38 | 0.503  0.097  0.157  24.47 | 4/18 | nan
```
## Point: sensitivity -- per seed (pooled | subject-mean)

```
stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short | review
detector     clean_seed42   38/ 76  442  0.500  0.079  0.137   38.21 | 0.588  0.092  0.154  37.39 | 4/18 | 0.0159
detector     clean_seed1    38/ 76  463  0.500  0.076  0.132   40.02 | 0.588  0.088  0.149  40.62 | 4/18 | 0.0158
detector     clean_seed2    35/ 76  461  0.461  0.071  0.122   39.85 | 0.562  0.085  0.143  39.11 | 3/18 | 0.0162
detector     clean_seed3    39/ 76  453  0.513  0.079  0.137   39.16 | 0.598  0.089  0.150  39.28 | 4/18 | 0.0157
localized    clean_seed42   37/ 76  426  0.487  0.080  0.137   36.83 | 0.577  0.093  0.155  35.83 | 4/18 | 0.0260
localized    clean_seed1    38/ 76  448  0.500  0.078  0.135   38.73 | 0.588  0.089  0.151  39.10 | 4/18 | 0.0283
localized    clean_seed2    35/ 76  449  0.461  0.072  0.125   38.81 | 0.562  0.086  0.146  38.06 | 3/18 | 0.0267
localized    clean_seed3    39/ 76  441  0.513  0.081  0.140   38.12 | 0.598  0.091  0.154  37.95 | 4/18 | 0.0261
look #6      clean_seed42   26/ 76  257  0.342  0.092  0.145   22.22 | 0.508  0.108  0.174  21.79 | 4/18 | nan
look #6      clean_seed1    25/ 76  277  0.329  0.083  0.132   23.95 | 0.491  0.098  0.158  24.12 | 3/18 | nan
look #6      clean_seed2    25/ 76  289  0.329  0.080  0.128   24.98 | 0.488  0.096  0.156  24.73 | 3/18 | nan
look #6      clean_seed3    26/ 76  282  0.342  0.084  0.135   24.38 | 0.503  0.097  0.157  24.47 | 4/18 | nan
```

## Headline (seed 42) and 4-seed mean +- SD

```
balanced    detector   seed 42: sens 0.500 @ 28.35, prec 0.104, F1 0.172, subject-mean 0.588 | 4 seeds: sens 0.480 +- 0.025, FP/day 29.91 +- 1.15, subject-mean 0.570 +- 0.021
balanced    localized  seed 42: sens 0.487 @ 27.49, prec 0.104, F1 0.172, subject-mean 0.577 | 4 seeds: sens 0.477 +- 0.022, FP/day 29.15 +- 1.26, subject-mean 0.567 +- 0.019
balanced    look #6    seed 42: sens 0.342 @ 22.22, prec 0.092, F1 0.145, subject-mean 0.508 | 4 seeds: sens 0.336 +- 0.008, FP/day 23.88 +- 1.19, subject-mean 0.498 +- 0.010
sensitivity detector   seed 42: sens 0.500 @ 38.21, prec 0.079, F1 0.137, subject-mean 0.588 | 4 seeds: sens 0.493 +- 0.023, FP/day 39.31 +- 0.82, subject-mean 0.584 +- 0.015
sensitivity localized  seed 42: sens 0.487 @ 36.83, prec 0.080, F1 0.137, subject-mean 0.577 | 4 seeds: sens 0.490 +- 0.022, FP/day 38.12 +- 0.92, subject-mean 0.581 +- 0.015
sensitivity look #6    seed 42: sens 0.342 @ 22.22, prec 0.092, F1 0.145, subject-mean 0.508 | 4 seeds: sens 0.336 +- 0.008, FP/day 23.88 +- 1.19, subject-mean 0.498 +- 0.010
```

## balanced: onset / offset |error| on matched seizures (n = 146 pairs)

```
detector  onset median  32.0 s bias +32.0 | offset median  20.0 s bias  -4.0
CPD       onset median  12.0 s bias  +8.0 | offset median  24.0 s bias +16.0
hybrid    onset median  12.0 s bias  +8.0 | offset median  16.0 s bias  +0.0
```

## balanced: patient-level bootstrap, P3 (after localizer) - look #6, 4-seed means, B = 10,000

```
pooled sens diff +0.141 [+0.000, +0.333]
subject-mean diff +0.070 [+0.000, +0.201]
FP/day diff +5.27 [+0.37, +13.60]
```

## balanced: per subject, seed 42: P3 after localizer | look #6

```
chb03  7/7 FP 22 ( 13.9/day, top 0.0052, q 0.0052) | 7/7 FP 22 ( 13.9/day)
chb06  2/10 FP 90 ( 32.4/day, top 0.0050, q 0.0019) | 2/10 FP 90 ( 32.4/day)
chb13  1/12 FP 40 ( 29.2/day, top 0.0050, q 0.0038) | 1/12 FP 40 ( 29.2/day)
chb14  6/8 FP 34 ( 31.5/day, top 0.0065, q 0.0065) | 6/8 FP 27 ( 25.0/day)
chb15  11/20 FP 53 ( 32.3/day, top 0.0200, q 0.0250) | 0/20 FP 14 (  8.5/day)
chb16  2/10 FP 16 ( 20.2/day, top 0.0050, q 0.0041) | 2/10 FP 16 ( 20.2/day)
chb17  3/3 FP 25 ( 29.5/day, top 0.0050, q 0.0024) | 3/3 FP 25 ( 29.5/day)
chb18  5/6 FP 38 ( 25.7/day, top 0.0082, q 0.0082) | 5/6 FP 23 ( 15.5/day)
```

## sensitivity: onset / offset |error| on matched seizures (n = 150 pairs)

```
detector  onset median  28.0 s bias +28.0 | offset median  20.0 s bias  +0.0
CPD       onset median  12.0 s bias  +8.0 | offset median  28.0 s bias +16.0
hybrid    onset median  12.0 s bias  +8.0 | offset median  24.0 s bias  +0.0
```

## sensitivity: patient-level bootstrap, P3 (after localizer) - look #6, 4-seed means, B = 10,000

```
pooled sens diff +0.155 [+0.012, +0.339]
subject-mean diff +0.084 [+0.010, +0.214]
FP/day diff +14.24 [+11.08, +18.88]
```

## sensitivity: per subject, seed 42: P3 after localizer | look #6

```
chb03  7/7 FP 42 ( 26.6/day, top 0.0075, q 0.0052) | 7/7 FP 22 ( 13.9/day)
chb06  2/10 FP 134 ( 48.2/day, top 0.0075, q 0.0019) | 2/10 FP 90 ( 32.4/day)
chb13  1/12 FP 57 ( 41.7/day, top 0.0075, q 0.0038) | 1/12 FP 40 ( 29.2/day)
chb14  6/8 FP 40 ( 37.0/day, top 0.0075, q 0.0065) | 6/8 FP 27 ( 25.0/day)
chb15  11/20 FP 53 ( 32.3/day, top 0.0200, q 0.0250) | 0/20 FP 14 (  8.5/day)
chb16  2/10 FP 24 ( 30.4/day, top 0.0075, q 0.0041) | 2/10 FP 16 ( 20.2/day)
chb17  3/3 FP 38 ( 44.9/day, top 0.0075, q 0.0024) | 3/3 FP 25 ( 29.5/day)
chb18  5/6 FP 38 ( 25.7/day, top 0.0082, q 0.0082) | 5/6 FP 23 ( 15.5/day)
```

Elapsed 93 s.