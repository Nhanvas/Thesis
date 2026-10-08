# Part A -- oracle upper bound of gating, validation only (3 patients, 15 reference events)

| variant | A8 matched/15 | A8 sens | A8 FA/day | A8 cell | at 50/2.0/90: TP | FP | FA/day | min FA/day with TP >= V0's A8 TP |
|---|---|---|---|---|---|---|---|---|
| V0 | 5 | 0.333 | 25.0 | m75/p5.0/mg300 | 11 | 448 | 96.5 | 25.0 |
| V1 | 15 | 1.000 | 7.5 | m80/p10.0/mg300 | 15 | 310 | 66.8 | 7.5 |
| V2 | 14 | 0.933 | 7.8 | m80/p5.0/mg300 | 14 | 254 | 54.7 | 3.7 |

V1 and V2 keep every ictal window untouched, so they are upper bounds that no gate without seizure labels can reach. Part of any gain comes from the lower background variance, hence a lower effective PELT penalty, once 40% of the windows are replaced by a constant.

# Part B -- seizure visibility vs smoothing length, by seizure length (DESCRIPTIVE ONLY)

e = share of equally long non-ictal spans whose smoothed maximum >= the seizure's peak. Compare k only within a row group. Nothing is selected from this table.

| set | seizure length | reference | k (windows) | seizures | median e | e <= 5% | e <= 2% |
|---|---|---|---|---|---|---|---|
| test | long (>=15) | all | 1 | 31 | 0.378 | 1 | 0 |
| test | long (>=15) | all | 3 | 31 | 0.303 | 1 | 0 |
| test | long (>=15) | all | 5 | 31 | 0.304 | 1 | 0 |
| test | long (>=15) | all | 9 | 31 | 0.260 | 1 | 0 |
| test | long (>=15) | all | 15 | 31 | 0.220 | 2 | 0 |
| test | long (>=15) | oracleV1 | 1 | 31 | 0.009 | 24 | 20 |
| test | long (>=15) | oracleV1 | 3 | 31 | 0.001 | 27 | 25 |
| test | long (>=15) | oracleV1 | 5 | 31 | 0.000 | 28 | 25 |
| test | long (>=15) | oracleV1 | 9 | 31 | 0.000 | 29 | 26 |
| test | long (>=15) | oracleV1 | 15 | 31 | 0.000 | 29 | 27 |
| test | mid (5-14) | all | 1 | 27 | 0.255 | 1 | 0 |
| test | mid (5-14) | all | 3 | 27 | 0.218 | 3 | 0 |
| test | mid (5-14) | all | 5 | 27 | 0.182 | 4 | 0 |
| test | mid (5-14) | all | 9 | 27 | 0.201 | 2 | 0 |
| test | mid (5-14) | all | 15 | 27 | 0.297 | 3 | 0 |
| test | mid (5-14) | oracleV1 | 1 | 27 | 0.013 | 17 | 14 |
| test | mid (5-14) | oracleV1 | 3 | 27 | 0.007 | 18 | 17 |
| test | mid (5-14) | oracleV1 | 5 | 27 | 0.005 | 19 | 17 |
| test | mid (5-14) | oracleV1 | 9 | 27 | 0.005 | 18 | 17 |
| test | mid (5-14) | oracleV1 | 15 | 27 | 0.011 | 18 | 17 |
| test | short (<=4 windows) | all | 1 | 18 | 0.369 | 0 | 0 |
| test | short (<=4 windows) | all | 3 | 18 | 0.519 | 0 | 0 |
| test | short (<=4 windows) | all | 5 | 18 | 0.539 | 0 | 0 |
| test | short (<=4 windows) | all | 9 | 18 | 0.483 | 0 | 0 |
| test | short (<=4 windows) | all | 15 | 18 | 0.495 | 0 | 0 |
| test | short (<=4 windows) | oracleV1 | 1 | 18 | 0.008 | 11 | 11 |
| test | short (<=4 windows) | oracleV1 | 3 | 18 | 0.007 | 11 | 10 |
| test | short (<=4 windows) | oracleV1 | 5 | 18 | 0.003 | 13 | 11 |
| test | short (<=4 windows) | oracleV1 | 9 | 18 | 0.001 | 13 | 12 |
| test | short (<=4 windows) | oracleV1 | 15 | 18 | 0.002 | 15 | 13 |
| val | long (>=15) | all | 1 | 10 | 0.078 | 2 | 1 |
| val | long (>=15) | all | 3 | 10 | 0.043 | 6 | 2 |
| val | long (>=15) | all | 5 | 10 | 0.042 | 6 | 2 |
| val | long (>=15) | all | 9 | 10 | 0.042 | 6 | 2 |
| val | long (>=15) | all | 15 | 10 | 0.045 | 5 | 3 |
| val | long (>=15) | oracleV1 | 1 | 10 | 0.003 | 10 | 8 |
| val | long (>=15) | oracleV1 | 3 | 10 | 0.000 | 10 | 10 |
| val | long (>=15) | oracleV1 | 5 | 10 | 0.000 | 10 | 10 |
| val | long (>=15) | oracleV1 | 9 | 10 | 0.000 | 10 | 10 |
| val | long (>=15) | oracleV1 | 15 | 10 | 0.000 | 10 | 10 |
| val | mid (5-14) | all | 1 | 3 | 0.331 | 0 | 0 |
| val | mid (5-14) | all | 3 | 3 | 0.219 | 0 | 0 |
| val | mid (5-14) | all | 5 | 3 | 0.172 | 0 | 0 |
| val | mid (5-14) | all | 9 | 3 | 0.109 | 0 | 0 |
| val | mid (5-14) | all | 15 | 3 | 0.146 | 0 | 0 |
| val | mid (5-14) | oracleV1 | 1 | 3 | 0.004 | 2 | 2 |
| val | mid (5-14) | oracleV1 | 3 | 3 | 0.001 | 2 | 2 |
| val | mid (5-14) | oracleV1 | 5 | 3 | 0.000 | 2 | 2 |
| val | mid (5-14) | oracleV1 | 9 | 3 | 0.000 | 2 | 2 |
| val | mid (5-14) | oracleV1 | 15 | 3 | 0.000 | 3 | 3 |