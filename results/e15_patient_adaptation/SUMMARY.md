# E15 -- patient-specific adaptation of v2 (2,000 steps) + S9, 15 non-test subjects

## Pooled seed mean: best <= 25 | <= 15 | <= 10 | validation-only | without chb12 at the cell | subject-mean sens/FP-day at the cell

```
S9base   0.622 (5, 0.01, 24.62) | 0.521 | 0.426 | val 0.867 | no-chb12 0.743 | subj 0.747 @ 25.4 | per seed 0.617, 0.628  (reference)
S9a500   0.622 (5, 0.01, 24.33) | 0.521 | 0.420 | val 0.867 | no-chb12 0.743 | subj 0.746 @ 25.6 | per seed 0.617, 0.574  (characterisation)
S9a1000  0.617 (5, 0.01, 24.47) | 0.527 | 0.420 | val 0.867 | no-chb12 0.743 | subj 0.745 @ 25.8 | per seed 0.617, 0.574  (characterisation)
S9a2000  0.628 (5, 0.01, 24.49) | 0.527 | 0.420 | val 0.867 | no-chb12 0.757 | subj 0.758 @ 26.0 | per seed 0.617, 0.638  <- PRIMARY
```

## Mechanism (median over subjects of seed means)

```
kind      seizure z  flagged z  tail flagged  AUC sz-flag
S9base         4.90      -0.00          0.95  0.969
S9a500         5.09       0.05          0.96  0.971
S9a1000        5.16       0.07          0.96  0.972
S9a2000        5.32       0.11          0.96  0.973
```

- G1 0.628 vs S9 0.622 + 0.05; per seed [0.617, 0.638] vs [0.617, 0.628] -> FAIL
- G2 subject-mean 0.758 vs 0.747 -> pass
- G3 without chb12 0.757 vs 0.743 -> pass
- G4 validation-only 0.867 vs 0.867 -> pass
- G5 subjects TP >= S9: 13/15 -> pass
- M  seizure z 5.32 vs base 4.90 - 10 % -> pass

## Per subject, seed-mean TP (adapted at its cell | S9 base at its cell) / n_ref

```
chb01   7.0 |  7.0 / 7
chb02   3.0 |  3.0 / 3
chb04   3.0 |  2.5 / 4
chb05   5.0 |  5.0 / 5
chb07   3.0 |  3.0 / 3
chb08   5.0 |  5.0 / 5
chb09   4.0 |  4.0 / 4
chb10   7.0 |  7.0 / 7
chb11   3.0 |  3.0 / 5
chb12   7.5 |  8.0 / 26
chb19   3.0 |  3.0 / 3
chb20   3.0 |  2.0 / 8
chb21   0.0 |  0.0 / 4
chb22   3.0 |  3.0 / 3
chb23   2.5 |  3.0 / 7
```

## Analysis only: seizure windows inside the first 150 windows (10 min)

patients whose first 10 min contain a seizure: 0/15; files whose first 10 min contain a seizure: 10/425

**NOT adopted at this budget: candidate = S9 base**

Elapsed 68 s.