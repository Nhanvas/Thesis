# results/continuous_eval/loss_decomposition/ -- producing script

`SUMMARY.md`, `categories.csv`, `fa_categories.csv`, `run.log` <- `src/diag_loss_decomposition.py` (docs/CC_PROMPT_LOSS_DECOMPOSITION.md). Reads only results/continuous_eval/cache/ (mask + Scope T scores + per-branch components where cached) and results/app_eval_v3/cache/ (application v3 fused scores, validation subjects only) -- no EDF is read, no model is run, nothing is recomputed.
