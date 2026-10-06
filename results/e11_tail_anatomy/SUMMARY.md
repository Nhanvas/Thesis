# E11 -- tail anatomy by readout, 15 non-test subjects (cache only)

subjects 15; smoothing 15 windows; tail = top 2% of the smoothed ensemble; max |ER ensemble - plain mean| = 7.11e-15

## M2 tail owner (count of subjects) and tail composition (median over subjects)

```
V1            owner {'g': 13, 'r': 1, 'l': 1} | flagged share in tail 0.95 | tail mean z r/l/g 1.61/1.07/6.08 | seizure mean z r/l/g 0.55/0.61/3.29
clean_seed42  owner {'g': 12, 'r': 3} | flagged share in tail 0.95 | tail mean z r/l/g 1.90/1.59/6.20 | seizure mean z r/l/g 0.68/3.15/3.29
clean_seed1   owner {'g': 12, 'r': 2, 'l': 1} | flagged share in tail 0.96 | tail mean z r/l/g 1.90/1.50/6.29 | seizure mean z r/l/g 0.71/3.50/3.29
```

## M1 window AUROC (median over subjects): seizure vs flagged | seizure vs clean

```
V1            r 0.487|0.673  l 0.701|0.731  g 0.762|0.938  E 0.735|0.949
clean_seed42  r 0.527|0.697  l 0.966|0.989  lg 0.919|0.950  g 0.762|0.938  E 0.911|0.990  Eg 0.892|0.976
clean_seed1   r 0.534|0.712  l 0.966|0.985  lg 0.929|0.961  g 0.762|0.938  E 0.917|0.992  Eg 0.903|0.979
```

## M3 exceedance (median over seizures): share of same-length non-ictal blocks above the seizure peak, all blocks | blocks without a flagged window

```
V1            E 0.092|0.000  g 0.104|0.000  l 0.189|0.067  r 0.371|0.012
clean_seed42  E 0.039|0.000  Eg 0.047|0.000  g 0.104|0.000  l 0.053|0.001  lg 0.060|0.003  r 0.345|0.011
clean_seed1   E 0.037|0.000  Eg 0.046|0.000  g 0.104|0.000  l 0.045|0.000  lg 0.055|0.000  r 0.336|0.011
```

## Reading rules (fixed before the run)

- clean_seed42: owner in >= 8/15 -> g ({'g': 12, 'r': 3})
- clean_seed1: owner in >= 8/15 -> g ({'g': 12, 'r': 2, 'l': 1})

Elapsed 174 s.