# P3 levers -- L2 per-patient budget and L6 localizer hybrid, 15 non-test, 4 seeds

Reproduction: frozen detector and E18 CPD match the record.

L2 calibration (seed 42, non-test): k = 4.0677 robust-z units; median q_i = 0.005.

## Detection and localization (pooled sens @ FA/day, 4-seed mean)

```
frozen detector          0.668 @ 19.98 | subject-mean 0.828 @ 19.52 | val 0.967 @ 17.50 | no-chb12 0.853 | chb12 TP 4.75 | short 2.00/3 | seeds 0.681, 0.660, 0.660, 0.670
frozen cpd               0.662 @ 19.55 | subject-mean 0.822 @ 19.19 | val 0.933 @ 17.34 | no-chb12 0.846 | chb12 TP 4.75 | short 2.00/3 | seeds 0.670, 0.660, 0.649, 0.670
frozen hybrid            0.662 @ 19.73 | subject-mean 0.822 @ 19.33 | val 0.933 @ 17.40 | no-chb12 0.846 | chb12 TP 4.75 | short 2.00/3 | seeds 0.670, 0.660, 0.649, 0.670
L2 detector              0.657 @ 20.53 | subject-mean 0.814 @ 19.76 | val 0.983 @ 13.14 | no-chb12 0.838 | chb12 TP 4.75 | short 1.50/3 | seeds 0.670, 0.649, 0.660, 0.649
L2 cpd                   0.649 @ 20.02 | subject-mean 0.804 @ 19.29 | val 0.933 @ 13.09 | no-chb12 0.827 | chb12 TP 4.75 | short 1.50/3 | seeds 0.660, 0.649, 0.638, 0.649
L2 hybrid                0.654 @ 20.21 | subject-mean 0.811 @ 19.49 | val 0.967 @ 13.09 | no-chb12 0.835 | chb12 TP 4.75 | short 1.50/3 | seeds 0.660, 0.649, 0.660, 0.649
```

## Per subject, detector (4-seed mean): budget top-p, TP, FP

```
             fp             top           tp        n_ref
budget       L2  frozen      L2 frozen    L2 frozen      
subject                                                  
chb01     37.50   16.75  0.0073  0.005  7.00   7.00     7
chb02     44.25   34.50  0.0061  0.005  3.00   3.00     3
chb04    161.50  174.00  0.0047  0.005  3.00   3.00     4
chb05     11.00   19.00  0.0044  0.005  5.00   5.00     5
chb07     30.75   34.25  0.0048  0.005  3.00   3.00     3
chb08      5.25    1.50  0.0105  0.005  5.00   4.25     5
chb09     81.75   42.50  0.0099  0.005  4.00   4.00     4
chb10     24.25   26.50  0.0048  0.005  7.00   7.00     7
chb11     22.00   18.25  0.0059  0.005  4.75   4.50     5
chb12     27.00   27.50  0.0049  0.005  4.75   4.75    26
chb19     47.75   22.25  0.0110  0.005  3.00   3.00     3
chb20     20.50   27.50  0.0041  0.005  2.50   3.00     8
chb21     32.50   61.75  0.0025  0.005  0.50   1.75     4
chb22     14.75   36.50  0.0027  0.005  3.00   3.00     3
chb23     14.25   17.00  0.0043  0.005  6.25   6.50     7
```

## L2 gate

- pooled pass subj pass val pass fa pass mech_chb12 pass

**L2 ADOPTED**

## L6 on the frozen detector (matched pairs n = 243)

```
onset   detector median  16.0 s IQR [12.0, 28.0] bias +16.0 | CPD median   8.0 s IQR [4.0, 12.0] bias  +4.0 | hybrid median   8.0 s IQR [4.0, 12.0] bias  +4.0
offset  detector median  20.0 s IQR [8.0, 56.0] bias  -4.0 | CPD median  16.0 s IQR [4.0, 44.0] bias  +4.0 | hybrid median  12.0 s IQR [4.0, 40.0] bias  +0.0
sens    detector 0.668 | CPD 0.662 | hybrid 0.662
```
- sensitivity >= detector - 0.005 -> FAIL; errors -> pass

**L6 on frozen: NOT adopted (CPD stays)**

## L6 on the L2 detector (matched pairs n = 239)

```
onset   detector median  16.0 s IQR [12.0, 20.0] bias +16.0 | CPD median   8.0 s IQR [4.0, 12.0] bias  +4.0 | hybrid median   8.0 s IQR [4.0, 12.0] bias  +4.0
offset  detector median  24.0 s IQR [8.0, 56.0] bias  -8.0 | CPD median  16.0 s IQR [4.0, 46.0] bias  +4.0 | hybrid median  12.0 s IQR [4.0, 40.0] bias  +0.0
sens    detector 0.657 | CPD 0.649 | hybrid 0.654
```
- sensitivity >= detector - 0.005 -> pass; errors -> pass

**L6 on L2: ADOPTED (hybrid localizer)**

**P3 configuration for the freeze: budget = L2, localizer = hybrid**

## Label-free budget p_i of the test patients under L2 (tier T-A, no annotation read; 4 seeds)

```
chb03  0.0052, 0.0042, 0.0047, 0.0045
chb06  0.0025, 0.0025, 0.0025, 0.0025
chb13  0.0038, 0.0034, 0.0037, 0.0032
chb14  0.0065, 0.0055, 0.0065, 0.0057
chb15  0.0200, 0.0200, 0.0200, 0.0200
chb16  0.0041, 0.0028, 0.0033, 0.0033
chb17  0.0025, 0.0025, 0.0026, 0.0025
chb18  0.0082, 0.0074, 0.0080, 0.0063
```

Elapsed 173 s.