"""
================================================================================
 attribution_c1.py  (Phase B / Stage C1)
   Seizure channel attribution + within-patient consistency GO/NO-GO
================================================================================
GOAL
    Label-free, no-retrain proof-of-concept for Phase B spatial attribution.
    For each seizure, rank the 18 channels by how anomalous their graph
    node-strength (and eigenvector centrality) is during the seizure vs the
    channel's own interictal baseline. Then ask the decisive question:
    ARE the top-k channels CONSISTENT across a patient's seizures (above a
    random null)?  If not, we do NOT claim localization (per the literature:
    within-patient consistency is the accepted proxy when CHB-MIT has no SOZ
    ground truth).

METHOD (all from cached adjacency; CPU; no labels; no GAE)
    strength_i(w)   = sum_j A_ij(w)                     (node degree/strength)
    eigcent_i(w)    = |principal eigenvector of A(w)|_i (eigenvector centrality)
    per channel, z vs interictal:  z_i = (mean_seizure - median_inter) / MAD_inter
    rank channels by |z_i| (drives the shift, either direction).
    Ictal windows are segmented per-seizure by replicating szcore_eval's exact
    window labelling (labels[:tl].reshape(n_win, WIN_SEC).max), so block i of the
    ictal adjacency array == seizure i. A hard check asserts
        sum(per-seizure ictal windows from summary) == len(ictal adjacency array)
    (mirrors the B2 baseline-fidelity self-check; if it fails, ordering is off).

CONSISTENCY (go/no-go)
    within-patient: mean pairwise Jaccard of top-k channel sets across the
    subject's seizures, and mean Spearman of full |z| vectors. Compared to the
    random-null expected Jaccard (k=5 of 18 ~ 0.16) and a shuffle-null p-value.

USAGE (Cursor / CPU)
    python attribution_c1.py --adj_root data/processed \
        --summary_dir "F:\\...\\summary" --variant _adjs_topk20 --topk 5
    # also try --variant _adjs (full weighted) as a robustness check
Requires evaluation_protocol.py importable (for the summary parser + WIN_SEC).
================================================================================
"""
import argparse
import glob
import itertools
import os
import numpy as np

import evaluation_protocol as E   # parse_summary_edf_list, WIN_SEC

WIN_SEC = E.WIN_SEC
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]


# ---------------------------------------------------------------- data access
def find_adj(adj_root, subj, split, variant):
    excl = ["interictal", "_inter"] if split == "ictal" else []
    toks = ["interictal", "inter"] if split == "inter" else ["ictal"]
    for p in sorted(glob.glob(os.path.join(adj_root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj not in b or not b.endswith(variant.lower() + ".npy"):
            continue
        if any(t in b for t in excl):
            continue
        if any(t in b for t in toks):
            return p
    return None


def seizure_window_blocks(subj, summary_dir):
    """Replicate szcore_eval window labelling to map each seizure -> the list of
    global ictal-window indices (in the order the ictal adjacency array is stored).
    Returns (blocks, total) where blocks[i] = np.array of indices for seizure i."""
    edfs = E.parse_summary_edf_list(os.path.join(summary_dir, f"{subj}-summary.txt"))
    blocks = []
    ictal_ptr = 0
    for edf in edfs:
        dur = int(edf["duration_s"])
        n_win = dur // WIN_SEC
        tl = n_win * WIN_SEC
        # per-second seizure id (1..S); 0 = non-ictal. Later seizure wins on overlap.
        sid = np.zeros(dur, dtype=np.int32)
        for k, (on, off) in enumerate(edf["seizures"], start=1):
            on = min(on, dur); off = min(off, dur)
            sid[on:off] = k
        if tl == 0:
            continue
        win_sid = sid[:tl].reshape(n_win, WIN_SEC).max(axis=1)  # window's seizure id
        wl = (win_sid > 0)
        # assign consecutive ictal windows to their seizure, advancing ictal_ptr
        local_seiz = {k: [] for k in range(1, len(edf["seizures"]) + 1)}
        for w in range(n_win):
            if wl[w]:
                local_seiz[int(win_sid[w])].append(ictal_ptr)
                ictal_ptr += 1
        for k in range(1, len(edf["seizures"]) + 1):
            if local_seiz[k]:
                blocks.append(np.array(local_seiz[k], dtype=int))
    return blocks, ictal_ptr


# ---------------------------------------------------------------- attribution
def node_strength(A):           # A: (n,C,C) -> (n,C)
    M = (A + np.transpose(A, (0, 2, 1))) / 2.0
    for i in range(M.shape[1]):
        M[:, i, i] = 0.0
    return M.sum(axis=2)


def eig_centrality(A):          # (n,C,C) -> (n,C) principal eigenvector |.|
    out = np.empty((A.shape[0], A.shape[1]))
    for w in range(A.shape[0]):
        M = (A[w] + A[w].T) / 2.0
        np.fill_diagonal(M, 0.0)
        vals, vecs = np.linalg.eigh(M)
        v = np.abs(vecs[:, -1])
        s = v.sum()
        out[w] = v / s if s > 0 else v
    return out


def robust_z_channels(seiz_feat, inter_feat):
    """seiz_feat: (n_seiz_win, C), inter_feat: (n_inter, C).
    Returns z per channel = (mean_seizure - median_inter)/MAD_inter."""
    med = np.median(inter_feat, axis=0)
    mad = np.median(np.abs(inter_feat - med), axis=0) + 1e-9
    return (seiz_feat.mean(axis=0) - med) / mad


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 0.0


def consistency(rankings, topk, C, n_perm=2000, seed=0):
    """rankings: list of |z| vectors (one per seizure). Returns dict."""
    if len(rankings) < 2:
        return None
    tops = [set(np.argsort(r)[::-1][:topk]) for r in rankings]
    pairs = list(itertools.combinations(range(len(rankings)), 2))
    obs_j = np.mean([jaccard(tops[i], tops[j]) for i, j in pairs])
    # Spearman of full |z| vectors (rank corr)
    def spearman(x, y):
        rx = np.argsort(np.argsort(x)); ry = np.argsort(np.argsort(y))
        rx = rx - rx.mean(); ry = ry - ry.mean()
        d = np.sqrt((rx**2).sum() * (ry**2).sum())
        return (rx * ry).sum() / d if d > 0 else 0.0
    obs_s = np.mean([spearman(rankings[i], rankings[j]) for i, j in pairs])
    # shuffle null on top-k Jaccard: random top-k sets
    rng = np.random.default_rng(seed)
    null = np.empty(n_perm)
    for p in range(n_perm):
        rt = [set(rng.choice(C, topk, replace=False)) for _ in rankings]
        null[p] = np.mean([jaccard(rt[i], rt[j]) for i, j in pairs])
    pval = (np.sum(null >= obs_j) + 1) / (n_perm + 1)
    return dict(mean_jaccard=obs_j, null_mean=float(null.mean()),
                mean_spearman=obs_s, p_value=pval, n_seiz=len(rankings))


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adj_root", default="data/processed")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--variant", default="_adjs_topk20")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--feature", default="strength", choices=["strength", "eigcent", "both"])
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    feats = ["strength", "eigcent"] if args.feature == "both" else [args.feature]

    print(f"\nVARIANT=*{args.variant}  top-k={args.topk}  WIN_SEC={WIN_SEC}")
    print("random-null expected Jaccard (k=%d of 18) ~ %.3f" %
          (args.topk, (args.topk * args.topk / 18) /
           (2 * args.topk - args.topk * args.topk / 18)))
    print("=" * 90)

    for feat in feats:
        print(f"\n########## FEATURE = {feat} ##########")
        print(f"{'subj':<7}{'n_sz':>5}{'segOK':>7}{'meanJacc':>10}{'nullJ':>8}"
              f"{'Spear':>8}{'p':>8}   top-channels(most frequent in top-k)")
        print("-" * 90)
        n_pass = n_multi = 0
        for subj in subjs:
            ip = find_adj(args.adj_root, subj, "inter", args.variant)
            cp = find_adj(args.adj_root, subj, "ictal", args.variant)
            if not ip or not cp:
                print(f"{subj:<7}  [adjacency missing]")
                continue
            inter = np.load(ip); ictal = np.load(cp)
            blocks, total = seizure_window_blocks(subj, args.summary_dir)
            seg_ok = (total == len(ictal))
            feat_fn = node_strength if feat == "strength" else eig_centrality
            F_inter = feat_fn(inter)
            F_ictal = feat_fn(ictal)
            C = F_inter.shape[1]
            rankings = []
            topk_counter = np.zeros(C, dtype=int)
            for blk in blocks:
                blk = blk[blk < len(F_ictal)]      # guard if seg_ok is False
                if len(blk) == 0:
                    continue
                z = robust_z_channels(F_ictal[blk], F_inter)
                rankings.append(np.abs(z))
                for c in np.argsort(np.abs(z))[::-1][:args.topk]:
                    topk_counter[c] += 1
            con = consistency(rankings, args.topk, C)
            top_ch = ",".join(str(c) for c in np.argsort(topk_counter)[::-1][:args.topk])
            if con:
                n_multi += 1
                passed = (con["mean_jaccard"] > con["null_mean"] * 1.5 and con["p_value"] < 0.05)
                n_pass += int(passed)
                flag = " *" if passed else ""
                print(f"{subj:<7}{con['n_seiz']:>5}{str(seg_ok):>7}"
                      f"{con['mean_jaccard']:>10.3f}{con['null_mean']:>8.3f}"
                      f"{con['mean_spearman']:>8.3f}{con['p_value']:>8.3f}{flag}   [{top_ch}]")
            else:
                print(f"{subj:<7}{len(rankings):>5}{str(seg_ok):>7}"
                      f"{'--':>10}{'--':>8}{'--':>8}{'--':>8}   [{top_ch}]  (single seizure)")
        print("-" * 90)
        print(f"  GO/NO-GO: {n_pass}/{n_multi} multi-seizure subjects show top-k "
              f"consistency above null (Jacc>1.5x null AND p<0.05).")
        print("  '*' = that subject passes. Read the falsification from this fraction.")
    print("\nPaste the whole output back to me (both features if you used --feature both).\n")


if __name__ == "__main__":
    main()