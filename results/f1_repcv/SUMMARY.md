# Track F1/F2 — repeated random patient-wise 4-fold CV (CHB-MIT, 24 cases / 23 subjects)

Partitions: [0, 1, 2, 3, 4, 5] (0 = the committed CV, seed 42; r = random partition r, seed r). Verification: PASS. Per-case means, own label-free point, after CPD.

## F1 — per partition

```
 partition model  sens  prec    f1  fp_day  auroc  seizures_caught  n_ref  false_alarms  sens_test8  fp_day_test8  caught_test8  sens_other16  fp_day_other16
         0   gae 0.735 0.128 0.203  28.387  0.802              115    186          1129       0.581        30.762            37         0.812          27.199
         0   mlp 0.711 0.189 0.273  20.183  0.890              115    186           827       0.505        25.892            36         0.814          17.329
         1   gae 0.735 0.143 0.222  25.928  0.814              114    186          1043       0.556        30.892            35         0.824          23.446
         1   mlp 0.745 0.201 0.289  18.652  0.894              117    186           765       0.588        23.956            37         0.824          16.001
         2   gae 0.723 0.131 0.203  27.393  0.811              110    186          1083       0.569        31.557            36         0.801          25.311
         2   mlp 0.753 0.189 0.276  20.697  0.891              121    186           860       0.560        26.837            38         0.850          17.627
         3   gae 0.746 0.141 0.222  26.596  0.810              119    186          1062       0.594        31.669            39         0.822          24.060
         3   mlp 0.720 0.208 0.294  18.775  0.892              115    186           764       0.495        24.965            34         0.832          15.680
         4   gae 0.724 0.132 0.207  26.936  0.813              112    186          1098       0.573        30.982            37         0.799          24.913
         4   mlp 0.715 0.202 0.286  18.580  0.893              117    186           777       0.533        24.981            39         0.806          15.380
         5   gae 0.753 0.128 0.202  28.725  0.807              117    186          1184       0.575        32.604            37         0.842          26.785
         5   mlp 0.714 0.209 0.295  18.281  0.891              115    186           745       0.515        23.364            36         0.814          15.740
```

## F1 — across partitions (SD = sensitivity to partition + seed, not uncertainty)

```
model         set  n_partitions       metric   mean    sd    min    max
  gae         all             6         sens  0.736 0.012  0.723  0.753
  gae         all             6         prec  0.134 0.006  0.128  0.143
  gae         all             6           f1  0.210 0.009  0.202  0.222
  gae         all             6       fp_day 27.327 1.070 25.928 28.725
  gae         all             6        auroc  0.809 0.004  0.802  0.814
  gae         all             6   sens_test8  0.575 0.013  0.556  0.594
  gae         all             6 sens_other16  0.817 0.016  0.799  0.842
  gae random_only             5         sens  0.736 0.013  0.723  0.753
  gae random_only             5         prec  0.135 0.006  0.128  0.143
  gae random_only             5           f1  0.211 0.010  0.202  0.222
  gae random_only             5       fp_day 27.116 1.046 25.928 28.725
  gae random_only             5        auroc  0.811 0.003  0.807  0.814
  gae random_only             5   sens_test8  0.573 0.014  0.556  0.594
  gae random_only             5 sens_other16  0.818 0.018  0.799  0.842
  mlp         all             6         sens  0.726 0.018  0.711  0.753
  mlp         all             6         prec  0.200 0.009  0.189  0.209
  mlp         all             6           f1  0.285 0.009  0.273  0.295
  mlp         all             6       fp_day 19.195 0.992 18.281 20.697
  mlp         all             6        auroc  0.892 0.002  0.890  0.894
  mlp         all             6   sens_test8  0.533 0.036  0.495  0.588
  mlp         all             6 sens_other16  0.823 0.016  0.806  0.850
  mlp random_only             5         sens  0.730 0.018  0.714  0.753
  mlp random_only             5         prec  0.202 0.008  0.189  0.209
  mlp random_only             5           f1  0.288 0.008  0.276  0.295
  mlp random_only             5       fp_day 18.997 0.967 18.281 20.697
  mlp random_only             5        auroc  0.892 0.001  0.891  0.894
  mlp random_only             5   sens_test8  0.538 0.037  0.495  0.588
  mlp random_only             5 sens_other16  0.825 0.017  0.806  0.850
```

## F1 — subject bootstrap of the across-partition mean (uncertainty)

```
model metric  mean_over_partitions     lo     hi  n_units  n_partitions
  gae   sens                 0.736  0.612  0.854       23             6
  gae     f1                 0.210  0.155  0.275       23             6
  gae fp_day                27.327 23.327 31.027       23             6
  gae   prec                 0.134  0.094  0.184       23             6
  mlp   sens                 0.726  0.604  0.839       23             6
  mlp     f1                 0.285  0.207  0.373       23             6
  mlp fp_day                19.195 15.702 22.586       23             6
  mlp   prec                 0.200  0.134  0.278       23             6
```

**Statement (pre-registered form):** over 6 patient partitions (each with its own training seed), the GAE's 4-fold CV per-case mean sensitivity is 0.736 ± 0.012 (range 0.723–0.753) at 27.3 ± 1.1 FP/day; 95 % CI of the mean over subjects [0.612, 0.854].

## F2 — MLP-AE minus GAE, per partition (paired subject bootstrap)

```
 partition   dF1  dF1_lo  dF1_hi  dSens  dSens_lo  dSens_hi  dFP_day  dAUROC  dF1_fixed0005  dF1_fixed_lo  dF1_fixed_hi  wins  losses  gae_fp_day  sens_at_gae_fp_gae  sens_at_gae_fp_mlp  caught_gae  caught_mlp  fa_gae  fa_mlp
         0 0.070   0.026   0.117 -0.024    -0.115     0.061   -8.203   0.088          0.064        -0.012         0.135    18       6      28.387               0.703               0.787         115         115    1129     827
         1 0.067   0.027   0.110  0.010    -0.061     0.079   -7.276   0.080          0.069         0.009         0.127    18       5      25.928               0.699               0.795         114         117    1043     765
         2 0.073   0.031   0.119  0.030    -0.046     0.103   -6.696   0.081          0.059        -0.003         0.122    17       6      27.393               0.713               0.793         110         121    1083     860
         3 0.072   0.023   0.125 -0.026    -0.123     0.064   -7.821   0.082          0.054        -0.027         0.125    16       8      26.596               0.721               0.793         119         115    1062     764
         4 0.078   0.037   0.121 -0.009    -0.097     0.070   -8.356   0.080          0.041        -0.037         0.112    19       5      26.936               0.704               0.780         112         117    1098     777
         5 0.093   0.042   0.148 -0.038    -0.123     0.042  -10.444   0.084          0.073        -0.008         0.147    17       7      28.725               0.727               0.797         117         115    1184     745
```

## F2 — across partitions

```
     quantity   mean      lo     hi
          dF1  0.075   0.034  0.121
dF1_fixed0005  0.060  -0.012  0.127
        dSens -0.009  -0.086  0.062
      dFP_day -8.133 -10.967 -5.257
       dAUROC  0.082   0.058  0.111
```

**Rule:** stable iff dF1 > 0 in ≥ 5 of 6 partitions AND the CI of the across-partition mean excludes 0. dF1 > 0 in 6 / 6; across-partition mean dF1 +0.075 [+0.034, +0.121] → **stable advantage of the MLP-AE (without message passing)**. Secondary rows (fixed 0.005, same alarm rate, AUROC) are descriptive only.

