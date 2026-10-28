# V9-T3 — Where and why the final system fails; why Siena looks better (Claude Code, laptop)

Estimated runtime: Part A 30–90 min, Part B 30–60 min (estimated, not measured). Measure Part A's first subject and report the projected total before running all.

## Context
- Final system = P3 frozen (`p3c_freeze.py`, `e23_test_look7.py`; external run `x1_external.py`). Seed 42 is the headline.
- The supervisor and the reviewer asked: (1) why the 8 test patients are "hard" — show it with **real EEG**, not words; (2) why Siena scores higher than CHB-MIT test ("something strange"); (3) what the false alarms actually are (artifact? state change?).
- Leads already in committed files (verify, do not trust):
  - `results/p3_anatomy/seizures.csv` (seed 42, pre-budget detector): test has 24 seizures ≤ 20 s (7 caught); the non-test development patients have only 3 such seizures.
  - Reachability in `results/p3_anatomy/SUMMARY.md`: most test seizures rank within the patient's top 2–10 % of windows, but only about a third within the top 0.5 %.
  - `results/application_eval_v4/per_subject.csv`: chb06 1/10, chb13 1/12, chb16 1/10 detected; chb03, chb14, chb17, chb18 ≥ 0.75.
  - `results/x1_external/SUMMARY.md`: Siena has only 3 short seizures out of 47; 6 of 14 Siena patients have ≤ 2 seizures; Siena FP/day ≈ 41–44 vs CHB-MIT test 27.5.

## Rules
- Read-only on every committed result and frozen script. New code: `src/v9_anatomy.py` (Part A) and `src/v9_eeg_samples.py` (Part B). New outputs: `results/v9_anatomy/` and `F:/Study/Thesis/Defense/slides/figs/eeg_samples/`.
- Reuse the frozen functions and caches (`results/p2_test/`, X1 caches); **do not refit or retrain**. If a needed cache is missing, stop and report what is missing and how long recomputing would take.
- Label use is for evaluation and for picking which events to draw, never for tuning.
- Another Claude Code terminal may work in `web_demo/`: do not touch it. Commit only your own new paths, explicitly staged.
- Smoke first (`--smoke` = one subject per set).

## Part A — numbers (`results/v9_anatomy/`)
1. **Per-seizure table**, final system, seed 42, after the localizer, for CHB-MIT test (8), chb24, Siena (14): subject, file, onset, duration, caught (y/n), the seizure's best score rank within its patient (top-p needed), number of channels with high amplitude, file position.
2. **Detection by duration bin** (≤ 20 s, 21–40, 41–80, > 80 s) for: development (train+val) patients, CHB-MIT test, chb24, Siena. Counts, not only rates.
3. **Matched operating point.** Sweep one global alarm budget (characterisation grid, e.g. top-p 0.001 → 0.05, same smoothing, merge, scorer; detector stage is fine, say so) and plot sensitivity (pooled and per-patient mean) against FP/day for CHB-MIT test, chb24 and Siena on the same axes. Report each set's sensitivity at 20, 27.5 and 44 FP/day (interpolated, labelled as such).
4. **Siena aggregate check:** per-patient mean with and without patients that have ≤ 2 seizures; pooled vs per-patient mean; seizures per patient.
5. **False-alarm anatomy** (seed 42, CHB-MIT test and Siena): for every false alarm: duration, peak score, position in file (first 15 min / middle / last 15 min), share of high-amplitude (±5 SD) windows, top channels, distance to the nearest seizure. Summarise into a few data-driven groups (do not invent categories you cannot measure).
6. `results/v9_anatomy/SUMMARY.md`: tables plus 5–8 plain findings, each with its number and file. Mark everything computed here as "computed in v9".

## Part B — real EEG figures (`F:/Study/Thesis/Defense/slides/figs/eeg_samples/`)
Selection rule, fixed **before** looking at any picture (write it at the top of the script and in `selection.csv`):
- CHB-MIT test, per patient: the true detection with the highest score; the missed seizure closest to the patient's median seizure duration; the false alarm with the highest score.
- Siena: same rule for the 4 patients with the most seizures; plus the shortest seizure overall.
Drawing (reuse the signal convention of `src/raw_eeg_view.py` — `filter_window_mem`, bit-exact with the pipeline):
- 18 bipolar channels, real signal, same µV scale within a figure, 60 s around the event (more if the event is longer), shaded annotation (grey) and system event (teal), the ensemble score as a strip under the traces, time axis in seconds from the event start. Title: patient · file · TP/FN/FP · duration. No calendar dates.
- PNG at 200 dpi plus one contact sheet per set. No AI drawing, no smoothing of the traces beyond the pipeline filter.

## Return format (paste back to the thesis chat)
- Part A: the SUMMARY.md findings (numbers + file) and the matched-operating-point table.
- Part B: number of figures, path, `selection.csv`, and 3–5 sentences describing what the missed seizures and the top false alarms look like on the EEG (morphology, amplitude, channels), without interpreting beyond what is visible.
