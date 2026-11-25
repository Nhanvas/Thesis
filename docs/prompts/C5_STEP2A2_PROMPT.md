# C5 Step 2a (rerun after the memory fix) — SzScan Step 2 tests and gates (Claude Code, laptop)

Chat C5 (Track C). Design: `results/c5_szscan/DESIGN_STEP2.md` (rows C7 and C8 record the fix). Run only committed
code; change no file in `web_demo/` or `src/`. Stop the demo (`bash web_demo/stop_demo.sh`) before starting, so that
memory is free. Never print, list or open anything under `F:/Study/Thesis/Dataset/Clinical/` yourself — only the gate
script reads it, and it writes only `Agent/inbox/C5_STEP2_PRIVATE.md`; do not paste that file into any committed file.

Work in `F:/Study/Thesis/Code` (Git Bash). Report to `F:/Study/Thesis/Agent/inbox/C5_STEP2A2_REPORT.md`.
Every command below is one line; run it as written.

1. `git log -1 --format=%H` and `git status --porcelain -- web_demo src` (report both).
2. Synthetic test (temporary folders only, about 5–8 min):
   `PYTHONUTF8=1 python src/c5_step2_test.py > ../Agent/inbox/C5_STEP2_TEST.log 2>&1` — must end with `ALL PASS (33 checks)`.
3. Backend tests: `cd web_demo/backend && PYTHONUTF8=1 python -m pytest -q tests; cd ../..` — must report `15 passed`.
   If step 2 or 3 does not pass, STOP and report.
4. Smoke (the shortest test subject and the largest Siena file):
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --smoke`
   Report the `SMOKE:` line and `results/c5_szscan/step2/smoke/g1.csv` and `siena.csv` in full. While it runs, look at
   Task Manager (memory of the python process) a few times and report the highest value you saw.
   If the line says `TOO HIGH`, STOP and report.
   Projection (write it as computed): G1 seconds per hour × 279.4 h + Siena (`load_s` + `phase_a_s`) per hour × 141 h,
   plus 30 % for the equality reference. If the projection is above 4 h, STOP and report (the author decides).
5. Full run:
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --private-dir F:/Study/Thesis/Dataset/Clinical > ../Agent/inbox/C5_STEP2_GATES.log 2>&1`
   Report the highest Task Manager memory you saw.
6. Check that no temporary folder is left: `ls "$TEMP" | grep -E "^c5(g1|g6|priv)_" | wc -l` (report the number).
7. Report: the last 3 lines of the log, the whole `results/c5_szscan/step2/GATES.md`, `siena.csv` in full, measured run
   times. Say only whether `Agent/inbox/C5_STEP2_PRIVATE.md` was written (do not copy its content). Do not commit; the
   author commits.
