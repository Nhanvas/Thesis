#!/usr/bin/env python3
"""
project_inventory.py — Multi-mode project audit scanner (v2)

Ba che do, chay tach roi de output khong bao gio qua lon cho mot lan doc:

  1) overview  — Quet TOAN BO cay thu muc tu goc, KHONG gioi han do sau.
                 Voi moi thu muc: danh sach con truc tiep (folder + file),
                 kem thoi gian tao/sua doi (mtime; ca ctime neu co tren OS).
                 Day la ban do tong the cua repo — chay dau tien.

  2) deep      — Quet sau MOT folder lon (vd ./src, ./results, ./docs).
                 Liet ke MOI file voi size/mtime, VA dump toan bo NOI DUNG
                 cho cac file text nho (.py/.md/.csv/.json/...) de doc lai
                 truc tiep trong file .md xuat ra — khong chi "peek" vai dong.
                 File nhi phan / qua lon chi liet ke metadata.

  3) audit     — Quet TOAN BO repo (kha nang nang, chay rieng):
                   (a) DUPLICATE NAME DETECTION: file trung ten o nhieu noi
                       khac nhau -> hash noi dung -> bao "GIONG HET" hay
                       "KHAC NHAU" giua cac ban, kem size/mtime/duong dan.
                   (b) STALE NUMBER GREP: quet noi dung file text tim cac
                       con so/pattern DA BIET la cu (vd "0.750", "0.829",
                       "39.77", "mag60/pen1.0", ten file CSV pre-rebuild...)
                       -> bao vi tri xuat hien de ra soat thay the.
                 Danh sach pattern cu nam trong STALE_PATTERNS ben duoi —
                 SUA/BO SUNG truoc khi chay cho khop voi RESULTS_OF_RECORD.md
                 hien tai cua ban.

ALL output ghi ra file trong audit folder (mac dinh _project_audit/) —
khong in tran noi dung lon ra terminal.

USAGE
-----
  # Buoc 1 — luon chay truoc, tu goc repo
  python project_inventory.py overview --root .

  # Buoc 2 — mo _project_audit/00_overview.md xem tong quan cay thu muc,
  # roi quet sau tung folder lon (co the sua danh sach trong NEXT_STEPS.md)
  python project_inventory.py deep --root ./src
  python project_inventory.py deep --root ./docs
  python project_inventory.py deep --root ./results
  python project_inventory.py deep --root ./data --no-content   # qua nhieu .npy, bo qua dump noi dung

  # Buoc 3 — audit toan repo: trung ten + so lieu loi thoi
  python project_inventory.py audit --root .

Tat ca lenh nhan --audit-dir de doi noi ghi output (mac dinh _project_audit,
tao ngay canh noi ban chay script).
"""

import argparse
import csv
import hashlib
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".idea",
    ".vscode", ".ipynb_checkpoints", ".pytest_cache", ".mypy_cache",
}

# Duoi file duoc coi la "text" -> co the dump full noi dung trong che do deep,
# va duoc quet trong che do audit (duplicate hash + stale-number grep).
TEXT_EXTS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".ini",
    ".sh", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".toml", ".csv",
}

SUSPECT_PATTERNS = [
    "old", "backup", "bak", "tmp", "temp", "scratch", "test_", "_test",
    "copy", "draft", "unused", "deprecated", "superseded", "wip",
    "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9",
]

# Gioi han an toan de khong dump file text khong lo (vd CSV hang chuc MB)
# vao markdown. File lon hon nguong nay van duoc liet ke (size/mtime/hash)
# nhung KHONG dump noi dung; deep se ghi ro "content skipped (too large)".
DEFAULT_MAX_CONTENT_BYTES = 300_000  # ~300KB

# ---------------------------------------------------------------------------
# STALE NUMBER PATTERNS — SUA/BO SUNG cho khop RESULTS_OF_RECORD.md hien tai.
# Moi tuple: (nhan hien thi, list cac chuoi can tim - substring match, khong
# phan biet hoa/thuong doi voi phan chu). Dung cho che do `audit`.
# ---------------------------------------------------------------------------
STALE_PATTERNS = [
    ("pre-rebuild balanced sensitivity 0.750", ["0.750", "0.7500"]),
    ("pre-rebuild high-sens sensitivity 0.829", ["0.829", "0.8289"]),
    ("pre-rebuild balanced FP/day 39.77", ["39.77"]),
    ("pre-rebuild high-sens FP/day 71.25", ["71.25"]),
    ("pre-rebuild window macro AUROC 0.791/0.796", ["0.791", "0.796"]),
    ("old ensemble weight 0.40/0.35/0.25", ["0.40, 0.35, 0.25", "0.40,0.35,0.25",
                                             "(0.40, 0.35", "0.4,0.35,0.25"]),
    ("older ensemble weight 0.35/0.30/0.35", ["0.35, 0.30, 0.35", "0.35,0.30,0.35"]),
    ("pre-rebuild operating point mag60/pen1.0 balanced", ["mag60/pen1.0", "mag60_pen1.0"]),
    ("pre-rebuild operating point mag50/pen0.5 high-sens", ["mag50/pen0.5", "mag50_pen0.5"]),
    ("superseded high-sens mag50/pen1.0 (Decision #16)", ["mag50/pen1.0"]),
    ("superseded high-sens mag70/pen0.3 (original)", ["mag70/pen0.3", "0.816"]),
    ("stale chb06 balanced 2/10 (should be 3/10 pre-rebuild, or current §0 value)",
     ["chb06 2/10", "chb06: 2/10"]),
    ("old Yildiz baseline 0.76 (correct is 0.68 pre-rebuild / 0.61 rebuild)", ["0.76"]),
    ("current §0 balanced sensitivity 0.632 (sanity: should appear in current docs)",
     ["0.632"]),
    ("current §0 high-sens sensitivity 0.776 (sanity check)", ["0.776"]),
]


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def fmt_ts(ts: float) -> str:
    return datetime.fromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")


def iter_files(root: Path, skip_path: Path = None):
    """Recursive walk, skipping EXCLUDE_DIRS and (if given) skip_path."""
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [
            d for d in sorted(dirnames)
            if d not in EXCLUDE_DIRS and (skip_path is None or (dp / d).resolve() != skip_path)
        ]
        for fname in sorted(filenames):
            fpath = Path(dirpath) / fname
            try:
                stat = fpath.stat()
            except OSError:
                continue
            yield fpath, stat


def file_created_str(stat) -> str:
    """Best-effort 'created' time. On Linux ext4 st_birthtime is often
    unavailable; fall back to ctime (metadata-change time) and label it
    clearly so it isn't mistaken for a true creation timestamp."""
    birth = getattr(stat, "st_birthtime", None)
    if birth:
        return fmt_ts(birth) + " (birth)"
    return fmt_ts(stat.st_ctime) + " (ctime*)"


# ===========================================================================
# MODE 1 — OVERVIEW: full-depth tree, every folder shows its direct children
# ===========================================================================
def write_overview(root: Path, audit_dir: Path, include_data_detail: bool):
    lines = []
    lines.append(f"# Project Overview (FULL DEPTH) — `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\nMoi thu muc duoc liet ke voi CON TRUC TIEP ben trong no (folder truoc, "
                  "file sau), kem kich thuoc va thoi gian sua doi (mtime) / metadata-change "
                  "(ctime*, xap xi 'created' tren Linux). Thu tu duyet = pre-order (thu muc "
                  "cha in ra truoc, roi lan luot vao tung thu muc con).")

    total_files = 0
    total_size = 0
    all_mtimes = []

    def walk(d: Path, depth: int):
        nonlocal total_files, total_size
        try:
            entries = list(os.scandir(d))
        except OSError as e:
            lines.append(f"\n{'  ' * depth}> [KHONG DOC DUOC: {e}]")
            return
        dirs = sorted([e for e in entries if e.is_dir() and e.name not in EXCLUDE_DIRS
                       and Path(e.path).resolve() != audit_dir],
                      key=lambda e: e.name.lower())
        files = sorted([e for e in entries if e.is_file()], key=lambda e: e.name.lower())

        indent = "  " * depth
        header = f"{indent}- **{d.name}/**" if depth > 0 else f"**{d.name}/** (ROOT)"
        lines.append(f"\n{header}")
        if not dirs and not files:
            lines.append(f"{indent}  _(rong)_")

        if dirs:
            lines.append(f"{indent}  Thu muc con truc tiep: "
                          + ", ".join(f"`{e.name}/`" for e in dirs))
        if files:
            lines.append(f"{indent}  | File | Size | Modified (mtime) | Created* |")
            lines.append(f"{indent}  |---|---|---|---|")
            for e in files:
                try:
                    st = e.stat()
                except OSError:
                    continue
                total_files += 1
                total_size += st.st_size
                all_mtimes.append(st.st_mtime)
                lines.append(f"{indent}  | {e.name} | {human_size(st.st_size)} | "
                              f"{fmt_ts(st.st_mtime)} | {file_created_str(st)} |")

        for e in dirs:
            p = Path(e.path)
            if p.name == "data" and not include_data_detail:
                # summarize instead of recursing file-by-file
                agg_files, agg_size, agg_old, agg_new = _aggregate(p, audit_dir)
                lines.append(f"\n{indent}  - **{e.name}/** _(TOM TAT — xem --include-data-detail "
                              f"de liet ke tung file)_")
                lines.append(f"{indent}    Files (de quy): {agg_files} | Dung luong: "
                              f"{human_size(agg_size)} | Cu nhat: "
                              f"{agg_old.strftime('%Y-%m-%d') if agg_old else '-'} | Moi nhat: "
                              f"{agg_new.strftime('%Y-%m-%d') if agg_new else '-'}")
                total_files += agg_files
                total_size += agg_size
                continue
            walk(p, depth + 1)

    walk(root, 0)

    header_lines = []
    header_lines.append(f"# Project Overview (FULL DEPTH) — `{root}`")
    header_lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    header_lines.append(f"\nTong so file (de quy, toan repo): **{total_files}**  |  "
                         f"Tong dung luong: **{human_size(total_size)}**")
    if all_mtimes:
        header_lines.append(f"File cu nhat (mtime): {fmt_ts(min(all_mtimes))}  |  "
                             f"File moi nhat (mtime): {fmt_ts(max(all_mtimes))}")
    header_lines.append("\n---")

    out_path = audit_dir / "00_overview.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(header_lines) + "\n" + "\n".join(lines[2:]))
        # lines[0:2] duplicate header info already in header_lines; skip them
    return out_path, total_files, total_size


def _aggregate(root: Path, skip_path: Path):
    files = 0
    size = 0
    oldest = newest = None
    for _fpath, stat in iter_files(root, skip_path=skip_path):
        files += 1
        size += stat.st_size
        mt = datetime.fromtimestamp(stat.st_mtime)
        if oldest is None or mt < oldest:
            oldest = mt
        if newest is None or mt > newest:
            newest = mt
    return files, size, oldest, newest


def write_next_steps(root: Path, audit_dir: Path):
    top_dirs = []
    try:
        for entry in os.scandir(root):
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
                p = Path(entry.path)
                if p.resolve() == audit_dir:
                    continue
                files, size, _o, _n = _aggregate(p, audit_dir)
                top_dirs.append((p, files, size))
    except OSError:
        pass
    top_dirs.sort(key=lambda t: -t[2])

    lines = []
    lines.append("# Next steps — cac lenh de chay tiep (lon -> nho)")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\n1. Mo `00_overview.md` de xem toan bo cay thu muc + mtime/created.")
    lines.append("2. Chay tung lenh `deep` ben duoi de xem NOI DUNG DAY DU cua file trong "
                  "tung folder lon (ghi ra `deep_<ten>.md` + `.csv`).")
    lines.append("3. Chay lenh `audit` (o cuoi) MOT LAN cho toan repo de tim file trung ten "
                  "va so lieu loi thoi.\n")
    lines.append("| # | Folder | Files (de quy) | Dung luong | Lenh de chay |")
    lines.append("|---|---|---|---|---|")
    for i, (p, files, size) in enumerate(top_dirs, 1):
        big = size > 200 * 1024 * 1024
        content_flag = " --no-content" if big else ""
        cmd = f'python project_inventory.py deep --root "{p}"{content_flag}'
        lines.append(f"| {i:02d} | {p.name} | {files} | {human_size(size)} | `{cmd}` |")

    lines.append("\n## File nam truc tiep o goc repo")
    try:
        root_files = [f for f in os.scandir(root) if f.is_file()]
    except OSError:
        root_files = []
    if root_files:
        lines.append("\n| File | Size | Modified |")
        lines.append("|---|---|---|")
        for f in sorted(root_files, key=lambda e: e.name.lower()):
            st = f.stat()
            lines.append(f"| {f.name} | {human_size(st.st_size)} | {fmt_ts(st.st_mtime)} |")
    else:
        lines.append("\n_(khong co)_")

    lines.append("\n## Lenh audit toan repo (chay rieng, sau khi da xem overview)")
    lines.append(f'\n```\npython project_inventory.py audit --root "{root}"\n```')

    out_path = audit_dir / "NEXT_STEPS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


# ===========================================================================
# MODE 2 — DEEP: full recursive scan of ONE folder, WITH file content dump
# ===========================================================================
def deep_scan(root: Path, dump_content: bool, skip_path: Path,
              max_content_bytes: int):
    rows = []
    for fpath, stat in iter_files(root, skip_path=skip_path):
        rel = fpath.relative_to(root)
        size = stat.st_size
        ext = fpath.suffix.lower()
        lower_name = fpath.name.lower()
        flags = [p for p in SUSPECT_PATTERNS if p in lower_name]

        content = None
        content_status = "not-text-ext"
        if dump_content and ext in TEXT_EXTS:
            if size > max_content_bytes:
                content_status = f"skipped (too large: {human_size(size)} > {human_size(max_content_bytes)})"
            else:
                try:
                    with open(fpath, "r", encoding="utf-8", errors="replace") as fh:
                        content = fh.read()
                    content_status = "ok"
                except Exception as e:
                    content_status = f"unreadable ({e})"

        rows.append({
            "path": str(rel).replace("\\", "/"),
            "folder": str(rel.parent).replace("\\", "/"),
            "name": fpath.name,
            "ext": ext,
            "size_bytes": size,
            "size_human": human_size(size),
            "mtime": fmt_ts(stat.st_mtime),
            "created": file_created_str(stat),
            "flags": ",".join(flags),
            "content_status": content_status,
            "content": content,
        })
    return rows


def write_deep_csv(rows, out_path: Path):
    fieldnames = ["path", "folder", "name", "ext", "size_bytes", "size_human",
                  "mtime", "created", "flags", "content_status"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow({k: r[k] for k in fieldnames})


def write_deep_markdown(rows, out_path: Path, root: Path, dump_content: bool):
    by_folder = defaultdict(list)
    for r in rows:
        by_folder[r["folder"]].append(r)

    total_size = sum(r["size_bytes"] for r in rows)
    lines = []
    lines.append(f"# Deep scan — `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nTotal files: **{len(rows)}**  |  Total size: **{human_size(total_size)}**")
    lines.append(f"Content dump: **{'ON' if dump_content else 'OFF (metadata only)'}**")

    lines.append("\n## Flagged files (ten goi y cu/backup/test/draft/version)\n")
    flagged = [r for r in rows if r["flags"]]
    if flagged:
        lines.append("| Path | Size | Modified | Flags |")
        lines.append("|---|---|---|---|")
        for r in sorted(flagged, key=lambda r: r["path"]):
            lines.append(f"| {r['path']} | {r['size_human']} | {r['mtime']} | {r['flags']} |")
    else:
        lines.append("_(khong co)_")

    lines.append("\n## Muc luc theo sub-folder\n")
    for folder in sorted(by_folder):
        label = folder if folder != "." else "(truc tiep trong folder nay)"
        lines.append(f"- [{label}](#{'folder-' + folder.replace('/', '-').replace('.', '').lower() or 'folder-root'})")

    lines.append("\n## Chi tiet + noi dung day du theo sub-folder\n")
    for folder in sorted(by_folder):
        label = folder if folder != "." else "(truc tiep trong folder nay)"
        anchor = 'folder-' + folder.replace('/', '-').replace('.', '').lower() or 'folder-root'
        lines.append(f"\n<a id=\"{anchor}\"></a>\n### {label}\n")
        lines.append("| File | Size | Modified | Created* | Status |")
        lines.append("|---|---|---|---|---|")
        for r in sorted(by_folder[folder], key=lambda r: r["path"]):
            lines.append(f"| {r['name']} | {r['size_human']} | {r['mtime']} | "
                          f"{r['created']} | {r['content_status']} |")

        if dump_content:
            for r in sorted(by_folder[folder], key=lambda r: r["path"]):
                if r["content"] is None:
                    continue
                lang = {"py": "python", "md": "markdown", "json": "json",
                        "yaml": "yaml", "yml": "yaml", "csv": "text",
                        "sh": "bash", "js": "javascript", "ts": "typescript"}.get(
                    r["ext"].lstrip("."), "")
                lines.append(f"\n#### `{r['path']}`\n")
                lines.append(f"```{lang}")
                lines.append(r["content"])
                lines.append("```")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ===========================================================================
# MODE 3 — AUDIT: whole-repo duplicate-name detection + stale-number grep
# ===========================================================================
def hash_file(fpath: Path, block_size=65536):
    h = hashlib.sha256()
    try:
        with open(fpath, "rb") as f:
            while True:
                chunk = f.read(block_size)
                if not chunk:
                    break
                h.update(chunk)
        return h.hexdigest()
    except OSError:
        return None


def find_duplicate_names(root: Path, skip_path: Path):
    by_name = defaultdict(list)
    for fpath, stat in iter_files(root, skip_path=skip_path):
        by_name[fpath.name].append((fpath, stat))
    dupes = {name: items for name, items in by_name.items() if len(items) > 1}
    return dupes


def write_duplicates_report(dupes, root: Path, out_path: Path, hash_max_bytes: int):
    lines = []
    lines.append(f"# Duplicate filenames across `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nSo ten file bi trung (xuat hien >=2 noi khac nhau): **{len(dupes)}**")
    lines.append(f"\nHash SHA256 duoc tinh cho file <= {human_size(hash_max_bytes)}; "
                  "file lon hon chi so sanh theo (size, mtime) va duoc ghi chu ro.")
    lines.append("\nNhom co cac ban **KHAC NHAU ve noi dung** duoc danh dau "
                  "**[!] KHAC NOI DUNG** — day la nhung cai can ra soat truoc tien "
                  "(co the mot ban la ban cu/loi thoi).\n")

    # sort: groups with content differences first, then by name
    def has_diff(items):
        hashes = set()
        for fpath, stat in items:
            if stat.st_size <= hash_max_bytes:
                hh = hash_file(fpath)
                hashes.add(hh)
            else:
                hashes.add(f"__toolarge__{stat.st_size}")
        return len(hashes) > 1

    groups = []
    for name, items in dupes.items():
        diff = has_diff(items)
        groups.append((diff, name, items))
    groups.sort(key=lambda g: (not g[0], g[1].lower()))

    n_diff = sum(1 for g in groups if g[0])
    lines.append(f"So nhom co noi dung KHAC NHAU giua cac ban: **{n_diff}** / {len(groups)}\n")

    for diff, name, items in groups:
        tag = "**[!] KHAC NOI DUNG**" if diff else "(giong het nhau)"
        lines.append(f"\n### `{name}` — {len(items)} ban — {tag}\n")
        lines.append("| Duong dan | Size | Modified | SHA256 (8 ky tu dau) |")
        lines.append("|---|---|---|---|")
        for fpath, stat in sorted(items, key=lambda t: t[1].st_mtime):
            rel = fpath.relative_to(root)
            if stat.st_size <= hash_max_bytes:
                hh = hash_file(fpath)
                hshort = hh[:8] if hh else "ERROR"
            else:
                hshort = "(qua lon, bo qua hash)"
            lines.append(f"| {rel} | {human_size(stat.st_size)} | {fmt_ts(stat.st_mtime)} | {hshort} |")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return n_diff, len(groups)


def grep_stale_patterns(root: Path, skip_path: Path, patterns, max_bytes=2_000_000):
    """Returns {label: [(path, line_no, line_text), ...]}"""
    hits = defaultdict(list)
    for fpath, stat in iter_files(root, skip_path=skip_path):
        if fpath.suffix.lower() not in TEXT_EXTS:
            continue
        if stat.st_size > max_bytes:
            continue
        try:
            with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                for lineno, line in enumerate(f, 1):
                    for label, needles in patterns:
                        for needle in needles:
                            if needle in line:
                                rel = fpath.relative_to(root)
                                hits[label].append(
                                    (str(rel).replace("\\", "/"), lineno, line.strip()[:200]))
                                break
        except Exception:
            continue
    return hits


def write_stale_report(hits, root: Path, out_path: Path, patterns):
    lines = []
    lines.append(f"# Stale-number / superseded-pattern scan — `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\nDanh sach pattern dang tim (SUA trong STALE_PATTERNS o dau script neu can):\n")
    for label, needles in patterns:
        lines.append(f"- **{label}**: {needles}")
    total_hits = sum(len(v) for v in hits.values())
    lines.append(f"\nTong so dong khop: **{total_hits}**\n")

    for label, needles in patterns:
        matches = hits.get(label, [])
        lines.append(f"\n## {label}  ({len(matches)} dong)\n")
        if not matches:
            lines.append("_(khong tim thay)_")
            continue
        lines.append("| File | Dong | Noi dung |")
        lines.append("|---|---|---|")
        for path, lineno, text in matches:
            text_esc = text.replace("|", "\\|")
            lines.append(f"| {path} | {lineno} | {text_esc} |")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Multi-mode project audit scanner (v2)")
    ap.add_argument("--audit-dir", default="_project_audit",
                     help="Thu muc luu tat ca ket qua audit (tu tao neu chua co)")
    sub = ap.add_subparsers(dest="mode", required=True)

    p_over = sub.add_parser("overview", help="Pass 1: toan bo cay thu muc, khong gioi han do sau")
    p_over.add_argument("--root", default=".", help="Thu muc goc can quet")
    p_over.add_argument("--include-data-detail", action="store_true",
                         help="Liet ke tung file trong data/ thay vi chi tom tat (co the RAT dai)")

    p_deep = sub.add_parser("deep", help="Pass 2: quet sau 1 folder, dump noi dung file text")
    p_deep.add_argument("--root", required=True, help="Folder can quet sau (vd ./src)")
    p_deep.add_argument("--no-content", action="store_true",
                         help="Chi liet ke metadata, KHONG dump noi dung file (dung cho data/, results/ nhieu file lon)")
    p_deep.add_argument("--max-content-bytes", type=int, default=DEFAULT_MAX_CONTENT_BYTES,
                         help=f"Gioi han kich thuoc file de dump full noi dung (mac dinh {DEFAULT_MAX_CONTENT_BYTES})")

    p_audit = sub.add_parser("audit", help="Pass 3: toan repo — file trung ten + so lieu loi thoi")
    p_audit.add_argument("--root", default=".", help="Thu muc goc can quet")
    p_audit.add_argument("--hash-max-bytes", type=int, default=50_000_000,
                          help="Gioi han kich thuoc file de tinh hash so sanh trung lap (mac dinh 50MB)")
    p_audit.add_argument("--grep-max-bytes", type=int, default=2_000_000,
                          help="Gioi han kich thuoc file de quet pattern (mac dinh 2MB)")

    args = ap.parse_args()
    audit_dir = Path(args.audit_dir).resolve()
    audit_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "overview":
        root = Path(args.root).resolve()
        if not root.exists():
            raise SystemExit(f"Khong tim thay thu muc: {root}")
        overview_path, n_files, total_size = write_overview(
            root, audit_dir, include_data_detail=args.include_data_detail)
        next_steps_path = write_next_steps(root, audit_dir)
        print(f"[overview] Da quet: {root}  ({n_files} files, {human_size(total_size)})")
        print(f"[overview] Ghi: {overview_path}")
        print(f"[overview] Ghi: {next_steps_path}")
        print(f"\nMo {overview_path.name} de xem toan bo cay thu muc, roi lam theo "
              f"{next_steps_path.name} de chay tiep 'deep' cho tung folder va 'audit' cho toan repo.")

    elif args.mode == "deep":
        root = Path(args.root).resolve()
        if not root.exists():
            raise SystemExit(f"Khong tim thay thu muc: {root}")
        dump_content = not args.no_content
        rows = deep_scan(root, dump_content=dump_content, skip_path=audit_dir,
                          max_content_bytes=args.max_content_bytes)
        safe_name = root.name.replace(" ", "_") or "root"
        csv_path = audit_dir / f"deep_{safe_name}.csv"
        md_path = audit_dir / f"deep_{safe_name}.md"
        write_deep_csv(rows, csv_path)
        write_deep_markdown(rows, md_path, root, dump_content=dump_content)
        print(f"[deep] Da quet {len(rows)} file trong: {root}")
        print(f"[deep] Ghi: {csv_path}")
        print(f"[deep] Ghi: {md_path}  (content dump: {'ON' if dump_content else 'OFF'})")

    elif args.mode == "audit":
        root = Path(args.root).resolve()
        if not root.exists():
            raise SystemExit(f"Khong tim thay thu muc: {root}")

        print(f"[audit] Dang tim file trung ten duoi: {root} ...")
        dupes = find_duplicate_names(root, skip_path=audit_dir)
        dup_path = audit_dir / "audit_duplicate_names.md"
        n_diff, n_groups = write_duplicates_report(dupes, root, dup_path, args.hash_max_bytes)
        print(f"[audit] Ghi: {dup_path}  ({n_groups} nhom trung ten, {n_diff} nhom KHAC NOI DUNG)")

        print(f"[audit] Dang grep {len(STALE_PATTERNS)} pattern so lieu cu ...")
        hits = grep_stale_patterns(root, skip_path=audit_dir, patterns=STALE_PATTERNS,
                                    max_bytes=args.grep_max_bytes)
        stale_path = audit_dir / "audit_stale_numbers.md"
        write_stale_report(hits, root, stale_path, STALE_PATTERNS)
        total_hits = sum(len(v) for v in hits.values())
        print(f"[audit] Ghi: {stale_path}  ({total_hits} dong khop)")


if __name__ == "__main__":
    main()