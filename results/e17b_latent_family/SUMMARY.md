# E17b -- latent-family rank ensemble {S6e, S9e, S12e, Smean_e} vs C (E16e), fine grid, 4 seeds

Reproduction of E21 C by S9e: 0.681 (5, 0.0075, 24.25) OK

Best <= 25 | <= 15 | <= 10 | val (gate) (val at cell) | no-chb12 | subject-mean @ FP/day | per seed | short

```
C        0.681 (5, 0.0075, 24.25) | 0.614 | 0.561 | val 0.900 (at cell 0.883) | 0.846 | 0.821 @ 24.1 | 0.691, 0.691, 0.660, 0.681 | 1.5/3
S6e      0.665 (5, 0.0075, 24.84) | 0.612 | 0.561 | val 0.867 (at cell 0.850) | 0.835 | 0.810 @ 24.6 | 0.681, 0.649, 0.649, 0.670 | 1.5/3
S12e     0.686 (5, 0.0075, 23.95) | 0.620 | 0.588 | val 0.950 (at cell 0.917) | 0.853 | 0.828 @ 24.1 | 0.691, 0.691, 0.670, 0.713 | 1.5/3
Smean_e  0.686 (5, 0.0075, 23.37) | 0.614 | 0.574 | val 0.917 (at cell 0.917) | 0.849 | 0.826 @ 23.3 | 0.691, 0.691, 0.670, 0.702 | 1.2/3
E17b     0.668 (5, 0.005, 19.98) | 0.622 | 0.548 | val 0.983 (at cell 0.967) | 0.853 | 0.828 @ 19.5 | 0.681, 0.660, 0.660, 0.670 | 2.0/3
```

Flagged share in the top-2 % non-ictal tail (median over subjects): C 0.889, E17b 0.834

- pooled 0.668 vs floor 0.661 -> pass; subject-mean 0.828 vs 0.801 -> pass; validation 0.983 vs 0.833 -> pass

**non-inferior: final scalar = E17b (latent family), cell (5, 0.005, 19.98)**

Elapsed 441 s.