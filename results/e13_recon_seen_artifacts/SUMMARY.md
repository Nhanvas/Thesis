# E13 -- does training on artifacts make the recon readout discriminative? (cache only)

Median over subjects of the seed-mean values.

```
set    variant branch  AUC sz-flag  AUC sz-clean  tail flagged  exceed all|no-flag
train  clean   r             0.534         0.750          0.89  0.264|0.001
train  clean   l             0.946         0.985          0.84  0.006|0.000
train  all     r             0.521         0.710          0.88  0.285|0.002
train  all     l             0.936         0.980          0.85  0.010|0.000
val    clean   r             0.343         0.583          0.87  0.619|0.012
val    clean   l             0.970         0.987          0.88  0.001|0.000
val    all     r             0.324         0.537          0.84  0.658|0.016
val    all     l             0.965         0.983          0.82  0.001|0.000
```

## Recon, seizure-vs-flagged AUROC, all - clean, per subject (seed mean)

```
chb01 (train)  clean 0.670  all 0.688  delta +0.017
chb02 (train)  clean 0.533  all 0.524  delta -0.010
chb04 (train)  clean 0.321  all 0.331  delta +0.010
chb05 (train)  clean 0.529  all 0.502  delta -0.027
chb07 (train)  clean 0.417  all 0.410  delta -0.007
chb08 (train)  clean 0.775  all 0.769  delta -0.007
chb09 (train)  clean 0.536  all 0.519  delta -0.016
chb10 (val  )  clean 0.267  all 0.260  delta -0.006
chb11 (val  )  clean 0.734  all 0.728  delta -0.006
chb12 (train)  clean 0.376  all 0.396  delta +0.020
chb19 (train)  clean 0.500  all 0.442  delta -0.058
chb20 (train)  clean 0.946  all 0.943  delta -0.003
chb21 (train)  clean 0.621  all 0.623  delta +0.001
chb22 (val  )  clean 0.343  all 0.324  delta -0.019
chb23 (train)  clean 0.535  all 0.523  delta -0.012
```

Decision rule (12 training subjects): median delta -0.007, positive in 4/12 -> **B** (adaptation not supported; next lever = spatial-recruitment readout)

Elapsed 19 s.