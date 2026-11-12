#!/usr/bin/env python
"""r2_rb1.py -- stage RB, step RB1 (`RB1_DATA`, Kaggle CPU): chb12 rebuilt with chb12_27-29 converted as SzCORE does,
new feature dataset `thesis-r2-chbmit-features-rb`. Design approved by the author 12/11 22:13 (plan §12 row 12/11 22:15,
handback Part 17); board R170, R176, R181, R182.

The record path of R0 is used unchanged (`r2_core.stats_record` -> `preprocessing.compute_subject_stats` /
`count_windows`; `r2_core.features_record` -> `c1b_build_trainset.build`), with the referential -> bipolar wrapper
`r2_rb.install()` active in every worker. No record module is edited.

Order (every gate STOPs the notebook with SystemExit; nothing is written to the dataset folder before the last gate):
  G-code   record modules imported from the pinned clone and byte-equal (sha256) to the files R0 ran (`235682a`);
           r2_core = R0's (902d15ad); r2_rb = D22-F's; the three referential files of r2_rb = R0's inventory sha256;
           the committed chb12 summary = PhysioNet's (inventory).
  mode     library versions that touch the arithmetic (python, numpy, scipy, mne) vs R0_CHB's run_meta: equal -> 'exact'
           (every comparison bit for bit), different -> 'tolerance' (R0's own gates: stats relative <= 1e-6 and counts
           exact; G-feat tolerances on the chain windows).
  G-raw    the 24 summary-listed chb12 EDFs + the summary under the Kaggle inputs, sha256 = R0's inventory
           (= PhysioNet); no download.
  G-R0     the 48 chb*.npz / chb*_stats.json of the R0 dataset `thesis-r2-chbmit-features` = R1_SMOKE's pinned hashes.
  Job A    (gate) wrapper + the 21 bipolar files: stats = R0's committed chb12 stats; features = R0's chb12.npz. The one
           allowed difference: skipped_files [] here vs the three referential files in R0's build (they are not in this
           view). Proves on Kaggle that the platform reproduces R0 and that the wrapper leaves bipolar files untouched.
  Job B    (build) wrapper + all 24 files. Gates: 24 files in summary order, nothing skipped; windows per file = header
           samples // 1024; seizures of the three files = expected (6 + 1 + 6) and the two record parsers agree on every
           file; is_ictal / is_buffer of every file = an independent recomputation from the summary times (window w is
           ictal iff [4w, 4w+4) meets a seizure; buffered iff it meets [offset, offset + 4 h) within the file); on the 21
           common files is_ictal, is_buffer, is_signal_loss = Job A per file; stats counts = the .npz labels (n_ictal =
           ictal windows; n_interictal + n_rejected = non-ictal, non-buffer windows) for A and B; f7 finite outside
           signal-loss windows.
  G-clip   (descriptive part, gated sum) samples at the EDF digital limits of the 19 electrodes of the three files, read
           with a small numpy EDF reader, per 4 s window; per-electrode clipped samples, per-derivation affected samples
           and per-file windows with any clipped sample = RB0b's committed tables (pyedflib) exactly.
  G-copy   the 23 other cases copied from the R0 dataset, sha256 = pin after the copy; new pin data_sha256.csv (63 rows,
           the two chb12 rows new; dataset labels unchanged so that the R1 / RP / R2 / R3 code reads it as before).
Descriptive (no rule, P2): diff_chb12.{json,md} (format of R0's diff_chb11_chb21 + seizures, n_ref, hours, clean
windows of the added files, flags by file group); clipping per window / per derivation / per seizure / by window class;
histogram tail of every electrode (Schlogl et al. 1999, DOI 10.1016/S1388-2457(99)00172-8: a header may not state the
real saturation value -> the most frequent values in the outer 0.5 % tails are listed, so a pile-up below the header
limits would show).
Outputs: WORK/thesis-r2-chbmit-features-rb/ (24 {case}.npz + {case}_stats.json + inventory.csv + RB1_NOTE.md) and
WORK/r2/r0_data/chb12_ref/rb1/ (gates.json, run_meta.json, data_sha256.csv, stats/, diff_chb12.*, clipping_*, logs/).
Test mode (synthetic data, build container only): R2_TEST, R2_TEST_RB_REFERENTIAL, R2_TEST_RB1_EXPECT
(src/r2_rb1_synthetic_test.py).
"""
import hashlib
import json
import os
import re
import shutil
import time
import traceback
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

import r2_core as R0          # unchanged (sha 902d15ad); sets REPO / WORK / INPUT / SCRATCH and sys.path
import r2_rb as RB            # the D22-F wrapper (sha 00d2c322)

CASE = "chb12"
NEW = ["chb12_27.edf", "chb12_28.edf", "chb12_29.edf"]
EXPECT_SEIZURES = {"chb12_27.edf": 6, "chb12_28.edf": 1, "chb12_29.edf": 6}        # summary (RB0)
if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_RB1_EXPECT"):
    EXPECT_SEIZURES = json.loads(os.environ["R2_TEST_RB1_EXPECT"])
DS_NAME = "thesis-r2-chbmit-features"           # the R0 dataset (folder and pin label)
DS_RB = R0.WORK / "thesis-r2-chbmit-features-rb"
TAG = "chb12_ref/rb1"
R0_OUT = R0.REPO / "results" / "r2" / "r0_data"
PIN = R0.REPO / "results" / "r2" / "r1_system" / "smoke" / "data_sha256.csv"
RB0B = R0_OUT / "chb12_ref" / "rb0b"
VERSION_KEYS = ("python", "numpy", "scipy", "mne")
WIN = 1024
BUF_S = 4 * 3600
# sha256 of the files R0_CHB ran (repository at 235682a; r2_core embedded, sha 902d15ad) and of r2_rb (commit 1d5fd70)
CODE_SHA = {
    "src/dataprep/preprocessing.py": "0172fbea61b285400a0cf1fb9052b98a39e2b09f2b4cb09bfa2352149b6c5af2",
    "src/continuous_eval.py": "8fea38dabee5ad252e1d23411805820a44c66802d7468233078d0173684164e8",
    "src/c1b_build_trainset.py": "b4596a8aa37976537de3cbba8fd16a248cdfffc005b0b365288749bc97696deb",
    "src/dataprep/graph_construction.py": "c22a976fdc531c8ceb45aeb9e7c96322235b71d666e7a44871e5dc1bed527838",
    "src/dataprep/feature_extraction.py": "df3c01546eedc76e546ee61034929739a9c6feeaf9b77712a0f84dddb5508384",
    "src/dataprep/compute_gamma_aec.py": "9a45058558b2aaa314bd18a6f52acd4bba87093bcedbe7579da38bbe982136c1",
    "src/evaluation_protocol.py": "7caacac9b31bd0f7809656940e46a7d0d68d0e13f8dadfe50f3113906e5732dc",
    "src/szcore_eval.py": "9cad5a6c9322c328b0ecb25cb6249e0d1f04da774097e0de3d1b3b8541e75f0f",
    "src/r2_core.py": "902d15ad4feb3e8ab76a7a3d3e818c37269811c537cf2b33b23b5a3f7d1850fd",
    "src/r2_rb.py": "00d2c322b1c7669a381d7050455e41329c8cf03b6c9e2a4f6eff61b60e688a84",
}
MODULE_FILES = {"preprocessing": "src/dataprep/preprocessing.py", "continuous_eval": "src/continuous_eval.py",
                "c1b_build_trainset": "src/c1b_build_trainset.py", "graph_construction": "src/dataprep/graph_construction.py",
                "feature_extraction": "src/dataprep/feature_extraction.py",
                "compute_gamma_aec": "src/dataprep/compute_gamma_aec.py", "evaluation_protocol": "src/evaluation_protocol.py",
                "szcore_eval": "src/szcore_eval.py", "r2_core": "src/r2_core.py", "r2_rb": "src/r2_rb.py"}

STATE = dict(mode=None, gates=[], versions_diff=None)
log = R0.log
sha256_file = R0.sha256_file
_jdump = R0._jdump


def out_dir():
    return R0.out_dir()


def gate(rec):
    """record a gate in gates.json; STOP (SystemExit) unless PASS."""
    STATE["gates"].append(rec)
    _jdump(out_dir() / "gates.json", dict(mode=STATE["mode"], versions_diff=STATE["versions_diff"], gates=STATE["gates"]))
    log(f"{rec['gate']}: {rec['status']}" + (f" ({rec.get('summary')})" if rec.get("summary") else ""))
    if rec["status"] != "PASS":
        raise SystemExit(f"{rec['gate']} {rec['status']}: "
                         f"{R0.jdumps({k: v for k, v in rec.items() if k != 'detail'})[:2000]}")


def _test_overrides():
    """synthetic test only: the referential files of the synthetic world (r2_rb identifies the files by sha256)."""
    if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_RB_REFERENTIAL"):
        RB.REFERENTIAL.clear()
        RB.REFERENTIAL.update(json.loads(os.environ["R2_TEST_RB_REFERENTIAL"]))


def inventory():
    inv = pd.read_csv(R0_OUT / "chb" / "inventory.csv")
    return inv[inv.case == CASE].copy()


# ============================================================================ start: run metadata, G-code, mode
def start(notebook, repo_commit):
    _test_overrides()
    meta = R0.run_meta(TAG, notebook, repo_commit)
    me = Path(__file__).read_bytes()
    R0.STATE["notes"].append(dict(r2_rb1_sha256=hashlib.sha256(me).hexdigest()))
    gate_code()
    check_mode(meta)
    return meta


def gate_code():
    import importlib
    det, bad = {}, []
    for rel, want in CODE_SHA.items():
        got = sha256_file(R0.REPO / rel)
        det[rel] = dict(sha256=got, expected=want, ok=got == want)
        if got != want:
            bad.append(f"{rel} differs")
    for mod, rel in MODULE_FILES.items():
        m = importlib.import_module(mod)
        p = Path(m.__file__).resolve()
        ok = p == (R0.REPO / rel).resolve()
        det[f"import {mod}"] = dict(file=str(p), ok=ok)
        if not ok:
            bad.append(f"{mod} imported from {p}, not the pinned repository")
    inv = inventory().set_index("file")
    for f in NEW:
        ok = RB.REFERENTIAL.get(f) == inv.loc[f, "sha256_physionet"]
        det[f"r2_rb.REFERENTIAL {f}"] = dict(ok=ok)
        if not ok:
            bad.append(f"r2_rb.REFERENTIAL[{f}] != inventory sha256")
    summ = R0.REPO / "data" / "summaries" / f"{CASE}-summary.txt"
    ok = sha256_file(summ) == inv.loc[f"{CASE}-summary.txt", "sha256_physionet"]
    det["committed summary = PhysioNet"] = dict(ok=ok)
    if not ok:
        bad.append("committed chb12 summary != PhysioNet sha256")
    gate(dict(gate="G-code", status="PASS" if not bad else "FAIL", bad=bad, detail=det,
              summary=f"{len(CODE_SHA)} files byte-equal to R0's, imports from the pinned clone" if not bad else "; ".join(bad)))


def check_mode(meta):
    r0v = json.loads((R0_OUT / "chb" / "run_meta.json").read_text())["versions"]
    diff = {k: (r0v.get(k), meta["versions"].get(k)) for k in VERSION_KEYS if r0v.get(k) != meta["versions"].get(k)}
    STATE["mode"] = "exact" if not diff else "tolerance"
    STATE["versions_diff"] = diff
    R0.STATE["notes"].append(dict(versions_vs_r0=diff, mode=STATE["mode"]))
    log(f"versions vs R0_CHB: {'equal' if not diff else diff} -> mode {STATE['mode']}")
    _jdump(out_dir() / "gates.json", dict(mode=STATE["mode"], versions_diff=diff, gates=STATE["gates"]))
    return STATE["mode"]


# ============================================================================ G-raw, G-R0, views
def gate_raw(workers=8):
    t = time.time()
    inv = inventory()
    want = {r.file: r.sha256_physionet for r in inv.itertuples()}
    edfs = sorted(f for f in want if f.endswith(".edf"))
    hits = {f: [] for f in want}
    for p in sorted(R0.INPUT.rglob(f"{CASE}*")):                    # one walk of the inputs
        if p.name in hits and p.is_file() and R0.SCRATCH not in p.parents and R0.WORK not in p.parents:
            hits[p.name].append(p)
    flat = [p for v in hits.values() for p in v]
    with ThreadPoolExecutor(workers) as ex:
        hashed = dict(zip(flat, ex.map(sha256_file, flat)))
    use, det, bad = {}, {}, []
    for f, w in want.items():
        ok = [p for p in hits[f] if hashed[p] == w]
        det[f] = dict(copies=len(hits[f]), equal=len(ok))
        if ok:
            use[f] = ok[0]
        else:
            bad.append(f"{f}: {len(hits[f])} copies, none with the PhysioNet sha256")
    smap = _parse(R0.REPO / "data" / "summaries" / f"{CASE}-summary.txt")
    if sorted(smap) != edfs:
        bad.append(f"summary lists {sorted(set(smap) ^ set(edfs))} differently from the inventory")
    rec = dict(gate="G-raw", status="PASS" if not bad else "FAIL", files=len(want), edfs=len(edfs), bad=bad, detail=det,
               summary=f"{len(edfs)} EDFs + summary, sha256 = PhysioNet" if not bad else f"{len(bad)} problems")
    R0.STATE["rates"]["raw_hash_MB_per_s"] = round(sum(p.stat().st_size for p in flat) / 1e6 / max(time.time() - t, 1e-9), 1)
    R0.phase("gate_raw", t)
    gate(rec)
    return use, edfs


def _r0_paths():
    out = {}
    for c in R0.CHB_CASES:
        for name in (f"{c}.npz", f"{c}_stats.json"):
            hits = [p for p in sorted(R0.INPUT.rglob(name)) if DS_NAME in p.parts and "r0_jobs" not in p.parts
                    and "stats_earlier" not in p.parts and R0.SCRATCH not in p.parents and R0.WORK not in p.parents]
            if not hits:
                raise SystemExit(f"STOP G-R0: {DS_NAME}/{name} not found under {R0.INPUT} (attach the R0 dataset)")
            if len({h.stat().st_size for h in hits}) != 1:
                raise SystemExit(f"STOP G-R0: copies of {name} differ in size: {hits}")
            out[name] = hits[0]
    return out


def gate_r0(workers=8):
    t = time.time()
    paths = _r0_paths()
    with ThreadPoolExecutor(workers) as ex:
        got = dict(zip(paths, ex.map(sha256_file, paths.values())))
    pin = pd.read_csv(PIN)
    pv = pin[pin.dataset == DS_NAME].set_index("file").sha256.to_dict()
    differ = sorted(n for n in set(pv) | set(got) if pv.get(n) != got.get(n))
    inv_ds = [p for p in sorted(R0.INPUT.rglob("inventory.csv")) if DS_NAME in p.parts and R0.SCRATCH not in p.parents
              and R0.WORK not in p.parents]
    rec = dict(gate="G-R0", status="PASS" if not differ else "FAIL", files=len(got), pinned=len(pv), differ=differ,
               pin=str(PIN.relative_to(R0.REPO)),
               summary=f"{len(got)} R0 dataset files = pinned R1_SMOKE hashes" if not differ else f"{len(differ)} differ")
    R0.phase("gate_r0", t)
    gate(rec)
    return paths, (inv_ds[0] if inv_ds else None)


def build_views(raw):
    """SCRATCH/rb1_view/{v21,v24}/chbmit/chb12/ -> verified files (symlinks)."""
    root = R0.SCRATCH / "rb1_view"
    shutil.rmtree(root, ignore_errors=True)
    views = {}
    for kind in ("v21", "v24"):
        d = root / kind / "chbmit" / CASE
        d.mkdir(parents=True)
        for f, p in raw.items():
            if kind == "v21" and f in NEW:
                continue
            os.symlink(p, d / f)
        views[kind] = str(root / kind)
    return views


# ============================================================================ jobs A and B (workers)
def rb_job(a):
    """one build with the wrapper installed IN this process (does not rely on fork)."""
    kind, view, scratch_out, logs, env = a
    os.environ.update(env)
    _test_overrides()
    t = time.time()
    res = dict(kind=kind)
    try:
        RB.install()
        if not RB.installed():
            raise SystemExit("STOP: wrapper not installed in the worker")
        st = R0.stats_record(CASE, view, Path(logs) / f"{CASE}_{kind}_stats.log")
        res["stats"] = st
        res["stats_s"] = round(time.time() - t, 1)
        t1 = time.time()
        npz = R0.features_record(CASE, view, st, Path(scratch_out) / kind, Path(logs) / f"{CASE}_{kind}_features.log")
        res["npz"] = str(npz)
        res["features_s"] = round(time.time() - t1, 1)
    except SystemExit as e:
        res["error"] = f"STOP: {e}"
    except Exception:                    # noqa: BLE001
        res["error"] = traceback.format_exc()[-3000:]
    res["wall_s"] = round(time.time() - t, 1)
    return res


def run_jobs(views, workers=2):
    t = time.time()
    env = {k: v for k, v in os.environ.items() if k.startswith("R2_")}
    logs = out_dir() / "logs"
    scratch_out = R0.SCRATCH / "rb1_build"
    shutil.rmtree(scratch_out, ignore_errors=True)
    args = [("B", views["v24"], str(scratch_out), str(logs), env), ("A", views["v21"], str(scratch_out), str(logs), env)]
    done = {}
    with Pool(min(workers, 2), maxtasksperchild=1) as pool:
        for res in pool.imap_unordered(rb_job, args):
            done[res["kind"]] = res
            log(f"job {res['kind']}: {'ERROR' if res.get('error') else 'built'} in {res['wall_s']:.0f} s")
            if res.get("error"):
                pool.terminate()
                gate(dict(gate=f"Job {res['kind']}", status="FAIL", error=res["error"], summary="build error"))
    sd = out_dir() / "stats"
    sd.mkdir(parents=True, exist_ok=True)
    _jdump(sd / "chb12_stats_jobA_21files.json", done["A"]["stats"])
    _jdump(sd / "chb12_stats.json", done["B"]["stats"])
    R0.STATE["rates"]["jobs_s"] = {k: dict(wall_s=v["wall_s"], stats_s=v["stats_s"], features_s=v["features_s"])
                                   for k, v in done.items()}
    R0.phase("jobs", t)
    return done


# ============================================================================ gates on the builds
def _parse(summary):
    """the stats parser (preprocessing.parse_summary) -> {file: [(on, off)]}."""
    import preprocessing as P
    return {f: [tuple(map(int, s)) for s in v] for f, v in P.parse_summary(summary).items()}


def _parse_c1b(summary):
    """the feature parser (evaluation_protocol.parse_summary_edf_list, what continuous_eval.list_files reads)."""
    import evaluation_protocol as E
    return {e["fname"]: [tuple(map(int, s)) for s in e["seizures"]] for e in E.parse_summary_edf_list(summary)}


def expected_labels(n, seizures):
    """independent of the record code: window w is ictal iff [4w, 4w+4) meets a seizure [on, off) clipped to the file;
    buffered iff it meets [off, off + 4 h) of a seizure (clipped to the file)."""
    secs = n * 4
    ict = np.zeros(n, bool)
    buf = np.zeros(n, bool)
    w0 = np.arange(n) * 4
    for on, off in seizures:
        a, b = max(0, on), min(secs, off)
        if b > a:
            ict |= (w0 < b) & (w0 + 4 > a)
        a, b = off, min(secs, off + BUF_S)
        if b > a:
            buf |= (w0 < b) & (w0 + 4 > a)
    return ict, buf


def _per_file(z):
    files = [str(x) for x in z["files"]]
    fi = np.asarray(z["file_idx"]).astype(int)
    return files, {f: np.flatnonzero(fi == i) for i, f in enumerate(files)}


def _count_identity(st, z):
    ict = np.asarray(z["is_ictal"], bool)
    buf = np.asarray(z["is_buffer"], bool)
    return dict(n_ictal=[int(st["n_ictal"]), int(ict.sum())],
                inter_plus_rejected=[int(st["n_interictal"]) + int(st["n_rejected"]), int((~ict & ~buf).sum())])


def gate_A(done, r0_paths):
    """Job A = R0's chb12 (stats and features); allowed difference: skipped_files."""
    t = time.time()
    stA = done["A"]["stats"]
    ref_st = json.loads((R0_OUT / "chb" / "stats_earlier" / f"{CASE}_stats.json").read_text())
    cs = R0.compare_stats(stA, ref_st)
    if STATE["mode"] == "exact":
        st_ok = all(cs[f"{k}_max_rel"] == 0.0 for k in R0.STATS_FLOAT_KEYS) and cs["status"] == "PASS"
    else:
        st_ok = cs["status"] == "PASS"
    N = np.load(done["A"]["npz"], allow_pickle=True)
    Rz = np.load(r0_paths[f"{CASE}.npz"], allow_pickle=True)
    det = dict(stats=cs, stats_ok=st_ok)
    ok = st_ok
    nf, rf = [str(x) for x in N["files"]], [str(x) for x in Rz["files"]]
    det["files_equal"] = nf == rf
    det["skipped_new"] = [str(x) for x in N["skipped_files"]]
    det["skipped_reference"] = [str(x) for x in Rz["skipped_files"]] if "skipped_files" in Rz.files else None
    det["skipped_as_expected"] = det["skipped_new"] == [] and det["skipped_reference"] == NEW
    det["keys_equal"] = sorted(N.files) == sorted(Rz.files)
    ok &= det["files_equal"] and det["skipped_as_expected"] and det["keys_equal"]
    if ok:
        n_ok = len(N["file_idx"]) == len(Rz["file_idx"])
        det["n_windows"] = [int(len(N["file_idx"])), int(len(Rz["file_idx"]))]
        ok &= n_ok
    if ok:
        for k in R0.FLAGS + ("file_idx",):
            eq = bool(np.array_equal(np.asarray(N[k]), np.asarray(Rz[k])))
            det[f"{k}_equal"] = eq
            ok &= eq
    if ok:
        W = R0.window_diffs(N, Rz, np.ones(len(Rz["file_idx"]), bool))
        sl = np.asarray(N["is_signal_loss"], bool)
        det["chain"] = R0.feat_block(W, ~sl)
        det["all_windows"] = R0.feat_block(W, np.ones(len(sl), bool))
        if STATE["mode"] == "exact":
            bit = {}
            for k in sorted(set(N.files) - {"files", "skipped_files"}):
                a, b = np.asarray(N[k]), np.asarray(Rz[k])
                bit[k] = bool(a.dtype == b.dtype and np.array_equal(a, b, equal_nan=a.dtype.kind == "f"))
            det["bit_equal"] = bit
            ok &= all(bit.values())
        else:
            ok &= det["chain"]["status"] == "PASS"
    det["count_identity_A"] = _count_identity(stA, N)
    ok &= all(v[0] == v[1] for v in det["count_identity_A"].values())
    R0.phase("gate_A", t)
    gate(dict(gate="Job A = R0 (wrapper + 21 bipolar files)", status="PASS" if ok else "FAIL", mode=STATE["mode"],
              detail=det, summary=(f"mode {STATE['mode']}: stats and every array equal to R0's chb12; skipped_files [] vs "
                                   f"the three referential files (expected)") if ok else "differs from R0"))
    return N


def gate_B(done, raw_edfs, A):
    t = time.time()
    stB, stA = done["B"]["stats"], done["A"]["stats"]
    B = np.load(done["B"]["npz"], allow_pickle=True)
    inv = inventory().set_index("file")
    summ = R0.REPO / "data" / "summaries" / f"{CASE}-summary.txt"
    sm, sm2 = _parse(summ), _parse_c1b(summ)
    det, bad = {}, []
    files, idx = _per_file(B)
    if files != sorted(raw_edfs):
        bad.append(f"files {files} != the 24 summary-listed files in order")
    if [str(x) for x in B["skipped_files"]]:
        bad.append(f"skipped {list(B['skipped_files'])}")
    det["parsers_agree"] = {f: sm.get(f, []) == sm2.get(f, []) for f in sorted(raw_edfs)}
    if not all(det["parsers_agree"].values()):
        bad.append("the two record parsers disagree on some file")
    det["seizures_new"] = {f: len(sm.get(f, [])) for f in NEW}
    if det["seizures_new"] != EXPECT_SEIZURES:
        bad.append(f"seizures in the new files {det['seizures_new']} != {EXPECT_SEIZURES}")
    ict, buf, sl = (np.asarray(B[k], bool) for k in ("is_ictal", "is_buffer", "is_signal_loss"))
    per = {}
    Afiles, Aidx = _per_file(A)
    for f in files:
        ix = idx.get(f, np.array([], int))
        n_hdr = int(inv.loc[f, "n_times"]) // WIN if f in inv.index else None
        ei, eb = expected_labels(len(ix), sm.get(f, []))
        row = dict(windows=int(len(ix)), windows_header=n_hdr, ictal=int(ict[ix].sum()), buffer=int(buf[ix].sum()),
                   signal_loss=int(sl[ix].sum()), ictal_expected_equal=bool(np.array_equal(ict[ix], ei)),
                   buffer_expected_equal=bool(np.array_equal(buf[ix], eb)))
        ok = row["windows"] == n_hdr and row["ictal_expected_equal"] and row["buffer_expected_equal"]
        if f in Aidx:
            ja = Aidx[f]
            row["equal_to_A"] = {k: bool(np.array_equal(np.asarray(B[k], bool)[ix], np.asarray(A[k], bool)[ja]))
                                 for k in ("is_ictal", "is_buffer", "is_signal_loss")}
            ok &= all(row["equal_to_A"].values())
        row["ok"] = bool(ok)
        per[f] = row
        if not ok:
            bad.append(f"{f}: {row}")
    det["per_file"] = per
    det["count_identity_B"] = _count_identity(stB, B)
    if not all(v[0] == v[1] for v in det["count_identity_B"].values()):
        bad.append(f"stats counts vs .npz labels: {det['count_identity_B']}")
    new_ix = np.concatenate([idx[f] for f in NEW]) if all(f in idx for f in NEW) else np.array([], int)
    det["ictal_new_files"] = int(ict[new_ix].sum())
    det["nonictal_nonbuffer_new_files"] = int((~ict & ~buf)[new_ix].sum())
    det["n_ictal_A_plus_new"] = [int(stB["n_ictal"]), int(stA["n_ictal"]) + det["ictal_new_files"]]
    det["inter_rej_A_plus_new"] = [int(stB["n_interictal"]) + int(stB["n_rejected"]),
                                   int(stA["n_interictal"]) + int(stA["n_rejected"]) + det["nonictal_nonbuffer_new_files"]]
    for k in ("n_ictal_A_plus_new", "inter_rej_A_plus_new"):
        if det[k][0] != det[k][1]:
            bad.append(f"{k}: {det[k]}")
    f7 = np.asarray(B["f7"])
    det["f7_finite_outside_signal_loss"] = bool(np.isfinite(f7[~sl]).all())
    if not det["f7_finite_outside_signal_loss"]:
        bad.append("non-finite f7 outside signal-loss windows")
    det["n_ref"] = [sum(len(v) for f, v in sm.items() if f not in NEW), sum(len(v) for v in sm.values())]
    R0.phase("gate_B", t)
    gate(dict(gate="Job B (wrapper + 24 files)", status="PASS" if not bad else "FAIL", bad=bad[:20], detail=det,
              summary=(f"{len(files)} files, seizures {det['seizures_new']}, labels = independent recomputation, "
                       f"21 common files = Job A, counts consistent; n_ref {det['n_ref'][0]} -> {det['n_ref'][1]}")
              if not bad else f"{len(bad)} problems"))
    return B


# ============================================================================ clipping (numpy EDF reader)
def edf_digital(path):
    """(labels, digital_min, digital_max, [int16 arrays]) of an EDF file, read from its bytes (EDF spec, Kemp 1992)."""
    path = Path(path)
    with open(path, "rb") as f:
        h = f.read(256)
        hdr_bytes = int(h[184:192].decode("ascii").strip())
        n_rec = int(h[236:244].decode("ascii").strip())
        ns = int(h[252:256].decode("ascii").strip())
        sh = f.read(ns * 256)
    if len(sh) != ns * 256 or hdr_bytes != 256 * (ns + 1):
        raise SystemExit(f"STOP G-clip: {path.name}: unexpected EDF header size")
    widths = [("label", 16), ("transducer", 80), ("dim", 8), ("pmin", 8), ("pmax", 8), ("dmin", 8), ("dmax", 8),
              ("prefilter", 80), ("spr", 8), ("reserved", 32)]
    fld, pos = {}, 0
    for name, w in widths:
        fld[name] = [sh[pos + i * w: pos + (i + 1) * w].decode("ascii", "replace").strip() for i in range(ns)]
        pos += ns * w
    spr = [int(x) for x in fld["spr"]]
    raw = np.fromfile(path, dtype="<i2", offset=hdr_bytes)
    rec = sum(spr)
    if n_rec < 0:
        n_rec = len(raw) // rec
    if len(raw) != n_rec * rec:
        raise SystemExit(f"STOP G-clip: {path.name}: data size {len(raw)} != {n_rec} records x {rec}")
    raw = raw.reshape(n_rec, rec)
    sig, o = [], 0
    for s in spr:
        sig.append(raw[:, o:o + s].reshape(-1))
        o += s
    return fld["label"], [int(x) for x in fld["dmin"]], [int(x) for x in fld["dmax"]], sig


def clip_file(path):
    """per-window clipping of one referential file: electrodes and derivations, plus the histogram tails."""
    labels, dmin, dmax, sig = edf_digital(path)
    idx = RB.match_electrodes(labels)
    els = RB.electrodes()
    n_s = min(len(sig[idx[e]]) for e in els)
    n = n_s // WIN
    clip = {e: (sig[idx[e]][:n_s] <= dmin[idx[e]]) | (sig[idx[e]][:n_s] >= dmax[idx[e]]) for e in els}
    any_c = np.zeros(n_s, bool)
    for v in clip.values():
        any_c |= v
    ch_rows, tails = [], []
    for e in els:
        i = idx[e]
        x = sig[i][:n_s]
        ch_rows.append(dict(file=path.name, channel=e, label=labels[i], digital_min=dmin[i], digital_max=dmax[i],
                            n_samples=int(x.size), clipped_samples=int(clip[e].sum())))
        lo, hi = np.percentile(x, [0.5, 99.5])
        tail = x[((x <= lo) | (x >= hi)) & (x > dmin[i]) & (x < dmax[i])]
        vals, cnt = np.unique(tail, return_counts=True)
        order = np.argsort(-cnt, kind="stable")[:3]
        tails.append(dict(file=path.name, electrode=e, at_digital_min=int((x <= dmin[i]).sum()),
                          at_digital_max=int((x >= dmax[i]).sum()), tail_samples_inside_limits=int(tail.size),
                          tail_distinct_values=int(vals.size),
                          **{f"top{k + 1}_value": (int(vals[j]) if k < len(order) else None) for k, j in
                             enumerate(list(order) + [None] * (3 - len(order)))},
                          **{f"top{k + 1}_count": (int(cnt[j]) if j is not None else None) for k, j in
                             enumerate(list(order) + [None] * (3 - len(order)))},
                          top1_share_of_tail=float(cnt[order[0]] / tail.size) if tail.size else None))
    dv_tot, dv_win = [], {}
    for a, b in RB.derivations():
        c = clip[a] | clip[b]
        dv_tot.append(dict(file=path.name, channel=f"{a}-{b}", affected_samples=int(c.sum())))
        dv_win[f"{a}-{b}"] = c[: n * WIN].reshape(n, WIN).sum(axis=1)
    aw = any_c[: n * WIN].reshape(n, WIN).sum(axis=1)
    return dict(file=path.name, n=n, n_samples=n_s, any_c=any_c, any_win=aw, dv_win=dv_win, ch_rows=ch_rows,
                dv_tot=dv_tot, tails=tails)


def clipping(raw, B):
    """per-window table of the three files joined to the rebuilt chb12 labels; G-clip vs RB0b; per seizure; classes."""
    t = time.time()
    files, idx = _per_file(B)
    sm = _parse(R0.REPO / "data" / "summaries" / f"{CASE}-summary.txt")
    labels = {k: np.asarray(B[k], bool) for k in R0.FLAGS}
    clean = R0._clean(B)
    win_rows, dv_rows, ch_rows, dv_tot, tails, file_rows, sz_rows = [], [], [], [], [], [], []
    for f in NEW:
        r = clip_file(raw[f])
        ix = idx[f]
        if len(ix) != r["n"]:
            gate(dict(gate="G-clip", status="FAIL", summary=f"{f}: {r['n']} windows read vs {len(ix)} in the build"))
        ch_rows += r["ch_rows"]
        dv_tot += r["dv_tot"]
        tails += r["tails"]
        file_rows.append(dict(file=f, windows=r["n"], windows_any_clipped=int((r["any_win"] > 0).sum())))
        dmat = np.stack([r["dv_win"][d] for d in r["dv_win"]], axis=1)          # [n, 18]
        for w in range(r["n"]):
            g = ix[w]
            win_rows.append(dict(file=f, window=w, start_s=4 * w, any_clipped_samples=int(r["any_win"][w]),
                                 any_clipped_share=float(r["any_win"][w] / WIN),
                                 derivations_affected=int((dmat[w] > 0).sum()),
                                 max_derivation_share=float(dmat[w].max() / WIN),
                                 is_ictal=bool(labels["is_ictal"][g]), is_buffer=bool(labels["is_buffer"][g]),
                                 is_flag5sd=bool(labels["is_flag5sd"][g]),
                                 is_signal_loss=bool(labels["is_signal_loss"][g]), clean=bool(clean[g])))
            for k, d in enumerate(r["dv_win"]):
                if dmat[w, k]:
                    dv_rows.append(dict(file=f, window=w, derivation=d, affected_samples=int(dmat[w, k])))
        for k, (on, off) in enumerate(sm.get(f, [])):
            a, b = on * 256, min(off * 256, r["n_samples"])
            seg = r["any_c"][a:b]
            wins = [w for w in range(r["n"]) if 4 * w < off and 4 * w + 4 > on]
            dshare = max((float((r["dv_win"][d][wins] if wins else np.zeros(1)).sum()) for d in r["dv_win"]), default=0.0)
            sz_rows.append(dict(file=f, seizure=k + 1, onset_s=on, offset_s=off, samples=int(b - a),
                                any_clipped_samples=int(seg.sum()), any_clipped_share=float(seg.mean()) if seg.size else 0.0,
                                windows=len(wins), windows_any_clipped=int(sum(r["any_win"][w] > 0 for w in wins)),
                                max_derivation_affected_samples_in_windows=int(dshare)))
    od = out_dir()
    W = pd.DataFrame(win_rows)
    W.to_csv(od / "clipping_windows.csv", index=False)
    pd.DataFrame(dv_rows, columns=["file", "window", "derivation", "affected_samples"]).to_csv(
        od / "clipping_windows_derivations.csv.gz", index=False)
    pd.DataFrame(sz_rows).to_csv(od / "clipping_seizures.csv", index=False)
    pd.DataFrame(tails).to_csv(od / "clipping_histogram_tails.csv", index=False)
    # G-clip: sums = RB0b's committed tables (pyedflib on the laptop)
    rc = pd.read_csv(RB0B / "C_clipping_channels.csv", dtype={"label": str, "channel": str})
    rd = pd.read_csv(RB0B / "C_clipping_derivations.csv")
    rf = pd.read_csv(RB0B / "C_clipping_files.csv")
    bad = []
    mine_c = pd.DataFrame(ch_rows).set_index(["file", "channel"])
    for r in rc[rc.file.isin(NEW)].itertuples():
        m = mine_c.loc[(r.file, r.channel)] if (r.file, r.channel) in mine_c.index else None
        if m is None or any(int(m[k]) != int(getattr(r, k)) for k in ("digital_min", "digital_max", "n_samples",
                                                                        "clipped_samples")) or str(m["label"]) != str(r.label):
            bad.append(f"electrode {r.file} {r.channel}")
    if len(mine_c) != int(rc.file.isin(NEW).sum()):
        bad.append(f"electrode rows {len(mine_c)} vs RB0b {int(rc.file.isin(NEW).sum())}")
    mine_d = pd.DataFrame(dv_tot).set_index(["file", "channel"]).affected_samples
    for r in rd[rd.file.isin(NEW)].itertuples():
        if int(mine_d.get((r.file, r.channel), -1)) != int(r.affected_samples):
            bad.append(f"derivation {r.file} {r.channel}")
    if len(mine_d) != int(rd.file.isin(NEW).sum()):
        bad.append("derivation row count")
    mine_f = {x["file"]: x for x in file_rows}
    for r in rf[rf.file.isin(NEW)].itertuples():
        x = mine_f.get(r.file)
        if x is None or x["windows"] != int(r.windows) or x["windows_any_clipped"] != int(r.windows_any_clipped):
            bad.append(f"file {r.file}")
    # classes
    cls = {}
    W["class"] = np.select([W.is_ictal, W.is_buffer, W.is_signal_loss, W.is_flag5sd], ["ictal", "buffer (non-ictal)",
                           "signal loss", "5-SD flagged"], "clean (training)")
    for c, g in W.groupby("class"):
        cls[c] = dict(windows=int(len(g)), windows_any_clipped=int((g.any_clipped_samples > 0).sum()))
    S = pd.DataFrame(sz_rows)
    summ = dict(files=file_rows, by_class=cls, seizures=int(len(S)),
                seizures_with_clipped_samples=int((S.any_clipped_samples > 0).sum()) if len(S) else 0,
                clean_windows_with_clipped_samples=cls.get("clean (training)", {}).get("windows_any_clipped", 0),
                histogram_tail_max_top1_share=float(pd.DataFrame(tails).top1_share_of_tail.max()))
    _jdump(od / "clipping_summary.json", summ)
    R0.phase("clipping", t)
    gate(dict(gate="G-clip", status="PASS" if not bad else "FAIL", bad=bad[:30],
              summary=(f"per electrode, per derivation and per file = RB0b's tables; {summ['seizures_with_clipped_samples']} "
                       f"of {summ['seizures']} seizures and {summ['clean_windows_with_clipped_samples']} clean windows hold "
                       f"clipped samples") if not bad else f"{len(bad)} differ from RB0b"))
    return summ


# ============================================================================ descriptive diff
def diff_report(done, A, B):
    stA, stB = done["A"]["stats"], done["B"]["stats"]
    af, aidx = _per_file(A)
    bf, bidx = _per_file(B)
    sm = _parse(R0.REPO / "data" / "summaries" / f"{CASE}-summary.txt")
    added = [f for f in bf if f not in af]
    common = [f for f in bf if f in af]
    ixc_B = np.concatenate([bidx[f] for f in common])
    ixc_A = np.concatenate([aidx[f] for f in common])
    ix_new = np.concatenate([bidx[f] for f in added])
    cA, cB = R0._clean(A), R0._clean(B)
    sd_e = np.asarray(stA["ch_std_uV"], float)
    rel = {"ch_mean_uV (change / earlier SD)": (np.asarray(stB["ch_mean_uV"], float) - np.asarray(stA["ch_mean_uV"], float)) / sd_e}
    rel.update({f"{k} (relative change)": (np.asarray(stB[k], float) - np.asarray(stA[k], float)) / np.asarray(stA[k], float)
                for k in ("ch_std_uV", "artifact_thresh_uV")})
    flags = lambda z, ix: int(np.asarray(z["is_flag5sd"], bool)[ix].sum())        # noqa: E731
    d = dict(files_earlier=len(af), files_complete=len(bf), files_added=added,
             windows_added={f: int(len(bidx[f])) for f in added}, windows_earlier=int(len(A["file_idx"])),
             windows_complete=int(len(B["file_idx"])), hours_added=round(len(ix_new) * 4 / 3600, 4),
             hours_earlier=round(len(A["file_idx"]) * 4 / 3600, 4), hours_complete=round(len(B["file_idx"]) * 4 / 3600, 4),
             ictal_windows=[int(np.asarray(A["is_ictal"]).sum()), int(np.asarray(B["is_ictal"]).sum())],
             seizure_windows_in_added_files=int(np.asarray(B["is_ictal"], bool)[ix_new].sum()),
             seizure_windows_identical_in_common_files=bool(np.array_equal(np.asarray(A["is_ictal"])[ixc_A],
                                                                          np.asarray(B["is_ictal"])[ixc_B])),
             seizures=[sum(len(sm.get(f, [])) for f in af), sum(len(sm.get(f, [])) for f in bf)],
             seizures_added={f: len(sm.get(f, [])) for f in added},
             clean_windows=[int(cA.sum()), int(cB.sum())], clean_windows_in_added_files=int(cB[ix_new].sum()),
             clean_windows_in_common_files=[int(cA[ixc_A].sum()), int(cB[ixc_B].sum())],
             flag5sd_windows=[int(np.asarray(A["is_flag5sd"]).sum()), int(np.asarray(B["is_flag5sd"]).sum())],
             flag5sd_in_common_files=[flags(A, ixc_A), flags(B, ixc_B)], flag5sd_in_added_files=flags(B, ix_new),
             nonictal_nonbuffer_in_added_files=int((~np.asarray(B["is_ictal"], bool) & ~np.asarray(B["is_buffer"], bool))[ix_new].sum()),
             signal_loss_windows=[int(np.asarray(A["is_signal_loss"]).sum()), int(np.asarray(B["is_signal_loss"]).sum())],
             signal_loss_in_added_files=int(np.asarray(B["is_signal_loss"], bool)[ix_new].sum()),
             counts_earlier={k: stA[k] for k in R0.STATS_INT_KEYS}, counts_complete={k: stB[k] for k in R0.STATS_INT_KEYS},
             stats_rel_change={k: dict(min=float(v.min()), median=float(np.median(v)), max=float(v.max()),
                                       per_channel=[float(x) for x in v]) for k, v in rel.items()})
    L = ["# RB1 -- chb12 with chb12_27-29 (converted as SzCORE) vs the earlier 21-file build\n",
         "Generated by `src/r2_rb1.py` (`diff_report`); descriptive, no rule. 'earlier' = Job A = R0's chb12 (gate).\n",
         f"- files: {d['files_earlier']} -> {d['files_complete']}; added {added}",
         f"- windows: {d['windows_earlier']} -> {d['windows_complete']} (+{d['hours_added']} h: {d['windows_added']})",
         f"- seizures (summary): {d['seizures'][0]} -> {d['seizures'][1]} ({d['seizures_added']})",
         f"- ictal windows: {d['ictal_windows'][0]} -> {d['ictal_windows'][1]}; in the added files "
         f"{d['seizure_windows_in_added_files']}; identical in the common files: {d['seizure_windows_identical_in_common_files']}",
         f"- clean training windows: {d['clean_windows'][0]} -> {d['clean_windows'][1]} (added files {d['clean_windows_in_added_files']}; "
         f"common files {d['clean_windows_in_common_files'][0]} -> {d['clean_windows_in_common_files'][1]})",
         f"- 5-SD flagged windows: {d['flag5sd_windows'][0]} -> {d['flag5sd_windows'][1]} (common files "
         f"{d['flag5sd_in_common_files'][0]} -> {d['flag5sd_in_common_files'][1]}; added files {d['flag5sd_in_added_files']} of "
         f"{d['nonictal_nonbuffer_in_added_files']} non-ictal, non-buffer windows)",
         f"- signal-loss windows: {d['signal_loss_windows'][0]} -> {d['signal_loss_windows'][1]} (added files {d['signal_loss_in_added_files']})",
         f"- stats.json counts {d['counts_earlier']} -> {d['counts_complete']}",
         "- change of the z-score statistics and 5-SD thresholds over the 18 channels:", "",
         "| value | min | median | max |", "|---|---|---|---|"]
    L += [f"| {k} | {v['min']:+.4%} | {v['median']:+.4%} | {v['max']:+.4%} |" for k, v in d["stats_rel_change"].items()]
    _jdump(out_dir() / "diff_chb12.json", {CASE: d})
    (out_dir() / "diff_chb12.md").write_text("\n".join(L) + "\n")
    log("diff_chb12:", R0.jdumps({k: d[k] for k in ("files_added", "hours_added", "seizures", "clean_windows",
                                                    "flag5sd_windows")}))
    return d


# ============================================================================ dataset + pin
def build_dataset(done, r0_paths, r0_inventory, copy=shutil.copyfile):
    """dataset folder: 23 cases copied from R0 (sha256 = pin after the copy), chb12 new; new pin."""
    t = time.time()
    tmp = R0.WORK / ".rb1_dataset_partial"
    shutil.rmtree(tmp, ignore_errors=True)
    tmp.mkdir(parents=True)
    pin = pd.read_csv(PIN)
    pv = pin[pin.dataset == DS_NAME].set_index("file").sha256.to_dict()
    bad, rows_new = [], {}
    for c in R0.CHB_CASES:
        if c == CASE:
            continue
        for name in (f"{c}.npz", f"{c}_stats.json"):
            copy(r0_paths[name], tmp / name)
            h = sha256_file(tmp / name)
            if h != pv.get(name):
                bad.append(f"{name}: copy sha256 {h[:12]} != pin")
    shutil.copyfile(done["B"]["npz"], tmp / f"{CASE}.npz")
    _jdump(tmp / f"{CASE}_stats.json", done["B"]["stats"])
    for name in (f"{CASE}.npz", f"{CASE}_stats.json"):
        rows_new[name] = dict(bytes=(tmp / name).stat().st_size, sha256=sha256_file(tmp / name))
    if r0_inventory is not None:
        shutil.copyfile(r0_inventory, tmp / "inventory.csv")
    (tmp / "RB1_NOTE.md").write_text(
        "# thesis-r2-chbmit-features-rb\n\n"
        "= thesis-r2-chbmit-features (R0) with chb12 rebuilt on all 24 of its files: chb12_27, chb12_28, chb12_29 are\n"
        "recorded with referential electrodes and are converted to the 18 bipolar derivations by subtraction, exactly as\n"
        "SzCORE's CHB-MIT converter does (esl-epfl/epilepsy2bids, commit d3fb175). The 23 other cases are byte copies of R0.\n"
        "inventory.csv is R0's (it still lists the three files as skipped by design; this note supersedes that column).\n"
        "Built by src/r2_rb1.py (github.com/Nhanvas/Thesis); gates in results/r2/r0_data/chb12_ref/rb1/gates.json.\n"
        "Sources: CHB-MIT Scalp EEG Database (PhysioNet, DOI 10.13026/C2K01R, Open Data Commons Attribution License v1.0).\n")
    rec = dict(gate="G-copy", status="PASS" if not bad else "FAIL", bad=bad, copied=2 * (len(R0.CHB_CASES) - 1),
               chb12=rows_new, summary=f"{2 * (len(R0.CHB_CASES) - 1)} files copied, sha256 = pin" if not bad else f"{len(bad)} differ")
    if bad:
        shutil.rmtree(tmp, ignore_errors=True)
        gate(rec)
    new_pin = pin.copy()
    for name, r in rows_new.items():
        m = (new_pin.dataset == DS_NAME) & (new_pin.file == name)
        if int(m.sum()) != 1:
            raise SystemExit(f"STOP G-copy: pin row {name} not found exactly once")
        new_pin.loc[m, "bytes"] = r["bytes"]
        new_pin.loc[m, "sha256"] = r["sha256"]
        new_pin.loc[m, "source"] = f"RB1_DATA build ({DS_RB.name}/{name})"
    new_pin.to_csv(out_dir() / "data_sha256.csv", index=False)
    if DS_RB.exists():
        shutil.rmtree(DS_RB)
    tmp.replace(DS_RB)
    R0.phase("dataset", t)
    gate(rec)
    return new_pin


def summary_md(diff, clip):
    g = json.loads((out_dir() / "gates.json").read_text())
    L = ["# RB1_DATA -- summary\n", f"mode: **{g['mode']}** (versions vs R0_CHB: {g['versions_diff'] or 'equal'})\n",
         "| gate | status | summary |", "|---|---|---|"]
    L += [f"| {x['gate']} | {x['status']} | {x.get('summary', '')} |" for x in g["gates"]]
    L += ["", "See `diff_chb12.md` for the data change.", "",
          f"Clipping (descriptive): {clip['seizures_with_clipped_samples']} of {clip['seizures']} seizures and "
          f"{clip['clean_windows_with_clipped_samples']} clean (training) windows hold clipped samples; by class: "
          f"{R0.jdumps(clip['by_class'])}"]
    (out_dir() / "SUMMARY.md").write_text("\n".join(L) + "\n")
