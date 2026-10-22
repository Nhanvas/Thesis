# CC_R1_REPRO — reproducibility check 2 on the laptop (R1, written 2026-10-22)

You are Claude Code on the author's Windows laptop (Git Bash, 16 GB RAM, CPU). Goal: show that a stranger
who clones the public repository, installs `requirements.txt` and uses the public recordings gets the
committed external-validation results with the committed checkpoints. Then look for the script of
report Figure 8. Read `README.md` (sections 3–5) and `docs/REPRODUCE.md` of the clone first.

**Estimated runtime (not measured):** environment 5–15 min, downloads depend on the network, the run
20–45 min, total about 0.5–1.5 h. Measure every step and write the measured times in the record.

## Ground rules

1. Work **only** in the fresh clone `F:/Study/Thesis/repro_R1/Thesis` (never in `F:/Study/Thesis/Code`
   until the final `git pull`). Do not edit any existing file under `src/`, `data/` or `results/x1_external/`.
2. The pass/fail criterion is fixed in `src/r1_compare_external.py`. Never change it, never rerun with
   other settings, never "fix" a difference. A FAIL is a valid result: record it and stop.
3. On anything unexpected (a missing file, a parsed seizure count that differs, a crash): STOP, write it
   in the handback, change nothing else.
4. Stage explicit paths only. Never commit EDF files or `results/x1_external/features/*.npz`.
5. Close Chrome, Edge and Cursor before step 6 (memory).

## Steps

**0. Machine.** Record CPU, RAM, free space on F:, Windows version. Need ≥ 15 GB free; else STOP.

**1. Clean clone.**
```bash
mkdir -p /f/Study/Thesis/repro_R1 && cd /f/Study/Thesis/repro_R1
test ! -e Thesis || { echo "STOP: repro_R1/Thesis exists"; exit 1; }
git clone https://github.com/Nhanvas/Thesis.git && cd Thesis && git log -1 --format='%h %s'
sha256sum data/models_v2/gae_v2_clean_seed*.pt      # must equal docs/PROVENANCE_V2.md
```

**2. New environment** (Python 3.11; if `py -3.11` is missing: STOP).
```bash
py -3.11 -m venv ../venv && source ../venv/Scripts/activate
python -m pip install -U pip && time pip install -r requirements.txt
python -c "import torch, torch_geometric, mne, ruptures, timescoring, sklearn; print(torch.__version__)"
```

**3. Data.** Subjects of this check (fixed): `chb24`, `PN10`, `PN00`, `PN11`.
- Look under `F:/Study/Thesis/Dataset/` for each subject folder (`chb24/` with `chb24_*.edf` and
  `chb24-summary.txt`; `PNxx/` with `PNxx-*.edf` and `Seizures-list-PNxx.txt`). Report what is present.
- For a missing subject, download its folder from PhysioNet into the matching corpus folder of
  `F:/Study/Thesis/Dataset/` (CHB-MIT: `https://physionet.org/files/chbmit/1.0.0/chb24/`; Siena:
  `https://physionet.org/files/siena-scalp-eeg/1.0.0/PN00/`, `…/PN11/`). Read the folder index first and
  report the total size; if it is above 5 GB, STOP and ask.

**4. Inventory** (Windows-safe wrapper of `x1_external.py`, same arguments):
```bash
python src/r1_x1_win.py inventory --data /f/Study/Thesis/Dataset 2>&1 | tee ../inventory.log
```
Required: chb24 16 seizures, PN00 5, PN10 10, PN11 1, and each subject found in one folder only. If a
subject appears twice (another copy of the dataset), make `../data/` with a copy of only the four subject
folders and use `--data ../data` from here on. Any other mismatch: STOP.

**5. Set the committed rows aside** (so that `run` does not skip these subjects):
```bash
mkdir -p results/r1_repro/committed results/r1_repro/rerun
for s in chb24 PN10 PN00 PN11; do
  cp results/x1_external/rows_$s.csv results/x1_external/errors_$s.csv results/r1_repro/committed/
  rm results/x1_external/rows_$s.csv results/x1_external/errors_$s.csv
done
```

**6. Run** the final system on the four subjects (committed checkpoints, label-free statistics):
```bash
( time python src/r1_x1_win.py run --data /f/Study/Thesis/Dataset --subjects chb24 PN10 PN00 PN11 --procs 2 ) 2>&1 | tee results/r1_repro/run.log
```
The log prints hours and seconds per hour of EEG for each subject; keep it.

**7. Keep the rerun, restore the committed files.**
```bash
for s in chb24 PN10 PN00 PN11; do cp results/x1_external/rows_$s.csv results/x1_external/errors_$s.csv results/r1_repro/rerun/; done
git checkout -- results/x1_external/
git status --short results/x1_external/     # only the untracked features/ folder may appear
```

**8. Compare** (criterion fixed before the run):
```bash
python src/r1_compare_external.py --ref results/r1_repro/committed --new results/r1_repro/rerun --out results/r1_repro
```
Exit 0 = PASS, 2 = FAIL. Also report, descriptively, the median |onset| and |offset| error of
`errors_*.csv` (columns `cpd_on`, `cpd_off`, balanced point) for committed vs rerun, per subject.

**9. Figure 8 search** (report Figure 8, "Baseline drift correction", file `fig08_drift.png`, chb03 first
three files, 9th-largest member, seed 42).
- Search `F:/Study/Thesis/` (skip `Dataset/`, `repro_R1/`, any `venv`/`.venv`, `node_modules`, `.git`) for
  files whose name or content contains `fig08_drift` or `fig08`, and for `.py` files that draw a running
  median over the 9th-largest member. Report every hit with its path and date.
- If a script is found: run it unchanged in the new environment with its output redirected to
  `../fig08_test/` (if it only writes to a fixed path, copy it to `../fig08_test/` and change only the
  output path there), list the inputs it reads and whether they are committed, and compare its PNG with
  `F:/Study/Thesis/Reports/v8/figures/fig08_drift.png` (sha256, and by eye). If it runs and draws the
  same figure, copy the original script unchanged to `src/figures_v8/fig08_drift.py` in the clone.
  If nothing is found, say so.

**10. Record.** In `docs/REPRODUCE.md` of the clone: fill "Check 2" (machine, commit, Python and key
package versions, install time, which subjects were local and which were downloaded, measured runtime per
subject, the whole of `results/r1_repro/COMPARE.md`, the onset/offset table, the verdict) and the Figure 8
item; set the status row of check 2 to PASS or FAIL with the date. Change nothing else in the file.

**11. Commit and push from the clone, then update the author's working copy.**
```bash
git add docs/REPRODUCE.md results/r1_repro/COMPARE.md results/r1_repro/compare.csv results/r1_repro/run.log \
  results/r1_repro/committed/*.csv results/r1_repro/rerun/*.csv          # + src/figures_v8/fig08_drift.py only if step 9 found it
git commit -m "R1 check 2: external rerun from a clean clone (chb24, PN10, PN00, PN11) vs committed results"
git push origin main
git -C /f/Study/Thesis/Code pull --ff-only
```

**12. Handback.** Write `F:/Study/Thesis/Agent/inbox/R1_check2_HANDBACK.md`: first line `VERDICT: PASS`
or `VERDICT: FAIL`; then the seed-42 table of COMPARE.md, the per-subject summary, measured times, the
Figure 8 finding, every deviation from this prompt and the commit hash. Print it at the end.
