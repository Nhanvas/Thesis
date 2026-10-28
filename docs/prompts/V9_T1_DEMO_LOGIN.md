# V9-T1 — SzScan login failure + cold-start reliability (Claude Code, laptop)

Estimated runtime: 20–40 min (estimated, not measured). The author will test the app himself at the end.

## Context
- The author demoed SzScan (`web_demo/`, build `szscan-frozen-v4.1`) to his supervisor and **login failed**. The defense is 05–06/11; a rehearsal is on 02/11. The demo must not fail.
- Login facts read from the code (verify them yourself, do not trust this list):
  - `backend/main.py` loads `backend/.env` with `load_dotenv`; `ADMIN_USER` / `ADMIN_PASS` default to `""` if missing.
  - Sessions are an in-memory dict: any backend restart (incl. `uvicorn --reload` reacting to file writes) logs everyone out.
  - CORS allows only `http://localhost:5173` and `http://127.0.0.1:5173`; Vite proxies `/api` to `http://127.0.0.1:8000`.
  - Frontend: `frontend/src/api.js` (credentials: 'include'), `screens/LoginScreen.jsx`.

## Rules
- **Diagnose first. Do not change any code until the author approves the fix in this terminal.**
- Never print the value of `ADMIN_PASS` (print length, ASCII-only yes/no, leading/trailing whitespace yes/no, BOM yes/no).
- Do not commit anything in this task unless the author approves a fix; then stage explicit paths only.
- Another Claude Code terminal may be running analysis in the repo at the same time: do not touch `src/`, `results/`, or git state outside `web_demo/`.

## Steps
1. Read `web_demo/backend/main.py`, `web_demo/frontend/src/api.js`, `web_demo/frontend/src/screens/LoginScreen.jsx`, `web_demo/frontend/vite.config.js`, any start script (`*.bat`, `*.sh`, `*.ps1`, README, `DEMO_FINAL_HANDBACK.md`, `STEP8_9_PREDEFENSE_CHECKLIST.md`).
2. Check `backend/.env`: exists? both keys present? encoding/BOM, CRLF, spaces, non-ASCII characters (Vietnamese Telex/Unikey can silently turn typed letters into "â", "đ", "ư" in the password box).
3. Find out exactly how the backend and frontend are started (command, `--reload` or not, working directory). If `--reload` is used, check whether ingest/DB/export writes files inside the watched directory (that would restart the server and drop the session mid-demo).
4. Reproduce with requests/curl against the running app:
   - correct login; wrong password; empty `.env`;
   - via `http://localhost:5173` and `http://127.0.0.1:5173`; what happens if Vite falls back to port 5174 because 5173 is busy;
   - backend not running: what the UI shows;
   - backend restarted after login: what the UI shows.
5. Report to the author, in Vietnamese, short: the most likely root cause(s) with evidence, ranked; and the **minimal** fix you propose (examples, only if supported by evidence: fail loudly at startup if credentials are empty; a single start script that runs the backend without `--reload` and the frontend on a fixed port with `--strictPort`; a `/api/health` check). Wait for approval.
6. After the fix (or if no code change is needed), write `F:/Study/Thesis/Defense/demo/COLD_START_CHECKLIST.md` (outside the repo): numbered steps from a powered-off laptop to the logged-in app with chb03 already ingested, offline (Wi-Fi off), plus a 1-minute self-test and what to do if each step fails (fallback video).
7. **Feasibility only, no change:** can the current ingest path (`batch_ingest.py`, `pipeline_demo.py`, `edf_order.py`) accept (a) `chb24` (CHB-MIT format) and (b) a Siena EDF (different electrode names, sampling rate, referential montage)? Answer per item: works as is / needs code change (which file, how big) / unknown. Do not ingest anything.

## Return format (paste back to the thesis chat)
- Root cause (ranked, with evidence) · fix applied or proposed (files, diff size) · self-test result · chb24/Siena feasibility · checklist path.
