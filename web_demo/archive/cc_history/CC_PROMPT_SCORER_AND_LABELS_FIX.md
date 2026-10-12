# Claude Code task — scorer hardening and two figure label fixes

**Owner:** Project 1 (thesis report). **Written:** 2026-09-29. **Runs at:** repo root `F:/Study/Thesis/Code`.
Writes only the three source files named below and the two figure PNGs they produce. Never writes
`web_demo/`. Stage explicit paths, one `bash -e` block per commit.

## 1. `src/eval_application_events.py`: a file name the annotation does not know must stop the run

In `score_exports()`, a file whose `file_name` is missing from the parsed summary currently gets
`ref_iv = []`. Its seizures then vanish and any detection in it is counted as a false alarm. The
coverage check reports the shortfall only after scoring.

- Before any scoring, check every `(subject, file_name)` in `files.csv` against `load_annotation(subject)`.
  If any is absent, raise `ScorerInputError` listing each missing name and the first three names the
  summary does have, so a format mismatch (for example a missing `.edf` extension) is obvious.
- Add a fifth smoke test, **Unknown file**: the oracle export plus one extra row in the synthetic
  `files.csv` whose `file_name` is `chb06_99.edf`. Expected result: the run stops with
  `ScorerInputError` and writes nothing.
- Run `python src/eval_application_events.py --smoke`. All five tests must pass. Paste the verdict lines.
- Commit `src/eval_application_events.py` alone. Message: `Scorer: fail fast on file names absent from the annotation`.

## 2. Figure 3.5 (`figures/fig3_9_attribution_rank_heatmap.png`): number seizures from 1

The row labels render as `"chb03 sz0"`, `"chb03 sz1"` and so on, counted from zero. Appendix Table A.2
numbers the same seizures from 1 within each patient (chb03 seizure 1 is `chb03_01`, onset 362 s). A
reader matching a row of the figure to a row of the table is off by one.

- In `src/figures/attribution_figures.py`, function `fig3_rank_heatmap()` (row labels at about lines 175
  and 199–200), render each row as `"{subject} {n}"` with `n` counted from 1 in the same order, keeping
  the `"  (gen.)"` suffix for generalized seizures. Example: `"chb03 1"`, `"chb06 1  (gen.)"`.
- First confirm that the row order is the same as the order of Table A.2: patient, then seizure onset
  within the patient. Read `results/attribution_v7/rank_readout_perseizure.csv` or whichever file the
  function reads, and state which it is. If the order differs from onset order, stop and report; do not
  reorder anything.
- Change nothing else: not the data, the colour map, the size or the dpi. Keep this function's own
  colours; do not switch it to `palette.py`.
- Regenerate only this figure. Before overwriting, save the old PNG to
  `figures/archive/fig3_9_attribution_rank_heatmap_zero_based.png`. Confirm that the underlying rank
  matrix is identical to what the old version drew: compute it with the function's own code path and
  compare element-wise with the committed source data.

## 3. Figure A.7 (`figures/fig3_10_diffuseness.png`): American spelling

The report uses American spelling throughout. In `src/figures/fig3_15_diffuseness.py`, the y-axis label
(about line 75) reads `"Diffuseness (normalised entropy of the 18 scores)"`. Change `normalised` to
`normalized`, nothing else, and regenerate this figure only. Archive the old PNG as
`figures/archive/fig3_10_diffuseness_british.png`.

## 4. Checks and commit for 2 and 3

- `ls figures/*.png | wc -l` must still print 21.
- Commit the two generators and the two PNGs, listing each path explicitly. Message:
  `Figures 3.5 and A.7: one-based seizure labels, American spelling`.

## Report back

Write the report to `F:/Study/Thesis/Agent/cc_reports/SCORER_AND_LABELS_FIX.md` and print its path.
Include: the five smoke-test verdict lines; the source file and row order for Figure 3.5 with the first
five and last five rendered labels; the element-wise comparison result; both commit hashes.
