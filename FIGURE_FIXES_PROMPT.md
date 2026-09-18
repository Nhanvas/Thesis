Fix presentation defects in six report figures. Figures only: no number, no computation, no
pipeline change.

RULES
- First: `git add -A && git commit -m "pre figure-fixes" && git tag pre-figure-fixes`.
- Figures read committed results; they never recompute. Do not touch any file under results/ or data/.
- Edit only the generators in src/figures/ that produce the files below, plus tables/CAPTIONS.md.
  Find each generator with `grep -rn "<png name>" src/figures/`, and open it before editing.
- Keep every existing numeric self-check. Save every edited figure at dpi=300.
- Rerun only these generators. Afterwards `ls figures/*.png | wc -l` must print 21. If it does not,
  a generator has escaped; stop and report.

FIXES
1. fig1_2_connectivity_heatmaps.png: the colorbar label is clipped at the right edge. Make it fully
   visible (bbox_inches="tight" or a shorter label on two lines).
2. fig2_2_raw_vs_preprocessed.png: the y-axis label of panel (c) is clipped at the left edge. Make it
   fully visible.
3. fig2_3_graph_construction.png: the panel (c) colorbar has no label. Add
   "Combined wPLI + AEC weight".
4. fig3_3_detection_output.png: the y-axis labels of panels 2 and 3 overlap. Use shorter labels, each
   on two lines if needed ("Reconstruction\nerror (z)", "Latent\ndistance (z)", "Gamma-band\ncoupling (z)",
   "Fused\nscore"), and align them with fig.align_ylabels().
5. fig3_4_detection_latency.png: the "+60 s after seizure end" line is drawn at x=+60, but the x axis
   is latency from ONSET, so the line is misplaced.
   - Remove that line and keep the -30 s pre-onset line.
   - Add "n = <matched seizures>" to the legend.
   - Assert that n equals TP at the reported operating point read from the committed results (expected
     47, from fig3_5: TP/FN/FP = 47/29/318). If it differs, do NOT force it: stop and report both values
     and where each comes from.
6. fig3_5_operating_curve.png: rename the legend entry "Dominated grid points (mag% x pen)" to
   "Other grid points (magnitude × penalty)". Raise dpi to 300.

CAPTIONS (tables/CAPTIONS.md), replace these two entries verbatim:
- Figure 3.4: "**Figure 3.4.** Detection latency relative to annotated onset for every matched seizure,
  with the pre-onset matching tolerance marked. The post-offset tolerance is measured from seizure end
  and cannot be drawn on this axis."
- Figure 3.9: "**Figure 3.9.** Per-seizure channel ranking by reconstruction anomaly, one row per
  annotated seizure of the eight test patients; rank 1 is the most anomalous channel within that
  seizure. Seizure intervals come from the corpus annotations; no channel-level annotation is used."

ALSO REPORT (read-only, no edit)
- The exact number of retained edges per window graph after top-20 % sparsification, read from
  src/dataprep/graph_construction.py (show the line). For 153 pairs, is it 30, 31, or counted on
  directed entries? The answer goes onto a hand-drawn figure.

FINISH
- Show a before/after table: file, change made, and self-check result.
- Commit with message "figure fixes: clipping, 3.4 tolerance line, 3.5 legend, captions 3.4/3.9".
- Do not tag; the author will review first.