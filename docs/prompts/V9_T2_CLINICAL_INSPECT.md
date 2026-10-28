# V9-T2 — Hospital EEG files: privacy-safe inspection (Claude Code, laptop)

Estimated runtime: 10–20 min (estimated, not measured). Reads headers and a few minutes of signal only.

## Context
- Two EDF files from a hospital, use approved: one ≈ 2.46 GB, one ≈ 0.47 GB. **No seizure annotation is known.**
- The question for the thesis: can the final system run on them, and is there anything (embedded annotations, montage, quality) that lets us evaluate or show something to the committee?
- Files are at: `F:/Study/Thesis/Dataset/clinical/` (the author moves them there before starting; outside the repo).

## Privacy rules (strict)
- The file names and the EDF header contain the patients' names. **Never print file names, patient fields, recording fields or the start date.** Refer to the files as `clin01` (larger) and `clin02` (smaller) by size order.
- Write outputs only to `F:/Study/Thesis/Defense/clinical/` (outside the repo). Never copy these files or their outputs into the repo; never commit anything in this task.
- If annotation texts contain anything that looks like a name, an ID or a date, replace it with `[REDACTED]` before writing.

## Steps
1. Use `mne` (preload=False) or `pyedflib`, whichever is installed (check, do not install torch).
2. For each file write to `F:/Study/Thesis/Defense/clinical/clinXX_header.md`:
   - EDF or EDF+ (continuous / discontinuous); number of signals; every channel label; sampling rate per channel; physical unit; prefilter strings; duration (h); number of data records.
   - **EDF+ annotations** (`EDF Annotations` channel): total count, every distinct text with its count, and the onset (seconds from file start, not clock time) of any text that could be an event marker (e.g. seizure, sz, crise, co giật, event, spike, push button, marker, patient event).
3. Montage check: can the 18 bipolar channels of the thesis be built from these electrodes?
   `FP1-F7, F7-T7, T7-P7, P7-O1, FP1-F3, F3-C3, C3-P3, P3-O1, FP2-F4, F4-C4, C4-P4, P4-O2, FP2-F8, F8-T8, T8-P8, P8-O2, FZ-CZ, CZ-PZ`
   (old names: T3=T7, T4=T8, T5=P7, T6=P8). List missing electrodes, if any.
4. Signal quality on 3 slices of 5 minutes (10 %, 50 %, 90 % of the file): per channel median absolute amplitude (µV), share of flat samples, share of clipped samples, 50/60 Hz line-noise power ratio (Vietnam mains is 50 Hz; the thesis notch is 60 Hz — report what you see).
5. Do not run the thesis model yet. Just answer: what would have to change to run the final system on these files (resampling, montage, notch frequency)?

## Return format (paste back to the thesis chat)
Per file: format · duration · fs · channels present/missing for the 18 bipolar pairs · annotation summary (distinct texts and counts, event-like markers with onsets) · quality summary · what must change to run the system.
