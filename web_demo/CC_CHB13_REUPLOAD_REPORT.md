# CC_CHB13_REUPLOAD_REPORT.md — chb13 completed to its full real 33-file set

Closes the gap `CC_FILECOUNT_AUDIT_REPORT.md` flagged (chb13 was the one allowlisted subject with
`db_file_count` far below `real_edf_count`: 2 of 33) and finishes what
`CC_STEP9_CHB13_COMPLETE_PROMPT.md` set out to do but never ran. Driven entirely via the real HTTP
flow (Python `requests`, no `claude-in-chrome` — chb13's real `.edf` files are far above its 10 MB
attachment cap), replaying `web_demo/frontend/src/api.js`'s own request shapes exactly, the same
method `CC_STEP9_PHASE2_REPORT.md` used for the other 6 subjects. Guards 4/4 green before, and
after. No `git add`/`commit`/`push` run — `git status` at the end (§6) shows only this session's
pre-existing untracked report files; chb13's DB/upload-state changes live in `szscan.db` and
`uploads/`, both gitignored, so they don't appear in a text diff at all.

## 1 · What was lost (acknowledged before deleting, per `CC_STEP9_CHB13_COMPLETE_PROMPT.md` §1)

The old 2-file chb13 (memo `"A2 concurrency test"`, built early in Step 3) carried hand-built test
state from Steps 5-8: file ids `10`/`11` (`chb13_02.edf`/`chb13_03.edf`), and on `chb13_03.edf`
(file id 11) 5 events — 4 AI (`id 46` Accept, `id 47` Reject, `id 48` Uncertain, `id 49` Reject) and
1 Human (`id 86`, `review_status: null` — `BUILD_PROGRESS.md §10.4`'s still-unexplained event).
`attribution_status` was already empty for these events at the time of this check (0 rows in the
whole table, not just for chb13) — whatever per-channel Accept/Reject state earlier reports
mentioned was apparently already gone before this session started. Deleting chb13 destroys all of
this. That's the intended outcome here (fresh, full, untouched real data replacing partial test
data), not an accident. `BUILD_PROGRESS.md §10.4`'s open item (event 86's origin) is now **moot, not
resolved** — the event is simply gone along with everything else.

## 2 · Delete — confirmed on disk, not just the 200 response

```
DELETE /api/subjects/chb13 -> 200 {"ok": true}
GET /api/subjects -> chb13 absent from the listing
```

Per the prompt's explicit instruction not to just trust the 200: separately confirmed
`uploads/chb13/` was actually removed from disk —

```
$ ls web_demo/backend/uploads/chb13
ls: cannot access 'web_demo/backend/uploads/chb13': No such file or directory
```

— and the backend's own log line for the same request:

```
INFO:main:Removed uploads directory for subject chb13: F:\Study\Thesis\Code\web_demo\backend\uploads\chb13
INFO:     127.0.0.1:51305 - "DELETE /api/subjects/chb13 HTTP/1.1" 200 OK
```

confirming the on-disk cleanup fixed in `CC_FIX_DELETE_CONCURRENCY_REPORT.md` actually fired for a
real subject, not just its own synthetic test fixture.

## 3 · Upload + Process — real HTTP flow, full 33-file real set

Preflight: confirmed 33 real `.edf` files under `F:/Study/Thesis/Dataset/CHB-MIT/chb13/` (glob
`chb13_*.edf`, case-sensitive extension match — the 8 `.edf.seizures` sidecar files in that
directory don't match and were never touched, consistent with `CLAUDE.md`'s label-file guard)
before starting, per the prompt's "don't proceed on a silent mismatch."

Sequence, one driver script (`requests.Session`, cookie-based login), mirroring `api.js`:
1. `POST /api/login` (admin creds from `backend/.env`).
2. `GET /api/uploads/current` — confirmed **no live session** before touching anything (the
   resume-safety check `CC_STEP9_PHASE2_RESUME_PROMPT.md §1` prescribes, run even on a fresh
   start, not assumed).
3. `DELETE /api/subjects/chb13`, then `GET /api/subjects` to confirm it's gone (§2 above).
4. `POST /api/uploads/current` `{project_id: "chb13", memo: "Step 9 completion - full real
   dataset"}` (same memo text `CC_STEP9_CHB13_COMPLETE_PROMPT.md §3` specified).
5. `POST /api/uploads/current/files` (multipart, one real file at a time, sequential, exactly
   `addUploadFile`'s shape) for all 33 files. No upload errors, no rejections.
6. Polled `GET /api/uploads/current` until `ready_to_process` (all 33 `status: "uploaded"`), then
   until `phase_b_done`.
7. `POST /api/uploads/current/process` `{project_id: "chb13", memo: ...}`.
8. Polled until `done: true` (checked `error` on every poll — never set).
9. `POST /api/uploads/current/acknowledge` to free the system-wide upload lock, mirroring the real
   frontend flow after showing the completion panel.

**No interruption occurred this run** — the whole sequence completed in one continuous pass (~19.6
minutes wall-clock, upload start to Process done), so `CC_STEP9_PHASE2_RESUME_PROMPT.md`'s recovery
procedure was never actually invoked; step 2 above is the same live-session check that procedure's
§1 would have used had an interruption happened.

## 4 · Timing table (same format as `CC_STEP9_PHASE2_REPORT.md` §3/§6.3)

| Subject | Files | Hours (real) | Phase A+B (s) | rate (s/h) | Process/PELT (s) | rate (s/h) | `pen_mult` | events/day | total events |
|---|---|---|---|---|---|---|---|---|---|
| `chb13` | 33 | 33.000 | 877.01 | 26.58 | 310.40 | 9.41 | 2.0 | 39.27 | 54 |

For context against the other 7 subjects (`CC_STEP9_PHASE2_REPORT.md §6.3`'s comparison table, O4
numbers — chb13's row there was left blank since it predated this timing method):

| Subject | Files | Hours | Phase A+B rate (s/h) | PELT rate (s/h) | `pen_mult` |
|---|---|---|---|---|---|
| `chb16` | 19 | 19.000 | 14.29 | 3.58 | 1.0 |
| `chb17` | 21 | 21.007 | 27.27 | 7.94 | 2.0 |
| `chb14` | 26 | 26.000 | 23.35 | 6.61 | 5.0 |
| `chb13` | 33 | 33.000 | **26.58** | **9.41** | **2.0** |
| `chb18` | 36 | 35.635 | 22.84 | 10.94 | 2.0 |
| `chb03` | 38 | 38.002 | 12.18 | 3.65 | 2.0 |
| `chb15` | 40 | 40.010 | 14.06 | 3.19 | 5.0 |
| `chb06` | 18 | 66.735 | 10.88 | 4.40 | 2.0 |

chb13's rates land within the same 11-27 s/h (Phase A+B) / 3.2-11 s/h (PELT) spread
`CC_STEP9_PHASE2_REPORT.md §3` already documented as ordinary dev-machine run-to-run variance — not
an outlier, not flagged as anomalous.

## 5 · Confirmed: no old row survived the delete (direct read-only DB check)

```
subject row: {'id': 'chb13', 'memo': 'Step 9 completion - full real dataset', 'created_at': '2026-09-27 09:18:31'}
n files: 33
total hours: 33.0
file id range: 233 - 265          # old ids were 10, 11 -- entirely different range, nothing reused
any old file ids present? False
total events for chb13: 54
old event ids still present? []    # ids 46, 47, 48, 49, 86 -- none found
total attribution_status rows (whole DB): 0
chb13 events by source/status: [{'source': 'AI', 'review_status': 'Unseen', 'n': 54}]
```

All 54 events are AI-sourced, `Unseen` (a freshly-processed subject, nothing reviewed yet) — no
Human event, no Accept/Reject/Uncertain carried over from the old 2-file state. The old Human event
(`id 86`) and all 4 old AI events (`46`-`49`) are gone; the new file ids (`233`-`265`) are a disjoint
range from the old ones (`10`, `11`), so nothing was reused or silently merged. `attribution_status`
is empty across the *entire* database, not just for chb13, confirming no stray row survived anywhere.

## 6 · Completion checks

**`GET /api/subjects` — exactly the 8-subject allowlist, no more, no fewer, no synthetic subject:**

```
chb16 Viewing (0/19) 19 files 19:00:00
chb17 View            21 files 21:00:24
chb14 View            26 files 1d:02:00:00
chb18 View            36 files 1d:11:38:05
chb03 View            38 files 1d:14:00:06
chb15 View            40 files 1d:16:00:36
chb06 View            18 files 2d:18:44:06
chb13 View            33 files 1d:09:00:00
total subjects: 8
```

(`chb16`'s `Viewing (0/19)` reflects one file left open mid-review from an earlier, unrelated
session in this same conversation — not something this task touched or needs to fix.)

**`pytest web_demo/backend/tests/test_guards.py -v`, before starting and again after everything above:**

```
============================= test session starts =============================
tests/test_guards.py::test_guard_no_build_timeline_masked PASSED         [ 25%]
tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED     [ 50%]
tests/test_guards.py::test_guard_no_labeled_npy PASSED                   [ 75%]
tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED       [100%]
============================== 4 passed in 7.39s ==============================
```

4/4 both times.

## 7 · `git status` (end of session)

```
 M web_demo/SZSCAN_SPEC_v5.md
 M web_demo/backend/main.py
 M web_demo/backend/pipeline_demo.py
 M web_demo/backend/upload_manager.py
 M web_demo/backend/waveform_serving.py
 M web_demo/frontend/src/components/EegPanel.jsx
 M web_demo/frontend/src/screens/AnalysisScreen.jsx
?? bme11/
?? web_demo/CC_FILECOUNT_AUDIT_REPORT.md
?? web_demo/CC_FIX_DELETE_CONCURRENCY_REPORT.md
?? web_demo/CC_FIX_FILTERSTAGES_REPORT.md
?? web_demo/CC_FIX_FILTER_SINGLE_TOGGLE_REPORT.md
?? web_demo/CC_STAGE_TIMING_REPORT.md
?? web_demo/CC_STEP9_CHB13_COMPLETE_PROMPT.md
?? web_demo/backend/backfill_bandpass.py
?? web_demo/backend/measure_stage_timing.py
```

All pre-existing from earlier, unrelated work this session (filter-toggle changes, stage-timing
instrumentation) — nothing here comes from this chb13 task, which touched only `szscan.db` and
`uploads/` (both gitignored). This report itself isn't shown above since `git status` was run before
writing it. `bme11/` remains Boti's own, unrelated, pre-existing untracked directory. **No `git
add`/`commit`/`push` was run at any point.**

---

**Stopping here.** chb13 is now a real, fully-processed, 33-file subject like the other 7 — the
8-subject allowlist is uniformly "every subject, full real file set." `BUILD_PROGRESS.md §10.4`'s
open item about event id 86 is closed as moot (§1 above). Nothing else was touched.
