#!/usr/bin/env python
"""
f1_build_partitions.py -- Track F1/F2 (docs/FUTURE_RESEARCH_PLAN.md rev 1, section 3): repeated random patient-wise
4-fold partitions of the 24 CHB-MIT cases (23 subjects; chb01 + chb21 one group). Written and committed BEFORE any
training of Track F. Annotation metadata only: the per-group seizure counts are read from results/v9_x3/folds.json
(the committed CV), no EDF or annotation file is read here, no model output is read.

Rule (pre-registered, plan rev 1 section 3; "rank blocks of 4"):
  partition r (r = 1 ... R) uses numpy.random.default_rng(r):
    1. each of the 23 groups gets a random tie-break key (one rng.random() per group, groups in folds.json order);
    2. groups are sorted by seizure count descending, ties by the random key;
    3. the sorted list is cut into consecutive blocks of 4 groups (the last block has 3);
    4. each block is dealt to the folds by a random permutation of (1, 2, 3, 4) (rng.permutation(4), first len(block)).
  -> every fold receives one group from each block of similar seizure count (stratified), the assignment inside a
     block is random. Partition 0 (the committed CV, folds.json, serpentine over a fixed ordering) is one member of
     this family: it deals every block in the order 1-2-3-4 or 4-3-2-1.
  Training seed of partition r = r (plan rev 1 O3); partition 0 keeps seed 42.

Checks (STOP on failure): every case held out exactly once per partition; chb01 and chb21 in the same fold; four
non-empty folds; train cases of a fold = all cases minus its held-out cases; no partition equal to another or to
partition 0 as a set of held-out groups (fold labels ignored).
Reported (not a selection criterion): seizures and cases per fold; adjusted Rand index of each partition vs
partition 0 and between partitions. Partitions are never regenerated or filtered after this file is committed.

Output: results/f1_repcv/partitions.json
  python src/f1_build_partitions.py [--n 10]
"""
import argparse
import hashlib
import itertools
import json
import subprocess
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
FOLDS_JSON = ROOT / "results" / "v9_x3" / "folds.json"
OUT = ROOT / "results" / "f1_repcv" / "partitions.json"
N_FOLDS, BLOCK = 4, 4


def ari(a, b):
    """adjusted Rand index of two labelings (same item order), no sklearn dependency."""
    from math import comb
    la, lb = sorted(set(a)), sorted(set(b))
    n = len(a)
    cont = np.zeros((len(la), len(lb)), int)
    for x, y in zip(a, b):
        cont[la.index(x), lb.index(y)] += 1
    s_ij = sum(comb(int(v), 2) for v in cont.ravel())
    s_a = sum(comb(int(v), 2) for v in cont.sum(1))
    s_b = sum(comb(int(v), 2) for v in cont.sum(0))
    exp = s_a * s_b / comb(n, 2)
    mx = (s_a + s_b) / 2
    return float((s_ij - exp) / (mx - exp)) if mx != exp else 1.0


def partition_r(groups, r):
    rng = np.random.default_rng(r)
    key = {g["group_id"]: float(rng.random()) for g in groups}
    order = sorted(groups, key=lambda g: (-g["seizures"], key[g["group_id"]]))
    fold_of = {}
    for b in range(0, len(order), BLOCK):
        blk = order[b:b + BLOCK]
        folds = rng.permutation(N_FOLDS)[:len(blk)] + 1
        for g, f in zip(blk, folds):
            fold_of[g["group_id"]] = int(f)
    return fold_of


def as_manifest(groups, fold_of):
    all_cases = [c for g in groups for c in g["cases"]]
    man = {}
    for k in range(1, N_FOLDS + 1):
        held = [c for g in groups if fold_of[g["group_id"]] == k for c in g["cases"]]
        man[str(k)] = dict(held_out_cases=held, train_cases=sorted(c for c in all_cases if c not in held),
                           held_out_groups=[g["group_id"] for g in groups if fold_of[g["group_id"]] == k],
                           seizures=int(sum(g["seizures"] for g in groups if fold_of[g["group_id"]] == k)))
    return man


def check(groups, man, name):
    all_cases = sorted(c for g in groups for c in g["cases"])
    held = [c for k in man for c in man[k]["held_out_cases"]]
    if sorted(held) != all_cases:
        raise SystemExit(f"STOP {name}: a case is not held out exactly once ({sorted(held)} vs {all_cases})")
    for k, v in man.items():
        if not v["held_out_cases"]:
            raise SystemExit(f"STOP {name}: fold {k} is empty")
        if sorted(v["train_cases"] + v["held_out_cases"]) != all_cases:
            raise SystemExit(f"STOP {name}: fold {k} train + held-out != all cases")
        if ("chb01" in v["held_out_cases"]) != ("chb21" in v["held_out_cases"]):
            raise SystemExit(f"STOP {name}: chb01 and chb21 split across folds")


def signature(man):
    return frozenset(frozenset(v["held_out_groups"]) for v in man.values())


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=10)
    a = ap.parse_args()
    raw = FOLDS_JSON.read_bytes()
    fj = json.loads(raw)
    groups = fj["groups"]                       # folds.json order (sorted by seizure count, ties by id)
    gids = [g["group_id"] for g in groups]
    p0_fold = {g["group_id"]: int(k) for k, v in fj["folds"].items() for g in v}
    parts = {"0": dict(seed=42, rule="committed CV (results/v9_x3/folds.json); not regenerated",
                       folds=as_manifest(groups, p0_fold), ari_vs_p0=1.0)}
    check(groups, parts["0"]["folds"], "partition 0")
    # partition 0 must equal the committed fold manifests (held-out cases per fold)
    fm = json.loads((ROOT / "results" / "v9_x3" / "fold_manifests.json").read_text())
    for k in map(str, range(1, N_FOLDS + 1)):
        if sorted(fm[k]["held_out_cases"]) != sorted(parts["0"]["folds"][k]["held_out_cases"]):
            raise SystemExit(f"STOP: partition 0 fold {k} != fold_manifests.json")
        if sorted(fm[k]["train_cases"]) != parts["0"]["folds"][k]["train_cases"]:
            raise SystemExit(f"STOP: partition 0 fold {k} train cases != fold_manifests.json")
    sigs = {signature(parts["0"]["folds"]): "0"}
    for r in range(1, a.n + 1):
        fo = partition_r(groups, r)
        man = as_manifest(groups, fo)
        check(groups, man, f"partition {r}")
        sg = signature(man)
        if sg in sigs:
            raise SystemExit(f"STOP: partition {r} equals partition {sigs[sg]}")
        sigs[sg] = str(r)
        parts[str(r)] = dict(seed=r, rule="rank blocks of 4, numpy.random.default_rng(r)", folds=man,
                             ari_vs_p0=round(ari([p0_fold[g] for g in gids], [fo[g] for g in gids]), 4))
    rnd = [str(r) for r in range(1, a.n + 1)]
    lab = {p: {g: next(int(k) for k, v in parts[p]["folds"].items() if g in v["held_out_groups"]) for g in gids}
           for p in parts}
    pair = [ari([lab[x][g] for g in gids], [lab[y][g] for g in gids]) for x, y in itertools.combinations(rnd, 2)]
    try:
        commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT).decode().strip()
    except Exception:                                                     # noqa: BLE001
        commit = None
    payload = dict(
        plan="docs/FUTURE_RESEARCH_PLAN.md rev 1, section 3",
        rule=("stratified group 4-fold, unit = subject (chb01+chb21 one group); groups sorted by seizure count "
              "(results/v9_x3/folds.json) descending, ties by a random key; consecutive blocks of 4 groups; each block "
              "dealt to the folds by a random permutation; numpy.random.default_rng(r) for partition r"),
        folds_json_sha256=hashlib.sha256(raw).hexdigest(),
        seizure_counts_by_group={g["group_id"]: g["seizures"] for g in groups},
        cases_by_group={g["group_id"]: g["cases"] for g in groups},
        pairwise_ari_random=dict(mean=round(float(np.mean(pair)), 4), max=round(float(np.max(pair)), 4)),
        git_commit_at_write=commit,
        partitions=parts,
    )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(payload, indent=1) + "\n")
    for p, v in parts.items():
        print(f"partition {p:>2} seed {v['seed']:>2}  ARI vs p0 {v['ari_vs_p0']:+.3f}  seizures/fold "
              f"{[v['folds'][k]['seizures'] for k in '1234']}  cases/fold "
              f"{[len(v['folds'][k]['held_out_cases']) for k in '1234']}")
    print(f"pairwise ARI between random partitions: {payload['pairwise_ari_random']}")
    print(f"wrote {OUT}")


if __name__ == "__main__":
    main()
