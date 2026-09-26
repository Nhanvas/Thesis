# CC_STEP9_PROMPT.md — Step 9, phase 1: inventory + cleanup (NOT the full cache build)

Read first: `web_demo/DEMO_BUILD_HANDOFF.md §6` row 9 and `§1.7` (Cost — measured, decided to run
live) and `§8` (Known risks), `web_demo/BUILD_PROGRESS.md §13` (open items — especially the synthetic-
subject item and the `chb06` real-upload item), `web_demo/STEP8_9_PREDEFENSE_CHECKLIST.md §2` (Tier 2
rules — for context only; this prompt does **not** run Tier 2).

**This step is deliberately split into two phases.** This prompt covers only **phase 1**: find out
exactly what real vs. synthetic data currently exists in the DB, clean up what must go, and report
back — before any multi-hour compute begins. Per `DEMO_BUILD_HANDOFF.md §7`'s own "stop between steps"
rule, do **not** proceed to phase 2 (actually running the pipeline on missing real subjects / building
the insurance cache) without a separate prompt once phase 1's findings have been reviewed.

Guards unchanged: `test_guards.py` must stay 4/4 green at the end, no write outside `web_demo/`, no
`git add`/`commit`/`push`.

---

## Part 1 — Inventory: what's really in the DB right now

For **each** of the 8 allowlisted TEST subjects (`chb03, chb06, chb13, chb14, chb15, chb16, chb17,
chb18`), determine and report:

- Does a DB row exist for this subject at all?
- If yes: how many files, and are they **real** EDFs originating from
  `F:/Study/Thesis/Dataset/CHB-MIT/{subject}/`, or synthetic/renamed clips (per `BUILD_PROGRESS.md
  §13`'s note that `chb14`/`chb15`/`chb16` were built from `chb15` clips)? Check by comparing each
  file's actual size/duration against the real EDF on disk for that subject and filename — don't infer
  from the DB filename string alone, since a renamed clip would look real by name.
- Per-file review state (`View`/`Viewing`/`Viewed`).
- Whether the subject already has real cached pipeline output (`.pernode.npy`, `pernode_baseline.npy`,
  `.score.npy` etc.) that looks genuine by the same real-vs-synthetic check, not just present.

This resolves two standing open items directly, with evidence instead of assumption:

1. Whether `chb06`'s apparent 18-file, full Progress upload (seen live in Boti's own screenshots this
   session) is genuinely the real ~4-hour, full-file-count subject, or still the old partial/synthetic
   state `BUILD_PROGRESS.md §8.5` described (`chb06` "has never been uploaded through the actual
   Create-New flow").
2. Exactly which of `chb14`/`chb15`/`chb16` are still synthetic and need removing, and whether any of
   the 8 real subjects (`chb03`, `chb17`, `chb18` in particular — not otherwise mentioned as tested
   yet) have no data in the DB at all.

## Part 2 — Remove synthetic data

Per `BUILD_PROGRESS.md §13` ("must be removed before any demo run") and
`STEP8_9_PREDEFENSE_CHECKLIST.md §2` item 2 (now also a hard Tier 2 requirement): delete every subject
row that Part 1 confirms is synthetic — not just hide it, actually delete it via the existing Delete
flow (or the equivalent DB-level delete plus matching cache-file cleanup), so no trace remains that
could later be mistaken for real data. Confirm afterward: the DB contains only subjects that are either
genuinely real (verified in Part 1) or entirely absent — never a subject row known to hold synthetic
data under a real subject's name.

## Part 3 — Report, then stop

Write `web_demo/CC_STEP9_PHASE1_REPORT.md`:

1. The full 8-subject inventory table from Part 1 (real/synthetic/absent, file counts, review states,
   cache status).
2. Exactly which subject rows were deleted in Part 2, with confirmation nothing synthetic remains.
3. A clear split of the 8 real subjects into: **ready** (real EDFs already uploaded, processed, and
   cached) vs. **needs a real upload** through Create-New before phase 2 can build cache for them.
4. A rough time estimate for uploading + processing whatever is missing, derived from
   `SZSCAN_SPEC_v5.md §1.7`'s own measured cost figure (read the actual `9.76 s/hour of EEG` figure
   from the file at build time, don't retype it from memory) and each missing subject's real file
   count/total duration on disk — so Boti can decide how to sequence phase 2 (all subjects in one long
   run, one at a time, overnight, etc.) instead of a long run starting blind.
5. Raw `pytest -v`, `git status`.

Then **stop. Do not run `git add`/`commit`/`push`. Do not start phase 2** — building cache files or
uploading any missing real subject is a separate prompt, to be written once this report is reviewed.
