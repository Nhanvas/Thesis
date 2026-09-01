# PHASE C — FULL TECHNICAL AUDIT (how each verdict in RESULTS_OF_RECORD_phaseB.md §8–9 was reached)

**Purpose:** `RESULTS_OF_RECORD_phaseB.md` states verdicts and locked numbers. This file preserves the
**reasoning trail** behind them — intermediate probes, near-misses, self-corrections, and the review
discipline that caught false positives before they burned the one-shot TEST. Useful for defense Q&A
("how do you know it's really negative and not a bug?") and for anyone tempted to re-propose a rejected
lever. **On any number conflict, `RESULTS_OF_RECORD_phaseB.md` wins — this file is narrative, not the
source of truth.**

Also included: the Phase-B representation search (S1–S5, E1–E2) that produced rlg itself, since the
same discipline (pre-register → VAL-gate → falsify) applies there too and it is the direct predecessor
to the Phase-C program.

---

## Part 0 · How rlg itself was found (Phase B representation search, before Phase C existed)

### Starting point and the T1/T2/T3/T4 diagnostic round
The rebuild baseline (§0) had a known problem: the shared operating point across all 8 test subjects
was strangling signal-strong subjects (chb13, chb16, chb18) while doing nothing for signal-limited ones
(chb06, chb14). The `window_event_gap` diagnostic quantified this: pooled sensitivity if each subject
used its own best operating point = 0.789 (oracle, uses seizure labels, NOT attainable) vs 0.618 shared
— a +0.171 sensitivity gap attributable purely to the single shared threshold, not to signal quality.

**T1 (operating-point search):** confirmed a mag/pen combination giving F1 0.313 @ 3.2 FP/day as an
honest low-FP headline. A reviewer pass caught that the *argmax*-selected cell (by raw F1) was
imbalanced — high precision, sensitivity far below the SzCORE-challenge SOTA band. The corrected,
three-axis-balanced point was **mag80/pen5: sens 0.395, prec 0.316, F1 0.351, FP/day 5.6** — this became
the reference "properly balanced" cell used throughout later gating.

**T4 (per-subject inversion probe):** found that chb06's zrecon component was inverted (ictal windows
scored LOWER than interictal — the opposite of every other subject). A same-direction "flip" fix was
tested and looked like a win — but was correctly rejected because determining the flip direction used
the test subject's own seizure labels (leakage). This confirmed chb06 as genuinely representation-limited
rather than a fixable normalization bug, and set the standard that any per-subject correction must be
derivable without touching that subject's own labels.

### S1–S5: representation upgrade attempts (all but one rejected)
Pre-registered, VAL-gated (chb10/11/22), against the baseline GAE-recon-only macro AUROC of 0.592
(chb10 badly inverted at 0.268).

- **S2 (learned graph structure, residual-gated GSL):** the gate weight collapsed to 0.0000 by epoch 40,
  reducing the model back to the baseline (macro 0.5921 ≈ 0.5920) — i.e., the model learned to ignore the
  learned-graph branch entirely. A forced-on variant (gate=1) made reconstruction *worse* (train loss
  0.028 vs 0.016) and did not fix chb10 (still 0.269 inverted; macro 0.579). **Verdict: REJECTED.**
  Diagnosis: graph *structure* is not the lever — a reconstruction-only loss on interictal-only data
  gives no gradient signal that would teach a discriminative graph. This is the direct precedent cited
  when Phase D considers any future graph-structure-learning attempt.
- **S3 (Deep-SVDD compactness term on the GAE latent):** the compactness term stayed ~0.0005 (flat)
  throughout training — the interictal manifold was already compact, so there was nothing for the term
  to compress. Readout after retrain: macro AUROC 0.686, *worse* than the eventual latent-readout win
  (0.731). **Verdict: REJECTED — negative, informative** (rules out "the manifold needs to be tightened,"
  narrowing the search toward "the manifold's existing shape already separates ictal — the problem is
  how we read it," which is exactly what E2 confirmed next).
- **S5 (multiband adjacency, weighted delta/theta/alpha/beta/gamma):** VAL macro AUROC 0.581, *below*
  the single-band top-k20 baseline (0.592); AUPRC also worse (0.021 vs 0.050); chb11 dropped sharply
  (0.852→0.709). **Verdict: REJECTED** — multiband adjacency does not beat single-band top-k20 for this
  objective.
- **E1 (branch ablation on the frozen GAE):** systematically ablated recon/temporal/gamma combinations
  to find which subset of views carries the most signal, establishing the baseline ensemble comparison
  point that E2's latent branch would need to beat.
- **E2 (latent-Mahalanobis readout) — THE WIN.** Same GAE, same checkpoint, no retraining: instead of
  scoring anomaly by reconstruction MSE, score by Mahalanobis distance (LedoitWolf-shrunk covariance) of
  the graph-mean-pooled 16-d latent Z to the interictal manifold, fit per-subject on that subject's own
  interictal data (label-free, so valid to compute on TEST too). Result: **chb10 recon-AUROC 0.268 →
  latent-AUROC 0.816**; VAL macro AUROC 0.592 → **0.731**. When combined into the ensemble:
  recon+temp+gamma 0.866 → recon+latent+temp+gamma 0.918 → **latent+temp+gamma 0.931**.
  **Conclusion of the whole S-series:** the GAE itself was fine all along — reconstruction-error anomaly
  *inverts* under ictal hypersynchrony (the network reconstructs *better*, not worse, during a highly
  synchronized seizure, which is exactly backwards for an anomaly score), but the *same* latent space,
  read as a manifold-distance, does not have this failure mode. The fix was in the **readout**, not the
  model. This insight (documented in `S2_S3_negatives.md`) is what makes the later Amendment A1 pivot
  (drop LSTM, promote latent readout) a natural continuation rather than an ad hoc patch.

### Why the Tier-2 pivot to rlg happened (Amendment A1)
While reproducing the locked §0 ensemble from committed checkpoints to prepare for the Phase-B upgrade,
a provenance audit compared freshly-regenerated per-branch robust-z components against the committed
`data/processed/components/` arrays for all 8 TEST subjects:

| branch | corr vs committed | max\|Δ\| | verdict |
|---|---|---|---|
| zgamma | 1.000 | ~0 | reproduces exactly |
| zrecon (GAE) | ~0.99 | 2–5σ | reproduces up to minor input drift |
| ztemp (LSTM) | **0.10–0.44** | **up to 218σ** | **NOT reproducible** |

The LSTM training code/config had been lost; only §0's frozen output arrays survived, and the VAL-split
ztemp array was never committed at all — so the temporal branch could neither be regenerated nor
back-validated. This meant the E1/E2 window numbers that *included* temporal (0.866, 0.918, 0.931 above)
were computed against a component now shown to be irreproducible noise, and were retired from the
Tier-2 decision on that basis. The only Phase-B result that survived the audit fully reproducible was
**recon+latent+gamma (rlg)**, VAL macro AUROC 0.928, AUPRC 0.329 — all three of its components
independently confirmed reproducible. This is Amendment A1, and it is a genuine methodological
improvement (removes a lost-artifact dependency), not merely a workaround forced by the bug.

### The one-shot TEST and the "closed too early" correction
rlg was evaluated once on TEST (§3 of `RESULTS_OF_RECORD_phaseB.md`): matched §0 at its own operating
points, and Pareto-improved at a VAL-derived point (F1 0.213 @ 27.4 FP/day vs §0's 0.168 @ 38.6). At this
point the natural instinct was to declare rlg the final result and move to writing. **This was
pushed back on**: the front-end (graph construction, connectivity measure, GAE architecture) had not
been systematically probed beyond the S-series above — only the *readout* had been optimized. This
pushback is what opened Phase C: a proper, staged, pre-registered search of decision/representation/
ensemble/signal levers, rather than declaring a ceiling after one successful pivot.

---

## Part 1 · Phase C decision-layer levers (C4-lite, C1, slope-gate)

### C0 probe (connectivity diagnostic that motivated C4-lite)
Before building anything, a cheap diagnostic compared symmetric (wPLI/AEC) vs directed (transfer-entropy,
TE) connectivity graphs on the subjects with the worst symmetric-graph signal:
- chb06: symmetric window AUROC 0.370 (near-inverted) → TE-based 0.733.
- chb22: symmetric 0.216 (badly inverted) → TE-based 0.827.

This was a strong, real per-subject signal in favor of directed connectivity, and is what justified
spending Phase-C budget on TE as a lever — first cheaply (C4-lite, a post-hoc ensemble branch), later
more thoroughly (C4-full, a joint representation).

### C4-lite: TE as a 4th ensemble branch
`rltg_te = 0.75·rlg + 0.25·zTE` (zTE = anomaly score from a PCA(12)+LedoitWolf readout on the vectorized
TE matrix; TE computation independently verified against a slower reference implementation,
max|Δ|=7e-15, ~33× faster). VAL-gated at two budgets:
- At B=40 (the more permissive VAL gate): +0.004 F1 — technically passed.
- At the Phase-C headline gate, B=3.6 FP/day: **−0.070 F1** — a clear harm.

**Verdict: REJECTED as a lever.** The C0 per-subject rescue is real (confirmed again: chb06 F1-relevant
metric 0.37→0.73, chb22 0.22→0.83 in the underlying connectivity signal) but a fixed 0.75/0.25 linear mix
cannot exploit a per-subject benefit without also diluting the subjects where TE hurts — this is the
first appearance of the "per-subject rescue that net-washes at aggregate" pattern that recurs throughout
Phase C. Kept as a **mechanism finding**, not reported as a working lever.

### C1: pre-CPD smoother swap (median vs the locked 15-window moving average)
Tested `median15` and `median9` as drop-in replacements for the locked MA-15 smoother in
`cpd_pipeline_v14.py` (the smoother choice was made module-level swappable specifically to allow this
test without touching the locked default).
- `median15`: sensitivity dropped — a median blunts short seizure onsets more than a mean does.
- `median9`: appeared to pass the B=40 VAL gate by +0.004 F1, but this **coincided exactly** with the
  C4-lite VAL-B=40 pass (+0.004 as well) — a reviewer check found the B=40 VAL cell only contains 15
  events across 3 subjects, so it is **quantization-saturated**: a coincidence of two unrelated levers
  producing the identical small delta at a coarse-grained cell is a sign the cell can't discriminate
  small effects, not evidence both levers work.
- Both variants harmed the low-FP headline cell.

**Verdict: REJECTED.**

### slope-gate / C-onset (the seed-discipline case study)
Hypothesis: many false positives are high-level *plateaus* in interictal data (the ensemble score sits
elevated but flat), while true onsets show a *rising* slope. A `MIN_SLOPE_PCT` gate was added to
`cpd_pipeline_v14.py` (default OFF, byte-exact when off) that keeps only change-points whose signed local
rise exceeds a percentile of background (interictal) change-point rises — label-free.

- **Window-level probe (seed42 only) showed real headroom:** slope-based separation AUROC 0.918 vs
  level-based 0.823 — a large, genuine-looking window-tier signal.
- **Event-level, seed42 only:** +0.023 F1 at the headline — looked like a pass, but this delta is
  *smaller* than the measured event-level seed-SD (0.034, established later in §7 of the results file).
  Per the project's own multi-seed discipline (a win must exceed the seed-SD to be distinguishable from
  noise), this could not yet be trusted.
- **Multi-seed check (the deciding step):** the same slope-gate rule was re-applied using GAE seeds
  {1,2,3} (each retrained fresh with the identical PREREG_01 recipe, purely for this seed-check — this is
  in fact what motivated training the extra seeds that later became the §7 seed-stability result).
  Seeds 1/2/3 **all failed**: ΔF1 ranged −0.039 to −0.065, with sensitivity dropping ~0.133 on each seed.

**Verdict: REJECTED.** This is the single clearest illustration in the whole project of why the
multi-seed-from-the-first-VAL-round rule exists: a seed42-only apparent win (+0.023, itself already
below the noise floor) was *actively harmful* on 3 of 4 seeds. Had the TEST one-shot been spent on
slope-gate based on the seed42 result alone, it would very likely have shown a real regression on the
locked 8-subject TEST set. The multi-seed check caught this before any TEST budget was spent.

### line-length / Hjorth node features (rejected before building)
Proposed as a possible 4th ensemble input (per-channel scalar time-domain features, same computational
class as the existing 5 band-power features). Rejected **a priori**, without building anything: (a) it
does not address the *directed-relationship* failure mode that C0/C4-lite/C4-full were built to test —
it is a same-family enrichment of an axis (scalar per-channel features) already well-represented; (b) it
would be difficult to defend to a committee as a meaningful 2024–2026 contribution alongside a
graph-learning thesis. This is recorded as a **scoped-out** lever, distinct from a *tested* negative.

---

## Part 2 · C4-full — multi-relational GAE (the representation-layer test)

### Architecture and engineering
A joint R-GCN-style autoencoder with two relations per window: R1 = the existing symmetric wPLI+AEC
top-k20 adjacency; R2 = directed transfer-entropy (TE) top-k20, using the same `te_matrix` function
validated in C4-lite. Design choices, each pre-registered before training:
- **Non-shared per-relation encoder weights** (separate GCN weight matrices for R1 vs R2 message passing)
  — chosen specifically so the model *could* fail by ignoring one relation (as S2's GSL gate did), which
  makes a "no collapse" result meaningful rather than assumed.
- **Per-relation decoders:** R1 keeps the existing inner-product decoder; R2 uses an asymmetric bilinear
  decoder appropriate for a directed adjacency (inner-product decoders are symmetric by construction and
  cannot represent a directed edge).
- **Monitoring metric `gate_R2` = ‖grad R2‖/‖grad R1‖**, tracked every epoch specifically to detect the
  S2-style collapse (a relation's gradient shrinking toward zero, meaning the model has learned to ignore
  it). This is the direct methodological lesson carried over from the S2 rejection.

### Engineering note (not a scientific result, but relevant to reproducibility)
An early implementation was severely host-bound (CPU-side data movement dominating GPU compute time on
Kaggle), giving an unusable per-seed ETA. This was diagnosed and fixed by batching the R2 edge/TE
computation instead of doing it per-window on the host; after the fix, per-seed training time became
~3.2 hours, making the pre-registered plan (seed42 first, then multi-seed if Stage 0 passed) feasible
within the Phase-C time-box.

### Training result
Trained on the full 270,187-window interictal training set (12 subjects), PREREG_01 recipe (Adam 1e-3,
cosine schedule, 200 epochs, batch 32), seed 42. `gate_R2` held in the range **1.01–1.03 across all 200
epochs** — i.e., R2's gradient magnitude stayed essentially equal to R1's throughout training, with no
sign of collapse toward zero. R2's own reconstruction loss converged from 0.069 to 0.051 over training,
confirming the directed relation was being actively fit, not ignored. This directly answers the concern
S2 raised (a learned/second graph component can be trivially ignored by the optimizer) — C4-full's R2
component was demonstrably used.

### Stage-0 window check (VAL, seed42) — the numbers
| front-end | window macro AUROC (VAL) |
|---|---|
| rlg-full (recon+latent+gamma) — incumbent | **0.928** |
| C4-full 3-branch (recon-mr + latent-mr + gamma) | 0.909 |
| C4-full 2-branch (latent-mr + gamma, drop the anti-discriminative recon-mr) | 0.926 |
| rlg-lg diagnostic (rlg's own latent+gamma, no TE at all) | **0.9386** |

The 3-branch variant underperformed because `recon-mr` (the multi-relational reconstruction readout) was
itself anti-discriminative on VAL (AUROC 0.439, below chance) and dragged the equal-weight ensemble down
— this mirrors the same reconstruction-inverts-under-hypersynchrony failure mode from the original
S-series, now reappearing in the multi-relational reconstruction head specifically. Dropping it (the
2-branch variant) recovered most of the gap (0.926) but still landed within the measured window seed-SD
(0.002) of rlg-full (0.928) — i.e., statistically a tie, not a win, and multi-seeding cannot rescue a
tie that is already inside the noise floor. The `rlg-lg` control (plain latent+gamma, no TE at all,
computed as a matched ablation specifically to answer "is the directed relation adding anything at the
2-branch level") scored *higher* (0.9386) than the TE-containing 2-branch variant (0.926) — the cleanest
single number in Phase C showing that adding TE to the joint representation is net-negative, not merely
neutral.

**Verdict: NO-GO**, per the pre-registered gate (a real win must exceed the seed-SD and hold across
seeds; here the best TE-containing variant did not even beat its own TE-free ablation control).

### Per-subject ablation (why it's a genuine trade-off, not a bug)
Zeroing R2's message-passing contribution and re-measuring each subject's latent-mr AUROC isolated
exactly what the directed relation was doing:
- **chb22** (the subject C0 identified as most rescued by TE): latent-mr AUROC 0.736 → 0.873 with TE
  present (+0.137); ablating R2 confirmed ΔR2(chb22) = +0.126 — TE is doing almost all of that work, as
  expected from C0.
- **chb11** (a subject where the symmetric representation was already good): ΔR2(chb11) = −0.049 — TE
  actively hurts a subject it wasn't needed for.
- **chb10** (also symmetric-good): latent AUROC dropped 0.816 → 0.757 with the joint 2-relation encoder,
  but the ablation showed ΔR2(chb10) = +0.040 (TE itself is mildly *helpful* here) — meaning the harm to
  chb10 is **not caused by the added relation's content**, but by **splitting the encoder's fixed
  capacity across two relations**. This distinction (content vs. capacity) is what became the seed for
  the Phase-D hypothesis: the bottleneck may be that the ~8.7k-parameter 2-layer GCN encoder is simply
  too small to profitably represent *either* one relation well *and* a second — a capacity question,
  not a graph-relation-choice question.

### Self-correction on record
The original Stage-0 pre-registration set an *expected* input-fidelity band of [0.78, 0.88] for chb22's
zTE reproducibility check (a sanity bound, not the actual result). The measured value was 0.888 (0.83 ±
0.058 across the check), just outside the pre-set band on the high side. This was flagged and
investigated rather than silently accepted or silently dismissed: the correct interpretation is that the
band itself was mis-specified too tightly, and the true result *more strongly* reproduces C0's original
direction, not less. This is recorded explicitly so a later reader does not misread the flagged
discrepancy as evidence of an R2-input bug.

---

## Part 3 · Ensemble and signal-layer levers (closing the remaining gaps)

### Ensemble reweight / drop-recon — why it was not re-run
After seeing `rlg-lg` (0.9386) beat `rlg-full` (0.928) at the window tier, the naive next step would be
to test dropping the recon branch from the production ensemble. This was **not re-run**, because the
record already contained the answer at the level that matters (event, not window): `lg` (latent+gamma,
no recon) had already been measured at the §0 comparison cells during Phase B and found to underperform
rlg (0.579 balanced event F1 vs rlg's 0.618) — recon was retained specifically because of this earlier
result. Separately, `PREREG_03`'s weight-derivation sweep found the VAL objective surface effectively
flat across weight triples (24 distinct weightings within 0.005 AUROC of the argmax), which is why equal
weights were adopted in the first place as an anti-overfitting choice rather than a fitted optimum. Both
facts together mean: window-tier metrics and event-tier metrics disagree about whether recon helps
(window says drop it, event says keep it), and the event-tier answer governs, because event-level
performance is the thing actually being reported. This "window≠event" disagreement recurs as a theme
throughout Phase C and is one of the most citable single sentences for the Discussion chapter.

### Artifact / signal-quality gate
Motivated by a label-free diagnostic: are rlg's false-positive-prone interictal windows structurally
different from its true-negative interictal windows? A battery of per-window signal-quality features
(gradient statistics, amplitude, cross-channel similarity) was tested; the best single feature,
`grad_max` (the maximum first-difference across channels — i.e., how "jumpy" a window is), separated
FP-prone from clean interictal windows with AUROC 0.78–0.80 across all three VAL subjects (versus a null
of ~0.51 from label-shuffled controls) — a real, consistent signal that false positives are associated
with transient artifacts (sudden jumps/pops) that the existing ±5-SD amplitude-based preprocessing
rejection does not catch.

Two gating strategies were then tried:
1. **Per-window score suppression** using `grad_max` directly: flagged 85% of *ictal* windows as
   artifact-like too (seizures themselves produce high-gradient transients), making this variant
   unusable — it would suppress true detections at least as often as false ones.
2. **Duration/isolation gate:** suppress only *isolated* short (≤2-window) spikes, explicitly sparing any
   sustained multi-window elevation (which a real seizure produces but an isolated artifact usually does
   not). This reduced the ictal-flag rate to 3.5% macro (much more usable) and did produce a VAL Pareto
   improvement — but investigation showed the improvement occurred **only at the 5 FP/day operating
   point**, driven **entirely by one subject (chb11)**, with the Phase-C headline cell (3.6 FP/day)
   **completely unchanged**.

**Verdict: REJECTED**, applying the same hard-limit rule that caught the slope-gate false positive: a
1-subject, 1-budget effect measured on only 3 VAL subjects is exactly the kind of noise signature that
must survive a seed-check before being trusted, and per the pre-registered rule a win must be at the
actual headline cell, on a majority of subjects, and confirmed across a majority of seeds — this result
met none of those three conditions, so it was rejected without spending a seed-check cycle on it (the
lever failed the cheapest of the three criteria first).

### Multi-band AEC — the one lever scoped but not executed
Extending the existing gamma-only AEC branch to a full multi-band (theta/alpha/beta/gamma) AEC
representation was identified as a remaining candidate direction late in Phase C, but was explicitly
**deprioritized rather than tested**, on two priors already established by this point in the project's
own data: (1) the ensemble weight surface is flat (PREREG_03), and a weak or anti-correlated additional
branch can actively *drag down* an equal-weight ensemble — exactly what happened with C4-full's
anti-discriminative `recon-mr` branch; (2) representation enrichment in general had just been shown
(C4-full) to net-wash at the event headline even when it helps individual subjects. Given the Phase-C
time-box, this was judged low-expected-value relative to its build cost and consciously left as a
disclosed Future-Work item rather than silently omitted or quietly tested and hidden if negative.

---

## Part 4 · The closing discipline

Late in Phase C there was a real risk of declaring the optimization program "exhausted" prematurely —
generalizing from "the levers we've tried so far are negative" to "no lever could possibly work," without
first enumerating what remained. This was caught and corrected: before closing, the full remaining lever
space (ensemble reweight, artifact gate, multi-band AEC) was explicitly enumerated and each one either
tested to a clean verdict (artifact gate — rejected) or dead-on-record (ensemble reweight — already
answered by existing data) or consciously scoped out with a stated reason (multi-band AEC — disclosed
Future Work). Only once all three were accounted for was Phase C actually closed. This is the discipline
recorded in `RESULTS_OF_RECORD_phaseB.md` §9 as "seven independent levers... none Pareto-improved rlg" —
the number seven is a *closed, itemized* count, not an approximate impression, precisely because of this
late-stage enumeration check.

The same discipline extended to Phase D: rather than either quietly running a smaller, rushed version of
it or silently dropping the idea, the capacity hypothesis was fully pre-registered (hypothesis, staged
plan, falsifiable GO/NO-GO criteria) and then a deliberate, dated, reasoned decision was made not to
execute it, given the real IELTS/report/defense timeline. See `PHASE_D_HANDOFF.md` for that decision in
full — it is designed to be defensible in exactly the same way the seven executed Phase-C levers are.
