# Application-detection scoring -- SUMMARY

Scores the SzScan web demo application's own exported AI detections against the seizure annotation. A separate evaluation tier; never merged with the offline numbers (project instructions Sec.11.5).

Application build commit (from `web_demo/REPORT_HANDBACK.md`): `0ffd99b0a301515e1251bece77d236d838632ab0`

## Per-subject

```
subject  files   hours  seizures  detected  false_alarms  sensitivity  precision        f1  false_alarms_per_day
  chb03     38 38.0017         7         1            69     0.142857   0.014286  0.025974             43.705463
  chb06     18 66.7350        10         3           101     0.300000   0.028846  0.052632             36.345916
  chb13     33 33.0000        12         3            63     0.250000   0.045455  0.076923             46.025451
  chb14     26 26.0000         8         3            99     0.375000   0.029412  0.054545             91.549914
  chb15     40 40.0100        20         4           145     0.200000   0.026846  0.047337             88.198023
  chb16     19 19.0000        10         0            25     0.000000   0.000000 undefined             31.617776
  chb17     21 21.0067         3         0            48     0.000000   0.000000 undefined             55.053033
  chb18     36 35.6347         6         2            58     0.333333   0.033333  0.060606             39.159790
```

## Pooled (all subjects)

- files: 231
- hours: 279.3881
- seizures: 76
- detected: 16
- false_alarms: 608
- sensitivity: 0.21052631578947367
- precision: 0.02564102564102564
- f1: 0.045714285714285714
- false_alarms_per_day: 52.4340920615021

## Boundary-crossing events

Events split across a file boundary (CC_PROMPT_SCORER_BOUNDARY.md): the part beyond L = n_windows * 4 s of a file is carried to the start of the next file in sorted file-name order, matching the offline evaluation's own concatenated per-subject timeline (szcore_eval.py).

- chb06: 0 event(s) crossed a file boundary, 0 s moved
- chb03: 0 event(s) crossed a file boundary, 0 s moved
- chb13: 0 event(s) crossed a file boundary, 0 s moved
- chb14: 0 event(s) crossed a file boundary, 0 s moved
- chb15: 2 event(s) crossed a file boundary, 268 s moved
- chb16: 0 event(s) crossed a file boundary, 0 s moved
- chb17: 1 event(s) crossed a file boundary, 20 s moved
- chb18: 0 event(s) crossed a file boundary, 0 s moved

## Coverage checks

- chb03: 38 EDF(s) on disk, 38 in files.csv, 0 not processed, 38 non-success status
- chb06: 18 EDF(s) on disk, 18 in files.csv, 0 not processed, 18 non-success status
- chb13: 33 EDF(s) on disk, 33 in files.csv, 0 not processed, 33 non-success status
- chb14: 26 EDF(s) on disk, 26 in files.csv, 0 not processed, 26 non-success status
- chb15: 40 EDF(s) on disk, 40 in files.csv, 0 not processed, 40 non-success status
- chb16: 19 EDF(s) on disk, 19 in files.csv, 0 not processed, 19 non-success status
- chb17: 21 EDF(s) on disk, 21 in files.csv, 0 not processed, 21 non-success status
- chb18: 36 EDF(s) on disk, 36 in files.csv, 0 not processed, 36 non-success status
- chb03: 7/7 annotated seizures in processed files
- chb06: 10/10 annotated seizures in processed files
- chb13: 12/12 annotated seizures in processed files
- chb14: 8/8 annotated seizures in processed files
- chb15: 20/20 annotated seizures in processed files
- chb16: 10/10 annotated seizures in processed files
- chb17: 3/3 annotated seizures in processed files
- chb18: 6/6 annotated seizures in processed files
- Total annotated seizures in processed files: 76/76
- Total processed hours: 279.39 vs 279.39 (report Table 2.1), delta -0.00 h

## Coverage issues

- **chb03/chb03_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_20.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_21.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_22.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_23.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_24.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_25.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_26.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_27.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_28.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_29.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_30.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_31.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_32.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_33.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_34.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_35.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_36.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_37.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb03/chb03_38.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb06/chb06_24.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_21.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_22.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_24.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_30.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_36.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_37.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_38.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_39.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_40.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_47.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_55.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_56.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_58.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_59.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_60.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb13/chb13_62.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_20.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_22.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_24.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_25.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_26.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_27.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_29.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_30.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_32.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_37.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_39.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb14/chb14_42.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_20.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_22.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_26.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_28.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_29.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_30.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_31.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_32.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_33.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_35.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_37.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_40.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_45.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_46.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_49.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_50.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_51.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_52.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_54.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_61.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_62.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb15/chb15_63.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb16/chb16_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17a_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17a_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17a_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17a_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17a_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_57.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_58.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_59.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_60.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_63.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_67.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_68.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17b_69.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb17/chb17c_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_01.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_02.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_03.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_04.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_05.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_06.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_07.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_08.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_09.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_10.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_11.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_12.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_13.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_14.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_15.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_16.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_17.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_18.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_19.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_20.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_21.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_22.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_23.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_24.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_25.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_26.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_27.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_28.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_29.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_30.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_31.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_32.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_33.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_34.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_35.edf: status='View' (not in ['done', 'ok', 'success'])**
- **chb18/chb18_36.edf: status='View' (not in ['done', 'ok', 'success'])**

## Input file hashes (sha256)

- `chb03_events.csv`: `0b3c6d4aedeb0f3dcca979608994c4743238ba658624c40043236e01c1a39884`
- `chb06_events.csv`: `314bf4497ddcf44767720df684e152e2c4c74f85fb79171967b949589313ba9f`
- `chb13_events.csv`: `41fade96c32384dd5843c404cb3911c5ffc2c3822583bd6e5ef6e04f063822bd`
- `chb14_events.csv`: `10534e8e102d5fed0bbf7cfbcc120a3b126dfbbff40c7d3100e87d3c73055b8c`
- `chb15_events.csv`: `1a176d89c8518c1baba1bfbde4736e3ba4f4d1c154d31bd5749b0486f10cbfdd`
- `chb16_events.csv`: `9f76ff19861428620b9d9fb0de153862265198ab5428a9fbe60610cb4c6af449`
- `chb17_events.csv`: `504a9b80855f98169692f84a1726eb85003acdbb6e4b0194070d863a26b0aa9e`
- `chb18_events.csv`: `7ded717f69974e3dba8b4242b271034ad742fca9edd4b252a1f930c722574f47`
- `files.csv`: `94359526ab853d639720233b982b8cd40c708e2385c93b3b77b1c68d234ac4f7`
