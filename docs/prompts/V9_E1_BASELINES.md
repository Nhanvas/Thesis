# V9-E1 — Does the graph autoencoder help? Non-graph baselines on the identical pipeline (Claude Code, laptop)

Estimated runtime: 3–6 h (estimated, not measured). Smoke on one patient first and report the projected total. Can run overnight.

## Question (fixed before running)
The reviewer asked why a Graph Autoencoder and not another model. The literature has no matched comparison (graph vs channel-wise features under continuous event-level evaluation), so we answer it experimentally: replace **only** the anomaly representation, keep everything downstream identical.

## Arms (each with ONE configuration fixed here; no tuning)
Downstream for every arm = the frozen P3 chain exactly as in `src/p3c_freeze.py` / `src/e23_test_look7.py`: per patient, per channel score → robust-z → order statistics 6/9/12 + channel mean → ±15-min running-median correction per file → patient percentiles → equal mean → smoothing 5 windows → per-patient budget `clip(q_i(k=4.0677), 0.005, 0.02)` → merge 90 s → kernel CPD → SzCORE scorer. Same label-free per-patient fits as the GAE arm.
- **G (reference)** — the frozen GAE latent (seed 42; also 4 seeds).
- **B1 features + Mahalanobis** — the 12 non-adjacency node features (5 band powers + 7 amplitude-preserving features) per channel instead of the 16-d latent; LedoitWolf Mahalanobis, as for G.
- **B2 adjacency only + Mahalanobis** — the 18-d adjacency row per channel (connectivity alone).
- **B3 features + IsolationForest** — same 12 features, per patient, per channel, `n_estimators=200, max_samples=256, random_state=42`, score = −score_samples.
- **B4 features + kNN** — same 12 features, distance to the 10th nearest neighbour in a random 20,000-window subsample of the same patient (excluding windows within ±60 s of the query), `random_state=42`.
- **F (fusion)** — rank-mean of G and the best of B1–B4, where "best" is chosen on the **development patients only** (train + validation), by event sensitivity at the frozen operating point, ties broken by FP/day.

## Evaluation
- Sets: development (15 patients), CHB-MIT test (8), chb24, Siena (all 14 if `V9_T4` has finished; otherwise the available ones, labelled).
- Report for each arm: tp/ref, FP, sensitivity, precision, F1, FP/day — **pooled and per-patient mean**; sensitivity by duration bin (≤20, 21–40, 41–80, >80 s); matched operating point curve (global budget sweep, detector stage) with sens at 20 / 27.5 / 44 FP/day; patient bootstrap 95% CI for the per-patient mean.
- Winner rule fixed now: an arm "beats G" only if it is better on the development patients **and** on CHB-MIT test **and** at matched FP/day; otherwise report "no better" or "mixed". All arms are reported whatever the result.

## Part C — re-reporting the frozen system under other papers' protocols (no new model)
To make the comparison table honest, compute for G (seed 42, frozen operating point) on CHB-MIT test: (i) excluding chb06, chb14, chb16 (the exclusion used in Clin Exp Pediatr 2026, DOI 10.3345/cep.2026.01011, mean seizure duration < 30 s); (ii) seizures ≥ 30 s only. Label as "secondary analysis under the protocol of [paper]", never as the headline.

## Rules
- Read-only on frozen scripts and committed results. New code `src/v9_e1_baselines.py`; outputs `results/v9_e1/`. Reuse cached node features (`data/pernode_v2/`, `results/p2_test/` …); if a cache is missing, stop and report.
- Labels only for scoring. Commit only your new paths, explicitly staged. `--smoke` first.

## Return format
Full report to `F:/Study/Thesis/Agent/inbox/V9_E1_REPORT.md`: one table per set (all arms, pooled + per-patient mean), duration-bin table, matched-FP table, the winner verdict per the rule above, Part C numbers, runtime measured.
