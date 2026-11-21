#!/usr/bin/env python
"""
fa15_perturb.py -- F-A1.5 diagnostic T2 (chat D35-F, approved by the author 21/11 13:30; design in
results/fa15/DESIGN_D35F.md §6, written before this runs): how sensitive is ASR (V9-X6 settings) to a relative
perturbation of its input at the last bits?

Why: FA15_DATA_A reproduced 48 of V9-X6's 57 files in its part bit for bit, but 9 files (and chb06_01 in the smoke)
differ from the record (laptop, 30/10) by up to 0.34 in a window share; recomputing with V9-X6's earlier chunkings did not
explain them. Hypothesis: platform arithmetic (laptop vs Kaggle machine types, handback Part 28.3) amplified by ASR's
discontinuous steps (clean-window selection in the calibration, keep / reject of components). Established test of
numerical sensitivity: perturb the input at the last bits and measure the output (Monte Carlo arithmetic in Kiar et al.
2021, PLoS One, DOI 10.1371/journal.pone.0250755; the repository's own conditioning test in R0_DIAG17: x (1 + 2^-40)).

What: every file of V9-X6's universe (70: the seizure files of the 8 test patients + chb24), ASR exactly as the F-A1.5
data run (fa15_asr.clean_cli: V9-X6's run_asr, 60-s chunks, cutoff 20, the one-sample block_covariance guard), twice:
P0 = the pipeline-filtered signal as is, P1 = the same signal x (1 + 2^-40) (a relative change of 9.1e-13); Measure 1 of
each (V9-X6's functions; thresholds = R0's 5-SD thresholds, as the data run). Per file: max |P1 - P0| per quantity,
max |P0 - record| (results/v9_x6), max |P0 - the data run's committed Measure 1| where present (results/fa15/a, b1, b2,
smoke: Kaggle vs Kaggle across sessions and machine types). Descriptive; no threshold on the result (the 2 x 2 table of
"differs from the record" x "moves under the perturbation" is read by the author).

Gates (STOP unless noted): G-mod, mode, R0.1 inventory (raw files sha256 = PhysioNet), G-ref (R0 references, for the
thresholds), G-done (all 70 files, both arms), G-worker-sha (every subprocess ran fa15_asr.py of this commit).
Outputs: WORK/fa15/perturb/ (perturb.csv, gates.json, run_meta.json incl. the machine, SUMMARY.md). No signal is kept.
  python src/fa15_perturb.py --run [--eps 9.094947017729282e-13] [--workers 4]
"""
import argparse
import json
import os
import platform
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
sys.path.insert(0, str(REPO / "src"))
import fa15_asr as F                     # noqa: E402  (this chat's module: clean path, Measure 1, comparison, gates)

EPS = 2.0 ** -40
TAG = "perturb"
QTY = ("share_seizure", "share_preictal60", "contrast_before", "contrast_after", "highamp_share",
       "background_share_sorted")
PRIOR = ("a", "b1", "b2", "smoke")                         # committed Measure 1 of the data runs (Kaggle)


def prior_frames(s, f):
    """the data run's committed Measure 1 of one file (first found among PRIOR), as V9-X6-format frames, or None."""
    for tag in PRIOR:
        p = REPO / "results" / "fa15" / tag / "measure" / f"{s}__{f}.json"
        if p.exists():
            m = json.loads(p.read_text())
            if m:
                return tag, F._measure_frames(m, s, f)
    return None, None


def run(eps=EPS, workers=None, notebook="local", commit="local"):
    F.STATE["tag"] = TAG
    t0 = time.time()
    v = F.versions()
    meta = dict(notebook=notebook, tag=TAG, repo_commit=commit, code_sha=F.CODE_SHA, eps=eps, versions=v,
                cpu_count=os.cpu_count(), platform=platform.platform(), machine=F.machine_info(),
                started=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), test=F.TEST)
    F.jdump(F.out_dir() / "run_meta.json", meta)
    F.gate(dict(gate="G-mod", status="PASS", summary=f"closed modules from {F.REPO / 'src'}; fa15_asr {F.CODE_SHA}"))
    F.gate_mode(v)
    rec = F.v9_record()
    universe = sorted(set(zip(rec[0].subject, rec[0].file)))
    if F.TEST and os.environ.get("FA15_TEST_PERTURB_FILES"):
        universe = [tuple(x) for x in json.loads(os.environ["FA15_TEST_PERTURB_FILES"])]
    cases = sorted({s for s, _ in universe})
    chb = [c for c in cases if c != "chb24" and c.startswith("chb")]
    ext = [c for c in cases if c not in chb]
    dbs = {"chbmit": sorted(set(chb) | {c for c in ext if c.startswith("chb")})}
    if any(c.startswith("PN") for c in ext):
        dbs["siena"] = sorted(c for c in ext if c.startswith("PN"))
    F.R0.run_meta(f"fa15_{TAG}_inventory", notebook, commit)          # as fa15_asr.run (sets r2_core's output tag)
    try:
        inv, _, complete, _ = F.R0.inventory(dbs)
    except SystemExit as e:
        F.gate(dict(gate="R0.1-inventory", status="FAIL", summary=str(e)))
    F.gate(dict(gate="R0.1-inventory", status="PASS", files=int(len(inv)),
                summary=f"{len(inv)} files sha256 = PhysioNet"))
    refs = F.r0_refs(chb, ext)
    specs = []
    for c in cases:
        set_ = "chb" if c in chb else "ext"
        specs += [s for s in F.plan_case(c, set_, complete, refs) if (c, Path(s["path"]).name) in set(universe)]
    missing = sorted(set(universe) - {(s["case"], Path(s["path"]).name) for s in specs})
    K = workers or max(1, (os.cpu_count() or 1))
    F.log(f"T2: {len(specs)} files ({sum(s['hours'] for s in specs):.1f} h), eps {eps:.3e}, {K} ASR processes; "
          f"missing {missing}")
    t = time.time()
    p0 = F.recompute(specs, 60.0, K)
    t_p0 = time.time() - t
    p1 = F.recompute(specs, 60.0, K, perturb=eps)
    t_p1 = time.time() - t - t_p0
    rows, sha_bad = [], []
    for (s, f) in sorted(set(p0) & set(p1)):
        a, b = p0[(s, f)], p1[(s, f)]
        for r in (a, b):
            if r["code_sha"] != F.CODE_SHA:
                sha_bad.append(f"{s}/{f}:{r['code_sha']}")
        w_pert, only_pert, rows_pert, *_ = F.compare_file(*b["frames"], s, f, (a["frames"][0], a["frames"][1],
                                                                                   a["frames"][2]))
        w_rec, only_rec, rows_rec, *_ = F.compare_file(*a["frames"], s, f, rec)
        tag, pf = prior_frames(s, f)
        w_pri = F.compare_file(*a["frames"], s, f, pf)[0] if pf is not None else None
        row = dict(subject=s, file=f, hours=a["hours"], mem_splits=a["mem_splits"],
                   power_removed_p0=a["power_removed_total"], power_removed_p1=b["power_removed_total"],
                   max_pert=max(w_pert.values()), highamp_only_pert=only_pert,
                   max_vs_record=max(w_rec.values()), highamp_only_record=only_rec,
                   prior=tag, max_vs_prior=max(w_pri.values()) if w_pri else np.nan,
                   asr_s_p0=a["asr_s"], asr_s_p1=b["asr_s"])
        row.update({f"pert_{q}": w_pert[q] for q in QTY})
        row.update({f"rec_{q}": w_rec[q] for q in QTY})
        rows.append(row)
    d = pd.DataFrame(rows)
    d["moves_under_perturbation"] = (d.max_pert > F.TOL["asr_explain"]) | (d.highamp_only_pert > 0)
    d["differs_from_record"] = (d.max_vs_record > F.TOL["asr_explain"]) | (d.highamp_only_record > 0)
    d.to_csv(F.out_dir() / "perturb.csv", index=False)
    done = len(d) == len(universe) and not missing
    F.gate(dict(gate="G-done", status="PASS" if done else "FAIL", files=len(d), universe=len(universe),
                missing=missing, summary=f"{len(d)} of {len(universe)} files, both arms"), stop=False)
    F.gate(dict(gate="G-worker-sha", status="PASS" if not sha_bad and len(d) else "FAIL", expected=F.CODE_SHA,
                differ=sha_bad[:10], summary=f"{2 * len(d) - len(sha_bad)} of {2 * len(d)} subprocesses ran fa15_asr "
                                             f"{F.CODE_SHA}"), stop=False)
    tab = pd.crosstab(d.differs_from_record, d.moves_under_perturbation) if len(d) else pd.DataFrame()
    pri = d[d.prior.notna()] if len(d) else d
    L = [f"# F-A1.5 T2 -- ASR sensitivity to a relative input perturbation of {eps:.3e} (fa15_asr {F.CODE_SHA})", "",
         f"Machine: {meta['machine']}. Files: {len(d)} of {len(universe)}. ASR wall time P0 {t_p0 / 3600:.2f} h, "
         f"P1 {t_p1 / 3600:.2f} h.", "",
         "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {str(g.get('summary', '')).replace('|', '/')[:300]} |" for g in F.STATE["gates"]]
    L += ["", "## Differs from the V9-X6 record (rows) x moves under the perturbation (columns), files", "",
          "```", tab.to_string() if len(tab) else "(none)", "```", "",
          f"Kaggle P0 vs the data run's committed Measure 1 (same code, another session): {len(pri)} files compared, "
          f"{int((pri.max_vs_prior > F.TOL['asr_explain']).sum()) if len(pri) else 0} differ beyond 1e-9.", "",
          "## Files that move under the perturbation", "",
          "```", d[d.moves_under_perturbation][["subject", "file", "max_pert", "max_vs_record", "max_vs_prior",
                                                "power_removed_p0"]].to_string(index=False) if len(d) else "(none)", "```"]
    (F.out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    meta.update(finished=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()), runtime_h=round((time.time() - t0) / 3600, 3),
                asr_h=dict(p0=round(t_p0 / 3600, 3), p1=round(t_p1 / 3600, 3)))
    F.jdump(F.out_dir() / "run_meta.json", meta)
    return [g["gate"] for g in F.STATE["gates"] if g["status"] not in ("PASS", "n/a", "NOT GATED")]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--run", action="store_true")
    ap.add_argument("--eps", type=float, default=EPS)
    ap.add_argument("--workers", type=int, default=None)
    a = ap.parse_args()
    if a.run:
        failed = run(a.eps, a.workers)
        print("FAILED GATES:", failed or "none")
        return 1 if failed else 0
    ap.print_help()
    return 2


if __name__ == "__main__":
    sys.exit(main())
