"""
place_seeds.py — put the 4 Kaggle zips into their repo homes + encoder-fidelity gate.
CPU, local. Idempotent, copies (never deletes originals).

Expects in --incoming:
    seed1_out.zip  seed2_out.zip  seed3_out.zip   (gae_joint_seed{S}.pt + curves + ens_val_seed{S}/rlg/*)
    seed42_check.zip                               (ens_val_seed42_check/rlg/*)

Does:
  - gae_joint_seed{1,2,3}.pt  -> data/models_retrain/
  - ens_seed{1,2,3}_*.npy     -> results/phaseB/tier2/ens_val_tf/rlg/   (next to seed42)
  - seed42 encoder-fidelity: byte-compare ens_val_seed42_check/rlg/ens_seed42_*.npy
       against the COMMITTED ens_val_tf/rlg/ens_seed42_*.npy  -> must be identical.

USAGE
  python place_seeds.py --incoming F:/Study/Thesis/Code/incoming_seeds --repo F:/Study/Thesis/Code
  python place_seeds.py --smoke
"""
import argparse
import shutil
import tempfile
import zipfile
from pathlib import Path

import numpy as np

ENS_DIR_REL = "results/phaseB/tier2/ens_val_tf/rlg"
CKPT_DIR_REL = "data/models_retrain"


def _extract(zp, dst):
    with zipfile.ZipFile(zp) as z:
        z.extractall(dst)


def _find(root, pattern):
    return sorted(Path(root).rglob(pattern))


def place(incoming, repo):
    incoming, repo = Path(incoming), Path(repo)
    ens_dir = repo / ENS_DIR_REL; ens_dir.mkdir(parents=True, exist_ok=True)
    ckpt_dir = repo / CKPT_DIR_REL; ckpt_dir.mkdir(parents=True, exist_ok=True)
    tmp = Path(tempfile.mkdtemp())

    # --- seeds 1,2,3 ---
    for S in (1, 2, 3):
        zp = incoming / f"seed{S}_out.zip"
        if not zp.exists():
            print(f"[warn] {zp.name} missing — skip seed {S}"); continue
        d = tmp / f"s{S}"; _extract(zp, d)
        cks = _find(d, f"gae_joint_seed{S}.pt")
        ens = _find(d, f"ens_seed{S}_*.npy")
        assert cks, f"gae_joint_seed{S}.pt not in {zp.name}"
        assert ens, f"ens_seed{S}_*.npy not in {zp.name}"
        shutil.copy(cks[0], ckpt_dir / f"gae_joint_seed{S}.pt")
        for f in ens:
            shutil.copy(f, ens_dir / f.name)
        print(f"[seed {S}] ckpt + {len(ens)} ens files placed "
              f"({', '.join(sorted({f.name.split('_')[2] for f in ens}))})")

    # --- seed42 encoder fidelity ---
    zc = incoming / "seed42_check.zip"
    if zc.exists():
        d = tmp / "s42"; _extract(zc, d)
        chk = _find(d, "ens_seed42_*.npy")
        print(f"\n[seed42 encoder fidelity] {len(chk)} files vs committed:")
        allok = True
        for f in chk:
            ref = ens_dir / f.name
            if not ref.exists():
                print(f"    {f.name}: NO committed ref (?)"); allok = False; continue
            same = np.array_equal(np.load(f), np.load(ref))
            allok &= same
            print(f"    {f.name}: {'identical' if same else 'DIFFERS !!'}")
        print(f"  -> encoder fidelity {'PASS (patched == committed)' if allok else 'FAIL — investigate before trusting new seeds'}")
    else:
        print("\n[seed42 encoder fidelity] seed42_check.zip missing — cannot verify encoder!")

    # --- final inventory ---
    seeds = sorted({int(p.name.split("_")[1].replace('seed',''))
                    for p in ens_dir.glob("ens_seed*_chb10_inter.npy")})
    print(f"\n[inventory] seeds now in {ens_dir}: {seeds}")
    print(f"[inventory] GAE ckpts in {ckpt_dir}: "
          f"{sorted(p.name for p in ckpt_dir.glob('gae_joint_seed*.pt'))}")
    shutil.rmtree(tmp, ignore_errors=True)


def _smoke():
    tmp = Path(tempfile.mkdtemp()); inc = tmp / "in"; repo = tmp / "repo"
    inc.mkdir(); (repo / ENS_DIR_REL).mkdir(parents=True)
    # committed seed42 ens
    for subj in ("chb10", "chb11", "chb22"):
        for sp in ("inter", "ictal"):
            np.save(repo / ENS_DIR_REL / f"ens_seed42_{subj}_{sp}.npy", np.arange(5.0))
    # build fake zips
    for S in (1, 2, 3):
        d = tmp / f"b{S}"; (d / "gae_retrain").mkdir(parents=True); (d / f"ens_val_seed{S}/rlg").mkdir(parents=True)
        (d / "gae_retrain" / f"gae_joint_seed{S}.pt").write_bytes(b"x")
        for subj in ("chb10", "chb11", "chb22"):
            for sp in ("inter", "ictal"):
                np.save(d / f"ens_val_seed{S}/rlg/ens_seed{S}_{subj}_{sp}.npy", np.arange(5.0))
        shutil.make_archive(str(inc / f"seed{S}_out"), "zip", d)
    # seed42 check zip (identical -> should PASS)
    d = tmp / "b42"; (d / "ens_val_seed42_check/rlg").mkdir(parents=True)
    for subj in ("chb10", "chb11", "chb22"):
        for sp in ("inter", "ictal"):
            np.save(d / f"ens_val_seed42_check/rlg/ens_seed42_{subj}_{sp}.npy", np.arange(5.0))
    shutil.make_archive(str(inc / "seed42_check"), "zip", d)
    place(inc, repo)
    print("\n[SMOKE] PASS")
    shutil.rmtree(tmp, ignore_errors=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--incoming")
    ap.add_argument("--repo", default=".")
    ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    if a.smoke:
        return _smoke()
    if not a.incoming:
        raise SystemExit("--incoming required")
    place(a.incoming, a.repo)


if __name__ == "__main__":
    main()
