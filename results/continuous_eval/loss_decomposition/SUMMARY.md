# Loss decomposition -- which windows make the continuous-timeline score fail -- SUMMARY

docs/CC_PROMPT_LOSS_DECOMPOSITION.md. Read-only diagnostic on cached scores; nothing recomputed, tuned or committed except this script and its outputs. Window categories (each window exactly one, priority order): ictal, signal-loss, post-ictal 0-2min, post-ictal 2-10min, post-ictal 10-60min, post-ictal 1-4h, artifact (+-5 SD rule), other background. Design decisions are taken on validation (chb10, chb11, chb22) only; the test table below is descriptive and was not used to choose anything -- this script selects nothing itself.

## VALIDATION (chb10, chb11, chb22)


## Item 1 -- count and hours per category

```
subject            category  n_windows   hours
  chb10               ictal        117  0.1300
  chb10         signal_loss          0  0.0000
  chb10   post_ictal_0_2min        210  0.2333
  chb10  post_ictal_2_10min        753  0.8367
  chb10 post_ictal_10_60min       3471  3.8567
  chb10     post_ictal_1_4h        965  1.0722
  chb10            artifact      10978 12.1978
  chb10          background      28526 31.6956
  chb11               ictal        204  0.2267
  chb11         signal_loss          0  0.0000
  chb11   post_ictal_0_2min         90  0.1000
  chb11  post_ictal_2_10min        360  0.4000
  chb11 post_ictal_10_60min        750  0.8333
  chb11     post_ictal_1_4h          0  0.0000
  chb11            artifact      12078 13.4200
  chb11          background      14231 15.8122
  chb22               ictal         55  0.0611
  chb22         signal_loss          0  0.0000
  chb22   post_ictal_0_2min         90  0.1000
  chb22  post_ictal_2_10min        199  0.2211
  chb22 post_ictal_10_60min        416  0.4622
  chb22     post_ictal_1_4h          0  0.0000
  chb22            artifact      15666 17.4067
  chb22          background      11476 12.7511
 POOLED               ictal        376  0.4178
 POOLED         signal_loss          0  0.0000
 POOLED   post_ictal_0_2min        390  0.4333
 POOLED  post_ictal_2_10min       1312  1.4578
 POOLED post_ictal_10_60min       4637  5.1522
 POOLED     post_ictal_1_4h        965  1.0722
 POOLED            artifact      38722 43.0244
 POOLED          background      54233 60.2589
```

## Item 2 -- AUROC, ictal vs. each negative category alone (Scope T)

```
           category  chb10  chb11  chb22  POOLED  n_ictal_pooled  n_category_pooled
        signal_loss    NaN    NaN    NaN     NaN             376                  0
  post_ictal_0_2min 0.5936 0.5989 0.4592  0.6312             376                390
 post_ictal_2_10min 0.7064 0.7457 0.8127  0.7839             376               1312
post_ictal_10_60min 0.8388 0.9066 0.8232  0.8906             376               4637
    post_ictal_1_4h 0.8832    NaN    NaN  0.9486             376                965
           artifact 0.5307 0.6322 0.7971  0.6536             376              38722
         background 0.8501 0.9567 0.9784  0.9284             376              54233
```

## Item 3 -- macro window AUROC, all windows and with each category removed in turn (Scope T)

```
   removed_category  macro_auroc  chb10  chb11  chb22
(none, all windows)       0.8161 0.7683 0.8089 0.8713
        signal_loss       0.8161 0.7683 0.8089 0.8713
  post_ictal_0_2min       0.8171 0.7691 0.8096 0.8726
 post_ictal_2_10min       0.8169 0.7693 0.8098 0.8717
post_ictal_10_60min       0.8135 0.7623 0.8062 0.8720
    post_ictal_1_4h       0.8153 0.7657 0.8089 0.8713
           artifact       0.9197 0.8451 0.9472 0.9666
         background       0.6908 0.6256 0.6505 0.7961
```

## Item 4 -- composition of the top 1%/5% non-ictal windows by fused score (Scope T)

```
subject  pct    k            category  share
  chb10  1.0  449         signal_loss 0.0000
  chb10  1.0  449   post_ictal_0_2min 0.0000
  chb10  1.0  449  post_ictal_2_10min 0.0200
  chb10  1.0  449 post_ictal_10_60min 0.0223
  chb10  1.0  449     post_ictal_1_4h 0.0045
  chb10  1.0  449            artifact 0.9154
  chb10  1.0  449          background 0.0379
  chb11  1.0  275         signal_loss 0.0000
  chb11  1.0  275   post_ictal_0_2min 0.0000
  chb11  1.0  275  post_ictal_2_10min 0.0109
  chb11  1.0  275 post_ictal_10_60min 0.0000
  chb11  1.0  275     post_ictal_1_4h 0.0000
  chb11  1.0  275            artifact 0.9818
  chb11  1.0  275          background 0.0073
  chb22  1.0  278         signal_loss 0.0000
  chb22  1.0  278   post_ictal_0_2min 0.0360
  chb22  1.0  278  post_ictal_2_10min 0.0072
  chb22  1.0  278 post_ictal_10_60min 0.0144
  chb22  1.0  278     post_ictal_1_4h 0.0000
  chb22  1.0  278            artifact 0.9424
  chb22  1.0  278          background 0.0000
 POOLED  1.0 1003         signal_loss 0.0000
 POOLED  1.0 1003   post_ictal_0_2min 0.0140
 POOLED  1.0 1003  post_ictal_2_10min 0.0120
 POOLED  1.0 1003 post_ictal_10_60min 0.0060
 POOLED  1.0 1003     post_ictal_1_4h 0.0000
 POOLED  1.0 1003            artifact 0.9581
 POOLED  1.0 1003          background 0.0100
  chb10  5.0 2245         signal_loss 0.0000
  chb10  5.0 2245   post_ictal_0_2min 0.0067
  chb10  5.0 2245  post_ictal_2_10min 0.0218
  chb10  5.0 2245 post_ictal_10_60min 0.0236
  chb10  5.0 2245     post_ictal_1_4h 0.0018
  chb10  5.0 2245            artifact 0.8579
  chb10  5.0 2245          background 0.0882
  chb11  5.0 1375         signal_loss 0.0000
  chb11  5.0 1375   post_ictal_0_2min 0.0073
  chb11  5.0 1375  post_ictal_2_10min 0.0167
  chb11  5.0 1375 post_ictal_10_60min 0.0000
  chb11  5.0 1375     post_ictal_1_4h 0.0000
  chb11  5.0 1375            artifact 0.9716
  chb11  5.0 1375          background 0.0044
  chb22  5.0 1392         signal_loss 0.0000
  chb22  5.0 1392   post_ictal_0_2min 0.0266
  chb22  5.0 1392  post_ictal_2_10min 0.0115
  chb22  5.0 1392 post_ictal_10_60min 0.0180
  chb22  5.0 1392     post_ictal_1_4h 0.0000
  chb22  5.0 1392            artifact 0.9296
  chb22  5.0 1392          background 0.0144
 POOLED  5.0 5013         signal_loss 0.0000
 POOLED  5.0 5013   post_ictal_0_2min 0.0140
 POOLED  5.0 5013  post_ictal_2_10min 0.0182
 POOLED  5.0 5013 post_ictal_10_60min 0.0082
 POOLED  5.0 5013     post_ictal_1_4h 0.0002
 POOLED  5.0 5013            artifact 0.9459
 POOLED  5.0 5013          background 0.0136
```

## Item 2 -- AUROC, ictal vs. each negative category alone (Application v3)

```
           category  chb10  chb11  chb22  POOLED  n_ictal_pooled  n_category_pooled
        signal_loss    NaN    NaN    NaN     NaN             376                  0
  post_ictal_0_2min 0.5194 0.6034 0.4883  0.5973             376                390
 post_ictal_2_10min 0.6373 0.7372 0.8185  0.7474             376               1312
post_ictal_10_60min 0.7618 0.9083 0.8185  0.8570             376               4637
    post_ictal_1_4h 0.7955    NaN    NaN  0.8931             376                965
           artifact 0.4996 0.6336 0.7957  0.6541             376              38722
         background 0.7654 0.9477 0.9660  0.8945             376              54233
```

## Item 3 -- macro window AUROC, all windows and with each category removed in turn (Application v3)

```
   removed_category  macro_auroc  chb10  chb11  chb22
(none, all windows)       0.7892 0.6975 0.8048 0.8654
        signal_loss       0.7892 0.6975 0.8048 0.8654
  post_ictal_0_2min       0.7902 0.6983 0.8055 0.8666
 post_ictal_2_10min       0.7900 0.6985 0.8057 0.8658
post_ictal_10_60min       0.7867 0.6921 0.8019 0.8661
    post_ictal_1_4h       0.7885 0.6953 0.8048 0.8654
           artifact       0.8851 0.7615 0.9388 0.9550
         background       0.6753 0.5792 0.6517 0.7949
```

## Item 4 -- composition of the top 1%/5% non-ictal windows by fused score (Application v3)

```
subject  pct    k            category  share
  chb10  1.0  449         signal_loss 0.0000
  chb10  1.0  449   post_ictal_0_2min 0.0045
  chb10  1.0  449  post_ictal_2_10min 0.0245
  chb10  1.0  449 post_ictal_10_60min 0.0290
  chb10  1.0  449     post_ictal_1_4h 0.0045
  chb10  1.0  449            artifact 0.8909
  chb10  1.0  449          background 0.0468
  chb11  1.0  275         signal_loss 0.0000
  chb11  1.0  275   post_ictal_0_2min 0.0000
  chb11  1.0  275  post_ictal_2_10min 0.0109
  chb11  1.0  275 post_ictal_10_60min 0.0000
  chb11  1.0  275     post_ictal_1_4h 0.0000
  chb11  1.0  275            artifact 0.9818
  chb11  1.0  275          background 0.0073
  chb22  1.0  278         signal_loss 0.0000
  chb22  1.0  278   post_ictal_0_2min 0.0216
  chb22  1.0  278  post_ictal_2_10min 0.0108
  chb22  1.0  278 post_ictal_10_60min 0.0216
  chb22  1.0  278     post_ictal_1_4h 0.0000
  chb22  1.0  278            artifact 0.9388
  chb22  1.0  278          background 0.0072
 POOLED  1.0 1003         signal_loss 0.0000
 POOLED  1.0 1003   post_ictal_0_2min 0.0070
 POOLED  1.0 1003  post_ictal_2_10min 0.0150
 POOLED  1.0 1003 post_ictal_10_60min 0.0100
 POOLED  1.0 1003     post_ictal_1_4h 0.0010
 POOLED  1.0 1003            artifact 0.9511
 POOLED  1.0 1003          background 0.0160
  chb10  5.0 2245         signal_loss 0.0000
  chb10  5.0 2245   post_ictal_0_2min 0.0076
  chb10  5.0 2245  post_ictal_2_10min 0.0258
  chb10  5.0 2245 post_ictal_10_60min 0.0281
  chb10  5.0 2245     post_ictal_1_4h 0.0045
  chb10  5.0 2245            artifact 0.7920
  chb10  5.0 2245          background 0.1421
  chb11  5.0 1375         signal_loss 0.0000
  chb11  5.0 1375   post_ictal_0_2min 0.0087
  chb11  5.0 1375  post_ictal_2_10min 0.0211
  chb11  5.0 1375 post_ictal_10_60min 0.0007
  chb11  5.0 1375     post_ictal_1_4h 0.0000
  chb11  5.0 1375            artifact 0.9629
  chb11  5.0 1375          background 0.0065
  chb22  5.0 1392         signal_loss 0.0000
  chb22  5.0 1392   post_ictal_0_2min 0.0244
  chb22  5.0 1392  post_ictal_2_10min 0.0129
  chb22  5.0 1392 post_ictal_10_60min 0.0201
  chb22  5.0 1392     post_ictal_1_4h 0.0000
  chb22  5.0 1392            artifact 0.9203
  chb22  5.0 1392          background 0.0223
 POOLED  5.0 5013         signal_loss 0.0000
 POOLED  5.0 5013   post_ictal_0_2min 0.0120
 POOLED  5.0 5013  post_ictal_2_10min 0.0201
 POOLED  5.0 5013 post_ictal_10_60min 0.0118
 POOLED  5.0 5013     post_ictal_1_4h 0.0006
 POOLED  5.0 5013            artifact 0.9280
 POOLED  5.0 5013          background 0.0275
```

## Item 5 -- per-branch AUROC per category (only where the Amendment A7 c1-components cache exists)

(no subject in this split has the per-branch components cache)

## Item 6 -- event level, Scope T, category of every false alarm's onset window


**mag_pct=50 pen_mult=2 merge_s=90** (point `50_2_0_90`, already selected on validation -- results/continuous_eval/stepA_selected.json)

```
subject  n_false_alarms  n_ictal  n_signal_loss  n_post_ictal_0_2min  n_post_ictal_2_10min  n_post_ictal_10_60min  n_post_ictal_1_4h  n_artifact  n_background  share_ictal  share_signal_loss  share_post_ictal_0_2min  share_post_ictal_2_10min  share_post_ictal_10_60min  share_post_ictal_1_4h  share_artifact  share_background
  chb10             170        0              0                    0                     4                      8                  1          66            91          0.0                0.0                      0.0                    0.0235                     0.0471                 0.0059          0.3882            0.5353
  chb11             158        0              0                    0                     3                      0                  0          90            65          0.0                0.0                      0.0                    0.0190                     0.0000                 0.0000          0.5696            0.4114
  chb22             120        0              0                    0                     0                      1                  0          77            42          0.0                0.0                      0.0                    0.0000                     0.0083                 0.0000          0.6417            0.3500
 POOLED             448        0              0                    0                     7                      9                  1         233           198          0.0                0.0                      0.0                    0.0156                     0.0201                 0.0022          0.5201            0.4420
```

**mag_pct=75 pen_mult=5 merge_s=300** (point `75_5_300`, already selected on validation -- results/continuous_eval/stepA_selected.json)

```
subject  n_false_alarms  n_ictal  n_signal_loss  n_post_ictal_0_2min  n_post_ictal_2_10min  n_post_ictal_10_60min  n_post_ictal_1_4h  n_artifact  n_background  share_ictal  share_signal_loss  share_post_ictal_0_2min  share_post_ictal_2_10min  share_post_ictal_10_60min  share_post_ictal_1_4h  share_artifact  share_background
  chb10              40        1              0                    0                     2                      1                  0          15            21       0.0250                0.0                      0.0                    0.0500                     0.0250                    0.0          0.3750            0.5250
  chb11              44        1              0                    0                     0                      0                  0          27            16       0.0227                0.0                      0.0                    0.0000                     0.0000                    0.0          0.6136            0.3636
  chb22              25        1              0                    0                     0                      0                  0          13            11       0.0400                0.0                      0.0                    0.0000                     0.0000                    0.0          0.5200            0.4400
 POOLED             109        3              0                    0                     2                      1                  0          55            48       0.0275                0.0                      0.0                    0.0183                     0.0092                    0.0          0.5046            0.4404
```

## TEST (chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18)


## Item 1 -- count and hours per category

```
subject            category  n_windows    hours
  chb03               ictal        106   0.1178
  chb03         signal_loss          0   0.0000
  chb03   post_ictal_0_2min        210   0.2333
  chb03  post_ictal_2_10min        840   0.9333
  chb03 post_ictal_10_60min       2650   2.9444
  chb03     post_ictal_1_4h          0   0.0000
  chb03            artifact      13191  14.6567
  chb03          background      17204  19.1156
  chb06               ictal         45   0.0500
  chb06         signal_loss          0   0.0000
  chb06   post_ictal_0_2min        299   0.3322
  chb06  post_ictal_2_10min       1080   1.2000
  chb06 post_ictal_10_60min       5630   6.2556
  chb06     post_ictal_1_4h       5483   6.0922
  chb06            artifact      27697  30.7744
  chb06          background      19826  22.0289
  chb13               ictal        144   0.1600
  chb13         signal_loss          0   0.0000
  chb13   post_ictal_0_2min        360   0.4000
  chb13  post_ictal_2_10min       1277   1.4189
  chb13 post_ictal_10_60min       2695   2.9944
  chb13     post_ictal_1_4h          0   0.0000
  chb13            artifact      12772  14.1911
  chb13          background      12452  13.8356
  chb14               ictal         49   0.0544
  chb14         signal_loss          0   0.0000
  chb14   post_ictal_0_2min        240   0.2667
  chb14  post_ictal_2_10min        895   0.9944
  chb14 post_ictal_10_60min       1565   1.7389
  chb14     post_ictal_1_4h          0   0.0000
  chb14            artifact       6668   7.4089
  chb14          background      13983  15.5367
  chb15               ictal        515   0.5722
  chb15         signal_loss          0   0.0000
  chb15   post_ictal_0_2min        600   0.6667
  chb15  post_ictal_2_10min       2021   2.2456
  chb15 post_ictal_10_60min       5498   6.1089
  chb15     post_ictal_1_4h          0   0.0000
  chb15            artifact      10348  11.4978
  chb15          background      17026  18.9178
  chb16               ictal         28   0.0311
  chb16         signal_loss          0   0.0000
  chb16   post_ictal_0_2min        300   0.3333
  chb16  post_ictal_2_10min       1090   1.2111
  chb16 post_ictal_10_60min       2152   2.3911
  chb16     post_ictal_1_4h          0   0.0000
  chb16            artifact       7102   7.8911
  chb16          background       6428   7.1422
  chb17               ictal         74   0.0822
  chb17         signal_loss        534   0.5933
  chb17   post_ictal_0_2min         90   0.1000
  chb17  post_ictal_2_10min        275   0.3056
  chb17 post_ictal_10_60min        157   0.1744
  chb17     post_ictal_1_4h          0   0.0000
  chb17            artifact       9006  10.0067
  chb17          background       8770   9.7444
  chb18               ictal         83   0.0922
  chb18         signal_loss          0   0.0000
  chb18   post_ictal_0_2min        167   0.1856
  chb18  post_ictal_2_10min        480   0.5333
  chb18 post_ictal_10_60min       1672   1.8578
  chb18     post_ictal_1_4h          0   0.0000
  chb18            artifact      14815  16.4611
  chb18          background      14853  16.5033
 POOLED               ictal       1044   1.1600
 POOLED         signal_loss        534   0.5933
 POOLED   post_ictal_0_2min       2266   2.5178
 POOLED  post_ictal_2_10min       7958   8.8422
 POOLED post_ictal_10_60min      22019  24.4656
 POOLED     post_ictal_1_4h       5483   6.0922
 POOLED            artifact     101599 112.8878
 POOLED          background     110542 122.8244
```

## Item 2 -- AUROC, ictal vs. each negative category alone (Scope T)

```
           category  chb03  chb06  chb13  chb14  chb15  chb16  chb17  chb18  POOLED  n_ictal_pooled  n_category_pooled
        signal_loss    NaN    NaN    NaN    NaN    NaN    NaN 0.9595    NaN  0.9368            1044                534
  post_ictal_0_2min 0.3486 0.2321 0.4225 0.6762 0.6468 0.4857 0.3351 0.6450  0.5490            1044               2266
 post_ictal_2_10min 0.5904 0.2741 0.5305 0.6437 0.6862 0.5538 0.4241 0.6918  0.6134            1044               7958
post_ictal_10_60min 0.6909 0.2946 0.5234 0.6338 0.7023 0.5121 0.5757 0.7365  0.6432            1044              22019
    post_ictal_1_4h    NaN 0.3571    NaN    NaN    NaN    NaN    NaN    NaN  0.8064            1044               5483
           artifact 0.5801 0.2474 0.3188 0.5118 0.4306 0.3132 0.3963 0.5877  0.5060            1044             101599
         background 0.9644 0.4988 0.8229 0.6974 0.8787 0.8764 0.8288 0.9201  0.8604            1044             110542
```

## Item 3 -- macro window AUROC, all windows and with each category removed in turn (Scope T)

```
   removed_category  macro_auroc  chb03  chb06  chb13  chb14  chb15  chb16  chb17  chb18
(none, all windows)       0.6208 0.7814 0.3453 0.5603 0.6379 0.7059 0.5687 0.6153 0.7517
        signal_loss       0.6196 0.7814 0.3453 0.5603 0.6379 0.7059 0.5687 0.6053 0.7517
  post_ictal_0_2min       0.6219 0.7841 0.3459 0.5620 0.6375 0.7069 0.5702 0.6167 0.7522
 post_ictal_2_10min       0.6225 0.7863 0.3466 0.5616 0.6376 0.7071 0.5697 0.6181 0.7526
post_ictal_10_60min       0.6242 0.7891 0.3506 0.5640 0.6382 0.7065 0.5769 0.6156 0.7525
    post_ictal_1_4h       0.6207 0.7814 0.3441 0.5603 0.6379 0.7059 0.5687 0.6153 0.7517
           artifact       0.7561 0.9085 0.4292 0.7440 0.6883 0.8191 0.7507 0.8160 0.8932
         background       0.4684 0.5951 0.2696 0.3690 0.5490 0.5465 0.3829 0.4292 0.6057
```

## Item 4 -- composition of the top 1%/5% non-ictal windows by fused score (Scope T)

```
subject  pct     k            category  share
  chb03  1.0   341         signal_loss 0.0000
  chb03  1.0   341   post_ictal_0_2min 0.0029
  chb03  1.0   341  post_ictal_2_10min 0.0235
  chb03  1.0   341 post_ictal_10_60min 0.4018
  chb03  1.0   341     post_ictal_1_4h 0.0000
  chb03  1.0   341            artifact 0.5689
  chb03  1.0   341          background 0.0029
  chb06  1.0   600         signal_loss 0.0000
  chb06  1.0   600   post_ictal_0_2min 0.0083
  chb06  1.0   600  post_ictal_2_10min 0.0150
  chb06  1.0   600 post_ictal_10_60min 0.2650
  chb06  1.0   600     post_ictal_1_4h 0.0783
  chb06  1.0   600            artifact 0.5967
  chb06  1.0   600          background 0.0367
  chb13  1.0   296         signal_loss 0.0000
  chb13  1.0   296   post_ictal_0_2min 0.0203
  chb13  1.0   296  post_ictal_2_10min 0.0203
  chb13  1.0   296 post_ictal_10_60min 0.1182
  chb13  1.0   296     post_ictal_1_4h 0.0000
  chb13  1.0   296            artifact 0.7939
  chb13  1.0   296          background 0.0473
  chb14  1.0   234         signal_loss 0.0000
  chb14  1.0   234   post_ictal_0_2min 0.0171
  chb14  1.0   234  post_ictal_2_10min 0.0342
  chb14  1.0   234 post_ictal_10_60min 0.0983
  chb14  1.0   234     post_ictal_1_4h 0.0000
  chb14  1.0   234            artifact 0.7393
  chb14  1.0   234          background 0.1111
  chb15  1.0   355         signal_loss 0.0000
  chb15  1.0   355   post_ictal_0_2min 0.0056
  chb15  1.0   355  post_ictal_2_10min 0.0113
  chb15  1.0   355 post_ictal_10_60min 0.1690
  chb15  1.0   355     post_ictal_1_4h 0.0000
  chb15  1.0   355            artifact 0.8141
  chb15  1.0   355          background 0.0000
  chb16  1.0   171         signal_loss 0.0000
  chb16  1.0   171   post_ictal_0_2min 0.0058
  chb16  1.0   171  post_ictal_2_10min 0.0058
  chb16  1.0   171 post_ictal_10_60min 0.0058
  chb16  1.0   171     post_ictal_1_4h 0.0000
  chb16  1.0   171            artifact 0.9766
  chb16  1.0   171          background 0.0058
  chb17  1.0   188         signal_loss 0.0000
  chb17  1.0   188   post_ictal_0_2min 0.0053
  chb17  1.0   188  post_ictal_2_10min 0.0106
  chb17  1.0   188 post_ictal_10_60min 0.0000
  chb17  1.0   188     post_ictal_1_4h 0.0000
  chb17  1.0   188            artifact 0.9787
  chb17  1.0   188          background 0.0053
  chb18  1.0   320         signal_loss 0.0000
  chb18  1.0   320   post_ictal_0_2min 0.0000
  chb18  1.0   320  post_ictal_2_10min 0.0000
  chb18  1.0   320 post_ictal_10_60min 0.0813
  chb18  1.0   320     post_ictal_1_4h 0.0000
  chb18  1.0   320            artifact 0.9187
  chb18  1.0   320          background 0.0000
 POOLED  1.0  2504         signal_loss 0.0000
 POOLED  1.0  2504   post_ictal_0_2min 0.0052
 POOLED  1.0  2504  post_ictal_2_10min 0.0244
 POOLED  1.0  2504 post_ictal_10_60min 0.1458
 POOLED  1.0  2504     post_ictal_1_4h 0.0000
 POOLED  1.0  2504            artifact 0.8191
 POOLED  1.0  2504          background 0.0056
  chb03  5.0  1705         signal_loss 0.0000
  chb03  5.0  1705   post_ictal_0_2min 0.0217
  chb03  5.0  1705  post_ictal_2_10min 0.0528
  chb03  5.0  1705 post_ictal_10_60min 0.1789
  chb03  5.0  1705     post_ictal_1_4h 0.0000
  chb03  5.0  1705            artifact 0.7402
  chb03  5.0  1705          background 0.0065
  chb06  5.0  3001         signal_loss 0.0000
  chb06  5.0  3001   post_ictal_0_2min 0.0047
  chb06  5.0  3001  post_ictal_2_10min 0.0113
  chb06  5.0  3001 post_ictal_10_60min 0.1949
  chb06  5.0  3001     post_ictal_1_4h 0.0550
  chb06  5.0  3001            artifact 0.6938
  chb06  5.0  3001          background 0.0403
  chb13  5.0  1478         signal_loss 0.0000
  chb13  5.0  1478   post_ictal_0_2min 0.0162
  chb13  5.0  1478  post_ictal_2_10min 0.0365
  chb13  5.0  1478 post_ictal_10_60min 0.0853
  chb13  5.0  1478     post_ictal_1_4h 0.0000
  chb13  5.0  1478            artifact 0.8437
  chb13  5.0  1478          background 0.0183
  chb14  5.0  1168         signal_loss 0.0000
  chb14  5.0  1168   post_ictal_0_2min 0.0120
  chb14  5.0  1168  post_ictal_2_10min 0.0274
  chb14  5.0  1168 post_ictal_10_60min 0.0779
  chb14  5.0  1168     post_ictal_1_4h 0.0000
  chb14  5.0  1168            artifact 0.6729
  chb14  5.0  1168          background 0.2098
  chb15  5.0  1775         signal_loss 0.0000
  chb15  5.0  1775   post_ictal_0_2min 0.0107
  chb15  5.0  1775  post_ictal_2_10min 0.0400
  chb15  5.0  1775 post_ictal_10_60min 0.1690
  chb15  5.0  1775     post_ictal_1_4h 0.0000
  chb15  5.0  1775            artifact 0.7775
  chb15  5.0  1775          background 0.0028
  chb16  5.0   854         signal_loss 0.0000
  chb16  5.0   854   post_ictal_0_2min 0.0070
  chb16  5.0   854  post_ictal_2_10min 0.0222
  chb16  5.0   854 post_ictal_10_60min 0.0375
  chb16  5.0   854     post_ictal_1_4h 0.0000
  chb16  5.0   854            artifact 0.9309
  chb16  5.0   854          background 0.0023
  chb17  5.0   942         signal_loss 0.0000
  chb17  5.0   942   post_ictal_0_2min 0.0074
  chb17  5.0   942  post_ictal_2_10min 0.0180
  chb17  5.0   942 post_ictal_10_60min 0.0000
  chb17  5.0   942     post_ictal_1_4h 0.0000
  chb17  5.0   942            artifact 0.9607
  chb17  5.0   942          background 0.0138
  chb18  5.0  1599         signal_loss 0.0000
  chb18  5.0  1599   post_ictal_0_2min 0.0031
  chb18  5.0  1599  post_ictal_2_10min 0.0156
  chb18  5.0  1599 post_ictal_10_60min 0.1201
  chb18  5.0  1599     post_ictal_1_4h 0.0000
  chb18  5.0  1599            artifact 0.8587
  chb18  5.0  1599          background 0.0025
 POOLED  5.0 12520         signal_loss 0.0000
 POOLED  5.0 12520   post_ictal_0_2min 0.0171
 POOLED  5.0 12520  post_ictal_2_10min 0.0431
 POOLED  5.0 12520 post_ictal_10_60min 0.1202
 POOLED  5.0 12520     post_ictal_1_4h 0.0002
 POOLED  5.0 12520            artifact 0.8089
 POOLED  5.0 12520          background 0.0105
```

## Item 5 -- per-branch AUROC per category (only where the Amendment A7 c1-components cache exists)

Cached for: chb17.
```
subject  branch            category  auroc  n_ictal  n_category
  chb17  zrecon         signal_loss 0.0404       74         534
  chb17  zrecon   post_ictal_0_2min 0.4317       74          90
  chb17  zrecon  post_ictal_2_10min 0.4693       74         275
  chb17  zrecon post_ictal_10_60min 0.7444       74         157
  chb17  zrecon     post_ictal_1_4h    NaN       74           0
  chb17  zrecon            artifact 0.2400       74        9006
  chb17  zrecon          background 0.6294       74        8770
  chb17 zlatent         signal_loss 0.7144       74         534
  chb17 zlatent   post_ictal_0_2min 0.4429       74          90
  chb17 zlatent  post_ictal_2_10min 0.5461       74         275
  chb17 zlatent post_ictal_10_60min 0.6006       74         157
  chb17 zlatent     post_ictal_1_4h    NaN       74           0
  chb17 zlatent            artifact 0.5492       74        9006
  chb17 zlatent          background 0.6075       74        8770
  chb17  zgamma         signal_loss 0.9981       74         534
  chb17  zgamma   post_ictal_0_2min 0.3656       74          90
  chb17  zgamma  post_ictal_2_10min 0.3942       74         275
  chb17  zgamma post_ictal_10_60min 0.3777       74         157
  chb17  zgamma     post_ictal_1_4h    NaN       74           0
  chb17  zgamma            artifact 0.5027       74        9006
  chb17  zgamma          background 0.8825       74        8770
```

## Item 6 -- event level, Scope T, category of every false alarm's onset window


**mag_pct=50 pen_mult=2 merge_s=90** (point `50_2_0_90`, already selected on validation -- results/continuous_eval/stepA_selected.json)

```
subject  n_false_alarms  n_ictal  n_signal_loss  n_post_ictal_0_2min  n_post_ictal_2_10min  n_post_ictal_10_60min  n_post_ictal_1_4h  n_artifact  n_background  share_ictal  share_signal_loss  share_post_ictal_0_2min  share_post_ictal_2_10min  share_post_ictal_10_60min  share_post_ictal_1_4h  share_artifact  share_background
  chb03             129        0              0                    0                     5                     16                  0          49            59       0.0000                0.0                   0.0000                    0.0388                     0.1240                 0.0000          0.3798            0.4574
  chb06             109        0              0                    0                     4                      7                  7          50            41       0.0000                0.0                   0.0000                    0.0367                     0.0642                 0.0642          0.4587            0.3761
  chb13             112        0              0                    0                     4                      8                  0          61            39       0.0000                0.0                   0.0000                    0.0357                     0.0714                 0.0000          0.5446            0.3482
  chb14             105        0              0                    0                     2                     11                  0          35            57       0.0000                0.0                   0.0000                    0.0190                     0.1048                 0.0000          0.3333            0.5429
  chb15             192        0              0                    1                    16                     30                  0          66            79       0.0000                0.0                   0.0052                    0.0833                     0.1562                 0.0000          0.3438            0.4115
  chb16              13        0              0                    0                     0                      0                  0           4             9       0.0000                0.0                   0.0000                    0.0000                     0.0000                 0.0000          0.3077            0.6923
  chb17              70        0              0                    0                     0                      0                  0          37            33       0.0000                0.0                   0.0000                    0.0000                     0.0000                 0.0000          0.5286            0.4714
  chb18             117        1              0                    0                     1                      5                  0          57            53       0.0085                0.0                   0.0000                    0.0085                     0.0427                 0.0000          0.4872            0.4530
 POOLED             847        1              0                    1                    32                     77                  7         359           370       0.0012                0.0                   0.0012                    0.0378                     0.0909                 0.0083          0.4238            0.4368
```

**mag_pct=75 pen_mult=5 merge_s=300** (point `75_5_300`, already selected on validation -- results/continuous_eval/stepA_selected.json)

```
subject  n_false_alarms  n_ictal  n_signal_loss  n_post_ictal_0_2min  n_post_ictal_2_10min  n_post_ictal_10_60min  n_post_ictal_1_4h  n_artifact  n_background  share_ictal  share_signal_loss  share_post_ictal_0_2min  share_post_ictal_2_10min  share_post_ictal_10_60min  share_post_ictal_1_4h  share_artifact  share_background
  chb03              34        0              0                    0                     0                      6                  0          15            13       0.0000                0.0                   0.0000                    0.0000                     0.1765                 0.0000          0.4412            0.3824
  chb06              26        0              0                    0                     0                      3                  2          10            11       0.0000                0.0                   0.0000                    0.0000                     0.1154                 0.0769          0.3846            0.4231
  chb13              35        0              0                    1                     0                      3                  0          17            14       0.0000                0.0                   0.0286                    0.0000                     0.0857                 0.0000          0.4857            0.4000
  chb14              15        0              0                    0                     1                      1                  0           3            10       0.0000                0.0                   0.0000                    0.0667                     0.0667                 0.0000          0.2000            0.6667
  chb15              49        0              0                    1                     3                      6                  0          18            21       0.0000                0.0                   0.0204                    0.0612                     0.1224                 0.0000          0.3673            0.4286
  chb16               7        0              0                    0                     0                      0                  0           3             4       0.0000                0.0                   0.0000                    0.0000                     0.0000                 0.0000          0.4286            0.5714
  chb17              16        0              0                    0                     0                      0                  0          11             5       0.0000                0.0                   0.0000                    0.0000                     0.0000                 0.0000          0.6875            0.3125
  chb18              28        1              0                    0                     0                      1                  0          15            11       0.0357                0.0                   0.0000                    0.0000                     0.0357                 0.0000          0.5357            0.3929
 POOLED             210        1              0                    2                     4                     20                  2          92            89       0.0048                0.0                   0.0095                    0.0190                     0.0952                 0.0095          0.4381            0.4238
```
