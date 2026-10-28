# V9-T4 -- Siena, all 14 patients (balanced point, localizer cpd, computed in v9)

Gate (step 3): every patient's recomputed tp/fp (seed-by-seed, detector+localized) reproduces results/x1_external/rows_PN*.csv within the tolerance documented in check_repro_ext (tp +-1, fp +-2) -- see gate.csv.

```
subject  passed  exact                                                                                                                                                                                                                                                                                                                                                         detail
   PN00    True   True                                                                                                                                                                                                                                                                                                                                                          exact
   PN01    True  False                                                                                          [('clean_seed1', 'detector', 'fp', 11, 12), ('clean_seed1', 'localized', 'fp', 11, 12), ('clean_seed2', 'detector', 'fp', 12, 13), ('clean_seed2', 'localized', 'fp', 12, 13), ('clean_seed3', 'detector', 'fp', 11, 12), ('clean_seed3', 'localized', 'fp', 11, 12)]
   PN03    True  False [('clean_seed42', 'detector', 'fp', 54, 55), ('clean_seed42', 'localized', 'fp', 53, 54), ('clean_seed1', 'detector', 'fp', 60, 59), ('clean_seed1', 'localized', 'fp', 58, 57), ('clean_seed2', 'detector', 'fp', 56, 55), ('clean_seed2', 'localized', 'fp', 54, 53), ('clean_seed3', 'detector', 'fp', 52, 53), ('clean_seed3', 'localized', 'fp', 51, 52)]
   PN05    True   True                                                                                                                                                                                                                                                                                                                                                          exact
   PN06    True  False                                                                                                                                                                               [('clean_seed42', 'detector', 'fp', 39, 38), ('clean_seed42', 'localized', 'fp', 39, 38), ('clean_seed3', 'detector', 'fp', 36, 35), ('clean_seed3', 'localized', 'fp', 35, 34)]
   PN07    True  False                                                                                                                                    [('clean_seed42', 'detector', 'fp', 35, 36), ('clean_seed42', 'localized', 'fp', 32, 33), ('clean_seed2', 'detector', 'fp', 28, 29), ('clean_seed3', 'detector', 'fp', 32, 31), ('clean_seed3', 'localized', 'fp', 30, 29)]
   PN09    True  False                                                                                                                                                                                                                                                                            [('clean_seed3', 'detector', 'fp', 4, 5), ('clean_seed3', 'localized', 'fp', 4, 5)]
   PN10    True  False                                                                                                  [('clean_seed2', 'detector', 'tp', 6, 5), ('clean_seed2', 'localized', 'tp', 6, 5), ('clean_seed3', 'detector', 'tp', 5, 6), ('clean_seed3', 'detector', 'fp', 21, 20), ('clean_seed3', 'localized', 'tp', 5, 6), ('clean_seed3', 'localized', 'fp', 20, 19)]
   PN11    True   True                                                                                                                                                                                                                                                                                                                                                          exact
   PN12    True  False             [('clean_seed42', 'detector', 'tp', 2, 3), ('clean_seed42', 'detector', 'fp', 9, 8), ('clean_seed42', 'localized', 'tp', 2, 3), ('clean_seed42', 'localized', 'fp', 9, 8), ('clean_seed2', 'detector', 'fp', 10, 8), ('clean_seed2', 'localized', 'fp', 10, 8), ('clean_seed3', 'detector', 'fp', 7, 8), ('clean_seed3', 'localized', 'fp', 7, 8)]
   PN13    True  False                                                                                                                                                                                                                                                                        [('clean_seed42', 'detector', 'fp', 13, 12), ('clean_seed42', 'localized', 'tp', 2, 1)]
   PN14    True  False                                                                                                                                   [('clean_seed42', 'detector', 'fp', 45, 44), ('clean_seed42', 'localized', 'fp', 45, 44), ('clean_seed2', 'detector', 'fp', 49, 48), ('clean_seed2', 'localized', 'fp', 48, 47), ('clean_seed3', 'localized', 'fp', 47, 46)]
   PN16    True  False                                                                                                                                                                               [('clean_seed42', 'detector', 'fp', 18, 19), ('clean_seed42', 'localized', 'fp', 15, 16), ('clean_seed2', 'detector', 'fp', 14, 15), ('clean_seed2', 'localized', 'fp', 13, 14)]
   PN17    True   True                                                                                                                                                                                                                                                                                                                                                          exact
```

## Duration bins, siena-14 (duration_bins.csv)

```
     set    bin  n  caught
siena-14  <=20s  5       3
siena-14 21-40s  6       2
siena-14 41-80s 27      21
siena-14   >80s  9       7
```

## Matched operating point (sweep_siena-14.csv; chb-test/chb24 reused from results/v9_anatomy/)

- chb-test: sensitivity @ FP/day 20=0.318, 27.5=0.355, 44=0.366
- chb24: sensitivity @ FP/day 20=0.626, 27.5=0.875, 44=0.875
- siena-14: sensitivity @ FP/day 20=0.481, 27.5=0.534, 44=0.673

## Siena event F1 / precision, pooled and per-patient mean, frozen operating point (f1_precision_per_seed.csv, f1_precision_summary.csv)

```
seed 42: sens 0.702, prec 0.114, F1 0.196, FP/day 44.01 | per-patient mean: sens 0.754, prec 0.179, F1 0.257
4-seed mean pooled sens: 0.617 +- 0.067
4-seed mean pooled prec: 0.102 +- 0.009
4-seed mean pooled F1: 0.174 +- 0.016
4-seed mean FP/day: 43.885 +- 1.820
4-seed mean per-patient sens: 0.635 +- 0.083
4-seed mean per-patient prec: 0.161 +- 0.012
4-seed mean per-patient F1: 0.226 +- 0.021
```

## False-alarm anatomy, siena-14 (false_alarms.csv, false_alarm_groups.csv)

```
   position  high_amp   n
first_15min     False   3
first_15min      True  13
 last_15min     False   1
 last_15min      True  14
     middle     False  25
     middle      True 197
```

253 false alarms; median duration 40 s; share with >=1 high-amplitude window >= 50% of the event: 89%; top channel mode: FP1-F7.

Elapsed 1 s.