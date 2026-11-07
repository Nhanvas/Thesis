# R0 diagnosis of chb17 (descriptive; plan §12 07/11 12:49)

Rebuilt with the record code on the earlier view and the committed stats.json; compared with `chb17.npz` (sha256 38dba59a2d01). Build 309 s.

- windows 18906; signal-loss 534; beyond tolerance 3226 (in signal-loss 529, outside 2697)
- G-feat: all windows FAIL; chain windows PASS; gate (scope chain) PASS
- non-finite flip cells: 1 (`cells_nonfinite.csv`)
- outside signal-loss, max |diff| quantiles (50/99/100 %): f7 {50: 0.0, 99: 0.0, 100: 9.5367431640625e-07}; bp5 {50: 0.0, 99: 0.0, 100: 3.5762786865234375e-07}

## Per file (files with signal-loss or beyond-tolerance windows)

| file | windows | signal_loss | beyond_tol | beyond_tol_in_signal_loss | beyond_tol_outside_signal_loss | signal_loss_equal_within_tol | f7_max_abs_outside_sl | bp5_max_abs_outside_sl | adj_windows_differing_outside_sl | f7_max_abs_in_sl | bp5_max_abs_in_sl | adj_windows_differing_in_sl | f7_finite_flips |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chb17a_03.edf | 900 | 0 | 138 | 0 | 138 | 0 | 0 | 0 | 138 | nan | nan | 0 | 0 |
| chb17a_04.edf | 900 | 0 | 119 | 0 | 119 | 0 | 3.725e-09 | 0 | 119 | nan | nan | 0 | 0 |
| chb17a_05.edf | 900 | 0 | 146 | 0 | 146 | 0 | 9.313e-10 | 0 | 146 | nan | nan | 0 | 0 |
| chb17a_06.edf | 900 | 0 | 139 | 0 | 139 | 0 | 9.537e-07 | 3.576e-07 | 139 | nan | nan | 0 | 0 |
| chb17a_08.edf | 900 | 0 | 140 | 0 | 140 | 0 | 0 | 0 | 140 | nan | nan | 0 | 0 |
| chb17b_57.edf | 900 | 0 | 140 | 0 | 140 | 0 | 0 | 0 | 140 | nan | nan | 0 | 0 |
| chb17b_58.edf | 900 | 0 | 146 | 0 | 146 | 0 | 1.49e-08 | 0 | 146 | nan | nan | 0 | 0 |
| chb17b_59.edf | 900 | 0 | 127 | 0 | 127 | 0 | 0 | 0 | 127 | nan | nan | 0 | 0 |
| chb17b_60.edf | 900 | 0 | 105 | 0 | 105 | 0 | 0 | 0 | 105 | nan | nan | 0 | 0 |
| chb17b_63.edf | 906 | 0 | 132 | 0 | 132 | 0 | 2.384e-07 | 1.192e-07 | 132 | nan | nan | 0 | 0 |
| chb17b_67.edf | 900 | 0 | 149 | 0 | 149 | 0 | 1.49e-08 | 0 | 149 | nan | nan | 0 | 0 |
| chb17b_68.edf | 900 | 0 | 132 | 0 | 132 | 0 | 0 | 0 | 132 | nan | nan | 0 | 0 |
| chb17b_69.edf | 900 | 534 | 583 | 529 | 54 | 5 | 1.164e-10 | 0 | 54 | 28.84 | 3.844 | 529 | 1 |
| chb17c_02.edf | 900 | 0 | 125 | 0 | 125 | 0 | 9.537e-07 | 3.576e-07 | 125 | nan | nan | 0 | 0 |
| chb17c_03.edf | 900 | 0 | 129 | 0 | 129 | 0 | 1.863e-09 | 0 | 129 | nan | nan | 0 | 0 |
| chb17c_04.edf | 900 | 0 | 126 | 0 | 126 | 0 | 1.192e-07 | 0 | 126 | nan | nan | 0 | 0 |
| chb17c_05.edf | 900 | 0 | 121 | 0 | 121 | 0 | 0 | 0 | 121 | nan | nan | 0 | 0 |
| chb17c_06.edf | 900 | 0 | 133 | 0 | 133 | 0 | 2.328e-10 | 0 | 133 | nan | nan | 0 | 0 |
| chb17c_07.edf | 900 | 0 | 124 | 0 | 124 | 0 | 5.821e-11 | 0 | 124 | nan | nan | 0 | 0 |
| chb17c_08.edf | 900 | 0 | 136 | 0 | 136 | 0 | 1.49e-08 | 0 | 136 | nan | nan | 0 | 0 |
| chb17c_13.edf | 900 | 0 | 136 | 0 | 136 | 0 | 5.96e-08 | 0 | 136 | nan | nan | 0 | 0 |

## Conditioning (raw x (1 + 2**-40); record filter replicated bit-equal first)

| file | group | windows | raw_sd_max_V_median | filtered_absmax_V_median | replica_filter_bit_equal | recomputed_vs_build_f7_max | recomputed_vs_build_adj_entries | scaled_f7_median | scaled_f7_max | scaled_f7_windows_with_flip | scaled_bp5_median | scaled_bp5_max | scaled_adj_windows_differing | signal_loss_rule_recomputed_equal |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| chb17a_03.edf | other | 900 | 4.873e-05 | 0.0002109 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 2.98e-07 | 49 | True |
| chb17a_04.edf | other | 900 | 4.391e-05 | 0.0001764 | True | 0 | 0 | 0 | 1.192e-07 | 0 | 0 | 0 | 50 | True |
| chb17a_05.edf | other | 900 | 6.897e-05 | 0.0002596 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 1.192e-07 | 43 | True |
| chb17a_06.edf | other | 900 | 6.013e-05 | 0.0001421 | True | 0 | 0 | 0 | 9.537e-07 | 0 | 0 | 3.576e-07 | 41 | True |
| chb17a_08.edf | other | 900 | 8.708e-05 | 0.0003748 | True | 0 | 0 | 0 | 2.98e-08 | 0 | 0 | 0 | 47 | True |
| chb17b_57.edf | other | 900 | 7.341e-05 | 0.0002944 | True | 0 | 0 | 0 | 1.192e-07 | 0 | 0 | 0 | 54 | True |
| chb17b_58.edf | other | 900 | 5.985e-05 | 0.0002581 | True | 0 | 0 | 0 | 4.657e-10 | 0 | 0 | 0 | 50 | True |
| chb17b_59.edf | other | 900 | 7.052e-05 | 0.0002956 | True | 0 | 0 | 0 | 7.451e-09 | 0 | 0 | 0 | 59 | True |
| chb17b_60.edf | other | 900 | 7.312e-05 | 0.0002807 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 2.384e-07 | 45 | True |
| chb17b_63.edf | other | 906 | 7.175e-05 | 0.0003503 | True | 0 | 0 | 0 | 2.98e-08 | 0 | 0 | 0 | 59 | True |
| chb17b_67.edf | other | 900 | 3.64e-05 | 0.0001412 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 3.576e-07 | 60 | True |
| chb17b_68.edf | other | 900 | 9.164e-05 | 0.0003967 | True | 0 | 0 | 0 | 1.192e-07 | 0 | 0 | 5.96e-08 | 58 | True |
| chb17b_69.edf | other | 366 | 7.957e-05 | 0.0003828 | True | 0 | 0 | 0 | 5.96e-08 | 0 | 0 | 0 | 24 | True |
| chb17b_69.edf | signal_loss | 534 | 5.294e-23 | 4.805e-22 | True | 0 | 0 | 28.65 | 28.65 | 526 | 2.969 | 2.969 | 529 | True |
| chb17c_02.edf | other | 900 | 5.311e-05 | 0.000146 | True | 0 | 0 | 0 | 2.98e-08 | 0 | 0 | 0 | 52 | True |
| chb17c_03.edf | other | 900 | 4.214e-05 | 0.0001143 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 1.192e-07 | 44 | True |
| chb17c_04.edf | other | 900 | 3.567e-05 | 0.0001322 | True | 0 | 0 | 0 | 9.537e-07 | 0 | 0 | 3.576e-07 | 54 | True |
| chb17c_05.edf | other | 900 | 2.943e-05 | 0.0001212 | True | 0 | 0 | 0 | 4.768e-07 | 0 | 0 | 2.086e-07 | 49 | True |
| chb17c_06.edf | other | 900 | 3.111e-05 | 0.0001297 | True | 0 | 0 | 0 | 2.384e-07 | 0 | 0 | 0 | 57 | True |
| chb17c_07.edf | other | 900 | 3.218e-05 | 0.0001211 | True | 0 | 0 | 0 | 2.384e-07 | 0 | 0 | 1.192e-07 | 60 | True |
| chb17c_08.edf | other | 900 | 5.838e-05 | 0.0001649 | True | 0 | 0 | 0 | 9.537e-07 | 0 | 0 | 2.384e-07 | 49 | True |
| chb17c_13.edf | other | 900 | 0.0001025 | 0.0005141 | True | 0 | 0 | 0 | 2.384e-07 | 0 | 0 | 2.384e-07 | 59 | True |

## G-feat blocks

```
{
 "all": {
  "n_windows": 18906,
  "f7_max_abs": Infinity,
  "f7_finite_mask_diff": 1,
  "f7_windows_over_tol": 528,
  "bp5_max_abs": 3.8435423374176025,
  "bp5_finite_mask_diff": 0,
  "bp5_windows_over_tol": 527,
  "zgamma_raw_max_abs": 0.005245152860879898,
  "zgamma_raw_finite_mask_diff": 0,
  "adj_frac_differing": 0.009168002058266171,
  "adj_windows_differing": 3226,
  "status": "FAIL"
 },
 "chain": {
  "n_windows": 18372,
  "f7_max_abs": 9.5367431640625e-07,
  "f7_finite_mask_diff": 0,
  "f7_windows_over_tol": 0,
  "bp5_max_abs": 3.5762786865234375e-07,
  "bp5_finite_mask_diff": 0,
  "bp5_windows_over_tol": 0,
  "zgamma_raw_max_abs": 2.9802322387695312e-08,
  "zgamma_raw_finite_mask_diff": 0,
  "adj_frac_differing": 0.000453084806992928,
  "adj_windows_differing": 2697,
  "status": "PASS"
 },
 "signal_loss": {
  "n_windows": 534,
  "f7_max_abs": Infinity,
  "f7_finite_mask_diff": 1,
  "f7_windows_over_tol": 528,
  "bp5_max_abs": 3.8435423374176025,
  "bp5_finite_mask_diff": 0,
  "bp5_windows_over_tol": 527,
  "zgamma_raw_max_abs": 0.005245152860879898,
  "zgamma_raw_finite_mask_diff": 0,
  "adj_frac_differing": 0.3090003236694872,
  "adj_windows_differing": 529,
  "status": "FAIL"
 }
}
```

## Earlier .npz scan (24 cases)

| case | windows | signal_loss | files_with_signal_loss | f7_nonfinite_cells_in_sl | f7_nonfinite_cells_outside_sl | bp5_nonfinite_cells_in_sl | bp5_nonfinite_cells_outside_sl | adj_nonfinite_cells_in_sl | adj_nonfinite_cells_outside_sl | zgamma_raw_nonfinite_cells_in_sl | zgamma_raw_nonfinite_cells_outside_sl |
|---|---|---|---|---|---|---|---|---|---|---|---|
| chb01 | 36496 | 1 | chb01_42.edf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb02 | 31739 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb03 | 34201 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb04 | 140453 | 2 | chb04_12.edf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb05 | 35102 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb06 | 60060 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb07 | 60345 | 4 | chb07_19.edf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb08 | 18005 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb09 | 61079 | 3 | chb09_14.edf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb10 | 45020 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb11 | 27713 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb12 | 18617 | 1 | chb12_08.edf | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb13 | 29700 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb14 | 23400 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb15 | 36008 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb16 | 17100 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb17 | 18906 | 534 | chb17b_69.edf | 1 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb18 | 32070 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb19 | 26936 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb20 | 24839 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb21 | 28646 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb22 | 27902 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb23 | 23900 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | 0 | 0 |
| chb24 | 19166 | 0 |  | 0 | 0 | 0 | 0 | 0 | 0 | nan | nan |
