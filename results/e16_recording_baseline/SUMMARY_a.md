# E16 -- per-recording baseline readout, arms ['a'], 4 seeds, 15 non-test subjects

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
S9base  0.612 (5, 0.01, 24.64) | 0.513 | 0.423 | val 0.867 | 0.735 | 0.742 @ 25.7 | 0.617, 0.628, 0.564, 0.606 | 1.0/3
E16a    0.191 (5, 0.02, 24.29) | 0.117 | 0.077 | val 0.217 | 0.235 | 0.244 @ 28.0 | 0.170, 0.191, 0.181, 0.191 | 0.0/3
```

## Mechanism (median over subjects of seed means)

```
E16a    seizure z 1.62  flagged z -0.14
S9base  seizure z 4.72  flagged z 0.00
```

## Diagnostics (median over subjects of seed means)

```
E16a    fit_noise_std_in_over_out 0.617  self_scoring_dz -0.920
S9base  drift_iqr_over_mad 0.851  tail_share_top_quartile_files 0.845
```

- E16a: G1 FAIL G2 FAIL G3 FAIL G4 FAIL G5 FAIL M FAIL (subjects 1/15) -> **NOT adopted**
  per subject 4-seed-mean TP (arm | S9 base): chb01 0.25|7.00, chb02 1.00|3.00, chb04 1.00|2.50, chb05 2.75|5.00, chb07 0.00|3.00, chb08 4.00|5.00, chb09 0.00|4.00, chb10 2.50|7.00, chb11 1.00|3.00, chb12 2.00|7.50, chb19 1.50|3.00, chb20 0.00|1.50, chb21 1.25|0.00, chb22 0.75|3.00, chb23 0.00|3.00

**Candidate C after this run: S9base** -- arm a not adopted: run arms b c d (record 6.3)

Elapsed 236 s.