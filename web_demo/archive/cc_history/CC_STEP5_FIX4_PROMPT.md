# CC_STEP5_FIX4_PROMPT.md — Step 5 fix round 4

Round 3's playback fix and the 250 µV legibility check are accepted. Two follow-up questions from
Boti need verifying with evidence before Step 5 closes — don't guess either one.

## 1 · Do the low amplitude levels (5/7/10/15/20/30 µV) still serve a purpose?

Round 3 confirmed the new 12-value list; the low end still looked unusable on the busy window tested.
Before deciding whether to keep or prune the low levels, verify on a CALMER segment, not the busy one:

- Find a quieter/flatter stretch of `chb13_03.edf` (e.g. away from any stored event's onset/offset —
  check the file's stored events and pick a window at least a few minutes from all of them).
- Screenshot that segment at 10 µV, 20 µV, and 100 µV.
- Report whether the low settings (10/20 µV) show legible waveform detail there that 100 µV flattens
  out/loses. If yes, the low levels are earning their place (SPEC §6.4/C18's own stated reasoning) and
  should stay. If the low levels are illegible even on a calm segment, say so plainly and recommend
  pruning them — but don't prune anything yourself; report the finding and let Boti decide.

## 2 · Is Panel EEG showing raw or already-filtered data by default?

This matters for the demo's integrity claim (`CLAUDE.md`: everything shown must be data that genuinely
went into the computation) — verify precisely, don't assume from how it looks:

- Read the current frontend code for the `lff`/`hff`/`60` toggle buttons and the green-dot indicator
  next to each. State plainly what the green dot actually means (on/active vs. merely available), and
  what the *default* state of all three is on a fresh page load.
- Confirm via the network request/response (not just visual guess) which series (`raw` vs `filtered`,
  per `DEMO_BUILD_HANDOFF.md §5`) is actually being drawn as the primary line when all three filters are
  off. Per `SZSCAN_SPEC_v5.md §6.4` and `SZSCAN_DESIGN_v2.md §3`, the default view (no filters toggled)
  should show the RAW series; filtered should only draw on top once a filter is explicitly turned on,
  and raw must never fully disappear even then.
- If the current default is actually showing filtered/preprocessed data (all filters defaulting to on,
  or raw not being distinguishable), fix it so the default view is genuinely raw, and each filter toggle
  is independently switchable.
- Once correct, screenshot the same segment from item 1 in this order to show the real progressive
  effect of each step: (a) all filters off (raw only), (b) `lff` only on, (c) `lff` + `hff` on
  (bandpass), (d) `lff` + `hff` + `60` on (bandpass + notch) — matching the actual preprocessing steps
  in `preprocessing.py`. The four screenshots should look visibly different from each other if the
  filters are real and independently wired, not decorative.

## Report

Write to `web_demo/CC_STEP5_FIX4_REPORT.md`, with all screenshots. Run
`pytest web_demo/backend/tests/test_guards.py -v` and `git status` again at the end, raw output included.

## Stop condition

Stop once both items are answered with concrete evidence (screenshots + code/network confirmation, not
assertions) and the report is written. Do not start Step 6.
