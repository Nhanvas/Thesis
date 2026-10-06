# E14 -- spatial-recruitment readout (k-th largest per-channel latent anomaly), 15 non-test

Reproduction of E8 frozen cell: E 0.489 @ 19.78 (E8: 0.489 @ 19.78)

## Best cell at FA/day <= 25 | <= 15 | <= 10 | validation-only <= 25 | mechanism (median over subjects)

```
E      0.489 (15, 0.02, 19.78) | 0.378 | 0.277 | val 0.733 | tail flagged 0.96 AUC sz-flag 0.914  (reference)
L      0.553 (3, 0.005, 23.78) | 0.511 | 0.426 | val 0.867 | tail flagged 0.87 AUC sz-flag 0.966  (reference)
S9     0.622 (5, 0.01, 24.62) | 0.521 | 0.426 | val 0.867 | tail flagged 0.95 AUC sz-flag 0.968  <- PRIMARY
S1     0.457 (15, 0.01, 13.21) | 0.457 | 0.330 | val 0.767 | tail flagged 0.88 AUC sz-flag 0.951  (characterisation)
S3     0.537 (3, 0.005, 21.06) | 0.484 | 0.367 | val 0.800 | tail flagged 0.92 AUC sz-flag 0.963  (characterisation)
S6     0.543 (15, 0.02, 20.97) | 0.495 | 0.410 | val 0.867 | tail flagged 0.94 AUC sz-flag 0.967  (characterisation)
S12    0.617 (5, 0.01, 23.95) | 0.516 | 0.436 | val 0.867 | tail flagged 0.95 AUC sz-flag 0.973  (characterisation)
Smean  0.601 (5, 0.01, 23.76) | 0.511 | 0.431 | val 0.867 | tail flagged 0.95 AUC sz-flag 0.972  (characterisation)
```

- G1 0.622 vs 0.589 -> pass
- G2 validation-only 0.867 vs 0.733 -> pass
- G3 subjects TP(S9) >= TP(E): 12/15 -> pass
- mechanism: tail flagged share S9 0.95 vs L (E12) 0.87 -> NOT lower

## Official SzCORE aggregation (mean over subjects)

```
E (15, 0.02): sens 0.651 prec 0.099 F1 0.164 FP/day 20.8
S9 (5, 0.01): sens 0.747 prec 0.122 F1 0.187 FP/day 25.4
```

## Per subject, seed-mean TP (S9 at its cell | E frozen) / n_ref

```
chb01   7.0 |  4.5 / 7
chb02   3.0 |  3.0 / 3
chb04   2.5 |  0.0 / 4
chb05   5.0 |  5.0 / 5
chb07   3.0 |  3.0 / 3
chb08   5.0 |  5.0 / 5
chb09   4.0 |  2.5 / 4
chb10   7.0 |  4.0 / 7
chb11   3.0 |  4.0 / 5
chb12   8.0 |  1.0 / 26
chb19   3.0 |  3.0 / 3
chb20   2.0 |  3.5 / 8
chb21   0.0 |  0.0 / 4
chb22   3.0 |  3.0 / 3
chb23   3.0 |  4.5 / 7
```

Short seizures (< 20 s) detected by S9: 1.0 of 3

**ADOPTED** -> FROZEN for one disclosed test look: v2 clean, S9, D1 smooth 5, top 0.01

Elapsed 252 s.