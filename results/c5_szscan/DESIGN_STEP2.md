# DESIGN — SzScan Step 2 (chat C5): any EDF, two engine modes, action log

*Written 24/11/2026 by chat C5 before any Step 2 code is run; approved scope: author 24/11 20:19 (points 1–5) and 20:43
(two modes, default session). Step 1 evidence: `results/c5_szscan/VERIFY.md` (V1–V7 PASS on 231 files, 279.4 h).
SzScan is a demonstration prototype of the model (author 24/11): nothing in it is tuned per subject or dataset, and it
never reads seizure annotations (integrity rule 8).*

## 1. What changes and why

| # | change | evidence that asks for it |
|---|---|---|
| C1 | **Any CHB-MIT case, chb24, Siena and hospital EDF accepted**; the subject-id allowlist (`db.ALLOWED_SUBJECTS`) is removed | V7 U1: the defense error was the allowlist rejecting `chb01`; author 24/11 18:36 |
| C2 | **Two engine modes**, chosen at upload, stored with the subject and shown on every screen and export: **session** (default) = the application chain of today on all files of the subject (label-free statistics pooled over the subject; V5 Section 3.6: 0.528 @ 26.9 FP/day on test, seed 42); **file** = the per-recording arm chosen by F2-03 (B-MCD-F: robust z-scale × `c_ch`, reweighted MCD 0.75, budget clip(q, 0.5 %, 2 %) per recording, k 9.914209, seed 42; recordings shorter than 30 min get no event, L3-short) | author 24/11 20:43; L2 (`results/m2l/l2/SELECTION.md`), L3-short (`results/m2l/l3short/T_L3SHORT.md`) |
| C3 | **Engine registry**: an engine = one module with `run(files, settings) -> events, scores, per-channel distances` and its own reproduction gate; F2-06's system, if it passes instructions §1 item 21, is added as a third entry; the (a) / (b) / (c) reference-context comparison is F2-06's task | §1 item 21; author 24/11 20:43 |
| C4 | **Input normalisation** (new `backend/edf_input.py`): bipolar CHB-MIT files as today; referential files → the 19 electrodes (names normalised, T3/T4/T5/T6 → T7/T8/P7/P8) → the 18 derivations by subtraction → `resample_poly` to 256 Hz — the construction of `x1_external.load_18` and of SzCORE's converter; only the 19 electrodes are read (hospital files hold 103 signals) | F-A1.1; `x1_external.load_18`; SzCORE data format (Dan et al. 2024, arXiv 2402.13005) |
| C5 | **Mains frequency per subject** (50 / 60 Hz), shown in the filter label (today fixed "60 Hz notch"); default suggested by a written spectral rule (§3), the user may override; the record used 60 Hz for CHB-MIT, 50 Hz for Siena and the hospital records | Step 1 V5; `x1_external` (`notch=60.0` chb, `50.0` siena), `v9_clinical_run.NOTCH = 50.0` |
| C6 | **Truncated files**: when the header declares more records than the file holds, the records present are used and a visible notice states the declared and the present duration (durations only) | V7 U8 (accepted silently); F-A1.1 (first hospital record: header 22.8 h, file 13.2 h) |
| C7 | **Bad electrodes** (referential inputs only): a written rule (§3) marks an electrode bad; it is interpolated by spherical splines as in `v9_clinical_run` and named in a notice; bipolar inputs: derivations are only flagged, never changed. Adopted as default only after its counts on CHB-MIT / Siena are seen (G5). Hypothesis (synthetic test, 25/11): a pure robust-z rule flags an electrode only 3 % above the median when all electrodes have almost the same amplitude (z 5.5); G5 now reports each flagged electrode's amplitude ratio to the median, which checks this on real data | F-A1.1 (artifactual C3 interpolated in the thesis run); PREP (Bigdely-Shamlo et al. 2015, DOI 10.3389/fninf.2015.00016); spherical splines (Perrin et al. 1989, DOI 10.1016/0013-4694(89)90180-6) |
| C8 | **Upload streamed to disk** in 1-MB chunks (`shutil.copyfileobj` from `UploadFile.file`) instead of `await file.read()`; Phase A measured on the longest file; if its peak exceeds 2 GB, filtering in overlapping chunks (≥ 60 s padding) with an equality gate. **Fix (25/11, logged before the gates are rerun):** the smoke measured 15.1 GB traced on the largest Siena file (11.7 h, 512 Hz), all in the reader (whole-recording copies); the cause was verified on a synthetic file before the fix. The reader now reads the electrodes in 600-s blocks into a disk copy, resamples and filters one derivation at a time and writes the Phase A arrays straight to their cache files (no chunked filtering needed: each derivation is filtered whole); the bipolar reader drops one redundant copy. Equality: synthetic test E10 (exact; interpolation matrix = MNE whole-recording interpolation) and G3 against `load_18`'s operations derivation by derivation. Synthetic 4-h 512-Hz file: 123 MB traced for reading and for Phase A (`load_18` alone 3,248 MB) | V7 U10 (whole file in memory; Phase A 797 MB per hour of EEG traced); laptop RAM (author 24/11 20:19) |
| C9 | **Private sessions** (option at upload; on for hospital files): the original file name (it holds the patient's name, `LOCAL_LAYOUT.md`) is never stored — files and caches get neutral names `<subject>_recNN`; no header field (patient, recording, date) is stored, shown, logged or exported; the time axis shows elapsed time from the recording start | integrity rule 7 |
| C10 | **Action log** (append-only table `audit_log`): time (UTC and local), actor, action, subject, file id, event id, detail — login ok / failed (username only), logout, session create / discard, upload (neutral name, size, sha256), file opened / closed, review decision changed (old → new), human event created / edited / deleted, channel judgement changed, export; an export of the log as CSV. Login stays a demo gate (127.0.0.1 only) | Step 2 status check (24/11 20:19): no audit trail, `demo_backend.log` overwritten at each start, decisions stored without time or actor; the meeting (Step 3) needs decision times |
| C11 | **Cache size**: 0.233 GB per hour of EEG (65 GB / 279.4 h, computed); all CHB-MIT + Siena ≈ 1,120 h ≈ 260 GB (computed). Options for the author: (a) keep the cache and ingest only the subjects he chooses (upload more during the demo); (b) read the raw display signal from the EDF copy (memory-mapped) instead of `raw.npy` (saves about 66 MB per hour, computed) — Step 1's V3 then runs on the new path | Step 1 cache; `LOCAL_LAYOUT.md` (286 GB free on 17/11) |
| C12 | **How good each subject is** is shown outside the app: `src/c5_score_app.py` scores the app's exported events against the annotations (SzCORE `timescoring`, the application-tier scorer `src/eval_application_events.py`) per subject, both modes, every CHB-MIT case and Siena; training patients marked "seen in training" | integrity rule 8; author 24/11 18:36 (the council will ask) |

Not changed: the session chain itself (code of `pipeline_demo.py` Phase A / B / events), the display (Step 1 PASS), the
login mechanism beyond logging.

## 2. Literature and reference tools (instructions §1 item 14)

Peer-reviewed: Bigdely-Shamlo et al. 2015, *The PREP pipeline: standardized preprocessing for large-scale EEG analysis*,
Front. Neuroinform. 9:16, DOI 10.3389/fninf.2015.00016 — noisy-channel detection by robust deviation, correlation and
high-frequency noise, then interpolation; its deviation criterion is the basis of §3 (applies: referential inputs).
Perrin et al. 1989, *Spherical splines for scalp potential and current density mapping*, Electroencephalogr. Clin.
Neurophysiol. 72:184–187, DOI 10.1016/0013-4694(89)90180-6 — the interpolation MNE implements (applies, as in the
thesis run). Halford et al. 2016, *ACNS Guideline 4: Recording clinical EEG on digital media*, J. Clin. Neurophysiol.
33:317–319, DOI 10.1097/WNP.0000000000000318 — display of digital EEG (filters and time base shown). Koren et al. 2021,
Epilepsia 62:426–438, DOI 10.1111/epi.16812 — commercial detectors are run on whole long-term recordings and differ by
their operating point (context for the two modes). Code / benchmarks: SzCORE (Dan et al. 2024, arXiv 2402.13005;
github.com/esl-epfl/szcore; challenge report arXiv 2505.18191: one EDF in, one TSV out, files ≥ 1 min, mostly ≈ 1 h,
19 electrodes common average at 256 Hz) — the file mode is the mode a SzCORE submission needs; pyprep (python port of
PREP) for the default thresholds; FastAPI / Starlette `UploadFile` (spooled temporary file; streaming to disk).

## 3. Written rules (fixed before any run)

- **Mains suggestion:** on every 10th 4-s window of the 19 electrodes (or the 18 derivations), Welch power in 49.5–50.5
  Hz and 59.5–60.5 Hz, each divided by the median power of 45–49 Hz and 51–55 Hz (resp. 55–59, 61–65 Hz); the larger
  median ratio wins; ties or both ratios < 3 → no suggestion (the user must choose). Shown with its two ratios.
- **Bad electrode (referential inputs):** robust amplitude of each of the 19 electrodes = IQR / 1.349 of its band-passed
  signal over every 10th 4-s window; robust z across the 19 electrodes = (amp − median) / (1.4826 × MAD); bad if z > 5
  (PREP's deviation default) or amp < 0.1 µV (flat). More than 3 bad electrodes → no interpolation, the file is refused
  with a notice. The rule runs on the whole file.
- **Truncated header:** records used = min(declared, present in the file); notice when they differ.
- **Duplicate labels:** the first signal with a label (as `preprocessing.open_edf` and SzCORE's converter).
- **Minimum length (file mode):** 30 min of valid signal (L3-short); shorter → no event, with a notice.

## 4. Gates (verification; every file, every channel, both modes; laptop runs ≤ 2 GB measured)

| gate | what | pass |
|---|---|---|
| G1 | session mode on the 8 test patients after the refactor | events = the committed export `web_demo/report_handback/tier2_v4/` (exact) |
| G2 | file mode, seed 42, on the test patients, chb24 and Siena | per-recording tp / fp / events = F2-03's committed L3 seed-42 rows of B-MCD-F (exact counts; waits for L3) |
| G3 | input normalisation | Siena (all 14 patients) through `edf_input` = `x1_external.load_18`, max relative difference ≤ 1e-9; CHB-MIT bipolar unchanged (Step 1 V1–V5 re-run on every ingested subject) |
| G4 | mains suggestion | reported per dataset: CHB-MIT files suggested 60 Hz, Siena 50 Hz, no suggestion — counts (a suggestion, not a gate on the user) |
| G5 | bad-electrode rule | counts per dataset (Siena files and electrodes flagged; CHB-MIT n/a); default ON only if the author accepts after seeing them; hospital: counts only, in a private report |
| G6 | memory | peak RSS while ingesting the longest CHB-MIT and the longest Siena file; ≤ 2 GB or chunked filtering, then chunked = whole-file ≤ 1e-3 µV on every test file |
| G7 | action log | synthetic test: each action writes exactly one row; updates / deletes of the table refused; the CSV export equals the table |
| G8 | privacy | synthetic hospital-like EDF with a fake person name in its file name and header: the name, the header fields and the date appear nowhere — database, cache file names, API responses, action log, exports, backend log (grep) |
| G9 | Step 1 re-run | `src/c5_szscan_verify.py` extended to both modes and the new inputs; its smoke on the longest file; memory streamed per channel |

Every gate has a synthetic test with a failing case (as Step 1: 26 / 26). Code is written and tested in this chat;
Claude Code installs it from the zip and runs the tests and gates on the laptop through a prompt.

## 5. Order and cost

S2a (no L3 needed): C1, C3–C10 code + frontend (mode, mains, private option, notices, elapsed time) + synthetic tests →
laptop: install, tests, G1, G3, G4, G6–G9 on the 8 test patients and Siena. S2b: ingest of the subjects the author
chooses (C11), G5 counts, `c5_score_app.py` (C12). S2c (after F2-03 commits L3): G2. Costs measured, not estimated: the
app's ingest rate (12.3 s per hour of EEG with two workers, `web_demo/BUILD_PROGRESS.md`) gives ≈ 3.3 h for all of
CHB-MIT and ≈ 0.5 h for Siena (computed).
