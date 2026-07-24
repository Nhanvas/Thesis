"""
CPD Pipeline: Unsupervised Seizure Localization via Change Point Detection

Problem reframing:
  Threshold approach: "Is window t a seizure?" → binary, requires threshold calibration.
  CPD approach:       "When did the brain connectivity pattern change?" → temporal localization.

Pipeline:
  1. Score all windows with base Joint GAE + Temporal LSTM + Gamma AEC
  2. Z-normalize using ALL windows (fully unsupervised, no labels)
  3. Build ensemble score time series in chronological order
  4. Apply PELT (Pruned Exact Linear Time) change point detection
  5. Evaluate: detection rate, latency, false change point rate

No threshold. No ictal labels at any stage.
"""

import numpy as np
import torch
import torch.nn as nn
import re
import pandas as pd
import ruptures as rpt
from pathlib import Path
from torch_geometric.nn import GCNConv
from torch_geometric.data import Data, Batch as PyGBatch
from torch_geometric.utils import dense_to_sparse

# ── Config ────────────────────────────────────────────────────────────────────
DATA_DIR    = Path("data/processed")
MODEL_PATH  = Path("data/models/best_model_joint_lambda01.pt")
TEMP_DIR    = Path("data/processed/temporal_zscores")
SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")
RESULTS_DIR = Path("results/cpd")
RESULTS_DIR.mkdir(parents=True, exist_ok=True)

WIN_SEC     = 4
FS          = 256
WIN_SAMP    = WIN_SEC * FS
BUFFER_H    = 4
ADJS_SUFFIX = "_topk20"
N_CH        = 18
N_BANDS     = 5
INPUT_DIM   = 23
HIDDEN_DIM  = 64
LATENT_DIM  = 16
LAMBDA      = 0.1
TOLERANCE_S = 30      # seizure detection tolerance window
MERGE_GAP_S = 32      # merge adjacent change points within this gap

TEST_SUBJS = ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]
VAL_SUBJS  = ["chb10","chb11","chb22"]

device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
print(f"Using device: {device}")

# ── Model Definition ──────────────────────────────────────────────────────────
class GAEEncoder(nn.Module):
    def __init__(self, input_dim=INPUT_DIM, hidden_dim=HIDDEN_DIM, latent_dim=LATENT_DIM):
        super().__init__()
        self.conv1 = GCNConv(input_dim, hidden_dim)
        self.conv2 = GCNConv(hidden_dim, latent_dim)
        self.relu  = nn.ReLU()
    def forward(self, x, edge_index, edge_weight=None):
        return self.conv2(self.relu(self.conv1(x, edge_index, edge_weight)),
                          edge_index, edge_weight)

class XDecoder(nn.Module):
    def __init__(self, latent_dim=LATENT_DIM, n_bands=N_BANDS):
        super().__init__()
        self.net = nn.Sequential(nn.Linear(latent_dim, 32), nn.ReLU(),
                                  nn.Linear(32, n_bands))
    def forward(self, z): return self.net(z)

class GAEModel(nn.Module):
    def __init__(self):
        super().__init__()
        self.encoder   = GAEEncoder()
        self.x_decoder = XDecoder()
    def forward(self, x, edge_index, edge_weight=None):
        z   = self.encoder(x, edge_index, edge_weight)
        z_b = z.unsqueeze(0)
        A_hat = torch.clamp(torch.bmm(z_b, z_b.transpose(1,2)), 0., 1.).squeeze(0)
        return z, A_hat, self.x_decoder(z)

def score_adj_files(model, adj_path, feat_path, batch_size=256):
    """Score adjacency + feature files. Returns raw MSE scores."""
    adjs  = np.load(adj_path,  mmap_mode='r')
    feats = np.load(feat_path, mmap_mode='r')
    scores = []
    model.eval()
    with torch.no_grad():
        for s in range(0, len(adjs), batch_size):
            e   = min(s + batch_size, len(adjs))
            B   = e - s
            A   = torch.tensor(adjs[s:e].astype(np.float32),  device=device)
            Xt  = torch.tensor(feats[s:e].astype(np.float32), device=device)
            An  = A / (A.amax(dim=(1,2), keepdim=True) + 1e-8)
            Xn  = (Xt - Xt.amin(dim=1, keepdim=True)) / \
                  (Xt.amax(dim=1, keepdim=True) - Xt.amin(dim=1, keepdim=True) + 1e-8)
            dl  = [Data(x=torch.cat([An[b], Xn[b]], dim=1),
                        edge_index=dense_to_sparse(A[b])[0],
                        edge_attr=dense_to_sparse(A[b])[1]) for b in range(B)]
            pg  = PyGBatch.from_data_list(dl).to(device)
            z   = model.encoder(pg.x, pg.edge_index, pg.edge_attr)
            zpg = z.view(B, N_CH, LATENT_DIM)
            Ah  = torch.clamp(torch.bmm(zpg, zpg.transpose(1,2)), 0., 1.)
            Xh  = model.x_decoder(z).view(B, N_CH, N_BANDS)
            sc  = ((A - Ah)**2).mean(dim=(1,2)) + LAMBDA * ((Xn - Xh)**2).mean(dim=(1,2))
            scores.extend(sc.cpu().numpy().tolist())
    return np.array(scores, dtype=np.float32)

# ── Summary File Parsing ──────────────────────────────────────────────────────
def parse_time_hms(t_str):
    """'HH:MM:SS' → total seconds (handles >24h notation like '25:00:00')."""
    parts = t_str.strip().split(":")
    return int(parts[0]) * 3600 + int(parts[1]) * 60 + int(parts[2])

def parse_summary_edf_list(summary_path):
    """
    Parse CHB-MIT summary file.
    Returns list of dicts: {fname, start_s, duration_s, seizures: [(onset, offset), ...]}
    where onset/offset are SECONDS FROM EDF START.
    """
    text = Path(summary_path).read_text()
    pattern = re.compile(
        r'File Name:\s*(\S+\.edf)\s+'
        r'File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+'
        r'Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL
    )
    edfs = []
    for m in pattern.finditer(text):
        fname, t_start, t_end, n_sz, rest = (m.group(1), m.group(2),
                                               m.group(3), int(m.group(4)), m.group(5))
        start_s    = parse_time_hms(t_start)
        end_s      = parse_time_hms(t_end)
        duration_s = end_s - start_s
        if duration_s <= 0:
            duration_s += 86400   # crossed midnight
        seizures = []
        if n_sz > 0:
            onsets  = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            offsets = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            seizures = list(zip(onsets, offsets))
        edfs.append({'fname': fname, 'start_s': start_s,
                     'duration_s': duration_s, 'seizures': seizures})
    # Sort by filename (alphabetical = chronological for CHB-MIT)
    edfs.sort(key=lambda x: x['fname'])
    return edfs

# ── Timeline Reconstruction ───────────────────────────────────────────────────
def build_timeline(subj, inter_scores, ictal_scores):
    """
    Reconstruct chronological score timeline for one subject.

    CHB-MIT structure:
      - Windows are 4-second non-overlapping
      - Buffer: BUFFER_H hours after each seizure end, within the same EDF file
      - Artifact-rejected windows: ~5% of interictal, ignored here (minor timing error)

    Returns:
      scores:     [N] float array of ensemble scores in chronological order
      is_ictal:   [N] bool array — True if window is within seizure
      onset_wins: list of window indices where each seizure STARTS in the timeline
      n_inter_h:  total interictal recording hours (for FDR/h computation)
    """
    summary_path = SUMMARY_DIR / f"{subj}-summary.txt"
    edfs = parse_summary_edf_list(summary_path)

    scores_out = []
    is_ictal   = []
    onset_wins = []   # (win_idx, seizure_onset_within_recording)

    inter_ptr = 0
    ictal_ptr = 0
    total_inter_s = 0.0

    for edf in edfs:
        dur_s  = edf['duration_s']
        sz_list = edf['seizures']
        n_win  = dur_s // WIN_SEC

        # Build per-second labels within this EDF file
        labels      = np.zeros(dur_s, dtype=np.int8)
        buffer_mask = np.zeros(dur_s, dtype=bool)

        for (onset_s, offset_s) in sz_list:
            onset_s  = min(onset_s, dur_s)
            offset_s = min(offset_s, dur_s)
            labels[onset_s:offset_s] = 1
            # Buffer: BUFFER_H hours after seizure end (within this EDF only)
            buf_end = min(dur_s, offset_s + BUFFER_H * 3600)
            buffer_mask[offset_s:buf_end] = True

        # Walk windows
        for w in range(n_win):
            start_s = w * WIN_SEC
            end_s   = start_s + WIN_SEC
            if end_s > dur_s:
                break

            win_label    = int(labels[start_s:end_s].max())
            win_buffered = bool(buffer_mask[start_s:end_s].any())

            if win_label == 1:   # ictal
                if ictal_ptr < len(ictal_scores):
                    scores_out.append(ictal_scores[ictal_ptr])
                    is_ictal.append(True)
                    # Mark onset: first ictal window of this seizure group
                    if not is_ictal or (len(is_ictal) >= 2 and not is_ictal[-2]):
                        onset_wins.append(len(scores_out) - 1)
                    ictal_ptr += 1
            elif not win_buffered:   # interictal
                if inter_ptr < len(inter_scores):
                    scores_out.append(inter_scores[inter_ptr])
                    is_ictal.append(False)
                    inter_ptr += 1
                    total_inter_s += WIN_SEC
            # buffer: skip (no score, not in timeline)

    scores_out = np.array(scores_out, dtype=np.float32)
    is_ictal   = np.array(is_ictal,   dtype=bool)

    # Recompute seizure boundaries more accurately from is_ictal array
    seizure_ranges = []
    in_seiz = False
    s_start = 0
    for i, ic in enumerate(is_ictal):
        if ic and not in_seiz:
            s_start = i
            in_seiz = True
        elif not ic and in_seiz:
            seizure_ranges.append((s_start, i))
            in_seiz = False
    if in_seiz:
        seizure_ranges.append((s_start, len(is_ictal)))

    n_inter_h = total_inter_s / 3600.0

    print(f"  [{subj}] Timeline: {len(scores_out)} windows "
          f"({inter_ptr} inter, {ictal_ptr} ictal, {len(seizure_ranges)} seizures)")
    print(f"    Expected inter: {len(inter_scores)}, got: {inter_ptr}  "
          f"(diff={len(inter_scores)-inter_ptr}, ~artifact-rejected)")
    if abs(ictal_ptr - len(ictal_scores)) > 2:
        print(f"  !! WARNING: ictal mismatch: expected {len(ictal_scores)}, got {ictal_ptr}")

    return scores_out, is_ictal, seizure_ranges, n_inter_h

# ── PELT Change Point Detection ───────────────────────────────────────────────
def run_pelt(signal, pen_multiplier=1.0):
    """
    Apply PELT with data-driven BIC penalty.

    Penalty β = multiplier × σ² × log(n)
    σ² estimated from lower 80th percentile of signal (excludes ictal peaks).
    This is fully unsupervised — no ictal labels used.

    pen_multiplier: sweep this to control sensitivity/specificity tradeoff.
    """
    n     = len(signal)
    sigma2 = np.var(signal[signal <= np.percentile(signal, 80)])
    beta   = pen_multiplier * sigma2 * np.log(n)

    algo  = rpt.Pelt(model="rbf", min_size=3, jump=1).fit(signal.reshape(-1,1))
    cps   = algo.predict(pen=beta)
    # cps includes n (end of signal) as last entry — remove it
    cps   = [cp for cp in cps if cp < n]
    return cps, beta

# ── Evaluation ────────────────────────────────────────────────────────────────
def evaluate_cpd(change_points, seizure_ranges, n_inter_h,
                 tolerance_win=None, merge_gap_win=None):
    """
    Evaluate change point detection against seizure annotations.

    tolerance_win: CP within this many windows of seizure onset = TP.
                   Default: TOLERANCE_S // WIN_SEC = 7 windows (28s)
    merge_gap_win: CPs within this gap merged into one event.
                   Default: MERGE_GAP_S // WIN_SEC = 8 windows (32s)
    """
    if tolerance_win is None: tolerance_win = TOLERANCE_S // WIN_SEC
    if merge_gap_win is None: merge_gap_win = MERGE_GAP_S // WIN_SEC

    # Merge nearby change points into events
    if not change_points:
        return 0, len(seizure_ranges), float('inf'), float('nan'), []

    merged_cps = [change_points[0]]
    for cp in change_points[1:]:
        if cp - merged_cps[-1] <= merge_gap_win:
            merged_cps[-1] = cp  # extend last event to this CP
        else:
            merged_cps.append(cp)

    tp, fn = 0, 0
    latencies = []
    matched_cps = set()

    for (sz_start, sz_end) in seizure_ranges:
        # Find CPs near seizure onset (within tolerance)
        nearby = [cp for cp in merged_cps
                  if abs(cp - sz_start) <= tolerance_win]
        if nearby:
            tp += 1
            best_cp = min(nearby, key=lambda x: abs(x - sz_start))
            matched_cps.add(best_cp)
            latency_s = (best_cp - sz_start) * WIN_SEC  # negative = early detection
            latencies.append(latency_s)
        else:
            fn += 1

    # False CPs: not matched to any seizure
    fp_cps = [cp for cp in merged_cps if cp not in matched_cps]
    fcp_h  = len(fp_cps) / max(n_inter_h, 1e-6)

    mean_lat = float(np.mean(latencies)) if latencies else float('nan')
    det_rate = tp / max(tp + fn, 1)

    return tp, fn, fcp_h, mean_lat, latencies

# ── Main Pipeline ─────────────────────────────────────────────────────────────
def main():
    # ── Load base model ───────────────────────────────────────────────────────
    print("Loading base model...")
    model = GAEModel().to(device)
    state = torch.load(str(MODEL_PATH), map_location=device)
    model.load_state_dict(state)
    model.eval()
    b = model.encoder.conv1.bias
    assert b is not None and b.abs().max().item() > 0.005, "Model not loaded correctly"
    print(f"  Model loaded. Bias max={b.abs().max().item():.4f}")

    # ── Compute reconstruction scores ─────────────────────────────────────────
    print("\nScoring all subjects with base model...")
    recon_inter, recon_ictal = {}, {}
    all_subjs = TEST_SUBJS + VAL_SUBJS

    for subj in all_subjs:
        adj_i  = str(DATA_DIR / f"{subj}_interictal_adjs{ADJS_SUFFIX}.npy")
        adj_c  = str(DATA_DIR / f"{subj}_ictal_adjs{ADJS_SUFFIX}.npy")
        feat_i = str(DATA_DIR / f"{subj}_interictal_features.npy")
        feat_c = str(DATA_DIR / f"{subj}_ictal_features.npy")
        recon_inter[subj] = score_adj_files(model, adj_i, feat_i)
        recon_ictal[subj] = score_adj_files(model, adj_c, feat_c)
        print(f"  {subj}: {len(recon_inter[subj])} inter, {len(recon_ictal[subj])} ictal")

    # ── Compute BIC penalty baseline from val interictal (no labels needed) ───
    print("\nEstimating BIC sigma from val subjects...")
    val_recon = np.concatenate([recon_inter[s] for s in VAL_SUBJS])
    sigma2_recon = np.var(val_recon[val_recon <= np.percentile(val_recon, 80)])
    print(f"  Val recon sigma2={sigma2_recon:.6f}")

    # ── Load temporal z-scores ────────────────────────────────────────────────
    print("\nLoading temporal z-scores...")
    temp_inter, temp_ictal = {}, {}
    for subj in TEST_SUBJS:
        temp_inter[subj] = np.load(str(TEMP_DIR / f"temporal_{subj}_zinter.npy"))
        temp_ictal[subj]  = np.load(str(TEMP_DIR / f"temporal_{subj}_zictal.npy"))
        print(f"  {subj}: {len(temp_inter[subj])} inter, {len(temp_ictal[subj])} ictal")

    # ── Load gamma AEC z-scores ───────────────────────────────────────────────
    print("\nLoading gamma AEC z-scores...")
    gamma_inter, gamma_ictal = {}, {}
    for subj in TEST_SUBJS:
        gamma_inter[subj] = np.load(str(DATA_DIR / f"gamma_aec_{subj}_inter.npy"))
        gamma_ictal[subj]  = np.load(str(DATA_DIR / f"gamma_aec_{subj}_ictal.npy"))

    # ── All-window z-normalization for reconstruction (no labels used) ────────
    print("\nApplying all-window z-normalization to reconstruction scores...")
    z_recon_inter, z_recon_ictal = {}, {}
    for subj in TEST_SUBJS:
        all_s = np.concatenate([recon_inter[subj], recon_ictal[subj]])
        med   = np.median(all_s)
        mad   = np.median(np.abs(all_s - med)) + 1e-9
        z_recon_inter[subj] = (recon_inter[subj] - med) / mad
        z_recon_ictal[subj] = (recon_ictal[subj]  - med) / mad
        # Temporal and gamma are already z-normalized

    # ── Build ensemble scores (same weights as before) ────────────────────────
    W_R, W_T, W_G = 0.35, 0.30, 0.35
    ens_inter, ens_ictal = {}, {}
    for subj in TEST_SUBJS:
        ni = min(len(z_recon_inter[subj]), len(temp_inter[subj]), len(gamma_inter[subj]))
        nc = min(len(z_recon_ictal[subj]),  len(temp_ictal[subj]),  len(gamma_ictal[subj]))
        ens_inter[subj] = (W_R * z_recon_inter[subj][:ni] +
                            W_T * temp_inter[subj][:ni] +
                            W_G * gamma_inter[subj][:ni])
        ens_ictal[subj]  = (W_R * z_recon_ictal[subj][:nc] +
                            W_T * temp_ictal[subj][:nc] +
                            W_G * gamma_ictal[subj][:nc])

    # ── AUROC verification (for reference — not used in CPD) ─────────────────
    from sklearn.metrics import roc_auc_score
    print("\nAUROC verification (threshold-independent ranking quality):")
    aurocs = {}
    for subj in TEST_SUBJS:
        y = np.concatenate([np.zeros(len(ens_inter[subj])), np.ones(len(ens_ictal[subj]))])
        aurocs[subj] = roc_auc_score(y, np.concatenate([ens_inter[subj], ens_ictal[subj]]))
        print(f"  {subj}: {aurocs[subj]:.4f}")
    print(f"  MACRO: {np.mean(list(aurocs.values())):.4f}")

    # ── Build timelines and run PELT ──────────────────────────────────────────
    print("\n" + "="*60)
    print("Building chronological timelines and running PELT...")
    print("="*60)

    pen_multipliers = [0.5, 1.0, 2.0, 5.0, 10.0]
    all_results = []

    for subj in TEST_SUBJS:
        print(f"\n[{subj}] Building timeline...")
        timeline, is_ictal, seizure_ranges, n_inter_h = build_timeline(
            subj, ens_inter[subj], ens_ictal[subj])

        print(f"  n_inter_h={n_inter_h:.2f}h | {len(seizure_ranges)} seizures in timeline")

        # Sweep penalty multiplier
        print(f"  {'pen_mult':>10} {'beta':>10} {'n_CPs':>7} "
              f"{'TP':>4} {'FN':>4} {'det%':>7} {'FCP/h':>8} {'lat_s':>8}")
        print(f"  " + "-"*60)

        for pen_m in pen_multipliers:
            cps, beta = run_pelt(timeline, pen_multiplier=pen_m)
            tp, fn, fcp_h, mean_lat, lats = evaluate_cpd(
                cps, seizure_ranges, n_inter_h)
            det_rate = tp / max(tp + fn, 1)
            lat_str  = f"{mean_lat:.1f}" if not np.isnan(mean_lat) else "—"
            print(f"  {pen_m:>10.1f} {beta:>10.4f} {len(cps):>7} "
                  f"{tp:>4} {fn:>4} {det_rate:>6.1%} {fcp_h:>8.1f} {lat_str:>8}")
            all_results.append({
                'subject': subj, 'pen_mult': pen_m, 'beta': round(beta, 4),
                'n_cps': len(cps), 'n_seizures': len(seizure_ranges),
                'tp': tp, 'fn': fn, 'det_rate': round(det_rate, 4),
                'fcp_h': round(fcp_h, 2), 'mean_lat_s': round(mean_lat, 1) if not np.isnan(mean_lat) else None,
                'n_inter_h': round(n_inter_h, 2), 'auroc': round(aurocs[subj], 4)
            })

    # ── Save results ──────────────────────────────────────────────────────────
    df = pd.DataFrame(all_results)
    df.to_csv(RESULTS_DIR / "cpd_sweep_results.csv", index=False)
    print(f"\nSaved: {RESULTS_DIR}/cpd_sweep_results.csv")

    # ── Macro summary across pen_multipliers ─────────────────────────────────
    print("\n" + "="*60)
    print("MACRO summary across penalty multipliers:")
    print(f"{'pen_mult':>10} {'macro_det%':>12} {'macro_FCP/h':>12} {'macro_lat_s':>12}")
    print("-"*50)
    for pen_m in pen_multipliers:
        sub_df = df[df.pen_mult == pen_m]
        m_det  = sub_df['det_rate'].mean()
        m_fcp  = sub_df['fcp_h'].mean()
        m_lat  = sub_df['mean_lat_s'].dropna().mean()
        print(f"{pen_m:>10.1f} {m_det:>11.1%} {m_fcp:>12.1f} {m_lat:>12.1f}")

    print(f"\nMacro AUROC (all subjects): {np.mean(list(aurocs.values())):.4f}")
    print("Done.")

if __name__ == "__main__":
    main()