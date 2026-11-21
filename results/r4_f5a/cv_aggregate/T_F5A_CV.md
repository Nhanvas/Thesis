# F5a Part B — CV models (GAE, MLP-AE; partitions 0–5) — reading tables (aggregate written before the run)

Gates: A0 PASS, A1 PASS, A3 PASS. 24 CHB-MIT cases out of fold, 6 partitions (as seeds), patient bootstrap B = 10000, rng 0, chb01 + chb21 one unit. Seconds; [95 % interval].

## V1 · Detection (per-patient means over partitions)

| model | arm | detector sens / F1 / FP/day | localizer | hybrid | loc − det Δsens | ΔFP/day | hyb − loc Δsens | ΔFP/day |
|---|---|---|---|---|---|---|---|---|
| gae | own | 0.737 / 0.208 / 28.2 | 0.733 / 0.211 / 27.4 | 0.736 / 0.210 / 27.6 | -0.003 [-0.009, +0.000] | -0.9 [-1.2, -0.6] | +0.003 [+0.000, +0.009] | +0.2 [+0.0, +0.4] |
| gae | fixed | 0.678 / 0.216 / 22.4 | 0.675 / 0.219 / 21.7 | 0.678 / 0.218 / 21.9 | -0.003 [-0.009, +0.000] | -0.7 [-1.0, -0.4] | +0.003 [+0.000, +0.009] | +0.2 [-0.0, +0.4] |
| mlp | own | 0.742 / 0.281 / 20.3 | 0.739 / 0.288 / 19.3 | 0.740 / 0.284 / 19.6 | -0.003 [-0.009, +0.000] | -0.9 [-1.4, -0.6] | +0.001 [+0.000, +0.004] | +0.2 [+0.0, +0.5] |
| mlp | fixed | 0.676 / 0.285 / 16.2 | 0.673 / 0.290 / 15.4 | 0.674 / 0.289 / 15.5 | -0.004 [-0.010, +0.000] | -0.8 [-1.3, -0.4] | +0.002 [+0.000, +0.005] | +0.1 [-0.1, +0.4] |

## V2 · Boundaries (matched pairs pooled over partitions)

| model | arm | pairs | onset det / loc / hyb | offset det / loc / hyb | offset signed det / loc / hyb | loc − det \|onset\| | loc − det \|offset\| | hyb − loc \|offset\| | localizer offset signed |
|---|---|---|---|---|---|---|---|---|---|
| gae | own | 677 | 16 / 8 / 8 | 16 / 16 / 12 | -4 / +4 / +0 | -8 [-12, -4] | +0 [-4, +8] | -4 [-12, +0] | +4 [+0, +16] |
| gae | fixed | 564 | 16 / 8 / 8 | 16 / 16 / 12 | -4 / +8 / +0 | -8 [-16, -8] | +0 [-4, +12] | -4 [-16, +0] | +8 [+0, +16] |
| mlp | own | 713 | 12 / 4 / 4 | 12 / 16 / 8 | -4 / +4 / +0 | -8 [-12, -4] | +4 [-6, +8] | -8 [-12, +0] | +4 [+0, +16] |
| mlp | fixed | 607 | 12 / 4 / 4 | 8 / 12 / 8 | -4 / +8 / +0 | -8 [-16, -4] | +4 [-4, +12] | -4 [-16, +0] | +8 [+4, +20] |

**Per partition (own arm):** localizer signed offset median / localizer − detector median |offset| / localizer − detector median |onset|

| model | p0 | p1 | p2 | p3 | p4 | p5 | partitions with signed offset > 0 |
|---|---|---|---|---|---|---|---|
| gae | +4 / +0 / -10 | +4 / +0 / -8 | +4 / +2 / -8 | +4 / +0 / -8 | +4 / +2 / -8 | +8 / +4 / -8 | 6 / 6 |
| mlp | +8 / +4 / -8 | +4 / +2 / -8 | +6 / +4 / -8 | +8 / +8 / -8 | +8 / +4 / -8 | +4 / +0 / -8 | 6 / 6 |

## D3 · Post-ictal profile of the score x (every valid seizure; partitions averaged per seizure)

| model | seizures | return − null | fall − rise | level 0–60 s after offset | level / seizure level |
|---|---|---|---|---|---|
| gae | 143 | +4 [+2, +8] | +1 [+0, +5] | +0.182 [+0.121, +0.278] | +0.58 [+0.39, +0.76] |
| mlp | 143 | +7 [+2, +11] | +7 [+4, +10] | +0.212 [+0.136, +0.325] | +0.49 [+0.38, +0.68] |

Model-free (the EEG features, once per seizure): mf_ll: return − null +4 [+0, +16]; mf_d: return − null +8 [+0, +20]; mf_pow: return − null +8 [+0, +20]

## D4 · Where the localizer puts the offset (own arm, localizer accepted)

| model | pairs | end − return point | share nearer return point | within-patient ρ(error, return) | ρ(error, fall) | edge share |
|---|---|---|---|---|---|---|
| gae | 619 | +0 [-8, +0] | +0.40 [+0.28, +0.54] | +0.39 [+0.22, +0.52] | +0.20 [+0.07, +0.32] | +0.01 [+0.00, +0.03] |
| mlp | 662 | +0 [-12, +0] | +0.37 [+0.26, +0.49] | +0.25 [+0.11, +0.39] | +0.02 [-0.11, +0.16] | +0.01 [+0.00, +0.02] |

## D5 · Diagnostic interventions (own arm, localizer accepted; not a localizer rule)

| model | \|offset\| record | 3 cp 2nd point Δ \|offset\| | 3rd point nearer return | m30 Δ signed |
|---|---|---|---|---|
| gae | 16 | +16 [+4, +24] | +0.64 [+0.58, +0.70] | +4 [+0, +8] |
| mlp | 16 | +12 [+4, +24] | +0.67 [+0.59, +0.75] | +4 [+0, +16] |

## HB2 · GAE − MLP-AE, paired by patient (own arm)

| quantity | GAE | MLP-AE | GAE − MLP-AE |
|---|---|---|---|
| localizer signed offset (patient median) | +29.667 | +30.417 | -0.750 [-7.391, +6.417] |
| loc − det |offset| (patient) | +1.917 | -1.000 | +2.917 [-6.692, +14.000] |
| return − null x (patient mean) | +22.568 | +40.026 | -17.459 [-31.763, -5.619] |
| level 0–60 s after offset (patient mean) | +0.259 | +0.304 | -0.046 [-0.089, -0.002] |
| level / seizure level (patient mean) | -0.061 | +2.226 | -2.287 [-6.375, +0.348] |
