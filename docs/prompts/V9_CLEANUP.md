# V9-CLEANUP — tidy the local workspace after the V9 experiments (Claude Code, laptop)

Run only after `V9_V1` has finished. Estimated runtime: 15–30 min plus the author's review (estimated).

## Principles (binding)
- **Inventory first, then a proposal, then wait for the author's approval.** Nothing is moved or deleted before he approves the table.
- Archive, don't delete: superseded material goes to `F:/Study/Thesis/Archive/2026-10-28/` with the same relative path. Only regenerable caches (`__pycache__`, `_parts/`, `_m/`, `cache/` of V9 scripts, partial downloads) may be proposed for deletion, each with its size and how to regenerate it.
- **Keep untouched:** every frozen result and script of the thesis system (`results/p3c_freeze/`, `e22_*`, `e23_*`, `x1_external/`, `attribution_v7/` (labels), `attribution_v8/`, `application_eval_v4/`, `continuous_eval/`, `p3_anatomy/`, `t1_demo/`), `data/trainset_v2/`, `data/testset_v2/`, `data/models_*`, `data/pernode_v2/`, `Reports/final/`, `web_demo/` database used for the demo, `bme11/`.
- Keep until after the defense (figures may need re-drawing): `results/v9_anatomy/xcache/`, the Siena and CHB-MIT EDFs, the clinical EDFs.
- Clinical data and anything derived from it never enter the repo; patient names never appear in any listing you print (refer to clin01/clin02).
- Commit with explicit paths only; never `git add` a directory that may hold unrelated work.

## Step 1 — inventory (print, do not change)
- `git status` (modified, untracked), with sizes; commits since tag `szscan-frozen-v4.1`.
- Uncommitted V9 work (e.g. `src/v9_e4_knn24.py`, `results/v9_e4/`, anything from V1).
- Sizes of every `results/v9_*/` directory and its cache subfolders; `__pycache__`; log files.
- `F:/Study/Thesis/Agent/inbox/` contents; `docs/prompts/` V9 files; `F:/Study/Thesis/Dataset/` (siena, clinical, partial-download leftovers); `F:/Study/Thesis/Archive/2026-10-27/` (Siena partial files).
- Duplicates or near-duplicates (same name in two places, same hash).

## Step 2 — proposal table for the author
Columns: path · size · proposed action (keep / commit / move to Defense/v9/ / move to Archive / delete-candidate) · reason. Group by folder. Then **stop and wait**.

## Step 3 — after approval
1. Commit pending V9 code and results (explicit paths), one commit per experiment if practical; then tag `v9-results`.
2. Create `docs/V9_RESULTS_INDEX.md` in the repo: one row per V9 task (T1, T3, T4, C1, E1, E1b, E2, E3, E4, V1): question, script, results directory, commit hash, report path. Commit it.
3. Move the V9 reports from `Agent/inbox/` to `F:/Study/Thesis/Defense/v9_reports/` (inbox stays a hand-over tray).
4. Apply the approved moves/deletions; write `F:/Study/Thesis/Archive/2026-10-28/CLEANUP_LOG.md` (every action, size freed).
5. Final `git status` must be clean except files the author chose to leave.

## Return format
Write the report (inventory summary, approved actions, sizes freed, final git status, the tag and commit hashes) to `F:/Study/Thesis/Agent/inbox/V9_CLEANUP_REPORT.md`.
