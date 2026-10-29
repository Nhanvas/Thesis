# V9-X1 -- why focal seizures are missed, and a focal-aware ensemble member

Part 0: see `results/v9_x1/part0/SUMMARY.md` (reproduced below is a pointer, not a copy).

Part A full tables: `results/v9_x1/*.csv`, `results/v9_x1/posthoc/*.csv`. Code: `src/v9_x1_focal.py` (new; every frozen script it calls -- p2_scalars, e16_recording_baseline, e17b_latent_family, e18_cpd_localizer, p3_levers, p3_anatomy, e22_test_oneshot, v9_e1_baselines, v9_e1b_calibrate, v9_e2_veto, v9_anatomy, v9_eeg_samples, v9_eeg_evidence -- is read-only and unmodified).

# V9-X1 Part 0 -- why focal seizures are missed (mechanism, no new model)

TIER T-B: CHB-MIT test channel annotations are read (test-informed), as results/p3_anatomy's own test rows already are; logged, not hidden.

## Item 1 -- channel-count vs caught, two stages, CHB-MIT test, seed 42 (focal seizures only)

- **Stage A** (p3_anatomy, fixed detector top-p=0.005): caught median 6.0 ch (n=21) vs missed median 3.0 ch (n=41), Mann-Whitney p=1.20e-04, no caught seizure below 4 channels.
- **Stage B** (final system, per-patient budget + CPD localizer, balanced point) -- detector sub-stage: caught median 4.0 ch (n=32) vs missed median 5.0 ch (n=30), p=0.792, min caught 1 ch; localized sub-stage identical (caught 4.0 vs missed 5.0, p=0.792) -- the CPD localizer itself changes no seizure's caught status here; the per-patient budget (clip(q_i(k), 0.005, 0.02), already adopted as L2) is what moves the picture, BEFORE the localizer runs.

The strong fixed-threshold relationship (stage A) partly washes out once each patient's own budget is applied (stage B): some patients with narrow-footprint seizures already get a wider-than-0.005 per-patient budget, rescuing roughly half of their <=3-channel focal seizures (table below) even under the FROZEN 4-member ensemble -- the per-patient budget, not the member set, is already doing some of this work.

### Annotated channels <=3 vs >=4 x caught/missed (focal only)

Stage A (fixed threshold):
```
caught       False  True 
channels<=3              
False           20     21
True            21      0
```
Stage B (final system, localized):
```
caught_loc   False  True 
channels<=3              
False           20     21
True            10     11
```

### chb06 (generalized, 18 channels, ~16-24 s) -- differs from the focal pattern

Stage A:
```
        file  onset_s  dur_s  n_ictal  caught
chb06_01.edf     1724     16       18   False
chb06_01.edf     7460     16       18   False
chb06_01.edf    13524     16       18   False
chb06_04.edf      324     24       18    True
chb06_04.edf     6208     24       18   False
chb06_09.edf    12500     16       18   False
chb06_10.edf    10832     16       18   False
chb06_13.edf      504     16       18    True
chb06_18.edf     7796     16       18   False
chb06_24.edf     9384     20       18   False
```
Stage B:
```
        file  onset_s  dur_s  n_ictal  caught_det  caught_loc
chb06_01.edf     1724     16       18       False       False
chb06_01.edf     7460     16       18       False       False
chb06_01.edf    13524     16       18       False       False
chb06_04.edf      324     24       18        True        True
chb06_04.edf     6208     24       18       False       False
chb06_09.edf    12500     16       18       False       False
chb06_10.edf    10832     16       18       False       False
chb06_13.edf      504     16       18        True        True
chb06_18.edf     7796     16       18       False       False
chb06_24.edf     9384     20       18       False       False
```

chb15 (median 2 channels): stage A 0/20 caught; stage B (localized) 11/20 caught.

## Item 2 -- mechanism: peak within-patient percentile of the r-th-largest-channel member, by annotated channel bucket and stage-A caught/missed (results/p3_anatomy/seizures.csv, already-computed pn_S{1,3,6,9,12}e columns, test rows, seed 42)

```
channels    <=3    >=4       
caught    False  False  True 
r                            
1         0.979  0.968  0.996
3         0.981  0.950  0.998
6         0.982  0.957  0.998
9         0.984  0.956  0.998
12        0.983  0.944  0.999
```

Expected if the hypothesis holds: missed, <=3-channel seizures high (low percentile) on r=1-3, low (high percentile) on r>=6. See mechanism.png.


## Item 3 -- CAR vs bipolar (src/c1b_build_trainset.py)

src/c1b_build_trainset.py: graph_and_bp(zw) computes `car = CE.GC.apply_car(zw[i])` and feeds car ONLY into the wPLI/AEC adjacency (`adj[i] = ... compute_wpli(car), compute_aec(car) ...`), the GNN's message-passing GRAPH. Both node-feature blocks that the GAE actually reconstructs -- `bp[i] = CE.FE.compute_band_powers(zw[i])` and `f7(zw)` (called as `parts['f7'].append(f7(zw))`, build(), line ~124) -- are computed on `zw` directly, the BIPOLAR double-banana z-scored signal, never on `car`. So: the per-channel reconstruction TARGET (and therefore the per-channel distance D that every ensemble member, r-th-largest or mean, is built from) stays bipolar -- in the 18-channel double banana each electrode appears in <=2 pairs, so a single bad electrode can only ever inflate <=2 of the 18 channel distances directly. CAR enters only through the adjacency (connectivity estimate for graph message-passing); if CAR itself smears a single-electrode artifact into the common average, that can still let the artifact's INFLUENCE reach other channels indirectly through GNN message-passing edges, even though their own reconstruction target is untouched -- a weaker, indirect path, not the direct one the r-th-largest-member construction is designed against.

Elapsed 20 s.

## Part A -- calibration

k_G = 3.970892, k_B4 = 11.188265, k_F = 1.895471 (primary, members [3, 6, 9, 12, 'mean']); descriptive secondary (2nd largest, development only): k_G2 = 3.961213, k_F2 = 1.917500.

### dev (15 patients)
```
G (GAE, members 3/6/9/12+mean)                   tp/ref 64/94  fp 655  sens 0.681  prec 0.089  F1 0.157  FP/day 23.38
B4 (kNN, members 3/6/9/12+mean)                  tp/ref 71/94  fp 451  sens 0.755  prec 0.136  F1 0.231  FP/day 16.10
F (fusion G+B4, members 3/6/9/12+mean)           tp/ref 67/94  fp 536  sens 0.713  prec 0.111  F1 0.192  FP/day 19.14
G2 descriptive (GAE, members 2/6/9/12+mean)      tp/ref 63/94  fp 642  sens 0.670  prec 0.089  F1 0.158  FP/day 22.92
F2 descriptive (fusion, members 2/6/9/12+mean)   tp/ref 66/94  fp 548  sens 0.702  prec 0.107  F1 0.186  FP/day 19.56
```

### test (8 patients)
```
G (GAE, members 3/6/9/12+mean)                   tp/ref 34/76  fp 328  sens 0.447  prec 0.094  F1 0.155  FP/day 28.35
B4 (kNN, members 3/6/9/12+mean)                  tp/ref 31/76  fp 214  sens 0.408  prec 0.127  F1 0.193  FP/day 18.50
F (fusion G+B4, members 3/6/9/12+mean)           tp/ref 38/76  fp 311  sens 0.500  prec 0.109  F1 0.179  FP/day 26.88
```

### chb24 (1 patients)
```
G (GAE, members 3/6/9/12+mean)                   tp/ref 14/16  fp 25  sens 0.875  prec 0.359  F1 0.509  FP/day 28.38
B4 (kNN, members 3/6/9/12+mean)                  tp/ref 13/16  fp 16  sens 0.812  prec 0.448  F1 0.578  FP/day 18.16
F (fusion G+B4, members 3/6/9/12+mean)           tp/ref 14/16  fp 12  sens 0.875  prec 0.538  F1 0.667  FP/day 13.62
```

### siena14 (14 patients)
```
G (GAE, members 3/6/9/12+mean)                   tp/ref 34/47  fp 262  sens 0.723  prec 0.115  F1 0.198  FP/day 44.87
B4 (kNN, members 3/6/9/12+mean)                  tp/ref 27/47  fp 117  sens 0.574  prec 0.188  F1 0.283  FP/day 20.04
F (fusion G+B4, members 3/6/9/12+mean)           tp/ref 28/47  fp 164  sens 0.596  prec 0.146  F1 0.234  FP/day 28.09
```

## Paired patient bootstrap vs the SAME arm without the change (B=10,000)

```
    set arm  fa_target  mean_diff   ci_lo   ci_hi  share_gt0  n_patients
    dev   G       20.0    -0.0034 -0.0249  0.0140     0.3983          15
    dev   G       27.5    -0.0043 -0.0145  0.0035     0.1861          15
    dev   G       44.0    -0.0087 -0.0201 -0.0005     0.0000          15
    dev   F       20.0     0.0099 -0.0030  0.0306     0.8398          15
    dev   F       27.5     0.0081 -0.0028  0.0242     0.8761          15
    dev   F       44.0     0.0042 -0.0073  0.0146     0.7785          15
   test   G       20.0        NaN     NaN     NaN        NaN           0
   test   G       27.5    -0.0300 -0.0651  0.0000     0.0250           8
   test   G       44.0    -0.0237 -0.0438 -0.0050     0.0036           8
   test   F       20.0        NaN     NaN     NaN        NaN           0
   test   F       27.5     0.0049 -0.0002  0.0118     0.9148           8
   test   F       44.0     0.0047 -0.0017  0.0118     0.9197           8
siena14   G       20.0     0.0169 -0.0038  0.0462     0.8932          14
siena14   G       27.5    -0.0132 -0.0403  0.0112     0.1594          14
siena14   G       44.0    -0.0169 -0.0472  0.0089     0.1171          14
siena14   F       20.0     0.0164 -0.0019  0.0486     0.8849          14
siena14   F       27.5     0.0085 -0.0061  0.0303     0.7771          14
siena14   F       44.0    -0.0000 -0.0070  0.0099     0.4603          14
```

### Adoption rule (fixed): dev paired diff @ 27.5 FP/day, point estimate > 0 AND 95% CI lower bound >= -0.02

- G: mean diff -0.0043, 95% CI [-0.0145, +0.0035] -> **NOT adopted**
- F: mean diff +0.0081, 95% CI [-0.0028, +0.0242] -> **ADOPTED**

## Detections by annotated channel count (test, new arm G, focal only)

```
caught   False  True 
n_ictal              
False       21     20
True        10     11
```

## Onset/offset |error| (median s), new arm, test

```
G (GAE, members 3/6/9/12+mean)                   onset median  16.0 s IQR [4.0, 32.0] bias  +8.0 | offset median  28.0 s IQR [8.0, 52.0] bias +16.0
F (fusion G+B4, members 3/6/9/12+mean)           onset median   4.0 s IQR [4.0, 20.0] bias  +4.0 | offset median  24.0 s IQR [12.0, 48.0] bias +16.0
```

## False-alarm types (arm G, test, same rule as results/v9_v1/ Part 4; scoped to test only -- see module docstring)

```
fp_type   n    share
     f1  11 0.034268
     f2 243 0.757009
     f3  28 0.087227
     f4  39 0.121495
```

## EEG evidence
3 panels at `F:\Study\Thesis\Defense\slides\figs\eeg_evidence\x1` (newly-caught / newly-lost test seizures, shortest first, strips r=1,3,9).