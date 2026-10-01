# results/lab_protocol/ -- producing script

`stepA_grid.csv`, `stepB.csv`, `stepC_auroc.csv`, `masking_cost.csv`, `denominators.csv`, `SUMMARY.md`, `run.log` <- `src/lab_protocol_eval.py` (docs/CC_PROMPT_LAB_PROTOCOL.md). Reads only results/continuous_eval/cache/ (mask + Scope T scores) -- never writes there, never re-reads an EDF, never runs the model.
