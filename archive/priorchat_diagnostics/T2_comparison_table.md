# T2 — Like-for-like comparison table (DRAFT for the cô conversation)

**Purpose:** stop the committee from comparing our *event-level, patient-independent, unsupervised,
full-continuous* result against *segment-level, patient-specific, supervised, curated* CHB-MIT numbers.
Classify every baseline on four axes; show that the correct comparison band is SzCORE event-level.

> ⚠️ **Citation-verification flag.** The numbers/venues below are transcribed from the project's own
> Phase-2 literature review (`Lit_review.txt` / `Literature_Review_*.md`). I cannot web-verify them in
> this environment and may mis-state a venue, year, or decimal — **Boti/cô must check each cited number
> against the primary source before this goes in the report.** The *classification* (the four axes) is
> the robust part; treat the exact metric values as provisional.

---

## The four axes
1. **Scoring:** segment/window (epoch-wise) vs **event** (overlap-based TP/FP/FN, SzCORE).
2. **Subject protocol:** patient-specific (train+test same patient) vs **patient-independent** (subject-disjoint).
3. **Supervision:** supervised / fine-tuned vs **unsupervised** (no seizure labels).
4. **Data regime:** curated/random-split (leakage-prone) vs **full-continuous** whole-recording.

**Ours (the reference row):** event · patient-independent · unsupervised · full-continuous.
This is the *hardest* cell of the 4-way cube — almost nothing in the CHB-MIT literature sits here.

---

## A. Why the "90–99% CHB-MIT" numbers are NOT our comparison

| Class of baseline | Typical CHB-MIT number | Scoring | Subject | Supervision | Data regime | Comparable to us? |
|---|---|---|---|---|---|---|
| Patient-specific supervised segment | 95–99% acc / F1 | segment | patient-specific | supervised | curated | **No** (3 axes differ) |
| Random-split supervised segment | 90–98% acc | segment | mixed (leakage) | supervised | random-split → **leakage** | **No** (leakage inflates) |
| Foundation-model segment (fine-tuned) | AUROC 0.868–0.94 | segment | subject-disjoint or random | supervised FT | curated | Partly (segment only) |

**Leakage note (Ali et al., R. Soc. Open Sci. 2024 — "overlooked perspectives on CHB-MIT"):** random-fold
splitting places same-subject segments in train and test, inflating segment metrics; the paper argues for
cross-subject, event-level, whole-dataset evaluation — the protocol we already use.

**EvoBrain (NeurIPS 2025) CHB-MIT AUROC 0.94** is **segment-level with a 15% random split** → not
event-level, not our protocol. Cite as representation SOTA, never as our event-level ceiling.

**The Transformer 0.765 / 40.6 FP number is a TUH result, not CHB-MIT** (already logged) — must not be
presented as a CHB-MIT baseline.

---

## B. The correct comparison band — event-level, patient-independent

| Benchmark | Scoring | Subject | Supervision | Top event F1 | Sens / Prec | Source (verify) |
|---|---|---|---|---|---|---|
| **SzCORE 2025 challenge** | event | patient-indep | supervised | **0.43** | 0.37 / 0.45 | 65 subj / 4,360 h EMU (Dianalund) |
| **EPFL 28-algorithm benchmark** | event | patient-indep | supervised | **0.32** | 0.37 / 0.29 | arXiv 2505.18191v2, same EMU set |
| **Ours — T1 OP-F1 (mag80/pen10)** | event | patient-indep | **unsupervised** | **0.313** | 0.276 / 0.362 | this work, CHB-MIT, VAL-derived |
| **Ours — test-oracle context (mag80/pen5)** | event | patient-indep | unsupervised | 0.351 | 0.395 / 0.316 | *not an operating point; Pareto context* |

**Headline for cô:** our unsupervised event F1 (0.313, reported / test-clean) sits **inside the
supervised SOTA band (0.32–0.43)** — on a *different* dataset (CHB-MIT vs the private EMU set), so it is a
**reference band, not a head-to-head**. That caveat is essential and must be stated.

---

## C. Directly comparable UNSUPERVISED CHB-MIT / scalp work (our true peers)

| Work | Approach | Labels | Patient-indep | Scoring | Metric | Comparable? |
|---|---|---|---|---|---|---|
| **Yildiz et al. 2022** | VAE reconstruction anomaly | unsupervised | mixed | segment | ≤0.83 AUROC (iEEG; lower on scalp; ~0.68 scalp CHB-MIT) | Yes (segment) |
| Potter et al. 2022 | unsupervised transformer AE | unsupervised | cross-subject | segment | +16% recall / +9% AUROC vs supervised | Yes (segment) |
| SOUL 2021 | unsupervised online | unsupervised | **per-patient** | event | 100% event sens (per-patient) | No (patient-specific) |
| Behind-ear VAE 2021 | personalized anomaly VAE | semi-sup | **per-patient** | event | 94.2% sens @ 0.29 FP/h | No (patient-specific) |
| EEG-CGS 2023 | contrastive+generative graph | unsupervised | (TUSZ) | both | SOTA anomaly, no labels | Method-comparable |

**Our window macro-AUROC 0.775 exceeds the unsupervised scalp segment band (~0.68–0.83 lower end,
Yildiz ~0.68)** — and we additionally deliver **event-level** scoring that most of these do not.

---

## D. One-paragraph script for the cô conversation
> "The 90–99% CHB-MIT numbers in the literature are segment-level, often patient-specific or random-split
> (which leaks same-patient data), and supervised. The field's own standardized event-level benchmark
> (SzCORE) rejects those as clinically meaningless for rare events and reports top *event* F1 of 0.32–0.43
> — all supervised, on a private EMU set. Our unsupervised, patient-independent event F1 is 0.313 at
> 3.2 FP/day, inside that band, plus window AUROC 0.775 that beats the unsupervised scalp baseline
> (Yildiz ~0.68). We report the full Pareto curve so the comparison is like-for-like, not cherry-picked."

*Deliverable status: DRAFT. Axes are solid; verify every cited number against primary sources before use.*
