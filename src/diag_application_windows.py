#!/usr/bin/env python
"""
diag_application_windows.py -- CC_PROMPT_APP_WINDOW_DIAG.md: does the application's
sensitivity/precision gap against the offline result (results/application_eval/, commit
901657e) already show up at the WINDOW level, or only at the detection (PELT/event) stage?
Also checks for a time-alignment defect between the score array and the annotation.

Read-only on web_demo/. Nothing is tuned, nothing is re-scored, the application is not
re-run: this reads the fused score the application already computed and cached
(web_demo/backend/uploads/{subject}/{stem}.score.npy) and the seizure annotation, and
reports discrimination metrics only.

Fused score confirmation (per this prompt's own Step 1 -- quoted, not assumed):
  - web_demo/backend/upload_manager.py:434-436 persists exactly `scores[fn]`, one .npy per
    file, as `{stem}.score.npy`:
        subject_dir = UPLOAD_DIR / session.project_id
        for fn, score in scores.items():
            np.save(subject_dir / f"{Path(fn).stem}.score.npy", score)
  - `scores` there is `session.files[fn].score`, in turn `pd.process_subject_phase_b_from_paths(...)`'s
    return value == `pipeline_demo.process_subject_phase_b()`'s own `scores` dict, built at
    pipeline_demo.py:487-491:
        score = ensemble_recipe.build_ensemble_subset(
            {"zrecon": zr, "zlatent": zl, "zgamma": zg},
            subset=ensemble_recipe.CANDIDATES["rlg"],
        )
        scores[f] = score.astype(np.float64)
    -- the fused rlg (zrecon+zlatent+zgamma) ensemble score, one value per window, exactly
    what the live Process path scores and what §1.1.2 of REPORT_HANDBACK.md already
    confirmed is the only score family in this build (no LSTM/temporal branch).
  - Window length and indexing: `src/dataprep/preprocessing.py:52-54`, `FS = 256`,
    `WIN_S = 4`, `WIN_SAMPLES = FS * WIN_S`; `pipeline_demo.process_subject_events()` converts
    a window index to file-relative seconds via `local_onset = (onset_win - lo) * win_sec`
    with `win_sec = float(preprocessing.WIN_S)` (pipeline_demo.py:584,617) -- window `i`
    covers `[4i, 4i+4)` s of its file, matching this prompt's own stated convention exactly.

Usage: python src/diag_application_windows.py
"""
import sys
import time
from pathlib import Path

import numpy as np
from sklearn.metrics import average_precision_score, roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

from evaluation_protocol import parse_summary_edf_list  # noqa: E402 -- reused, not retyped

TEST_SUBJECTS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

DATASET_DIR = Path("F:/Study/Thesis/Dataset/CHB-MIT")
SUMMARY_DIR = DATASET_DIR / "CHB info" / "summary"
UPLOADS_DIR = ROOT / "web_demo" / "backend" / "uploads"
OUT_DIR = ROOT / "results" / "application_eval"

WIN_S = 4
SHIFTS = [-15, -10, -5, -2, -1, 0, 1, 2, 5, 10, 15]

# report Table 3.1, for comparison only -- printed alongside, never used in any computation.
OFFLINE_AUROC = {
    "chb03": 0.964, "chb06": 0.501, "chb13": 0.822, "chb14": 0.698,
    "chb15": 0.879, "chb16": 0.876, "chb17": 0.782, "chb18": 0.920,
}
OFFLINE_MACRO_AUROC = 0.805


def load_annotation(subject: str) -> dict:
    edfs = parse_summary_edf_list(SUMMARY_DIR / f"{subject}-summary.md")
    return {e["fname"]: e["seizures"] for e in edfs}


def window_labels(n_windows: int, seizures: list) -> np.ndarray:
    """Window i is ictal if [4i, 4i+4) overlaps ANY annotated seizure of the file. Every
    window counts -- no exclusion, matching the application's own no-artifact-rejection
    setting (already confirmed elsewhere; this script does not re-check that)."""
    labels = np.zeros(n_windows, dtype=np.int8)
    starts = np.arange(n_windows) * WIN_S
    ends = starts + WIN_S
    for on, off in seizures:
        labels[(starts < off) & (ends > on)] = 1
    return labels


def shift_labels(labels: np.ndarray, k: int) -> np.ndarray:
    """shifted[i] = labels[i - k] ("a positive k moves the labels later"), zero-padded at
    whichever edge has no source index. Applied PER FILE, before concatenation across a
    subject's files -- a systematic alignment offset is a per-recording timing question,
    not something that should cross a file boundary."""
    n = len(labels)
    out = np.zeros(n, dtype=labels.dtype)
    if k >= 0:
        if k < n:
            out[k:] = labels[: n - k]
    else:
        kk = -k
        if kk < n:
            out[: n - kk] = labels[kk:]
    return out


def main() -> None:
    t_start = time.perf_counter()

    rows = []
    auroc_values = []
    missing_report = []

    for subject in TEST_SUBJECTS:
        annotation = load_annotation(subject)
        subject_dir = UPLOADS_DIR / subject

        per_file_scores = []
        per_file_labels = []  # {k: array} filled below per shift
        file_names = []
        for fname, seizures in sorted(annotation.items()):
            score_path = subject_dir / f"{Path(fname).stem}.score.npy"
            if not score_path.exists():
                missing_report.append(f"{subject}/{fname}: no {score_path.name} on disk -- skipped")
                continue
            score = np.load(score_path)
            labels = window_labels(len(score), seizures)
            per_file_scores.append(score)
            per_file_labels.append(labels)
            file_names.append(fname)

        if not per_file_scores:
            raise SystemExit(f"{subject}: no per-file scores found under {subject_dir} -- nothing to diagnose.")

        all_scores = np.concatenate(per_file_scores)
        all_labels = np.concatenate(per_file_labels)
        n_windows = len(all_scores)
        n_ictal = int(all_labels.sum())

        auroc = roc_auc_score(all_labels, all_scores) if 0 < n_ictal < n_windows else float("nan")
        auprc = average_precision_score(all_labels, all_scores) if 0 < n_ictal < n_windows else float("nan")

        best_k, best_auroc = 0, auroc
        for k in SHIFTS:
            shifted = np.concatenate([shift_labels(lab, k) for lab in per_file_labels])
            n_ictal_k = int(shifted.sum())
            if 0 < n_ictal_k < n_windows:
                a = roc_auc_score(shifted, all_scores)
                if a > best_auroc:
                    best_k, best_auroc = k, a

        rows.append(dict(
            subject=subject, n_windows=n_windows, n_ictal_windows=n_ictal,
            auroc=auroc, auprc=auprc, best_shift_k=best_k, auroc_at_best_shift=best_auroc,
        ))
        auroc_values.append(auroc)
        print(f"{subject}: n_windows={n_windows} n_ictal={n_ictal} auroc={auroc:.4f} "
              f"auprc={auprc:.4f} best_k={best_k} auroc_at_best_k={best_auroc:.4f} "
              f"(files={len(file_names)})")

    macro_auroc = float(np.mean(auroc_values))
    elapsed_s = time.perf_counter() - t_start

    misaligned_subjects = [r["subject"] for r in rows if r["best_shift_k"] not in (-1, 0, 1)]

    print(f"\nmacro AUROC (application): {macro_auroc:.4f}   (offline macro: {OFFLINE_MACRO_AUROC:.3f})")
    if missing_report:
        print("\nMissing score files (skipped):")
        for m in missing_report:
            print(" ", m)
    if misaligned_subjects:
        print(f"\nALIGNMENT FLAG -- best shift is not in {{-1,0,+1}} for: {misaligned_subjects}")
    else:
        print("\nAlignment check: best shift is 0 or +/-1 for every subject -- no alignment defect indicated.")
    print(f"\nTotal computation time: {elapsed_s:.2f} s")

    # ---- outputs ----
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "window_diagnostic.csv"
    with open(csv_path, "w", newline="") as f:
        f.write("subject,n_windows,n_ictal_windows,auroc,auprc,best_shift_k,auroc_at_best_shift\n")
        for r in rows:
            f.write(f"{r['subject']},{r['n_windows']},{r['n_ictal_windows']},"
                    f"{r['auroc']:.6f},{r['auprc']:.6f},{r['best_shift_k']},{r['auroc_at_best_shift']:.6f}\n")

    md_path = OUT_DIR / "window_diagnostic.md"
    lines = ["# Window-level discrimination and alignment of application scores", ""]
    lines.append("Diagnosis only -- nothing tuned, nothing re-scored, the application was not re-run "
                  "(`CC_PROMPT_APP_WINDOW_DIAG.md`). Offline AUROC (report Table 3.1) is printed for "
                  "comparison only, without comment.")
    lines.append("")
    lines.append("| Subject | n_windows | n_ictal_windows | AUROC (app) | AUPRC (app) | best shift k | AUROC at best shift | AUROC (offline) |")
    lines.append("|---|---|---|---|---|---|---|---|")
    for r in rows:
        lines.append(f"| {r['subject']} | {r['n_windows']} | {r['n_ictal_windows']} | "
                      f"{r['auroc']:.3f} | {r['auprc']:.3f} | {r['best_shift_k']:+d} | "
                      f"{r['auroc_at_best_shift']:.3f} | {OFFLINE_AUROC[r['subject']]:.3f} |")
    lines.append(f"| **macro** | | | **{macro_auroc:.3f}** | | | | **{OFFLINE_MACRO_AUROC:.3f}** |")
    lines.append("")
    if misaligned_subjects:
        lines.append(f"**Alignment flag:** best shift is not in {{-1, 0, +1}} for: {', '.join(misaligned_subjects)}.")
    else:
        lines.append("**Alignment check:** best shift is 0 or ±1 for every subject -- no alignment defect indicated.")
    lines.append("")
    lines.append(f"Total computation time: {elapsed_s:.2f} s.")
    lines.append("")
    md_path.write_text("\n".join(lines))

    print(f"\nWrote {csv_path}")
    print(f"Wrote {md_path}")


if __name__ == "__main__":
    main()
