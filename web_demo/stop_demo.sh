#!/usr/bin/env bash
# Stops whatever listens on the demo ports 8000 (backend) and 5173 (frontend).
# Usage:  bash F:/Study/Thesis/Code/web_demo/stop_demo.sh
for p in 8000 5173; do
  pids=$(netstat -ano | grep LISTENING | grep ":$p " | awk '{print $NF}' | sort -u)
  if [ -z "$pids" ]; then
    echo "Port $p: free"
  else
    for pid in $pids; do
      echo "Port $p: stopping PID $pid"
      taskkill //PID "$pid" //F > /dev/null 2>&1
    done
  fi
done
