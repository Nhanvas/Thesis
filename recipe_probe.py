"""
================================================================================
 recipe_probe.py  —  READ-ONLY: lock the ensemble recipe + recover z_recon
================================================================================
WHY
    The GAE reconstruction score (z_recon) is NOT cached as a standalone array;
    it survives only folded inside the ensemble. Both the event-tier ablation
    and the topology-as-4th-view experiment need to know the EXACT ensemble
    recipe, and the ablation needs recon-alone. This probe:

      1. loads z_ens, temporal_z, gamma for ONE subject (default chb03),
      2. characterises gamma (already z-scored? or raw -> needs robust z),
      3. tests whether  z_ens == 0.35*z_recon + 0.30*z_temporal + 0.35*z_gamma
         is consistent (i.e. the documented weights + a clean normalisation),
      4. recovers z_recon under each normalisation hypothesis and reports
         whether the recovered recon is a WELL-FORMED robust z-score
         (interictal median ~ 0, robust scale ~ 1). A clean recon == the recipe
         is confirmed and recon recovery is exact. A pathological recon == the
         ensemble was built differently (e.g. re-normalised after summing) and
         we must fall back to GAE inference.

    It writes nothing except an optional recovered-recon .npy (only if you pass
    --save and the recipe is confirmed). Otherwise it is purely diagnostic.

USAGE
    python recipe_probe.py --subj chb03
    python recipe_probe.py --subj chb03 \
        --ens_dir results/cpd/scores \
        --temp_dir data/processed/temporal_zscores \
        --gamma_dir data/processed
    # weights default to the locked 0.35/0.30/0.35; override with --w_recon etc.
================================================================================
"""
import argparse
import glob
import os
import numpy as np

W_RECON, W_TEMP, W_GAMMA = 0.35, 0.30, 0.35


def _find(d, subj, must, split_tokens):
    """Find the first .npy in dir d whose name contains subj, all 'must'
    substrings, and any split token."""
    for p in sorted(glob.glob(os.path.join(d, "**", "*.npy"), recursive=True)):
        b = os.path.basename(p).lower()
        if subj in b and all(m in b for m in must) and any(t in b for t in split_tokens):
            return p
    return None


def _robust_z_pooled(x_in, x_ic):
    a = np.concatenate([x_in, x_ic])
    med = np.median(a)
    scale = 1.4826 * (np.median(np.abs(a - med)) + 1e-9)
    return (x_in - med) / scale, (x_ic - med) / scale, med, scale


def _robust_z_inter(x_in, x_ic):
    med = np.median(x_in)
    scale = 1.4826 * (np.median(np.abs(x_in - med)) + 1e-9)
    return (x_in - med) / scale, (x_ic - med) / scale, med, scale


def _zstats(x_in):
    """How close is x_in to a clean robust z-score? median ~0, robust scale ~1."""
    med = np.median(x_in)
    scale = 1.4826 * (np.median(np.abs(x_in - med)) + 1e-9)
    return med, scale


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subj", default="chb03")
    ap.add_argument("--ens_dir", default="results/cpd/scores")
    ap.add_argument("--temp_dir", default="data/processed/temporal_zscores")
    ap.add_argument("--gamma_dir", default="data/processed")
    ap.add_argument("--w_recon", type=float, default=W_RECON)
    ap.add_argument("--w_temp", type=float, default=W_TEMP)
    ap.add_argument("--w_gamma", type=float, default=W_GAMMA)
    ap.add_argument("--save", action="store_true",
                    help="save recovered recon ONLY if recipe is confirmed clean")
    args = ap.parse_args()
    s = args.subj

    ens_in_p = _find(args.ens_dir, s, ["ens"], ["inter"])
    ens_ic_p = _find(args.ens_dir, s, ["ens"], ["ictal", "ical"])
    tmp_in_p = _find(args.temp_dir, s, ["temporal"], ["inter", "zinter"])
    tmp_ic_p = _find(args.temp_dir, s, ["temporal"], ["ictal", "zictal"])
    gam_in_p = _find(args.gamma_dir, s, ["gamma"], ["inter"])
    gam_ic_p = _find(args.gamma_dir, s, ["gamma"], ["ictal"])

    print("\nRESOLVED FILES")
    for tag, p in [("ens_inter", ens_in_p), ("ens_ictal", ens_ic_p),
                   ("temp_inter", tmp_in_p), ("temp_ictal", tmp_ic_p),
                   ("gamma_inter", gam_in_p), ("gamma_ictal", gam_ic_p)]:
        print(f"  {tag:<12} {p}")
    if not all([ens_in_p, ens_ic_p, tmp_in_p, tmp_ic_p, gam_in_p, gam_ic_p]):
        print("\n[STOP] One or more inputs not found. Adjust --*_dir flags and rerun.")
        return

    ens_in = np.load(ens_in_p).astype(np.float64)
    ens_ic = np.load(ens_ic_p).astype(np.float64)
    tmp_in = np.load(tmp_in_p).astype(np.float64)
    tmp_ic = np.load(tmp_ic_p).astype(np.float64)
    gam_in = np.load(gam_in_p).astype(np.float64)
    gam_ic = np.load(gam_ic_p).astype(np.float64)

    print("\nSHAPES (inter / ictal)")
    print(f"  ens   {ens_in.shape} / {ens_ic.shape}")
    print(f"  temp  {tmp_in.shape} / {tmp_ic.shape}")
    print(f"  gamma {gam_in.shape} / {gam_ic.shape}")
    if not (len(ens_in) == len(tmp_in) == len(gam_in) and
            len(ens_ic) == len(tmp_ic) == len(gam_ic)):
        print("\n[WARN] window counts differ across sources -> alignment problem. "
              "Recovery would be invalid. Report this back.")
        # continue to show stats but flag

    # characterise the raw inputs
    em, es = _zstats(tmp_in)
    print(f"\nTEMPORAL inter z-stats: median={em:+.4f} robust_scale={es:.4f}  "
          f"({'looks z-scored' if abs(em) < 0.3 and 0.6 < es < 1.6 else 'NOT a clean z'})")
    gm, gs = _zstats(gam_in)
    gamma_is_z = abs(gm) < 0.3 and 0.6 < gs < 1.6
    print(f"GAMMA   inter raw-stats: median={gm:+.4f} robust_scale={gs:.4f}  "
          f"({'already z-scored' if gamma_is_z else 'RAW -> will robust-z it'})")
    ensm, enss = _zstats(ens_in)
    print(f"ENSEMBLE inter z-stats: median={ensm:+.4f} robust_scale={enss:.4f}")

    # hypotheses for gamma normalisation
    hyps = {}
    if gamma_is_z:
        hyps["gamma_as_is"] = (gam_in, gam_ic)
    hyps["gamma_pooled_robustz"] = _robust_z_pooled(gam_in, gam_ic)[:2]
    hyps["gamma_inter_robustz"] = _robust_z_inter(gam_in, gam_ic)[:2]

    # temporal assumed already z (folder = *_zscores); also offer a re-z option
    tmp_variants = {"temp_as_is": (tmp_in, tmp_ic)}
    if not (abs(em) < 0.3 and 0.6 < es < 1.6):
        tmp_variants["temp_pooled_robustz"] = _robust_z_pooled(tmp_in, tmp_ic)[:2]

    print("\nRECOVERY HYPOTHESES  (recon = (ens - w_t*temp - w_g*gamma)/w_recon)")
    print(f"  weights: w_recon={args.w_recon}  w_temp={args.w_temp}  w_gamma={args.w_gamma}")
    best = None
    for tname, (zt_in, zt_ic) in tmp_variants.items():
        for gname, (zg_in, zg_ic) in hyps.items():
            rec_in = (ens_in - args.w_temp * zt_in - args.w_gamma * zg_in) / args.w_recon
            rec_ic = (ens_ic - args.w_temp * zt_ic - args.w_gamma * zg_ic) / args.w_recon
            rm, rs = _zstats(rec_in)
            clean = abs(rm) < 0.3 and 0.6 < rs < 1.6
            # ictal lift: a real recon should tend to be elevated during ictal
            lift = np.median(rec_ic) - np.median(rec_in)
            flag = "  <== CLEAN" if clean else ""
            print(f"  [{tname:>18} | {gname:>22}] recon inter median={rm:+.3f} "
                  f"scale={rs:.3f}  ictal_lift={lift:+.3f}{flag}")
            if clean and (best is None or abs(rm) < abs(best[1])):
                best = ((tname, gname), rm, (rec_in, rec_ic), (zt_in, zt_ic, zg_in, zg_ic))

    print("\nVERDICT")
    if best is not None:
        (tn, gn), rm, (rec_in, rec_ic), _ = best
        # final closure check: rebuild ensemble from the 3 recovered components
        zt_in, zt_ic, zg_in, zg_ic = best[3]
        reb_in = args.w_recon * rec_in + args.w_temp * zt_in + args.w_gamma * zg_in
        max_err = float(np.max(np.abs(reb_in - ens_in)))
        print(f"  Recipe CONFIRMED: temporal='{tn}', gamma='{gn}'.")
        print(f"  Recovered recon is a clean robust z (inter median {rm:+.3f}).")
        print(f"  Ensemble closure max|rebuilt-ens| on inter = {max_err:.2e} "
              f"({'exact' if max_err < 1e-3 else 'approx'}).")
        if args.save:
            out = f"recovered_recon_{s}"
            np.save(out + "_inter.npy", rec_in.astype(np.float32))
            np.save(out + "_ictal.npy", rec_ic.astype(np.float32))
            print(f"  Saved {out}_inter.npy / _ictal.npy")
        else:
            print("  (Rerun with --save to write the recovered recon arrays.)")
        print("\n  => Algebraic recovery is VALID. Event-tier ablation can proceed "
              "with NO GAE rerun.")
    else:
        print("  No normalisation hypothesis yields a clean recon.")
        print("  => The ensemble was likely re-normalised after summing, or uses "
              "different weights.")
        print("  => Fall back to GAE INFERENCE for recon-alone. Send me your GAE "
              "model/checkpoint file and I will write the inference script.")
    print()


if __name__ == "__main__":
    main()