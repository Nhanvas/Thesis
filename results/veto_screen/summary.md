# Veto screen (kurt_max, Q=95) -- validation only

| variant | A8 matched/15 | A8 sens | A8 FA/day | cell | at 50/2.0/90: TP | FA/day | min FA/day with TP >= 5 |
|---|---|---|---|---|---|---|---|
| V0 (cached) | 5 | 0.333 | 25.0 | m75/p5.0/mg300 | 11 | 96.5 | 25.0 |
| veto | 11 | 0.733 | 20.3 | m80/p5.0/mg300 | 13 | 93.3 | 10.8 |

## What the rule touched (labels used only here, after the rule was applied)

subject  threshold  windows  vetoed_share  ictal_vetoed  flagged_nonictal_vetoed  seizures_over_half_vetoed  seizures
  chb10      3.605    45020         0.090         0.000                    0.369                          0         7
  chb11     10.500    27713         0.078         0.000                    0.179                          0         3
  chb22     12.360    27902         0.144         0.000                    0.256                          0         3

Pooled ictal windows vetoed: 0.000 (unweighted mean over patients).

Pre-registered criteria: (1) A8 matched >= 8/15; (2) mean ictal-window veto share <= 0.15; (3) no validation seizure has more than half of its windows vetoed.