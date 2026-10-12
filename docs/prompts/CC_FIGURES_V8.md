# CC_FIGURES_V8 — data for Figures 12 and 14 of the v8 report (Claude Code, laptop)

**Estimated runtime: 25–50 min in total (estimated, not measured)** — per-seizure export 10–30 min
(8 test patients × 4 seeds, cache-based), gallery EEG 2–5 min, Siena panel 5–15 min if its EDF files are
on this machine. Close Chrome, Edge and other heavy programs first (chb06 needs ~10 GB).

Read first: `web_demo/CLAUDE.md` is NOT relevant here; read `docs/PROJECT_INSTRUCTIONS.md` §6 (integrity
rules) and `docs/writing/REPORT_OUTLINE_v8.md` §3 (3.3.3, 3.3.5) and §5. Code style: explicit `sys.path`
block, fail-fast, `--smoke`.

## Ground rules

1. **Nothing in the frozen system changes.** You only call the frozen functions (tag `p3-frozen`):
   `e22_test_oneshot.test_context / final_scalar`, `p2_scalars.smoothed / d1_events / score`,
   `p3_levers.q_of / member_mean_z / refs_of / localize`, `results/p3c_freeze/freeze.json`. Pattern to copy:
   `src/figures_v6/fig_example_chb03.py export()` (it already reproduces chb03 exactly).
2. **Every export is gated** against committed results; on any mismatch: STOP, write the mismatch in the
   handback, change nothing else.
3. Figures never recompute (rule 13): the export writes data files; the plot scripts that already exist in
   `src/figures_v8/` read them.
4. Stage explicit paths only; never `git add` a directory.

## Step 1 — `src/figures_v8/export_v8_data.py perseizure`

For each test patient (chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18) and each seed
(clean_seed42, clean_seed1, clean_seed2, clean_seed3):
- final system: budget `clip(q, 0.005, 0.02)` (freeze.json "balanced"), detector → `localize(..., "cpd")`;
- held-out evaluation: the same with floor = cap = 0.005;
- for every annotated reference seizure (`refs_of(ctx)`), `detected_final` / `detected_heldout` = 1 if a
  localized event matches it **under the scorer's rule** (SzCORE: 30 s before onset, 60 s after offset,
  events merged < 90 s). First try the overlap rule of `p2_scalars.caught`; if, for any patient and seed,
  the number of hits differs from the scorer's TP, score that file's references one at a time with the
  scorer (`p2_scalars.score` on a context with only that reference) and use those hits.

Write `results/figures_v8_data/perseizure_final.csv` with columns
`subject, seed, file, onset_s, offset_s, dur_s, detected_final, detected_heldout`
(file = EDF name; times in seconds within the file; dur_s = offset_s − onset_s).

**Gates:** 76 rows per seed; for every subject and seed, sum(detected_final) = `tp` of
`results/e23_test_look7/per_subject_seed.csv` (point balanced, stage localized) and sum(detected_heldout) =
`tp` of `results/e22_test_oneshot/per_subject_seed.csv` (stage localized). Seed 42 totals 37 and 26.

## Step 2 — `src/figures_v8/export_v8_data.py gallery`

Write one `.npz` per panel to `results/figures_v8_data/gallery/` with exactly the keys listed in the
docstring of `src/figures_v8/fig14_gallery.py` (eeg float16 [18, n] at 128 Hz covering onset −10 s to
onset +20 s, clipped to the file; score_t/score/score_sm over ±300 s around the onset inside the file;
thr; thr_heldout; ann; det; loc; ch; eeg_t0; fs; title). EEG = the evaluation's own filtered, z-scored
signal (`continuous_eval.filter_file`, `continuous_eval.zscore` with the statistics the evaluation used),
decimated 256 → 128 Hz (`scipy.signal.decimate`, q = 2, zero-phase). Seed 42, final system.

Panels — chosen by these rules (fixed now, no other choice):
- **a** chb03: the first annotated seizure (by file order, then onset) → title `chb03: detected`.
- **b** chb15: the first seizure with detected_final = 1 and detected_heldout = 0 → title
  `chb15: detected with the per-patient budget`; set thr_heldout = threshold at budget 0.005.
- **c** chb16: the shortest seizure with detected_final = 0 (ties: first) → title `chb16: short seizure, missed`.
- **d** the final-system false alarm (seed 42, all 8 test patients) with the highest peak smoothed score
  and no annotated seizure within ±10 min (ties: first) → title `<subject>: false alarm`; ann = empty.
- **e** Siena PN10, its first seizure detected by the final system (seed 42), built with the frozen external
  path (`x1_external.build_subject` + `evaluate_ctx`, label-free statistics, 50 Hz notch) → title
  `PN10 (Siena): detected`. **Only if** the Siena EDF files are on this machine (path from the author:
  `<SIENA_DIR>`); otherwise skip panel e and say so in the handback.

**Gates:** for each CHB-MIT panel, the full-patient detector and localized tp/fp computed in the export equal
`results/e23_test_look7/per_subject_seed.csv` (seed 42); for panel e, PN10 tp/fp equal
`results/x1_external/rows_PN10.csv` (balanced, clean_seed42, localized). Each `.npz` < 3 MB.

## Step 3 — plots and commit

```bash
python src/figures_v8/fig14_gallery.py            # -> ../Reports/v8/figures/fig14_gallery.png
python src/figures_v8/make_v8_exhibits.py         # now also draws fig12_duration.png; all gates must pass
git add src/figures_v8/export_v8_data.py results/figures_v8_data/perseizure_final.csv \
        results/figures_v8_data/gallery/a.npz results/figures_v8_data/gallery/b.npz \
        results/figures_v8_data/gallery/c.npz results/figures_v8_data/gallery/d.npz \
        docs/prompts/CC_FIGURES_V8_HANDBACK.md      # + gallery/e.npz if it exists
git commit -m "figures v8: per-seizure detection file and gallery data (gated vs e22/e23/x1)"
git push origin main
```

## Handback — `docs/prompts/CC_FIGURES_V8_HANDBACK.md`

Measured runtime per step; gate table (subject × seed, tp expected vs got) for Step 1; the five chosen
events (subject, file, onset, duration, why chosen by the rule); panel e done or skipped; the printout of
`make_v8_exhibits.py` (detection by duration table); any deviation.
