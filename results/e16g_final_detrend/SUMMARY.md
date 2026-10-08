# E16g -- drift correction of the final ensemble scalar (Eb_dt vs Eb), 4 seeds, 15 non-test

Reproduction of E17 Eb: 0.617 (E17 0.617) OK

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
Eb     0.617 (15, 0.02, 22.84) | 0.545 | 0.441 | val 0.800 | 0.824 | 0.791 @ 24.3 | 0.628, 0.606, 0.617, 0.617 | 1.0/3
Eb_dt  0.529 (15, 0.01, 20.65) | 0.441 | 0.359 | val 0.800 | 0.713 | 0.658 @ 18.9 | 0.532, 0.521, 0.521, 0.543 | 0.2/3
```

```
Eb     seizure z 2.89  flagged z 0.55
Eb_dt  seizure z 2.48  flagged z 0.21
```

- G1 FAIL G2 FAIL G3 FAIL G4 pass G5 FAIL M FAIL (subjects 8/15)
  per subject 4-seed-mean TP (Eb_dt | Eb): chb01 3.75|5.00, chb02 1.25|3.00, chb04 3.00|2.75, chb05 5.00|5.00, chb07 3.00|3.00, chb08 4.50|5.00, chb09 4.00|4.00, chb10 7.00|6.00, chb11 2.00|5.00, chb12 1.25|2.00, chb19 1.00|3.00, chb20 5.00|4.25, chb21 0.00|0.00, chb22 3.00|3.00, chb23 6.00|7.00

**NOT adopted: candidate scalar = Eb**

Elapsed 104 s.