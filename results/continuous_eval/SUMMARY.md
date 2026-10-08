# Continuous-timeline evaluation -- SUMMARY

docs/CC_PROMPT_CONTINUOUS_EVAL.md. Locked thesis pipeline, unchanged, run on the real continuous timeline (every window scored, files concatenated in file-name order), two fitting scopes (T = background-fitted, W = whole-recording-fitted).

## Gate G1 -- Scope W reproduces the application's own scores

Per-file Pearson r >= 0.999 on all 231 test files. min r = -0.280261. **G1: FAIL**

G1 results per file, grouped by subject:

**chb03** -- 38 files, min r = 0.998777, 3 below 0.999:
       fname   n  pearson_r
chb03_01.edf 900   0.999565
chb03_02.edf 900   0.999753
chb03_03.edf 900   0.999732
chb03_04.edf 900   0.999306
chb03_05.edf 900   0.999534
chb03_06.edf 900   0.999009
chb03_07.edf 900   0.999498
chb03_08.edf 900   0.999333
chb03_09.edf 900   0.998824
chb03_10.edf 900   0.999768
chb03_11.edf 900   0.999133
chb03_12.edf 900   0.999119
chb03_13.edf 900   0.999369
chb03_14.edf 900   0.999069
chb03_15.edf 900   0.999263
chb03_16.edf 900   0.999717
chb03_17.edf 900   0.999407
chb03_18.edf 900   0.999651
chb03_19.edf 900   0.999693
chb03_20.edf 901   0.999298
chb03_21.edf 900   0.999655
chb03_22.edf 900   0.999781
chb03_23.edf 900   0.998777
chb03_24.edf 900   0.998986
chb03_25.edf 900   0.999454
chb03_26.edf 900   0.999304
chb03_27.edf 900   0.999723
chb03_28.edf 900   0.999852
chb03_29.edf 900   0.999649
chb03_30.edf 900   0.999352
chb03_31.edf 900   0.999787
chb03_32.edf 900   0.999715
chb03_33.edf 900   0.999713
chb03_34.edf 900   0.999642
chb03_35.edf 900   0.999656
chb03_36.edf 900   0.999771
chb03_37.edf 900   0.999673
chb03_38.edf 900   0.999537

**chb06** -- 18 files, min r = 0.998853, 5 below 0.999:
       fname    n  pearson_r
chb06_01.edf 3606   0.998919
chb06_02.edf 3600   0.998999
chb06_03.edf 3600   0.999281
chb06_04.edf 3315   0.999345
chb06_05.edf 3600   0.999181
chb06_06.edf 3600   0.999104
chb06_07.edf 3600   0.999182
chb06_08.edf 3600   0.999299
chb06_09.edf 3600   0.999343
chb06_10.edf 3600   0.999521
chb06_12.edf 3600   0.998853
chb06_13.edf 3600   0.998943
chb06_14.edf 3600   0.998941
chb06_15.edf 3600   0.999452
chb06_16.edf  757   0.999413
chb06_17.edf 3600   0.999275
chb06_18.edf 1982   0.999151
chb06_24.edf 3600   0.999462

**chb13** -- 33 files, min r = 0.998886, 1 below 0.999:
       fname   n  pearson_r
chb13_02.edf 900   0.998886
chb13_03.edf 900   0.999001
chb13_04.edf 900   0.999501
chb13_05.edf 900   0.999621
chb13_06.edf 900   0.999551
chb13_07.edf 900   0.999671
chb13_08.edf 900   0.999454
chb13_09.edf 900   0.999492
chb13_10.edf 900   0.999653
chb13_11.edf 900   0.999496
chb13_12.edf 900   0.999620
chb13_13.edf 900   0.999729
chb13_14.edf 900   0.999585
chb13_15.edf 900   0.999560
chb13_16.edf 900   0.999562
chb13_18.edf 900   0.999397
chb13_19.edf 900   0.999453
chb13_21.edf 900   0.999334
chb13_22.edf 900   0.999308
chb13_24.edf 900   0.999658
chb13_30.edf 900   0.999580
chb13_36.edf 900   0.999376
chb13_37.edf 900   0.999722
chb13_38.edf 900   0.999687
chb13_39.edf 900   0.999569
chb13_40.edf 900   0.999620
chb13_47.edf 900   0.999630
chb13_55.edf 900   0.999499
chb13_56.edf 900   0.999116
chb13_58.edf 900   0.999558
chb13_59.edf 900   0.999597
chb13_60.edf 900   0.999432
chb13_62.edf 900   0.999256

**chb14** -- 26 files, min r = 0.998957, 1 below 0.999:
       fname   n  pearson_r
chb14_01.edf 900   0.999493
chb14_02.edf 900   0.999482
chb14_03.edf 900   0.998957
chb14_04.edf 900   0.999457
chb14_06.edf 900   0.999565
chb14_07.edf 900   0.999335
chb14_11.edf 900   0.999317
chb14_12.edf 900   0.999463
chb14_13.edf 900   0.999131
chb14_14.edf 900   0.999405
chb14_16.edf 900   0.999038
chb14_17.edf 900   0.999288
chb14_18.edf 900   0.999515
chb14_19.edf 900   0.999376
chb14_20.edf 900   0.999147
chb14_22.edf 900   0.999188
chb14_24.edf 900   0.999156
chb14_25.edf 900   0.999494
chb14_26.edf 900   0.999442
chb14_27.edf 900   0.999372
chb14_29.edf 900   0.999333
chb14_30.edf 900   0.999525
chb14_32.edf 900   0.999356
chb14_37.edf 900   0.999030
chb14_39.edf 900   0.999019
chb14_42.edf 900   0.999406

**chb15** -- 40 files, min r = 0.999164, 0 below 0.999:
       fname   n  pearson_r
chb15_01.edf 900   0.999856
chb15_02.edf 900   0.999955
chb15_03.edf 900   0.999770
chb15_04.edf 900   0.999515
chb15_05.edf 900   0.999734
chb15_06.edf 900   0.999213
chb15_07.edf 900   0.999593
chb15_08.edf 900   0.999694
chb15_09.edf 900   0.999164
chb15_10.edf 900   0.999615
chb15_11.edf 900   0.999591
chb15_12.edf 900   0.999800
chb15_13.edf 900   0.999909
chb15_14.edf 900   0.999826
chb15_15.edf 900   0.999938
chb15_16.edf 900   0.999851
chb15_17.edf 900   0.999550
chb15_19.edf 900   0.999924
chb15_20.edf 900   0.999941
chb15_22.edf 900   0.999884
chb15_26.edf 900   0.999802
chb15_28.edf 900   0.999777
chb15_29.edf 900   0.999278
chb15_30.edf 900   0.999328
chb15_31.edf 900   0.999523
chb15_32.edf 900   0.999631
chb15_33.edf 900   0.999640
chb15_35.edf 900   0.999594
chb15_37.edf 900   0.999542
chb15_40.edf 900   0.999826
chb15_45.edf 900   0.999913
chb15_46.edf 900   0.999817
chb15_49.edf 906   0.999912
chb15_50.edf 900   0.999827
chb15_51.edf 900   0.999749
chb15_52.edf 902   0.999800
chb15_54.edf 900   0.999541
chb15_61.edf 900   0.999859
chb15_62.edf 900   0.999778
chb15_63.edf 900   0.999710

**chb16** -- 19 files, min r = 0.999036, 0 below 0.999:
       fname   n  pearson_r
chb16_01.edf 900   0.999738
chb16_02.edf 900   0.999272
chb16_03.edf 900   0.999135
chb16_04.edf 900   0.999260
chb16_05.edf 900   0.999700
chb16_06.edf 900   0.999763
chb16_07.edf 900   0.999746
chb16_08.edf 900   0.999723
chb16_09.edf 900   0.999791
chb16_10.edf 900   0.999377
chb16_11.edf 900   0.999394
chb16_12.edf 900   0.999819
chb16_13.edf 900   0.999601
chb16_14.edf 900   0.999705
chb16_15.edf 900   0.999534
chb16_16.edf 900   0.999214
chb16_17.edf 900   0.999388
chb16_18.edf 900   0.999192
chb16_19.edf 900   0.999036

**chb17** -- 21 files, min r = -0.280261, 21 below 0.999:
        fname   n  pearson_r
chb17a_03.edf 900   0.986199
chb17a_04.edf 900   0.985373
chb17a_05.edf 900   0.989132
chb17a_06.edf 900   0.993531
chb17a_08.edf 900   0.993935
chb17b_57.edf 900   0.995917
chb17b_58.edf 900   0.991678
chb17b_59.edf 900   0.995689
chb17b_60.edf 900   0.995187
chb17b_63.edf 906   0.993527
chb17b_67.edf 900   0.992535
chb17b_68.edf 900   0.995407
chb17b_69.edf 900  -0.280261
chb17c_02.edf 900   0.991434
chb17c_03.edf 900   0.995667
chb17c_04.edf 900   0.992827
chb17c_05.edf 900   0.995135
chb17c_06.edf 900   0.994616
chb17c_07.edf 900   0.994619
chb17c_08.edf 900   0.991166
chb17c_13.edf 900   0.978409

**chb18** -- 36 files, min r = 0.998564, 2 below 0.999:
       fname   n  pearson_r
chb18_01.edf 902   0.999745
chb18_02.edf 900   0.999491
chb18_03.edf 900   0.999267
chb18_04.edf 900   0.999453
chb18_05.edf 900   0.999215
chb18_06.edf 900   0.999284
chb18_07.edf 900   0.999145
chb18_08.edf 900   0.999269
chb18_09.edf 900   0.999028
chb18_10.edf 900   0.999001
chb18_11.edf 900   0.998982
chb18_12.edf 900   0.999227
chb18_13.edf 900   0.999165
chb18_14.edf 900   0.999431
chb18_15.edf 900   0.999214
chb18_16.edf 900   0.999351
chb18_17.edf 900   0.999153
chb18_18.edf 900   0.999210
chb18_19.edf 900   0.999055
chb18_20.edf 900   0.999612
chb18_21.edf 900   0.999569
chb18_22.edf 900   0.999404
chb18_23.edf 900   0.999327
chb18_24.edf 900   0.999141
chb18_25.edf 900   0.999103
chb18_26.edf 900   0.998564
chb18_27.edf 900   0.999506
chb18_28.edf 900   0.999466
chb18_29.edf 900   0.999510
chb18_30.edf 900   0.999376
chb18_31.edf 568   0.999586
chb18_32.edf 900   0.999543
chb18_33.edf 900   0.999305
chb18_34.edf 900   0.999408
chb18_35.edf 900   0.999188
chb18_36.edf 900   0.999409

## Gate G2 -- Scope T rank-matches the committed offline arrays

Amendment A6: `fit`/`rho_*` are the gating computation (Correction C1 fit, flagged windows included, for a subject with any flagged window -- chb17; otherwise identical to A2). `rho_*_a2` is the Amendment-A2-fitted agreement (flagged windows excluded from the fit), reported for information -- what Steps A/B/C actually use -- not used to gate. Both over windows not flagged.

subject fit  n_mine_ictal  n_off_ictal  ictal_count_match  n_flagged_ictal  rho_ictal  rho_ictal_a2  n_mine_inter  n_off_inter  inter_count_match  n_flagged_inter  rho_inter  rho_inter_a2  g2_pass
  chb03  A2           106          106               True                0     0.9996        0.9996         17204        17204               True                0     0.9997        0.9997     True
  chb06  A2            45           45               True                0     0.9983        0.9983         19826        19826               True                0     0.9995        0.9995     True
  chb13  A2           144          144               True                0     0.9994        0.9994         12452        12452               True                0     0.9997        0.9997     True
  chb14  A2            49           49               True                0     0.9993        0.9993         13983        13983               True                0     0.9995        0.9995     True
  chb15  A2           515          515               True                0     0.9999        0.9999         17026        17026               True                0     0.9997        0.9997     True
  chb16  A2            28           28               True                0     0.9995        0.9995          6428         6428               True                0     0.9997        0.9997     True
  chb17  C1            74           74               True                0     0.9901        0.9947          9304         9304               True              534     0.9837        0.9894    False
  chb18  A2            83           83               True                0     0.9997        0.9997         14853        14853               True                0     0.9996        0.9996     True

**G2: FAIL**

### Amendment A7 -- per-branch diagnostic for chb17's recorded G2 FAIL

zrecon, zlatent, zgamma vs. the offline components (Correction C1 fit, windows not flagged signal-loss). Cause: the committed offline arrays were fitted on signal-loss windows whose GAE reconstruction score is numerically undefined and hardware-dependent (zrecon 48.70 on the GPU that produced them, 3.00 on this CPU; chb17_zrecon_outliers.txt, chb17b_69_inspect.txt) -- no CPU recomputation can reproduce them. By the author's decision, Steps A and B below proceed regardless.

 branch  rho_ictal  rho_inter
 zrecon     0.9997     0.9999
zlatent     0.9539     0.9352
 zgamma     1.0000     1.0000

**Amendment A3 (before Step A): Scope W is computed through G1 only. Steps A, B and C below are Scope T only -- Scope W's operating point and test result come from the application's own rerun, not this script -- regardless of whether G1 passed (Amendment A1: G1 failing does not stop this run).**

## Step A -- validation patients (chb10, chb11, chb22): selected operating point

Scope T: mag_pct=80 pen_mult=5 merge_s=300  (sens=0.133 prec=0.021 |gap|=0.1121 FA/day=19.82)
  best point with FA/day<=25 (info only): {'scope': 'T', 'mag_pct': 75.0, 'pen_mult': 5.0, 'merge_s': 300, 'tp': 5, 'fp': 116, 'n_ref': 15, 'fn': 10, 'sensitivity': 0.3333333333333333, 'precision': 0.04132231404958678, 'f1': 0.07352941176470588, 'fp_per_day': 24.99127260395575, 'n_inter_h': 111.39888888888889, 'abs_gap': 0.2920110192837465}
  @ 50/2.0/merge90: sens=0.733 prec=0.024 FA/day=96.52

## Step B -- test patients at Scope T's selected point and at 50/2.0/merge90

Amendment A7: POOLED_no_chb17 excludes chb17 (see the per-branch diagnostic above for why its G2 is recorded as FAIL) from the pooled sensitivity row.

scope        point  mag_pct  pen_mult  merge_s         subject  tp  fp  n_ref  fn  sensitivity  precision       f1  fp_per_day  n_inter_h  mean_lat_s  window_auroc_macro
    T     selected     80.0       5.0      300          POOLED   5 181     76  71     0.065789   0.026882 0.038168   15.646724 277.630000         NaN            0.620809
    T     selected     80.0       5.0      300 POOLED_no_chb17   5 168     73  68     0.068493   0.028902 0.040650   15.670491 257.298889         NaN            0.621595
    T fixed_50_2.0     50.0       2.0       90          POOLED  23 848     76  53     0.302632   0.026406 0.048574   73.306199 277.630000         NaN            0.620809
    T fixed_50_2.0     50.0       2.0       90 POOLED_no_chb17  23 778     73  50     0.315068   0.028714 0.052632   72.569299 257.298889         NaN            0.621595

## Step C -- results of record

| row | sens | prec | F1 | FA/day | macro window AUROC |
|---|---|---|---|---|---|
| offline reconstructed (Table 9) | 0.618 | 0.129 | 0.213 | 27.4 | -- |
| Scope T continuous (m80/p5/merge300) | 0.066 | 0.027 | 0.038 | 15.65 | 0.621 |

### Amendment A8 -- reported operating point (75/5/300)

Maximizes pooled validation sensitivity subject to pooled validation FA/day <= 25 (validation sensitivity 0.333, 24.99 FA/day), decided before this test grid was read. The Step A rule's own point (above) stays reported; this is the one actually proposed.

| row | TP | FP | n_ref | sens | prec | FA/day |
|---|---|---|---|---|---|---|
| POOLED | 6 | 222 | 76 | 0.079 | 0.026 | 19.19 |
| POOLED_no_chb17 | 6 | 204 | 73 | 0.082 | 0.029 | 19.03 |

Per patient:

subject  n_seizures  detected  false_alarms  sensitivity  precision     f1  fp_per_day  n_signal_loss  excluded_h
  chb03           7         0            36       0.0000     0.0000 0.0000      22.807              0      0.0000
  chb06          10         1            26       0.1000     0.0370 0.0541       9.358              0      0.0000
  chb13          12         1            35       0.0833     0.0278 0.0417      25.579              0      0.0000
  chb14           8         0            16       0.0000     0.0000 0.0000      14.800              0      0.0000
  chb15          20         2            55       0.1000     0.0351 0.0519      33.471              0      0.0000
  chb16          10         0             7       0.0000     0.0000 0.0000       8.857              0      0.0000
  chb17           3         0            18       0.0000     0.0000 0.0000      21.248            534      0.5933
  chb18           6         2            29       0.3333     0.0645 0.1081      19.583              0      0.0000

## Pre-registered expectations

E1 (Scope T sens < 0.618 and FA/day > 27.4): NOT MET
E2 (Scope T vs. application's own pooled result, gap small vs. offline-application gap): NOT MET (T-application gap=36.93, offline-application gap=25.41)

Wall-clock time: 1695.1 s (0.47 h).