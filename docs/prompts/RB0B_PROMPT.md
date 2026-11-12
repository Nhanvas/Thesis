# RB0B — full check of the chb12_27–29 conversion and amplitude (Claude Code, laptop; Track F, chat D22-F)

**Estimated runtime: 10–20 min (computed estimate, not measured)** — 24 chb12 EDF files of ≈ 1 h each, read and
filtered once each, plus three SzCORE conversions. Memory ≈ 2 GB.

**What and why (do not interpret results; the chat does that).** chb12_27, _28 and _29 are recorded in a referential
montage. The research track converts them to the 18 bipolar derivations exactly as SzCORE's own CHB-MIT converter does
(`epilepsy2bids`, commit `d3fb175`). The earlier header check (RB0) passed, but the amplitude of the derived channels
was outside the range of two neighbouring files. This task runs the committed script `src/r2_rb0b.py`, which checks on
**all 24 chb12 files, every channel, the whole recording**: (A) inputs = PhysioNet; (B) our conversion = SzCORE's,
sample by sample; (C) clipped samples; (D) amplitude through the pipeline vs the 21 bipolar files, 5-SD flags;
(E) narrow spectral peaks. Plan: `docs/FUTURE_RESEARCH_PLAN.md` §12 row 12/11 21:30.

## Ground rules

1. Change no file under `src/`, `data/`, `results/` except the new output folder `results/r2/r0_data/chb12_ref/rb0b/`.
   Do not edit the script; if it fails, stop and report (rule 5).
2. Install nothing into the main Python environment. Extra packages go only into `F:/Study/Thesis/_tmp/rb0b/pkgs`
   with `--no-deps`. Never install `resampy` or `numba` (the script handles a missing `resampy` itself).
3. Everything temporary lives in `F:/Study/Thesis/_tmp/rb0b/` and is deleted at the end.
4. Stage explicit paths only; never `git add .` or a parent directory.
5. On any `STOPPED` / `STOP RB0b` / traceback: do not retry with changes, do not work around it. Keep whatever the
   output folder holds, still commit and push it (it is evidence), and write the error in the report.

## Steps (Git Bash, from `F:/Study/Thesis/Code`)

**0 — repository.**
```bash
cd F:/Study/Thesis/Code
git pull
git log -1 --oneline
ls src/r2_rb.py src/r2_rb0b.py docs/prompts/RB0B_PROMPT.md
```
All three files must exist. Note the commit hash for the report.

**1 — environment.**
```bash
python -c "import sys, numpy, scipy, pandas, mne, torch; print(sys.version.split()[0], numpy.__version__, scipy.__version__, pandas.__version__, mne.__version__, torch.__version__)"
python -c "import pyedflib; print(pyedflib.__version__)"
```
If the second line fails (no `pyedflib`):
```bash
mkdir -p F:/Study/Thesis/_tmp/rb0b
python -m pip install --no-deps --target F:/Study/Thesis/_tmp/rb0b/pkgs pyedflib==0.1.42
```
(if no wheel exists for this Python version, use the newest `pyedflib` with the same flags and write the version used
in the report).

**2 — SzCORE converter at the pinned commit.**
```bash
mkdir -p F:/Study/Thesis/_tmp/rb0b
git clone https://github.com/esl-epfl/epilepsy2bids.git F:/Study/Thesis/_tmp/rb0b/epilepsy2bids
git -C F:/Study/Thesis/_tmp/rb0b/epilepsy2bids checkout d3fb17526b8a483e292ae9ba2e51b02d5f9128ff
```
The script checks the sha256 of `src/epilepsy2bids/eeg.py` itself (line endings normalised) and stops if it differs.

**3 — run** (the CHB-MIT folder is the default `F:/Study/Thesis/Dataset/CHB-MIT`; `--pkgs` is appended to the end of
`sys.path`, so it does nothing when step 1 installed nothing and never shadows the main environment):
```bash
mkdir -p results/r2/r0_data/chb12_ref/rb0b
python src/r2_rb0b.py \
  --e2b-eeg F:/Study/Thesis/_tmp/rb0b/epilepsy2bids/src/epilepsy2bids/eeg.py \
  --pkgs F:/Study/Thesis/_tmp/rb0b/pkgs \
  2>&1 | tee results/r2/r0_data/chb12_ref/rb0b/run.log
```
Expected log: `A: 24 listed, 24 present, sha256 equal 24 -> PASS`, then one line per file (21 `bipolar`,
3 `referential`), then `END gates {'A_inputs': 'PASS', 'B_szcore_equal': ...}`. Do not judge the values.

**4 — check the output folder** `results/r2/r0_data/chb12_ref/rb0b/`. It must hold: `A_inputs.csv`,
`B_szcore_compare.json`, `C_clipping_channels.csv`, `C_clipping_files.csv`, `C_clipping_derivations.csv`,
`D_rms_files.csv`, `D_rms_blocks_5min.csv`, `D_flags.csv`, `D_position.csv`, `E_peaks.csv`,
`E_peaks_referential_only.csv`, `rb0b.json`, `SUMMARY.md`, `run.log`. List the files with their sizes. No EDF, no
`.npz`, nothing over 20 MB (if a file is larger, do not commit it; say so in the report).

**5 — commit and push** (explicit path only):
```bash
git add results/r2/r0_data/chb12_ref/rb0b
git status --short
git commit -m "RB0b: chb12_27-29 conversion vs SzCORE, clipping, amplitude, spectrum (D22-F)"
git push
```
`git status --short` must list only paths under `results/r2/r0_data/chb12_ref/rb0b/` as staged (pre-existing `??`
lines: leave them). Note the new commit hash.

**6 — report** `F:/Study/Thesis/Agent/inbox/RB0B_REPORT.md` (facts only, no interpretation):
- the commit hash of step 0 and of step 5;
- measured runtime (`runtime_s` in `rb0b.json`) and the wall time of the Python process;
- environment line of step 1; where `pyedflib` came from (installed / `_tmp`, version); the `resampy` line of
  `rb0b.json` (real or stub);
- the gates (`gates` in `rb0b.json`);
- the full text of `SUMMARY.md`;
- any warning or error from `run.log` (copy the lines);
- `git status --short` after the commit.

**7 — clean up.**
```bash
rm -rf F:/Study/Thesis/_tmp/rb0b
ls F:/Study/Thesis/_tmp
```
Leave this prompt file (it is committed in `docs/prompts/`).
