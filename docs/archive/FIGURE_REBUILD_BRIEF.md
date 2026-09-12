# Figure Rebuild Brief

For the session that rebuilds the detection figures. Run it against the repository, not in a
chat window: it needs to open files, run scripts, look at the output and iterate.

Authority: `docs/VERIFIED_NUMBERS.md` for every value, `FIGURES_TABLES_LIST.md` for what each
exhibit must contain. If this brief and either of those disagree, they win and this file is
wrong.

---

# Why this session exists

Five figures already in `figures/` were built from the **earlier configuration**, not the system
the report describes. They were checked on 2026-09-06 by opening them:

| File | Exhibit | Evidence it is the wrong system |
|---|---|---|
| `figures/event_level/E1_operating_curve.png` | Fig 3.6 | Marks the balanced point at 0.632 and 38.6 |
| `figures/event_level/E2_persubject_breakdown.png` | Fig 3.7 | Uses the earlier configuration's two cells |
| `figures/window_level/W1_roc_curves.png` | Fig 3.3 | Per-subject 0.954, 0.437, 0.805, 0.626, 0.826, 0.871, 0.747, 0.938; macro 0.775 |
| `figures/window_level/W2_pr_curves.png` | Fig 3.3 | Same script family |
| `figures/window_level/W3_score_distribution.png` | Fig 3.2 | Cannot be attributed from the image; no generating script exists |

The final system's per-subject values are 0.9643, 0.5011, 0.8223, 0.6982, 0.8785, 0.8763,
0.7815, 0.9201, for a macro of **0.805**. None of the values on the existing figure match.

If these go into the report unchanged, Chapter 3 will contain a table reading 0.618 at 27.4
false alarms per day beside a figure reading 0.632 at 38.6, and a macro of 0.805 beside a
figure showing 0.775. That is the failure the exhibit list's fourth rule exists to prevent:
*a figure must not be able to disagree with the table beside it.*

---

# Rules

1. **Every number is read from a committed file. None is typed in.** If a value has to be
   entered by hand for the figure to render, that is the signal that the wrong source is being
   used.
2. **The system is the final one.** Grids come from `results/phaseB/tier2/rlg_test/`; score
   arrays come from `results/phaseB/tier2/ens_test_tf/rlg/`. Anything under `baseline_rtg`,
   `ens_test_base`, `retrain_v3p1` or `history_superseded` is the earlier configuration or
   worse, and is out of scope.
3. **The headline operating point is m50 / p2.0**: sensitivity 0.618, precision 0.129,
   F1 0.213, 27.4 false alarms per day. Every figure that marks an operating point marks this
   one.
4. **No confidence intervals on detection figures.** That was decided; error bars would
   contradict the tables.
5. **Do not delete the old figures.** Move them to `figures/archive/` and write the new files
   under new names, so the two can be compared.
6. **Number formatting:** three decimals for discrimination, precision, sensitivity and F1;
   one decimal for false alarms per day.
7. **One shared palette** across all five: one colour for interictal, one for ictal, one for
   detected intervals. Chance level and noise bands are drawn, never implied.

---

# What to build

## Fig 3.2 — fused score distributions per patient
Violin or box per patient, interictal against ictal, eight panels.
Source: `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy`.
Window counts, for checking: chb03 17204/106 · chb06 19826/45 · chb13 12452/144 ·
chb14 13983/49 · chb15 17026/515 · chb16 6428/28 · chb17 9304/74 · chb18 14853/83.

## Fig 3.3 — per-patient discrimination curves
Two panels: receiver-operating on the left, precision-recall on the right.
**One curve per patient. No pooled curve, no macro-mean curve** — the existing figure has one
and the specification forbids it. The precision-recall panel is the point of the figure: it is
what makes the low seizure prevalence visible.
Same source as Fig 3.2. Each curve's discrimination value must reproduce
`results/phaseB/tier2/ens_test_tf/rlg/window_auroc_seed42.json` to four decimals. If it does
not, stop — the wrong arrays are being read.

## Fig 3.6 — sensitivity against false alarms per day
Step curve over the full 48-cell grid, dominated points de-emphasised, frontier connected.
Mark **two** points: the headline (m50/p2.0, 0.618 at 27.4) and the best point on the curve
(m80/p5.0, F1 0.426 at 4.9, sensitivity 0.474, precision 0.387).
Label the second one as the best achievable point on this curve, **not** as a result. It was
located after the held-out set had been scored, and the caption must say so.
Source: `results/phaseB/tier2/rlg_test/final_eval_seed42.csv`, pooled across subjects as
total true positives over total seizures, total false positives over total interictal days.
`src/figures/plot_event_level.py` can be adapted: it already takes a `--csv` argument, but its
`LOCKED_OPS` constant holds the earlier configuration's two cells and must be replaced.

## Fig 3.7 — event-level performance per patient
Grouped bars, one group per patient, at the headline point only. The existing figure shows two
operating points; one is enough, and the second was the earlier configuration's.
Source: the same grid file, rows at m50/p2.0.

## Fig 3.5 — detection latency
Histogram of `latency_s` from
`results/phaseB/tier2/latency/latency_per_seizure.csv`, rows where
`operating_point = val_derived_balanced` and `matched = True`. n = 48.
**Draw vertical lines at −30 s and +60 s.** These are the matching tolerance, and the
distribution is truncated exactly at −28 s because of them. That truncation is the whole point
of the figure: it is what shows the negative values come from the matching rule and not from
detection before onset. Median is −4 s; 25 of 48 are negative.

---

# Also worth building while the tooling is open

**Fig 2.8 — reconstruction error in two patients.** Two panels, interictal and ictal
distributions overlaid, one patient where the score behaves as expected and one where it
inverts. Use **chb11 and chb10**, both validation subjects: chb11's reconstruction
discrimination is 0.8517, chb10's is 0.2680, fully inverted. `data/pernode_v2/seed42/` holds
both. Do not use a held-out subject to illustrate a design decision in the methodology chapter.

**Fig 2.9 — ensemble weight surface.** Ternary heatmap over the 231 grid points in
`results/phaseB/tier2/weights_rlg/derive_weights_rlg_grid.csv`. Mark the best point
(0.10, 0.45, 0.45; 0.9405), the equal-weight point (0.9283, the last row of the file), and the
region within 0.005 of the best, which holds 29 points. The equal-weight point falls **outside**
that region — that is what the figure is for, and the caption says so plainly.

**Fig 3.1 — separation between ictal and interictal connectivity.** Bars per patient from
`results/diagnostics/density_frobenius_v2/separation_per_subject.csv`. Plot a **normalised**
column, `pct_change_rel_topk_vs_fixed` or `pct_change_cos_topk_vs_fixed`. Do **not** plot the
raw Frobenius column: the two rules produce matrices with different numbers of non-zero
entries, so the raw norm shrinks for arithmetic reasons and reverses the apparent direction.
The caption states which measure is plotted and why the raw one is not.

**Fig 3.9 — effect of each variant.** Horizontal dot plot of the difference in event-level F1,
from `results/phaseB/tier2/alternatives/alternatives_vs_incumbent.csv`. **Shade the band from
−0.034 to +0.034 around zero**: that is the spread across four independently trained models,
and every variant inside it is a tie, not a result. The reconstruction-removal variant sits at
+0.012, inside the band.

---

# Before finishing

For each rebuilt figure, print the values it plots and check them against
`docs/VERIFIED_NUMBERS.md`. A figure that cannot be reconciled with that document is not
finished, whatever it looks like.
