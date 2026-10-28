#!/usr/bin/env bash
# SzScan demo launcher (Git Bash on Windows). Usage:  bash F:/Study/Thesis/Code/web_demo/start_demo.sh
# Starts the backend (127.0.0.1:8000, no --reload), waits until it answers, then starts the
# frontend on 5173 with --strictPort. Ctrl+C in this window stops both.
# If you use a virtual environment, activate it first or run:  PY=/path/to/python bash start_demo.sh
set -u
ROOT="F:/Study/Thesis/Code/web_demo"
PY="${PY:-python}"
LOG="$ROOT/backend/demo_backend.log"

port_busy() { netstat -ano | grep LISTENING | grep -q ":$1 "; }

echo "[1/4] Checking ports 8000 and 5173 ..."
for p in 8000 5173; do
  if port_busy "$p"; then
    echo "  Port $p is already in use. Run:  bash $ROOT/stop_demo.sh   then start again."
    exit 1
  fi
done

echo "[2/4] Checking backend/.env ..."
if ! grep -q "^ADMIN_USER=." "$ROOT/backend/.env" 2>/dev/null || ! grep -q "^ADMIN_PASS=." "$ROOT/backend/.env" 2>/dev/null; then
  echo "  backend/.env is missing ADMIN_USER or ADMIN_PASS."
  exit 1
fi

echo "[3/4] Starting backend (log: $LOG) ..."
cd "$ROOT/backend" || exit 1
"$PY" -m uvicorn main:app --host 127.0.0.1 --port 8000 > "$LOG" 2>&1 &
BACK=$!
trap 'echo "Stopping backend ..."; kill $BACK 2>/dev/null' EXIT

ok=0
for i in $(seq 1 90); do
  code=$(curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8000/api/session || true)
  if [ "$code" = "401" ] || [ "$code" = "200" ]; then ok=1; break; fi
  if ! kill -0 "$BACK" 2>/dev/null; then break; fi
  sleep 1
done
if [ "$ok" != "1" ]; then
  echo "  Backend did not start. Last lines of the log:"
  tail -n 25 "$LOG"
  exit 1
fi
echo "  Backend OK (answered in ${i}s)."

echo "[4/4] Starting frontend on http://localhost:5173 (Ctrl+C stops everything) ..."
cd "$ROOT/frontend" || exit 1
npx vite --host 127.0.0.1 --port 5173 --strictPort
