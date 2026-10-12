# CC_STEP9_PHASE2_DOCFIX_PROMPT.md — two confirmations + close out BUILD_PROGRESS.md for Step 9 phase 2

Read first: `web_demo/CC_STEP9_PHASE2_REPORT.md` (this session's own full account — don't re-derive
anything it already established), `web_demo/BUILD_PROGRESS.md` §1 (status table) and §14/§15 (open
items / Step 9 detail — the pattern every prior step's closeout already follows).

No pipeline/code changes in this prompt — this is a documentation closeout plus two quick factual
confirmations already answerable from what happened in the phase 2 session. Guards unchanged: 4/4, no
writes outside `web_demo/`, no `git add`/`commit`/`push`.

## 1 · Two quick confirmations — answer from what already happened, don't re-run anything

1. **Are the 5 subjects processed before `chb06`'s fix (`chb17`/`chb14`/`chb18`/`chb03`/`chb15`)
   affected by the `pipeline_demo.py` change in any way — does any of them need to be reprocessed?**
   State plainly: yes/no, and why. (The fix is claimed bit-identical to the old computation; those 5
   were already fully cached under the old code before the fix existed, so if the claim holds, their
   cached output is exactly what the new code would also have produced and nothing changes for them.)
2. **Was the `np.array_equal()` bit-identical check for the mean/std chunking fix run at a scale
   actually matching `chb06`'s real shape** (`n_windows_total=50121`, 18 files), **or only at a
   smaller "realistic" synthetic scale?** If only the latter, say so plainly — it doesn't invalidate
   the fix (the math argument is scale-independent, and `chb06`'s real retry completed cleanly with
   plausible `pen_mult`/events-per-day numbers), but the report should be precise about what was
   actually tested versus what's argued mathematically.

## 2 · Update `BUILD_PROGRESS.md` to close out Step 9 phase 2 — same pattern as every prior step

1. §1's status table: change Step 9's row from "IN PROGRESS — phase 1 & 1b done; phase 2 ... not
   started" to reflect phase 2 now done — all 8 allowlisted subjects real and processed.
2. Add a new subsection under §15 (e.g. §15.3 "Step 9 phase 2 — detail") consolidating
   `CC_STEP9_PHASE2_REPORT.md`: the processing order, the per-subject timing table, the 3
   interruptions and how each resumed, the `chb06` OOM bug (root cause, fix, verification, retry
   result), and the flagged-but-not-fixed connection to Phase A's concurrency issue.
3. Update §14's open-items list: remove anything phase 2 resolved (file-count-per-subject scope is
   now moot — it's done for all 8 subjects), keep only what's genuinely still open — O4 (which
   subject for the live-upload scenario; comparison numbers now exist in `CC_STEP9_PHASE2_REPORT.md`
   §6.3), the `DELETE` endpoint's on-disk cleanup, and Phase A's upload-thread concurrency (now with
   the `chb06` evidence attached).
4. Update §2's repo map to list the 4 new `CC_STEP9_PHASE2_*` files alongside the existing Step 9
   entries.

## Report

Answer §1's two questions directly in your reply — no separate report file needed for those. For §2,
show the exact `git diff` (not `--stat`) of `BUILD_PROGRESS.md`. Raw `pytest -v`, `git status`.

Then stop. Do not run `git add`/`commit`/`push`.
