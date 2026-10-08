# Veto screen v2 (kurt_max, Q=95; flag computed from the signal for every window) -- validation only

| variant | A8 matched/15 | A8 sens | A8 FA/day | cell | at 50/2.0/90: TP | FA/day | min FA/day with TP >= 5 |
|---|---|---|---|---|---|---|---|
| V0 (cached) | 5 | 0.333 | 25.0 | m75/p5.0/mg300 | 11 | 96.5 | 25.0 |
| veto | 9 | 0.600 | 21.5 | m75/p5.0/mg300 | 11 | 88.8 | 12.7 |

## What the rule touched (labels used only here, after the rule was applied)

subject  threshold  windows  vetoed_share  ictal_flagged  ictal_vetoed  flagged_nonictal_vetoed  seizures_over_half_vetoed  seizures
  chb10      3.420    45020         0.105          0.991         0.188                    0.395                          0         7
  chb11      9.970    27713         0.090          1.000         0.142                    0.195                          0         3
  chb22     11.465    27902         0.166          0.964         0.036                    0.287                          0         3

Pooled ictal windows vetoed: 0.122 (unweighted mean over patients).

Pre-registered criteria: (1) A8 matched >= 8/15; (2) mean ictal-window veto share <= 0.15; (3) no validation seizure has more than half of its windows vetoed.