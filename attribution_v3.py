"""
================================================================================
 attribution_v3.py  —  STAGE 1 of ATTRIBUTION REDESIGN (PRE-REGISTRATION v3.1)
 TEST A ONLY: attribution CONCENTRATION vs a length-matched pseudo-seizure null
================================================================================
Implements EXACTLY §3 of ATTRIBUTION_PREREGISTRATION_v3_1.md. No other test is
implemented here (Tests B/C/E are permanently dropped; Test D is Stage 2).

QUESTION (§3)
  Is the ictal attribution more, or less, spatially concentrated than baseline
  fluctuation?

STATISTIC
  Per seizure : Gini of |z| across the 18 bipolar derivations.
  Per subject : median of that subject's per-seizure Gini values.
  z_i = (mean_event r_i - median_interictal r_i) / MAD_interictal r_i   (§1.4)
  (formula and the +1e-9 MAD epsilon are kept byte-identical to
   attribution_gae_pernode.z_channels so the two are directly comparable)

NULL (§3)  length-matched pseudo-seizure draw
  For each seizure of length L windows, draw a random CONTIGUOUS interictal
  block of the SAME length L, compute |z| by the identical formula against the
  SAME interictal baseline, compute its Gini. One null replicate for the
  subject = median across that subject's seizures (i.e. the null replicates the
  full per-subject statistic, not just a single seizure). Repeated n_null times.
  Length matching is mandatory: shorter blocks give noisier means -> inflated
  Gini.

  CAVEAT (recorded, not a criterion change): the interictal per-node array is a
  concatenation of the retained interictal windows across EDF files, so a
  "contiguous" block is contiguous in that concatenated index space and may
  straddle a file boundary. This is the same index space the locked pipeline
  uses for interictal scores. Reported in the provenance JSON.

INFERENCE (§3, §1.5)
  - per subject : two-sided empirical p from the null (add-one corrected)
  - across the 8 subjects : Benjamini-Hochberg FDR at q = 0.05
    (this is the ONLY FDR family in the whole redesign, §1.5)
  - cohort : EXACT two-sided sign test on the signed deviations
             (obs Gini - null median), + subject-level bootstrap CI of the
             median signed deviation
  Two-sided is mandatory: a DISTRIBUTED signature sits markedly BELOW the null,
  so A1 is supported by active evidence (significant negative deviation), not
  by failure to reject.

MANDATORY GUARD (§7 Stage 1)
  The script ASSERTS that every null distribution contains > 1 distinct value
  before any p-value is computed. This is the regression test against the v1
  degeneracy bug (permutation null on a permutation-invariant statistic) and
  fails LOUDLY if violated.

OUTPUTS
  attribution_v3_summary.csv      one row per subject (A4 fields)
  attribution_v3_perseizure.csv   one row per seizure
  attribution_v3_cohort.csv       sign test + bootstrap CI (one row)
  attribution_v3_provenance.json  seed, n_null, inputs, versions, caveats
  attribution_v3_concentration.png

USAGE (Cursor / CPU, no GPU, no retraining)
  python attribution_v3.py \
      --pernode_root data/processed/pernode \
      --summary_dir "F:\\Study\\Thesis\\Dataset\\CHB-MIT\\CHB info\\summary" \
      --outdir results/attribution_v3

SELF-TEST (synthetic, no real data needed)
  python attribution_v3.py --selftest
================================================================================
"""
import argparse
import glob
import json
import math
import os
import platform
import sys
from datetime import datetime, timezone

import numpy as np
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

SCRIPT_VERSION = "attribution_v3.py / pre-registration v3.1 / Stage 1 (Test A)"
TEST_SUBJS = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
CH_NAMES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
            "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
            "FZ-CZ", "CZ-PZ"]
N_CH = 18
TOPK = 5
UNIFORM_TOP5_REF = TOPK / N_CH          # 0.2777...
MAD_EPS = 1e-9                          # identical to attribution_gae_pernode.py


# ----------------------------------------------------------------------------
# concentration statistics
# ----------------------------------------------------------------------------
def gini(x):
    """Gini coefficient of a non-negative vector. PRIMARY concentration measure.
    Scale-invariant; satisfies all six Hurley-Rickard (2009) criteria."""
    x = np.asarray(x, dtype=float)
    if np.any(x < 0):
        raise ValueError("gini() requires non-negative input (use |z|)")
    s = x.sum()
    if not np.isfinite(s) or s <= 0:
        return np.nan
    xs = np.sort(x)
    n = xs.size
    idx = np.arange(1, n + 1)
    return float((2.0 * np.sum(idx * xs)) / (n * s) - (n + 1.0) / n)


def norm_entropy(x):
    """Shannon entropy of x/sum(x), normalised by ln(n). 1 = uniform."""
    x = np.asarray(x, dtype=float)
    s = x.sum()
    if not np.isfinite(s) or s <= 0:
        return np.nan
    p = x / s
    p = p[p > 0]
    return float(-np.sum(p * np.log(p)) / np.log(x.size))


def topk_mass(x, k=TOPK):
    x = np.asarray(x, dtype=float)
    s = x.sum()
    if not np.isfinite(s) or s <= 0:
        return np.nan
    return float(np.sort(x)[::-1][:k].sum() / s)


def abs_z(block_feat, inter_med, inter_mad):
    """|z_i| = |(mean_block r_i - median_inter r_i) / MAD_inter r_i|  (§1.4)."""
    return np.abs((block_feat.mean(axis=0) - inter_med) / inter_mad)


# ----------------------------------------------------------------------------
# inference helpers
# ----------------------------------------------------------------------------
def two_sided_empirical_p(obs, null):
    """Add-one corrected two-sided empirical p. Never returns exactly 0."""
    null = np.asarray(null, dtype=float)
    b = null.size
    p_lo = (1.0 + np.sum(null <= obs)) / (b + 1.0)
    p_hi = (1.0 + np.sum(null >= obs)) / (b + 1.0)
    return float(min(1.0, 2.0 * min(p_lo, p_hi)))


def bh_fdr(pvals):
    """Benjamini-Hochberg adjusted q-values (monotone step-up)."""
    p = np.asarray(pvals, dtype=float)
    n = p.size
    order = np.argsort(p)
    ranked = p[order] * n / np.arange(1, n + 1)
    ranked = np.minimum.accumulate(ranked[::-1])[::-1]
    q = np.empty(n)
    q[order] = np.minimum(ranked, 1.0)
    return q


def exact_sign_test(deviations):
    """Exact two-sided sign test. Zeros are discarded (standard).
    Returns (n_used, n_positive, p_two_sided)."""
    d = np.asarray(deviations, dtype=float)
    d = d[np.isfinite(d) & (d != 0)]
    n = d.size
    k = int(np.sum(d > 0))
    if n == 0:
        return 0, 0, 1.0

    def cdf_le(j):
        return sum(math.comb(n, i) for i in range(0, j + 1)) / (2.0 ** n)

    p_le = cdf_le(k)
    p_ge = 1.0 - cdf_le(k - 1) if k > 0 else 1.0
    return n, k, float(min(1.0, 2.0 * min(p_le, p_ge)))


def bootstrap_median_ci(values, rng, n_boot=10000, alpha=0.05):
    """Subject-level bootstrap CI of the median (resample the 8 subjects)."""
    v = np.asarray(values, dtype=float)
    v = v[np.isfinite(v)]
    if v.size == 0:
        return (np.nan, np.nan)
    idx = rng.integers(0, v.size, size=(n_boot, v.size))
    meds = np.median(v[idx], axis=1)
    return (float(np.percentile(meds, 100 * alpha / 2)),
            float(np.percentile(meds, 100 * (1 - alpha / 2))))


# ----------------------------------------------------------------------------
# data loading
# ----------------------------------------------------------------------------
def find_pernode(root, subj, split):
    """split in {'inter','ictal'}. Mirrors attribution_gae_pernode.find_file."""
    excl = ["interictal", "_inter"] if split == "ictal" else []
    toks = ["interictal", "inter"] if split == "inter" else ["ictal"]
    for p in sorted(glob.glob(os.path.join(root, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj.lower() not in b or not b.endswith("pernode.npy"):
            continue
        if any(t in b for t in excl):
            continue
        if any(t in b for t in toks):
            return p
    return None


def seizure_window_blocks(subj, summary_dir, win_sec, parse_fn):
    """Per-seizure index blocks into the concatenated ICTAL per-node array.
    Verbatim logic from attribution_gae_pernode.seizure_window_blocks."""
    edfs = parse_fn(os.path.join(summary_dir, f"{subj}-summary.txt"))
    blocks, ptr = [], 0
    for edf in edfs:
        dur = int(edf["duration_s"])
        n_win = dur // win_sec
        tl = n_win * win_sec
        if tl == 0:
            continue
        sid = np.zeros(dur, dtype=np.int32)
        for k, (on, off) in enumerate(edf["seizures"], start=1):
            sid[min(on, dur):min(off, dur)] = k
        win_sid = sid[:tl].reshape(n_win, win_sec).max(axis=1)
        local = {k: [] for k in range(1, len(edf["seizures"]) + 1)}
        for w in range(n_win):
            if win_sid[w] > 0:
                local[int(win_sid[w])].append(ptr)
                ptr += 1
        for k in range(1, len(edf["seizures"]) + 1):
            if local[k]:
                blocks.append(np.array(local[k], dtype=int))
    return blocks, ptr


# ----------------------------------------------------------------------------
# core: Test A for one subject
# ----------------------------------------------------------------------------
def test_a_subject(subj, inter, ictal, blocks, rng, n_null):
    """Returns (subject_record, perseizure_records, subject_null_array)."""
    inter_med = np.median(inter, axis=0)
    inter_mad = np.median(np.abs(inter - inter_med), axis=0) + MAD_EPS
    n_inter = inter.shape[0]

    per_sz = []
    obs_g, obs_h, obs_t5, lens = [], [], [], []
    for j, blk in enumerate(blocks, start=1):
        blk = blk[blk < ictal.shape[0]]
        if blk.size == 0:
            continue
        az = abs_z(ictal[blk], inter_med, inter_mad)
        g, h, t5 = gini(az), norm_entropy(az), topk_mass(az)
        obs_g.append(g); obs_h.append(h); obs_t5.append(t5); lens.append(blk.size)
        per_sz.append(dict(subject=subj, seizure_idx=j, n_windows=int(blk.size),
                           gini=g, entropy_norm=h, top5_mass=t5,
                           top5_channels="|".join(
                               CH_NAMES[i] for i in np.argsort(az)[::-1][:TOPK])))

    if not obs_g:
        raise RuntimeError(f"{subj}: no usable seizure blocks")

    # ---- length-matched pseudo-seizure null -------------------------------
    L = np.array(lens, dtype=int)
    if np.any(L > n_inter):
        raise RuntimeError(
            f"{subj}: seizure longer ({L.max()} win) than interictal pool "
            f"({n_inter} win) - length matching impossible")

    null_per_sz = np.empty((len(L), n_null), dtype=float)
    for j, Lj in enumerate(L):
        starts = rng.integers(0, n_inter - Lj + 1, size=n_null)
        for r, s0 in enumerate(starts):
            az = abs_z(inter[s0:s0 + Lj], inter_med, inter_mad)
            null_per_sz[j, r] = gini(az)
    subj_null = np.median(null_per_sz, axis=0)          # replicates the statistic

    # ---- MANDATORY GUARD (v1 degeneracy regression test) ------------------
    for j in range(len(L)):
        nd = np.unique(null_per_sz[j][np.isfinite(null_per_sz[j])]).size
        assert nd > 1, (
            f"DEGENERATE NULL for {subj} seizure {j+1}: {nd} distinct value(s). "
            "This is the v1 bug signature (permutation-invariant statistic). ABORT.")
    nd_subj = np.unique(subj_null[np.isfinite(subj_null)]).size
    assert nd_subj > 1, (
        f"DEGENERATE SUBJECT-LEVEL NULL for {subj}: {nd_subj} distinct value(s). ABORT.")

    for j, rec in enumerate(per_sz):
        rec["gini_null_median"] = float(np.median(null_per_sz[j]))
        rec["signed_deviation"] = rec["gini"] - rec["gini_null_median"]

    g_obs = float(np.median(obs_g))
    g_null_med = float(np.median(subj_null))
    dev = g_obs - g_null_med
    rec = dict(
        subject=subj,
        n_seizures=len(obs_g),
        n_interictal_windows=int(n_inter),
        median_seizure_len_win=int(np.median(L)),
        gini_obs=g_obs,
        gini_null_median=g_null_med,
        gini_null_p2_5=float(np.percentile(subj_null, 2.5)),
        gini_null_p97_5=float(np.percentile(subj_null, 97.5)),
        signed_deviation=dev,
        p_raw=two_sided_empirical_p(g_obs, subj_null),
        entropy_norm=float(np.median(obs_h)),
        top5_mass=float(np.median(obs_t5)),
        top5_mass_uniform_ref=UNIFORM_TOP5_REF,
        n_null_distinct=int(nd_subj),
        direction=("below_null(distributed)" if dev < 0 else
                   "above_null(concentrated)" if dev > 0 else "zero"),
    )
    return rec, per_sz, subj_null


# ----------------------------------------------------------------------------
# figure
# ----------------------------------------------------------------------------
def make_figure(recs, nulls, path):
    subs = [r["subject"] for r in recs]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.boxplot([nulls[s] for s in subs], positions=range(len(subs)),
               widths=0.55, showfliers=False,
               medianprops=dict(color="#555555"))
    ax.scatter(range(len(subs)), [r["gini_obs"] for r in recs],
               color="#d62728", zorder=5, s=55, label="observed (median over seizures)")
    ax.set_xticks(range(len(subs)))
    ax.set_xticklabels(subs, rotation=0)
    ax.set_ylabel("Gini of |z| across 18 derivations")
    ax.set_title("Test A - ictal attribution concentration vs length-matched "
                 "pseudo-seizure null")
    ax.legend(loc="best", fontsize=9)
    ax.grid(axis="y", alpha=0.3)
    fig.tight_layout()
    fig.savefig(path, dpi=160)
    plt.close(fig)


# ----------------------------------------------------------------------------
# writers
# ----------------------------------------------------------------------------
def write_csv(path, rows, fields):
    import csv
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in fields})


# ----------------------------------------------------------------------------
# main
# ----------------------------------------------------------------------------
def run(pernode_root, summary_dir, outdir, subjects, n_null, seed,
        win_sec, parse_fn, n_boot=10000):
    os.makedirs(outdir, exist_ok=True)
    rng = np.random.default_rng(seed)

    recs, per_sz_all, nulls = [], [], {}
    for subj in subjects:
        p_int = find_pernode(pernode_root, subj, "inter")
        p_ict = find_pernode(pernode_root, subj, "ictal")
        if p_int is None or p_ict is None:
            raise FileNotFoundError(f"{subj}: per-node .npy not found under {pernode_root}")
        inter = np.load(p_int).astype(float)
        ictal = np.load(p_ict).astype(float)
        if inter.shape[1] != N_CH or ictal.shape[1] != N_CH:
            raise ValueError(f"{subj}: expected {N_CH} channels, got "
                             f"{inter.shape[1]}/{ictal.shape[1]}")
        blocks, ptr = seizure_window_blocks(subj, summary_dir, win_sec, parse_fn)
        if ptr != ictal.shape[0]:
            print(f"  [warn] {subj}: summary implies {ptr} ictal windows, "
                  f"array has {ictal.shape[0]} - blocks truncated to array length")
        rec, psz, subj_null = test_a_subject(subj, inter, ictal, blocks, rng, n_null)
        recs.append(rec); per_sz_all.extend(psz); nulls[subj] = subj_null
        print(f"  {subj}: n_sz={rec['n_seizures']:>2}  gini_obs={rec['gini_obs']:.4f}  "
              f"null_med={rec['gini_null_median']:.4f}  dev={rec['signed_deviation']:+.4f}  "
              f"p={rec['p_raw']:.4f}  [{rec['direction']}]")

    # ---- BH-FDR across the 8 subjects (the ONLY FDR family, §1.5) ---------
    q = bh_fdr([r["p_raw"] for r in recs])
    for r, qq in zip(recs, q):
        r["q_bh"] = float(qq)

    # ---- cohort inference -------------------------------------------------
    devs = [r["signed_deviation"] for r in recs]
    n_used, n_pos, p_sign = exact_sign_test(devs)
    lo, hi = bootstrap_median_ci(devs, rng, n_boot=n_boot)
    n_sig_bh = int(sum(1 for r in recs if r["q_bh"] < 0.05))

    if p_sign < 0.05 and n_pos == 0:
        verdict = "A1 (distributed): sign test significant, deviations all negative"
    elif p_sign < 0.05 and n_pos == n_used:
        verdict = "A2 (concentrated): sign test significant, deviations all positive"
    elif p_sign < 0.05:
        verdict = ("A1/A2 significant with mixed signs - report predominant direction "
                   "explicitly and do NOT overstate")
    else:
        verdict = "A3 (indeterminate): sign test not significant"

    cohort = dict(
        n_subjects=len(recs), n_used_sign_test=n_used, n_positive=n_pos,
        n_negative=n_used - n_pos, sign_test_p_two_sided=p_sign,
        median_signed_deviation=float(np.median(devs)),
        median_signed_deviation_ci_lo=lo, median_signed_deviation_ci_hi=hi,
        n_subjects_bh_significant_q05=n_sig_bh,
        preregistered_verdict=verdict, seed=seed, n_null=n_null, n_boot=n_boot,
    )

    write_csv(os.path.join(outdir, "attribution_v3_summary.csv"), recs,
              ["subject", "n_seizures", "n_interictal_windows", "median_seizure_len_win",
               "gini_obs", "gini_null_median", "gini_null_p2_5", "gini_null_p97_5",
               "signed_deviation", "p_raw", "q_bh", "entropy_norm", "top5_mass",
               "top5_mass_uniform_ref", "n_null_distinct", "direction"])
    write_csv(os.path.join(outdir, "attribution_v3_perseizure.csv"), per_sz_all,
              ["subject", "seizure_idx", "n_windows", "gini", "gini_null_median",
               "signed_deviation", "entropy_norm", "top5_mass", "top5_channels"])
    write_csv(os.path.join(outdir, "attribution_v3_cohort.csv"), [cohort],
              list(cohort.keys()))
    make_figure(recs, nulls, os.path.join(outdir, "attribution_v3_concentration.png"))

    prov = dict(
        script=SCRIPT_VERSION,
        preregistration="ATTRIBUTION_PREREGISTRATION_v3_1.md (Test A only)",
        run_utc=datetime.now(timezone.utc).isoformat(timespec="seconds"),
        seed=seed, rng="np.random.default_rng", n_null=n_null, n_boot=n_boot,
        win_sec=win_sec, subjects=list(subjects),
        pernode_root=os.path.abspath(pernode_root),
        summary_dir=os.path.abspath(summary_dir),
        statistic="Gini of |z| over 18 bipolar derivations; per subject = median over seizures",
        null="length-matched contiguous interictal pseudo-seizure draw",
        mad_epsilon=MAD_EPS,
        weight_invariant=True,
        caveats=[
            "Interictal contiguity is contiguity in the concatenated interictal "
            "window index space; a drawn block may straddle an EDF boundary.",
            "Attribution lives in bipolar-derivation space; adjacent derivations "
            "share a physical electrode and are inherently correlated, which caps "
            "attainable concentration (pre-registration §1.4).",
            "No clinical localization claim is made under any outcome (A5).",
        ],
        python=platform.python_version(), numpy=np.__version__,
    )
    with open(os.path.join(outdir, "attribution_v3_provenance.json"), "w",
              encoding="utf-8") as f:
        json.dump(prov, f, indent=2)

    print("\n--- COHORT (Test A) ---")
    for k, v in cohort.items():
        print(f"  {k}: {v}")
    print(f"\nOutputs -> {os.path.abspath(outdir)}")
    return recs, cohort


# ----------------------------------------------------------------------------
# self-test on synthetic data
# ----------------------------------------------------------------------------
def selftest():
    print("=== SELF-TEST (synthetic) ===")
    ok = True

    # 1. Gini sanity
    uni = np.ones(18)
    spike = np.zeros(18); spike[0] = 1.0
    g_u, g_s = gini(uni), gini(spike)
    print(f" gini(uniform)={g_u:.4f} (expect 0)   gini(one-hot)={g_s:.4f} (expect ~0.944)")
    ok &= abs(g_u) < 1e-12 and abs(g_s - 17 / 18) < 1e-9
    print(f" entropy(uniform)={norm_entropy(uni):.4f} (expect 1)   "
          f"top5(uniform)={topk_mass(uni):.4f} (expect {UNIFORM_TOP5_REF:.4f})")
    ok &= abs(norm_entropy(uni) - 1) < 1e-12 and abs(topk_mass(uni) - UNIFORM_TOP5_REF) < 1e-12

    # 2. the three pre-registered scenarios (§3 table)
    rng = np.random.default_rng(0)
    inter = rng.normal(0, 1, size=(4000, 18))
    med = np.median(inter, axis=0)
    mad = np.median(np.abs(inter - med), axis=0) + MAD_EPS
    base = abs_z(rng.normal(0, 1, size=(50, 18)), med, mad)
    foc = rng.normal(0, 1, size=(50, 18)); foc[:, [2, 3]] += 6.0
    dis = rng.normal(0, 1, size=(50, 18)) + 6.0
    print(f" baseline Gini={gini(base):.3f} | FOCAL={gini(abs_z(foc, med, mad)):.3f} "
          f"| DISTRIBUTED={gini(abs_z(dis, med, mad)):.3f}")
    ok &= gini(abs_z(foc, med, mad)) > gini(base) > gini(abs_z(dis, med, mad))

    # 3. BH + sign test + p-value sanity
    q = bh_fdr([0.001, 0.01, 0.03, 0.2, 0.5, 0.6, 0.7, 0.9])
    ok &= np.all(np.diff(q[np.argsort([0.001, 0.01, 0.03, 0.2, 0.5, 0.6, 0.7, 0.9])]) >= -1e-12)
    n, k, p = exact_sign_test([-1] * 8)
    print(f" sign test all-negative(8): n={n} k={k} p={p:.4f} (expect 0.0078)")
    ok &= abs(p - 2 / 256) < 1e-9
    pn = two_sided_empirical_p(0.0, rng.normal(0, 1, 1000))
    print(f" two-sided empirical p at null centre = {pn:.3f} (expect ~1)")
    ok &= pn > 0.7

    # 4. guard must FIRE on a degenerate null
    class _FakeRng:
        def integers(self, lo, hi, size=None):
            return np.zeros(size, dtype=int)          # always the same block -> degenerate
    fake_inter = rng.normal(0, 1, size=(300, 18))
    fake_ict = rng.normal(0, 1, size=(40, 18))
    try:
        test_a_subject("chbXX", fake_inter, fake_ict, [np.arange(40)], _FakeRng(), 50)
        print(" GUARD: FAILED TO FIRE  <-- BUG")
        ok = False
    except AssertionError as e:
        print(f" GUARD fired correctly: {str(e)[:70]}...")

    # 5. end-to-end on a synthetic 2-subject cohort (chbXX distributed, chbYY focal)
    root = "/home/claude/fake"
    pn_dir = os.path.join(root, "pernode")
    sm_dir = os.path.join(root, "summary")
    os.makedirs(pn_dir, exist_ok=True); os.makedirs(sm_dir, exist_ok=True)
    r2 = np.random.default_rng(7)
    for subj, mode in [("chbXX", "dist"), ("chbYY", "focal")]:
        it = r2.normal(0, 1, size=(3000, 18))
        ic = r2.normal(0, 1, size=(60, 18))          # 2 seizures x 30 windows
        if mode == "dist":
            ic += 5.0
        else:
            ic[:, [5, 6]] += 8.0
        np.save(os.path.join(pn_dir, f"{subj}_interictal_pernode.npy"), it)
        np.save(os.path.join(pn_dir, f"{subj}_ictal_pernode.npy"), ic)
        with open(os.path.join(sm_dir, f"{subj}-summary.txt"), "w") as f:
            f.write("File Name: a.edf\nFile Start Time: 00:00:00\n"
                    "File End Time: 01:00:00\nNumber of Seizures in File: 1\n"
                    "Seizure Start Time: 100 seconds\nSeizure End Time: 220 seconds\n\n"
                    "File Name: b.edf\nFile Start Time: 01:00:00\n"
                    "File End Time: 02:00:00\nNumber of Seizures in File: 1\n"
                    "Seizure Start Time: 300 seconds\nSeizure End Time: 420 seconds\n\n")
    from evaluation_protocol import parse_summary_edf_list as _pf
    recs, cohort = run(pn_dir, sm_dir, "/home/claude/fake/out",
                       ["chbXX", "chbYY"], n_null=200, seed=0, win_sec=4,
                       parse_fn=_pf, n_boot=2000)
    d = {r["subject"]: r["signed_deviation"] for r in recs}
    print(f" end-to-end deviations: chbXX(dist)={d['chbXX']:+.3f} (expect <0)  "
          f"chbYY(focal)={d['chbYY']:+.3f} (expect >0)")
    ok &= d["chbXX"] < 0 and d["chbYY"] > 0
    for fn in ["attribution_v3_summary.csv", "attribution_v3_perseizure.csv",
               "attribution_v3_cohort.csv", "attribution_v3_provenance.json",
               "attribution_v3_concentration.png"]:
        e = os.path.exists(os.path.join("/home/claude/fake/out", fn))
        ok &= e
        print(f" output {fn}: {'OK' if e else 'MISSING'}")

    print("\n=== SELF-TEST", "PASSED" if ok else "FAILED", "===")
    return 0 if ok else 1


def main():
    ap = argparse.ArgumentParser(description="Test A - attribution concentration (pre-reg v3.1)")
    ap.add_argument("--pernode_root", default=None)
    ap.add_argument("--summary_dir", default=None)
    ap.add_argument("--outdir", default="results/attribution_v3")
    ap.add_argument("--subjects", nargs="+", default=TEST_SUBJS)
    ap.add_argument("--n_null", type=int, default=1000)
    ap.add_argument("--n_boot", type=int, default=10000)
    ap.add_argument("--seed", type=int, default=0)
    ap.add_argument("--selftest", action="store_true")
    a = ap.parse_args()

    if a.selftest:
        sys.exit(selftest())
    if not a.pernode_root or not a.summary_dir:
        ap.error("--pernode_root and --summary_dir are required (or use --selftest)")

    import evaluation_protocol as E    # single source of truth for parsing + WIN_SEC
    print(SCRIPT_VERSION)
    print(f"seed={a.seed}  n_null={a.n_null}  WIN_SEC={E.WIN_SEC}\n")
    run(a.pernode_root, a.summary_dir, a.outdir, a.subjects, a.n_null, a.seed,
        E.WIN_SEC, E.parse_summary_edf_list, n_boot=a.n_boot)


if __name__ == "__main__":
    main()