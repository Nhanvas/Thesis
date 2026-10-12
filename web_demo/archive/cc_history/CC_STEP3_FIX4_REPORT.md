# CC_STEP3_FIX4_REPORT.md — Step 3 fix round 4: minimize/restore bug + 2 author decisions + font check

Scope: `web_demo/CC_STEP3_FIX4_PROMPT.md`. All edits this round are frontend-only
(`web_demo/frontend/src/screens/CreateNewPanel.jsx`, `web_demo/frontend/src/screens/DatabaseScreen.jsx`) —
nothing from rounds 1–3 needed re-touching, and no backend change was required for any of the four
items. Rounds 1–3 re-verified at the end, all still hold.

---

## Bug — minimize/restore reverts edits

**Root cause, confirmed exactly as the prompt suspected:** `DatabaseScreen.jsx` rendered
`CreateNewPanel` only when `panelMode === 'open'`, so minimizing (`panelMode = 'minimized'`) fully
unmounted the component — destroying its local `projectId`/`memo` React state — and restoring
re-mounted a brand-new instance, whose `hydratedRef`-guarded seed effect then fired again (this
*is* a true first mount for that instance) and overwrote whatever the user had typed with the
session's last-known `project_id`/`memo`.

**Fix applied — the cleanest option, exactly as suggested:** `CreateNewPanel` now stays mounted for
the panel's entire `open`/`minimized` lifetime; only a `hidden` prop toggles visibility.

- `DatabaseScreen.jsx`: the render condition changed from `panelMode === 'open'` to
  `panelMode === 'open' || panelMode === 'minimized'`, and a `hidden={panelMode === 'minimized'}`
  prop is passed through. The component only actually unmounts when `panelMode` becomes `'closed'`
  (a real discard or Done) — which is exactly when losing local state is correct.
- `CreateNewPanel.jsx`: root `<div>`'s className now switches between `flex` (visible) and `hidden`
  (Tailwind's `display:none` utility) based on the new `hidden` prop, instead of always being
  `flex`. These two are never combined in the same class list (only one is ever present), so there's
  no Tailwind utility-ordering/specificity conflict between `.hidden{display:none}` and
  `.flex{display:flex}`.
- `hydratedRef`'s one-shot seed effect itself needed **no logic change** — it already only seeds
  once per component instance; keeping the instance alive across minimize/restore is what makes
  "once" mean what it was originally meant to mean (true first mount / session restored after a
  page reload), not "once per minimize cycle."

No reason was found to make this impractical (no other code assumes `CreateNewPanel` unmounts on
minimize), so the suggested next-best alternative (lifting state to `DatabaseScreen`) wasn't needed.

**Verified** (`claude-in-chrome`, real browser):
- **No files yet, mid-typing:** opened a fresh draft, typed `chb06typed` into Project ID (no file
  added, no backend session exists yet), clicked "−", clicked the "Create New (draft)" toast to
  restore — field showed `chb06typed` exactly, unchanged.
- **Files already uploaded:** started a session for `chb06` with `chb06_01.edf` already uploaded
  (via the backend — see the note in round 3's report on why large CHB-MIT files are POSTed
  directly rather than through the browser's own file picker), reloaded once to hydrate the panel
  (`chb06` / `chb06_01.edf` showing ✕), then **triple-clicked and retyped `chb06test`**, clicked
  "−", clicked the toast to restore — Project ID showed `chb06test` exactly (not the original
  `chb06`), Memo and the file list both intact. This is the exact author repro, now fixed.

---

## Decision 1 — confirmation dialog on × (discard draft)

Implemented by reusing `ConfirmDialog.jsx` unmodified (imported into `CreateNewPanel.jsx`), rendered
as an overlay inside the panel's own root (which is already `position: absolute`, so
`ConfirmDialog`'s `inset-0` fills exactly the panel's box, the same containing-block relationship
`DatabaseScreen.jsx` already relies on for the delete-subject dialog).

- **Wording chosen:** *"Discard this draft? Any uploaded files and progress will be lost."* — states
  what's actually at stake (an in-progress draft, uploaded files, background Phase A/B work) without
  reusing the delete-subject wording ("Are you sure you want to delete this process?"), which is
  about a different, already-saved-to-the-Database entity.
- **Conditional per the prompt:** `hasDraftContent()` = Project ID non-empty (trimmed) OR Memo
  non-empty (trimmed) OR at least one file present in `session.files`. A completely untouched panel
  (blank fields, no session) skips the dialog and closes immediately — I didn't find a reason this
  reading is wrong; it matches the prompt's own justification ("nothing to confirm") and the
  existing `discardUpload()` call is still made whenever a session exists regardless of which path
  was taken, so no session/lock is ever leaked by the fast path.
- **Yes/No wiring:** "Yes" (`handleConfirmDiscard`) runs exactly what × used to do unconditionally —
  `discardUpload()` if a session exists and isn't processing/done, then `onClose()`. "No" just clears
  the `confirmDiscard` flag, returning to the panel with all state (fields, files) untouched — it
  never touched anything to begin with.

**Verified:**
- Non-empty Project ID (no files): × → dialog appeared with the exact wording above → "No" →
  returned to the intact panel, typed value still there → × again → "Yes" → panel closed, back to
  the Database screen, no session left behind (confirmed via `GET /api/uploads/current` — no
  session existed here since no file had been added, so there was nothing to leak in the first
  place; the with-files case below is the real leak-check).
- Files present (`chb06_01.edf` uploaded under a real session): × → same dialog → "Yes" → panel
  closed; `GET /api/uploads/current` afterward 404s (no session) and `uploads/` no longer contains
  the draft's files after cleanup — confirms `discardUpload()` still ran and freed the session lock.
- Completely blank, untouched panel (opened fresh, nothing typed, no files): × closed immediately,
  no dialog rendered at all.

## Decision 2 — remove the progress bar

Removed the `<div className="w-full h-2 rounded-full ...">...</div>` progress-bar element from both
the `session?.processing` branch and the `session?.done` branch in `CreateNewPanel.jsx`. Each now
renders only spinner+text (processing) or checkmark+text+Done button (done), nothing else changed.

**Mockup comparison:** copied `UI/A2a - Processing.png` and `UI/A2b - Done processed.png` to scratch
and compared directly. **Both mockups do show a full-width filled progress bar** (a solid bar under
the "Please wait for processing…" text in A2a, and a fully-filled bar under "Upload Complete!" in
A2b) — flagging this discrepancy for the author's awareness per the prompt's own instruction, while
still removing the bar per the explicit instruction in this round (SZSCAN_DESIGN_v2.md §8's "no fake
percentage" reasoning is the more specific, currently-authoritative instruction here since it's a
deliberate reversal of what the static mockup shows, not an oversight).

**Verified:** ran a real single-file upload → PROCESS click → the "Processing subject — combining
files and detecting change points…" screen showed only the spinner and text (screenshotted, zoomed);
it resolved to "Upload Complete!" showing only the checkmark, text, and "Done" button (screenshotted)
— no bar in either state.

## Font check

Compared the Processing/Upload-Complete panel against `UI/A2a`/`A2b` visually, then confirmed
programmatically rather than by eye alone: `getComputedStyle()` on both the "Processing subject…"
paragraph and the "Upload Complete!" paragraph returned `font-family: "Inter, sans-serif"`, identical
to `document.body`'s computed font. Tracing why: `index.css`'s `body { font-family: var(--font-ui) }`
sets Inter (self-hosted `@font-face`, files present under `public/fonts/`) for the whole app, and
nothing in `CreateNewPanel.jsx` sets a conflicting `font-family` anywhere — no `font-mono` or inline
style on any element in this panel. **No code was broken and no fix was needed here**: the font was
already correctly Inter by inheritance, confirmed by computed style, not just visual impression. My
best guess for what the author actually saw is that the now-removed progress bar (an element not
used anywhere else in the app's visual language) made the panel read as visually inconsistent with
the rest of the UI even though the text itself was already rendering in the right font — plausible
but not something I can confirm after the fact, so I'm reporting the measurement rather than a
speculative diagnosis.

---

## Verification checklist (prompt's seven items)

1. **Minimize/restore preserves edits, with and without files.** Both scenarios verified above (Bug
   section) — exact typed values survived in both cases.
2. **× with non-empty content or an uploaded file → dialog → No intact → Yes discards cleanly.**
   Verified above (Decision 1) for both the no-files and with-files cases; "No" confirmed to return
   with the typed value untouched (screenshotted mid-test).
3. **× on a completely blank panel closes immediately, no dialog.** Verified — screenshotted the
   Database screen immediately after clicking ×, no `ConfirmDialog` rendered.
4. **Real upload → Process cycle shows no progress bar in either state.** Verified via a real
   `chb06_01.edf` upload and PROCESS click through to a subject correctly appearing in the table
   (`chb06`, 1 file, Alert 7) — screenshotted both the processing and done states, neither shows a
   bar.
5. **Font screenshot + comparison.** Screenshotted and zoomed the "Processing subject…" state;
   `getComputedStyle` confirms `Inter, sans-serif` on both panel states, matching the rest of the
   app (see Font check above).
6. **Rounds 1–3 regression check.**
   - Round 1 (no auto-close): opened a fresh draft, typed a Project ID, scrolled, waited 8s — stayed
     open, value intact.
   - Round 1 (overlay layout): `document.querySelector('main > div').getBoundingClientRect().width`
     measured identical (1318 px) with the panel open and closed.
   - Round 2 (PROCESS gates on upload only): the same real process cycle in item 4 above exercised
     this end-to-end successfully (PROCESS was clickable as soon as the file showed ✕, and the
     existing `_wait_phase_b_then_process` mechanism was untouched this round).
   - Round 3 (Project ID/Memo editable): triple-click-and-retype worked both before minimizing (as
     already shown in round 3's own report) and is now additionally proven to survive minimize too,
     which is what this round's bug fix is about.
7. **Guards + git status.**
   ```
   pytest web_demo/backend/tests/test_guards.py -v
   web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
   4 passed in 1.95s
   ```
   ```
   git status --short
    M .gitignore
    M tables/tables_ch2.md
    M web_demo/backend/db.py
    M web_demo/backend/main.py
    M web_demo/backend/pipeline_demo.py
    M web_demo/frontend/src/api.js
    M web_demo/frontend/src/components/icons.jsx
    M web_demo/frontend/src/screens/DatabaseScreen.jsx
   ?? check_t8p8.py
   ?? docs/VERIFIED_CORRECTIONS.md
   ?? web_demo/CC_STEP3_FIX2_PROMPT.md
   ?? web_demo/CC_STEP3_FIX2_REPORT.md
   ?? web_demo/CC_STEP3_FIX3_PROMPT.md
   ?? web_demo/CC_STEP3_FIX3_REPORT.md
   ?? web_demo/CC_STEP3_FIX4_PROMPT.md
   ?? web_demo/CC_STEP3_FIX_PROMPT.md
   ?? web_demo/CC_STEP3_FIX_REPORT.md
   ?? web_demo/CC_STEP3_REPORT.md
   ?? web_demo/backend/pipeline_worker.py
   ?? web_demo/backend/upload_manager.py
   ?? web_demo/frontend/src/components/ConfirmDialog.jsx
   ?? web_demo/frontend/src/screens/CreateNewPanel.jsx
   ```
   This round's only edits are inside `web_demo/frontend/src/screens/CreateNewPanel.jsx` (already
   untracked/new from Step 3, so no `M` line for it) and `web_demo/frontend/src/screens/DatabaseScreen.jsx`
   (shows as the existing `M` line — unchanged from before this round in file identity, just further
   edited). No backend file was touched this round. `check_t8p8.py` at the repo root is not mine —
   it's an unrelated MNE channel-debugging script (references `src/dataprep/preprocessing.py`,
   CHB-MIT files) that showed up as untracked before I started; leaving it alone, consistent with
   `tables_ch2.md`/`docs/VERIFIED_CORRECTIONS.md` predating this session per earlier rounds' reports.

## Stop condition

Per the prompt: not proceeding to Step 4. Minimize/restore now preserves edits in both tested
scenarios, both author decisions are implemented and verified, the font is confirmed correct
(computed-style, not just visual), and rounds 1–3 all still hold.
