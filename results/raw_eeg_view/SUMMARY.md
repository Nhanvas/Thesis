# raw_eeg_view — what the ±5 SD flagged windows actually are

Produced by `src/raw_eeg_view.py` (one pass over the EDFs), 2026-10-05 16:08. Total elapsed 3.7 min.

## 0. Conventions, and what is and is not used

- **Signal.** Every trace and every number uses `preprocessing.filter_window`'s own filtering: 0.5–60 Hz Butterworth-4 `sosfiltfilt` then 60 Hz notch (Q=30) `filtfilt`, applied to the window plus `FILTER_PAD` = 768 samples each side, centre kept. The implementation slices an in-RAM copy of the EDF instead of re-reading per window; it reproduces `P.filter_window` to **max abs difference 0.0** (asserted once per file at run time, and over 12 windows of two subjects by `--selfcheck`). This matters: `continuous_eval.py` documents that whole-file filtering can flip borderline 5 SD accept/reject decisions, which is exactly what Part 2 counts.
- **Flagged.** `is_artifact` = at least one sample with |x| above that channel's committed threshold `data/processed/{subj}_stats.json: artifact_thresh_uV` (= 5 × the per-channel SD of filtered interictal), on a window that is neither ictal nor inside the 4 h post-seizure buffer — the same definition and the same thresholds `continuous_eval.compute_artifact_flags` used to build `results/continuous_eval/cache/mask/`.
- **No model, no score, no fitted threshold** appears anywhere in this file. Seizure labels are used only to pick which seizures to draw (Part 1) and to measure AUROC (Part 3).
- **Test subjects contribute no numbers.** Parts 2 and 3 use the 3 validation subjects and the 12 training subjects only (chb10, chb11, chb22, chb01, chb02, chb04, chb05, chb07, chb08, chb09, chb12, chb19, chb20, chb21, chb23). Test subjects appear only in the Part 1 pictures.

### Data actually read for Parts 2 and 3

| subject | n_files | n_windows | n_seizure | n_flagged | n_background | n_buffer | n_signal_loss | n_sz_lt20 | n_sz_ge20 |
|---|---|---|---|---|---|---|---|---|---|
| chb10 | 25 | 45020 | 117 | 10978 | 28526 | 5405 | 0 | 0 | 117 |
| chb11 | 31 | 27713 | 204 | 12078 | 14231 | 1202 | 0 | 0 | 204 |
| chb22 | 31 | 27902 | 55 | 15666 | 11476 | 708 | 0 | 0 | 55 |
| chb01 | 9 | 7781 | 115 | 2143 | 2434 | 3093 | 0 | 0 | 115 |
| chb02 | 5 | 3839 | 45 | 1874 | 1543 | 379 | 0 | 3 | 42 |
| chb04 | 5 | 16789 | 99 | 3064 | 8117 | 5542 | 0 | 0 | 99 |
| chb05 | 7 | 6300 | 143 | 1464 | 2489 | 2207 | 0 | 0 | 143 |
| chb07 | 5 | 15335 | 83 | 6537 | 6134 | 2580 | 4 | 0 | 83 |
| chb08 | 7 | 6300 | 234 | 3244 | 1808 | 1019 | 0 | 0 | 234 |
| chb09 | 5 | 14232 | 73 | 3226 | 7500 | 3454 | 0 | 0 | 73 |
| chb12 | 12 | 10513 | 271 | 1710 | 3383 | 5325 | 1 | 4 | 267 |
| chb19 | 5 | 4436 | 62 | 2186 | 1218 | 972 | 0 | 0 | 62 |
| chb20 | 8 | 6808 | 81 | 1182 | 2494 | 3080 | 0 | 0 | 81 |
| chb21 | 6 | 5247 | 53 | 2766 | 1150 | 1280 | 0 | 4 | 49 |
| chb23 | 5 | 9954 | 109 | 1729 | 1881 | 6293 | 0 | 0 | 109 |

All files of chb10/chb11/chb22; for each of the 12 training subjects every file that contains a seizure plus 2 other files drawn with `random.Random(42)`.

## PART 1 — pictures

Seizure panels span onset−20 s to onset+40 s; window panels span 30 s centred on the 4 s window (shaded red). 18 channels, pipeline-filtered, one amplitude scale per sheet written on every panel (channel spacing, plus a scale bar). The lower sub-panel of each panel is the Welch PSD of the **same segment, raw and unfiltered**, 0.5–100 Hz, log power; the dashed line is 60 Hz.

**Sheet A** — A: the 3 shortest seizures of chb16, the 3 shortest of chb06, the 2 shortest of chb14

Files: `sheet_A.png`; common channel spacing 500 µV. Individual panels in `panels/A_*.png`.

| subject | file | onset (s) | offset (s) | duration (s) |
|---|---|---|---|---|
| chb16 | chb16_16.edf | 1214 | 1220 | 6 |
| chb16 | chb16_17.edf | 1694 | 1700 | 6 |
| chb16 | chb16_18.edf | 1909 | 1916 | 7 |
| chb06 | chb06_10.edf | 10833 | 10845 | 12 |
| chb06 | chb06_18.edf | 7799 | 7811 | 12 |
| chb06 | chb06_13.edf | 506 | 519 | 13 |
| chb14 | chb14_03.edf | 1986 | 2000 | 14 |
| chb14 | chb14_06.edf | 1911 | 1925 | 14 |

**Sheet B** — B: 3 seizures of chb15, 2 of chb03, 2 of chb18, each drawn with random.Random(42) over that subject's seizures (no model score)

Files: `sheet_B.png`; common channel spacing 300 µV. Individual panels in `panels/B_*.png`.

| subject | file | onset (s) | offset (s) | duration (s) |
|---|---|---|---|---|
| chb15 | chb15_06.edf | 272 | 397 | 125 |
| chb15 | chb15_17.edf | 1925 | 1960 | 35 |
| chb15 | chb15_40.edf | 834 | 894 | 60 |
| chb03 | chb03_01.edf | 362 | 414 | 52 |
| chb03 | chb03_35.edf | 2592 | 2656 | 64 |
| chb18 | chb18_29.edf | 3477 | 3527 | 50 |
| chb18 | chb18_36.edf | 463 | 509 | 46 |

**Sheet CD** — C: flagged (is_artifact) non-ictal non-buffer windows -- 2 per subject from chb10, chb11, chb22, chb13, one single-spike and one sustained each, first of each cause met in a random.Random(42) permutation of that subject's flagged windows  •  D: chb13's 2 files with the highest flagged share, 3 random.Random(42) flagged windows each; the per-channel SD of the file divided by the subject-wide per-channel SD (stats.json ch_std_uV) is printed beside each trace

Files: `sheet_CD.png`, `sheet_CD_p2.png`; common channel spacing 500 µV. Individual panels in `panels/CD_*.png`.

C panels:

| subject | file | window (s) | samples >5 SD | cause |
|---|---|---|---|---|
| chb10 | chb10_05.edf | [4008, 4012] | 3 | single-spike |
| chb10 | chb10_13.edf | [6972, 6976] | 60 | sustained |
| chb11 | chb11_56.edf | [2708, 2712] | 1 | single-spike |
| chb11 | chb11_99.edf | [1060, 1064] | 867 | sustained |
| chb22 | chb22_18.edf | [8, 12] | 3 | single-spike |
| chb22 | chb22_04.edf | [3392, 3396] | 30 | sustained |
| chb13 | chb13_47.edf | [240, 244] | 3 | single-spike |
| chb13 | chb13_19.edf | [1936, 1940] | 18 | sustained |

D panels (chb13, the 2 files with the highest flagged share):

| subject | file | window (s) | samples >5 SD | cause |
|---|---|---|---|---|
| chb13 | chb13_04.edf | [112, 116] | 94 | sustained |
| chb13 | chb13_04.edf | [472, 476] | 16 | sustained |
| chb13 | chb13_04.edf | [2708, 2712] | 179 | sustained |
| chb13 | chb13_05.edf | [104, 108] | 194 | sustained |
| chb13 | chb13_05.edf | [460, 464] | 490 | sustained |
| chb13 | chb13_05.edf | [2716, 2720] | 6 | sustained |

chb13 flagged share by file (top 6):

| file | flagged | windows | flagged share |
|---|---|---|---|
| chb13_04.edf | 869 | 900 | 0.9656 |
| chb13_05.edf | 853 | 900 | 0.9478 |
| chb13_22.edf | 828 | 900 | 0.9200 |
| chb13_03.edf | 826 | 900 | 0.9178 |
| chb13_30.edf | 823 | 900 | 0.9144 |
| chb13_06.edf | 801 | 900 | 0.8900 |

`chb13_04.edf`: per-channel SD(file)/SD(subject) median **1.28**, min 0.85 (FZ-CZ), max 1.67 (C3-P3); per-channel values are printed beside each trace on the panel.
`chb13_05.edf`: per-channel SD(file)/SD(subject) median **1.27**, min 0.76 (FZ-CZ), max 2.15 (C3-P3); per-channel values are printed beside each trace on the panel.


> Note on the 8-panels-per-PNG cap: C+D is 14 panels, so sheet CD is written as `sheet_CD.png` (8 panels) and `sheet_CD_p2.png` (6 panels).

## PART 2 — what the flagged windows are

Every flagged window of the 15 non-test subjects (69,847 windows). `cause = single-spike` iff the total number of samples above 5 SD, summed over all 18 channels, is ≤ 3; `sustained` otherwise. `top_*` = share of flagged windows whose channel with the most exceedances is in that group; `any_*` = share with at least one exceedance anywhere in that group (groups overlap, so `any_*` does not sum to 1).

### Cause and exceedance magnitude

| subject | flagged | single-spike | sustained | median >5SD samples | mean | p95 | median #ch | mean #ch | share 1 channel only | most frequent top channel |
|---|---|---|---|---|---|---|---|---|---|---|
| chb10 | 10978 | 0.1495 | 0.8505 | 17.0000 | 73.1417 | 281.0000 | 2.0000 | 2.9476 | 0.3498 | T7-P7 |
| chb11 | 12078 | 0.0974 | 0.9026 | 52.0000 | 142.5763 | 584.1500 | 4.0000 | 4.9168 | 0.1848 | FP1-F3 |
| chb22 | 15666 | 0.0506 | 0.9494 | 79.0000 | 132.0271 | 444.0000 | 5.0000 | 5.4436 | 0.1284 | FP1-F7 |
| chb01 | 2143 | 0.0700 | 0.9300 | 50.0000 | 97.1087 | 352.9000 | 4.0000 | 4.3574 | 0.1848 | FP1-F7 |
| chb02 | 1874 | 0.0704 | 0.9296 | 36.0000 | 204.3164 | 593.3500 | 3.0000 | 4.6499 | 0.1110 | P8-O2 |
| chb04 | 3064 | 0.0594 | 0.9406 | 1936.0000 | 1240.6041 | 2120.0000 | 15.0000 | 11.3283 | 0.1025 | P7-O1 |
| chb05 | 1464 | 0.1175 | 0.8825 | 25.0000 | 56.5287 | 219.7000 | 3.0000 | 3.8381 | 0.2117 | P8-O2 |
| chb07 | 6537 | 0.0586 | 0.9414 | 75.0000 | 131.5466 | 364.0000 | 4.0000 | 4.8492 | 0.1210 | FP2-F4 |
| chb08 | 3244 | 0.0700 | 0.9300 | 75.0000 | 107.3579 | 339.8500 | 5.0000 | 4.8184 | 0.1415 | FP2-F8 |
| chb09 | 3226 | 0.1810 | 0.8190 | 17.0000 | 173.5955 | 1036.0000 | 2.0000 | 3.4684 | 0.3655 | FP2-F4 |
| chb12 | 1710 | 0.1158 | 0.8842 | 25.0000 | 62.1088 | 217.1000 | 3.0000 | 3.3789 | 0.2918 | FZ-CZ |
| chb19 | 2186 | 0.0453 | 0.9547 | 80.0000 | 138.3577 | 451.7500 | 5.0000 | 5.3678 | 0.1016 | FP2-F8 |
| chb20 | 1182 | 0.1396 | 0.8604 | 23.0000 | 62.2860 | 255.7000 | 3.0000 | 3.5601 | 0.3198 | FP2-F4 |
| chb21 | 2766 | 0.0474 | 0.9526 | 85.0000 | 127.6916 | 423.0000 | 5.0000 | 5.3651 | 0.0763 | FP1-F7 |
| chb23 | 1729 | 0.0833 | 0.9167 | 41.0000 | 70.7536 | 245.6000 | 3.0000 | 3.9572 | 0.1810 | FP1-F7 |
| POOLED | 69847 | 0.0885 | 0.9115 | 51.0000 | 168.8591 | 619.0000 | 4.0000 | 4.8295 | 0.1913 |  |

### Share of flagged windows by channel group of the dominant channel

| subject | frontopolar | temporal | central | parieto-occipital | midline |
|---|---|---|---|---|---|
| chb10 | 0.2974 | 0.3588 | 0.1182 | 0.1355 | 0.0900 |
| chb11 | 0.4299 | 0.2355 | 0.1205 | 0.1215 | 0.0927 |
| chb22 | 0.4307 | 0.1711 | 0.1380 | 0.1233 | 0.1370 |
| chb01 | 0.2683 | 0.1736 | 0.1927 | 0.2445 | 0.1209 |
| chb02 | 0.2898 | 0.1249 | 0.0795 | 0.4397 | 0.0662 |
| chb04 | 0.0424 | 0.0718 | 0.1919 | 0.6567 | 0.0372 |
| chb05 | 0.3948 | 0.2220 | 0.1578 | 0.2036 | 0.0219 |
| chb07 | 0.6693 | 0.1040 | 0.0428 | 0.0526 | 0.1313 |
| chb08 | 0.5734 | 0.2053 | 0.0829 | 0.0990 | 0.0395 |
| chb09 | 0.4299 | 0.2942 | 0.0911 | 0.0725 | 0.1122 |
| chb12 | 0.3690 | 0.0988 | 0.1678 | 0.1187 | 0.2456 |
| chb19 | 0.6107 | 0.0737 | 0.0823 | 0.1061 | 0.1272 |
| chb20 | 0.3579 | 0.1294 | 0.1650 | 0.1675 | 0.1802 |
| chb21 | 0.4877 | 0.1988 | 0.1092 | 0.0936 | 0.1106 |
| chb23 | 0.6709 | 0.1648 | 0.0411 | 0.0746 | 0.0486 |
| POOLED | 0.4231 | 0.2037 | 0.1170 | 0.1498 | 0.1064 |

### Share of flagged windows with at least one exceedance in the group

| subject | frontopolar | temporal | central | parieto-occipital | midline |
|---|---|---|---|---|---|
| chb10 | 0.4712 | 0.6017 | 0.2183 | 0.4375 | 0.1557 |
| chb11 | 0.5880 | 0.5540 | 0.4901 | 0.3556 | 0.2897 |
| chb22 | 0.5935 | 0.5776 | 0.4337 | 0.4849 | 0.2810 |
| chb01 | 0.4410 | 0.5035 | 0.4951 | 0.4690 | 0.3719 |
| chb02 | 0.5678 | 0.5763 | 0.4861 | 0.6649 | 0.1590 |
| chb04 | 0.7311 | 0.8136 | 0.8845 | 0.7990 | 0.6890 |
| chb05 | 0.6510 | 0.5936 | 0.3094 | 0.5403 | 0.0792 |
| chb07 | 0.8371 | 0.5958 | 0.3365 | 0.1719 | 0.2252 |
| chb08 | 0.7090 | 0.6998 | 0.3542 | 0.3924 | 0.1378 |
| chb09 | 0.6175 | 0.5363 | 0.2269 | 0.1959 | 0.2610 |
| chb12 | 0.4930 | 0.3813 | 0.4064 | 0.2801 | 0.3480 |
| chb19 | 0.7223 | 0.6459 | 0.2539 | 0.3568 | 0.2795 |
| chb20 | 0.4992 | 0.4501 | 0.2868 | 0.3646 | 0.3113 |
| chb21 | 0.6493 | 0.6602 | 0.3749 | 0.3420 | 0.2646 |
| chb23 | 0.8149 | 0.5697 | 0.1457 | 0.2267 | 0.1122 |
| POOLED | 0.6121 | 0.5894 | 0.3895 | 0.4043 | 0.2605 |

Groups: frontopolar = FP1-F7, FP1-F3, FP2-F4, FP2-F8 · temporal = F7-T7, T7-P7, F8-T8, T8-P8 · central = F3-C3, C3-P3, F4-C4, C4-P4 · parieto-occipital = P7-O1, P3-O1, P4-O2, P8-O2 · midline = FZ-CZ, CZ-PZ.

Full tables: `tables/part2_by_subject.csv`.

## PART 3 — label-free features, labels used only to score separability

Per window and per channel, on the pipeline-filtered signal in µV: Hjorth mobility `sqrt(var(dx)/var(x))` and complexity `sqrt(var(ddx)/var(dx))/mobility`; line length `sum|dx|` divided by the channel SD; relative power in 0.5–4, 4–8, 8–13, 13–30, 30–60 Hz (Welch, nperseg 512, noverlap 256, df 0.5 Hz; relative to 0.5–60 Hz, so the five sum to 1); muscle proxy 20–60/0.5–60; slow proxy 0.5–2/0.5–60; spectral entropy over 0.5–60 Hz normalised by log(#bins); rhythmicity = share of 0.5–60 Hz power within ±1.5 Hz of the spectral peak; kurtosis (Fisher, unbiased). Each is summarised across the 18 channels as **median** (`_med`) and **max** (`_max`). One spatial feature, `frac_ch_sd_gt3med`: fraction of channels whose window SD exceeds 3× that channel's median window SD over all of this subject's analysed windows (label-free). 27 features in total.

Contrasts: `sz_vs_flagged` (seizure vs flagged non-seizure), `sz_vs_bg` (seizure vs unflagged background), `flagged_vs_bg`. **AUROC is reported with the first-named class as positive**, so >0.5 means the feature is higher in the first class and <0.5 means higher in the second. Pooled = all windows of the 3 validation + 12 training subjects pooled. Signal-loss windows are excluded from every group.

### sz_vs_flagged — pooled AUROC (direction: >0.5 = higher in seizure)

| feature | pooled (all) | pooled (sz <20 s) | pooled (sz ≥20 s) | chb10 (all) | chb11 (all) | chb22 (all) |
|---|---|---|---|---|---|---|
| frac_ch_sd_gt3med | 0.7558 | 0.4430 | 0.7578 | 0.8547 | 0.9165 | 0.8809 |
| kurtosis_max | 0.2646 | 0.3088 | 0.2643 | 0.3051 | 0.4519 | 0.3159 |
| kurtosis_med | 0.3113 | 0.4209 | 0.3106 | 0.4628 | 0.3227 | 0.2529 |
| rel_4_8_med | 0.6748 | 0.7443 | 0.6744 | 0.9064 | 0.9295 | 0.8251 |
| slow_05_2_med | 0.3325 | 0.3633 | 0.3323 | 0.2378 | 0.1723 | 0.1341 |
| rel_4_8_max | 0.6648 | 0.5946 | 0.6653 | 0.9406 | 0.9099 | 0.8259 |
| slow_05_2_max | 0.3504 | 0.3248 | 0.3506 | 0.3168 | 0.2091 | 0.2035 |
| linelen_sd_max | 0.3803 | 0.3093 | 0.3808 | 0.4004 | 0.4227 | 0.5564 |
| mobility_max | 0.3846 | 0.3035 | 0.3852 | 0.3885 | 0.4504 | 0.5344 |
| rel_30_60_max | 0.3858 | 0.2838 | 0.3865 | 0.3582 | 0.4622 | 0.5684 |
| muscle_20_60_max | 0.3891 | 0.2943 | 0.3897 | 0.3848 | 0.4526 | 0.5222 |
| complexity_max | 0.3988 | 0.2938 | 0.3995 | 0.1635 | 0.5237 | 0.3241 |
| rel_d05_4_max | 0.4125 | 0.3187 | 0.4131 | 0.1813 | 0.4026 | 0.2551 |
| spec_entropy_max | 0.4310 | 0.3789 | 0.4313 | 0.5381 | 0.4716 | 0.5115 |
| rel_8_13_med | 0.5655 | 0.7292 | 0.5645 | 0.9617 | 0.4828 | 0.5492 |
| rel_30_60_med | 0.4372 | 0.3815 | 0.4376 | 0.4362 | 0.3868 | 0.6258 |
| rel_13_30_max | 0.4407 | 0.4544 | 0.4406 | 0.5123 | 0.3710 | 0.4486 |
| rel_d05_4_med | 0.4452 | 0.3784 | 0.4456 | 0.1093 | 0.4372 | 0.3202 |
| muscle_20_60_med | 0.4649 | 0.4473 | 0.4650 | 0.5664 | 0.3847 | 0.5987 |
| rel_8_13_max | 0.5328 | 0.6695 | 0.5319 | 0.9619 | 0.4055 | 0.5727 |
| linelen_sd_med | 0.4674 | 0.4899 | 0.4673 | 0.6993 | 0.3480 | 0.5708 |
| mobility_med | 0.4709 | 0.4735 | 0.4709 | 0.6946 | 0.3665 | 0.6079 |
| rhythmicity_max | 0.4725 | 0.3528 | 0.4732 | 0.2541 | 0.5789 | 0.3538 |
| spec_entropy_med | 0.5099 | 0.5825 | 0.5094 | 0.8351 | 0.3825 | 0.5667 |
| rel_13_30_med | 0.5072 | 0.5565 | 0.5069 | 0.7943 | 0.3081 | 0.5069 |
| rhythmicity_med | 0.4949 | 0.4279 | 0.4954 | 0.1480 | 0.5838 | 0.4371 |
| complexity_med | 0.5019 | 0.4439 | 0.5023 | 0.1136 | 0.6406 | 0.4273 |

n = 1,744 seizure vs 69,847 flagged (pooled, stratum all).

### sz_vs_bg — pooled AUROC (direction: >0.5 = higher in seizure)

| feature | pooled (all) | pooled (sz <20 s) | pooled (sz ≥20 s) | chb10 (all) | chb11 (all) | chb22 (all) |
|---|---|---|---|---|---|---|
| frac_ch_sd_gt3med | 0.8663 | 0.6319 | 0.8678 | 0.8974 | 0.9853 | 0.9635 |
| rel_30_60_max | 0.6539 | 0.5781 | 0.6543 | 0.7803 | 0.5929 | 0.8373 |
| muscle_20_60_max | 0.6493 | 0.5895 | 0.6497 | 0.8117 | 0.5590 | 0.8052 |
| mobility_max | 0.6489 | 0.6110 | 0.6492 | 0.8345 | 0.5732 | 0.8253 |
| spec_entropy_max | 0.6277 | 0.6285 | 0.6277 | 0.9091 | 0.5338 | 0.7617 |
| rel_30_60_med | 0.6252 | 0.6296 | 0.6252 | 0.8443 | 0.3894 | 0.7921 |
| muscle_20_60_med | 0.6194 | 0.6372 | 0.6193 | 0.9022 | 0.3672 | 0.7593 |
| rel_13_30_max | 0.6124 | 0.6158 | 0.6124 | 0.8847 | 0.3513 | 0.7267 |
| slow_05_2_med | 0.3894 | 0.4418 | 0.3891 | 0.2458 | 0.2410 | 0.1776 |
| linelen_sd_max | 0.6078 | 0.5739 | 0.6080 | 0.8187 | 0.4512 | 0.7976 |
| mobility_med | 0.6033 | 0.6273 | 0.6032 | 0.9276 | 0.3517 | 0.7753 |
| slow_05_2_max | 0.4200 | 0.4016 | 0.4201 | 0.3607 | 0.3515 | 0.2531 |
| rel_13_30_med | 0.5764 | 0.6259 | 0.5761 | 0.9411 | 0.2004 | 0.6436 |
| linelen_sd_med | 0.5720 | 0.6067 | 0.5718 | 0.9055 | 0.2776 | 0.7298 |
| rel_d05_4_med | 0.4493 | 0.3848 | 0.4498 | 0.1007 | 0.5423 | 0.3403 |
| rel_4_8_max | 0.5488 | 0.4514 | 0.5494 | 0.9170 | 0.8430 | 0.6578 |
| kurtosis_max | 0.5473 | 0.6247 | 0.5468 | 0.5689 | 0.6310 | 0.6120 |
| spec_entropy_med | 0.5420 | 0.6186 | 0.5415 | 0.9081 | 0.2960 | 0.6331 |
| complexity_med | 0.4606 | 0.3976 | 0.4610 | 0.1085 | 0.7100 | 0.3431 |
| kurtosis_med | 0.5363 | 0.6634 | 0.5355 | 0.6327 | 0.4634 | 0.5781 |
| rhythmicity_max | 0.5359 | 0.4335 | 0.5366 | 0.2317 | 0.7836 | 0.5408 |
| rel_4_8_med | 0.5272 | 0.5572 | 0.5270 | 0.8483 | 0.8156 | 0.5712 |
| rel_8_13_max | 0.5236 | 0.6321 | 0.5230 | 0.9781 | 0.2250 | 0.5495 |
| rhythmicity_med | 0.4878 | 0.4207 | 0.4883 | 0.1132 | 0.7020 | 0.4586 |
| rel_d05_4_max | 0.4880 | 0.4219 | 0.4884 | 0.1840 | 0.6073 | 0.4414 |
| rel_8_13_med | 0.4942 | 0.6192 | 0.4935 | 0.9601 | 0.1567 | 0.3458 |
| complexity_max | 0.4977 | 0.4042 | 0.4983 | 0.2222 | 0.7235 | 0.5933 |

n = 1,744 seizure vs 94,384 background (pooled, stratum all).

### flagged_vs_bg — pooled AUROC (direction: >0.5 = higher in flagged)

| feature | pooled (all) | pooled (sz <20 s) | pooled (sz ≥20 s) | chb10 (all) | chb11 (all) | chb22 (all) |
|---|---|---|---|---|---|---|
| kurtosis_max | 0.7803 | 0.7803 | 0.7803 | 0.7878 | 0.6724 | 0.7780 |
| kurtosis_med | 0.7362 | 0.7362 | 0.7362 | 0.6776 | 0.6914 | 0.8061 |
| mobility_max | 0.7001 | 0.7001 | 0.7001 | 0.8179 | 0.5996 | 0.6480 |
| rel_30_60_max | 0.6965 | 0.6965 | 0.6965 | 0.8114 | 0.5888 | 0.6478 |
| muscle_20_60_max | 0.6870 | 0.6870 | 0.6870 | 0.8155 | 0.5668 | 0.6401 |
| rel_4_8_med | 0.3139 | 0.3139 | 0.3139 | 0.3596 | 0.2446 | 0.1903 |
| frac_ch_sd_gt3med | 0.6829 | 0.6829 | 0.6829 | 0.5609 | 0.7516 | 0.7554 |
| linelen_sd_max | 0.6703 | 0.6703 | 0.6703 | 0.7913 | 0.5302 | 0.6176 |
| spec_entropy_max | 0.6594 | 0.6594 | 0.6594 | 0.7955 | 0.5525 | 0.6117 |
| rel_30_60_med | 0.6488 | 0.6488 | 0.6488 | 0.7963 | 0.5701 | 0.5875 |
| rel_4_8_max | 0.3520 | 0.3520 | 0.3520 | 0.3998 | 0.3236 | 0.2738 |
| rel_13_30_max | 0.6418 | 0.6418 | 0.6418 | 0.8035 | 0.4822 | 0.6025 |
| muscle_20_60_med | 0.6258 | 0.6258 | 0.6258 | 0.7852 | 0.5497 | 0.5795 |
| mobility_med | 0.6129 | 0.6129 | 0.6129 | 0.7635 | 0.5571 | 0.5790 |
| complexity_max | 0.6011 | 0.6011 | 0.6011 | 0.5978 | 0.6406 | 0.7137 |
| linelen_sd_med | 0.5889 | 0.5889 | 0.5889 | 0.7374 | 0.5146 | 0.5644 |
| slow_05_2_max | 0.5858 | 0.5858 | 0.5858 | 0.5554 | 0.7052 | 0.5866 |
| rel_d05_4_max | 0.5778 | 0.5778 | 0.5778 | 0.4873 | 0.6785 | 0.6921 |
| slow_05_2_med | 0.5731 | 0.5731 | 0.5731 | 0.5082 | 0.6533 | 0.5763 |
| rel_13_30_med | 0.5653 | 0.5653 | 0.5653 | 0.7439 | 0.4607 | 0.5519 |
| rhythmicity_max | 0.5645 | 0.5645 | 0.5645 | 0.4411 | 0.6508 | 0.6701 |
| rel_8_13_med | 0.4394 | 0.4394 | 0.4394 | 0.5330 | 0.2224 | 0.3238 |
| complexity_med | 0.4597 | 0.4597 | 0.4597 | 0.5125 | 0.5154 | 0.4408 |
| spec_entropy_med | 0.5319 | 0.5319 | 0.5319 | 0.6612 | 0.4892 | 0.5195 |
| rhythmicity_med | 0.4927 | 0.4927 | 0.4927 | 0.3835 | 0.5611 | 0.5356 |
| rel_d05_4_med | 0.5022 | 0.5022 | 0.5022 | 0.4463 | 0.5954 | 0.5471 |
| rel_8_13_max | 0.5008 | 0.5008 | 0.5008 | 0.6044 | 0.3338 | 0.4643 |

n = 69,847 flagged vs 94,384 background (pooled, stratum all).

### Marked features — pooled seizure-vs-flagged AUROC ≥ 0.75 or ≤ 0.25

| feature | pooled AUROC | direction | val subjects agreeing | ≥2 of 3 agree | chb10 | chb11 | chb22 |
|---|---|---|---|---|---|---|---|
| frac_ch_sd_gt3med | 0.7558 | higher in seizures | 3 | True | 0.8547 | 0.9165 | 0.8809 |

Per-subject values for every feature, contrast and stratum: `tables/part3_auroc.csv`; marked features: `tables/part3_marked.csv`; per-subject window counts: `tables/part3_groups.csv`.

## PART 4 — read-only facts (nothing was changed)

### (a) Does `data/processed/{subj}_interictal.npy` contain only windows that passed the ±5 SD rule?

Yes -- only windows that passed the +-5 SD rule are written. In preprocessing.write_windows a window reaches mm_inter only on the `elif not win_buffered` branch, and inside it only `if not is_artifact and idx_inter < n_inter_max`, where is_artifact is True as soon as any of the 18 channels has max|x| > artifact_threshold[ch] = 5 x ch_std[ch]. So {subj}_interictal.npy holds exactly the non-ictal, non-4h-post-seizure-buffer windows whose peak amplitude stays within 5 SD on every channel (then z-scored). Ictal windows go to {subj}_ictal.npy and are deliberately NOT artifact-rejected.

| subject | windows (stats.json) | windows (.npy shape[0]) | windows (adjs_topk20) | rejected by 5 SD | ictal (separate file) |
|---|---|---|---|---|---|
| chb01 | 15409 | 15409 | 15409 | 17883 | 115 |
| chb02 | 17805 | 17805 | 17805 | 13512 | 45 |
| chb04 | 94438 | 94438 | 94438 | 40407 | 99 |
| chb05 | 18692 | 18692 | 18692 | 14063 | 143 |
| chb07 | 28019 | 28019 | 28019 | 29666 | 83 |
| chb08 | 7550 | 7550 | 7550 | 9207 | 234 |
| chb09 | 36434 | 36434 | 36434 | 21139 | 73 |
| chb12 | 7459 | 7459 | 7459 | 5739 | 271 |
| chb19 | 12926 | 12926 | 12926 | 12978 | 62 |
| chb20 | 11852 | 11852 | 11852 | 9855 | 81 |
| chb21 | 11047 | 11047 | 11047 | 16268 | 53 |
| chb23 | 8556 | 8556 | 8556 | 9000 | 109 |

**Total over the 12 training subjects: 270,187 interictal windows.** stats.json, the `.npy` shape and the committed graph tensors agree exactly for every subject.

### (b) The original GAE training

- **Windows trained on: 270,187.** sum of n_interictal over the 12 training subjects in data/processed/{subj}_stats.json, equal to the committed {subj}_interictal_adjs_topk20.npy row counts; independently recorded as "270,187 interictal windows" in docs/PHASE_C_FULL_AUDIT.md:202 and docs/PHASE_C_CLOSEOUT_provenance.md:37 and docs/RESULTS_OF_RECORD_phaseB.md:152.
- **Subjects:** docs/archive/PROVENANCE_MAP.md:160 -- "The joint model was trained on 12 of the 15 (interictal only) with 3 held-out as validation subjects: train = chb01,02,04,05,07,08,09,12,19,20,21,23; val = chb10,11,22"; the same 12 are TRAIN_SUBJS in src/retrain/train_gae_joint.py.
- **Kaggle wall-clock:** No wall-clock time for the ORIGINAL GAE training exists anywhere in the repo, the notebooks or on Kaggle: docs/archive/PROVENANCE_MAP.md:152 records that the original training notebook was "confirmed unrecoverable (not in repo, notebook, or Kaggle)" and notebooks/kaggle_gpu/thesis-cpd-final.ipynb only loads the trained checkpoint and scores with it (Sections 1B/2) -- it contains no training loop. The recorded Kaggle wall-clock figures are for the reconstructed retrain (PREREG 01 recipe, same 270,187 windows): ~3.5 h per GAE seed (docs/PHASE_C_FINAL_HANDOFF.md:20) and ~3.2 h per seed (docs/PHASE_D_HANDOFF.md:44 for the small rlg-class model; docs/PHASE_C_FULL_AUDIT.md:198 reports the same ~3.2 h after a host-bound data-movement bug was fixed), 200 epochs, 4 Kaggle accounts in parallel.
- **Script defining the training windows:** Two scripts, in sequence. (1) src/dataprep/preprocessing.py defines WHICH windows exist: write_windows() (called from process_subject) emits data/processed/{subj}_interictal.npy = non-ictal, non-buffer, 5 SD-passing, z-scored 4 s windows. (2) src/retrain/train_gae_joint.py defines which of them are the TRAINING set: TRAIN_SUBJS (the 12 subjects, lines 35-38) + build_dataset()/load_subject(), which read {subj}_interictal_adjs_topk20.npy and {subj}_interictal_features.npy -- the graph/feature tensors derived from those same interictal windows by src/dataprep/build_graphs.py + apply_topk_multiband.py. The window grid itself (4 s, 1024 samples, no overlap) is preprocessing.py's WIN_S/WIN_SAMPLES.

## Outputs

```
results/raw_eeg_view/
  SUMMARY.md                  this file
  sheet_A.png sheet_B.png sheet_CD.png sheet_CD_p2.png
  panels/                     one PNG per panel
  tables/part2_by_subject.csv part3_auroc.csv part3_marked.csv part3_groups.csv
  cache/{subj}.npz            per-window flags, exceedance counts, features
  part1_panels.json part4_facts.json run.log
```
