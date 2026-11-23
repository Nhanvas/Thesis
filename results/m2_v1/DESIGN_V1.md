# M2 item V1 — seizures found against the share of the recording reviewed (design; chat F2-02)

*Approved by the author 23/11/2026 13:39, before any code ran on real data. Written and committed before the run;
the reader `src/eur_v1_read.py` is committed with it. Plan: `docs/FUTURE_RESEARCH_PLAN.md` §15.4 (V1); this text becomes
a row of plan §12 tagged F2-02.*

## 1 · Question and why

**How many seizures does the V5 system put in front of the reader for a given share of the recording reviewed?**
V5 is reported at one label-free operating point (test: 0.567 at 28.7 FP/day, 2.1 % of the recording reviewed). A
reader who can open more, or less, of a recording needs the whole curve; SzScan's intended use is offline review support
that ranks candidate intervals for a human (plan §15.2). V1 answers this for the frozen baseline (V5), as evidence for
M2 streams L, X and G and for CNCL's later choice of method and model.

## 2 · Literature (read before the design)

| work | what it did | use here |
|---|---|---|
| Roy et al. 2021, *Evaluation of artificial intelligence systems for assisting neurologists with fast and accurate annotations of scalp electroencephalography data*, EBioMedicine 66:103275, DOI 10.1016/j.ebiom.2021.103275 | sensitivity 75–91.6 % with the raw EEG to review reduced 142× to 22× (≈ 0.7–4.5 % of the data; computed) | axis (a): the share of the raw recording the reader opens |
| Moura et al. 2014, *Spectrogram screening of adult EEGs is sensitive and efficient*, Neurology 83:56–64, DOI 10.1212/WNL.0000000000000537 | readers viewed 120 s of raw EEG around each suspicious CSA segment; 24 h reviewed in 8 vs 38 min | (b2): a fixed 120-s clip per candidate |
| Koren et al. 2018, *Automated long-term EEG review: fast and precise analysis in critical care patients*, Front Neurol 9:454, DOI 10.3389/fneur.2018.00454 | 6-h datasets reviewed in 3.3 min with automated pattern detection; agreement against unlimited conventional review | design of a later reader study (H1) |
| Scheuer et al. 2021, *Seizure detection: interreader agreement and detection algorithm assessments using a large dataset*, J Clin Neurophysiol 38:439–447, DOI 10.1097/WNP.0000000000000709 | experts 0.4–1.0 false positives per day; Persyst 14 78.2 % at 1.0/day | context only (other data, other scoring) |
| Reus et al. 2022, *Automated seizure detection in an EMU setting: are software packages ready for implementation?*, Seizure 96:13–17 (PMID 35042003) | commercial packages: median 1.7–5.5 false positives per 24 h | context only |

None scored CHB-MIT or Siena with SzCORE event scoring; no number of theirs is compared with ours in a table.

## 3 · Data, model, sets

- The four committed V5 checkpoints `data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt`; inference only; the defense-time data
  copy (`v9-x3-fold1`, `v9-x3-fold3`) and the external features (`thesis-r2-external-features`), as EUR_ABL.
- Sets: development 15 (12 training + 3 validation patients; optimistic), test 8, chb24, Siena 14. Test, chb24 and Siena
  are descriptive; the test patients have been seen many times (plan §15.2).
- The V5 chain unchanged: ensemble score x = `e22_test_oneshot.final_scalar`, budget signal m = `p3_levers.member_mean_z`,
  k by V5's label-free rule (`p3_levers.calibrate`, 15 development patients, seed 42), smoothing 5 windows, merge 90 s,
  change point localizer (`p3_levers.localize`, mode cpd), SzCORE scoring (`timescoring`, 30 s / 60 s, merge < 90 s,
  split > 300 s).

## 4 · What is computed (per case and seed)

1. **V5's own point** (`eur_abl.run_budget_s`, arms own and fixed, stages detector / cpd / hybrid) = EUR_ABL's V0 rows.
2. **(a) Budget sweep.** The same share of windows flagged for every patient — 0.1, 0.2, 0.3, 0.4, 0.5, 0.65, 0.75, 1, 1.5,
   2, 3, 5, 7.5, 10, 15, 20 % (the six committed curve points included) — at the detector stage (primary: the ranking
   itself) and the cpd stage (secondary: the deployed chain; the localizer was not designed for the long merged events of
   large budgets). Per row: tp, fp, n_ref, non-ictal hours, **review time = the time of the events actually opened**
   (after merging and the localizer), number of events; per annotated seizure caught or not.
3. **Chance reference.** x circularly shifted within each file over its valid windows (10 shifts; rng fixed by case, seed
   and shift; the values of each file are only permuted, so every budget flags the same number of windows), detector
   stage, every budget. Reason: at 10–20 % review a ranking without information already catches seizures through the
   30 / 60-s tolerances and the merging.
4. **(b) Top-N events per hour of EEG**, unit = the whole recording of one patient, H = its recorded hours, rates r = 0.1,
   0.25, 0.5, 1, 2, 4, 8 per hour, N = ceil(r × H):
   - **b1** V5's own events (cpd stage, own budget) ranked by peak smoothed score; N capped by the number of events; "all"
     = every event (= the own cpd row);
   - **b2** peak-centred 120-s clips (windows i − 15 … i + 14) chosen by non-maximum suppression on the smoothed score;
     two clip centres of a file are > 53 windows apart, so two clips are always > 90 s apart and the scorer never merges
     them; review time = the clips' total length.
5. **(c) Missed seizures** at 5 % and 10 % of windows flagged, both stages: per annotated seizure the number of seeds that
   caught it (0–4), joined to the model-free descriptors of `results/v9_v1/part1_descriptors.csv` (amplitude ratio,
   duration, spatial extent, dominant frequency); a registry column for `docs/FAILURE_REGISTRY.md` (F2-01; not yet on
   `main` on 23/11) stays empty until it exists.

**Per-seizure flag:** the scorer's own TP loop re-read event by event on its own (merged / split) reference events; an
annotated seizure is caught if a scorer reference event overlapping it is a TP. Where the scorer merged two seizures or
split one longer than 300 s, the flags are descriptive.

## 5 · Reading (the reader, committed before the outputs)

- Per patient: 4-seed mean (chance: mean over seeds and shifts) of tp / n_ref (patients with ≥ 1 seizure), FP/day =
  fp / non-ictal h × 24, review share = review time / recorded time, events per hour. Per set: mean over patients;
  pooled seizures found / annotated (4-seed mean) beside it.
- Patient bootstrap B = 10,000, rng 0; units = patients, chb01 + chb21 one unit; V5 − chance paired (same draw).
- Tables: (a) per set × stage × budget; V5's own point beside; (b) per set × method × rate; (c) per seizure and a
  summary (caught by all / some / no seed; descriptor medians); one figure (seizures found against the share reviewed, one
  panel per set, chance and V5's own point drawn).
- **No pass / fail threshold.** Expectations written now, as hypotheses only: (H1) V5 is above chance at every budget
  ≤ 5 % on every set; (H2) the seizures still missed at 10 % are the short, low-amplitude ones (the V5 / RP4 association).
- Reader gates: M0 rows complete; M1 every run gate PASS; M2 per-seizure flags sum to tp wherever the scorer's reference
  count equals the annotated count; M3 b1 "all" = the own cpd rows.

## 6 · Gates of the run (STOP unless PASS)

G-self-v1 (synthetic: shift, NMS, scorer replica = `e10_kernel_cpd.score_events` on 20 random worlds); G-data; SMOKE
(chb01, chb03, chb24 end to end; projection STOP if > 10.5 h); R1.0-dev / R1.0-test / GE / G-k (`r2_r1.r10` unchanged);
G-kv1 (k = EUR_ABL's V0 k, relative 1e-6); **G-v5own** (own rows and onset / offset errors = the committed
`results/eureka_d31f/abl` V0 rows: development and test exactly — integers equal, floats relative 1e-12 — external within
the GE tolerance |Δtp| ≤ 1, |Δfp| ≤ 2 with non-ictal hours and recorded seconds exact); **G-curve** (detector rows at the
six committed budgets = `curve.csv` V0, same rule); G-score (every grid row: the scorer replica = `p2_scalars.score`) and
G-b1all inside each job; G-worker (sha256 of every module in every pool job).

## 7 · Wording limits

Development includes the 12 training patients; test, chb24 and Siena descriptive; external V0 rows come from the rebuilt
external features (Siena V0 0.645 against the report's 0.633) — the deliverables keep V5's numbers. A budget is the share of
windows above the threshold; the share of the recording reviewed is larger (merging, change point boundaries) and is the
x of every curve. Event-level SzCORE matching with 30 / 60-s tolerances: at large review shares chance catches many
seizures, so V5 is read against chance. Nothing here is a reader study: review time in minutes is not measured.

## 8 · Code, run, cost

- `src/eur_v1.py` (new module of the EUR suite; imports `eur_abl` and the record modules read only), `src/eur_v1_read.py`,
  `src/eur_v1_synthetic_test.py` (ALL PASS, incl. the negative paths), notebook `EUR_V1` (`src/eur_make_notebooks.py
  --only EUR_V1`, sha256 of every module asserted).
- Kaggle `nhancoding`, CPU, Internet ON; inputs `nhn2mm/v9-x3-fold1`, `nhannguyen26/v9-x3-fold3`,
  `norncreades/thesis-r2-external-features`. Output
  `/kaggle/working/eureka/v1` → `results/m2_v1/run/`; reading → `results/m2_v1/reading/`.
- Cost ≈ 1–2 h (computed from EUR_ABL's measured 0.868 h; about the same number of scorer calls per case and seed); the
  SMOKE measures it and writes `projection.json`.
