"""
consolidate_outputs.py  —  gather scattered thesis outputs into a clean results/ tree.
COPIES (never deletes) known artifacts, searched recursively from --root, into
categorized subfolders, and writes results/MANIFEST.txt. Safe to re-run.

Categories:
  results/locked/           locked event/window CSVs + auroc_verification
  results/attribution/      per-node recon attribution (primary) + eigencentrality (convergent)
  results/ablation/         event-tier ablation + window<->event gap
  results/phaseA_appendix/  corrected mag%xpen grid (v2) + duration-stratified CSVs
                            + per-subject event detail at the Decision #19/#20 points
  results/history_topology/ rejected topology extension (kept as development record)
  results/history_superseded/ old-weight / seeding-bug artifacts (kept ONLY for comparison;
                            never cite — current numbers are in locked/ + phaseA_appendix/)

USAGE:  python consolidate_outputs.py --root . --out results
"""
import argparse, glob, os, shutil

MANIFEST = {
    "locked": [
        "locked_phaseA_event_results.csv", "eval_window_level.csv",
        "eval_stat_tests.csv", "auroc_verification.csv",
    ],
    "attribution": [
        "attribution_pernode_summary.csv", "attribution_pernode_profile.csv",
        "attribution_pernode_figure.png",
        "attribution_summary.csv", "attribution_profile.csv", "attribution_figure.png",
    ],
    "ablation": [
        "event_ablation_pooled.csv", "event_ablation_persubject.csv",
        "window_event_gap.csv",
    ],
    "phaseA_appendix": [
        # corrected mag%xpen grid (v2, seeding-bug-fixed) underlying Decisions #19-#20
        "mag_pen_grid_v2_pooled.csv", "mag_pen_grid_v2_persubject.csv",
        "mag_pen_grid_v2_reproducibility_check.csv",
        # duration-stratified sensitivity, re-verified on the Decision #20 point (mag50/pen0.5)
        "duration_bucket_summary.csv", "duration_hit_persubject.csv",
        # per-subject event detail at the CURRENT (Decision #19 weight) operating points
        "szcore_event_level_new_decision19_mag60.csv",
        "szcore_event_level_new_decision19_mag50.csv",
        # Decision #19 evidence trail (weight-change round; Layers 3-4)
        "weight_candidate_crosscheck_pooled.csv",
        "weight_candidate_crosscheck_persubject.csv",
        "weight_seed_robustness_summary.csv",
        "weight_seed_robustness_raw.csv",
    ],
    "history_topology": [
        "topo_standalone_auroc.csv",
    ],
    "history_superseded": [
        # old-weight (0.35/0.30/0.35) per-subject event detail — kept ONLY for comparison.
        # Current per-subject detail lives in phaseA_appendix/ (Decision #19 weight).
        "szcore_event_level_mag60.csv",   # old-weight balanced
        "szcore_event_level_mag70.csv",   # retired high-sens operating point (mag70/pen0.3)
        # pre-_v2 mag%xpen grid — contained the seeding bug (RESULTS_OF_RECORD.md §13.2).
        # If these are found on disk they are quarantined here so they are NEVER mistaken
        # for the corrected mag_pen_grid_v2_* files in phaseA_appendix/.
        "mag_pen_grid_pooled.csv", "mag_pen_grid_persubject.csv",
    ],
}
DIR_ARTIFACTS = {
    "history_topology": ["topo_features"],
    "attribution": ["attribution_out"],
}


CATEGORY_DIRS = ("locked", "attribution", "ablation", "phaseA_appendix", "history_topology", "history_superseded")
def _in_dest(path, out_abs):
    ap = os.path.abspath(path)
    return any(ap.startswith(os.path.join(out_abs, c) + os.sep) for c in CATEGORY_DIRS)


def find_one(root, name, out_abs):
    hits = sorted(glob.glob(os.path.join(root, "**", name), recursive=True))
    return [h for h in hits if not _in_dest(h, out_abs)]


def find_in_dest(name, out_abs):
    """Categories under out/ where `name` already sits. Lets us distinguish
    'already correctly in place' and 'present but in the WRONG category (misplaced)'
    from genuinely 'missing' — needed when outputs are saved straight into results/."""
    return [c for c in CATEGORY_DIRS if os.path.exists(os.path.join(out_abs, c, name))]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="results")
    args = ap.parse_args()
    out_abs = os.path.abspath(args.out)
    print(f"[diag] consolidating from {os.path.abspath(args.root)} -> {out_abs}\n")

    manifest_lines, n_copied, n_present, n_misplaced, n_missing = [], 0, 0, 0, 0
    for cat, names in MANIFEST.items():
        os.makedirs(os.path.join(args.out, cat), exist_ok=True)
        for name in names:
            hits = find_one(args.root, name, out_abs)
            if hits:
                src = hits[0]
                shutil.copy2(src, os.path.join(args.out, cat, os.path.basename(src)))
                print(f"  [copy] {os.path.relpath(src, args.root)}  ->  {cat}/")
                manifest_lines.append(f"{cat}/{os.path.basename(src)}  <=  {os.path.abspath(src)}")
                n_copied += 1
                if len(hits) > 1:
                    print(f"         (note: {len(hits)} copies found; used first)")
                continue
            # No source outside the results/ tree. Is it already sitting in a dest category?
            in_dest = find_in_dest(name, out_abs)
            if cat in in_dest:
                print(f"  [ok]   {cat}/{name}  (already in place)")
                manifest_lines.append(f"{cat}/{name}  (already in place)")
                n_present += 1
                others = [c for c in in_dest if c != cat]
                if others:
                    print(f"         (warning: duplicate copies also in {others})")
                    manifest_lines.append(f"  DUP-WARN  {name} also in {others}")
                continue
            if in_dest:  # present, but only in the WRONG category -> misplaced
                print(f"  [MISPLACED] {name}  is in {in_dest}, expected {cat}/  -> move it manually")
                manifest_lines.append(f"MISPLACED  expected {cat}/{name}, currently in {in_dest}")
                n_misplaced += 1
                continue
            print(f"  [skip] {name}  (not found)"); n_missing += 1
            manifest_lines.append(f"MISSING  {cat}/{name}")

    for cat, dirs in DIR_ARTIFACTS.items():
        for dname in dirs:
            hits = [p for p in glob.glob(os.path.join(args.root, "**", dname), recursive=True)
                    if os.path.isdir(p) and not _in_dest(p, out_abs)]
            if not hits:
                print(f"  [skip] {dname}/  (dir not found)"); continue
            src = hits[0]; dst = os.path.join(args.out, cat, dname)
            if os.path.exists(dst):
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            nf = sum(len(f) for _, _, f in os.walk(dst))
            print(f"  [copy] {os.path.relpath(src, args.root)}/  ->  {cat}/{dname}/  ({nf} files)")
            manifest_lines.append(f"{cat}/{dname}/  <=  {os.path.abspath(src)}  ({nf} files)")

    os.makedirs(args.out, exist_ok=True)
    with open(os.path.join(args.out, "MANIFEST.txt"), "w") as f:
        f.write("# consolidated results manifest (copies; originals untouched)\n")
        f.write("\n".join(manifest_lines) + "\n")
    print(f"\n  copied {n_copied} file(s); {n_present} already in place; "
          f"{n_misplaced} MISPLACED; {n_missing} MISSING.")
    if n_misplaced:
        print("  -> MISPLACED files exist but are in the wrong category folder; move them manually, then re-run.")
    print(f"  [saved] {os.path.abspath(os.path.join(args.out, 'MANIFEST.txt'))}")
    print("  Originals were NOT modified or deleted.")


if __name__ == "__main__":
    main()