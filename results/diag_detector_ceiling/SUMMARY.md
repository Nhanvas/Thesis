# diag_detector_ceiling -- validation only, descriptive

## Q1 FP anatomy (approximate match: overlap with [onset-30, offset+60])

     point subject  n_events  n_fp_approx  fp_falls_only  fp_near_file_boundary  fp_onset_flagged  n_file_boundaries
 50_2.0_90   chb10       178          170             59                      2                66                 24
 50_2.0_90   chb11       161          158             62                     11                90                 30
 50_2.0_90   chb22       123          120             47                      2                77                 30
75_5.0_300   chb10        41           39             15                      1                16                 24
75_5.0_300   chb11        44           43             10                      3                27                 30
75_5.0_300   chb22        28           26              5                      0                14                 30

Share of change points that rise / sit within 60 s of a file boundary / sit in a flagged window, split by whether the change point is inside a seizure:

                   rise  near_boundary  flagged
point      ictal                               
50_2.0_90  False  0.517          0.028    0.511
           True   0.875          0.000    0.000
75_5.0_300 False  0.540          0.025    0.509
           True   1.000          0.000    0.000

## Q2 locked PELT vs rises-only without boundary change points (SzCORE)

     point                     variant  tp  n_ref  fp  sensitivity  fa_per_day
 50_2.0_90                 locked PELT  11     15 448       0.7333       96.52
 50_2.0_90 rises only, no boundary CPs  10     15 284       0.6667       61.19
75_5.0_300                 locked PELT   5     15 116       0.3333       24.99
75_5.0_300 rises only, no boundary CPs   5     15  80       0.3333       17.24

## Q3 threshold detector, per-file smoothing, per-patient quantile threshold

 oracle_flag_removed  smooth_windows  top_fraction  tp  n_ref  fp  sensitivity  fa_per_day per_subject_tp
               False               1         0.050  14     15 864       0.9333      186.14          7/4/3
               False               1         0.020  11     15 633       0.7333      136.37          4/4/3
               False               1         0.010   7     15 417       0.4667       89.84          4/0/3
               False               1         0.005   5     15 260       0.3333       56.01          3/0/2
               False               1         0.002   2     15 129       0.1333       27.79          2/0/0
               False               1         0.001   1     15  65       0.0667       14.00          1/0/0
               False               3         0.050  13     15 671       0.8667      144.56          6/4/3
               False               3         0.020  10     15 420       0.6667       90.49          4/3/3
               False               3         0.010   9     15 263       0.6000       56.66          4/2/3
               False               3         0.005   7     15 164       0.4667       35.33          2/2/3
               False               3         0.002   3     15  68       0.2000       14.65          2/0/1
               False               3         0.001   1     15  38       0.0667        8.19          1/0/0
               False               5         0.050  11     15 529       0.7333      113.97          5/3/3
               False               5         0.020  10     15 276       0.6667       59.46          4/3/3
               False               5         0.010   8     15 172       0.5333       37.06          3/2/3
               False               5         0.005   6     15 103       0.4000       22.19          2/2/2
               False               5         0.002   4     15  43       0.2667        9.26          1/1/2
               False               5         0.001   0     15  25       0.0000        5.39          0/0/0
               False              15         0.050  10     15 267       0.6667       57.52          4/3/3
               False              15         0.020   7     15 119       0.4667       25.64          1/3/3
               False              15         0.010   7     15  65       0.4667       14.00          1/3/3
               False              15         0.005   5     15  29       0.3333        6.25          0/3/2
               False              15         0.002   3     15  14       0.2000        3.02          0/2/1
               False              15         0.001   2     15  11       0.1333        2.37          0/1/1
                True               1         0.050  14     15 198       0.9333       42.66          7/4/3
                True               1         0.020  11     15  68       0.7333       14.65          4/4/3
                True               1         0.010   7     15  34       0.4667        7.33          4/0/3
                True               1         0.005   5     15  21       0.3333        4.52          3/0/2
                True               1         0.002   2     15  10       0.1333        2.15          2/0/0
                True               1         0.001   1     15   6       0.0667        1.29          1/0/0
                True               3         0.050  13     15 225       0.8667       48.47          6/4/3
                True               3         0.020  10     15  66       0.6667       14.22          4/3/3
                True               3         0.010   9     15  32       0.6000        6.89          4/2/3
                True               3         0.005   7     15  18       0.4667        3.88          2/2/3
                True               3         0.002   3     15   5       0.2000        1.08          2/0/1
                True               3         0.001   1     15   3       0.0667        0.65          1/0/0
                True               5         0.050  11     15 214       0.7333       46.10          5/3/3
                True               5         0.020  10     15  76       0.6667       16.37          4/3/3
                True               5         0.010   8     15  30       0.5333        6.46          3/2/3
                True               5         0.005   6     15  10       0.4000        2.15          2/2/2
                True               5         0.002   4     15   3       0.2667        0.65          1/1/2
                True               5         0.001   0     15   2       0.0000        0.43          0/0/0
                True              15         0.050  10     15 169       0.6667       36.41          4/3/3
                True              15         0.020   7     15  43       0.4667        9.26          1/3/3
                True              15         0.010   7     15  19       0.4667        4.09          1/3/3
                True              15         0.005   5     15   9       0.3333        1.94          0/3/2
                True              15         0.002   3     15   3       0.2000        0.65          0/2/1
                True              15         0.001   2     15   2       0.1333        0.43          0/1/1
