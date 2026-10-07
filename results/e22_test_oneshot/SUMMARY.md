# E22 -- single test look (#6) of the P2 frozen system, 8 test patients, 4 seeds

Localizer: kernel1d. Reproduction gates R1 (non-test path) and R2 (E = E9) passed.
Hashes (sha256/16, LF): e22_test_oneshot.py 669350bbfaaf0f4e, p2_scalars.py 11feeaf3ba95ced4, e18_cpd_localizer.py e18c0ffe37f78e77, e17b_latent_family.py 3b4f034dca00eaf3

## Per seed (pooled | subject-mean)

```
system/stage        seed          tp/ref  FP   sens   prec   F1     FP/day | s-sens s-prec s-F1  s-FP/day | short
final detector     clean_seed42   27/ 76  265  0.355  0.092  0.147   22.91 | 0.519  0.109  0.175  22.60 | 4/18
final detector     clean_seed1    25/ 76  286  0.329  0.080  0.129   24.72 | 0.491  0.094  0.154  25.06 | 3/18
final detector     clean_seed2    25/ 76  292  0.329  0.079  0.127   25.24 | 0.488  0.095  0.155  25.01 | 3/18
final detector     clean_seed3    26/ 76  293  0.342  0.082  0.132   25.33 | 0.503  0.093  0.153  25.45 | 4/18
final localized    clean_seed42   26/ 76  257  0.342  0.092  0.145   22.22 | 0.508  0.108  0.174  21.79 | 4/18
final localized    clean_seed1    25/ 76  277  0.329  0.083  0.132   23.95 | 0.491  0.098  0.158  24.12 | 3/18
final localized    clean_seed2    25/ 76  289  0.329  0.080  0.128   24.98 | 0.488  0.096  0.156  24.73 | 3/18
final localized    clean_seed3    26/ 76  282  0.342  0.084  0.135   24.38 | 0.503  0.097  0.157  24.47 | 4/18
E (P1 frozen)      clean_seed42    3/ 76  279  0.039  0.011  0.017   24.12 | 0.039  0.011  0.018  26.91 | 0/18
E (P1 frozen)      clean_seed1     3/ 76  298  0.039  0.010  0.016   25.76 | 0.039  0.010  0.016  30.01 | 0/18
E (P1 frozen)      clean_seed2     4/ 76  287  0.053  0.014  0.022   24.81 | 0.054  0.015  0.024  28.76 | 0/18
E (P1 frozen)      clean_seed3     3/ 76  285  0.039  0.010  0.016   24.64 | 0.039  0.010  0.016  28.44 | 0/18
```

## Headline (seed 42) and 4-seed mean +- SD

```
final detector     seed 42: sens 0.355 @ 22.91 FP/day, prec 0.092, F1 0.147 | 4 seeds: sens 0.339 +- 0.013, FP/day 24.55 +- 1.13, subject-mean sens 0.500 +- 0.014
final localized    seed 42: sens 0.342 @ 22.22 FP/day, prec 0.092, F1 0.145 | 4 seeds: sens 0.336 +- 0.008, FP/day 23.88 +- 1.19, subject-mean sens 0.498 +- 0.010
E (P1 frozen)      seed 42: sens 0.039 @ 24.12 FP/day, prec 0.011, F1 0.017 | 4 seeds: sens 0.043 +- 0.007, FP/day 24.83 +- 0.69, subject-mean sens 0.043 +- 0.008
```

## Onset / offset |error| on matched seizures (n = 103 seizure-seed pairs; 25.8 per seed)

```
detector   onset median  28.0 s IQR [12.0, 40.0] bias +28.0 | offset median  16.0 s IQR [8.0, 28.0] bias  +0.0
localizer  onset median   8.0 s IQR [4.0, 20.0] bias  +4.0 | offset median  20.0 s IQR [8.0, 40.0] bias +16.0
control 1  onset median  20.0 s IQR [8.0, 28.0] bias  +0.0 | offset median  32.0 s IQR [14.0, 52.0] bias +32.0
control 2  onset median  20.0 s IQR [6.0, 32.0] bias +20.0 | offset median  12.0 s IQR [4.0, 24.0] bias  +4.0
```

## Per subject (seed 42, after the localizer | E)

```
chb03  7/7 FP 22 ( 13.9/day) | 1/7 FP 21 ( 13.3/day)
chb06  2/10 FP 90 ( 32.4/day) | 0/10 FP 74 ( 26.6/day)
chb13  1/12 FP 40 ( 29.2/day) | 2/12 FP 42 ( 30.7/day)
chb14  6/8 FP 27 ( 25.0/day) | 0/8 FP 33 ( 30.5/day)
chb15  0/20 FP 14 (  8.5/day) | 0/20 FP 18 ( 11.0/day)
chb16  2/10 FP 16 ( 20.2/day) | 0/10 FP 45 ( 56.9/day)
chb17  3/3 FP 25 ( 29.5/day) | 0/3 FP 30 ( 35.4/day)
chb18  5/6 FP 23 ( 15.5/day) | 0/6 FP 16 ( 10.8/day)
```

Pre-registered expectation: FP/day ~ 23.5; sensitivity at most a moderate improvement over E9.

Elapsed 13 s.