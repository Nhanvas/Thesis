# A6_FIGURES — redraw the report's real-EEG figures in one simple style (Claude Code, laptop)

Context: final thesis report, chat A6 (17/11). The author approved one plain style for every real-EEG figure:
18 named derivations coloured by chain, the annotated seizure as a light band, the system's event as a bar, the
anomaly score below with the threshold, no titles or legends inside the figure. The drawing code is
`src/a6_figs/draw_eeg_figures.py` (plot only; it reads panel files in the format of
`src/figures_v8/export_v8_data.py`). Figures 9, 16b and 17a are already drawn from the committed panel files
`results/figures_v8_data/gallery/{a,b,c,d}.npz`. This task exports the missing panels and draws them.

## Rules
- Read-only reuse of the thesis code; change no result, no model, no frozen file. The events are the thesis
  system's own (seed 42, final system after the localizer), exactly the events of the selection rules below.
  If a rule gives a different event than the one listed, STOP and report — draw nothing for that figure.
- No hospital data in this task (Figure 10 keeps the two existing hospital images as they are).
- Do not commit `.npz` or images (EEG); commit only the new script and this prompt's report.
- Runtime: measure it and report it.

## Step 1 — write `src/a6_figs/export_a6_panels.py` (export only)
Reuse `src/v9_eeg_evidence.py` (`ctx_and_res_G`, `read_window`, `file_index`), `src/v9_final_figs.py` (its picks)
and `src/p3_levers.py::refs_of`. For each panel write `results/a6_figs_data/<key>.npz` with the keys of
`draw_eeg_figures.py`: `eeg` [18, n] float16 (filtered EEG of `read_window`, µV, 256 Hz or decimated to 128 Hz),
`fs`, `eeg_t0` (s in the file, page = anchor −10 s … +20 s), `ch` (montage order), `score_t`, `score`,
`score_sm` (the system's own score of that file over anchor ±300 s; if only one score series exists use it for
both), `thr` (the patient's final threshold), `thr_heldout` (NaN), `ann`, `det`, `loc` (seconds in the file; the
listed event first). Gate per panel: the listed annotated seizure and/or localized event must be present in the
system's own output for that file (times within 1 s).

| key | figure | event (rule source) |
|---|---|---|
| `f16a` | 16 (a) | chb06, chb06_18.edf, seizure onset 7796 s, 16 s, missed by the final system — the missed test seizure whose amplitude ratio is closest to the median of the 38 missed (`FIGURE_INDEX.md` item 2; `v9_final_figs.pick_missed_test`) |
| `f17b` | 17 (b) | chb14, chb14_29.edf, false alarm 1476 s, 32 s, peak score 0.9998 — the highest-peak false alarm of the patient whose false-alarm count is closest to the median (`FIGURE_INDEX.md` item 3; `v9_final_figs.pick_false_alarm`); `ann` empty |
| `f10a` | 10 (a) | chb24: the true detection whose onset error is closest to the median onset error of the chb24 detections, seed 42 (rule and gate of `Defense/slides/gen/d9c/d9c_eeg_figs.py::chb24`, 16 seizures / 14 detected) |
| `f10b` | 10 (b) | Siena PN09, PN09-2.edf, seizure onset 7124 s, 64 s, localized 7144–7196 s (`FIGURE_INDEX.md` item 4a; `v9_final_figs.pick_siena_detected_missed`) |
| `f12a`, `f12b` | 12 (a), (b) | the focal test seizures with the highest (chb15, seizure 2, AUROC 0.969) and lowest (chb16, seizure 7, AUROC 0.214) channel-ranking AUROC, seed 42 (`Defense/slides/figs/eeg_evidence/part6/selection.csv` and the script that drew `focal_match_chb15_s2_full18.png`). Extra keys: `ch_mark` bool[18] = channels in the blind annotation of that seizure; `ch_top` bool[18] = the same number of channels ranked highest by the model's channel-level anomaly (as in the part6 figure). Read the annotation and the ranking from the files that script used |
| `f18` | 18 | chb15, chb15_40.edf, seizure onset 3362 s, 63 s — the seizure closest to the median share of power removed by ASR (`FIGURE_INDEX.md` item 8a; `src/v9_x6_asr.py --item8`, asrpy 0.0.8, cutoff 20, per-file calibration). `eeg` = the 18 filtered derivations before ASR, `eeg_after` = the same page after ASR, exactly as `--item8` computes them; `ann` = the seizure; score keys may hold the file's score (not drawn) |

## Step 2 — draw
Output folder `F:/Study/Thesis/Reports/A6_figures/`:
```
python src/a6_figs/draw_eeg_figures.py --fig 9   --panels results/figures_v8_data/gallery/a.npz results/figures_v8_data/gallery/b.npz --out <out>
python src/a6_figs/draw_eeg_figures.py --fig 10  --panels results/a6_figs_data/f10a.npz results/a6_figs_data/f10b.npz --out <out>
python src/a6_figs/draw_eeg_figures.py --fig 12  --panels results/a6_figs_data/f12a.npz results/a6_figs_data/f12b.npz --out <out>
python src/a6_figs/draw_eeg_figures.py --fig 16  --panels results/a6_figs_data/f16a.npz results/figures_v8_data/gallery/c.npz --out <out>
python src/a6_figs/draw_eeg_figures.py --fig 17  --panels results/figures_v8_data/gallery/d.npz results/a6_figs_data/f17b.npz --out <out>
python src/a6_figs/draw_eeg_figures.py --fig 18  --panels results/a6_figs_data/f18.npz --out <out>
```

## Step 3 — report and commit
Write `Agent/inbox/A6_FIGURES_REPORT.md`: for each figure the event drawn (subject, file, onset, duration,
event times), the gate result, runtime. Commit only `src/a6_figs/export_a6_panels.py`,
`src/a6_figs/draw_eeg_figures.py` and `docs/prompts/A6_FIGURES.md` (`git add` explicit paths; message
"A6: report EEG figures in one style (export + draw)"), push `main`.
