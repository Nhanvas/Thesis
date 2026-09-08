"""
================================================================================
 label_eeg_pilot.py  —  channel-labeling viewer
================================================================================
Renders segments of the raw scalp EEG recording around each seizure so the reader
can mark the suspect bipolar derivation(s), exactly the way a clinician reads
ictal EEG. It reads the recordings and the summary timings only, and never any
model output. The annotations produced from this script are an AI draft, not
blind and not supervisor-frozen; authority rests with the supervisor.

What it does, per subject:
  1. Reads the subject's summary, enumerates seizures in the SAME global order the
     per-node blocks are built (edf-name-sorted; seizures within a file in order;
     a seizure that would yield 0 ictal windows is flagged — it would be dropped
     downstream, so its index must not silently shift). Verified on chb17 -> 3
     seizures, 74 windows, matching {subj}_ictal_pernode.npy.
  2. For each seizure: loads the EDF named in the summary, selects the 18 bipolar
     derivations BY NAME (CH_NAMES; first occurrence — CHB-MIT lists T8-P8 twice),
     applies a DISPLAY-ONLY band-pass + notch, and renders two panels:
        [ baseline (clean pre-onset) | onset window (onset & offset marked) ]
     Saves a PNG for the supervisor's review record, and (default) opens an
     interactive matplotlib window (pan/zoom toolbar) for careful reading.
  3. Writes/updates labels_{subj}.csv with one row per seizure, meta pre-filled,
     label columns BLANK for the reader to fill (primary_ch, secondary_ch, ...).

It never reads pernode / ensemble / any results file, and the annotations it
produces are an AI draft, not blind and not supervisor-frozen.

USAGE (Cursor / CPU)
  pip install mne scipy matplotlib numpy
  python label_eeg_pilot.py --subject chb17 \
      --edf_root  "F:/Study/Thesis/Dataset/CHB-MIT" \
      --summary_dir "F:/Study/Thesis/Dataset/CHB-MIT/CHB info/summary" \
      --out_dir   "results/attribution_v5/labels"
  # one seizure only:      --seizure 0
  # save PNGs, no windows: --save_only
  # wider onset view:      --pre 20 --post 60
================================================================================
"""
import argparse
import csv
import os
import re
from pathlib import Path

import numpy as np
from scipy.signal import butter, sosfiltfilt, iirnotch, filtfilt

# --- the 18 bipolar derivations, in per-node / CH_NAMES order (double-banana) ---
CH_NAMES = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1",
            "FP2-F4", "F4-C4", "C4-P4", "P4-O2", "FP2-F8", "F8-T8", "T8-P8", "P8-O2",
            "FZ-CZ", "CZ-PZ"]
WIN_SEC = 4  # must match evaluation_protocol.WIN_SEC (segmentation alignment)


# ----------------------------------------------------------------- summary parse
def parse_time_hms(t):
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary_edf_list(summary_path):
    """Verbatim behaviour of evaluation_protocol.parse_summary_edf_list."""
    text = Path(summary_path).read_text()
    pat = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)(.*?)(?=File Name:|$)',
        re.DOTALL)
    edfs = []
    for m in pat.finditer(text):
        fname, t0, t1, nsz, rest = m.groups()
        dur = parse_time_hms(t1) - parse_time_hms(t0)
        if dur <= 0:
            dur += 86400
        szs = []
        if int(nsz) > 0:
            ons = [int(x) for x in re.findall(r'Seizure.*?Start Time.*?:\s*(\d+)', rest, re.I)]
            ofs = [int(x) for x in re.findall(r'Seizure.*?End Time.*?:\s*(\d+)',   rest, re.I)]
            szs = list(zip(ons, ofs))
        edfs.append({'fname': fname, 'duration_s': dur, 'seizures': szs})
    edfs.sort(key=lambda x: x['fname'])
    return edfs


def enumerate_seizures(edfs):
    """Global seizure list matching per-node block order; flag 0-window seizures."""
    out, gidx = [], 0
    for edf in edfs:
        dur = int(edf['duration_s']); n_win = dur // WIN_SEC; tl = n_win * WIN_SEC
        if tl == 0:
            continue
        sid = np.zeros(dur, dtype=np.int32)
        for k, (on, off) in enumerate(edf['seizures'], start=1):
            sid[min(on, dur):min(off, dur)] = k
        win_sid = sid[:tl].reshape(n_win, WIN_SEC).max(axis=1)
        for k, (on, off) in enumerate(edf['seizures'], start=1):
            nwin = int((win_sid == k).sum())
            if nwin == 0:
                print(f"   [WARN] {edf['fname']} seizure(on={on}s) -> 0 ictal windows; "
                      f"downstream this seizure is DROPPED. Tell me before labeling.")
                continue
            out.append(dict(gidx=gidx, fname=edf['fname'], on=on, off=off, nwin=nwin))
            gidx += 1
    return out


# ------------------------------------------------------------------- channel pick
def _norm(s):
    s = re.sub(r'\s+', '', s).upper().replace("-REF", "")
    # strip mne's duplicate-name suffix so 'T8-P8-0' -> 'T8-P8'. Safe: real
    # derivation names never end in a bare '-<int>' (last token has a letter).
    s = re.sub(r'-\d+$', '', s)
    return s


def pick_18(ch_names, data):
    """Select the 18 CH_NAMES by name (first occurrence), return (names, data, missing).
    data: (n_channels, n_samples). Robust to whitespace/case/duplicate names."""
    norm_avail = [_norm(c) for c in ch_names]
    rows, missing = [], []
    for target in CH_NAMES:
        t = _norm(target)
        idx = norm_avail.index(t) if t in norm_avail else None
        if idx is None:
            missing.append(target)
        else:
            rows.append(idx)
    if missing:
        return None, None, missing
    return CH_NAMES[:], data[rows, :], []


# ------------------------------------------------------------------- display filter
def display_filter(data, sfreq, lo=1.0, hi=70.0, notch=60.0):
    """DISPLAY-ONLY band-pass + notch. Does NOT touch the model. data: (C, N)."""
    ny = sfreq / 2.0
    hi = min(hi, ny * 0.99)
    sos = butter(4, [lo / ny, hi / ny], btype="band", output="sos")
    out = sosfiltfilt(sos, data, axis=1)
    if notch and notch < ny:
        b, a = iirnotch(notch / ny, Q=30.0)
        out = filtfilt(b, a, out, axis=1)
    return out


# ------------------------------------------------------------------- EDF reader
def read_edf(path):
    """Return (ch_names, data_uV, sfreq). Isolated so only THIS needs mne."""
    import mne  # lazy import: everything else runs without mne
    raw = mne.io.read_raw_edf(path, preload=True, verbose="ERROR")
    sfreq = float(raw.info["sfreq"])
    ch_names = list(raw.ch_names)
    data = raw.get_data()  # mne returns Volts when units are recognised
    med = np.median(np.abs(data))
    data_uV = data * 1e6 if med < 1e-2 else data  # auto-scale V->uV if needed
    return ch_names, data_uV, sfreq


# ------------------------------------------------------------------- rendering
def _slice(data_uV, sfreq, t0, t1, dur_s):
    a = max(0, int(round(t0 * sfreq)))
    b = min(data_uV.shape[1], int(round(t1 * sfreq)))
    return data_uV[:, a:b], a / sfreq

def render_seizure(names, data_uV, sfreq, on, off, dur_s, uv_per_trace, pre, post,
                   base_gap, base_len, title, png_path, save_only, highlight=None,
                   zoom_pre=8.0, zoom_post=10.0):
    # highlight: {channel_index: color}. Empty/None = all black (BLIND labeling view).
    import matplotlib
    if save_only:
        matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    # three views: baseline reference | onset ZOOM (expanded) | full-seizure evolution
    o0 = max(0.0, on - pre); o1 = min(dur_s, max(on + post, off + 5))
    z0 = max(0.0, on - zoom_pre); z1 = min(dur_s, on + zoom_post)
    b1 = max(0.0, on - base_gap); b0 = max(0.0, b1 - base_len)
    seg_bl, bl_start = _slice(data_uV, sfreq, b0, b1, dur_s)
    seg_zm, zm_start = _slice(data_uV, sfreq, z0, z1, dur_s)
    seg_on, on_start = _slice(data_uV, sfreq, o0, o1, dur_s)
    C = len(names)
    offs = np.arange(C)[::-1] * uv_per_trace
    hl = highlight or {}

    fig, (axb, axz, axo) = plt.subplots(
        1, 3, figsize=(21, 9), gridspec_kw={"width_ratios": [1, 1.2, 2.2]})

    def draw(ax, seg, start_t, label, mark=False):
        n = seg.shape[1]; t = start_t + np.arange(n) / sfreq
        for i in range(C):
            col = hl.get(i, "k")
            ax.plot(t, seg[i] + offs[i], lw=0.8 if col != "k" else 0.4, color=col)
        ax.set_yticks(offs); ax.set_yticklabels(names, fontsize=7)
        for tick, i in zip(ax.get_yticklabels(), range(C)):
            if i in hl:
                tick.set_color(hl[i]); tick.set_fontweight("bold")
        ax.set_xlabel("time (s)"); ax.set_title(label, fontsize=10); ax.margins(x=0)
        ax.grid(axis="x", alpha=0.25)
        if mark:
            ax.axvline(on, color="r", lw=1.2)
            ax.text(on, offs[0] + uv_per_trace, "onset", color="r", fontsize=8, ha="center")
            if start_t <= off <= t[-1]:
                ax.axvline(off, color="r", lw=1.0, ls="--")

    draw(axb, seg_bl, bl_start, f"BASELINE ({b0:.0f}-{b1:.0f}s ref)")
    draw(axz, seg_zm, zm_start, f"ONSET ZOOM (+/-{zoom_pre:.0f}/{zoom_post:.0f}s) - read onset here",
         mark=True)
    draw(axo, seg_on, on_start, f"FULL seizure (onset={on}s, offset={off}s) - read dominant here",
         mark=True)
    axo.plot([on_start + 1, on_start + 1], [offs[-1], offs[-1] + 100], color="b", lw=2)
    axo.text(on_start + 1.3, offs[-1] + 20, "100 uV", color="b", fontsize=8)

    blind_tag = "" if hl else "   —   BLIND: no model output shown"
    fig.suptitle(title + blind_tag, fontsize=12)
    fig.tight_layout(rect=[0, 0, 1, 0.97])
    Path(png_path).parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(png_path, dpi=130, bbox_inches="tight")
    print(f"   [saved] {png_path}")
    if not save_only:
        plt.show()
    plt.close(fig)


# ------------------------------------------------------------------- labels csv
# region_ch = ALL derivations showing ictal activity = the coarse INVOLVED REGION
#             (e.g. the whole left-temporal chain). PRIMARY target (doctor-style coarse
#             localisation), robust to which single channel leads.
# onset_ch  = derivation(s) with the EARLIEST change (1-2) = finer SECONDARY field.
LABEL_COLS = ["subject", "seizure_idx", "fname", "onset_s", "offset_s",
              "region_ch", "onset_ch", "confidence", "diffuse", "notes"]

def ensure_labels_csv(path, subject, seizures):
    """Create labels_{subj}.csv with meta pre-filled + blank label columns.
    Never overwrites existing reader entries; only appends missing seizures."""
    existing = {}
    if Path(path).exists():
        with open(path, newline="") as f:
            for row in csv.DictReader(f):
                existing[int(row["seizure_idx"])] = row
    rows = []
    for s in seizures:
        if s["gidx"] in existing:
            rows.append(existing[s["gidx"]])
        else:
            rows.append(dict(subject=subject, seizure_idx=s["gidx"], fname=s["fname"],
                             onset_s=s["on"], offset_s=s["off"], region_ch="",
                             onset_ch="", confidence="", diffuse="", notes=""))
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=LABEL_COLS); w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in LABEL_COLS})
    print(f"   [labels] {path}  ({len(rows)} rows; fill region_ch / onset_ch / ...)")


# ------------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--subject", required=True)
    ap.add_argument("--edf_root", required=True, help="folder with per-subject subfolders")
    ap.add_argument("--summary_dir", required=True)
    ap.add_argument("--out_dir", default="results/attribution_v5/labels")
    ap.add_argument("--seizure", type=int, default=None, help="global gidx; default=all")
    ap.add_argument("--pre", type=float, default=15.0)
    ap.add_argument("--post", type=float, default=45.0)
    ap.add_argument("--base_gap", type=float, default=60.0)
    ap.add_argument("--base_len", type=float, default=60.0)
    ap.add_argument("--uv_per_trace", type=float, default=250.0)
    ap.add_argument("--save_only", action="store_true")
    ap.add_argument("--review", action="store_true",
                    help="re-render each seizure with labeled channels highlighted "
                         "(blue=onset_ch, red=dominant_ch) for supervisor review")
    args = ap.parse_args()

    subj = args.subject
    edfs = parse_summary_edf_list(Path(args.summary_dir) / f"{subj}-summary.txt")
    seizures = enumerate_seizures(edfs)
    print(f"\n{subj}: {len(seizures)} seizures (global order):")
    for s in seizures:
        print(f"  gidx={s['gidx']}  {s['fname']}  onset={s['on']}s  offset={s['off']}s  "
              f"dur={s['off']-s['on']}s  n_ictal_win={s['nwin']}")

    labels_path = Path(args.out_dir) / f"labels_{subj}.csv"
    ensure_labels_csv(labels_path, subj, seizures)

    # review mode loads the (filled) labels to highlight channels for the supervisor
    label_map = {}
    if args.review:
        if not labels_path.exists():
            print(f"  [ERR] --review needs {labels_path}; produce labels first."); return
        with open(labels_path, newline="") as f:
            for row in csv.DictReader(f):
                label_map[int(row["seizure_idx"])] = row

    def _idx_list(cell):
        out = []
        for c in (cell or "").replace(";", ",").split(","):
            n = _norm(c.strip())
            if not n:
                continue
            hit = [i for i, nm in enumerate(CH_NAMES) if _norm(nm) == n]
            if hit:
                out.append(hit[0])
        return out

    todo = seizures if args.seizure is None else [s for s in seizures if s["gidx"] == args.seizure]
    for s in todo:
        edf_path = Path(args.edf_root) / subj / s["fname"]
        if not edf_path.exists():
            print(f"  [ERR] EDF not found: {edf_path}  (check --edf_root / subfolder)")
            continue
        print(f"\n>>> gidx={s['gidx']}  reading {edf_path.name} ...")
        ch_names, data_uV, sfreq = read_edf(str(edf_path))
        names, data18, missing = pick_18(ch_names, data_uV)
        if missing:
            print(f"  [ERR] missing derivations {missing}. Available: {ch_names}")
            print("       -> paste this to me; I will adapt the name map for this file.")
            continue
        print(f"      sfreq={sfreq:g}Hz  picked 18/18  amp(uV) med|.|="
              f"{np.median(np.abs(data18)):.1f}  file_dur={data18.shape[1]/sfreq:.0f}s")
        filt = display_filter(data18, sfreq)
        dur = data18.shape[1] / sfreq
        if args.review:
            row = label_map.get(s["gidx"], {})
            hl = {}
            for i in _idx_list(row.get("region_ch", "")):
                hl[i] = "#ff7f0e"                       # orange = involved region
            for i in _idx_list(row.get("onset_ch", "")):
                hl[i] = "#1f77b4"                       # blue = onset (wins on overlap)
            title = (f"{subj} sz{s['gidx']} REVIEW  (orange=region, blue=onset)  "
                     f"conf={row.get('confidence','')}  diffuse={row.get('diffuse','')}")
            png = Path(args.out_dir) / f"{subj}_sz{s['gidx']}_review.png"
            render_seizure(names, filt, sfreq, s["on"], s["off"], dur, args.uv_per_trace,
                           args.pre, args.post, args.base_gap, args.base_len,
                           title, str(png), True, highlight=hl)
        else:
            title = f"{subj}  seizure gidx={s['gidx']}  ({s['fname']})"
            png = Path(args.out_dir) / f"{subj}_sz{s['gidx']}_onset.png"
            render_seizure(names, filt, sfreq, s["on"], s["off"], dur, args.uv_per_trace,
                           args.pre, args.post, args.base_gap, args.base_len,
                           title, str(png), args.save_only)

    print("\nDONE. Read each ONSET panel, mark the derivation(s) with the earliest/"
          "clearest ictal change into the labels CSV. Do NOT look at any model output.\n")


if __name__ == "__main__":
    main()
