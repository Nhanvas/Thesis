"""Read-only external memory monitor for the overnight Part 3 v2 run.
Samples the uvicorn backend process and any pipeline_worker.py subprocess every 5s.
Writes CSV to web_demo/report_handback/part3_v2_memory.csv. Changes no app code/setting.
"""
import csv
import sys
import time
from pathlib import Path

import psutil

BACKEND_PID = int(sys.argv[1])
OUT_PATH = Path(sys.argv[2])
STATE_PATH = Path(sys.argv[3])  # driver writes current subject name here

OUT_PATH.parent.mkdir(parents=True, exist_ok=True)

with open(OUT_PATH, "w", newline="") as f:
    w = csv.writer(f)
    w.writerow(["timestamp_utc", "subject", "backend_rss_mb", "worker_rss_mb", "worker_pid", "total_rss_mb", "system_available_mb"])
    f.flush()

    while True:
        ts = time.strftime("%Y-%m-%dT%H:%M:%S", time.gmtime())
        try:
            subject = STATE_PATH.read_text().strip() if STATE_PATH.exists() else ""
        except Exception:
            subject = ""

        backend_rss = 0.0
        worker_rss = 0.0
        worker_pid = ""
        try:
            bp = psutil.Process(BACKEND_PID)
            backend_rss = bp.memory_info().rss / 1e6
            for child in bp.children(recursive=True):
                try:
                    cmdline = " ".join(child.cmdline())
                except Exception:
                    cmdline = ""
                if "pipeline_worker" in cmdline:
                    worker_rss += child.memory_info().rss / 1e6
                    worker_pid = str(child.pid) if not worker_pid else worker_pid + f"+{child.pid}"
        except psutil.NoSuchProcess:
            # backend gone -- record and stop, caller (driver) already knows from its own poll
            w.writerow([ts, subject, "BACKEND_GONE", "", "", "", ""])
            f.flush()
            break

        try:
            sysmem = psutil.virtual_memory()
            avail_mb = sysmem.available / 1e6
        except Exception:
            avail_mb = ""

        total_rss = backend_rss + worker_rss
        w.writerow([ts, subject, f"{backend_rss:.1f}", f"{worker_rss:.1f}", worker_pid, f"{total_rss:.1f}", f"{avail_mb:.1f}" if avail_mb != "" else ""])
        f.flush()
        time.sleep(5)
