# RB0b — chb12_27-29 conversion and amplitude check

Gates: A inputs **PASS**, B conversion = SzCORE **PASS**; runtime 295.2 s; 24 files.

## B conversion vs SzCORE (max |diff| uV, whole file)

| file | labels equal | B1 reref | B2 standardize |
|---|---|---|---|
| chb12_27.edf | True | 9.66e-13 | 9.66e-13 |
| chb12_28.edf | True | 6.68e-13 | 6.68e-13 |
| chb12_29.edf | True | 6.71e-13 | 6.71e-13 |

## C clipping (share of 4 s windows with any clipped sample)

| file | windows | share |
|---|---|---|
| chb12_06.edf | 901 | 0.0255 |
| chb12_08.edf | 900 | 0.0033 |
| chb12_09.edf | 903 | 0.0011 |
| chb12_10.edf | 902 | 0.0011 |
| chb12_11.edf | 607 | 0.0000 |
| chb12_19.edf | 900 | 0.0078 |
| chb12_20.edf | 900 | 0.0022 |
| chb12_21.edf | 900 | 0.0078 |
| chb12_23.edf | 900 | 0.0067 |
| chb12_24.edf | 900 | 0.0178 |
| chb12_27.edf | 900 | 0.3156 |
| chb12_28.edf | 900 | 0.2722 |
| chb12_29.edf | 906 | 0.5055 |
| chb12_32.edf | 900 | 0.0333 |
| chb12_33.edf | 900 | 0.0189 |
| chb12_34.edf | 900 | 0.0189 |
| chb12_35.edf | 900 | 0.0011 |
| chb12_36.edf | 900 | 0.0311 |
| chb12_37.edf | 904 | 0.0177 |
| chb12_38.edf | 900 | 0.0133 |
| chb12_39.edf | 900 | 0.0644 |
| chb12_40.edf | 900 | 0.0167 |
| chb12_41.edf | 900 | 0.0022 |
| chb12_42.edf | 900 | 0.0522 |

## D position of the referential files among the 21 bipolar files (median window RMS)

| file | channels inside range | ratio to bipolar median (min / median / max) |
|---|---|---|
| chb12_27.edf | 17/18 | 0.94 / 1.08 / 1.30 |
| chb12_28.edf | 18/18 | 0.84 / 0.94 / 1.09 |
| chb12_29.edf | 16/18 | 0.86 / 0.98 / 1.33 |

## E narrow spectral peaks in a referential file only (>= 9 channels)

3 rows (`E_peaks_referential_only.csv`).
