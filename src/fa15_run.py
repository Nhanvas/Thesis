#!/usr/bin/env python
"""
fa15_run.py -- F-A1.5 / PC5 training and scoring (chat D35-F; design approved by the author 21/11 19:13, option A:
results/fa15/DESIGN_D35F.md §7, written before any training output). Project verification outside the report (R204).

Question: does ASR (V9-X6 settings) in the preprocessing change the detection of the thesis system once the GAE is
retrained on the cleaned signals? Arms (each = the path-2 recipe: r2_r1.train_job unchanged, 200 epochs, then k per seed
by p3_levers.calibrate on the 15 development cases, then p3c_freeze.run_budget for the 4 recorded budget arms x 3 stages
on every set):
  control  the path-2 model on R0's data: seeds 42, 1, 2, 3, 4 committed (results/r2/r1_system/rp, k per seed) +
           seeds 5, 6, 7 trained here (notebook FA15_RUN_CTRL)
  asr      the same recipe on the ASR datasets of FA15_DATA_A / _B1 / _B2: seeds 42, 1, 2, 3 (FA15_RUN_ASR_A) and
           4, 5, 6, 7 (FA15_RUN_ASR_B)
Record code called unchanged: r2_r1.py (sha16 76cbe51ff0180d4a = R1_RUN / RP_RUN) and r2_rp.py (5281446e6168312e = RP_RUN):
views, d_job, calibrate_per_seed, score_k_job, train_seeds / train_job, gate_vec, gate_data, gate_const_new. Only
r2_r1.expected_counts is replaced in the asr notebooks (the ASR data have their own 5-SD flags; the expected clean
window counts are counted from the ASR files themselves, then train_job checks them as it does for R0).

Gates (STOP unless noted):
  G-mod       r2_r1.py / r2_rp.py of the pinned clone = the control's code (sha16 above)
  mode        library versions vs R1_RUN (r2_rp.check_versions): exact / tolerance
  G-data      R0's datasets = the pinned R1_SMOKE hashes (r2_rp.gate_data)
  G-repro     the committed control checkpoint of seed 4 on R0's data, scored by this module's path with its committed k,
              = results/r2/r1_system/rp/rp2 rows of clean_seed4 (exact: tp, fp, n_ref, top equal, errors equal; tolerance
              |dtp| <= 1, |dfp| <= 2) -> the scoring path is the control's
  ctrl:  G-const-new (r2_rp.gate_const_new: constants and window counts of R0's data = the R1 checkpoints)
  asr:   G-asr-data (every ASR file found once in the three inputs; labels, buffer, signal loss, file index and file
         lists = R0's for every case; sha256 of every ASR file recorded) and G-asr-counts (clean training / validation
         windows counted on the ASR files; logged beside R0's, no reference)
  G-vec       r2_r1.gate_vec on the data in use (train_gae_v2.py --smoke vs the tensor loop)
  training    r2_r1.train_seeds: window counts = expected, 3,964 parameters, G2
  RUN-complete rows = 38 cases x seeds x 4 budget arms x 3 stages
  G-worker-sha the pool workers imported r2_r1.py, r2_rp.py and fa15_run.py of this commit (sha16 = the main process's)
Machine (CPU model, AVX-512, BLAS) in run_meta (Kaggle machine types train with different arithmetic, handback 28.3).
Outputs: WORK/r2/r1_system/fa15_<arm>_<part>/ (run_meta.json, gates.json, data_sha256.csv, asr_data.csv, models/,
training/, repro/, run/ (per_subject.csv, errors.csv, q.csv, k.json, thresholds.csv), SUMMARY.md). No reading here: the
tables come from src/fa15_aggregate.py, committed before these notebooks run.
"""
import hashlib
import json
import os
import platform
import shutil
import time
import traceback
from pathlib import Path

import numpy as np
import pandas as pd

import r2_rp as RP                       # stage RP (sha16 5281446e6168312e), read only

R1 = RP.R1
R0, TGV2 = R1.R0, R1.TGV2
REPO = R1.REPO
RP_DIR = REPO / "results" / "r2" / "r1_system" / "rp"
SHA_R1, SHA_RP = "76cbe51ff0180d4a", "5281446e6168312e"
TEST = bool(os.environ.get("R2_TEST"))
REPRO_TAG = "clean_seed4"
ARMS = {"ctrl": dict(seeds=[5, 6, 7]), "asr_a": dict(seeds=[42, 1, 2, 3]), "asr_b": dict(seeds=[4, 5, 6, 7])}
ASR_TOKEN = dict(new="fa15-asr-chbmit-features", ext="fa15-asr-external-features")
LAB_KEYS = dict(new=("is_ictal", "is_buffer", "is_signal_loss", "file_idx", "files"),
                ext=("is_ictal", "is_signal_loss", "file_idx", "files"))
log = R1.log


def sha16(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()[:16]


def machine_info():
    """CPU model, AVX-512, numpy BLAS (as fa15_asr.machine_info; not imported, to keep this module's imports minimal)."""
    info = dict(cpu_model=None, avx512f=None, blas=None)
    try:
        txt = Path("/proc/cpuinfo").read_text()
        info["cpu_model"] = next((l.split(":", 1)[1].strip() for l in txt.splitlines() if l.startswith("model name")), None)
        info["avx512f"] = " avx512f" in next((l for l in txt.splitlines() if l.startswith("flags")), "")
    except OSError:
        info["cpu_model"] = platform.processor()
    try:
        b = np.show_config(mode="dicts")["Build Dependencies"]["blas"]
        info["blas"] = f"{b.get('name')} {b.get('version')}"
    except Exception:                    # noqa: BLE001
        pass
    return info


def import_own(models_dir, arm):
    """resume: finished seeds of a previous version of THIS notebook attached as input (a folder named fa15_<arm>, same
    r2_r1 sha, checkpoint hash intact) -> models_dir. r2_r1.import_models is not used: it would also accept another
    arm's checkpoints of the same seed."""
    got = []
    for dj in sorted(R1.INPUT.rglob("gae_v2_clean_seed*_DONE.json")):
        if f"fa15_{arm}" not in dj.parts:
            continue
        d = json.loads(dj.read_text())
        tag = dj.name.replace("_DONE.json", "")
        pt = dj.parent / f"{tag}.pt"
        if d.get("r2_r1_sha256", "")[:16] != sha16(R1.__file__) or not pt.exists() or R1.sha256_file(pt) != d.get(
                "checkpoint_sha256"):
            log(f"resume: {tag} not usable (code sha / checkpoint hash)")
            continue
        models_dir.mkdir(parents=True, exist_ok=True)
        if not (models_dir / dj.name).exists():
            for suf in (".pt", ".json", "_DONE.json"):
                shutil.copyfile(dj.parent / f"{tag}{suf}", models_dir / f"{tag}{suf}")
            got.append(int(d["seed"]))
    if got:
        log(f"resume: seeds {got} imported from a previous output of fa15_{arm}")
    return got


def code_shas():
    return dict(r2_r1=sha16(R1.__file__), r2_rp=sha16(RP.__file__), fa15_run=sha16(__file__))


# ============================================================================ worker sha
def worker_sha_job(_):
    """run in a pool worker (r2_rp's initializer): the sha16 of the modules the worker imported."""
    try:
        import r2_r1
        import r2_rp
        import fa15_run
        return dict(case="worker", r2_r1=sha16(r2_r1.__file__), r2_rp=sha16(r2_rp.__file__),
                    fa15_run=sha16(fa15_run.__file__), pid=os.getpid())
    except Exception:                    # noqa: BLE001
        return dict(case="worker", error=traceback.format_exc()[-1500:])


def gate_worker_sha(workers, tags):
    main = code_shas()
    if TEST and os.environ.get("FA15_TEST_WORKER_SHA"):
        main = dict(main, fa15_run=os.environ["FA15_TEST_WORKER_SHA"])
    res = RP._run(worker_sha_job, list(range(max(1, workers))), workers, tags, "G-worker-sha")
    bad = [r for r in res if {k: r[k] for k in main} != main]
    R1.gate(dict(gate="G-worker-sha", status="PASS" if res and not bad else "FAIL", main=main, workers=len(res),
                 differ=bad[:4], summary=f"{len(res) - len(bad)} of {len(res)} workers imported r2_r1 {main['r2_r1']}, "
                                         f"r2_rp {main['r2_rp']}, fa15_run {main['fa15_run']}"))


# ============================================================================ G-mod
def gate_mod():
    got = code_shas()
    ok = TEST or (got["r2_r1"] == SHA_R1 and got["r2_rp"] == SHA_RP)
    R1.gate(dict(gate="G-mod", status="PASS" if ok else "FAIL", got=got, want=dict(r2_r1=SHA_R1, r2_rp=SHA_RP),
                 summary=f"r2_r1 {got['r2_r1']}, r2_rp {got['r2_rp']} (control's code), fa15_run {got['fa15_run']}"))


# ============================================================================ G-repro
def gate_repro(workers):
    """the committed control checkpoint of seed 4, R0's data, its committed k, this path = rp2's rows of clean_seed4."""
    t = time.time()
    mode = RP.STATE["mode"]
    ck = R1.SCRATCH / "fa15_repro_ckpt"
    shutil.rmtree(ck, ignore_errors=True)
    ck.mkdir(parents=True)
    for suf in (".pt", ".json"):
        (ck / f"gae_v2_{REPRO_TAG}{suf}").symlink_to((RP_DIR / "models" / f"gae_v2_{REPRO_TAG}{suf}").resolve())
    kmap = {REPRO_TAG: float(json.loads((RP_DIR / "rp2" / "k.json").read_text())["k"][REPRO_TAG])}
    RP.distances(RP.all_cases(), ck, "repro", [REPRO_TAG], workers)
    sc = RP.scoring("repro", kmap, [REPRO_TAG], workers)
    o = R1.out_dir() / "repro"
    o.mkdir(parents=True, exist_ok=True)
    sc["rows"].to_csv(o / "per_subject.csv", index=False)
    sc["errs"].to_csv(o / "errors.csv", index=False)
    ref = pd.read_csv(RP_DIR / "rp2" / "per_subject.csv")
    ref = ref[ref.seed == REPRO_TAG]
    refe = pd.read_csv(RP_DIR / "rp2" / "errors.csv")
    refe = refe[refe.seed == REPRO_TAG]
    n, exact, bad = RP._cmp_rows(sc["rows"], ref, mode)
    ne, ebad = RP._cmp_errors(sc["errs"], refe)
    ok = not bad and (mode == "tolerance" or not ebad)
    R1.phase("g_repro", t)
    R1.gate(dict(gate="G-repro", status="PASS" if ok else "FAIL", mode=mode, rows=n, exact_rows=exact, mismatches=bad[:20],
                 n_mismatch=len(bad), error_pairs=ne, error_groups_differ=len(ebad), k=kmap,
                 summary=f"mode {mode}: control seed 4 rescored = rp2 ({n} rows, {exact} exact, {len(bad)} mismatches; "
                         f"{len(ebad)} error groups differ)"))


# ============================================================================ ASR views and data gates
def build_views_asr():
    """symlink views SCRATCH/r1_views/{new,ext} on the ASR datasets (the r2_rp layout); every case found once."""
    t = time.time()
    shutil.rmtree(R1.VIEWS, ignore_errors=True)
    src = {"new": {}, "new_stats": {}, "ext": {}}
    for c in R0.CHB_CASES:
        if c == "chb24":
            continue                                      # chb24 is external (x1 convention), as in R1 / RP
        src["new"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}.npz")) if R1._under(p, ASR_TOKEN["new"])],
                                     f"{ASR_TOKEN['new']}*/{c}.npz")
        src["new_stats"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_stats.json"))
                                            if R1._under(p, ASR_TOKEN["new"])], f"{ASR_TOKEN['new']}*/{c}_stats.json")
    for c in R1.EXT:
        src["ext"][c] = R1._one_copy([p for p in sorted(R1.INPUT.rglob(f"{c}_lf.npz")) if R1._under(p, ASR_TOKEN["ext"])],
                                     f"{ASR_TOKEN['ext']}*/{c}_lf.npz")
    out = {"new": {}, "ext": {}}
    for kind in ("new", "ext"):
        (R1.VIEWS / kind).mkdir(parents=True, exist_ok=True)
        for c, p in src[kind].items():
            q = R1.VIEWS / kind / (f"{c}_lf.npz" if kind == "ext" else f"{c}.npz")
            q.symlink_to(p)
            out[kind][c] = q
    for c, p in src["new_stats"].items():
        (R1.VIEWS / "new" / f"{c}_stats.json").symlink_to(p)
    out["src"] = {k: {c: str(p) for c, p in v.items()} for k, v in src.items()}
    R1.phase("views_asr", t)
    return out


def gate_asr_data(asr, r0):
    """every ASR case's labels / buffer / signal loss / file index / file list = R0's; sha256 of every file recorded."""
    t = time.time()
    rows, bad = [], []
    for kind in ("new", "ext"):
        for c, p in asr[kind].items():
            with np.load(p, allow_pickle=True) as za, np.load(r0[kind][c], allow_pickle=True) as zr:
                eq = {k: bool(np.array_equal(np.asarray(za[k]), np.asarray(zr[k]))) for k in LAB_KEYS[kind]}
                n = int(len(za["is_ictal"]))
                fl = int(np.asarray(za["is_flag5sd"]).sum()) if "is_flag5sd" in za.files else None
                flr = int(np.asarray(zr["is_flag5sd"]).sum()) if "is_flag5sd" in zr.files else None
            if not all(eq.values()):
                bad.append(dict(case=c, kind=kind, equal=eq))
            rows.append(dict(kind=kind, case=c, file=Path(p).name, windows=n, flag5sd_asr=fl, flag5sd_r0=flr,
                             sha256=R1.sha256_file(p), source=asr["src"][kind][c], labels_equal=all(eq.values())))
            if kind == "new":
                st = R1.VIEWS / "new" / f"{c}_stats.json"
                rows.append(dict(kind="stats", case=c, file=st.name, sha256=R1.sha256_file(st),
                                 source=asr["src"]["new_stats"][c]))
    pd.DataFrame(rows).to_csv(R1.out_dir() / "asr_data.csv", index=False)
    R1.phase("gate_asr_data", t)
    n_cases = len(asr["new"]) + len(asr["ext"])
    R1.gate(dict(gate="G-asr-data", status="PASS" if not bad and n_cases == len(R0.CHB_CASES) - 1 + len(R1.EXT) else "FAIL",
                 cases=n_cases, differ=bad[:10],
                 summary=f"{n_cases} ASR cases; labels / buffer / signal loss / file index / files = R0 in "
                         f"{n_cases - len(bad)} of {n_cases}"))


def counts_from_views(views=None):
    """clean training / validation window counts of the files in VIEWS/new (the ASR data's own 5-SD flags)."""
    tr, va = {}, {}
    for s in R1.TRAIN + R1.VAL:
        with np.load(R1.VIEWS / "new" / f"{s}.npz", allow_pickle=True) as z:
            (tr if s in R1.TRAIN else va)[s] = int(TGV2.mask(z, "clean").sum())
    return tr, va


def gate_asr_counts(r0_counts):
    tr, va = counts_from_views()
    rt, rv = r0_counts
    R1.gate(dict(gate="G-asr-counts", status="PASS", train=tr, val=va, train_r0=rt, val_r0=rv,
                 n_train=int(sum(tr.values())), n_train_r0=int(sum(rt.values())),
                 summary=f"clean training windows ASR {sum(tr.values())} vs R0 {sum(rt.values())}; validation "
                         f"{sum(va.values())} vs {sum(rv.values())} (logged; counted on the ASR files)"))


# ============================================================================ training, distances, k, scoring
def train(views, seeds, epochs, models_dir, arm):
    import_own(models_dir, arm)
    todo = [s for s in seeds if not (models_dir / f"gae_v2_clean_seed{s}_DONE.json").exists()]
    proj = None
    if todo:
        tt = R1.step_timing(workers=len(todo))
        exp, _ = R1.expected_counts(views)
        proj = (int(np.ceil(sum(exp.values()) / 32)) * epochs * max(tt["ms_per_step"]) / 1000 + 900) / 3600
        R1.STATE["notes"].append(dict(step_timing=tt, projected_training_h=round(proj, 2)))
        log(f"step timing ({len(todo)} workers) {tt} -> projected training {proj:.2f} h (computed estimate)")
    return R1.train_seeds(views, seeds, epochs, models_dir, R1.out_dir() / "training", projected_h=proj)


def score_run(models_dir, tags, workers):
    t = time.time()
    RP.distances(RP.all_cases(), models_dir, "run", tags, workers)
    kmap = RP.calibrate_per_seed("run", tags, workers)
    o = R1.out_dir() / "run"
    o.mkdir(parents=True, exist_ok=True)
    R1._jdump(o / "k.json", dict(k=kmap, cases=list(R1.DEV), rule="p3_levers.calibrate on each seed's own model: median "
                                 "over the 15 development cases of q_i(k) = 0.005 (as rp2)"))
    sc = RP.scoring("run", kmap, tags, workers)
    sc["rows"].to_csv(o / "per_subject.csv", index=False)
    sc["errs"].to_csv(o / "errors.csv", index=False)
    sc["q"].to_csv(o / "q.csv", index=False)
    sc["thr"].to_csv(o / "thresholds.csv", index=False)
    n_want = (len(R1.DEV) + len(R1.TEST) + len(R1.EXT)) * len(tags) * len(R1.ARMS) * 3
    R1.phase("score_run", t)
    R1.gate(dict(gate="RUN-complete", status="PASS" if len(sc["rows"]) == n_want else "FAIL", rows=int(len(sc["rows"])),
                 expected=n_want, k=kmap, summary=f"{len(sc['rows'])} rows (expected {n_want}); k per seed {kmap}"))
    return kmap


# ============================================================================ orchestration
def run(arm, notebook="local", commit="local", epochs=200, workers=None):
    """one notebook: arm in ARMS. Returns the output folder."""
    tag = f"fa15_{arm}"
    seeds = list(json.loads(os.environ["FA15_TEST_SEEDS"]) if TEST and os.environ.get("FA15_TEST_SEEDS")
                 else ARMS[arm]["seeds"])
    tags = [f"clean_seed{s}" for s in seeds]
    meta = R1.run_meta(tag, notebook, commit)
    meta.update(arm=arm, seeds=seeds, machine=machine_info(), code=code_shas(), epochs=epochs)
    R1._jdump(R1.out_dir() / "run_meta.json", meta)
    W = workers or R1.n_workers()
    gate_mod()
    mode, vdiff = RP.check_versions(meta)
    log(f"arm {arm}, seeds {seeds}, mode {mode}, workers {W}, machine {meta['machine']}")
    r0v = RP.build_views()
    RP.gate_data(r0v)
    if arm == "ctrl":
        RP.gate_const_new(r0v)
    gate_repro(W)
    views = r0v
    if arm != "ctrl":
        r0_counts = R1.expected_counts(r0v)
        r0_paths = {k: dict(v) for k, v in r0v.items() if k in ("new", "ext")}
        r0_keep = R1.SCRATCH / "fa15_r0_view"                  # keep R0's files reachable after the views are rebuilt
        shutil.rmtree(r0_keep, ignore_errors=True)
        for kind in ("new", "ext"):
            (r0_keep / kind).mkdir(parents=True)
            for c, p in r0_paths[kind].items():
                (r0_keep / kind / p.name).symlink_to(Path(r0v["src"][kind][c]))
                r0_paths[kind][c] = r0_keep / kind / p.name
        views = build_views_asr()
        gate_asr_data(views, r0_paths)
        R1.expected_counts = counts_from_views                 # main process only: train_seeds passes the counts on
        gate_asr_counts(r0_counts)
    R1.gate_vec(seed=42)
    models = R1.out_dir() / "models"
    train(views, seeds, epochs, models, arm)
    score_run(models, tags, W)
    gate_worker_sha(W, tags)
    return R1.out_dir()


def summary_md():
    L = [f"# {R1.STATE['tag']} -- F-A1.5 / PC5 training and scoring (gates and timing; no research number; mode "
         f"{RP.STATE['mode']})\n", "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {g['gate']} | {g['status']} | {str(g.get('summary', '')).replace('|', '/')[:400]} |" for g in R1.STATE["gates"]]
    L += ["", f"Phases (s): {R1.jdumps(R1.STATE['phases'])}", "",
          "Tables: `python src/fa15_aggregate.py` (committed before this run)."]
    (R1.out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
    return "\n".join(L)
