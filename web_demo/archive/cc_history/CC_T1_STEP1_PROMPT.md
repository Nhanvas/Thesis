# CC_T1_STEP1_PROMPT.md — backend on the final system (HANDOFF_T1 step 1) + panel title

**Estimated duration:** 60–90 min (estimate, not measured). **Laptop must stay plugged in and awake.**
Nothing else heavy may run (no real-data processing, no other long job).

Read first: `web_demo/CLAUDE.md` (rev 2026-10-10, wins over stale V1 text in other docs),
`docs/HANDOFF_T1_DEMO_REBUILD.md` §2, §3, §5, §6, `docs/DEMO_REBUILD_BRIEF.md`,
`web_demo/THESIS_CONTEXT_FOR_DEMO.md`.

Scope: HANDOFF step 1 only (backend on the final system, via the thesis-written reference patch) plus the
one-line panel-title change. Do NOT process any real recording, do NOT tag, do NOT push, do NOT touch
`src/`, `docs/`, `results/`, `UI/`, or any other doc. Never `git add .`.

## 1 · Preconditions (STOP and report if any fails)

```
cd /f/Study/Thesis/Code
git status -s                                   # no modified/untracked TRACKED web_demo files expected
git merge-base --is-ancestor f37a7b1 HEAD && echo base-ok
ls -l /f/Study/Thesis/Agent/t1_demo/t1_demo_reference.patch
ls src/*.py | head -50                          # confirm x1_external.py, p3_levers.py, e22_test_oneshot.py exist
sha256sum data/models_v2/gae_v2_clean_seed42.pt data/models_v2/gae_v2_clean_seed42.json
```

The two hashes must equal those in `web_demo/CLAUDE.md` "Model identity".

## 2 · Review the patch BEFORE applying (read-only)

`git apply --stat` the patch, then read all of it. Checklist — **any FAIL → do not apply, write the finding
to the report and STOP**:

a. No demo code CALLS a label-reading thesis function (list in CLAUDE.md "Three hard guards"). Importing the
   modules is fine.
b. Checkpoint `.pt` and `.json` sha256 verified against the constants above BEFORE loading; training
   constants for the 7 added features come from the `.json`, not typed in.
c. `stats_override` (thesis statistics) is unreachable from `main.py`, `upload_manager.py`,
   `pipeline_worker.py` and any HTTP path — gate use only.
d. Every write goes under `web_demo/`. Nothing writes to `results/`, `data/`, `docs/`.
e. k, smoothing, floor, cap come from `results/p3c_freeze/freeze.json`, point `"balanced"`, read at runtime;
   nothing hardcoded.
f. No budget / k / score parameter / metric is returned by any API endpoint or shown in the UI.
g. The §6 interface contract of the handoff exists with the stated names and return shapes
   (`MODEL_TAG`, `WIN_S`, `process_subject_headless(..., stats_override, timing)`,
   `process_subject_phase_b(filtered, flags, moments, stats_override)`,
   `process_subject_events(scores, flags, dists, trace)`, `export_tier2.py` writing `files.csv`,
   `{subject}_events.csv`, `MANIFEST.txt` with `commit <sha>` and
   `uncommitted changes in web_demo/backend or src: no|YES`).
h. Signal-loss windows: flagged on RAW std < 1e-10 V on all 18 channels, excluded from the per-subject fits,
   NaN distance, kept on the timeline.

## 3 · Apply

If HEAD is exactly one commit above `f37a7b1` for this patch's purposes use `git am`; otherwise
`git apply --3way`. Say which you used. Do not commit extra content with it.

## 4 · Panel title (UI-only)

`grep -rn "reconstruction anomaly" web_demo/backend web_demo/frontend/src` and change ONLY that title string
to `Channel-level latent anomaly — Event N`. Nothing else in the UI changes.

## 5 · Tests

Run `pytest web_demo/backend/tests -v`.

- `test_guards.py` must be 4/4 green. Never weaken it.
- Tests tied to the earlier system are invalid by design and must be replaced, not deleted blindly:
  bit-identity against tag `szscan-frozen-v2`, `FIXED_MAG_PCT/FIXED_PEN_MULT/FIXED_MERGE_S` reaching
  `detect_events`, "3 median/MAD calls", the V1 checkpoint hash. Write the final-system equivalents
  (flagged windows excluded from every fit and NaN/score handling; constants read from `freeze.json`;
  headless path == live Phase A + Phase B path; checkpoint hash enforced). List every test changed and why.
- Add a runtime label-guard test: monkeypatch each function in the forbidden list so it raises, run the
  synthetic-EDF pipeline end to end, assert nothing fires.
- Add a real-GAE test (real checkpoint, synthetic EDF, tiny). This needs `torch` / `torch_geometric` on the
  laptop; if unavailable, say so plainly instead of skipping silently.

## 6 · Commit

Commit locally, explicit `web_demo/` paths only, no push, no tag:
`web_demo: backend on the final system (GAE v2 clean seed42, per-channel latent, budget + CPD localizer)`

Co-Authored-By: Claude Sonnet 5.5 <noreply@anthropic.com>
Claude-Session: https://claude.ai/code/session_01DApMeNeryLNsMBUAaefvU4

## 7 · Report and STOP

Write `web_demo/CC_T1_STEP1_REPORT.md` containing: how the patch was applied; each checklist item a–h with
PASS/FAIL and evidence (file:line); files changed; tests changed and why; RAW `pytest -v` output; `git status -s`;
`git log -1 --stat`; anything not verified (the patch was only tested on synthetic EDFs with a fake GAE — say
what is still unproven on real data). Then stop; the next step is a smoke run on `chb16` driven by Boti.
