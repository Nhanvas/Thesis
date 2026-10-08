# Attribution A5 -- final system (per-channel latent anomaly), seed 42 primary

Pre-registered in ATTRIBUTION_SPEC A5 and the docstring of src/attribution_v8.py. Method, labels and tests of A4; only the per-channel score changes. Gates G1, G2, G3 passed.

```
focal=62  generalized=14 (excluded: AUROC undefined)  macro prevalence=0.2527

wrote F:\Study\Thesis\Code\results\attribution_v8\attribution_perseizure.csv  (62 rows)
=== L1 PRIMARY (seed42, p95, all focal) ===
  ALL focal (primary)        n=62  AUROC=0.5473 [0.4992,0.5971] p=0.0180  AUPRC=0.4275 (prev 0.253)  R@S=0.3215  prior=0.7387

=== descriptive panels ===
  focal excl. chb15 (D8)     n=42  AUROC=0.4864 [0.4362,0.5323] p=0.7123  AUPRC=0.4134 (prev 0.312)  R@S=0.3104  prior=0.8164
  focal n_win>=3 (D5)        n=59  AUROC=0.5490 [0.5033,0.5942] p=0.0160  AUPRC=0.4239 (prev 0.249)  R@S=0.3196  prior=0.7328
  ALL focal (mean agg)       n=62  AUROC=0.5559 [0.5074,0.6066] p=0.0110  AUPRC=0.4518 (prev 0.253)  R@S=0.3365  prior=0.7387
  ALL focal seed1            n=62  AUROC=0.5434 [0.5027,0.5876] p=0.0350  AUPRC=0.4025 (prev 0.253)  R@S=0.2999  prior=0.7387
  ALL focal seed2            n=62  AUROC=0.5881 [0.5361,0.6382] p=0.0010  AUPRC=0.4696 (prev 0.253)  R@S=0.3557  prior=0.7387
  ALL focal seed3            n=62  AUROC=0.5449 [0.5008,0.5914] p=0.0350  AUPRC=0.4138 (prev 0.253)  R@S=0.3160  prior=0.7387

=== per subject ===
  subject chb03              n=4   AUROC=0.4044 [0.3187,0.5288] p=0.9271  AUPRC=0.4834 (prev 0.458)  R@S=0.3889  prior=0.9032
  subject chb06              n=0  (no channel metric: all seizures generalized)
  subject chb13              n=11  AUROC=0.5078 [0.4280,0.5851] p=0.4456  AUPRC=0.4182 (prev 0.303)  R@S=0.3485  prior=0.7525
  subject chb14              n=8   AUROC=0.5547 [0.4447,0.6721] p=0.1409  AUPRC=0.4997 (prev 0.319)  R@S=0.3552  prior=0.8074
  subject chb15              n=20  AUROC=0.6754 [0.6020,0.7538] p=0.0010  AUPRC=0.4570 (prev 0.128)  R@S=0.3450  prior=0.5757
  subject chb16              n=10  AUROC=0.4870 [0.3631,0.6108] p=0.5864  AUPRC=0.4224 (prev 0.306)  R@S=0.3110  prior=0.8458
  subject chb17              n=3   AUROC=0.4178 [0.2679,0.6462] p=0.7912  AUPRC=0.3119 (prev 0.241)  R@S=0.2167  prior=0.8313
  subject chb18              n=6   AUROC=0.4438 [0.3588,0.5184] p=0.8062  AUPRC=0.2788 (prev 0.269)  R@S=0.1742  prior=0.8309
wrote F:\Study\Thesis\Code\results\attribution_v8\attribution_summary.csv  (14 rows)
wrote F:\Study\Thesis\Code\results\attribution_v8\attribution_tests.csv  (4 rows)

=== PRE-REGISTERED TESTS (spec v4 §4.1-§4.5) ===
  L1 chance                            macro_AUROC              +0.5473  ref=0.4994  CI=[0.4992,0.5971]  p=0.018  p_holm=None  PASS=True
  L2 anatomical prior                  AUROC - AUROC_prior      -0.1914  ref=0.7387  CI=[-0.2618,-0.1182]  p=1.0  p_holm=1.0  PASS=False
  L3 matched vs swapped                mean(matched - swapped)  -0.0017  ref=-0.0006  CI=[None,None]  p=0.5335  p_holm=1.0  PASS=False
  D7 subject-constant (as registered)  AUROC - AUROC_ctrl       -0.0754  ref=0.6228  CI=[None,None]  p=None  p_holm=None  PASS=False

  per-subject T (descriptive):
    chb03  n=4   T=+0.0096
    chb13  n=11  T=-0.0300
    chb14  n=8   T=+0.0465
    chb15  n=20  T=-0.0007
    chb16  n=10  T=-0.0086
    chb17  n=3   T=-0.0603
    chb18  n=6   T=+0.0156

  generalized seizures (no channel metric): 14 {'chb03': 3, 'chb06': 10, 'chb13': 1}

Read the verdict with ATTRIBUTION_SPEC v4 §4.7. Nothing here may be tuned (A4.9).
```

Elapsed 70 s.
