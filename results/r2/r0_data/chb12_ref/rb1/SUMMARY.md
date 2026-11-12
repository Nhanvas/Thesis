# RB1_DATA -- summary

mode: **exact** (versions vs R0_CHB: equal)

| gate | status | summary |
|---|---|---|
| G-code | PASS | 10 files byte-equal to R0's, imports from the pinned clone |
| G-raw | PASS | 24 EDFs + summary, sha256 = PhysioNet |
| G-R0 | PASS | 48 R0 dataset files = pinned R1_SMOKE hashes |
| Job A = R0 (wrapper + 21 bipolar files) | PASS | mode exact: stats and every array equal to R0's chb12; skipped_files [] vs the three referential files (expected) |
| Job B (wrapper + 24 files) | PASS | 24 files, seizures {'chb12_27.edf': 6, 'chb12_28.edf': 1, 'chb12_29.edf': 6}, labels = independent recomputation, 21 common files = Job A, counts consistent; n_ref 27 -> 40 |
| G-clip | PASS | per electrode, per derivation and per file = RB0b's tables; 8 of 13 seizures and 14 clean windows hold clipped samples |
| G-copy | PASS | 46 files copied, sha256 = pin |

See `diff_chb12.md` for the data change.

Clipping (descriptive): 8 of 13 seizures and 14 clean (training) windows hold clipped samples; by class: {"5-SD flagged": {"windows": 177, "windows_any_clipped": 144}, "buffer (non-ictal)": {"windows": 2277, "windows_any_clipped": 783}, "clean (training)": {"windows": 123, "windows_any_clipped": 14}, "ictal": {"windows": 129, "windows_any_clipped": 46}}
