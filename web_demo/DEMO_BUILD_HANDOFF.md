# DEMO_BUILD_HANDOFF.md — SzScan build plan

**Status: LOCKED to start coding.** This file collects the stack, folder structure, working process, and
how to handle legacy code. Fully absorbs `WEB_DEMO_CODE_MIGRATION_NOTES.md` (→ `docs/archive/demo_v4/`).

Behavior/logic: `SZSCAN_SPEC_v5.md`. Visuals: `SZSCAN_DESIGN_v2.md`. Locked mockups: `UI/`.

---

## 1 · Stack — all free

| Layer | Choice | Reason |
|---|---|---|
| Backend | **Python + FastAPI** | Python is mandatory: real inference uses torch/torch_geometric, can't be rewritten in JS. FastAPI is lightweight, low boilerplate |
| Review storage | **SQLite** (1 `.db` file) | Built into Python, nothing to install, enough for a single-user demo |
| Frontend | **React + Vite + Tailwind** | Tokens in `SZSCAN_DESIGN_v2.md §9` map straight onto the Tailwind config, almost copy-paste |
| Waveform rendering | **Hand-written Canvas** | Ordinary chart libraries (recharts…) stutter when drawing 18 channels × thousands of points. Must render by hand |
| Font | Inter + IBM Plex Mono | Google Fonts, free. **Downloaded and bundled with the app**, not loaded via CDN (the defense venue may have no internet) |
| Running at the defense | 1 start command, runs entirely locally, **no internet needed** | Eliminates network/deploy risk |

**No Figma MCP.** The `.fig` file has real layers, but Dev Mode MCP is a paid tier and isn't needed: every
hex/spacing value has already been measured directly from the PNGs and recorded in `SZSCAN_DESIGN_v2.md`.
If more measurements are needed later, two free routes: read pixels from the PNG, or open Figma and copy
values by hand via Inspect.

**The demo machine = the dev machine.** No need to package a portable build/installer.

---

## 2 · Folder structure

Uses the **same repo**, `F:/Study/Thesis/Code` — because the demo reuses the exact single-source modules
(`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `edf_index.py`, `edf_order.py`), which must
not be copied/duplicated. This is also a complete product in its own right, so it should live in the same
place.

```
web_demo/
├── CLAUDE.md                  # rules for Claude Code (read before coding)
├── SZSCAN_SPEC_v5.md          # behavior/logic/data boundaries
├── SZSCAN_DESIGN_v2.md        # visual tokens
├── DEMO_BUILD_HANDOFF.md      # this file
├── PROJECT2_SETUP.md          # how to set up Claude project #2 + upload file list
├── UI/                        # locked PNGs + UI (figma).fig  ← MANDATORY REFERENCE
├── backend/                   # created by Claude Code
│   ├── main.py                # FastAPI app
│   ├── pipeline_demo.py       # ★ continuous label-free path (NEW code, see §4)
│   ├── db.py                  # SQLite schema + queries
│   ├── export_txt.py          # generates the export file per SPEC §7
│   ├── .env.example           # ADMIN_USER / ADMIN_PASS (the real .env file is NOT committed)
│   └── tests/
│       └── test_guards.py     # ★ integrity tests, see CLAUDE.md
├── frontend/                  # created by Claude Code
└── cache/                     # precomputed demo-pipeline output (gitignored)
```

`web_demo/backend/` and `web_demo/frontend/` **do not exist** until coding starts — Claude Code creates
them.

---

## 3 · Handling legacy code

| File | Action | Reason |
|---|---|---|
| `edf_index.py` | **Does NOT exist, does NOT need to be rewritten** | Belonged to the v3 architecture and has been deleted from the repo. The v5 architecture derives each file's offset by construction — see `SZSCAN_SPEC_v5.md` §1.5. The old `WEB_DEMO_CODE_MIGRATION_NOTES.md` describes it as an available module; that document has been archived |
| `web_demo/backend/edf_order.py` | **Keep entirely unchanged** | Independent concern: the **display** order of files in the UI (by the real time in the EDF header) differs from the **processing** order (by FILE NAME — the locked convention needed to match the thesis results). There are real mismatch cases like `chb03_24/25`. Moved from `docs/demo/` to here on 2026-09-03; demo-only, not shared with the thesis |
| `src/cpd_pipeline_v14.py`, `ensemble_recipe.py`, `szcore_eval.py`, `retrain/gae_joint.py` | **Read-only, do not edit** | Single-source, shared with the thesis |
| `src/szcore_eval.build_timeline_masked()` | **FORBIDDEN to call from the demo** | Requires ground truth — see `SZSCAN_SPEC_v5.md` §1.2 |

Don't conflate the two concerns: "which file does this event belong to" (cumulative offset,
`SZSCAN_SPEC_v5.md` §1.5) and "what position does this file show at in the UI" (`edf_order.py`).

⚠️ **Before pulling parameters from `src/retrain/fp_budget_operating_point.py`**, check that the import
chain actually runs — `evaluation_protocol.py` and `stat_validation.py` were mistakenly archived once and
were only restored to `src/` on 2026-09-03 (tag `repo-deps-fixed`, details in `docs/REPO_MAP.md` §7.7).

---

## 4 · `pipeline_demo.py` — the new code, the core of the demo

No module in the repo does this yet. This is the **label-free twin** of the thesis path, and it must
**never overwrite** any module in `src/`.

```
# stage 1 — runs as soon as 1 file finishes uploading
def process_file(edf_path) -> np.ndarray:      # continuous ensemble score over time
    read the 18 standard channels (drop EKG/EOG/Ref)
    bandpass 0.5–60 + notch 60
    cut into 4 s windows, do NOT drop any window     # ⇒ t_seconds = idx * 4, exact 1-1 mapping
    z-score per-channel, stats fit on the subject's ENTIRE set of windows
    CAR → wPLI + AEC → top-k 20% → node feat [adj-row 18 | band-power 5]
    GAE seed42 forward → zrecon, Z
    zlatent = Mahalanobis(Z, LedoitWolf fit on the ENTIRE Z)
    zgamma  = gamma-AEC (continuous version — see O5 in SPEC §8)
    robust-z per branch → equal-weight 1/3 ensemble
    return score            # length exactly equals the file's window count

# stage 2 — runs when "Process" is clicked
def process_subject(files) -> dict[file -> list[Event]]:
    files_sorted = sort by FILE NAME          # NOT display order
    global_score = concat([score[f] for f in files_sorted])
    events_global = cpd_pipeline_v14.detect_events(global_score, ...)   # label-free
    op = FP-budget operating point (read the parameter from file, see SPEC §8 O1)
    offsets = cumulative sum of len(score[f]) over files_sorted     # no lookup module needed
    for ev in events_global:
        file = f such that offsets[f] <= ev.onset_win < offsets[f] + len(score[f])
        assign ev to that file's event list, local onset = ev.onset_win - offsets[file]
```

**Four places where fitting differs from the thesis pipeline** — recorded and justified in
`SZSCAN_SPEC_v5.md §1.6`. Read before writing, don't re-derive it from scratch.

---

## 5 · Waveform — important technical note

18 channels × 256 Hz × 1 hour = **16.6 million points/file**. Do not send this straight to the browser.

- The backend serves the waveform for the **currently viewed time window**, **decimated** down to
  ~2–4 points/pixel (min/max envelope, not naive subsampling — subsampling would lose sharp spikes, and
  spikes are exactly what the clinician needs to see).
- Changing the window length (`⊲▷ [X] hr`) → calls the backend again with a different decimation level.
- Changing the amplitude (`⇕ [X] uV`) → **frontend-only**, just rescales, no backend call.
- Toggling the filter → the backend returns **both series** (raw + filtered) in one call, the frontend
  layers them itself.

---

## 6 · Build order — lock each screen once it's built

| # | Step | Done when |
|---|---|---|
| 0 | Repo scaffold, Tailwind tokens from `SZSCAN_DESIGN_v2.md §9`, `test_guards.py` passing | tests green |
| 1 | `pipeline_demo.py` + CLI runs on 1 file → prints the score length. **Measure real timing** | matches the ~15 s/hour estimate |
| 2 | Log in + empty Database + footer | compare against `UI/A0c`, `A0a` |
| 3 | Create new → upload → Process → subject appears in the table | compare against `UI/A1a–A2b`, `A4a` |
| 4 | Analysis: EEG Panel + toolbar + scrub (no events yet) | compare against `UI/B1a`, `B1b`, `B1d` |
| 5 | Mini-timeline + Event Panel + 3-panel sync | compare against `UI/B2a–B2d` |
| 6 | Select Range creates a manual event | compare against `UI/B3a–B3c` |
| 7 | Attribution Panel | compare against `UI/B2a` |
| 8 | Export `.txt` | compare against `UI/Annotaiton (format_ ID-summary.txt).png` |
| 9 | Build cache for 8 subjects + pick the subject for the live-upload scenario | have the measurements |

**Step 1 must finish before step 2.** If the label-free pipeline produces nonsensical results (e.g. zero
events for every subject), it must be caught now — not after 8 UI screens have already been built.

---

## 7 · Working process with Claude Code

**Run autonomously within one step, stop between steps.** Within one step from §6, Claude Code does all
the small work itself (creating files, editing, test-running, fixing its own errors) without asking
line-by-line. Once a step is done, **stop**, so Boti can open the real app and compare it against the
mockups before moving to the next step.

Reason for this pace: running the whole app freely and only reviewing it at the end means one small
early misunderstanding repeats across all 9 steps; asking permission at every small step is too slow and
wastes the point of automation. This level of autonomy is adjustable if it doesn't feel right.

**Boti holds final decision-making authority** on every substantive choice, per the project's overall
convention.

---

## 8 · Known risks

| Risk | Handling |
|---|---|
| Label-free pipeline produces results far from the thesis (too many/too few events) | Caught at **step 1**, before building the UI. If the deviation is too large, adjust the **operating point** (label-free, legitimate) — **do not** touch the model, **do not** use labels to adjust |
| Processing 17 files takes ~6 minutes during a live demo | Pick a subject with few files for the live scenario; pre-cache the rest |
| Committee asks why the demo's numbers differ from the report | Prepared answer in `SZSCAN_SPEC_v5.md §1.6` |
| Ground truth accidentally leaks into the demo | `test_guards.py` blocks it in CI/local, see `CLAUDE.md` |
| Timeline: report due 15 Oct, IELTS 09 Oct | **The report is priority 1.** If something must be cut, cut backward from step 8 → 6. Steps 0–5 are the minimum demo that's still defensible |

---

*End of DEMO_BUILD_HANDOFF.md.*
