#!/usr/bin/env python
"""
c5_step3_clips.py -- chat C5c (Track C), Step 3: the blinded clips of the exploratory expert review with Dr. An, chosen
by the rules of results/c5_szscan/step3/PROTOCOL_STEP3.md §3 (approved by the author 27/11, committed before this ran).

READ ONLY on the application (database opened read-only; caches only read). From the session-mode studies:
  hospital clips   the private studies (clin01, clin02): flagged events (highest peak score; random among the rest) and
                   controls (random 60-s segments >= 5 min from any AI event, not in the first or last minute)
  anchor clips     the 8 CHB-MIT test patients and the 14 Siena patients: seizures found, seizures missed, false alarms
                   (matching as SzCORE's tolerance: an AI event overlapping [onset - 30 s, offset + 60 s])
Each clip: 60 s of the application's filtered signal ({stem}.filtered.npy, verified against the EDF by G9), 18
derivations in µV; event clips start 15 s before the onset; no clip holds signal loss (all 18 derivations flat in a
window of {stem}.raw.npy, the application's own rule). Order shuffled with the seed; numbered C01 ...

Outputs ONLY in the private folder (--out, default F:/Study/Thesis/Eureka/C5_review; never committed):
  review.html   offline review page (Vietnamese): clip images at two gains, the form of PROTOCOL §4, time per clip;
                answers kept in the browser and downloaded as CSV ("Tải kết quả")
  key.csv       which clip is which (hospital rows with neutral study and file names only)
  selection.json the rule's inputs and counts (seed, version, candidates per set)
  clips/        PNG images (two 30-s pages per clip, standard and half gain)
Nothing is printed about a hospital recording except counts.

Run: PYTHONUTF8=1 python src/c5_step3_clips.py --chb F:/Study/Thesis/Dataset/CHB-MIT --siena F:/Study/Thesis/Dataset/siena --version 24
"""
import argparse
import base64
import csv
import json
import re
import sqlite3
import sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
BACKEND = ROOT / "web_demo" / "backend"
sys.path.insert(0, str(ROOT / "src"))

FS, WIN, NW = 256, 1024, 4.0           # samples per second, per window; seconds per window
CLIP_S, LEAD_S = 60.0, 15.0
CTRL_GAP_S, EDGE_S = 300.0, 60.0
PRE_S, POST_S = 30.0, 60.0            # SzCORE tolerance for "an event finds a seizure"
SEED = 20261127
CH = ["FP1-F7", "F7-T7", "T7-P7", "P7-O1", "FP1-F3", "F3-C3", "C3-P3", "P3-O1", "FP2-F4", "F4-C4", "C4-P4", "P4-O2",
      "FP2-F8", "F8-T8", "T8-P8", "P8-O2", "FZ-CZ", "CZ-PZ"]
TEST = ["chb03", "chb06", "chb13", "chb14", "chb15", "chb16", "chb17", "chb18"]
VERSIONS = {24: dict(top=5, rnd=5, ctrl=6, found=(2, 1), missed=(1, 1), fa=(1, 2)),
            18: dict(top=4, rnd=3, ctrl=5, found=(1, 1), missed=(1, 1), fa=(1, 1))}   # (Siena, CHB-MIT)
DEFAULT_OUT = Path("F:/Study/Thesis/Eureka/C5_review")


# ════════════════════════════════════════════════════════════════════ reading
def db_read(db_path):
    con = sqlite3.connect(f"file:{Path(db_path).as_posix()}?mode=ro", uri=True)
    con.row_factory = sqlite3.Row
    subs = {r["id"]: dict(r) for r in con.execute("SELECT id, mode, mains_hz, private FROM subjects")}
    files = [dict(r) for r in con.execute("SELECT id, subject_id, filename, duration_seconds, notice FROM files "
                                          "ORDER BY subject_id, filename")]
    ev = [dict(r) for r in con.execute("SELECT file_id, onset_sec, offset_sec FROM events WHERE source = 'AI' "
                                       "ORDER BY file_id, onset_sec")]
    con.close()
    return subs, files, ev


class Rec:
    """one recording of the database with its caches (memory-mapped, read only)."""
    def __init__(self, f, subj, uploads):
        self.f, self.sid, self.fn = f, f["subject_id"], f["filename"]
        stem = Path(self.fn).stem
        d = Path(uploads) / self.sid
        self.score = np.load(d / f"{stem}.score.npy", mmap_mode="r")
        self.raw_p, self.flt_p = d / f"{stem}.raw.npy", d / f"{stem}.filtered.npy"
        raw = np.load(self.raw_p, mmap_mode="r")
        self.n = raw.shape[0]
        self.loss = np.array([bool(np.all(np.asarray(raw[i], np.float64).std(axis=1) < 1e-10)) for i in range(self.n)])
        del raw
        self.dur = self.n * NW
        self.mains = subj["mains_hz"]
        self.interp = "C3" if "C3" in (f.get("notice") or "") and "interpolated" in (f.get("notice") or "") else ""

    def peak(self, on, off):
        a, b = int(on // NW), max(int(np.ceil(off / NW)), int(on // NW) + 1)
        return float(np.max(self.score[a:min(b, self.n)])) if a < self.n else float("nan")

    def clip_start(self, t):
        return float(min(max(0.0, t - LEAD_S), self.dur - CLIP_S))

    def clean(self, s):
        a, b = int(s // NW), int(np.ceil((s + CLIP_S) / NW))
        return s >= 0 and s + CLIP_S <= self.dur + 1e-9 and not self.loss[a:b].any()

    def signal(self, s):
        """60 s of the filtered cache, µV, (18, 15360)."""
        flt = np.load(self.flt_p, mmap_mode="r")
        a = int(round(s * FS))
        w0, w1 = a // WIN, (a + int(CLIP_S * FS) - 1) // WIN
        x = np.asarray(flt[w0:w1 + 1], np.float64).transpose(1, 0, 2).reshape(18, -1)
        off = a - w0 * WIN
        out = x[:, off:off + int(CLIP_S * FS)] * 1e6
        del flt, x
        return out


# ════════════════════════════════════════════════════════════════════ selection (PROTOCOL §3)
def hospital(recs, evs, v, rng):
    pool = []
    for r in recs:
        for e in evs.get(r.f["id"], []):
            s = r.clip_start(e["onset_sec"])
            if r.clean(s):
                pool.append(dict(rec=r, on=e["onset_sec"], off=e["offset_sec"], peak=r.peak(e["onset_sec"],
                                                                                        e["offset_sec"]), start=s))
    pool.sort(key=lambda c: (-c["peak"], c["rec"].sid, c["on"]))
    top = pool[:v["top"]]
    rest = pool[v["top"]:]
    idx = sorted(rng.choice(len(rest), size=min(v["rnd"], len(rest)), replace=False).tolist()) if rest else []
    rnd = [rest[i] for i in idx]
    n_ctrl = v["ctrl"] + (v["top"] - len(top)) + (v["rnd"] - len(rnd))
    tot = sum(r.dur for r in recs)
    alloc = {}
    if len(recs) == 1:
        alloc[recs[0].sid] = n_ctrl
    else:
        small = min(recs, key=lambda r: r.dur)
        alloc[small.sid] = max(1, int(round(n_ctrl * small.dur / tot)))
        for r in recs:
            if r is not small:
                alloc[r.sid] = n_ctrl - alloc[small.sid]
    ctrl = []
    for r in recs:
        ev = [(e["onset_sec"], e["offset_sec"]) for e in evs.get(r.f["id"], [])]
        got, tries = 0, 0
        while got < alloc[r.sid] and tries < 100000:
            tries += 1
            s = float(rng.uniform(EDGE_S, r.dur - EDGE_S - CLIP_S)) if r.dur > 2 * EDGE_S + CLIP_S else -1.0
            if s < 0:
                break
            if any(s < b + CTRL_GAP_S and s + CLIP_S > a - CTRL_GAP_S for a, b in ev) or not r.clean(s):
                continue
            if any(c["rec"] is r and abs(c["start"] - s) < CLIP_S for c in ctrl):
                continue
            ctrl.append(dict(rec=r, on=None, off=None, peak=r.peak(s, s + CLIP_S), start=s))
            got += 1
    out = [dict(c, set="flagged, highest score") for c in top] + [dict(c, set="flagged, random") for c in rnd] + \
          [dict(c, set="control") for c in ctrl]
    return out, dict(events_with_clean_clip=len(pool), top=len(top), random=len(rnd), controls=len(ctrl),
                     controls_per_study={k: v_ for k, v_ in alloc.items()})


def anchor_candidates(recs_by_sid, evs, ann_of):
    """found / missed seizures and false-alarm events per dataset: dicts with rec, on, off, dur, peak."""
    out = {d: dict(found=[], missed=[], fa=[]) for d in ("Siena", "CHB-MIT")}
    for sid, recs in sorted(recs_by_sid.items()):
        d = "Siena" if sid.startswith("PN") else "CHB-MIT"
        ann = ann_of(sid)
        for r in recs:
            ev = [(e["onset_sec"], e["offset_sec"]) for e in evs.get(r.f["id"], [])]
            sz = ann.get(r.fn, [])
            hit = [False] * len(ev)
            for (a, b) in sz:
                m = [i for i, (x, y) in enumerate(ev) if x < b + POST_S and y > a - PRE_S]
                for i in m:
                    hit[i] = True
                c = dict(rec=r, on=float(a), off=float(b), dur=float(b - a), peak=r.peak(a, b), start=r.clip_start(a))
                if r.clean(c["start"]):
                    out[d]["found" if m else "missed"].append(c)
            for i, (x, y) in enumerate(ev):
                if not hit[i]:
                    c = dict(rec=r, on=x, off=y, dur=y - x, peak=r.peak(x, y), start=r.clip_start(x))
                    if r.clean(c["start"]):
                        out[d]["fa"].append(c)
    return out


def anchors(cands, v):
    chosen, info = [], {}
    for d, k in (("Siena", 0), ("CHB-MIT", 1)):
        used = set()
        for cat, label in (("found", "seizure found"), ("missed", "seizure missed"), ("fa", "false alarm")):
            pool = cands[d][cat]
            if cat == "fa":
                key = lambda c: (-c["peak"], c["rec"].sid, c["on"])  # noqa: E731
            else:
                med = float(np.median([c["dur"] for c in pool])) if pool else 0.0
                key = lambda c, med=med: (abs(c["dur"] - med), c["rec"].sid, c["on"])  # noqa: E731
            n = v[cat][k]
            got = []
            for c in sorted(pool, key=key):
                if len(got) == n:
                    break
                if c["rec"].sid in used:
                    continue
                got.append(dict(c, set=label, dataset=d))
                used.add(c["rec"].sid)
            chosen += got
            info[f"{d} {label}"] = dict(candidates=len(pool), chosen=len(got),
                                        median_duration_s=None if cat == "fa" or not pool else
                                        float(np.median([c["dur"] for c in pool])))
    return chosen, info


# ════════════════════════════════════════════════════════════════════ rendering and review page
def render(sig, path, spacing_uv, title_note):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    pages = []
    for p in range(2):
        seg = sig[:, p * 30 * FS:(p + 1) * 30 * FS]
        t = np.arange(seg.shape[1]) / FS + p * 30
        fig, ax = plt.subplots(figsize=(15, 8.5), dpi=100)
        for i in range(18):
            ax.plot(t, seg[i] - i * spacing_uv, color="black", lw=0.6)
        ax.set_yticks([-i * spacing_uv for i in range(18)])
        ax.set_yticklabels(CH, fontsize=9)
        ax.set_xlim(t[0], t[0] + 30)
        ax.set_ylim(-17.8 * spacing_uv - spacing_uv, spacing_uv * 1.2)
        ax.set_xticks(np.arange(p * 30, p * 30 + 31, 1), minor=True)
        ax.set_xticks(np.arange(p * 30, p * 30 + 31, 5))
        ax.grid(axis="x", which="minor", color="#dddddd", lw=0.5)
        ax.grid(axis="x", which="major", color="#bbbbbb", lw=0.8)
        ax.set_xlabel("giây trong clip")
        x0 = t[0] + 29.0
        ax.plot([x0, x0], [spacing_uv * 0.9, spacing_uv * 0.9 - 100], color="tab:blue", lw=2)
        ax.text(x0 - 0.2, spacing_uv * 0.9 - 50, "100 µV", color="tab:blue", ha="right", va="center", fontsize=9)
        ax.set_title(title_note, fontsize=10, loc="left")
        for s in ("top", "right"):
            ax.spines[s].set_visible(False)
        fig.tight_layout()
        q = path.with_name(f"{path.stem}_p{p + 1}.png")
        fig.savefig(q)
        plt.close(fig)
        pages.append(q)
    return pages


FORM_JS = r"""
const CLIPS = __CLIPS__;
const CLASSES = ["Cơn động kinh (dạng ictal)", "Phóng điện dạng động kinh giữa cơn (IED)", "Nhiễu: cơ",
  "Nhiễu: cử động mắt", "Nhiễu: điện cực", "Nhiễu: cử động", "Nhiễu: khác",
  "Hoạt động sinh lý / biến thể bình thường (kể cả giấc ngủ)", "Nền bình thường", "Không chắc chắn"];
let i = 0, gain = "std", shown = Date.now();
let A = {};
try { A = JSON.parse(localStorage.getItem("c5_review_answers") || "{}"); } catch (e) { A = {}; }
function save() { try { localStorage.setItem("c5_review_answers", JSON.stringify(A)); } catch (e) {} }
function el(id) { return document.getElementById(id); }
function addTime() { const c = CLIPS[i].id; A[c] = A[c] || {}; A[c].seconds = (A[c].seconds || 0) + (Date.now() - shown) / 1000; shown = Date.now(); }
function show() {
  const c = CLIPS[i];
  el("hdr").textContent = `Clip ${c.id}  (${i + 1} / ${CLIPS.length})`;
  el("note").textContent = c.note;
  el("p1").src = c.img[gain][0]; el("p2").src = c.img[gain][1];
  el("gainbtn").textContent = gain === "std" ? "Giảm độ khuếch đại ×½" : "Độ khuếch đại chuẩn";
  const a = A[c.id] || {};
  document.querySelectorAll("input[name=cls]").forEach(r => r.checked = (r.value === a.cls));
  document.querySelectorAll("input[name=conf]").forEach(r => r.checked = (r.value === String(a.conf)));
  document.querySelectorAll("input[name=show]").forEach(r => r.checked = (r.value === a.show));
  el("cmt").value = a.comment || "";
  el("status").textContent = Object.keys(A).filter(k => A[k].cls).length + " / " + CLIPS.length + " clip đã trả lời";
  shown = Date.now(); window.scrollTo(0, 0);
}
function record() {
  const c = CLIPS[i].id; A[c] = A[c] || {};
  const g = n => { const r = document.querySelector(`input[name=${n}]:checked`); return r ? r.value : ""; };
  A[c].cls = g("cls"); A[c].conf = g("conf"); A[c].show = g("show"); A[c].comment = el("cmt").value;
  A[c].gain_halved = (A[c].gain_halved || false) || gain === "half";
}
function next(d) { addTime(); record(); save(); i = Math.min(CLIPS.length - 1, Math.max(0, i + d)); gain = "std"; show(); }
function toggleGain() { gain = gain === "std" ? "half" : "std"; show(); }
function download() {
  addTime(); record(); save();
  const rows = [["clip", "class", "confidence", "show_me", "seconds", "gain_halved", "comment"]];
  CLIPS.forEach(c => { const a = A[c.id] || {}; rows.push([c.id, a.cls || "", a.conf || "", a.show || "",
    (a.seconds || 0).toFixed(1), a.gain_halved ? "yes" : "no", (a.comment || "").replace(/[\r\n]+/g, " ")]); });
  const csv = rows.map(r => r.map(x => '"' + String(x).replace(/"/g, '""') + '"').join(",")).join("\r\n");
  const b = new Blob(["\ufeff" + csv], {type: "text/csv;charset=utf-8"});
  const u = URL.createObjectURL(b); const l = document.createElement("a");
  l.href = u; l.download = "c5_review_answers.csv"; document.body.appendChild(l); l.click(); l.remove();
}
window.onload = () => {
  el("classes").innerHTML = CLASSES.map(c => `<label><input type=radio name=cls value="${c}"> ${c}</label>`).join("<br>");
  show();
};
"""


def page(clips):
    body = """<!DOCTYPE html><html lang="vi"><head><meta charset="utf-8"><title>Đánh giá clip EEG</title>
<style>body{font-family:Segoe UI,Arial,sans-serif;margin:16px;max-width:1550px}img{width:100%;border:1px solid #ccc}
.form{display:flex;gap:40px;margin:12px 0}.box{border:1px solid #ccc;padding:10px;border-radius:6px}
button{font-size:15px;padding:6px 14px;margin-right:8px}#hdr{font-size:20px;font-weight:600}#note{color:#555}</style>
</head><body>
<p><b>Hướng dẫn.</b> Mỗi clip là 60 giây EEG, 18 đạo trình lưỡng cực (montage dọc), đơn vị µV, đã lọc 0,5–60 Hz và
lọc nhiễu điện lưới. Không có điểm số hay đánh dấu nào của hệ thống. Bác sĩ chọn một loại, độ tin cậy và trả lời câu hỏi
thứ ba; có thể giảm độ khuếch đại; có thể quay lại clip trước. Kết quả được lưu trong trình duyệt và tải về bằng nút
cuối trang.</p>
<div id=hdr></div><div id=note></div>
<img id=p1><img id=p2>
<div class=form><div class=box><b>1. Loại</b><br><div id=classes></div></div>
<div class=box><b>2. Độ tin cậy</b><br>""" + " ".join(
        f'<label><input type=radio name=conf value="{k}"> {k}</label>' for k in range(1, 6)) + """
<br><small>1 = rất không chắc … 5 = chắc chắn</small><br><br>
<b>3. Bác sĩ có muốn hệ thống cho xem đoạn này khi đọc bản ghi không?</b><br>
<label><input type=radio name=show value=yes> Có</label> <label><input type=radio name=show value=no> Không</label>
<label><input type=radio name=show value=unsure> Không chắc</label><br><br>
<b>Ghi chú</b><br><textarea id=cmt rows=4 cols=50></textarea></div></div>
<button onclick="next(-1)">◀ Clip trước</button><button onclick="toggleGain()" id=gainbtn></button>
<button onclick="next(1)">Lưu và clip tiếp ▶</button><span id=status></span>
<hr><button onclick="download()">Tải kết quả (CSV)</button>
<script>""" + FORM_JS.replace("__CLIPS__", json.dumps(clips, ensure_ascii=False)) + "</script></body></html>"
    return body


def b64(p):
    return "data:image/png;base64," + base64.b64encode(Path(p).read_bytes()).decode()


# ════════════════════════════════════════════════════════════════════ main
def main(argv=None):
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--chb", required=True)
    ap.add_argument("--siena", required=True)
    ap.add_argument("--db", default=str(BACKEND / "szscan.db"))
    ap.add_argument("--uploads", default=str(BACKEND / "uploads"))
    ap.add_argument("--out", default=str(DEFAULT_OUT))
    ap.add_argument("--version", type=int, choices=[24, 18], default=24)
    ap.add_argument("--seed", type=int, default=SEED)
    a = ap.parse_args(argv)
    out = Path(a.out)
    if out.exists() and any(out.iterdir()):
        raise SystemExit(f"STOP: {out} is not empty (a selection exists; the rule runs once)")
    import c5_score_app as SA
    subs, files, ev = db_read(a.db)
    evs = {}
    for e in ev:
        evs.setdefault(e["file_id"], []).append(e)
    rng = np.random.default_rng(a.seed)
    v = VERSIONS[a.version]
    hosp = [Rec(f, subs[f["subject_id"]], a.uploads) for f in files
            if subs[f["subject_id"]]["private"] and subs[f["subject_id"]]["mode"] == "session"]
    if not hosp:
        raise SystemExit("STOP: no private session-mode study in the database")
    hclips, hinfo = hospital(hosp, evs, v, rng)
    pub = {}
    for f in files:
        s = subs[f["subject_id"]]
        sid = f["subject_id"]
        if s["private"] or s["mode"] != "session" or not (sid in TEST or re.fullmatch(r"PN\d\d", sid)):
            continue
        pub.setdefault(sid, []).append(Rec(f, s, a.uploads))
    cache = {}

    def ann_of(sid):
        if sid not in cache:
            ann = SA.annotations(sid, a.chb, a.siena)
            cache[sid] = ann
        return cache[sid]
    aclips, ainfo = anchors(anchor_candidates(pub, evs, ann_of), v)
    clips = [dict(c, source="hospital", dataset="hospital") for c in hclips] + [dict(c, source="anchor") for c in aclips]
    order = rng.permutation(len(clips)).tolist()
    clips = [clips[k] for k in order]
    (out / "clips").mkdir(parents=True)
    keyrows, page_clips = [], []
    for k, c in enumerate(clips):
        cid = f"C{k + 1:02d}"
        r = c["rec"]
        sig = c["rec"].signal(c["start"])
        note = (f"Lọc 0,5–60 Hz, notch {r.mains:.0f} Hz"
                + (" · C3 được nội suy (điện cực hỏng)" if r.interp and c["source"] == "hospital" else ""))
        img = {}
        for g, sp in (("std", 150.0), ("half", 300.0)):
            img[g] = [b64(p) for p in render(sig, out / "clips" / f"{cid}_{g}", sp, f"Clip {cid}   {note}")]
        page_clips.append(dict(id=cid, note=note, img=img))
        keyrows.append(dict(clip=cid, source=c["source"], set=c["set"], dataset=c["dataset"], study=r.sid,
                            file=r.fn, clip_start_s=round(c["start"], 2),
                            event_or_seizure_onset_s="" if c["on"] is None else round(c["on"], 2),
                            event_or_seizure_offset_s="" if c["off"] is None else round(c["off"], 2),
                            peak_score=round(c["peak"], 4), mains_hz=r.mains, interpolated=r.interp))
    (out / "review.html").write_text(page(page_clips), encoding="utf-8")
    with open(out / "key.csv", "w", newline="", encoding="utf-8") as fh:
        w = csv.DictWriter(fh, fieldnames=list(keyrows[0]))
        w.writeheader()
        w.writerows(keyrows)
    sel = dict(protocol="results/c5_szscan/step3/PROTOCOL_STEP3.md", version=a.version, seed=a.seed,
               clips=len(clips), hospital=hinfo, anchors=ainfo)
    (out / "selection.json").write_text(json.dumps(sel, indent=1), encoding="utf-8")
    print(f"{len(clips)} clips: hospital {len(hclips)} ({hinfo['top']} highest, {hinfo['random']} random, "
          f"{hinfo['controls']} controls), anchors {len(aclips)}; review page and key in the private folder")
    return sel


if __name__ == "__main__":
    main()
