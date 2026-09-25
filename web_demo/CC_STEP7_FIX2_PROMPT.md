# CC_STEP7_FIX2_PROMPT.md — Step 7, fix round 2: attribution scoring definition

Read first: `web_demo/CLAUDE.md`, `web_demo/CC_STEP7_REPORT.md` §3 (items 2–3, the two PROVISIONAL
defaults), `web_demo/CC_STEP7_FIX_REPORT.md`, and `src/attribution_pipeline.py` lines ~495–525 — read the
real file, do not trust any paraphrase, and confirm line 519 does `np.abs(...)` before the p95 at line
520.

This closes the two PROVISIONAL defaults from Step 7 (aggregation + score shown). Decided by the thesis
project (2026-09-25), confirmed here. **This is the SAME divergence already recorded in `SZSCAN_SPEC_v5.md`
§1.6(a) — not a new one.** The only change from the thesis formula is baseline scope (whole-subject
recording instead of interictal-only); everything else is identical.

Guards that still apply: 4/4 green at the end, no `git add/commit/push`, no CPD/events-table write, sha256
of every `.filtered.npy`/`.raw.npy`/`.score.npy` under `web_demo/backend/uploads/` unchanged. Use
`claude-in-chrome` for live checks; if not connected, stop and say so. **Do not click Save on any real
`chb13` event or its attribution status** — Boti clears event 46's attribution status by hand before this
round runs (see Part 8; not your job).

**Files you may edit this round:** `web_demo/backend/attribution.py`, `pipeline_demo.py`,
`pipeline_worker.py`, `backfill_pernode.py`, `web_demo/SZSCAN_SPEC_v5.md`, `web_demo/CLAUDE.md`,
`web_demo/THESIS_CONTEXT_FOR_DEMO.md`, `web_demo/PROJECT2_SETUP.md`. Do not touch
`AnalysisScreen.jsx`, `AttributionPanel.jsx`, `PanelEvent.jsx`, `eventStyle.js`, `MiniTimeline.jsx`,
`EegPanel.jsx`, `attributionStyle.js` — the round-1 layout/position/colour work is final. The one narrow
exception is Part 3 below (display decimal places), and only if it turns out to require a frontend touch.

---

## Part 1 — Attribution formula (backend)

Implement exactly, per channel:

```
med   = median(base, axis=0)                    # [18]
mad   = median(|base - med|, axis=0) + 1e-9     # [18], NO 1.4826 factor
z     = |(r_event_windows - med) / mad|         # per window, per channel, absolute value
score = percentile(z, 95, axis=0)               # [18] — event-level score
rank  = argsort(-score) + 1                     # 1..18, highest first
```

- `base` = every window of **every file belonging to the same subject** as the event's file, drawn from
  each file's `.pernode.npy`. **Per-subject scope, not per-file** (the 2026-09-12 decision already on
  record — do not re-derive it).
- `med`/`mad` (the baseline) are computed **once, in Phase B** (the subject-level Process step) and
  persisted to disk as `{subj}.pernode_baseline.npy` — two 18-length float32 vectors; choose a concrete
  on-disk layout (e.g. stacked `[2, 18]`, or two separate arrays — your call, just document exactly what
  you picked) and say so in the report. **Never recompute the baseline on an attribution read.**
- Consequence to implement correctly, not just note: adding a new file to an existing subject and
  reprocessing changes the baseline — and therefore every event's score/rank for that subject — only when
  that subject's Process step reruns. Same rule already governs the other per-subject stats (z-score,
  LedoitWolf); don't special-case attribution.
- `attribution.py`'s `get_event_attribution` loads the persisted baseline file and applies the formula
  above to the event's windows. If the baseline file is missing for a subject (not yet backfilled), return
  the same `{"available": false, ...}` shape already used for the missing-`.pernode.npy` case (Step 7
  Part 4 item 12) — do not silently fall back to computing it on the fly.
- Rank is computed from the **unrounded internal score**, never from the rounded display value — two
  channels may legitimately display the same 2-decimal number while still having a well-defined internal
  order; do not reorder based on what's shown.

## Part 2 — Backfill for existing subjects

Extend `backfill_pernode.py` (a clearly separate function or CLI flag — don't conflate with the existing
per-node backfill) to compute and write `{subj}.pernode_baseline.npy` for every subject currently in the
DB, reading only each file's already-cached `.pernode.npy`. **Must not run CPD, must not touch the
`events` table, must not re-read raw EDFs.** Run it once; report which subjects got a baseline file
(expect `chb13`, `chb14`, `chb15`, `chb16` — whatever is actually in the DB right now).

## Part 3 — Frontend display (only if strictly necessary)

Display: `|z|` (already non-negative — no sign-formatting problem), **2 decimal places**.

Check where the current 5-decimal formatting lives (`AttributionPanel.jsx` or the API response itself).
- If the API already sends a pre-rounded value/string and the frontend just renders it: change the
  rounding at the API layer only (`attribution.py`/`main.py`), touch nothing in `AttributionPanel.jsx`.
- If the decimal count is hardcoded in `AttributionPanel.jsx` (e.g. `.toFixed(5)`): this is the one
  permitted exception to "don't touch the frontend" — change only that formatting call, nothing else in
  the file (no layout, no colour, no structure). State plainly in the report which case it was.

## Part 4 — Gate checks (all must pass before declaring this round done)

1. **Independent recompute**, read-only Python, for one AI event on `chb13_03.edf` (any of ids 46–49),
   from `.pernode.npy` + the persisted baseline file — must match the live API's returned score/rank.
   The API may round for display; use a tolerance matched to the **displayed** precision (2 decimals →
   tolerance ≤ 0.005), not 1e-9.
2. **sha256** of every `.filtered.npy`/`.raw.npy`/`.score.npy` under `web_demo/backend/uploads/`
   unchanged — same three-checkpoint style as Step 7 round 1 (before Part 1/2, after, after all live
   testing).
3. `pytest web_demo/backend/tests/test_guards.py -v` → 4/4, raw output.
4. **Ranking genuinely changed.** Re-run the independent recompute on a second event and report its new
   top-3 channels side by side with `CC_STEP7_REPORT.md §3`'s old top-3 for the same event id, so the
   change from raw-score to p95-|z| is visible, not just claimed.
5. **Display-collapse check.** For every event tested, confirm the 18 displayed 2-decimal values are not
   an artifact of over-rounding relative to the internal score's actual spread — i.e. if two channels
   round to the same displayed number, verify their internal scores are genuinely close (report the
   unrounded values for any such pair), not that precision was lost the way 4-decimals once did in Step 7
   round 1.

## Part 5 — `SZSCAN_SPEC_v5.md` updates

**C20:** replace the PROVISIONAL wording for items 2–3 with: score = 95th percentile of `|robust-z|`
across an event's windows; robust-z computed per channel against a whole-subject baseline (median/MAD
over every window of every file belonging to that subject, from `.pernode.npy`; no 1.4826 factor). Same
formula as `src/attribution_pipeline.py` (lines ~514–520), differing only in baseline scope (whole-subject
recording, not interictal-only) — **the same divergence already in §1.6(a), not a new one.**

**§1.6:** restructure the divergence list into exactly **three** items, matching the thesis report's own
enumeration:
1. Normalization statistics, covariance (`LedoitWolf`), and robust-z fit on the whole recording, with no
   artifact rejection — the attribution baseline (this round) belongs to this same item.
2. No post-ictal buffer exclusion.
3. Background statistics for the PELT penalty and the CPD threshold, estimated on the whole recording.

Keep every existing piece of evidence (the chb06/chb13 AUROC/Spearman table, the post-ictal
justification, the prepared committee answer) — this is re-grouping into 3 numbered items, not a rewrite.
If anything currently in §1.6 doesn't cleanly fit one of the three, say so in the report instead of
force-fitting it.

## Part 6 — `CLAUDE.md` correction

Replace "~16.9 ms per 4 s window ⇒ ~15 s per hour of EEG" with the true **end-to-end** measured figure:
**9.76 s per hour of EEG**, measured end-to-end on a real 4-hour recording (`chb06_01.edf`), CPU, Step 1
(`BUILD_PROGRESS.md`). State plainly that run-to-run variation was about **5×** — keep that caveat, don't
drop it. The 13.2 ms + 3.7 ms = 16.9 ms/window component breakdown may stay **only if clearly labeled as
component-level, not the end-to-end figure** — otherwise remove it so the two numbers aren't read as the
same thing.

## Part 7 — `THESIS_CONTEXT_FOR_DEMO.md` §5 and `PROJECT2_SETUP.md` §9.2(B) correction

Attribution evaluation is now **closed**, not provisional: labels were produced by blind human readers,
the evaluation was approved, the result is negative (does not support a localization/SOZ reading). Remove
"PROVISIONAL" and any leftover numeric evaluation figure from both files. **The panel's own UI wording
does not change** — still no metric shown on screen, still "not localization, not SOZ." This is a
documentation-only correction about the evaluation's status, not a product change.

## Part 8 — Manual pre-step (report only — do not execute)

State in the report, don't act on it: Boti clears the 18 test `attribution_status` rows on
`chb13_03.edf` event id 46 by hand (open the event → `Clear all` → `Save`) before running this prompt,
if they were only a test — this round's new baseline/formula changes that event's ranking, and the old
saved statuses were keyed to the old one.

---

## Report

Write `web_demo/CC_STEP7_FIX2_REPORT.md`: 1 summary; 2 exact formula + baseline file format chosen;
3 backfill output (which subjects got a baseline); 4 Part 3 finding (frontend touched or not, and why);
5 all 5 gate results with numbers; 6 the three spec-doc diffs (SPEC/CLAUDE/CONTEXT+SETUP); 7 confirmation
of the manual pre-step reminder; 8 raw `pytest -v`, `git status`, `git diff --stat`. Then **stop. Do not
run git add/commit/push. Do not start Step 8.**
