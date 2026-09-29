#!/usr/bin/env python
"""
eval_application_events.py -- scores the SzScan web demo APPLICATION's own exported AI
detections against the seizure annotation, using the SAME SzCORE event-scoring call and
parameters as szcore_eval.py (`SZ_PARAM`, `score_szcore` -- imported, never retyped), and
the same summary-file parser as evaluation_protocol.py (`parse_summary_edf_list`).

Why this file exists (CC_PROMPT_APP_EVAL_SCORER.md, owner: Project 1): the application
never reads the seizure annotation (web_demo/backend/tests/test_guards.py enforces this).
The comparison against ground truth happens here, entirely outside the application, on the
event intervals it already exported. This is a SEPARATE evaluation tier from the offline
one (szcore_eval.py / evaluation_protocol.py) and its numbers are never merged with those
(project instructions Sec.11.5):
  - every AI event counts, before review -- Human-sourced rows are dropped, review_status
    is ignored;
  - the false-alarm denominator is the recorded time of the PROCESSED files minus their
    seizure time -- not the background hours of the offline evaluation;
  - the run is one-shot: a defect found after scoring means the whole application run is
    repeated on a fixed build and rescored, never a single subject alone.

Writes only under results/application_eval/ (plus stdout). Never edits web_demo/, never
edits szcore_eval.py or evaluation_protocol.py (imports them read-only).

Usage
-----
  python src/eval_application_events.py --smoke   # Step 3: synthetic proof, writes nothing
                                                    # under results/application_eval/
  python src/eval_application_events.py            # Step 4: real run on
                                                    # web_demo/report_handback/tier2/*,
                                                    # writes results/application_eval/
"""
import argparse
import hashlib
import json
import re
import sys
import tempfile
from pathlib import Path

import numpy as np
import pandas as pd

# Explicit sys.path block -- same pattern as src/verify_provenance.py:20-23.
ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from evaluation_protocol import parse_summary_edf_list  # noqa: E402 -- reused, not retyped
from szcore_eval import SZ_PARAM, score_szcore  # noqa: E402 -- reused, not retyped

TEST_SUBJECTS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# Full test-set annotated-seizure count per subject (CC_PROMPT_APP_EVAL_SCORER.md Step 2:
# "the full test set holds 7, 10, 12, 8, 20, 10, 3, 6 (76 in total)"), for the coverage check.
EXPECTED_SEIZURES = {
    "chb03": 7, "chb06": 10, "chb13": 12, "chb14": 8,
    "chb15": 20, "chb16": 10, "chb17": 3, "chb18": 6,
}
EXPECTED_TOTAL_SEIZURES = sum(EXPECTED_SEIZURES.values())  # 76
EXPECTED_TOTAL_HOURS = 279.39  # report Table 2.1

DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = DATASET_DIR / "CHB info" / "summary"

DEFAULT_TIER2_DIR = ROOT / "web_demo" / "report_handback" / "tier2"
OUT_DIR = ROOT / "results" / "application_eval"
REPORT_HANDBACK = ROOT / "web_demo" / "REPORT_HANDBACK.md"

# Seconds per window (src/dataprep/preprocessing.py: FS=256, WIN_S=4, WIN_SAMPLES=FS*WIN_S=1024).
# L = n_windows * WIN_S is a file's length on the APPLICATION's own concatenated timeline
# (web_demo/backend/pipeline_demo.py process_subject_events(): "No window is ever dropped ...
# t_seconds = window_index * 4" per SZSCAN_SPEC_v5.md Sec.1.3) -- it can differ from the EDF
# header's duration_s by up to WIN_S seconds (n_windows is a floor-division window count).
# Event onset/offset boundary checks (CC_PROMPT_SCORER_BOUNDARY.md) use L, not duration_s;
# duration_s remains the unit for seizure time and the false-alarm-per-day denominator.
WIN_S = 4
# FS(256) * WIN_S(4). Only used to fill the required n_windows column of a synthetic files.csv
# (Step 3 smoke tests); never used in the scoring math itself.
WIN_SAMPLES = 1024

REQUIRED_EVENT_COLS = ["subject", "file_name", "event_id", "onset_s", "offset_s", "source", "review_status"]
REQUIRED_FILE_COLS = ["subject", "file_name", "duration_s", "n_windows", "status"]
OK_STATUSES = {"success", "ok", "done"}

# A real calendar date (year-month-day) must never appear in an export -- SzScan's own
# anonymization-shifted meas_date rule (SZSCAN_SPEC_v5.md Sec.0; project instructions Sec.11.5
# item 5). onset_s/offset_s/duration_s are plain numbers, so this only fires on an actual
# embedded date string.
CALENDAR_DATE_RE = re.compile(r"\b(19|20)\d{2}[-/](0[1-9]|1[0-2])[-/](0[1-9]|[12]\d|3[01])\b")


class ScorerInputError(Exception):
    """Fail-fast on a malformed export. The message is meant to be read directly."""


# ---------------------------------------------------------------------------------------
# Annotation (reads the .md summary -- CLAUDE.md: `.md`, not `.txt`)
# ---------------------------------------------------------------------------------------
def load_annotation(subject: str) -> dict:
    """{file_name: {'duration_s': int, 'seizures': [(onset_s, offset_s), ...]}} for one
    subject, straight from evaluation_protocol.parse_summary_edf_list (reused, not retyped).
    All times are file-relative seconds."""
    edfs = parse_summary_edf_list(SUMMARY_DIR / f"{subject}-summary.md")
    return {e["fname"]: {"duration_s": e["duration_s"], "seizures": e["seizures"]} for e in edfs}


# ---------------------------------------------------------------------------------------
# Fail-fast export validation
# ---------------------------------------------------------------------------------------
def _check_no_calendar_date(path: Path) -> None:
    text = path.read_text()
    m = CALENDAR_DATE_RE.search(text)
    if m:
        raise ScorerInputError(f"{path}: looks like a calendar date ({m.group(0)!r}) in the export.")


def _check_test_subjects(df: pd.DataFrame, path: Path) -> None:
    bad = sorted(set(df["subject"]) - set(TEST_SUBJECTS))
    if bad:
        raise ScorerInputError(f"{path}: subject(s) outside the 8 test subjects: {bad}.")


def load_files_csv(path: Path) -> pd.DataFrame:
    if not path.exists():
        raise ScorerInputError(f"{path} does not exist.")
    _check_no_calendar_date(path)
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_FILE_COLS if c not in df.columns]
    if missing:
        raise ScorerInputError(f"{path}: missing column(s) {missing}.")
    _check_test_subjects(df, path)
    dupes = df[df.duplicated(["subject", "file_name"], keep=False)]
    if len(dupes):
        raise ScorerInputError(f"{path}: duplicate (subject, file_name) rows: "
                                f"{sorted(set(zip(dupes['subject'], dupes['file_name'])))}.")
    return df


def load_events_csv(path: Path, files_df: pd.DataFrame) -> pd.DataFrame:
    if not path.exists():
        raise ScorerInputError(f"{path} does not exist.")
    _check_no_calendar_date(path)
    df = pd.read_csv(path)
    missing = [c for c in REQUIRED_EVENT_COLS if c not in df.columns]
    if missing:
        raise ScorerInputError(f"{path}: missing column(s) {missing}.")
    if len(df) == 0:
        return df
    _check_test_subjects(df, path)
    bad_span = df[df["offset_s"] <= df["onset_s"]]
    if len(bad_span):
        raise ScorerInputError(
            f"{path}: offset_s <= onset_s for event_id(s) {list(bad_span['event_id'])}."
        )
    L_by_key = (files_df.set_index(["subject", "file_name"])["n_windows"] * WIN_S)
    order_by_subject = {
        s: sorted(files_df.loc[files_df["subject"] == s, "file_name"])
        for s in files_df["subject"].unique()
    }
    for row in df.itertuples():
        fk = (row.subject, row.file_name)
        if fk not in L_by_key.index:
            raise ScorerInputError(
                f"{path}: file_name {row.file_name!r} (subject {row.subject}) is absent from files.csv."
            )
        L = L_by_key.loc[fk]
        if not (0 <= row.onset_s < L):
            raise ScorerInputError(
                f"{path}: event_id {row.event_id} in {row.file_name} has onset_s={row.onset_s} "
                f"outside [0, {L}) -- L = n_windows * {WIN_S} for that file."
            )
        if row.offset_s > L:
            # PELT runs once per subject on all files concatenated in sorted file-name order
            # with no gap (web_demo/backend/pipeline_demo.py process_subject_events()), so an
            # event's offset can legitimately continue past L into the next file -- but only
            # if a next file exists; the last file of a subject cannot overflow
            # (CC_PROMPT_SCORER_BOUNDARY.md Background). The actual split happens later, in
            # split_boundary_events() -- this is a fail-fast check only.
            order = order_by_subject[row.subject]
            if order.index(row.file_name) + 1 >= len(order):
                raise ScorerInputError(
                    f"{path}: event_id {row.event_id} in {row.file_name} has offset_s="
                    f"{row.offset_s} > L={L}, but {row.file_name} is {row.subject}'s last file "
                    f"(sorted file-name order) -- an event cannot overflow past the end of a "
                    f"subject's recording."
                )
    return df


def check_files_known_to_annotation(files_df: pd.DataFrame, annotation_by_subject: dict) -> None:
    """Before any scoring: every (subject, file_name) in files.csv must be a real file name in
    that subject's annotation (the same 'fname' keys load_annotation() returns from
    evaluation_protocol.parse_summary_edf_list). If it isn't, score_exports() would silently
    treat that file as seizure-free (ref_iv=[]) -- its real seizures vanish and any AI event in
    it is counted as a false alarm, and the shortfall would only surface afterwards, in the
    coverage check. Fail fast here instead, naming every missing (subject, file_name) plus the
    first three names the summary DOES have for that subject, so a format mismatch (e.g. a
    missing '.edf' extension) is obvious immediately."""
    missing = [(s, f) for s, f in zip(files_df["subject"], files_df["file_name"])
              if f not in annotation_by_subject.get(s, {})]
    if not missing:
        return
    missing_subjects = sorted({s for s, _ in missing})
    lines = [f"  {s}/{f!r}" for s, f in missing]
    sample_lines = [
        f"  {s}: first 3 names the summary has: "
        f"{sorted(annotation_by_subject.get(s, {}).keys())[:3]}"
        for s in missing_subjects
    ]
    raise ScorerInputError(
        "files.csv names file(s) absent from the annotation -- their seizures would silently "
        "vanish and any AI event in them would be counted as a false alarm:\n"
        + "\n".join(lines) + "\n" + "\n".join(sample_lines)
    )


def split_boundary_events(events_df: pd.DataFrame, files_df: pd.DataFrame):
    """Before any scoring: an AI event's offset_s can exceed its own file's length
    L = n_windows * WIN_S when the underlying change-point interval continues into the next
    file -- the application runs PELT once per subject, on all files concatenated in sorted
    file-name order with no gap (web_demo/backend/pipeline_demo.py process_subject_events()).

    Matching that same convention (CC_PROMPT_SCORER_BOUNDARY.md Step 1: the offline evaluation,
    szcore_eval.py build_timeline_masked()/evaluate_subject(), scores one concatenated
    per-subject timeline too, never per file), the overflow is SPLIT: the file that held the
    event keeps [onset_s, L) and the remainder [0, offset_s - L) is carried to the START of the
    next file in sorted file-name order -- repeated if that also overflows. Only `source=="AI"`
    rows are split (reference seizures never cross a file boundary; Human rows are dropped
    before scoring and never reach this function's caller in a way that matters). `onset_s` is
    already guaranteed in [0, L) and a next file is already guaranteed to exist whenever
    offset_s > L, by load_events_csv()'s own fail-fast checks -- this function re-derives L and
    file order itself rather than trusting that invariant blindly, so it still raises
    ScorerInputError (not, say, an IndexError) if it somehow doesn't hold.

    Returns (split_events_df, boundary_stats), boundary_stats = {subject: {"n_crossed": int,
    "seconds_moved": float}} -- n_crossed counts ORIGINAL events that crossed at least one
    boundary (an event carried across two boundaries counts once), seconds_moved sums every
    segment's carried length.
    """
    L_by_key = {(r.subject, r.file_name): int(r.n_windows) * WIN_S for r in files_df.itertuples()}
    order_by_subject = {
        s: sorted(files_df.loc[files_df["subject"] == s, "file_name"])
        for s in files_df["subject"].unique()
    }
    boundary_stats = {s: dict(n_crossed=0, seconds_moved=0.0) for s in files_df["subject"].unique()}

    if len(events_df) == 0:
        return events_df, boundary_stats

    out_rows = []
    for row in events_df.itertuples(index=False):
        d = row._asdict()
        if d["source"] != "AI":
            out_rows.append(d)
            continue
        subject, fname = d["subject"], d["file_name"]
        onset, offset = float(d["onset_s"]), float(d["offset_s"])
        order = order_by_subject[subject]
        idx = order.index(fname)
        crossed_this_event = False
        while True:
            L = L_by_key[(subject, fname)]
            if offset <= L:
                piece = dict(d, file_name=fname, onset_s=onset, offset_s=offset)
                out_rows.append(piece)
                break
            if idx + 1 >= len(order):
                raise ScorerInputError(
                    f"event_id {d['event_id']} in {subject}/{fname}: offset_s={offset:g} > "
                    f"L={L:g} but {fname} is {subject}'s last file (sorted file-name order) -- "
                    f"cannot carry the overflow to a next file."
                )
            out_rows.append(dict(d, file_name=fname, onset_s=onset, offset_s=float(L)))
            moved = offset - L
            boundary_stats[subject]["seconds_moved"] += moved
            if not crossed_this_event:
                boundary_stats[subject]["n_crossed"] += 1
                crossed_this_event = True
            idx += 1
            fname = order[idx]
            onset, offset = 0.0, moved

    return pd.DataFrame(out_rows, columns=events_df.columns), boundary_stats


# ---------------------------------------------------------------------------------------
# Scoring -- per file via szcore_eval.score_szcore (SZ_PARAM imported, not retyped),
# accumulated per subject and pooled per CC_PROMPT_APP_EVAL_SCORER.md's own formulas.
# ---------------------------------------------------------------------------------------
def _score_from_counts(tp: int, fp: int, n_ref: int, duration_s: float, seizure_s: float) -> dict:
    precision = (tp / (tp + fp)) if (tp + fp) > 0 else 0.0
    sensitivity = (tp / n_ref) if n_ref > 0 else 0.0
    # "When precision and sensitivity are both zero, F1 is 'undefined', not 0."
    if precision == 0.0 and sensitivity == 0.0:
        f1 = "undefined"
    else:
        f1 = 2 * precision * sensitivity / (precision + sensitivity)
    denom_days = (duration_s - seizure_s) / 86400.0
    false_alarms_per_day = (fp / denom_days) if denom_days > 0 else "undefined"
    return dict(
        seizures=n_ref, detected=tp, false_alarms=fp,
        sensitivity=sensitivity, precision=precision, f1=f1,
        false_alarms_per_day=false_alarms_per_day,
    )


def score_exports(events_df: pd.DataFrame, files_df: pd.DataFrame, annotation_by_subject: dict):
    """Per-file scoring: reference = that file's annotated seizures (file-relative seconds),
    hypothesis = that file's AI events (source == 'AI' only; review_status ignored). TP/FP/
    n_ref are accumulated per subject and pooled; sensitivity/precision/F1/FP-per-day are
    computed from the ACCUMULATED counts, not averaged per file."""
    if len(events_df):
        ai = events_df[events_df["source"] == "AI"].copy()
    else:
        ai = events_df

    subjects = list(files_df["subject"].unique())
    acc = {s: dict(tp=0, fp=0, n_ref=0, duration_s=0.0, seizure_s=0.0, files=0) for s in subjects}

    for frow in files_df.itertuples():
        subject, fname, dur = frow.subject, frow.file_name, float(frow.duration_s)
        ann = annotation_by_subject.get(subject, {}).get(fname)
        ref_iv = list(ann["seizures"]) if ann is not None else []
        seiz_s = sum(off - on for on, off in ref_iv)
        if len(ai):
            hyp_rows = ai[(ai["subject"] == subject) & (ai["file_name"] == fname)]
            hyp_iv = [(float(r.onset_s), float(r.offset_s)) for r in hyp_rows.itertuples()]
        else:
            hyp_iv = []
        sc = score_szcore(ref_iv, hyp_iv, total_dur_s=dur,
                          n_inter_h=max(dur - seiz_s, 0.0) / 3600.0)
        a = acc[subject]
        a["tp"] += sc["tp"]
        a["fp"] += sc["fp"]
        a["n_ref"] += sc["n_ref"]
        a["duration_s"] += dur
        a["seizure_s"] += seiz_s
        a["files"] += 1

    per_subject_rows = []
    pooled_acc = dict(tp=0, fp=0, n_ref=0, duration_s=0.0, seizure_s=0.0, files=0)
    for subject in [s for s in TEST_SUBJECTS if s in acc]:
        a = acc[subject]
        row = dict(subject=subject, files=a["files"], hours=round(a["duration_s"] / 3600.0, 4))
        row.update(_score_from_counts(a["tp"], a["fp"], a["n_ref"], a["duration_s"], a["seizure_s"]))
        per_subject_rows.append(row)
        for k in pooled_acc:
            pooled_acc[k] += a[k]

    pooled_row = dict(files=pooled_acc["files"], hours=round(pooled_acc["duration_s"] / 3600.0, 4))
    pooled_row.update(_score_from_counts(pooled_acc["tp"], pooled_acc["fp"], pooled_acc["n_ref"],
                                         pooled_acc["duration_s"], pooled_acc["seizure_s"]))
    return per_subject_rows, pooled_row


# ---------------------------------------------------------------------------------------
# Coverage checks
# ---------------------------------------------------------------------------------------
def coverage_checks(files_df: pd.DataFrame, annotation_by_subject: dict):
    lines, issues = [], []
    subjects = [s for s in TEST_SUBJECTS if s in set(files_df["subject"])]

    if set(TEST_SUBJECTS) - set(subjects):
        issues.append(f"Subjects entirely absent from files.csv: "
                      f"{sorted(set(TEST_SUBJECTS) - set(subjects))}")

    for subject in subjects:
        disk_files = sorted(p.name for p in (DATASET_DIR / subject).glob("*.edf"))
        csv_files = set(files_df.loc[files_df["subject"] == subject, "file_name"])
        missing = [f for f in disk_files if f not in csv_files]
        if missing:
            issues.append(f"{subject}: {len(missing)} EDF(s) on disk not processed (absent from "
                          f"files.csv): {missing}")
        bad_status = files_df[(files_df["subject"] == subject) & (~files_df["status"].isin(OK_STATUSES))]
        for r in bad_status.itertuples():
            issues.append(f"{subject}/{r.file_name}: status={r.status!r} (not in {sorted(OK_STATUSES)})")
        lines.append(f"{subject}: {len(disk_files)} EDF(s) on disk, {len(csv_files)} in files.csv, "
                     f"{len(missing)} not processed, {len(bad_status)} non-success status")

    total_seizures_processed = 0
    for subject in subjects:
        ann = annotation_by_subject.get(subject, {})
        processed = set(files_df.loc[files_df["subject"] == subject, "file_name"])
        processed_seizures = sum(len(v["seizures"]) for k, v in ann.items() if k in processed)
        total_seizures_processed += processed_seizures
        expected = EXPECTED_SEIZURES.get(subject)
        line = f"{subject}: {processed_seizures}"
        if expected is not None:
            line += f"/{expected}"
            if processed_seizures < expected:
                missing_files = sorted(k for k, v in ann.items()
                                       if k not in processed and v["seizures"])
                issues.append(
                    f"{subject}: {processed_seizures}/{expected} annotated seizures in processed "
                    f"files -- shortfall traced to unprocessed file(s) with seizures: {missing_files}"
                )
        line += " annotated seizures in processed files"
        lines.append(line)
    lines.append(f"Total annotated seizures in processed files: {total_seizures_processed}"
                 f"/{EXPECTED_TOTAL_SEIZURES if set(subjects) == set(TEST_SUBJECTS) else 'n/a (partial subject set)'}")

    total_hours = files_df["duration_s"].sum() / 3600.0
    lines.append(f"Total processed hours: {total_hours:.2f} vs {EXPECTED_TOTAL_HOURS} "
                 f"(report Table 2.1), delta {total_hours - EXPECTED_TOTAL_HOURS:+.2f} h")

    return lines, issues


# ---------------------------------------------------------------------------------------
# Orchestration
# ---------------------------------------------------------------------------------------
def discover_export_paths(tier2_dir: Path):
    files_csv = tier2_dir / "files.csv"
    event_csvs = sorted(tier2_dir.glob("*_events.csv"))
    return files_csv, event_csvs


def extract_app_commit() -> str | None:
    if not REPORT_HANDBACK.exists():
        return None
    m = re.search(r"\*\*Commit:\*\*\s*`([0-9a-f]{7,40})`", REPORT_HANDBACK.read_text())
    return m.group(1) if m else None


def build_summary_md(per_subject_rows, pooled_row, boundary_lines, coverage_lines, coverage_issues,
                     input_hashes: dict, app_commit: str | None) -> str:
    lines = ["# Application-detection scoring -- SUMMARY", ""]
    lines.append("Scores the SzScan web demo application's own exported AI detections against the "
                 "seizure annotation. A separate evaluation tier; never merged with the offline "
                 "numbers (project instructions Sec.11.5).")
    lines.append("")
    if app_commit:
        lines.append(f"Application build commit (from `web_demo/REPORT_HANDBACK.md`): `{app_commit}`")
    else:
        lines.append("Application build commit: not stated in `web_demo/REPORT_HANDBACK.md`.")
    lines.append("")
    lines.append("## Per-subject")
    lines.append("")
    df = pd.DataFrame(per_subject_rows)
    if len(df):
        lines.append("```")
        lines.append(df.to_string(index=False))
        lines.append("```")
    else:
        lines.append("(no subjects)")
    lines.append("")
    lines.append("## Pooled (all subjects)")
    lines.append("")
    for k, v in pooled_row.items():
        lines.append(f"- {k}: {v}")
    lines.append("")
    lines.append("## Boundary-crossing events")
    lines.append("")
    lines.append("Events split across a file boundary (CC_PROMPT_SCORER_BOUNDARY.md): the part "
                 "beyond L = n_windows * 4 s of a file is carried to the start of the next file "
                 "in sorted file-name order, matching the offline evaluation's own concatenated "
                 "per-subject timeline (szcore_eval.py).")
    lines.append("")
    for l in boundary_lines:
        lines.append(f"- {l}")
    lines.append("")
    lines.append("## Coverage checks")
    lines.append("")
    for l in coverage_lines:
        lines.append(f"- {l}")
    lines.append("")
    lines.append("## Coverage issues")
    lines.append("")
    if coverage_issues:
        for i in coverage_issues:
            lines.append(f"- **{i}**")
    else:
        lines.append("- none found")
    lines.append("")
    lines.append("## Input file hashes (sha256)")
    lines.append("")
    for name, h in sorted(input_hashes.items()):
        lines.append(f"- `{name}`: `{h}`")
    lines.append("")
    return "\n".join(lines)


def run_eval(tier2_dir: Path, out_dir: Path | None, label: str) -> dict:
    """Core entry point for both the real run (Step 4, out_dir=results/application_eval)
    and the smoke tests (Step 3, out_dir=None -- print only, no filesystem writes)."""
    files_csv_path, event_csv_paths = discover_export_paths(tier2_dir)
    if not files_csv_path.exists():
        raise ScorerInputError(f"{files_csv_path} does not exist.")
    files_df = load_files_csv(files_csv_path)
    if not event_csv_paths:
        raise ScorerInputError(f"No *_events.csv found under {tier2_dir}.")
    events_df = pd.concat([load_events_csv(p, files_df) for p in event_csv_paths], ignore_index=True)

    annotation_by_subject = {s: load_annotation(s) for s in files_df["subject"].unique()}
    check_files_known_to_annotation(files_df, annotation_by_subject)

    events_df, boundary_stats = split_boundary_events(events_df, files_df)

    per_subject_rows, pooled_row = score_exports(events_df, files_df, annotation_by_subject)
    coverage_lines, coverage_issues = coverage_checks(files_df, annotation_by_subject)

    boundary_lines = [
        f"{s}: {v['n_crossed']} event(s) crossed a file boundary, {v['seconds_moved']:g} s moved"
        for s, v in boundary_stats.items() if s in set(files_df["subject"])
    ]

    print(f"\n=== {label} ===")
    print(pd.DataFrame(per_subject_rows).to_string(index=False) if per_subject_rows else "(no subjects)")
    print("\nPooled:", pooled_row)
    print("\nBoundary-crossing events:")
    for l in boundary_lines:
        print(" ", l)
    print("\nCoverage checks:")
    for l in coverage_lines:
        print(" ", l)
    if coverage_issues:
        print("Coverage ISSUES:")
        for i in coverage_issues:
            print("  !", i)
    else:
        print("Coverage issues: none")

    n_ai_events = int((events_df["source"] == "AI").sum()) if len(events_df) else 0

    if out_dir is not None:
        out_dir.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(per_subject_rows).to_csv(out_dir / "per_subject.csv", index=False)
        (out_dir / "pooled.json").write_text(json.dumps(pooled_row, indent=2))
        hashes = {p.name: hashlib.sha256(p.read_bytes()).hexdigest()
                 for p in [files_csv_path, *event_csv_paths]}
        commit = extract_app_commit()
        summary = build_summary_md(per_subject_rows, pooled_row, boundary_lines, coverage_lines,
                                   coverage_issues, hashes, commit)
        (out_dir / "SUMMARY.md").write_text(summary)
        print(f"\nWrote {out_dir}/per_subject.csv, pooled.json, SUMMARY.md")

    return dict(per_subject=per_subject_rows, pooled=pooled_row,
               coverage_lines=coverage_lines, coverage_issues=coverage_issues,
               n_ai_events=n_ai_events, boundary_stats=boundary_stats)


# ---------------------------------------------------------------------------------------
# Step 3 -- synthetic smoke tests (never write under web_demo/, never write to
# results/application_eval/)
# ---------------------------------------------------------------------------------------
def build_synthetic_files_csv(tmp_dir: Path, subject: str) -> Path:
    """files.csv does not exist yet at this step, so build one from the real EDF headers
    (duration only), per CC_PROMPT_APP_EVAL_SCORER.md Step 3 -- NOT from the annotation's own
    start/end-time arithmetic (a genuinely independent duration source)."""
    import mne
    mne.set_log_level("ERROR")
    rows = []
    for edf in sorted((DATASET_DIR / subject).glob("*.edf")):
        raw = mne.io.read_raw_edf(str(edf), preload=False, verbose=False)
        n_times = int(raw.n_times)
        sfreq = float(raw.info["sfreq"])
        duration_s = n_times / sfreq
        n_windows = n_times // WIN_SAMPLES
        rows.append(dict(subject=subject, file_name=edf.name, duration_s=duration_s,
                         n_windows=n_windows, status="success"))
    df = pd.DataFrame(rows, columns=REQUIRED_FILE_COLS)
    path = tmp_dir / "files.csv"
    df.to_csv(path, index=False)
    return path


def _find_displaced_start(dur: float, seizures: list, span: float, used: list,
                          min_gap: float = 600.0, min_gap_used: float = 100.0):
    """First point (5 s steps) where [t, t+span] stays >= min_gap s from every seizure
    interval, and >= min_gap_used s from every already-placed displaced event in this same
    file (`used`) -- otherwise two displaced events could land within SzCORE's own 90 s
    minDurationBetweenEvents and get merged into one hypothesis event, breaking the
    1-displaced-row == 1-false-alarm invariant this smoke test checks. Inside [0, dur].
    None if no such point exists in this file."""
    forbidden = [(max(0.0, on - min_gap), min(dur, off + min_gap)) for on, off in seizures]
    forbidden += [(max(0.0, u0 - min_gap_used), min(dur, u1 + min_gap_used)) for u0, u1 in used]
    t = 0.0
    step = 5.0
    while t + span <= dur:
        if all(not (t < f1 and t + span > f0) for f0, f1 in forbidden):
            return t
        t += step
    return None


def build_synthetic_events_csv(tmp_dir: Path, subject: str, annotation: dict, mode: str,
                               L_by_fname: dict) -> Path:
    rows = []
    eid = 0
    for fname, ann in sorted(annotation.items()):
        # L (files.csv's n_windows * WIN_S), not the annotation's own duration_s -- the two can
        # differ by up to WIN_S seconds, and event onset/offset validation now checks against L
        # (CC_PROMPT_SCORER_BOUNDARY.md), so the displaced-placement search must respect the
        # same bound or it could place an event just past L while still inside duration_s.
        dur = L_by_fname[fname]
        seizures = ann["seizures"]
        if mode == "oracle":
            for on, off in seizures:
                eid += 1
                rows.append(dict(subject=subject, file_name=fname, event_id=eid,
                                 onset_s=on, offset_s=off, source="AI", review_status="Unseen"))
        elif mode == "human":
            for on, off in seizures:
                eid += 1
                rows.append(dict(subject=subject, file_name=fname, event_id=eid,
                                 onset_s=on, offset_s=off, source="Human", review_status=""))
        elif mode == "displaced":
            used = []
            for on, off in seizures:
                span = off - on
                start = _find_displaced_start(dur, seizures, span, used)
                if start is None:
                    continue
                used.append((start, start + span))
                eid += 1
                rows.append(dict(subject=subject, file_name=fname, event_id=eid,
                                 onset_s=start, offset_s=start + span, source="AI",
                                 review_status="Unseen"))
        elif mode == "empty":
            pass
        else:
            raise ValueError(mode)
    df = pd.DataFrame(rows, columns=REQUIRED_EVENT_COLS)
    path = tmp_dir / f"{subject}_events.csv"
    df.to_csv(path, index=False)
    return path


def run_smoke_tests(subject: str = "chb06") -> dict:
    print(f"=== Step 3: smoke tests (subject={subject}) ===")
    print(f"{DEFAULT_TIER2_DIR}/files.csv does not exist yet -- building a synthetic files.csv "
         f"from the real EDF headers (duration only) for {subject}, per Step 3.")
    annotation = load_annotation(subject)

    results = {}
    unknown_error = None
    unknown_raised_right_type = False
    with tempfile.TemporaryDirectory(prefix="szscan_app_eval_smoke_") as tmp:
        tmp_root = Path(tmp)
        files_csv_path = build_synthetic_files_csv(tmp_root, subject)
        files_csv_bytes = files_csv_path.read_bytes()
        files_df = pd.read_csv(files_csv_path)
        L_by_fname = {r.file_name: int(r.n_windows) * WIN_S for r in files_df.itertuples()}
        for mode in ("oracle", "empty", "displaced", "human"):
            mode_dir = tmp_root / mode
            mode_dir.mkdir()
            (mode_dir / "files.csv").write_bytes(files_csv_bytes)
            build_synthetic_events_csv(mode_dir, subject, annotation, mode, L_by_fname)
            res = run_eval(mode_dir, out_dir=None, label=f"SMOKE[{mode}]")
            results[mode] = res

        # 5th smoke test: "Unknown file" -- the oracle export plus one extra files.csv row
        # whose file_name is not in the annotation at all. Must stop with ScorerInputError
        # and write nothing (guaranteed here by out_dir=None; in a real run the same
        # ScorerInputError raises before run_eval() ever reaches its out_dir-writing block).
        unknown_dir = tmp_root / "unknown_file"
        unknown_dir.mkdir()
        extra_row = pd.DataFrame([dict(
            subject=subject, file_name=f"{subject}_99.edf", duration_s=3600.0,
            n_windows=int(3600 * 256) // WIN_SAMPLES, status="success",
        )])
        pd.concat([files_df, extra_row], ignore_index=True).to_csv(
            unknown_dir / "files.csv", index=False
        )
        build_synthetic_events_csv(unknown_dir, subject, annotation, "oracle", L_by_fname)
        print(f"\n=== SMOKE[unknown_file] ===")
        try:
            run_eval(unknown_dir, out_dir=None, label="SMOKE[unknown_file]")
        except ScorerInputError as exc:
            unknown_raised_right_type = True
            unknown_error = str(exc)
            print(f"Raised ScorerInputError (expected):\n{unknown_error}")
        except Exception as exc:  # wrong exception type -- still a failure, but report it
            unknown_error = f"{type(exc).__name__}: {exc}"
            print(f"Raised the WRONG exception type: {unknown_error}")

        # 6th smoke test: "Boundary" -- a real seizure in the first minutes of a file that is
        # not the subject's first file, hit by one AI event that starts 20 s before the end
        # (L) of the PREVIOUS file in sorted order, with offset_s = onset_s + 20 +
        # (seizure offset) -- so after the split it covers the seizure exactly
        # (CC_PROMPT_SCORER_BOUNDARY.md Step 3). Also a failing case: an event whose
        # offset_s > L in the subject's LAST file must raise ScorerInputError.
        order = sorted(annotation.keys())
        chosen = None
        for i in range(1, len(order)):
            seizure_file = order[i]
            szs = annotation[seizure_file]["seizures"]
            if not szs:
                continue
            s_on, s_off = szs[0]
            if s_on > 600:  # keep it comfortably "in the first minutes" of the file
                continue
            prev_file = order[i - 1]
            if annotation[prev_file]["seizures"]:
                continue  # keep the pair unconfounded: no seizure of its own near prev_file's end
            chosen = (prev_file, seizure_file, s_on, s_off)
            break
        if chosen is None:
            raise SystemExit(
                f"No usable (previous file, seizure file) pair found for {subject} to build "
                f"the Boundary smoke test -- pick a different --smoke_subject."
            )
        prev_file, seizure_file, s_on, s_off = chosen
        L_prev = L_by_fname[prev_file]
        boundary_onset = float(L_prev - 20)
        boundary_offset = float(L_prev + s_off)
        print(f"\n[Boundary smoke test] subject={subject} prev_file={prev_file} (L={L_prev}) "
             f"seizure_file={seizure_file} seizure=({s_on},{s_off}) event in {prev_file}="
             f"({boundary_onset:g},{boundary_offset:g})")

        boundary_dir = tmp_root / "boundary"
        boundary_dir.mkdir()
        pair_files_df = files_df[files_df["file_name"].isin([prev_file, seizure_file])]
        pair_files_df.to_csv(boundary_dir / "files.csv", index=False)
        pd.DataFrame([dict(
            subject=subject, file_name=prev_file, event_id=1,
            onset_s=boundary_onset, offset_s=boundary_offset,
            source="AI", review_status="Unseen",
        )], columns=REQUIRED_EVENT_COLS).to_csv(boundary_dir / f"{subject}_events.csv", index=False)
        boundary_res = run_eval(boundary_dir, out_dir=None, label="SMOKE[boundary]")
        boundary_pooled = boundary_res["pooled"]
        boundary_crossed = boundary_res["boundary_stats"][subject]["n_crossed"]

        last_file = order[-1]
        L_last = L_by_fname[last_file]
        overflow_dir = tmp_root / "boundary_overflow_last_file"
        overflow_dir.mkdir()
        files_df.to_csv(overflow_dir / "files.csv", index=False)
        pd.DataFrame([dict(
            subject=subject, file_name=last_file, event_id=1,
            onset_s=float(L_last - 10), offset_s=float(L_last + 10),
            source="AI", review_status="Unseen",
        )], columns=REQUIRED_EVENT_COLS).to_csv(overflow_dir / f"{subject}_events.csv", index=False)
        print(f"\n[Boundary smoke test: last-file overflow] subject={subject} last_file="
             f"{last_file} (L={L_last}) event=({L_last - 10:g},{L_last + 10:g})")
        overflow_raised_right_type = False
        overflow_error = None
        try:
            run_eval(overflow_dir, out_dir=None, label="SMOKE[boundary_overflow_last_file]")
        except ScorerInputError as exc:
            overflow_raised_right_type = True
            overflow_error = str(exc)
            print(f"Raised ScorerInputError (expected):\n{overflow_error}")
        except Exception as exc:
            overflow_error = f"{type(exc).__name__}: {exc}"
            print(f"Raised the WRONG exception type: {overflow_error}")

    checks = []
    o, e, d, h = (results[m]["pooled"] for m in ("oracle", "empty", "displaced", "human"))
    checks.append(("oracle: sensitivity == 1.000", o["sensitivity"] == 1.0))
    checks.append(("oracle: precision == 1.000", o["precision"] == 1.0))
    checks.append(("oracle: false_alarms == 0", o["false_alarms"] == 0))
    checks.append(("empty: sensitivity == 0.000", e["sensitivity"] == 0.0))
    checks.append(("empty: false_alarms == 0", e["false_alarms"] == 0))
    checks.append(("empty: f1 == 'undefined'", e["f1"] == "undefined"))
    checks.append(("displaced: sensitivity == 0.000", d["sensitivity"] == 0.0))
    checks.append(("displaced: false_alarms == number of AI events",
                   d["false_alarms"] == results["displaced"]["n_ai_events"]))
    checks.append(("human: pooled identical to empty", h == e))
    checks.append(("unknown file: raises ScorerInputError, writes nothing",
                   unknown_raised_right_type))
    checks.append(("boundary: split carried the overflow into the next file",
                   boundary_crossed == 1))
    checks.append(("boundary: one TP for the seizure covered after the split",
                   boundary_pooled["detected"] == 1))
    checks.append(("boundary: last-file overflow raises ScorerInputError",
                   overflow_raised_right_type))

    print("\n=== Step 3 smoke-test verdicts ===")
    all_ok = True
    for name, ok in checks:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_ok = all_ok and ok
    if not all_ok:
        raise SystemExit("Smoke tests FAILED -- fix the scorer before running on real exports (Step 4).")
    print("\nAll six smoke tests PASS.")
    return results


# ---------------------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--smoke", action="store_true",
                    help="Step 3 only: synthetic proof, writes nothing under results/application_eval/")
    ap.add_argument("--smoke_subject", default="chb06",
                    help="which test subject's real EDFs/annotation to build synthetic exports from")
    ap.add_argument("--tier2_dir", default=str(DEFAULT_TIER2_DIR),
                    help="real run only: directory holding files.csv and {subject}_events.csv")
    args = ap.parse_args()

    if args.smoke:
        run_smoke_tests(args.smoke_subject)
        return

    if OUT_DIR.exists() and any(OUT_DIR.iterdir()):
        raise SystemExit(
            f"{OUT_DIR} already holds results -- refusing to overwrite silently. "
            f"Inspect it, and remove or move it aside yourself if a fresh run is really wanted."
        )

    tier2_dir = Path(args.tier2_dir)
    if not tier2_dir.exists():
        raise SystemExit(
            f"{tier2_dir} does not exist -- the real Part 3 tier-2 export "
            f"(REPORT_REQUEST_TO_PROJECT2.md Part 3) has not been produced yet. "
            f"Run `--smoke` to prove the scorer in the meantime."
        )

    run_eval(tier2_dir, OUT_DIR, label="Step 4: real run")


if __name__ == "__main__":
    main()
