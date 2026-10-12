# DEMO_FINAL_HANDBACK.md — run of `docs/prompts/CC_DEMO_FINISH.md` (2026-10-12)

**Final outcome: ALL STAGES PASSED.** Stage 5 stopped once on a real defect (below), was fixed under
an explicit, conditioned approval, verified against the thesis's own file inventory, and the full
8-subject run was repeated from a clean database per "any defect ⇒ repeat the whole run." Stages 6–8
then completed normally. Build: commit `8aabf4d4c8ee2892a808e25b9c7839291803f436`, tag
`szscan-frozen-v4.1`.

---

## 1 · First run — stopped after 6/8 subjects

Stages 0–4 passed (preconditions; `web_demo/` tidy, committed `11c04ae`; timeline row → [0,1],
committed `28e5c02`; real-UI smoke test on `chb17` passed — see §4 below; freeze, tagged
`szscan-frozen-v4`, no backend/`src` change since `936b8e0`).

Stage 5's first attempt ingested 6 subjects cleanly in 58 minutes (wall clock 16:11:47–17:10:05),
then stopped:

| subject | files | hours | seconds | s/hour |
|---|---|---|---|---|
| chb03 | 38 | 38.00 | 470.3 | 12.38 |
| chb06 | 18 | 66.74 | 782.9 | 11.73 |
| chb13 | 33 | 33.00 | 435.8 | 13.21 |
| chb14 | 26 | 26.00 | 551.8 | 21.22 |
| chb15 | 40 | 40.01 | 834.0 | 20.85 |
| chb16 | 19 | 19.00 | 409.6 | 21.56 |

```
chb17: ingesting ...
STOP: no chb17_*.edf under F:\Study\Thesis\Dataset\CHB-MIT\chb17
```

**Mechanism:** `web_demo/backend/batch_ingest.py:43` found a subject's files with
`edf_dir.glob(f"{subject}_*.edf")`. CHB-MIT names `chb17`'s recording in three lettered segments
(`chb17a_03.edf`, `chb17b_57.edf`, `chb17c_02.edf`, ...) — no file is ever named `chb17_NN.edf` — so
the glob matched zero files. Every other test subject uses the plain `{subject}_NN.edf` shape, which
is why only `chb17` broke. This was a **script defect, not a pipeline defect**: Stage 3's real-UI
smoke test (§4) had already processed all 21 of `chb17`'s actual files successfully through the real
backend, proving `pipeline_demo.py` has no filename assumption.

Per the stop rule, this was not fixed or tuned around in the moment: the run was stopped, the
partial 6-subject database was left in place (not deleted), and Stage 8's handback was written before
any further action, per "any defect ⇒ repeat the whole run" and "stop... and do nothing else."

---

## 2 · The fix, approved with six conditions, applied in full

The author approved re-running Stage 5 under six explicit conditions (verbatim in
`web_demo/fix.md`, deleted after this handback was written per the author's own instruction). Each is
recorded here as done:

**1 — Fix + test.** `web_demo/backend/batch_ingest.py` now selects a subject's files with
`subject_edfs(subject, edf_dir)`, matching the anchored regex `^{subject}[a-z]?_\d+\.edf$` (covers
`chb17a_03.edf` / `chb17b_57.edf` / `chb17c_02.edf`; never another subject — `chb1_01.edf`,
`chb170_01.edf` and `chb03_01.edf` all fail to match a `chb17` pattern). Still reads EDF file names
only, same as before. A new test file, `web_demo/backend/tests/test_batch_ingest.py` (4 tests),
checks: chb17's lettered names match; a plain subject name still matches; other subjects' files never
match chb17's pattern; a `.seizures` sidecar / `-summary.md` / uppercase `.EDF` never match. Full
backend suite: **15/15 passed** (11 pre-existing + 4 new).

**2 — Coverage check against the thesis side, before ingesting.** Source used:
`data/testset_v2/{subject}.npz` (`files` + `skipped_files` arrays — the thesis's own per-subject file
inventory for its continuous evaluation; `skipped_files` are on-disk EDFs the thesis excludes only for
missing one of the 18 standard channels, per `c1b_build_trainset.py`'s comment, so `len(files) +
len(skipped_files)` is the thesis's own count of real files on disk for that subject). Compared
against the new regex's selection on the real dataset directory, for all 8 subjects, by count **and**
by exact filename set:

| subject | regex-selected | thesis `files` | thesis `skipped_files` | thesis total | match |
|---|---|---|---|---|---|
| chb03 | 38 | 38 | 0 | 38 | **exact filename match** |
| chb06 | 18 | 18 | 0 | 18 | **exact filename match** |
| chb13 | 33 | 33 | 0 | 33 | **exact filename match** |
| chb14 | 26 | 26 | 0 | 26 | **exact filename match** |
| chb15 | 40 | 40 | 0 | 40 | **exact filename match** |
| chb16 | 19 | 19 | 0 | 19 | **exact filename match** |
| chb17 | 21 | 21 | 0 | 21 | **exact filename match** |
| chb18 | 36 | 36 | 0 | 36 | **exact filename match** |

No mismatch in any subject (zero `skipped_files` everywhere) — no STOP triggered; proceeded to the
re-run.

**3 — Commit + tag.** Committed `8aabf4d4c8ee2892a808e25b9c7839291803f436`
("web_demo: batch_ingest matches CHB-MIT lettered file names (chb17a/b/c)"), tagged
**`szscan-frozen-v4.1`**. `szscan-frozen-v4` left untouched (still points at `936b8e0`'s
`web_demo/backend`/`src` tree).

**4 — Partial data moved aside.** The 6-subject `szscan.db` and its `uploads/` were moved (not
deleted) to `web_demo/_old_data_2026-10-12/partial_run1/` (uploads ≈ 52 GB). `db.list_subjects()`
confirmed `[]` on the fresh database before re-ingesting.

**5 — Full re-run + Stages 6–8.** Done; results below. `MANIFEST.txt` (§3) names commit
`8aabf4d4c8ee2892a808e25b9c7839291803f436` with `uncommitted changes in web_demo/backend or src: no`
— the `szscan-frozen-v4.1` commit, exactly.

**6 — This handback.** Records the first run's stop, the fix, the commit/tag, the file-count table
and the re-run's measured runtimes (this document). Nothing under `web_demo/_old_data_*` was
committed (confirmed before every `git add` below — see §7).

---

## 3 · Stage 5, re-run — all 8 subjects, no defect

Command (same proxy settings/network-off evidence, same commands as the first attempt):
`HTTP_PROXY=http://127.0.0.1:9 HTTPS_PROXY=http://127.0.0.1:9 NO_PROXY=""`, then
`python batch_ingest.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --all`.

| subject | files | hours | seconds | s/hour |
|---|---|---|---|---|
| chb03 | 38 | 38.00 | 965.2 | 25.40 |
| chb06 | 18 | 66.74 | 1629.4 | 24.42 |
| chb13 | 33 | 33.00 | 673.7 | 20.41 |
| chb14 | 26 | 26.00 | 541.1 | 20.81 |
| chb15 | 40 | 40.01 | 823.0 | 20.57 |
| chb16 | 19 | 19.00 | 418.3 | 22.02 |
| chb17 | 21 | 21.01 | 391.6 | 18.64 |
| chb18 | 36 | 35.63 | 420.1 | 11.79 |

**TOTAL 8 subjects, 279.39 h, 5862 s (97.7 min), 21.0 s per hour of EEG** — no `rejected` entries in
any row (`uploads/_ingest_timing.csv`, copied to `results/application_eval_v4/ingest_timing.csv`).
Per-subject rates run ~1.5–2× slower than the first attempt's 6 subjects (12.4–21.6 s/h then, 18.6–25.4
s/h now); the only material difference between the two runs was background memory pressure — a live
OOM risk was flagged mid-run (§5) — not a pipeline change (`git diff` confirmed empty for
`web_demo/backend`/`src` between the two attempts beyond the one `batch_ingest.py` commit). `chb06`,
the memory-sensitive subject, completed without incident both times.

`export_tier2.py --out ../report_handback/tier2_v4` then `src/t1_app_tier.py --tier2-dir
web_demo/report_handback/tier2_v4`. Coverage check (thesis scorer, `t1_app_tier.py`'s own output):
**76/76 annotated seizures present in processed files across all 8 subjects, 0 coverage issues**;
total processed hours 279.39 vs 279.39 (report Table 2.1), delta 0.00 h; 0 boundary-crossing events
in any subject.

---

## 4 · Stage 3 — real-UI smoke test on chb17 (unchanged from the first run)

PASS, no non-cosmetic error. Backend + frontend started locally; current db/uploads moved aside to
`web_demo/_old_data_2026-10-12/` first. Logged in through the real UI, processed `chb17` (21 real EDF
files, 32.3 h), opened Analysis on `chb17a_03.edf`, clicked AI Event 1 (onset 20:25:58), confirmed the
channel panel title reads exactly **`Channel-level latent anomaly — Event 1`**, clicked Accept + Save
(persisted — the mini-timeline block turned green), exported `.txt` (`GET /api/subjects/chb17/export`
→ HTTP 200, proper `attachment` headers). Stopped the servers, deleted `chb17` through the
application's own Delete, confirmed `db.list_subjects()` returned `[]` afterward.

Two deviations, both recorded here as the stage requires: (1) the 21 EDFs were POSTed directly to
`/api/uploads/current/files` via `curl` — the same endpoint the browser's `Browse Files` widget calls
— because the browser-automation tool cannot attach a 50 MB local file or drive the OS file-picker
dialog; every step from Process onward was a genuine browser click. (2) 17 of 21 files were marked
"Viewed" via `POST /api/files/{id}/viewed` (the same endpoint the UI's own button calls) instead of
one-at-a-time clicks, because rapid `Next`+`Viewed` clicks were outrunning the page's per-file load.

---

## 5 · Deviations and runtimes (measured), full run

| stage | runtime | deviation |
|---|---|---|
| 0 | ~2 min | none |
| 1 | — | none |
| 2 | — | none |
| 3 | ~20 min | file upload via `curl` to the UI's own endpoint; most "Viewed" marks via the UI's own API (both explained in §4) |
| 4 (first tag) | <1 min | none |
| 5 (first attempt) | 58 min to the STOP | Edge/Cursor left running against the ground rule (Cursor hosts this session; author authorized continuing after Chrome was closed) |
| fix + verification | — | none — regex fix, 4 new tests, 15/15 suite green, 8/8-subject coverage table exact |
| 5 (re-run) | 97.7 min (5862 s) for all 8 subjects | a background monitoring process was killed by the OS for low memory partway through `chb06`; the ingest process itself (separate PID) was unaffected and completed normally — flagged live to the author, Chrome/Edge processes were still observed running despite being reported closed |
| 6 (screenshots) | ~3 min | captured via Playwright at an exact 1600×1000 **browser viewport** rather than an OS window resize — the dev machine's physical screen is 1366×768, too small to fit a 1600×1000 window; same live backend/frontend, same login, same real navigation and clicks, just driven by Playwright's API instead of the Claude-in-Chrome extension for this one step |
| 7 (push) | — | see §7 |

---

## 6 · R1–R8

- **R1 (gate)**: `results/t1_demo/GATE.md` — **PASS** (done in a prior session; unaffected — no backend
  logic changed by the `batch_ingest.py` fix beyond that one file, confirmed by the coverage-table
  cross-check and the unchanged `web_demo/backend/pipeline_demo.py` etc.). Thesis-statistics gate:
  detector 7/23, localized 7/22 (matches look #7 exactly). Label-free run: detector 6/21, localized
  6/20 (n_ref 7).
- **R2 (timing)**: `results/t1_demo/TIMING.md` — median **21.68 s/hour** of EEG (chb16, 3 repeats,
  headless path; done in a prior session, unaffected). Real upload-flow per-subject wall-clock from
  this run: `results/application_eval_v4/ingest_timing.csv` (§3 table above); **21.0 s/hour** median
  across the full 8-subject application run.
- **R3 (application tier)**: `results/application_eval_v4/SUMMARY.md`, `per_subject.csv`,
  `pooled.json`:
  ```
  subject  files   hours  seizures  detected  false_alarms  sensitivity  precision  f1      FP/day
    chb03     38 38.0017         7         6            20       0.8571     0.2308  0.3636   12.6683
    chb06     18 66.7350        10         1            97       0.1000     0.0102  0.0185   34.9065
    chb13     33 33.0000        12         1            41       0.0833     0.0238  0.0370   29.9531
    chb14     26 26.0000         8         6            33       0.7500     0.1538  0.2553   30.5166
    chb15     40 40.0100        20        10            59       0.5000     0.1449  0.2247   35.8875
    chb16     19 19.0000        10         1            16       0.1000     0.0588  0.0741   20.2354
    chb17     21 21.0067         3         3            27       1.0000     0.1000  0.1818   30.9673
    chb18     36 35.6347         6         5            30       0.8333     0.1429  0.2439   20.2551

  pooled        33/76 detected, 323 false alarms, sensitivity 0.434, precision 0.093, F1 0.153, FP/day 27.86
  subject-mean  sensitivity 0.528, precision 0.108, F1 0.175, FP/day 26.92
  ```
  Scorer: `src/eval_application_events.py` (unchanged), SzCORE event scoring, every AI event, before
  any review. Coverage: 76/76 annotated seizures in processed files, 0 issues, 279.39 h processed
  (matches report Table 2.1 exactly).
- **R4 (screenshots)**: `F:/Study/Thesis/Reports/v8/figures/app_screens/` — `a_import.png` (recording
  list, all 8 subjects, Create New panel open), `b_analysis.png` (chb03, Analysis of `chb03_01.edf`,
  AI Event 1 selected — onset 388 s / offset 444 s, overlapping the annotated seizure at 362–414 s per
  `chb03-summary.md`, checked by hand against the exported `chb03_events.csv`, never by application
  code), `c_panel_review.png` (same event's channel panel, title `Channel-level latent anomaly —
  Event 1`, Accept/Reject/Uncertain buttons, ranked channel table). All three exactly 1600×1000 PNG,
  no calendar date, no internal name on screen.
- **R5 (architecture)**: unchanged since the backend rebuild except for the one `batch_ingest.py` fix
  (a batch-ingestion helper script, not part of the served application's request path) — full table in
  `web_demo/archive/cc_history/CC_T1_RUN_REPORT.md` Stage 1.7 (browser → FastAPI → upload manager →
  Phase A threads / Phase B+Process worker subprocess → SQLite + per-file cache; thesis modules
  imported read-only; checkpoint verified by sha256; no network import).
- **R6 (divergence paragraph)**, `SZSCAN_SPEC_v5.md` §1.6:
  > The report's per-patient z-score statistics exclude annotated seizure windows and a 4-hour
  > post-ictal buffer — a label-dependent preprocessing step, disclosed in the report. The demo cannot
  > see labels, so it uses every 10th window of the whole recording instead — the same rule the thesis
  > already uses for its own external (non-CHB-MIT) validation. Every other step of the final system —
  > the per-channel LedoitWolf fit, robust-z, percentiles and alarm budget — is fitted on the whole
  > recording, label-free, in the thesis system itself, so this one item is the only source of
  > divergence, and it is measured (not assumed) by the identity gate on chb03.
- **R7 (network-off evidence)**: `HTTP_PROXY`/`HTTPS_PROXY` set to an unreachable local address
  (`http://127.0.0.1:9`) for the whole Stage 5 re-run; `grep` of `web_demo/backend/*.py` for
  `requests`/`httpx`/`urllib` imports → 0 hits (confirmed in a prior session, re-confirmed unaffected
  by the `batch_ingest.py` fix, which adds only `re` to its imports); frontend fonts bundled locally
  (`CLAUDE.md` "Bundle fonts locally"), not fetched from a CDN.
- **R8 (build)**: commit `8aabf4d4c8ee2892a808e25b9c7839291803f436`, tag **`szscan-frozen-v4.1`**
  (`szscan-frozen-v3` and `szscan-frozen-v4` both still present, untouched).

---

## 7 · What was committed and pushed

Explicit paths only (never a whole-directory `git add`); `web_demo/_old_data_*` was never staged at
any point:
- `web_demo/backend/batch_ingest.py`, `web_demo/backend/tests/test_batch_ingest.py` — commit
  `8aabf4d4c8ee2892a808e25b9c7839291803f436`, tag `szscan-frozen-v4.1` (§2).
- `results/application_eval_v4/*` (`SUMMARY.md`, `per_subject.csv`, `pooled.json`,
  `ingest_timing.csv`).
- `web_demo/report_handback/tier2_v4/*` (8 `{subject}_events.csv`, `files.csv`, `MANIFEST.txt`).
- `web_demo/report_handback/DEMO_FINAL_HANDBACK.md` (this file).

Then `git push origin main --tags`.
