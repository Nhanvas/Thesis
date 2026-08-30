# PRE-REGISTRATION 09 — Minimum-event-duration post-filter (Phase-B · A1', FP reduction)

**Status:** COMMITTED before touching test. Replaces the earlier "artifact gate" idea, which is
**infeasible with available data** (only normalized band-power features; no raw amplitude, no interictal
raw signal, no labeled artifact corpus → no Ingolfsson-style trained artifact classifier). This lever needs
only the score timeline the pipeline already builds and is fully label-free.

## 0. Motivation (from the code, not speculation)
`cpd_pipeline_v14.detect_events` has **no minimum-event-duration constraint**: an isolated high-magnitude
change point becomes a single-window (~4 s) event. Merge (≤90 s) does not remove isolated CPs. These
single-window interictal events are a clean, physiologically implausible FP source (real seizures persist).
Adding a minimum duration is standard seizure-detection post-processing (SzCORE itself uses minimum
durations) and cannot leak test labels.

## 1. What changes
A post-filter on the hypothesis events `hyp_iv` (list of (onset_s, end_s)) **before** SzCORE scoring:
drop events with (end_s − onset_s) < D. Applied at a **fixed operating point** (the reported balanced
headline mag80/pen5; also reported at the triage point mag55/pen0.3). No change to PELT, magnitude filter,
weights, or ensemble. `cpd_pipeline_v14` core untouched; D is an add-on post-step.

## 2. Derivation of D (VAL only, sensitivity-first)
Sweep **D ∈ {0, 4, 8, 12, 16, 20, 30} s** on the VAL subjects at mag80/pen5.
**D\* = the largest D such that VAL pooled TP count is unchanged from D=0** (i.e. zero sensitivity cost),
maximizing FP reduction at no recall loss. If even D=4 drops a VAL TP → **D\* = 0 (revert, lever rejected)**.
Freeze D\*.

## 3. Apply to test (one shot) + report
Apply D\* to the 8 test subjects at mag80/pen5. Report pooled sens / prec / F1 / FP/day (Wilson + Poisson
CIs) at D=0 vs D=D\*, and the per-subject TP/FP deltas. Also report the effect at the triage point.
Integration self-check: at **D=0 the harness must reproduce mag80/pen5 = sens 0.395 / FP/day 5.6** and the
§0 points, else the timeline/scoring path is inconsistent — stop.

## 4. Success / falsification
- **Success:** test FP/day drops with **test TP count unchanged** (sensitivity held) → precision & F1 rise
  → all-metrics-up move; keep D\* as a reported post-filter alongside the operating point.
- **Falsification:** if test sensitivity drops (any TP lost) or FP/day does not fall materially → report
  as-is and **revert to D=0**. A duration filter that costs recall is rejected, not reframed.

## 5. Guardrails
Label-free (duration only); D derived on VAL, test touched once; harness reproduces the locked numbers at
D=0 before use; result ADDED alongside, nothing in §0 overwritten.

*End PREREG_09. Runs in `duration_filter_sweep.py` (imports the repo's szcore_eval + cpd_pipeline_v14).*
