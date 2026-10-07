# E21b -- rank ensemble C(E16e) + L + gamma_dt vs C alone, fine grid, 4 seeds, 15 non-test

Reproduction of E21 C: 0.681 (5, 0.0075, 24.25) OK

Best <= 25 | <= 15 | <= 10 | val (gate) (val at cell) | no-chb12 | subject-mean @ FP/day | per seed | short

```
C       0.681 (5, 0.0075, 24.25) | 0.614 | 0.561 | val 0.900 (at cell 0.883) | 0.846 | 0.821 @ 24.1 | 0.691, 0.691, 0.660, 0.681 | 1.5/3
Eb      0.636 (15, 0.015, 22.29) | 0.545 | 0.471 | val 0.933 (at cell 0.933) | 0.853 | 0.815 @ 21.8 | 0.628, 0.638, 0.638, 0.638 | 1.0/3
E21b    0.609 (15, 0.01, 16.98) | 0.559 | 0.492 | val 0.867 (at cell 0.867) | 0.812 | 0.768 @ 15.9 | 0.606, 0.606, 0.628, 0.596 | 1.0/3
```

Mechanism (median over subjects): share of the top-2 % non-ictal tail in gamma's top-quartile files | flagged share in that tail

```
C     0.400 | 0.889
E21b  0.387 | 0.900
Eb    0.575 | 0.945
```

- pooled 0.609 vs floor 0.661 -> FAIL; subject-mean 0.768 vs 0.801 -> FAIL; validation 0.867 vs 0.833 -> pass

**inferior: final scalar = C (E16e), cell (5, 0.0075, 24.25)**

Elapsed 124 s.