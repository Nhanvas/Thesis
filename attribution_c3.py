"""
================================================================================
 attribution_c3.py  (Phase B / Stage C3)  —  FAITHFULNESS of the attribution
================================================================================
QUESTION reviewers ask: "are the attributed channels actually LOAD-BEARING for
the connectivity anomaly, or merely correlated with it?"  Two CPU-only tests,
no GAE / no GPU, on the same eigencentrality-anomaly used for detection's
connectivity component:

  (1) ATTRIBUTION-MASS CONCENTRATION.
      Per-window anomaly of channel i:  a_i(w) = |(eigcent_i(w) - med_inter_i)/MAD_inter_i|.
      Over a subject's ictal windows, what fraction of total anomaly mass
      sum_i a_i sits in the top-k attributed channels?  Random baseline = k/C.
      >> k/C  =>  attribution is concentrated / load-bearing, not diffuse.

  (2) OCCLUSION.
      Window anomaly score S(w) = sum_i a_i(w) (all channels) separates ictal
      from interictal windows -> AUROC_full. Drop the subject's consensus top-k
      channels (S computed over the remaining C-k) -> AUROC_drop_topk.
      Drop random k channels (averaged) -> AUROC_drop_rand.
      If dropping top-k collapses the ictal/inter separability MORE than dropping
      random-k, the attributed channels carry the seizure-discriminative signal
      => the attribution is FAITHFUL.
      (Scope: faithfulness w.r.t. the CONNECTIVITY anomaly. Tying it to the full
       GAE ensemble would need GPU inference and is left as future work.)

PRE-REGISTERED FALSIFICATION
  For the majority of subjects: top-k mass >> k/C AND
  (AUROC_full - AUROC_drop_topk) clearly > (AUROC_full - AUROC_drop_rand).
  If not, attribution is not faithful -> claim "consistent" only, not "load-bearing".

USAGE (Cursor / CPU)
  python attribution_c3.py --adj_root data/processed \
      --summary_dir "F:\\...\\summary" --topk 5
Requires evaluation_protocol.py importable.
================================================================================
"""
import argparse
import glob
import os
import numpy as np

import evaluation_protocol as E
WIN_SEC = E.WIN_SEC
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CH_NAMES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
            "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
            "FZ-CZ", "CZ-PZ"]


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
    edfs = E.parse_summary_edf_list(os.path.join(summary_dir, f"{subj}-summary.txt"))
    blocks, ptr = [], 0
    for edf in edfs:
        dur = int(edf["duration_s"]); n_win = dur // WIN_SEC; tl = n_win * WIN_SEC
        if tl == 0:
            continue
        sid = np.zeros(dur, dtype=np.int32)
        for k, (on, off) in enumerate(edf["seizures"], start=1):
            sid[min(on, dur):min(off, dur)] = k
        win_sid = sid[:tl].reshape(n_win, WIN_SEC).max(axis=1)
        local = {k: [] for k in range(1, len(edf["seizures"]) + 1)}
        for w in range(n_win):
            if win_sid[w] > 0:
                local[int(win_sid[w])].append(ptr); ptr += 1
        for k in range(1, len(edf["seizures"]) + 1):
            if local[k]:
                blocks.append(np.array(local[k], dtype=int))
    return blocks, ptr


def eig_centrality(A):
    out = np.empty((A.shape[0], A.shape[1]))
    for w in range(A.shape[0]):
        M = (A[w] + A[w].T) / 2.0
        np.fill_diagonal(M, 0.0)
        _, vecs = np.linalg.eigh(M)
        v = np.abs(vecs[:, -1]); s = v.sum()
        out[w] = v / s if s > 0 else v
    return out


def node_strength(A):
    M = (A + np.transpose(A, (0, 2, 1))) / 2.0
    for i in range(M.shape[1]):
        M[:, i, i] = 0.0
    return M.sum(axis=2)


def auroc(neg, pos):
    y = np.concatenate([np.zeros(len(neg)), np.ones(len(pos))])
    s = np.concatenate([neg, pos])
    order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    n1, n0 = len(pos), len(neg)
    return (ranks[len(neg):].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adj_root", default="data/processed")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--variant", default="_adjs_topk20")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--n_rand", type=int, default=500)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    rng = np.random.default_rng(0)

    print(f"\nFAITHFULNESS  (eigencentrality on *{args.variant}, top-k={args.topk})")
    print(f"random mass baseline k/C = {args.topk}/18 = {args.topk/18:.3f}")
    print(f"{'subj':<7}{'topkMass':>9}{'pMass':>7}{'AUROCful':>9}"
          f"{'ΔTopk':>8}{'ΔRand':>8}{'pOccl':>8}{'faith':>7}")
    print("-" * 72)
    n_pass = n_tot = 0
    for subj in subjs:
        ip = find_adj(args.adj_root, subj, "inter", args.variant)
        cp = find_adj(args.adj_root, subj, "ictal", args.variant)
        if not ip or not cp:
            print(f"{subj:<7}  [adjacency missing]"); continue
        inter, ictal = np.load(ip), np.load(cp)
        # RANK by eigencentrality (stable selector); PROBE faithfulness by node-
        # strength (local -> occlusion cleanly removes a channel's contribution).
        Ec_e, Ei_e = eig_centrality(ictal), eig_centrality(inter)
        me = np.median(Ei_e, axis=0); ae = np.median(np.abs(Ei_e - me), axis=0) + 1e-9
        C = Ei_e.shape[1]
        Sc, Si = node_strength(ictal), node_strength(inter)
        ms = np.median(Si, axis=0); as_ = np.median(np.abs(Si - ms), axis=0) + 1e-9
        Ai = np.abs((Sc - ms) / as_)           # ictal strength-anomaly  (n_ic, C)
        Bi = np.abs((Si - ms) / as_)           # inter strength-anomaly  (n_in, C)

        # consensus top-k by EIGENCENTRALITY attribution (matches C2)
        blocks, total = seizure_window_blocks(subj, args.summary_dir)
        prof = np.zeros(C); nb = 0
        for blk in blocks:
            blk = blk[blk < len(Ec_e)]
            if len(blk):
                prof += np.abs((Ec_e[blk] - me) / ae).mean(0); nb += 1
        prof /= max(nb, 1)
        topk = np.argsort(prof)[::-1][:args.topk]

        # (1) attribution-mass concentration over ictal windows
        total_mass = Ai.sum()
        topk_mass = Ai[:, topk].sum() / (total_mass + 1e-9)
        rand_mass = args.topk / C

        # (2) occlusion: window score = sum over kept channels
        def score(M, keep):
            return M[:, keep].sum(axis=1)
        keep_all = np.arange(C)
        auroc_full = auroc(score(Bi, keep_all), score(Ai, keep_all))
        keep_topk = np.array([c for c in range(C) if c not in set(topk)])
        auroc_topk = auroc(score(Bi, keep_topk), score(Ai, keep_topk))
        rand_drops = np.empty(args.n_rand); rand_masses = np.empty(args.n_rand)
        for t in range(args.n_rand):
            drop = rng.choice(C, args.topk, replace=False)
            keep = np.array([c for c in range(C) if c not in set(drop)])
            rand_drops[t] = auroc_full - auroc(score(Bi, keep), score(Ai, keep))
            rand_masses[t] = Ai[:, drop].sum() / (total_mass + 1e-9)
        d_rand = float(rand_drops.mean())
        d_topk = auroc_full - auroc_topk
        # significance: is the attributed-channel effect beyond the random distribution?
        p_occl = (np.sum(rand_drops >= d_topk) + 1) / (args.n_rand + 1)
        p_mass = (np.sum(rand_masses >= topk_mass) + 1) / (args.n_rand + 1)
        faithful = (p_occl < 0.05) and (d_topk > 0)
        n_tot += 1; n_pass += int(faithful)
        print(f"{subj:<7}{topk_mass:>9.3f}{p_mass:>7.3f}{auroc_full:>9.3f}"
              f"{d_topk:>+8.3f}{d_rand:>+8.3f}{p_occl:>8.3f}"
              f"{'  yes' if faithful else '   no':>7}")
    print("-" * 72)
    print(f"  FAITHFUL: {n_pass}/{n_tot} subjects (occlusion drop significantly > random, "
          f"p_occl<0.05).")
    print("  ΔTopk = AUROC lost by dropping the attributed channels; should exceed ΔRand.")
    print("\n  Paste the table back to me.\n")


if __name__ == "__main__":
    main()