# DESIGN_PC6 — edge type of the graph: wPLI only / AEC only (Track F, chat D37-F, 22/11/2026)

Approved by the author 22/11 07:32 ("Tôi duyệt PC6"; the design proposed in chat D37-F on 21/11). Written and committed
**before any run**; nothing below is a result.

## 1 · Question and why it matters

V5 builds one graph per 4-s window: CAR → weighted phase lag index (wPLI) and amplitude envelope correlation (AEC) on the
18 derivations → A = 0.5·wPLI + 0.5·AEC → the top 20 % of the 153 channel pairs kept with their weights, diagonal zero
(`src/dataprep/graph_construction.py`: `combine_adjacency`, `apply_topk_threshold`; `c1b_build_trainset.graph_and_bp`).
The graph enters the GAE three times: the edges of message passing, the 18-value connectivity row of each node's input,
and the adjacency the decoder reconstructs. The council may ask why both measures and what each contributes.

- **Q1** Does a graph of one measure only change the detection: 11a = wPLI only (phase, insensitive to zero-lag
  coupling), 11b = AEC only (amplitude envelopes)?

Evidence already measured (for the hypothesis): the encoder adds no measurable development sensitivity over its own
30-value input (ablation 8b); removing every edge at inference changes FP/day by −0.3 [−2.4, +2.2] in V5 (ablation 8a)
and accounts for about a quarter of the GAE's excess false alarms against the autoencoder without message passing
(F-A1.4 fact 4); a time-stable graph at inference left that excess unchanged (fact 3).

## 2 · Arms (retrained)

| arm | graph per window (top 20 %, weights kept, diagonal 0) | node input | reconstruction target | parameters |
|---|---|---|---|---|
| **R0** (control) | 0.5·wPLI + 0.5·AEC (the record graphs) | 30 | 12 + adjacency | 3,964 |
| **11a** | wPLI only (`combine_adjacency(alpha = 1)`) | 30, connectivity row from the 11a graph | 12 + 11a adjacency | 3,964 |
| **11b** | AEC only (`combine_adjacency(alpha = 0)`) | 30, connectivity row from the 11b graph | 12 + 11b adjacency | 3,964 |

The arm's graph replaces the record graph everywhere the graph enters, at training and at inference; everything else is
R0's recipe (PC1 / PC7 / PC8): the 12 training patients' clean windows of the defense-time data (270,190 windows),
V5's feature constants, Adam 1e-3, cosine, batch 32, 200 epochs, last epoch, `eur_abl.train_masked` (gate below), then
V5's chain with **k recalibrated per arm on seed 42**. **Seeds 42, 1–7** per arm. Control R0 = PC7's primary seeds (the
16 new seeds of `pc7_A` / `pc7_B`), rows read, as PC8.

## 3 · Data step: the arm graphs (notebook `EUR_PC6_DATA`)

The record `.npz` hold only the combined graph, so wPLI and AEC are recomputed from the raw EDF:

- Raw CHB-MIT and Siena EDF verified against PhysioNet's SHA256SUMS in the session (`r2_core.inventory`, as EUR_9A and
  R0_EXT).
- **CHB-MIT (the 23 cases, defense-time file set = the `earlier` view):** the record builder `r2_core.features_record` →
  `c1b_build_trainset.build` with the **committed record statistics** (`data/processed/{case}_stats.json`), as EUR_9A's
  G-feat0. **chb24 + Siena:** the record builder of the external set `r2_core.ext_job` → `x1_external.build_subject`
  (label-free statistics), as R0_EXT.
- One change inside both builders: `c1b_build_trainset.graph_and_bp` is wrapped so that, per window, wPLI and AEC are
  computed **once** (the record functions) and three graphs are returned — the combined record rule (alpha 0.5), wPLI
  only (alpha 1) and AEC only (alpha 0), each `apply_topk_threshold(·, 0.20)` and float16 as the record. The builder
  saves the stack; the module splits it.
- **Gates (STOP):** G-raw (every EDF = PhysioNet); G-stack (every case returned three graphs per window: the wrapper ran
  in every builder process); G-struct (file list, window count, file index and every flag of each rebuilt case = the
  record `.npz` exactly); **G-adj** (the rebuilt combined graph = the record graph within R0's tolerance — entries
  differing by > 1e-3 ≤ 0.5 % on the chain windows, `r2_core.compare_features`; EUR_9A measured 0.04 % on chb08); bp5 and
  f7 within R0's tolerances (same function); G-edges (each arm graph: zero diagonal, finite, edges per window recorded);
  G-worker (every job ran the parent's modules). Recorded: fraction of differing entries per case, edges per window per
  arm, the share of window pairs whose kept edge set differs between 11a and 11b and the record.
- **Outputs:** `{case}_g11.npz` (`adj_11a`, `adj_11b`, float16, aligned with the record windows; no EEG) in
  `/kaggle/working/eureka/pc6_data/graphs/` + `manifest.csv` (sha256 of every file); small files (gates, per-case table,
  run_meta, manifest) are committed; the graph files become a Kaggle dataset (`thesis-pc6-graphs`) attached to the two
  training notebooks, never committed.
- Runtime ≈ 2.5–3.5 h (computed: EUR_9A's measured 6,103 s for the features of the 23 CHB-MIT cases + R0_EXT's measured
  1,903 s for the external set + inventory and comparisons; PC8 ran 15–30 % slower than computed, so the upper end is
  used).

## 4 · Training notebooks `EUR_PC6_11a`, `EUR_PC6_11b`

`src/eur_abl.py` with variants V0, R0 (PC1's seed 42 reused, gates G-pc7reuse / G-pc7k / G-pc7r0 as PC8) and the arm.
Additional gates: **G-g11data** (every graph file's sha256 = the committed manifest), **G-g11align** (each case's arm graph
has the record `.npz`'s window count), **G-pc6vec** (`train_masked` with the graph source = the record graph itself =
`f1_core.train` exactly: the override path changes nothing but the graph), **G-pc6enc** (the arm's inference with the
record graph = the record encoder's construction, first case of each set). Runtime ≈ 9.5 h each (measured basis: PC8's
9.42–9.56 h on the same machine type; same size as R0).

## 5 · Hypotheses (fixed before the run)

- **H11:** the edge type changes development sensitivity by less than the smallest detectable difference (≈ 0.024,
  computed from PC7, lower bound): 11a − R0 and 11b − R0 intervals containing 0. No directional prediction for F1 or
  FP/day.
- No arm can replace V5 in the Euréka files (results for the Q&A of 11/12); R214 not evaluated.

## 6 · Reading rule (`src/eur_pc6_read.py`, committed before the training runs)

As PC8 (`DESIGN_PC8.md` §4): per-patient means, own label-free point, after the localizer; development primary; test,
chb24, Siena descriptive. **R1** arm − R0 with the two-level bootstrap (B = 10,000) and PC8's wording; **R1m** (written
now, from the start) the same against the control seeds of the machine type of the arm run (G-pc7rep status); **R3**
seeds (losses, ms per step, machine); **R4** events at each budget (CPD stage); also **11a − 11b** (descriptive, same
bootstrap). Reader gates: M-gates, M0 (V0 rows identical in the two runs, the control runs and pc1_r0), M1 (R0 seed 42 rows
and k = pc1_r0), M2 (completeness), M4 (PC7's 10a − R0 reproduced: the control rows are PC7's).

## 7 · Limitations (stated)

The arm graphs are rebuilt on a Kaggle machine while R0's graphs are the record files (G-adj measures the difference;
retraining a control on the rebuilt combined graph is parked, plan §14). Arm and machine type are confounded within an
arm (R1m). Two measures at one density (20 %) and broadband only; band-specific graphs are not tested.

## 8 · Literature

- Tang, S., Dunnmon, J. A., Saab, K., et al. (2022). Self-supervised graph neural networks for improved
  electroencephalographic seizure analysis. *ICLR 2022*. https://doi.org/10.48550/arXiv.2104.08336 — correlation graphs per
  clip (absolute normalised cross-correlation) for seizure detection; a correlation graph localised focal seizures better
  than a distance graph.
- Duclos, C., et al. (2021). Differential classification of states of consciousness using envelope- and phase-based
  functional connectivity. *NeuroImage, 237*, 118171. https://doi.org/10.1016/j.neuroimage.2021.118171 — AEC and wPLI carry
  different information on the same data.
- Colclough, G. L., et al. (2016). How reliable are MEG resting-state connectivity metrics? *NeuroImage, 138*, 284–293.
  https://doi.org/10.1016/j.neuroimage.2016.05.070 — amplitude envelope correlation the most consistent; phase-lag measures
  poorer test–retest reliability (older than 5 years; the reference study of the question).
- Scientific Reports (2025). Reliability and state-dependency of EEG connectivity, complexity and network characteristics.
  https://doi.org/10.1038/s41598-025-23662-z — on EEG, phase-lag measures moderate-to-good reliability, amplitude-based
  measures inconsistent (the two reliability studies disagree, so no direction is predicted).
- Vinck, M., et al. (2011). An improved index of phase-synchronization for electrophysiological data in the presence of
  volume-conduction, noise and sample-size bias. *NeuroImage, 55*(4), 1548–1565. https://doi.org/10.1016/j.neuroimage.2011.01.055
  — the wPLI used here (the record function cites it).

## 9 · What this design does not do

No other measure (PLV, coherence, correlation), no other density, no learned graph; no change of the chain. The
deliverables keep V5's numbers.
