# results/lab_protocol/v3/ -- producing script

`stepA_grid.csv`, `stepB.csv`, `stepC_auroc.csv`, `denominators.csv`, `SUMMARY.md`, `run.log`, `v2_detected_seizures_full.csv`, `v2_entirely_masked_detected_seizures.csv` <- `src/lab_protocol_eval.py --v3` (docs/CC_PROMPT_LAB_PROTOCOL_V3.md). Reads only results/continuous_eval/cache/ (mask + Scope T scores); the v2-record report also reads nothing new -- same cache, same deterministic ictal-artifact recompute as v2. Does not edit v1's or v2's own results/lab_protocol/ files.
