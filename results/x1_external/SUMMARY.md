# X1 -- external validation of the P3 frozen system (no tuning, one run)

Gates R-feat and R-model passed before any external recording was scored.

Subjects not scored (no file with all 19 electrodes): none

## chb24

```
point        stage      seed          tp/ref  FP   sens   prec   F1    FP/day | s-sens s-FP/day | short
balanced     detector   clean_seed42   14/ 16   26  0.875  0.350  0.500  29.52 | 0.875  29.52 | 0/1
balanced     detector   clean_seed1    13/ 16   25  0.812  0.342  0.481  28.38 | 0.812  28.38 | 0/1
balanced     detector   clean_seed2    12/ 16   28  0.750  0.300  0.429  31.79 | 0.750  31.79 | 0/1
balanced     detector   clean_seed3    14/ 16   28  0.875  0.333  0.483  31.79 | 0.875  31.79 | 0/1
balanced     localized  clean_seed42   14/ 16   26  0.875  0.350  0.500  29.52 | 0.875  29.52 | 0/1
balanced     localized  clean_seed1    13/ 16   23  0.812  0.361  0.500  26.11 | 0.812  26.11 | 0/1
balanced     localized  clean_seed2    12/ 16   26  0.750  0.316  0.444  29.52 | 0.750  29.52 | 0/1
balanced     localized  clean_seed3    14/ 16   25  0.875  0.359  0.509  28.38 | 0.875  28.38 | 0/1
sensitivity  detector   clean_seed42   14/ 16   26  0.875  0.350  0.500  29.52 | 0.875  29.52 | 0/1
sensitivity  detector   clean_seed1    13/ 16   25  0.812  0.342  0.481  28.38 | 0.812  28.38 | 0/1
sensitivity  detector   clean_seed2    12/ 16   28  0.750  0.300  0.429  31.79 | 0.750  31.79 | 0/1
sensitivity  detector   clean_seed3    14/ 16   28  0.875  0.333  0.483  31.79 | 0.875  31.79 | 0/1
sensitivity  localized  clean_seed42   14/ 16   26  0.875  0.350  0.500  29.52 | 0.875  29.52 | 0/1
sensitivity  localized  clean_seed1    13/ 16   23  0.812  0.361  0.500  26.11 | 0.812  26.11 | 0/1
sensitivity  localized  clean_seed2    12/ 16   26  0.750  0.316  0.444  29.52 | 0.750  29.52 | 0/1
sensitivity  localized  clean_seed3    14/ 16   25  0.875  0.359  0.509  28.38 | 0.875  28.38 | 0/1
```

Per subject, balanced point, seed 42, after the localizer:

```
subject  tp  n_ref  fp  fa_day    top  q_raw   hours  skipped
  chb24  14     16  26  29.516 0.0107 0.0107 21.2956        0
```

Onset/offset |error| (balanced, n = 53): detector 12/8 s, CPD 4/4 s, hybrid 4/4 s
## siena

```
point        stage      seed          tp/ref  FP   sens   prec   F1    FP/day | s-sens s-FP/day | short
balanced     detector   clean_seed42   32/ 47  268  0.681  0.107  0.184  45.90 | 0.676  44.74 | 2/3
balanced     detector   clean_seed1    27/ 47  249  0.574  0.098  0.167  42.64 | 0.569  38.66 | 2/3
balanced     detector   clean_seed2    30/ 47  276  0.638  0.098  0.170  47.27 | 0.660  44.65 | 1/3
balanced     detector   clean_seed3    27/ 47  264  0.574  0.093  0.160  45.21 | 0.593  43.51 | 2/3
balanced     localized  clean_seed42   33/ 47  257  0.702  0.114  0.196  44.01 | 0.748  41.52 | 2/3
balanced     localized  clean_seed1    27/ 47  243  0.574  0.100  0.170  41.62 | 0.569  37.84 | 2/3
balanced     localized  clean_seed2    29/ 47  267  0.617  0.098  0.169  45.73 | 0.624  42.67 | 1/3
balanced     localized  clean_seed3    27/ 47  256  0.574  0.095  0.164  43.84 | 0.593  41.97 | 2/3
sensitivity  detector   clean_seed42   33/ 47  284  0.702  0.104  0.181  48.64 | 0.700  47.20 | 2/3
sensitivity  detector   clean_seed1    28/ 47  264  0.596  0.096  0.165  45.21 | 0.576  40.44 | 2/3
sensitivity  detector   clean_seed2    32/ 47  287  0.681  0.100  0.175  49.15 | 0.674  46.12 | 2/3
sensitivity  detector   clean_seed3    28/ 47  290  0.596  0.088  0.153  49.67 | 0.600  47.16 | 2/3
sensitivity  localized  clean_seed42   34/ 47  273  0.723  0.111  0.192  46.75 | 0.771  43.98 | 2/3
sensitivity  localized  clean_seed1    28/ 47  257  0.596  0.098  0.169  44.01 | 0.576  39.59 | 2/3
sensitivity  localized  clean_seed2    31/ 47  277  0.660  0.101  0.175  47.44 | 0.638  44.05 | 2/3
sensitivity  localized  clean_seed3    28/ 47  282  0.596  0.090  0.157  48.29 | 0.600  45.62 | 2/3
```

Per subject, balanced point, seed 42, after the localizer:

```
subject  tp  n_ref  fp  fa_day    top  q_raw   hours  skipped
   PN00   5      5   1  7.6244 0.0113 0.0113  3.2422        0
   PN01   2      2  10 17.8424 0.0050 0.0044 13.4878        0
   PN03   2      2  54 53.6473 0.0200 0.0213 24.2267        0
   PN05   0      3   6 23.9867 0.0050 0.0037  6.0344        0
   PN06   3      5  38 76.0845 0.0200 0.0204 12.0711        0
   PN07   1      1  33 90.8604 0.0174 0.0174  8.7356        0
   PN09   1      3   6 21.2181 0.0052 0.0052  6.8467        0
   PN10   7     10  18 23.2383 0.0050 0.0044 18.7244        0
   PN11   1      1   3 30.0836 0.0200 0.0364  2.4100        0
   PN12   3      4   8 31.9173 0.0137 0.0137  6.0978        0
   PN13   1      3  11 30.7414 0.0113 0.0113  8.6633        0
   PN14   3      4  44 51.7422 0.0189 0.0189 20.4622        0
   PN16   2      2  16 79.7784 0.0200 0.0207  4.8789        0
   PN17   2      2   9 42.5197 0.0200 0.0223  5.1244        0
```

Onset/offset |error| (balanced, n = 116): detector 36/28 s, CPD 20/28 s, hybrid 20/20 s