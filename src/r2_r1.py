#!/usr/bin/env python
"""
r2_r1.py -- independent research track, stage R1: the thesis system (P3 frozen design) on complete data
(docs/FUTURE_RESEARCH_PLAN.md rev 2, §5, §9, §12 rows from 07/11 D15-F). Kaggle CPU. Written before any R1 result.

Frozen and closed modules are imported READ ONLY and called unchanged; this file only points their path globals at
symlink views of the attached inputs (inside each worker process), builds the window bookkeeping, and compares outputs
with the committed record. r2_core.py (stage R0, sha 902d15ad) is imported unchanged for its helpers.

Record code called verbatim (never re-implemented):
  retrain/train_gae_v2.py      norm_constants (f7 constants), mask, main (G-vec reference: its own --smoke = 2,000 real
                               windows of chb01, 2 epochs), sanity_auroc (validation sanity AUROC after training)
  f1_core.train / _loss        tensor training loop (bit-equal to the PyG DataLoader loop: gate G-vec, plan §2)
  x1_external.model_outputs    node latent of the 4 checkpoints (p2_dump_seeds23.run_model: PyG per-window batches) +
                               per-channel LedoitWolf distance D; .make_ctx and .evaluate_ctx (external path)
  p3c_freeze.run_budget        one budget arm: D1 detector, CPD and hybrid (L6) localizers, SzCORE counts, errors
  e23_test_look7.evaluate      the test path of look #7 (and look #6 with floor = cap = 0.005)
  e22_test_oneshot.final_scalar, p3_levers.member_mean_z / q_of / calibrate, p2_scalars.smoothed

Two conventions of the record are kept per set (plan §12, 07/11 D15-F):
  CHB-MIT (development, test): D stored as float32 and read back as float64 (the dumps e14 / p2_seeds / p2_test);
  window bookkeeping = the fields of e22_test_oneshot.test_context (= p2_scalars.subject_context for the chain).
  External (chb24, Siena): x1_external.model_outputs (float64 D) and x1_external.make_ctx, unchanged.

Stages (plan §5):
  G-data   the attached feature datasets are R0's outputs: every file present; sha256 recorded (data_sha256.csv);
           stats.json = the committed R0 statistics (22 gap-free cases) / the R0 diff report (chb11, chb21); flags and
           file_idx = the earlier .npz (22 cases) / window, ictal, clean and 5 SD counts = the R0 diff report (chb11,
           chb21); external windows / ictal / signal-loss counts = results/r2/r0_data/ext/external_cases.csv; R0's
           G-feat (r2_core.compare_features, chain scope) re-read on the cases a notebook reads.
  G-const  train_gae_v2.norm_constants on the earlier training windows = the committed checkpoints' constants
           (relative 1e-9); G-count: clean training / validation window counts = the committed metas, exactly.
  R1.0     committed checkpoints data/models_v2/gae_v2_clean_seed{42,1,2,3} on the earlier .npz reproduce, exactly:
           results/p3c_freeze/per_subject.csv + errors.csv (development: 4 arms x 3 stages x 4 seeds),
           results/e23_test_look7/per_subject_seed.csv + errors.csv (test: points balanced and sensitivity),
           results/e22_test_oneshot/per_subject_seed.csv (look #6 = floor = cap = 0.005, CPD), and run_budget on the
           test bookkeeping = those rows (one code path for every CHB-MIT set); G-k: p3_levers.calibrate on the 15
           development cases, seed 42 = results/p3_levers/calibration.json (relative 1e-6, library versions).
  GE       the same checkpoints on the R0.4 features reproduce results/x1_external/rows_*.csv within the measured
           tolerance |dtp| <= 1, |dfp| <= 2 per row (src/v9_anatomy.py check_repro_ext); exact rows counted.
  G-vec    train_gae_v2.py --smoke (verbatim) vs the tensor loop on the same 2,000 new chb01 windows, 2 epochs, CPU:
           max |weight difference| <= 1e-6 (exact expected).
  R1.1     training, 4 seeds (one worker each, 1 thread, CPU): the thesis recipe on the new data of the 12 training
           patients (f7 constants recomputed by norm_constants; Adam 1e-3, cosine T_max = epochs, batch 32, 200 epochs,
           last epoch kept); per seed: training-window count = expected (committed counts, chb21 from the R0 diff
           report), 3,964 parameters, last-epoch loss < first (G2); validation loss once after the last epoch +
           train_gae_v2.sanity_auroc (both logged only, as in the record); checkpoint + json in the record format, loss
           curve as CSV (the record's _loss.npz is not written: .npz files are never committed).
  R1.2     k = p3_levers.calibrate on the 15 development cases, seed 42, new models (label-free).
  R1.3     every CHB-MIT case (development 15, test 8) and every external case (chb24 + Siena 14): p3c_freeze.run_budget
           for the 4 recorded arms (frozen 0.005; L2 clip(q, 0.0025, 0.02); L2f clip(q, 0.005, 0.02); S clip(q, 0.0075,
           0.02); 0.0075 = freeze.json's sensitivity floor, not re-selected), stages detector / cpd / hybrid, 4 seeds.
           No reading here: the rerun-vs-record tables are made by an aggregate script committed before R1_RUN.
Outputs (WORK = /kaggle/working): WORK/r2/r1_system/<tag>/ (run_meta.json, data_gate.json, data_sha256.csv,
gates.json, r10/, models/, training/, r13/, projection.json, logs/). Scratch (views, D arrays) in SCRATCH (/tmp/r2).
Test mode (synthetic data, build container only): environment R2_TEST (see src/r2_r1_synthetic_test.py).
"""
import contextlib
import hashlib
import json
import multiprocessing as mp
import os
import platform
import resource
import shutil
import sys
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

import r2_core as R0                     # noqa: E402  (stage R0, read only: sha256, json, log, compare_features)
import p2_scalars as PS                  # noqa: E402  (record, read only)
import p3_levers as P3L                  # noqa: E402
import p3c_freeze as P3C                 # noqa: E402
import e8_gae_v2_eval as E8              # noqa: E402
import e22_test_oneshot as E22           # noqa: E402
import e23_test_look7 as E23             # noqa: E402
import x1_external as X1                 # noqa: E402
import p2_dump_seeds23 as PD             # noqa: E402
import train_gae_v2 as TGV2              # noqa: E402

# the record modules find their own files (freeze.json, checkpoints, record results) through __file__: every one of them
# must come from the pinned repository, never from another copy that happens to sit earlier on sys.path (found 07/11 by
# the synthetic test: a spawned worker that re-ran a script's top level imported x1_external from another tree)
_OUTSIDE = [m.__name__ for m in (R0, PS, P3L, P3C, E8, E22, E23, X1, PD, TGV2)
            if (REPO / "src") not in Path(m.__file__).resolve().parents]
if _OUTSIDE:
    raise SystemExit(f"STOP: record modules imported from outside {REPO / 'src'}: {_OUTSIDE}")

WORK = Path(os.environ.get("R2_WORK", "/kaggle/working"))
INPUT = Path(os.environ.get("R2_INPUT", "/kaggle/input"))
SCRATCH = Path(os.environ.get("R2_SCRATCH", "/tmp/r2"))
OUT_ROOT = WORK / "r2" / "r1_system"
VIEWS = SCRATCH / "r1_views"
DSTORE = SCRATCH / "r1_D"

DEV = list(E8.SUBJS)                     # 15 development cases, record order
TEST = list(E22.TEST)                    # 8 test cases
TRAIN, VAL = list(TGV2.TRAIN), list(TGV2.VAL)
CHB = sorted(DEV + TEST)                 # the 23 thesis cases (chb24 is external: x1 convention)
GAP = ("chb11", "chb21")                 # cases rebuilt on all their files in R0.3 (plan §1)
TAGS = list(E22.TAGS)                    # clean_seed42, clean_seed1, clean_seed2, clean_seed3
SEED_OF = {t: int(t.split("seed")[1]) for t in TAGS}
FRZ = json.loads((REPO / "results" / "p3c_freeze" / "freeze.json").read_text())
K_RECORD = float(json.loads((REPO / "results" / "p3_levers" / "calibration.json").read_text())["k"])
ARMS = {"frozen": (0.005, 0.005), "L2": (P3L.P_MIN, P3C.CAP), "L2f": (0.005, P3C.CAP),
        "S": (float(FRZ["points"]["sensitivity"][0]), P3C.CAP)}            # = p3c_freeze.main's arms (t_s = 0.0075)
POINT_ARM = {"balanced": "L2f", "sensitivity": "S"}                       # e23 / x1 points = these arms, stage cpd
TOL = dict(float_rel=1e-9, k_rel=1e-6, const_rel=1e-9, gvec=1e-6, ext_tp=1, ext_fp=2)
SESSION_STOP_H, REFUSE_H = 11.3, 10.5
R0_OUT = REPO / "results" / "r2" / "r0_data"
X1_DIR = REPO / "results" / "x1_external"
EXT = ["chb24"] + sorted(p.stem.replace("rows_", "") for p in X1_DIR.glob("rows_PN*.csv"))
STATE = dict(tag=None, phases={}, notes=[], gates=[])
T0 = float(os.environ.get("R2_T0", time.time()))
log = R0.log
jdumps, _jdump, sha256_file = R0.jdumps, R0._jdump, R0.sha256_file


def sha16(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()[:16]


def hours():
    return (time.time() - T0) / 3600


def out_dir():
    d = OUT_ROOT / STATE["tag"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def phase(name, t):
    STATE["phases"][name] = round(time.time() - t, 1)
    log(f"phase {name}: {STATE['phases'][name]:.0f} s")


def gate(rec):
    """record a gate in gates.json; STOP (SystemExit) unless PASS."""
    STATE["gates"].append(rec)
    _jdump(out_dir() / "gates.json", STATE["gates"])
    log(f"{rec['gate']}: {rec['status']}" + (f" ({rec.get('summary')})" if rec.get("summary") else ""))
    if rec["status"] != "PASS":
        raise SystemExit(f"{rec['gate']} {rec['status']}: {jdumps({k: v for k, v in rec.items() if k != 'detail'})[:1500]}")


# ============================================================================ run metadata
def run_meta(tag, notebook, repo_commit):
    STATE["tag"] = tag
    import scipy
    import sklearn
    import torch
    vers = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                sklearn=sklearn.__version__, pandas=pd.__version__, torch=torch.__version__)
    for mod in ("torch_geometric", "ruptures", "timescoring", "mne"):
        try:
            vers[mod] = __import__(mod).__version__
        except Exception as e:          # noqa: BLE001
            vers[mod] = f"not importable: {e}"
    meta = dict(notebook=notebook, tag=tag, repo_commit=repo_commit, r2_r1_sha256=hashlib.sha256(
        Path(__file__).read_bytes()).hexdigest(), r2_core_sha256=sha256_file(R0.__file__),
                started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), cpu_count=os.cpu_count(), platform=platform.platform(),
                torch_threads=torch.get_num_threads(), versions=vers, input=str(INPUT), work=str(WORK),
                scratch=str(SCRATCH), test_mode=bool(os.environ.get("R2_TEST")))
    _jdump(out_dir() / "run_meta.json", meta)
    log("run_meta", jdumps({k: meta[k] for k in ("notebook", "repo_commit", "cpu_count", "torch_threads", "versions")}))
    return meta


def finish_meta(extra=None):
    p = out_dir() / "run_meta.json"
    meta = json.loads(p.read_text())
    meta.update(finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"), runtime_h=round(hours(), 3), phases_s=STATE["phases"],
                notes=STATE["notes"], peak_rss_self_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1),
                peak_rss_children_mb=round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1))
    meta.update(extra or {})
    _jdump(p, meta)
    return meta


# ============================================================================ views of the inputs
def _under(p, token):
    return any(token in x for x in Path(p).parts) and "r0_jobs" not in Path(p).parts \
        and SCRATCH not in Path(p).parents and WORK not in Path(p).parents


def _one_copy(hits, what):
    if not hits:
        raise SystemExit(f"STOP G-data: {what} not found under {INPUT}")
    if len({h.stat().st_size for h in hits}) != 1:
        raise SystemExit(f"STOP G-data: copies of {what} differ in size: {[str(h) for h in hits]}")
    return hits[0]


def build_views(chb_cases=None, ext_cases=None, earlier_cases=None):
    """symlink views SCRATCH/r1_views/{earlier,new,ext}: earlier = the record .npz (v9-x3-fold* inputs, R0's
    is_reference_path); new = thesis-r2-chbmit-features ({case}.npz + {case}_stats.json); ext =
    thesis-r2-external-features ({case}_lf.npz). Returns {kind: {case: path}}."""
    t = time.time()
    chb_cases = list(chb_cases or R0.CHB_CASES)            # all 24: G-data pins the whole dataset (chb24 is used by R2)
    ext_cases = list(ext_cases or EXT)
    earlier_cases = list(earlier_cases or chb_cases)
    shutil.rmtree(VIEWS, ignore_errors=True)
    v = {k: {} for k in ("earlier", "new", "new_stats", "ext")}
    for c in earlier_cases:
        v["earlier"][c] = R0.locate_earlier(c)
    for c in chb_cases:
        v["new"][c] = _one_copy([p for p in sorted(INPUT.rglob(f"{c}.npz")) if _under(p, "thesis-r2-chbmit-features")],
                                f"thesis-r2-chbmit-features/{c}.npz")
        v["new_stats"][c] = _one_copy([p for p in sorted(INPUT.rglob(f"{c}_stats.json"))
                                       if _under(p, "thesis-r2-chbmit-features") and "stats_earlier" not in p.parts],
                                      f"thesis-r2-chbmit-features/{c}_stats.json")
    for c in ext_cases:
        v["ext"][c] = _one_copy([p for p in sorted(INPUT.rglob(f"{c}_lf.npz")) if _under(p, "thesis-r2-external-features")],
                                f"thesis-r2-external-features/{c}_lf.npz")
    out = {}
    for kind in ("earlier", "new", "ext"):
        d = VIEWS / kind
        d.mkdir(parents=True, exist_ok=True)
        out[kind] = {}
        for c, p in v[kind].items():
            name = f"{c}_lf.npz" if kind == "ext" else f"{c}.npz"
            (d / name).symlink_to(p)
            out[kind][c] = d / name
    for c, p in v["new_stats"].items():
        (VIEWS / "new" / f"{c}_stats.json").symlink_to(p)
    out["src"] = {k: {c: str(p) for c, p in v[k].items()} for k in v}
    phase("views", t)
    return out


# ============================================================================ G-data
def _flag_counts(z):
    return dict(windows=int(len(z["is_ictal"])), ictal=int(np.asarray(z["is_ictal"]).sum()),
                clean=int(TGV2.mask(z, "clean").sum()), flag5sd=int(np.asarray(z["is_flag5sd"]).sum()),
                signal_loss=int(np.asarray(z["is_signal_loss"]).sum()))


def _feat_job(a):
    case, new, ref = a
    R0._limit_threads()
    try:
        rep = R0.compare_features(new, ref)
        return case, dict(status=rep["status"], scope=rep.get("gate_scope"), all_windows=rep.get("status_all_windows"),
                          f7=rep.get("windows", {}).get("chain", {}).get("f7_max_abs"),
                          bp5=rep.get("windows", {}).get("chain", {}).get("bp5_max_abs"),
                          adj=rep.get("windows", {}).get("chain", {}).get("adj_frac_differing"))
    except Exception:                    # noqa: BLE001
        return case, dict(status="FAIL", error=traceback.format_exc()[-1500:])


def gate_data(views, feat_cases=(), workers=4, pin=None):
    """G-data (see module docstring). Writes data_sha256.csv and data_gate.json; STOP on any difference. pin = a
    data_sha256.csv committed by an earlier R1 notebook (R1_RUN pins the smoke's): every file hashed here must have
    the pinned sha256 (same dataset versions)."""
    t = time.time()
    bad, rows, det = [], [], {}
    diff = json.loads((R0_OUT / "chb" / "diff_chb11_chb21.json").read_text())
    for c, p in views["new"].items():
        st_new = json.loads((VIEWS / "new" / f"{c}_stats.json").read_text())
        rows.append(dict(dataset="thesis-r2-chbmit-features", file=f"{c}.npz", bytes=p.stat().st_size,
                         sha256=sha256_file(p), source=views["src"]["new"][c]))
        rows.append(dict(dataset="thesis-r2-chbmit-features", file=f"{c}_stats.json",
                         bytes=(VIEWS / "new" / f"{c}_stats.json").stat().st_size,
                         sha256=sha256_file(VIEWS / "new" / f"{c}_stats.json"), source=views["src"]["new_stats"][c]))
        with np.load(p, allow_pickle=True) as z:
            cn = _flag_counts(z)
            if c in GAP:
                d = diff[c]
                want = dict(windows=d["windows_complete"], ictal=d["ictal_windows"][1], clean=d["clean_windows"][1],
                            flag5sd=d["flag5sd_windows"][1])
                got = {k: cn[k] for k in want}
                st_old = json.loads((R0_OUT / "chb" / "stats_earlier" / f"{c}_stats.json").read_text())
                cnt = {k: st_new[k] for k in d["counts_complete"]}
                sdo, sdn = np.asarray(st_old["ch_std_uV"]), np.asarray(st_new["ch_std_uV"])
                rel = {"ch_std_uV (relative change)": (sdn - sdo) / sdo,
                       "artifact_thresh_uV (relative change)": (np.asarray(st_new["artifact_thresh_uV"])
                                                                - np.asarray(st_old["artifact_thresh_uV"]))
                       / np.asarray(st_old["artifact_thresh_uV"]),
                       "ch_mean_uV (change / earlier SD)": (np.asarray(st_new["ch_mean_uV"])
                                                            - np.asarray(st_old["ch_mean_uV"])) / sdo}
                dev = max(float(np.max(np.abs(rel[k] - np.asarray(d["stats_rel_change"][k]["per_channel"])))) for k in rel)
                ok = got == want and cnt == d["counts_complete"] and dev <= 1e-12
                det[c] = dict(check="R0 diff report", counts=got, want=want, stats_counts=cnt, stats_rel_dev=dev, ok=ok)
            else:
                st_ref = json.loads((R0_OUT / "chb" / "stats_earlier" / f"{c}_stats.json").read_text())
                with np.load(views["earlier"][c], allow_pickle=True) as r:
                    same = {k: bool(np.array_equal(np.asarray(z[k]), np.asarray(r[k]))) for k in R0.FLAGS + ("file_idx",)}
                    same["files"] = [str(x) for x in z["files"]] == [str(x) for x in r["files"]]
                ok = st_new == st_ref and all(same.values())
                det[c] = dict(check="earlier .npz + committed R0 stats", counts=cn, stats_equal=st_new == st_ref,
                              exact=same, ok=ok)
        if not det[c]["ok"]:
            bad.append(c)
    ext_ref = pd.read_csv(R0_OUT / "ext" / "external_cases.csv").set_index("case")
    for c, p in views["ext"].items():
        rows.append(dict(dataset="thesis-r2-external-features", file=f"{c}_lf.npz", bytes=p.stat().st_size,
                         sha256=sha256_file(p), source=views["src"]["ext"][c]))
        with np.load(p, allow_pickle=True) as z:
            cn = _flag_counts(dict(is_ictal=z["is_ictal"], is_signal_loss=z["is_signal_loss"],
                                   is_buffer=np.zeros(len(z["is_ictal"]), bool),
                                   is_flag5sd=np.zeros(len(z["is_ictal"]), bool)))
            nfiles = len(z["files"])
        r = ext_ref.loc[c]
        want = dict(windows=int(r.windows), ictal=int(r.ictal_windows), signal_loss=int(r.signal_loss_windows),
                    files=int(r.files))
        got = dict(windows=cn["windows"], ictal=cn["ictal"], signal_loss=cn["signal_loss"], files=nfiles)
        det[c] = dict(check="results/r2/r0_data/ext/external_cases.csv", counts=got, want=want, ok=got == want)
        if got != want:
            bad.append(c)
    pd.DataFrame(rows).to_csv(out_dir() / "data_sha256.csv", index=False)
    pinned = None
    if pin is not None and Path(pin).exists():
        pv = pd.read_csv(pin).set_index(["dataset", "file"]).sha256.to_dict()
        diff_pin = [f"{r['dataset']}/{r['file']}" for r in rows if pv.get((r["dataset"], r["file"])) != r["sha256"]]
        pinned = dict(file=str(Path(pin).relative_to(REPO)) if REPO in Path(pin).parents else str(pin),
                      files_compared=len(rows), differ=diff_pin)
        bad += [f"sha256 differs from the pinned {pinned['file']}: {x}" for x in diff_pin]
    feat = {}
    jobs = [(c, str(views["new"][c]), str(views["earlier"][c])) for c in feat_cases if c not in GAP]
    if jobs:
        with mp.get_context("spawn").Pool(min(workers, len(jobs)), initializer=_init_worker, initargs=(_env(),)) as pool:
            for c, r in pool.imap_unordered(_feat_job, sorted(jobs, key=lambda j: -Path(j[1]).stat().st_size)):
                feat[c] = r
                if r["status"] != "PASS":
                    bad.append(f"{c}: G-feat re-read {r}")
    rec = dict(gate="G-data", status="PASS" if not bad else "FAIL", bad=bad, files_hashed=len(rows), pinned=pinned,
               gfeat_reread={c: feat[c] for c in sorted(feat)}, detail=det,
               summary=f"{len(views['new'])} CHB-MIT + {len(views['ext'])} external cases; G-feat re-read on "
                       f"{len(feat)} cases")
    _jdump(out_dir() / "data_gate.json", rec)
    phase("gate_data", t)
    gate(rec)
    return rec


# ============================================================================ G-const + G-count
def committed_meta(tag):
    return json.loads((REPO / "data" / "models_v2" / f"gae_v2_{tag}.json").read_text())


def expected_counts(views):
    """clean training / validation window counts expected on the new data: the committed metas for the gap-free
    cases (G-data proved their flags equal), the R0 diff report for chb11 / chb21."""
    diff = json.loads((R0_OUT / "chb" / "diff_chb11_chb21.json").read_text())
    m = committed_meta("clean_seed42")
    tr = {s: (diff[s]["clean_windows"][1] if s in GAP else int(m["n_train"][s])) for s in TRAIN}
    va = {s: (diff[s]["clean_windows"][1] if s in GAP else int(m["n_val"][s])) for s in VAL}
    return tr, va


def gate_const_count():
    t = time.time()
    mu, sd = TGV2.norm_constants(VIEWS / "earlier", "clean")
    rel, metas = 0.0, {t_: committed_meta(t_) for t_ in TAGS}
    same = all(metas[t_]["add_mean"] == metas[TAGS[0]]["add_mean"] and metas[t_]["add_std"] == metas[TAGS[0]]["add_std"]
               for t_ in TAGS)
    for got, key in ((mu, "add_mean"), (sd, "add_std")):
        want = np.asarray(metas[TAGS[0]][key])
        rel = max(rel, float(np.max(np.abs(got - want) / np.maximum(np.abs(want), 1e-12))))
    gate(dict(gate="G-const", status="PASS" if rel <= TOL["const_rel"] and same else "FAIL", max_rel=rel,
              four_seeds_equal=same, summary=f"max relative difference {rel:.2e}"))
    cnt, bad = {}, []
    for s in TRAIN + VAL:
        with np.load(VIEWS / "earlier" / f"{s}.npz", allow_pickle=True) as z:
            cnt[s] = int(TGV2.mask(z, "clean").sum())
        want = metas[TAGS[0]]["n_train" if s in TRAIN else "n_val"][s]
        if cnt[s] != int(want):
            bad.append((s, cnt[s], want))
    gate(dict(gate="G-count", status="PASS" if not bad else "FAIL", counts=cnt, bad=bad,
              summary=f"{len(cnt)} cases, clean windows = committed metas"))
    phase("gate_const_count", t)


# ============================================================================ workers
def _env():
    return {k: os.environ[k] for k in os.environ if k.startswith(("R2_", "THESIS_", "OMP_", "OPENBLAS_", "MKL_"))} | \
        dict(R1_SYS_PATH=os.pathsep.join(sys.path))


def _init_worker(env):
    os.environ.update(env)
    for q in env.get("R1_SYS_PATH", "").split(os.pathsep):
        if q and q not in sys.path:
            sys.path.insert(0, q)
    try:
        import torch
        torch.set_num_threads(1)
    except Exception:                    # noqa: BLE001
        pass
    R0._limit_threads()


def _pool(n):
    return mp.get_context("spawn").Pool(n, initializer=_init_worker, initargs=(_env(),), maxtasksperchild=1)


def n_workers(gb_per_worker=6.0):
    mem_gb = os.sysconf("SC_PAGE_SIZE") * os.sysconf("SC_PHYS_PAGES") / 1e9
    return max(1, min(4, os.cpu_count() or 1, int(mem_gb // gb_per_worker)))


# ============================================================================ D, bookkeeping, scoring
def load_case(case, src):
    """src 'earlier' | 'new' -> NpzFile (thesis convention); 'ext' -> (dict, meta) as x1_external.cmd_run loads it."""
    if src == "ext":
        z = dict(np.load(VIEWS / "ext" / f"{case}_lf.npz", allow_pickle=True))
        return z, json.loads(str(z.pop("meta")))
    return np.load(VIEWS / src / f"{case}.npz", allow_pickle=True), None


def chb_ctx(case, z, idx, D):
    """the window bookkeeping of e22_test_oneshot.test_context, built from the npz and the distances (no dump file):
    the same fields p2_scalars.subject_context gives a development case (the chain reads D, idx, n, ok, fidx, wf, ict,
    z); proven equal on synthetic caches by src/r2_r1_synthetic_test.py and, on real data, by gate R1.0."""
    ok = ~z["is_signal_loss"].astype(bool)
    if not np.array_equal(idx, np.flatnonzero(ok)):
        raise SystemExit(f"STOP {case}: window index differs from the non-signal-loss windows")
    ict = z["is_ictal"].astype(bool)
    fidx = z["file_idx"].astype(int)
    fl5 = z["is_flag5sd"].astype(bool) if "is_flag5sd" in z.files else np.zeros(len(ict), bool)
    return dict(s=case, z=z, idx=idx, D={t: np.asarray(D[t], dtype=np.float64) for t in TAGS}, Z={t: None for t in TAGS},
                c8={}, p2={}, n=len(ict), ok=ok, fidx=fidx, wf=fidx[idx], ict=ict, ict_ok=ict & ok, fl5=fl5,
                nonict=~ict & ~z["is_buffer"].astype(bool) & ok, nh=float((~ict & ok).sum()) * E22.WIN / 3600)


def d_job(a):
    """distances of one case with the 4 checkpoints in ckpt_dir (x1_external.model_outputs, unchanged; PD.CKPT pointed
    at ckpt_dir), stored in SCRATCH/r1_D/<label>/<case>.npz: CHB-MIT float32 (dump convention), external float64.
    Returns timing and, for development cases, the seed-42 smoothed member mean (for k)."""
    case, src, ckpt_dir, label, want_smm = a
    t = time.time()
    try:
        PD.CKPT = Path(ckpt_dir)
        z, meta = load_case(case, src)
        idx, D = X1.model_outputs(z)
        if src != "ext":
            D = {t_: D[t_].astype(np.float32) for t_ in TAGS}
        d = DSTORE / label
        d.mkdir(parents=True, exist_ok=True)
        np.savez(d / f".{case}.npz", idx=idx, **{f"{t_}_d": D[t_] for t_ in TAGS})
        (d / f".{case}.npz").replace(d / f"{case}.npz")
        smm = None
        if want_smm:
            ctx = chb_ctx(case, z, idx, D)
            smm = PS.smoothed(ctx, P3L.member_mean_z(ctx, "clean_seed42"), P3C.SMOOTH)
        n = int(len(z["is_ictal"]))
        return dict(case=case, src=src, label=label, windows=n, eeg_h=n * E22.WIN / 3600, valid=int(len(idx)),
                    d_s=round(time.time() - t, 1), finite=bool(all(np.isfinite(D[t_]).all() for t_ in TAGS)),
                    smm=smm, peak_rss_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
    except SystemExit as e:
        return dict(case=case, src=src, label=label, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, label=label, error=traceback.format_exc()[-3000:])


def ctx_from_store(case, src, label):
    z, meta = load_case(case, src)
    d = np.load(DSTORE / label / f"{case}.npz")
    idx, D = d["idx"], {t: d[f"{t}_d"] for t in TAGS}
    if src == "ext":
        return X1.make_ctx(z, idx, D), meta
    return chb_ctx(case, z, idx, D), meta


def score_job(a):
    """one case, 4 seeds, from the stored distances. mode 'r10' adds the record functions' own rows (test: e23.evaluate
    at the two points and at floor = cap = 0.005; external: x1_external.evaluate_ctx); every mode runs
    p3c_freeze.run_budget for the 4 arms (development: the record function of p3c_freeze)."""
    case, src, label, k, mode, set_name = a
    t = time.time()
    try:
        ctx, meta = ctx_from_store(case, src, label)
        rows, errs, qrows, extra = [], [], [], {}
        for tag in TAGS:
            x = E22.final_scalar(ctx, tag)
            q = P3L.q_of(PS.smoothed(ctx, P3L.member_mean_z(ctx, tag), P3C.SMOOTH), k)
            qrows.append(dict(set=set_name, subject=case, seed=tag, k=k, q_raw=q))
            for name, (fl, cp) in ARMS.items():
                P3C.run_budget(ctx, case, tag, x, q, fl, cp, name, rows, errs)
        for r in rows + errs:
            r["set"] = set_name
        if mode == "r10" and src != "ext":
            e_rows, e_errs, l6 = [], [], []
            if case in TEST:
                for pt, (fl, cp) in FRZ["points"].items():
                    for tag in TAGS:
                        out, er = E23.evaluate(ctx, tag, FRZ, fl, cp, FRZ["localizer"])
                        e_rows += [dict(point=pt, subject=case, seed=tag, stage=st, **v) for st, v in out.items()]
                        e_errs += [dict(point=pt, subject=case, seed=tag, **e) for e in er]
                for tag in TAGS:
                    out, _ = E23.evaluate(ctx, tag, FRZ, 0.005, 0.005, "cpd")
                    l6 += [dict(subject=case, seed=tag, stage=st, **v) for st, v in out.items()]
            extra = dict(e23_rows=e_rows, e23_errs=e_errs, look6=l6)
        if mode == "r10" and src == "ext":
            x_rows, x_errs = [], []
            sname = "chb24" if case.startswith("chb") else "siena"
            X1.evaluate_ctx(ctx, case, sname, x_rows, x_errs)
            extra = dict(x1_rows=[dict(r, hours=meta["hours"], skipped=len(meta["skipped"])) for r in x_rows],
                         x1_errs=x_errs)
        return dict(case=case, src=src, label=label, rows=rows, errs=errs, q=qrows, score_s=round(time.time() - t, 1),
                    **extra)
    except SystemExit as e:
        return dict(case=case, src=src, label=label, error=f"STOP: {e}")
    except Exception:                    # noqa: BLE001
        return dict(case=case, src=src, label=label, error=traceback.format_exc()[-3000:])


def _run(fn, specs, workers, what):
    """run specs in a spawn pool (largest first); STOP at the first error."""
    out = []
    if not specs:
        return out
    with _pool(min(workers, len(specs))) as pool:
        for r in pool.imap_unordered(fn, specs):
            if r.get("error"):
                pool.terminate()
                raise SystemExit(f"{what} {r['case']} ({r['src']}): {r['error']}")
            out.append(r)
            log(f"{what} {r['case']}:{r['src']} done ({r.get('d_s', r.get('score_s'))} s)")
    return out


def _size(case, src):
    p = VIEWS / src / (f"{case}_lf.npz" if src == "ext" else f"{case}.npz")
    return p.stat().st_size


def distances(cases_src, ckpt_dir, label, workers):
    """cases_src: [(case, src)]; returns {case: d_job result}."""
    t = time.time()
    specs = sorted([(c, s, str(ckpt_dir), label, c in DEV) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    res = {r["case"]: r for r in _run(d_job, specs, workers, f"D[{label}]")}
    bad = [c for c, r in res.items() if not r["finite"]]
    if bad:
        raise SystemExit(f"STOP: non-finite distances for {bad} ({label})")
    phase(f"D_{label}", t)
    return res


def set_of(case, src):
    return "external" if src == "ext" else ("development" if case in DEV else "test")


def scoring(cases_src, label, k, mode, workers):
    t = time.time()
    specs = sorted([(c, s, label, k, mode, set_of(c, s)) for c, s in cases_src], key=lambda a: -_size(a[0], a[1]))
    res = {r["case"]: r for r in _run(score_job, specs, workers, f"score[{label}]")}
    phase(f"score_{label}", t)
    return res


# ============================================================================ R1.0 comparisons with the record
def _cmp_rows(mine, ref, keys, ints, floats):
    """row-wise comparison: ints exact, floats relative TOL['float_rel']; returns (n_rows, mismatches)."""
    m = pd.DataFrame(mine)
    mg = m.merge(ref, on=keys, how="outer", suffixes=("", "_ref"), indicator=True)
    bad = [dict(r) for _, r in mg[mg._merge != "both"][keys + ["_merge"]].iterrows()]
    both = mg[mg._merge == "both"]
    for c in ints:
        d = both[both[c].astype(np.int64) != both[f"{c}_ref"].astype(np.int64)]
        bad += [dict(**{k_: r[k_] for k_ in keys}, col=c, got=int(r[c]), want=int(r[f"{c}_ref"])) for _, r in d.iterrows()]
    for c in floats:
        a, b = both[c].astype(float).values, both[f"{c}_ref"].astype(float).values
        rel = np.abs(a - b) / np.maximum(np.abs(b), 1e-12)
        for i in np.flatnonzero(rel > TOL["float_rel"]):
            r = both.iloc[i]
            bad.append(dict(**{k_: r[k_] for k_ in keys}, col=c, got=float(a[i]), want=float(b[i])))
    return int(len(both)), bad


def _cmp_errors(mine, ref, keys, cols):
    """errors: per group (keys) the ordered list of tuples must be equal."""
    a = pd.DataFrame(mine)
    bad, n = [], 0
    ga = {k: g[cols].astype(int).values.tolist() for k, g in a.groupby(keys)} if len(a) else {}
    gb = {k: g[cols].astype(int).values.tolist() for k, g in ref.groupby(keys)} if len(ref) else {}
    for k in sorted(set(ga) | set(gb), key=str):
        n += len(gb.get(k, []))
        if ga.get(k) != gb.get(k):
            bad.append(dict(group=str(k), got=ga.get(k), want=gb.get(k)))
    return n, bad


ROW_INT = ["tp", "fp", "n_ref", "short_tp", "short_n"]
ERR_COLS = ["det_on", "det_off", "cpd_on", "cpd_off", "hyb_on", "hyb_off"]


def r10_compare(res, cases_dev, cases_test, cases_ext):
    """gates R1.0 (development, test, look #6, run_budget on test) and GE (external) from the scored results."""
    o = out_dir() / "r10"
    o.mkdir(parents=True, exist_ok=True)
    recs = []
    if cases_dev:
        rows = [r for c in cases_dev for r in res[c]["rows"]]
        errs = [r for c in cases_dev for r in res[c]["errs"]]
        pd.DataFrame(rows).to_csv(o / "dev_per_subject.csv", index=False)
        pd.DataFrame(errs).to_csv(o / "dev_errors.csv", index=False)
        ref = pd.read_csv(REPO / "results" / "p3c_freeze" / "per_subject.csv")
        ref = ref[ref.subject.isin(cases_dev)]
        n, bad = _cmp_rows([{k: v for k, v in r.items() if k != "set"} for r in rows], ref,
                           ["subject", "seed", "budget", "stage"], ROW_INT + ["review_s", "rec_s"], ["top", "nonict_h"])
        eref = pd.read_csv(REPO / "results" / "p3c_freeze" / "errors.csv")
        ne, ebad = _cmp_errors(errs, eref[eref.subject.isin(cases_dev)], ["subject", "seed", "budget"], ERR_COLS)
        recs.append(dict(gate="R1.0-dev", status="PASS" if not bad and not ebad else "FAIL", rows=n, error_pairs=ne,
                         mismatches=bad[:50], n_mismatch=len(bad), error_mismatches=ebad[:20], n_error_mismatch=len(ebad),
                         cases=cases_dev, summary=f"p3c_freeze: {n} rows, {ne} error pairs; {len(bad) + len(ebad)} differ"))
    if cases_test:
        er = [r for c in cases_test for r in res[c]["e23_rows"]]
        ee = [r for c in cases_test for r in res[c]["e23_errs"]]
        l6 = [r for c in cases_test for r in res[c]["look6"]]
        pd.DataFrame(er).to_csv(o / "test_e23_rows.csv", index=False)
        pd.DataFrame(ee).to_csv(o / "test_e23_errors.csv", index=False)
        pd.DataFrame(l6).to_csv(o / "test_look6_rows.csv", index=False)
        ref = pd.read_csv(REPO / "results" / "e23_test_look7" / "per_subject_seed.csv")
        ref = ref[ref.subject.isin(cases_test)]
        n, bad = _cmp_rows(er, ref, ["point", "subject", "seed", "stage"], ROW_INT + ["review_s", "rec_s"],
                           ["top", "q_raw", "nonict_h"])
        eref = pd.read_csv(REPO / "results" / "e23_test_look7" / "errors.csv")
        ne, ebad = _cmp_errors(ee, eref[eref.subject.isin(cases_test)], ["point", "subject", "seed"], ERR_COLS)
        r6 = pd.read_csv(REPO / "results" / "e22_test_oneshot" / "per_subject_seed.csv")
        n6, bad6 = _cmp_rows([{k: r[k] for k in ["subject", "seed", "stage"] + ROW_INT + ["nonict_h"]} for r in l6],
                             r6[r6.subject.isin(cases_test)], ["subject", "seed", "stage"], ROW_INT, ["nonict_h"])
        rows = [r for c in cases_test for r in res[c]["rows"]]
        errs = [r for c in cases_test for r in res[c]["errs"]]
        pd.DataFrame(rows).to_csv(o / "test_run_budget.csv", index=False)
        pd.DataFrame(errs).to_csv(o / "test_run_budget_errors.csv", index=False)
        # one code path: run_budget's detector / cpd rows on test = e23 (L2f, S) and look #6 (frozen)
        rb = pd.DataFrame(rows)
        cons = []
        for _, r in pd.DataFrame(er).iterrows():
            st = "cpd" if r.stage == "localized" else "detector"
            q = rb[(rb.subject == r.subject) & (rb.seed == r.seed) & (rb.budget == POINT_ARM[r.point]) & (rb.stage == st)]
            if len(q) != 1 or (int(q.tp.iloc[0]), int(q.fp.iloc[0])) != (int(r.tp), int(r.fp)):
                cons.append((r.point, r.subject, r.seed, r.stage))
        for _, r in pd.DataFrame(l6).iterrows():
            st = "cpd" if r.stage == "localized" else "detector"
            q = rb[(rb.subject == r.subject) & (rb.seed == r.seed) & (rb.budget == "frozen") & (rb.stage == st)]
            if len(q) != 1 or (int(q.tp.iloc[0]), int(q.fp.iloc[0])) != (int(r.tp), int(r.fp)):
                cons.append(("look6", r.subject, r.seed, r.stage))
        ok = not bad and not ebad and not bad6 and not cons
        recs.append(dict(gate="R1.0-test", status="PASS" if ok else "FAIL", rows_e23=n, error_pairs=ne, rows_look6=n6,
                         mismatches=bad[:50], n_mismatch=len(bad), error_mismatches=ebad[:20], n_error_mismatch=len(ebad),
                         look6_mismatches=bad6[:20], run_budget_vs_record=cons[:20], cases=cases_test,
                         summary=f"e23 {n} rows + {ne} error pairs, look #6 {n6} rows, run_budget consistency "
                                 f"{len(cons)} differ; {len(bad) + len(ebad) + len(bad6)} differ from the record"))
    if cases_ext:
        xr = [r for c in cases_ext for r in res[c]["x1_rows"]]
        xe = [r for c in cases_ext for r in res[c]["x1_errs"]]
        pd.DataFrame(xr).to_csv(o / "ext_x1_rows.csv", index=False)
        pd.DataFrame(xe).to_csv(o / "ext_x1_errors.csv", index=False)
        ref = pd.concat([pd.read_csv(X1_DIR / f"rows_{c}.csv") for c in cases_ext], ignore_index=True)
        keys = ["subject", "point", "seed", "stage"]
        mg = pd.DataFrame(xr).merge(ref, on=keys, how="outer", suffixes=("", "_ref"), indicator=True)
        miss = mg[mg._merge != "both"]
        both = mg[mg._merge == "both"].copy()
        both["dtp"] = both.tp.astype(int) - both.tp_ref.astype(int)
        both["dfp"] = both.fp.astype(int) - both.fp_ref.astype(int)
        over = both[(both.dtp.abs() > TOL["ext_tp"]) | (both.dfp.abs() > TOL["ext_fp"])]
        nref = both[(both.n_ref.astype(int) != both.n_ref_ref.astype(int))
                    | ((both.nonict_h - both.nonict_h_ref).abs() > 1e-6)]
        exact = int(((both.dtp == 0) & (both.dfp == 0)).sum())
        both[keys + ["tp", "tp_ref", "fp", "fp_ref", "dtp", "dfp"]].to_csv(o / "ext_vs_x1.csv", index=False)
        eref = pd.concat([pd.read_csv(X1_DIR / f"errors_{c}.csv") for c in cases_ext
                          if (X1_DIR / f"errors_{c}.csv").stat().st_size > 2], ignore_index=True)
        edesc = {}
        if len(xe) and len(eref):
            a = pd.DataFrame(xe)
            for col in ERR_COLS:
                edesc[col] = dict(median_abs=float(a[col].abs().median()), median_abs_ref=float(eref[col].abs().median()))
            edesc["pairs"], edesc["pairs_ref"] = int(len(a)), int(len(eref))
        ok = not len(miss) and not len(over) and not len(nref)
        recs.append(dict(gate="GE", status="PASS" if ok else "FAIL", rows=int(len(both)), exact_rows=exact,
                         max_abs_dtp=int(both.dtp.abs().max()) if len(both) else 0,
                         max_abs_dfp=int(both.dfp.abs().max()) if len(both) else 0, missing=int(len(miss)),
                         over_tolerance=over[keys + ["dtp", "dfp"]].to_dict("records")[:30],
                         n_ref_or_hours_differ=int(len(nref)), errors_descriptive=edesc, cases=cases_ext,
                         summary=f"{len(both)} rows, {exact} exact, max |dtp| "
                                 f"{int(both.dtp.abs().max()) if len(both) else 0}, max |dfp| "
                                 f"{int(both.dfp.abs().max()) if len(both) else 0} (tolerance 1 / 2)"))
    for r in recs:
        gate(r)
    return recs


def gate_k(smm_by_case):
    """G-k: p3_levers.calibrate on the 15 development cases, seed 42 = calibration.json (relative 1e-6)."""
    k = float(P3L.calibrate([smm_by_case[s] for s in DEV]))
    rel = abs(k - K_RECORD) / abs(K_RECORD)
    gate(dict(gate="G-k", status="PASS" if rel <= TOL["k_rel"] else "FAIL", k=k, k_record=K_RECORD, rel=rel,
              summary=f"k {k:.9f} vs record {K_RECORD:.9f} (relative {rel:.1e})"))
    return k


def r10(cases_dev, cases_test, cases_ext, workers=None, with_k=False):
    """R1.0 + GE: committed checkpoints on the earlier .npz (CHB-MIT) and on the R0.4 features (external)."""
    workers = workers or n_workers()
    cs = [(c, "earlier") for c in list(cases_dev) + list(cases_test)] + [(c, "ext") for c in cases_ext]
    dres = distances(cs, REPO / "data" / "models_v2", "r10", workers)
    if with_k:
        gate_k({c: dres[c]["smm"] for c in DEV})
    sres = scoring(cs, "r10", K_RECORD, "r10", workers)
    timing = pd.DataFrame([{k: v for k, v in r.items() if k != "smm"} | dict(score_s=sres[r["case"]]["score_s"])
                           for r in dres.values()])
    (out_dir() / "r10").mkdir(parents=True, exist_ok=True)
    timing.to_csv(out_dir() / "r10" / "timing.csv", index=False)
    recs = r10_compare(sres, cases_dev, cases_test, cases_ext)
    return recs, timing


# ============================================================================ G-vec on the thesis recipe
def gate_vec(seed=42):
    """the thesis recipe's own smoke (train_gae_v2.main --smoke: chb01 first 2,000 clean windows, 2 epochs, constants
    from the 12 training patients, validation loss logged) run verbatim on the new data, vs the tensor loop of
    f1_core on the same windows, CPU, same process: max |weight difference| <= 1e-6."""
    import torch
    import f1_core as F
    import gae_joint as G
    t = time.time()
    ref_dir = SCRATCH / "r1_gvec"
    shutil.rmtree(ref_dir, ignore_errors=True)
    ref_dir.mkdir(parents=True)
    argv = sys.argv
    sys.argv = ["train_gae_v2.py", "--variant", "clean", "--seed", str(seed), "--data_root", str(VIEWS / "new"),
                "--out_dir", str(ref_dir), "--smoke"]
    logf = out_dir() / "logs" / "gvec_train_gae_v2_smoke.log"
    logf.parent.mkdir(parents=True, exist_ok=True)
    try:
        with open(logf, "w") as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
            TGV2.main()
    finally:
        sys.argv = argv
    tag = f"gae_v2_clean_seed{seed}_SMOKE"
    rmeta = json.loads((ref_dir / f"{tag}.json").read_text())
    ref = G.GAEModel(in_dim=TGV2.IN_DIM, bands=TGV2.OUT_X)
    ref.load_state_dict(torch.load(str(ref_dir / f"{tag}.pt"), map_location="cpu"), strict=True)
    point_npz(TRAIN + VAL, "new")
    meta = dict(add_mean=rmeta["add_mean"], add_std=rmeta["add_std"], clip=rmeta["clip"])
    mine, info, _ = F.train("gae", TRAIN[:1], meta, seed, torch.device("cpu"), epochs=2, max_windows=2000, tag=" G-vec")
    d = F._maxdiff(ref, mine)
    st = "PASS" if d <= TOL["gvec"] and info["n_train"] == rmeta["n_train"][TRAIN[0]] else "FAIL"
    rec = dict(gate="G-vec", status=st, max_abs_diff=d, exact=d == 0.0, case=TRAIN[0], windows=info["n_train"],
               reference_windows=rmeta["n_train"][TRAIN[0]], epochs=2, seed=seed, torch=torch.__version__,
               threads=torch.get_num_threads(), seconds=round(time.time() - t, 1),
               summary=f"train_gae_v2.py --smoke vs tensor loop: max |weight difference| {d:.3e}")
    phase("gate_vec", t)
    gate(rec)
    return rec


# ============================================================================ R1.1 training
def point_npz(cases, src):
    """model_cmp_core's npz registry (read by f1_core's tensor builder) -> the view of src."""
    import model_cmp_core as C
    for s in cases:
        C._NPZ[s] = VIEWS / src / f"{s}.npz"
    C._CACHE.clear()


def train_job(a):
    """one seed: the thesis recipe on the new data (module docstring, R1.1); writes the checkpoint in the record format
    (gae_v2_clean_seed{s}.pt + .json; loss curve as CSV) and _DONE.json last."""
    seed, epochs, out_models, out_train, expected, expected_val, smoke = a
    import torch
    import f1_core as F
    t0 = time.time()
    tag = f"gae_v2_clean_seed{seed}"
    try:
        dev = torch.device("cpu")
        mu, sd = TGV2.norm_constants(VIEWS / "new", "clean")
        meta = dict(add_mean=mu.tolist(), add_std=sd.tolist(), clip=4.0)
        point_npz(TRAIN + VAL, "new")
        model, info, rows = F.train("gae", TRAIN, meta, seed, dev, epochs=epochs, tag=f" seed {seed}")
        exp_n = sum(expected.values())
        if info["n_train"] != exp_n:
            raise SystemExit(f"training windows {info['n_train']} != expected {exp_n}")
        if info["G2"] != "PASS":
            raise SystemExit(f"G2: last-epoch loss {info['last_loss']} not below the first {info['first_loss']}")
        t1 = time.time()
        import model_cmp_core as C
        vl, nv = 0.0, {}
        with torch.no_grad():
            for s in VAL:
                A, X, T = C._mlp_tensors([s], meta, dev, lambda z: TGV2.mask(z, "clean"))
                nv[s] = int(len(A))
                for i in range(0, len(A), 512):
                    vl += float(F._loss("gae", model, A[i:i + 512], X[i:i + 512], T[i:i + 512]).sum())
        final_val = vl / max(1, sum(nv.values()))
        if nv != expected_val:
            raise SystemExit(f"validation windows {nv} != expected {expected_val}")
        san = TGV2.sanity_auroc(model, VIEWS / "new", mu, sd, dev)
        val_s = round(time.time() - t1, 1)
        out_models.mkdir(parents=True, exist_ok=True)
        torch.save({k: v.cpu() for k, v in model.state_dict().items()}, out_models / f"{tag}.pt")
        m = dict(variant="clean", seed=seed, in_dim=TGV2.IN_DIM, out_x=TGV2.OUT_X, n_add=TGV2.N_ADD,
                 add_features=["logbp_delta", "logbp_theta", "logbp_alpha", "logbp_beta", "logbp_gamma", "log_linelen",
                               "slog_kurtosis"], add_mean=mu.tolist(), add_std=sd.tolist(), clip=4.0,
                 n_train={s: int(expected[s]) for s in TRAIN}, n_val=nv, epochs=epochs, batch=F.BATCH, lr=F.LR,
                 lambda_=0.1, final_train=rows[-1]["train_loss"], final_val=final_val, val_sanity_auroc=san,
                 elapsed_s=round(time.time() - t0), loop="f1_core.train (tensor loop; G-vec)", device=str(dev),
                 threads=torch.get_num_threads(), torch=torch.__version__, first_loss=info["first_loss"],
                 last_loss=info["last_loss"], G2=info["G2"], n_params=info["n_params"], ms_per_step=info["ms_per_step"],
                 fit_s=info["fit_s"], load_s=info["load_s"], val_and_sanity_s=val_s, smoke=smoke,
                 r2_r1_sha256=hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
                 note="validation loss computed once after the last epoch (the record logged it every epoch; it never "
                      "affects training); loss curve in training/training_log_seed{s}.csv (no .npz: never committed); "
                      "plan §12 07/11 16:40")
        m["checkpoint_sha256"] = sha256_file(out_models / f"{tag}.pt")
        (out_models / f"{tag}.json").write_text(json.dumps(m, indent=1))
        out_train.mkdir(parents=True, exist_ok=True)
        pd.DataFrame(rows).assign(seed=seed).to_csv(out_train / f"training_log_seed{seed}.csv", index=False)
        peak = round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1)
        done = dict(seed=seed, status="done", seconds=round(time.time() - t0), epochs=epochs, n_train=info["n_train"],
                    ms_per_step=info["ms_per_step"], fit_s=info["fit_s"], load_s=info["load_s"], val_and_sanity_s=val_s,
                    peak_rss_mb=peak, checkpoint_sha256=m["checkpoint_sha256"], r2_r1_sha256=m["r2_r1_sha256"])
        (out_models / f"{tag}_DONE.json").write_text(json.dumps(done, indent=1))
        return done
    except SystemExit as e:
        return dict(seed=seed, status="STOP", error=str(e))
    except Exception:                    # noqa: BLE001
        return dict(seed=seed, status="FAILED", error=traceback.format_exc()[-3000:])


def import_models(out_models, repo_sha=None):
    """resume: finished seeds of a previous version's output attached as input (…/r1_system/run/models/*_DONE.json,
    same r2_r1 sha, checkpoint hash intact) -> out_models. Returns the seeds imported."""
    got = []
    me = hashlib.sha256(Path(__file__).read_bytes()).hexdigest()
    for dj in sorted(INPUT.rglob("gae_v2_clean_seed*_DONE.json")):
        if "r1_system" not in dj.parts or "smoke" in dj.parts:
            continue
        d = json.loads(dj.read_text())
        tag = dj.name.replace("_DONE.json", "")
        pt = dj.parent / f"{tag}.pt"
        if d.get("r2_r1_sha256") != (repo_sha or me) or not pt.exists() or sha256_file(pt) != d.get("checkpoint_sha256"):
            log(f"resume: {tag} not usable (code sha / checkpoint hash)")
            continue
        out_models.mkdir(parents=True, exist_ok=True)
        if not (out_models / dj.name).exists():
            for suf in (".pt", ".json", "_DONE.json"):
                shutil.copyfile(dj.parent / f"{tag}{suf}", out_models / f"{tag}{suf}")
            got.append(int(d["seed"]))
    if got:
        log(f"resume: seeds {got} imported from a previous output")
    return got


def train_seeds(views, seeds, epochs, out_models, out_train, smoke=False, projected_h=None):
    """R1.1: one worker per seed (1 thread each). STOP on any job failure."""
    t = time.time()
    exp, exp_val = expected_counts(views)
    todo = [s for s in seeds if not (out_models / f"gae_v2_clean_seed{s}_DONE.json").exists()]
    if projected_h is not None and todo and hours() + projected_h * 1.1 > SESSION_STOP_H:
        raise SystemExit(f"STOP: training projected {projected_h:.2f} h would end after {SESSION_STOP_H} h of session "
                         f"(now {hours():.2f} h)")
    res = []
    if todo:
        with _pool(len(todo)) as pool:
            for r in pool.imap_unordered(train_job, [(s, epochs, out_models, out_train, exp, exp_val, smoke) for s in todo]):
                log(f"training seed {r['seed']}: {r['status']} ({r.get('seconds')} s, {r.get('ms_per_step')} ms/step)")
                res.append(r)
                if r["status"] != "done":
                    pool.terminate()
                    raise SystemExit(f"training seed {r['seed']}: {r['status']}: {r.get('error')}")
    done = [json.loads((out_models / f"gae_v2_clean_seed{s}_DONE.json").read_text()) for s in seeds]
    rec = dict(gate="R1.1-training" + ("-smoke" if smoke else ""), status="PASS", epochs=epochs, expected_n_train=exp,
               expected_n_val=exp_val, jobs=done, trained_now=[r["seed"] for r in res],
               summary=f"seeds {seeds}: n_train {sum(exp.values())}, 3,964 parameters, G2 PASS")
    phase("train" + ("_smoke" if smoke else ""), t)
    gate(rec)
    return done


def step_timing(n_steps=200, n_windows=20000, workers=None):
    """measured ms per training step (batch 32), GAE, on new chb01 windows, W concurrent workers."""
    workers = workers or n_workers()
    with _pool(workers) as pool:
        r = pool.map(_timing_one, [(n_steps, n_windows)] * workers)
    return dict(workers=workers, ms_per_step=[round(x, 3) for x in r], mean=round(float(np.mean(r)), 3))


def _timing_one(a):
    n_steps, n_windows = a
    import torch
    import f1_core as F
    mu, sd = TGV2.norm_constants(VIEWS / "new", "clean")
    point_npz(TRAIN[:1], "new")
    import model_cmp_core as C
    A, X, T = C._mlp_tensors(TRAIN[:1], dict(add_mean=mu, add_std=sd, clip=4.0), torch.device("cpu"), C.clean_mask,
                             n_windows)
    model = F.build("gae")
    opt = torch.optim.Adam(model.parameters(), lr=F.LR)
    g = torch.Generator().manual_seed(0)
    for rep in range(2):
        t = time.time()
        for _ in range(n_steps):
            ii = torch.randint(0, len(A), (F.BATCH,), generator=g)
            opt.zero_grad(); F._loss("gae", model, A[ii], X[ii], T[ii]).mean().backward(); opt.step()
        dt = (time.time() - t) / n_steps * 1000
    return dt


# ============================================================================ R1.2 + R1.3
def r13(cases_dev, cases_test, cases_ext, models_dir, label, workers=None):
    """distances with the new checkpoints on the new data (CHB-MIT) and the R0.4 features (external); k by
    p3_levers.calibrate on the development cases, seed 42; p3c_freeze.run_budget for the 4 arms on every case.
    Writes r13/<label>/per_subject.csv, errors.csv, q.csv, k.json, timing.csv."""
    workers = workers or n_workers()
    cs = [(c, "new") for c in list(cases_dev) + list(cases_test)] + [(c, "ext") for c in cases_ext]
    dres = distances(cs, models_dir, label, workers)
    k = float(P3L.calibrate([dres[c]["smm"] for c in cases_dev]))
    o = out_dir() / "r13" / label
    o.mkdir(parents=True, exist_ok=True)
    _jdump(o / "k.json", dict(k=k, k_record=K_RECORD, cases=list(cases_dev), seed="clean_seed42", rule=
                              "p3_levers.calibrate: median over patients of q_i(k) = 0.005 (label-free)"))
    log(f"R1.2 [{label}]: k computed on {len(cases_dev)} development cases (value in k.json)")
    sres = scoring(cs, label, k, "r13", workers)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["rows"]]).to_csv(o / "per_subject.csv", index=False)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["errs"]]).to_csv(o / "errors.csv", index=False)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["q"]]).to_csv(o / "q.csv", index=False)
    pd.DataFrame([{kk: v for kk, v in dres[c].items() if kk != "smm"} | dict(score_s=sres[c]["score_s"])
                  for c, _ in cs]).to_csv(o / "timing.csv", index=False)
    return k, sres, dres


def rescore(cases_src, d_label, out_label, k, workers=None):
    """scoring only, from distances already stored under d_label, at a given k; outputs under r13/<out_label>."""
    workers = workers or n_workers()
    o = out_dir() / "r13" / out_label
    o.mkdir(parents=True, exist_ok=True)
    sres = scoring(cs := list(cases_src), d_label, k, "r13", workers)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["rows"]]).to_csv(o / "per_subject.csv", index=False)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["errs"]]).to_csv(o / "errors.csv", index=False)
    pd.DataFrame([r for c, _ in cs for r in sres[c]["q"]]).to_csv(o / "q.csv", index=False)
    _jdump(o / "k.json", dict(k=k, k_record=K_RECORD, distances_from=d_label, rule="fixed k (no calibration)"))
    return sres


def counterfactual(cases_dev, cases_test, cases_ext, workers=None):
    """descriptive decomposition of rerun - record (plan §12 07/11 18:55): the COMMITTED checkpoints on the NEW data
    (CHB-MIT complete .npz; external R0.4 features), scored (i) with k recomputed by p3_levers.calibrate (label 'cf') and
    (ii) at the record's k (label 'cf_krec', same distances). Then cf_krec - record = data, cf - cf_krec = k,
    rerun - cf = new models (training on complete data + retraining randomness). Scoring only, no training."""
    t = time.time()
    k, _, _ = r13(cases_dev, cases_test, cases_ext, REPO / "data" / "models_v2", "cf", workers)
    cs = [(c, "new") for c in list(cases_dev) + list(cases_test)] + [(c, "ext") for c in cases_ext]
    rescore(cs, "cf", "cf_krec", K_RECORD, workers)
    phase("counterfactual", t)
    return k


# ============================================================================ projection (computed estimate)
def projection(r10_timing, train_smoke, views, gfeat_s_per_case=None, limit_h=REFUSE_H):
    """R1_RUN wall time from smoke measurements: R1.0 distances + scoring (s per hour of EEG per worker, measured on
    the smoke cases) over all cases / workers; training = steps x ms per step measured with 4 concurrent full-size
    jobs + their non-epoch time; R1.3 like R1.0 on the new data; G-feat re-read; computed estimate, labelled so."""
    w = n_workers()
    T = r10_timing.copy()
    T["s_per_h"] = (T.d_s + T.score_s) / T.eeg_h
    chb_rate = float(T[T.src != "ext"].s_per_h.max()) if (T.src != "ext").any() else np.nan
    ext_rate = float(T[T.src == "ext"].s_per_h.max()) if (T.src == "ext").any() else chb_rate
    # per-task overhead (worker start + imports; every task runs in a fresh worker): pool wall time x workers used,
    # minus the time measured inside the tasks, per task; two tasks per case (distances, scoring)
    n, wu = len(T), min(w, len(T))
    ph = STATE["phases"]
    ov = max(0.0, ((ph.get("D_r10", 0) + ph.get("score_r10", 0)) * wu - float((T.d_s + T.score_s).sum())) / max(1, 2 * n))
    n_cases = len(CHB) + len(EXT)
    inv = pd.read_csv(R0_OUT / "chb" / "inventory_cases.csv")
    chb_h_earlier = float(inv[inv.case.isin(CHB)].earlier_hours_used_windows.sum())
    chb_h_new = float(inv[inv.case.isin(CHB)].hours_used_windows.sum())
    ext_h = float(pd.read_csv(R0_OUT / "ext" / "external_cases.csv").hours.sum())
    r10_h = (chb_h_earlier * chb_rate + ext_h * ext_rate + 2 * n_cases * ov) / w / 3600
    r13_h = (chb_h_new * chb_rate + ext_h * ext_rate + 2 * n_cases * ov) / w / 3600
    exp, _ = expected_counts(views)
    steps = int(np.ceil(sum(exp.values()) / 32)) * 200
    ms = float(np.max([j["ms_per_step"] for j in train_smoke]))
    extra_s = float(np.max([j["load_s"] + j["val_and_sanity_s"] for j in train_smoke]))
    train_h = (steps * ms / 1000 + extra_s) / 3600
    gfeat_h = (gfeat_s_per_case or 0) * 22 / w / 3600
    total = 0.25 + gfeat_h + r10_h + train_h + r13_h
    p = dict(computed_estimate=True, workers=w, chb_s_per_eeg_h_per_worker=round(chb_rate, 2),
             ext_s_per_eeg_h_per_worker=round(ext_rate, 2), task_overhead_s=round(ov, 1), chb_hours_earlier=round(chb_h_earlier, 2),
             chb_hours_new=round(chb_h_new, 2), ext_hours=round(ext_h, 2), r10_h=round(r10_h, 2), steps_per_seed=steps,
             ms_per_step_4_concurrent=round(ms, 3), train_nonepoch_s=round(extra_s, 1), train_h=round(train_h, 2),
             r13_h=round(r13_h, 2), gfeat_reread_h=round(gfeat_h, 2), setup_h=0.25, total_h=round(total, 2),
             limit_h=limit_h, split=bool(total > limit_h),
             note="largest per-case rate used (conservative); training = slowest of 4 concurrent 2-epoch jobs")
    _jdump(out_dir() / "projection.json", p)
    log("projection (computed estimate): " + jdumps(p))
    return p


def summary_md(extra_lines=()):
    """SUMMARY.md of a notebook: gates (status + one line), phases, projection; no research number."""
    L = [f"# R1 {STATE['tag']} — gates and timing (no research number)\n", "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {g.get('summary', '')} |" for g in STATE["gates"]]
    L += ["", f"Phases (s): {jdumps(STATE['phases'])}", ""] + list(extra_lines)
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
