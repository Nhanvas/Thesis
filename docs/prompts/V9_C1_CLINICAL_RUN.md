# V9-C1 — Run the final system on the two hospital EEG files (qualitative, privacy-safe) (Claude Code, laptop)

Estimated runtime: 30–60 min (estimated, not measured).

## Why
No clinician can review the output, and there is no seizure annotation. What we can show honestly: (1) the system runs on real hospital EEG from Vietnam; (2) what share of the recording it flags (review burden); (3) how it reacts to known non-seizure events annotated by the technician in clin02 (eyes open/closed, hyperventilation, photic stimulation) and to the 7 "Spike" markers; (4) what the flagged segments look like. This answers the committee's questions on clinical data and on "artifacts/normal states vs seizures". No metric of seizure detection is claimed.

## Inputs
`F:/Study/Thesis/Dataset/clinical/` — `clin01` (larger, 13.2 h real data, header truncated) and `clin02` (smaller, 1.25 h, 512 Hz, activation protocol). Facts in `F:/Study/Thesis/Defense/clinical/clin0X_header.md`.

## Privacy rules
Same as `V9_T2`: never print or write names, file names, patient/recording header fields or dates; outputs only in `F:/Study/Thesis/Defense/clinical/run/`; nothing from this task enters the repo except the new script; never commit outputs.

## Processing (reuse, do not re-implement)
- Reuse the external-data path of `src/x1_external.py` (referential → 18 bipolar with T3/T4/T5/T6 aliases, `resample_poly` to 256 Hz, **notch at 50 Hz** as for Siena, label-free z-score statistics, CAR, graphs, frozen GAE seed 42, frozen score chain, per-patient budget, merge, CPD). New wrapper `src/v9_clinical_run.py`; do not edit frozen files.
- clin01: read by the real sample count (truncated header).
- clin02 channel C3 is artifactual (amplitude 5–10× others, extreme 50 Hz). Run twice: (a) C3 interpolated from neighbours (MNE spherical spline on the referential data before the bipolar build), (b) as recorded. Report both; (a) is the main run. Say which bipolar pairs use C3 (F3-C3, C3-P3).
- Disclose: clin02 is only 1.25 h, so the per-patient fits (statistics, budget, ±15-min correction) rest on little data.

## Outputs (`F:/Study/Thesis/Defense/clinical/run/`)
1. `events_clinXX.csv`: every system event (start, end, duration, peak score).
2. Flagged-time fraction per file (system events' total duration / recording duration).
3. clin02: overlap table of events with each annotated segment type (eyes open/closed, HV phases, photic steps, spike marker ± 10 s), with the share of recording time each type occupies (chance level).
4. Score timeline figure per file with the annotation segments shaded and system events marked.
5. EEG panels (same drawing convention as `src/v9_eeg_samples.py`, 18 bipolar channels, real signal): every event of clin02; the 10 highest-score events of clin01; plus 3 panels around spike markers.
6. `SUMMARY.md`: numbers + 5–8 plain observations of what is visible, no diagnosis.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_C1_REPORT.md`.
