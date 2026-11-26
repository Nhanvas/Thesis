#!/usr/bin/env python
"""
c5_gates_from_log.py -- chat C5b: the Step 2 gate outputs rebuilt from the log of the full run (25-26/11).

The full run of src/c5_step2_gates.py (commit 17b86fc) printed every G1 and G3-G6 row as it finished, then stopped in
the hospital part (private memory 11,152 MB; diagnosis src/c5_diag_edfplus.py) before writing any output, because the
script wrote its files only at the end. The printed rows are the dictionaries the script would have written. This
script parses them from the log and writes g1.csv, siena.csv, gates.json and GATES.md with the gate script's own writer
(write_outputs), adding a note that the files were rebuilt from the log. Checks before writing (STOP otherwise): the 8
test subjects of TEST exactly once each; the 41 Siena files of the PhysioNet SHA256 list exactly once each.
Run: PYTHONUTF8=1 python src/c5_gates_from_log.py --log ../Agent/inbox/C5_STEP2_GATES.log --commit 17b86fc
"""
import argparse
import ast
import re
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))


def parse(text):
    def rows(prefix):
        out = []
        for m in re.finditer(prefix + r"[^:]*: (\{[^{}]*\})", text):
            out.append(ast.literal_eval(re.sub(r"\s*\n\s*", " ", m.group(1))))
        return out
    return rows(r"G1 chb\d\d"), rows(r"G3-G6 ")


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--log", required=True)
    ap.add_argument("--commit", required=True)
    a = ap.parse_args()
    import c5_step2_gates as G
    text = Path(a.log).read_text(encoding="utf-8", errors="replace")
    g1rows, srows = parse(text)
    subj = [r["subject"] for r in g1rows]
    if sorted(subj) != sorted(G.TEST):
        raise SystemExit(f"STOP: G1 rows {subj} are not the 8 test subjects once each")
    listed = sorted(line.split()[1].lstrip("*").removeprefix("./").split("/")[-1]
                    for line in G.SIENA_SUMS.read_text().splitlines() if line.strip().endswith(".edf"))
    got = sorted(r["file"] for r in srows)
    if got != listed:
        raise SystemExit(f"STOP: Siena rows ({len(got)}) are not the {len(listed)} listed files once each")
    G.OUT.mkdir(parents=True, exist_ok=True)
    gates = G.write_outputs(G.OUT, g1rows, srows, smoke=False, commit=a.commit,
                            note="Rebuilt from the run log by `src/c5_gates_from_log.py` (the run stopped in the "
                                 "hospital part before writing; every row below was printed by the run itself).")
    print(f"rebuilt from the log: {len(g1rows)} G1 subjects, {len(srows)} Siena files; "
          + ", ".join(f"{k} {'PASS' if v['PASS'] else 'FAIL'}" for k, v in gates.items() if "PASS" in v))


if __name__ == "__main__":
    main()
