# 02 · MISTAKES & ANTI-PATTERNS (prior chat) — do not repeat

## Root mistake
**Confused "select the best operating point" with "upgrade the pipeline."** The entire prior chat was
decision-layer selection + diagnostics + rejected post-filters. **Zero pipeline components were changed.**
The headline gain (F1 0.168→0.31/0.35) came only from re-thresholding the same weak model. This is NOT
optimization. Optimization = make the model/features/graph stronger and retrain.

## Anti-patterns to avoid
1. **Risk-averse avoidance.** Deferred the real representation upgrades (learned graph, richer features,
   SSL) to "Phase 2 / GPU / gated / Future Work / pending sign-off" while doing only cheap threshold work.
   → In the new chat: go straight at the highest-ROI model upgrade; guardrails serve the build, not replace it.
2. **Diagnose-forever.** Ran many diagnostics (T3, T4, per-subject, duration, selective) that each ended in
   "can't do it at the decision layer." Useful once (localized weak link = representation), then became
   avoidance. → Diagnose only enough to pick the next upgrade, then build.
3. **Premature "exhausted / freeze."** Declared the decision layer exhausted and leaned to freeze before
   trying any actual pipeline upgrade. → Freeze is never a first move.
4. **Sloppy headline provenance.** Called mag80/pen5 "the headline" loosely though it was chosen after
   seeing the test Pareto; cleanest headline is mag80/pen10 (PREREG_05). → Always attach derivation +
   integrity caveat; keep pen10 primary until a stronger, cleanly-derived number exists.
5. **Naive auto-gates.** `t4_chb06_probe.py` printed "free fix" for a per-subject sign flip that would be
   test leakage. → Any auto-verdict must check the decision's data provenance (train/val vs test labels).
6. **Fidelity drift in off-harness scripts.** `duration_filter_sweep.py` didn't reproduce the grid
   bit-exact (0.382 vs 0.395; missing seed before `build_timeline_masked`). → New scripts must reproduce
   the locked baseline in a self-check before use; if not, stop.
7. **Over-long, token-heavy replies.** → verdict + next action + command only.

## What WAS done right (keep)
Harness-reproduces-§0 before trusting; pre-registration before touching test; honest negative results;
caught the SzCORE >5-min split denominator bug (chb11) and audited impact; T2 flagged unverified citations.
Keep these disciplines — but in service of building upgrades, fast.
