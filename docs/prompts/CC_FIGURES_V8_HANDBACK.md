# CC_FIGURES_V8 — handback (Claude Code, laptop, 2026-10-12)

Executed `docs/prompts/CC_FIGURES_V8.md` with `<SIENA_DIR> = F:/Study/Thesis/Dataset/siena` (only PN10's
EDF files are present on this machine). New file: `src/figures_v8/export_v8_data.py` (`perseizure` and
`gallery` subcommands). Nothing in the frozen system (tag `p3-frozen`) changed; only its frozen functions
were called (`e22_test_oneshot.test_context/final_scalar`, `p2_scalars.smoothed/d1_events/score`,
`p3_levers.q_of/member_mean_z/refs_of/localize`, `results/p3c_freeze/freeze.json`, and for panel e
`x1_external.build_subject/model_outputs/make_ctx`).

## Measured runtime per step

| step | command | measured |
|---|---|---|
| 1 | `export_v8_data.py perseizure` (8 subjects × 4 seeds) | 116 s (~2 min) |
| 2a | `export_v8_data.py gallery` (panels a–d, CHB-MIT) | 21 s |
| 2b | `export_v8_data.py gallery --siena <dir>` (panel e, PN10) | ~340 s to the gate STOP (labelfree stats 116 s + feature build 196 s + model/gate ~28 s) — not re-attempted |
| 3 | `fig14_gallery.py` | 2.2 s |
| 3 | `make_v8_exhibits.py` | 4.3 s |

Total ≈ 8 min (well under the 25–50 min estimate): the test set is small (8 subjects, 76 seizures) and
every evaluation is cache-based: no EEG is re-filtered except for the gallery's own display panels (4
CHB-MIT files + the Siena attempt).

## Step 1 gate table (subject × seed, tp expected vs got)

`n` = reference seizures for that subject; `final`/`held` = sum of `detected_final` / `detected_heldout`
in `results/figures_v8_data/perseizure_final.csv` (`got`) against `results/e23_test_look7/per_subject_seed.csv`
(point balanced, stage localized) and `results/e22_test_oneshot/per_subject_seed.csv` (stage localized)
(`exp`). Every one of the 32 subject×seed cells matched on the first pass (the overlap rule of
`p2_scalars.caught`); the per-reference exact-scorer fallback was never needed.

```
subject   seed  n  final_got  final_exp  held_got  held_exp
  chb03 seed42  7          7          7         7         7
  chb03  seed1  7          7          7         7         7
  chb03  seed2  7          6          6         6         6
  chb03  seed3  7          7          7         7         7
  chb06 seed42 10          2          2         2         2
  chb06  seed1 10          1          1         1         1
  chb06  seed2 10          1          1         1         1
  chb06  seed3 10          2          2         2         2
  chb13 seed42 12          1          1         1         1
  chb13  seed1 12          2          2         2         2
  chb13  seed2 12          2          2         2         2
  chb13  seed3 12          2          2         2         2
  chb14 seed42  8          6          6         6         6
  chb14  seed1  8          5          5         5         5
  chb14  seed2  8          6          6         6         6
  chb14  seed3  8          6          6         5         5
  chb15 seed42 20         11         11         0         0
  chb15  seed1 20         11         11         0         0
  chb15  seed2 20          9          9         0         0
  chb15  seed3 20         11         11         0         0
  chb16 seed42 10          2          2         2         2
  chb16  seed1 10          2          2         2         2
  chb16  seed2 10          2          2         2         2
  chb16  seed3 10          2          2         2         2
  chb17 seed42  3          3          3         3         3
  chb17  seed1  3          3          3         3         3
  chb17  seed2  3          3          3         3         3
  chb17  seed3  3          3          3         3         3
  chb18 seed42  6          5          5         5         5
  chb18  seed1  6          5          5         5         5
  chb18  seed2  6          5          5         5         5
  chb18  seed3  6          5          5         5         5
```

Overall: 304 rows (76 × 4), seed-42 totals `detected_final` = 37, `detected_heldout` = 26 — matches the
prompt's gate exactly. chb15 is 0/20 held-out at every seed (the per-patient budget is the whole effect
for this patient, consistent with record 9.2's chb15-at-the-cap finding).

## The five chosen events

| panel | subject | file | onset (s, in file) | duration (s) | why chosen |
|---|---|---|---|---|---|
| a | chb03 | chb03_01.edf | 360 | 56 | first annotated seizure, file order then onset |
| b | chb15 | chb15_15.edf | 1588 | 160 | first seizure with `detected_final=1`, `detected_heldout=0` (11 candidates tied on the flag; file order picks chb15_15) |
| c | chb16 | chb16_18.edf | 1908 | 8 | shortest seizure with `detected_final=0` (unique minimum at 8 s; seven other missed seizures are 12–16 s) |
| d | chb03 | chb03_23.edf | 2768 | 132 | final-system false alarm, highest peak smoothed score (0.999) among localized events with no annotated seizure within ±10 min, across all 8 test patients, seed 42 |
| e | — | — | — | — | **skipped** (gate mismatch, see below) |

Panel d's event is visibly a high-amplitude artifact in the EEG panel, consistent with the thesis's own
false-alarm-anatomy finding (record 9.2 / `results/p3b_diag/tail.csv`: file-level drift and high-amplitude
artifact own most false alarms).

## Panel e (Siena PN10) — skipped

PN10's EDF files are present at `<SIENA_DIR>/PN10/`. The frozen external path (`x1_external.build_subject`
→ `model_outputs` → `make_ctx`, label-free statistics computed once and reused via `stats_mode="json"` to
avoid reading the ~3 GB of EDF twice, 50 Hz notch) reproduced **tp = 7** (matches
`results/x1_external/rows_PN10.csv`, balanced/clean_seed42/localized) but **fp = 17 vs the committed 18**.
Per ground rule 2 ("on any mismatch: STOP, write the mismatch in the handback, change nothing else") the
run stopped there; `gallery/e.npz` was never written and `fig14_gallery.py` drew 4 panels. Not re-attempted
or tuned. Most likely cause: PN10's features were rebuilt fresh on this machine (no cached
`results/x1_external/features/*.npz` exists in the repository) under a different library stack than the
original Kaggle run (mne/scipy/sklearn versions) — tp matching exactly while fp is off by one is
consistent with one borderline interictal window flipping classification under a tiny floating-point
difference somewhere in the filtering/LedoitWolf chain, not a construction error (the held-out/final
construction itself is identical code, and the CHB-MIT panels, same code path, gated exactly on this same
machine).

## `make_v8_exhibits.py` — detection by duration (Figure 12)

```
          n  fin  held
bin
< 20     18    4     4
20–39    18    6     5
40–59     9    8     8
60–119   23   13     9
>= 120    8    6     0
```

Matches the outline's pre-stated reading exactly: "4 of the 18 seizures shorter than five whole windows
detected in both evaluations." `ALL GATES PASSED -> F:\Study\Thesis\Reports\v8`.

## Deviations

1. **Windows `mktime` platform bug (not a frozen-system change).** `x1_external.py`'s Siena annotation
   parser (verbatim from `epilepsy2bids`, written for Kaggle/Linux) calls `time.mktime` on a
   `time.strptime` result defaulted to year 1900; Windows' C runtime raises `OverflowError` for any
   pre-1970 date, Linux's does not. Worked around with a **scoped** monkey-patch of `time.mktime` inside
   `export_v8_data.py`'s `build_panel_e` only (restored in a `finally`, never left patched), replacing it
   with the HH:MM:SS-of-day arithmetic that is all `_substractTimeStamps` actually uses — numerically
   identical to the original for this use, platform-independent, and `x1_external.py` itself was not
   edited. Parsed PN10's 6 files / 10 seizures correctly (cross-checked against `Seizures-list-PN10.txt`
   by hand).
2. **A bug in the new export script, found and fixed before committing (not the frozen system).** The
   first `gallery` run wrote `d.npz` (the false-alarm panel) with its `det`/`loc` arrays in file order;
   `fig14_gallery.py`'s own `anchor()` takes time 0 from the *first* entry of `loc` (since `ann` is empty
   for a false alarm) — chb03's file 23 has other localized events earlier in the file, so the plot
   centered on the wrong one (blank EEG panel, score plot showing raw in-file seconds instead of
   time-from-onset). Fixed in `export_v8_data.py` (`_anchor_first`): the selected event is moved to the
   front of `det`/`loc` before saving. Re-ran steps 2 (CHB-MIT panels only) and 3; `fig14_gallery.png`
   checked visually and is now correctly centered on all four panels.
3. **Windows console `cp1252` encoding (cosmetic only, no file changed).** `make_v8_exhibits.py`'s final
   `print` of the duration table contains "≥", which the default Windows console codepage can't encode;
   the crash happens *after* every gate check and `fig.savefig` call, so `fig12_duration.png` and every
   table were already written correctly on the first run. Re-ran with `PYTHONIOENCODING=utf-8` (an
   environment variable, no code or file change) to capture the clean printout above.
4. `x1_external.build_subject` was called with `procs=2` (not its default 4) for panel e, to bound peak
   RAM on this 16 GB laptop given PN10's two combined files are 689–767 MB each (ground rule 17/laptop
   note already flags chb06 alone needing ~10 GB); peak observed RSS was ~1.5 GB per worker, well within
   budget. This does not affect the computed numbers (order-preserving, deterministic feature build).

## Files to commit

```
src/figures_v8/export_v8_data.py
results/figures_v8_data/perseizure_final.csv
results/figures_v8_data/gallery/a.npz
results/figures_v8_data/gallery/b.npz
results/figures_v8_data/gallery/c.npz
results/figures_v8_data/gallery/d.npz
docs/prompts/CC_FIGURES_V8_HANDBACK.md
```

No `gallery/e.npz` (gate mismatch, not written). `../Reports/v8/figures/fig14_gallery.png` and
`fig12_duration.png` are outside the repository (`F:/Study/Thesis/Reports/v8/`), per the usual split.
