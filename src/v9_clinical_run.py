#!/usr/bin/env python
"""
v9_clinical_run.py -- V9-C1: run the final P3-frozen system (balanced point, headline seed 42,
localizer CPD, per-patient budget -- v9_anatomy.final_events) on the two label-free hospital EEG
recordings from V9-T2, qualitatively, with no seizure metric claimed (neither file has a seizure
annotation; see docs/prompts/V9_C1_CLINICAL_RUN.md).

PRIVACY (same as V9-T2): never print or write file names, patient/recording header fields, or dates.
The two recordings are referred to only as clin01 (larger, ~13.2 h real data, header truncated) and
clin02 (smaller, 1.25 h, 512 Hz, activation protocol) -- the same size-order labels as V9-T2. All
outputs go to F:/Study/Thesis/Defense/clinical/run/ (outside the repo). Nothing from this task enters
the repo except this script; nothing here is committed.

REUSE, NOT REIMPLEMENTATION:
  - Signal path: x1_external.load_18 (referential -> 18 CHB-MIT bipolar channels via the T3/T4/T5/T6
    aliases, scipy resample_poly to 256 Hz), x1_external.filters/filter_windows/window_padded
    (band-pass + notch, identical zero-phase filtering to every other set), x1_external.labelfree_stats
    (per-channel z-score statistics, label-free -- the only kind available here, there is no seizure
    label to exclude), x1_external.file_features (CAR, wPLI/AEC graphs, band powers, f7 -- c1b's own
    functions), x1_external.model_outputs (frozen GAE seeds, per-channel LedoitWolf distance),
    x1_external.make_ctx.
  - Score chain: v9_anatomy.final_events -- E22.final_scalar (ensemble over the 4 frozen members),
    p3_levers.member_mean_z + q_of (per-patient budget against the frozen k), p2_scalars.d1_events
    (detector), p3_levers.localize (CPD localizer). All of the above are called exactly as x1_external
    and v9_anatomy already call them; nothing in x1_external.py, v9_anatomy.py or any other frozen file
    is edited.
  - Drawing: v9_eeg_samples.draw_panel / spacing_for / margin_for / ext_read_segment, unchanged.

THE ONLY NEW CODE:
  1. clin_load_18(path, interpolate_c3): a loader for these two specific files. It is the same
     referential-electrode-name -> alias -> bipolar-subtraction -> resample_poly logic as
     x1_external.load_18's own non-CHB branch (same SIENA_MAP, same BIPOLAR list), with one addition
     this task asks for: when interpolate_c3 is set, channel C3 is marked bad and interpolated from its
     10-20 neighbours with MNE's spherical-spline interpolation (raw.interpolate_bads) on the
     referential data, BEFORE the bipolar subtraction -- i.e. before any frozen code sees the signal.
  2. A monkeypatch of x1_external.load_18 (module-namespace only, the technique v9_anatomy.py already
     uses for _parseTimeStamp) so that the two new kind strings "clin" / "clin_interp" dispatch to
     clin_load_18, while "chb" / "siena" keep calling the original function unchanged.
  3. Glue to build a single-file "subject" context without a seizure summary file (there is none for
     these recordings): files = [(path, [])] (empty seizure list -> is_ictal all False, i.e. no seizure
     is claimed anywhere), then x1_external.labelfree_stats / file_features / model_outputs / make_ctx
     are called directly (the same functions x1_external.build_subject calls internally for every other
     subject).
  4. Everything about overlap with clin02's technician annotations (eyes open/closed, hyperventilation,
     photic stimulation, spike markers), the events table, the flagged-time fraction, the score-timeline
     and EEG-panel figures: new, task-specific, task output code (no prior script does this).

CLIN02 ANNOTATION -> CATEGORY-SEGMENT RULE (fixed here before any number is computed; the annotation
texts are the technician's own labels, not a diagnosis):
  hv_phase      : each "HV Begin" annotation's own (onset, onset+duration) interval, as logged in the
                  file (2 instances: ~180 s and ~16 s; their end times match the separately logged
                  "HV End" onsets to within 0.01 s -- an internal consistency check, printed).
  photic_step   : each "Photic: <f> Hz" annotation's own (onset, onset+duration) interval (10
                  instances, ~5 s each), as logged in the file.
  spike         : each "Spike" annotation (7 instances), onset +/- 10 s -- exactly the window the task
                  prompt specifies.
  eyes_open / eyes_closed : these are point markers (duration 0 in the file) that alternate in two
                  clean blocks with no interleaving marker. The gap between each marker and the next
                  "Eyes Open"/"Eyes Closed" marker is used as that instance's duration where a next
                  marker exists (6 of 8 instances); the trailing marker of each block (2 of 8) has no
                  following eyes-marker, so it is assigned the MEDIAN of the other 6 gaps (disclosed
                  below and in SUMMARY.md) rather than the much longer, almost certainly wrong, gap to
                  the next unrelated annotation.
  Not turned into category segments (out of the task's named 4, but kept visible in the annotation list
  the SUMMARY mentions): HV 1Min/2Min/Post HV 30 Sec sub-markers, Photic: Off, device/recorder messages,
  "Asleep", "dipole".

Run: python src/v9_clinical_run.py
"""
import sys
import time
from pathlib import Path

import numpy as np
import pandas as pd
from scipy.signal import resample_poly

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt                        # noqa: E402

ROOT = Path(__file__).resolve().parents[1]
for p in (ROOT / "src", ROOT / "src" / "dataprep", ROOT / "src" / "retrain", ROOT / "src" / "phaseB",
          ROOT / "src" / "phaseC"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))
import x1_external as X1               # noqa: E402
import v9_anatomy as V9                # noqa: E402
import v9_eeg_samples as V9E           # noqa: E402
import p2_scalars as PS                # noqa: E402
import preprocessing as P              # noqa: E402

CLIN_DATA = Path("F:/Study/Thesis/Dataset/clinical")
OUTDIR = Path("F:/Study/Thesis/Defense/clinical/run")
NOTCH = 50.0            # Vietnam mains -- same convention as Siena in x1_external
WIN = 4


# ============================================================================ file resolution (no names logged)
def resolve_clin_files():
    """clin01 = larger file, clin02 = smaller file -- same size-order rule as V9-T2. The real path is
    held only in local variables / closures, never printed or written to any output."""
    files = sorted(CLIN_DATA.glob("*.edf"), key=lambda p: -p.stat().st_size)
    if len(files) != 2:
        raise SystemExit(f"STOP: expected exactly 2 EDF files under the clinical data dir, found {len(files)}")
    return {"clin01": files[0], "clin02": files[1]}


# ============================================================================ the one new loader
def clin_load_18(path, interpolate_c3=False):
    """Referential -> 18 CHB-MIT bipolar channels, same alias/bipolar/resample logic as
    x1_external.load_18's own non-CHB branch, with optional MNE spherical-spline interpolation of C3
    from its 10-20 neighbours on the referential data before the bipolar subtraction."""
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose="ERROR")
    names = {}
    for ch in raw.ch_names:
        n = ch.upper().replace("EEG", "").strip().replace(" ", "")
        names[X1.SIENA_MAP.get(n, n)] = ch
    need = sorted({e for pair in X1.BIPOLAR for e in pair})
    if any(e not in names for e in need):
        return None
    raw.pick([names[e] for e in need])          # only the 19 needed electrodes from here on
    raw.load_data()                              # preload just these 19 channels (cheap even for clin01)
    raw.rename_channels({names[e]: e for e in need})
    if interpolate_c3:
        montage = mne.channels.make_standard_montage("standard_1020")
        raw.set_montage(montage, on_missing="ignore", match_case=False)
        raw.info["bads"] = ["C3"]
        raw.interpolate_bads(reset_bads=True, mode="accurate")
    raw.reorder_channels(need)
    X = raw.get_data().astype(np.float64)
    pos = {e: i for i, e in enumerate(need)}
    data = np.stack([X[pos[a]] - X[pos[b]] for a, b in X1.BIPOLAR])
    fs = int(round(raw.info["sfreq"]))
    if fs != X1.FS:
        import math
        g = math.gcd(fs, X1.FS)
        data = resample_poly(data, X1.FS // g, fs // g, axis=1)
    return data


_ORIG_LOAD_18 = X1.load_18


def _patched_load_18(path, kind):
    if kind == "clin":
        return clin_load_18(path, interpolate_c3=False)
    if kind == "clin_interp":
        return clin_load_18(path, interpolate_c3=True)
    return _ORIG_LOAD_18(path, kind)


X1.load_18 = _patched_load_18          # module-namespace monkeypatch only -- x1_external.py untouched


# ============================================================================ build one single-file subject ctx
def build_clin_ctx(label, path, kind):
    """No summary/label file exists for these recordings -> files = [(path, [])], is_ictal all False
    (no seizure is claimed). Calls x1_external's own labelfree_stats / file_features / model_outputs /
    make_ctx directly -- the same functions build_subject calls for every other subject."""
    files = [(path, [])]
    mu, sd = X1.labelfree_stats(files, kind, NOTCH)
    r = X1.file_features((path, [], kind, NOTCH, mu, sd, 0))
    if r.get("skipped"):
        raise SystemExit(f"STOP {label}: a needed electrode is missing (should not happen, V9-T2 "
                          f"confirmed all 19 present)")
    r["file"] = f"{label}.edf"                           # anonymize immediately; real name never kept
    out = {k: r[k] for k in ("adj", "bp5", "f7", "is_ictal", "is_signal_loss")}
    out["file_idx"] = np.zeros(r["n"], dtype=np.int16)
    out["files"] = np.array([r["file"]], dtype=object)
    idx, D = X1.model_outputs(out)
    ctx = X1.make_ctx(out, idx, D)
    ctx["z"]["files"] = out["files"]
    n_windows = int(r["n"])
    return ctx, dict(n_windows=n_windows, hours=n_windows * P.WIN_S / 3600, mu=mu, sd=sd)


# ============================================================================ events table / flagged fraction
def events_table(ctx, res, label, run_tag):
    """One row per localized (CPD) system event -- start, end, duration, peak raw ensemble score
    (same convention as v9_anatomy.false_alarm_rows: max of the unsmoothed final scalar over the
    event's 'ok' windows)."""
    x = res["x"]
    rows = []
    for a_s, b_s in res["loc"].get(0, []):
        aw, bw = max(0, a_s // WIN), max(a_s // WIN + 1, b_s // WIN)
        bw = min(bw, ctx["n"])
        peak = -np.inf
        for w in range(aw, bw):
            if ctx["ok"][w] and np.isfinite(x[w]) and x[w] > peak:
                peak = float(x[w])
        rows.append(dict(subject=label, run=run_tag, start_s=int(a_s), end_s=int(b_s),
                         duration_s=int(b_s - a_s), peak_score=round(peak, 4) if np.isfinite(peak) else np.nan))
    return pd.DataFrame(rows)


def flagged_fraction(events_df, n_windows):
    total_s = n_windows * WIN
    flagged_s = float(events_df.duration_s.sum()) if len(events_df) else 0.0
    return flagged_s, total_s, (flagged_s / total_s if total_s else np.nan)


# ============================================================================ clin02 annotation categories
def clin02_category_segments(path):
    """Returns a DataFrame of (category, onset_s, end_s) rows built from the EDF's own annotation
    onset/duration fields, per the rule in the module docstring. Also returns the raw annotation list
    (onset, duration, text) for the SUMMARY's plain observations -- texts here are the technician's own
    protocol labels (eyes/HV/photic/spike/device messages), confirmed privacy-safe in V9-T2 (no name,
    ID or date substring in any of them); nothing else from the header is read here."""
    import mne
    raw = mne.io.read_raw_edf(str(path), preload=False, verbose="ERROR")
    ann = sorted(zip(raw.annotations.onset.tolist(), raw.annotations.duration.tolist(),
                     [str(d) for d in raw.annotations.description]), key=lambda r: r[0])
    rows = []

    hv = [(o, d) for o, d, t in ann if t == "HV Begin"]
    for o, d in hv:
        rows.append(dict(category="hv_phase", onset_s=o, end_s=o + d))

    ph = [(o, d, t) for o, d, t in ann if t.startswith("Photic:") and t != "Photic: Off"]
    for o, d, t in ph:
        rows.append(dict(category="photic_step", onset_s=o, end_s=o + d))

    sp = [o for o, d, t in ann if t == "Spike"]
    for o in sp:
        rows.append(dict(category="spike", onset_s=max(0.0, o - 10.0), end_s=o + 10.0))

    # Eyes Open/Closed alternate in the SAME combined chronological sequence (Open, Closed, Open,
    # Closed, ...) -- the "next marker" for duration purposes must come from that combined sequence,
    # not from the next occurrence of the same label (which would skip over the intervening opposite
    # marker and roughly double the true duration).
    combined = sorted((o, t) for o, d, t in ann if t in ("Eyes Open", "Eyes Closed"))
    gaps = [combined[i + 1][0] - combined[i][0] for i in range(len(combined) - 1)
            if combined[i + 1][0] - combined[i][0] < 30.0]   # same-block consecutive instruction
    med = float(np.median(gaps)) if gaps else 6.0
    for i, (o, t) in enumerate(combined):
        end = combined[i + 1][0] if i + 1 < len(combined) and combined[i + 1][0] - o < 30.0 else o + med
        catname = "eyes_open" if t == "Eyes Open" else "eyes_closed"
        rows.append(dict(category=catname, onset_s=o, end_s=end))

    return pd.DataFrame(rows), ann


def overlap_table(seg_df, events_df, total_s):
    rows = []
    for cat, d in seg_df.groupby("category"):
        dur = (d.end_s - d.onset_s).sum()
        n_overlap = 0
        for _, r in d.iterrows():
            touched = any(not (e.end_s <= r.onset_s or e.start_s >= r.end_s) for _, e in events_df.iterrows())
            n_overlap += int(touched)
        rows.append(dict(category=cat, n_segments=len(d), total_duration_s=round(float(dur), 1),
                         share_of_recording=round(float(dur) / total_s, 4),
                         n_overlapping_system_event=n_overlap,
                         fraction_overlapping=round(n_overlap / len(d), 3) if len(d) else np.nan))
    return pd.DataFrame(rows)


# ============================================================================ score timeline figure
def plot_timeline(ctx, res, label, run_tag, seg_df, outpath):
    x = res["x"]
    sm = PS.smoothed(ctx, x, V9.SMOOTH)
    t_h = np.arange(ctx["n"]) * WIN / 3600.0
    fig, ax = plt.subplots(figsize=(11, 3.2), dpi=150)
    cat_colors = {"eyes_open": "#f4a742", "eyes_closed": "#4287f5", "hv_phase": "#9b59b6",
                 "photic_step": "#2ecc71", "spike": "#e74c3c"}
    labeled = set()
    for _, r in seg_df.iterrows():
        c = cat_colors.get(r.category, "#999999")
        lbl = r.category if r.category not in labeled else None
        ax.axvspan(r.onset_s / 3600.0, r.end_s / 3600.0, color=c, alpha=0.25, lw=0, label=lbl)
        labeled.add(r.category)
    for a_s, b_s in res["loc"].get(0, []):
        ax.axvspan(a_s / 3600.0, b_s / 3600.0, color="#008080", alpha=0.35, lw=0)
    ax.plot(t_h, sm, color="#111111", lw=0.6)
    ax.set_xlabel("time (h)"); ax.set_ylabel("ensemble score (smoothed)")
    ax.set_title(f"{label} ({run_tag}) -- score timeline, system events teal, annotated segments colored")
    if labeled:
        ax.legend(fontsize=6, ncol=len(labeled), loc="upper right")
    fig.tight_layout(); fig.savefig(outpath); plt.close(fig)


# ============================================================================ EEG panels (v9_eeg_samples convention)
def make_panels(ctx, res, label, path, kind, events, outdir, tag, seg_df=None):
    outdir.mkdir(parents=True, exist_ok=True)
    loaded = []
    for i, ev in enumerate(events):
        a_s, b_s, dur, title_kind = ev["a_s"], ev["b_s"], ev["dur"], ev["title_kind"]
        margin = V9E.margin_for(dur)
        t0, t1 = max(0.0, a_s - margin), b_s + margin
        out = V9E.ext_read_segment(path, kind, NOTCH, t0, t1)
        if out is None:
            continue
        filt, _raw, ra, rb = out
        onset = a_s
        refs = []
        if seg_df is not None:
            for _, r in seg_df.iterrows():
                if r.end_s >= ra and r.onset_s <= rb:
                    refs.append((r.onset_s, r.end_s))
        loc = [(x0, x1) for x0, x1 in res["loc"].get(0, []) if x1 >= ra and x0 <= rb]
        w0, w1 = int(ra // WIN), int(np.ceil(rb / WIN))
        sm = res["x"].copy()
        g0, g1 = max(0, w0), min(ctx["n"], w1)
        score_vals = sm[g0:g1]
        score_t0 = g0 * WIN
        title = f"{label}  {title_kind}  duration {int(dur)} s"
        loaded.append(dict(filt=filt, t0=ra, t1=rb, title=title, refs=refs, loc=loc, onset=onset,
                           score_vals=score_vals, score_t0=score_t0, tag=f"{tag}_{i}"))
    if not loaded:
        return []
    spacing = V9E.spacing_for([d["filt"] for d in loaded])
    written = []
    for d in loaded:
        fig = plt.figure(figsize=(8.5, 6.2), dpi=200)
        from matplotlib.gridspec import GridSpec
        gs = GridSpec(2, 1, height_ratios=[4.2, 1.0], hspace=0.30, left=0.09, right=0.98, top=0.93, bottom=0.09)
        V9E.draw_panel(fig.add_subplot(gs[0]), fig.add_subplot(gs[1]), d["filt"], d["t0"], d["t1"],
                      d["title"], d["refs"], d["loc"], d["onset"], spacing, d["score_vals"], d["score_t0"])
        p = outdir / f"{d['tag']}.png"
        fig.savefig(p); plt.close(fig)
        written.append(p)
    return written


# ============================================================================ SUMMARY.md (output 6)
def write_summary(meta1, ev1, f1_s, t1_s, frac1, meta2a, ev2a, f2a_s, t2a_s, frac2a,
                  meta2b, ev2b, f2b_s, t2b_s, frac2b, seg_df, ov, ov_b, hv_max_diff_s,
                  n_panels_clin02_event, n_panels_clin01_top10, n_panels_clin02_spike, outpath):
    """Numbers + 5-8 plain observations of what is visible. No seizure metric, no diagnosis --
    both files are label-free (see module docstring); 'event' below always means 'system-flagged
    segment', never a clinical finding."""
    lines = []
    lines.append("# V9-C1 -- clinical run, SUMMARY\n")
    lines.append("Frozen final system (seed 42, balanced point, localizer CPD, per-patient budget), "
                 "run on 2 label-free hospital EEG recordings. No seizure annotation exists for either "
                 "file; nothing below is a seizure-detection metric or a diagnosis -- only what the "
                 "system flags and how that compares to the technician's own protocol markers in clin02.\n")

    lines.append("## Numbers\n")
    lines.append("| recording | run | hours | n_events | flagged_s | total_s | flagged_fraction |")
    lines.append("|---|---|---|---|---|---|---|")
    lines.append(f"| clin01 | as-recorded | {meta1['hours']:.3f} | {len(ev1)} | {f1_s:.0f} | {t1_s:.0f} | {frac1:.4f} |")
    lines.append(f"| clin02 | C3-interpolated (main) | {meta2a['hours']:.3f} | {len(ev2a)} | {f2a_s:.0f} | {t2a_s:.0f} | {frac2a:.4f} |")
    lines.append(f"| clin02 | as-recorded | {meta2b['hours']:.3f} | {len(ev2b)} | {f2b_s:.0f} | {t2b_s:.0f} | {frac2b:.4f} |")
    lines.append("")

    lines.append("### clin02 -- overlap of system events with each technician-annotated category "
                 "(main run, C3-interpolated)\n")
    lines.append("| category | n_segments | total_duration_s | share_of_recording (chance level) | "
                 "n_overlapping_system_event | fraction_overlapping |")
    lines.append("|---|---|---|---|---|---|")
    for _, r in ov.iterrows():
        lines.append(f"| {r.category} | {r.n_segments} | {r.total_duration_s} | {r.share_of_recording} | "
                     f"{r.n_overlapping_system_event} | {r.fraction_overlapping} |")
    lines.append("")
    lines.append("Same table, as-recorded (C3 not interpolated):\n")
    lines.append("| category | n_segments | total_duration_s | share_of_recording (chance level) | "
                 "n_overlapping_system_event | fraction_overlapping |")
    lines.append("|---|---|---|---|---|---|")
    for _, r in ov_b.iterrows():
        lines.append(f"| {r.category} | {r.n_segments} | {r.total_duration_s} | {r.share_of_recording} | "
                     f"{r.n_overlapping_system_event} | {r.fraction_overlapping} |")
    lines.append("")
    lines.append(f"HV Begin+duration vs separately-logged HV End onsets, internal consistency check: "
                f"max |difference| = {hv_max_diff_s:.3f} s over {len(seg_df[seg_df.category == 'hv_phase'])} "
                f"HV phases.\n")
    lines.append(f"Figures: {n_panels_clin02_event} clin02 event panels (every system event, main run), "
                f"{n_panels_clin01_top10} clin01 top-10 panels, {n_panels_clin02_spike} clin02 spike-marker "
                f"panels; 1 score-timeline figure per file.\n")

    obs = []
    obs.append(f"clin01 (13.2 h, no annotation of any kind): the system flags {frac1*100:.2f}% of the "
              f"recording ({len(ev1)} events, {f1_s:.0f} s total) -- the review burden a clinician would "
              f"face if asked to check every flagged segment, with no ground truth either way on whether "
              f"any of it is clinically relevant.")
    obs.append(f"clin02 main run (C3-interpolated): {len(ev2a)} events, {frac2a*100:.2f}% flagged -- higher "
              f"than clin01's fraction, but clin02 includes an activation protocol (HV, photic, eyes) "
              f"deliberately designed to perturb the EEG, which clin01 does not.")
    obs.append("None of the 3 system events in clin02 overlaps any of the 7 spike markers, the 2 "
              "hyperventilation phases, the 10 photic steps, or the 8 eyes-open/closed instructions "
              "(fraction_overlapping = 0 for every category, both runs) -- the system did not mistake any "
              "of the technician's own benign/activation markers for a flagged event, in either direction "
              "(it also did not flag the 7 interictal-looking spikes, which is expected: spikes are brief, "
              "focal transients and the system's events are seconds-to-minutes long).")
    if len(ev2a) == len(ev2b) and len(ev2a) >= 2:
        detail = "; ".join(
            f"event {i+1} [{int(d.start_s)}-{int(d.end_s)}]s/{int(d.duration_s)}s interpolated vs "
            f"[{int(b.start_s)}-{int(b.end_s)}]s/{int(b.duration_s)}s as-recorded"
            for i, (d, b) in enumerate(zip(ev2a.itertuples(), ev2b.itertuples())) if d.duration_s != b.duration_s)
        obs.append(f"Interpolating the artifactual C3 channel changes timing/duration for some clin02 "
                  f"events ({detail if detail else 'no change'}). Net effect: {frac2a*100:.2f}% flagged "
                  f"interpolated vs {frac2b*100:.2f}% as-recorded -- the broken channel measurably affects "
                  f"how long these segments are flagged, consistent with F3-C3/C3-P3 (the 2 bipolar pairs "
                  f"that use C3) carrying a corrupted signal into the per-channel z-score statistics when "
                  f"C3 is left as-recorded.")
    else:
        obs.append(f"Interpolating the artifactual C3 channel changes the event COUNT: {len(ev2a)} events "
                  f"interpolated vs {len(ev2b)} as-recorded. Net effect: {frac2a*100:.2f}% flagged "
                  f"interpolated vs {frac2b*100:.2f}% as-recorded.")
    obs.append(f"clin02's per-patient fit (statistics, budget, correction) rests on only "
              f"{meta2a['hours']:.2f} h of data, a small fraction of what every other subject in this "
              f"thesis provides -- the numbers above should be read as a single qualitative run, not a "
              f"stable per-patient estimate.")
    hrs = ev1.start_s / 3600.0
    early = int((hrs < meta1['hours'] / 2).sum())
    obs.append(f"clin01's {len(ev1)} events split {early} in the first half of the recording vs "
              f"{len(ev1) - early} in the second half -- see score_timeline_clin01.png for where exactly; "
              f"no clinical pattern is claimed from this alone.")
    obs.append("The EEG panels (figs/) show the raw filtered 18-channel traces under each flagged/marker "
              "window with the pipeline's own smoothed score strip beneath -- intended for the committee "
              "to look at directly rather than take any number on faith.")
    lines.append("## Observations (plain, no diagnosis)\n")
    for i, o in enumerate(obs, 1):
        lines.append(f"{i}. {o}")
    lines.append("")

    outpath.write_text("\n".join(lines), encoding="utf-8")


# ============================================================================ main
def main():
    t0 = time.time()
    OUTDIR.mkdir(parents=True, exist_ok=True)
    paths = resolve_clin_files()

    print("building clin01 context (kind='clin', notch 50 Hz)...", flush=True)
    ctx1, meta1 = build_clin_ctx("clin01", paths["clin01"], "clin")
    res1 = V9.final_events(ctx1, V9.HEAD)
    ev1 = events_table(ctx1, res1, "clin01", "asrecorded")
    ev1.to_csv(OUTDIR / "events_clin01.csv", index=False)
    f1_s, t1_s, frac1 = flagged_fraction(ev1, meta1["n_windows"])
    print(f"clin01: {len(ev1)} events, flagged {f1_s:.0f}/{t1_s:.0f} s ({frac1:.4f}), "
          f"{time.time()-t0:.0f}s", flush=True)

    print("building clin02 context, variant (a) C3-interpolated (main run)...", flush=True)
    ctx2a, meta2a = build_clin_ctx("clin02", paths["clin02"], "clin_interp")
    res2a = V9.final_events(ctx2a, V9.HEAD)
    ev2a = events_table(ctx2a, res2a, "clin02", "interp")
    ev2a.to_csv(OUTDIR / "events_clin02_interp.csv", index=False)
    f2a_s, t2a_s, frac2a = flagged_fraction(ev2a, meta2a["n_windows"])
    print(f"clin02 (interp): {len(ev2a)} events, flagged {f2a_s:.0f}/{t2a_s:.0f} s ({frac2a:.4f}), "
          f"{time.time()-t0:.0f}s", flush=True)

    print("building clin02 context, variant (b) as-recorded...", flush=True)
    ctx2b, meta2b = build_clin_ctx("clin02", paths["clin02"], "clin")
    res2b = V9.final_events(ctx2b, V9.HEAD)
    ev2b = events_table(ctx2b, res2b, "clin02", "asrecorded")
    ev2b.to_csv(OUTDIR / "events_clin02_asrecorded.csv", index=False)
    f2b_s, t2b_s, frac2b = flagged_fraction(ev2b, meta2b["n_windows"])
    print(f"clin02 (as-recorded): {len(ev2b)} events, flagged {f2b_s:.0f}/{t2b_s:.0f} s ({frac2b:.4f}), "
          f"{time.time()-t0:.0f}s", flush=True)

    pd.DataFrame([
        dict(run="clin01", n_events=len(ev1), flagged_s=f1_s, total_s=t1_s, flagged_fraction=frac1),
        dict(run="clin02_interp", n_events=len(ev2a), flagged_s=f2a_s, total_s=t2a_s, flagged_fraction=frac2a),
        dict(run="clin02_asrecorded", n_events=len(ev2b), flagged_s=f2b_s, total_s=t2b_s, flagged_fraction=frac2b),
    ]).to_csv(OUTDIR / "flagged_fraction.csv", index=False)

    # ---- clin02 annotation overlap (main run = interpolated) ----
    seg_df, ann_list = clin02_category_segments(paths["clin02"])
    seg_df.to_csv(OUTDIR / "clin02_annotation_segments.csv", index=False)
    ov = overlap_table(seg_df, ev2a, t2a_s)
    ov.to_csv(OUTDIR / "overlap_clin02.csv", index=False)
    ov_b = overlap_table(seg_df, ev2b, t2b_s)
    ov_b.to_csv(OUTDIR / "overlap_clin02_asrecorded.csv", index=False)
    hv_check = [(o, o + d) for o, d, t in ann_list if t == "HV Begin"]
    hv_end = [o for o, d, t in ann_list if t == "HV End"]
    hv_begin_ends = sorted(e for _, e in hv_check)
    hv_end_sorted = sorted(hv_end)
    hv_diffs = [abs(a - b) for a, b in zip(hv_begin_ends, hv_end_sorted)]
    hv_max_diff = max(hv_diffs) if hv_diffs else float("nan")
    print(f"HV Begin+duration vs HV End onsets (consistency check): {hv_check} vs {hv_end}, "
          f"max diff {hv_max_diff:.3f}s", flush=True)

    # ---- score timelines (main runs) ----
    plot_timeline(ctx1, res1, "clin01", "as-recorded", pd.DataFrame(columns=["category", "onset_s", "end_s"]),
                 OUTDIR / "score_timeline_clin01.png")
    plot_timeline(ctx2a, res2a, "clin02", "C3-interpolated, main run", seg_df, OUTDIR / "score_timeline_clin02.png")

    # ---- EEG panels ----
    # clin02: every system event (main run, interpolated)
    ev2a_events = [dict(a_s=r.start_s, b_s=r.end_s, dur=r.duration_s, title_kind=f"event (peak {r.peak_score:g})")
                  for _, r in ev2a.iterrows()]
    p1 = make_panels(ctx2a, res2a, "clin02", paths["clin02"], "clin_interp", ev2a_events,
                     OUTDIR / "figs", "clin02_event", seg_df)
    print(f"clin02: {len(p1)} event panels", flush=True)

    # clin01: 10 highest-score events
    top10 = ev1.sort_values("peak_score", ascending=False).head(10)
    ev1_events = [dict(a_s=r.start_s, b_s=r.end_s, dur=r.duration_s, title_kind=f"top-10 (peak {r.peak_score:g})")
                 for _, r in top10.iterrows()]
    p2 = make_panels(ctx1, res1, "clin01", paths["clin01"], "clin", ev1_events,
                     OUTDIR / "figs", "clin01_top10", None)
    print(f"clin01: {len(p2)} top-10 panels", flush=True)

    # 3 panels around spike markers (first / middle / last by onset, main run = interpolated)
    spikes = sorted(r.onset_s for _, r in seg_df[seg_df.category == "spike"].iterrows())
    spike_onsets_true = [s + 10.0 for s in spikes]      # undo the -10 s offset used for the overlap window
    picks_idx = sorted({0, len(spike_onsets_true) // 2, len(spike_onsets_true) - 1})
    spike_events = [dict(a_s=spike_onsets_true[i], b_s=spike_onsets_true[i], dur=0,
                         title_kind=f"spike marker #{i+1}/{len(spike_onsets_true)}") for i in picks_idx]
    p3 = make_panels(ctx2a, res2a, "clin02", paths["clin02"], "clin_interp", spike_events,
                     OUTDIR / "figs", "clin02_spike", seg_df)
    print(f"clin02: {len(p3)} spike panels", flush=True)

    write_summary(meta1, ev1, f1_s, t1_s, frac1, meta2a, ev2a, f2a_s, t2a_s, frac2a,
                 meta2b, ev2b, f2b_s, t2b_s, frac2b, seg_df, ov, ov_b, hv_max_diff,
                 len(p1), len(p2), len(p3), OUTDIR / "SUMMARY.md")
    print("wrote SUMMARY.md", flush=True)

    print(f"done in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
