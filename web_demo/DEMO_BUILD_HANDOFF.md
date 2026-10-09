# DEMO_BUILD_HANDOFF.md — SzScan build plan

Rev. 2026-10-03. **All nine build steps are done.** This file is kept as the record of stack, folder
structure and working process; current state and open items are in `BUILD_PROGRESS.md` §14 and §18.

Behavior/logic: `SZSCAN_SPEC_v5.md`. Visuals: `SZSCAN_DESIGN_v2.md`. Locked mockups: `UI/`.
What the demo may assume about the thesis: `THESIS_CONTEXT_FOR_DEMO.md`.

---

## 1 · Stack — all free

| Layer | Choice | Reason |
|---|---|---|
| Backend | **Python + FastAPI** | Python is mandatory: real inference uses torch/torch_geometric, can't be rewritten in JS. FastAPI is lightweight, low boilerplate |
| Review storage | **SQLite** (1 `.db` file) | Built into Python, nothing to install, enough for a single-user demo |
| Frontend | **React + Vite + Tailwind v3** | Tokens in `SZSCAN_DESIGN_v2.md §9` map straight onto the Tailwind config |
| Waveform rendering | **Hand-written Canvas** | Ordinary chart libraries stutter when drawing 18 channels × thousands of points |
| Font | Inter + IBM Plex Mono | **Bundled locally**, not loaded via CDN (the defense venue may have no internet) |
| Running at the defense | 1 start command, entirely local, **no internet needed** | Network-off full run passed (2026-09-28) |

**No Figma MCP.** Every hex/spacing value was measured directly from the PNGs and recorded in
`SZSCAN_DESIGN_v2.md`.

**The demo machine = the dev machine.** No portable build or installer.

---

## 2 · Folder structure

Same repo, `F:/Study/Thesis/Code`, because the demo reuses the single-source modules
(`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `edf_order.py`), which must not be copied.

```
web_demo/
├── CLAUDE.md                  # rules for Claude Code (read before coding)
├── SZSCAN_SPEC_v5.md          # behavior/logic/data boundaries
├── SZSCAN_DESIGN_v2.md        # visual tokens
├── DEMO_BUILD_HANDOFF.md      # this file
├── BUILD_PROGRESS.md          # history log (append-only sections)
├── THESIS_CONTEXT_FOR_DEMO.md # what the demo may assume about the thesis
├── PROJECT2_SETUP.md          # how the Claude project is set up + upload list (shared file)
├── UI/                        # locked PNGs + UI (figma).fig  ← MANDATORY REFERENCE
├── backend/
│   ├── main.py                # FastAPI app
│   ├── pipeline_demo.py       # ★ continuous label-free path (fixed operating point, signal-loss rule)
│   ├── pipeline_worker.py     # Phase A worker process
│   ├── upload_manager.py      # upload → Phase A (concurrency cap) → Phase B orchestration
│   ├── db.py                  # SQLite schema + queries
│   ├── attribution.py         # channel-level reconstruction anomaly (p95 |robust-z| vs baseline)
│   ├── waveform_serving.py    # decimated min/max envelope serving
│   ├── edf_order.py           # display order of files (header time), not processing order
│   ├── export_txt.py          # export file per SPEC §7
│   ├── .env.example           # ADMIN_USER / ADMIN_PASS (the real .env is NOT committed)
│   └── tests/
│       ├── test_guards.py          # ★ four integrity guards
│       └── test_signal_loss_v3.py  # signal-loss rule tests (9 tests pass at commit 3336bd7)
├── frontend/
├── report_handback/           # tier-2 CSVs, timing, memory, scripts, figures handed to the report side
└── cache/                     # gitignored
```

---

## 3 · Handling legacy code

| File | Action | Reason |
|---|---|---|
| `edf_index.py` | **Does NOT exist, does NOT need to be rewritten** | Belonged to the v3 architecture and was deleted. The v5 architecture derives each file's offset by construction — `SZSCAN_SPEC_v5.md` §1.5 |
| `web_demo/backend/edf_order.py` | **Keep unchanged** | **Display** order (real EDF header time) differs from **processing** order (FILE NAME — the locked convention). Real mismatch cases exist, e.g. `chb03_24/25` |
| `src/cpd_pipeline_v14.py`, `ensemble_recipe.py`, `szcore_eval.py`, `retrain/gae_joint.py` | **Read-only** | Single-source, shared with the thesis |
| `src/szcore_eval.build_timeline_masked()` | **FORBIDDEN to call from the demo** | Requires ground truth — `SZSCAN_SPEC_v5.md` §1.2 |

Two concerns, not to be conflated: "which file does this event belong to" (cumulative offset, SPEC §1.5)
and "what position does this file show at in the UI" (`edf_order.py`).

Operating-point constants are **not** pulled from `src/retrain/fp_budget_operating_point.py` any more:
the live path uses one fixed point set in `pipeline_demo.py` (`FIXED_MAG_PCT`, `FIXED_PEN_MULT`; v3 code
adds `FIXED_MERGE_S`). `calibrate_operating_point()` survives only in the dev `__main__`.

---

## 4 · `pipeline_demo.py` — the core of the demo

The **label-free twin** of the thesis path; it never overwrites any module in `src/`.

```
# Phase A — per file, runs as soon as a file finishes uploading
read 18 standard channels → bandpass 0.5–60 + notch 60 → 4 s windows, NONE dropped
  (t_seconds = idx * 4, exact 1-1 mapping)
flag signal-loss windows (raw std < 1e-10 V on all 18 channels) → {stem}.flag.npy
z-score per channel (stats on the subject's entire set; not masked)
CAR → wPLI + AEC → top-k 20 % → node feat [adj-row 18 | band-power 5]
GAE (checkpoint by sha256) → zrecon, Z ; zgamma = continuous gamma-AEC

# Phase B — when "Process" is clicked
sort files by FILE NAME (not display order)
zlatent = Mahalanobis(Z, LedoitWolf fit on all non-flagged windows)
robust-z per branch (flagged windows excluded from the fit) → equal-weight 1/3 ensemble
flagged windows → score 0
cpd_pipeline_v14 on the concatenated score with the FIXED operating point; flagged windows excluded
  from the background statistics (inter_mask)
offsets = cumulative window counts over files; each event goes to the file holding its onset
  (offset may run past that file's end — not clipped)
```

Divergences from the thesis pipeline are recorded in `SZSCAN_SPEC_v5.md` §1.6 — read it, do not
re-derive them.

---

## 5 · Waveform — technical note

18 channels × 256 Hz × 1 hour = 16.6 million points per file; never sent raw to the browser.

- The backend serves the currently viewed window, **decimated** to ~2–4 points per pixel as a min/max
  envelope (naive subsampling would lose the spikes the clinician needs to see).
- Changing window length → new backend call with a different decimation level.
- Changing amplitude → **frontend-only**.
- The filter control is a **single Preprocessed toggle** (C24), **ON by default** (C27); the backend can
  return raw and preprocessed series in one call.
- The mini-timeline pages by 1 h (C26).

---

## 6 · Build order — status

| # | Step | Status |
|---|---|---|
| 0 | Scaffold, Tailwind tokens, `test_guards.py` | done |
| 1 | `pipeline_demo.py` + CLI, real timing measured | done |
| 2 | Log in + empty Database + footer | done |
| 3 | Create new → upload → Process → subject in table | done |
| 4 | Analysis: EEG Panel + toolbar + scrub | done |
| 5 | Mini-timeline + Event Panel + 3-panel sync | done |
| 6 | Select Range creates a manual event | done |
| 7 | Attribution Panel | done |
| 8 | Export `.txt` | done |
| 9 | All 8 subjects built; live-upload subject chosen | done — live `chb16`, backup `chb03` |

Post-step changes (C24, C26–C28) are in the SPEC. Frozen evaluated build: tag `szscan-frozen-v2`
(commit `0ffd99b`, Phase A concurrency 2).

---

## 7 · Working process with Claude Code

**Autonomous within a task, stop between tasks.** Claude Code does the small work itself (files, edits,
tests, fixing its own errors); at the end of a task it stops so Boti can compare the running app against
the mockups.

- Every prompt states an estimated duration and whether the laptop must stay plugged in and awake.
- Long prompts live in a file (`web_demo/X.md`); the message to Claude Code is "Read and execute
  web_demo/X.md".
- Verification is against raw console output pasted by Boti, never a self-report.
- Commits touch `web_demo/` paths only, by explicit path (never `git add .`). Two sessions at once only
  on disjoint paths. Never run the demo on real data while another heavy job runs.
- **Boti holds final decision-making authority** on every substantive choice.

### Freeze procedure

Any change to code that affects pipeline output (constants, checkpoint, filters, concurrency, masks):
guards 4/4 → commit `web_demo/` paths only → new tag → back up `szscan.db` and `*.score.npy` → wipe via
the real Delete endpoint → re-run **all 8 subjects** from an empty DB. Never a single subject. UI-only
changes need no re-run but are tagged separately and not described as the evaluated build.

---

## 8 · Measured figures (frozen v2 build)

Two timing figures, never interchangeable:

| Figure | Value | What it is |
|---|---|---|
| Processing only, sequential | **21.9 s per hour of EEG** | `chb06_01.edf` repeated, median, range 21.5–22.6 |
| End to end, whole run | **≈ 12.3 s per hour** | 8 subjects, 231 EDF, 279.39 h in 57 min 27 s, including upload, two Phase A workers |

Peak memory 10.2 GB (`chb06`). Earlier figures (9.76, 10.83, "~15 s/hour") are superseded. Per-file
timing was not logged in the clean run.

Runtime environment of that run: pagefile on `F:`, `TMP/TEMP/TMPDIR` on `F:/tmp`.

---

## 9 · Known risks

| Risk | Handling |
|---|---|
| Demo numbers differ from the report | Prepared answer in `SZSCAN_SPEC_v5.md` §1.6 |
| Live upload + Process takes minutes, not seconds | Live subject `chb16`, chosen by measured total time (≈5.7 min end to end in the earlier pre-freeze measurement — the fastest of the 8; re-time before the defense); pre-built copies of all 8 subjects are the insurance, backup live subject `chb03` |
| Memory exhaustion on `chb06` when another heavy job runs | Run nothing else heavy during a demo run; Phase A cap 2 |
| Ground truth leaks into the demo | `test_guards.py` (4 guards) |
| Event edges, loudest raw moment and top attribution channel disagree (seen on `chb06`) | Prepared answer, not a bug: they are different quantities (`BUILD_PROGRESS.md` §16–§17) |
| Committee sees internal labels | Committee-facing wording rule in the Instructions |
| Timeline: report due 15 Oct, defense 5–6 Nov | The report is priority 1; the evaluated v2 build with its pre-built database is the insurance |

---

*End of DEMO_BUILD_HANDOFF.md.*
