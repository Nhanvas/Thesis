# THESIS_CONTEXT_FOR_DEMO.md

Rev. 2026-10-09 — **DRAFT by Project #2 from `DEMO_REBUILD_BRIEF.md` (2026-10-08); sections 1-3 and 5 need
Project #1's confirmation.** Items marked `<<…>>` are values Project #2 does not have and must not invent.

**Purpose.** Everything the demo build needs to know about the thesis — and nothing more. The scientific
record (results, pre-registrations, evaluation reports) is deliberately absent: the product shows no
evaluation number.

**Authority.** A *summary*, not a source of truth. If it disagrees with the thesis project's records or
with the thesis code in `src/`, those win and this file must be fixed. For demo behaviour,
`web_demo/SZSCAN_SPEC_v5.md` wins. **Only the thesis project may change §1-§3 and §5.**

---

## 1 · What the thesis does

Unsupervised, patient-independent-at-training, label-free-at-use temporal localization of epileptic
seizures in scalp EEG: a graph autoencoder over dynamic functional connectivity, a per-patient anomaly
score, a threshold detector and a change-point localizer.

**Framing the product must match: post-hoc EEG review triage.** The clinician already has the recording;
the system points at segments worth a second look. Not a real-time alarm, not a validated clinical device.
The final system is **non-causal by design** (±15-min running median, patient-level fits).

**Data.** CHB-MIT scalp EEG, 18-channel bipolar montage, 4 s non-overlapping windows at 256 Hz, band-pass
0.5-60 Hz + 60 Hz notch.

**Splits (locked).** TRAIN (12): chb01, 02, 04, 05, 07, 08, 09, 12, 19, 20, 21, 23 · VAL (3): chb10, 11, 22 ·
**TEST (8): chb03, 06, 13, 14, 15, 16, 17, 18.** The demo serves **only the 8 TEST subjects**.

## 2 · The pipeline the demo re-implements (final system, thesis tag `p3-frozen`)

```
per window: CAR → wPLI + AEC (alpha 0.5) → strongest 20 % of edges
node input 30 = adjacency row 18 | band powers 5 | 7 added features
              (log band power x5, log line length, signed-log kurtosis;
               scaled with the TRAINING constants saved beside the checkpoint, clip ±4 -> [0,1])
GAE v2 clean, seed 42 (encoder -> 16-d node latent)
per subject, per channel: LedoitWolf Mahalanobis distance of the node latent
   (fitted on all non-signal-loss windows of the subject) -> per-channel robust-z (median/MAD)
members: 6th, 9th, 12th largest of 18 channels, and the channel mean
   each minus its centred ±15-min (451-window) running median INSIDE each file
   each -> subject percentile ; equal mean = ONE ensemble anomaly score
detector: per-file centred moving average of 5 windows (signal loss = NaN, min_periods 1)
   threshold = (1 - p_i) quantile of the subject's smoothed score ; contiguous runs ; merge gaps <= 90 s
   p_i = clip(q_i, lo, hi) ; q_i = share of the smoothed mean of the four members' robust-z above k
   (k, lo, hi: read from results/p3c_freeze/freeze.json — never from prose)
localizer: ruptures KernelCPD (rbf, min_size 2, exactly 2 change points) on the unsmoothed score over
   each event ± 15 windows inside the file; accept the middle segment if >= 2 windows and its mean is above
   both outer segments, else keep the detector's boundaries; merge again (90 s)
event panel: per-channel robust-z of the distance (before the order statistic and the drift correction),
   p95 of |z| over the event's windows
```

Per-subject statistics (z-score from every 10th window of the whole recording, per-channel LedoitWolf,
robust-z, percentiles, q_i) are all fitted on **all windows of the uploaded subject, label-free**.

**Not in the system** (if any document describes them as live, it is stale): reconstruction readout,
gamma-AEC readout, graph-mean latent, PELT / `cpd_pipeline_v14`, LSTM, per-subject operating-point
calibration, the earlier fixed operating point 50 / 2.0 / 90, ensemble weights 1/3.

Defining code (read-only, `src/`): `retrain/train_gae_v2.py`, `c1b_build_trainset.py` (`f7`),
`p2_scalars.py`, `e16_recording_baseline.py` (`s_from_d`, `rz`), `e17b_latent_family.py`,
`e18_cpd_localizer.py` (`cpd_event`), `p3_levers.py`, `p3c_freeze.py`, `e23_test_look7.py`,
`attribution_v8.py`; template for a label-free upload pipeline: `x1_external.py`.

## 3 · The one checkpoint the demo may load

```
data/models_v2/gae_v2_clean_seed42.pt
3,964 parameters; node input 30
sha256  <<from docs/PROVENANCE_V2.md — Project #1 to supply>>
training constants saved beside the checkpoint: <<path / format — Project #1 to supply>>
```

**Identify it by hash, never by filename.** Retired and never to be loaded by the demo:
`data/models_retrain/gae_joint_seed42.pt` (earlier system, 3,285 params, node input 23),
`archive/pre_rebuild_s0/*`, `gae_multirel_seed42.pt`, v2 seeds 1/2/3 and the `all` variants (robustness
checks only). The training constants are part of the checkpoint's identity.

## 4 · The demo's relationship to the thesis numbers

The product displays **no evaluation metric**. The demo is, however, evaluated once as an application
(task T1): every AI event is exported to CSV before any review and scored **outside the demo** by the
thesis scorer. Demo output differs from offline thesis output by construction (label-free statistics vs the
thesis's CHB-MIT z-score statistics, which exclude annotated seizure and buffer windows). The one place
where agreement *is* required is the identity gate: fed the same statistics, the demo chain must reproduce
the thesis code path on chb03. **Never tune the demo to match numbers.**

## 5 · Attribution — the constraint that matters for the UI

The panel is XAI for the GAE per-channel latent readout: which channels are most anomalous during a flagged
event. **Not localization, not seizure onset zone.** The label-scored evaluation is closed and negative on
two different readouts. Panel title: `Channel-level latent anomaly — Event N`. No causal or localizing
language ("causing", "focus", "origin", "source"). No attribution metric on screen. It applies equally to
user-created events (any window range).

## 6 · What may change on the thesis side, and how it reaches the demo

Only: (1) the checkpoint and its constants (§3); (2) the pipeline definition (§2); (3) the attribution
interpretation limits (§5) — each as a new version of this file carried by Boti.

## 7 · Vocabulary

| Term | Meaning here |
|---|---|
| window | 4 s of EEG; `t_seconds = window_index × 4` |
| ensemble anomaly score | the one per-window scalar of §2 (percentile mean of four members) |
| budget p_i | the per-patient share of time the detector may flag |
| event | a contiguous flagged region after localization; what the UI shows; lives inside one file |
| localizer | the kernel-CPD step that refines event onset/offset |
| signal-loss window | raw std < 1e-10 V on all 18 channels; excluded from every fit, NaN in the score |
| interictal / ictal | thesis vocabulary, **never surfaced in the UI** |
| label-free | uses no annotation at any step |
| SzCORE | the scoring standard used outside the demo; not used by the demo |
