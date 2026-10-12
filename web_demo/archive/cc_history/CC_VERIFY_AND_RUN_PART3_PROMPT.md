# CC_VERIFY_AND_RUN_PART3_PROMPT.md — resolve the frozen-build check, then run Part 3

The prerequisite check in CC_REPORT_HANDBACK_PART3_PROMPT.md was too strict: it required HEAD to
equal the exact tagged commit, but 4 commits landed since the tag from unrelated work at the repo
root (src/, figures/) that never touches web_demo/ (per CC_PROMPT_SCORER_BOUNDARY.md's own stated
scope: "Never writes web_demo/"). A frozen build only needs web_demo/ itself unchanged, not the
whole monorepo.

1. Run: git diff szscan-frozen-v1..HEAD --stat -- web_demo/
   - If this is EMPTY (no output): web_demo/ is byte-identical to the tagged commit. State this,
     list the 4 intervening commits (git log szscan-frozen-v1..HEAD --oneline) and confirm each
     one's changed files (git show --stat for each) lie outside web_demo/, then proceed directly
     to CC_REPORT_HANDBACK_PART3_PROMPT.md's Part 3 work (sections 1-4) at the CURRENT HEAD -- do
     not checkout the old tag, do not create or move any tag, do not touch git otherwise beyond
     what Part 3 itself already specifies (no commit/push of Tier 2 outputs). Record in the Part 3
     report both commit hashes (the tag commit and the HEAD actually used) and the fact that
     web_demo/ was verified identical between them.
   - If it is NOT empty: STOP. Print the full diff --stat output and do nothing else -- this is a
     real conflict needing a human decision, not something to resolve on your own.
2. The six untracked files already under web_demo/ (CC_PROMPT_SCORER_AND_LABELS_FIX.md,
   CC_PROMPT_SCORER_BOUNDARY.md, CC_REPORT_HANDBACK_PART3_PROMPT.md, REPORT_HANDBACK.md,
   REPORT_REPLY_TO_PROJECT2_3.md, REPORT_REQUEST_TO_PROJECT2.md) are expected reference documents,
   not code -- leave them alone, they do not count as "dirty" for this check.

Everything else in CC_REPORT_HANDBACK_PART3_PROMPT.md stands unchanged.