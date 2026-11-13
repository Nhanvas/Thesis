# RB1C — robustness of the z-score statistic in every case (Claude Code, laptop; Track F, chat D23-F)

**Estimated runtime: 1–1.5 h with 2 processes (computed estimate from RB1b's measured rates, not measured).** Reads
every CHB-MIT EDF (24 cases, ≈ 983 h) and every Siena EDF (14 patients, 141 h): sha256, the statistics loop, the
clipping, the whole-file filter for the flags, the signal-loss flags. Peak memory ≈ 3 GB per process (chb04); with 2
processes ≈ 6 GB. If the laptop has less than 12 GB free, use `--procs 1` (≈ 2–3 h).

**What and why (do not interpret results; the chat does that).** RB1b showed that chb12's statistic (per-channel mean
/ SD used for the z-score and the 5-SD flag) is moved by a few large windows. The committed script `src/r2_rb1c.py`
measures, for every case, the record statistic and its alternatives (SD without windows holding clipped samples,
MAD, IQR), how concentrated it is, and the flagged / clean windows under each. Gates: inputs = PhysioNet (G-in), the
replicated statistic = the committed one (G-stats), flag and clean counts = the committed ones (G-flags; chb24 not
gated). Plan: `docs/FUTURE_RESEARCH_PLAN.md` §12 row 13/11 09:30.

## Ground rules

1. Change no file under `src/`, `data/`, `results/` except the new output folder `results/r2/r0_data/rb1c/`. Do not
   edit the script; if it fails, stop and report (rule 5).
2. Install nothing. The script uses what RB1b used (numpy, scipy, pandas, mne, the repository's modules, which import
   torch); `pyedflib` and the SzCORE clone are not needed.
3. Nothing temporary is created outside the output folder.
4. Stage explicit paths only; never `git add .` or a parent directory.
5. On any `STOP RB1c` / traceback: do not retry with changes, do not work around it. Keep whatever the output folder
   holds (`rb1c.json` and the log), still commit and push it (it is evidence), and write the error in the report.
6. Siena and CHB-MIT file names are public; nothing from `Dataset/Clinical/` is read.

## Steps (Git Bash, from `F:/Study/Thesis/Code`)

**0 — repository.**
```bash
cd F:/Study/Thesis/Code
git pull
git log -1 --oneline
ls src/r2_rb1c.py src/r2_rb.py docs/prompts/RB1C_PROMPT.md results/r2/r1_system/run/data_gate.json results/r2/r0_data/ext/external_cases.csv
ls F:/Study/Thesis/Dataset/CHB-MIT | head -3; ls F:/Study/Thesis/Dataset/siena | head -3
```
All files must exist; note the commit hash. The Siena folder must hold the patient folders (`PN00`, …) with their
`Seizures-list-*.txt`. If the Siena root on this laptop has another name, use it as `--siena-dir` below and say so in
the report.

**1 — environment and free memory.**
```bash
python -c "import sys, numpy, scipy, pandas, mne, torch; print(sys.version.split()[0], numpy.__version__, scipy.__version__, pandas.__version__, mne.__version__, torch.__version__)"
python -c "import psutil; print(round(psutil.virtual_memory().available/2**30,1), 'GB free')" 2>/dev/null || echo "psutil not installed (skip)"
```

**2 — run** (`--procs 1` if less than 12 GB free):
```bash
mkdir -p results/r2/r0_data/rb1c
python src/r2_rb1c.py --siena-dir F:/Study/Thesis/Dataset/siena --procs 2 2>&1 | tee results/r2/r0_data/rb1c/run.log
```
Expected log: `versions …`, then one line per case `chbXX: {"G-in": "PASS", "G-stats": "PASS", "G-flags": "PASS"} (… s)`
(chb24: `"G-flags": "NOT GATED"`; Siena `PNxx`: G-in and G-stats only), then `END 38 cases, every gate PASS`. Do not
judge the values. MNE prints many `RuntimeWarning: Scaling factor is not defined` lines for the dummy `-` channels of
CHB-MIT (seen in RB0b / RB1b); they are expected.

**3 — check the output folder** `results/r2/r0_data/rb1c/`: `rb1c.json`, `SUMMARY.md`, `cases.csv`, `channels.csv`,
`flag_grid.csv`, `files.csv`, `top_windows.csv`, `run.log`. List them with sizes. No EDF, no `.npz`, nothing over 20 MB
(if `run.log` is larger, keep only its lines that do not contain `RuntimeWarning` or `read_raw_edf` and say so).

**4 — commit and push** (explicit path only):
```bash
git add results/r2/r0_data/rb1c
git status --short
git commit -m "RB1c: robustness of the z-score statistic, every case (D23-F)"
git push
```
`git status --short` must list only paths under `results/r2/r0_data/rb1c/` as staged. Note the new commit hash.

**5 — report** `F:/Study/Thesis/Agent/inbox/RB1C_REPORT.md` (facts only, no interpretation):
- the commit hash of step 0 and of step 4;
- measured runtime (`runtime_s` in `rb1c.json`), the wall time of the Python process, `--procs` used, free memory;
- the environment line of step 1 and the Siena folder used;
- the gate line of every case (from `run.log`);
- the full text of `SUMMARY.md`;
- any warning or error from `run.log` other than the expected MNE scaling warnings (copy the lines);
- `git status --short` after the commit.

Leave this prompt file (it is committed in `docs/prompts/`).
