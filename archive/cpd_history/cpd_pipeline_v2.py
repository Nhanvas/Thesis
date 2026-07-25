"""
CPD Pipeline v2 — corrected:
Fix 1: chb17 filename pattern (chb17a/b/c prefix support)
Fix 2: Empty signal crash in run_pelt
Fix 3: Inter-exhaustion → synthetic neutral windows maintain seizure separation
"""

import numpy as np
import torch
import torch.nn as nn
import re
import pandas as pd
import ruptures as rpt
from pathlib import Path
from sklearn.metrics import roc_auc_score
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data, Batch as PyGBatch
from torch_geometric.utils import dense_to_sparse

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/processed")
MODEL_PATH  = Path("data/models/best_model_joint_lambda01.pt")
TEMP_DIR    = Path("data/processed/temporal_zscores")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
CHB_MIT_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT")
SCORES_DIR  = Path("results/cpd/scores")
RESULTS_DIR = Path("results/cpd")
SCORES_DIR.mkdir(parents=True, exist_ok=True)
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC     = 4;  FS = 256
BUFFER_H    = 4;  ADJS_SUFFIX = "_topk20"
N_CH=18; N_BANDS=5; INPUT_DIM=23; HIDDEN_DIM=64; LATENT_DIM=16; LAMBDA=0.1
TOLERANCE_S = 30;  MERGE_GAP_S = 32

TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
W_R, W_T, W_G = 0.35, 0.30, 0.35

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Device: {device}")

# ── Model ─────────────────────────────────────────────────────────────────────
class GAEEncoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.conv1 = GCNConv(INPUT_DIM, HIDDEN_DIM)
        self.conv2 = GCNConv(HIDDEN_DIM, LATENT_DIM)
        self.relu  = nn.ReLU()
    def forward(self, x, ei, ea=None):
        return self.conv2(self.relu(self.conv1(x, ei, ea)), ei, ea)

class XDecoder(nn.Module):
    def __init__(self):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(LATENT_DIM,32), nn.ReLU(),
                                  nn.Linear(32, N_BANDS))
    def forward(self, z): return self.net(z)

class GAEModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder   = GAEEncoder()
        self.x_decoder = XDecoder()

def score_adj_files(model, adj_path, feat_path, batch_size=256):
    adjs  = np.load(adj_path,  mmap_mode='r')
    feats = np.load(feat_path, mmap_mode='r')
    scores = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch_size):
            e  = min(s + batch_size, len(adjs)); B = e - s
            A  = torch.tensor(adjs[s:e].astype(np.float32),  device=device)
            Xt = torch.tensor(feats[s:e].astype(np.float32), device=device)
            An = A / (A.amax(dim=(1,2), keepdim=True) + 1e-8)
            Xn = (Xt - Xt.amin(dim=1, keepdim=True)) / \
                 (Xt.amax(dim=1, keepdim=True) - Xt.amin(dim=1, keepdim=True) + 1e-8)
            dl = [Data(x=torch.cat([An[b], Xn[b]], dim=1),
                       edge_index=dense_to_sparse(A[b])[0],
                       edge_attr=dense_to_sparse(A[b])[1]) for b in range(B)]
            pg = PyGBatch.from_data_list(dl).to(device)
            z  = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
            zpg= z.view(B, N_CH, LATENT_DIM)
            Ah = torch.clamp(torch.bmm(zpg, zpg.transpose(1,2)), 0., 1.)
            Xh = model.x_decoder(z).view(B, N_CH, N_BANDS)
            sc = ((A - Ah)**2).mean(dim=(1,2)) + \
                 LAMBDA * ((Xn - Xh)**2).mean(dim=(1,2))
            scores.extend(sc.cpu().numpy().tolist())
    return np.array(scores, dtype=np.float32)

# ── Summary parsing ───────────────────────────────────────────────────────────
def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0])*3600 + int(p[1])*60 + int(p[2])

def parse_summary_edf_list(summary_path):
    text = Path(summary_path).read_text()
    pat  = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fname, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0: dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({'fname': fname, 'duration_s': dur, 'seizures': szs})
    edfs.sort(key=lambda x: x['fname'])
    return edfs

def get_all_edfs_for_subject(subj, summary_path, chb_mit_dir):
    """
    Get ALL EDF files from subject directory (including unlisted ones).
    Unlisted files: assumed 3600s, no seizures.
    """
    summary_edfs = parse_summary_edf_list(summary_path)
    seizure_map  = {e['fname']: e['seizures']  for e in summary_edfs}
    duration_map = {e['fname']: e['duration_s'] for e in summary_edfs}

    subj_dir = chb_mit_dir / subj
    if not subj_dir.exists():
        print(f"  WARNING: {subj_dir} not found, using summary only")
        return summary_edfs

    # FIX 1: use "*.edf" not f"{subj}_*.edf"
    # This handles chb17a_03.edf, chb17b_57.edf, chb17c_02.edf correctly
    all_edf_files = sorted(subj_dir.glob("*.edf"))

    if len(all_edf_files) == 0:
        print(f"  WARNING: No .edf files found in {subj_dir}, using summary only")
        return summary_edfs

    all_edfs = []
    for edf_path in all_edf_files:
        fname = edf_path.name
        dur   = duration_map.get(fname, 3600)   # default 1 hour if unlisted
        szs   = seizure_map.get(fname,  [])
        all_edfs.append({'fname': fname, 'duration_s': dur, 'seizures': szs})

    n_listed   = sum(1 for e in all_edfs if e['fname'] in duration_map)
    n_unlisted = len(all_edfs) - n_listed
    print(f"  EDF files: {len(all_edfs)} total "
          f"({n_listed} in summary, {n_unlisted} unlisted)")

    return sorted(all_edfs, key=lambda x: x['fname'])

# ── Timeline reconstruction ───────────────────────────────────────────────────
def build_timeline(subj, inter_scores, ictal_scores):
    edfs = get_all_edfs_for_subject(subj,
                                     SUMMARY_DIR / f"{subj}-summary.txt",
                                     CHB_MIT_DIR)

    scores_out, is_ictal_out = [], []
    inter_ptr = ictal_ptr = 0
    total_inter_s  = 0.0
    synthetic_count = 0   # windows padded with 0 when inter exhausted

    for edf in edfs:
        dur   = edf['duration_s']
        n_win = dur // WIN_SEC
        labels = np.zeros(dur, dtype=np.int8)
        buf    = np.zeros(dur, dtype=bool)

        for (on, off) in edf['seizures']:
            on  = min(on,  dur)
            off = min(off, dur)
            labels[on:off] = 1
            buf[off:min(dur, off + BUFFER_H * 3600)] = True

        for w in range(n_win):
            ss, es = w * WIN_SEC, (w + 1) * WIN_SEC
            if es > dur: break
            lbl = int(labels[ss:es].max())
            bfr = bool(buf[ss:es].any())

            if lbl == 1:
                # Ictal window: pull from ictal_scores
                if ictal_ptr < len(ictal_scores):
                    scores_out.append(float(ictal_scores[ictal_ptr]))
                    ictal_ptr += 1
                else:
                    scores_out.append(0.0)   # rare: ictal exhausted
                is_ictal_out.append(True)

            else:
                # Non-ictal window (clean inter OR buffer): include to maintain temporal separation
                if inter_ptr < len(inter_scores):
                    scores_out.append(float(inter_scores[inter_ptr]))
                    inter_ptr += 1
                else:
                    scores_out.append(0.0)
                    synthetic_count += 1
                is_ictal_out.append(False)
                total_inter_s += WIN_SEC
            # buffer windows: skip entirely (not added to timeline)

    scores_out = np.array(scores_out, dtype=np.float32)
    is_ictal   = np.array(is_ictal_out, dtype=bool)

    # Detect seizure ranges: consecutive runs of ictal windows
    sz_ranges, in_s, ss_idx = [], False, 0
    for i, ic in enumerate(is_ictal):
        if ic and not in_s:
            ss_idx = i; in_s = True
        elif not ic and in_s:
            sz_ranges.append((ss_idx, i)); in_s = False
    if in_s:
        sz_ranges.append((ss_idx, len(is_ictal)))

    n_inter_h = total_inter_s / 3600.0
    print(f"  [{subj}] Timeline: {len(scores_out)} windows "
          f"({inter_ptr}+{synthetic_count}synthetic inter, {ictal_ptr} ictal)"
          f" | {len(sz_ranges)} seizures | {n_inter_h:.1f}h inter")
    if synthetic_count > 0:
        print(f"    NOTE: {synthetic_count} synthetic zeros added "
              f"(inter exhausted after {inter_ptr}/{len(inter_scores)} windows)")

    return scores_out, is_ictal, sz_ranges, n_inter_h

# ── PELT ──────────────────────────────────────────────────────────────────────
def run_pelt_all(signal, pen_multipliers):
    n = len(signal)
    if n < 10:
        return {pm: ([], 0.0) for pm in pen_multipliers}
    s2 = np.var(signal[signal <= np.percentile(signal, 80)])
    if s2 < 1e-10:
        s2 = 1.0
    # FIT ONCE — expensive step
    algo = rpt.Pelt(model="l2", min_size=3, jump=8).fit(signal.reshape(-1, 1))
    results = {}
    for pm in pen_multipliers:
        print(f"    [PELT] Calculating for pen_mult = {pm}...")
        beta = pm * s2 * np.log(n)
        cps = [c for c in algo.predict(pen=beta) if c < n]
        results[pm] = (cps, beta)
    return results

# ── Evaluation ────────────────────────────────────────────────────────────────
def evaluate_cpd(cps, sz_ranges, n_inter_h):
    tol = TOLERANCE_S // WIN_SEC    # 7 windows = 28s
    gap = MERGE_GAP_S  // WIN_SEC   # 8 windows = 32s

    if not cps or not sz_ranges:
        fn = len(sz_ranges)
        return 0, fn, float('inf') if n_inter_h > 0 else 0.0, float('nan')

    # Merge nearby change points into events
    merged = [cps[0]]
    for c in cps[1:]:
        if c - merged[-1] <= gap:
            merged[-1] = c
        else:
            merged.append(c)

    tp, fn, lats, matched = 0, 0, [], set()
    for (sz_start, sz_end) in sz_ranges:
        near = [c for c in merged if abs(c - sz_start) <= tol]
        if near:
            tp += 1
            best = min(near, key=lambda x: abs(x - sz_start))
            matched.add(best)
            lats.append((best - sz_start) * WIN_SEC)
        else:
            fn += 1

    fp    = len([c for c in merged if c not in matched])
    fcp_h = fp / max(n_inter_h, 1e-6)
    mean_lat = float(np.mean(lats)) if lats else float('nan')
    return tp, fn, fcp_h, mean_lat

# ── Main ──────────────────────────────────────────────────────────────────────
def main():
    model = GAEModel().to(device)
    state = torch.load(str(MODEL_PATH), map_location=device)
    model.load_state_dict(state)
    model.eval()
    print(f"Model loaded. Bias={model.encoder.conv1.bias.abs().max().item():.4f}\n")

    all_results   = []
    pen_multipliers = [0.3, 0.5, 1.0, 2.0, 5.0, 10.0]

    for subj in TEST_SUBJS:
        print(f"\n{'='*55}\n[{subj}]")

        # ── Load or compute ensemble scores ──────────────────────────────────
        ens_i_path = SCORES_DIR / f"{subj}_ens_inter.npy"
        ens_c_path = SCORES_DIR / f"{subj}_ens_ictal.npy"

        if ens_i_path.exists() and ens_c_path.exists():
            ens_inter = np.load(str(ens_i_path))
            ens_ictal = np.load(str(ens_c_path))
            print(f"  Cached: {len(ens_inter)} inter, {len(ens_ictal)} ictal")
        else:
            print("  Scoring...")
            s_i = score_adj_files(model,
                str(DATA_DIR / f"{subj}_interictal_adjs{ADJS_SUFFIX}.npy"),
                str(DATA_DIR / f"{subj}_interictal_features.npy"))
            s_c = score_adj_files(model,
                str(DATA_DIR / f"{subj}_ictal_adjs{ADJS_SUFFIX}.npy"),
                str(DATA_DIR / f"{subj}_ictal_features.npy"))
            all_s = np.concatenate([s_i, s_c])
            med = np.median(all_s); mad = np.median(np.abs(all_s - med)) + 1e-9
            z_i = (s_i - med) / mad;  z_c = (s_c - med) / mad
            del s_i, s_c, all_s

            t_i = np.load(str(TEMP_DIR / f"temporal_{subj}_zinter.npy"))
            t_c = np.load(str(TEMP_DIR / f"temporal_{subj}_zictal.npy"))
            g_i = np.load(str(DATA_DIR / f"gamma_aec_{subj}_inter.npy"))
            g_c = np.load(str(DATA_DIR / f"gamma_aec_{subj}_ictal.npy"))

            ni = min(len(z_i), len(t_i), len(g_i))
            nc = min(len(z_c), len(t_c), len(g_c))

            ens_inter = W_R*z_i[:ni] + W_T*t_i[:ni] + W_G*g_i[:ni]
            ens_ictal = W_R*z_c[:nc] + W_T*t_c[:nc] + W_G*g_c[:nc]
            del z_i, z_c, t_i, t_c, g_i, g_c

            np.save(str(ens_i_path), ens_inter)
            np.save(str(ens_c_path), ens_ictal)
            print(f"  Saved: {len(ens_inter)} inter, {len(ens_ictal)} ictal")

        # AUROC (threshold-independent)
        y     = np.concatenate([np.zeros(len(ens_inter)), np.ones(len(ens_ictal))])
        auroc = roc_auc_score(y, np.concatenate([ens_inter, ens_ictal]))
        print(f"  AUROC={auroc:.4f}")

        # ── Build timeline ────────────────────────────────────────────────────
        timeline, is_ictal, sz_ranges, n_inter_h = build_timeline(
            subj, ens_inter, ens_ictal)
        del ens_inter, ens_ictal

        if len(timeline) == 0:
            print(f"  SKIP: empty timeline — check EDF directory path")
            continue

        # ── PELT sweep ────────────────────────────────────────────────────────
        print(f"  {'pen':>5} {'beta':>8} {'nCP':>5} {'TP':>3} {'FN':>3}"
              f" {'det%':>6} {'FCP/h':>7} {'lat_s':>7}")
        print(f"  " + "-"*52)

        pelt_results = run_pelt_all(timeline, pen_multipliers)
        for pm in pen_multipliers:
            cps, beta = pelt_results[pm]
            tp, fn, fcp_h, lat = evaluate_cpd(cps, sz_ranges, n_inter_h)
            dr  = tp / max(tp + fn, 1)
            ls  = f"{lat:.1f}" if not np.isnan(lat) else "—"
            print(f"  {pm:>5.1f} {beta:>8.3f} {len(cps):>5} {tp:>3} {fn:>3}"
                  f" {dr:>5.1%} {fcp_h:>7.1f} {ls:>7}")
            all_results.append({
                'subject': subj, 'pen_mult': pm, 'beta': round(beta, 4),
                'n_cps': len(cps), 'n_seizures': len(sz_ranges),
                'tp': tp, 'fn': fn, 'det_rate': round(dr, 4),
                'fcp_h': round(fcp_h, 2),
                'mean_lat_s': round(lat, 1) if not np.isnan(lat) else None,
                'n_inter_h': round(n_inter_h, 2), 'auroc': round(auroc, 4)
            })
        del timeline, is_ictal

    # ── Save & summarize ──────────────────────────────────────────────────────
    df = pd.DataFrame(all_results)
    df.to_csv(RESULTS_DIR / "cpd_results_v5.csv", index=False)

    print("\n" + "="*55)
    print("MACRO summary:")
    print(f"{'pen':>6} {'TP/GT':>8} {'det%':>7} {'FCP/h':>8} {'lat_s':>8} {'AUROC':>8}")
    print("-"*50)
    for pm in pen_multipliers:
        sub = df[df.pen_mult == pm]
        if sub.empty: continue
        tp_sum = sub['tp'].sum()
        sz_sum = (sub['tp'] + sub['fn']).sum()
        print(f"{pm:>6.1f} {tp_sum:>4}/{sz_sum:<4} {tp_sum/sz_sum:>6.1%}"
              f" {sub['fcp_h'].mean():>8.1f}"
              f" {sub['mean_lat_s'].dropna().mean():>8.1f}"
              f" {sub['auroc'].mean():>8.4f}")

    print(f"\nSaved: {RESULTS_DIR}/cpd_results_v5.csv")

if __name__ == "__main__":
    main()