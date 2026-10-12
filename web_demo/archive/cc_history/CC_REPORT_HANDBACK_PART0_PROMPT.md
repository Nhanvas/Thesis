# CC_REPORT_HANDBACK_PART0_PROMPT.md — freeze the build, verify integrity

Read REPORT_REQUEST_TO_PROJECT2.md, REPORT_REPLY_TO_PROJECT2_OP.md and
REPORT_REPLY_TO_PROJECT2_2.md in full first (all under web_demo/).

1. Commit every currently-uncommitted web_demo/ change (git add web_demo/ only — never git add .;
   confirm via git status that nothing outside web_demo/ is staged). Tag the commit
   `szscan-frozen-v1`. Report the tag and the full commit hash (`git rev-parse HEAD`).
2. On that exact commit: `python -m pytest web_demo/backend/tests/test_guards.py -v` — paste the
   full raw output.
3. Run `python src/verify_provenance.py | grep -a -i verdict` and paste the line; confirm it reads
   VERDICT: PASS. Quote the lines in pipeline_demo.py that set the checkpoint path and its sha256
   (CHECKPOINT_PATH / CHECKPOINT_SHA256).
4. If step 2 or 3 fails: STOP, report the failure in detail, do NOT create the tag until fixed and
   re-verified.
5. Write "## 0. Frozen build" of web_demo/REPORT_HANDBACK.md (template in
   REPORT_REQUEST_TO_PROJECT2.md Part 5), plus a "Fixes since the last tag" list, one line each,
   each stating what was wrong and how it was found (not what looked wrong):
     - score.npy never persisted by the live Process flow (found by reading upload_manager.py
       against waveform_serving.get_timeline's own error path)
     - MiniTimeline.jsx hardcoded to a 1-hour domain (found by reading the component after chb06,
       a subject with >1h files, was added to the DB)
     - filter toolbar collapsed from 3 buttons to 1 (found: 2 of 3 buttons toggled the same
       cached array; measured negligible difference between the two real filter stages)
     - Delete endpoint not removing uploads/{id}/ on disk; unbounded Phase-A upload concurrency
       (both found by code review, not by any subject's output)
     - chb13 short 31 of its 33 real files (found by a file-count audit against the dataset dir)
     - operating point switched to the fixed validation point mag_pct=50/pen_mult=2.0 (Project 1's
       methodological decision, not a bug)
   State plainly for the chb06 diagnostic: no defect found, no change made.
   Do not attempt Parts 1-4 in this prompt.

Do not touch src/*.py. Never open chb*-summary.md seizure fields or
results/attribution_v7/labels/.