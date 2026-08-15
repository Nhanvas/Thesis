"""
retrain_io.py — shared I/O + pure-logic helpers for PREREG 03 (PHA 1, step 3).

Both derive_weights.py (non-test weight search) and final_eval.py (one test pass)
import from here so they assemble components with the IDENTICAL recipe and share
the same weight-grid / Pareto / operating-point rule. Nothing scientific is
re-implemented in the two callers.

Design contract:
  * Data/checkpoint discovery + the Kaggle-extraction-tolerant loader are copied
    VERBATIM (behaviourally) from lstm_gate_full.py so the same datasets load the
    same way.
  * robust_z is the pinned recipe (median/MAD, inter+ictal pooled, per subject,
    +1e-9), identical to lstm_gate_full.robust_z and PROVENANCE_MAP.
  * The per-subject component assembly mirrors lstm_gate_full.py's L2 block
    exactly: recon via gae_joint.score_windows; temporal via
    lstm_temporal.score_full_array on flat-Z of the SAME GAE seed, warm-up filled
    with nanmedian(inter) on BOTH splits before robust_z; gamma via load_gamma.
  * The ensemble weighted sum comes from ensemble_recipe.build_ensemble (single
    source); no weight math is duplicated.

torch / torch_geometric / gae_joint / lstm_temporal are imported LAZILY (inside
the functions that need a GPU), so the pure-logic helpers below run in a plain
numpy/sklearn environment for smoke-testing.
"""
import os as _os, sys as _sys
_here = _os.path.dirname(_os.path.abspath(__file__))
for _p in (_here, _os.path.dirname(_here)):      # src/retrain/ and src/ (flat)
    if _p not in _sys.path:
        _sys.path.insert(0, _p)

import glob
import os
import random
import re
import shutil
from pathlib import Path

import numpy as np
from sklearn.metrics import roc_auc_score

import ensemble_recipe as ER   # single source for the weighted-sum ensemble

# ---- fixed splits (from lstm_gate_full.py / PREREG) -------------------------
VAL_SUBJS = ["chb10", "chb11", "chb22"]
TRAIN_SUBJS = ["chb01", "chb02", "chb04", "chb05", "chb07", "chb08",
               "chb09", "chb12", "chb19", "chb20", "chb21", "chb23"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
L_CONTEXT = 16          # PREREG_02: sequence context (15 past + current)
CANON_SEED = 42         # canonical model seed (GAE + LSTM)


# ============================================================================
# robust-z (pinned recipe) — identical to lstm_gate_full.robust_z
# ============================================================================
def robust_z(raw_i, raw_c):
    allx = np.concatenate([raw_i, raw_c])
    med = np.median(allx)
    mad = np.median(np.abs(allx - med)) + 1e-9
    return (raw_i - med) / mad, (raw_c - med) / mad


def window_auroc(scores_inter, scores_ictal):
    """Rank-based ensemble window AUROC (inter=0, ictal=1). NaN-safe."""
    si = np.asarray(scores_inter, float); sc = np.asarray(scores_ictal, float)
    si = si[~np.isnan(si)]; sc = sc[~np.isnan(sc)]
    if len(si) == 0 or len(sc) == 0:
        return float("nan")
    y = np.r_[np.zeros(len(si)), np.ones(len(sc))]
    return float(roc_auc_score(y, np.r_[si, sc]))


# ============================================================================
# checkpoint / data discovery (Kaggle-extraction tolerant) — from lstm_gate_full
# ============================================================================
def find_ckpts(root, prefix):
    """{seed: ('file', Path) | ('dir', Path)} for a checkpoint prefix. Prefers an
    intact .pt over an unpacked directory (Kaggle unpacks .pt into data.pkl dirs)."""
    p = Path(root); byseed = {}
    for c in p.rglob("*.pt"):
        if prefix in c.name:
            m = re.search(r"seed(\d+)", c.name)
            if m:
                byseed.setdefault(int(m.group(1)), []).append(("file", c, c.stat().st_size))
    for dpk in p.rglob("data.pkl"):
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
        raise FileNotFoundError(
            f"No '{prefix}*' ckpt under {p}. "
            f"sample data.pkl: {[str(x) for x in list(p.rglob('data.pkl'))[:6]]}")
    return out


def load_state(entry, work="/kaggle/working"):
    """Load a state_dict from either an intact .pt (file) or a Kaggle-unpacked dir."""
    import torch  # lazy
    kind, path = entry
    if kind == "file":
        return torch.load(str(path), map_location="cpu")
    Path(work).mkdir(parents=True, exist_ok=True)
    z = f"{work}/_rez_{path.name}_{random.randint(0, 10**6)}"
    shutil.make_archive(z, "zip", root_dir=str(path.parent), base_dir=path.name)
    os.replace(z + ".zip", z + ".pt")
    return torch.load(z + ".pt", map_location="cpu")


def find_data_dir(root, sample_glob):
    hits = list(Path(root).rglob(sample_glob))
    if not hits:
        raise FileNotFoundError(
            f"'{sample_glob}' not found under {root}. "
            f"top: {[str(x) for x in Path(root).glob('*')]}")
    return str(hits[0].parent)


def find_gamma_dir(root):
    for d in Path(root).rglob("*"):
        if d.is_dir() and "gamma" in d.name.lower() and \
                any(x.suffix == ".npy" for x in d.iterdir() if x.is_file()):
            return str(d)
    hits = list(Path(root).rglob("*gamma*.npy"))
    if hits:
        return str(hits[0].parent)
    raise FileNotFoundError(f"gamma dir not found under {root}")


def load_gamma(gdir, subj, split):
    """split in {'inter','ictal'}. Files: gamma_aec_{subj}_{inter,ictal}.npy."""
    want_inter = (split == "inter")
    for c in sorted(glob.glob(f"{gdir}/*{subj}*")):
        b = os.path.basename(c).lower()
        if not b.endswith(".npy"):
            continue
        is_inter = "inter" in b
        is_ictal = ("ictal" in b) and not is_inter
        if (want_inter and is_inter) or ((not want_inter) and is_ictal):
            return np.load(c).astype(np.float32)
    raise FileNotFoundError(f"gamma {subj}/{split} not in {gdir}")


# ============================================================================
# per-subject component assembly (mirrors lstm_gate_full.py L2 exactly)
# ============================================================================
def build_subject_components(gae, lstm, subj, adj_dir, feat_dir, gamma_dir,
                             suffix, device, L=L_CONTEXT):
    """Returns dict of robust-z components for one subject:
        {'zrecon': (zi, zc), 'ztemp': (zi, zc), 'zgamma': (zi, zc)}
    gae   = adopted GAE seed-k model (gae_joint.GAEModel, loaded)
    lstm  = LSTM seed-k model (lstm_temporal.LSTMPredictor, loaded)
    Warm-up (first L-1 windows/array) filled with nanmedian(interictal raw_temp)
    on BOTH splits before robust_z — the pinned convention (ΔTP=0 on headline)."""
    import gae_joint as G          # lazy (needs torch + torch_geometric)
    import lstm_temporal as T      # lazy

    ai = Path(adj_dir) / f"{subj}_interictal_adjs{suffix}.npy"
    ac = Path(adj_dir) / f"{subj}_ictal_adjs{suffix}.npy"
    fi = Path(feat_dir) / f"{subj}_interictal_features.npy"
    fc = Path(feat_dir) / f"{subj}_ictal_features.npy"

    # recon (GAE joint MSE score)
    rri = G.score_windows(gae, ai, fi, device)
    rrc = G.score_windows(gae, ac, fc, device)
    zri, zrc = robust_z(rri, rrc)

    # gamma (deterministic, retained)
    gi = load_gamma(gamma_dir, subj, "inter")
    gc = load_gamma(gamma_dir, subj, "ictal")
    zgi, zgc = robust_z(gi, gc)

    # temporal (LSTM prediction error on flat-Z of the SAME GAE seed)
    Zi = T.flat(T.compute_raw_Z(gae, ai, fi, device))
    Zc = T.flat(T.compute_raw_Z(gae, ac, fc, device))
    rti = T.score_full_array(lstm, Zi, L, device)   # first L-1 = NaN
    rtc = T.score_full_array(lstm, Zc, L, device)
    fill = np.nanmedian(rti)
    rti = np.where(np.isnan(rti), fill, rti)
    rtc = np.where(np.isnan(rtc), fill, rtc)
    zti, ztc = robust_z(rti, rtc)

    return {"zrecon": (zri, zrc), "ztemp": (zti, ztc), "zgamma": (zgi, zgc)}


def ensemble_from_components(comp, weights):
    """comp = output of build_subject_components -> (ens_inter, ens_ictal) via the
    single-source weighted sum. Order (recon, temporal, gamma) matches ENS_WEIGHTS."""
    zr_i, zr_c = comp["zrecon"]; zt_i, zt_c = comp["ztemp"]; zg_i, zg_c = comp["zgamma"]
    ens_i = ER.build_ensemble(zr_i, zt_i, zg_i, weights=weights)
    ens_c = ER.build_ensemble(zr_c, zt_c, zg_c, weights=weights)
    return ens_i, ens_c


# ============================================================================
# weight simplex grid + tie-break (PREREG_03 §2)
# ============================================================================
def simplex_grid(step=0.05):
    """All (wr, wt, wg) with wr+wt+wg=1 on the `step` lattice, each >= 0.
    Deterministic order. step=0.05 -> 231 points."""
    q = int(round(1.0 / step))
    if abs(q * step - 1.0) > 1e-9:
        raise ValueError("step must divide 1 evenly")
    pts = []
    for i in range(q + 1):
        for j in range(q + 1 - i):
            k = q - i - j
            pts.append((round(i / q, 10), round(j / q, 10), round(k / q, 10)))
    return pts


def _dist_to_equal(w):
    e = 1.0 / 3.0
    return sum((wi - e) ** 2 for wi in w) ** 0.5


def pick_weights_tiebreak_equal(grid_rows, tol=0.005):
    """grid_rows: list of dict(w=(wr,wt,wg), objective=<VAL macro AUROC>).
    Best objective; among all within `tol` of the best, choose the weight closest
    to (1/3,1/3,1/3). Returns (chosen_w, chosen_row, tied_rows)."""
    valid = [r for r in grid_rows if r["objective"] == r["objective"]]  # drop NaN
    if not valid:
        raise ValueError("no valid grid rows")
    best = max(r["objective"] for r in valid)
    tied = [r for r in valid if best - r["objective"] <= tol]
    chosen = min(tied, key=lambda r: _dist_to_equal(r["w"]))
    return chosen["w"], chosen, tied


def neighbours_pm(w, step=0.05):
    """The (up to) 6 adjacent simplex points reachable by moving `step` from one
    coordinate to another — used for the ±0.05 weight-sensitivity report."""
    out = []
    for src in range(3):
        for dst in range(3):
            if src == dst:
                continue
            nw = list(w)
            nw[src] = round(nw[src] - step, 10)
            nw[dst] = round(nw[dst] + step, 10)
            if nw[src] < -1e-9:
                continue
            out.append(tuple(nw))
    # de-dup
    seen, uniq = set(), []
    for p in out:
        key = tuple(round(x, 6) for x in p)
        if key not in seen and abs(sum(p) - 1.0) < 1e-6:
            seen.add(key); uniq.append(p)
    return uniq


# ============================================================================
# Pareto frontier + operating-point rule (PREREG_03 §3, option A)
# ============================================================================
def mark_pareto(pooled_rows):
    """Set r['on_pareto_frontier'] for a list of pooled dicts with keys
    'sensitivity' and 'fp_per_day' (maximize sens, minimize fp_per_day).
    Mutates in place and returns the list."""
    for r in pooled_rows:
        dominated = any(
            (o["sensitivity"] >= r["sensitivity"] and o["fp_per_day"] <= r["fp_per_day"]
             and (o["sensitivity"] > r["sensitivity"] or o["fp_per_day"] < r["fp_per_day"]))
            for o in pooled_rows if o is not r)
        r["on_pareto_frontier"] = not dominated
    return pooled_rows


def select_operating_points_optionA(pooled_rows, target_fp=40.0, fp_cap=75.0):
    """Pre-registered option-A rule on the Pareto frontier:
        balanced  = frontier point with FP/day nearest target_fp (40)
        high-sens = max sensitivity among frontier points with FP/day <= fp_cap (75)
    Returns dict(balanced=row, highsens=row, notes=...). Deterministic tie-breaks."""
    frontier = [r for r in pooled_rows if r.get("on_pareto_frontier")]
    if not frontier:
        raise ValueError("empty Pareto frontier")
    notes = []

    # balanced: nearest FP/day to target; tie -> higher sensitivity
    balanced = min(frontier, key=lambda r: (abs(r["fp_per_day"] - target_fp),
                                            -r["sensitivity"]))
    # high-sens: max sensitivity s.t. FP/day <= cap; tie -> lower FP/day
    cands = [r for r in frontier if r["fp_per_day"] <= fp_cap]
    if cands:
        highsens = max(cands, key=lambda r: (r["sensitivity"], -r["fp_per_day"]))
    else:
        highsens = min(frontier, key=lambda r: r["fp_per_day"])
        notes.append(f"no frontier point with FP/day<= {fp_cap}; "
                     f"high-sens fell back to the lowest-FP frontier point")
    return dict(balanced=balanced, highsens=highsens, notes=notes)
