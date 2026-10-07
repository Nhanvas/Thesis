# E17 -- rank ensemble to one scalar, C = S9base, 4 seeds, 15 non-test subjects

## Best <= 25 | <= 15 | <= 10 | val | no-chb12 | subject-mean sens @ FP/day | per seed | short

```
C     0.612 (5, 0.01, 24.64) | 0.513 | 0.423 | val 0.867 | 0.735 | 0.742 @ 25.7 | 0.617, 0.628, 0.564, 0.606 | 1.0/3   (reference C)
Ea    0.535 (15, 0.02, 22.16) | 0.481 | 0.378 | val 0.717 | 0.710 | 0.667 @ 23.3 | 0.543, 0.532, 0.543, 0.521 | 1.0/3   C+recon+gamma
Eb    0.617 (15, 0.02, 22.84) | 0.545 | 0.441 | val 0.800 | 0.824 | 0.791 @ 24.3 | 0.628, 0.606, 0.617, 0.617 | 1.0/3   C+L+gamma
Ec    0.572 (3, 0.005, 21.52) | 0.511 | 0.457 | val 0.867 | 0.699 | 0.696 @ 22.2 | 0.543, 0.596, 0.574, 0.596 | 0.0/3   C+L
```

## Components (median over subjects of seed means): AUROC seizure-vs-flagged | mean percentile in the combination's top-2 % non-ictal tail | in seizures

```
Ea    C      0.908 | 0.768 | 0.929
Ea    gamma  0.651 | 0.832 | 0.786
Ea    recon  0.445 | 0.767 | 0.593
Eb    C      0.908 | 0.835 | 0.929
Eb    L      0.858 | 0.787 | 0.872
Eb    gamma  0.651 | 0.832 | 0.786
Ec    C      0.908 | 0.904 | 0.929
Ec    L      0.858 | 0.864 | 0.872
```
- Ea: pooled FAIL, subject-mean FAIL, validation FAIL -> inferior
- Eb: pooled pass, subject-mean pass, validation pass -> non-inferior
- Ec: pooled FAIL, subject-mean FAIL, validation pass -> inferior

**Chosen ensemble: Eb (C+L+gamma)**

Elapsed 190 s.