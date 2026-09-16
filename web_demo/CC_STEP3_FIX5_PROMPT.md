# CC_STEP3_FIX5_PROMPT.md — Step 3 closeout: verify 2 leftover items + apply C17 (Recording N display)

**Context:** Rounds 1–4 fixed every bug found in live browser testing so far (panel auto-close, overlay
layout, PROCESS gating, editable Project ID/Memo, minimize/restore, discard confirmation, progress bar
removal). This is the closeout round before Step 4 — two parts, both scoped tightly.

`web_demo/SZSCAN_SPEC_v5.md` has already been updated by the author (replace your copy with the version
attached/provided alongside this prompt — it now contains **C17** in §5.1 and a note in §1.5). Read the
new §5.1 and its footnote in full before touching code for Part B.

---

## Part A — verify the two items never manually tested in a browser

Both were only ever exercised via Claude Code's own `curl` calls in the original Step 3 build. Use
`claude-in-chrome` for both — actually click through, don't just hit the API.

### A1 — malformed/wrong-channel upload rejection

**Required behavior (SPEC §2):** a file that's the wrong format or missing the standard 18-channel
configuration is rejected from the pipeline and the Database, with the exact toast:
`File rejected — unsupported format or channel configuration.`

You'll need a real bad file to trigger this — none of the CHB-MIT test files are malformed, so construct
one (e.g. a tiny text file renamed to `.edf`, or a corrupted/truncated copy of a real EDF header). Upload
it through the real UI and confirm the toast appears verbatim and the file does not end up counted as
uploaded. If this doesn't work as specified, find the actual bug and fix it — don't blind-patch.

### A2 — single-subject concurrency lock

**Required behavior (SPEC §5.5, `UI/A1d`):** only one subject may be mid-pipeline system-wide, even
while minimized. Clicking "Create new" while another subject is processing must block with the message
shown in `UI/A1d`, not open a second panel.

Repro path: start a session for one allowlisted subject, upload file(s), click PROCESS (entering the
`processing` state), then click "−" to minimize (per SPEC this shows a `Processing...` toast). With that
still running, click "Create new" from the now-visible Database screen — confirm it's blocked with the
`UI/A1d` message rather than opening a new panel. If a small/fast subject finishes before you can test
this, use a subject with more files to give yourself a longer processing window.

If either A1 or A2 turns up a real bug, fix it (find the actual root cause) and say so clearly in the
report. If both already work correctly, say so with the same level of proof (screenshot description,
state captured mid-test) as prior rounds' reports — a bare "confirmed working" isn't enough on its own,
show what you actually observed.

---

## Part B — C17: change "Start date" from absolute date to `Recording N, HH:MM:SS`

**Author-approved design decision, not a bug.** CHB-MIT (via PhysioNet) applies a fixed per-patient date
shift to de-identify recordings — the year/date in `meas_date` is not real, though the shift is constant
within one subject, so *ordering*, *time-of-day*, and *spacing between recordings* are all still
meaningful; only the absolute year/date is fabricated. Read the new §5.1 in `SZSCAN_SPEC_v5.md` and its
footnote for the full reasoning — don't re-derive it.

**Required change — Database table's "Start date" column, both levels:**

- **Subject row:** `Recording 1, HH:MM:SS` — the time-of-day of the subject's *earliest* recording
  (N=1 always refers to the earliest).
- **Child file rows:** `Recording N, HH:MM:SS` — N is that specific file's position when all of the
  subject's files are sorted by `meas_date` ascending (N=1 for the earliest file, N=2 for the next, etc).
  HH:MM:SS is that file's own `meas_date` time-of-day.

**This N is a display-only ordering, computed by sorting on `meas_date`.** It is completely separate
from and must not change the existing filename-based sort used for event-offset assignment (SPEC §1.5) —
that pipeline logic is untouched by this round. Two different orderings, two different purposes; do not
conflate them (this is the exact distinction `edf_order.py`'s own docstring already draws between
"which file an event belongs to" vs "what position a file displays at").

**No absolute year or date should render anywhere in this column** — not in a tooltip, not in an
underlying attribute a screenshot might catch, nothing. If you find anywhere else in the frontend that
surfaces `meas_date`'s raw year (there shouldn't be any per the SPEC footnote's own audit, but check),
flag it in the report even if you don't think it needs changing this round.

**Verification:**
1. Create/inspect a subject with ≥2 files (e.g. `chb06` with multiple files) and confirm the subject row
   shows `Recording 1, HH:MM:SS` and each child row shows its correct `Recording N, HH:MM:SS`, with N
   ordering matching `meas_date` ascending (not necessarily filename order — check this distinction
   explicitly if the subject's files happen to have `meas_date` order matching filename order, note that
   you couldn't fully distinguish the two orderings with that data, and say so).
2. Confirm no absolute year/date renders anywhere in the Database table.
3. Confirm event-offset assignment (SPEC §1.5) still uses filename order, unchanged — quick regression
   check only (re-run a real Process cycle, confirm events land in the correct files as before).
4. Re-run `pytest web_demo/backend/tests/test_guards.py -v` and `git status`.

---

**Write your report to `web_demo/CC_STEP3_FIX5_REPORT.md`.** Cover both parts fully: A1/A2's findings
(bug found + fixed, or confirmed-working with proof) and C17's implementation + verification.

## Stop condition

This is intended to close Step 3 for good. Stop once Part A's two items are confirmed correct (fixed if
they weren't) and Part B's `Recording N` display is implemented and verified per the four checks above.
