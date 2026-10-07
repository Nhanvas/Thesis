# E16g arm h -- drift correction (Eb_h vs Eb), 4 seeds, 15 non-test

Reproduction of E17 Eb: 0.617 (E17 0.617) OK

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
Eb     0.617 (15, 0.02, 22.84) | 0.545 | 0.441 | val 0.800 | 0.824 | 0.791 @ 24.3 | 0.628, 0.606, 0.617, 0.617 | 1.0/3
Eb_h   0.598 (15, 0.01, 15.21) | 0.471 | 0.471 | val 0.867 | 0.801 | 0.775 @ 14.8 | 0.585, 0.606, 0.596, 0.606 | 1.0/3
```

```
Eb     seizure z 2.89  flagged z 0.55
Eb_h   seizure z 2.85  flagged z 0.57
```

- G1 FAIL G2 FAIL G3 FAIL G4 pass G5 pass M pass (subjects 11/15)
  per subject 4-seed-mean TP (Eb_h | Eb): chb01 5.75|5.00, chb02 3.00|3.00, chb04 3.00|2.75, chb05 5.00|5.00, chb07 3.00|3.00, chb08 5.00|5.00, chb09 4.00|4.00, chb10 6.00|6.00, chb11 4.00|5.00, chb12 1.75|2.00, chb19 3.00|3.00, chb20 3.50|4.25, chb21 0.00|0.00, chb22 3.00|3.00, chb23 6.25|7.00

**NOT adopted: candidate scalar = Eb**

Elapsed 105 s.