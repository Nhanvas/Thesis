# V9-V1 — Real-EEG evidence for every claim the committee questioned (Claude Code, laptop)

Estimated runtime: 1.5–3 h (estimated, not measured). Single worker; one recording in memory at a time. Smoke on one patient first.

## Why
The supervisor asked that every claim be backed by **real EEG**, not words and numbers alone: why the 8 test patients are hard, why Siena scores higher, what the false alarms are (artifact?), what the web demo detected right and wrong, and how the model comparison differs on real signal. `V9_T3`/`V9_T4` drew per-patient TP/FN/FP panels; this task builds the rest as **measured, rule-selected** evidence.

## Common rules
- Drawing convention exactly as `src/v9_eeg_samples.py` (pipeline filter via `filter_window_mem`, 18 bipolar channels, same µV scale within a figure, annotation shaded grey, system event teal, ensemble score strip under the traces, time in seconds from event start, no calendar dates). No AI drawing, no extra smoothing.
- **Every selection rule is written at the top of the script and in `selection.csv` before any figure is drawn.** No hand-picking.
- Read-only on frozen scripts and committed results. New code `src/v9_eeg_evidence.py`; numbers to `results/v9_v1/`; figures to `F:/Study/Thesis/Defense/slides/figs/eeg_evidence/<part>/`. Commit only the script and `results/v9_v1/`.
- For slide use, also save each key figure in a **slide version**: 16:9, ≥ 14 pt labels, 8 channels max (the 8 channels with the highest per-channel score in that event, named on the axis), plus the full 18-channel version for backup.

## Part 1 — "Hard patients" measured, not asserted
Seizure descriptors (fixed now), computed for every annotated seizure in development, CHB-MIT test, chb24 and Siena 14:
- duration (s);
- amplitude ratio: median channel RMS during the seizure / RMS of the 60 s before onset;
- spatial extent: number of channels whose RMS ratio > 2;
- dominant frequency during the seizure (peak of the median-channel PSD, 1–30 Hz);
- background busyness: share of the 10 min before onset in high-amplitude (±5 SD label-free) windows.
Outputs: per-seizure CSV with caught / missed (frozen system G, seed 42, after the localizer); a figure of each descriptor by set (dev / test / chb24 / Siena) with caught vs missed marked; a gallery of the **median-duration seizure of every CHB-MIT patient** (dev and test side by side, same scale, 30 s before onset to 30 s after offset).

## Part 2 — Siena vs CHB-MIT on the signal
Same descriptors, Siena vs CHB-MIT test (distributions). Panels: for each set, the seizure closest to the set's median duration and the one closest to the set's median amplitude ratio.

## Part 3 — Web-demo (application run) events, right and wrong
Source: the exported events of the application run (`results/application_eval_v4/` manifest; find the event CSVs it hashes — do not re-run the app). Label each event TP/FP with the same scorer.
- Draw **every** TP event (expected 33) and, per patient, the highest-score FP plus 2 random FPs (`random_state=0`).
- One contact sheet per patient with all events of that patient (backup).
- If the demo database still holds the 8 test subjects, take real **SzScan screenshots** (Playwright, read-only, no code change, Unikey irrelevant) of one TP and one FP event view for chb03 and one other patient; if the database does not hold them, say so and skip — do not re-ingest.

## Part 4 — What the false alarms are (artifact question)
Use the event features f1–f5 already computed in `results/v9_e2/` for every FP of G (seed 42) on test and Siena.
- Fixed typing rule: assign each FP to the feature on which it is most extreme relative to the development TP distribution (percentile of f1 high-frequency share, f3 frontal-polar share, f4 single-channel dominance, f2 spatial extent); "unassigned" if none above the 90th percentile. Report the share of FPs per type.
- Two panels per type (the most extreme and the median member).
- "Look-alike pairs": in 4 test patients, the TP and the FP of the same patient with the closest peak score, drawn side by side at the same scale.

## Part 5 — Model comparison on the signal
On CHB-MIT test (seed 42, each arm at its own calibrated point, `results/v9_e1b/`): every seizure caught by F but missed by G, and every seizure caught by G but missed by F; draw up to 3 of each (shortest first), with both score strips (G and F) under the traces.

## Part 6 — Channel-level latent anomaly on real seizures (attribution, descriptive)
From `results/attribution_v8/` (read only) and the author's labels in `results/attribution_v7/labels/source/` (read only, never edit): one focal seizure where the top-scored channels match the annotated channels, one where they do not, one generalized seizure. Draw the EEG with a per-channel heat strip of the channel-level latent anomaly and the annotated channels marked. Caption: "XAI concordance, not localization". No new metric.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_V1_REPORT.md`: per part the selection rule, the numbers (descriptor table summary, FP-type shares), the list of figures with paths, and 3–5 plain sentences per part on what is visible (no interpretation beyond the trace).
