# E21 -- finer top-p grid [0.05, 0.03, 0.02, 0.015, 0.01, 0.0075, 0.005, 0.002, 0.001], gates unchanged, 4 seeds, 15 non-test

Ledger note: grid changed after seeing E16e and Eb_h.

## Stage 1 (reference S9 base)

Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
S9base  0.612 (5, 0.01, 24.64) | 0.513 | 0.489 | val 0.867 | 0.735 | 0.742 @ 25.7 | 0.617, 0.628, 0.564, 0.606 | 1.0/3
E16e    0.681 (5, 0.0075, 24.25) | 0.614 | 0.561 | val 0.900 | 0.846 | 0.821 @ 24.1 | 0.691, 0.691, 0.660, 0.681 | 1.5/3
E16b    0.596 (5, 0.0075, 23.27) | 0.548 | 0.492 | val 0.833 | 0.757 | 0.755 @ 23.7 | 0.617, 0.606, 0.574, 0.585 | 1.2/3
E15tta  0.617 (5, 0.01, 24.9) | 0.519 | 0.497 | val 0.867 | 0.750 | 0.749 @ 26.3 | 0.617, 0.638, 0.564, 0.617 | 1.0/3
```
- E16e: G1 pass G2 pass G3 pass G4 pass G5 pass M pass (subjects 13/15) -> **ADOPTED**
- E16b: G1 FAIL G2 pass G3 pass G4 FAIL G5 pass M FAIL (subjects 11/15) -> **NOT adopted**
- E15tta: G1 FAIL G2 pass G3 pass G4 pass G5 pass M pass (subjects 13/15) -> **NOT adopted**

**C' = E16e**

## Stage 2 (rank ensembles with C' = E16e)

```
C       0.681 (5, 0.0075, 24.25) | 0.614 | 0.561 | val 0.900 | 0.846 | 0.821 @ 24.1 | 0.691, 0.691, 0.660, 0.681 | 1.5/3
Ea      0.548 (15, 0.015, 20.8) | 0.444 | 0.351 | val 0.733 | 0.732 | 0.700 @ 21.0 | 0.543, 0.543, 0.553, 0.553 | 1.0/3   C+recon+gamma
Eb      0.636 (15, 0.015, 22.29) | 0.545 | 0.471 | val 0.933 | 0.853 | 0.815 @ 21.8 | 0.628, 0.638, 0.638, 0.638 | 1.0/3   C+L+gamma
Ec      0.628 (15, 0.015, 24.76) | 0.580 | 0.527 | val 0.883 | 0.798 | 0.776 @ 24.8 | 0.628, 0.606, 0.638, 0.628 | 0.8/3   C+L
```
- Ea: pooled FAIL, subject-mean FAIL, validation FAIL (val 0.733 vs floor 0.833)
- Eb: pooled FAIL, subject-mean pass, validation pass (val 0.933 vs floor 0.833)
- Ec: pooled FAIL, subject-mean FAIL, validation pass (val 0.883 vs floor 0.833)

**Final scalar after E21: C with C' = E16e, D1 cell (5, 0.0075, 24.25)**

## Diagnostics (median over subjects of seed means)

```
L       drift IQR/MAD 0.685 | final-tail share in its top files 0.180 | flag top/other 0.474/0.465 | top files with seizure 0.083 vs all files 0.158
S9base  drift IQR/MAD 0.851 | final-tail share in its top files 0.180 | flag top/other 0.459/0.459 | top files with seizure 0.083 vs all files 0.158
gamma   drift IQR/MAD 1.540 | final-tail share in its top files 0.575 | flag top/other 0.660/0.395 | top files with seizure 0.125 vs all files 0.158
recon   drift IQR/MAD 0.744 | final-tail share in its top files 0.187 | flag top/other 0.500/0.455 | top files with seizure 0.031 vs all files 0.158
```

Per subject (S9base, seed mean): flag share top/other, files with seizure top/all

```
chb01  0.511/0.543   0.455/0.167  files 42
chb02  0.352/0.459   0.083/0.083  files 36
chb04  0.403/0.266   0.091/0.071  files 42
chb05  0.514/0.398   0.000/0.128  files 39
chb07  0.459/0.538   0.000/0.158  files 19
chb08  0.415/0.599   0.000/0.250  files 20
chb09  0.387/0.362   0.200/0.158  files 19
chb10  0.091/0.358   0.071/0.280  files 25
chb11  0.539/0.432   0.094/0.097  files 31
chb12  0.507/0.418   0.833/0.476  files 21
chb19  0.398/0.539   0.250/0.100  files 30
chb20  0.474/0.449   0.500/0.207  files 29
chb21  0.638/0.580   0.000/0.125  files 32
chb22  0.508/0.602   0.000/0.097  files 31
chb23  0.441/0.579   0.000/0.333  files 9
```

Elapsed 317 s.