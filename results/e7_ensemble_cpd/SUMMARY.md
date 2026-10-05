# E7 -- 4-branch ensemble (B) and change-point segment detector (D2)

## Best pooled sensitivity at FA/day caps (15 non-test subjects, SzCORE)

```
score detector  sens_fa25  sens_fa15  sens_fa10
   G0       D1      0.479      0.287      0.202
   G0       D2      0.213      0.213      0.213
    F       D1      0.596      0.521      0.372
    F       D2      0.362      0.362      0.234
    B       D1      0.521      0.351      0.245
    B       D2      0.298      0.298      0.149
```

Cells at FA/day <= 25:

```
score detector                                                                               cell25
   G0       D1 {'detector': 'D1', 'param': 15.0, 'top': 0.02, 'tp': 45, 'fp': 234, 'fa_day': 24.49}
   G0       D2   {'detector': 'D2', 'param': 10.0, 'top': 0.05, 'tp': 20, 'fp': 66, 'fa_day': 6.91}
    F       D1 {'detector': 'D1', 'param': 15.0, 'top': 0.02, 'tp': 56, 'fp': 217, 'fa_day': 22.71}
    F       D2 {'detector': 'D2', 'param': 1.0, 'top': 0.005, 'tp': 34, 'fp': 138, 'fa_day': 14.44}
    B       D1 {'detector': 'D1', 'param': 15.0, 'top': 0.02, 'tp': 49, 'fp': 230, 'fa_day': 24.07}
    B       D2  {'detector': 'D2', 'param': 10.0, 'top': 0.05, 'tp': 28, 'fp': 96, 'fa_day': 10.05}
```

- R1: B 0.521 vs F 0.596 vs G0 0.479 -> B NOT adopted (F alone is better than B: report, supervisor decides)
- R2 on score G0: D1 0.479 vs D2 0.213 -> D1
- R2 on score F: D1 0.596 vs D2 0.362 -> D1
- R2 on score B: D1 0.521 vs D2 0.298 -> D1

**FROZEN for the one-shot test: NONE -- F alone beats B; supervisor decides between F and B before any test run**

## Per subject AUROC

```
         G0_sz_flag  G0_sz_bg  F_sz_flag  F_sz_bg  B_sz_flag  B_sz_bg
subject                                                              
chb01        0.5666    0.7600     0.6416   0.6839     0.6520   0.7985
chb02        0.6780    0.9441     0.8549   0.9279     0.7674   0.9721
chb04        0.2657    0.7990     0.8936   0.9354     0.5787   0.8830
chb05        0.5014    0.7662     0.7716   0.9369     0.5681   0.8795
chb07        0.6466    0.9120     0.8670   0.9609     0.8320   0.9793
chb08        0.6409    0.8751     0.4731   0.6748     0.6325   0.9236
chb09        0.6900    0.9484     0.9357   0.9961     0.8235   0.9928
chb12        0.3134    0.5766     0.6465   0.8012     0.4002   0.6976
chb19        0.7628    0.8561     0.9139   0.9498     0.8792   0.9387
chb20        0.7873    0.9499     0.7954   0.9379     0.8286   0.9786
chb21        0.5357    0.7487     0.6451   0.6332     0.6021   0.7639
chb23        0.8312    0.9794     0.7575   0.8939     0.8480   0.9888
chb10        0.5183    0.7846     0.8965   0.9843     0.7062   0.9470
chb11        0.6360    0.9473     0.9185   0.9773     0.7457   0.9802
chb22        0.7937    0.9643     0.9554   0.9848     0.8677   0.9869
```

Elapsed 7754 s.