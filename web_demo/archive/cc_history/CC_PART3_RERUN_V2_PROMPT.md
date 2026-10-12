# CC_PART3_RERUN_V2_PROMPT.md — fix Phase A memory, re-freeze, re-run Part 3 in full

Decision by Boti, 2026-09-29. Two out-of-memory failures on chb06, the second on a freshly rebooted
idle machine, make this a reproducible build defect on the target hardware, not a load problem. Fix it
and re-run Part 3 in full on a new frozen build.

1. Stop the Part 3 driver and the backend gracefully. Do not resume the live chb06 session.
2. In `web_demo/backend/upload_manager.py`, change `_PHASE_A_MAX_CONCURRENCY` from 4 to 2. Nothing else.
   Quote the line before and after (file:line).
3. Run `python -m pytest web_demo/backend/tests/test_guards.py -v`. It must pass 4/4; paste the raw output.
4. Commit ONLY `web_demo/backend/upload_manager.py`, with the message
   `Phase A concurrency 4 -> 2: chb06 exceeds memory at 4 on the target laptop`, then tag
   `szscan-frozen-v2`. Do not stage `REPORT_HANDBACK.md`, `uvicorn.log` or anything else.
   Report the commit hash and the tag.
5. Start the backend on the new commit. Empty the database through the real DELETE endpoint: every
   subject, including chb03 and the partial chb06. Delete any orphaned draft on disk. Confirm that
   `GET /api/subjects` returns an empty list and that `uploads/` holds none of the 8 subject
   directories.
6. Re-run Part 3 exactly as in `CC_REPORT_HANDBACK_PART3_PROMPT.md` sections 2–4, on
   `szscan-frozen-v2`, with the memo `frozen build szscan-frozen-v2`, in this order: chb06 first, then
   chb03, chb13, chb14, chb15, chb16, chb17, chb18. Do not review any event and do not add any Human
   event.
7. While it runs, record peak memory with an external read-only monitor: psutil, sampling the backend
   and worker processes every 5 s, written to a CSV under `web_demo/report_handback/`. Do not change
   any code for this. Report the peak per subject.
8. As soon as chb06 finishes, print its wall-clock time and processed hours. Then print an estimated
   finish time for the remaining subjects, computed from the measured rate.
9. In `REPORT_HANDBACK.md`, record:
   - both OOM failures: time, subject, and files done;
   - the decision and the reason for it;
   - the new tag, and that the earlier partial run on `szscan-frozen-v1` was discarded in full;
   - the runtime environment: pagefile on F:, TMP on F:.
   Update "## 0. Frozen build" to the new tag, including the provenance check line.
10. If chb06 runs out of memory again at concurrency 2, STOP and report. Do not lower the concurrency
    further on your own.
11. After the export, do NOT delete the processed subjects or their caches. The screenshots (Part 2)
    and the repeated timing runs (Part 4) still need them. Cleanup is a separate, later step.
