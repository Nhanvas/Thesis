"""
================================================================================
 topo_extract.py  (Script B1)  —  DIAGNOSTIC ONLY: does graph topology carry a
                                  seizure signal, especially for chb06?
================================================================================
CONTEXT
    chb06 is the one genuine limitation: ictal connectivity MAGNITUDE decreases
    (inverted wPLI/AEC), so reconstruction/gamma struggle. History (v11, Part 2.2)
    found that graph TOPOLOGY features detect chb06 through STRUCTURAL
    reorganization (standalone AUROC ~0.737) even when magnitude drops. That
    finding was made in the threshold era and rejected for a fixed-weight blend.
    Under the current CPD pipeline (bidirectional shift detection, label-free
    magnitude filter) it deserves a fresh test -- but FIRST we must confirm the
    topology signal still exists per subject. That is all this script does.

    NO ensemble integration, NO CPD here. This is the falsification gate:
      - If topology gives chb06 AUROC clearly > 0.5 in a consistent direction
        (and ideally helps other inverted-ish subjects) -> proceed to B2.
      - If it does not -> stop; topology is documented as a negative/limitation.

WHAT IT COMPUTES  (per 18x18 weighted adjacency window)
    spectral_radius : largest eigenvalue of A           (overall coupling strength)
    graph_energy    : sum |eigenvalues of A|            (total connectivity)
    fiedler         : 2nd-smallest eigenvalue of L=D-A  (algebraic connectivity /
                                                          integration vs segregation)
    degree_entropy  : Shannon entropy of normalized degree dist (uniform vs hubby)
    Then per subject, per feature: AUROC(ictal vs inter) + direction.
    spectral_radius/graph_energy are MAGNITUDE features (expected to invert for
    chb06); fiedler/degree_entropy are STRUCTURE features (the interesting ones).

ADJACENCY VARIANT
    Defaults to '*_adjs_topk20.npy' (the top-k 20% graph the GAE actually sees,
    per the locked method). Override with --variant to compare (e.g. base '_adjs').

USAGE  (Cursor / CPU)
    python topo_extract.py --root data/processed
    python topo_extract.py --root data/processed --variant _adjs        # full weighted
    python topo_extract.py --root data/processed --subj chb06           # one subject
    # outputs: topo_features/{subj}_topo_inter.npy / _ictal.npy  (n_win x 4)
    #          topo_standalone_auroc.csv
================================================================================
"""
import argparse
import glob
import os
import numpy as np

try:
    from sklearn.metrics import roc_auc_score
    HAVE_SK = True
except Exception:
    HAVE_SK = False

TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
FEATS = ["spectral_radius", "graph_energy", "fiedler", "degree_entropy"]


def _auroc(inter, ictal):
    """AUROC of ictal>inter. Returns (auroc, direction) where direction is +1 if
    ictal scores tend higher, -1 if lower. AUROC reported in [0,1] for 'ictal high'.
    The *detectability* is max(auroc, 1-auroc)."""
    y = np.concatenate([np.zeros(len(inter)), np.ones(len(ictal))])
    s = np.concatenate([inter, ictal])
    if HAVE_SK:
        a = roc_auc_score(y, s)
    else:  # manual Mann-Whitney AUROC
        order = np.argsort(s, kind="mergesort")
        ranks = np.empty_like(order, dtype=float)
        ranks[order] = np.arange(1, len(s) + 1)
        n1 = len(ictal); n0 = len(inter)
        a = (ranks[len(inter):].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)
    direction = +1 if a >= 0.5 else -1
    return float(a), direction


def _topo_features(A):
    """A: (C,C) weighted, possibly slightly asymmetric. Returns 4 scalars."""
    C = A.shape[0]
    A = (A + A.T) / 2.0
    np.fill_diagonal(A, 0.0)
    deg = A.sum(axis=1)
    # eigenvalues of A (symmetric -> eigvalsh, real)
    evA = np.linalg.eigvalsh(A)
    spectral_radius = float(np.max(np.abs(evA)))
    graph_energy = float(np.sum(np.abs(evA)))
    # Laplacian fiedler value (2nd smallest eigenvalue of L = D - A)
    L = np.diag(deg) - A
    evL = np.linalg.eigvalsh(L)
    evL = np.sort(evL)
    fiedler = float(evL[1]) if C > 1 else 0.0
    # degree entropy
    s = deg.sum()
    if s <= 1e-12:
        degree_entropy = 0.0
    else:
        p = deg / s
        p = p[p > 0]
        degree_entropy = float(-np.sum(p * np.log(p)) / np.log(C))  # normalized [0,1]
    return np.array([spectral_radius, graph_energy, fiedler, degree_entropy])


def _resolve(root, subj, split_tokens, variant, exclude_tokens=()):
    for p in sorted(glob.glob(os.path.join(root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj not in b:
            continue
        if not b.endswith(variant.lower() + ".npy"):
            continue
        if any(t in b for t in exclude_tokens):
            continue
        if any(t in b for t in split_tokens):
            return p
    return None


def _extract(adj_path):
    A = np.load(adj_path)
    if A.ndim == 2:           # single window edge-case
        A = A[None]
    if A.ndim != 3 or A.shape[1] != A.shape[2]:
        raise ValueError(f"unexpected adjacency shape {A.shape} in {adj_path}")
    return np.stack([_topo_features(A[i]) for i in range(A.shape[0])])  # (n_win,4)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="data/processed")
    ap.add_argument("--variant", default="_adjs_topk20",
                    help="adjacency filename suffix before .npy (e.g. _adjs_topk20, _adjs)")
    ap.add_argument("--subj", default=None, help="restrict to one subject")
    ap.add_argument("--out_dir", default="topo_features")
    args = ap.parse_args()
    subs = [args.subj] if args.subj else TEST_SUBJS
    os.makedirs(args.out_dir, exist_ok=True)

    rows = []
    print(f"\nADJACENCY VARIANT: *{args.variant}.npy")
    print(f"{'subj':<7} " + " ".join(f"{f[:12]:>14}" for f in FEATS) + "   (AUROC | dir)")
    print("-" * 86)
    missing = []
    for subj in subs:
        ip = _resolve(args.root, subj, ["interictal"], args.variant)
        if ip is None:
            ip = _resolve(args.root, subj, ["inter"], args.variant)
        cp = _resolve(args.root, subj, ["ictal"], args.variant,
                      exclude_tokens=["interictal", "_inter"])
        if not ip or not cp:
            missing.append((subj, ip, cp))
            print(f"{subj:<7}  [missing adjacency: inter={bool(ip)} ictal={bool(cp)}]")
            continue
        ti = _extract(ip)   # (n_inter,4)
        tc = _extract(cp)   # (n_ictal,4)
        np.save(os.path.join(args.out_dir, f"{subj}_topo_inter.npy"), ti.astype(np.float32))
        np.save(os.path.join(args.out_dir, f"{subj}_topo_ictal.npy"), tc.astype(np.float32))
        cells = []
        for j, f in enumerate(FEATS):
            a, d = _auroc(ti[:, j], tc[:, j])
            detect = max(a, 1 - a)
            cells.append(f"{detect:.3f}|{'+' if d > 0 else '-'}")
            rows.append({"subject": subj, "feature": f, "auroc_ictal_high": round(a, 4),
                         "direction": "ictal_high" if d > 0 else "ictal_low",
                         "detectability": round(detect, 4),
                         "n_inter": len(ti), "n_ictal": len(tc)})
        print(f"{subj:<7} " + " ".join(f"{c:>14}" for c in cells))

    # summary: best topology feature per subject
    print("\nBEST SINGLE TOPOLOGY FEATURE PER SUBJECT (by detectability)")
    print("-" * 60)
    bysub = {}
    for r in rows:
        bysub.setdefault(r["subject"], []).append(r)
    for subj, rs in bysub.items():
        best = max(rs, key=lambda r: r["detectability"])
        tag = ""
        if subj == "chb06":
            tag = "   <-- the limitation subject"
        print(f"  {subj:<7} {best['feature']:<16} detectability={best['detectability']:.3f} "
              f"({best['direction']}){tag}")

    if rows:
        import csv
        out_csv = "topo_standalone_auroc.csv"
        with open(out_csv, "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
            w.writeheader(); w.writerows(rows)
        print(f"\nWrote {out_csv} and per-subject topo feature arrays -> {args.out_dir}/")
    print("\nINTERPRETATION GUIDE")
    print("  detectability = max(AUROC, 1-AUROC); 0.5 = chance, higher = separable.")
    print("  For chb06, watch fiedler / degree_entropy (STRUCTURE features): if they")
    print("  show detectability clearly > magnitude features (spectral_radius/energy),")
    print("  that reproduces the 'structural reorganization' finding and justifies B2.")
    print("  Paste the table + topo_standalone_auroc.csv back to me.\n")


if __name__ == "__main__":
    main()