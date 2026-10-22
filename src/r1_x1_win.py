#!/usr/bin/env python
"""
r1_x1_win.py -- runs src/x1_external.py unchanged on Windows (R1, 2026-10-22).

Why: the Siena seizure-list parser copied verbatim from epilepsy2bids calls time.mktime on a
time.strptime result whose year defaults to 1900; the Windows C runtime raises OverflowError for any
date before 1970 (Linux does not). The parser only uses differences of two such values
(_substractTimeStamps, + 24 h when negative), so seconds-of-day give exactly the same seizure times.
time.mktime is replaced for this process only; x1_external.py itself is not edited. Same workaround as
src/figures_v8/export_v8_data.py (handback CC_FIGURES_V8, 12/10).

  python src/r1_x1_win.py run --data DIR --subjects chb24 PN10 --procs 2      (same arguments as x1_external.py)
"""
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))


def _seconds_of_day(st):
    return float(st.tm_hour * 3600 + st.tm_min * 60 + st.tm_sec)


if __name__ == "__main__":
    time.mktime = _seconds_of_day
    import x1_external as X  # noqa: E402
    X.main()
