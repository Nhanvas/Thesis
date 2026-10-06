# E9 -- ONE-SHOT TEST of the E8-frozen configuration (8 test patients)

Frozen: GAE v2 clean, V2_LW, D1 smooth 15 windows, top 2%, merge 90 s, SzCORE.
FA denominator = non-ictal recorded hours of the processed files (277.6 h).
Precision (approx.) = (hypothesised events - SzCORE false positives) / hypothesised events.

## Pooled

```
               tp  n_ref     fp    sens  precision      f1   fa_day  window_auroc_macro  short_tp  short_n
model                                                                                                     
V1            2.0   76.0  280.0  0.0263    -0.1290  0.0661  24.2049              0.6399       0.0     18.0
clean_seed1   3.0   76.0  298.0  0.0395    -0.0956  0.1345  25.7609              0.6636       0.0     18.0
clean_seed2   4.0   76.0  287.0  0.0526    -0.0996  0.2232  24.8100              0.6793       0.0     18.0
clean_seed3   3.0   76.0  285.0  0.0395    -0.1004  0.1301  24.6371              0.6697       0.0     18.0
clean_seed42  3.0   76.0  279.0  0.0395    -0.1028  0.1282  24.1184              0.6795       0.0     18.0
```

Headline (seed 42): see row clean_seed42. Spread over 4 clean seed(s): sens 0.043 +- 0.007, FA/day 24.8 +- 0.7, F1 0.154

## Per patient (frozen cell)

```
subject        model  tp  n_ref   fp  window_auroc  tp_short  n_short  fa_day
  chb03           V1 1.0    7.0 23.0        0.8008         0        0    14.6
  chb03  clean_seed1 1.0    7.0 23.0        0.8726         0        0    14.6
  chb03  clean_seed2 1.0    7.0 21.0        0.8726         0        0    13.3
  chb03  clean_seed3 1.0    7.0 22.0        0.8704         0        0    13.9
  chb03 clean_seed42 1.0    7.0 21.0        0.8713         0        0    13.3
  chb06           V1 0.0   10.0 67.0        0.3789         0        7    24.1
  chb06  clean_seed1 0.0   10.0 68.0        0.2510         0        7    24.5
  chb06  clean_seed2 0.0   10.0 68.0        0.2896         0        7    24.5
  chb06  clean_seed3 0.0   10.0 65.0        0.2885         0        7    23.4
  chb06 clean_seed42 0.0   10.0 74.0        0.3077         0        7    26.6
  chb13           V1 0.0   12.0 49.0        0.6494         0        0    35.8
  chb13  clean_seed1 2.0   12.0 47.0        0.6641         0        0    34.3
  chb13  clean_seed2 2.0   12.0 42.0        0.6750         0        0    30.7
  chb13  clean_seed3 2.0   12.0 48.0        0.6610         0        0    35.1
  chb13 clean_seed42 2.0   12.0 42.0        0.6556         0        0    30.7
  chb14           V1 1.0    8.0 47.0        0.6029         0        1    43.5
  chb14  clean_seed1 0.0    8.0 33.0        0.7538         0        1    30.5
  chb14  clean_seed2 1.0    8.0 33.0        0.7825         0        1    30.5
  chb14  clean_seed3 0.0    8.0 30.0        0.7568         0        1    27.8
  chb14 clean_seed42 0.0    8.0 33.0        0.7706         0        1    30.5
  chb15           V1 0.0   20.0 19.0        0.7077         0        0    11.6
  chb15  clean_seed1 0.0   20.0 18.0        0.7003         0        0    11.0
  chb15  clean_seed2 0.0   20.0 18.0        0.7049         0        0    11.0
  chb15  clean_seed3 0.0   20.0 18.0        0.6926         0        0    11.0
  chb15 clean_seed42 0.0   20.0 18.0        0.7050         0        0    11.0
  chb16           V1 0.0   10.0 29.0        0.6028         0       10    36.7
  chb16  clean_seed1 0.0   10.0 60.0        0.5643         0       10    75.9
  chb16  clean_seed2 0.0   10.0 56.0        0.6085         0       10    70.9
  chb16  clean_seed3 0.0   10.0 54.0        0.6023         0       10    68.3
  chb16 clean_seed42 0.0   10.0 45.0        0.6302         0       10    56.9
  chb17           V1 0.0    3.0 28.0        0.5962         0        0    33.1
  chb17  clean_seed1 0.0    3.0 32.0        0.6491         0        0    37.8
  chb17  clean_seed2 0.0    3.0 32.0        0.6485         0        0    37.8
  chb17  clean_seed3 0.0    3.0 31.0        0.6366         0        0    36.6
  chb17 clean_seed42 0.0    3.0 30.0        0.6520         0        0    35.4
  chb18           V1 0.0    6.0 18.0        0.7805         0        0    12.2
  chb18  clean_seed1 0.0    6.0 17.0        0.8532         0        0    11.5
  chb18  clean_seed2 0.0    6.0 17.0        0.8524         0        0    11.5
  chb18  clean_seed3 0.0    6.0 17.0        0.8492         0        0    11.5
  chb18 clean_seed42 0.0    6.0 16.0        0.8437         0        0    10.8
```

## Characterisation (not selection): smooth 15, top-p grid

```
       model   top   tp  n_ref    fp  sens  fa_day
          V1 0.001  0.0   76.0  36.0 0.000   3.112
          V1 0.002  0.0   76.0  52.0 0.000   4.495
          V1 0.005  0.0   76.0  89.0 0.000   7.694
          V1 0.010  0.0   76.0 134.0 0.000  11.584
          V1 0.020  2.0   76.0 280.0 0.026  24.205
          V1 0.050 24.0   76.0 718.0 0.316  62.068
 clean_seed1 0.001  0.0   76.0  35.0 0.000   3.026
 clean_seed1 0.002  0.0   76.0  52.0 0.000   4.495
 clean_seed1 0.005  1.0   76.0 100.0 0.013   8.645
 clean_seed1 0.010  2.0   76.0 149.0 0.026  12.880
 clean_seed1 0.020  3.0   76.0 298.0 0.039  25.761
 clean_seed1 0.050 25.0   76.0 711.0 0.329  61.463
 clean_seed2 0.001  0.0   76.0  34.0 0.000   2.939
 clean_seed2 0.002  0.0   76.0  47.0 0.000   4.063
 clean_seed2 0.005  1.0   76.0  93.0 0.013   8.039
 clean_seed2 0.010  1.0   76.0 152.0 0.013  13.140
 clean_seed2 0.020  4.0   76.0 287.0 0.053  24.810
 clean_seed2 0.050 25.0   76.0 703.0 0.329  60.772
 clean_seed3 0.001  0.0   76.0  40.0 0.000   3.458
 clean_seed3 0.002  0.0   76.0  51.0 0.000   4.409
 clean_seed3 0.005  1.0   76.0  94.0 0.013   8.126
 clean_seed3 0.010  2.0   76.0 153.0 0.026  13.226
 clean_seed3 0.020  3.0   76.0 285.0 0.039  24.637
 clean_seed3 0.050 24.0   76.0 692.0 0.316  59.821
clean_seed42 0.001  0.0   76.0  28.0 0.000   2.420
clean_seed42 0.002  0.0   76.0  40.0 0.000   3.458
clean_seed42 0.005  1.0   76.0  89.0 0.013   7.694
clean_seed42 0.010  2.0   76.0 148.0 0.026  12.794
clean_seed42 0.020  3.0   76.0 279.0 0.039  24.118
clean_seed42 0.050 27.0   76.0 701.0 0.355  60.599
```