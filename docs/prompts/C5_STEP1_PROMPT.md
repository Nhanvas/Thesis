# C5 Step 1 — SzScan verification run (Claude Code, laptop)

Chat C5 (Track C). Run the committed script `src/c5_szscan_verify.py`; do not change any file in `web_demo/` or `src/`.
Read only on the application's database and upload cache (the script opens the database read-only; V7 uses a temporary
database and upload folder). CHB-MIT only: the script STOPs if the database holds a subject that is not `chbNN`.
Never print, list or open anything under `F:/Study/Thesis/Dataset/Clinical/`.

Work in `F:/Study/Thesis/Code` (Git Bash). Report to `F:/Study/Thesis/Agent/inbox/C5_STEP1_REPORT.md`.

1. Check: `git log -1 --format=%H` and `git status --porcelain -- web_demo src` (report both).
   `PYTHONUTF8=1 python -c "import fastapi, fastapi.testclient, httpx, mne, torch, torch_geometric; print('ok')"` and
   `node --version`. If an import fails, STOP and report which (do not install anything).
2. Synthetic test: `PYTHONUTF8=1 python src/c5_szscan_verify_test.py > Agent/inbox/C5_TEST.log 2>&1`
   (≈ 2–5 min). It must end with `ALL PASS`; otherwise STOP and report the FAIL lines.
3. Smoke: `PYTHONUTF8=1 python src/c5_szscan_verify.py --dataset F:/Study/Thesis/Dataset/CHB-MIT --smoke`.
   Report the line starting with `SMOKE:` (seconds per hour of EEG, projected full run).
4. If the projected full run is ≤ 3 h: run the full check
   `PYTHONUTF8=1 python src/c5_szscan_verify.py --dataset F:/Study/Thesis/Dataset/CHB-MIT > Agent/inbox/C5_FULL.log 2>&1`.
   If it is > 3 h, STOP after the smoke and report (the author decides).
5. Report: the last 3 lines of the log, the whole `results/c5_szscan/VERIFY.md`, the measured run time and the peak
   memory if Windows Task Manager showed it. Do not commit; the author commits `results/c5_szscan/`.
