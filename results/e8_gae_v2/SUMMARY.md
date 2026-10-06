# E8 -- GAE v2 (option C) on full recordings, 15 non-test subjects

V1 (locked): best sens FA/day<=25 = 0.330 {'kind': 'V1', 'smooth': 15, 'top': 0.02, 'fa_day': 23.67, 'sens_sd': np.float64(nan), 'n_seeds': 1}; validation-only 0.467
  clean V2_LW: 0.489 {'kind': 'V2_LW', 'smooth': 15, 'top': 0.02, 'fa_day': 19.78, 'sens_sd': np.float64(0.030089650263257307), 'n_seeds': 2}  (FA/day<=15: 0.378)
  clean V2_GMM: 0.484 {'kind': 'V2_GMM', 'smooth': 15, 'top': 0.02, 'fa_day': 23.85, 'sens_sd': np.float64(0.007522412565814307), 'n_seeds': 2}  (FA/day<=15: 0.372)
clean: best 0.489 {'kind': 'V2_LW', 'smooth': 15, 'top': 0.02, 'fa_day': 19.78, 'sens_sd': np.float64(0.030089650263257307), 'n_seeds': 2}; validation-only 0.733
  all V2_LW: 0.468 {'kind': 'V2_LW', 'smooth': 15, 'top': 0.02, 'fa_day': 20.69, 'sens_sd': np.float64(0.06017930052651467), 'n_seeds': 2}  (FA/day<=15: 0.367)
  all V2_GMM: 0.495 {'kind': 'V2_GMM', 'smooth': 15, 'top': 0.02, 'fa_day': 23.6, 'sens_sd': np.float64(0.007522412565814366), 'n_seeds': 2}  (FA/day<=15: 0.356)
all: best 0.495 {'kind': 'V2_GMM', 'smooth': 15, 'top': 0.02, 'fa_day': 23.6, 'sens_sd': np.float64(0.007522412565814366), 'n_seeds': 2}; validation-only 0.700

- Rule V: chosen variant = clean
- Rule C: 0.489 vs V1 0.330 + 0.10; validation-only 0.733 vs 0.467 -> ADOPTED

**FROZEN for the one-shot test: GAE v2 clean, score V2_LW, smooth 15, top 0.02**

Short seizures (< 20 s) in this set: n_ref_short = 3