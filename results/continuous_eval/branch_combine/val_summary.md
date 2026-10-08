# Branch combination on the continuous timeline -- VALIDATION only

Variants fixed in advance; no test patient used. Gate passed (equal-weight recomputation reproduces the cached Scope T score).

    variant  window_auroc_all  a8_mag  a8_pen  a8_merge  a8_tp  a8_sens  a8_fa_day  fixed_tp  fixed_sens  fixed_fa_day
      equal             0.816  75.000   5.000       300      5    0.333     24.991        11       0.733        96.518
 w_10_45_45             0.834  60.000  10.000       300      7    0.467     21.329        11       0.733        98.457
   no_recon             0.835  80.000   5.000       300      6    0.400     21.113        11       0.733        92.425
    median3             0.738  55.000  10.000       300      5    0.333     20.252         9       0.600        92.856
min_lat_gam             0.726  55.000  10.000       300      3    0.200     19.174         7       0.467        84.022

A8 rule: highest pooled validation sensitivity with pooled FA/day <= 25 (ties: lower FA/day, lower penalty). n_ref is small (13 seizures): a difference of one or two matched events is within noise.