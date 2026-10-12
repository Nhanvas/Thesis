# CC_STEP8_FIX_PROMPT.md — Step 8 fix round 1

Read first: `web_demo/CC_STEP8_REPORT.md` (this step's own prior report — all four items below refer
back to specific sections of it), `web_demo/SZSCAN_SPEC_v5.md` §7 (export structure, in full).

This is a **fix round on Step 8** (Export `.txt`), not a new step. Four items, all reviewed and
confirmed by Boti. Guards that still apply, unchanged: `test_guards.py` must stay 4/4 green at the
end, no write outside `web_demo/`, no `git add`/`commit`/`push`.

---

## 1 · Score formatting — fixed `.6f`

`CC_STEP8_REPORT.md` §6.1's sample export shows inconsistent digit counts across scores in the
Channel Attribution tables — e.g. `1.27291` (5 digits) next to `0.050504` (6 digits) — because
Python's default float-to-string conversion drops trailing zeros after `round(x, 6)`.

Fix: wherever `export_txt.py` prints a channel's score, format it as a **fixed 6-decimal string**
(`f"{score:.6f}"`), so every score line has exactly 6 digits after the decimal point regardless of
trailing zeros. This is a print-format change only — do **not** touch the underlying stored/computed
precision, which stays exactly what `attribution.py` already returns (6-decimal internal rounding,
confirmed unchanged since Step 7 fix round 2).

## 2 · Verify file order — proven, not just claimed

Round 1's live test only covered `chb13` (`chb13_02.edf`, `chb13_03.edf`), where file-name order and
`meas_date`/Recording-N order happen to coincide. That test could not actually distinguish "sorted by
file name" (the correct rule — `SZSCAN_SPEC_v5.md §7.1`, and the original `CC_STEP8_PROMPT.md`'s own
instruction to use file-name order, "not the `meas_date` 'Recording N' display order used elsewhere")
from "sorted by `meas_date`" (wrong — that's the Database screen's Recording-N order, a completely
different concern; `edf_order.py`'s own module docstring and `SZSCAN_SPEC_v5.md §1.5` both go out of
their way to keep these two orderings from ever being conflated).

Do this in order:

1. Read `export_txt.py`'s `build_subject_export` (or whatever the report's own naming turns out to be)
   and quote **verbatim** the exact query / `ORDER BY` clause or Python sort key it uses to order a
   subject's files. State plainly whether it sorts by file-name string, by `meas_date`, or by DB
   insertion/row order — don't infer, quote the actual line.
2. If it is **not** explicitly sorting by file-name string, fix it to sort by file name, matching
   §7.1's "exactly matching the original structure of CHB-MIT's `chbXX-summary.txt`" and the
   file-name-order convention that `edf_order.py`'s docstring documents as the locked processing-order
   rule.
3. Check whether any subject currently in the DB (the real 8-subject allowlist or the known synthetic
   test subjects) has files whose file-name order and `meas_date`/Recording-N order actually **differ**
   — list each file's name alongside its derived Recording-N position directly, don't guess. If one
   exists, run the export on it and show the resulting file order in the output, confirming it follows
   file-name order even where that diverges from Recording-N order. If no such subject currently exists
   in the DB, say so plainly and don't fabricate one for the test — reading the sort code directly
   (step 1) is sufficient evidence on its own when no differing-order subject is available.

## 3 · Comment for the guard-2 string-split workaround

`export_txt.py` currently writes the required "Number of Seizures in File" label as two concatenated
string halves to avoid guard #2's string-matching false positive (`CC_STEP8_REPORT.md §5.4`) — this
was the right fix (a *write* of a self-computed count, not a *read* of ground truth) and stays exactly
as-is, no logic change.

Add a short comment immediately above that line explaining **why** the string is split, without
spelling out the guarded phrase itself anywhere in the comment (the guard scans comments too, and
re-triggering it here would be circular) — e.g. reference this fix round and report section instead
of the literal phrase, something like:
```python
# String deliberately split across two literals — see CC_STEP8_REPORT.md §5.4 / this file's
# item 3 for why the whole phrase must never appear as one literal in this tree.
```
Word it however reads clearest, as long as the guarded phrase itself never appears whole. After
adding it, re-run `pytest web_demo/backend/tests/test_guards.py -v` and confirm it is still 4/4 —
this specific check matters, since the whole point of item 3 is making sure the comment doesn't
accidentally reintroduce the flagged phrase.

## 4 · Record the settled `N`-interpretation in the spec

This was an open judgment call in the initial Step 8 report (`CC_STEP8_REPORT.md §3`); Boti has now
confirmed it as a real decision, not a placeholder: `N` in `Number of Seizures in File: N` = the count
of every `Event` block listed below that file — **AI (including Rejected) + Human, combined**. The
field records everything the clinician is being shown as "this many things worth flagging," whether
the system flagged it (and it was later Accepted, Rejected, Uncertain, or never reviewed) or the
clinician drew it by hand with Select Range. This is now locked, not open.

Add a short, dated note to `SZSCAN_SPEC_v5.md §7.2` recording this — in the same terse style as the
existing C17–C21 notes elsewhere in that file (a short addition to the existing bullet or a small
parenthetical, not a new full section). Keep it factual and short: what `N` counts, that it's the
author's confirmed decision, and today's date. Don't touch anything else in §7.2/§7.3's wording.

---

## Report

Write `web_demo/CC_STEP8_FIX_REPORT.md`:

1. Summary of what changed, in the same order as the four items above.
2. Item 2's exact `ORDER BY`/sort key, quoted verbatim, plus the differing-order-subject check result
   — either a real subject was found and tested (show the export's resulting file order), or none
   exists in the current DB and that's stated plainly.
3. Item 1's before/after formatting, using the same two example scores from the original report
   (`1.27291` → `1.272910`, `0.050504` → confirm it stays `0.050504` i.e. unchanged) so the fix is
   directly visible against what was flagged.
4. Item 3's exact comment text as added, plus the guard re-run output (raw, not summarized).
5. Item 4's exact diff added to `SZSCAN_SPEC_v5.md §7.2`.
6. Raw `pytest -v`, `git status`, `git diff --stat`.

Then **stop. Do not run `git add`/`commit`/`push`.**
