# RB1b -- why chb12's statistics changed (descriptive)

versions {'python': '3.11.9', 'numpy': '2.4.4', 'scipy': '1.17.1', 'pandas': '3.0.3', 'mne': '1.12.1'}; runtime 201.7 s

| gate | status |
|---|---|
| G-in | PASS |
| G-stats | PASS |
| G-clip | PASS |
| G-flags | PASS |

sampled windows: {'A': 1319, 'B': 1349, 'B_added_files': 30, 'B_chb12_27_before_first_seizure': 23, 'B_with_clipped': 36}

| scenario | kind | windows | median change vs A | max change vs A |
|---|---|---|---|---|
| A: 21 earlier files (R0) | SD (record statistic) | 1319 | +0.00% | +0.00% |
| B: 24 files (RB1) | SD (record statistic) | 1349 | +10.14% | +24.60% |
| B: windows of the 21 earlier files only (phase shifted) | SD (record statistic) | 1319 | +0.00% | +0.00% |
| B: windows of the 3 added files only | SD (record statistic) | 30 | +225.26% | +408.34% |
| B without windows holding a clipped sample | SD (record statistic) | 1313 | -2.36% | +0.92% |
| B without chb12_27 before its first seizure | SD (record statistic) | 1326 | -0.16% | -0.10% |
| B without both | SD (record statistic) | 1304 | -2.87% | -0.03% |
| B: 24 files (RB1) | IQR / 1.349 | 1349 | +0.20% | +0.78% |
| B: 24 files (RB1) | MAD x 1.4826 | 1349 | +0.20% | +0.77% |

share of B's total squared deviation (median over the 18 channels): added files 19.4% (of the windows 2.2%), chb12_27 before its first seizure 19.2% (windows 1.7%), windows with clipped samples 24.1% (windows 2.7%)

windows unflagged with B: {'windows': 707, 'by_file': {'chb12_06.edf': 39, 'chb12_08.edf': 25, 'chb12_09.edf': 40, 'chb12_11.edf': 29, 'chb12_19.edf': 43, 'chb12_20.edf': 41, 'chb12_21.edf': 52, 'chb12_23.edf': 8, 'chb12_24.edf': 40, 'chb12_27.edf': 1, 'chb12_32.edf': 40, 'chb12_33.edf': 12, 'chb12_34.edf': 20, 'chb12_35.edf': 51, 'chb12_36.edf': 10, 'chb12_37.edf': 53, 'chb12_38.edf': 63, 'chb12_39.edf': 23, 'chb12_40.edf': 48, 'chb12_41.edf': 58, 'chb12_42.edf': 11}, 'max_peak_over_thr_A_median': 1.0569981668533506}; flagged only with B: 0
