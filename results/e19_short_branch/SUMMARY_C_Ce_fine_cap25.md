# E19b -- short branch on C_Ce_fine_cap25, fine grid, total cap 25, 4 seeds, 15 non-test

Main-only reference (fine grid, <= 25): 0.681 @ (5, 0.0075, 24.25) | val (gate definition) 0.900 | val at the cell 0.883 | subject-mean 0.821 @ 24.1

Best eligible union:
```
main cell 5/0.0075  p_s 0.001  sens 0.681  FA/day 24.25 (main 24.25, added 0.00)
```
Union 0.681 vs main-only 0.681 -> **NOT adopted** (difference +0.000 = +0.0 seizures of 94)

## The 3 short seizures of the selection set (per seed)

```
subject         seed  file  onset_s  dur_s  peak_pct  main_caught          p0.001          p0.002          p0.005
  chb02 clean_seed42    19     3368     12  0.983679         True below threshold below threshold below threshold
  chb02  clean_seed1    19     3368     12  0.988531         True below threshold below threshold below threshold
  chb02  clean_seed2    19     3368     12  0.971549         True below threshold below threshold below threshold
  chb02  clean_seed3    19     3368     12  0.992690         True below threshold below threshold below threshold
  chb12 clean_seed42     1     1424     16  0.811677        False below threshold below threshold below threshold
  chb12  clean_seed1     1     1424     16  0.823656        False below threshold below threshold below threshold
  chb12  clean_seed2     1     1424     16  0.908148        False below threshold below threshold below threshold
  chb12  clean_seed3     1     1424     16  0.809421        False below threshold below threshold below threshold
  chb21 clean_seed42    20     2552     16  0.995008         True below threshold below threshold            kept
  chb21  clean_seed1    20     2552     16  0.983872        False below threshold below threshold below threshold
  chb21  clean_seed2    20     2552     16  0.992844         True below threshold below threshold below threshold
  chb21  clean_seed3    20     2552     16  0.982476        False below threshold below threshold below threshold
```

Elapsed 124 s.