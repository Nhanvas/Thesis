# Checks of the EUR_DIAG rerun (D32-F, read only; src/eur_diag_check.py)

## EV — within-patient (stratified) AUROC, seizure vs false-alarm events, development

Pairs compared only within the same patient and seed, so the reading does not depend on the per-patient robust-z
scale (which reaches ~1e9 where the background MAD is 0). Patient-cluster bootstrap, B = 2,000. Rule as EV:
lower bound ≥ 0.80.

| feature | direction | dev events with |value| > 1e6 | dev stratified AUROC [95 % CI] | test | chb24 | Siena | rule |
|---|---|---|---|---|---|---|---|
| duration | higher in seizures | 0.0% | 0.795 [0.734, 0.862] | 0.61 | 0.41 | 0.76 | not met |
| evo_dfreq | higher in seizures | 0.0% | 0.735 [0.647, 0.805] | 0.65 | 0.67 | 0.66 | not met |
| n_involved_med | higher in seizures | 6.1% | 0.717 [0.596, 0.821] | 0.52 | 0.79 | 0.65 | not met |
| flat_frac_med | lower in seizures | 4.9% | 0.687 [0.606, 0.750] | 0.59 | 0.47 | 0.52 | not met |
| contiguity_med | higher in seizures | 60.8% | 0.677 [0.558, 0.781] | 0.52 | 0.89 | 0.60 | not met |
| line_length_max | higher in seizures | 0.0% | 0.654 [0.533, 0.750] | 0.45 | 0.40 | 0.72 | not met |
| crest_med | lower in seizures | 0.0% | 0.649 [0.571, 0.739] | 0.70 | 0.76 | 0.71 | not met |
| step_med | lower in seizures | 0.1% | 0.622 [0.473, 0.724] | 0.70 | 0.40 | 0.67 | not met |
| dominance_med | lower in seizures | 0.0% | 0.621 [0.480, 0.746] | 0.52 | 0.66 | 0.59 | not met |
| evo_amp | lower in seizures | 0.0% | 0.609 [0.494, 0.732] | 0.57 | 0.66 | 0.64 | not met |
| line_length_med | higher in seizures | 0.0% | 0.580 [0.458, 0.688] | 0.46 | 0.49 | 0.66 | not met |
| hf_share_med | lower in seizures | 0.0% | 0.575 [0.462, 0.707] | 0.60 | 0.72 | 0.48 | not met |
| hjorth_mob_med | lower in seizures | 0.0% | 0.556 [0.437, 0.687] | 0.58 | 0.71 | 0.45 | not met |
| frontopolar_med | higher in seizures | 0.0% | 0.551 [0.474, 0.617] | 0.42 | 0.67 | 0.54 | not met |
| hjorth_comp_med | higher in seizures | 0.0% | 0.520 [0.377, 0.687] | 0.53 | 0.70 | 0.47 | not met |
| acf_peak_med | lower in seizures | 0.0% | 0.508 [0.393, 0.613] | 0.35 | 0.17 | 0.63 | not met |
| spec_peak_share_med | higher in seizures | 0.0% | 0.501 [0.368, 0.656] | 0.54 | 0.71 | 0.39 | not met |

## D1 — budget the short seizures need (median over seeds)

| set | subject | short seizures | budget (top) | needed at shift 0 | needed at best shift |
|---|---|---|---|---|---|
| chb24 | chb24 | 1 | 1.06% | 3.01% | 0.69% |
| development | chb02 | 1 | 0.62% | 1.35% | 0.61% |
| development | chb12 | 1 | 0.51% | 31.67% | 21.48% |
| development | chb21 | 1 | 0.50% | 0.29% | 0.15% |
| siena | PN10 | 2 | 0.50% | 1.82% | 0.51% |
| siena | PN14 | 1 | 1.85% | 13.14% | 10.22% |
| test | chb06 | 7 | 0.50% | 8.22% | 3.92% |
| test | chb14 | 1 | 0.61% | 0.38% | 0.25% |
| test | chb16 | 10 | 0.50% | 19.86% | 5.29% |
