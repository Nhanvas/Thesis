# V9-FINAL Part C -- Siena gap decomposition, formally

CHB-MIT test: 76 seizures (8 patients), thesis system seed 42 after the localizer, actual sensitivity 0.500. Siena: 47 seizures (14 patients), actual sensitivity 0.702. Raw gap -0.202.

## Duration-bin reweighting (CHB-MIT-test per-bin rate, Siena's own bin mix)

```
   bin  test_tp  test_n  test_rate  siena_n  siena_weight
  0-20        7      24   0.291667        5      0.106383
 20-40        4      12   0.333333        6      0.127660
 40-80       16      27   0.592593       27      0.574468
80-inf       11      13   0.846154        9      0.191489
```

Reweighted sensitivity (test's own per-bin rate, Siena's duration mix): 0.576  [0.342, 0.898] (patient bootstrap, B=2000, 213 replicates dropped for undefined support)
Share of the test-vs-Siena gap explained by the duration mix alone: 0.376  [-1.880, 3.534]

## Amplitude-ratio-bin reweighting (quartiles of the pooled test+Siena distribution)

```
            bin  test_tp  test_n  test_rate  siena_n  siena_weight
 Q1 (0.51,1.11]        9      27   0.333333        4      0.085106
 Q2 (1.11,1.42]        7      22   0.318182        9      0.191489
 Q3 (1.42,2.23]       11      16   0.687500       14      0.297872
Q4 (2.23,54.54]       11      11   1.000000       20      0.425532
```

Reweighted sensitivity (test's own per-bin rate, Siena's amplitude-ratio mix): 0.720  [0.517, 0.883] (patient bootstrap, B=2000, 14 replicates dropped)
Share of the test-vs-Siena gap explained by the amplitude-ratio mix alone: 1.087  [-2.290, 4.787]

Elapsed 119s.