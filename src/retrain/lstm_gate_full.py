"""
lstm_gate_full.py — COMPLETE Gate R-LSTM (PREREG_02 §5): L1 + L2 + L3 + L4 in ONE inference pass.
No retraining. Auto-discovers all inputs under /kaggle/input and TOLERATES Kaggle's dataset extraction
(checkpoints unpacked into directories) by re-zipping them back into loadable .pt on the fly.
"""
import argparse, glob, os, re, csv, shutil, random
from pathlib import Path
import numpy as np
import torch

import gae_joint as G
import lstm_temporal as T

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TRAIN_SUBJS = ["chb01","chb02","chb04","chb05","chb07","chb08","chb09","chb12","chb19","chb20","chb21","chb23"]
TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
L = 16; CANON = 42; L1_BAR = 0.60; L3_BAR = 0.05


def robust_z(raw_i, raw_c):
    allx = np.concatenate([raw_i, raw_c]); med = np.median(allx); mad = np.median(np.abs(allx - med)) + 1e-9
    return (raw_i - med) / mad, (raw_c - med) / mad


# ---------- checkpoint discovery + Kaggle-extraction-tolerant loader ----------
def find_ckpts(root, prefix):
    """Return {seed: ('file', Path) | ('dir', Path)} for a given checkpoint prefix.
    Prefers an intact .pt file over an unpacked directory. Matches prefix in the file name
    OR its enclosing folder path (Kaggle unpacks .pt into folders named like the checkpoint)."""
    p = Path(root); byseed = {}
    for c in p.rglob("*.pt"):                    # intact .pt files
        if prefix in c.name:
            m = re.search(r"seed(\d+)", c.name)
            if m:
                byseed.setdefault(int(m.group(1)), []).append(("file", c, c.stat().st_size))
    for dpk in p.rglob("data.pkl"):              # unpacked torch dirs (Kaggle extraction)
        d = dpk.parent
        if prefix in str(d):
            m = re.search(rf"{re.escape(prefix)}(\d+)", str(d))
            if m:
                byseed.setdefault(int(m.group(1)), []).append(("dir", d, -1))
    out = {}
    for sd, lst in byseed.items():
        files = [x for x in lst if x[0] == "file"]
        pick = sorted(files, key=lambda x: -x[2])[0] if files else lst[0]
        out[sd] = (pick[0], pick[1])
    if not out:
        raise FileNotFoundError(f"No '{prefix}*' ckpt under {p}. sample: {[str(x) for x in list(p.rglob('data.pkl'))[:6]]}")
    return out


def load_state(entry, work="/kaggle/working"):
    kind, path = entry
    if kind == "file":
        return torch.load(str(path), map_location="cpu")
    z = f"{work}/_rez_{path.name}_{random.randint(0,10**6)}"      # re-zip unpacked dir -> .pt
    shutil.make_archive(z, "zip", root_dir=str(path.parent), base_dir=path.name)
    os.replace(z + ".zip", z + ".pt")
    return torch.load(z + ".pt", map_location="cpu")


# ---------- data discovery ----------
def find_data_dir(root, sample_glob):
    hits = list(Path(root).rglob(sample_glob))
    if not hits:
        raise FileNotFoundError(f"'{sample_glob}' not found under {root}. top: {[str(x) for x in Path(root).glob('*')]}")
    return str(hits[0].parent)


def find_gamma_dir(root):
    for d in Path(root).rglob("*"):
        if d.is_dir() and "gamma" in d.name.lower() and any(x.suffix == ".npy" for x in d.iterdir() if x.is_file()):
            return str(d)
    hits = list(Path(root).rglob("*gamma*.npy"))
    if hits: return str(hits[0].parent)
    raise FileNotFoundError(f"gamma dir not found under {root}")


def load_gamma(gdir, subj, split):
    want_inter = (split == "inter")
    for c in sorted(glob.glob(f"{gdir}/*{subj}*")):
        b = os.path.basename(c).lower()
        if not b.endswith(".npy"): continue
        is_inter = "inter" in b; is_ictal = ("ictal" in b) and not is_inter
        if (want_inter and is_inter) or ((not want_inter) and is_ictal):
            return np.load(c).astype(np.float32)
    raise FileNotFoundError(f"gamma {subj}/{split} not in {gdir}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input_root", default="/kaggle/input")
    ap.add_argument("--suffix", default="_topk20")
    ap.add_argument("--out_dir", default="/kaggle/working/gate_out")
    a = ap.parse_args()
    dev = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"device={dev}")

    root = a.input_root
    adj_dir = find_data_dir(root, f"chb13_interictal_adjs{a.suffix}.npy")
    feat_dir = find_data_dir(root, "chb13_interictal_features.npy")
    gamma_dir = find_gamma_dir(root)
    gae_ck = find_ckpts(root, "gae_joint_seed")
    lstm_ck = find_ckpts(root, "lstm_temporal_seed")
    print(f"adj_dir   = {adj_dir}")
    print(f"feat_dir  = {feat_dir}")
    print(f"gamma_dir = {gamma_dir}")
    print(f"GAE seeds = { {k: v[0] for k,v in sorted(gae_ck.items())} }  (using 42)")
    print(f"LSTM seeds= { {k: v[0] for k,v in sorted(lstm_ck.items())} }")

    # ---------- L4 (code-level) ----------
    parts = set(TRAIN_SUBJS), set(VAL_SUBJS), set(TEST_SUBJS)
    disjoint = len(parts[0] | parts[1] | parts[2]) == 23 and not (parts[0] & parts[1]) and not (parts[0] & parts[2])
    mmask = T.score_full_array(T.LSTMPredictor(in_dim=8), np.random.randn(50, 8).astype(np.float32), 16, torch.device("cpu"))
    warm_ok = bool(np.all(np.isnan(mmask[:15])) and np.all(np.isfinite(mmask[15:])))
    print(f"\nL4a partition disjoint (23 unique): {disjoint} | L4b warm-up mask 15-NaN: {warm_ok}")
    L4 = disjoint and warm_ok

    # ---------- adopted GAE (seed 42) ----------
    gae = G.GAEModel().to(dev)
    gsd = load_state(gae_ck[42]); gae.load_state_dict(gsd.get("state_dict", gsd), strict=True); gae.eval()

    # VAL flat-Z
    Zval = {}
    for s in VAL_SUBJS:
        Zi = T.flat(T.compute_raw_Z(gae, Path(adj_dir)/f"{s}_interictal_adjs{a.suffix}.npy",
                                    Path(feat_dir)/f"{s}_interictal_features.npy", dev))
        Zc = T.flat(T.compute_raw_Z(gae, Path(adj_dir)/f"{s}_ictal_adjs{a.suffix}.npy",
                                    Path(feat_dir)/f"{s}_ictal_features.npy", dev))
        Zval[s] = (Zi, Zc)
    in_dim = Zval[VAL_SUBJS[0]][0].shape[1]

    # ---------- L1 + L3 ----------
    seeds = sorted(lstm_ck.keys()); lstms = {}; psm = {}; pss = {}
    for sd in seeds:
        mdl = T.LSTMPredictor(in_dim=in_dim).to(dev)
        st = load_state(lstm_ck[sd]); mdl.load_state_dict(st.get("state_dict", st), strict=True); mdl.eval()
        lstms[sd] = mdl
        aucs = {s: T.window_auroc(T.score_full_array(mdl, Zval[s][0], L, dev),
                                  T.score_full_array(mdl, Zval[s][1], L, dev)) for s in VAL_SUBJS}
        pss[sd] = aucs; psm[sd] = float(np.mean(list(aucs.values())))
        print(f"  seed {sd}: VAL AUROC {{{', '.join(f'{k}:{v:.3f}' for k,v in aucs.items())}}} mean={psm[sd]:.4f}")
    mv = np.array([psm[s] for s in seeds]); mean_m, sd_m = mv.mean(), mv.std(ddof=1)
    L1 = bool(mean_m >= L1_BAR and np.all(mv >= L1_BAR)); L3 = bool(sd_m <= L3_BAR)
    rank42 = sorted(mv, reverse=True).index(psm[CANON]) + 1

    # ---------- L2 (canonical seed, equal-weight robust-z) ----------
    print("\n--- L2 (canonical seed 42, equal-weight robust-z) ---")
    l2_rg, l2_rgt = [], []
    for s in VAL_SUBJS:
        rri = G.score_windows(gae, Path(adj_dir)/f"{s}_interictal_adjs{a.suffix}.npy",
                              Path(feat_dir)/f"{s}_interictal_features.npy", dev)
        rrc = G.score_windows(gae, Path(adj_dir)/f"{s}_ictal_adjs{a.suffix}.npy",
                              Path(feat_dir)/f"{s}_ictal_features.npy", dev)
        zri, zrc = robust_z(rri, rrc)
        gi, gc = load_gamma(gamma_dir, s, "inter"), load_gamma(gamma_dir, s, "ictal")
        zgi, zgc = robust_z(gi, gc)
        rti = T.score_full_array(lstms[CANON], Zval[s][0], L, dev)
        rtc = T.score_full_array(lstms[CANON], Zval[s][1], L, dev)
        fill = np.nanmedian(rti); rti = np.where(np.isnan(rti), fill, rti); rtc = np.where(np.isnan(rtc), fill, rtc)
        zti, ztc = robust_z(rti, rtc)
        n_i = min(len(zri), len(zgi), len(zti)); n_c = min(len(zrc), len(zgc), len(ztc))
        rg_i = (zri[:n_i]+zgi[:n_i])/2; rg_c = (zrc[:n_c]+zgc[:n_c])/2
        rgt_i = (zri[:n_i]+zgi[:n_i]+zti[:n_i])/3; rgt_c = (zrc[:n_c]+zgc[:n_c]+ztc[:n_c])/3
        a_rg = T.window_auroc(rg_i, rg_c); a_rgt = T.window_auroc(rgt_i, rgt_c)
        l2_rg.append(a_rg); l2_rgt.append(a_rgt)
        print(f"  {s}: recon+gamma={a_rg:.4f}  +temporal={a_rgt:.4f}  Δ={a_rgt-a_rg:+.4f}")
    m_rg, m_rgt = float(np.mean(l2_rg)), float(np.mean(l2_rgt)); L2 = m_rgt > m_rg

    print("\n================ Gate R-LSTM (PREREG_02 §5) ================")
    print(f"  L1 mean VAL AUROC = {mean_m:.4f} (min {mv.min():.4f}, bar 0.60) -> {'PASS' if L1 else 'FAIL'}")
    print(f"  L2 VAL macro: recon+gamma {m_rg:.4f} -> +temporal {m_rgt:.4f} (Δ={m_rgt-m_rg:+.4f}) -> {'PASS' if L2 else 'FAIL'}")
    print(f"  L3 across-seed SD = {sd_m:.4f} (bar 0.05) -> {'PASS' if L3 else 'FAIL'}")
    print(f"  L4 leakage + warm-up mask -> {'PASS' if L4 else 'FAIL'}")
    print(f"  (seed-42 canonical rank {rank42}/{len(seeds)} — kept regardless, pre-registered)")
    verdict = L1 and L2 and L3 and L4
    print(f"\nVERDICT: {'PASS — temporal branch accepted; proceed to PREREG 03 (weights)' if verdict else 'REVIEW — see PREREG_02 §5'}")

    out = Path(a.out_dir); out.mkdir(parents=True, exist_ok=True)
    with open(out/"lstm_gate_full.csv", "w", newline="") as f:
        w = csv.writer(f); w.writerow(["subject"]+[f"seed{s}" for s in seeds]+["L2_rg","L2_rgt"])
        for i, s in enumerate(VAL_SUBJS):
            w.writerow([s]+[f"{pss[sd][s]:.4f}" for sd in seeds]+[f"{l2_rg[i]:.4f}", f"{l2_rgt[i]:.4f}"])
        w.writerow(["MACRO"]+[f"{psm[sd]:.4f}" for sd in seeds]+[f"{m_rg:.4f}", f"{m_rgt:.4f}"])
    print(f"Wrote {out/'lstm_gate_full.csv'}")


if __name__ == "__main__":
    main()
