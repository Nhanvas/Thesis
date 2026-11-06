#!/usr/bin/env python
"""
r2_core.py -- independent research track, stage R0: data rebuild on complete data (docs/FUTURE_RESEARCH_PLAN.md rev 2,
§1, §3, §4, §9, §12). Kaggle CPU. Frozen and closed modules are imported READ ONLY and called unchanged; this file only
points their path globals at a verified copy of the raw data (inside its own worker process) and compares outputs.

Record code called verbatim (never re-implemented):
  dataprep/preprocessing.py   parse_summary, compute_subject_stats, count_windows, ARTIFACT_SD_MULTIPLIER, open_edf
                              (the stats.json of data/processed/ = process_subject without its write pass)
  c1b_build_trainset.build    thesis-convention features of chb01-chb23 (the call c1t_build_testset makes for test cases)
  v9_x3_build_chb24.build     thesis-convention features of chb24 (its own file-list and summary quirks)
  x1_external.build_subject   x1-convention (label-free statistics) features of chb24 + Siena; seizure lists of Siena
                              through its vendored SzCORE converter

R0.1 inventory     every EDF and summary of CHB-MIT 1.0.0 and Siena Scalp EEG 1.0.0 listed in PhysioNet's SHA256SUMS.txt
                   (downloaded in the session): Kaggle copy hashed (sha256); absent or different -> downloaded from
                   PhysioNet and hashed the same way; still unverifiable -> STOP. Two read-only views of symlinks under
                   the scratch folder: 'complete' (every verified file) and 'earlier' (complete minus the five files of
                   plan §1: chb11_12-15, chb21_11), so the record code sees exactly the earlier or the complete copy.
R0.2 gates (STOP)  G-stats: stats on the earlier view = committed data/processed/{case}_stats.json (23 cases; float values
                   relative <= 1e-6, window counts exact). G-feat: features on the earlier view with those stats = the
                   earlier .npz of v9-x3-fold1/3 (24 cases; flags and file_idx exact, files exact, f7 and bp5 max |diff|
                   <= 1e-3, adjacency entries differing by > 1e-3 <= 0.5 %).
R0.3 complete      chb11 and chb21 on every file: stats, then features; diff report vs the earlier copy.
R0.4 external      chb24 + Siena (14) with x1_external.build_subject (label-free statistics); feature identity is proven
                   downstream by gate GE (plan §5).
Outputs (WORK = /kaggle/working):
  WORK/thesis-r2-chbmit-features/   {case}.npz + {case}_stats.json + inventory.csv     (24 cases; dataset)
  WORK/thesis-r2-external-features/ {case}_lf.npz + inventory.csv                       (chb24 + Siena 14; dataset)
  WORK/r2/r0_data/<tag>/            inventory.csv, inventory_cases.csv, checks.json, gates.json, diff_chb11_chb21.md,
                                    stats_earlier/, run_meta.json, projection.json (smoke), logs/
Views, downloads and intermediate builds live in SCRATCH (/tmp/r2), never in WORK (symlinks there would be copied
into the notebook output).
Test mode (synthetic data in the build container only): environment R2_TEST_* (see src/r2_synthetic_test.py).
"""
import contextlib
import hashlib
import json
import os
import platform
import re
import resource
import shutil
import sys
import time
import traceback
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from multiprocessing import Pool
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
for _p in ("src", "src/dataprep", "src/retrain", "src/phaseB", "src/phaseC"):
    if str(REPO / _p) not in sys.path:
        sys.path.insert(0, str(REPO / _p))

WORK = Path(os.environ.get("R2_WORK", "/kaggle/working"))
INPUT = Path(os.environ.get("R2_INPUT", "/kaggle/input"))
SCRATCH = Path(os.environ.get("R2_SCRATCH", "/tmp/r2"))
DS_CHB = WORK / "thesis-r2-chbmit-features"
DS_EXT = WORK / "thesis-r2-external-features"
R0 = WORK / "r2" / "r0_data"

PHYSIONET = {"chbmit": os.environ.get("R2_PHYSIONET_CHBMIT", "https://physionet.org/files/chbmit/1.0.0/"),
             "siena": os.environ.get("R2_PHYSIONET_SIENA", "https://physionet.org/files/siena-scalp-eeg/1.0.0/")}
CHB_CASES = [f"chb{i:02d}" for i in range(1, 25)]
THESIS_23 = CHB_CASES[:23]
EARLIER_MISSING = {"chb11": ["chb11_12.edf", "chb11_13.edf", "chb11_14.edf", "chb11_15.edf"], "chb21": ["chb21_11.edf"]}
if os.environ.get("R2_TEST") and os.environ.get("R2_TEST_EARLIER_MISSING"):        # synthetic test only
    EARLIER_MISSING = json.loads(os.environ["R2_TEST_EARLIER_MISSING"])
GAP_CASES = tuple(EARLIER_MISSING)
SKIPPED_BY_DESIGN = {"chb12": ["chb12_27.edf", "chb12_28.edf", "chb12_29.edf"]}
# expected from the record (plan §4, R0.1): checked and reported, never tuned
EXPECTED = dict(chb_seizures_listed=198, siena_seizures=47, siena_hours=141.0)
TOL = dict(stats_rel=1e-6, f7=1e-3, bp5=1e-3, adj_entry=1e-3, adj_frac=0.005)
FLAGS = ("is_ictal", "is_buffer", "is_flag5sd", "is_signal_loss")
STATS_FLOAT_KEYS = ("ch_mean_uV", "ch_std_uV", "artifact_thresh_uV")
STATS_INT_KEYS = ("n_interictal", "n_ictal", "n_rejected")
UA = "r2-data-rebuild/1.0 (research; python-urllib)"
SIENA_MAP = {"T3": "T7", "T4": "T8", "T5": "P7", "T6": "P8"}       # = x1_external.SIENA_MAP (header check only)

T0 = float(os.environ.get("R2_T0", time.time()))
STATE = dict(tag=None, phases={}, rates={}, notes=[])


def log(*a):
    print(time.strftime("%H:%M:%S"), f"[{(time.time() - T0) / 60:6.1f} min]", *a, flush=True)


def out_dir():
    d = R0 / STATE["tag"]
    d.mkdir(parents=True, exist_ok=True)
    return d


def _np_default(o):
    """numpy scalars / arrays -> plain JSON types (bug fix 06/11 D14-F: np.bool_ broke json.dumps in projection)."""
    if isinstance(o, np.bool_):
        return bool(o)
    if isinstance(o, np.integer):
        return int(o)
    if isinstance(o, np.floating):
        return float(o)
    if isinstance(o, np.ndarray):
        return o.tolist()
    return str(o)


def jdumps(obj, **kw):
    return json.dumps(obj, default=_np_default, **kw)


def _jdump(path, obj):
    tmp = Path(str(path) + ".tmp")
    tmp.write_text(jdumps(obj, indent=1))
    tmp.replace(path)


def phase(name, t_start):
    STATE["phases"][name] = round(time.time() - t_start, 1)
    log(f"phase {name}: {STATE['phases'][name]:.0f} s")


# ============================================================================ run metadata
def run_meta(tag, notebook, repo_commit):
    STATE["tag"] = tag
    import scipy
    import sklearn
    vers = dict(python=platform.python_version(), numpy=np.__version__, scipy=scipy.__version__,
                sklearn=sklearn.__version__, pandas=pd.__version__)
    for mod in ("mne", "torch"):
        try:
            vers[mod] = __import__(mod).__version__
        except Exception as e:          # noqa: BLE001
            vers[mod] = f"not importable: {e}"
    me = Path(__file__).read_bytes()
    meta = dict(notebook=notebook, tag=tag, repo_commit=repo_commit, r2_core_sha256=hashlib.sha256(me).hexdigest(),
                started=time.strftime("%Y-%m-%d %H:%M:%S %Z"), cpu_count=os.cpu_count(), platform=platform.platform(),
                versions=vers, input=str(INPUT), work=str(WORK), scratch=str(SCRATCH), test_mode=bool(os.environ.get("R2_TEST")))
    _jdump(out_dir() / "run_meta.json", meta)
    log("run_meta", jdumps({k: meta[k] for k in ("notebook", "repo_commit", "cpu_count", "versions")}))
    return meta


def finish_meta(extra=None):
    p = out_dir() / "run_meta.json"
    meta = json.loads(p.read_text())
    meta.update(finished=time.strftime("%Y-%m-%d %H:%M:%S %Z"), runtime_h=round((time.time() - T0) / 3600, 3),
                phases_s=STATE["phases"], rates=STATE["rates"], notes=STATE["notes"],
                peak_rss_children_mb=round(resource.getrusage(resource.RUSAGE_CHILDREN).ru_maxrss / 1024, 1),
                peak_rss_self_mb=round(resource.getrusage(resource.RUSAGE_SELF).ru_maxrss / 1024, 1))
    meta.update(extra or {})
    _jdump(p, meta)
    return meta


# ============================================================================ R0.1 inventory + sha256 vs PhysioNet
def sha256_file(path, chunk=8 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(chunk)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def _download(url, dest, tries=3):
    dest = Path(dest)
    dest.parent.mkdir(parents=True, exist_ok=True)
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=120) as r, open(str(dest) + ".part", "wb") as f:
                shutil.copyfileobj(r, f, 8 << 20)
            Path(str(dest) + ".part").replace(dest)
            return dest
        except Exception as e:          # noqa: BLE001
            last = e
            time.sleep(5 * (k + 1))
    raise SystemExit(f"STOP R0.1: cannot download {url} ({last}). Internet on? PhysioNet reachable?")


def fetch_sums(db):
    """PhysioNet SHA256SUMS.txt of the database version -> {relpath: sha256}; the text is kept in the outputs."""
    dest = out_dir() / f"physionet_SHA256SUMS_{db}.txt"
    _download(PHYSIONET[db] + "SHA256SUMS.txt", dest)
    sums = {}
    for line in dest.read_text().splitlines():
        parts = line.strip().split(maxsplit=1)
        if len(parts) != 2 or not re.fullmatch(r"[0-9a-fA-F]{64}", parts[0]):
            continue
        rel = parts[1].strip().lstrip("*")
        rel = rel[2:] if rel.startswith("./") else rel
        sums[rel] = parts[0].lower()
    if not sums:
        raise SystemExit(f"STOP R0.1: {db} SHA256SUMS.txt has no parsable line")
    return sums


def needed(db, sums, cases=None):
    """relpaths this stage needs: CHB-MIT EDFs + summaries of the cases; Siena EDFs + seizure lists."""
    out = []
    for rel in sorted(sums):
        top, name = rel.split("/")[0], rel.split("/")[-1]
        if db == "chbmit":
            ok = (name.endswith(".edf") or name.endswith("-summary.txt")) and re.fullmatch(r"chb\d\d", top)
        else:
            ok = (name.endswith(".edf") or name.startswith("Seizures-list-")) and re.fullmatch(r"PN\d\d", top)
        if ok and (cases is None or top in cases):
            out.append(rel)
    return out


def index_input(root):
    """basename -> [paths] of every EDF / summary / seizure list under the Kaggle inputs (any nesting)."""
    idx = {}
    for pat in ("*.edf", "*-summary.txt", "Seizures-list-*.txt"):
        for p in sorted(Path(root).rglob(pat)):
            if SCRATCH in p.parents or WORK in p.parents:
                continue
            idx.setdefault(p.name, []).append(p)
    return idx


def acquire(db, sums, rels, idx, workers=8):
    """every needed file -> a verified path. Kaggle copy first (first copy whose sha256 equals PhysioNet's); otherwise
    PhysioNet download into SCRATCH/fix, hashed again; still different -> STOP."""
    t = time.time()
    first = {rel: (idx.get(rel.split("/")[-1]) or [None])[0] for rel in rels}
    todo = [p for p in first.values() if p is not None]
    nbytes = sum(p.stat().st_size for p in todo)
    with ThreadPoolExecutor(workers) as ex:
        hashed = dict(zip(todo, ex.map(sha256_file, todo)))
    rows = []
    for rel in rels:
        name = rel.split("/")[-1]
        cands = idx.get(name, [])
        want = sums[rel]
        use, status, kaggle_eq = None, None, None
        for i, p in enumerate(cands):
            h = hashed[p] if i == 0 else sha256_file(p)
            if i == 0:
                kaggle_eq = h == want
            if h == want:
                use, status = p, "kaggle: sha256 equal"
                break
        if use is None:
            dest = SCRATCH / "fix" / db / rel
            _download(PHYSIONET[db] + rel, dest)
            h = sha256_file(dest)
            if h != want:
                raise SystemExit(f"STOP R0.1: {db}/{rel} downloaded from PhysioNet but sha256 {h[:12]} != {want[:12]}")
            use, status = dest, ("physionet: absent on Kaggle" if not cands else "physionet: Kaggle copy differs")
            nbytes += dest.stat().st_size
        rows.append(dict(db=db, relpath=rel, case=rel.split("/")[0], file=name, sha256_physionet=want,
                         kaggle_copies=len(cands), kaggle_sha_equal=kaggle_eq, source=status, path=str(use),
                         size_bytes=Path(use).stat().st_size))
    dt = time.time() - t
    STATE["rates"][f"hash_{db}_MB_per_s"] = round(nbytes / 1e6 / max(dt, 1e-9), 1)
    log(f"{db}: {len(rels)} files verified ({sum(r['source'].startswith('physionet') for r in rows)} from PhysioNet), "
        f"{nbytes / 1e9:.1f} GB in {dt:.0f} s")
    return rows


def build_views(rows):
    """SCRATCH/view/{complete,earlier}/{db}/{relpath} -> verified file (symlinks); earlier = complete minus plan §1."""
    missing = {f for fs in EARLIER_MISSING.values() for f in fs}
    for kind in ("complete", "earlier"):
        root = SCRATCH / "view" / kind
        for r in rows:
            if kind == "earlier" and (r["db"] != "chbmit" or r["file"] in missing):
                continue
            dst = root / r["db"] / r["relpath"]
            dst.parent.mkdir(parents=True, exist_ok=True)
            if dst.is_symlink() or dst.exists():
                dst.unlink()
            os.symlink(r["path"], dst)
    return SCRATCH / "view" / "complete", SCRATCH / "view" / "earlier"


def _header(path):
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose=False)
    return int(raw.n_times), float(raw.info["sfreq"]), list(raw.ch_names)


def _siena_ok(chs):
    """header-only form of x1_external.load_18's electrode check (descriptive, inventory only)."""
    import preprocessing as P
    names = {SIENA_MAP.get(c.upper().replace("EEG", "").strip().replace(" ", ""),
                           c.upper().replace("EEG", "").strip().replace(" ", "")) for c in chs}
    need = {e for c in P.COMMON_CHANNELS for e in c.split("-")}
    return need <= names


def inventory(dbs, cases=None, workers=8):
    """R0.1 for the given databases ({'chbmit': [cases] or None, 'siena': None}); writes inventory.csv,
    inventory_cases.csv, checks.json; builds the views. STOP only when a file cannot be verified or when one of the
    five files of plan §1 is not available."""
    import preprocessing as P
    t = time.time()
    idx = index_input(INPUT)
    log(f"Kaggle inputs: {sum(len(v) for v in idx.values())} EDF/summary/list files under {INPUT}")
    rows = []
    for db, cs in dbs.items():
        sums = fetch_sums(db)
        rels = needed(db, sums, cs)
        if not rels:
            raise SystemExit(f"STOP R0.1: no {db} file selected (cases {cs})")
        rows += acquire(db, sums, rels, idx, workers)
    complete, earlier = build_views(rows)
    inv = pd.DataFrame(rows)
    # headers, listing, design skips, seizures, hours (from the verified files)
    edf = inv[inv.file.str.endswith(".edf")].copy()
    with ThreadPoolExecutor(workers) as ex:
        hdr = list(ex.map(_header, edf.path))
    edf["n_times"] = [h[0] for h in hdr]
    edf["sfreq"] = [h[1] for h in hdr]
    edf["hours"] = edf.n_times / edf.sfreq / 3600
    edf["windows_4s"] = (edf.n_times // (edf.sfreq * 4)).astype(int)
    missing5 = {f for fs in EARLIER_MISSING.values() for f in fs}
    listed, nsz, design, earl = [], [], [], []
    smaps, siena_sz = {}, {}
    for r in edf.itertuples():
        if r.db == "chbmit":
            if r.case not in smaps:
                smaps[r.case] = P.parse_summary(complete / "chbmit" / r.case / f"{r.case}-summary.txt")
            listed.append(r.file in smaps[r.case])
            nsz.append(len(smaps[r.case].get(r.file, [])))
            design.append(P.open_edf(Path(r.path)) is None)
            earl.append(r.file not in missing5)
        else:
            if r.case not in siena_sz:
                import x1_external as X1
                files, _ = X1.siena_subject(complete / "siena", r.case)
                siena_sz[r.case] = {p.name: s for p, s in files}
            listed.append(None)
            nsz.append(len(siena_sz[r.case].get(r.file, [])))
            design.append(not _siena_ok(_header(r.path)[2]))
            earl.append(None)
    edf["listed_in_summary"], edf["seizures"], edf["skipped_by_design"], edf["in_earlier_set"] = listed, nsz, design, earl
    inv = inv.merge(edf[["relpath", "n_times", "sfreq", "hours", "windows_4s", "listed_in_summary", "seizures",
                         "skipped_by_design", "in_earlier_set"]], on="relpath", how="left")
    # committed summaries vs PhysioNet (23 cases)
    summ = []
    for r in inv[inv.file.str.endswith("-summary.txt")].itertuples():
        mine = REPO / "data" / "summaries" / r.file
        summ.append(None if not mine.exists() else sha256_file(mine) == r.sha256_physionet)
    inv.loc[inv.file.str.endswith("-summary.txt"), "committed_summary_equal"] = summ
    inv.drop(columns=["path"]).to_csv(out_dir() / "inventory.csv", index=False)
    # per case
    cs_rows = []
    for (db, case), g in inv[inv.file.str.endswith(".edf")].groupby(["db", "case"]):
        used = g[~g.skipped_by_design.astype(bool)]
        row = dict(db=db, case=case, files_physionet=len(g), files_on_kaggle=int((g.kaggle_copies > 0).sum()),
                   files_kaggle_sha_equal=int((g.kaggle_sha_equal == True).sum()),          # noqa: E712
                   files_from_physionet=int(g.source.str.startswith("physionet").sum()),
                   files_skipped_by_design=int(g.skipped_by_design.astype(bool).sum()),
                   seizures_listed=int(g.seizures.sum()), seizures_in_used_files=int(used.seizures.sum()),
                   hours=round(float(g.hours.sum()), 4), hours_used_windows=round(float(used.windows_4s.sum()) * 4 / 3600, 4))
        if db == "chbmit":
            row.update(files_listed_in_summary=int(g.listed_in_summary.astype(bool).sum()),
                       summary_entries=len(smaps[case]),
                       earlier_files=int(g.in_earlier_set.astype(bool).sum()),
                       earlier_hours_used_windows=round(float(used[used.in_earlier_set.astype(bool)].windows_4s.sum()) * 4 / 3600, 4))
        cs_rows.append(row)
    cases_df = pd.DataFrame(cs_rows)
    cases_df.to_csv(out_dir() / "inventory_cases.csv", index=False)
    # checks against the record (reported; only the five files are required)
    ch = cases_df[cases_df.db == "chbmit"]
    sn = cases_df[cases_df.db == "siena"]
    checks = []

    def chk(name, got, want, required=False):
        ok = (got == want) if not isinstance(want, float) else abs(float(got) - want) < 0.05
        checks.append(dict(check=name, got=got, expected=want, status="PASS" if ok else "DIFF", required=required))

    present = set(edf.file)
    need5 = [f for c, fs in EARLIER_MISSING.items() for f in fs if "chbmit" in dbs and (dbs["chbmit"] is None or c in dbs["chbmit"])]
    chk("five files of plan §1 present and verified", sorted(f for f in need5 if f in present), sorted(need5), True)
    if len(ch):
        if dbs.get("chbmit") is None:
            chk("CHB-MIT seizures listed, 24 cases", int(ch.seizures_listed.sum()), EXPECTED["chb_seizures_listed"])
        des = sorted(edf[(edf.db == "chbmit") & edf.skipped_by_design.astype(bool)].file)
        exp = sorted(f for c, fs in SKIPPED_BY_DESIGN.items() for f in fs if dbs["chbmit"] is None or c in dbs["chbmit"])
        chk("CHB-MIT files skipped by design (missing common channel)", des, exp)
        nl = ch[ch.case != "chb24"]
        chk("CHB-MIT chb01-23: every EDF listed in its summary", int((nl.files_physionet - nl.files_listed_in_summary).sum()), 0)
        cse = inv[inv.file.str.endswith("-summary.txt") & inv.committed_summary_equal.notna()]
        chk("committed data/summaries = PhysioNet summaries", int((cse.committed_summary_equal != True).sum()), 0)   # noqa: E712
    if len(sn):
        chk("Siena patients with all electrodes", int((sn.files_skipped_by_design < sn.files_physionet).sum()), 14)
        chk("Siena seizures (SzCORE converter)", int(sn.seizures_listed.sum()), EXPECTED["siena_seizures"])
        chk("Siena hours (4 s windows)", round(float(sn.hours_used_windows.sum()), 1), EXPECTED["siena_hours"])
    _jdump(out_dir() / "checks.json", checks)
    for c in checks:
        log(f"check {c['status']:4s} {c['check']}: {c['got']} (record {c['expected']})")
    bad = [c for c in checks if c["required"] and c["status"] != "PASS"]
    if bad:
        raise SystemExit(f"STOP R0.1: {bad}")
    phase("inventory", t)
    return inv, cases_df, complete, earlier


# ============================================================================ record code inside worker processes
@contextlib.contextmanager
def _captured(logfile):
    """stdout/stderr of the record code -> one log file per job (kept in the outputs)."""
    Path(logfile).parent.mkdir(parents=True, exist_ok=True)
    with open(logfile, "a") as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
        yield


def _limit_threads():
    try:
        from threadpoolctl import threadpool_limits
        threadpool_limits(1)
    except Exception:                    # noqa: BLE001
        pass


def summary_path(view_root, case):
    """the committed summary for chb01-chb23 (what continuous_eval.list_files reads); chb24 from the verified copy."""
    mine = REPO / "data" / "summaries" / f"{case}-summary.txt"
    return mine if mine.exists() else Path(view_root) / "chbmit" / case / f"{case}-summary.txt"


def stats_record(case, view_root, logfile):
    """preprocessing.process_subject without its write pass: compute_subject_stats -> 5 x SD -> count_windows;
    the dict has the keys of data/processed/{case}_stats.json (+ 'r2' provenance)."""
    import preprocessing as P
    _limit_threads()
    raw_dir = Path(view_root) / "chbmit"
    t = time.time()
    with _captured(logfile):
        smap = P.parse_summary(summary_path(view_root, case))
        ch_mean, ch_std = P.compute_subject_stats(case, raw_dir, smap)
        thr = P.ARTIFACT_SD_MULTIPLIER * ch_std
        t1 = time.time()
        n_inter, n_ictal, n_rej = P.count_windows(case, raw_dir, smap, thr)
    files = sorted(p.name for p in (raw_dir / case).glob("*.edf"))
    return {"subject_id": case, "n_interictal": n_inter, "n_ictal": n_ictal, "n_rejected": n_rej,
            "ratio": round(n_inter / max(n_ictal, 1), 1), "ch_mean_uV": (ch_mean * 1e6).tolist(),
            "ch_std_uV": (ch_std * 1e6).tolist(), "artifact_thresh_uV": (thr * 1e6).tolist(),
            "r2": dict(view=str(view_root), files_globbed=files, stats_s=round(t1 - t, 1), count_s=round(time.time() - t1, 1))}


def features_record(case, view_root, stats, out_d, logfile, max_files=None):
    """thesis-convention features with the record builders; returns the .npz path."""
    import continuous_eval as CE
    import c1b_build_trainset as C1B
    import v9_x3_build_chb24 as B24
    _limit_threads()
    out_d = Path(out_d)
    out_d.mkdir(parents=True, exist_ok=True)
    sdir = out_d / f"_stats_{case}"
    sdir.mkdir(parents=True, exist_ok=True)
    (sdir / f"{case}_stats.json").write_text(json.dumps(stats, indent=2))
    CE.DATASET_DIR = Path(view_root) / "chbmit"                          # path globals only (this process)
    CE.PROCESSED_DIR = sdir
    with _captured(logfile):
        if case == "chb24":
            B24.RAW_DIR = Path(view_root) / "chbmit"
            B24.SUMMARY_PATH = B24.RAW_DIR / case / f"{case}-summary.txt"
            B24.OUT = sdir                                                # build_stats() reuses sdir/chb24_stats.json
            B24.XCACHE = sdir / "_no_xcache.npz"
            B24.build(max_files=max_files)
            made = sdir / (f"{case}_SMOKE.npz" if max_files else f"{case}.npz")
        else:
            C1B.build(case, max_files=max_files, out_dir=sdir, allow_test=True)
            made = sdir / (f"{case}_SMOKE.npz" if max_files else f"{case}.npz")
    dst = out_d / made.name
    made.replace(dst)
    return dst


# ============================================================================ gates
def compare_stats(new, ref):
    rep, ok = {}, True
    for k in STATS_FLOAT_KEYS:
        a, b = np.asarray(new[k], float), np.asarray(ref[k], float)
        rel = float(np.max(np.abs(a - b) / np.maximum(np.abs(b), 1e-30)))
        rep[f"{k}_max_rel"] = rel
        ok &= rel <= TOL["stats_rel"]
    for k in STATS_INT_KEYS + ("ratio",):
        rep[k] = [new[k], ref.get(k)]
        ok &= new[k] == ref.get(k)
    rep["status"] = "PASS" if ok else "FAIL"
    return rep


def _nanmaxdiff(a, b):
    a = np.asarray(a, np.float64)
    b = np.asarray(b, np.float64)
    fa, fb = np.isfinite(a), np.isfinite(b)
    if not np.array_equal(fa, fb):
        return float("inf"), int((fa != fb).sum())
    return (float(np.max(np.abs(a[fa] - b[fb]))) if fa.any() else 0.0), 0


def compare_features(new_npz, ref_npz, n_files=None):
    """G-feat on one case; n_files limits the reference to its first n files (smoke on a file subset)."""
    N = np.load(new_npz, allow_pickle=True)
    R = np.load(ref_npz, allow_pickle=True)
    rf = [str(x) for x in R["files"]]
    nf = [str(x) for x in N["files"]]
    m = np.ones(len(R["file_idx"]), bool) if n_files is None else R["file_idx"].astype(int) < n_files
    rep = dict(files_equal=nf == (rf if n_files is None else rf[:n_files]), n_windows=[int(len(N["file_idx"])), int(m.sum())])
    if n_files is None:
        rep["skipped_equal"] = [str(x) for x in N["skipped_files"]] == [str(x) for x in R["skipped_files"]]
    ok = rep["files_equal"] and rep["n_windows"][0] == rep["n_windows"][1] and rep.get("skipped_equal", True)
    if ok:
        for k in FLAGS + ("file_idx",):
            eq = np.array_equal(np.asarray(N[k]).astype(np.int64), np.asarray(R[k])[m].astype(np.int64))
            rep[f"{k}_equal"] = bool(eq)
            ok &= eq
        for k in ("f7", "bp5"):
            d, nfin = _nanmaxdiff(N[k], R[k][m])
            rep[f"{k}_max_abs"], rep[f"{k}_finite_mask_diff"] = d, nfin
            ok &= d <= TOL[k]
        a = N["adj"].astype(np.float32)
        b = R["adj"][m].astype(np.float32)
        both_nan = np.isnan(a) & np.isnan(b)
        diff = (np.abs(a - b) > TOL["adj_entry"]) | (np.isnan(a) != np.isnan(b))
        diff &= ~both_nan
        rep["adj_frac_differing"] = float(diff.mean())
        ok &= rep["adj_frac_differing"] <= TOL["adj_frac"]
        if "zgamma_raw" in N.files and "zgamma_raw" in R.files:          # descriptive (not used by the frozen system)
            rep["zgamma_raw_max_abs"] = _nanmaxdiff(N["zgamma_raw"], R["zgamma_raw"][m])[0]
    rep["status"] = "PASS" if ok else "FAIL"
    return rep


def locate_earlier(case):
    """the earlier .npz of a case under the Kaggle inputs (v9-x3-fold1/3; any nesting); copies must agree in size."""
    hits = [p for p in sorted(INPUT.rglob(f"{case}.npz")) if SCRATCH not in p.parents and WORK not in p.parents
            and "thesis-r2" not in str(p)]
    if not hits:
        raise SystemExit(f"STOP G-feat: no earlier {case}.npz under {INPUT} (attach v9-x3-fold1 and v9-x3-fold3)")
    if len({p.stat().st_size for p in hits}) != 1:
        raise SystemExit(f"STOP G-feat: copies of {case}.npz differ in size: {hits}")
    return hits[0]


def committed_stats(case):
    p = REPO / "data" / "processed" / f"{case}_stats.json"
    return json.loads(p.read_text()) if p.exists() else None


# ============================================================================ one case: gates + build (worker)
def case_job(a):
    """(case, kind) with kind 'earlier' (G-stats + build + G-feat on the earlier view) or 'complete' (R0.3: stats and
    build on the complete view; finalised only after every gate passed)."""
    case, kind, views, scratch_out, logs = a
    t = time.time()
    res = dict(case=case, kind=kind)
    try:
        view = views[kind]
        st = stats_record(case, view, Path(logs) / f"{case}_{kind}_stats.log")
        res["stats"] = st
        res["stats_s"] = round(time.time() - t, 1)
        if kind == "earlier":
            ref = committed_stats(case)
            res["g_stats"] = compare_stats(st, ref) if ref else dict(status="n/a (no committed stats.json; proven by G-feat)")
            if res["g_stats"]["status"] == "FAIL":
                res["wall_s"] = round(time.time() - t, 1)
                return res
        t1 = time.time()
        npz = features_record(case, view, st, Path(scratch_out) / kind, Path(logs) / f"{case}_{kind}_features.log")
        res["npz"] = str(npz)
        res["features_s"] = round(time.time() - t1, 1)
        if kind == "earlier":
            res["g_feat"] = compare_features(npz, locate_earlier(case))
    except SystemExit as e:
        res["error"] = f"STOP: {e}"
    except Exception:                    # noqa: BLE001
        res["error"] = traceback.format_exc()
    res["wall_s"] = round(time.time() - t, 1)
    return res


def _hours_used(cases_df, case, kind):
    r = cases_df[(cases_df.db == "chbmit") & (cases_df.case == case)].iloc[0]
    return float(r.earlier_hours_used_windows if kind == "earlier" else r.hours_used_windows)


def run_chb(cases_df, complete, earlier, cases=None, workers=None):
    """R0.2 + R0.3 for the CHB-MIT cases: every case 'earlier' (gates), then chb11 and chb21 'complete'. Jobs run in
    parallel, largest first; the first failed gate terminates the pool (STOP). The dataset folder is written only after
    every gate passed."""
    t = time.time()
    cases = list(cases or CHB_CASES)
    workers = workers or min(4, os.cpu_count() or 1)
    views = {"earlier": str(earlier), "complete": str(complete)}
    scratch_out = SCRATCH / "build"
    logs = out_dir() / "logs"
    jobs = sorted(((c, "earlier") for c in cases), key=lambda j: -_hours_used(cases_df, j[0], "earlier"))
    jobs += [(c, "complete") for c in GAP_CASES if c in cases]
    gates = dict(G_stats={}, G_feat={}, jobs={}, status="RUNNING", tolerances=TOL)
    done = {}
    log(f"R0_CHB: {len(jobs)} jobs on {workers} workers: {[f'{c}:{k}' for c, k in jobs]}")
    with Pool(workers, maxtasksperchild=1) as pool:
        for res in pool.imap_unordered(case_job, [(c, k, views, str(scratch_out), str(logs)) for c, k in jobs]):
            c, k = res["case"], res["kind"]
            done[(c, k)] = res
            h = _hours_used(cases_df, c, k)
            gates["jobs"][f"{c}:{k}"] = dict(wall_s=res["wall_s"], stats_s=res.get("stats_s"),
                                             features_s=res.get("features_s"), eeg_hours=round(h, 3),
                                             s_per_h=round(res["wall_s"] / max(h, 1e-9), 1), error=res.get("error"))
            if k == "earlier":
                if "g_stats" in res:
                    gates["G_stats"][c] = res["g_stats"]
                if "g_feat" in res:
                    gates["G_feat"][c] = res["g_feat"]
            fail = res.get("error") or (k == "earlier" and (res.get("g_stats", {}).get("status") == "FAIL"
                                                            or res.get("g_feat", {}).get("status") != "PASS"))
            log(f"{c}:{k} {'FAIL' if fail else 'ok'} in {res['wall_s']:.0f} s ({h:.1f} h EEG)"
                + (f" G-stats {res['g_stats']['status']}" if "g_stats" in res else "")
                + (f" G-feat {res['g_feat']['status']}" if "g_feat" in res else ""))
            if fail:
                pool.terminate()
                gates["status"] = f"STOP at {c}:{k}"
                _jdump(out_dir() / "gates.json", gates)
                raise SystemExit(f"STOP R0.2 {c}:{k}: {res.get('error') or res.get('g_stats') or res.get('g_feat')}")
            _jdump(out_dir() / "gates.json", gates)
    gates["status"] = "PASS"
    _jdump(out_dir() / "gates.json", gates)
    phase("chb_jobs", t)
    _finalise_chb(done, cases, cases_df)
    STATE["rates"]["chb_s_per_h_parallel"] = round(sum(j["wall_s"] for j in gates["jobs"].values())
                                                   / max(sum(j["eeg_hours"] for j in gates["jobs"].values()), 1e-9), 1)
    return gates, done


def _finalise_chb(done, cases, cases_df):
    """dataset folder: complete .npz + stats per case (earlier build for gap-free cases, complete build for chb11 and
    chb21); earlier stats of every case kept under r0_data/<tag>/stats_earlier; diff report for chb11 / chb21."""
    DS_CHB.mkdir(parents=True, exist_ok=True)
    se = out_dir() / "stats_earlier"
    se.mkdir(parents=True, exist_ok=True)
    for c in cases:
        _jdump(se / f"{c}_stats.json", done[(c, "earlier")]["stats"])
        src = done[(c, "complete")] if c in GAP_CASES else done[(c, "earlier")]
        shutil.copyfile(src["npz"], DS_CHB / f".{c}.npz.part")
        (DS_CHB / f".{c}.npz.part").replace(DS_CHB / f"{c}.npz")
        _jdump(DS_CHB / f"{c}_stats.json", src["stats"])
    inv = pd.read_csv(out_dir() / "inventory.csv")
    inv.to_csv(DS_CHB / "inventory.csv", index=False)
    if any(c in cases for c in GAP_CASES):
        diff_report(done, [c for c in GAP_CASES if c in cases], cases_df)


def _clean(z):
    return ~z["is_ictal"] & ~z["is_buffer"] & ~z["is_signal_loss"] & ~z["is_flag5sd"]


def diff_report(done, cases, cases_df):
    """R0.3: windows added, change of every stats value, clean-window count, seizure windows identical."""
    L = ["# R0.3 -- chb11 and chb21 on the complete file set vs the earlier copy\n",
         "Generated by `src/r2_core.py` (`diff_report`) from the builds of this run; descriptive, no gate.\n"]
    js = {}
    for c in cases:
        e, f = done[(c, "earlier")], done[(c, "complete")]
        E = np.load(e["npz"], allow_pickle=True)
        F = np.load(f["npz"], allow_pickle=True)
        ef, ff = [str(x) for x in E["files"]], [str(x) for x in F["files"]]
        added = [x for x in ff if x not in ef]
        per_file_added = {x: int((F["file_idx"] == ff.index(x)).sum()) for x in added}
        common_same_ictal = all(np.array_equal(E["is_ictal"][E["file_idx"] == ef.index(x)],
                                               F["is_ictal"][F["file_idx"] == ff.index(x)]) for x in ef)
        # the mean is ~0 uV, so its change is given in uV and in units of the earlier SD; SD and threshold relative
        sd_e = np.asarray(e["stats"]["ch_std_uV"], float)
        dst = {"ch_mean_uV (change / earlier SD)": (np.asarray(f["stats"]["ch_mean_uV"], float)
                                                    - np.asarray(e["stats"]["ch_mean_uV"], float)) / sd_e}
        dst.update({f"{k} (relative change)": (np.asarray(f["stats"][k], float) - np.asarray(e["stats"][k], float))
                    / np.asarray(e["stats"][k], float) for k in ("ch_std_uV", "artifact_thresh_uV")})
        d = dict(files_earlier=len(ef), files_complete=len(ff), files_added=added, windows_added=per_file_added,
                 windows_earlier=int(len(E["file_idx"])), windows_complete=int(len(F["file_idx"])),
                 hours_added=round(sum(per_file_added.values()) * 4 / 3600, 4),
                 ictal_windows=[int(E["is_ictal"].sum()), int(F["is_ictal"].sum())],
                 seizure_windows_in_added_files=int(sum(int(F["is_ictal"][F["file_idx"] == ff.index(x)].sum()) for x in added)),
                 seizure_windows_identical_in_common_files=bool(common_same_ictal),
                 clean_windows=[int(_clean(E).sum()), int(_clean(F).sum())],
                 flag5sd_windows=[int(E["is_flag5sd"].sum()), int(F["is_flag5sd"].sum())],
                 counts_earlier={k: e["stats"][k] for k in STATS_INT_KEYS},
                 counts_complete={k: f["stats"][k] for k in STATS_INT_KEYS},
                 stats_rel_change={k: dict(min=float(v.min()), median=float(np.median(v)), max=float(v.max()),
                                           per_channel=[float(x) for x in v]) for k, v in dst.items()})
        js[c] = d
        L += [f"## {c}\n",
              f"- files: {len(ef)} earlier -> {len(ff)} complete; added {added}",
              f"- windows: {d['windows_earlier']} -> {d['windows_complete']} (+{d['hours_added']} h: {per_file_added})",
              f"- seizure (ictal) windows: {d['ictal_windows'][0]} -> {d['ictal_windows'][1]}; identical in the common files: "
              f"{d['seizure_windows_identical_in_common_files']}; in the added files: {d['seizure_windows_in_added_files']}",
              f"- clean training windows (not ictal, buffer, signal loss, 5 SD flag): {d['clean_windows'][0]} -> {d['clean_windows'][1]}",
              f"- 5 SD flagged windows: {d['flag5sd_windows'][0]} -> {d['flag5sd_windows'][1]}",
              f"- stats.json counts earlier {d['counts_earlier']} -> complete {d['counts_complete']}",
              "- change of the z-score statistics and 5 SD thresholds over the 18 channels (complete vs earlier):", "",
              "| value | min | median | max |", "|---|---|---|---|"]
        L += [f"| {k} | {v['min']:+.4%} | {v['median']:+.4%} | {v['max']:+.4%} |" for k, v in d["stats_rel_change"].items()]
        L.append("")
    _jdump(out_dir() / "diff_chb11_chb21.json", js)
    (out_dir() / "diff_chb11_chb21.md").write_text("\n".join(L) + "\n")
    log("R0.3 diff report written:", jdumps({c: {k: js[c][k] for k in ("files_added", "hours_added",
                                                                            "seizure_windows_identical_in_common_files",
                                                                            "clean_windows")} for c in js}))


# ============================================================================ R0.4 external (x1 convention)
def ext_job(case, complete, procs, logfile):
    import x1_external as X1
    captured = []
    orig = X1.labelfree_stats

    def rec(*a, **k):                    # records the label-free statistics; the function itself is unchanged
        r = orig(*a, **k)
        captured.append(r)
        return r

    X1.labelfree_stats = rec
    t = time.time()
    try:
        with _captured(logfile):
            z, meta = X1.build_subject(str(complete), case, "labelfree", procs=procs)
    finally:
        X1.labelfree_stats = orig
    if z is None:
        return None, dict(meta, wall_s=round(time.time() - t, 1))
    mu, sd = captured[-1]
    meta = dict(meta, labelfree_mean_uV=(mu * 1e6).tolist(), labelfree_std_uV=(sd * 1e6).tolist(),
                wall_s=round(time.time() - t, 1), procs=procs)
    return z, meta


def x1_record_row(case):
    p = REPO / "results" / "x1_external" / f"rows_{case}.csv"
    if not p.exists():
        return None
    d = pd.read_csv(p)
    d = d[(d.point == "balanced") & (d.seed == "clean_seed42") & (d.stage == "localized")]
    return d.iloc[0] if len(d) else None


def run_ext(cases_df, complete, cases, out_folder=None, procs=None):
    """R0.4: chb24 + Siena with x1_external.build_subject; {case}_lf.npz (x1 save format + meta) + descriptive
    comparison with the x1 record (hours, n_ref); a case already in the output folder is skipped (resume)."""
    t = time.time()
    out_folder = Path(out_folder or DS_EXT)
    out_folder.mkdir(parents=True, exist_ok=True)
    rows = []
    for c in cases:
        dst = out_folder / f"{c}_lf.npz"
        if dst.exists():
            meta = json.loads(str(np.load(dst, allow_pickle=True)["meta"]))
            log(f"{c}: exists, skip")
        else:
            inv = pd.read_csv(out_dir() / "inventory.csv")
            hh = inv[(inv.case == c) & inv.file.str.endswith(".edf")].hours
            longest = float(hh.max()) if len(hh) else 0.0
            # workers per subject: memory only (x1 loads a whole file per worker); results do not depend on it
            p = procs or (int(os.environ.get("R2_EXT_PROCS", 0)) or (4 if longest <= 6 else 2))
            z, meta = ext_job(c, complete, p, out_dir() / "logs" / f"{c}_ext.log")
            if z is None:
                rows.append(dict(case=c, scored=False, note="no file with all electrodes", **{k: meta.get(k) for k in ("hours",)}))
                continue
            tmp = out_folder / f".{c}_lf.npz.part.npz"
            np.savez(tmp, **z, meta=jdumps(meta))
            tmp.replace(dst)
            h = meta["hours"]
            STATE["rates"][f"ext_{c}_s_per_h"] = round(meta["wall_s"] / max(h, 1e-9), 1)
            log(f"{c}: {h:.2f} h in {meta['wall_s']:.0f} s ({meta['wall_s'] / max(h, 1e-9):.0f} s/h, {p} procs)")
        z = np.load(dst, allow_pickle=True)
        rec = x1_record_row(c)
        n_ict = int(z["is_ictal"].sum())
        rows.append(dict(case=c, scored=True, files=len(z["files"]), windows=int(len(z["file_idx"])), hours=meta["hours"],
                         ictal_windows=n_ict, signal_loss_windows=int(z["is_signal_loss"].sum()),
                         skipped=len(meta.get("skipped", [])), x1_hours=None if rec is None else float(rec.hours),
                         hours_equal_x1=None if rec is None else bool(abs(float(rec.hours) - meta["hours"]) < 1e-9),
                         x1_n_ref=None if rec is None else int(rec.n_ref), x1_nonict_h=None if rec is None else float(rec.nonict_h),
                         nonict_h=round(float((~z["is_ictal"].astype(bool) & ~z["is_signal_loss"].astype(bool)).sum()) * 4 / 3600, 6),
                         wall_s=meta.get("wall_s"), procs=meta.get("procs")))
    df = pd.DataFrame(rows)
    df.to_csv(out_dir() / "external_cases.csv", index=False)
    inv = pd.read_csv(out_dir() / "inventory.csv")
    inv.to_csv(out_folder / "inventory.csv", index=False)
    phase("external", t)
    if "nonict_h" in df and df.x1_nonict_h.notna().any():
        dd = df.dropna(subset=["x1_nonict_h"])
        log("external vs x1 record: hours equal", int(dd.hours_equal_x1.sum()), "of", len(dd),
            "| non-ictal hours equal", int((abs(dd.nonict_h - dd.x1_nonict_h) < 1e-6).sum()), "of", len(dd))
    return df


# ============================================================================ smoke
def smoke_probe_files(cases_df, earlier, case="chb11", n_first=2, workers=None):
    """G-stats on the whole earlier set of `case` (record functions, one process) and G-feat on its first n files;
    then a parallel probe: `workers` processes, each building one other file alone (G-feat on that file), to measure
    the speed under load."""
    t = time.time()
    logs = out_dir() / "logs"
    st = stats_record(case, earlier, logs / f"{case}_earlier_stats.log")
    h_all = _hours_used(cases_df, case, "earlier")
    g_stats = compare_stats(st, committed_stats(case))
    STATE["rates"]["stats_count_s_per_h_1proc"] = round((st["r2"]["stats_s"] + st["r2"]["count_s"]) / h_all, 2)
    STATE["rates"]["stats_s_per_h_1proc"] = round(st["r2"]["stats_s"] / h_all, 2)
    STATE["rates"]["count_s_per_h_1proc"] = round(st["r2"]["count_s"] / h_all, 2)
    log(f"G-stats {case} (earlier, {h_all:.1f} h): {g_stats['status']} {jdumps(g_stats)}; "
        f"stats {st['r2']['stats_s']:.0f} s + count {st['r2']['count_s']:.0f} s")
    res = dict(G_stats={case: g_stats})
    if g_stats["status"] != "PASS":
        _jdump(out_dir() / "gates.json", res)
        raise SystemExit(f"STOP G-stats {case}: {g_stats}")
    ref = locate_earlier(case)
    t1 = time.time()
    npz = features_record(case, earlier, st, SCRATCH / "smoke_build", logs / f"{case}_smoke_features.log", max_files=n_first)
    z = np.load(npz, allow_pickle=True)
    h_sub = len(z["file_idx"]) * 4 / 3600
    STATE["rates"]["features_s_per_h_1proc"] = round((time.time() - t1) / h_sub, 2)
    g_feat = compare_features(npz, ref, n_files=n_first)
    log(f"G-feat {case} first {n_first} files ({h_sub:.2f} h): {g_feat['status']} {jdumps(g_feat)}")
    res["G_feat"] = {f"{case}[files 1-{n_first}]": g_feat}
    if g_feat["status"] != "PASS":
        _jdump(out_dir() / "gates.json", res)
        raise SystemExit(f"STOP G-feat {case}: {g_feat}")
    # parallel probe: one other file per worker (mini views), G-feat on each
    workers = workers or min(4, os.cpu_count() or 1)
    R = np.load(ref, allow_pickle=True)
    rf = [str(x) for x in R["files"]]
    probe = rf[n_first:n_first + workers]
    jobs = []
    for f in probe:
        mv = SCRATCH / "probe" / f.replace(".edf", "")
        d = mv / "chbmit" / case
        d.mkdir(parents=True, exist_ok=True)
        lnk = d / f
        if not lnk.exists():
            os.symlink(os.path.realpath(Path(earlier) / "chbmit" / case / f), lnk)
        jobs.append((case, str(mv), st, str(SCRATCH / "probe_build" / f.replace(".edf", "")), str(logs / f"probe_{f}.log"), f))
    t2 = time.time()
    with Pool(len(jobs), maxtasksperchild=1) as pool:
        outs = pool.map(_probe_job, jobs)
    wall = time.time() - t2
    probe_rep = {}
    for (c, mv, _, od, lg, f), (npz_p, sec) in zip(jobs, outs):
        Z = np.load(npz_p, allow_pickle=True)
        k = rf.index(f)
        sub = dict(files=[f], n=int((R["file_idx"] == k).sum()))
        Nn = {key: Z[key] for key in Z.files}
        Rr = {key: (R[key][R["file_idx"] == k] if key not in ("files", "skipped_files") else R[key]) for key in R.files}
        Rr["file_idx"] = np.zeros(sub["n"], np.int16)
        Rr["files"] = np.array([f], dtype=object)
        tmp_r = SCRATCH / "probe" / f"ref_{f}.npz"
        np.savez(tmp_r, **Rr)
        rep = compare_features(npz_p, tmp_r, n_files=1)
        rep["seconds"] = round(sec, 1)
        rep["eeg_h"] = round(len(Nn["file_idx"]) * 4 / 3600, 3)
        probe_rep[f] = rep
        if rep["status"] != "PASS":
            res["G_feat"][f"{case}[{f}]"] = rep
            _jdump(out_dir() / "gates.json", res)
            raise SystemExit(f"STOP G-feat probe {f}: {rep}")
    res["G_feat"].update({f"{case}[{f}]": r for f, r in probe_rep.items()})
    tot_h = sum(r["eeg_h"] for r in probe_rep.values())
    STATE["rates"]["features_s_per_h_per_worker_parallel"] = round(float(np.mean([r["seconds"] / r["eeg_h"] for r in probe_rep.values()])), 2)
    STATE["rates"]["parallel_workers"] = len(jobs)
    STATE["rates"]["parallel_wall_s"] = round(wall, 1)
    STATE["rates"]["parallel_eeg_h"] = round(tot_h, 3)
    log(f"parallel probe: {len(jobs)} workers, {tot_h:.2f} h of EEG in {wall:.0f} s wall; per worker "
        f"{STATE['rates']['features_s_per_h_per_worker_parallel']} s/h; all G-feat PASS")
    res["status"] = "PASS"
    _jdump(out_dir() / "gates.json", res)
    phase("smoke_chb", t)
    return res


def _probe_job(a):
    case, mv, st, od, lg, f = a
    t = time.time()
    p = features_record(case, mv, st, od, lg)
    return str(p), time.time() - t


def projection(cases_df, ext_rate_s_per_h=None, workers=None, limit_h=10.5):
    """R0_CHB and R0_EXT wall-time projection from the smoke measurements (computed estimate, labelled as such)."""
    r = STATE["rates"]
    workers = workers or min(4, os.cpu_count() or 1)
    ch = cases_df[cases_df.db == "chbmit"].set_index("case")
    slow = r["features_s_per_h_per_worker_parallel"] / max(r["features_s_per_h_1proc"], 1e-9)
    per_h = (r["stats_count_s_per_h_1proc"] + r["features_s_per_h_1proc"]) * max(slow, 1.0)
    jobs = {c: float(ch.loc[c, "earlier_hours_used_windows"]) * per_h for c in ch.index}
    for c in GAP_CASES:
        if c in ch.index:
            jobs[f"{c}:complete"] = float(ch.loc[c, "hours_used_windows"]) * per_h
    # longest-processing-time-first schedule on `workers` lanes
    lanes = [0.0] * workers
    for c, s in sorted(jobs.items(), key=lambda kv: -kv[1]):
        lanes[lanes.index(min(lanes))] += s
    gb_chb = None
    inv = pd.read_csv(out_dir() / "inventory.csv")
    gb_chb = float(inv[inv.db == "chbmit"].size_bytes.sum()) / 1e9
    hash_s = gb_chb * 1e3 / max(r.get("hash_chbmit_MB_per_s", 100.0), 1e-9)
    chb_h = (max(lanes) + hash_s + 600) / 3600
    out = dict(note="computed estimate from the smoke measurements, not a measurement",
               per_hour_of_eeg_s=round(per_h, 2), parallel_slowdown=round(slow, 2), workers=workers,
               chb_jobs_s={k: round(v) for k, v in jobs.items()}, chb_hash_s=round(hash_s),
               R0_CHB_projected_h=round(float(chb_h), 2), split_R0_CHB=bool(chb_h > limit_h), limit_h=limit_h)
    if ext_rate_s_per_h:
        sn = cases_df[cases_df.db == "siena"]
        ext_hours = float(sn.hours_used_windows.sum()) + float(ch.loc["chb24", "hours_used_windows"]) if "chb24" in ch.index \
            else float(sn.hours_used_windows.sum())
        gb_ext = float(inv[(inv.db == "siena") | (inv.case == "chb24")].size_bytes.sum()) / 1e9
        out.update(ext_s_per_h_measured=ext_rate_s_per_h, ext_hours=round(ext_hours, 2),
                   R0_EXT_projected_h=round((ext_hours * ext_rate_s_per_h + gb_ext * 1e3 / max(r.get("hash_siena_MB_per_s", 100.0), 1e-9) + 600) / 3600, 2))
        out["split_R0_EXT"] = bool(out["R0_EXT_projected_h"] > limit_h)
    _jdump(out_dir() / "projection.json", out)
    log("projection", jdumps(out))
    return out


# ============================================================================ resume
def import_previous(dest_folder, pattern):
    """files of an earlier version of this notebook's output attached as an input: copied when not yet present."""
    n = 0
    for p in sorted(INPUT.rglob(pattern)):
        if Path(dest_folder).name in str(p.parent) and not (Path(dest_folder) / p.name).exists():
            Path(dest_folder).mkdir(parents=True, exist_ok=True)
            shutil.copyfile(p, Path(dest_folder) / p.name)
            n += 1
    if n:
        log(f"resume: {n} files copied from a previous output into {dest_folder}")
    return n
