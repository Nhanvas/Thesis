# PHASE C-FINAL HANDOFF — C4-full Multi-Relational GAE
**Written end of a long chat so the NEXT chat starts clean. Read this first, then
`docs/RESULTS_OF_RECORD_phaseB.md` §0 + `docs/PHASE_C_HANDOFF.md`.**
**On any NUMBER conflict, RESULTS_OF_RECORD wins. TEST is UNTOUCHED and stays one-shot.**

---

## 0. ROLE + OPERATING RULES (unchanged, restated for the new chat)
- Claude = senior Stanford/MIT-style research mentor. **Boti (Nguyen Quoc Trung Nhan)
  is the final decision-maker.** Propose → he approves → he executes locally/Kaggle.
  No autonomous changes. Communicate in **Vietnamese**; code/deliverables in English.
- **State hypothesis + falsification + stop-condition BEFORE any experiment.** Reproduce
  before trusting a number. Null-check evaluations. Archive-don't-delete. Commit same day.
- **Never tune on the 8 TEST subjects.** VAL = chb10/11/22 gates iteration. TEST = single
  one-shot at the very end. Every new script carries a TEST guard.
- Anti-rationalization: never reframe a failed prediction as expected post-hoc.
- If Claude drifts to diagnosis-only / long-no-code, Boti says "build" to cut to code.
- Kaggle = notebooks (cells), not bash; `/kaggle/working` writable only via code; datasets
  mount at `/kaggle/input/datasets/<user>/<slug>/` (non-standard nesting — auto-discover
  paths with rglob, never hardcode). 4 Kaggle accounts run in parallel (~3.5 h/GAE-seed).
- **Timeline: Phase C hard-closes in ~1 week from this handoff.** IELTS 9 Oct, submit 15
  Oct, defense Nov 2-3.

---

## 1. LOCKED STATE (system-of-record)
- **Optimized pipeline = rlg** (recon-MSE + latent-Mahalanobis + gamma-AEC, equal 1/3,
  temporal-free; LSTM branch dropped, code lost, Amendment A1). Single GAE seed42.
- **rlg headline (report this):** window macro AUROC **0.805** (TEST); event held-out
  triage **F1 0.361 @ 3.6 FP/day** (TEST, SzCORE SOTA band 0.32–0.43). §0 historical
  baseline: sens 0.632 @ 38.6 FP/day (balanced), 0.776 @ 72.7 (high-sens).
- **CPD algorithm:** `src/cpd_pipeline_v14.py` (PELT on 15-win MA-smoothed ensemble +
  label-free per-subject FP-budget OP). Scorer: `src/retrain/score_ens.py` →
  `src/szcore_eval.py` (`timescoring`). Single-source ensemble weight in
  `src/ensemble_recipe.py` (equal).
- **NEW result this chat — GAE seed-stability (report-worthy, add to record):**
  4 GAE seeds {42,1,2,3} trained (PREREG_01 recipe). rlg is highly seed-stable:
  - window macro AUROC (VAL): 0.928 / 0.929 / 0.925 / 0.932 → **0.929 ± 0.002**
  - chb13 recon AUROC (Gate R-GAE G1): 0.836 / 0.835 / 0.833 / 0.834 (tight)
  - rlg event F1@3.6 (VAL): 0.489 / 0.565 / 0.522 / 0.478 → **≈0.51 ± 0.034** (seed-SD
    ≈ 0.034 — this number is the bar any challenger must beat to be "real").

---

## 2. PHASE C SO FAR — 4 LEVERS, 4 EVIDENCE-BASED NEGATIVES
All challengers VAL-gated; **none earned one-shot TEST**. Report as negative contributions.
1. **C4-lite (TE as a 4th ensemble branch, rltg_te = 0.75·rlg + 0.25·zTE):** passed the
   B=40 gate marginally (+0.004 F1) but **HARMED the low-FP headline** (F1 −0.070 @ B=3.6).
   TE rescues symmetric-inverted subjects at the connectivity level (C0: chb06 sym AUROC
   0.37→TE 0.73; chb22 0.22→0.83) but the benefit is **per-subject** and **net-washes** at
   event aggregate. Rejected as a headline lever; kept as an analysis/mechanism finding.
2. **C1 (median pre-CPD smoother vs MA-15):** median15 dropped sensitivity (blunts short
   onsets); median9 "passed" B=40 by +0.004 but coincided exactly with rltg_te → VAL@B=40
   is quantization-saturated (15 events / 3 subjects). Harmed the low-FP headline. Rejected.
3. **slope-gate (C-onset, MIN_SLOPE_PCT=75, reject high-level interictal PLATEAU CPs, keep
   rising onsets):** C-onset probe showed real WINDOW headroom (slope AUROC 0.918 vs level
   0.823) BUT it was **seed42-specific**. Multi-seed check: seed42 PASS (+0.023 F1) but
   seeds 1/2/3 all FAIL (ΔF1 −0.039…−0.065, sens −0.133 each). The seed42 "win" (+0.023) <
   seed-noise SD (0.034). **Rejected — this is exactly why we now require multi-seed from
   the first VAL round.**
4. **line-length / Hjorth node features:** proposed then REJECTED before building — they are
   per-channel scalar time-domain features (same class as the existing 5 band-powers), do
   NOT address the directed-relationship failure mode C0 identified, and are weak to defend
   ("why 1970s Hjorth in a 2024-26 graph-learning thesis?").

**Unifying diagnosis (the scientific story):** window/representation gains repeatedly die at
the **CPD-transfer** (CPD detects sustained level shifts / onset sharpness, not rank
separation), and per-subject rescue levers **net-wash** because each hard subject fails on a
different mechanism and the ceiling subjects (chb06/chb14) sit in TEST. Decision-layer and
per-channel-feature levers are exhausted **with evidence**.

---

## 3. THE DECISION — Phase C-final = C4-full (multi-relational GAE)
**Why this and not more of the above (literature-grounded, searched 2024-2026):**
- C4-lite only did HALF the job: TE as a *separate ensemble branch*, linearly combined
  post-hoc. The GAE never learned a JOINT representation of symmetric + directed coupling.
  C4-full closes exactly that gap — the one place with direct positive evidence (C0).
- **Multi-relational / heterogeneous unsupervised graph autoencoders are a current
  paradigm:** R-GCN-as-autoencoder (Schlichtkrull); **UMGAD** (Nov 2024, unsupervised
  multiplex graph anomaly — decouple into relational subgraphs, per-relation reconstruction,
  learn relation importance); AutoGraphAD (2025, heterogeneous VGAE anomaly); HRGCN (2023).
  Directed/effective connectivity (TE/Granger/DTF) is an established "richer representation"
  for EEG seizure (Sci Rep 2025, s41598-025-01882-7). This lands squarely on the thesis'
  claimed novelty and matches its lit review (IRENE, EvoBrain, dynamic/multi-relational GNN).
- Uniform lever (lifts all subjects via a better learned latent), NOT a per-subject rescue →
  not obviously subject to the net-wash that killed TE/slope.

**Architecture sketch (to be finalized in the build chat):**
- 2 relations per window: R1 = undirected symmetric (current wPLI+AEC top-k20 adjacency),
  R2 = directed TE (18×18, the validated C0/C4-lite computation; vectorized `te_matrix`,
  ~8.7 ms/window, numerically identical to `connectivity_probe.conn_matrix('te')`).
- R-GCN-style encoder (relation-specific message passing) → shared node latent → per-relation
  decoder → reconstruction loss per relation (à la UMGAD). Anomaly = recon error (+ optional
  latent-Mahalanobis, mirroring rlg's latent readout). Keep it UNSUPERVISED, interictal-fit.
- gamma-AEC branch (zgamma) unchanged; the C4-full GAE replaces the recon+latent branches.

**HONEST DOMINANT RISK (literature does NOT cover this):** every cited paper is supervised
or window/node-level unsupervised — none do **unsupervised patient-independent EVENT-level via
CPD**. A window-level win from C4-full must still survive CPD-transfer. Base-rate Phase C is
0/4. So the plan MUST test event-level early and cheaply and kill fast.

---

## 4. PRE-REGISTRATION + STAGED GATES (Boti's two conditions are baked in)
**Condition 1: multi-seed from the FIRST VAL round. Condition 2: hard day-boxed kill.
Condition 3: preserve-current (all C4-full in parallel modules/paths; rlg untouched).**

- **Stage 0 — cheap prototype (Day 1, KILL EARLY).** Build the multi-relational GAE, train
  ONE seed on a small subset (or all-12 quick), encode VAL, compare **latent/recon window
  AUROC vs rlg's symmetric-only** (0.929), *especially* whether chb22 (VAL inverted subject)
  improves WITHOUT hurting chb10/11. Also a quick S2-style check: does the 2-relation latent
  collapse toward one relation (residual → 0)?  **KILL if no window signal by end of Day 1.**
- **Stage 1 — multi-seed VAL event gate (Days 2-4).** If Stage 0 GO: train seeds {42,1,2,3}
  (4 accounts), encode rlg-analogue ens, run the EVENT seed-check vs rlg at B=3.6.
  **GO iff mean ΔF1(C4full − rlg) ≥ +0.03 across 4 seeds AND ≥3/4 seeds ΔF1 ≥ 0 AND no seed
  sens drop > 0.02.** (Threshold set above the 0.034 seed-SD so a "win" isn't noise.)
  Cheap pre-screen: if window macro AUROC ≤ 0.929 on ≥3/4 seeds → early NO-GO.
- **Stage 2 — one-shot TEST (Days 5-6).** ONLY if Stage 1 GO. Freeze VAL-derived OP cell,
  score TEST grid via the C4-full ens, run `tier2_oneshot_compare` (A1 procedure) vs rlg+§0.
  **Falsification:** no Pareto-improvement over rlg at matched FP/day → rlg stands.
- **Stage 3 — close either way (Day 7).** Write up C4-full result (win or negative) +
  the 4 prior negatives + seed-stability. Update record. Move to report/attribution/defense.

---

## 5. FILES BUILT THIS CHAT (paths + purpose + how tested) — all under src/phaseC/ unless noted
- `build_te_branch.py` — C4-lite TE anomaly branch (zTE). Contains the vectorized
  `te_matrix` (bincount TE, max|Δ|=7e-15 vs `connectivity_probe.conn_matrix('te')`, 33×
  faster, ~8.7 ms/win). **Reuse `te_matrix` for C4-full's R2 edges.** PCA(12)+LedoitWolf
  readout. Smoke + fidelity pass.
- `run_slopegate_grid.py`, `c1_lowfp_compare.py`, `c_onset_probe.py`, `seed_check_slopegate.py`,
  `run_c1_grid.py` — Phase C challenger drivers / comparators. **`c1_lowfp_compare.py`
  (low-FP pooled event F1, reuses g2_val_gate pooling) and `seed_check_slopegate.py`
  (auto-discovers seeds, per-seed ΔF1 at matched budget) are directly reusable for the
  C4-full event gate — just point at the new ens dir.**
- `place_seeds.py` — extract Kaggle zips → repo, byte/tolerance fidelity compare.
- **cpd_pipeline_v14.py (PATCHED, default-off, byte-exact):** added swappable `SMOOTHER`
  (C1) + `MIN_SLOPE_PCT` slope-gate (C-onset) + `_cp_slope`/`_slope_filter`. Both DEFAULT
  OFF → reproduce §0/rlg byte-exact. **Keep as-is (documents tested-negative levers); do NOT
  need to touch for C4-full.**
- **score_ens.py (PATCHED):** 2-line gated slope hook (default off, byte-exact). Keep.
- **build_ens_tier2.py (PATCHED):** (a) robust sys.path, (b) lstm-optional so GAE-only
  seeds build rlg (`lstm_ck` find is now INSIDE the `need_temp` branch — was the bug that
  crashed rlg-only encode), (c) lazy `import lstm_temporal`, (d) `rlg_components` helper
  (recon+gamma, no lstm) with a **strict gamma loader requiring 'gamma' in the filename**
  (fixes local `data/processed/` where gamma shares a dir with raw windows and the loose
  `*{subj}*` glob grabbed `{subj}_interictal.npy`). **This patched builder is what encodes
  multi-seed rlg VAL ens; adapt/branch it for the C4-full GAE module.**

Latest patched copies of these four files were delivered in this chat's outputs — make sure
the repo has them before the next chat builds on top.

---

## 6. DATA / CKPT / ENS LAYOUT (verified this chat)
- Raw windows + features + adj + **gamma** all LOCAL under `data/processed/` (32.9 GB,
  gitignored but present): `{subj}_{interictal,ictal}.npy [N,18,1024]`,
  `{subj}_{split}_adjs_topk20.npy`, `{subj}_{split}_features.npy [N,18,5]`,
  `gamma_aec_{subj}_{inter,ictal}.npy`.
- GAE ckpts: `data/models_retrain/gae_joint_seed{42,1,2,3}.pt` (committed). seed42 also
  exists as a Kaggle-unpacked folder + `.zip` (unzip → `find_ckpts` reads the `data.pkl`
  dir; Windows re-zip needs `touch` to fix pre-1980 timestamps before `load_state`).
- rlg VAL ens (4 seeds): `results/phaseB/tier2/ens_val_tf/rlg/ens_seed{42,1,2,3}_{subj}_{inter,ictal}.npy`.
  seed42 = original Kaggle-GPU build; seeds 1/2/3 = local CPU re-encode (float noise
  max|Δ|≈8.6e-5 vs GPU, corr=1.000000 — faithful; record the CPU/GPU caveat).
- Training recipe: `src/retrain/train_gae_joint.py` (PREREG_01: Adam 1e-3, cosine, 200
  epochs, batch 32, 12 train subjects interictal, save final epoch, `--seeds` list, prints
  chb13 AUROC vs locked 0.836). Kaggle data at `nhn2mm/chbmit-topk20`, `nhn2mm/chbmit-processed`,
  `nhn2mm/gamma-aec-scores`; code dataset `norncreades/thesis-c-onset-code` (+ gae-s5).

---

## 7. WHAT THE NEXT CHAT SHOULD DO FIRST
1. Confirm the C4-full architecture with Boti (R-GCN AE vs 2-branch GCN; per-relation vs
   shared decoder; recon-only vs recon+latent readout). Ground in UMGAD / R-GCN-AE.
2. **Stage 0 build (isolated, preserve-current):** `feature_extraction`/graph stays; add a
   directed-TE relation using `te_matrix` (from `build_te_branch.py`); new modules
   `gae_joint_multirel.py`, `train_gae_multirel.py`, separate ckpt/ens paths. Smoke on
   synthetic + 1-subject before any full run.
3. Run Stage 0 window check on VAL (esp. chb22). Kill or proceed per §4.
4. Keep TEST untouched until Stage 2, and only after Boti signs off the one-shot.

---

## 8. PROJECT-DOC UPDATES TO APPLY (short)
- `docs/RESULTS_OF_RECORD_phaseB.md`: add the §1 seed-stability CI (numbers in §1 above) and
  a Phase-C negatives log (C4-lite / C1 / slope-gate rejected, with the low-FP evidence).
- Project custom instructions (CURRENT STATUS): "Phase C decision-layer + per-channel-feature
  levers exhausted with evidence; seed-stability established (4 GAE seeds); Phase C-final =
  C4-full multi-relational GAE IN PROGRESS (staged-gated, ~1 week); rlg remains
  system-of-record until a one-shot TEST replaces it."
- Keep the cpd/score_ens/build_ens_tier2 patches (all default-off / byte-exact / correctness).
