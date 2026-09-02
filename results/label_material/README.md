# Label material — EEG renderings used for channel labelling

Not results. Inputs to the human/AI reading pass that produced the ictal-channel labels.

| path | content |
|---|---|
| `seizure_segments/` | 76 per-seizure segment renderings (one per TEST seizure) |
| `../attribution_v5/labels/*_onset.png` | 76 onset views — the images the reading pass actually scored |
| `../attribution_v5/labels/*_review.png` | 76 wider review views |
| `../attribution_v5/labels/labels_*_FINAL.csv` | **the labels themselves — irreplaceable, never delete** |
| `../attribution_v6/labels/ictal_channels_DRAFT.csv` | §3.2-schema conversion of the above (AI-DRAFT, PROVISIONAL) |

Duplicate PNG/zip copies under `attribution_v6/labels/` were removed 2026-09-02 after byte-level
verification that they were identical to the v5 originals.
Regenerate views with `src/labeling/label_eeg_pilot.py`.
