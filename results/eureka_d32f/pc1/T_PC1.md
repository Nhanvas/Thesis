# Table T_PC1 — retraining ablations (feature effect)

Per-patient means after the change point localizer, 4 seeds, own label-free point. Paired patient bootstrap (chb01 + chb21 one unit). Development = primary; test, chb24, Siena descriptive. R0 = the GAE retrained here with the full input (same recipe and platform as 10a / 10b).

| comparison | set | Δ sensitivity | Δ F1 | Δ FP/day |
|---|---|---|---|---|
| 10a - R0 (feature effect) | development | -0.277 [-0.393, -0.163] | -0.159 [-0.250, -0.095] | +26.2 [+20.7, +32.4] |
| 10b - R0 (feature effect) | development | +0.012 [-0.006, +0.033] | +0.009 [+0.002, +0.016] | -1.5 [-2.3, -0.6] |
| R0 - V0 (retraining on CPU) | development | -0.042 [-0.074, -0.013] | -0.006 [-0.019, +0.014] | +0.5 [-0.8, +1.9] |
| 10a - R0 (feature effect) | test | -0.160 [-0.398, +0.032] | -0.092 [-0.135, -0.047] | +24.9 [+18.3, +31.8] |
| 10b - R0 (feature effect) | test | +0.018 [-0.038, +0.079] | +0.015 [-0.013, +0.048] | -2.3 [-4.1, -0.1] |
| R0 - V0 (retraining on CPU) | test | -0.073 [-0.122, -0.024] | -0.027 [-0.049, -0.007] | +1.3 [+0.2, +2.4] |
| 10a - R0 (feature effect) | chb24 | -0.594 | -0.385 | +19.3 |
| 10b - R0 (feature effect) | chb24 | -0.125 | -0.005 | -6.5 |
| R0 - V0 (retraining on CPU) | chb24 | -0.016 | +0.011 | -2.0 |
| 10a - R0 (feature effect) | siena | -0.102 [-0.276, +0.050] | -0.099 [-0.146, -0.053] | +27.2 [+20.6, +33.5] |
| 10b - R0 (feature effect) | siena | -0.097 [-0.259, +0.020] | -0.014 [-0.057, +0.023] | -0.3 [-3.1, +2.6] |
| R0 - V0 (retraining on CPU) | siena | +0.026 [-0.052, +0.123] | -0.003 [-0.033, +0.025] | -1.4 [-4.0, +1.3] |
