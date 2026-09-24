# CC_STEP6_FIX_PROMPT.md — Step 6, fix round 1: header layout/sizing, solid event blocks, Uncertain colour

**Context:** Step 6 (Select Range) was tested live by Boti and works correctly and per spec. Do **not**
touch Select Range behaviour, event creation/edit/delete logic, or the event numbering you implemented.
This round is visual adjustments only, all approved by Boti (the final decision-maker).

**Prerequisite:** `pytest web_demo/backend/tests/test_guards.py -v` green before you start.

**Do not run any `git add` / `git commit` / `git push`.** Boti commits himself. Do not touch anything
outside `web_demo/`. Do not reset the review states or the test events currently stored for
`chb13_03.edf`.

Use `claude-in-chrome` from the start. If it is not connected, say so immediately and stop (do not fall
back to Playwright/curl — the visual checks here need the real browser).

## Read first

1. `UI/B1a*.png`, `UI/B2a*.png` (Analysis header + mini-timeline), `UI/A0c*.png` / `UI/A0a*.png`
   (Database header) — copy to scratch first, view them.
2. `web_demo/SZSCAN_DESIGN_v2.md` §1, §2, §9, §10.
3. `frontend/src/components/Header.jsx`, `frontend/src/eventStyle.js`,
   `frontend/src/components/MiniTimeline.jsx`, the Event Time strip inside `EegPanel.jsx`,
   `frontend/src/index.css` (`:root` tokens), `tailwind.config.js`, `design-tokens.js`.

**Resolution warning:** the mockup PNGs are lower resolution than the live app. Compare **proportions**
(fractions of header height / viewport width), never absolute pixel sizes.

## Scope — five changes

### 1. Analysis header: move the button group next to the file dropdown

Currently `Previous / Next | Viewed / Export` sit right after the title. In the mockup they sit in the
**right-hand cluster, immediately to the left of the file-select dropdown**. Move them there. The title
`<ID> (<N> alerts to check)` stays on the left. Keep the thin divider between `Previous/Next` and
`Viewed/Export`. Do not change button behaviour, enabled/disabled logic, or the Progress bar (Boti
accepts the progress bar as-is).

### 2. Header sizing: logo + wordmark and avatar are too large

The `SzScan` logo mark + wordmark (left) and the avatar circle (right) look oversized compared with the
mockup. Measure, from the locked PNGs, the header height, logo-mark height, wordmark height and avatar
diameter, each as a fraction of header height. Measure the live values with `getBoundingClientRect()`.
Resize the live elements to match the mockup's proportions.

`Header.jsx` is shared across screens. **Only change a screen where the live app differs from that
screen's own locked mockup** (compare `UI/A0c`/`A0a` for Database, `UI/B1a`/`B2a` for Analysis). If the
Database screen already matches its mockup and only Analysis is off, fix it in a way that does not alter
the Database screen. In the report, state per screen (Log in has no in-app header — check only if it
uses the same component) what changed and what did not.

Do not change the header gradient, colours or the footer.

### 3. Event blocks: solid colour, no hatch

Boti wants event blocks on the **mini-timeline "Detections" row** to be full solid colour, like the
design, not hatched.

In the shared `blockStyle()` in `eventStyle.js`:
- Remove the diagonal hatch on Reject blocks.
- Use the **full-opacity token colour** for the fill for each review status (drop the per-status
  ~75% / ~55% opacity) — that is the interpretation of "full màu"; state in the report that this is what
  you did.
- **Keep unchanged:** the dimming rule (other events drop to ~40% opacity while one is selected), the
  violet selected outline, Human = solid `#2563EB`, unreviewed AI = current token, and the block
  geometry/position.

The same helper also feeds the Event Time strip under the EEG canvas. Check `UI/B2*` and `UI/B3*`: if the
mockup shows solid blocks there too, the shared change applies to both; if the mockup shows a different
treatment for the strip, keep the strip per the mockup and report the difference instead of guessing.

If the current Unseen / Accept colours on screen differ from what the mockup shows (the mockup
`Detections` row shows grey blocks), **do not change them** — just report the difference with a
screenshot.

### 4. Uncertain colour → `#FFE262`

Boti's decision: the Uncertain amber (`#D97706`) reads too close to the Reject red and sinks into the
background. Change the Uncertain status colour to **`#FFE262`**.

- Change it in the single source of truth (`index.css` `:root` → `--color-uncertain`), and keep
  `design-tokens.js` / `tailwind.config.js` consistent — no second hard-coded hex anywhere.
- It applies everywhere the Uncertain colour is used as a fill: mini-timeline block, Event Time strip
  block, Event Panel row left bar, any status dot/icon, the Uncertain option in the expanded event.
- A light yellow is illegible as **text on white**. Where the Uncertain token is used as a text or thin
  icon-stroke colour on a light background, add `--color-uncertain-text: #D97706` (the old value) and use
  that there, so labels stay readable.
- Leave `--color-uncertain-bg` (`#FFFBEB`) alone, but report if it has become visually
  indistinguishable from the white/cream surfaces.
- **Visibility check (important):** `#FFE262` on the cream EEG canvas (`#FEFBEF`) and on white may be low
  contrast. Take a screenshot of an Uncertain block on the mini-timeline, on the Event Time strip and on
  its Event Panel row. If it is not clearly visible, **do not invent extra styling** (no added borders or
  shadows) — report it with the screenshot and let Boti decide.

### 5. Update `SZSCAN_DESIGN_v2.md` to match (English, minimal edits)

- §2 Axis 2 table: Uncertain colour `#FFE262`; note the text-use variant `#D97706`.
- §2 mini-timeline / Event Time rules: Reject is now a solid block with no hatch, and status blocks use
  the full token colour. Add one sentence recording that this is the author's decision, and that it
  relaxes principle 3 ("never colour alone") for these blocks — status text remains on Event Panel rows
  and badges.
- §9 token block and §10 change table: add the new/changed rows (with the reason: Uncertain amber read
  too close to Reject red; hatch dropped to match the mockup).
- Edit only those lines. Do not reformat the file, do not change line endings, do not rewrite it whole.

## Verification (evidence required — screenshots and measured values, not code-read confidence)

Save screenshots to `web_demo/CC_STEP6_FIX_SCREENSHOTS/`.

1. **Before** screenshots of the Analysis header and mini-timeline for `chb13_03.edf`.
2. **After**, Analysis header: the button group sits adjacent to the file dropdown, title on the left.
   Literal side-by-side with the `UI/B1a` / `B2a` header.
3. Measured values: header height, logo-mark height, wordmark height, avatar diameter — live vs mockup
   as proportions of header height, in a small table in the report.
4. Database screen header (and Log in if it shares the component) — before/after screenshots proving
   they still match their own mockups (`UI/A0c`, `A0a`) or, if they were off too, what was fixed.
5. Mini-timeline with all review states visible (the states already stored for `chb13_03.edf`, plus
   the Human test events already there — do not change them): **pixel-sample** the fill of one block per
   status, with no event selected, and confirm: Reject `#DC2626` solid (no hatch pattern — sample
   several pixels across the block), Accept `#16A34A`, Uncertain `#FFE262`, Human `#2563EB`.
6. Select one event: confirm the other blocks drop to ~40% opacity (computed style), the selected block
   has the violet outline, and the selected block's fill is unchanged.
7. Event Time strip under the EEG canvas: same colour/hatch check as item 5 (or the mockup-driven
   exception from scope item 3).
8. Event Panel: an Uncertain row shows the new colour on its left bar; its text badge is readable (screenshot).
9. Visibility screenshots for `#FFE262` per scope item 4.
10. Quick Select Range regression: create one disposable manual event, confirm it appears with the Human
    blue block, then Delete it and confirm Alert returns to its previous value in the header.
11. `pytest web_demo/backend/tests/test_guards.py -v` and `git status` / `git diff --stat` — **raw output**
    pasted into the report. Confirm nothing outside `web_demo/` changed.

## Report

Write `web_demo/CC_STEP6_FIX_REPORT.md` (a file, not terminal output). Include: what changed per file,
the measurement table (item 3), the exact interpretation choices made (opacity, strip vs mockup), any
mockup-vs-live differences you found but deliberately did not change, and the test-state note (which
events remain in `chb13_03.edf`).

## Stop condition

Do not start Step 7. Stop once items 1–5 are done, verified live with evidence, and the report is written.
