# C5 → C5b hand-off (SzScan for the Euréka final and the meeting with Dr. An)

*Written 25/11/2026 by chat C5 when the chat grew long (author 25/11 13:34). Public file: no hospital name, file name,
header field or date appears here. Design of Step 2: `results/c5_szscan/DESIGN_STEP2.md` (rows C1–C12, rules §3,
gates §4, order §5).*

## 1. Task of C5 (start prompt, 24/11) and where it stands

| step | content | state |
|---|---|---|
| 1 | Verify SzScan as it was (R216 checklist: original EDF, 18 bipolar derivations by name and order, µV, time stamps and durations, filter shown, the EDF upload error of the defense) | **done, PASS** — `results/c5_szscan/VERIFY.md` (V1–V7 on 231 files, 279.4 h; commit `1891bee`); the defense error = the subject allowlist rejecting `chb01` |
| 2a | Code: any EDF (C1), two engine modes (C3: session = V5 chain, default; file = SzScan 1.0 B-MCD-F), input normalisation (C4), mains per study with a spectral suggestion (C5), truncated-header notice (C6), bad electrodes (C7), streamed upload and memory-light reading (C8), private studies (C9), action log (C10) | **code done and tested** (synthetic test 33 / 33, backend pytest 15 / 15, frontend build) — commits `8b3f9b1`, `21ef792`, `d322357` and the C5 close-out commit; **real-data gates G1, G3–G6 not yet run to the end** (see §3) |
| 2b | Ingest the chosen cases into the app (C11); G5 counts read with the author; offline scoring per subject `src/c5_score_app.py` (C12); G9 = Step 1 verifier extended to the new inputs and both modes | not started |
| 2c | G2: file mode, seed 42 = F2-03's committed L3 rows (`results/m2l/l3eval/per_file.csv`, `budget == B-MCD-F`, `seed == clean_seed42`: events, q, top, short per recording) | not started (L3 committed 25/11, `8d21a0b`) |
| 3 | Meeting with Dr. An designed for evidence (literature first): blinded review of 16–22 clips of 30–60 s from the two hospital recordings (flagged by a written rule + random controls, shuffled, no score shown), classes likely ictal / epileptiform non-ictal / artifact (type) / normal / uncertain with confidence 1–5; structured interview (usefulness, which false alarms disturb, acceptable alarm budget, what the review screen lacks; **workflow questions approved 24/11**: one continuous file or many files, session length, read during or after the recording); optional reading-time comparison (plan §15 stream H); clip set, form, order; consent and data-use points (who provided the data, permission — semi-final judge 2; status recorded in R233 (d)) | not started |
| 4 | After the meeting: results as "exploratory expert review" (never clinical validation, no sensitivity claim) handed to C8 through `TRACKS_PROGRESS.md` | not started |

## 2. Author's decisions in C5 (24–25/11)

- The repository stays public until the author announces the switch (now in instructions rev ag).
- Every hypothesis is checked with evidence, then fixes are decided together.
- SzScan must accept every EDF: all CHB-MIT cases (training and validation included), chb24, Siena, hospital records.
  It is a demonstration prototype: nothing is tuned per subject or dataset; it never reads annotations.
- Two engine modes, **session (default)** and **file**; the Euréka final demo is the priority.
- Whole-session vs per-file vs cumulative reference is **not decided** — the comparison (a) per file, (b) whole session,
  (c) cumulative reference is a task for **F2-06** (added to its start prompt).
- The cases to ingest are chosen by C5 ("show the best", author 24/11): chb24; validation chb10, chb11, chb22; all 14
  Siena patients (mains 50 Hz or the suggestion); the two hospital records as private studies (engine mode decided in
  Step 3); the 8 test patients are already in the app. Training patients may be added for the council (marked "seen in
  training" in C12's table).
- Every command given to the author is one line (no backslash continuations).
- If the chat grows long, a new chat continues after the step is finished and the project is updated.

## 3. Memory on the laptop (what happened, what is in place)

1. First smoke (Step 2a): the reader peaked at 15.1 GB on the largest Siena file (11.7 h, 512 Hz) — whole-recording
   copies. Fix 1 (`21ef792`): block reading into memory-mapped disk copies.
2. Second smoke: stopped for low system memory. Cause verified (here, Linux): memory-mapped pages stay in the process's
   physical memory and are invisible to the traced heap (4-h file: resident file pages +1.5 GB, heap +122 MB).
   Fix 2 (`d322357`): no memory map — each derivation reads its two electrodes over the whole file and is written with
   ordinary file writes; Phase A per channel, caches assembled in blocks of 512 windows. Synthetic 4-h 512-Hz file:
   826 → 1,031 MB resident during Phase A. Exactness: test E10 and gate G3.
3. Third smoke: Claude Code itself stopped the run (its background commands are stopped when the system reports memory
   pressure; the second attempt died during the imports at about 440 MB). G1 (chb16) completed: 0 files differ, 692.7 s
   for 19.0 h, resident 1,948 MB, traced heap 495 MB (the rest are cache pages Phase B reads, reclaimable).
   Adjustment (C5 close-out): the watchdog limits **private** memory to 2 GB; resident is recorded; **the author runs
   the gates in his own Git Bash terminal**, not through a Claude Code background command.
4. Not yet measured: Phase B in **file** mode on long Siena recordings (F2-03 measured 0.81 GB per hour at 512 Hz for
   the whole m2l chain on Kaggle — SzScan's file mode runs on its cached features, so its memory must be measured at
   ingest, Step 2b).

## 4. Open findings to read with the author

- **Bad-electrode rule (C7):** on synthetic data a pure robust-z rule flagged an electrode only 3 % above the median
  (z 5.5) because all electrodes had almost the same amplitude. Hypothesis for real data; G5 now reports each flagged
  electrode's amplitude ratio to the median — read it before the rule becomes a default.
- **Mains on synthetic referential data:** a line identical on every electrode cancels in the bipolar differences, so the
  suggestion needs a line that differs between electrodes (real recordings do); G4 counts show the real behaviour.

## 5. Next actions (C5b)

1. Read the author's gate run: `results/c5_szscan/step2/` (smoke first, then the full run), `Agent/inbox/C5_STEP2_GATES.log`
   (the author pastes the last lines), and only whether `Agent/inbox/C5_STEP2_PRIVATE.md` exists (its content stays on
   the laptop; the author reads it himself or reports counts only).
2. Then Steps 2b → 2c → 3 → 4 as in §1.
3. At the end: `TRACKS_PROGRESS.md` (Track C, C5 row; hand-off to C8), the board, the project update list, one zip.
