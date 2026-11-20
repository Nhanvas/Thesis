# D32-F — optimisations O6 and O7 on the V5 model (design 20/11/2026 14:30; approved by the author 14:14)

*Written before any O6 / O7 code or output. Chat D32-F, Track F. Frame: `results/eureka_d31f/STEP1_DESIGN.md` (suite,
readings, R214 rule) and `ROADMAP_LOGBOOK.md` Phase B. The author's direction (20/11 12:58, 13:50): optimise on the GAE
basis, raise the novelty and remove limits from the causes already identified; no change of direction.*

## 0 · The cause each experiment acts on (measured, not assumed)

- **L1 / L2 share one cause** (V5 Figure 18, the oracle bound; `EUREKA_PLAN.md` §10): the patient's own high-amplitude
  non-seizure activity outranks the seizures.
- **That activity is not rare, it is a large state of the background:** the 5-SD flag marks 28–60 % of every patient's
  non-ictal windows (RB1c, board R189); false alarms carry the flag 1.3–2.9 times their base rate (F-A1.3).
- **V5 models each channel's normal latent as ONE Gaussian** (Ledoit–Wolf mean and covariance over the whole
  recording). A frequent high-amplitude state far from the bulk is then scored by its distance to a centre it does not
  belong to, so its windows fill the top of the ranking; ablation 1a / 1b showed the covariance is the core of V5, but
  not whether one component is enough.
- **Indirect evidence that more than one mode exists:** on the same node input, per patient and channel, the
  silhouette chose 2 clusters in 390 of 432 pairs and the nearest-centroid score beat the GAE in 6 / 6 partitions
  (F-A1.6). *Disclosure:* that comparison is a 4-fold CV over the 24 cases, test patients included, so the idea is
  informed by it; the choice below is made on the development patients only.
- **The GAE's false alarms are more and shorter events and its background score alternates from window to window**
  (lag-1 autocorrelation −0.13 [−0.14, −0.12], F-A1.4): window-level noise in the latent that a short temporal context
  could average out before the distance (the registered Objective 1 names spatial-temporal features).

## 1 · Literature (read 20/11)

- Zong et al. (2018), *Deep Autoencoding Gaussian Mixture Model for Unsupervised Anomaly Detection*, ICLR 2018
  (https://iclr.cc/virtual/2018/poster/126): an autoencoder's low-dimensional representation scored by a Gaussian
  mixture density — the precedent for a mixture on an autoencoder latent.
- Coupled IGMM-GANs (arXiv 1809.02728): the latent treated as a mixture of Gaussians and scored by a multimodal
  Mahalanobis distance to the components.
- Multi-normal prototypes (arXiv 2408.14498): a single normal prototype fails on a multi-modal normal distribution and
  gives normal samples in other modes high scores.
- Rippel et al. (2021), DOI 10.1109/ICPR48806.2021.9412109; Defard et al. (2021), DOI 10.1007/978-3-030-68799-1_35: the
  single-Gaussian Mahalanobis on features (V5's construction).
- No peer-reviewed EEG seizure study with a per-patient mixture on a learned latent was found (search 20/11).

## 2 · Variants (inference only, the four V5 checkpoints, everything else V5)

| ID | change from V5 | label-free choices (fixed now) |
|---|---|---|
| **O6a** | per patient and channel, the latent is modelled as **K Gaussian components**: a full-covariance Gaussian mixture fitted on 5,000 of the patient's windows (sampled with rng 42; all windows if fewer) assigns every window to its most probable component; each component's mean and covariance are re-estimated by Ledoit–Wolf on all its windows; score = **the smallest Mahalanobis distance to a component** | K ∈ {1, 2, 3, 4} by the lowest BIC of that mixture (sklearn `GaussianMixture`, reg_covar 1e-6, n_init 3, random_state 42); a component holding fewer than max(64 windows, 5 % of the patient's windows) is dropped — a kept component must be a substantial background state like the high-amplitude state (28–60 % of the background), because a small component could hold the patient's seizures and mask them (the masking world of F-A1.6's synthetic test) and its windows re-assigned to the most probable remaining component (fixed before the run; counted); K = 1 is exactly V5's `LedoitWolf().fit(X).mahalanobis(X)` (gate G-mix1) |
| **O6b** | as O6a with K = 2 for every patient and channel | — |
| **O7** | the latent of each window averaged with its two neighbours in the same file (3 windows, 12 s) before V5's single-Gaussian distance | neighbours = the previous and next valid windows of the same file (signal-loss windows are not in the sequence); file edges use the neighbours that exist |

The members (6th / 9th / 12th + mean), drift correction, percentile ensemble, smoothing 5, budget clip(q, 0.5 %, 2 %)
with **k recalibrated per variant** on development (seed 42) and the kernel CPD localizer are V5's code unchanged.

## 3 · Rules (fixed before the run)

- **Replacement rule R214 (as 19/11):** on the 15 development patients, own label-free point after the localizer, 4-seed
  per-patient means, paired patient bootstrap (B = 10,000, rng 0, chb01 + chb21 one unit): a variant is a candidate only
  if its ΔF1 interval is above 0 **and** its Δsensitivity ≥ 0. If several pass, the one with the larger development ΔF1
  point; then its combination check (O6 × O7) only if both pass, under the same rule. The test, chb24 and Siena rows of
  the candidate are read once, after that choice. Three variants are tried; this multiplicity is disclosed.
- **Premise read beside the result (development, descriptive):** the K chosen per patient and channel; the share of
  5-SD-flagged background windows outside the largest component; for O7, the change of the lag-1 autocorrelation.
- **Wording limits:** a passing variant changes V5's density model on the GAE latent (O6) or adds a temporal context to
  it (O7); the GAE, the graphs and the inputs are unchanged. A non-passing variant is reported as an ablation with all
  its rows.

## 4 · Gates and cost

- Gates as EUR_ABL (G-data, SMOKE, R1.0, GE, G-k, G-kv0, G-D0, G-enc, G-x0, G-eng, G-worker, G-self) plus **G-mix1**:
  K = 1 gives V0's distances exactly (one case per set), and a synthetic two-mode world where O6a lowers the score of
  the second mode.
- Code: `src/eur_abl.py` (distances `mix` / `mix2`, encoder option `ctx3`), notebook `EUR_OPT` (`EUR_VARIANTS=V0,O6a,O6b,O7`,
  `EUR_TAG=opt`); aggregate `src/eur_abl_aggregate.py` unchanged.
- Kaggle: one verified account, ≈ 1–1.5 h (computed: EUR_ABL 0.868 h measured + mixture fits on 5,000 windows × 18
  channels × 4 seeds × 38 cases); synthetic test before delivery. Run tonight 20/11, read 21/11 morning, hand-off before
  the freeze (22/11 evening).
