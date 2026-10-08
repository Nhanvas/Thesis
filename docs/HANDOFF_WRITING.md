# HANDOFF — report writing session (from the 2026-10-08 sync chat)

Read this first, then `docs/HANDOFF_REPORT.md` (what the report says) and `docs/PERF_PHASE_RECORD.md`
sections 3, 9.8, 9.9, 10 (every number). The project instructions apply in full; this file only adds the
state and the plan of the writing session.

## 0 · Working rules the author set in this chat (binding)

- **Never write or delete project files.** End every deliverable with ONE list: add / replace / delete,
  with the local path of each file. The author updates the 8 Claude projects by hand.
- **One thing at a time.** Finish a step, give one consolidated result, then the next step. No scattered
  small deliverables, no parallel workstreams (Project 2 / web demo waits until the chapters are done).
- **Say where every file is saved** — e.g. "download this file into `F:\Study\Thesis\Agent\<task>\`" —
  before any command that reads it. Downloads land in the browser folder unless told otherwise.
- Commands: `bash -e <<'EOF' … EOF`, short, one purpose each, dry run before writing, explicit `git add`
  paths. State the expected runtime. Tell the author exactly what output to look for.
- Converse in Vietnamese; files in English; whole files with exact target paths.

## 1 · State at hand-off (2026-10-08 evening)

Done and committed:
- Project sync for the report phase (record rev R, HANDOFF_REPORT rev 2, PROJECT_STATUS rev G).
- Attribution of the final system (A5) — HANDOFF_REPORT section 3.
- Exhibit set v5 approved (`EXHIBIT_SET_v5.md`: 13 figures, 16 tables). Figures still to redraw because they
  show the earlier pipeline or its data: Fig 2 (framework), Fig 6 (pipeline), Fig 11 (app screens),
  Fig 12 (literature plot); Fig 8 (app architecture) to edit after the demo rebuild. Fig 1, 3, 4, 5, 9 are
  unchanged (montage, preprocessing and graph construction did not change). Two export scripts are still
  needed before drawing: Fig 7 (drift example, one non-test patient, seed 42) and Fig 10 (chb03, seed 42,
  frozen code path).
- **Reference sheet rev 2026-10-08** (`Thesis_Reference_Sheet.md`, 108 entries): new groups K (Siena,
  benchmark repo, DynaSD/NDD, epilepsy2bids, SzCORE preprint), L (Ledoit–Wolf, kernel CPD, ruptures, MAD,
  bootstrap, Mahalanobis), M (comparison papers); flags 6–10. Benchmark evidence: `docs/BENCHMARK_CHECK_szcore_c57da2f.md`.
  Commit "Reference verification 2026-10-08" (script `src/refs_sync_1008.py`).
- Corrections recorded (`VERIFIED_CORRECTIONS.md` 15): SeizureTransformer trained on Siena; DynaSD tuned on
  CHB-MIT and its paper has no CHB-MIT/Siena numbers; the RF/XGBoost CHB-MIT rows are the SzCORE arXiv
  Table 2; Ingolfsson's 22.9 → 1.0 FP/h is TUAR data; Ali et al. 2024 verified as supervised LOSO.

Open items the chapters must handle:
1. **Siena hours:** PhysioNet "about 128 recording hours" vs ~140 h in our X1 summary (sheet flag 10).
   Check `results/x1_external/` before writing Section 2 data; describe the dataset with PhysioNet's
   figure and our scored hours as our measurement, or reconcile.
2. **Application tier (Table 14, Fig 8, Fig 11)** waits for the demo rebuild. Fallback (HANDOFF_REPORT
   section 0): if not done by 12/10, the report describes the application as running the earlier system.
3. Ali et al. 2024 is usable as the supervised patient-independent comparator only with its protocol note
   (sheet U-F2).

## 2 · Plan approved by the author (2026-10-08)

**Step A — distil the writing inputs (first thing in the new chat).** The author sends: two high-scoring
sample reports (VBPH, Tri), the detailed reviewer feedback of his earlier CHB-MIT epilepsy paper, the
grading rubric, and his own requirements. Do NOT read them into the main context. Hand them to sub-agents
(Agent tool), which return only:
- `REVIEWER_RULES.md` (≤ 2 pages): each reviewer point as a checkable rule, tagged by chapter. A point
  that contradicts this project's verified facts or decisions is marked **CONFLICT** with the reason, never
  applied silently (the paper differs from this thesis).
- `SAMPLE_PATTERNS.md` (≤ 2 pages): chapter structure, section names, pages per chapter, number of figures
  and tables, how results, limitations and comparisons are presented in the two samples.
- `RUBRIC_MAP.md` (≤ 1 page): each rubric criterion → where the report meets it.
The author approves the three files before any chapter is written. They are the per-chapter checklist,
and the final review pass after assembly.

**Step B — numbers pack.** Before writing, the author runs the command in section 4 and uploads
`report_numbers.zip`. Every number in a chapter is read from these files (or the record); a computed value
is labelled computed. A sub-agent may cross-check each finished chapter's numbers against the pack (the
`xanh` role) — numbers only, fixed return format.

**Step C — chapters, in this order:** Chapter 2 → 3 → 4 → 1 → 5 → front matter (abstract, keywords,
lists). Base text: `Chapter_*_v4.md` / `Front_matter_v4.md` (the author confirmed these are the latest in
`F:\Study\Thesis\Reports\`). New files: `F:\Study\Thesis\Reports\Chapter_N_..._v5.md`. Content changes per
chapter (approved):

| Ch. | Add | Remove or shorten |
|---|---|---|
| 2 | 7 amplitude-preserving node features (input 30); per-patient per-channel Ledoit–Wolf Mahalanobis latent anomaly + robust z; ±15-min per-file drift correction; ensemble of order statistics 6/9/12 + mean via patient percentiles; per-patient alarm budget; kernel CPD as onset/offset localizer; chb24 and Siena; settings table (what is fitted where); one paragraph on the earlier offline protocol (HANDOFF_REPORT section 4) | reconstruction and gamma-AEC readouts, PELT as detector (one sentence in the design comparison only) |
| 3 | component contribution (non-test); clean and test-informed test results side by side with bootstrap; per-patient table; onset/offset error; external validation with the benchmark rows; attribution, two readouts | offline results, earlier ablations, the old app-gap diagnosis |
| 4 | DynaSD on the same Siena data; Ali 2024 with protocol note; protocol rows (M1–M3) only beside the full result; why chb06, chb13, chb16 fail | discussion of the earlier system |
| 1, 5 | rewritten for the final system and results | |

**Step D — figures/tables** from committed results (rule 13), then checks (Grammarly, rubric, review
pass with `REVIEWER_RULES.md`, page count by building the document), then slides.

**Page limit.** `Report format.md`: "The full thesis should not exceed 50 pages (excluding list of tables,
list of figures, appendices and references)". The rule stands even if samples are longer. v4 measured 49
body pages (Ch1 9, Ch2 15, Ch3 15, Ch4 8, Ch5 2): new content replaces old, it is not added. Target ≤ 48.

**After the chapters:** Project 2 (web demo rebuild on the final system with Claude Code,
`docs/DEMO_REBUILD_BRIEF.md`); the author will send that project's knowledge files.

## 3 · Report wording reminders (details: HANDOFF_REPORT section 6, PROSE_STYLE_SPEC)

No stage/look/experiment/tag names, no repo paths, no internal labels. Look #6 = "the held-out evaluation",
look #7 = "the final system, whose last design choice used information from the test set". Headline seed 42
with 4-seed mean ± SD and patient bootstrap; pooled and subject-mean side by side. DynaSD = "label-free
detector with a threshold tuned on labelled intracranial recordings". Benchmark numbers cite the
repository (sheet K3), never the DynaSD paper.

## 4 · Numbers pack command (run once at the start of the writing session; a few seconds)

```bash
bash -e <<'EOF'
cd /f/Study/Thesis/Code
OUT=/f/Study/Thesis/Agent/report_numbers; rm -rf "$OUT"; mkdir -p "$OUT/results"
for d in results/p3c_freeze results/e22_test_oneshot results/e23_test_look7 results/x1_external \
         results/attribution_v8 results/attribution_v7 results/continuous_eval results/p3_anatomy \
         results/e18_cpd_localizer results/e17b_latent_family results/e21_fine_grid results/e8_gae_v2 \
         results/e9_test_oneshot; do
  if [ -d "$d" ]; then
    find "$d" -maxdepth 2 -type f \( -name '*.md' -o -name '*.csv' -o -name '*.json' \) -size -2M \
         -not -path '*/labels/*' -not -path '*/cache/*' | while read -r f; do
      mkdir -p "$OUT/$(dirname "$f")"; cp "$f" "$OUT/$f"; done
  else echo "absent: $d"; fi
done
cp results/p2_ledger.csv "$OUT/results/" 2>/dev/null || echo "absent: results/p2_ledger.csv"
{ git rev-parse --short HEAD; git describe --tags --always; } > "$OUT/GIT_HEAD.txt"
( cd "$OUT" && find . -type f ! -name MANIFEST.txt | sort | xargs -d '\n' sha256sum > MANIFEST.txt )
python -c "import shutil; shutil.make_archive('F:/Study/Thesis/Agent/report_numbers','zip','F:/Study/Thesis/Agent/report_numbers')"
ls -la /f/Study/Thesis/Agent/report_numbers.zip; wc -l < "$OUT/MANIFEST.txt"
EOF
```

Expected: a few `absent:` lines are fine (a folder may not exist under that name); the last two lines show
the zip size and the number of files. Upload `F:\Study\Thesis\Agent\report_numbers.zip` to the new chat.
If a needed result is missing from the pack, ask for it with one `ls` command before writing.
