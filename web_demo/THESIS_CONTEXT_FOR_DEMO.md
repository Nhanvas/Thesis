# THESIS_CONTEXT_FOR_DEMO.md

**Purpose.** Everything the demo build needs to know about the thesis — and nothing more. This exists so
the demo project does not have to carry the scientific document set (`RESULTS_OF_RECORD_phaseB.md`,
the pre-registrations, the Phase-C audit). Those files govern the thesis; this file governs what the
demo is allowed to assume about it.

**Authority.** This is a *summary*, not a source of truth. If it ever disagrees with
`docs/RESULTS_OF_RECORD_phaseB.md` or `docs/PROVENANCE.md` in the main repo, those win and this file is
wrong and must be fixed. For demo behaviour, `web_demo/SZSCAN_SPEC_v5.md` wins over this file.

---

## 1 · What the thesis does

Unsupervised, patient-independent temporal localization of epileptic seizures in scalp EEG, using a
graph autoencoder over dynamic functional connectivity plus change-point detection.

**Framing, which the product must match: post-hoc EEG review triage.** A clinician already has the
recording and is rewatching it; the system points at segments worth a second look. It is **not** a
real-time alarm, and it is **not** a validated clinical device.

**Data.** CHB-MIT scalp EEG, 18-channel bipolar montage, 4 s non-overlapping windows at 256 Hz,
bandpass 0.5–60 Hz plus 60 Hz notch, per-subject z-scored.

**Splits (locked, never violate).**

| split | subjects |
|---|---|
| TRAIN (12) | chb01, 02, 04, 05, 07, 08, 09, 12, 19, 20, 21, 23 |
| VAL (3) | chb10, 11, 22 |
| **TEST (8, one-shot)** | **chb03, 06, 13, 14, 15, 16, 17, 18** |

The demo serves **only the 8 TEST subjects**. Serving a TRAIN subject would mean demonstrating on
training data — the one question the whole thesis design was built to survive.

---

## 2 · The pipeline the demo re-implements (`rlg`)

```
per-window graphs (wPLI + AEC, top-k 20 %)
 → Joint GAE (seed 42; encoder GCNConv 23→64→16, ~8.7k params;
              node features = [adjacency row 18 | band powers 5])
 → 3 readouts
     zrecon   reconstruction MSE
     zlatent  latent Mahalanobis (LedoitWolf on graph-mean 16-d Z)
     zgamma   gamma-band AEC anomaly
 → per-branch robust-z (median / MAD)
 → EQUAL-weight ensemble, 1/3 each
 → PELT change-point detection (cpd_pipeline_v14)
 → label-free per-subject FP-budget operating point
```

**There is no LSTM / temporal branch.** It was dropped: its training code was unrecoverable and its
numbers depended on lost components. The latent-Mahalanobis readout replaced it, and that replacement is
the core contribution. Five LSTM files still sit in `src/retrain/` purely as provenance of the decision.
**If any document, comment, or older spec describes a temporal branch, that text is stale — do not
implement it.**

The ensemble weights are equal by pre-registration; the weight surface was measured flat. Do not
introduce weight tuning.

---

## 3 · The one checkpoint the demo may load

```
data/models_retrain/gae_joint_seed42.pt
15258 bytes
sha256  dea06cb533df1c7d0520ae21c4cbb1b8a938297f937366bc9915b040726ea108
```

**Identify it by hash, never by filename.** A retired model in `archive/pre_rebuild_s0/` reproduces the
same outputs at correlation 0.987–0.999 — close enough to pass a careless check and be the wrong model.
It did exactly that once. `gae_multirel_seed42.pt` is a killed experiment and must not be used.

Seeds 1/2/3 exist for robustness checks and are not the demo's model.

---

## 4 · The demo's relationship to the thesis numbers

**The demo displays no evaluation metrics.** No sensitivity, no FP/day, no AUROC, no precision, no
operating-point parameters. Those belong to the thesis report and the defense slides, not to the product.
This is why the scientific document set is deliberately absent from the demo project: there is nothing in
the product that needs a number from it.

**Demo output will not match thesis output, by construction.** The thesis evaluates on label-derived,
artifact-filtered segments with the 4-hour post-seizure buffer removed. The demo runs label-free on the
intact continuous recording. Same model, same weights, different input conditions. See
`SZSCAN_SPEC_v5.md` §1.6 for the two divergence groups and the prepared answer for the committee.

**Never make demo numbers match thesis numbers.** If they diverge more than expected, the response is to
observe and document, not to tune.

---

## 5 · Attribution — the constraint that matters for the UI

The channel attribution panel is **XAI for the GAE reconstruction branch**. It shows which channels the
autoencoder reconstructs worst during a flagged event.

**It is not localization. It is not seizure onset zone.** The label-scored evaluation is
**PROVISIONAL**, and the labels it was scored against record only the reader's dominant channel or two
per seizure, not the full ictal channel set — so the numbers answer a narrower question than intended.

Consequences the UI must respect:
- Panel title: `Channel-level reconstruction anomaly — Event N`.
- No causal or localizing language anywhere ("channel causing", "seizure focus", "origin", "source").
- No attribution evaluation metric on screen.
- Attribution is computed per window, so it aggregates over any time range — it works for user-created
  events exactly as it does for AI-detected ones.

Full detail lives in `docs/ATTRIBUTION_SPEC.md` §9 in the main repo. Only §9 is relevant here.

---

## 6 · What is closed and must not be reopened

Optimization is over. The final pipeline is fixed. Seven pre-registered levers were tried and none
improved the result; the closure is documented as an evidence-based negative, which is itself a
contribution. **The demo project must never propose a model change, an ensemble reweighting, a new
feature, or a "small improvement" to detection quality.**

If demo detections look wrong, the only permitted lever is the **operating point** — which is label-free
and therefore legitimate. Everything upstream of it is frozen.

---

## 7 · Vocabulary

| Term | Meaning here |
|---|---|
| **window** | 4 s of EEG, the atomic unit; `t_seconds = window_index × 4` |
| **event** | a contiguous flagged region produced by change-point detection; what the UI shows |
| **interictal / ictal** | between seizures / during a seizure — thesis vocabulary, **never surfaced in the UI** |
| **operating point** | the label-free threshold rule converting scores into events |
| **label-free** | uses no ground-truth annotation at any step; the demo's central claim |
| **SzCORE** | the event-scoring standard used by the thesis; **not used by the demo at all** |
