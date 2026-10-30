#!/usr/bin/env python
"""
v9_x3_build_folds.py -- V9-X3 prep (docs/prompts/V9_X3_CV_PREP.md), step 2: 4-fold stratified
group k-fold over all 23 CHB-MIT subjects (24 cases; chb01 and chb21 are the same subject,
always in the same fold -- one group of 2 cases).

Rule (pre-registered, fixed): count annotated seizures per group from the CHB-MIT summary files,
same file-skip rule as the thesis (chb12_27/28/29 excluded -- missing a common channel, never in
any committed array: docs/PROJECT_INSTRUCTIONS.md); sort groups by seizure count descending, ties
by case id ascending; serpentine assignment to folds 1,2,3,4,4,3,2,1,1,2,...
Seizure counts read directly from data/summaries/*-summary.txt (chb01..chb20, chb22, chb23) and,
for chb24 (not part of the original 23-subject split, no file under data/summaries/), directly
from F:/Study/Thesis/Dataset/CHB-MIT/chb24/chb24-summary.txt -- same parser
(evaluation_protocol.parse_summary_edf_list), read-only, no file written outside results/v9_x3/.
No model output is read; this step uses annotation metadata only.

Output: results/v9_x3/folds.json (rule, counts, assignment, git commit hash of HEAD at write time).
Commit it (with this script) BEFORE any training, per the prompt's rule.
Run:  python src/v9_x3_build_folds.py
"""
import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src", ROOT / "src" / "dataprep"):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))
import preprocessing as P         # noqa: E402

SUMMARY_DIR = ROOT / "data" / "summaries"
CHB24_SUMMARY = Path("F:/Study/Thesis/Dataset/CHB-MIT/chb24/chb24-summary.txt")
CHB_RAW_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
OUT = ROOT / "results" / "v9_x3"
SKIP_FILES = {"chb12_27.edf", "chb12_28.edf", "chb12_29.edf"}
SUBJECTS_23 = [f"chb{i:02d}" for i in range(1, 24)]     # chb01..chb23
N_FOLDS = 4


def seizure_count(subj):
    """preprocessing.parse_summary (index-agnostic on Start/End Time lines; the only parser that
    tolerates chb24-summary.txt's different header -- no File Start/End Time fields, unlike every
    other subject -- which made evaluation_protocol.parse_summary_edf_list silently return 0 files
    for chb24 on a first attempt; x1_external.py's chb_subject() uses this same parser for chb24,
    for the same reason), restricted to EDF files actually present (same glob convention as
    continuous_eval.list_files / preprocessing.process_subject)."""
    path = SUMMARY_DIR / f"{subj}-summary.txt" if subj != "chb24" else CHB24_SUMMARY
    sz = P.parse_summary(path)
    present = {p.name for p in (CHB_RAW_DIR / subj).glob("*.edf")}
    n = 0
    skipped_seizures = 0
    for fname, seizures in sz.items():
        if fname not in present:
            continue
        if fname in SKIP_FILES:
            skipped_seizures += len(seizures)
            continue
        n += len(seizures)
    return n, skipped_seizures


def main():
    counts = {}
    skipped_report = {}
    for s in SUBJECTS_23 + ["chb24"]:
        n, skipped = seizure_count(s)
        counts[s] = n
        if skipped:
            skipped_report[s] = skipped
    print("per-case seizure counts (file-skip rule applied):")
    for s in SUBJECTS_23 + ["chb24"]:
        tag = f"  (excludes {skipped_report[s]} in skipped files)" if s in skipped_report else ""
        print(f"  {s}: {counts[s]}{tag}")

    # groups: chb01+chb21 merged (same subject); every other case is its own group
    groups = []
    seen = set()
    for s in SUBJECTS_23 + ["chb24"]:
        if s in seen:
            continue
        if s == "chb01":
            cases = ["chb01", "chb21"]
            seen.update(cases)
            gcount = counts["chb01"] + counts["chb21"]
            gid = "chb01"
        elif s == "chb21":
            continue  # handled with chb01
        else:
            cases = [s]
            seen.add(s)
            gcount = counts[s]
            gid = s
        groups.append(dict(group_id=gid, cases=cases, seizures=gcount))

    # sort by seizure count descending, ties by case id (group_id) ascending
    groups.sort(key=lambda g: (-g["seizures"], g["group_id"]))

    # serpentine assignment to folds 1..4: 1,2,3,4,4,3,2,1,1,2,3,4,4,3,2,1,...
    pattern = list(range(1, N_FOLDS + 1)) + list(range(N_FOLDS, 0, -1))
    fold_of_group = {}
    for i, g in enumerate(groups):
        fold_of_group[g["group_id"]] = pattern[i % len(pattern)]

    folds = {k: [] for k in range(1, N_FOLDS + 1)}
    for g in groups:
        folds[fold_of_group[g["group_id"]]].append(g)

    print("\nfold assignment (serpentine order over seizure-count-sorted groups):")
    for k in range(1, N_FOLDS + 1):
        total = sum(g["seizures"] for g in folds[k])
        gids = [g["group_id"] for g in folds[k]]
        ncases = sum(len(g["cases"]) for g in folds[k])
        print(f"  fold {k}: {gids} ({total} seizures, {ncases} cases)")

    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:
        commit = None

    payload = dict(
        rule="stratified group k-fold, 4 folds; unit = subject (chb01+chb21 merged); groups sorted "
             "by annotated seizure count descending (ties by case id ascending), serpentine "
             "assignment 1,2,3,4,4,3,2,1,1,2,...; seizure counts from the CHB-MIT summary files, "
             "chb12_27/28/29 excluded (missing a common channel, never in any committed array)",
        seizure_counts=counts,
        skipped_files=sorted(SKIP_FILES),
        groups=groups,
        folds={str(k): folds[k] for k in folds},
        git_commit_at_write=commit,
    )
    OUT.mkdir(parents=True, exist_ok=True)
    (OUT / "folds.json").write_text(json.dumps(payload, indent=1))
    print(f"\nwrote {OUT / 'folds.json'}")


if __name__ == "__main__":
    main()
