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