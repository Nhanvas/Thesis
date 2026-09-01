#!/usr/bin/env python
"""
build_seizure_blocks.py — map each row of {subj}_ictal.npy back to its seizure.

Reuses src/dataprep/preprocessing.py directly (parse_summary / open_edf / build_labels /
WIN_S / WIN_SAMPLES / FS) so window indexing is IDENTICAL to how the arrays were written.
Checkpoint-independent. No thresholds, no labels, no tuning.

Hard gates:
  - rows mapped per subject MUST equal len({subj}_ictal.npy)
  - TEST seizures registered MUST equal 76 (RoR S3)

Usage (from repo ROOT):
  python src/build_seizure_blocks.py \
    --edf_root "F:/Study/Thesis/Dataset/CHB-MIT" \
    --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary"
"""
import argparse, csv, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if p.is_dir() and str(p) not in sys.path:
        sys.path.insert(0, str(p))

import numpy as np
import preprocessing as pp

TEST_SUBJ = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VAL_SUBJ  = ["chb10", "chb11", "chb22"]
EXPECTED_TEST_SEIZURES = 76          # RoR S3


def die(m):
    print(f"\n[FATAL] {m}\n", file=sys.stderr)
    sys.exit(1)


def resolve_summary(summary_dir: Path, subj: str) -> Path:
    """On-disk summaries are .md; preprocessing.py referenced .txt. Accept either."""
    for ext in (".txt", ".md"):
        f = summary_dir / f"{subj}-summary{ext}"
        if f.is_file():
            return f
    die(f"summary not found for {subj} (tried .txt/.md) in {summary_dir}")


def blocks_for_subject(subj: str, edf_root: Path, summary_dir: Path):
    seizure_map = pp.parse_summary(resolve_summary(summary_dir, subj))
    n_sz_in_summary = sum(len(v) for v in seizure_map.values())

    subj_dir = edf_root / subj
    if not subj_dir.is_dir():
        die(f"EDF dir not found: {subj_dir}")

    registry, rows, skipped = [], [], []
    idx = 0
    for edf_path in sorted(subj_dir.glob("*.edf")):
        raw = pp.open_edf(edf_path)
        if raw is None:
            skipped.append(edf_path.name)
            continue
        seizure_list = seizure_map.get(edf_path.name, [])
        n_samples = int(raw.n_times)
        n_seconds = n_samples // pp.FS
        n_windows = n_samples // pp.WIN_SAMPLES
        labels = pp.build_labels(n_seconds, seizure_list)

        local = []
        for (on, off) in sorted(seizure_list):
            registry.append({"edf": edf_path.name, "onset_s": on, "offset_s": off})
            local.append((len(registry) - 1, on, off))

        for i in range(n_windows):
            s0, s1 = i * pp.WIN_S, i * pp.WIN_S + pp.WIN_S
            if int(labels[s0:s1].max()) == 1:
                best, bov = None, -1
                for gid, on, off in local:
                    ov = max(0, min(s1, off) - max(s0, on))
                    if ov > bov:
                        bov, best = ov, gid
                rows.append({"row": idx, "edf": edf_path.name, "win_i": i,
                             "start_s": s0, "sz": best, "overlap_s": bov})
                idx += 1
        del raw
    return rows, registry, n_sz_in_summary, skipped


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--edf_root", required=True,
                    help="dir containing chb03/, chb06/, ... subfolders of .edf")
    ap.add_argument("--summary_dir", required=True,
                    help="dir containing chb03-summary.md (or .txt), ...")
    ap.add_argument("--proc_dir", default=str(ROOT / "data" / "processed"))
    ap.add_argument("--out_dir", default=str(ROOT / "results" / "attribution_v6"))
    a = ap.parse_args()

    edf_root, summary_dir, proc = Path(a.edf_root), Path(a.summary_dir), Path(a.proc_dir)
    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    for d, nm in [(edf_root, "edf_root"), (summary_dir, "summary_dir"), (proc, "proc_dir")]:
        if not d.is_dir():
            die(f"{nm} not found: {d}")

    blocks, rowmap, fails, n_test_sz = [], [], [], 0
    for subj in TEST_SUBJ + VAL_SUBJ:
        rows, registry, n_summary, skipped = blocks_for_subject(subj, edf_root, summary_dir)
        arr = proc / f"{subj}_ictal.npy"
        if not arr.is_file():
            die(f"missing {arr}")
        n_arr = int(np.load(arr, mmap_mode="r").shape[0])

        status = "OK" if len(rows) == n_arr else "MISMATCH"
        if status == "MISMATCH":
            fails.append(f"{subj}: mapped {len(rows)} rows vs array {n_arr}")
        if len(registry) != n_summary:
            fails.append(f"{subj}: {n_summary - len(registry)} seizure(s) lost in "
                         f"skipped EDFs {skipped}")

        by_sz = {}
        for r in rows:
            by_sz.setdefault(r["sz"], []).append(r["row"])
        empty = [g for g in range(len(registry)) if g not in by_sz]

        for g, meta in enumerate(registry):
            rr = sorted(by_sz.get(g, []))
            contig = bool(rr) and (rr[-1] - rr[0] + 1 == len(rr))
            blocks.append({"subject": subj, "seizure_idx": g, "edf_file": meta["edf"],
                           "onset_s": meta["onset_s"], "offset_s": meta["offset_s"],
                           "dur_s": meta["offset_s"] - meta["onset_s"],
                           "n_windows": len(rr),
                           "row_start": rr[0] if rr else -1,
                           "row_end": rr[-1] if rr else -1,
                           "contiguous": contig})
        for r in rows:
            rowmap.append({"subject": subj, "row": r["row"], "seizure_idx": r["sz"],
                           "edf_file": r["edf"], "start_s": r["start_s"],
                           "overlap_s": r["overlap_s"]})

        if subj in TEST_SUBJ:
            n_test_sz += len(registry)
        print(f"  {subj:<7} seizures={len(registry):>2} (summary {n_summary:>2})  "
              f"rows mapped={len(rows):>5} / array={n_arr:<5} [{status}]"
              + (f"  EMPTY_SZ={empty}" if empty else "")
              + (f"  SKIPPED_EDF={len(skipped)}" if skipped else ""))

    def write(fn, data):
        if not data:
            die(f"no data for {fn}")
        with open(out / fn, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(data[0].keys()))
            w.writeheader(); w.writerows(data)
        print(f"wrote {out / fn}  ({len(data)} rows)")

    write("seizure_blocks.csv", blocks)
    write("ictal_row_to_seizure.csv", rowmap)

    nw = [b["n_windows"] for b in blocks if b["subject"] in TEST_SUBJ]
    print(f"\nTEST seizures registered = {n_test_sz} (RoR S3 expects {EXPECTED_TEST_SEIZURES})")
    print(f"TEST windows/seizure: min={min(nw)} p25={int(np.percentile(nw,25))} "
          f"median={int(np.median(nw))} max={max(nw)}  |  n_sz with <3 windows = "
          f"{sum(1 for v in nw if v < 3)}")
    if n_test_sz != EXPECTED_TEST_SEIZURES:
        fails.append(f"TEST seizure count {n_test_sz} != {EXPECTED_TEST_SEIZURES}")
    if fails:
        die("GATE FAILED:\n  " + "\n  ".join(fails))
    print("GATE PASSED — row->seizure map is exact.")


if __name__ == "__main__":
    main()