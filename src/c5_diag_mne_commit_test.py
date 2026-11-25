#!/usr/bin/env python
"""
c5_diag_mne_commit_test.py -- synthetic test of c5_diag_mne_commit.py (chat C5b).

Writes an EDF (specification, Kemp et al. 1992) with N signals at 512 Hz, the first two named 'EEG Fp1' and 'EEG F7',
then runs the diagnosis on it. Checks: (1) the two reads are equal bit for bit; (2) with 49 signals the whole-file
commit growth is about the all-signal buffer (H1's mechanism exists in mne 1.12.1); (3) with 2 signals the same read
commits only about the output rows (the control: growth follows the number of signals in the file, not our code).
Run: PYTHONUTF8=1 python src/c5_diag_mne_commit_test.py
"""
import sys
import tempfile
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
import c5_diag_mne_commit as D   # noqa: E402


def write_edf(path, n_sig, hours, fs=512):
    n_rec = int(hours * 3600)
    labels = ["EEG Fp1", "EEG F7"] + [f"EEG X{i:02d}" for i in range(n_sig - 2)]

    def f(v, w):
        return str(v)[:w].ljust(w).encode("ascii")
    hdr = (f("0", 8) + f("X X X X", 80) + f("Startdate X X X X", 80) + f("01.01.01", 8) + f("00.00.00", 8)
           + f(256 * (n_sig + 1), 8) + f("", 44) + f(n_rec, 8) + f(1, 8) + f(n_sig, 4))
    for w, vals in ((16, labels), (80, [""] * n_sig), (8, ["uV"] * n_sig), (8, ["-3276.8"] * n_sig),
                    (8, ["3276.7"] * n_sig), (8, ["-32768"] * n_sig), (8, ["32767"] * n_sig), (80, [""] * n_sig),
                    (8, [fs] * n_sig), (32, [""] * n_sig)):
        hdr += b"".join(f(v, w) for v in vals)
    rng = np.random.default_rng(0)
    with open(path, "wb") as fh:
        fh.write(hdr)
        for k in range(0, n_rec, 600):
            m = min(600, n_rec - k)
            fh.write(rng.integers(-2000, 2000, size=(m, n_sig, fs), dtype=np.int16).tobytes())


def main():
    ok = True
    with tempfile.TemporaryDirectory() as d:
        for n_sig, hours, expect_h1 in ((49, 2.0, True), (2, 2.0, False)):
            p = Path(d) / f"syn_{n_sig}.edf"
            write_edf(p, n_sig, hours)
            r = D.run(p, block_s=600, max_gb=4.0, out=Path(d) / "out.json")
            g = r["whole"]["commit_growth_mb"]
            pw = r["predicted_if_H1"]["whole_mb"]
            rows = r["predicted_if_H1"]["rows_only_mb"]
            c1 = r["equal_bit_for_bit"]
            c2 = (abs(g - pw) < 0.15 * pw) if expect_h1 else (g < 1.6 * rows)
            print(f"TEST {n_sig} signals: equal {c1}; commit growth {g} MB (all-signal buffer {pw}, rows {rows}) "
                  f"-> {'PASS' if c1 and c2 else 'FAIL'}")
            ok &= c1 and c2
            p.unlink()
    print("ALL PASS" if ok else "FAIL")
    sys.exit(0 if ok else 1)


if __name__ == "__main__":
    main()
