Three items. The first cancels an earlier instruction of mine.

1. fig3_9 — you were right to refuse. The band is correct as drawn. My 0.0338 was not
   fabricated but I gave it without a source, and 0.0345 in the document was my own error:
   the true sample SD over 0.4783, 0.5306, 0.4898, 0.4490 is 0.033806. Both documents are
   now corrected. A band drawn at 0.034 is that value rounded, so leave the figure alone.
   Add one line to the caption: directed connectivity sits at -0.0339, on the boundary.

2. Every figure from now on is PNG only. Stop writing PDF. Delete the .pdf files already
   under figures/ and remove the PDF output from the scripts, so there is one file per
   exhibit and no chance of the two drifting apart.

3. src/dataprep/plot_raw_vs_preprocessed.py is broken: it calls find_eventful_segment at
   line 227 and that function does not exist in the file. Fix it or replace the call, then
   regenerate figures/raw_vs_preprocessed.png. Nothing about the preprocessing itself
   changes; this figure is illustrative.

Also, fig3_7's title still names the operating point twice, once inside a nested
parenthesis. State it once.