# ictal_channels_DRAFT.csv — AI-DRAFT, PROVISIONAL

Converted verbatim from `results/attribution_v5/labels/labels_ALL_FINAL.csv` by
`src/build_label_draft.py`. **Not reviewed or frozen by the supervisor.** Every result
scored against this file must be reported as PROVISIONAL (ATTRIBUTION_SPEC §9, A2/D2).

Rows with an empty `ictal_channels` are **generalized** seizures whose reader note reads
DIFFUSE (no localisable lead channel) — they are labels, not missing data. Per §4.5 they are
excluded from AUROC/AUPRC (y would be undefined) and enter only the spread analysis.

Alignment with `seizure_blocks.csv` verified on all 76 seizures (edf_file + onset_s).
