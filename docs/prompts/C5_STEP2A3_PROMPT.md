# C5 Step 2a (rerun after the second memory fix) — SzScan Step 2 tests and gates (Claude Code, laptop)

Chat C5 (Track C). Design: `results/c5_szscan/DESIGN_STEP2.md` (row C8 records both fixes). Run only committed code;
change no file in `web_demo/` or `src/`. Stop the demo (`bash web_demo/stop_demo.sh`) before starting. Never print,
list or open anything under `F:/Study/Thesis/Dataset/Clinical/` yourself — only the gate script reads it, and it
writes only `Agent/inbox/C5_STEP2_PRIVATE.md`; do not paste that file into any committed file.

Work in `F:/Study/Thesis/Code` (Git Bash). Report to `F:/Study/Thesis/Agent/inbox/C5_STEP2A3_REPORT.md`.
Every command below is one line; run it as written.

The gate script now measures the memory of its own process (file pages included) and stops itself with a line
starting `STOP: process memory` if it goes above 2 GB. If the laptop's own low-memory guard kills the process
instead, write down the free system memory just before (Task Manager), do not retry more than once, and report.

1. `git log -1 --format=%H` and `git status --porcelain -- web_demo src` (report both).
2. Remove the folder left by the killed run: `rm -rf "$TEMP"/c5g6_j5ghy4vb` and report `ls "$TEMP" | grep -cE "^c5(g1|g6|priv)_"`.
3. `python -c "import psutil; print(psutil.__version__)"` (report the output; if it fails, report that and continue —
   the script then uses the Windows API).
4. Synthetic test (temporary folders only, about 10–15 min):
   `PYTHONUTF8=1 python src/c5_step2_test.py > ../Agent/inbox/C5_STEP2_TEST.log 2>&1` — must end with `ALL PASS (33 checks)`.
5. Backend tests: `cd web_demo/backend && PYTHONUTF8=1 python -m pytest -q tests; cd ../..` — must report `15 passed`.
   If step 4 or 5 does not pass, STOP and report.
6. Smoke (the shortest test subject and the largest Siena file):
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --smoke`
   Report the first line (available memory at start), the `SMOKE:` line, and `results/c5_szscan/step2/smoke/g1.csv`
   and `siena.csv` in full. If it says `TOO HIGH` or `STOP`, STOP and report.
   Projection (write it as computed): G1 `seconds` per hour × 279.4 h + Siena (`load_s` + `phase_a_s`) per hour ×
   141 h, plus 30 % for the equality reference. If the projection is above 4 h, STOP and report (the author decides).
7. Full run:
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --private-dir F:/Study/Thesis/Dataset/Clinical > ../Agent/inbox/C5_STEP2_GATES.log 2>&1`
8. `ls "$TEMP" | grep -cE "^c5(g1|g6|priv)_"` (report the number).
9. Report: the last 3 lines of the log, the whole `results/c5_szscan/step2/GATES.md`, `siena.csv` in full, measured
   run times. Say only whether `Agent/inbox/C5_STEP2_PRIVATE.md` was written (do not copy its content). Do not
   commit; the author commits.
