# EV — event properties of V5's flagged events (EUR_DIAG)

Development: seizure events vs false-alarm events of V5 (arm L2f, after the localizer, 4 seeds); features as robust z against the patient's own background. Oriented AUROC (4-seed mean) with its patient-cluster bootstrap interval; rule: lower bound ≥ 0.80 and the same direction in ≥ 10 of 15 patients. Test, chb24 and Siena: AUROC, descriptive.

| feature | direction | dev AUROC [95 % interval] | patients same direction | rule | test | chb24 | Siena |
|---|---|---|---|---|---|---|---|
| duration | higher in seizures | 0.778 [0.715, 0.846] | 14 of 15 | not met | 0.65 | 0.59 | 0.68 |
| evo_dfreq | higher in seizures | 0.701 [0.636, 0.775] | 15 of 15 | not met | 0.63 | 0.67 | 0.65 |
| n_involved_med | higher in seizures | 0.671 [0.546, 0.788] | 14 of 15 | not met | 0.58 | 0.78 | 0.51 |
| flat_frac_med | lower in seizures | 0.637 [0.543, 0.722] | 14 of 15 | not met | 0.68 | 0.53 | 0.51 |
| line_length_max | higher in seizures | 0.635 [0.548, 0.721] | 10 of 15 | not met | 0.60 | 0.60 | 0.55 |
| contiguity_med | higher in seizures | 0.615 [0.511, 0.718] | 12 of 15 | not met | 0.63 | 0.89 | 0.50 |
| crest_med | lower in seizures | 0.611 [0.517, 0.718] | 12 of 15 | not met | 0.58 | 0.76 | 0.70 |
| evo_amp | lower in seizures | 0.602 [0.498, 0.695] | 10 of 15 | not met | 0.64 | 0.66 | 0.52 |
| line_length_med | higher in seizures | 0.583 [0.497, 0.660] | 10 of 15 | not met | 0.58 | 0.50 | 0.52 |
| acf_peak_med | higher in seizures | 0.552 [0.480, 0.621] | 8 of 15 | not met | 0.61 | 0.83 | 0.61 |
| dominance_med | lower in seizures | 0.551 [0.451, 0.651] | 11 of 15 | not met | 0.55 | 0.66 | 0.52 |
| step_med | lower in seizures | 0.549 [0.458, 0.647] | 11 of 15 | not met | 0.55 | 0.61 | 0.66 |
| frontopolar_med | higher in seizures | 0.519 [0.421, 0.626] | 11 of 15 | not met | 0.57 | 0.67 | 0.51 |
| hjorth_comp_med | lower in seizures | 0.518 [0.374, 0.662] | 5 of 15 | not met | 0.50 | 0.70 | 0.59 |
| hjorth_mob_med | higher in seizures | 0.517 [0.386, 0.645] | 4 of 15 | not met | 0.52 | 0.71 | 0.60 |
| hf_share_med | lower in seizures | 0.516 [0.388, 0.640] | 12 of 15 | not met | 0.52 | 0.72 | 0.61 |
| spec_peak_share_med | higher in seizures | 0.510 [0.351, 0.665] | 9 of 15 | not met | 0.56 | 0.71 | 0.53 |
