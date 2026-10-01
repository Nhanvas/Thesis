# CC_PROMPT_LOSS_DECOMPOSITION.md — which windows make the continuous-timeline score fail

Read-only diagnostic on cached scores; nothing is recomputed, tuned or committed except this script and
its outputs. Expected time 15–25 minutes, CPU light. Code `src/diag_loss_decomposition.py`, outputs
`results/continuous_eval/loss_decomposition/`.

**Design decisions will be taken on the validation patients only (chb10, chb11, chb22).** The test
patients are reported in a separate table, descriptively, and must not be used to choose anything.

## Inputs

- Scope T fused scores per window (A2 cache) for the 3 validation and 8 test patients, and their
  per-branch scores (zrecon, zlatent, zgamma) if cached.
- The application v3 headless fused scores for the 3 validation patients
  (`results/app_eval_v3/cache/`).
- The thesis's own ±5 SD artifact flag per window (Scope T artifact-mask cache) and the signal-loss
  flag.
- The annotation (for labelling categories only).

## Window categories (each window gets exactly one, in this priority order)

ictal · signal-loss · post-ictal 0–2 min · post-ictal 2–10 min · post-ictal 10–60 min ·
post-ictal 1–4 h · artifact (±5 SD rule) · other background. "Post-ictal x" is measured from the
annotated offset of the most recent seizure in the same file.

## Report, per patient and pooled, separately for validation (both scorers) and test (Scope T)

1. Count and hours per category.
2. AUROC of ictal windows against each negative category alone.
3. Macro window AUROC over all windows, and with each negative category removed in turn.
4. Composition of the highest-scoring negatives: share of each category among the top 1 % and top 5 %
   of non-ictal windows by fused score.
5. Per branch (if cached): the same item 2 for zrecon, zlatent, zgamma.
6. Event level, Scope T at 50/2.0/90 and at 75/5/300 (validation selections already made): category of
   the onset window of every false alarm, as counts and shares.

## Output

`SUMMARY.md` with the tables above (validation first, test second), no interpretation, plus
`categories.csv` and `fa_categories.csv`. Commit the script and the outputs with explicit paths inside
`bash -e`.
