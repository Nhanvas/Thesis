# E16 -- per-recording baseline readout, arms ['b', 'c', 'd'], 4 seeds, 15 non-test subjects

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
S9base  0.612 (5, 0.01, 24.64) | 0.513 | 0.423 | val 0.867 | 0.735 | 0.742 @ 25.7 | 0.617, 0.628, 0.564, 0.606 | 1.0/3
E16b    0.582 (3, 0.005, 22.51) | 0.548 | 0.444 | val 0.800 | 0.732 | 0.735 @ 22.7 | 0.617, 0.585, 0.574, 0.564 | 1.2/3
E16c    0.295 (5, 0.02, 22.27) | 0.226 | 0.122 | val 0.283 | 0.353 | 0.367 @ 26.4 | 0.287, 0.330, 0.287, 0.277 | 1.0/3
E16d    0.487 (5, 0.01, 18.23) | 0.372 | 0.372 | val 0.683 | 0.577 | 0.581 @ 20.4 | 0.489, 0.521, 0.479, 0.457 | 0.0/3
```

## Mechanism (median over subjects of seed means)

```
E16b    seizure z 4.08  flagged z 0.07
E16c    seizure z 1.93  flagged z -0.15
E16d    seizure z 3.70  flagged z -0.15
S9base  seizure z 4.72  flagged z 0.00
```

## Diagnostics (median over subjects of seed means)

```
E16c    fit_noise_std_in_over_out 0.748  self_scoring_dz -0.647
S9base  drift_iqr_over_mad 0.851  tail_share_top_quartile_files 0.845
```

- E16b: G1 FAIL G2 FAIL G3 FAIL G4 FAIL G5 pass M FAIL (subjects 10/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 4.00|7.00, chb02 3.00|3.00, chb04 3.00|2.50, chb05 5.00|5.00, chb07 3.00|3.00, chb08 4.25|5.00, chb09 4.00|4.00, chb10 6.50|7.00, chb11 2.25|3.00, chb12 5.00|7.50, chb19 3.00|3.00, chb20 3.00|1.50, chb21 0.75|0.00, chb22 3.00|3.00, chb23 5.00|3.00

- E16c: G1 FAIL G2 FAIL G3 FAIL G4 FAIL G5 FAIL M FAIL (subjects 2/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 0.75|7.00, chb02 2.00|3.00, chb04 1.00|2.50, chb05 4.00|5.00, chb07 0.50|3.00, chb08 4.00|5.00, chb09 0.00|4.00, chb10 4.00|7.00, chb11 0.25|3.00, chb12 3.75|7.50, chb19 2.00|3.00, chb20 1.75|1.50, chb21 2.25|0.00, chb22 1.50|3.00, chb23 0.00|3.00

- E16d: G1 FAIL G2 FAIL G3 FAIL G4 FAIL G5 FAIL M FAIL (subjects 4/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 5.50|7.00, chb02 2.00|3.00, chb04 3.00|2.50, chb05 4.75|5.00, chb07 3.00|3.00, chb08 5.00|5.00, chb09 0.25|4.00, chb10 5.00|7.00, chb11 1.75|3.00, chb12 6.50|7.50, chb19 2.25|3.00, chb20 1.25|1.50, chb21 1.00|0.00, chb22 2.00|3.00, chb23 2.50|3.00

**Candidate C after this run: S9base**

Elapsed 633 s.