# E12 -- readout composition (latent-only L vs frozen ensemble E), 15 non-test subjects

Reproduction of E8 frozen cell: E 0.489 @ 19.78 FA/day vs (0.489, 19.78) -> OK

## Best cell at FA/day <= 25 (pooled, seed mean) | <= 15 | <= 10 | validation-only <= 25

```
E   0.489 (15, 0.02, 19.78) | 0.378 | 0.277 | val 0.733   (reference)
L   0.553 (3, 0.005, 23.78) | 0.511 | 0.426 | val 0.867   <- PRIMARY
RL  0.452 (15, 0.02, 23.49) | 0.383 | 0.298 | val 0.600   (characterisation)
LG  0.500 (15, 0.02, 21.46) | 0.415 | 0.340 | val 0.700   (characterisation)
L2  0.553 (3, 0.005, 22.03) | 0.521 | 0.426 | val 0.867   (characterisation)
```

- G1 0.553 vs E 0.489 + 0.10 -> FAIL
- G2 validation-only 0.867 vs 0.733 -> pass
- G3 subjects with TP(L) >= TP(E): 9/15 -> pass
- mechanism: flagged share in the top-2 % non-ictal tail, median over subjects and seeds: E 0.96 -> L 0.87

## Official SzCORE aggregation (mean over subjects) beside pooled

```
E cell (15, 0.02): subject-mean sens 0.651 prec 0.099 F1 0.164 FP/day 20.8 | pooled prec 0.077 F1 0.133
L cell (3, 0.005): subject-mean sens 0.676 prec 0.122 F1 0.180 FP/day 23.8 | pooled prec 0.072 F1 0.128
```

## Per subject, seed-mean TP (L at its cell | E frozen) / n_ref

```
chb01   4.0 |  4.5 / 7
chb02   2.0 |  3.0 / 3
chb04   2.0 |  0.0 / 4
chb05   5.0 |  5.0 / 5
chb07   3.0 |  3.0 / 3
chb08   4.0 |  5.0 / 5
chb09   4.0 |  2.5 / 4
chb10   6.5 |  4.0 / 7
chb11   3.0 |  4.0 / 5
chb12   6.5 |  1.0 / 26
chb19   3.0 |  3.0 / 3
chb20   2.0 |  3.5 / 8
chb21   0.0 |  0.0 / 4
chb22   3.0 |  3.0 / 3
chb23   4.0 |  4.5 / 7
```

Short seizures (< 20 s) detected by L at its cell: 0.0 of 3

**NOT adopted**

Elapsed 130 s.