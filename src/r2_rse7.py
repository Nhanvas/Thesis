#!/usr/bin/env python
"""
r2_rse7.py -- research track, stage RP, path 2: gate RS-E7 of fix B (docs/FUTURE_RESEARCH_PLAN.md §12 14/11 18:30 (c);
implementation D27-F). Kaggle CPU, notebooks RS_E7_<part> (src/r2_rse7_make_notebook.py), in parallel with RP_SERIES.

QUESTION. Does src/r2_e7exact.py segment exactly as ruptures 1.1.10 does inside the D2 segmenter of
src/e7_ensemble_cpd.py, on the real path-2 series? RULE (fixed before the run): RS-E7 PASS iff, on every file of the
committed path-2 final scores (results/r2/r1_system/rp/rp2/scores: the 8 test patients, chb24, Siena 14 = 23 cases),
for the 4 seeds and the 3 penalties of E7 (c = 1, 3, 10), the breakpoint list of r2_e7exact.pelt_l2 equals the one of
ruptures.Pelt(model="l2", min_size=2, jump=1) exactly (list equality), and every expected call is present once. Any
difference STOPs the part at once (pool terminated), with the case, seed, penalty, file and the first differing
breakpoint. The E7 D2 rows of RP_SERIES enter report version A2 only if RS-E7 passes in full; if it fails, the cause is
diagnosed before any other choice.

HOW. E7's own d2_grid is compiled from the committed source of src/e7_ensemble_cpd.py (AST: the function `d2_grid` and
the constant `PENS`, nothing else; the file's sha256 is recorded) in a namespace where `E1.TOPS` is empty (so only the
segmentation runs, no scoring) and `rpt` is a recorder: each Pelt(...).fit(X).predict(pen) call runs ruptures itself
(timed) and r2_e7exact.pelt_l2 on the same array and penalty (timed), records both, and returns ruptures' result. So the
inputs (median fill of signal-loss windows, noise scale, penalty, file split, the array passed) are E7's own. Per case:
the d of d2_grid = {is_signal_loss: not ok, file_idx} of the scores file, the score = x of the seed.

GATES (STOP): G-code (ruptures 1.1.10; E7's PENS = [1, 3, 10]; d2_grid found once); G-in (every assigned scores file
present, columns, x finite on ok windows, file_idx non-decreasing); RS-E7 (above). Jobs = (case, seed), one spawned
process each, largest first (cost proxy = sum over files of n^2); each job writes jobs/<case>_s<seed>.csv + DONE.json
(code sha256s) last; a previous output attached as input is reused when the code shas match (resume); a job is not
started after LIMIT_H hours of session (it is reported NOT RUN; re-run the version with the output attached).
Outputs: WORK/r2/r1_system/rp_series/rse7/<part>/ (gates.json, files.csv, jobs.csv, run_meta.json, SUMMARY.md, jobs/).
Merge (container, after all parts): python src/r2_rse7.py --merge <part dirs> --out results/r2/r1_system/rp_series/rse7
-> gate.json (RS-E7 over the 92 jobs), files.csv, SUMMARY.md (counts, measured ruptures / exact seconds).
Tests: src/r2_rse7_synthetic_test.py.
"""
import argparse
import ast
import hashlib
import json
import multiprocessing as mp
import os
import platform
import sys
import time
import traceback
import types
from pathlib import Path

import numpy as np
import pandas as pd

REPO = Path(os.environ.get("THESIS_REPO", Path(__file__).resolve().parents[1]))
WORK = Path(os.environ.get("R2_WORK", "/kaggle/working"))
INPUT = Path(os.environ.get("R2_INPUT", "/kaggle/input"))
SCORES = REPO / "results" / "r2" / "r1_system" / "rp" / "rp2" / "scores"
E7_FILE = REPO / "src" / "e7_ensemble_cpd.py"
CASES = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18", "chb24", "PN00", "PN01", "PN03",
         "PN05", "PN06", "PN07", "PN09", "PN10", "PN11", "PN12", "PN13", "PN14", "PN16", "PN17"]
SEEDS = [1, 2, 3, 4]
RUPTURES = "1.1.10"
LIMIT_H = float(os.environ.get("R2_RSE7_LIMIT_H", "11.0"))
T0 = float(os.environ.get("R2_T0", time.time()))
STATE = dict(gates=[], phases={})


def log(*a):
    print(time.strftime("%H:%M:%S"), *a, flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def code_shas():
    here = Path(__file__).resolve()
    return dict(r2_rse7=sha(here), r2_e7exact=sha(here.parent / "r2_e7exact.py"), e7_ensemble_cpd=sha(E7_FILE))


def out_root(part):
    return WORK / "r2" / "r1_system" / "rp_series" / "rse7" / part


def gate(rec, part):
    STATE["gates"] = [g for g in STATE["gates"] if g["gate"] != rec["gate"]] + [rec]
    (out_root(part) / "gates.json").write_text(json.dumps(STATE["gates"], indent=1, default=str))
    log(f"{rec['gate']}: {rec['status']} — {rec.get('summary', '')}")
    if rec["status"] != "PASS":
        write_summary(out_root(part), part, collect(out_root(part)))      # the record is written before the STOP
        raise SystemExit(f"{rec['gate']} {rec['status']}: {rec.get('summary', '')}")


# ============================================================================ E7's d2_grid, from the committed source
def load_d2(rec):
    """compile the function d2_grid and the constant PENS of src/e7_ensemble_cpd.py (nothing else) into a namespace with
    np, the recorder `rpt` and E1.TOPS = [] (segmentation only); returns (d2_grid, PENS, its source text)."""
    src = E7_FILE.read_text(encoding="utf-8")
    tree = ast.parse(src)
    fns = [n for n in tree.body if isinstance(n, ast.FunctionDef) and n.name == "d2_grid"]
    pens = [n for n in tree.body if isinstance(n, ast.Assign) and any(getattr(t, "id", None) == "PENS" for t in n.targets)]
    if len(fns) != 1 or len(pens) != 1:
        raise SystemExit("G-code: d2_grid / PENS not found once in e7_ensemble_cpd.py")
    g = {"np": np, "rpt": rec, "E1": types.SimpleNamespace(TOPS=[], WIN=4), "PENS": ast.literal_eval(pens[0].value),
         "merge": None, "score_events": None, "__name__": "e7_d2_from_source"}
    exec(compile(ast.Module(body=[fns[0]], type_ignores=[]), str(E7_FILE), "exec"), g)
    return g["d2_grid"], list(g["PENS"]), ast.get_source_segment(src, fns[0])


class Recorder:
    """stands for the ruptures module inside d2_grid: Pelt(...).fit(X).predict(pen) runs ruptures and the exact
    implementation on the same array, records both and returns ruptures' breakpoints."""

    def __init__(self, exact_fn):
        self.calls = []
        rec = self

        class Pelt:
            def __init__(self, model="l2", custom_cost=None, min_size=2, jump=5, params=None):
                import ruptures as rpt
                self.args = (model, min_size, jump)
                self.ref = rpt.Pelt(model=model, custom_cost=custom_cost, min_size=min_size, jump=jump, params=params)

            def fit(self, signal):
                self.signal = signal
                self.ref.fit(signal)
                return self

            def predict(self, pen):
                t = time.perf_counter()
                a = self.ref.predict(pen=pen)
                tr = time.perf_counter() - t
                t = time.perf_counter()
                b, info = exact_fn(self.signal, pen)
                tm = time.perf_counter() - t
                diff = next((i for i, (u, v) in enumerate(zip(a, b)) if u != v), None if len(a) == len(b) else min(len(a), len(b)))
                rec.calls.append(dict(n=int(np.asarray(self.signal).shape[0]), pen=float(pen), args=str(self.args),
                                      equal=bool(a == b), n_bkps_ruptures=len(a), n_bkps_exact=len(b),
                                      first_diff=diff, bk_ruptures_at_diff=None if diff is None or diff >= len(a) else a[diff],
                                      bk_exact_at_diff=None if diff is None or diff >= len(b) else b[diff],
                                      t_ruptures_s=round(tr, 4), t_exact_s=round(tm, 4), exact_costs=info["exact"],
                                      max_adm=info["max_adm"]))
                return a
        self.Pelt = Pelt


def case_cost(case):
    s = pd.read_csv(SCORES / f"{case}.csv.gz", usecols=["file_idx"])
    n = s.groupby("file_idx").size().values.astype(float)
    return float((n ** 2).sum())


def job(a):
    """one (case, seed): every Pelt call of E7's d2_grid on that seed's score, ruptures vs exact."""
    case, seed, outdir = a
    t0 = time.time()
    try:
        if time.time() - T0 > LIMIT_H * 3600:
            return dict(case=case, seed=seed, not_run=True)
        planted = os.environ.get("R2_TEST_E7X_FILE") if os.environ.get("R2_TEST_REPO") else None
        if planted:                                   # synthetic test only: a deliberately wrong implementation
            import importlib.util
            spec = importlib.util.spec_from_file_location("r2_e7exact_planted", planted)
            E7X = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(E7X)
        else:
            import r2_e7exact as E7X
        rec = Recorder(E7X.pelt_l2)
        d2, pens, _ = load_d2(rec)
        s = pd.read_csv(SCORES / f"{case}.csv.gz")
        ok = s.ok.values.astype(bool)
        fidx = s.file_idx.values.astype(int)
        d = {"is_signal_loss": ~ok, "file_idx": fidx}
        d2(d, s[f"x_s{seed}"].values.astype(np.float64))
        files = [f for f in np.unique(fidx) if int((fidx == f).sum()) >= 4]
        short = [f for f in np.unique(fidx) if int((fidx == f).sum()) < 4]
        expect = [(c, f) for c in pens for f in files]
        if len(rec.calls) != len(expect):
            raise SystemExit(f"{case} s{seed}: {len(rec.calls)} Pelt calls, expected {len(expect)}")
        rows = []
        for (c, f), r in zip(expect, rec.calls):
            if r["n"] != int((fidx == f).sum()):
                raise SystemExit(f"{case} s{seed}: call order differs from (penalty, file) at file {f}")
            rows.append(dict(case=case, seed=seed, c=c, file_idx=int(f), **r))
        df = pd.DataFrame(rows)
        jd = Path(outdir) / "jobs"
        jd.mkdir(parents=True, exist_ok=True)
        tmp = jd / f".{case}_s{seed}.csv"
        df.to_csv(tmp, index=False)
        tmp.replace(jd / f"{case}_s{seed}.csv")
        (jd / f"{case}_s{seed}.DONE.json").write_text(json.dumps(dict(code=code_shas(), short_files=[int(f) for f in short],
                                                                       s=round(time.time() - t0, 1))))
        return dict(case=case, seed=seed, rows=len(df), unequal=int((~df.equal).sum()), short=len(short),
                    s=round(time.time() - t0, 1), first_bad=df[~df.equal].head(3).to_dict("records"))
    except SystemExit as e:
        return dict(case=case, seed=seed, error=f"STOP: {e}")
    except Exception:                                 # noqa: BLE001
        return dict(case=case, seed=seed, error=traceback.format_exc()[-3000:])


def _init(env):
    os.environ.update(env)
    sys.path[:0] = [p for p in env.get("R2_SYSPATH", "").split(os.pathsep) if p]


def reuse(part, todo):
    """finished jobs of an attached previous output (same code shas) -> copied into this part's jobs/."""
    want, got = code_shas(), []
    jd = out_root(part) / "jobs"
    jd.mkdir(parents=True, exist_ok=True)
    for p in sorted(INPUT.rglob("*.DONE.json")) if INPUT.exists() else []:
        if "rse7" not in p.parts:
            continue
        name = p.name.replace(".DONE.json", "")
        try:
            case, seed = name.rsplit("_s", 1)
            seed = int(seed)
        except ValueError:
            continue
        if (case, seed) not in todo or json.loads(p.read_text()).get("code") != want:
            continue
        csvp = p.with_name(f"{name}.csv")
        if csvp.exists() and not (jd / csvp.name).exists():
            (jd / csvp.name).write_bytes(csvp.read_bytes())
            (jd / p.name).write_bytes(p.read_bytes())
            got.append((case, seed))
    return got


def run(part, cases, workers):
    """the notebook's main cell for one part: G-code, G-in, jobs, RS-E7 of the part."""
    t = time.time()
    o = out_root(part)
    o.mkdir(parents=True, exist_ok=True)
    import ruptures
    shas = code_shas()
    _, pens, d2src = load_d2(Recorder(lambda s, p: ([], {})))
    bad = [] if ruptures.__version__.lstrip("v") == RUPTURES else [f"ruptures {ruptures.__version__} != {RUPTURES}"]
    if pens != [1.0, 3.0, 10.0]:
        bad.append(f"PENS {pens}")
    unknown = [c for c in cases if c not in CASES]
    if unknown:
        bad.append(f"unknown cases {unknown}")
    gate(dict(gate="G-code", status="PASS" if not bad else "FAIL", code=shas, ruptures=ruptures.__version__, pens=pens,
              d2_grid_source_sha256=hashlib.sha256(d2src.encode()).hexdigest(), bad=bad,
              summary="ruptures 1.1.10, E7 PENS [1, 3, 10], d2_grid compiled from the committed source" if not bad else str(bad)),
         part)
    bad, files = [], {}
    for c in cases:
        p = SCORES / f"{c}.csv.gz"
        if not p.exists():
            bad.append(f"{c}: missing"); continue
        s = pd.read_csv(p)
        need = {"ok", "file_idx", *[f"x_s{k}" for k in SEEDS]}
        if not need <= set(s.columns):
            bad.append(f"{c}: columns"); continue
        ok = s.ok.values.astype(bool)
        if not all(np.isfinite(s[f"x_s{k}"].values[ok]).all() for k in SEEDS) or not ok.any():
            bad.append(f"{c}: x not finite on ok windows")
        if (np.diff(s.file_idx.values) < 0).any():
            bad.append(f"{c}: file_idx not ordered")
        files[c] = dict(sha256=sha(p), windows=int(len(s)), files=int(s.file_idx.nunique()))
    gate(dict(gate="G-in", status="PASS" if not bad else "FAIL", files=files, bad=bad,
              summary=f"{len(files)} scores files read, sha256 recorded" if not bad else str(bad)), part)
    todo = {(c, k) for c in cases for k in SEEDS}
    reused = set(reuse(part, todo))
    specs = sorted([(c, k, str(o)) for c, k in todo - reused], key=lambda a: (-case_cost(a[0]), a[0], a[1]))
    log(f"part {part}: {len(todo)} jobs ({len(reused)} reused), {len(specs)} to run on {workers} workers")
    env = dict(os.environ, R2_SYSPATH=os.pathsep.join(sys.path), R2_T0=str(T0))
    res, stop = [], None
    if specs:
        with mp.get_context("spawn").Pool(min(workers, len(specs)), initializer=_init, initargs=(env,),
                                          maxtasksperchild=1) as pool:
            for r in pool.imap_unordered(job, specs):
                res.append(r)
                if r.get("error") or r.get("unequal"):
                    stop = r
                    pool.terminate()
                    break
                log(f"{r['case']} s{r['seed']}: " + ("NOT RUN (session time)" if r.get("not_run") else
                                                     f"{r['rows']} calls equal ({r['s']} s)"))
    STATE["phases"]["jobs"] = round(time.time() - t, 1)
    jobs = collect(o)
    jobs.to_csv(o / "files.csv", index=False)
    done = {(c, k) for c, k in jobs[["case", "seed"]].drop_duplicates().itertuples(index=False)} if len(jobs) else set()
    not_run = sorted(todo - done)
    unequal = jobs[~jobs.equal] if len(jobs) else jobs
    if stop is not None:
        rec = dict(gate=f"RS-E7[{part}]", status="FAIL", stop=stop, done=len(done), not_run=not_run,
                   summary=f"STOP at {stop['case']} seed {stop['seed']}: " + (stop.get("error") or
                           f"{stop['unequal']} calls differ; first {stop['first_bad'][:1]}"))
    else:
        ok = not not_run and len(unequal) == 0
        rec = dict(gate=f"RS-E7[{part}]", status="PASS" if ok else ("NOT DONE" if not len(unequal) else "FAIL"),
                   jobs=len(done), calls=int(len(jobs)), unequal=int(len(unequal)), not_run=not_run,
                   summary=f"{len(done)} of {len(todo)} jobs, {len(jobs)} Pelt calls, {len(unequal)} differ"
                           + (f"; NOT RUN {not_run}" if not_run else ""))
    write_summary(o, part, jobs)
    gate(rec, part)
    return rec


def collect(o):
    fs = sorted((Path(o) / "jobs").glob("*.csv"))
    fs = [f for f in fs if not f.name.startswith(".")]
    return pd.concat([pd.read_csv(f) for f in fs], ignore_index=True) if fs else pd.DataFrame(
        columns=["case", "seed", "c", "file_idx", "n", "equal"])


def write_summary(o, label, jobs):
    L = [f"# RS-E7 {label} — exact E7 D2 segmentation vs ruptures {RUPTURES} (gate; no research number)\n"]
    if len(jobs):
        g = jobs.groupby("case").agg(seeds=("seed", "nunique"), calls=("equal", "size"), unequal=("equal", lambda v: int((~v).sum())),
                                     max_n=("n", "max"), t_ruptures_s=("t_ruptures_s", "sum"), t_exact_s=("t_exact_s", "sum"))
        L += ["| case | seeds | calls | differ | longest file | ruptures s | exact s |", "|---|---|---|---|---|---|---|"]
        L += [f"| {c} | {r.seeds} | {r.calls} | {r.unequal} | {r.max_n} | {r.t_ruptures_s:.0f} | {r.t_exact_s:.1f} |"
              for c, r in g.iterrows()]
        L += ["", f"Total: {len(jobs)} calls, {int((~jobs.equal).sum())} differ; ruptures {jobs.t_ruptures_s.sum():.0f} s, "
                  f"exact {jobs.t_exact_s.sum():.1f} s (measured, one process each)."]
    L += ["", "Gates: " + "; ".join(f"{g['gate']} {g['status']}" for g in STATE["gates"])]
    (Path(o) / "SUMMARY.md").write_text("\n".join(L) + "\n")


def run_meta(part, notebook, commit):
    import ruptures
    m = dict(notebook=notebook, part=part, repo_commit=commit, python=platform.python_version(), numpy=np.__version__,
             pandas=pd.__version__, ruptures=ruptures.__version__, cpu=os.cpu_count(), code=code_shas(),
             started_utc=time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(T0)))
    out_root(part).mkdir(parents=True, exist_ok=True)
    (out_root(part) / "run_meta.json").write_text(json.dumps(m, indent=1))
    return m


def finish_meta(part):
    p = out_root(part) / "run_meta.json"
    m = json.loads(p.read_text())
    m.update(runtime_h=round((time.time() - T0) / 3600, 3), phases_s=STATE["phases"])
    p.write_text(json.dumps(m, indent=1))
    return m


# ============================================================================ merge (container)
def merge(parts, out):
    out = Path(out)
    out.mkdir(parents=True, exist_ok=True)
    frames, gates, metas = [], {}, {}
    for p in parts:
        p = Path(p)
        frames.append(collect(p))
        gates[p.name] = json.loads((p / "gates.json").read_text()) if (p / "gates.json").exists() else []
        metas[p.name] = json.loads((p / "run_meta.json").read_text()) if (p / "run_meta.json").exists() else {}
    J = pd.concat(frames, ignore_index=True) if frames else pd.DataFrame()
    bad = []
    keys = J[["case", "seed"]].drop_duplicates()
    dup = J.groupby(["case", "seed", "c", "file_idx"]).size()
    if (dup > 1).any():
        bad.append(f"{int((dup > 1).sum())} calls present more than once")
    missing = sorted({(c, k) for c in CASES for k in SEEDS} - set(map(tuple, keys.values.tolist())))
    if missing:
        bad.append(f"jobs missing: {missing}")
    for c, k in set(map(tuple, keys.values.tolist())):
        s = pd.read_csv(SCORES / f"{c}.csv.gz", usecols=["file_idx"])
        n = s.groupby("file_idx").size()
        want = 3 * int((n >= 4).sum())
        got = int(((J.case == c) & (J.seed == k)).sum())
        if got != want:
            bad.append(f"{c} s{k}: {got} calls, expected {want}")
    shas = {json.dumps(m.get("code"), sort_keys=True) for m in metas.values() if m}
    if len(shas) > 1:
        bad.append("parts ran different code")
    vers = {m.get("ruptures") for m in metas.values() if m}
    if vers - {RUPTURES, "v" + RUPTURES}:
        bad.append(f"ruptures versions {vers}")
    une = int((~J.equal.astype(bool)).sum()) if len(J) else 0
    status = "PASS" if not bad and une == 0 else "FAIL"
    rec = dict(gate="RS-E7", status=status, jobs=int(len(keys)), calls=int(len(J)), unequal=une, bad=bad,
               parts={k: [(g["gate"], g["status"]) for g in v] for k, v in gates.items()},
               code=json.loads(next(iter(shas))) if len(shas) == 1 else None,
               runtime_h={k: m.get("runtime_h") for k, m in metas.items()},
               summary=f"{len(keys)} of {len(CASES) * len(SEEDS)} jobs, {len(J)} Pelt calls, {une} differ" + (f"; {bad}" if bad else ""))
    (out / "gate.json").write_text(json.dumps(rec, indent=1, default=str))
    J.to_csv(out / "files.csv", index=False)
    STATE["gates"] = [rec]
    write_summary(out, "merged", J)
    log(f"RS-E7 {status}: {rec['summary']}")
    return rec


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--merge", nargs="+", metavar="PART_DIR")
    ap.add_argument("--out", default=str(REPO / "results" / "r2" / "r1_system" / "rp_series" / "rse7"))
    a = ap.parse_args()
    if not a.merge:
        ap.error("--merge PART_DIR ... (the parts run in the notebooks RS_E7_<part>)")
    r = merge(a.merge, a.out)
    sys.exit(0 if r["status"] == "PASS" else 1)
