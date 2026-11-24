# C5 Step 2a — SzScan Step 2 tests and gates (Claude Code, laptop)

Chat C5 (Track C). Design: `results/c5_szscan/DESIGN_STEP2.md`. Run only committed code; change no file in `web_demo/` or
`src/`. Stop the demo (`bash web_demo/stop_demo.sh`) before starting, so that memory is free. Never print, list or
open anything under `F:/Study/Thesis/Dataset/Clinical/` yourself — only the gate script reads it, and it writes only
`Agent/inbox/C5_STEP2_PRIVATE.md`; do not paste that file into any committed file.

Work in `F:/Study/Thesis/Code` (Git Bash). Report to `F:/Study/Thesis/Agent/inbox/C5_STEP2A_REPORT.md`.

1. `git log -1 --format=%H`; `git status --porcelain -- web_demo src` (report both).
2. Synthetic test of Step 2 (temporary folders only, ≈ 3–6 min):
   `PYTHONUTF8=1 python src/c5_step2_test.py > ../Agent/inbox/C5_STEP2_TEST.log 2>&1` — must end with `ALL PASS (27 checks)`.
3. Existing backend tests: `cd web_demo/backend && PYTHONUTF8=1 python -m pytest -q tests; cd ../..` — must report
   `15 passed`.
4. Frontend build check: `cd web_demo/frontend && npx vite build && rm -rf dist; cd ../..` — must end with `built in`.
   If steps 2–4 do not pass, STOP and report.
5. Smoke of the real-data gates (one test subject, the largest Siena file):
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --smoke`
   Report the `SMOKE:` line and `results/c5_szscan/step2/smoke/g1.csv`, `siena.csv`. If it says `TOO HIGH`, STOP.
   Projection (write it as computed): G1 seconds per hour × 279.4 h + Siena (load + Phase A) seconds per hour × 141 h.
   If the projection is above 4 h, STOP and report (the author decides).
6. Full run (watch Task Manager memory a few times and report what you saw):
   `PYTHONUTF8=1 python src/c5_step2_gates.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --private-dir F:/Study/Thesis/Dataset/Clinical > ../Agent/inbox/C5_STEP2_GATES.log 2>&1`
7. Report: the last 3 lines of the log, the whole `results/c5_szscan/step2/GATES.md`, measured run times. Say only
   whether `Agent/inbox/C5_STEP2_PRIVATE.md` was written (do not copy its content). Do not commit; the author commits.
