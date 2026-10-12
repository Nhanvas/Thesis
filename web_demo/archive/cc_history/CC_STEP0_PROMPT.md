# CC_STEP0_PROMPT.md — Step 0: repo scaffold, Tailwind tokens, test_guards.py

Read before doing anything else, in this order:
1. `web_demo/CLAUDE.md`
2. `web_demo/DEMO_BUILD_HANDOFF.md` §1, §2, §6 (row 0)
3. `web_demo/SZSCAN_SPEC_v5.md` §1.2 (the three hard guards + the write guard)
4. `web_demo/SZSCAN_DESIGN_v2.md` §9 (design tokens)

## Goal (Step 0 of 9 — DEMO_BUILD_HANDOFF.md §6)

"Khung repo, token Tailwind từ SZSCAN_DESIGN_v2.md §9, test_guards.py chạy PASS" — done when the tests
are green. Do not start Step 1 work in this session.

## 1. Folder structure

Per HANDOFF §2, create (touch nothing outside `web_demo/`):

```
web_demo/backend/
web_demo/backend/tests/
web_demo/frontend/
web_demo/cache/
```

Add `web_demo/cache/` to `.gitignore`.

In `web_demo/backend/`, create these as thin stub files (docstring only, e.g.
`"""Step N will implement this. See DEMO_BUILD_HANDOFF.md §6."""`) — do NOT implement logic yet, that
happens in later steps:
- `main.py`
- `pipeline_demo.py` (Step 1 will fill this in)
- `db.py`
- `export_txt.py`

Add `web_demo/backend/.env.example`:
```
ADMIN_USER=
ADMIN_PASS=
```
Do not create a real `.env` — that stays local and gitignored, Boti fills it in by hand.

## 2. Frontend scaffold + Tailwind tokens

Set up Vite + React + Tailwind in `web_demo/frontend/`. Generate:
- `tailwind.config.js`
- the Tailwind base stylesheet (e.g. `src/index.css`)
- `src/design-tokens.js` — the same values as a plain JS export, for anything that needs raw hex outside
  a Tailwind class name (e.g. canvas drawing code for the EEG waveform later)

**Copy the `:root { ... }` CSS variable block from `SZSCAN_DESIGN_v2.md §9` verbatim.** Do not re-derive,
round, or approximate any hex value — they were pixel-sampled from the locked PNGs in `web_demo/UI/`, not
guessed. Map every token into `tailwind.config.js`'s `theme.extend` (colors, fontFamily, radius, shadow).

Fonts: Inter + IBM Plex Mono, **downloaded and self-hosted** under `web_demo/frontend/public/fonts/` (or
equivalent), referenced with local `@font-face` rules — no Google Fonts CDN `<link>` or `@import`. The
defense machine may have no internet (HANDOFF §1).

## 3. `test_guards.py` — the four guards

Write `web_demo/backend/tests/test_guards.py`. It scans the `web_demo/` source tree (backend + frontend
source; exclude `node_modules`, `venv`, `.git`, `web_demo/cache/`) and **fails the build** if any of:

1. Any Python file imports or calls `szcore_eval.build_timeline_masked` — scan for that name (AST or
   text) across `.py` files under `web_demo/`.
2. Any Python file reads the fields `Seizure Start Time`, `Seizure End Time`, or `Number of Seizures`
   from a `chb*-summary.md` path at runtime — i.e. string literals matching those field names used in a
   file-parsing context under `web_demo/`. Do **not** flag `File Name`, `File Start Time`, `File End
   Time`, or duration parsing — those are explicitly allowed (SZSCAN_SPEC_v5.md §1.2).
3. Any Python file loads `{subj}_interictal.npy` or `{subj}_ictal.npy` — pattern-match `_interictal.npy`
   / `_ictal.npy` in any `open(...)`, `np.load(...)`, `Path(...)` call under `web_demo/`.
4. Any file under `web_demo/` writes to `results/`, `data/models_retrain/`, `data/processed/`, or
   `docs/` — scan for those path strings passed to `open(..., 'w'/'a')`, `np.save`, `Path(...).write_text`,
   `torch.save`, etc., anywhere under `web_demo/`.

For each guard: one **positive** test (a small injected-violation fixture must be caught) and one
**negative** test (the current clean `web_demo/` tree passes with zero false positives). Use `pytest`,
four independently named test functions so a failure is legible, e.g.:
- `test_guard_no_build_timeline_masked`
- `test_guard_no_seizure_fields_at_runtime`
- `test_guard_no_labeled_npy`
- `test_guard_no_writes_outside_web_demo`

## 4. Run and report — then stop

Run `pytest web_demo/backend/tests/test_guards.py -v`. Fix any failures yourself (self-correct, don't ask
permission mid-step per CLAUDE.md's working rhythm). **Stop once all four tests PASS.**

Report back:
- the final `web_demo/` folder tree
- full pytest output
- confirmation that nothing outside `web_demo/` was created or modified
- a one-line note if you had to deviate from anything above, and why

Do not proceed to Step 1 in this session.
