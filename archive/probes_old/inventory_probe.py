"""
================================================================================
 inventory_probe.py  —  READ-ONLY artifact discovery for the thesis repo
================================================================================
PURPOSE
    Phase A.5 decision gate, step 0. Before designing any ablation or upgrade
    experiment, we must know EXACTLY what is already cached on disk, so we know
    which experiments are "post-hoc, no retrain" (cheap) vs. "needs upstream
    rerun" (expensive). This script touches nothing -- it only reads and reports.

WHAT IT LOOKS FOR (per the 8 test subjects)
    1. Ensemble scores        {subj}_ens_inter.npy / _ens_ictal.npy   (known to exist)
    2. Component scores        any *recon*, *temporal*/*lstm*, *gamma* arrays
                               (needed for EVENT-tier ablation without retrain)
    3. Adjacency matrices      any *adj* arrays, shape (n_win, C, C)
                               (needed for topology feature AND Phase B spatial
                                localization without re-running the GAE)
    It DISCOVERS filenames by globbing, so it does not assume any naming scheme.

USAGE (Cursor / terminal)
    python inventory_probe.py --root .
    python inventory_probe.py --root results/cpd/scores --adj_root results/cpd
    # --root may be any directory; the script recurses. Give the repo root if unsure.

OUTPUT
    A per-subject table printed to stdout + a machine-readable inventory.json
    written to the current directory (so you can paste either back to me).
================================================================================
"""
import argparse
import glob
import json
import os
import numpy as np

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]

# substring patterns used to bucket discovered .npy files (lower-cased filename)
PATTERNS = {
    "ensemble":  ["_ens_", "ensemble"],
    "recon":     ["recon", "_gae", "reconstruction"],
    "temporal":  ["temporal", "_lstm", "lstm"],
    "gamma":     ["gamma", "_aec", "_hfo"],
    "adjacency": ["adj", "_adjs", "adjacency"],
}
SPLIT_TAGS = {"inter": ["inter", "interictal", "background"],
              "ictal": ["ictal", "seizure", "_sz"]}


def _safe_shape(path):
    """Read only the .npy header to get shape/dtype -- does not load the array."""
    try:
        with open(path, "rb") as f:
            version = np.lib.format.read_magic(f)
            if version == (1, 0):
                shape, fortran, dtype = np.lib.format.read_array_header_1_0(f)
            else:
                shape, fortran, dtype = np.lib.format.read_array_header_2_0(f)
        return list(shape), str(dtype)
    except Exception as e:
        return None, f"<unreadable: {e}>"


def _bucket(fname_lower):
    for kind, subs in PATTERNS.items():
        if any(s in fname_lower for s in subs):
            return kind
    return "other"


def _split(fname_lower):
    for tag, subs in SPLIT_TAGS.items():
        if any(s in fname_lower for s in subs):
            return tag
    return "?"


def scan(root, adj_root):
    files = set(glob.glob(os.path.join(root, "**", "*.npy"), recursive=True))
    if adj_root:
        files |= set(glob.glob(os.path.join(adj_root, "**", "*.npy"), recursive=True))
    inv = {s: {k: [] for k in list(PATTERNS) + ["other"]} for s in TEST_SUBJS}
    unmatched = []
    for path in sorted(files):
        base = os.path.basename(path).lower()
        subj = next((s for s in TEST_SUBJS if s in base), None)
        if subj is None:
            unmatched.append(path)
            continue
        kind = _bucket(base)
        shape, dtype = _safe_shape(path)
        inv[subj][kind].append({
            "file": os.path.relpath(path),
            "split": _split(base),
            "shape": shape,
            "dtype": dtype,
        })
    return inv, unmatched


def summarize(inv):
    print("\n" + "=" * 78)
    print(" ARTIFACT INVENTORY  (8 test subjects)")
    print("=" * 78)
    header = f"{'subj':<7} {'ensemble':<9} {'recon':<7} {'temporal':<9} {'gamma':<7} {'adjacency':<10}"
    print(header)
    print("-" * 78)
    flags = {"ensemble": True, "recon": True, "temporal": True, "gamma": True, "adjacency": True}
    for s in TEST_SUBJS:
        def mark(kind):
            n = len(inv[s][kind])
            return "yes" if n else " -"
        for kind in flags:
            if not inv[s][kind]:
                flags[kind] = False
        print(f"{s:<7} {mark('ensemble'):<9} {mark('recon'):<7} "
              f"{mark('temporal'):<9} {mark('gamma'):<7} {mark('adjacency'):<10}")
    print("-" * 78)
    print(" LEGEND: 'yes' = at least one matching .npy found for that subject.")
    print("\n FEASIBILITY READOUT")
    print("   - EVENT-tier component ablation (no retrain): "
          + ("FEASIBLE" if (flags["recon"] and flags["gamma"]) else
             "NOT directly feasible -> component scores missing for >=1 subject"))
    print("   - Topology-feature upgrade + Phase B spatial localization (no GAE retrain): "
          + ("FEASIBLE" if flags["adjacency"] else
             "NOT feasible from cache -> per-window adjacency NOT found "
             "(would need regeneration from upstream)"))
    # show one example shape of each kind, if present, to confirm structure
    print("\n EXAMPLE SHAPES (first found of each kind)")
    seen = set()
    for s in TEST_SUBJS:
        for kind in list(PATTERNS):
            for rec in inv[s][kind]:
                if kind not in seen and rec["shape"] is not None:
                    print(f"   {kind:<10} {rec['file']}  shape={rec['shape']} {rec['dtype']}")
                    seen.add(kind)
    print("=" * 78 + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".", help="repo root or scores dir (recursed)")
    ap.add_argument("--adj_root", default=None,
                    help="optional extra dir to scan for adjacency arrays")
    ap.add_argument("--out", default="inventory.json")
    args = ap.parse_args()

    inv, unmatched = scan(args.root, args.adj_root)
    summarize(inv)
    if unmatched:
        print(f" NOTE: {len(unmatched)} .npy files did not match any test subject "
              f"(showing up to 8):")
        for p in unmatched[:8]:
            print("   ", os.path.relpath(p))
        print()
    with open(args.out, "w") as f:
        json.dump({"inventory": inv, "unmatched_count": len(unmatched)}, f, indent=2)
    print(f" Wrote machine-readable inventory -> {args.out}")
    print(" Paste either the table above or inventory.json back to me.\n")


if __name__ == "__main__":
    main()