#!/usr/bin/env python
"""
p3_seizure_burden.py -- phase 3, first check (author hypothesis 2026-10-07): is the fixed top-p
budget of the D1 detector (top 0.5 % of each patient's time) too small for patients with many
seizures, e.g. chb15 (0/20 at look #6)?
Reads annotation metadata only: the CHB-MIT summary files (seizure start/end times) and the window
labels of the v2 sets (is_ictal, is_signal_loss, file_idx). No model output is read.
NOTE: for the 8 test subjects this is test-set information; anything designed from it makes the next
test look less clean and must be disclosed in the record (look log, section 3).

Per subject: seizures (summary count | v2 window-run count), durations (median, min, max, < 20 s),
total ictal minutes, recorded hours (non-signal-loss), the D1 budget at top 0.5 % in minutes, and
ictal minutes / budget. Note on reading: an event-level TP needs only ONE supra-threshold window per
seizure, so ictal time > budget does not by itself prevent detection; the ratio shows whether the
budget can be spent on seizures at all once FPs take their share.
Run:  python src/p3_seizure_burden.py        (seconds)
"""
import re
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
WIN, TOP = 4, 0.005
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
NONTEST = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08", "chb09", "chb12",
           "chb19", "chb20", "chb21", "chb23", "chb10", "chb11", "chb22"]
DS = ROOT.parent / "Dataset"


def runs(mask):
    out, i, n = [], 0, len(mask)
    while i < n:
        if mask[i]:
            j = i
            while j < n and mask[j]:
                j += 1
            out.append((i, j)); i = j
        else:
            i += 1
    return out


def summary_durations(s):
    hits = sorted(DS.rglob(f"{s}-summary*"))
    if not hits:
        return None, "summary not found"
    t = hits[0].read_text(encoding="utf-8", errors="replace")
    st = [int(x) for x in re.findall(r"(?i)start time:\s*(\d+)\s*s", t)]
    en = [int(x) for x in re.findall(r"(?i)end time:\s*(\d+)\s*s", t)]
    if len(st) != len(en):
        return None, f"unparsed ({len(st)} starts, {len(en)} ends) in {hits[0].name}"
    return [e - a for a, e in zip(st, en)], hits[0].name


def main():
    print(f"summary root searched: {DS}")
    print("subject set   n_sum n_v2  dur med/min/max (s)  <20s  ictal_min  rec_h   budget_min  ictal/budget  source")
    for group, subs, data in (("test", TEST, ROOT / "data" / "testset_v2"), ("non-test", NONTEST, ROOT / "data" / "trainset_v2")):
        for s in subs:
            z = np.load(data / f"{s}.npz", allow_pickle=True)
            ict = z["is_ictal"].astype(bool); ok = ~z["is_signal_loss"].astype(bool); fidx = z["file_idx"].astype(int)
            durs_v2 = []
            for f in np.unique(fidx):
                m = np.flatnonzero(fidx == f)
                durs_v2 += [(b - a) * WIN for a, b in runs(ict[m])]
            ds, src = summary_durations(s)
            d = np.array(ds if ds else durs_v2, float)
            ictal_min = (ict & ok).sum() * WIN / 60
            rec_h = ok.sum() * WIN / 3600
            budget = TOP * len(ict) * WIN / 60
            print(f"{s:7s} {group:8s} {len(ds) if ds else -1:5d} {len(durs_v2):4d}  "
                  f"{np.median(d):5.0f}/{d.min():4.0f}/{d.max():5.0f}        {int((d < 20).sum()):3d}  {ictal_min:8.1f}  "
                  f"{rec_h:6.1f}  {budget:9.1f}  {ictal_min / budget:11.2f}  {src}")


if __name__ == "__main__":
    sys.exit(main())
