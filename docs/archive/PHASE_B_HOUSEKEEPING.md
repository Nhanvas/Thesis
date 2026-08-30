# PHASE B — HOUSEKEEPING, PROVENANCE & PROJECT UPDATE
**Read with `TIER2_HANDOFF.md`.** This doc fixes the #1 failure of the whole project — results
scattered on Kaggle, un-committable, lost → forced a full baseline rebuild. From now: **every artifact
that feeds the report or the web demo must live LOCALLY, in the git repo, at a repo-map-defined path.**
Kaggle is compute-only and disposable.

---

## 1 · PROVENANCE PRINCIPLE (non-negotiable)
- **Kaggle produces, local git stores.** After any Kaggle run: pull the artifacts down, place them at the
  repo-map path, `git add` + commit. A result that exists only in `/kaggle/working` DOES NOT EXIST.
- **One path per artifact, declared in `docs/REPO_MAP.md` BEFORE the run** (so nothing lands ad-hoc).
- **Numbers → a CSV/JSON in `results/…`; rationale → a `.md` in `docs/…`.** Never leave a headline number
  living only in a chat log or a notebook cell output.
- **Checkpoints are the crown jewels.** `.pt` files: keep the ORIGINAL zipped file in git-LFS or a
  `models/` folder; do NOT rely on the Kaggle-unzipped folder (it is not directly loadable).

---

## 2 · LOCAL DIRECTORY LAYOUT FOR PHASE B (declare in REPO_MAP, create now)
```
F:/Study/Thesis/Code/
├─ src/
│  └─ phaseB/                      # NEW — Phase B scripts (committed)
│     ├─ latent_anomaly.py         # E2 WIN — latent-Mahalanobis readout
│     ├─ dump_val_components.py     # dumps zrecon/ztemp/zgamma/zlatent
│     ├─ branch_ablation.py         # E1 ablation leaderboard
│     ├─ val_gate.py                # VAL-only GAE-recon gate
│     └─ archive/                   # negative/superseded — kept for provenance
│        ├─ gae_joint_gsl.py        # S2 REJECTED
│        ├─ train_gae_gsl.py        # S2 REJECTED
│        └─ train_gae_compact.py    # S3 NEGATIVE
├─ data/
│  ├─ models_retrain/
│  │  ├─ gae_joint_seed42.pt        # baseline GAE (latent readout uses THIS) — VERIFY committed
│  │  └─ lstm_temporal_seed42.pt    # temporal branch — VERIFY committed (move from models_train)
│  └─ processed/
│     ├─ components/                # per-branch robust-z (TEST already; VAL to add)
│     └─ gamma_aec/                 # gamma_aec_{subj}_{inter,ictal}.npy — VERIFY local copy exists
├─ results/
│  └─ phaseB/                       # NEW — all Phase B numbers
│     ├─ E2_latent_val.csv          # recon vs latent per VAL subj (from this session)
│     ├─ E1_ablation_val.csv        # full ablation leaderboard
│     ├─ S2_S3_negatives.md         # multiband/GSL/compact numbers + verdicts
│     └─ (Tier-2 outputs land here) # ensemble_val_grid.csv, tier2_test_oneshot.csv, ...
└─ docs/
   ├─ TIER2_HANDOFF.md              # technical handoff to the new chat
   ├─ PHASE_B_HOUSEKEEPING.md       # this file
   ├─ 01_EXPERIMENT_LOG.md          # append E2 WIN + S2/S3 negatives (entries in TIER2_HANDOFF §8/log)
   └─ PROJECT_INSTRUCTIONS.md       # apply §6 edits below
```

---

## 3 · COMMIT TO GITHUB NOW (before the new chat)
From this session, place + `git add` + commit:
1. `src/phaseB/{latent_anomaly,dump_val_components,branch_ablation,val_gate}.py`
2. `src/phaseB/archive/{gae_joint_gsl,train_gae_gsl,train_gae_compact}.py`
3. `results/phaseB/E2_latent_val.csv`, `E1_ablation_val.csv`, `S2_S3_negatives.md`
   (transcribe the numbers from TIER2_HANDOFF §2–§3 into these small files)
4. `docs/TIER2_HANDOFF.md`, `docs/PHASE_B_HOUSEKEEPING.md`
5. Verify already-committed: `data/models_retrain/gae_joint_seed42.pt`,
   `lstm_temporal_seed42.pt`, and the gamma scores. **If any lives only on Kaggle, pull it down and commit.**

`gae_compact_seed42.pt` (S3 negative) → do NOT commit the weights; the negative result is documented,
the script is archived; re-runnable if ever needed.

---

## 4 · CLEANUP (keep / archive / delete)
**Output folder (this session):**
- KEEP → `src/phaseB/`: latent_anomaly, dump_val_components, branch_ablation, val_gate.
- KEEP (repo code, unchanged): gae_joint, lstm_temporal, retrain_io, train_gae_joint, ensemble_recipe.
- KEEP → `data/models_retrain/`: gae_joint_seed42.pt, lstm_temporal_seed42.pt.
- ARCHIVE → `src/phaseB/archive/`: gae_joint_gsl.py, train_gae_gsl.py, train_gae_compact.py.
- DELETE: `__pycache__/`, `gae_compact/` weights, `val_components/` (regenerable via dump script).

**Prior-chat docs folder (00–04, t1/t3/persubj/reselect/T2/T3/WINDOW_SUITE…):**
- KEEP ALL (provenance). Move loose diagnostic CSV/RESULT files into `results/history_superseded/priorchat/`.
- `00`–`04` + `PHASE_B_ROADMAP_v2.md`: keep; `TIER2_HANDOFF.md` supersedes the "current status" parts.

---

## 5 · WHAT "PHASE-B OPTIMIZED PIPELINE" MUST CONTAIN (finish line, after Tier-2)
A single committed chain that reproduces the reported optimized result from raw inputs:
`adj + feat + gamma + {gae_joint_seed42.pt, lstm_temporal_seed42.pt}`
→ components incl. **zlatent** → ensemble (chosen branch set) → CPD → SzCORE → event metrics.
Deliverables to commit at that point:
- `src/phaseB/build_phaseB_ensemble.py` (adds zlatent as a first-class component).
- `results/phaseB/RESULTS_OF_RECORD_phaseB.md` (new event/window numbers, VAL-derived OP, one-shot TEST).
- Update `docs/RESULTS_OF_RECORD.md` in ONE reconcile pass; update `docs/REPO_MAP.md`.
- The web demo reads the SAME committed components/checkpoints — never a Kaggle path.

---

## 6 · CLAUDE PROJECT UPDATE — exact actions
**Upload to the Claude Project (knowledge):**
- ADD: `TIER2_HANDOFF.md`, `PHASE_B_HOUSEKEEPING.md`, updated `01_EXPERIMENT_LOG.md`.
- ADD (code the new chat should see): `latent_anomaly.py`, `dump_val_components.py`, `branch_ablation.py`, `val_gate.py`.
- DO NOT upload the rejected scripts (gsl/compact) — they add noise; the handoff records their status.
- REPLACE if a stale copy exists; otherwise just add.

**Edit `PROJECT_INSTRUCTIONS.md` (custom instructions) — precise deltas:**

(a) In `## CURRENT STATUS`, REPLACE the bullet
> "- **Next = Giai đoạn B (optimization)**, only after governance cleanup + cô sign-off. Evidence says
>   headroom is per-subject signal (chb06/chb14 representation), NOT LSTM capacity, NOT weight."

WITH:
> - **Phase B (optimization) — IN PROGRESS.** Graph-structure upgrades (S2 learned graph, S5 multiband)
>   and objective compactness (S3 Deep-SVDD) were tested and **REJECTED/NEGATIVE**. The WIN is a
>   **latent-manifold readout on the same baseline GAE** (Mahalanobis of pooled latent Z to the
>   interictal manifold): it fixes the recon-anomaly inversion under ictal hypersynchrony (chb10 VAL
>   AUROC 0.268→0.816) and lifts the ensemble on VAL window AUROC (recon+temp+gamma 0.866 →
>   recon+latent+temp+gamma 0.918 / latent+temp+gamma 0.931). **This is validated at WINDOW/VAL level
>   only; event-level + TEST are the Tier-2 job and NOT yet reported.** SSL/masked = declined.
> - **Next = Tier-2 integration:** ensemble-with-latent → CPD → SzCORE on VAL → derive OP → one-shot
>   TEST → compare to the locked event baseline. See `docs/TIER2_HANDOFF.md`.

(b) In `## LOCKED NUMBERS`, ADD (do NOT change §0 event numbers — they stay the reported baseline until
Tier-2 replaces them):
> - **Phase-B window WIN (VAL, PENDING Tier-2 event/TEST):** GAE latent-readout macro AUROC 0.731 vs
>   recon 0.592; ensemble latent+temp+gamma 0.931 / recon+latent+temp+gamma 0.918 vs recon+temp+gamma
>   0.866. NOT yet a report headline — event+TEST pending.

(c) In `## CORE OPERATING RULES`, ADD:
> 13. **Local-first provenance.** Kaggle is compute-only. Every artifact feeding the report or web demo
>     is pulled down, placed at a `REPO_MAP` path, and committed to git the same day. A result living
>     only on Kaggle does not exist (this caused the baseline rebuild).

(d) In `## COMMON PITFALLS`, ADD:
> - Graph structure is NOT the lever for the GAE branch (S2/S5 rejected); the readout is (recon-MSE →
>   latent-Mahalanobis). Recon-anomaly INVERTS under ictal hypersynchrony — do not treat low recon as
>   "normal" for such subjects.
> - Kaggle unzips uploaded `.pt` into folders → not directly loadable; rebuild via marker helper.
> - Do not learn ensemble weights on 3 VAL subjects; equal weight stays default. gamma is strong on VAL
>   alone — do not over-index on VAL-lucky branches; TEST decides.

---

## 7 · NEW-CHAT DISCIPLINE (avoid repeating this + prior chats' mistakes)
- **Diagnose only enough to choose the next build, then build.** This session's early turns thrashed on
  Kaggle plumbing/path errors — front-load a fail-fast precheck cell; verify paths before long runs.
- **Optimize the pipeline, not the operating point.** (Prior-chat root mistake.)
- **VAL gates; TEST is one-shot at the very end.** Every script keeps the TEST-guard.
- **State hypothesis + falsification + stop-condition BEFORE running.** Report negatives honestly; do not
  reframe. (S2/S3 negatives are contributions, not failures.)
- **Reproduce the locked baseline in-harness before trusting any new number.**
- **Researcher stance:** decisive, paper-grounded proposals; user approves; no autonomous changes;
  concise (verdict + next action + command). Push back when evidence warrants.
- **Provenance every run** (§1). No scattered files.
