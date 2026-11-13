#!/usr/bin/env python
"""d9c_eeg_figs.py -- real-EEG figures for the defense deck (chat D9b, 01/11/2026). Runs on the laptop
(EEG files are only there). Read-only on the repository; writes only under
F:/Study/Thesis/Defense/slides/figs/d9c/.

  --intro   p3 (Introduction): the WHOLE long-term recording of one child (chb01, the first case of
            CHB-MIT, a training patient), 18 channels, real clock time with the gaps between files; the
            annotated seizures in red, each with its duration; a zoom on the first seizure with its
            onset and offset. Selection rule fixed before drawing: chb01 (first case of the database),
            zoom = its first seizure in time. Numbers printed come from the summary file only.
            Step 1 reads every EDF once (one file at a time) and caches a per-bin min/max envelope
            (8 s bins) + the zoom segment to d9c/cache_intro_chb01.npz; step 2 draws from the cache.
  --chb24   p16 / backup: a detected seizure of chb24 (one more unseen CHB-MIT patient) on real EEG,
            thesis system, seed 42, after the localizer. Rule (same as the test-patient figure of
            p14): the true detection whose onset error is closest to the median onset error over all
            chb24 detections. Style = v9_final_figs.draw_event_panel (identical to p14).
  --clin02  hospital EEG, 1.25 h activation recording: copies the already privacy-checked panel of the
            system event with the HIGHEST peak score (events_clin02_interp.csv, V9-C1 run). No clinical
            EEG is opened. Never call it seizure or artifact.
  --smoke   with --intro: only the first 2 files (writes *_smoke.png); with --chb24: selection only.

Run from Git Bash, browsers closed, one job at a time:
  cd /f/Study/Thesis/Code && python /f/Study/Thesis/Defense/slides/gen/d9c/d9c_eeg_figs.py --intro --smoke
  cd /f/Study/Thesis/Code && python /f/Study/Thesis/Defense/slides/gen/d9c/d9c_eeg_figs.py --intro --chb24 --clin02
Estimated time: intro ~5-8 min (42 one-hour files, read + filter each once); chb24 < 2 min if the
x1/anatomy cache exists, else ~8 min; clin02 seconds. Peak RAM ~1 GB.
"""
import argparse
import re
import shutil
import sys
import time
from pathlib import Path

import numpy as np

CODE = Path("F:/Study/Thesis/Code")
for p in (CODE / "src", CODE / "src" / "retrain", CODE / "src" / "phaseB", CODE / "src" / "phaseC",
          CODE / "src" / "dataprep"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

OUT = Path("F:/Study/Thesis/Defense/slides/figs/d9c")
SUMMARY = CODE / "data" / "summaries" / "chb01-summary.txt"
DATA = Path("F:/Study/Thesis/Dataset/CHB-MIT/chb01")
CLIN_RUN = Path("F:/Study/Thesis/Defense/clinical/run")
FS = 256
BIN_S = 8
ZOOM_PAD_S = 60
RED, GREY, INK, BLUE = "#DC433A", "#5F6B7A", "#1E2A38", "#1F6FB2"


# ============================================================================ summary (numbers source)
def _sec(t):
    h, m, s = map(int, t.split(":"))
    return h * 3600 + m * 60 + s


def parse_summary(path):
    """Files in summary order with absolute clock seconds (day wrap handled) and seizures."""
    files, cur, on = [], None, None
    for line in open(path):
        line = line.strip()
        if line.startswith("File Name:"):
            cur = dict(name=line.split(":", 1)[1].strip(), sz=[]); files.append(cur)
        elif line.startswith("File Start Time:"):
            cur["st"] = line.split(":", 1)[1].strip()
        elif line.startswith("File End Time:"):
            cur["en"] = line.split(":", 1)[1].strip()
        elif "Start Time:" in line and cur is not None:
            on = int(re.search(r"(\d+)\s*seconds", line).group(1))
        elif "End Time:" in line and cur is not None:
            cur["sz"].append((on, int(re.search(r"(\d+)\s*seconds", line).group(1))))
    off, prev = 0, None
    for f in files:
        a, b = _sec(f["st"]), _sec(f["en"])
        if prev is not None:
            while a + off < prev:
                off += 86400
        f["A"] = a + off
        f["B"] = b + off
        while f["B"] < f["A"]:
            f["B"] += 86400
        prev = f["B"]
    t0 = files[0]["A"]
    for f in files:
        f["a_h"], f["b_h"] = (f["A"] - t0) / 3600, (f["B"] - t0) / 3600
    return files


def summary_numbers(files):
    rec_h = sum(f["B"] - f["A"] for f in files) / 3600
    sz = [(f["name"], a, b, (f["A"] - files[0]["A"] + a) / 3600) for f in files for a, b in f["sz"]]
    tot = sum(b - a for _, a, b, _ in sz)
    return rec_h, sz, tot


# ============================================================================ intro: step 1 (EEG -> cache)
def build_intro_cache(files, smoke=False):
    import preprocessing as P
    from scipy.signal import filtfilt, sosfiltfilt
    OUT.mkdir(parents=True, exist_ok=True)
    cache = OUT / ("cache_intro_chb01_smoke.npz" if smoke else "cache_intro_chb01.npz")
    if cache.exists():
        print(f"cache exists: {cache.name}", flush=True)
        return cache
    first = next((f, a, b) for f in files for a, b in f["sz"])
    use = files[:2] if smoke else files
    starts, mins, maxs, done = [], [], [], []
    zoom = None
    nb = BIN_S * FS
    t_all = time.time()
    for f in use:
        p = DATA / f["name"]
        if not p.exists():
            print(f"  missing on disk (gap kept): {f['name']}", flush=True); continue
        t = time.time()
        raw = P.open_edf(p)
        if raw is None:
            print(f"  no 18 common channels (gap kept): {f['name']}", flush=True); continue
        x = raw.get_data(); del raw
        x = filtfilt(P._NOTCH_B, P._NOTCH_A, sosfiltfilt(P._BP_SOS, x, axis=1), axis=1) * 1e6
        n = x.shape[1] // nb
        xb = x[:, :n * nb].reshape(18, n, nb)
        mins.append(xb.min(axis=2).astype(np.float32)); maxs.append(xb.max(axis=2).astype(np.float32))
        starts.append((f["A"] - files[0]["A"]) + np.arange(n) * BIN_S)
        if f["name"] == first[0]["name"]:
            a, b = first[1], first[2]
            s0, s1 = max(0, (a - ZOOM_PAD_S) * FS), min(x.shape[1], (b + ZOOM_PAD_S) * FS)
            zoom = dict(seg=x[:, s0:s1].astype(np.float32), t0=s0 / FS, onset=a, offset=b, file=f["name"],
                        clock0=f["A"])
        done.append(f["name"]); del x, xb
        print(f"  {f['name']}: {n} bins, {time.time() - t:.1f}s", flush=True)
    np.savez_compressed(cache, t=np.concatenate(starts), mn=np.concatenate(mins, axis=1),
                        mx=np.concatenate(maxs, axis=1), files=np.array(done),
                        zoom_seg=zoom["seg"] if zoom else np.zeros((18, 0), np.float32),
                        zoom_t0=zoom["t0"] if zoom else 0.0, zoom_on=zoom["onset"] if zoom else 0,
                        zoom_off=zoom["offset"] if zoom else 0, zoom_file=zoom["file"] if zoom else "",
                        zoom_clock0=zoom["clock0"] - files[0]["A"] if zoom else 0)
    print(f"cache written: {cache} ({len(done)} files, {time.time() - t_all:.0f}s)", flush=True)
    return cache


# ============================================================================ intro: step 2 (cache -> figures)
def _clock(sec_from_start, files):
    s = int(round(_sec(files[0]["st"]) + sec_from_start)) % 86400
    return f"{s // 3600:02d}:{(s % 3600) // 60:02d}:{s % 60:02d}"


def draw_intro(cache, files, smoke=False):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    plt.rcParams.update({"font.family": ["Calibri", "Carlito", "DejaVu Sans"], "font.size": 15})
    from preprocessing import COMMON_CHANNELS as CH
    z = np.load(cache, allow_pickle=True)
    t_h, mn, mx = z["t"] / 3600, z["mn"], z["mx"]
    rec_h, sz, tot = summary_numbers(files)
    span_h = files[-1]["b_h"]
    # one robust scale for all rows: 99th percentile of |envelope| over the whole record
    scale = float(np.percentile(np.abs(np.concatenate([mn.ravel(), mx.ravel()])), 99.0))
    gap = 2.2 * scale
    offs = np.arange(18)[::-1] * gap
    suffix = "_smoke" if smoke else ""

    def strip(ax, label_seizures=True):
        # break the trace at gaps between files (> 1 bin apart)
        brk = np.flatnonzero(np.diff(z["t"]) > BIN_S + 0.5) + 1
        for r in range(18):
            lo, hi = np.clip(mn[r], -scale, scale), np.clip(mx[r], -scale, scale)
            for seg in np.split(np.arange(len(t_h)), brk):
                ax.fill_between(t_h[seg], lo[seg] + offs[r], hi[seg] + offs[r], color=GREY, lw=0, alpha=0.85)
        y0, y1 = -1.6 * gap, offs[0] + 1.3 * gap
        min_w = 0.0035 * span_h                       # drawn wider than true so a 30 s seizure is visible
        last_h, lvl = -99.0, 0
        for k, (fn, a, b, h) in enumerate(sz, 1):
            w = max((b - a) / 3600, min_w)
            ax.fill_between([h, h + w], y0, y1, color=RED, alpha=0.9, lw=0)
            lvl = (lvl + 1) % 2 if h - last_h < 0.035 * span_h else 0   # stagger labels of close seizures
            last_h = h
            if label_seizures:
                ax.text(h + w / 2, y1 + (0.15 + 1.1 * lvl) * gap, f"{b - a} s", color=RED, ha="center",
                        va="bottom", fontsize=15, fontweight="bold")
        for f in files:   # light marks at file boundaries
            ax.axvline(f["a_h"], color="#C9D3DF", lw=0.4, zorder=0)
        ax.set_xlim(0, span_h); ax.set_ylim(y0, y1 + 2.8 * gap)
        ax.set_yticks(offs[[0, 8, 17]]); ax.set_yticklabels([CH[0], CH[8], CH[17]], fontsize=11, color=GREY)
        ax.set_xticks(np.arange(0, span_h + 0.1, 6))
        ax.set_xticklabels([f"{int(h)} h" for h in np.arange(0, span_h + 0.1, 6)])
        for sp in ("top", "right", "left"):
            ax.spines[sp].set_visible(False)

    # (a) strip only, wide
    fig, ax = plt.subplots(figsize=(19.2, 4.6), dpi=150)
    strip(ax)
    ax.set_xlabel("hours since the start of the recording (clock time; blank = between files; red bars drawn wider than the seizure so they are visible)", color=INK)
    ax.set_title(f"One child, {rec_h:.1f} hours of EEG on 18 channels: {len(sz)} seizures in red, "
                 f"{tot} s in total = {100 * tot / (rec_h * 3600):.1f} % of the recording",
                 loc="left", fontsize=19, color=INK)
    fig.tight_layout(); fig.savefig(OUT / f"intro_full_record_chb01{suffix}.png"); plt.close(fig)

    # (b) strip + zoom on the first seizure
    seg = z["zoom_seg"]
    if seg.shape[1]:
        fig = plt.figure(figsize=(19.2, 9.6), dpi=150)
        gs = fig.add_gridspec(2, 1, height_ratios=[1.0, 1.25], hspace=0.32)
        ax = fig.add_subplot(gs[0]); strip(ax)
        ax.set_title(f"One child, {rec_h:.1f} hours of EEG: {len(sz)} seizures (red), "
                     f"{100 * tot / (rec_h * 3600):.1f} % of the recording", loc="left", fontsize=19, color=INK)
        ax.set_xlabel("hours since the start of the recording (red bars drawn wider than the seizure so they are visible)", color=INK)
        az = fig.add_subplot(gs[1])
        t = float(z["zoom_t0"]) + np.arange(seg.shape[1]) / FS
        sc = float(np.percentile(np.abs(seg), 99.0)); g = 2.0 * sc
        o = np.arange(18)[::-1] * g
        on, off = int(z["zoom_on"]), int(z["zoom_off"])
        for r in range(18):
            ins = (t >= on) & (t <= off)
            az.plot(t, np.clip(seg[r], -1.2 * sc, 1.2 * sc) + o[r], color=INK, lw=0.45)
            az.plot(t[ins], np.clip(seg[r][ins], -1.2 * sc, 1.2 * sc) + o[r], color=RED, lw=0.55)
        az.axvspan(on, off, color=RED, alpha=0.08, lw=0)
        top = o[0] + 1.5 * g
        for x, lab, ha in ((on, "onset", "right"), (off, "offset", "left")):
            az.axvline(x, color=RED, lw=1.6)
            clock = _clock(float(z["zoom_clock0"]) + x, files)
            pad = 0.006 * (t[-1] - t[0]) * (-1 if ha == "right" else 1)
            az.text(x + pad, top, f"{lab} {clock}", color=RED, ha=ha, va="bottom", fontsize=16, fontweight="bold")
        az.set_yticks(o); az.set_yticklabels(CH, fontsize=9, color=GREY)
        az.set_xlim(t[0], t[-1]); az.set_ylim(-1.5 * g, top + 1.2 * g)
        c0 = _sec(files[0]["st"]) + float(z["zoom_clock0"])          # clock seconds of file second 0
        xt = np.arange(np.ceil((c0 + t[0]) / 30) * 30, c0 + t[-1], 30) - c0   # ticks on whole 30 s of clock
        az.set_xticks(xt); az.set_xticklabels([_clock(float(z["zoom_clock0"]) + v, files) for v in xt])
        az.set_title(f"Zoom on the first seizure: {off - on} s", loc="left", fontsize=17, color=INK)
        for sp in ("top", "right", "left"):
            az.spines[sp].set_visible(False)
        fig.savefig(OUT / f"intro_full_record_zoom_chb01{suffix}.png", bbox_inches="tight"); plt.close(fig)
    print(f"intro numbers (summary file): {len(files)} files, {rec_h:.2f} h recorded, span {span_h:.2f} h, "
          f"{len(sz)} seizures, {tot} s = {100 * tot / (rec_h * 3600):.3f} % (computed)", flush=True)
    for fn, a, b, h in sz:
        print(f"   {fn} {a}-{b} s ({b - a} s) at hour {h:.2f}", flush=True)


# ============================================================================ chb24
def chb24(select_only=False):
    import v9_final_figs as V9F
    V9V, P3L, E18 = V9F.V9V, V9F.P3L, V9F.E18
    import pandas as pd
    ctx, res = V9V.ctx_and_res_G("chb24", "chb24")
    refs = P3L.refs_of(ctx)
    rows = [dict(file_idx=int(f), file=V9F._fname(ctx, f), onset_s=a, offset_s=b, loc_on=h0, loc_off=h1,
                 onset_err=h0 - a) for f, a, b, h0, h1 in E18.match_errors(refs, res["loc"])]
    D = pd.DataFrame(rows)
    n_ref = sum(len(v) for v in refs.values())
    print(f"chb24: {n_ref} annotated seizures, {len(D)} matched detections (report: 14/16, seed 42)", flush=True)
    if not 13 <= len(D) <= 16 or n_ref != 16:
        raise SystemExit("STOP: chb24 counts differ from the report (16 seizures, 14 detected) -- nothing drawn")
    med = D.onset_err.median()
    pick = D.iloc[(D.onset_err - med).abs().values.argmin()]
    print(f"rule: onset error closest to the median ({med:g} s over {len(D)}): {pick.file} onset {pick.onset_s} s, "
          f"duration {pick.offset_s - pick.onset_s} s, localized {pick.loc_on}-{pick.loc_off} s, "
          f"onset error {pick.onset_err:g} s", flush=True)
    D.to_csv(OUT / "chb24_detections.csv", index=False)
    if select_only:
        return
    f = int(pick.file_idx)
    ref_band, loc_band = (pick.onset_s, pick.offset_s), (pick.loc_on, pick.loc_off)
    m = np.flatnonzero(ctx["fidx"] == f)
    p = V9F.draw_event_panel(OUT, "chb24_detected", "chb24", "chb24", f,
                             min(ref_band[0], loc_band[0]) - V9F.MARGIN_S, max(ref_band[1], loc_band[1]) + V9F.MARGIN_S,
                             "Detected seizure -- patient chb24 (unseen)", ref_band, loc_band, ref_band[0],
                             res["x"][m], 0.0, res["thr"])
    print(f"wrote {p}", flush=True)


# ============================================================================ clin02
def clin02():
    import pandas as pd
    ev = pd.read_csv(CLIN_RUN / "events_clin02_interp.csv")
    i = int(ev.peak_score.values.argmax())
    src = CLIN_RUN / "figs" / f"clin02_event_{i}.png"
    if not src.exists():
        raise SystemExit(f"STOP: {src.name} not found")
    dst = OUT / "hospital_activation_top_event.png"
    shutil.copy2(src, dst)
    r = ev.iloc[i]
    print(f"clin02: {len(ev)} system events; highest peak score = event {i} (peak {r.peak_score}, "
          f"duration {r.duration_s} s) -> {dst.name}. Check: no name / file name / date in the image.", flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--intro", action="store_true"); ap.add_argument("--chb24", action="store_true")
    ap.add_argument("--clin02", action="store_true"); ap.add_argument("--smoke", action="store_true")
    a = ap.parse_args()
    OUT.mkdir(parents=True, exist_ok=True)
    if a.intro:
        files = parse_summary(SUMMARY)
        draw_intro(build_intro_cache(files, a.smoke), files, a.smoke)
    if a.chb24:
        chb24(select_only=a.smoke)
    if a.clin02:
        clin02()
    if not (a.intro or a.chb24 or a.clin02):
        ap.error("pass --intro, --chb24 and/or --clin02")


if __name__ == "__main__":
    main()
