# R3 aggregate — F1 / F2 re-executed on complete data vs the record (earlier data copy)

Gates: A0 PASS, A1 PASS (partitions [1, 2, 3, 4, 5]; r2_r3 ['7dc1697cbf792dff'])

## Pre-registered verdict (src/f1_aggregate.py, unchanged)

```
                    system  n_pos  n_neg  need  dF1_mean  dF1_lo  dF1_hi                                                  verdict
record (earlier data copy)      6      0     5     0.075   0.034   0.121 stable advantage of the MLP-AE (without message passing)
     rerun (complete data)      6      0     5     0.077   0.038   0.120 stable advantage of the MLP-AE (without message passing)
```

## F2 across partitions, record vs rerun

```
     quantity  mean_record  lo_record  hi_record  mean_rerun  lo_rerun  hi_rerun
          dF1        0.075      0.034      0.121       0.077     0.038     0.120
dF1_fixed0005        0.060     -0.012      0.127       0.071     0.008     0.130
        dSens       -0.009     -0.086      0.062       0.006    -0.053     0.059
      dFP_day       -8.133    -10.967     -5.257      -8.012   -10.926    -5.040
       dAUROC        0.082      0.058      0.111       0.084     0.060     0.112
```

## F1 across partitions (GAE, MLP-AE; SD = sensitivity to partition + seed, not uncertainty)

```
model set  n_partitions_record       metric  mean_record  sd_record  min_record  max_record  n_partitions_rerun  mean_rerun  sd_rerun  min_rerun  max_rerun
  gae all                    6         sens        0.736      0.012       0.723       0.753                   6       0.733     0.011      0.713      0.745
  gae all                    6         prec        0.134      0.006       0.128       0.143                   6       0.137     0.008      0.129      0.151
  gae all                    6           f1        0.210      0.009       0.202       0.222                   6       0.211     0.008      0.204      0.225
  gae all                    6       fp_day       27.327      1.070      25.928      28.725                   6      27.352     0.707     26.436     28.227
  gae all                    6        auroc        0.809      0.004       0.802       0.814                   6       0.806     0.006      0.795      0.811
  gae all                    6   sens_test8        0.575      0.013       0.556       0.594                   6       0.565     0.013      0.545      0.575
  gae all                    6 sens_other16        0.817      0.016       0.799       0.842                   6       0.818     0.013      0.793      0.832
  mlp all                    6         sens        0.726      0.018       0.711       0.753                   6       0.739     0.016      0.712      0.760
  mlp all                    6         prec        0.200      0.009       0.189       0.209                   6       0.202     0.006      0.194      0.209
  mlp all                    6           f1        0.285      0.009       0.273       0.295                   6       0.288     0.005      0.282      0.296
  mlp all                    6       fp_day       19.195      0.992      18.281      20.697                   6      19.340     0.660     18.434     19.998
  mlp all                    6        auroc        0.892      0.002       0.890       0.894                   6       0.890     0.002      0.887      0.893
  mlp all                    6   sens_test8        0.533      0.036       0.495       0.588                   6       0.556     0.041      0.500      0.606
  mlp all                    6 sens_other16        0.823      0.016       0.806       0.850                   6       0.831     0.008      0.819      0.841
```

## Per-case means per partition, own point, after CPD (record / cf / rerun)

```
                    f1                fp_day                   sens              
system              cf record  rerun      cf  record   rerun     cf record  rerun
model partition                                                                  
gae   0          0.200  0.203  0.208  28.323  28.387  27.786  0.724  0.735  0.737
      1          0.218  0.222  0.225  26.161  25.928  27.078  0.735  0.735  0.740
      2          0.201  0.203  0.204  27.648  27.393  28.227  0.719  0.723  0.745
      3          0.222  0.222  0.210  26.886  26.596  27.851  0.746  0.746  0.728
      4          0.209  0.207  0.205  27.009  26.936  26.436  0.724  0.724  0.713
      5          0.201  0.202  0.214  28.520  28.725  26.733  0.753  0.753  0.737
mlp   0          0.279  0.273  0.284  20.076  20.183  19.998  0.719  0.711  0.735
      1          0.287  0.289  0.282  18.777  18.652  19.592  0.745  0.745  0.760
      2          0.271  0.276  0.285  20.965  20.697  19.673  0.743  0.753  0.737
      3          0.294  0.294  0.288  18.909  18.775  19.761  0.728  0.720  0.751
      4          0.286  0.286  0.296  18.733  18.580  18.583  0.724  0.715  0.738
      5          0.294  0.295  0.291  18.291  18.281  18.434  0.714  0.714  0.712
```

## Rerun vs record and its split, across partitions (own point, after CPD)

```
model point     stage partition                    step metric   diff     lo    hi  n_cases  n_units  cases_changed
  gae   own localized       all          rerun - record   sens -0.003 -0.013 0.008       24       23             13
  gae   own localized       all          rerun - record     f1  0.001 -0.008 0.010       24       23             24
  gae   own localized       all          rerun - record fp_day  0.024 -0.695 0.836       24       23             23
  gae   own localized       all      data (cf - record)   sens -0.002 -0.006 0.000       24       23              3
  gae   own localized       all      data (cf - record)     f1 -0.001 -0.006 0.002       24       23             24
  gae   own localized       all      data (cf - record) fp_day  0.097 -0.337 0.625       24       23             22
  gae   own localized       all new models (rerun - cf)   sens -0.000 -0.011 0.010       24       23             12
  gae   own localized       all new models (rerun - cf)     f1  0.003 -0.004 0.010       24       23             24
  gae   own localized       all new models (rerun - cf) fp_day -0.073 -0.696 0.591       24       23             23
  mlp   own localized       all          rerun - record   sens  0.013 -0.007 0.036       24       23             10
  mlp   own localized       all          rerun - record     f1  0.002 -0.005 0.010       24       23             24
  mlp   own localized       all          rerun - record fp_day  0.145 -0.315 0.661       24       23             24
  mlp   own localized       all      data (cf - record)   sens  0.002 -0.005 0.013       24       23              2
  mlp   own localized       all      data (cf - record)     f1 -0.000 -0.002 0.002       24       23             20
  mlp   own localized       all      data (cf - record) fp_day  0.097 -0.071 0.269       24       23             18
  mlp   own localized       all new models (rerun - cf)   sens  0.010 -0.005 0.029       24       23             10
  mlp   own localized       all new models (rerun - cf)     f1  0.003 -0.003 0.008       24       23             24
  mlp   own localized       all new models (rerun - cf) fp_day  0.049 -0.418 0.547       24       23             23
```

## dF1 (MLP-AE - GAE) per partition: record, counterfactual, rerun

```
system partition           quantity  diff    lo    hi  n_cases  n_units  cases_changed
record         0 dF1 (MLP-AE - GAE) 0.070 0.026 0.117       24       23             24
record         1 dF1 (MLP-AE - GAE) 0.067 0.027 0.110       24       23             23
record         2 dF1 (MLP-AE - GAE) 0.073 0.031 0.119       24       23             23
record         3 dF1 (MLP-AE - GAE) 0.072 0.023 0.125       24       23             24
record         4 dF1 (MLP-AE - GAE) 0.078 0.037 0.121       24       23             24
record         5 dF1 (MLP-AE - GAE) 0.093 0.042 0.148       24       23             24
record       all dF1 (MLP-AE - GAE) 0.075 0.034 0.121       24       23             24
    cf         0 dF1 (MLP-AE - GAE) 0.078 0.031 0.131       24       23             24
    cf         1 dF1 (MLP-AE - GAE) 0.069 0.030 0.110       24       23             22
    cf         2 dF1 (MLP-AE - GAE) 0.071 0.031 0.116       24       23             23
    cf         3 dF1 (MLP-AE - GAE) 0.072 0.023 0.124       24       23             24
    cf         4 dF1 (MLP-AE - GAE) 0.077 0.036 0.119       24       23             24
    cf         5 dF1 (MLP-AE - GAE) 0.092 0.041 0.147       24       23             24
    cf       all dF1 (MLP-AE - GAE) 0.077 0.035 0.122       24       23             24
 rerun         0 dF1 (MLP-AE - GAE) 0.076 0.036 0.122       24       23             24
 rerun         1 dF1 (MLP-AE - GAE) 0.057 0.023 0.091       24       23             23
 rerun         2 dF1 (MLP-AE - GAE) 0.081 0.037 0.135       24       23             24
 rerun         3 dF1 (MLP-AE - GAE) 0.079 0.039 0.124       24       23             24
 rerun         4 dF1 (MLP-AE - GAE) 0.091 0.044 0.145       24       23             24
 rerun         5 dF1 (MLP-AE - GAE) 0.077 0.036 0.122       24       23             24
 rerun       all dF1 (MLP-AE - GAE) 0.077 0.038 0.120       24       23             24
```

## 8 thesis test patients (descriptive, not pre-registered)

```
 partition model  sens  fp_day    f1  caught  n_ref system
         0   gae 0.581  30.762 0.176      37     76 record
         0   mlp 0.505  25.892 0.195      36     76 record
         1   gae 0.556  30.892 0.170      35     76 record
         1   mlp 0.588  23.956 0.219      37     76 record
         2   gae 0.569  31.557 0.163      36     76 record
         2   mlp 0.560  26.837 0.187      38     76 record
         3   gae 0.594  31.669 0.184      39     76 record
         3   mlp 0.495  24.965 0.202      34     76 record
         4   gae 0.573  30.982 0.170      37     76 record
         4   mlp 0.533  24.981 0.209      39     76 record
         5   gae 0.575  32.604 0.157      37     76 record
         5   mlp 0.515  23.364 0.217      36     76 record
         0   gae 0.575  32.410 0.167      37     76  rerun
         0   mlp 0.553  26.049 0.199      38     76  rerun
         1   gae 0.575  30.111 0.181      37     76  rerun
         1   mlp 0.606  24.869 0.214      40     76  rerun
         2   gae 0.572  33.168 0.155      36     76  rerun
         2   mlp 0.529  25.796 0.193      38     76  rerun
         3   gae 0.545  33.888 0.151      35     76  rerun
         3   mlp 0.600  25.155 0.216      39     76  rerun
         4   gae 0.554  29.487 0.173      35     76  rerun
         4   mlp 0.547  23.943 0.215      38     76  rerun
         5   gae 0.569  31.632 0.165      36     76  rerun
         5   mlp 0.500  23.697 0.210      35     76  rerun
```

## R3.0 gates

```
 partition model status  rows  exact_rows  missing  n_ref_differ  max_abs_dtp  max_abs_dfp  k_max_rel  seizures  caught_differ              tolerance
         1   gae   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         1   mlp   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         2   gae   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         2   mlp   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         3   gae   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         3   mlp   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         4   gae   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         4   mlp   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         5   gae   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
         5   mlp   PASS    96          96        0             0            0            0        0.0       185              0 |dtp| <= 1, |dfp| <= 2
```

The pre-registered reading itself: `f1_reading/` (SUMMARY.md, VERDICT.json). Per subject: `per_subject.csv`; k per fold: `k.csv`; seizures: `seizures.csv`. Descriptive only (plan P2); no row replaces a locked number of the thesis.
