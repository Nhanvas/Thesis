# Model comparison rev 2 -- CHB-MIT, 4-fold patient-wise CV, 24 cases, seed 42

Gates not PASS: 0; jobs not run: 0. Per-case means, own label-free point, after CPD.

| model | sensitivity | precision | F1 | FP/day | window AUROC |
|---|---|---|---|---|---|
| GAE (graph autoencoder, label-free) | 0.735 | 0.128 | 0.203 | 28.4 | 0.802 |
| MLP autoencoder (no graph, label-free) | 0.711 | 0.189 | 0.273 | 20.2 | 0.890 |
| Isolation Forest (label-free) | 0.680 | 0.141 | 0.212 | 24.1 | 0.852 |
| Linear SVM (supervised) | 0.626 | 0.099 | 0.163 | 33.7 | 0.810 |
| Gradient-boosted trees (supervised) | 0.755 | 0.145 | 0.221 | 35.2 | 0.870 |
| 1-D CNN (supervised) | 0.777 | 0.143 | 0.218 | 35.1 | 0.843 |

## B · paired subject bootstrap (model - GAE)

```
model reference metric  n_cases  n_units   diff     lo     hi  wins  ties  losses most_influential_unit  diff_without_it
  mlp       gae     f1       24       23  0.070  0.026  0.117    18     0       6                 chb05            0.059
  mlp       gae   sens       24       23 -0.024 -0.115  0.061     5    12       7                 chb17            0.004
   if       gae     f1       24       23  0.008 -0.030  0.047    14     0      10                 chb08           -0.001
   if       gae   sens       24       23 -0.055 -0.124  0.011     3    12       9                 chb19           -0.072
  svm       gae     f1       24       23 -0.041 -0.087  0.004    10     0      14                 chb01           -0.051
  svm       gae   sens       24       23 -0.109 -0.207 -0.024     1    15       8                 chb04           -0.081
  hgb       gae     f1       24       23  0.018 -0.035  0.065    12     1      11                 chb01            0.007
  hgb       gae   sens       24       23  0.020 -0.086  0.115     7    14       3                 chb14            0.053
  cnn       gae     f1       24       23  0.014 -0.032  0.056    15     0       9                 chb05            0.025
  cnn       gae   sens       24       23  0.042 -0.045  0.124     9    11       4                 chb14            0.066
```

## C · sensitivity at the GAE's FP/day

```
model  sens_at_gae_fp_day  gae_fp_day
  gae               0.703      28.387
  mlp               0.787      28.387
   if               0.704      28.387
  svm               0.618      28.387
  hgb               0.747      28.387
  cnn               0.753      28.387
```

## D · per-seizure complementarity with the GAE

```
model      group  n  amp_ratio_median  duration_median
  mlp       both 98             2.420             68.0
  mlp   gae_only 16             1.537             34.0
  mlp model_only 17             1.423             32.0
  mlp    neither 54             1.280             32.0
   if       both 88             2.634             68.0
   if   gae_only 26             1.374             36.0
   if model_only  9             1.569             52.0
   if    neither 62             1.273             32.0
  svm       both 82             2.612             72.0
  svm   gae_only 32             1.555             34.0
  svm model_only 10             1.140             52.0
  svm    neither 61             1.291             32.0
  hgb       both 96             2.305             72.0
  hgb   gae_only 18             1.125             28.0
  hgb model_only 24             1.322             48.0
  hgb    neither 47             1.270             28.0
  cnn       both 99             2.388             68.0
  cnn   gae_only 15             1.148             24.0
  cnn model_only 24             1.280             50.0
  cnn    neither 47             1.285             28.0
```

## F · window AUROC vs event F1

```
model  spearman_auroc_vs_f1     p  n
  gae                 0.468 0.021 24
  mlp                 0.476 0.019 24
   if                 0.557 0.005 24
  svm                 0.417 0.043 24
  hgb                 0.462 0.023 24
  cnn                 0.502 0.012 24
```
