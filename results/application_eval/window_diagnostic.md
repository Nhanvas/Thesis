# Window-level discrimination and alignment of application scores

Diagnosis only -- nothing tuned, nothing re-scored, the application was not re-run (`CC_PROMPT_APP_WINDOW_DIAG.md`). Offline AUROC (report Table 3.1) is printed for comparison only, without comment.

| Subject | n_windows | n_ictal_windows | AUROC (app) | AUPRC (app) | best shift k | AUROC at best shift | AUROC (offline) |
|---|---|---|---|---|---|---|---|
| chb03 | 34201 | 106 | 0.774 | 0.007 | +10 | 0.845 | 0.964 |
| chb06 | 60060 | 45 | 0.389 | 0.001 | +15 | 0.709 | 0.501 |
| chb13 | 29700 | 144 | 0.632 | 0.007 | +5 | 0.648 | 0.822 |
| chb14 | 23400 | 49 | 0.635 | 0.005 | +0 | 0.635 | 0.698 |
| chb15 | 36008 | 515 | 0.715 | 0.025 | +1 | 0.718 | 0.879 |
| chb16 | 17100 | 28 | 0.572 | 0.002 | +10 | 0.576 | 0.876 |
| chb17 | 18906 | 74 | 0.575 | 0.004 | +15 | 0.663 | 0.782 |
| chb18 | 32070 | 83 | 0.770 | 0.007 | +1 | 0.780 | 0.920 |
| **macro** | | | **0.633** | | | | **0.805** |

**Alignment flag:** best shift is not in {-1, 0, +1} for: chb03, chb06, chb13, chb16, chb17.

Total computation time: 3.82 s.
