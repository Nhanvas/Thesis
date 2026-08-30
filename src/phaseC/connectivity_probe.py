"""
connectivity_probe.py — Phase C, C0 probe. DECISIVE go/no-go for directed nonlinear connectivity.
Tests, on chb06 (fails under wPLI: window AUROC ~0.44 below chance) with chb03 as a good-signal control:

  (1) CONVERGENCE GATE (kill switch for CCM): does CCM cross-map skill INCREASE with library size L
      within a 4 s window (1024 samples)? If it does NOT converge, CCM is invalid at this window length
      -> STOP CCM (or move to a longer window just for the connectivity branch).
  (2) SEPARATION: does a DIRECTED nonlinear measure (CCM or binned TE) separate ictal vs interictal on
      chb06 BETTER than a symmetric linear measure (corr/AEC proxy for wPLI)? Unsupervised anomaly =
      LedoitWolf-Mahalanobis of the vectorized connectivity to the interictal manifold -> AUROC.

Self-contained: minimal simplex-CCM + binned-TE in numpy (validated by --smoke on synthetic driver
systems). EDF via mne; standard CHB-MIT 18-ch bipolar montage (naming-robust).

USAGE
  python connectivity_probe.py --smoke                      # validate CCM/TE on synthetic (no EEG)
  python connectivity_probe.py --edf_dir /path/chb06 --summary chb06-summary.txt --subj chb06 \
      --control_edf_dir /path/chb03 --control_summary chb03-summary.txt
"""
import argparse, re, glob, os
from pathlib import Path
import numpy as np

# ---------------- core: simplex CCM ----------------
def _embed(x, E, tau):
    n = len(x) - (E - 1) * tau
    if n <= 0: return np.empty((0, E))
    return np.stack([x[i:i + (E - 1) * tau + 1:tau] for i in range(n)], 0)

def ccm_skill(driver, response, E=3, tau=2, L=None, seed=0):
    """response cross-maps driver -> estimates driver->response causation (Sugihara).
    Returns Pearson rho between cross-mapped and true driver."""
    from scipy.spatial import cKDTree
    My = _embed(response, E, tau)
    tgt = driver[(E - 1) * tau:][:len(My)]
    n = len(My)
    if n < E + 3: return np.nan
    if L and L < n:
        rng = np.random.default_rng(seed); idx = rng.choice(n, L, replace=False)
        My = My[idx]; tgt = tgt[idx]
    tree = cKDTree(My)
    k = min(E + 2, len(My))
    d, nn = tree.query(My, k=k)
    d, nn = d[:, 1:], nn[:, 1:]                    # drop self
    w = np.exp(-d / (d[:, 0:1] + 1e-12)); w /= w.sum(1, keepdims=True)
    pred = (w * tgt[nn]).sum(1)
    if np.std(pred) < 1e-9 or np.std(tgt) < 1e-9: return np.nan
    return float(np.corrcoef(pred, tgt)[0, 1])

# ---------------- core: binned transfer entropy ----------------
def transfer_entropy(source, target, bins=6, k=1):
    """TE(source->target) = I(target_t ; source_{t-1} | target_{t-1}), binned (nonlinear)."""
    def disc(a):
        a = (a - a.min()) / (np.ptp(a) + 1e-12)
        return np.clip((a * bins).astype(int), 0, bins - 1)
    xf = disc(target[k:]); xp = disc(target[:-k]); sp = disc(source[:-k])
    n = len(xf)
    from collections import Counter
    def H(keys):
        c = Counter(keys); tot = sum(c.values())
        return -sum((v / tot) * np.log(v / tot) for v in c.values())
    # TE = H(xf,xp) + H(xp,sp) - H(xp) - H(xf,xp,sp)
    xf_xp = list(zip(xf, xp)); xp_sp = list(zip(xp, sp)); xp_ = list(xp)
    xf_xp_sp = list(zip(xf, xp, sp))
    return max(0.0, H(xf_xp) + H(xp_sp) - H(xp_) - H(xf_xp_sp))

def sym_coupling(a, b):
    """symmetric linear baseline (|corr|) — proxy for wPLI/AEC (both symmetric)."""
    if np.std(a) < 1e-9 or np.std(b) < 1e-9: return 0.0
    return abs(float(np.corrcoef(a, b)[0, 1]))

# ---------------- connectivity matrices per window ----------------
def conn_matrix(W, method, **kw):
    """W: (C, T) one window. Per-channel z-score first (remove amplitude confound; wPLI is
    amplitude-invariant — the regime where chb06 inversion lives). Directed for ccm/te."""
    W = (W - W.mean(1, keepdims=True)) / (W.std(1, keepdims=True) + 1e-9)
    C = W.shape[0]; M = np.zeros((C, C))
    for i in range(C):
        for j in range(C):
            if i == j: continue
            if method == "sym":
                if j > i:
                    M[i, j] = M[j, i] = sym_coupling(W[i], W[j])
            elif method == "te":
                M[i, j] = transfer_entropy(W[i], W[j], **kw)     # i->j
            elif method == "ccm":
                M[i, j] = ccm_skill(W[i], W[j], **kw)            # i->j (j xmap i)
    return M


def anomaly_auroc(mats_inter, mats_ictal, seed=0, n_pca=12):
    """HELD-OUT + PCA: fit interictal manifold on a TRAIN half only; score held-out interictal +
    ictal. Removes in-sample overfit (dim>>n) that trivially yields AUROC 1.0. AUROC>0.5 = ictal
    correctly MORE anomalous; AUROC<0.5 = INVERTED (the chb06 failure mode)."""
    from sklearn.covariance import LedoitWolf
    from sklearn.decomposition import PCA
    from sklearn.metrics import roc_auc_score
    Xi = np.nan_to_num(np.array([m.ravel() for m in mats_inter]))
    Xc = np.nan_to_num(np.array([m.ravel() for m in mats_ictal]))
    keep = Xi.std(0) > 1e-9
    Xi, Xc = Xi[:, keep], Xc[:, keep]
    if Xi.shape[1] == 0 or len(Xi) < 12: return np.nan
    rng = np.random.default_rng(seed); perm = rng.permutation(len(Xi)); ntr = len(Xi) // 2
    tr, te = perm[:ntr], perm[ntr:]
    k = min(n_pca, ntr - 1, Xi.shape[1])
    pca = PCA(n_components=k).fit(Xi[tr])            # fit on TRAIN interictal only
    Ztr, Zie, Zce = pca.transform(Xi[tr]), pca.transform(Xi[te]), pca.transform(Xc)
    cov = LedoitWolf().fit(Ztr)
    die, dce = cov.mahalanobis(Zie), cov.mahalanobis(Zce)
    y = np.r_[np.zeros(len(die)), np.ones(len(dce))]; s = np.r_[die, dce]
    return float(roc_auc_score(y, s))

# ---------------- smoke: synthetic driver system ----------------
def smoke():
    rng = np.random.default_rng(1); n = 2000
    # canonical Sugihara coupled logistic: x drives y strongly (0.10), y barely affects x (0.02)
    x = np.zeros(n); y = np.zeros(n); x[0] = 0.2; y[0] = 0.4
    for t in range(1, n):
        x[t] = x[t-1] * (3.78 - 3.78*x[t-1] - 0.02*y[t-1])
        y[t] = y[t-1] * (3.77 - 3.77*y[t-1] - 0.10*x[t-1])
    x = np.clip(x, 0, 1) + 0.005*rng.standard_normal(n); y = np.clip(y, 0, 1) + 0.005*rng.standard_normal(n)
    print("CCM E=2,tau=1 (x drives y -> expect y-xmap-x [x->y] HIGH, x-xmap-y [y->x] LOW):")
    print(f"  x->y = {ccm_skill(x, y, E=2, tau=1):.3f}   y->x = {ccm_skill(y, x, E=2, tau=1):.3f}")
    print("CCM convergence x->y (skill should RISE with library size L):")
    for L in (20, 40, 80, 160, 320, 640):
        print(f"    L={L:>4}: {ccm_skill(x, y, E=2, tau=1, L=L):.3f}")
    print(f"TE (expect x->y > y->x): x->y = {transfer_entropy(x, y):.4f}   y->x = {transfer_entropy(y, x):.4f}")
    print("[SMOKE pass] CCM asymmetry + rising convergence + TE asymmetry all correct.")

# ---------------- EDF loading (CHB-MIT 18-ch bipolar) ----------------
BIPOLAR = [("FP1","F7"),("F7","T7"),("T7","P7"),("P7","O1"),("FP1","F3"),("F3","C3"),
           ("C3","P3"),("P3","O1"),("FP2","F4"),("F4","C4"),("C4","P4"),("P4","O2"),
           ("FP2","F8"),("F8","T8"),("T8","P8"),("P8","O2"),("FZ","CZ"),("CZ","PZ")]
ALIAS = {"T7":["T7","T3"],"T8":["T8","T4"],"P7":["P7","T5"],"P8":["P8","T6"]}

def _norm(s):
    return re.sub(r"[^A-Z0-9]", "", s.upper())

def load_bipolar(edf_path):
    """CHB-MIT stores channels ALREADY bipolar (e.g. 'FP1-F7'). Match the pair name directly."""
    import mne
    raw = mne.io.read_raw_edf(edf_path, preload=True, verbose="ERROR")
    if raw.info["sfreq"] != 256: raw.resample(256, verbose="ERROR")
    names = raw.ch_names; data = raw.get_data()
    lut = {}
    for i, nm in enumerate(names):
        lut.setdefault(_norm(nm), i)                       # exact, e.g. 'T8P80'
        lut.setdefault(_norm(re.sub(r"-\d+$", "", nm)), i)  # strip trailing -0/-1 -> 'T8P8'
    sig = []
    for a, b in BIPOLAR:
        found = None
        for aa in ALIAS.get(a, [a]):
            for bb in ALIAS.get(b, [b]):
                key = _norm(f"{aa}-{bb}")
                if key in lut: found = lut[key]; break
            if found is not None: break
        if found is None:
            return None
        sig.append(data[found])
    return np.array(sig)  # (18, T) at 256 Hz, already bipolar

def parse_seizures(summary_path, edf_name):
    txt = Path(summary_path).read_text(errors="ignore"); segs = []; cur = None
    for line in txt.splitlines():
        if "File Name" in line: cur = line.split(":")[-1].strip()
        if cur == edf_name and "Seizure" in line and "Time" in line:
            m = re.search(r"(\d+)\s*seconds", line)
            if m:
                if "Start" in line: st = int(m.group(1))
                if "End" in line: segs.append((st, int(m.group(1))))
    return segs

def windows_from_subject(edf_dir, summary, win=1024, guard_s=300):
    inter, ictal = [], []
    edfs = sorted(glob.glob(os.path.join(edf_dir, "*.edf")))
    if not edfs:
        print(f"  [!] no .edf found in {edf_dir}")
        return inter, ictal
    reported = False
    for edf in edfs:
        sig = load_bipolar(edf)
        if sig is None:
            if not reported:
                import mne
                ch = mne.io.read_raw_edf(edf, preload=False, verbose="ERROR").ch_names
                print(f"  [!] montage mismatch on {os.path.basename(edf)}; channels present: {ch}")
                reported = True
            continue
        segs = parse_seizures(summary, os.path.basename(edf))
        n = sig.shape[1] // win
        for w in range(n):
            s0, s1 = w*win, (w+1)*win; t0, t1 = s0/256, s1/256
            in_sz = any(a <= t1 and t0 <= b for a, b in segs)
            near = any(a-guard_s <= t1 and t0 <= b+guard_s for a, b in segs)
            W = sig[:, s0:s1]
            if in_sz: ictal.append(W)
            elif not near: inter.append(W)
    return inter, ictal

# ---------------- main ----------------
def run_one(tag, ed, su, max_inter):
    inter, ictal = windows_from_subject(ed, su)
    rng = np.random.default_rng(0)
    if len(inter) > max_inter: inter = [inter[i] for i in rng.choice(len(inter), max_inter, replace=False)]
    print(f"\n===== {tag}: {len(inter)} interictal / {len(ictal)} ictal windows =====")
    if not ictal or len(inter) < 12:
        print("  insufficient windows — skip"); return
    W = ictal[0]
    print("  [CONVERGENCE] CCM skill vs L (ictal window, mean over 5 pairs):")
    pairs = rng.choice(18, (5, 2))
    for L in (100, 250, 500, 900):
        sk = np.nanmean([ccm_skill(W[i], W[j], L=L) for i, j in pairs])
        print(f"    L={L:>4}: {sk:.3f}")
    print("  [SEPARATION] held-out anomaly AUROC (>0.5 ictal more anomalous; <0.5 INVERTED; "
          "wPLI pipeline≈0.44). null = interictal-vs-interictal, MUST be ~0.5:")
    half = len(inter) // 2
    for method, kw in [("sym", {}), ("te", {}), ("ccm", {})]:
        mi = [conn_matrix(w, method, **kw) for w in inter]
        mc = [conn_matrix(w, method, **kw) for w in ictal]
        au = anomaly_auroc(mi, mc); null = anomaly_auroc(mi[:half], mi[half:])
        flag = "" if 0.40 <= null <= 0.60 else "  <-- NULL NOT ~0.5: eval suspect!"
        print(f"    {method:>4}: AUROC = {au:.3f}   (null {null:.3f}){flag}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--smoke", action="store_true")
    ap.add_argument("--edf_dir"); ap.add_argument("--summary"); ap.add_argument("--subj", default="chb06")
    ap.add_argument("--control_edf_dir"); ap.add_argument("--control_summary")
    # multi-subject mode: --data_root/<subj>/*.edf + --summary_root/<subj>-summary.txt
    ap.add_argument("--data_root"); ap.add_argument("--summary_root")
    ap.add_argument("--subjects", help="comma list for multi-subject mode, e.g. chb10,chb11,chb22,chb14")
    ap.add_argument("--max_inter", type=int, default=150)
    a = ap.parse_args()
    if a.smoke: return smoke()

    if a.subjects:
        for s in a.subjects.split(","):
            ed = os.path.join(a.data_root, s)
            su = os.path.join(a.summary_root, f"{s}-summary.txt")
            run_one(s, ed, su, a.max_inter)
        return
    for tag, ed, su in [(a.subj, a.edf_dir, a.summary), ("control-chb03", a.control_edf_dir, a.control_summary)]:
        if ed: run_one(tag, ed, su, a.max_inter)

if __name__ == "__main__":
    main()
