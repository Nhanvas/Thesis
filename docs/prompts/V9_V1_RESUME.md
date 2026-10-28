# V9-V1-RESUME — finish the EEG evidence task without freezing the laptop (Claude Code, laptop)

The first run of `docs/prompts/V9_V1_EEG_EVIDENCE.md` froze the laptop and it restarted. Same task, same rules, but run it **light and resumable**.

## Step 0 — state (no computing)
List what the crashed run left: which parts/figures/CSVs exist under `results/v9_v1/` and `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/`, and whether `src/v9_eeg_evidence.py` exists and is complete. Keep finished outputs; do not redraw them.

## Memory rules (binding)
- **Never preload a whole EDF.** Open with `mne.io.read_raw_edf(path, preload=False)` and read only the needed span (`raw.get_data(start=..., stop=...)`) plus the filter padding that `filter_window_mem` / `preprocessing.filter_window` uses; verify on one segment that the result equals the pipeline filter (max-abs difference reported).
- For descriptors needing 10 min of background, read that span alone; never a whole file.
- One recording open at a time; `del` + `gc.collect()` after each; matplotlib: `plt.close(fig)` after each save, `matplotlib.use("Agg")`.
- No multiprocessing. Run each **Part as its own OS process** (`--part 1` … `--part 6`), resumable with a per-item cache (`results/v9_v1/_parts/`), and print peak RAM per part (`psutil`). If peak RAM of any process passes 8 GB, stop and report.
- Order: Part 3 (web-demo events), Part 4 (false-alarm types), Part 5 (model comparison), Part 6 (attribution), Part 2 (Siena vs CHB-MIT), Part 1 (descriptors, largest). Smoke each part on one patient first.

## Also, before Part 1
`V9_E4` showed that the literature definition "mean seizure duration < 30 s" (chb06, chb14, chb16) does **not** separate hard cases well: chb14 is 8/8 while chb13 (1/12, median 54 s), chb15 (6/20, median 94 s), chb12 (7/26) and chb21 (1/4) fail. In Part 1 therefore also mark, for every CHB-MIT case, the per-case sensitivity of B4 (leave-one-case-out k, `results/v9_e4/`) and report the descriptors of the six low cases (sensitivity < 0.35: chb06, chb12, chb13, chb15, chb16, chb21) against the rest — descriptive only.

## Before starting
Ask the author to close Chrome/Edge/Cursor and other heavy apps.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_V1_REPORT.md` as in the original prompt, plus peak RAM per part. Commit `src/v9_eeg_evidence.py` and `results/v9_v1/` (explicit paths; not `_parts/` caches if they are large — say their size).
