# Ictal vs flagged windows -- training patients chb12, chb08, chb20, chb05

## Windows per group

group    background  buffer  flagged  ictal
subject                                    
chb05         18681    2204    14074    143
chb08          7549    1014     9208    234
chb12          7460    5148     5738    271
chb20         11854    3051     9853     81

Share of ictal windows that the +-5 SD peak rule would flag: 0.752 (per subject: chb05 0.99, chb08 0.97, chb12 0.43, chb20 0.80)

## AUROC, ictal (positive) vs flagged non-ictal windows. 0.5 = no separation; 'sign ok' = same side of 0.5 in every subject

| feature | chb12 | chb08 | chb20 | chb05 | pooled | sign ok | pooled vs background |
|---|---|---|---|---|---|---|---|
| crest_max | 0.220 | 0.226 | 0.284 | 0.362 | 0.258 | yes | 0.524 |
| crest_med | 0.277 | 0.164 | 0.334 | 0.622 | 0.333 | no | 0.543 |
| kurt_max | 0.159 | 0.209 | 0.231 | 0.311 | 0.224 | yes | 0.491 |
| kurt_med | 0.232 | 0.180 | 0.370 | 0.546 | 0.306 | no | 0.502 |
| mob_med | 0.507 | 0.351 | 0.397 | 0.751 | 0.517 | no | 0.570 |
| cx_med | 0.387 | 0.769 | 0.659 | 0.106 | 0.457 | no | 0.466 |
| sent_med | 0.631 | 0.214 | 0.339 | 0.847 | 0.529 | no | 0.521 |
| frac_rms2 | 0.439 | 0.869 | 0.726 | 0.958 | 0.719 | no | 0.802 |
| rms_med_sd | 0.371 | 0.907 | 0.710 | 0.951 | 0.692 | no | 0.864 |
| coh_mean | 0.367 | 0.515 | 0.661 | 0.551 | 0.493 | no | 0.547 |

## Leave-one-subject-out logistic regression on all 10 features (diagnostic upper bound for a supervised combination; any rule would do no better)

| held-out subject | AUROC ictal vs flagged | AUROC ictal vs flagged+background |
|---|---|---|
| chb12 | 0.602 | 0.676 |
| chb08 | 0.814 | 0.771 |
| chb20 | 0.689 | 0.557 |
| chb05 | 0.924 | 0.931 |

Mean LOSO AUROC ictal vs flagged: 0.758.

Pre-set reading: a usable veto needs LOSO AUROC >= 0.80 AND at least one single feature with pooled AUROC >= 0.75 or <= 0.25 and 'sign ok' = yes. Otherwise the artifact-filtering lever is closed with this evidence. No threshold is derived here.