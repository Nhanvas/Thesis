# E16 -- per-recording baseline readout, arms ['e', 'f'], 4 seeds, 15 non-test subjects

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
S9base  0.612 (5, 0.01, 24.64) | 0.513 | 0.423 | val 0.867 | 0.735 | 0.742 @ 25.7 | 0.617, 0.628, 0.564, 0.606 | 1.0/3
E16e    0.628 (3, 0.005, 22.33) | 0.614 | 0.487 | val 0.867 | 0.783 | 0.766 @ 22.2 | 0.649, 0.638, 0.596, 0.638 | 1.2/3
E16f    0.559 (3, 0.005, 19.59) | 0.519 | 0.420 | val 0.867 | 0.695 | 0.706 @ 20.1 | 0.553, 0.585, 0.564, 0.553 | 1.0/3
```

## Mechanism (median over subjects of seed means)

```
E16e    seizure z 4.62  flagged z 0.05
E16f    seizure z 4.47  flagged z 0.08
S9base  seizure z 4.72  flagged z 0.00
```

## Diagnostics (median over subjects of seed means)

```
S9base  drift_iqr_over_mad 0.851  tail_share_top_quartile_files 0.845  top_files_with_seizure 0.083  flag_share_top_files 0.459  flag_share_other_files 0.459
```

- E16e: G1 FAIL G2 pass G3 pass G4 pass G5 pass M pass (subjects 11/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 4.50|7.00, chb02 3.00|3.00, chb04 2.75|2.50, chb05 5.00|5.00, chb07 3.00|3.00, chb08 4.75|5.00, chb09 4.00|4.00, chb10 7.00|7.00, chb11 2.50|3.00, chb12 5.75|7.50, chb19 3.00|3.00, chb20 4.00|1.50, chb21 0.25|0.00, chb22 3.00|3.00, chb23 6.50|3.00

- E16f: G1 FAIL G2 FAIL G3 FAIL G4 pass G5 pass M pass (subjects 10/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 3.50|7.00, chb02 3.00|3.00, chb04 2.75|2.50, chb05 5.00|5.00, chb07 3.00|3.00, chb08 4.25|5.00, chb09 4.00|4.00, chb10 6.75|7.00, chb11 2.75|3.00, chb12 5.25|7.50, chb19 3.00|3.00, chb20 3.00|1.50, chb21 0.00|0.00, chb22 3.00|3.00, chb23 3.25|3.00

**Candidate C after this run: S9base**

Elapsed 211 s.