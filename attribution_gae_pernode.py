"""
================================================================================
 attribution_gae_pernode.py  (Phase B / Priority-1)
   Full attribution battery on PER-NODE GAE RECONSTRUCTION ERROR
   (the method the original plan specified; model-based, ties to the GAE)
================================================================================
Runs C1 (within-patient consistency), C2 (seizure-specificity vs interictal
null + lateralization), C3 (faithfulness: mass + occlusion) on the per-node
recon-error signal dumped from the GAE, AND reports CONVERGENT VALIDITY against
the eigencentrality attribution (do the two independent attributions agree?).

Why this may beat eigencentrality: recon error is LOCAL per node, so occlusion
removes a channel's contribution cleanly (eigencentrality is holistic -> weak
occlusion). If the GAE reconstructs seizure-onset channels worse, the error
concentrates there -> stronger, model-grounded faithfulness.

Feature per channel i, per window w:  r_i(w) = per-node GAE recon error
  z_i = (mean_seizure r_i - median_inter r_i) / MAD_inter r_i     (elevated = anomalous)
Ranking / mass / occlusion use |z| (consistent with C1-C3); signed direction reported.

INPUTS
  --pernode_root  dir with {subj}_{interictal,ictal}_pernode.npy   ([n_win,18])
  --adj_root      dir with {subj}_{...}_adjs_topk20.npy  (for eigencentrality)
  --summary_dir   dir with chbXX-summary.txt

USAGE (Cursor / CPU)
  python attribution_gae_pernode.py --pernode_root data/processed/pernode \
      --adj_root data/processed --summary_dir "F:\\...\\summary" --outdir results/phaseB
Requires evaluation_protocol.py importable; matplotlib.
================================================================================
"""
import argparse
import csv
import glob
import itertools
import os
import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

import evaluation_protocol as E
WIN_SEC = E.WIN_SEC
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CH_NAMES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
            "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
            "FZ-CZ", "CZ-PZ"]
REGION = (["L-temp"] * 4 + ["L-cent"] * 4 + ["R-cent"] * 4 + ["R-temp"] * 4 + ["Mid"] * 2)
HEMI = np.array(["L"] * 8 + ["R"] * 8 + ["M"] * 2)
REGION_COLOR = {"L-temp": "#1f77b4", "L-cent": "#4c9be8", "R-cent": "#e8794c",
                "R-temp": "#d62728", "Mid": "#7f7f7f"}


def find_file(root, subj, split, must_suffix):
    excl = ["interictal", "_inter"] if split == "ictal" else []
    toks = ["interictal", "inter"] if split == "inter" else ["ictal"]
    for p in sorted(glob.glob(os.path.join(root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj not in b or not b.endswith(must_suffix.lower() + ".npy"):
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


def z_channels(block_feat, inter_feat):
    med = np.median(inter_feat, axis=0)
    mad = np.median(np.abs(inter_feat - med), axis=0) + 1e-9
    return (block_feat.mean(axis=0) - med) / mad


def per_window_abs_z(F_win, inter_feat):
    med = np.median(inter_feat, axis=0)
    mad = np.median(np.abs(inter_feat - med), axis=0) + 1e-9
    return np.abs((F_win - med) / mad)


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 0.0


def topk_set(vec, k):
    return set(np.argsort(vec)[::-1][:k])


def mean_pairwise_jaccard(vecs, k):
    tops = [topk_set(v, k) for v in vecs]
    pairs = list(itertools.combinations(range(len(vecs)), 2))
    return np.mean([jaccard(tops[i], tops[j]) for i, j in pairs]) if pairs else np.nan


def auroc(neg, pos):
    s = np.concatenate([neg, pos]); order = np.argsort(s, kind="mergesort")
    ranks = np.empty(len(s)); ranks[order] = np.arange(1, len(s) + 1)
    n1, n0 = len(pos), len(neg)
    return (ranks[len(neg):].sum() - n1 * (n1 + 1) / 2) / (n1 * n0)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--pernode_root", default="data/processed")
    ap.add_argument("--adj_root", default="data/processed")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--variant", default="_adjs_topk20")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--n_null", type=int, default=1000)
    ap.add_argument("--n_rand", type=int, default=500)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="results/phaseB")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(0)
    k = args.topk

    # ---- startup diagnostic: where are the per-node files? ----
    def _scan(base):
        return sorted(glob.glob(os.path.join(base, "**", "*pernode*.npy"), recursive=True))
    found = _scan(args.pernode_root)
    if not found:
        for alt in [args.adj_root, "."]:
            found = _scan(alt)
            if found:
                print(f"[diag] no *pernode*.npy under '{args.pernode_root}', "
                      f"but FOUND under '{alt}'. Use --pernode_root {alt}")
                break
    print(f"[diag] pernode files visible: {len(found)}"
          + ("" if not found else "  e.g. " + os.path.abspath(found[0])))
    if not found:
        print(f"[diag] Searched '{os.path.abspath(args.pernode_root)}' (recursive) and "
              f"found none. Check the download location / --pernode_root.")
    print(f"[diag] outputs will be written to: {os.path.abspath(args.outdir)}")

    print(f"\nATTRIBUTION on PER-NODE GAE RECON ERROR (top-k={k})   [eigcent comparison]")
    print(f"{'subj':<7}{'n_sz':>5}{'segOK':>6}{'cons':>7}{'null':>7}{'pCons':>7}"
          f"{'pSpec':>7}{'topkMass':>9}{'pOccl':>7}{'convEig':>8}{'LI':>7}  dominant (recon)")
    print("-" * 118)
    summ, prof_rows, fig_data = [], [], {}
    n_occl_pass = n_spec_pass = n_cons_pass = 0
    for subj in subjs:
        pi = (find_file(args.pernode_root, subj, "inter", "_pernode")
              or find_file(args.adj_root, subj, "inter", "_pernode")
              or find_file(".", subj, "inter", "_pernode"))
        pc = (find_file(args.pernode_root, subj, "ictal", "_pernode")
              or find_file(args.adj_root, subj, "ictal", "_pernode")
              or find_file(".", subj, "ictal", "_pernode"))
        ai = find_file(args.adj_root, subj, "inter", args.variant)
        ac = find_file(args.adj_root, subj, "ictal", args.variant)
        if not (pi and pc):
            print(f"{subj:<7}  [pernode missing]"); continue
        Ri, Rc = np.load(pi), np.load(pc)              # per-node recon error [n,18]
        C = Ri.shape[1]
        blocks, total = seizure_window_blocks(subj, args.summary_dir)
        seg_ok = (total == len(Rc))

        # eigencentrality (for convergent validity), if adjacency present
        have_eig = bool(ai and ac)
        if have_eig:
            Ei, Ec = eig_centrality(np.load(ai)), eig_centrality(np.load(ac))

        z_recon, z_eig_top, sizes = [], [], []
        for blk in blocks:
            blk = blk[blk < len(Rc)]
            if len(blk) == 0:
                continue
            z_recon.append(np.abs(z_channels(Rc[blk], Ri)))
            sizes.append(len(blk))
            if have_eig:
                be = blk[blk < len(Ec)]
                if len(be):
                    z_eig_top.append(topk_set(np.abs(z_channels(Ec[be], Ei)), k))
        if len(z_recon) < 2:
            continue
        Z = np.array(z_recon)                          # (n_sz, C)
        profile = Z.mean(0); profile_sd = Z.std(0)
        dom = np.argsort(profile)[::-1][:k]

        # C1 consistency vs random-set null
        real_cons = mean_pairwise_jaccard(z_recon, k)
        null = np.empty(args.n_null)
        for t in range(args.n_null):
            rt = [set(rng.choice(C, k, replace=False)) for _ in z_recon]
            pr = list(itertools.combinations(range(len(z_recon)), 2))
            null[t] = np.mean([jaccard(rt[i], rt[j]) for i, j in pr])
        p_cons = (np.sum(null >= real_cons) + 1) / (args.n_null + 1)

        # C2 seizure-specificity: pseudo-seizure interictal blocks
        med_sz = int(np.median(sizes)); nb = len(z_recon)
        spec_null = np.empty(args.n_null)
        for t in range(args.n_null):
            pz = []
            for _ in range(nb):
                st = rng.integers(0, max(1, len(Ri) - med_sz))
                pz.append(np.abs(z_channels(Ri[st:st + med_sz], Ri)))
            spec_null[t] = mean_pairwise_jaccard(pz, k)
        p_spec = (np.sum(spec_null >= real_cons) + 1) / (args.n_null + 1)

        # C3 faithfulness: mass + occlusion on the per-node recon anomaly
        Ai = per_window_abs_z(Rc, Ri)                  # ictal (n_ic,C)
        Bi = per_window_abs_z(Ri, Ri)                  # inter (n_in,C)
        consensus = np.argsort(Ai.mean(0))[::-1][:k]   # subject-level top-k for occlusion
        total_mass = Ai.sum()
        topk_mass = Ai[:, dom].sum() / (total_mass + 1e-9)

        def score(M, keep):
            return M[:, keep].sum(axis=1)
        keep_all = np.arange(C)
        a_full = auroc(score(Bi, keep_all), score(Ai, keep_all))
        keep_topk = np.array([c for c in range(C) if c not in set(dom)])
        a_topk = auroc(score(Bi, keep_topk), score(Ai, keep_topk))
        d_topk = a_full - a_topk
        rand_drops = np.empty(args.n_rand)
        for t in range(args.n_rand):
            drop = rng.choice(C, k, replace=False)
            keep = np.array([c for c in range(C) if c not in set(drop)])
            rand_drops[t] = a_full - auroc(score(Bi, keep), score(Ai, keep))
        p_occl = (np.sum(rand_drops >= d_topk) + 1) / (args.n_rand + 1)

        # convergent validity: recon top-k vs eigcent top-k per seizure
        conv_eig = np.nan
        if have_eig and z_eig_top:
            recon_tops = [topk_set(z, k) for z in z_recon[:len(z_eig_top)]]
            conv_eig = np.mean([jaccard(recon_tops[i], z_eig_top[i])
                                for i in range(len(z_eig_top))])

        wL = profile[HEMI == "L"].sum(); wR = profile[HEMI == "R"].sum()
        LI = (wL - wR) / (wL + wR + 1e-9)
        n_cons_pass += int(real_cons > 1.5 * null.mean() and p_cons < 0.05)
        n_spec_pass += int(p_spec < 0.05)
        n_occl_pass += int(p_occl < 0.05 and d_topk > 0)
        dom_names = ", ".join(CH_NAMES[c] for c in dom)
        print(f"{subj:<7}{len(z_recon):>5}{str(seg_ok):>6}{real_cons:>7.3f}"
              f"{null.mean():>7.3f}{p_cons:>7.3f}{p_spec:>7.3f}{topk_mass:>9.3f}"
              f"{p_occl:>7.3f}{conv_eig:>8.3f}{LI:>+7.2f}  {dom_names}")
        fig_data[subj] = (profile, profile_sd, LI)
        summ.append(dict(subject=subj, n_seizures=len(z_recon), seg_ok=seg_ok,
                         consistency=round(real_cons, 3), cons_null=round(float(null.mean()), 3),
                         p_consistency=round(p_cons, 4), p_seizure_specific=round(p_spec, 4),
                         topk_mass=round(float(topk_mass), 3), p_occlusion=round(p_occl, 4),
                         convergent_vs_eigcent=None if np.isnan(conv_eig) else round(float(conv_eig), 3),
                         lateralization_index=round(float(LI), 3),
                         dominant_channels=dom_names))
        for c in range(C):
            prof_rows.append(dict(subject=subj, ch_index=c, channel=CH_NAMES[c],
                                  region=REGION[c], hemisphere=HEMI[c],
                                  mean_abs_z=round(float(profile[c]), 4),
                                  sd_abs_z=round(float(profile_sd[c]), 4)))
    print("-" * 118)
    print(f"  SUMMARY (per-node recon):  consistency {n_cons_pass}/{len(summ)}  |  "
          f"seizure-specific {n_spec_pass}/{len(summ)}  |  faithful(occl) {n_occl_pass}/{len(summ)}")
    print(f"  COMPARE to eigencentrality (C1-C3): consistency 7/8, specific 5/8, faithful 3/8.")

    if summ:
        with open(os.path.join(args.outdir, "attribution_pernode_summary.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summ[0].keys())); w.writeheader(); w.writerows(summ)
        with open(os.path.join(args.outdir, "attribution_pernode_profile.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(prof_rows[0].keys())); w.writeheader(); w.writerows(prof_rows)
        print(f"  [saved] {os.path.abspath(os.path.join(args.outdir, 'attribution_pernode_summary.csv'))}")
        print(f"  [saved] {os.path.abspath(os.path.join(args.outdir, 'attribution_pernode_profile.csv'))}")
    else:
        print("  [warn] no subjects processed -> no CSV written (fix pernode path above).")
    if fig_data:
        n = len(fig_data); ncol = 2; nrow = int(np.ceil(n / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(14, 2.5 * nrow), squeeze=False)
        colors = [REGION_COLOR[r] for r in REGION]
        for ax, (subj, (prof, sd, LI)) in zip(axes.ravel(), fig_data.items()):
            ax.bar(range(len(prof)), prof, yerr=sd, color=colors, edgecolor="k", linewidth=0.3)
            ax.set_title(f"{subj}  (LI={LI:+.2f})", fontsize=10)
            ax.set_xticks(range(len(CH_NAMES))); ax.set_xticklabels(CH_NAMES, rotation=90, fontsize=6)
            ax.set_ylabel("|z| recon", fontsize=8)
        for ax in axes.ravel()[len(fig_data):]:
            ax.axis("off")
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in REGION_COLOR.values()]
        fig.legend(handles, list(REGION_COLOR.keys()), loc="upper right", ncol=5, fontsize=8)
        fig.suptitle("GAE per-node reconstruction-error attribution (mean |z| across seizures)", y=1.0)
        fig.tight_layout()
        _fp = os.path.join(args.outdir, "attribution_pernode_figure.png")
        fig.savefig(_fp, dpi=140, bbox_inches="tight")
        print(f"  [saved] {os.path.abspath(_fp)}")
    print("\n  Paste the table + the SUMMARY line back to me (and attribution_pernode_summary.csv).\n")


if __name__ == "__main__":
    main()