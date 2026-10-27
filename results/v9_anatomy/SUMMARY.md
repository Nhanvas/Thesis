# V9-T3 Part A -- failure anatomy of the final P3 frozen system (balanced point, localizer cpd, seed 42), computed in v9

Reproduction: development vs results/p3c_freeze/per_subject.csv, CHB-MIT test vs results/e23_test_look7/per_subject_seed.csv, chb24/Siena vs results/x1_external/rows_*.csv (4 seeds, detector + localized) -- all passed before any number below was computed.

**Data availability**: chb24's raw EDF (22 files) is fully present. Siena's raw EDF is present for only 3/14 patients in this checkout (PN00, PN10, PN11); PN01, PN03, PN05, PN06, PN07, PN09, PN12, PN13, PN14, PN16, PN17 are absent, so every Siena number tagged 'siena-3of14' below is restricted to those 3 patients and is NOT the full Siena set (item 4, the aggregate check, needs no raw data and uses all 14 from the committed results/x1_external/rows_PN*.csv).

## 1-2. Per-seizure table and duration bins (computed in v9: results/v9_anatomy/per_seizure.csv, duration_bins.csv)

```
        set    bin  n  caught
development  <=20s  3       2
development 21-40s 30      13
development 41-80s 29      19
development   >80s 31      29
   chb-test  <=20s 24       7
   chb-test 21-40s 12       4
   chb-test 41-80s 27      16
   chb-test   >80s 13      11
      chb24  <=20s  4       2
      chb24 21-40s  9       9
      chb24 41-80s  3       3
      chb24   >80s  0       0
siena-3of14  <=20s  4       2
siena-3of14 21-40s  2       1
siena-3of14 41-80s 10      10
siena-3of14   >80s  0       0
```

chb-test: 38/76 seizures caught after the localizer (seed 42, E1 overlap rule -- p2_scalars.caught, a descriptive per-seizure count; the reproduction gate above checks the official SzCORE tp/fp used for sensitivity, which can differ by about 1 seizure from this count on sets with split/merged events). Missed seizures' median p_need = 0.0372 (n=38).

chb24: 14/16 seizures caught after the localizer (seed 42, same E1-overlap convention). Missed seizures' median p_need = 0.0218 (n=2).

siena-3of14: 13/16 seizures caught after the localizer (seed 42, same E1-overlap convention). Missed seizures' median p_need = 0.0183 (n=3).

## 3. Matched operating point (characterisation, detector stage, seed 42, results/v9_anatomy/sweep_*.csv, matched_operating_point.png)

- chb-test: sensitivity @ FP/day 20=0.318, 27.5=0.355, 44=0.366
- chb24: sensitivity @ FP/day 20=0.626, 27.5=0.875, 44=0.875
- siena-3of14: sensitivity @ FP/day 20=0.626, 27.5=0.688, 44=0.801

## 4. Siena aggregate check, all 14 patients (results/v9_anatomy/siena_per_patient.csv, siena_aggregate.json)

```
{
 "per_patient_mean_all": 0.6333333333333334,
 "per_patient_mean_ex_le2": 0.5302083333333334,
 "pooled_sens_all": 0.6170212765957447,
 "pooled_sens_ex_le2": 0.5675675675675675,
 "n_patients_le2": 6,
 "patients_le2": [
  "PN01",
  "PN03",
  "PN07",
  "PN11",
  "PN16",
  "PN17"
 ]
}
```

## 5. False-alarm anatomy (results/v9_anatomy/false_alarms.csv, false_alarm_groups.csv)

```
        set    position  high_amp   n
   chb-test first_15min     False   9
   chb-test first_15min      True  64
   chb-test  last_15min     False  13
   chb-test  last_15min      True  53
   chb-test      middle     False  47
   chb-test      middle      True 125
      chb24 first_15min      True   9
      chb24  last_15min     False   1
      chb24  last_15min      True   6
      chb24      middle      True  10
siena-3of14 first_15min     False   1
siena-3of14 first_15min      True   1
siena-3of14  last_15min      True   1
siena-3of14      middle     False   1
siena-3of14      middle      True  19
```

Median FP duration 36 s; share with >=1 high-amplitude window >= 50% of the event: 80.00%; top channel mode: FP1-F7; median distance to the nearest reference seizure (within file): 1592 s (n with a seizure in the same file = 108/360).

## Findings (computed in v9)

- [chb-test, per_seizure.csv] 38/76 seizures caught after the localizer (seed 42, balanced point).
- [chb24, per_seizure.csv] 14/16 seizures caught after the localizer (seed 42, balanced point).
- [siena-3of14, per_seizure.csv] 13/16 seizures caught after the localizer (seed 42, balanced point).
- [duration_bins.csv] development/<=20s: 2/3; development/21-40s: 13/30; development/41-80s: 19/29; development/>80s: 29/31; chb-test/<=20s: 7/24; chb-test/21-40s: 4/12; chb-test/41-80s: 16/27; chb-test/>80s: 11/13; chb24/<=20s: 2/4; chb24/21-40s: 9/9; chb24/41-80s: 3/3; siena-3of14/<=20s: 2/4; siena-3of14/21-40s: 1/2; siena-3of14/41-80s: 10/10
- [chb-test, sweep_chb-test.csv] sensitivity 0.355 at FP/day 27.5 (CHB-MIT test's own balanced-point rate), global budget, detector stage.
- [chb24, sweep_chb24.csv] sensitivity 0.875 at FP/day 27.5 (CHB-MIT test's own balanced-point rate), global budget, detector stage.
- [siena-3of14, sweep_siena-3of14.csv] sensitivity 0.688 at FP/day 27.5 (CHB-MIT test's own balanced-point rate), global budget, detector stage.
- [siena_aggregate.json] pooled sensitivity 0.617 vs per-patient mean 0.633 (all 14); excluding the 6 patients with <=2 seizures: pooled 0.568 vs per-patient mean 0.530.
- [false_alarms.csv] 360 false alarms (seed 42, balanced, after the localizer: chb-test=311, chb24=26, siena-3of14=23); 80% have >=1 high-amplitude channel in at least half their windows.

Elapsed 737 s.