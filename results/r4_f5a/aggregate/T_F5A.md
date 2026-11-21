# F5a on V5 — reading tables (aggregate written before the run; design results/r4_f5a/DESIGN_F5A.md)

Gates: A0 PASS, A1 PASS, A2 PASS, A3 PASS. Patient bootstrap B = 10000, rng 0, chb01 + chb21 one unit. Values in seconds unless stated; [95 % interval].

## V1 · Detection (per-patient means; paired differences)

| set | detector sens / F1 / FP/day | localizer | hybrid | localizer − detector Δsens | ΔFP/day | hybrid − localizer Δsens | ΔF1 | ΔFP/day | seizures Δ (loc−det, hyb−loc; per seed) |
|---|---|---|---|---|---|---|---|---|---|
| development | 0.842 / 0.224 / 23.7 | 0.832 / 0.225 / 23.2 | 0.838 / 0.225 / 23.4 | -0.010 [-0.032, +0.000] | -0.5 [-0.7, -0.3] | +0.007 [+0.000, +0.021] | -0.001 [-0.007, +0.005] | +0.2 [+0.1, +0.4] | -0.19, +0.12 |
| test held-out | 0.500 / 0.159 / 24.5 | 0.498 / 0.161 / 23.8 | 0.500 / 0.162 / 23.8 | -0.003 [-0.008, +0.000] | -0.8 [-1.2, -0.4] | +0.003 [+0.000, +0.008] | +0.001 [-0.001, +0.004] | +0.0 [-0.4, +0.3] | -0.06, +0.06 |
| test final | 0.570 / 0.177 / 29.6 | 0.567 / 0.180 / 28.7 | 0.570 / 0.181 / 28.8 | -0.003 [-0.008, +0.000] | -0.9 [-1.2, -0.6] | +0.003 [+0.000, +0.008] | +0.000 [-0.002, +0.003] | +0.1 [-0.3, +0.4] | -0.06, +0.06 |
| chb24 | 0.844 / 0.482 / 30.1 | 0.844 / 0.500 / 27.8 | 0.844 / 0.495 / 28.4 | +0.000 | -2.3 | +0.000 | -0.005 | +0.6 | +0.00, +0.00 |
| Siena | 0.630 / 0.229 / 42.5 | 0.645 / 0.233 / 40.6 | 0.645 / 0.235 / 40.7 | +0.015 [-0.021, +0.060] | -1.9 [-3.3, -0.7] | +0.000 [+0.000, +0.000] | +0.002 [-0.002, +0.008] | +0.1 [-0.9, +0.8] | +0.06, +0.00 |

## V2 · Boundaries (matched pairs; median |error|, signed median, share late)

| set | pairs | onset det / loc / hyb | offset det / loc / hyb | offset signed det / loc / hyb | offset late det / loc / hyb | loc − det \|onset\| | loc − det \|offset\| | hyb − loc \|offset\| |
|---|---|---|---|---|---|---|---|---|
| development | 247 | 16 / 4 / 8 | 24 / 16 / 12 | -4 / +4 / +0 | 0.39 / 0.51 / 0.46 | -12 [-12, -4] | -8 [-20, +4] | -4 [-12, +4] |
| test held-out | 103 | 28 / 8 / 8 | 16 / 20 / 12 | +0 / +16 / +4 | 0.43 / 0.73 / 0.51 | -20 [-28, -8] | +4 [-6, +20] | -8 [-20, +4] |
| test final | 146 | 32 / 12 / 12 | 20 / 24 / 16 | -4 / +16 / +0 | 0.44 / 0.72 / 0.44 | -20 [-28, -8] | +4 [-4, +16] | -8 [-20, +4] |
| chb24 | 54 | 12 / 4 / 4 | 8 / 4 / 4 | -8 / +0 / -4 | 0.07 / 0.24 / 0.07 | -8 | -4 | +0 |
| Siena | 117 | 36 / 20 / 20 | 28 / 28 / 20 | +8 / +20 / +4 | 0.50 / 0.66 / 0.53 | -16 [-24, -4] | +0 [-8, +24] | -8 [-76, +4] |

x1 record (Table 10, external): chb24 53 pairs, offset det 8 / loc 4 / hyb 4; siena 116 pairs, offset det 28 / loc 28 / hyb 20

## D3 · Post-ictal profile (every valid annotated seizure; return time k = 3, censored at 180 s)

| set | seizures valid / all | series | return time median | null (same rule in the pre-onset background) | return − null | share censored | fall − rise |
|---|---|---|---|---|---|---|---|
| development | 70 / 93 | x | +8 [+5, +22] | +0 [+0, +1] | +7 [+2, +17] | 0.04 | +1 [-0, +9] |
| development | 70 / 93 | x caught | +10 [+8, +32] | +0 [+0, +1] | +8 [+2, +28] | 0.05 | +2 [+0, +14] |
| development | 70 / 93 | m | +8 [+5, +24] | +0 [+0, +1] | +8 [+3, +18] | 0.04 |  |
| development | 70 / 93 | ll | +16 [+8, +28] | +0 [+0, +0] | +16 [+4, +28] | 0.10 | +0 [-8, +20] |
| development | 70 / 93 | d | +14 [+4, +24] | +0 [+0, +0] | +8 [+4, +20] | 0.06 |  |
| development | 70 / 93 | pow | +20 [+8, +32] | +0 [+0, +0] | +14 [+4, +24] | 0.07 |  |
| test | 64 / 76 | x | +8 [+4, +10] | +1 [+0, +2] | +3 [+0, +8] | 0.00 | +0 [-1, +4] |
| test | 64 / 76 | x caught | +10 [+8, +16] | +2 [+0, +3] | +8 [+0, +15] | 0.00 | +0 [-2, +5] |
| test | 64 / 76 | m | +7 [+3, +11] | +1 [+0, +2] | +2 [+0, +8] | 0.00 |  |
| test | 64 / 76 | ll | +0 [+0, +8] | +0 [+0, +0] | +0 [+0, +4] | 0.02 | +0 [+0, +20] |
| test | 64 / 76 | d | +10 [+0, +36] | +0 [+0, +0] | +4 [+0, +36] | 0.03 |  |
| test | 64 / 76 | pow | +4 [+0, +40] | +0 [+0, +0] | +2 [+0, +40] | 0.02 |  |
| chb24 | 9 / 16 | x | +2 | +4 | -1 | 0.00 | +0 |
| chb24 | 9 / 16 | x caught | +2 | +4 | -2 | 0.00 | +0 |
| chb24 | 9 / 16 | m | +2 | +4 | -1 | 0.00 |  |
| chb24 | 9 / 16 | ll | +0 | +0 | +0 | 0.11 | +8 |
| chb24 | 9 / 16 | d | +4 | +0 | +0 | 0.00 |  |
| chb24 | 9 / 16 | pow | +4 | +0 | +0 | 0.00 |  |
| Siena | 46 / 47 | x | +6 [+4, +12] | +3 [+0, +4] | +5 [+2, +10] | 0.03 | +3 [+1, +14] |
| Siena | 46 / 47 | x caught | +10 [+4, +13] | +2 [+0, +6] | +6 [+0, +12] | 0.04 | +4 [+1, +14] |
| Siena | 46 / 47 | m | +6 [+4, +12] | +2 [+0, +4] | +5 [+2, +11] | 0.02 |  |
| Siena | 46 / 47 | ll | +12 [+0, +38] | +0 [+0, +0] | +12 [+0, +36] | 0.11 | +4 [+4, +28] |
| Siena | 46 / 47 | d | +16 [+8, +48] | +0 [+0, +0] | +16 [+4, +38] | 0.15 |  |
| Siena | 46 / 47 | pow | +10 [+0, +42] | +0 [+0, +0] | +8 [+0, +36] | 0.20 |  |

| set | within-patient ρ(return x, return line length) | ρ(return x, return δ power) |
|---|---|---|
| development | +0.38 [+0.21, +0.54] | +0.00 [-0.34, +0.30] |
| test | +0.02 [-0.17, +0.30] | +0.09 [-0.18, +0.29] |
| chb24 | +0.27 | -0.31 |
| Siena | +0.38 [-0.06, +0.70] | +0.37 [-0.05, +0.70] |

## D4 · Where the localizer puts the offset (matched pairs, localizer accepted)

| set | pairs | signed offset error | end − return point | share nearer return point | within-patient ρ(error, return) | ρ(error, fall) | edge share |
|---|---|---|---|---|---|---|---|
| development | 239 | +4 [-4, +24] | -8 [-16, +0] | +0.35 [+0.20, +0.52] | +0.19 [-0.05, +0.39] | +0.24 [-0.01, +0.44] | +0.01 [+0.00, +0.03] |
| test held-out | 91 | +16 [+4, +36] | +0 [-8, +20] | +0.52 [+0.26, +0.68] | +0.60 [+0.01, +0.83] | +0.36 [-0.14, +0.64] | +0.04 [+0.00, +0.14] |
| test final | 131 | +16 [+8, +36] | +0 [+0, +8] | +0.51 [+0.36, +0.65] | +0.50 [+0.13, +0.79] | +0.09 [-0.24, +0.45] | +0.04 [+0.01, +0.11] |
| chb24 | 48 | +0 | -4 | +0.02 | -0.06 | +0.15 | +0.04 |
| Siena | 93 | +16 [+4, +88] | +0 [-8, +68] | +0.42 [+0.34, +0.53] | +0.43 [+0.03, +0.75] | -0.07 [-0.38, +0.28] | +0.01 [+0.00, +0.03] |

## D5 · Diagnostic interventions (same pairs; not a localizer rule)

| set | \|offset\| record (2 cp, m15) | 3 cp: 2nd point \|offset\| | Δ (2nd − record) | 3rd point nearer return | m30 \|offset\| | Δ signed (m30 − record) |
|---|---|---|---|---|---|---|
| development | 16 | 36 | +20 [+0, +40] | +0.64 [+0.55, +0.73] | 24 | +4 [+0, +24] |
| test held-out | 20 | 28 | +8 [-16, +28] | +0.51 [+0.36, +0.65] | 36 | +16 [-8, +46] |
| test final | 20 | 36 | +16 [-8, +28] | +0.59 [+0.43, +0.71] | 28 | +4 [-4, +28] |
| chb24 | 4 | 24 | +20 | +0.68 | 8 | +0 |
| Siena | 20 | 32 | +12 [-68, +40] | +0.58 [+0.39, +0.75] | 20 | +0 [-16, +44] |

## D2 · Strata (localizer − detector median |offset| in the remaining pairs without the stratum)

| set | all | − fallback | − event > 300 s | − merged runs | − ≥ 2 references | − reference < 20 s | − reference > 300 s |
|---|---|---|---|---|---|---|---|
| development | -8 [-20, +4] | -8 [-20, +4] (n−8) | -8 [-16, +4] (n−16) | +0 [-8, +4] (n−78) | -8 [-20, +4] (n−0) | -8 [-20, +4] (n−8) | -4 [-18, +4] (n−4) |
| test held-out | +4 [-6, +20] | +4 [-8, +20] (n−12) | +4 [-6, +20] (n−0) | +4 [-8, +12] (n−20) | +4 [-6, +20] (n−0) | +4 [-12, +20] (n−14) | +4 [-6, +20] (n−0) |
| test final | +4 [-4, +16] | +4 [-8, +20] (n−15) | +4 [-4, +16] (n−0) | +4 [-4, +12] (n−40) | +4 [-4, +16] (n−0) | +4 [-8, +20] (n−14) | +4 [-4, +16] (n−0) |
| chb24 | -4 | -4 (n−6) | -4 (n−0) | -4 (n−8) | -4 (n−0) | -4 (n−0) | -4 (n−0) |
| Siena | +0 [-8, +24] | +4 [-12, +24] (n−24) | +0 [-8, +24] (n−1) | -4 [-8, +8] (n−52) | +0 [-8, +24] (n−0) | -8 [-8, +24] (n−7) | +0 [-8, +24] (n−0) |

## H7 · Pair-weighted vs patient-weighted (localizer − detector median |offset|)

| set | pair-weighted | patient-weighted (median of patient medians) | share of pairs in the 2 largest patients |
|---|---|---|---|
| development | -8 | +0 | 0.23 |
| test held-out | +4 | +10 | 0.48 |
| test final | +4 | +10 | 0.47 |
| chb24 | -4 | -4 | 1.00 |
| Siena | +0 | +0 | 0.33 |
