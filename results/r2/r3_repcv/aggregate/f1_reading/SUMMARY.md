# Track F1/F2 — repeated random patient-wise 4-fold CV (CHB-MIT, 24 cases / 23 subjects)

Partitions: [0, 1, 2, 3, 4, 5] (0 = the committed CV, seed 42; r = random partition r, seed r). Verification: PASS. Per-case means, own label-free point, after CPD.

## F1 — per partition

```
 partition model  sens  prec    f1  fp_day  auroc  seizures_caught  n_ref  false_alarms  sens_test8  fp_day_test8  caught_test8  sens_other16  fp_day_other16
         0   gae 0.737 0.134 0.208  27.786  0.795              115    186          1143       0.575        32.410            37         0.818          25.473
         0   mlp 0.735 0.198 0.284  19.998  0.890              120    186           813       0.553        26.049            38         0.826          16.973
         1   gae 0.740 0.151 0.225  27.078  0.802              117    186          1098       0.575        30.111            37         0.822          25.562
         1   mlp 0.760 0.194 0.282  19.592  0.892              121    186           807       0.606        24.869            40         0.837          16.954
         2   gae 0.745 0.130 0.204  28.227  0.810              114    186          1112       0.572        33.168            36         0.832          25.756
         2   mlp 0.737 0.199 0.285  19.673  0.887              121    186           806       0.529        25.796            38         0.841          16.611
         3   gae 0.728 0.137 0.210  27.851  0.809              112    186          1109       0.545        33.888            35         0.820          24.832
         3   mlp 0.751 0.203 0.288  19.761  0.893              120    186           811       0.600        25.155            39         0.826          17.064
         4   gae 0.713 0.129 0.205  26.436  0.811              109    186          1066       0.554        29.487            35         0.793          24.911
         4   mlp 0.738 0.209 0.296  18.583  0.891              119    186           770       0.547        23.943            38         0.834          15.904
         5   gae 0.737 0.139 0.214  26.733  0.809              114    186          1094       0.569        31.632            36         0.820          24.283
         5   mlp 0.712 0.206 0.291  18.434  0.889              114    186           765       0.500        23.697            35         0.819          15.802
```

## F1 — across partitions (SD = sensitivity to partition + seed, not uncertainty)

```
model         set  n_partitions       metric   mean    sd    min    max
  gae         all             6         sens  0.733 0.011  0.713  0.745
  gae         all             6         prec  0.137 0.008  0.129  0.151
  gae         all             6           f1  0.211 0.008  0.204  0.225
  gae         all             6       fp_day 27.352 0.707 26.436 28.227
  gae         all             6        auroc  0.806 0.006  0.795  0.811
  gae         all             6   sens_test8  0.565 0.013  0.545  0.575
  gae         all             6 sens_other16  0.818 0.013  0.793  0.832
  gae random_only             5         sens  0.733 0.012  0.713  0.745
  gae random_only             5         prec  0.137 0.009  0.129  0.151
  gae random_only             5           f1  0.212 0.009  0.204  0.225
  gae random_only             5       fp_day 27.265 0.754 26.436 28.227
  gae random_only             5        auroc  0.808 0.003  0.802  0.811
  gae random_only             5   sens_test8  0.563 0.013  0.545  0.575
  gae random_only             5 sens_other16  0.818 0.015  0.793  0.832
  mlp         all             6         sens  0.739 0.016  0.712  0.760
  mlp         all             6         prec  0.202 0.006  0.194  0.209
  mlp         all             6           f1  0.288 0.005  0.282  0.296
  mlp         all             6       fp_day 19.340 0.660 18.434 19.998
  mlp         all             6        auroc  0.890 0.002  0.887  0.893
  mlp         all             6   sens_test8  0.556 0.041  0.500  0.606
  mlp         all             6 sens_other16  0.831 0.008  0.819  0.841
  mlp random_only             5         sens  0.740 0.018  0.712  0.760
  mlp random_only             5         prec  0.202 0.006  0.194  0.209
  mlp random_only             5           f1  0.288 0.005  0.282  0.296
  mlp random_only             5       fp_day 19.209 0.644 18.434 19.761
  mlp random_only             5        auroc  0.890 0.002  0.887  0.893
  mlp random_only             5   sens_test8  0.556 0.046  0.500  0.606
  mlp random_only             5 sens_other16  0.832 0.009  0.819  0.841
```

## F1 — subject bootstrap of the across-partition mean (uncertainty)

```
model metric  mean_over_partitions     lo     hi  n_units  n_partitions
  gae   sens                 0.733  0.608  0.851       23             6
  gae     f1                 0.211  0.154  0.281       23             6
  gae fp_day                27.352 23.238 31.156       23             6
  gae   prec                 0.137  0.093  0.193       23             6
  mlp   sens                 0.739  0.618  0.849       23             6
  mlp     f1                 0.288  0.208  0.378       23             6
  mlp fp_day                19.340 15.765 22.788       23             6
  mlp   prec                 0.202  0.134  0.282       23             6
```

**Statement (pre-registered form):** over 6 patient partitions (each with its own training seed), the GAE's 4-fold CV per-case mean sensitivity is 0.733 ± 0.011 (range 0.713–0.745) at 27.4 ± 0.7 FP/day; 95 % CI of the mean over subjects [0.608, 0.851].

## F2 — MLP-AE minus GAE, per partition (paired subject bootstrap)

```
 partition   dF1  dF1_lo  dF1_hi  dSens  dSens_lo  dSens_hi  dFP_day  dAUROC  dF1_fixed0005  dF1_fixed_lo  dF1_fixed_hi  wins  losses  gae_fp_day  sens_at_gae_fp_gae  sens_at_gae_fp_mlp  caught_gae  caught_mlp  fa_gae  fa_mlp
         0 0.076   0.036   0.122 -0.002    -0.064     0.063   -7.787   0.095          0.081         0.031         0.137    18       6      27.786               0.681               0.787         115         120    1143     813
         1 0.057   0.023   0.091  0.020    -0.039     0.077   -7.486   0.089          0.069        -0.014         0.139    17       6      27.078               0.706               0.799         117         121    1098     807
         2 0.081   0.037   0.135 -0.008    -0.089     0.058   -8.554   0.078          0.076         0.025         0.134    19       5      28.227               0.707               0.781         114         121    1112     806
         3 0.079   0.039   0.124  0.023    -0.027     0.067   -8.090   0.083          0.077         0.004         0.142    18       6      27.851               0.703               0.799         112         120    1109     811
         4 0.091   0.044   0.145  0.025    -0.042     0.090   -7.853   0.081          0.070         0.013         0.129    18       6      26.436               0.704               0.780         109         119    1066     770
         5 0.077   0.036   0.122 -0.024    -0.110     0.047   -8.299   0.080          0.051        -0.030         0.119    19       5      26.733               0.712               0.760         114         114    1094     765
```

## F2 — across partitions

```
     quantity   mean      lo     hi
          dF1  0.077   0.038  0.120
dF1_fixed0005  0.071   0.008  0.130
        dSens  0.006  -0.053  0.059
      dFP_day -8.012 -10.926 -5.040
       dAUROC  0.084   0.060  0.112
```

**Rule:** stable iff dF1 > 0 in ≥ 5 of 6 partitions AND the CI of the across-partition mean excludes 0. dF1 > 0 in 6 / 6; across-partition mean dF1 +0.077 [+0.038, +0.120] → **stable advantage of the MLP-AE (without message passing)**. Secondary rows (fixed 0.005, same alarm rate, AUROC) are descriptive only.

