# RB1B — why chb12's z-score statistics changed in RB1 (Claude Code, laptop; Track F, chat D23-F)

**Estimated runtime: 5–15 min (computed estimate, not measured)** — the 24 chb12 EDF files (≈ 24 h of EEG) are read
three times: the statistics loop for 21 and for 24 files (≈ 1,350 sampled 4 s windows each), the whole-file filter for
the flags, the raw samples for clipping. Memory ≈ 2 GB.

**What and why (do not interpret results; the chat does that).** RB1 rebuilt chb12 with chb12_27–29 on Kaggle; every
gate passed, but chb12's per-channel SD (the z-score statistic) rose by +0.6 … +24.6 %, so 706 windows of the earlier
21 files lost their artifact flag. The committed script `src/r2_rb1b.py` measures where that change comes from: it
re-runs the record's statistics loop (`preprocessing.compute_subject_stats`) on 21 and on 24 files with the conversion
wrapper installed, keeps the sums of every sampled window, and recomputes the statistic for subsets. Gates: inputs =
PhysioNet (G-in), the replicated statistic = RB1's (G-stats), the flag counts = RB1's (G-flags), clipping = RB0b's
(G-clip). Plan: `docs/FUTURE_RESEARCH_PLAN.md` §12 row 13/11 08:35.

## Ground rules

1. Change no file under `src/`, `data/`, `results/` except the new output folder `results/r2/r0_data/chb12_ref/rb1b/`.
   Do not edit the script; if it fails, stop and report (rule 5).
2. Install nothing. The script needs only what RB0b already used (numpy, scipy, pandas, mne, and the repository's own
   modules, which import torch); it does **not** need `pyedflib` or the SzCORE clone.
3. Nothing temporary is created outside the output folder.
4. Stage explicit paths only; never `git add .` or a parent directory.
5. On any `STOP RB1b` / traceback: do not retry with changes, do not work around it. Keep whatever the output folder
   holds, still commit and push it (it is evidence), and write the error in the report.

## Steps (Git Bash, from `F:/Study/Thesis/Code`)

**0 — repository.**
```bash
cd F:/Study/Thesis/Code
git pull
git log -1 --oneline
ls src/r2_rb.py src/r2_rb1b.py docs/prompts/RB1B_PROMPT.md results/r2/r0_data/chb12_ref/rb1/stats/chb12_stats.json
```
All four files must exist. Note the commit hash for the report.

**1 — environment.**
```bash
python -c "import sys, numpy, scipy, pandas, mne, torch; print(sys.version.split()[0], numpy.__version__, scipy.__version__, pandas.__version__, mne.__version__, torch.__version__)"
```

**2 — run** (the CHB-MIT folder is the default `F:/Study/Thesis/Dataset/CHB-MIT`):
```bash
mkdir -p results/r2/r0_data/chb12_ref/rb1b
python src/r2_rb1b.py 2>&1 | tee results/r2/r0_data/chb12_ref/rb1b/run.log
```
Expected log, in order: `G-in: PASS`, `sampled windows: A …, B …`, `G-stats: {'status': 'PASS', …}`,
`G-clip: PASS`, `G-flags: {'status': 'PASS', …}`, `END {"G-in": "PASS", …}`. Do not judge the values.

**3 — check the output folder** `results/r2/r0_data/chb12_ref/rb1b/`. It must hold: `rb1b.json`, `SUMMARY.md`,
`scenarios.csv`, `contributions.csv`, `sampled_windows.csv.gz`, `unflagged_windows.csv`, `run.log`. List the files with
their sizes. No EDF, no `.npz`, nothing over 20 MB (if a file is larger, do not commit it; say so in the report).

**4 — commit and push** (explicit path only):
```bash
git add results/r2/r0_data/chb12_ref/rb1b
git status --short
git commit -m "RB1b: why chb12's z-score statistics changed (D23-F)"
git push
```
`git status --short` must list only paths under `results/r2/r0_data/chb12_ref/rb1b/` as staged (pre-existing `??`
lines: leave them). Note the new commit hash.

**5 — report** `F:/Study/Thesis/Agent/inbox/RB1B_REPORT.md` (facts only, no interpretation):
- the commit hash of step 0 and of step 4;
- measured runtime (`runtime_s` in `rb1b.json`) and the wall time of the Python process;
- the environment line of step 1;
- the gates (`gates` in `rb1b.json`);
- the full text of `SUMMARY.md`;
- any warning or error from `run.log` (copy the lines);
- `git status --short` after the commit.

Leave this prompt file (it is committed in `docs/prompts/`).
