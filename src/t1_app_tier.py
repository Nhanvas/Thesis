#!/usr/bin/env python
"""
t1_app_tier.py -- application-tier evaluation of the REBUILT demo (final system). Scores the
application's own exported AI events (web_demo/backend/export_tier2.py, every AI event before any
review) against the annotation with the existing application scorer, unchanged
(eval_application_events.run_eval: SzCORE `score_szcore` per file, counts summed per subject;
false-alarm denominator = recorded time of the processed files minus seizure time).

Rules (project instructions 11.5, fixed before the run): frozen build (the export's MANIFEST names
the commit; uncommitted changes in web_demo/backend or src = STOP), clean database with the 8 test
subjects, export before review, one run; any defect => the whole application run is repeated.
Reported: per subject tp, n_ref, fp, hours; pooled and subject-mean sensitivity, precision, F1,
FP/day, all from the scorer's counts (F1 = 2tp / (2tp + fp + fn) per subject for the mean, as
e22_test_oneshot.metrics). A separate tier: never merged with the thesis's offline numbers.

  python src/t1_app_tier.py --tier2-dir web_demo/report_handback/tier2_v4
Writes results/application_eval_v4/ (refuses to overwrite).
"""
import argparse
import json
import re
import sys
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import eval_application_events as EA   # noqa: E402  (the existing application scorer, read-only)

OUT = ROOT / "results" / "application_eval_v4"


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--tier2-dir", required=True)
    a = ap.parse_args()
    t2 = Path(a.tier2_dir)
    man = (t2 / "MANIFEST.txt").read_text()
    commit = re.search(r"^commit (\S+)", man, re.M).group(1)
    if "uncommitted changes in web_demo/backend or src: YES" in man:
        raise SystemExit("STOP: the export was made from a build with uncommitted changes (not a frozen build)")
    if OUT.exists() and any(OUT.iterdir()):
        raise SystemExit(f"STOP: {OUT} already holds results")
    files = pd.read_csv(t2 / "files.csv")
    if sorted(files.subject.unique()) != sorted(EA.TEST_SUBJECTS):
        raise SystemExit(f"STOP: export holds {sorted(files.subject.unique())}, expected the 8 test subjects")

    res = EA.run_eval(t2, None, label="application tier, rebuilt demo (final system)")
    if res["coverage_issues"]:
        raise SystemExit(f"STOP: coverage issues {res['coverage_issues']}")
    P = pd.DataFrame(res["per_subject"])
    P["fn"] = P.seizures - P.detected
    P["f1_counts"] = 2 * P.detected / (2 * P.detected + P.false_alarms + P.fn)
    P["precision_counts"] = (P.detected / (P.detected + P.false_alarms)).where(P.detected + P.false_alarms > 0)
    tp, fp, nr = int(P.detected.sum()), int(P.false_alarms.sum()), int(P.seizures.sum())
    pooled = res["pooled"]
    subj_mean = dict(sensitivity=float(P.sensitivity.mean()), precision=float(P.precision_counts.mean()),
                     f1=float(P.f1_counts.mean()), false_alarms_per_day=float(pd.to_numeric(P.false_alarms_per_day).mean()))
    pooled_counts = dict(tp=tp, fp=fp, n_ref=nr, sensitivity=tp / nr, precision=tp / (tp + fp) if tp + fp else float("nan"),
                         f1=2 * tp / (2 * tp + fp + (nr - tp)), false_alarms_per_day=pooled["false_alarms_per_day"],
                         hours=pooled["hours"])
    OUT.mkdir(parents=True)
    P.to_csv(OUT / "per_subject.csv", index=False)
    (OUT / "pooled.json").write_text(json.dumps(dict(pooled=pooled_counts, subject_mean=subj_mean, commit=commit), indent=1))
    L = ["# Application tier -- rebuilt demo (final system), 8 test subjects\n",
         f"Build commit {commit}; export manifest:\n", "```", man.strip(), "```\n",
         "Scorer: src/eval_application_events.py (unchanged): SzCORE event scoring per file, counts summed per subject; "
         "FP/day denominator = recorded time of the processed files minus seizure time. Every AI event, before review.\n",
         "## Per subject\n", "```",
         P[["subject", "files", "hours", "seizures", "detected", "false_alarms", "sensitivity", "precision_counts",
            "f1_counts", "false_alarms_per_day"]].round(4).to_string(index=False), "```\n",
         "## Pooled and subject-mean (from the scorer's counts)\n", "```",
         f"pooled        {tp}/{nr} detected, {fp} false alarms, sensitivity {pooled_counts['sensitivity']:.3f}, "
         f"precision {pooled_counts['precision']:.3f}, F1 {pooled_counts['f1']:.3f}, FP/day {pooled_counts['false_alarms_per_day']:.2f}",
         f"subject-mean  sensitivity {subj_mean['sensitivity']:.3f}, precision {subj_mean['precision']:.3f}, "
         f"F1 {subj_mean['f1']:.3f}, FP/day {subj_mean['false_alarms_per_day']:.2f}", "```",
         "\nBoundary lines: " + "; ".join(f"{s}: {v['n_crossed']}" for s, v in res["boundary_stats"].items()),
         "\nCoverage: " + "; ".join(res["coverage_lines"][-3:])]
    (OUT / "SUMMARY.md").write_text("\n".join(L), encoding="utf-8")
    print("\n".join(L))


if __name__ == "__main__":
    main()
