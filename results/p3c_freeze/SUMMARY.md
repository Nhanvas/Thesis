# P3 freeze step -- L2f (budget never below 0.005) and the sensitivity-priority point, 15 non-test, 4 seeds

Reproduction: floor 0.0025 = p3_levers L2 and floor = cap = 0.005 = frozen detector, every subject and seed.

k = 4.0677 (p3_levers); sensitivity-priority floor t_s = 0.0075 (grid at smoothing 5: 0.705 @ 32.3 FA/day).

## Pooled sens @ FA/day (4-seed mean), subject-mean, validation, review fraction

```
frozen detector          0.668 @ 19.98 | subject-mean 0.828 @ 19.52 | val 0.967 @ 17.50 | no-chb12 0.853 | chb12 TP 4.75 | short 2.00/3 | seeds 0.681, 0.660, 0.660, 0.670 | review 0.0082
frozen cpd               0.662 @ 19.55 | subject-mean 0.822 @ 19.19 | val 0.933 @ 17.34 | no-chb12 0.846 | chb12 TP 4.75 | short 2.00/3 | seeds 0.670, 0.660, 0.649, 0.670 | review 0.0141
frozen hybrid            0.662 @ 19.73 | subject-mean 0.822 @ 19.33 | val 0.933 @ 17.40 | no-chb12 0.846 | chb12 TP 4.75 | short 2.00/3 | seeds 0.670, 0.660, 0.649, 0.670 | review 0.0109
L2 detector              0.657 @ 20.53 | subject-mean 0.814 @ 19.76 | val 0.983 @ 13.14 | no-chb12 0.838 | chb12 TP 4.75 | short 1.50/3 | seeds 0.670, 0.649, 0.660, 0.649 | review 0.0089
L2 cpd                   0.649 @ 20.02 | subject-mean 0.804 @ 19.29 | val 0.933 @ 13.09 | no-chb12 0.827 | chb12 TP 4.75 | short 1.50/3 | seeds 0.660, 0.649, 0.638, 0.649 | review 0.0146
L2 hybrid                0.654 @ 20.21 | subject-mean 0.811 @ 19.49 | val 0.967 @ 13.09 | no-chb12 0.835 | chb12 TP 4.75 | short 1.50/3 | seeds 0.660, 0.649, 0.660, 0.649 | review 0.0118
L2f detector             0.678 @ 23.81 | subject-mean 0.842 @ 23.70 | val 0.983 @ 18.53 | no-chb12 0.868 | chb12 TP 4.75 | short 2.00/3 | seeds 0.691, 0.670, 0.670, 0.681 | review 0.0097
L2f cpd                  0.670 @ 23.25 | subject-mean 0.832 @ 23.19 | val 0.933 @ 18.37 | no-chb12 0.857 | chb12 TP 4.75 | short 2.00/3 | seeds 0.681, 0.670, 0.649, 0.681 | review 0.0162
L2f hybrid               0.676 @ 23.48 | subject-mean 0.838 @ 23.43 | val 0.967 @ 18.42 | no-chb12 0.864 | chb12 TP 4.75 | short 2.00/3 | seeds 0.681, 0.670, 0.670, 0.681 | review 0.0130
S detector               0.705 @ 33.65 | subject-mean 0.862 @ 32.51 | val 1.000 @ 30.11 | no-chb12 0.893 | chb12 TP 5.50 | short 2.00/3 | seeds 0.702, 0.702, 0.691, 0.723 | review 0.0133
S cpd                    0.697 @ 32.73 | subject-mean 0.849 @ 31.66 | val 0.933 @ 29.52 | no-chb12 0.879 | chb12 TP 5.75 | short 2.00/3 | seeds 0.681, 0.702, 0.670, 0.734 | review 0.0219
S hybrid                 0.707 @ 33.09 | subject-mean 0.863 @ 32.08 | val 1.000 @ 29.68 | no-chb12 0.893 | chb12 TP 5.75 | short 2.00/3 | seeds 0.702, 0.702, 0.691, 0.734 | review 0.0178
```

## Per subject, detector (4-seed mean): TP | top-p

```
           TP                        top                       
budget     L2   L2f     S frozen      L2     L2f       S frozen
subject                                                        
chb01    7.00  7.00  7.00   7.00  0.0073  0.0073  0.0076  0.005
chb02    3.00  3.00  3.00   3.00  0.0061  0.0061  0.0075  0.005
chb04    3.00  3.00  3.00   3.00  0.0047  0.0051  0.0075  0.005
chb05    5.00  5.00  5.00   5.00  0.0044  0.0050  0.0075  0.005
chb07    3.00  3.00  3.00   3.00  0.0048  0.0050  0.0075  0.005
chb08    5.00  5.00  5.00   4.25  0.0105  0.0105  0.0105  0.005
chb09    4.00  4.00  4.00   4.00  0.0099  0.0099  0.0099  0.005
chb10    7.00  7.00  7.00   7.00  0.0048  0.0051  0.0075  0.005
chb11    4.75  4.75  5.00   4.50  0.0059  0.0059  0.0075  0.005
chb12    4.75  4.75  5.50   4.75  0.0049  0.0051  0.0075  0.005
chb19    3.00  3.00  3.00   3.00  0.0110  0.0110  0.0110  0.005
chb20    2.50  3.00  3.75   3.00  0.0041  0.0050  0.0075  0.005
chb21    0.50  1.75  2.00   1.75  0.0025  0.0050  0.0075  0.005
chb22    3.00  3.00  3.00   3.00  0.0027  0.0050  0.0075  0.005
chb23    6.25  6.50  7.00   6.50  0.0043  0.0050  0.0075  0.005
```

## L2f gate

- pooled pass subj pass val pass fa pass mech_monotone pass; pooled 0.678 vs L2 0.657

**Balanced budget: L2f (L2f replaces L2)**

L6 on L2f: onset CPD 4.0 / hybrid 8.0 s, offset CPD 16.0 / hybrid 12.0 s; sens detector 0.678, hybrid 0.676 -> **localizer cpd**

Sensitivity-priority point (floor 0.0075): 0.697 @ 32.73 FA/day after the localizer -> **kept**

## Test patients, label-free (tier T-A): raw q_i and budgets (balanced | sensitivity), 4 seeds

```
chb03  q_raw 0.0052, 0.0042, 0.0047, 0.0045 | 0.0052, 0.0050, 0.0050, 0.0050 | 0.0075, 0.0075, 0.0075, 0.0075
chb06  q_raw 0.0019, 0.0018, 0.0019, 0.0018 | 0.0050, 0.0050, 0.0050, 0.0050 | 0.0075, 0.0075, 0.0075, 0.0075
chb13  q_raw 0.0038, 0.0034, 0.0037, 0.0032 | 0.0050, 0.0050, 0.0050, 0.0050 | 0.0075, 0.0075, 0.0075, 0.0075
chb14  q_raw 0.0065, 0.0055, 0.0065, 0.0057 | 0.0065, 0.0055, 0.0065, 0.0057 | 0.0075, 0.0075, 0.0075, 0.0075
chb15  q_raw 0.0250, 0.0247, 0.0249, 0.0231 | 0.0200, 0.0200, 0.0200, 0.0200 | 0.0200, 0.0200, 0.0200, 0.0200
chb16  q_raw 0.0041, 0.0028, 0.0033, 0.0033 | 0.0050, 0.0050, 0.0050, 0.0050 | 0.0075, 0.0075, 0.0075, 0.0075
chb17  q_raw 0.0024, 0.0024, 0.0026, 0.0019 | 0.0050, 0.0050, 0.0050, 0.0050 | 0.0075, 0.0075, 0.0075, 0.0075
chb18  q_raw 0.0082, 0.0074, 0.0080, 0.0063 | 0.0082, 0.0074, 0.0080, 0.0063 | 0.0082, 0.0075, 0.0080, 0.0075
```

**Freeze candidate: {"localizer": "cpd", "points": {"balanced": [0.005, 0.02], "sensitivity": [0.0075, 0.02]}}**

Elapsed 76 s.