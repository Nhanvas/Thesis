# V9-X6 -- does ASR delete seizure activity?

**Reduced scope (fixed by the author 2026-10-30, before this ran):** Measure 1 (what ASR removes) + the EEG panels only; Measure 2 (effect on B4 detection) was skipped. Files: every seizure-containing file of the 8 CHB-MIT test patients + chb24 (58 + 12 = 70 files), no development patients, no seizure-free matched files. cutoff=20 run over every file first, cutoff=5 afterward as time allowed; 4.5h wall-clock stop.

Full tables: `results/v9_x6/*.csv`. Code: `src/v9_x6_asr.py` (new).

## Coverage
```
cutoff= 20   70/70 files
cutoff=  5    1/70 files
```

## cutoff = 20

### Pooled share of power removed (1 - after/before)
```
seizure span                 n=  92  mean +0.482  median +0.542  p10 +0.000  p90 +0.917
60s pre-seizure              n=  92  mean +0.348  median +0.206  p10 +0.000  p90 +0.819
high-amplitude (label-free) windows n=16503  mean +0.411  median +0.412  p10 +0.000  p90 +0.868
ordinary background windows  n=19467  mean +0.068  median +0.000  p10 +0.000  p90 +0.311
```

### Per patient (seizure-span share removed; test patients + chb24)
```
chb03   seizure n=  7 mean +0.913  |  high-amp n= 819 mean +0.722  |  background n= 1675 mean +0.203
chb06   seizure n= 10 mean +0.024  |  high-amp n=5818 mean +0.224  |  background n= 4948 mean +0.040
chb13   seizure n= 12 mean +0.276  |  high-amp n=1196 mean +0.270  |  background n= 1528 mean +0.021
chb14   seizure n=  8 mean +0.041  |  high-amp n=1454 mean +0.038  |  background n= 2097 mean +0.001
chb15   seizure n= 20 mean +0.348  |  high-amp n=1843 mean +0.678  |  background n= 2131 mean +0.044
chb16   seizure n= 10 mean +0.633  |  high-amp n=1212 mean +0.757  |  background n=  618 mean +0.165
chb17   seizure n=  3 mean +0.778  |  high-amp n=1022 mean +0.700  |  background n= 1088 mean +0.253
chb18   seizure n=  6 mean +0.689  |  high-amp n=1019 mean +0.583  |  background n= 1647 mean +0.094
chb24   seizure n= 16 mean +0.895  |  high-amp n=2120 mean +0.489  |  background n= 3735 mean +0.036
```

### Seizure-span share removed, by duration bin
```
0-20s      n= 32  mean +0.363
20-40s     n= 17  mean +0.520
40-80s     n= 30  mean +0.599
>80s       n= 13  mean +0.457
```

### Seizure-span share removed vs annotated channel count (TEST seizures only, `results/attribution_v7/labels/ictal_channels_FINAL.csv`; n=76, Spearman rho = -0.046)
```
n_ictal 1-3: n= 21  mean share +0.347
n_ictal 4-6: n= 33  mean share +0.429
n_ictal 7-10: n=  8  mean share +0.599
n_ictal 11-max: n= 14  mean share +0.270
```

### Contrast (median-channel RMS of the span / RMS of the preceding 60 s), before vs after ASR, cutoff=20 (patient bootstrap, B=2000)

```
seizure span       n=  92  before 2.087  after 1.407  diff -0.685 [-1.405, -0.120]
high-amp windows   n=16004  before 1.061  after 1.035  diff -0.030 [-0.062, -0.010]
```

Per patient:
```
chb03   seizure n=  7 4.056->1.888       | high-amp n= 771 1.236->1.057
chb06   seizure n= 10 0.779->0.863       | high-amp n=5757 1.061->1.058
chb13   seizure n= 12 1.381->1.215       | high-amp n=1128 1.005->0.994
chb14   seizure n=  8 0.681->0.679       | high-amp n=1408 1.094->1.087
chb15   seizure n= 20 1.337->1.241       | high-amp n=1751 1.017->1.004
chb16   seizure n= 10 1.594->1.504       | high-amp n=1157 1.100->1.028
chb17   seizure n=  3 2.222->1.651       | high-amp n=1006 1.067->1.009
chb18   seizure n=  6 2.927->1.878       | high-amp n= 981 1.074->1.048
chb24   seizure n= 16 4.183->1.967       | high-amp n=2045 1.010->0.982
```

Negative diff = ASR LOWERS the seizure/window contrast (removes what a detector needs); CI excluding 0 is the evidence that matters here, not the point estimate alone.

## cutoff = 5

### Pooled share of power removed (1 - after/before)
```
seizure span                 n=   1  mean +0.986  median +0.986  p10 +0.986  p90 +0.986
60s pre-seizure              n=   1  mean +0.743  median +0.743  p10 +0.743  p90 +0.743
high-amplitude (label-free) windows n=  32  mean +0.843  median +0.844  p10 +0.746  p90 +0.942
ordinary background windows  n=  58  mean +0.708  median +0.737  p10 +0.538  p90 +0.859
```

### Per patient (seizure-span share removed; test patients + chb24)
```
chb03   seizure n=  1 mean +0.986  |  high-amp n=  32 mean +0.843  |  background n=   58 mean +0.708
chb06   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb13   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb14   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb15   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb16   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb17   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb18   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
chb24   seizure n=  0 mean +nan  |  high-amp n=   0 mean +nan  |  background n=    0 mean +nan
```

### Seizure-span share removed, by duration bin
```
0-20s      n=0
20-40s     n=0
40-80s     n=  1  mean +0.986
>80s       n=0
```

### Seizure-span share removed vs annotated channel count (TEST seizures only, `results/attribution_v7/labels/ictal_channels_FINAL.csv`; n=1, Spearman rho = nan)
```
n_ictal 1-3: n=0
n_ictal 4-6: n=0
n_ictal 7-10: n=  1  mean share +0.986
n_ictal 11-max: n=0
```

### Contrast (median-channel RMS of the span / RMS of the preceding 60 s), before vs after ASR, cutoff=5 (patient bootstrap, B=2000)

(contrast measure not available for this cutoff -- see coverage above)