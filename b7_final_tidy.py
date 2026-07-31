#!/usr/bin/env python3
"""b7_final_tidy.py -- FINAL repo tidy: loose root files + superseded results/ CLUTTER.
REVERSIBLE (git mv into archive/ or results/history_superseded/final_tidy/; explicit-delete only
3 scratch files). Default DRY-RUN (the dry-run doubles as the scan: it prints exactly which listed
paths exist -> would move, and which don't -> skip). Add --apply to execute.
WHITELIST: anything not listed is untouched. Keeps entry.sh / Makefile / Dockerfile / pip_freeze.txt."""
import os, sys, subprocess
APPLY = "--apply" in sys.argv
HIST = "results/history_superseded/final_tidy"

# dest -> [sources]  (files OR dirs)
PLAN = {
 # --- loose root files -> proper homes ---
 "src": ["edf_index.py"],
 "src/fp_reduction_prior": ["fp_filter_step1_diagnose.py", "fp_filter_step2_cusum.py",
                            "fp_filter_step2b_duration_diag.py", "fp_filter_step2c_fine_cliff.py"],
 "archive/rejected": ["evaluate_full.py", "oversegmentation_diag.py",
                      "topo_standalone_auroc.csv", "topo_features"],
 # --- superseded results/ CLUTTER (old pipeline lineage, old eval variants, old baselines) ---
 # moved under HIST preserving their results/ subpath (dry-run shows which actually exist)
 HIST: [
   "results/cpd/cpd_results.csv", "results/cpd/cpd_results_v3.csv", "results/cpd/cpd_results_v4.csv",
   "results/cpd/cpd_results_v5.csv", "results/cpd/cpd_results_v6.csv", "results/cpd/cpd_results_v7.csv",
   "results/cpd/cpd_results_v8.csv", "results/cpd/cpd_results_v9.csv", "results/cpd/cpd_results_v10.csv",
   "results/cpd/cpd_results_v11.csv", "results/cpd/cpd_results_v12.csv",
   "results/cpd/cpd_results_v12_combined.csv", "results/cpd/cpd_tolerance_sweep.csv",
   "results/cpd/window_metrics.csv",
   "results/eval",
   "results/cpd/evaluation/sweep", "results/cpd/evaluation/szcore",
   "results/cpd/evaluation/szcore_mag60", "results/cpd/evaluation/lock_mag60",
   "results/cpd/evaluation/lock_mag70", "results/cpd/evaluation/oversegmentation",
   "results/cpd/evaluation/eval_event_level.csv",
   "results/ce_results.csv", "results/ce_znorm_results.csv", "results/znorm_results.csv",
   "results/results_log.csv",
 ],
}
DELETE = ["file_list.txt", "inventory.json", "mean_inter"]

def sh(a): return subprocess.run(a, capture_output=True, text=True)
def main():
    if not os.path.isdir(".git"): sys.exit("ERROR: run from repo root.")
    print(f"=== B7 final tidy [{'APPLY' if APPLY else 'DRY-RUN'}] ===\n")
    if APPLY:
        dirty=[l for l in sh(["git","status","--porcelain"]).stdout.splitlines() if not l.startswith("??")]
        if dirty: sys.exit("ERROR: tracked changes present. Commit/stash first.\n"+"\n".join(dirty))
    moved=miss=0
    for dest,items in PLAN.items():
        for s in items:
            s=os.path.normpath(s)
            if not os.path.exists(s): print(f"  skip (not found): {s}"); miss+=1; continue
            # for HIST, preserve the results/ subpath; else flat basename
            if dest==HIST and (s.startswith("results"+os.sep) or s.startswith("results/")):
                tgt=os.path.normpath(os.path.join(HIST, os.path.relpath(s,"results")))
            else:
                tgt=os.path.normpath(os.path.join(dest, os.path.basename(s)))
            if os.path.normpath(os.path.dirname(s))==os.path.normpath(os.path.dirname(tgt)): continue
            if APPLY:
                os.makedirs(os.path.dirname(tgt) or ".",exist_ok=True); r=sh(["git","mv",s,tgt])
                print(("  moved:  " if r.returncode==0 else f"  FAIL({r.stderr.strip()}): ")+f"{s} -> {tgt}")
            else: print(f"  would move: {s} -> {tgt}")
            moved+=1
    print("\n-- DELETE (scratch) --")
    for f in DELETE:
        if not os.path.exists(f): print(f"  skip (not found): {f}"); continue
        if APPLY: r=sh(["git","rm","-q",f]); print(("  deleted: " if r.returncode==0 else f"  FAIL({r.stderr.strip()}): ")+f)
        else: print(f"  would delete: {f}")
    print(f"\nSummary: {moved} would-move, {miss} not-found(skipped).")
    print("KEPT at root (template): entry.sh, Makefile, Dockerfile, pip_freeze.txt, README.md")
    if not APPLY: print("\n(DRY-RUN. Paste this output to Claude to review, then re-run with --apply.)")
if __name__=="__main__": main()