# Kurtosis veto -- ONE-SHOT on the test patients (8 patients)

| cell | variant | matched / reference events | sensitivity | FP | FA/day |
|---|---|---|---|---|---|
| m75/p5.0/mg300 | V0 | 6 / 76 | 0.079 | 222 | 19.2 |
| m75/p5.0/mg300 | veto | 6 / 76 | 0.079 | 207 | 17.9 |
| m50/p2.0/mg90 | V0 | 23 / 76 | 0.303 | 848 | 73.3 |
| m50/p2.0/mg90 | veto | 28 / 76 | 0.368 | 903 | 78.1 |

Descriptive, not a selected operating point: best pooled sensitivity with FA/day <= 25 on the test grid.

- V0: 7 / 76 matched, sensitivity 0.092, FA/day 22.9, cell m70/p5.0/mg300
- veto: 11 / 76 matched, sensitivity 0.145, FA/day 23.9, cell m40/p10.0/mg300

## Per patient at the validation cell (m75/p5.0/mg300)

| patient | V0 matched/ref | V0 FP | veto matched/ref | veto FP |
|---|---|---|---|---|
| chb03 | 0/7 | 36 | 1/7 | 31 |
| chb06 | 1/10 | 26 | 0/10 | 29 |
| chb13 | 1/12 | 35 | 1/12 | 37 |
| chb14 | 0/8 | 16 | 0/8 | 12 |
| chb15 | 2/20 | 55 | 1/20 | 40 |
| chb16 | 0/10 | 7 | 0/10 | 6 |
| chb17 | 0/3 | 18 | 0/3 | 12 |
| chb18 | 2/6 | 29 | 3/6 | 40 |

## What the rule touched (labels used only for this diagnostic)

subject  threshold  windows  vetoed_share  ictal_flagged  ictal_vetoed  flagged_nonictal_vetoed
  chb03     13.142    34201         0.122          1.000         0.179                    0.288
  chb06      8.270    60060         0.103          0.333         0.156                    0.180
  chb13      5.812    29700         0.263          0.542         0.056                    0.528
  chb14      5.075    23400         0.058          0.551         0.102                    0.181
  chb15      8.174    36008         0.132          0.882         0.216                    0.337
  chb16     13.716    17100         0.151          0.929         0.071                    0.243
  chb17     13.429    18906         0.096          0.892         0.189                    0.197
  chb18     12.057    32070         0.195          0.904         0.157                    0.401

This is a one-shot result. The test patients were scored several times earlier in the work; the report states that.