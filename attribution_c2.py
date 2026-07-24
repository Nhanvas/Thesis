"""
================================================================================
 attribution_c2.py  (Phase B / Stage C2)
   Consolidate seizure channel attribution into a thesis-ready result:
   attribution profile + convergent validity + interictal-null (seizure-
   specificity) + lateralization, with a per-subject "which channel" figure.
================================================================================
LOCKED CONFIG (from C1 go/no-go): feature = eigenvector centrality, graph =
_adjs_topk20 (the graph the GAE sees). Strength is computed too, only to test
CONVERGENT VALIDITY (do two independent graph statistics agree?).

WHAT IT PRODUCES (label-free, no retrain)
  1. Attribution profile  : per subject, mean |z| eigencentrality per channel
                            across that subject's seizures (+ SD), dominant
                            channels ranked, mapped to the 18 bipolar pairs/regions.
  2. Convergent validity  : Jaccard(top-k eigcent, top-k strength) per subject.
                            High -> attribution is not an artifact of one metric.
  3. Interictal null      : the CONFOUND KILLER. Random interictal window-blocks
     (seizure-specificity)  ("pseudo-seizures", matched size) are attributed the
                            same way; if their cross-block top-k consistency is
                            NOT below the real seizures' consistency, then the
                            "consistent channels" are just anatomy (always-central
                            electrodes), NOT seizure-specific. We report
                            real_consistency vs null_consistency + p.
  4. Lateralization       : LI = (sum|z|_Left - sum|z|_Right)/(sum Left+Right);
                            per-seizure dominant hemisphere + agreement fraction.
  5. Figure               : one multi-panel PNG, 18 channels x subject, colored
                            by region, error bars = SD across seizures.
  Outputs: attribution_profile.csv, attribution_summary.csv, attribution_figure.png

USAGE (Cursor / CPU)
  python attribution_c2.py --adj_root data/processed \
      --summary_dir "F:\\...\\summary" --topk 5
Requires evaluation_protocol.py importable; matplotlib installed.
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
HEMI = ["L"] * 8 + ["R"] * 8 + ["M"] * 2
REGION_COLOR = {"L-temp": "#1f77b4", "L-cent": "#4c9be8", "R-cent": "#e8794c",
                "R-temp": "#d62728", "Mid": "#7f7f7f"}


# ---------- shared with C1 ----------
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
    blocks = []
    ictal_ptr = 0
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
                local[int(win_sid[w])].append(ictal_ptr); ictal_ptr += 1
        for k in range(1, len(edf["seizures"]) + 1):
            if local[k]:
                blocks.append(np.array(local[k], dtype=int))
    return blocks, ictal_ptr


def node_strength(A):
    M = (A + np.transpose(A, (0, 2, 1))) / 2.0
    for i in range(M.shape[1]):
        M[:, i, i] = 0.0
    return M.sum(axis=2)


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


def jaccard(a, b):
    a, b = set(a), set(b)
    return len(a & b) / len(a | b) if (a | b) else 0.0


def mean_pairwise_jaccard(zlist, topk):
    tops = [set(np.argsort(z)[::-1][:topk]) for z in zlist]
    pairs = list(itertools.combinations(range(len(zlist)), 2))
    if not pairs:
        return np.nan
    return np.mean([jaccard(tops[i], tops[j]) for i, j in pairs])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--adj_root", default="data/processed")
    ap.add_argument("--summary_dir", default=".")
    ap.add_argument("--variant", default="_adjs_topk20")
    ap.add_argument("--topk", type=int, default=5)
    ap.add_argument("--n_null", type=int, default=1000)
    ap.add_argument("--subjs", default=",".join(TEST_SUBJS))
    ap.add_argument("--outdir", default="attribution_out")
    args = ap.parse_args()
    subjs = args.subjs.split(",")
    os.makedirs(args.outdir, exist_ok=True)
    rng = np.random.default_rng(0)

    prof_rows, summ_rows, fig_data = [], [], {}
    print(f"\nLOCKED: eigencentrality on *{args.variant}, top-k={args.topk}")
    print(f"{'subj':<7}{'n_sz':>5}{'realCons':>9}{'nullCons':>9}{'p_spec':>8}"
          f"{'convValid':>10}{'LI':>7}{'hemi':>6}{'latAgree':>9}  dominant channels")
    print("-" * 108)

    for subj in subjs:
        ip = find_adj(args.adj_root, subj, "inter", args.variant)
        cp = find_adj(args.adj_root, subj, "ictal", args.variant)
        if not ip or not cp:
            print(f"{subj:<7}  [adjacency missing]"); continue
        inter, ictal = np.load(ip), np.load(cp)
        blocks, total = seizure_window_blocks(subj, args.summary_dir)
        Ei, Ec = eig_centrality(inter), eig_centrality(ictal)
        Si, Sc = node_strength(inter), node_strength(ictal)
        C = Ei.shape[1]

        # per-seizure z (eigcent primary, strength for convergent validity)
        z_eig, z_str, sizes = [], [], []
        for blk in blocks:
            blk = blk[blk < len(Ec)]
            if len(blk) == 0:
                continue
            z_eig.append(z_channels(Ec[blk], Ei))
            z_str.append(z_channels(Sc[blk], Si))
            sizes.append(len(blk))
        if len(z_eig) < 2:
            continue
        Z = np.abs(np.array(z_eig))                      # (n_sz, C)
        profile = Z.mean(0); profile_sd = Z.std(0)
        dom = np.argsort(profile)[::-1][:args.topk]

        # convergent validity: eigcent-top vs strength-top per seizure
        conv = np.mean([jaccard(np.argsort(np.abs(a))[::-1][:args.topk],
                                np.argsort(np.abs(b))[::-1][:args.topk])
                        for a, b in zip(z_eig, z_str)])

        # real cross-seizure consistency
        real_cons = mean_pairwise_jaccard([np.abs(z) for z in z_eig], args.topk)

        # INTERICTAL NULL: pseudo-seizures = random interictal blocks (matched sizes)
        null_cons = np.empty(args.n_null)
        med_sz = int(np.median(sizes))
        n_blocks = len(z_eig)
        for t in range(args.n_null):
            pz = []
            for _ in range(n_blocks):
                start = rng.integers(0, max(1, len(Ei) - med_sz))
                pz.append(np.abs(z_channels(Ei[start:start + med_sz], Ei)))
            null_cons[t] = mean_pairwise_jaccard(pz, args.topk)
        p_spec = (np.sum(null_cons >= real_cons) + 1) / (args.n_null + 1)

        # lateralization (on the mean profile)
        wL = profile[np.array(HEMI) == "L"].sum()
        wR = profile[np.array(HEMI) == "R"].sum()
        LI = (wL - wR) / (wL + wR + 1e-9)
        hemi = "Left" if LI > 0.1 else ("Right" if LI < -0.1 else "Bilateral")
        # per-seizure dominant hemisphere agreement
        def sz_hemi(z):
            az = np.abs(z)
            return "L" if az[np.array(HEMI) == "L"].sum() >= az[np.array(HEMI) == "R"].sum() else "R"
        hs = [sz_hemi(z) for z in z_eig]
        lat_agree = max(hs.count("L"), hs.count("R")) / len(hs)

        dom_names = ", ".join(f"{CH_NAMES[c]}" for c in dom)
        print(f"{subj:<7}{len(z_eig):>5}{real_cons:>9.3f}{null_cons.mean():>9.3f}"
              f"{p_spec:>8.3f}{conv:>10.3f}{LI:>+7.2f}  {hemi:<9}{lat_agree:>7.2f}  {dom_names}")

        fig_data[subj] = (profile, profile_sd, LI, hemi)
        summ_rows.append(dict(subject=subj, n_seizures=len(z_eig),
                              real_consistency=round(real_cons, 3),
                              null_consistency=round(float(null_cons.mean()), 3),
                              p_seizure_specific=round(p_spec, 4),
                              convergent_validity=round(conv, 3),
                              lateralization_index=round(LI, 3),
                              dominant_hemisphere=hemi,
                              lateralization_agreement=round(lat_agree, 2),
                              dominant_channels=dom_names))
        for c in range(C):
            prof_rows.append(dict(subject=subj, ch_index=c, channel=CH_NAMES[c],
                                  region=REGION[c], hemisphere=HEMI[c],
                                  mean_abs_z=round(float(profile[c]), 4),
                                  sd_abs_z=round(float(profile_sd[c]), 4)))

    # ---------- write CSVs ----------
    if summ_rows:
        with open(os.path.join(args.outdir, "attribution_summary.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(summ_rows[0].keys())); w.writeheader(); w.writerows(summ_rows)
        with open(os.path.join(args.outdir, "attribution_profile.csv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(prof_rows[0].keys())); w.writeheader(); w.writerows(prof_rows)

    # ---------- figure ----------
    if fig_data:
        n = len(fig_data); ncol = 2; nrow = int(np.ceil(n / ncol))
        fig, axes = plt.subplots(nrow, ncol, figsize=(14, 2.5 * nrow), squeeze=False)
        colors = [REGION_COLOR[r] for r in REGION]
        for ax, (subj, (prof, sd, LI, hemi)) in zip(axes.ravel(), fig_data.items()):
            ax.bar(range(len(prof)), prof, yerr=sd, color=colors, edgecolor="k", linewidth=0.3)
            ax.set_title(f"{subj}  (LI={LI:+.2f}, {hemi})", fontsize=10)
            ax.set_xticks(range(len(CH_NAMES)))
            ax.set_xticklabels(CH_NAMES, rotation=90, fontsize=6)
            ax.set_ylabel("|z| eigcent", fontsize=8)
        for ax in axes.ravel()[len(fig_data):]:
            ax.axis("off")
        handles = [plt.Rectangle((0, 0), 1, 1, color=c) for c in REGION_COLOR.values()]
        fig.legend(handles, list(REGION_COLOR.keys()), loc="upper right", ncol=5, fontsize=8)
        fig.suptitle("Seizure channel attribution (mean |z| eigencentrality across seizures)", y=1.0)
        fig.tight_layout()
        fpath = os.path.join(args.outdir, "attribution_figure.png")
        fig.savefig(fpath, dpi=140, bbox_inches="tight")
        print(f"\nWrote {args.outdir}/attribution_summary.csv, attribution_profile.csv, {fpath}")

    print("\nREAD: real_consistency should exceed null_consistency with p_spec<0.05 "
          "(seizure-specific, not anatomy). convergent_validity high => not a metric "
          "artifact. Paste the table + send attribution_summary.csv back.\n")


if __name__ == "__main__":
    main()