# Claude Code prompt — F-A1.5 diagnostic T1 on the laptop (chat D35-F, 21/11)

You are Claude Code in the repository `F:/Study/Thesis/Code` (Git Bash). Run one committed script, check its output,
write a short report. Do not edit any file, do not install or upgrade any package, do not commit.

1. `cd /f/Study/Thesis/Code && git status --short src/fa15_diag_laptop.py src/v9_x6_asr.py` — both must be unmodified.
2. Find the Python that has asrpy (V9-X6 ran with asrpy 0.0.8 on this laptop): `python -c "import asrpy, mne, scipy,
   numpy; print(numpy.__version__, scipy.__version__, mne.__version__)"`. If it fails, check whether the repository has a
   virtual environment (`.venv/`, `venv/`) whose Python imports asrpy, and use that one. If none does, STOP and write the
   report with "asrpy not found" — do not install it.
3. Check that the inputs exist (read only; print only yes / no, never list the Dataset folder): `data/processed/chb03_stats.json`,
   `data/processed/chb06_stats.json`, `data/processed/chb15_stats.json`, `data/processed/chb16_stats.json`,
   `results/v9_anatomy/xcache/chb24.npz`, `F:/Study/Thesis/Dataset/CHB-MIT/chb06/chb06_01.edf`. If one is missing, STOP
   and report which.
4. Check free memory (`wmic OS get FreePhysicalMemory` or `systeminfo`): at least 4 GB free is needed (one file at a time,
   ≤ 2 GB per process for the 4-h file). If less, report and ask the author before running.
5. Run: `PYTHONUTF8=1 python src/fa15_diag_laptop.py --run` (≈ 35 min, computed: 12 files, 15 h of EEG at V9-X6's
   measured 135 s per hour). It is resumable: if it stops, run the same command again.
6. Check: `results/fa15/diag_laptop/` holds `compare.csv`, `env.json`, `SUMMARY.md` and 12 files in `parts/`; nothing
   was written to `results/v9_x6/`.
7. Write `F:/Study/Thesis/Agent/inbox/FA15_DIAG_LAPTOP_REPORT.md`: the Python used, the full `SUMMARY.md`, the runtime,
   any warning or error. Then stop; the author commits `results/fa15/diag_laptop/` himself.
