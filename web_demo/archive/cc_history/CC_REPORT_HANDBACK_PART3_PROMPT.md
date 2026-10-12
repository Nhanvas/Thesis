# CC_REPORT_HANDBACK_PART3_PROMPT.md — the second evaluation tier (Tier 2)

Read web_demo/REPORT_REQUEST_TO_PROJECT2.md Part 3 and web_demo/REPORT_REPLY_TO_PROJECT2_3.md in
full first (both must already be under web_demo/ -- stop and ask if either is missing).

Prerequisite check: confirm `git rev-parse HEAD` equals the szscan-frozen-v1 commit
(66f7c89c4d9931c0895c5efb739289859293af16) and `git status` shows a clean web_demo/ (no
uncommitted changes). Stop and report if either fails -- do not proceed on a dirty or
different tree.

## 1. Empty the database

Delete all 8 currently-processed subjects via the real DELETE endpoint (which also removes
uploads/{id}/ on disk, per CC_FIX_DELETE_CONCURRENCY_REPORT.md). Confirm GET /api/subjects
returns an empty list and uploads/ holds none of the 8 subject directories. State exactly how
this was done.

## 2. Reprocess every real EDF, all 8 subjects

Same method as CC_STEP9_PHASE2/CC_CHB13_REUPLOAD used: the real HTTP flow (login, sequential
per-file upload POSTs, Process, poll), never claude-in-chrome (real file sizes exceed its
attachment cap). For each of chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18: confirm the
real .edf count on disk under F:/Study/Thesis/Dataset/CHB-MIT/{subject}/ before starting (glob
{subject}_*.edf, case-sensitive, excluding .edf.seizures sidecars), upload every one of them
(not only files containing a seizure), then Process. Memo: "Tier 2 -- frozen build
szscan-frozen-v1". If a file fails to upload or process, record its name and the exact error and
continue with the rest -- do not silently skip.

Resume-safety: if this session is interrupted, check GET /api/uploads/current for a live session
before restarting a subject from scratch (same pattern as CC_STEP9_PHASE2_RESUME_PROMPT.md) --
server-side state survives independently of this driver script.

Do NOT review any event, do NOT add any Human event, at any point during this task.

## 3. Export

For each subject, `web_demo/report_handback/tier2/{subject}_events.csv`, columns exactly:
`subject,file_name,event_id,onset_s,offset_s,source,review_status`
-- every event from `db.list_events(...)` for that subject's files, straight from the DB, no time
reformatting, no clipping, no splitting (offset_s may exceed that file's own duration for a
boundary-spanning event -- leave it as-is, per REPORT_REPLY_TO_PROJECT2_3.md). No calendar date
anywhere.

Also `web_demo/report_handback/tier2/files.csv`, columns exactly:
`subject,file_name,duration_s,n_windows,status`
-- `duration_s` from the EDF header (as already stored/derivable), `n_windows` from
`np.load(uploads/{subject}/{stem}.raw.npy, mmap_mode="r").shape[0]` (not the DB), kept as two
separate columns since they can differ by up to 4 s (trailing partial window dropped).

## 4. Report

Per-subject: real file count confirmed vs. uploaded, any failure/skip with reason, count of AI
events (sanity figure only -- no other number about detection quality), wall-clock per subject.
State plainly: no event was reviewed and no Human event was added before export. Append this as
"## 3. Tier 2 run" in web_demo/REPORT_HANDBACK.md, following the template in
REPORT_REQUEST_TO_PROJECT2.md Part 5.

Guards must stay 4/4 (paste raw output) -- this task should not need any code change, so a
guard failure means something else broke; stop and report if that happens.
Do not touch src/*.py. No git add/commit/push (the frozen tag stays as the code state; the
report/CSV files are new content on top of it, committing them is a separate step Boti decides).