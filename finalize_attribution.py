"""
finalize_attribution.py — closes the attribution redesign in the record.
Performs the 4 remaining bookkeeping actions. DRY-RUN by default; --apply to write.

  1. Append Addendum 1 then Addendum 2 to ATTRIBUTION_PREREGISTRATION_v3_1.md
     (append-only; original text never edited; skipped if already present)
  2. Replace section 7 of RESULTS_OF_RECORD.md with the new §7 text
     (writes a .bak first; verifies §6 and §8 survive intact)
  3. Move superseded attribution artifacts to results/history_superseded/
  4. Append the decision-log entry to PLAN_AND_STATUS.md

USAGE
  python finalize_attribution.py                # dry run, shows every action
  python finalize_attribution.py --apply        # actually do it
"""
import argparse
import os
import re
import shutil
import sys
from datetime import date

ROOT = "."
PREREG = "ATTRIBUTION_PREREGISTRATION_v3_1.md"
ROR = "RESULTS_OF_RECORD.md"
PLAN = "PLAN_AND_STATUS.md"
ADD1 = "ATTRIBUTION_PREREG_v3_1_ADDENDUM_2026-07-19.md"
ADD2 = "ATTRIBUTION_PREREG_v3_1_ADDENDUM_2_2026-07-19.md"
SEC7 = "RESULTS_OF_RECORD_section7_REPLACEMENT.md"
QUAR = os.path.join("results", "history_superseded")

QUARANTINE_GLOBS = [
    "attribution_pernode_summary.csv", "attribution_pernode_*.csv",
    "attribution_out", "attribution_c1_*.csv", "attribution_c2_*.csv",
    "attribution_c3_*.csv", "results/phaseB/attribution_*",
]

DECISION_LOG = """
### Decision #23 — Attribution redesign closed, two pre-registered negative results ({d})
Executed under `ATTRIBUTION_PREREGISTRATION_v3.1`; outcomes recorded in Addendum 1 (Test A)
and Addendum 2 (Test D), both append-only and dated.
- **Test A → A3 (indeterminate).** Sign test p = 0.289 (6 neg / 2 pos); median signed
  deviation -0.0114 [-0.0272, +0.0225]; 0/8 subjects significant after BH-FDR.
  The pre-registered expectation (A1, distributed) was NOT confirmed.
- **Test D → D1 and D2 both FAIL.** Incremental AUROC +0.0106 [-0.0158, +0.0172],
  permutation p = 0.356; concentration-alone AUROC 0.530 [0.444, 0.620]. D3 not computed
  (correctly gated). D4 indistinguishable. Harness reproduced the lock exactly
  (TP 57/76, FP 461, sens 0.750, FP/day 39.77) before any result was read.
- **§5 faithfulness NOT reinstated** — its trigger (A2) never fired.
- **Disclosed:** v1 null was mathematically degenerate; older top-k mass is a different
  estimand; 22/65 TP events (and 0/461 FP) lack per-node data, TP-specific by construction,
  so chb06 drops out of D1 (7 subjects, not 8). Remediation = GPU re-export, future work.
- **Claim scope, binding:** evidence-surfacing display for human EEG review. No triage,
  no concentration claim, no localization under any outcome.
- Withdrawn from the old §7: "DISTRIBUTED", "seizure-specific 6/8", "faithful 5/8",
  eigencentrality convergent check.
- Phase C: channel heat-map may be shown, labelled "unvalidated display".
Decided by Claude under delegation of {d}; Boti retains veto.
""".format(d=date.today().isoformat())


def find(name):
    """Locate a governance/source file anywhere under the tree (they may live in
    docs/, notes/, etc. rather than the repo root)."""
    if os.path.exists(name):
        return name
    import glob as _g
    hits = [h for h in _g.glob(os.path.join("**", name), recursive=True)
            if "history_superseded" not in h.replace("\\", "/")]
    return hits[0] if hits else None


def say(ok, msg):
    print(f"  [{'OK ' if ok else '!! '}] {msg}")


def do_append(target, source, marker, apply_):
    target, source = find(target), find(source)
    if target is None:
        say(False, f"{PREREG} not found anywhere under {os.path.abspath(ROOT)} — skipped")
        return
    if source is None:
        say(False, f"source addendum .md not found — put it in this folder — skipped")
        return
    body = open(target, encoding="utf-8").read()
    if marker in body:
        say(True, f"{os.path.basename(source)} already appended to {target} — skipped")
        return
    add = open(source, encoding="utf-8").read()
    if apply_:
        with open(target, "a", encoding="utf-8") as f:
            f.write("\n\n---\n\n" + add)
    say(True, f"append {os.path.basename(source)} -> {target} "
              f"({len(add)} chars){'' if apply_ else '  [dry-run]'}")


def do_section7(apply_):
    ror, sec7 = find(ROR), find(SEC7)
    if ror is None:
        say(False, f"{ROR} not found anywhere under {os.path.abspath(ROOT)} — skipped")
        return
    if sec7 is None:
        say(False, f"{SEC7} not found — put it in this folder — skipped"); return
    body = open(ror, encoding="utf-8").read()
    new = open(sec7, encoding="utf-8").read()
    new = new.split("---\n", 2)[-1] if new.lstrip().startswith("#") and "---" in new else new
    m7 = re.search(r"^##\s*7\.", body, re.M)
    m8 = re.search(r"^##\s*8\.", body, re.M)
    if not (m7 and m8 and m8.start() > m7.start()):
        say(False, "could not locate '## 7.' ... '## 8.' boundaries — DO THIS ONE BY HAND")
        return
    out = body[:m7.start()] + new.strip() + "\n\n" + body[m8.start():]
    for probe in ("## 6.", "## 8."):
        if probe not in out:
            say(False, f"refusing: {probe} would be lost"); return
    if apply_:
        shutil.copy2(ror, ror + ".bak")
        open(ror, "w", encoding="utf-8").write(out)
    say(True, f"replace §7 in {ror}: {m8.start()-m7.start()} chars -> {len(new)} "
              f"(backup {ror}.bak){'' if apply_ else '  [dry-run]'}")


def do_quarantine(apply_):
    import glob
    n, seen = 0, set()
    for pat in QUARANTINE_GLOBS:
        for p in sorted(glob.glob(pat)):
            key = os.path.normpath(p)
            if key in seen or QUAR.replace("\\", "/") in p.replace("\\", "/"):
                continue
            seen.add(key)
            dst = os.path.join(QUAR, os.path.basename(p))
            if apply_:
                os.makedirs(QUAR, exist_ok=True)
                if os.path.exists(dst):
                    shutil.rmtree(dst) if os.path.isdir(dst) else os.remove(dst)
                shutil.move(p, dst)
            say(True, f"quarantine {p} -> {dst}{'' if apply_ else '  [dry-run]'}")
            n += 1
    if n == 0:
        say(True, "no superseded attribution artifacts found (already clean)")


def do_plan(apply_):
    plan = find(PLAN)
    if plan is None:
        say(False, f"{PLAN} not found anywhere under {os.path.abspath(ROOT)} — skipped")
        return
    if "Decision #23" in open(plan, encoding="utf-8").read():
        say(True, "Decision #23 already in PLAN_AND_STATUS.md — skipped"); return
    if apply_:
        with open(plan, "a", encoding="utf-8") as f:
            f.write("\n" + DECISION_LOG)
    say(True, f"append Decision #23 -> {plan}{'' if apply_ else '  [dry-run]'}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--apply", action="store_true")
    a = ap.parse_args()
    print("=== finalize_attribution ===",
          "APPLY" if a.apply else "DRY RUN (nothing written; use --apply)", "\n")
    print("1. addenda")
    do_append(PREREG, ADD1, "ADDENDUM 1 to ATTRIBUTION_PREREGISTRATION", a.apply)
    do_append(PREREG, ADD2, "ADDENDUM 2 to ATTRIBUTION_PREREGISTRATION", a.apply)
    print("2. section 7")
    do_section7(a.apply)
    print("3. quarantine")
    do_quarantine(a.apply)
    print("4. decision log")
    do_plan(a.apply)
    print("\nDone." if a.apply else "\nDry run only. Re-run with --apply.")


if __name__ == "__main__":
    main()