# Archived figures

Figures removed from the report's exhibit set. **Archived, not deleted.** A cut is an editorial
decision about the report, not a defect in the figure: every one of these was built from committed
data, passed its numeric self-check, and remains correct.

Their generating scripts were deliberately left untouched. Re-running a generator puts its figure
back at the root of `figures/`, which is the intended behaviour if a cut is reversed.

## Cut in round 10

The exhibit set was reduced from 69 to 51 after comparison against the two reference theses, which
carry 27 and 43 exhibits respectively. Every cut falls into one of three categories: a figure that
plots a table printed beside it, an exhibit whose content is already stated in the prose in numbers,
or two exhibits doing one job. No cut removed evidence, and every mandatory caption sentence survives
on an exhibit that stays.

| File | Was | Reason |
|---|---|---|
| `fig2_2_seizure_durations.png` | Figure 2.2 | Table 2.2 gives the minimum, median, mean and maximum, and the prose gives the count below 20 s. A histogram of four tabulated numbers. |
| `fig2_5_sparsification_rules.png` | Figure 2.5 | Panel (d) of Figure 2.4 already shows the sparse graph and Table 2.6 carries the comparison. Two figures and a table for one decision. |
| `fig2_9_weight_simplex.png` | Figure 2.9 | It is a measurement, and Chapter 2 reports no measurement. Its four values are stated in Chapter 3. |
| `fig2_10_changepoint_detection.png` | Figure 2.10 | Figure 3.4 shows the same recording with more context. Two figures of chb13_62. |
| `fig3_2_score_distributions.png` | Figure 3.2 | Three exhibits for one window-level result. Table 3.2 gives the numbers and Figure 3.3 gives the shape. |
| `fig3_7_persubject_event.png` | Figure 3.7 | Plots Table 3.4 row for row. |
| `fig3_9_alternatives_effect.png` | Figure 3.9 | Plots the delta-F1 column of Table 3.6 against a band the table states in its own text. |
| `fig3_12_attribution_seed_stability.png` | Figure 3.12 | Two numbers, both stated in the prose. |
| `fig3_14_attribution_persubject_forest.png` | Figure 3.14 | Table 3.9 carries the panels and the per-patient values are named in the prose. |

Source of the decision: `docs/EXHIBIT_TRIAGE.md`.

## Earlier

Six files predating round 10, superseded rather than cut: three under `window_level/`, two under
`event_level/`, and one superseded version of the preprocessing comparison. They were built from an
earlier configuration or replaced by a corrected version, and must not be cited.
