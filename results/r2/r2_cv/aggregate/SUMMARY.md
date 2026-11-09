# R2 aggregate — four-fold CV and six models re-executed on complete data vs the record (descriptive)

Gates: A0 PASS, A1 PASS (counterfactual models: ['cnn', 'gae', 'mlp'])

## Per-case means, own label-free point, after CPD (record / counterfactual / rerun)

```
           f1                fp_day                   sens              
system     cf record  rerun      cf  record   rerun     cf record  rerun
model                                                                   
gae     0.200  0.203  0.208  28.323  28.387  27.786  0.724  0.735  0.737
mlp     0.279  0.273  0.284  20.076  20.183  19.998  0.719  0.711  0.735
if        NaN  0.212  0.213     NaN  24.084  24.114    NaN  0.680  0.688
svm       NaN  0.163  0.162     NaN  33.730  32.817    NaN  0.626  0.632
hgb       NaN  0.221  0.200     NaN  35.206  36.591    NaN  0.755  0.736
cnn     0.217  0.218  0.218  34.831  35.111  33.418  0.777  0.777  0.754
```

## Model - GAE (paired subject bootstrap): record vs rerun

```
model metric  diff_record  lo_record  hi_record  diff_rerun  lo_rerun  hi_rerun
  mlp     f1        0.070      0.026      0.117       0.076     0.036     0.122
  mlp   sens       -0.024     -0.115      0.061      -0.002    -0.064     0.063
   if     f1        0.008     -0.030      0.047       0.005    -0.030     0.042
   if   sens       -0.055     -0.124      0.011      -0.049    -0.111     0.014
  svm     f1       -0.041     -0.087      0.004      -0.047    -0.094    -0.003
  svm   sens       -0.109     -0.207     -0.024      -0.105    -0.179    -0.040
  hgb     f1        0.018     -0.035      0.065      -0.008    -0.055     0.034
  hgb   sens        0.020     -0.086      0.115      -0.001    -0.113     0.104
  cnn     f1        0.014     -0.032      0.056       0.009    -0.035     0.052
  cnn   sens        0.042     -0.045      0.124       0.017    -0.066     0.097
```

## Rerun vs record and its split (own point, after CPD)

```
model point     stage                                               step metric   diff     lo     hi  n_cases  n_units  cases_changed
  gae   own localized                                     rerun - record   sens  0.002 -0.027  0.037       24       23              6
  gae   own localized                                     rerun - record     f1  0.005 -0.011  0.020       24       23             23
  gae   own localized                                     rerun - record fp_day -0.601 -2.170  0.970       24       23             23
  gae   own localized                                 data (cf - record)   sens -0.010 -0.029  0.000       24       23              1
  gae   own localized                                 data (cf - record)     f1 -0.003 -0.008  0.001       24       23             20
  gae   own localized                                 data (cf - record) fp_day -0.064 -0.450  0.310       24       23             20
  gae   own localized                            new models (rerun - cf)   sens  0.013 -0.022  0.051       24       23              7
  gae   own localized                            new models (rerun - cf)     f1  0.008 -0.009  0.025       24       23             24
  gae   own localized                            new models (rerun - cf) fp_day -0.537 -2.099  1.036       24       23             24
  mlp   own localized                                     rerun - record   sens  0.024 -0.005  0.062       24       23              5
  mlp   own localized                                     rerun - record     f1  0.011 -0.003  0.026       24       23             19
  mlp   own localized                                     rerun - record fp_day -0.185 -1.027  0.679       24       23             19
  mlp   own localized                                 data (cf - record)   sens  0.008  0.000  0.026       24       23              1
  mlp   own localized                                 data (cf - record)     f1  0.006 -0.000  0.014       24       23             11
  mlp   own localized                                 data (cf - record) fp_day -0.107 -0.351  0.148       24       23             11
  mlp   own localized                            new models (rerun - cf)   sens  0.016 -0.010  0.051       24       23              4
  mlp   own localized                            new models (rerun - cf)     f1  0.006 -0.007  0.019       24       23             20
  mlp   own localized                            new models (rerun - cf) fp_day -0.078 -0.877  0.726       24       23             20
   if   own localized                                     rerun - record   sens  0.008  0.000  0.026       24       23              1
   if   own localized                                     rerun - record     f1  0.002 -0.001  0.006       24       23             11
   if   own localized                                     rerun - record fp_day  0.029 -0.270  0.288       24       23             12
   if   own localized data (rerun - record; no training / deterministic)   sens  0.008  0.000  0.026       24       23              1
   if   own localized data (rerun - record; no training / deterministic)     f1  0.002 -0.001  0.006       24       23             11
   if   own localized data (rerun - record; no training / deterministic) fp_day  0.029 -0.270  0.288       24       23             12
  svm   own localized                                     rerun - record   sens  0.006 -0.037  0.046       24       23              8
  svm   own localized                                     rerun - record     f1 -0.001 -0.016  0.012       24       23             21
  svm   own localized                                     rerun - record fp_day -0.914 -2.587  0.749       24       23             23
  svm   own localized data (rerun - record; no training / deterministic)   sens  0.006 -0.037  0.046       24       23              8
  svm   own localized data (rerun - record; no training / deterministic)     f1 -0.001 -0.016  0.012       24       23             21
  svm   own localized data (rerun - record; no training / deterministic) fp_day -0.914 -2.587  0.749       24       23             23
  hgb   own localized                                     rerun - record   sens -0.019 -0.053  0.003       24       23              4
  hgb   own localized                                     rerun - record     f1 -0.021 -0.038 -0.006       24       23             21
  hgb   own localized                                     rerun - record fp_day  1.386 -1.392  4.012       24       23             22
  hgb   own localized data (rerun - record; no training / deterministic)   sens -0.019 -0.053  0.003       24       23              4
  hgb   own localized data (rerun - record; no training / deterministic)     f1 -0.021 -0.038 -0.006       24       23             21
  hgb   own localized data (rerun - record; no training / deterministic) fp_day  1.386 -1.392  4.012       24       23             22
  cnn   own localized                                     rerun - record   sens -0.023 -0.079  0.023       24       23              7
  cnn   own localized                                     rerun - record     f1 -0.000 -0.024  0.029       24       23             23
  cnn   own localized                                     rerun - record fp_day -1.694 -8.320  4.025       24       23             24
  cnn   own localized                                 data (cf - record)   sens  0.000  0.000  0.000       24       23              0
  cnn   own localized                                 data (cf - record)     f1 -0.001 -0.004  0.001       24       23             13
  cnn   own localized                                 data (cf - record) fp_day -0.280 -0.862  0.279       24       23             13
  cnn   own localized                            new models (rerun - cf)   sens -0.023 -0.079  0.023       24       23              7
  cnn   own localized                            new models (rerun - cf)     f1  0.001 -0.021  0.030       24       23             23
  cnn   own localized                            new models (rerun - cf) fp_day -1.413 -7.982  4.413       24       23             24
```

## Own-point k per fold

```
model  fold  k_record  k_rerun   k_cf
  cnn     1    0.6073   0.6184 0.6144
  cnn     2    0.5206   0.5787 0.5218
  cnn     3    0.5851   0.5993 0.5851
  cnn     4    0.4667   0.5012 0.4672
  gae     1    4.0775   3.9173 4.0817
  gae     2    3.8550   3.9359 3.8440
  gae     3    3.5109   3.9620 3.5486
  gae     4    3.8213   3.5446 3.8417
  hgb     1    0.2111   0.2184    NaN
  hgb     2    0.2028   0.1999    NaN
  hgb     3    0.2338   0.2270    NaN
  hgb     4    0.1230   0.0997    NaN
   if     1    5.4250   5.4088    NaN
   if     2    4.7648   4.7761    NaN
   if     3    4.7648   4.7761    NaN
   if     4    4.7920   4.7853    NaN
  mlp     1    6.1634   6.0974 6.1354
  mlp     2    6.7648   6.4730 6.6808
  mlp     3    5.9255   5.9212 5.9762
  mlp     4    6.5881   6.1421 6.5891
  svm     1    0.6354   0.6229    NaN
  svm     2    0.6751   0.6696    NaN
  svm     3    0.6476   0.6513    NaN
  svm     4    0.6557   0.6641    NaN
```

## Seizures caught, record vs rerun

```
model  seizures  unmatched  caught_record  caught_rerun  both  record_only  rerun_only  neither
  cnn       185          0            123           121   113           10           8       54
  gae       185          0            114           114   110            4           4       67
  hgb       185          0            120           117   113            7           4       61
   if       185          0             97            98    97            0           1       87
  mlp       185          0            115           119   114            1           5       65
  svm       185          0             92            91    83            9           8       85
```

Pre-registered analyses A-F on the rerun: `model_cmp/`. Per row: `rows_vs_record.csv`; per subject: `per_subject.csv`. Descriptive only (plan P2); no row replaces a locked number of the thesis.
