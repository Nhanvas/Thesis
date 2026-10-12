# CC_OVERNIGHT_RUN_PROMPT.md — unattended overnight Part 3 run

This is an overnight run, unattended. Boti will not be there to confirm anything, so do not stop to
ask. The full plan is `web_demo/CC_PART3_RERUN_V2_PROMPT.md`. Steps 1–4 there are **already done**:
concurrency set to 2, commit made, tag `szscan-frozen-v2` created. The machine was just rebooted, so
nothing is running.

**A. Verify.**
- Tag `szscan-frozen-v2` exists.
- `git diff szscan-frozen-v2..HEAD --stat -- web_demo/` shows no change to code. Untracked `.md` and
  `.log` files do not count.
- Guards pass 4/4.

If the code differs from the tag, STOP and report. That is the only reason to stop before step C.

**B.** Start the backend on this checkout and log in.

**C. Delete.** Boti explicitly authorizes, through this file, which he asked you to execute:
- deleting every subject from the demo database through `DELETE /api/subjects/{id}`, including chb03,
  which is left over from the discarded `szscan-frozen-v1` run;
- deleting any orphaned draft on disk.

If a permission check still blocks the deletion of chb03, do NOT stop. Skip chb03 for now and leave it
untouched. Process the other seven subjects. Boti will delete and re-run chb03 in the morning. Record
which case happened.

**D. Run.** Execute steps 6–11 of `web_demo/CC_PART3_RERUN_V2_PROMPT.md` in this order:
1. chb06
2. chb03, only if it was deleted in step C
3. chb13, chb14, chb15, chb16, chb17, chb18

Keep the peak-memory monitor on. Print the estimated finish time after chb06.

**E. Failures.**
- If a single file fails, record it with the exact error and continue.
- If any subject runs out of memory, record it, change no code and no setting, skip that subject, and
  continue with the next one.

**F. At the end.**
- Write everything into `web_demo/REPORT_HANDBACK.md`, sections 0 and 3:
  - the runtime environment;
  - failures and skipped subjects;
  - per-subject wall-clock time;
  - peak memory;
  - AI-event counts.
- Write the exports.
- Leave the backend and all processed data in place.
- Make no git commit, and delete nothing after the run.
