#!/usr/bin/env python
"""
eur_abl.py -- Euréka ablation suite on the V5 model (Track F, chat D31-F; design results/eureka_d31f/STEP1_DESIGN.md,
approved by the author 19/11/2026 20:35). Inference only: the four committed V5 checkpoints
data/models_v2/gae_v2_clean_seed{42,1,2,3}.pt on the defense-time data copy (v9-x3-fold1/3) and the external features
(thesis-r2-external-features). Written before any output.

Every stage of V5 is the record code, imported read only through r2_r1 (whose import guard requires every record
module to come from this repository). A variant swaps ONE function; everything else is the record code:
  latent        p2_dump_seeds23.run_model (8a: the same construction with an empty propagation graph, self loops only;
                8b (added 20/11, chat D32-F, approved by the author 13:04): no encoder -- the distance is taken on the
                30-value node input the encoder receives, built by node_x = the record construction;
                O7 (D32-F 20/11, approved 14:14): the latent averaged with its previous and next valid window of the same
                file before the distance; R0 / 10a / 10b (D32-F 20/11, approved 16:17; design
                results/eureka_d32f/DESIGN_PC1.md): GAEs RETRAINED in this run on the record training windows with the
                thesis recipe (f1_core's tensor loop, gate G-pc1vec) -- R0 full node input (control), 10a without the 7
                absolute features, 10b without the relative and absolute gamma powers -- then the V5 chain unchanged)
  distance      per-channel LedoitWolf Mahalanobis (x1_external.model_outputs); 1a diagonal, 1b Euclidean; 4a reference
                fitted on the clean windows of the 12 training patients (leave the scored patient out); 4b / 4c per-file
                baselines of 10 / 30 min (e16_recording_baseline.arm_distances arms a / c); O6a / O6b (D32-F 20/11,
                approved 14:14; design results/eureka_d32f/DESIGN_O6_O7.md): a per-patient Gaussian-mixture normal model
                of each channel's latent -- K components (O6a: BIC over 1-4; O6b: 2), Ledoit-Wolf per component, score =
                the smallest Mahalanobis distance to a component (K = 1 is exactly the V5 distance, gate G-mix1)
  members       e17b_latent_family.member (robust z per channel, order statistic, minus a +-15 min running median per
                file); 2a no drift correction, 2b level + spread (running median and running MAD, same window); 3a / 3m /
                3c one member; 3g / 3r the gamma-AEC / reconstruction readout added as a fifth member (as E17)
  ensemble      percentile ranks, equal mean (e22_test_oneshot.final_scalar); budget signal = mean robust z of the same
                parts (p3_levers.member_mean_z)
  detection     p3c_freeze.run_budget (smoothing as a parameter for 5a: 1 / 3 / 9 windows), localizer cpd and hybrid
  k             p3_levers.calibrate on the 15 development patients, seed 42, per variant (V5's own rule)
Arms per variant: own (clip(q, 0.005, 0.02), the variant's own k) and fixed (0.005 for every patient). 6a = V0 fixed;
7a = V0 detector stage; 7b = V0 hybrid stage. A detection curve over a global budget (detector stage) gives the
sensitivity at matched FP/day (reading ii of the design).

Gates (STOP unless PASS):
  G-data   every earlier .npz sha256 = docs/PROVENANCE_V2.md; every external file = R1_SMOKE's pinned sha256
  SMOKE    chb01 + chb03 (+ the first external case) end to end before the full run: R1.0 rows, G-D0, G-x0, G-eng, every
           variant computed once; measured seconds -> projection (STOP if > 10.5 h)
  R1.0-dev / R1.0-test / GE / G-k    r2_r1.r10 unchanged (V0 = the V5 rows; external within |dtp| <= 1, |dfp| <= 2)
  G-D0     the V0 distances recomputed in the variant pass = the stored r2_r1 distances, exactly
  G-x0     V0's scalar and budget signal = e22_test_oneshot.final_scalar and p3_levers.member_mean_z, exactly
  G-eng    run_budget with the smoothing parameter = p3c_freeze.run_budget for V0 (own = L2f, fixed = frozen), exactly
  G-enc    the 8a encoder with the window's own graph = p2_dump_seeds23.run_model (first case of each set), exactly
  G-kv0    V0's k from the variant pass = results/p3_levers/calibration.json (relative 1e-6)
  G-worker every pool job ran the same eur_abl.py / r2_r1.py / record modules as the parent (sha256)
  G-self   unit checks on synthetic arrays at start (member construction = e17b, distances by definition)
Variant selection (added 20/11, D32-F): EUR_VARIANTS="V0,8b" runs only those variants (V0 is always included: the
record gates and the paired differences need it); EUR_TAG names the output folder (default abl). The 4a reference
pass runs only when a 4a-type variant is selected.
Arm seeds (added 21/11, chat D34-F, PC7; design results/eureka_d34f/DESIGN_PC7.md, approved 01:26): the retrained arms
(R0 / 10a / 10b) use the seeds of EUR_ARM_SEEDS (comma list; default = the four V0 seeds, so PC1 runs unchanged); V0 keeps
the four V5 seeds. EUR_ARM_REUSE lists arm seeds whose checkpoints are copied from the committed run EUR_PC7_REF
(<ref>/models/<arm>/) instead of trained (gate G-pc7reuse); with EUR_PC7_REF set the run also records G-pc7plat (library
versions = the reference run) and G-pc7rep (seed 42, 1 epoch: epoch-1 loss = the reference log exactly) -- both without
stopping -- and stops unless R0's k = the reference k (G-pc7k) and the reused seeds' R0 rows = the reference rows
(G-pc7r0). Trainings run in chunks of `workers`; a further chunk starts only if elapsed + the last chunk's duration +
PC7_RESERVE_S <= PC7_GUARD_H (gate G-guard lists the seeds trained). Variant R0s = R0's latents with k recalibrated on
each seed's own development scores (kmode "seed"; every other variant: k of seed 42). An arm's node input uses the
constants of its own checkpoint json (= V5's, gate G-pc1const).
PC8 (added 21/11, chat D37-F; design results/eureka_d37f/DESIGN_PC8.md): arms P8a (without the 5 log band powers), P8b
(without log line length + kurtosis), P8c (the 7 absolute features only), retrained like R0 / 10a / 10b. Seeds and reuse
per arm: EUR_ARM_SEEDS_<ARM> / EUR_ARM_REUSE_<ARM> override EUR_ARM_SEEDS / EUR_ARM_REUSE for that arm (unset: PC1 / PC7
behaviour unchanged). Gate G-pc8cols: the dropped columns by name = the design, seed 42 in every PC8 arm. run_meta records
the CPU model (/proc/cpuinfo) and the seeds of every arm.
Outputs: WORK/eureka/<tag>/ (run_meta.json, gates.json, data_sha256.csv, r10/, per_subject.csv, errors.csv, curve.csv,
k.csv, jobs.csv, projection.json, SUMMARY.md). The reading is done by src/eur_abl_aggregate.py (committed first); PC7 by
src/eur_pc7_read.py.
  python src/eur_abl.py [--workers N]
Test mode (synthetic world, build container only): R2_TEST=1 (see src/eur_abl_synthetic_test.py).
"""
import hashlib
import json
import os
import platform
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

if platform.system() == "Windows" and "resource" not in sys.modules:      # r2_r1 logs peak memory with `resource`
    import types
    _r = types.ModuleType("resource")
    _r.RUSAGE_SELF, _r.RUSAGE_CHILDREN = 0, -1
    _r.getrusage = lambda *_: types.SimpleNamespace(ru_maxrss=0)
    sys.modules["resource"] = _r

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import r2_r1 as R1                       # noqa: E402  (import guard: record modules from REPO/src only)
import e16_recording_baseline as E16     # noqa: E402
import e17b_latent_family as F17         # noqa: E402

PS, P3L, P3C, E22, X1, PD, TGV2, R0 = R1.PS, R1.P3L, R1.P3C, R1.E22, R1.X1, R1.PD, R1.TGV2, R1.R0
_OUT = [m.__name__ for m in (E16, F17) if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUT:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUT}")
log = R1.log

TAGS, DEV, TEST, TRAIN, VAL = R1.TAGS, list(R1.DEV), list(R1.TEST), list(R1.TRAIN), list(R1.VAL)
EXT = list(R1.EXT)
K_RECORD = R1.K_RECORD
SCR = R1.SCRATCH / "eur"
MEMBERS = tuple(F17.MEMBERS.values())                   # (6, 9, 12, "mean") -- V5
ARMS = {"own": (0.005, P3C.CAP), "fixed": (0.005, 0.005)}
CURVE_TOPS = (0.003, 0.004, 0.005, 0.0065, 0.0075, 0.01)
REFUSE_H = 10.5
TEST_MODE = bool(os.environ.get("R2_TEST"))
WIDTH = 451                                               # +-15 min running window (e17b_latent_family.member)


def _v(dist="maha", enc="own", members=MEMBERS, drift="level", extra=(), smooth=5, text="", kmode="s42"):
    return dict(dist=dist, enc=enc, members=tuple(members), drift=drift, extra=tuple(extra), smooth=smooth, text=text,
                kmode=kmode)


VARIANTS = {
    "V0": _v(text="V5 system"),
    "1a": _v(dist="diag", text="diagonal covariance instead of Mahalanobis"),
    "1b": _v(dist="eucl", text="Euclidean distance instead of Mahalanobis"),
    "4a": _v(dist="ref", text="reference = clean windows of the training patients (leave-self-out)"),
    "4b": _v(dist="base10", text="reference = first 10 min of each file"),
    "4c": _v(dist="base30", text="reference = first 30 min of each file"),
    "2a": _v(drift="none", text="no drift correction"),
    "2b": _v(drift="levspread", text="drift correction of level and spread"),
    "3a": _v(members=(9,), text="one member: 9th largest"),
    "3m": _v(members=("mean",), text="one member: channel mean"),
    "3c": _v(members=(1,), text="one member: largest"),
    "3g": _v(extra=("gamma",), text="+ gamma-AEC readout (fifth member)"),
    "3r": _v(extra=("recon",), text="+ reconstruction-error readout (fifth member)"),
    "5a1": _v(smooth=1, text="smoothing 1 window"),
    "5a3": _v(smooth=3, text="smoothing 3 windows"),
    "5a9": _v(smooth=9, text="smoothing 9 windows"),
    "8a": _v(enc="self", text="no edges at inference (self loops only)"),
    "8b": _v(enc="input", text="no encoder: Mahalanobis on the 30-value node input the GAE receives"),
    "O6a": _v(dist="mixbic", text="latent mixture normal model, K by BIC (1-4), smallest component Mahalanobis"),
    "O6b": _v(dist="mix2", text="latent mixture normal model, K = 2, smallest component Mahalanobis"),
    "O7": _v(enc="ctx3", text="latent averaged over 3 windows (previous, own, next valid window of the file)"),
    "R0": _v(enc="armR0", text="GAE retrained here (CPU, thesis recipe), full node input: control of 10a / 10b"),
    "10a": _v(enc="arm10a", text="GAE retrained without the 7 absolute features (node input 23, target 5)"),
    "10b": _v(enc="arm10b", text="GAE retrained without the gamma powers, relative and absolute (input 28, target 10)"),
    "R0s": _v(enc="armR0", kmode="seed", text="R0 with k recalibrated on each seed's own development scores (PC7, Q6)"),
    "P8a": _v(enc="armP8a", text="GAE retrained without the 5 log band powers (input 25, target 7; PC8)"),
    "P8b": _v(enc="armP8b", text="GAE retrained without log line length and kurtosis (input 28, target 10; PC8)"),
    "P8c": _v(enc="armP8c", text="GAE retrained on the 7 absolute features only (input 7, target 7; PC8)"),
}
PC7_GUARD_H, PC7_RESERVE_S = 11.3, 4500.0
REUSE_FILES = ("gae_v2_{t}.pt", "gae_v2_{t}.json", "gae_v2_{t}_DONE.json", "training_log_{t}.csv")


def _env_list(name, arm):
    """EUR_<name>_<ARM> (per arm; added 21/11, chat D37-F, PC8) else EUR_<name>; in test mode EUR_TEST_<name>[_<ARM>]
    first. Unset per-arm variables leave PC1 / PC7 behaviour unchanged."""
    test = bool(os.environ.get("R2_TEST"))
    keys = ([f"EUR_TEST_{name}_{arm}"] if (test and arm) else []) + ([f"EUR_{name}_{arm}"] if arm else []) + \
           ([f"EUR_TEST_{name}"] if test else []) + [f"EUR_{name}"]
    for k in keys:
        if os.environ.get(k, "").strip():
            return os.environ[k]
    return ""


def arm_tags(arm=None):
    """arm seeds (EUR_ARM_SEEDS_<ARM> or EUR_ARM_SEEDS; default = the four V0 seeds). Test mode: EUR_TEST_ARM_SEEDS[_<ARM>]
    overrides."""
    seeds = [int(x) for x in _env_list("ARM_SEEDS", arm).split(",") if x.strip()]
    return [f"clean_seed{x}" for x in seeds] if seeds else list(TAGS)


def reuse_tags(arm=None):
    return [f"clean_seed{int(x)}" for x in _env_list("ARM_REUSE", arm).split(",") if x.strip()]


def pc7_ref():
    r = os.environ.get("EUR_PC7_REF", "")
    return (REPO / r) if r else None


def seeds_of(vid):
    enc = VARIANTS[vid]["enc"]
    return arm_tags(enc[3:]) if enc.startswith("arm") else list(TAGS)
# PC1 arms: columns kept of the 30-value node input [adjacency 0-17 | relative band powers 18-22 (delta..gamma) |
# 7 absolute features 23-29 (log band powers delta..gamma, log line length, kurtosis)] and of the 12-value
# reconstruction target [relative band powers 0-4 | absolute features 5-11]
# PC8 arms (21/11, chat D37-F; design results/eureka_d37f/DESIGN_PC8.md): P8a without the 5 log band powers (input 23-27,
# target 5-9), P8b without log line length + kurtosis (input 28-29, target 10-11), P8c the 7 absolute features only.
PC1_ARMS = {"R0": (list(range(30)), list(range(12))),
        "10a": (list(range(23)), list(range(5))),
        "10b": ([i for i in range(30) if i not in (22, 27)], [i for i in range(12) if i not in (4, 9)]),
        "P8a": ([i for i in range(30) if i not in range(23, 28)], [i for i in range(12) if i not in range(5, 10)]),
        "P8b": ([i for i in range(30) if i not in (28, 29)], [i for i in range(12) if i not in (10, 11)]),
        "P8c": (list(range(23, 30)), list(range(5, 12)))}
IN_NAMES = ([f"adj{c}" for c in range(18)] + [f"rel_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] +
            [f"logbp_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")] + ["log_linelen", "slog_kurtosis"])
OUT_NAMES = IN_NAMES[18:]
PC8_DROP = {"P8a": {f"logbp_{b}" for b in ("delta", "theta", "alpha", "beta", "gamma")},      # design §2, by name
            "P8b": {"log_linelen", "slog_kurtosis"},
            "P8c": set(IN_NAMES[:23])}
PC1_EPOCHS = 200
MIX_SAMPLE, MIX_KMAX, MIX_MIN, MIX_MIN_SHARE, MIX_SEED = 5000, 4, 64, 0.05, 42


def selected():
    """EUR_VARIANTS (comma list) or every variant; V0 always first."""
    want = [v.strip() for v in os.environ.get("EUR_VARIANTS", "").split(",") if v.strip()]
    if not want:
        return list(VARIANTS)
    bad = [v for v in want if v not in VARIANTS]
    if bad:
        raise SystemExit(f"STOP: unknown variants {bad}")
    return ["V0"] + [v for v in VARIANTS if v in want and v != "V0"]
STATE = R1.STATE


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


CODE_FILES = {n: Path(m.__file__) for n, m in (("eur_abl", sys.modules[__name__]), ("r2_r1", R1), ("e16", E16),
                                                ("e17b", F17), ("p3c_freeze", P3C), ("p3_levers", P3L),
                                                ("p2_scalars", PS), ("e22", E22), ("x1_external", X1),
                                                ("p2_dump_seeds23", PD))}
CODE_SHA = sha16(__file__)


def code_shas():
    return {n: sha16(p) for n, p in CODE_FILES.items()}


# ============================================================================ inputs
def build_views(dev, test, ext):
    """links SCRATCH/r1_views/{earlier,ext} as r2_r1.build_views does (earlier = v9-x3-fold* record .npz; ext =
    thesis-r2-external-features), without the new CHB-MIT dataset, which this suite does not use. Symlink, else hard
    link, else copy (Windows)."""
    import shutil
    t = time.time()
    shutil.rmtree(R1.VIEWS, ignore_errors=True)
    src = {"earlier": {c: R0.locate_earlier(c) for c in list(dev) + list(test)},
           "ext": {c: R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_lf.npz"))
                                    if R1._under(p, "thesis-r2-external-features")], f"{c}_lf.npz") for c in ext}}
    for kind, m in src.items():
        d = R1.VIEWS / kind
        d.mkdir(parents=True, exist_ok=True)
        for c, p in m.items():
            dst = d / (f"{c}_lf.npz" if kind == "ext" else f"{c}.npz")
            for how in (dst.symlink_to, lambda q: os.link(q, dst), lambda q: shutil.copyfile(q, dst)):
                try:
                    how(p)
                    break
                except OSError:
                    continue
    R1.phase("views", t)
    return src


def gate_data(src):
    rows, bad = [], []
    prov = R0.provenance_v2()
    pin_f = REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
    pin = pd.read_csv(pin_f) if pin_f.exists() else pd.DataFrame(columns=["dataset", "file", "sha256"])
    pin = pin[pin.dataset == "thesis-r2-external-features"].set_index("file").sha256.to_dict()
    for kind, m in src.items():
        for c, p in m.items():
            s = R0.sha256_file(p)
            want = (prov.get(c, (None, None))[1] if kind == "earlier" else pin.get(Path(p).name))
            rows.append(dict(kind=kind, case=c, file=Path(p).name, bytes=Path(p).stat().st_size, sha256=s, want=want,
                             source=str(p)))
            if want is None and not TEST_MODE:
                bad.append(f"{c}: no pinned sha256")
            elif want is not None and s != want:
                bad.append(f"{c}: sha256 {s[:16]} != {want[:16]}")
    pd.DataFrame(rows).to_csv(R1.out_dir() / "data_sha256.csv", index=False)
    R1.gate(dict(gate="G-data", status="PASS" if not bad else "FAIL", files=len(rows), bad=bad[:20],
                 pinned=int(sum(r["want"] is not None for r in rows)),
                 summary=f"{len(rows)} files hashed, {len(bad)} differ" + (" (test mode: unpinned allowed)" if TEST_MODE else "")))


# ============================================================================ building blocks
def model_inputs(z):
    """the inputs of x1_external.model_outputs (verbatim construction)."""
    idx = np.flatnonzero(~z["is_signal_loss"].astype(bool))
    adj = z["adj"][idx].astype(np.float32); adj[~np.isfinite(adj).all(axis=(1, 2))] = 0.0
    bp5 = z["bp5"][idx].astype(np.float32); bp5[~np.isfinite(bp5)] = 0.0
    f7 = z["f7"][idx].astype(np.float64)
    xn = (bp5 - bp5.min(axis=1, keepdims=True)) / (bp5.max(axis=1, keepdims=True) - bp5.min(axis=1, keepdims=True) + 1e-8)
    return idx, adj, xn, f7


def node_x(tag, adj, xn, f7, meta=None):
    """the node input the encoder receives (n x 18 x 30, float32): normalised adjacency row 18 + relative band powers 5
    + the 7 clipped absolute features with the checkpoint's constants -- p2_dump_seeds23.run_model's construction, line
    for line (torch ops). encode() builds its graphs from this array, so gate G-enc (encode with the window graph =
    run_model, exactly) also proves that this is the record's input. meta: a retrained arm's checkpoint json (its
    add_mean / add_std / clip = V5's, gate G-pc1const); default the V5 checkpoint of the tag."""
    import torch
    if meta is None or "add_mean" not in meta:
        meta = json.loads((PD.CKPT / f"gae_v2_{tag}.json").read_text())
    mu, sd, clip = np.array(meta["add_mean"]), np.array(meta["add_std"]), meta["clip"]
    fa = ((np.clip((f7 - mu) / sd, -clip, clip) + clip) / (2 * clip)).astype(np.float32)
    n = len(adj)
    X = None
    for i in range(n):
        A = torch.tensor(adj[i]); An = A / (A.amax() + 1e-8)
        xt = torch.cat([torch.tensor(xn[i].astype(np.float32)), torch.tensor(fa[i])], dim=1)
        xi = torch.cat([An, xt], dim=1).numpy()
        if X is None:
            X = np.empty((n,) + xi.shape, np.float32)
        X[i] = xi
    return X if X is not None else np.empty((0, 18, 30), np.float32)


def encode(tag, adj, xn, f7, prop="own", ckpt_dir=None):
    """p2_dump_seeds23.run_model's construction; prop 'self' = empty propagation graph (GCN self loops only). The node
    input keeps the window's own connectivity row in both cases (as F-A1.4's I-self). ckpt_dir: a PC1 arm's retrained
    checkpoints (their json holds the kept input columns)."""
    import torch
    from torch_geometric.data import Data, Batch
    from torch_geometric.utils import dense_to_sparse
    import gae_joint as G
    E8 = R1.E8
    ck = (Path(ckpt_dir) if ckpt_dir else PD.CKPT) / f"gae_v2_{tag}.pt"
    meta = json.loads(ck.with_suffix(".json").read_text())
    X = node_x(tag, adj, xn, f7, meta if ckpt_dir else None)
    if "keep_in" in meta:
        X = np.ascontiguousarray(X[:, :, meta["keep_in"]])
    model = G.GAEModel(in_dim=meta["in_dim"], bands=meta["out_x"])
    model.load_state_dict(torch.load(str(ck), map_location="cpu"), strict=True)
    model.eval()
    n = len(adj)
    Z = np.empty((n, G.N_CH, G.LATENT_DIM), np.float32)
    with torch.no_grad():
        for s in range(0, n, E8.CHUNK):
            e = min(s + E8.CHUNK, n)
            dl = []
            for i in range(s, e):
                A = torch.tensor(adj[i])
                ei, ew = dense_to_sparse(A if prop == "own" else torch.zeros_like(A))
                dl.append(Data(x=torch.from_numpy(X[i]), edge_index=ei, edge_attr=ew))
            b = Batch.from_data_list(dl)
            Z[s:e] = model.encoder(b.x, b.edge_index, b.edge_attr).view(b.num_graphs, G.N_CH, G.LATENT_DIM).numpy()
    return Z


def d_maha(Z):
    from sklearn.covariance import LedoitWolf
    return np.column_stack([LedoitWolf().fit(Z[:, c, :].astype(np.float64)).mahalanobis(Z[:, c, :].astype(np.float64))
                            for c in range(Z.shape[1])]).astype(np.float64)


def mix_channel(X, kmode):
    """O6 for one channel: X (n x d, float64). kmode 'bic' (K in 1..MIX_KMAX by the lowest BIC) or an int K.
    Returns (distance n, info dict). K = 1 is exactly LedoitWolf().fit(X).mahalanobis(X)."""
    from sklearn.covariance import LedoitWolf
    from sklearn.mixture import GaussianMixture
    n = len(X)
    rng = np.random.default_rng(MIX_SEED)
    S = X[np.sort(rng.choice(n, MIX_SAMPLE, replace=False))] if n > MIX_SAMPLE else X
    fits = {}
    ks = range(1, MIX_KMAX + 1) if kmode == "bic" else [int(kmode)]
    for k in ks:
        if k == 1:
            fits[1] = None
            continue
        g = GaussianMixture(k, covariance_type="full", reg_covar=1e-6, n_init=3, random_state=MIX_SEED).fit(S)
        fits[k] = g
    if kmode == "bic":
        bic = {k: (GaussianMixture(1, covariance_type="full", reg_covar=1e-6, n_init=3, random_state=MIX_SEED).fit(S)
                   if k == 1 else fits[k]).bic(S) for k in ks}
        K = min(bic, key=lambda k: (bic[k], k))
    else:
        K, bic = int(kmode), {}
    if K == 1:
        return LedoitWolf().fit(X).mahalanobis(X), dict(K=1, K_used=1, dropped=0, bic=bic, lab=np.zeros(n, int))
    g = fits[K]
    P = g.predict_proba(X)
    lab = P.argmax(1)
    keep = [c for c in range(K) if (lab == c).sum() >= max(MIX_MIN, MIX_MIN_SHARE * n)]   # a component must be a
    # substantial background state (>= 5 % of the windows): a small component could hold a patient's seizures and mask them
    dropped = K - len(keep)
    if not keep:
        return LedoitWolf().fit(X).mahalanobis(X), dict(K=K, K_used=1, dropped=dropped, bic=bic, lab=np.zeros(n, int))
    lab = np.asarray(keep)[P[:, keep].argmax(1)]
    if len(keep) == 1:
        return LedoitWolf().fit(X).mahalanobis(X), dict(K=K, K_used=1, dropped=dropped, bic=bic, lab=np.zeros(n, int))
    D = np.column_stack([LedoitWolf().fit(X[lab == c]).mahalanobis(X) for c in keep])
    return D.min(axis=1), dict(K=K, K_used=len(keep), dropped=dropped, bic=bic, lab=lab)


def d_mix(Z, kmode, flags=None):
    """O6 on every channel; flags: optional (flagged, unflagged) bool arrays (n) of background windows with / without
    the 5-SD flag -> the share of each outside the channel's largest component (descriptive premise)."""
    cols, info = [], []
    for c in range(Z.shape[1]):
        d, inf = mix_channel(Z[:, c, :].astype(np.float64), kmode)
        cols.append(d)
        lab = inf.pop("lab")
        big = np.bincount(lab).argmax()
        r = dict(channel=c, K=inf["K"], K_used=inf["K_used"], dropped=inf["dropped"],
                 share_outside_largest=float((lab != big).mean()))
        if flags is not None:
            fg, ug = flags
            r["flag_share_outside_largest"] = float((lab[fg] != big).mean()) if fg.any() else np.nan
            r["unflag_share_outside_largest"] = float((lab[ug] != big).mean()) if ug.any() else np.nan
        info.append(r)
    return np.column_stack(cols).astype(np.float64), info


def ctx3(Z, wf):
    """O7: each window's latent averaged with the previous and next window of the same file (valid-window sequence)."""
    Z = Z.astype(np.float64)
    out = np.empty_like(Z)
    for f in np.unique(wf):
        w = np.flatnonzero(wf == f)
        X = Z[w]
        s = X.copy(); c = np.ones(len(w))
        if len(w) > 1:
            s[1:] += X[:-1]; c[1:] += 1
            s[:-1] += X[1:]; c[:-1] += 1
        out[w] = s / c[:, None, None]
    return out


def d_diag(Z):
    X = Z.astype(np.float64)
    mu, var = X.mean(axis=0), X.var(axis=0) + 1e-12
    return (((X - mu) ** 2) / var).sum(axis=2)


def d_eucl(Z):
    X = Z.astype(np.float64)
    return ((X - X.mean(axis=0)) ** 2).sum(axis=2)


def d_ref(Z, loc, prec):
    """squared Mahalanobis distance of each channel's latent to a fixed reference (loc: C x d, prec: C x d x d)."""
    X = Z.astype(np.float64) - loc[None]
    return np.einsum("ncd,cde,nce->nc", X, prec, X)


def conv(D, ext):
    """record convention: CHB-MIT distances stored as float32 and read back as float64; external kept float64."""
    return np.asarray(D, np.float64) if ext else np.asarray(np.asarray(D, np.float32), np.float64)


def _roll_med(v, wf):
    out = np.empty_like(v)
    for f in np.unique(wf):
        w = np.flatnonzero(wf == f)
        out[w] = pd.Series(v[w]).rolling(WIDTH, min_periods=1, center=True).median().values
    return out


def member_series(D, wf, ks, drift):
    """e17b_latent_family.member for drift 'level' (identical construction); 'none' and 'levspread' change only the
    correction step."""
    okk = np.ones(len(D), bool)
    Zc = np.column_stack([E16.rz(D[:, j], okk) for j in range(D.shape[1])])
    out = []
    for k in ks:
        v = Zc.mean(axis=1) if k == "mean" else -np.sort(-Zc, axis=1)[:, k - 1]
        if drift == "level":
            o = v.copy()
            for f in np.unique(wf):                      # identical loop to e17b_latent_family.member
                w = np.flatnonzero(wf == f)
                o[w] = v[w] - pd.Series(v[w]).rolling(WIDTH, min_periods=1, center=True).median().values
            v = o
        elif drift == "levspread":
            med = _roll_med(v, wf)
            v = (v - med) / (_roll_med(np.abs(v - med), wf) + 1e-9)
        elif drift != "none":
            raise ValueError(drift)
        out.append(v)
    return out


def scalar_and_m(lite, parts_valid, extra_full=()):
    full = [PS._full(lite, p) for p in parts_valid] + list(extra_full)
    x = np.mean([PS.pct(v, lite["ok"]) for v in full], axis=0)
    m = np.mean([E16.rz(v, lite["ok"]) for v in full], axis=0)
    return x, m


def run_budget_s(ctx, s, tag, x, q, floor, cap, name, rows, errs, smooth):
    """p3c_freeze.run_budget with the smoothing as a parameter (identical otherwise; gate G-eng)."""
    E18 = P3C.E18
    top = P3C.budget(q, floor, cap)
    det = PS.d1_events(ctx, x, smooth, top)
    thr = np.nanquantile(PS.smoothed(ctx, x, smooth), 1 - top)
    stages, pairs = {"detector": det}, {}
    for mode in ("cpd", "hybrid"):
        stages[mode], pairs[mode] = P3L.localize(ctx, x, det, thr, mode)
    rec_s = ctx["n"] * PS.WIN
    for st, ev in stages.items():
        tp, fp, nr, h = PS.score(ctx, ev)
        k, ns = PS.caught(PS.short_refs(ctx), ev)
        rows.append(dict(subject=s, seed=tag, budget=name, stage=st, top=top, tp=tp, fp=fp, n_ref=nr, nonict_h=h,
                         short_tp=k, short_n=ns, review_s=float(sum(b - a for v in ev.values() for a, b in v)), rec_s=rec_s))
    for f, ra, rb, h0, h1 in E18.match_errors(P3L.refs_of(ctx), det):
        c0, c1 = pairs["cpd"][(f, h0, h1)]; y0, y1 = pairs["hybrid"][(f, h0, h1)]
        errs.append(dict(subject=s, seed=tag, budget=name, det_on=h0 - ra, det_off=h1 - rb, cpd_on=c0 - ra,
                         cpd_off=c1 - rb, hyb_on=y0 - ra, hyb_off=y1 - rb))


def self_checks():
    """G-self: member_series('level') = e17b_latent_family.member exactly; distances by definition."""
    rng = np.random.default_rng(0)
    D = rng.gamma(2.0, 1.0, (900, 18)); wf = np.repeat([0, 1, 2], 300)
    bad = []
    for k in MEMBERS:
        if not np.array_equal(member_series(D, wf, (k,), "level")[0], F17.member(D, wf, k)):
            bad.append(f"member {k}")
    Z = rng.normal(0, 1, (500, 18, 16)).astype(np.float32)
    X = Z.astype(np.float64)
    if not np.allclose(d_eucl(Z)[:, 3], ((X[:, 3] - X[:, 3].mean(0)) ** 2).sum(1)):
        bad.append("eucl")
    if not np.allclose(d_diag(Z)[:, 5], (((X[:, 5] - X[:, 5].mean(0)) ** 2) / X[:, 5].var(0)).sum(1), rtol=1e-6):
        bad.append("diag")
    from sklearn.covariance import LedoitWolf
    lw = LedoitWolf().fit(X[:, 2])
    loc = np.zeros((18, 16)); prec = np.tile(np.eye(16), (18, 1, 1)); loc[2], prec[2] = lw.location_, lw.precision_
    if not np.allclose(d_ref(Z, loc, prec)[:, 2], lw.mahalanobis(X[:, 2]), rtol=1e-8):
        bad.append("ref vs sklearn mahalanobis")
    # O6: K = 1 is the V5 distance exactly; on a two-mode world (70 % / 30 % of background, a few true outliers) the
    # mixture lowers the second mode's rank below the outliers, which one Gaussian does not
    X2 = np.concatenate([rng.normal(0, 1, (1400, 16)), rng.normal(6, 1.5, (600, 16)), rng.normal(0, 1, (20, 16)) + 
                         np.r_[np.full(8, 4.0), np.zeros(8)]])
    if not np.array_equal(mix_channel(X2, 1)[0], LedoitWolf().fit(X2).mahalanobis(X2)):
        bad.append("mix K=1 vs LedoitWolf")
    dm, inf = mix_channel(X2, "bic")
    d1 = LedoitWolf().fit(X2).mahalanobis(X2)
    def mode2_above_outliers(d):          # share of second-mode windows scored above the median outlier
        return float((d[1400:2000] > np.median(d[2000:])).mean())
    if not (inf["K_used"] >= 2 and mode2_above_outliers(dm) < mode2_above_outliers(d1)):
        bad.append(f"mix two-mode (K {inf['K_used']}, {mode2_above_outliers(dm):.3f} vs {mode2_above_outliers(d1):.3f})")
    Zc = rng.normal(0, 1, (10, 2, 3)); wfc = np.array([0] * 6 + [1] * 4)
    cz = ctx3(Zc, wfc)
    if not (np.allclose(cz[1], Zc[0:3].mean(0)) and np.allclose(cz[0], Zc[0:2].mean(0)) and np.allclose(cz[6], Zc[6:8].mean(0))
            and np.allclose(cz[5], Zc[4:6].mean(0))):
        bad.append("ctx3")
    lv = member_series(D, wf, (9,), "levspread")[0]
    if not np.isfinite(lv).all():
        bad.append("levspread finite")
    R1.gate(dict(gate="G-self", status="PASS" if not bad else "FAIL", bad=bad,
                 summary="member construction = e17b; distances by definition; O6 K=1 and two-mode; O7 context" if not bad else str(bad)))


# ============================================================================ pool jobs
def _job_meta(t, **kw):
    import resource
    return dict(kw, shas=code_shas(), s=round(time.time() - t, 1),
                peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))


def p1_job(a):
    """training patient: latents of the 4 seeds; every 10th clean window (thesis training mask) kept for the 4a
    reference."""
    case, = a
    t = time.time()
    try:
        PD.CKPT = REPO / "data" / "models_v2"
        z, _ = R1.load_case(case, "earlier")
        idx, adj, xn, f7 = model_inputs(z)
        clean = np.asarray(TGV2.mask(z, "clean"), bool)[idx]
        sel = np.flatnonzero(clean)[::10]
        d = SCR / "p1"
        d.mkdir(parents=True, exist_ok=True)
        out = {}
        for tag in TAGS:
            _, Zt = PD.run_model(tag, adj, xn, f7)
            out[tag] = Zt[sel].astype(np.float32)
        np.savez(d / f".{case}.npz", **out)
        (d / f".{case}.npz").replace(d / f"{case}.npz")
        return _job_meta(t, case=case, job="p1", n_sub=int(len(sel)))
    except Exception:                    # noqa: BLE001
        return dict(case=case, job="p1", error=traceback.format_exc()[-3000:])


def reference_fits(train_cases):
    """per seed, per channel: LedoitWolf on the pooled subsample of the training patients, once with all of them
    (for every other case) and once leaving each training patient out (for that patient)."""
    from sklearn.covariance import LedoitWolf
    t = time.time()
    sub = {c: np.load(SCR / "p1" / f"{c}.npz") for c in train_cases}
    fits, counts = {}, {}
    for tag in TAGS:
        for excl in [None] + list(train_cases):
            use = [c for c in train_cases if c != excl]
            if not use:
                continue
            X = np.concatenate([sub[c][tag] for c in use]).astype(np.float64)
            loc = np.empty((X.shape[1], X.shape[2])); prec = np.empty((X.shape[1], X.shape[2], X.shape[2]))
            for c in range(X.shape[1]):
                lw = LedoitWolf().fit(X[:, c, :])
                loc[c], prec[c] = lw.location_, lw.precision_
            key = f"{tag}|{excl or 'all'}"
            fits[key + "|loc"], fits[key + "|prec"] = loc, prec
            counts[key] = dict(patients=len(use), windows=int(len(X)), excluded=excl)
    np.savez(SCR / "ref_fits.npz", **fits)
    R1.phase("reference_fits", t)
    return counts


def prep_job(a):
    """one case: every variant's ensemble scalar x and budget signal m, 4 seeds (stored in SCR/xm/<case>.npz).
    Returns the seed-42 smoothed m of each variant (development cases, for k) and the G-D0 / G-enc checks."""
    case, src, want_smm, check_enc, variants = a
    t = time.time()
    try:
        PD.CKPT = REPO / "data" / "models_v2"
        ext = src == "ext"
        z, _ = R1.load_case(case, src)
        idx, adj, xn, f7 = model_inputs(z)
        ok = ~z["is_signal_loss"].astype(bool)
        fidx = z["file_idx"].astype(int)
        lite = dict(n=int(len(ok)), idx=idx, ok=ok, fidx=fidx)
        wf = fidx[idx]
        stored = np.load(R1.DSTORE / "r10" / f"{case}.npz")
        if not np.array_equal(stored["idx"], idx):
            raise SystemExit(f"{case}: window index differs from the stored r10 distances")
        fits = np.load(SCR / "ref_fits.npz") if any(VARIANTS[v]["dist"] == "ref" for v in variants) else None
        fkey = case if case in TRAIN else "all"
        gam = (PS._full(lite, np.asarray(z["zgamma_raw"], np.float64)[idx])
               if (not ext and "zgamma_raw" in getattr(z, "files", z)) else None)
        store, smm, d0_bad, enc_bad, na = {}, {}, [], None, []
        mixdiag, mix1_bad = [], None
        fl = np.asarray(z["is_flag5sd"]).astype(bool)[idx] if (not ext and "is_flag5sd" in getattr(z, "files", z)) else None
        bgm = (~np.asarray(z["is_ictal"]).astype(bool)[idx]) & (~np.asarray(z["is_buffer"]).astype(bool)[idx]) \
            if (fl is not None and "is_buffer" in getattr(z, "files", z)) else None
        flag_bg = (fl & bgm, (~fl) & bgm) if bgm is not None else None
        for tag in TAGS:
            rec, Z = PD.run_model(tag, adj, xn, f7)
            D0raw = d_maha(Z)
            Ds = {"maha": conv(D0raw, ext)}
            if not np.array_equal(Ds["maha"], np.asarray(stored[f"{tag}_d"], np.float64)):
                d0_bad.append(tag)
            need = {VARIANTS[v]["dist"] for v in variants} | {"enc_" + VARIANTS[v]["enc"] for v in variants}
            if "diag" in need:
                Ds["diag"] = conv(d_diag(Z), ext)
            if "eucl" in need:
                Ds["eucl"] = conv(d_eucl(Z), ext)
            if "ref" in need and f"{tag}|{fkey}|loc" in fits.files:
                Ds["ref"] = conv(d_ref(Z, fits[f"{tag}|{fkey}|loc"], fits[f"{tag}|{fkey}|prec"]), ext)
            if "base10" in need:
                Ds["base10"] = conv(E16.arm_distances("a", D0raw, Z, wf)[0], ext)
            if "base30" in need:
                Ds["base30"] = conv(E16.arm_distances("c", D0raw, Z, wf)[0], ext)
            if "enc_self" in need:
                Ds["self"] = conv(d_maha(encode(tag, adj, xn, f7, "self")), ext)
            if "enc_input" in need:
                Ds["input"] = conv(d_maha(node_x(tag, adj, xn, f7)), ext)
            if "enc_ctx3" in need:
                Ds["ctx3"] = conv(d_maha(ctx3(Z, wf)), ext)
            for mk, km in (("mixbic", "bic"), ("mix2", 2)):
                if mk in need:
                    Dm, inf = d_mix(Z, km, flags=flag_bg)
                    Ds[mk] = conv(Dm, ext)
                    mixdiag += [dict(r, case=case, seed=tag, variant=mk) for r in inf]
            if check_enc and tag == TAGS[0] and ({"mixbic", "mix2"} & need):
                d1, _ = d_mix(Z, 1)
                mix1_bad = float(np.abs(d1 - D0raw).max())
            if check_enc and tag == TAGS[0]:
                enc_bad = float(np.abs(encode(tag, adj, xn, f7, "own") - Z).max())
            recf = PS._full(lite, rec.astype(np.float64))
            for vid in variants:
                v = VARIANTS[vid]
                if v["enc"].startswith("arm"):              # retrained arms: own seeds, below
                    continue
                key = v["enc"] if v["enc"] in ("self", "input", "ctx3") else v["dist"]
                if key not in Ds or ("gamma" in v["extra"] and gam is None):
                    na.append(vid)
                    continue
                extra = [gam if e == "gamma" else recf for e in v["extra"]]
                x, m = scalar_and_m(lite, member_series(Ds[key], wf, v["members"], v["drift"]), extra)
                store[f"{vid}|{tag}|x"], store[f"{vid}|{tag}|m"] = x, m
                if want_smm and tag == "clean_seed42":
                    smm[vid] = PS.smoothed(lite, m, v["smooth"])
        arm_vids = [v for v in variants if VARIANTS[v]["enc"].startswith("arm")]
        smm_t = {}
        arm_seed_union = list(dict.fromkeys(t for v in arm_vids for t in seeds_of(v)))
        for tag in arm_seed_union:  # retrained arms: each arm's own seeds (EUR_ARM_SEEDS[_<ARM>]), not V0's four
            Ds = {}
            for enc in sorted({VARIANTS[v]["enc"] for v in arm_vids}):
                if tag not in arm_tags(enc[3:]):
                    continue
                if (arm_dir(enc[3:]) / f"gae_v2_{tag}.pt").exists():      # absent: a chunk skipped by the guard
                    Ds[enc] = conv(d_maha(encode(tag, adj, xn, f7, ckpt_dir=arm_dir(enc[3:]))), ext)
            for vid in arm_vids:
                v = VARIANTS[vid]
                if tag not in seeds_of(vid):
                    continue
                if v["enc"] not in Ds:
                    na.append(f"{vid}|{tag}")
                    continue
                x, m = scalar_and_m(lite, member_series(Ds[v["enc"]], wf, v["members"], v["drift"]), [])
                store[f"{vid}|{tag}|x"], store[f"{vid}|{tag}|m"] = x, m
                if want_smm:
                    sm = PS.smoothed(lite, m, v["smooth"])
                    if v["kmode"] == "seed":
                        smm_t.setdefault(vid, {})[tag] = sm
                    elif tag == "clean_seed42":
                        smm[vid] = sm
        if "O7" in variants:                 # O7 premise: lag-1 autocorrelation of the scalar within files (ok windows)
            for tag in TAGS:
                for vid in ("V0", "O7"):
                    k = f"{vid}|{tag}|x"
                    if k in store:
                        x = np.asarray(store[k], np.float64)
                        same = (fidx[1:] == fidx[:-1]) & ok[1:] & ok[:-1]
                        a_, b_ = x[:-1][same], x[1:][same]
                        mixdiag.append(dict(case=case, seed=tag, variant=vid, lag1=float(np.corrcoef(a_, b_)[0, 1])
                                            if len(a_) > 2 else np.nan))
        d = SCR / "xm"
        d.mkdir(parents=True, exist_ok=True)
        np.savez(d / f".{case}.npz", **store)
        (d / f".{case}.npz").replace(d / f"{case}.npz")
        return _job_meta(t, case=case, src=src, job="prep", smm=smm, smm_t=smm_t, d0_bad=d0_bad, enc_maxabs=enc_bad,
                         na=sorted(set(na)), hours=float(len(ok) * PS.WIN / 3600), mixdiag=mixdiag, mix1=mix1_bad)
    except SystemExit as e:
        return dict(case=case, src=src, job="prep", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="prep", error=traceback.format_exc()[-3000:])


def score_job(a):
    """one case: run_budget_s for every variant x seed x arm (+ the detector curve); for V0 also p3c_freeze.run_budget
    and the scalar / budget-signal identity with the record functions (G-eng, G-x0)."""
    case, src, ks, set_name, variants = a
    t = time.time()
    try:
        ctx, _ = R1.ctx_from_store(case, src, "r10")
        xm = np.load(SCR / "xm" / f"{case}.npz")
        rows, errs, curve, x0_bad, eng_bad = [], [], [], [], []
        for vid in variants:
            for tag in seeds_of(vid):
                if f"{vid}|{tag}|x" not in xm.files:
                    continue
                v = VARIANTS[vid]
                x, m = xm[f"{vid}|{tag}|x"], xm[f"{vid}|{tag}|m"]
                kv = ks[vid][tag] if isinstance(ks[vid], dict) else ks[vid]
                q = P3L.q_of(PS.smoothed(ctx, m, v["smooth"]), kv)
                r_, e_ = [], []
                for arm, (fl, cp) in ARMS.items():
                    run_budget_s(ctx, case, tag, x, q, fl, cp, arm, r_, e_, v["smooth"])
                rows += [dict(r, variant=vid, set=set_name, q_raw=q, k=kv) for r in r_]
                errs += [dict(e, variant=vid, set=set_name) for e in e_]
                sm = PS.smoothed(ctx, x, v["smooth"])
                for top in CURVE_TOPS:
                    det = PS.d1_events(ctx, x, v["smooth"], top)
                    tp, fp, nr, h = PS.score(ctx, det)
                    curve.append(dict(subject=case, seed=tag, variant=vid, set=set_name, top=top, tp=tp, fp=fp,
                                      n_ref=nr, nonict_h=h))
                del sm
                if vid == "V0":
                    if not (np.array_equal(x, E22.final_scalar(ctx, tag)) and
                            np.array_equal(m, P3L.member_mean_z(ctx, tag))):
                        x0_bad.append(tag)
                    rr, ee = [], []
                    for arm, rec_arm in (("own", "L2f"), ("fixed", "frozen")):
                        fl, cp = R1.ARMS[rec_arm]
                        P3C.run_budget(ctx, case, tag, x, q, fl, cp, arm, rr, ee)
                    if not (pd.DataFrame(rr).equals(pd.DataFrame(r_)) and pd.DataFrame(ee).equals(pd.DataFrame(e_))):
                        eng_bad.append(tag)
        return _job_meta(t, case=case, src=src, job="score", rows=rows, errs=errs, curve=curve, x0_bad=x0_bad,
                         eng_bad=eng_bad)
    except SystemExit as e:
        return dict(case=case, src=src, job="score", error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, job="score", error=traceback.format_exc()[-3000:])


def _run(fn, specs, workers, what):
    out = []
    if not specs:
        return out
    if workers <= 1:
        R1._init_worker(R1._env())
        it = map(fn, specs)
        pool = None
    else:
        pool = R1._pool(min(workers, len(specs)))
        it = pool.imap_unordered(fn, specs)
    try:
        for r in it:
            if r.get("error"):
                raise SystemExit(f"{what} {r['case']}: {r['error']}")
            out.append(r)
            log(f"{what} {r['case']} done ({r['s']} s)")
    finally:
        if pool is not None:
            pool.terminate()
    return out


def _size(case, src):
    p = R1.VIEWS / src / (f"{case}_lf.npz" if src == "ext" else f"{case}.npz")
    return p.stat().st_size


def set_of(case, src):
    return "external" if src == "ext" else ("development" if case in DEV else "test")


# ============================================================================ phases
def variant_pass(cases_src, workers, ks=None, check_enc=(), label="full"):
    """prep (x, m per variant), k per variant, scoring. ks given (smoke) -> no calibration."""
    variants = selected()
    t = time.time()
    specs = sorted([(c, s, c in DEV, c in check_enc, variants) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    prep = _run(prep_job, specs, workers, f"prep[{label}]")
    R1.phase(f"prep_{label}", t)
    d0_bad = {r["case"]: r["d0_bad"] for r in prep if r["d0_bad"]}
    R1.gate(dict(gate=f"G-D0[{label}]", status="PASS" if not d0_bad else "FAIL", bad=d0_bad,
                 summary=f"V0 distances = stored r10 distances in {len(prep)} cases x {len(TAGS)} seeds" if not d0_bad
                 else str(d0_bad)))
    enc = {r["case"]: r["enc_maxabs"] for r in prep if r["enc_maxabs"] is not None}
    mix1 = {r["case"]: r["mix1"] for r in prep if r.get("mix1") is not None}
    if check_enc and {"mixbic", "mix2"} & {VARIANTS[v]["dist"] for v in variants}:
        R1.gate(dict(gate=f"G-mix1[{label}]", status="PASS" if mix1 and max(mix1.values()) == 0.0 else "FAIL",
                     max_abs=mix1, summary=f"mixture distance with K = 1 = the V5 distance: max |dD| {mix1}"))
    md = [r for x in prep for r in x.get("mixdiag", [])]
    if md:
        pd.DataFrame(md).to_csv(R1.out_dir() / "mix_diag.csv", index=False)
    if check_enc:
        R1.gate(dict(gate=f"G-enc[{label}]", status="PASS" if enc and max(enc.values()) == 0.0 else "FAIL", max_abs=enc,
                     summary=f"8a encoder with the window graph = run_model: max |dZ| {enc}"))
    if ks is None:
        ks = {}
        for vid in variants:
            if VARIANTS[vid]["kmode"] == "seed":              # R0s: one k per seed, on that seed's own scores
                ks[vid] = {}
                for tag in seeds_of(vid):
                    sm = [r["smm_t"][vid][tag] for r in prep if r["case"] in DEV and tag in r.get("smm_t", {}).get(vid, {})]
                    if len(sm) == len(DEV):
                        ks[vid][tag] = float(P3L.calibrate(sm))
                continue
            sm = [r["smm"][vid] for r in prep if r["case"] in DEV and vid in r["smm"]]
            ks[vid] = float(P3L.calibrate(sm)) if len(sm) == len(DEV) else float("nan")
        rel = abs(ks["V0"] - K_RECORD) / abs(K_RECORD)
        R1.gate(dict(gate="G-kv0", status="PASS" if rel <= R1.TOL["k_rel"] else "FAIL", k=ks["V0"], k_record=K_RECORD,
                     rel=rel, summary=f"V0 k {ks['V0']:.9f} vs record {K_RECORD:.9f} (relative {rel:.1e})"))
    krows = []
    for v, k in ks.items():
        if isinstance(k, dict):
            krows += [dict(variant=v, k=kk, text=VARIANTS[v]["text"], seed=t) for t, kk in k.items()]
        else:
            krows.append(dict(variant=v, k=k, text=VARIANTS[v]["text"]))
    kd = pd.DataFrame(krows)
    if "seed" in kd and kd["seed"].isna().all():
        kd = kd.drop(columns="seed")
    kd.to_csv(R1.out_dir() / "k.csv", index=False)
    t = time.time()
    specs = sorted([(c, s, ks, set_of(c, s), variants) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    sc = _run(score_job, specs, workers, f"score[{label}]")
    R1.phase(f"score_{label}", t)
    x0 = {r["case"]: r["x0_bad"] for r in sc if r["x0_bad"]}
    eng = {r["case"]: r["eng_bad"] for r in sc if r["eng_bad"]}
    R1.gate(dict(gate=f"G-x0[{label}]", status="PASS" if not x0 else "FAIL", bad=x0,
                 summary="V0 scalar and budget signal = the record functions" if not x0 else str(x0)))
    R1.gate(dict(gate=f"G-eng[{label}]", status="PASS" if not eng else "FAIL", bad=eng,
                 summary="run_budget_s = p3c_freeze.run_budget for V0 (own = L2f, fixed = frozen)" if not eng else str(eng)))
    want = code_shas()
    wbad = sorted({r["case"] for r in prep + sc if r["shas"] != want})
    R1.gate(dict(gate=f"G-worker[{label}]", status="PASS" if not wbad else "FAIL", bad=wbad, want=want,
                 summary=f"{len(prep) + len(sc)} jobs ran eur_abl {want['eur_abl']}, r2_r1 {want['r2_r1']}"))
    na = {r["case"]: r["na"] for r in prep if r["na"]}
    jobs = pd.DataFrame([dict(case=r["case"], job=r["job"], s=r["s"], peak_rss_mb=r["peak_rss_mb"],
                              hours=r.get("hours")) for r in prep + sc])
    return prep, sc, ks, na, jobs


def write_outputs(sc, label):
    o = R1.out_dir()
    pd.DataFrame([r for x in sc for r in x["rows"]]).to_csv(o / f"per_subject{label}.csv", index=False)
    pd.DataFrame([r for x in sc for r in x["errs"]]).to_csv(o / f"errors{label}.csv", index=False)
    pd.DataFrame([r for x in sc for r in x["curve"]]).to_csv(o / f"curve{label}.csv", index=False)


# ============================================================================ PC1: retraining (D32-F)
def arm_dir(arm):
    return R1.WORK / "eureka" / os.environ.get("EUR_TAG", "abl") / "models" / arm


def _pc1_meta():
    """V5's checkpoint constants (equal for the 4 seeds; gate G-pc1const) and training-window counts."""
    m = json.loads((REPO / "data" / "models_v2" / "gae_v2_clean_seed42.json").read_text())
    return dict(add_mean=m["add_mean"], add_std=m["add_std"], clip=m["clip"]), m["n_train"], m.get("n_val")


def _loss_m(model, A, X, T):
    """f1_core._loss('gae') with the input / target widths of the arm."""
    import torch
    import gae_joint as G
    B = A.shape[0]
    b_, r_, c_ = A.nonzero(as_tuple=True)
    ei = torch.stack([b_ * G.N_CH + r_, b_ * G.N_CH + c_])
    z = model.encoder(X.reshape(B * G.N_CH, X.shape[2]), ei, A[b_, r_, c_])
    zp = z.view(B, G.N_CH, G.LATENT_DIM)
    Ah = torch.clamp(torch.bmm(zp, zp.transpose(1, 2)), 0.0, 1.0)
    Xh = model.x_decoder(z).view(B, G.N_CH, T.shape[2])
    return ((A - Ah) ** 2).mean(dim=(1, 2)) + G.LAMBDA * ((T - Xh) ** 2).mean(dim=(1, 2))


def train_masked(cases, meta, seed, keep_in, keep_out, epochs, max_windows=None, tag=""):
    """f1_core.train('gae') (the thesis recipe; window order of torch's DataLoader) on the kept columns. With every column
    kept no indexing is done, so it is f1_core.train exactly (gate G-pc1vec)."""
    import torch
    import f1_core as F
    import gae_joint as G
    import model_cmp_core as C
    t_load = time.time()
    A, X, T = C._mlp_tensors(sorted(cases), meta, torch.device("cpu"), C.clean_mask, max_windows)
    if not (len(keep_in) == F.IN_DIM and len(keep_out) == F.OUT_X):
        X = X[:, :, torch.tensor(keep_in)].contiguous()
        T = T[:, :, torch.tensor(keep_out)].contiguous()
    n = len(A)
    t_load = time.time() - t_load
    torch.manual_seed(seed); np.random.seed(seed)
    g = torch.Generator().manual_seed(seed)
    model = G.GAEModel(in_dim=len(keep_in), bands=len(keep_out))
    n_params = sum(q.numel() for q in model.parameters())
    opt = torch.optim.Adam(model.parameters(), lr=F.LR)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=epochs)
    rows, t0 = [], time.time()
    for ep in range(epochs):
        model.train()
        tot = torch.zeros(())
        torch.empty((), dtype=torch.int64).random_(generator=g)
        perm = torch.randperm(n, generator=g)
        torch.randperm(n, generator=g)
        for i in range(0, n, F.BATCH):
            ii = perm[i:i + F.BATCH]
            opt.zero_grad()
            loss = _loss_m(model, A[ii], X[ii], T[ii]).mean()
            loss.backward(); opt.step()
            tot += loss.detach() * len(ii)
        sched.step()
        rows.append(dict(epoch=ep + 1, train_loss=float(tot) / n, s=round(time.time() - t0, 1)))
        if ep < 2 or (ep + 1) % 20 == 0 or ep == epochs - 1:
            log(f"[pc1{tag}] epoch {ep+1}/{epochs} loss {rows[-1]['train_loss']:.6f} ({rows[-1]['s']}s)")
    steps = epochs * ((n + F.BATCH - 1) // F.BATCH)
    info = dict(n_train=int(n), epochs=epochs, seed=int(seed), n_params=int(n_params), first_loss=rows[0]["train_loss"],
                last_loss=rows[-1]["train_loss"], fit_s=round(time.time() - t0, 1), load_s=round(t_load, 1),
                ms_per_step=round((time.time() - t0) / steps * 1000, 3),
                G2="PASS" if rows[-1]["train_loss"] < rows[0]["train_loss"] else "FAIL")
    return model.eval(), info, rows


def train_arm_job(a):
    """one arm x one seed: train_masked on the 12 training patients' clean windows of the record data, V5's constants;
    validation loss on the 3 validation patients; checkpoint + json (+ kept columns) and _DONE.json last."""
    arm, tag, epochs = a
    t0 = time.time()
    try:
        import resource
        import torch
        import model_cmp_core as C
        out = arm_dir(arm)
        done = out / f"gae_v2_{tag}_DONE.json"
        if done.exists() and json.loads(done.read_text()).get("eur_abl_sha") == CODE_SHA:
            return dict(case=f"{arm}/{tag}", s=0.0, reused=True)
        R1.point_npz(TRAIN + VAL, "earlier")
        meta, n_exp, n_val = _pc1_meta()
        seed = int(tag.split("seed")[-1])
        ki, ko = PC1_ARMS[arm]
        model, info, rows = train_masked(TRAIN, meta, seed, ki, ko, epochs, tag=f" {arm} {tag}")
        if info["n_train"] != sum(n_exp.values()):
            raise SystemExit(f"training windows {info['n_train']} != V5's {sum(n_exp.values())}")
        if info["G2"] != "PASS":
            raise SystemExit("G2: last-epoch loss not below the first")
        vl, nv = 0.0, {}
        with torch.no_grad():
            for s in VAL:
                A, X, T = C._mlp_tensors([s], meta, torch.device("cpu"), C.clean_mask)
                X = X[:, :, torch.tensor(ki)]; T = T[:, :, torch.tensor(ko)]
                nv[s] = int(len(A))
                for i in range(0, len(A), 512):
                    vl += float(_loss_m(model, A[i:i + 512], X[i:i + 512], T[i:i + 512]).sum())
        if n_val and nv != {s: int(n_val[s]) for s in VAL}:
            raise SystemExit(f"validation windows {nv} != V5's {n_val}")
        out.mkdir(parents=True, exist_ok=True)
        torch.save({k: v.cpu() for k, v in model.state_dict().items()}, out / f"gae_v2_{tag}.pt")
        m = dict(arm=arm, in_dim=len(ki), out_x=len(ko), keep_in=ki, keep_out=ko, clip=meta["clip"],
                 add_mean=meta["add_mean"], add_std=meta["add_std"], n_val=nv, final_val=vl / max(1, sum(nv.values())),
                 loop="eur_abl.train_masked (= f1_core.train with every column; gate G-pc1vec)", eur_abl_sha=CODE_SHA,
                 torch=torch.__version__, threads=torch.get_num_threads(), **info)
        (out / f"gae_v2_{tag}.json").write_text(json.dumps(m, indent=1))
        pd.DataFrame(rows).assign(arm=arm, seed=seed).to_csv(out / f"training_log_{tag}.csv", index=False)
        peak = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        done.write_text(json.dumps(dict(arm=arm, tag=tag, seconds=round(time.time() - t0), peak_rss_mb=peak,
                                        eur_abl_sha=CODE_SHA, n_train=info["n_train"], n_params=info["n_params"],
                                        ms_per_step=info["ms_per_step"]), indent=1))
        return dict(case=f"{arm}/{tag}", s=round(time.time() - t0, 1))
    except SystemExit as e:
        return dict(case=f"{arm}/{tag}", s=round(time.time() - t0, 1), error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        import traceback
        return dict(case=f"{arm}/{tag}", s=round(time.time() - t0, 1), error=traceback.format_exc()[-3000:])


def pc1_prepare(arms, workers):
    """gates G-pc1const (V5's constants = the recipe's own constants on the record data) and G-pc1vec (train_masked
    with every column = f1_core.train, 2,000 windows, 2 epochs, exactly; each arm runs 2 epochs), then the trainings
    (arms x 4 seeds, in parallel)."""
    import torch
    import f1_core as F
    t = time.time()
    meta, _, _ = _pc1_meta()
    mu, sd = R1.TGV2.norm_constants(R1.VIEWS / "earlier", "clean")
    rel = 0.0
    for got, key in ((mu, "add_mean"), (sd, "add_std")):
        want = np.asarray(meta[key])
        rel = max(rel, float(np.max(np.abs(got - want) / np.maximum(np.abs(want), 1e-12))))
    R1.gate(dict(gate="G-pc1const", status="PASS" if rel <= R1.TOL["const_rel"] else "FAIL", max_rel=rel,
                 summary=f"V5 constants = norm_constants on the record training windows (relative {rel:.1e})"))
    R1.point_npz(TRAIN + VAL, "earlier")
    ref, _, _ = F.train("gae", TRAIN[:1], meta, 42, torch.device("cpu"), epochs=2, max_windows=2000, tag=" G-pc1vec")
    mine, info, _ = train_masked(TRAIN[:1], meta, 42, *PC1_ARMS["R0"], 2, max_windows=2000, tag=" G-pc1vec")
    d = F._maxdiff(ref, mine)
    smoke = {}
    for a_ in arms:
        _, inf, _ = train_masked(TRAIN[:1], meta, 42, *PC1_ARMS[a_], 2, max_windows=2000, tag=f" smoke {a_}")
        smoke[a_] = dict(n_params=inf["n_params"], G2=inf["G2"], ms_per_step=inf["ms_per_step"])
    ok = d == 0.0 and all(v["G2"] == "PASS" for v in smoke.values())
    R1.gate(dict(gate="G-pc1vec", status="PASS" if ok else "FAIL", max_abs_diff=d, arms=smoke,
                 summary=f"train_masked (every column) = f1_core.train: max |weight diff| {d:.1e}; arms 2 epochs {smoke}"))
    if any(a_ in PC8_DROP for a_ in arms):
        pc8_columns(arms)
    R1.phase("pc1_gates", t)
    reused = pc7_reuse(arms) if any(reuse_tags(a_) for a_ in arms) else []
    if pc7_ref() is not None:
        pc7_platform_checks(meta)
    t = time.time()
    epochs = int(os.environ.get("EUR_PC1_EPOCHS", PC1_EPOCHS)) if os.environ.get("R2_TEST") else PC1_EPOCHS
    specs = [(a_, tg, epochs) for a_ in arms for tg in arm_tags(a_) if (a_, tg) not in reused]
    res = train_chunks(specs, workers)
    R1.phase("pc1_training", t)
    R1._jdump(R1.WORK / "eureka" / os.environ.get("EUR_TAG", "abl") / "pc1_training.json", res)


def pc8_columns(arms):
    """G-pc8cols (PC8): each PC8 arm drops exactly the named columns of design §2 from the node input and the matching
    ones from the reconstruction target; each arm runs with seed 42 among its seeds (k is calibrated on seed 42)."""
    bad = {}
    for a_ in arms:
        if a_ not in PC8_DROP:
            continue
        ki, ko = PC1_ARMS[a_]
        drop_in = {IN_NAMES[i] for i in range(30) if i not in ki}
        drop_out = {OUT_NAMES[i] for i in range(12) if i not in ko}
        want_out = PC8_DROP[a_] & set(OUT_NAMES)
        if drop_in != PC8_DROP[a_] or drop_out != want_out or ki != sorted(ki) or ko != sorted(ko):
            bad[a_] = dict(drop_in=sorted(drop_in), drop_out=sorted(drop_out))
        if "clean_seed42" not in arm_tags(a_):
            bad[f"{a_}/seeds"] = arm_tags(a_)
    R1.gate(dict(gate="G-pc8cols", status="PASS" if not bad else "FAIL", bad=bad,
                 arms={a_: dict(keep_in=[IN_NAMES[i] for i in PC1_ARMS[a_][0]], keep_out=[OUT_NAMES[i] for i in PC1_ARMS[a_][1]],
                                seeds=arm_tags(a_)) for a_ in arms if a_ in PC8_DROP},
                 summary="PC8 arms drop exactly the design's columns; seed 42 in every arm" if not bad else str(bad)))


def cpu_model():
    """the CPU model of the machine (first 'model name' of /proc/cpuinfo) and the distinct models; Track F standard from
    PC8 (plan §0, board R224)."""
    try:
        names = [ln.split(":", 1)[1].strip() for ln in Path("/proc/cpuinfo").read_text().splitlines()
                 if ln.lower().startswith("model name")]
    except OSError:
        names = []
    return dict(cpu_model=names[0] if names else platform.processor() or "unknown", cpu_models=sorted(set(names)),
                cpu_logical=len(names) or os.cpu_count())


def train_chunks(specs, workers):
    """trainings in chunks of `workers` (4 in parallel on Kaggle); a further chunk starts only if the time so far + the
    last chunk's duration + PC7_RESERVE_S stays within PC7_GUARD_H (gate G-guard records it). Without EUR_PC7_REF every
    chunk runs (PC1 behaviour: one pool over all specs)."""
    if pc7_ref() is None:
        return _run(train_arm_job, specs, workers, "pc1 training")
    guard_h = float(os.environ.get("EUR_TEST_GUARD_H", PC7_GUARD_H)) if os.environ.get("R2_TEST") else PC7_GUARD_H
    res, skipped, chunks = [], [], []
    for i in range(0, len(specs), max(1, workers)):
        ch = specs[i:i + max(1, workers)]
        el = time.time() - R1.T0
        if chunks and el + chunks[-1]["s"] + PC7_RESERVE_S > guard_h * 3600:
            skipped += [f"{a}/{t}" for a, t, _ in specs[i:]]
            break
        t = time.time()
        res += _run(train_arm_job, ch, workers, "pc1 training")
        chunks.append(dict(seeds=[f"{a}/{tg}" for a, tg, _ in ch], s=round(time.time() - t, 1),
                           elapsed_h=round((time.time() - R1.T0) / 3600, 3)))
    R1.gate(dict(gate="G-guard", status="PASS", chunks=chunks, skipped=skipped, guard_h=guard_h, reserve_s=PC7_RESERVE_S,
                 summary=f"{sum(len(c['seeds']) for c in chunks)} trained in {len(chunks)} chunk(s); skipped {skipped}"))
    return res


def pc7_reuse(arms):
    """copies the committed checkpoints of the reused seeds from EUR_PC7_REF/models/<arm>/ into this run (G-pc7reuse)."""
    import shutil
    ref, rows, bad, done = pc7_ref(), [], [], []
    ep_want = int(os.environ.get("EUR_PC1_EPOCHS", PC1_EPOCHS)) if os.environ.get("R2_TEST") else PC1_EPOCHS
    for a_ in arms:
        if not reuse_tags(a_):
            continue
        out = arm_dir(a_)
        out.mkdir(parents=True, exist_ok=True)
        for tg in reuse_tags(a_):
            src = ref / "models" / a_
            for f in REUSE_FILES:
                p = src / f.format(t=tg)
                if not p.exists():
                    bad.append(f"missing {p}")
                    continue
                shutil.copyfile(p, out / p.name)
                rows.append(dict(arm=a_, seed=tg, file=p.name, sha256=hashlib.sha256(p.read_bytes()).hexdigest()))
            js = out / f"gae_v2_{tg}.json"
            if js.exists():
                m = json.loads(js.read_text())
                ki, ko = PC1_ARMS[a_]
                if not (m.get("keep_in") == ki and m.get("keep_out") == ko and m.get("epochs") == ep_want
                        and m.get("G2") == "PASS"):
                    bad.append(f"{a_}/{tg}: json columns / epochs / G2 differ")
            done.append((a_, tg))
    pd.DataFrame(rows).to_csv(R1.out_dir() / "reused_checkpoints.csv", index=False)
    R1.gate(dict(gate="G-pc7reuse", status="PASS" if not bad else "FAIL", bad=bad, reused=[f"{a}/{t}" for a, t in done],
                 summary=f"{len(done)} checkpoints copied from {ref.relative_to(REPO)}; sha256 in reused_checkpoints.csv"
                 if not bad else str(bad)))
    return done


def note(rec):
    """a recorded check that does not stop the run (G-pc7plat, G-pc7rep): status PASS or DIFF."""
    STATE["gates"].append(rec)
    R1._jdump(R1.out_dir() / "gates.json", STATE["gates"])
    log(f"{rec['gate']}: {rec['status']} ({rec.get('summary')})")


def pc7_platform_checks(meta):
    """G-pc7plat (library versions = the reference run) and G-pc7rep (R0 seed 42 retrained for 1 epoch on the full
    training data: epoch-1 loss = the reference training log exactly). Recorded, no stop (pooling rule of the design)."""
    ref = pc7_ref()
    want = json.loads((ref / "run_meta.json").read_text()).get("versions", {})
    got = json.loads((R1.out_dir() / "run_meta.json").read_text()).get("versions", {})
    keys = ("python", "numpy", "scipy", "sklearn", "pandas", "torch", "torch_geometric")
    diff = {k: (got.get(k), want.get(k)) for k in keys if got.get(k) != want.get(k)}
    note(dict(gate="G-pc7plat", status="PASS" if not diff else "DIFF", diff=diff, stops=False,
              summary="library versions = the reference run" if not diff else f"differ: {diff}"))
    log_f = ref / "models" / "R0" / "training_log_clean_seed42.csv"
    want_l = float(pd.read_csv(log_f, float_precision="round_trip").query("epoch == 1").train_loss.iloc[0])  # exact digits
    _, info, rows = train_masked(TRAIN, meta, 42, *PC1_ARMS["R0"], 1, tag=" G-pc7rep")
    got_l = float(rows[0]["train_loss"])
    note(dict(gate="G-pc7rep", status="PASS" if got_l == want_l else "DIFF", got=repr(got_l), want=repr(want_l),
              stops=False, s=info["fit_s"], summary=f"epoch-1 loss {got_l!r} vs reference {want_l!r}"))


def pc7_final_gates(ks):
    """G-pc7k (R0's k = the reference k) and G-pc7r0 (the reused seeds' R0 rows = the reference rows), after the run."""
    ref = pc7_ref()
    kr = pd.read_csv(ref / "k.csv")
    want = float(kr[kr.variant == "R0"].k.iloc[0])
    rel = abs(ks["R0"] - want) / abs(want)
    R1.gate(dict(gate="G-pc7k", status="PASS" if rel <= R1.TOL["k_rel"] else "FAIL", k=ks["R0"], k_ref=want, rel=rel,
                 summary=f"R0 k {ks['R0']:.9f} vs reference {want:.9f} (relative {rel:.1e})"))
    bad = {}
    seeds = set(reuse_tags("R0"))
    for f in ("per_subject.csv", "errors.csv"):
        a = pd.read_csv(R1.out_dir() / f)
        b = pd.read_csv(ref / f)
        a = a[(a.variant == "R0") & a.seed.isin(seeds)]
        b = b[(b.variant == "R0") & b.seed.isin(seeds)]
        ca = a.sort_values(list(a.columns), kind="mergesort").reset_index(drop=True)
        cb = b[list(a.columns)].sort_values(list(a.columns), kind="mergesort").reset_index(drop=True)
        if len(a) == 0 or not ca.equals(cb):
            bad[f] = dict(rows=len(a), ref_rows=len(b))
    R1.gate(dict(gate="G-pc7r0", status="PASS" if not bad else "FAIL", bad=bad,
                 summary=f"R0 rows of {sorted(seeds)} = the reference rows (per_subject, errors)" if not bad else str(bad)))


def main(notebook="EUR_ABL", repo_commit="local", workers=None, smoke_only=False):
    R1.OUT_ROOT = R1.WORK / "eureka"
    workers = int(workers or os.environ.get("EUR_WORKERS") or R1.n_workers())
    tag = os.environ.get("EUR_TAG", "abl")
    sel = selected()
    need_ref = any(VARIANTS[v]["dist"] == "ref" for v in sel)
    meta = R1.run_meta(tag, notebook, repo_commit)
    meta.update(eur_abl_sha=CODE_SHA, code_shas=code_shas(), variants={v: VARIANTS[v] for v in sel}, workers=workers,
                arm_seeds=arm_tags(), arm_reuse=reuse_tags(), pc7_ref=os.environ.get("EUR_PC7_REF", ""),
                arm_seeds_by_arm={a_: arm_tags(a_) for a_ in PC1_ARMS}, arm_reuse_by_arm={a_: reuse_tags(a_) for a_ in PC1_ARMS},
                **cpu_model())
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    self_checks()
    src = build_views(DEV, TEST, EXT)
    gate_data(src)
    arms = list(dict.fromkeys(VARIANTS[v]["enc"][3:] for v in sel if VARIANTS[v]["enc"].startswith("arm")))  # R0s = R0
    if arms:
        pc1_prepare(arms, workers)
    # ---- SMOKE (the small check before the full run): chb01 + chb03 (+ first external case), measured
    t = time.time()
    s_dev, s_test, s_ext = [DEV[0]], [TEST[0]], EXT[:1]
    STATE["tag"] = f"{tag}/smoke"
    R1.r10(s_dev, s_test, s_ext, workers=min(workers, 3), with_k=False)
    if need_ref:
        p1 = _run(p1_job, [(c,) for c in s_dev], 1, "p1[smoke]")
        reference_fits(s_dev)
    cs = [(c, "earlier") for c in s_dev + s_test] + [(c, "ext") for c in s_ext]
    prep, sc, _, na, jobs = variant_pass(cs, min(workers, 3), ks={v: K_RECORD for v in sel},
                                         check_enc=set(s_dev + s_test + s_ext), label="smoke")
    write_outputs(sc, "")
    jobs.to_csv(R1.out_dir() / "jobs.csv", index=False)
    smoke_s = time.time() - t
    h_smoke = sum(r["hours"] for r in prep)
    h_all = sum(float(np.load(R1.VIEWS / ("ext" if c in EXT else "earlier") / (f"{c}_lf.npz" if c in EXT else f"{c}.npz"),
                              allow_pickle=True)["is_ictal"].shape[0]) * PS.WIN / 3600 for c in DEV + TEST + EXT)
    proj = dict(smoke_s=round(smoke_s, 1), smoke_eeg_h=round(h_smoke, 2), all_eeg_h=round(h_all, 1), workers=workers,
                note="computed: smoke seconds x (all hours / smoke hours) / workers x 1.3 (training-patient pass 1)",
                projected_h=round(smoke_s * (h_all / max(h_smoke, 1e-9)) / max(workers, 1) * 1.3 / 3600, 2),
                not_available=na)
    STATE["tag"] = tag
    R1._jdump(R1.out_dir() / "projection.json", proj)
    R1.gate(dict(gate="SMOKE", status="PASS" if proj["projected_h"] <= REFUSE_H else "FAIL", **proj,
                 summary=f"smoke {smoke_s:.0f} s on {h_smoke:.1f} h of EEG; full run projected {proj['projected_h']} h"))
    if smoke_only:
        return
    # ---- FULL
    t = time.time()
    R1.r10(DEV, TEST, EXT, workers=workers, with_k=True)
    R1.phase("r10_full", t)
    t = time.time()
    if need_ref:
        p1 = _run(p1_job, [(c,) for c in TRAIN], workers, "p1")
        counts = reference_fits(TRAIN)
        R1._jdump(R1.out_dir() / "reference_fits.json", counts)
        R1.phase("p1", t)
    cs = [(c, "earlier") for c in DEV + TEST] + [(c, "ext") for c in EXT]
    prep, sc, ks, na, jobs = variant_pass(cs, workers, check_enc={DEV[0], TEST[0], EXT[0]} if EXT else {DEV[0], TEST[0]})
    write_outputs(sc, "")
    if pc7_ref() is not None:
        pc7_final_gates(ks)
    jobs.to_csv(R1.out_dir() / "jobs.csv", index=False)
    R1._jdump(R1.out_dir() / "not_available.json", na)
    R1.finish_meta(dict(ks=ks))
    (R1.out_dir() / "SUMMARY.md").write_text(
        f"# EUR_ABL run ({notebook}, commit {repo_commit})\n\nEvery gate PASS (gates.json). Variants: "
        f"{', '.join(sel)}. Rows: per_subject.csv; errors.csv; curve.csv; k.csv. Not available: {na}.\n"
        "No reading here: src/eur_abl_aggregate.py makes the tables (committed before this run).\n")
    log("EUR_ABL done")


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--workers", type=int)
    ap.add_argument("--smoke-only", action="store_true")
    a = ap.parse_args()
    main(workers=a.workers, smoke_only=a.smoke_only)
