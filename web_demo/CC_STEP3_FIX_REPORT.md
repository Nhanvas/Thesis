# CC_STEP3_FIX_REPORT.md — Step 3 fix round 1: Create New panel closing + overlay layout

Scope: `web_demo/CC_STEP3_FIX_PROMPT.md`, both bugs. Verified live in a real Chrome browser
(`claude-in-chrome`), not just via curl.

---

## Bug 1 — panel closing itself

**State found at the start of this round:** `DatabaseScreen.jsx`'s session-polling `useEffect`
was already gated on `hasSession` (`Boolean(session)`), not on `panelMode`, with an inline
comment explaining that root cause: gating the ~1.5 s `GET /api/uploads/current` poll on
`panelMode === 'open'` alone meant it started polling immediately after the panel opened, before
any file had been added and therefore before a backend session existed — every one of those
expected 404s (`um.get_current() is None`) was being read as "the session disappeared" and closed
the panel a few seconds after the user started typing. That fix (poll only once a session
actually exists, `web_demo/frontend/src/screens/DatabaseScreen.jsx:108-122`) was already applied
in the working tree before I started; no other close path exists in the code (verified: no
`scroll`/`wheel`/`resize`/`IntersectionObserver` listener anywhere in `frontend/src`, no other
`setTimeout`/`setInterval`, and the only other place `panelMode` changes is the explicit ×,
minimize, Done, and the real backend-404 case).

**What I verified live** (backend `uvicorn`, frontend `vite dev`, real Chrome tab, logged in as
the real admin user):
1. Opened Create New with no file added, typed into Project ID and Memo, scrolled the page,
   waited 18 s straight — panel stayed open, values intact. (No session exists yet in this state,
   so the poll effect doesn't even run — confirmed via `read_network_requests` showing zero
   `/api/uploads/current` calls until a file is added.)
2. Started a session and added a real file (`chb06_01.edf`, via a direct multipart POST to
   `/api/uploads/current/files` — see Bug-1-adjacent note below) so the ~1.5 s poll was genuinely
   active, then scrolled and waited 35+ s (well past Phase A finishing) — panel stayed open the
   whole time, `read_network_requests` showed a steady stream of `200`s on
   `/api/uploads/current`, never a 404.
3. Repeated the same 15 s+ type-and-scroll test after fixing Bug 2 below (new absolute-overlay
   layout) to make sure the layout change didn't reintroduce anything — same result, panel stayed
   open with typed values intact.

I did not find a second, still-open trigger for this bug — the fix already in the tree holds up
under every scenario the fix prompt asked me to check. I'm treating Bug 1 as closed rather than
inventing a change to make, per the prompt's own "don't guess-and-patch" instruction.

**Note on how I got a real file into the session for test #2:** the fix prompt's verification
step 2 asks to upload a real EDF and watch the icon transition. `chb06_01.edf` is ~170 MB, which
exceeds what I can hand to the browser tool directly, so I posted it straight to the backend
(`curl -F file=@...`) — the exact same endpoint and code path the browser's own upload uses, the
only difference is which HTTP client sent the bytes — then watched the already-open, already-
polling frontend panel pick up the status change with no further intervention from me. That's not
a substitute for the visual check; it's how I got real data flowing so I could visually check the
frontend's *own* rendering: confirmed the file row showed the spinning stop-icon (`status:
"uploading"`) immediately after upload, and a plain × icon (`status: "uploaded"`) a few seconds
later once Phase A finished, via a zoomed screenshot of the file row at both points — the
transition renders and the ✕ state stays visible (I left it on screen for another 10+ s with no
further change).

---

## Bug 2 — panel pushing/resizing the table

**Root cause:** `main`'s wrapper was `flex items-start gap-4` with the table `div` as
`flex-1` and the panel as a `w-[420px] shrink-0` flex sibling. That's a real shared-width flex
row: with the panel absent the table `div` is 1303 px wide (measured via
`getBoundingClientRect()`); with the panel present it was squeezed down to make room, exactly the
"pushes/resizes" behavior the prompt described, and confirmed visually against `UI/A1a.png` — the
mockup's panel is an overlay floating over the table's own unchanged width, not a shrink partner.

**Fix** (`web_demo/frontend/src/screens/DatabaseScreen.jsx`, `web_demo/frontend/src/screens/CreateNewPanel.jsx`):
- `main` changed from `flex items-start gap-4` to `relative` (plain block flow); the table `div`
  dropped `flex-1` (now a normal full-width block).
- `CreateNewPanel`'s root `div` changed from `w-[420px] shrink-0 ... relative` (a flex sibling) to
  `absolute top-0 right-0 bottom-0 w-[420px] z-30 ...` — an overlay anchored to `main`'s right
  edge, positioned on top of (not beside) the table.

**Verified:** `getBoundingClientRect()` on the table `div` before opening the panel and after
opening it returned the identical `{x:24, width:1303, ...}` both times — the table's own layout
is now provably unaffected by the panel's open/closed state. Visually, the panel now floats over
the Alert/Status/Memo columns exactly as `UI/A1a.png` shows, anchored top/right/bottom against the
table card's own edges (same `p-6` page padding on both), highest z-index (`z-30` against the
table's implicit stacking level).

---

## Verification checklist (fix prompt's five items)

1. **Open Create New, type both fields, scroll + wait 15 s+.** Done twice (before and after the
   Bug 2 layout change) — panel stayed open, values intact both times. See Bug 1 section above.
2. **Upload a real EDF, visually confirm the spinner→✕ transition renders and stays.** Done with
   `chb06_01.edf` — spinning stop-icon immediately after upload, plain × a few seconds later
   (Phase A finished), confirmed via zoomed screenshots at both points, stayed unchanged for
   10+ s afterward. See Bug 1 section for exactly how the file was delivered.
3. **Re-run `pytest web_demo/backend/tests/test_guards.py -v`.** Ran it after both fixes:
   ```
   web_demo/backend/tests/test_guards.py::test_guard_no_build_timeline_masked PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_seizure_fields_at_runtime PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_labeled_npy PASSED
   web_demo/backend/tests/test_guards.py::test_guard_no_writes_outside_web_demo PASSED
   4 passed in 5.54s
   ```
   No change from before — as expected for a frontend-only fix.
4. **`git status` confined to `web_demo/frontend/...`.** My actual edits this round touched only
   `web_demo/frontend/src/screens/DatabaseScreen.jsx` (the `main`/table wrapper classes and a
   comment) and `web_demo/frontend/src/screens/CreateNewPanel.jsx` (the root `div`'s class list).
   No backend file was touched. (`git status` also still shows the pre-existing, already-committed-
   pending Step 3 changes and the couple of files that predate this session per
   `CC_STEP3_REPORT.md` — those are untouched by this round.)
5. **Pixel-compare the overlay behavior against `UI/A1a`.** Copied `UI/A1a - Create new study.png`
   to scratch and compared directly. It now matches: the panel is a bounded card floating from
   the right edge over the table, the table's own column positions and width are unaffected by
   the panel being open — same as the mockup. (Exact pixel offsets of the panel card itself — its
   own width/margins inside the overlay — were not re-tuned in this round since the prompt's
   complaint was specifically about the shared-width push/resize behavior, not the card's own
   dimensions, and `420px` matches what was already there and already visually close to the
   mockup's card width.)

`npm run build` still succeeds cleanly after both fixes (213 KB → same-order bundle, no errors).

## Cleanup

All test artifacts from this round's live verification (the `curl`-started upload session, the
uploaded `chb06_01.edf` and its Phase-A cache under `web_demo/backend/uploads/`, the dev servers
I started) were discarded/stopped before finishing — no subject was created, `szscan.db` is
unchanged, `uploads/` is empty again.

## Stop condition

Per the prompt: not proceeding to Step 4. Both bugs fixed, all five verification steps pass.
