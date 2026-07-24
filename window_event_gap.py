"""
window_event_gap.py  (Phase B / Week 6)  — REPRO of the window<->event gap table.
Reads the locked eval_window_level.csv + szcore_event_level_mag60.csv (pen 1.0),
joins per subject, computes the gap, macro summaries, and the structural-failure
subset (excluding chb06 inverted + chb16 brief). Writes results/phaseB/window_event_gap.csv.

USAGE:  python window_event_gap.py --window eval_window_level.csv \
            --event szcore_event_level_mag60.csv --outdir results/phaseB
"""
import argparse, csv, os, statistics as st

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--window", default="eval_window_level.csv")
    ap.add_argument("--event", default="szcore_event_level_mag60.csv")
    ap.add_argument("--pen", type=float, default=1.0)
    ap.add_argument("--outdir", default="results/phaseB")
    ap.add_argument("--exclude", default="chb06,chb16")
    args = ap.parse_args()
    os.makedirs(args.outdir, exist_ok=True)
    print(f"[diag] outputs -> {os.path.abspath(args.outdir)}")

    import glob as _glob
    def _resolve(path):
        if os.path.exists(path):
            return path
        hits = _glob.glob(os.path.join(".", "**", os.path.basename(path)), recursive=True)
        if hits:
            print(f"[diag] '{path}' not in cwd; using {os.path.abspath(hits[0])}")
            return hits[0]
        raise FileNotFoundError(f"{os.path.basename(path)} not found anywhere under cwd")
    args.window = _resolve(args.window); args.event = _resolve(args.event)

    W = {r["subject"]: r for r in csv.DictReader(open(args.window))}
    E = {}
    for r in csv.DictReader(open(args.event)):
        if abs(float(r["pen_mult"]) - args.pen) < 1e-9:
            E[r["subject"]] = r
    subs = [s for s in W if s in E]
    rows = []
    for s in subs:
        w, e = W[s], E[s]
        nsz = int(e["n_seizures"]); nic = int(w["n_ictal"])
        ws = float(w["sensitivity"]); es = int(e["tp"]) / nsz
        rows.append(dict(subject=s, win_per_sz=round(nic / nsz, 1),
                         window_auroc=round(float(w["auroc"]), 3),
                         window_sens=round(ws, 3), event_sens=round(es, 3),
                         gap=round(es - ws, 3)))
    excl = set(args.exclude.split(","))
    ws_all = [r["window_sens"] for r in rows]; es_all = [r["event_sens"] for r in rows]
    ws_sub = [r["window_sens"] for r in rows if r["subject"] not in excl]
    es_sub = [r["event_sens"] for r in rows if r["subject"] not in excl]

    print(f"\n{'subj':<7}{'win/sz':>7}{'wAUROC':>8}{'wSens':>7}{'eSens':>7}{'gap':>7}")
    for r in rows:
        print(f"{r['subject']:<7}{r['win_per_sz']:>7}{r['window_auroc']:>8}"
              f"{r['window_sens']:>7}{r['event_sens']:>7}{r['gap']:>+7}")
    print(f"\nMACRO (all 8):          window {st.mean(ws_all):.3f} -> event {st.mean(es_all):.3f}")
    print(f"MACRO (excl {','.join(excl)}): window {st.mean(ws_sub):.3f} -> event {st.mean(es_sub):.3f}")

    with open(os.path.join(args.outdir, "window_event_gap.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys())); w.writeheader(); w.writerows(rows)
    print(f"\n  [saved] {os.path.abspath(os.path.join(args.outdir, 'window_event_gap.csv'))}")

if __name__ == "__main__":
    main()