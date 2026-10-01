#!/usr/bin/env python
"""
diag_loss_decomposition.py -- docs/CC_PROMPT_LOSS_DECOMPOSITION.md: which windows make the
continuous-timeline score fail.

Read-only diagnostic on CACHED scores -- nothing is recomputed, tuned or committed except
this script and its outputs. No EDF is read, no model is run.

Inputs (all read-only):
  - Scope T fused scores per window (A2 cache, results/continuous_eval/cache/scores/T_{subj}.npy)
    for the 3 validation + 8 test patients, and per-branch robust-z scores (zrecon/zlatent/
    zgamma, results/continuous_eval/cache/scores/T_c1_{subj}_components.npz) for whichever
    subject(s) that cache exists for (currently chb17 only -- Amendment A7's own per-branch
    diagnostic, src/continuous_eval.py).
  - The application v3 headless fused scores for the 3 validation patients
    (results/app_eval_v3/cache/{subj}_scores.npz, src/app_val_op.py's own cache -- read
    directly here, NOT via importing app_val_op.py, to avoid that module's heavy top-level
    imports (pipeline_demo/torch) for what is a pure cache read).
  - The thesis's own +-5 SD artifact flag and signal-loss flag per window (results/
    continuous_eval/cache/mask/{subj}.npz's is_artifact/is_signal_loss -- src/continuous_eval.py's
    own compute_artifact_flags/compute_signal_loss_flags, already baked into the cache).
  - The annotation, for labelling categories only -- is_ictal and sz_ranges are themselves
    already the annotation, baked into the same mask cache; nothing is re-derived from EDFs.

Window categories (docs' own list, each window gets EXACTLY one, in this priority order):
  ictal > signal-loss > post-ictal 0-2min > post-ictal 2-10min > post-ictal 10-60min >
  post-ictal 1-4h > artifact (+-5 SD rule) > other background.
"Post-ictal x" is measured from the annotated OFFSET of the most recent seizure in the SAME
file (file boundaries from the cache's own `spans`) -- exactly preprocessing.build_buffer_mask's
own per-file, 4h convention (BUFFER_S = 4*3600s), which is already baked into the cache's
is_buffer flag; this script only recovers, for each is_buffer window, how many minutes have
elapsed since that nearest preceding same-file offset, to pick which of the four sub-buckets
it falls in (is_buffer's own 4h span exactly covers all four, by construction).

Report, per patient and pooled, separately for VALIDATION (both scorers: Scope T and the
application v3) and TEST (Scope T only) -- six items (module docstring order mirrors
docs/CC_PROMPT_LOSS_DECOMPOSITION.md's own numbered list):
  1. Count and hours per category.
  2. AUROC of ictal windows against each negative category ALONE (pairwise, ictal-vs-that-
     category-only), per patient and POOLED (concatenated windows across patients, not an
     average of per-patient AUROCs).
  3. Macro window AUROC (nanmean of per-patient AUROCs, ictal vs every other window) over all
     windows, and with each negative category removed from the negatives in turn.
  4. Composition of the highest-scoring negatives: share of each category among the top 1%
     and top 5% of non-ictal windows by fused score, per patient and pooled.
  5. Per branch (zrecon/zlatent/zgamma), item 2's AUROC-per-category, for whichever subject(s)
     have the c1-components cache (chb17 only, currently).
  6. Event level, Scope T ONLY, at the two already-selected fixed operating points
     results/continuous_eval/stepA_selected.json records (mag_pct/pen_mult/merge_s):
     "fixed_50_2_0" = 50/2.0/90, and the Amendment A8 reported point = 75/5/300 -- no new
     selection happens here. Category of the ONSET window of every FALSE ALARM (a detected
     event matching no annotated seizure, szcore_eval.per_interval_match's own assignment),
     as counts and shares, per patient and pooled.

Design decisions are never taken from the test table (it is descriptive only) -- trivially
satisfied here since this script selects nothing; both sections are produced the same way.

Usage
-----
  python src/diag_loss_decomposition.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from sklearn.metrics import roc_auc_score

ROOT = Path(__file__).resolve().parents[1]
for _p in (ROOT / "src",):
    if str(_p) not in sys.path:
        sys.path.insert(0, str(_p))

import cpd_pipeline_v14 as V14                                    # noqa: E402 -- read-only, locked
from szcore_eval import per_interval_match                         # noqa: E402 -- reused, not retyped

VAL_SUBJS = ["chb10", "chb11", "chb22"]
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
ALL_SUBJS = VAL_SUBJS + TEST_SUBJS

WIN_SEC = V14.WIN_SEC_DEFAULT  # 4

CONT_CACHE = ROOT / "results" / "continuous_eval" / "cache"
APP_V3_CACHE = ROOT / "results" / "app_eval_v3" / "cache"
OUT_DIR = ROOT / "results" / "continuous_eval" / "loss_decomposition"

# Priority order (ictal highest); used both for category assignment and table row order.
CATEGORIES = ["ictal", "signal_loss", "post_ictal_0_2min", "post_ictal_2_10min",
             "post_ictal_10_60min", "post_ictal_1_4h", "artifact", "background"]
NEG_CATEGORIES = [c for c in CATEGORIES if c != "ictal"]

# results/continuous_eval/stepA_selected.json -- both already selected on validation by
# src/continuous_eval.py; reused as-is, no new selection happens in this script.
FIXED_POINTS = [("50_2_0_90", 50.0, 2.0, 90), ("75_5_300", 75.0, 5.0, 300)]


class DiagError(Exception):
    """Fail-fast: the message is meant to be read directly."""


def log(tag, msg):
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    line = f"[{tag}] {time.strftime('%Y-%m-%d %H:%M:%S')} {msg}"
    print(line, flush=True)
    with open(OUT_DIR / "run.log", "a", encoding="utf-8") as f:
        f.write(line + "\n")


# ---------------------------------------------------------------------------------------
# Loading (cache-only -- no EDF, no model)
# ---------------------------------------------------------------------------------------
def load_mask(subj):
    z = np.load(CONT_CACHE / "mask" / f"{subj}.npz", allow_pickle=True)
    return dict(is_ictal=z["is_ictal"], is_buffer=z["is_buffer"], is_artifact=z["is_artifact"],
               is_signal_loss=z["is_signal_loss"],
               sz_ranges=[tuple(int(v) for v in x) for x in z["sz_ranges"]],
               spans=[tuple(x) for x in z["spans"]])


def load_scope_t_score(subj):
    path = CONT_CACHE / "scores" / f"T_{subj}.npy"
    if not path.exists():
        raise DiagError(f"{subj}: missing Scope T score cache ({path})")
    return np.load(path).astype(np.float64)


def components_cache_path(subj):
    return CONT_CACHE / "scores" / f"T_c1_{subj}_components.npz"


def load_branch_scores(subj):
    """zr/zl/zg (zrecon/zlatent/zgamma robust-z components), only for subjects whose
    Amendment-A7 per-branch cache exists (chb17, currently) -- "if cached" (docs item 5).
    Returns None when not cached, never recomputes."""
    path = components_cache_path(subj)
    if not path.exists():
        return None
    z = np.load(path, allow_pickle=True)
    return dict(zrecon=z["zr"].astype(np.float64), zlatent=z["zl"].astype(np.float64),
               zgamma=z["zg"].astype(np.float64))


def load_app_v3_score(subj, spans):
    """Concatenates the application v3 headless fused score (src/app_val_op.py's own cache,
    results/app_eval_v3/cache/{subj}_scores.npz) in the SAME file order as the mask cache's
    own `spans`, so it lands on the exact same global window-index timeline as is_ictal/
    is_artifact/etc. Reads the npz directly (not via importing app_val_op.py, which pulls in
    pipeline_demo/torch at module load for what is here a plain cache read)."""
    path = APP_V3_CACHE / f"{subj}_scores.npz"
    if not path.exists():
        raise DiagError(f"{subj}: missing application v3 score cache ({path}) -- "
                        f"src/app_val_op.py must have already run.")
    z = np.load(path, allow_pickle=False)
    parts = []
    for (fname, s, e) in spans:
        key = f"score__{str(fname).replace('.', '_')}"
        if key not in z:
            raise DiagError(f"{subj}/{fname}: app v3 cache missing key {key!r}")
        arr = np.asarray(z[key], dtype=np.float64)
        if len(arr) != (int(e) - int(s)):
            raise DiagError(f"{subj}/{fname}: app v3 score length {len(arr)} != "
                            f"mask span length {int(e) - int(s)} -- caches disagree on "
                            f"this file's window count.")
        parts.append(arr)
    return np.concatenate(parts)


# ---------------------------------------------------------------------------------------
# Window categories
# ---------------------------------------------------------------------------------------
def compute_post_ictal_minutes(sz_ranges, spans, is_buffer):
    """For every is_buffer window, minutes elapsed since the nearest preceding seizure
    OFFSET in the SAME file (spans gives file boundaries in the same global window-index
    space sz_ranges/is_buffer use). is_buffer itself (preprocessing.build_buffer_mask, baked
    into the cache) never crosses a file boundary and is only ever set following a same-file
    seizure offset, so every True entry here is expected to resolve to a finite value."""
    import bisect
    n = len(is_buffer)
    minutes = np.full(n, np.nan, dtype=np.float64)
    for (fname, s, e) in spans:
        s, e = int(s), int(e)
        local_sz_ends = sorted(se for (ss, se) in sz_ranges if s <= se <= e)
        if not local_sz_ends:
            continue
        for i in (np.nonzero(is_buffer[s:e])[0] + s):
            i = int(i)
            pos = bisect.bisect_right(local_sz_ends, i)
            if pos == 0:
                continue
            minutes[i] = (i - local_sz_ends[pos - 1]) * WIN_SEC / 60.0
    return minutes


def assign_categories(is_ictal, is_signal_loss, is_buffer, is_artifact, post_ictal_minutes):
    """Priority order low-to-high (each later assignment overrides earlier ones): background
    < artifact < post-ictal sub-bucket < signal-loss < ictal -- i.e. exactly docs' own
    'ictal > signal-loss > post-ictal buckets > artifact > background' read in reverse."""
    n = len(is_ictal)
    cat = np.full(n, "background", dtype=object)
    cat[is_artifact] = "artifact"
    # A window can be BOTH is_ictal and is_buffer (build_buffer_mask works in seconds; a
    # window straddling a seizure's offset has its tail seconds >= offset, so wb is True,
    # while wl is also True because an earlier second in the same window is still ictal).
    # Such a window is always re-labelled "ictal" below regardless, so only non-ictal buffer
    # windows need a resolvable post-ictal bucket here.
    buf_idx = np.nonzero(is_buffer & (~is_ictal))[0]
    for i in buf_idx:
        m = post_ictal_minutes[i]
        if not np.isfinite(m):
            raise DiagError(f"non-ictal is_buffer window {i} has no computable post-ictal "
                            f"time -- same-file preceding seizure offset not found.")
        if m < 2:
            cat[i] = "post_ictal_0_2min"
        elif m < 10:
            cat[i] = "post_ictal_2_10min"
        elif m < 60:
            cat[i] = "post_ictal_10_60min"
        else:
            cat[i] = "post_ictal_1_4h"
    cat[is_signal_loss] = "signal_loss"
    cat[is_ictal] = "ictal"
    return cat


def load_subject(subj):
    mask = load_mask(subj)
    n = len(mask["is_ictal"])
    post_min = compute_post_ictal_minutes(mask["sz_ranges"], mask["spans"], mask["is_buffer"])
    category = assign_categories(mask["is_ictal"], mask["is_signal_loss"], mask["is_buffer"],
                                 mask["is_artifact"], post_min)
    scope_t = load_scope_t_score(subj)
    if len(scope_t) != n:
        raise DiagError(f"{subj}: Scope T score length ({len(scope_t)}) != mask length ({n})")
    data = dict(subject=subj, mask=mask, category=category, scope_t=scope_t, n_windows=n,
               branches=load_branch_scores(subj))
    if subj in VAL_SUBJS:
        app_v3 = load_app_v3_score(subj, mask["spans"])
        if len(app_v3) != n:
            raise DiagError(f"{subj}: app v3 score length ({len(app_v3)}) != mask length ({n})")
        data["app_v3"] = app_v3
    return data


# ---------------------------------------------------------------------------------------
# Item 1 -- count/hours per category
# ---------------------------------------------------------------------------------------
def category_counts_table(all_data, subjs):
    rows = []
    for s in subjs:
        cat = all_data[s]["category"]
        for c in CATEGORIES:
            n = int((cat == c).sum())
            rows.append(dict(subject=s, category=c, n_windows=n, hours=round(n * WIN_SEC / 3600.0, 4)))
    for c in CATEGORIES:
        n = sum(int((all_data[s]["category"] == c).sum()) for s in subjs)
        rows.append(dict(subject="POOLED", category=c, n_windows=n, hours=round(n * WIN_SEC / 3600.0, 4)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Item 2 -- AUROC of ictal windows against each negative category ALONE
# ---------------------------------------------------------------------------------------
def _pairwise_auroc(is_ictal, score, neg_mask):
    n_pos, n_neg = int(is_ictal.sum()), int(neg_mask.sum())
    if n_pos == 0 or n_neg == 0:
        return float("nan"), n_pos, n_neg
    y = np.concatenate([np.ones(n_pos), np.zeros(n_neg)])
    sc = np.concatenate([score[is_ictal], score[neg_mask]])
    return float(roc_auc_score(y, sc)), n_pos, n_neg


def item2_table(all_data, subjs, score_key):
    rows = []
    for c in NEG_CATEGORIES:
        row = dict(category=c)
        for s in subjs:
            d = all_data[s]
            auc, n_pos, n_neg = _pairwise_auroc(d["mask"]["is_ictal"], d[score_key],
                                                d["category"] == c)
            row[s] = round(auc, 4) if auc == auc else float("nan")
        cat_all = np.concatenate([all_data[s]["category"] for s in subjs])
        score_all = np.concatenate([all_data[s][score_key] for s in subjs])
        ictal_all = np.concatenate([all_data[s]["mask"]["is_ictal"] for s in subjs])
        auc, n_pos, n_neg = _pairwise_auroc(ictal_all, score_all, cat_all == c)
        row["POOLED"] = round(auc, 4) if auc == auc else float("nan")
        row["n_ictal_pooled"] = n_pos
        row["n_category_pooled"] = n_neg
        rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Item 3 -- macro window AUROC, all windows and with each category removed in turn
# ---------------------------------------------------------------------------------------
def _macro_auroc(all_data, subjs, score_key, remove_cat=None):
    per_subj = {}
    for s in subjs:
        d = all_data[s]
        is_ictal = d["mask"]["is_ictal"]
        keep = np.ones(d["n_windows"], dtype=bool) if remove_cat is None else (d["category"] != remove_cat)
        y = is_ictal[keep].astype(int)
        sc = d[score_key][keep]
        per_subj[s] = float(roc_auc_score(y, sc)) if 0 < y.sum() < len(y) else float("nan")
    macro = float(np.nanmean(list(per_subj.values())))
    return macro, per_subj


def item3_table(all_data, subjs, score_key):
    rows = []
    macro, per_subj = _macro_auroc(all_data, subjs, score_key, remove_cat=None)
    rows.append(dict(removed_category="(none, all windows)", macro_auroc=round(macro, 4),
                     **{s: round(v, 4) if v == v else float("nan") for s, v in per_subj.items()}))
    for c in NEG_CATEGORIES:
        macro, per_subj = _macro_auroc(all_data, subjs, score_key, remove_cat=c)
        rows.append(dict(removed_category=c, macro_auroc=round(macro, 4),
                         **{s: round(v, 4) if v == v else float("nan") for s, v in per_subj.items()}))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Item 4 -- composition of the top 1%/5% non-ictal windows by fused score
# ---------------------------------------------------------------------------------------
def item4_table(all_data, subjs, score_key, pct):
    rows = []
    for s in list(subjs) + ["POOLED"]:
        if s == "POOLED":
            nonictal_scores = np.concatenate(
                [all_data[s2][score_key][~all_data[s2]["mask"]["is_ictal"]] for s2 in subjs])
            nonictal_cats = np.concatenate(
                [all_data[s2]["category"][~all_data[s2]["mask"]["is_ictal"]] for s2 in subjs])
        else:
            nonictal = ~all_data[s]["mask"]["is_ictal"]
            nonictal_scores = all_data[s][score_key][nonictal]
            nonictal_cats = all_data[s]["category"][nonictal]
        n = len(nonictal_scores)
        k = max(1, int(round(n * pct / 100.0)))
        top_cats = nonictal_cats[np.argsort(nonictal_scores)[-k:]]
        for c in NEG_CATEGORIES:
            share = float((top_cats == c).sum()) / k
            rows.append(dict(subject=s, pct=pct, k=k, category=c, share=round(share, 4)))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Item 5 -- per-branch AUROC-per-category, only where the c1 components cache exists
# ---------------------------------------------------------------------------------------
def item5_table(all_data, subjs):
    rows = []
    for s in subjs:
        br = all_data[s]["branches"]
        if br is None:
            continue
        for branch_name, branch_score in br.items():
            d = all_data[s]
            if len(branch_score) != d["n_windows"]:
                raise DiagError(f"{s}: branch {branch_name} length {len(branch_score)} != "
                                f"mask length {d['n_windows']}")
            for c in NEG_CATEGORIES:
                auc, n_pos, n_neg = _pairwise_auroc(d["mask"]["is_ictal"], branch_score,
                                                    d["category"] == c)
                rows.append(dict(subject=s, branch=branch_name, category=c,
                                 auroc=round(auc, 4) if auc == auc else float("nan"),
                                 n_ictal=n_pos, n_category=n_neg))
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# Item 6 -- event level at the two fixed Scope T points: category of every FA's onset window
# ---------------------------------------------------------------------------------------
def false_alarm_categories(all_data, subjs, mag, pen, merge_s):
    rows = []
    pooled_counts = {c: 0 for c in CATEGORIES}
    pooled_fa = 0
    for s in subjs:
        d = all_data[s]
        mask = d["mask"]
        inter_mask = (~mask["is_ictal"]) & (~mask["is_buffer"]) & (~mask["is_artifact"]) & (~mask["is_signal_loss"])
        ev = V14.detect_events(d["scope_t"], pen, min_mag_pct=mag, local_win=15,
                               win_sec=WIN_SEC, inter_mask=inter_mask, merge_s=merge_s)
        ref_iv = [(ss * WIN_SEC, se * WIN_SEC) for (ss, se) in mask["sz_ranges"]]
        total_dur_s = d["n_windows"] * WIN_SEC
        matches = per_interval_match(ref_iv, ev, total_dur_s) if ev else []
        counts = {c: 0 for c in CATEGORIES}
        n_fa = 0
        for e, m in zip(ev, matches):
            if m["matched"]:
                continue
            onset_win = min(int(round(e[0] / WIN_SEC)), d["n_windows"] - 1)
            counts[d["category"][onset_win]] += 1
            n_fa += 1
        for c in CATEGORIES:
            pooled_counts[c] += counts[c]
        pooled_fa += n_fa
        row = dict(subject=s, n_false_alarms=n_fa)
        for c in CATEGORIES:
            row[f"n_{c}"] = counts[c]
            row[f"share_{c}"] = round(counts[c] / n_fa, 4) if n_fa else float("nan")
        rows.append(row)
    row = dict(subject="POOLED", n_false_alarms=pooled_fa)
    for c in CATEGORIES:
        row[f"n_{c}"] = pooled_counts[c]
        row[f"share_{c}"] = round(pooled_counts[c] / pooled_fa, 4) if pooled_fa else float("nan")
    rows.append(row)
    return pd.DataFrame(rows)


# ---------------------------------------------------------------------------------------
# SUMMARY.md
# ---------------------------------------------------------------------------------------
def _section(title):
    return ["", f"## {title}", ""]


def build_summary(all_data, categories_df, fa_df):
    lines = ["# Loss decomposition -- which windows make the continuous-timeline score fail -- SUMMARY", ""]
    lines.append(
        "docs/CC_PROMPT_LOSS_DECOMPOSITION.md. Read-only diagnostic on cached scores; nothing "
        "recomputed, tuned or committed except this script and its outputs. Window categories "
        "(each window exactly one, priority order): ictal, signal-loss, post-ictal 0-2min, "
        "post-ictal 2-10min, post-ictal 10-60min, post-ictal 1-4h, artifact (+-5 SD rule), "
        "other background. Design decisions are taken on validation (chb10, chb11, chb22) "
        "only; the test table below is descriptive and was not used to choose anything -- "
        "this script selects nothing itself."
    )

    for split_key, split_name, subjs, score_keys in [
        ("validation", "VALIDATION (chb10, chb11, chb22)", VAL_SUBJS,
         [("scope_t", "Scope T"), ("app_v3", "Application v3")]),
        ("test", "TEST (chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18)", TEST_SUBJS,
         [("scope_t", "Scope T")]),
    ]:
        lines.extend(_section(split_name))

        lines.extend(_section("Item 1 -- count and hours per category"))
        # categories_df stacks both splits' rows (including each split's own POOLED rows)
        # under one table, disambiguated by the `split` column.
        sub_df = categories_df[categories_df.split == split_key]
        lines.append("```")
        lines.append(sub_df[["subject", "category", "n_windows", "hours"]].to_string(index=False))
        lines.append("```")

        for score_key, score_label in score_keys:
            lines.extend(_section(f"Item 2 -- AUROC, ictal vs. each negative category alone ({score_label})"))
            lines.append("```")
            lines.append(item2_table(all_data, subjs, score_key).to_string(index=False))
            lines.append("```")

            lines.extend(_section(f"Item 3 -- macro window AUROC, all windows and with each "
                                  f"category removed in turn ({score_label})"))
            lines.append("```")
            lines.append(item3_table(all_data, subjs, score_key).to_string(index=False))
            lines.append("```")

            lines.extend(_section(f"Item 4 -- composition of the top 1%/5% non-ictal windows "
                                  f"by fused score ({score_label})"))
            lines.append("```")
            t1 = item4_table(all_data, subjs, score_key, 1.0)
            t5 = item4_table(all_data, subjs, score_key, 5.0)
            lines.append(pd.concat([t1, t5], ignore_index=True).to_string(index=False))
            lines.append("```")

        lines.extend(_section("Item 5 -- per-branch AUROC per category (only where the "
                              "Amendment A7 c1-components cache exists)"))
        it5 = item5_table(all_data, subjs)
        if len(it5):
            lines.append(f"Cached for: {', '.join(sorted(it5.subject.unique()))}.")
            lines.append("```")
            lines.append(it5.to_string(index=False))
            lines.append("```")
        else:
            lines.append("(no subject in this split has the per-branch components cache)")

        lines.extend(_section("Item 6 -- event level, Scope T, category of every false "
                              "alarm's onset window"))
        for label, mag, pen, ms in FIXED_POINTS:
            lines.append("")
            lines.append(f"**mag_pct={mag:g} pen_mult={pen:g} merge_s={ms:g}** (point `{label}`, "
                         f"already selected on validation -- results/continuous_eval/stepA_selected.json)")
            lines.append("")
            sub_fa = fa_df[(fa_df.split == split_key) & (fa_df.point == label)]
            cols = ["subject", "n_false_alarms"] + [f"n_{c}" for c in CATEGORIES] + [f"share_{c}" for c in CATEGORIES]
            lines.append("```")
            lines.append(sub_fa[cols].to_string(index=False))
            lines.append("```")

    lines.append("")
    return "\n".join(lines)


def write_readme():
    (OUT_DIR / "README.md").write_text(
        "# results/continuous_eval/loss_decomposition/ -- producing script\n\n"
        "`SUMMARY.md`, `categories.csv`, `fa_categories.csv`, `run.log` <- "
        "`src/diag_loss_decomposition.py` (docs/CC_PROMPT_LOSS_DECOMPOSITION.md). Reads only "
        "results/continuous_eval/cache/ (mask + Scope T scores + per-branch components where "
        "cached) and results/app_eval_v3/cache/ (application v3 fused scores, validation "
        "subjects only) -- no EDF is read, no model is run, nothing is recomputed.\n",
        encoding="utf-8")


def run():
    t0 = time.time()
    OUT_DIR.mkdir(parents=True, exist_ok=True)

    log("LOAD", f"loading cached masks + Scope T scores (+ app v3 scores for validation, + "
               f"per-branch components where cached) for {len(ALL_SUBJS)} subjects -- no EDF "
               f"read, no model run")
    all_data = {s: load_subject(s) for s in ALL_SUBJS}
    for s in ALL_SUBJS:
        log("LOAD", f"{s}: {all_data[s]['n_windows']} windows, branches_cached="
                   f"{all_data[s]['branches'] is not None}")

    cat_parts = []
    for split_name, subjs in [("validation", VAL_SUBJS), ("test", TEST_SUBJS)]:
        cat_parts.append(category_counts_table(all_data, subjs).assign(split=split_name))
    categories_df = pd.concat(cat_parts, ignore_index=True)
    categories_df.to_csv(OUT_DIR / "categories.csv", index=False)
    log("ITEM1", f"categories.csv written ({len(categories_df)} rows)")

    fa_parts = []
    for split_name, subjs in [("validation", VAL_SUBJS), ("test", TEST_SUBJS)]:
        for label, mag, pen, ms in FIXED_POINTS:
            t0_fa = time.time()
            df = false_alarm_categories(all_data, subjs, mag, pen, ms)
            fa_parts.append(df.assign(split=split_name, point=label))
            log("ITEM6", f"{split_name}/{label} (mag={mag:g} pen={pen:g} merge={ms:g}): "
                        f"pooled {df[df.subject == 'POOLED'].n_false_alarms.iloc[0]} false "
                        f"alarms ({time.time() - t0_fa:.1f}s)")
    fa_df = pd.concat(fa_parts, ignore_index=True)
    fa_df.to_csv(OUT_DIR / "fa_categories.csv", index=False)
    log("ITEM6", f"fa_categories.csv written ({len(fa_df)} rows)")

    summary = build_summary(all_data, categories_df, fa_df)
    (OUT_DIR / "SUMMARY.md").write_text(summary, encoding="utf-8")
    write_readme()

    elapsed = time.time() - t0
    log("DONE", f"SUMMARY.md written. total wall-clock: {elapsed / 60:.1f} min")


if __name__ == "__main__":
    run()
