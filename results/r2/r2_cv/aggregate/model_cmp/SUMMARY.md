# Model comparison rev 2 -- CHB-MIT, 4-fold patient-wise CV, 24 cases, seed 42

Gates not PASS: 0; jobs not run: 0. Per-case means, own label-free point, after CPD.

| model | sensitivity | precision | F1 | FP/day | window AUROC |
|---|---|---|---|---|---|
| GAE (graph autoencoder, label-free) | 0.737 | 0.134 | 0.208 | 27.8 | 0.795 |
| MLP autoencoder (no graph, label-free) | 0.735 | 0.198 | 0.284 | 20.0 | 0.890 |
| Isolation Forest (label-free) | 0.688 | 0.142 | 0.213 | 24.1 | 0.851 |
| Linear SVM (supervised) | 0.632 | 0.097 | 0.162 | 32.8 | 0.809 |
| Gradient-boosted trees (supervised) | 0.736 | 0.125 | 0.200 | 36.6 | 0.867 |
| 1-D CNN (supervised) | 0.754 | 0.147 | 0.218 | 33.4 | 0.832 |

## B · paired subject bootstrap (model - GAE)

```
model reference metric  n_cases  n_units   diff     lo     hi  wins  ties  losses most_influential_unit  diff_without_it
  mlp       gae     f1       24       23  0.076  0.036  0.122    18     0       6                 chb05            0.061
  mlp       gae   sens       24       23 -0.002 -0.064  0.063     5    15       4                 chb20           -0.024
   if       gae     f1       24       23  0.005 -0.030  0.042    11     0      13                 chb20           -0.004
   if       gae   sens       24       23 -0.049 -0.111  0.014     3    12       9                 chb20           -0.068
  svm       gae     f1       24       23 -0.047 -0.094 -0.003    10     0      14                 chb01           -0.057
  svm       gae   sens       24       23 -0.105 -0.179 -0.040     1    12      11                 chb04           -0.088
  hgb       gae     f1       24       23 -0.008 -0.055  0.034    13     1      10                 chb01           -0.018
  hgb       gae   sens       24       23 -0.001 -0.113  0.104     8    11       5                 chb01           -0.035
  cnn       gae     f1       24       23  0.009 -0.035  0.052    12     1      11                 chb10            0.019
  cnn       gae   sens       24       23  0.017 -0.066  0.097     6    13       5                 chb01           -0.004
```

## C · sensitivity at the GAE's FP/day

```
model  sens_at_gae_fp_day  gae_fp_day
  gae               0.681      27.786
  mlp               0.787      27.786
   if               0.699      27.786
  svm               0.628      27.786
  hgb               0.745      27.786
  cnn               0.762      27.786
```

## D · per-seizure complementarity with the GAE

```
model      group   n  amp_ratio_median  duration_median
  mlp       both 103             2.393             68.0
  mlp   gae_only  11             1.458             28.0
  mlp model_only  16             1.357             32.0
  mlp    neither  55             1.285             32.0
   if       both  89             2.665             68.0
   if   gae_only  25             1.339             36.0
   if model_only   9             1.593             32.0
   if    neither  62             1.280             32.0
  svm       both  86             2.509             72.0
  svm   gae_only  28             1.344             32.0
  svm model_only   5             0.996             24.0
  svm    neither  66             1.303             32.0
  hgb       both  95             2.388             72.0
  hgb   gae_only  19             1.148             28.0
  hgb model_only  22             1.383             48.0
  hgb    neither  49             1.275             28.0
  cnn       both 100             2.390             72.0
  cnn   gae_only  14             1.087             26.0
  cnn model_only  21             1.534             48.0
  cnn    neither  50             1.263             26.0
```

## F · window AUROC vs event F1

```
model  spearman_auroc_vs_f1     p  n
  gae                 0.464 0.022 24
  mlp                 0.396 0.056 24
   if                 0.564 0.004 24
  svm                 0.457 0.025 24
  hgb                 0.405 0.049 24
  cnn                 0.337 0.107 24
```
