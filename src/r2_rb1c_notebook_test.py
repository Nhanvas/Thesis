#!/usr/bin/env python
"""r2_rb1c_notebook_test.py -- end-to-end test of notebooks/r2/RB1C_SURVEY.ipynb on SYNTHETIC data (build container
only). The world of src/r2_rb1c_synthetic_test.py is laid out as the Kaggle raw dataset (one EDF absent, one EDF with a
changed byte) and as a fake PhysioNet (file:// URLs with SHA256SUMS.txt), so R0's `r2_core.inventory` has to verify
every file and download the two from "PhysioNet". The notebook's cells run in one namespace, as on Kaggle.
Checks: the notebook ends without STOP; the two files come from PhysioNet; the archive holds rb1c/ with every table and
the Kaggle inventory; every gate PASS; the five tables are byte-equal to a direct run of r2_rb1c.py on the same world;
failure path: a committed flag count + 1 -> r2_rb1c STOPs at G-flags, the END cell still archives rb1c.json and run.log
and then raises STOPPED.
  python src/r2_rb1c_notebook_test.py [--root DIR]
"""
import argparse
import hashlib
import json
import shutil
import sys
import time
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))
import r2_rb1c_synthetic_test as W  # noqa: E402
import r2_rb1_synthetic_test as T  # noqa: E402
import r2_rb1c_make_notebook as NB  # noqa: E402

RAWNAME = "combined-siena-scalp-and-chb-mit-eeg-datasets"
TABLES = ("cases.csv", "channels.csv", "flag_grid.csv", "files.csv", "top_windows.csv")
RES = []


def check(name, ok, detail=""):
    RES.append((name, bool(ok)))
    print(f"[{'PASS' if ok else 'FAIL'}] {name} {detail}", flush=True)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def layout(root):
    """Kaggle input (chb01_01 absent, chb11_02 one byte changed) + fake PhysioNet trees with SHA256SUMS.txt."""
    inp = root / "input" / RAWNAME
    for db, src in (("chbmit", root / "chbmit"), ("siena", root / "siena")):
        phys = root / "physionet" / db
        shutil.copytree(src, phys)
        lines = [f"{sha(p)}  {p.relative_to(phys).as_posix()}" for p in sorted(phys.rglob("*")) if p.is_file()]
        (phys / "SHA256SUMS.txt").write_text("\n".join(lines) + "\n")
        shutil.copytree(src, inp / db)
    (inp / "chbmit" / "chb01" / "chb01_01.edf").unlink()
    p = inp / "chbmit" / "chb11" / "chb11_02.edf"
    b = bytearray(p.read_bytes())
    b[-11] ^= 0xFF
    p.write_bytes(bytes(b))


def nb_env(root, tag):
    return dict(R2_TEST="1", R2_TEST_REPO=str(root / "repo"), R2_TEST_INPUT=str(root / "input"),
                R2_TEST_WORK=str(root / f"work_{tag}"), R2_TEST_SCRATCH=str(root / f"scratch_{tag}"),
                R2_PHYSIONET_CHBMIT=(root / "physionet" / "chbmit").as_uri() + "/",
                R2_PHYSIONET_SIENA=(root / "physionet" / "siena").as_uri() + "/",
                R2_TEST_EARLIER_MISSING=json.dumps({"chb11": ["chb11_12.edf"]}),
                R2_TEST_RB1C_CASES="chb01,chb11,chb12,chb24,PN05",
                R2_TEST_RB_REFERENTIAL=json.dumps({f: T.sha(root / "chbmit" / "chb12" / f) for f in W.REFERENTIAL}))


def unzip(root, tag):
    z = root / f"work_{tag}" / "rb1c_results.zip"
    dest = root / f"unzip_{tag}"
    shutil.rmtree(dest, ignore_errors=True)
    if z.exists():
        zipfile.ZipFile(z).extractall(dest)
    return z.exists(), dest / "rb1c"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default="/tmp/rb1c_nb")
    a = ap.parse_args()
    t0 = time.time()
    root, repo, chb, refmap, K = W.build_world(a.root)
    rc, txt, direct = W.run(root, "direct")
    check("direct run of r2_rb1c.py on the world: exit 0", rc == 0)
    layout(root)
    nb = NB.build()
    shutil.copytree(ROOT / "notebooks", repo / "notebooks", dirs_exist_ok=True)

    ns, err = T.run_notebook(nb, nb_env(root, "ok"))
    check("RB1C_SURVEY: every cell ran, no STOP", err is None, str(err)[:300])
    have, out = unzip(root, "ok")
    files = sorted(p.name for p in out.iterdir()) if out.exists() else []
    check("archive rb1c_results.zip holds rb1c/ with every table, run.log, rb1c.json, SUMMARY.md, kaggle_inventory",
          have and set(TABLES) | {"run.log", "rb1c.json", "SUMMARY.md", "kaggle_inventory"} <= set(files), str(files))
    inv = __import__("pandas").read_csv(out / "kaggle_inventory" / "inventory.csv")
    src = dict(zip(inv.file, inv.source))
    check("inventory: chb01_01 (absent) and chb11_02 (Kaggle copy differs) taken from PhysioNet; the rest from Kaggle",
          src.get("chb01_01.edf") == "physionet: absent on Kaggle" and src.get("chb11_02.edf") == "physionet: Kaggle copy differs"
          and sum(str(s).startswith("physionet") for s in src.values()) == 2, str({k: v for k, v in src.items() if "physionet" in str(v)}))
    R = json.loads((out / "rb1c.json").read_text())
    st = {c: {k: v["status"] for k, v in g.items()} for c, g in R["gates"].items()}
    check("every gate PASS (chb24 flags NOT GATED)",
          all(s == "PASS" for c, g in st.items() for k, s in g.items() if not (c == "chb24" and k == "G-flags"))
          and st.get("chb24", {}).get("G-flags") == "NOT GATED" and len(st) == 5, str(st))
    same = {f: (out / f).read_bytes() == (direct / f).read_bytes() for f in TABLES}
    check("the five tables are byte-equal to the direct run (view of symlinks + inventory change nothing)",
          all(same.values()), str(same))
    meta = json.loads((out / "kaggle_inventory" / "run_meta.json").read_text())
    check("run metadata: commit, exit code 0, phases (inventory, rb1c), procs",
          meta.get("repo_commit") == NB.COMMIT and meta.get("rb1c_exit_code") == 0 and "rb1c" in meta.get("phases_s", {})
          and "inventory" in meta.get("phases_s", {}) and meta.get("procs") >= 1, str({k: meta.get(k) for k in ("rb1c_exit_code", "procs", "phases_s")}))

    # failure path
    g = repo / "results" / "r2" / "r1_system" / "run" / "data_gate.json"
    keep = g.read_bytes()
    d = json.loads(keep)
    d["detail"]["chb01"]["counts"]["flag5sd"] += 1
    g.write_text(json.dumps(d))
    ns, err = T.run_notebook(nb, nb_env(root, "neg"))
    g.write_bytes(keep)
    have, out = unzip(root, "neg")
    Rn = json.loads((out / "rb1c.json").read_text()) if (out / "rb1c.json").exists() else {}
    check("STOP path: r2_rb1c stops at G-flags chb01; END archives rb1c.json + run.log (no cache), then raises STOPPED",
          err is not None and "STOPPED: r2_rb1c exit code" in err and have and (out / "run.log").exists()
          and any("G-flags chb01" in s for s in Rn.get("stopped", [])) and not (out / "_cache").exists(), f"{str(err)[:120]} | {Rn.get('stopped')}")

    n_ok = sum(r[1] for r in RES)
    print(f"\n{n_ok}/{len(RES)} checks PASS in {time.time() - t0:.0f} s")
    print("ALL PASS" if n_ok == len(RES) else "FAILURES: " + "; ".join(r[0] for r in RES if not r[1]))
    sys.exit(0 if n_ok == len(RES) else 1)


if __name__ == "__main__":
    main()
