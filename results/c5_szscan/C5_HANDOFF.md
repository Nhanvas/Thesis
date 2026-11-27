# C5 close-out: SzScan for the Euréka final and the review with Dr. An (hand-off to C8)

*Written 25/11/2026 by chat C5, updated 26/11 by C5b and rewritten 27/11/2026 by chat C5c at the close of C5 (author
27/11 10:30). Public file: no hospital name, file name, header field or date appears here. Design of Step 2:
`results/c5_szscan/DESIGN_STEP2.md` (rows C1–C12, G9); protocol of Step 3: `results/c5_szscan/step3/PROTOCOL_STEP3.md`.*

## 1. Steps and where they stand

| step | content | state |
|---|---|---|
| 1 | Verify SzScan as it was (R216 checklist: original EDF, 18 bipolar derivations by name and order, µV, time stamps and durations, filter shown, the defense upload error) | **done, PASS** — `VERIFY.md` (V1–V7, 231 files, 279.4 h; `1891bee`); the defense error = the subject allowlist rejecting `chb01` |
| 2a | Any EDF (C1), two engine modes (C3: **session** = V5 chain, default; **file** = SzScan 1.0, B-MCD-F, 30-min minimum), input normalisation (C4), mains per study (C5), truncated-header notice (C6), bad-electrode flag (C7), streamed upload and memory-light reading (C8), private studies (C9), action log (C10) | **done** — synthetic test 52 / 52 (E1–E12), backend pytest 15 / 15; real data: **G1 PASS** (8 test subjects, 231 files, 0 differ), **G3 PASS** (41 Siena files, sha256 = PhysioNet), G6 private peak 1,691 MB (`step2/GATES.md`); fix 4 for EDF+ (§3 item 9, `20c5172`) — the hospital records open |
| 2b | Ingest (C11), offline scoring per subject (C12), extended verifier G9, file-mode memory | **done** — 21 studies ingested (§4); `src/c5_score_app.py` gates **S0 PASS** (test, session mode = the committed application result) and **S1 PASS** (reference seizures per file = L3's rows, 316 files) → `step2/score_app/`; **G9 PASS** (`src/c5_verify2.py`: 407 files, 578.8 h, V1–V6) → `step2/g9/VERIFY2.md` (`13a0f7e`) |
| 2c | G2: file mode, seed 42 = F2-03's L3 rows (`results/m2l/l3eval/per_file.csv`, `budget == B-MCD-F`, `seed == clean_seed42`) | **done, PASS** on Kaggle (`C5_G2_CHB` 253 / 253 recordings, 1.32 h; `C5_G2_SIENA` 41 / 41, 0.86 h) → `step2/g2/` (`a896f4b`) |
| 3 | Meeting with Dr. An: blinded clips, demo, interview, consent | **protocol approved 27/11 10:30, material ready** (`step3/`, §5); **the session has not taken place** — it is the author's step |
| 4 | Result to C8 at the level it took place | after the session: the author runs `src/c5_step3_report.py` (§5); C8 reads `step3/REVIEW.md` |

## 2. Author's decisions (C5 24–25/11, C5b 25–26/11, C5c 26–27/11)

- SzScan accepts every EDF and is a demonstration prototype: nothing tuned per subject or dataset; it never reads
  annotations. Two engine modes, session (default) and file; the Euréka demo is the priority.
- The reference unit (per file / whole session / cumulative) is **not decided** — compared by F2-06.
- Cases ingested chosen by C5 ("show the best"); training patients may be added for the council, marked "seen in
  training".
- **G5 (C5c, 26/11): option A** — bad-electrode interpolation is **off by default**; the application flags and the reader
  decides; clin02's C3 is interpolated at ingest, as in the thesis run. The stricter rule B (time-resolved per segment,
  threshold and effect measured on development by a rule written before, clinician confirmation) is parked for Track F
  (`FUTURE_RESEARCH_PLAN.md` §14.24 row 121).
- **G2 on Kaggle** (author's preference), G9 and the hospital part on the laptop in the author's own terminal.
- **Step 3 (C5c prompt, 26/11):** (a) 8 anchor clips from annotated public data, 4 Siena + 4 CHB-MIT test patients,
  chosen by a rule written before (found, missed, high-score false alarm); (b) 24 clips (16 hospital + 8 anchors) if she
  gives about 1 h, otherwise 18 (12 + 6); (c) **no reading-time comparison** — time per clip recorded descriptively and
  her usual reading time asked in the interview (§14.24 row 122). Protocol approved 27/11 10:30.
- Every command given to the author is one line; memory-heavy laptop runs in his own terminal; laptop code avoids the
  Windows / Linux differences already met and every command is first run through the script's parser (instructions
  rev ai §1 item 15).

## 3. Memory on the laptop (what happened, what is in place)

1. Whole-recording copies peaked at 15.1 GB (largest Siena file) → block reading (`21ef792`).
2. Memory-mapped pages stay resident, invisible to the traced heap → ordinary file I/O, no memory map (`d322357`).
3. Claude Code stops its background commands under memory pressure → the author runs the gates in his own terminal;
   the watchdog limits **private** memory (2 GB), resident recorded.
4. (C5b) **MNE 1.12.1 allocates its read buffer for every signal of the file** whatever the picks; Windows counts it as
   private (commit), Linux only in VmData → every reader reads in 600-s blocks, a header-based model `predict_mb` is
   checked before each file (`17b86fc`); test E11 measures committed memory.
5. (C5b) Full run: G1, G3 PASS; the hospital part stopped at 11,152 MB — **both hospital records are EDF+ with an
   annotation signal, which MNE reads over the whole file while opening it**, with the same all-signal buffer
   (`src/c5_diag_edfplus.py`).
6. Laptop: 16 GB RAM, about 4.3 GB free when the C5b run started (daily use).
7. **(C5c) Fix 4** (`20c5172`): `web_demo/backend/edf_input.py` opens every EDF inside `no_edf_annotations()`, which
   empties MNE's annotation-channel index while the file is opened (MNE pinned at 1.12.1; the version is checked), so no
   annotation is read; data equal to MNE's normal read bit for bit (test E12); the open-time memory is in `predict_mb`.
   The gate script writes each row as it finishes (`RowLog`) and runs by part (`--parts`). Hospital rerun: both records
   open within the model; counts in the author's private report only.
8. **(C5c) Ingest** (`web_demo/backend/batch_ingest.py --max-gb`, log `uploads/_ingest_log_c5c.csv` on the laptop):
   private peak 2.08–2.38 GB per study, 24–97 s per hour of EEG. **File mode on the longest Siena recording** (13.5 h,
   512 Hz): Phase A +622 MB (model 696), engine +209 MB, 485 s.
9. Windows defects met in C5c and fixed (the rule of instructions rev ai §1 item 15 comes from them): `time.mktime`
   refuses pre-1970 dates (Siena clock → second of the day, `siena_clock`); a memory-mapped file cannot be deleted
   (closed before deletion in G2); a verifier that filtered after the cut differed at file edges (filter before the cut);
   a file absent from a CHB-MIT summary (chb24) counts as seizure-free, as F2-03's L3.

## 4. What C8 can use now

**The application (live demo).** SzScan opens any CHB-MIT or Siena EDF and the two hospital recordings; both modes are
verified against the thesis code: session = the committed application events (G1), file = Track F's L3 events on 294 /
294 recordings (G2); the signal shown = the original EDF, 18 derivations by name and order, µV, times and filter,
confirmed by an independent reader on 407 files, 578.8 h (G9).

**Demo database (laptop, 21 studies):** test chb03, chb06, chb13–chb18; chb24 (session) and `chb24-file` (file mode);
validation chb10, chb11, chb22; Siena PN00, PN01, PN03, PN05, PN06, PN07, PN09, PN10, PN11, PN12, PN13, PN14, PN16,
PN17; two hospital recordings as private studies (neutral names, no header field, elapsed time only).

**Numbers.** Headline numbers stay V5's (`EUREKA_PLAN.md` Appendix D); the deployment mode is Track F hand-off item
(14) (L3). The application's own scoring of its database (`step2/score_app/SUMMARY.md`; seed 42, application tier,
per-patient means, SzCORE event scoring) describes the demo database, never a new thesis result:

| group | mode | patients | hours | seizures found | sensitivity | FP/day | wording limit |
|---|---|---|---|---|---|---|---|
| test | session | 8 | 279.4 | 33 / 76 | 0.528 | 26.9 | = the thesis application row (V5 Section 3.6) |
| validation | session | 3 | 115.8 | 14 / 15 | 0.933 | 20.4 | development patients (the design was chosen on them) — not an independent result |
| chb24 | session | 1 | 21.3 | 14 / 16 | 0.875 | 28.4 | one patient; V5 quotes 0.828 (4 seeds) |
| chb24 | file | 1 | 21.3 | 15 / 16 | 0.938 | 54.5 | one patient, one seed (L3: 0.984 at 52.8) |
| Siena | session | 14 | 141.0 | 33 / 47 | 0.748 | 40.7 | one seed, application tier; quote V5's 0.633 at 41.0 |

**Security (Q&A G15)** — from the code: one admin account in `backend/.env`, an in-memory token without expiry or roles
(a symbolic gate), bound to 127.0.0.1 (the real protection); since C5 an append-only action log of review decisions,
exportable as CSV (C10); no access log of its own.

**The doctor's review.** Nothing yet: the slide slot says nothing about her review until `REVIEW.md` exists (§5).

## 5. The review session (protocol `step3/PROTOCOL_STEP3.md`; Vietnamese material in `step3/vi/`)

- **Session (≈ 60 min):** consent (`vi/DONG_Y.md`) → blinded review of 24 one-minute clips (16 hospital: 5 highest-score
  events, 5 random events, 6 controls ≥ 5 min from any event; 8 anchors from annotated public data: found 2 Siena + 1
  CHB-MIT, missed 1 + 1, false alarm 1 + 2; or the 18-clip version) → demo on clin01 → interview
  (`vi/HUONG_DAN_PHONG_VAN.md`). Form per clip: IFCN class, confidence 1–5, "would you want the system to show you
  this?"; time per clip from the review page. Paper backup form `vi/PHIEU_DANH_GIA.md`.
- **Author's run-sheet:** `vi/HUONG_DAN_BUOI_GAP.md`. Before: `src/c5_step3_clips.py` once (the output folder must be
  empty — the rule runs once; if a run fails, the folder is emptied before the second run and the failure noted in the
  protocol). After: `src/c5_step3_report.py` writes `step3/REVIEW.md` and `step3/anchors.csv` (public: counts and
  public anchors only) and a private every-clip table in `F:/Study/Thesis/Eureka/C5_review/`; the report stops if a
  clip has no class.
- **Code:** `src/c5_step3_clips.py`, `src/c5_step3_report.py`; synthetic test `src/c5_step3_test.py` (T1–T9, every rule
  of the protocol against a hand-derived selection; T9 emulates Windows' `mktime` and mapped-file deletion; ALL PASS). The review page was checked in a headless browser
  (navigation, CSV download); its in-browser storage may not survive a reload — the run-sheet asks for a CSV download
  about every 6 clips.
- **Wording for C8 (integrity rule 10):** "exploratory expert review" — one reader, two recordings, counts by class;
  never clinical validation, no sensitivity or specificity; her opinion cited only at the level she chooses in the
  consent; the permission status of the recordings as recorded in the project (board R233 (d)).

## 6. Open items (not C5's; recorded for whoever needs them)

- Reference unit of the application (file / session / cumulative) → F2-06.
- Rule B for bad electrodes → Track F (§14.24 row 121); a reader study with timing → stream H (row 122).
- A de-identified working copy of the hospital recordings and a written confirmation from the doctor → the author
  (board R233 (d)).
- If the session needs help (the clip script stops, the answers file is incomplete), the author opens a short chat C5d
  (prompt in `STATUS_BOARD.md` §4).

## 7. Literature (title + DOI)

Scheuer et al. 2021, J Clin Neurophysiol, 10.1097/WNP.0000000000000709; Halford et al. 2015, Clin Neurophysiol,
10.1016/j.clinph.2014.11.008; Reus et al. 2023, Seizure, 10.1016/j.seizure.2023.04.010; Reus et al. 2022, Seizure,
10.1016/j.seizure.2022.01.009; Vasey et al. 2022 (DECIDE-AI), Nat Med, 10.1038/s41591-022-01772-9; Kane et al. 2017
(IFCN glossary), Clin Neurophysiol Pract, 10.1016/j.cnp.2017.07.002.
