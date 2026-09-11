# CC_STEP2_PROMPT.md — Step 2: Log in + empty Database + footer

**Prerequisite:** Steps 0 and 1 are both done (guards green, `pipeline_demo.py` working). If
`pytest web_demo/backend/tests/test_guards.py -v` isn't currently green, stop and say so first.

**Side note, non-blocking — answer in your report, don't investigate now if it costs real time:**
during the Step 1 filter-optimization work, `web_demo/UI/Annotaiton (format_ ID-summary.txt).png` got
modified (confirmed via `git diff --stat`, since reverted with `git checkout`). Do you know how that
happened? If you don't know, say so plainly rather than guessing.

Read before doing anything else, in this order:
1. `web_demo/CLAUDE.md`
2. `web_demo/SZSCAN_SPEC_v5.md` §0, §3, §4, §5.1, §5.2
3. `web_demo/DEMO_BUILD_HANDOFF.md` §6 (row 2)
4. **View the actual mockup images** — `web_demo/UI/A0a*.png` (Database, empty), `web_demo/UI/A0b*.png`
   (avatar/logout dropdown), `web_demo/UI/A0c*.png` (Log in). The PNGs win on anything visible
   (CLAUDE.md authority order) — don't build layout from the prose spec alone.

**Never write to anything under `web_demo/UI/`.** Read/view only. If your tooling opens an image and
re-saves it (this may be what happened to the PNG above), find a way to view it that doesn't touch the
file, or copy it to a scratch location first and view the copy.

## Goal (Step 2 of 9 — DEMO_BUILD_HANDOFF.md §6)

"Log in + Database rỗng + footer" — done when it matches `UI/A0c` (Log in) and `UI/A0a` (Database, empty)
closely enough for Boti to compare side by side.

## Scope boundary — read this twice

This step is the **shell only**. Do **not** build in this step (all of it is Step 3, HANDOFF §6 row 3):
- the "Create new" panel, file upload, or the Process pipeline trigger
- Search filtering behavior (§5.4)
- Delete / Open row actions (§5.6 / §5.7)
- any subject data — the database is empty by construction, there is nothing to seed

It's fine if the "Create new" button and the search box render visually (per the mockup) without being
wired to real behavior yet — a Step 3 TODO comment on each is enough.

## 1. Backend — minimal session auth

- Read `ADMIN_USER` / `ADMIN_PASS` from `web_demo/backend/.env` (never hardcode credentials in
  frontend code — CLAUDE.md). If `.env` has no real values yet, generate a simple dev-only
  username/password pair, write it into `.env`, and print it once in your final report so Boti can
  change it. This is explicitly **not** a real security mechanism (SZSCAN_SPEC_v5.md §4) — a simple
  session (signed cookie or in-memory token, your call) is enough. Don't over-engineer this.
- A login endpoint that checks credentials and starts a session; a logout endpoint that ends it.
- `web_demo/backend/db.py`: create the SQLite schema for subjects/files per SPEC §5.1's columns (ID,
  No. files, Start date, Duration, Alert, Status, Memo) — schema only, no seed data. An endpoint that
  lists subjects (returns an empty list right now, since nothing has been created).

## 2. Frontend — Log in screen (SPEC §4, `UI/A0c`)

- Single login form. **Password field must be `type="password"` (masked)** — the mockup shows it in
  plain text for illustration only, SPEC §4 is explicit that the real screen must mask it.
- No registration, no forgot/change password.
- **No footer disclaimer on this screen** — it's the pre-app screen (SPEC §4, §0).
- On success, navigate to the Database screen. On failure, show an error (match whatever the mockup
  shows, or a plain inline message if the mockup doesn't specify one).

## 3. Frontend — Database screen, empty (SPEC §5.1, `UI/A0a`)

- Header with the gradient chrome (`--header-gradient`, already in the Step 0 tokens) and an avatar in
  the top right that opens a dropdown with **Log out** (`UI/A0b`) — calls the logout endpoint, returns
  to Log in.
- Main table area: column headers per SPEC §5.1 (ID, No. files, Start date, Duration, Alert, Status,
  Memo), body showing the empty state. Match the mockup's exact empty-state wording and layout — SPEC
  §5.4 only gives the wording for the *no-search-results* variant (`No results for '...'`), so the
  plain empty-database wording comes from `UI/A0a` itself, not the spec prose.
- **Footer disclaimer bar, persistent** (SPEC §0): `#0F172A` background, white text, exact copy:
  `SzScan is an AI-assisted tool designed to support clinicians, not replace them.`
  This appears on every screen from here on except Log in.

## 4. Guard check + report

Run `pytest web_demo/backend/tests/test_guards.py -v` — new backend code, must still pass all four
(this touches no EEG/label logic at all, should be a trivial pass, but confirm it).

Run `git status` and paste the full output — confirm nothing outside `web_demo/` changed, and
specifically confirm nothing under `web_demo/UI/` shows as modified.

Give Boti the exact commands to start both the backend and the frontend dev server, so he can open it
in a browser himself and compare against `UI/A0a` / `UI/A0b` / `UI/A0c` — comparing the rendered app to
the mockups is his step, not something to describe in text.

## Stop condition

Report: guard test output, `git status` output, the dev-server start commands, the printed dev
credentials if you generated new ones, and the answer to the PNG side-note above. **Do not start
Step 3.**
