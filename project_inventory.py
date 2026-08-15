#!/usr/bin/env python3
"""
project_inventory.py — Multi-pass project inventory scanner for cleanup triage.

WHY MULTI-PASS
--------------
The project is large (many folders, large data/results). One giant recursive
scan produces output too big to review in a terminal. Use two modes instead:

  1) OVERVIEW pass — shallow, depth-limited. Shows top-level folders/files
     with AGGREGATE stats (recursive file count, total size, oldest/newest
     modified) so you see the big picture first. Also auto-generates
     NEXT_STEPS.md with ready-to-run commands for the deep pass on every
     top-level folder found, ranked largest-first.

  2) DEEP pass — full recursive scan of ONE folder at a time (every file,
     exact size, exact mtime, name-based "suspect" flags, optional content
     peek for small text files). Run once per major folder, after reviewing
     the overview.

ALL output is written to files inside an audit folder (default:
_project_audit/) — nothing large is ever printed to the terminal.

USAGE
-----
  # Step 1 — always start here (run from the project root, or pass --root)
  python project_inventory.py overview --root .

  # Step 2 — open _project_audit/00_overview.md to see the big picture,
  # then open _project_audit/NEXT_STEPS.md and run the listed commands
  # one at a time, e.g.:
  python project_inventory.py deep --root ./src --peek
  python project_inventory.py deep --root ./docs --peek
  python project_inventory.py deep --root ./data          # skip --peek: large/binary
  python project_inventory.py deep --root ./results       # skip --peek: large/binary

All commands accept --audit-dir to change where output is written
(default: _project_audit, created next to wherever you run the script).
"""

import argparse
import csv
import os
from collections import defaultdict
from datetime import datetime
from pathlib import Path

EXCLUDE_DIRS = {
    ".git", "__pycache__", "node_modules", ".venv", "venv", ".idea",
    ".vscode", ".ipynb_checkpoints", ".pytest_cache", ".mypy_cache",
}
TEXT_EXTS = {
    ".py", ".md", ".txt", ".json", ".yaml", ".yml", ".cfg", ".ini",
    ".sh", ".js", ".ts", ".tsx", ".jsx", ".html", ".css", ".toml",
}
SUSPECT_PATTERNS = [
    "old", "backup", "bak", "tmp", "temp", "scratch", "test_", "_test",
    "copy", "draft", "unused", "deprecated", "superseded", "wip",
    "v1", "v2", "v3", "v4", "v5", "v6", "v7", "v8", "v9",
]


def human_size(n: float) -> str:
    for unit in ("B", "KB", "MB", "GB", "TB"):
        if n < 1024:
            return f"{n:.1f}{unit}"
        n /= 1024
    return f"{n:.1f}PB"


def iter_files(root: Path, skip_path: Path = None):
    """Shared recursive walk, skipping EXCLUDE_DIRS and (if given) skip_path
    everywhere — used to keep the audit output folder out of its own scan,
    so re-running the tool doesn't make it grow on every pass."""
    for dirpath, dirnames, filenames in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [
            d for d in dirnames
            if d not in EXCLUDE_DIRS and (skip_path is None or (dp / d).resolve() != skip_path)
        ]
        for fname in filenames:
            fpath = Path(dirpath) / fname
            try:
                stat = fpath.stat()
            except OSError:
                continue
            yield fpath, stat


# ---------------------------------------------------------------------------
# OVERVIEW MODE
# ---------------------------------------------------------------------------
def build_dir_stats(root: Path, skip_path: Path = None):
    """Aggregate (recursive file count, total size, oldest/newest mtime) for
    EVERY directory under root (including root), plus immediate subfolder
    names for each directory."""
    stats = defaultdict(lambda: {"files": 0, "size": 0, "oldest": None, "newest": None})
    subdirs = defaultdict(set)

    for fpath, stat in iter_files(root, skip_path=skip_path):
        mtime = datetime.fromtimestamp(stat.st_mtime)
        d = fpath.parent
        while True:
            s = stats[d]
            s["files"] += 1
            s["size"] += stat.st_size
            if s["oldest"] is None or mtime < s["oldest"]:
                s["oldest"] = mtime
            if s["newest"] is None or mtime > s["newest"]:
                s["newest"] = mtime
            if d == root:
                break
            parent = d.parent
            subdirs[parent].add(d.name)
            d = parent

    # record immediate subdirs even for directories with zero direct files
    for dirpath, dirnames, _ in os.walk(root):
        dp = Path(dirpath)
        dirnames[:] = [
            x for x in dirnames
            if x not in EXCLUDE_DIRS and (skip_path is None or (dp / x).resolve() != skip_path)
        ]
        for dn in dirnames:
            subdirs[dp].add(dn)

    return stats, subdirs


def write_overview(root: Path, max_depth: int, audit_dir: Path):
    stats, subdirs = build_dir_stats(root, skip_path=audit_dir)

    def fmt_row(path: Path, depth: int, is_file=False, file_stat=None):
        indent = "&nbsp;&nbsp;" * depth
        if is_file:
            mtime = datetime.fromtimestamp(file_stat.st_mtime).strftime("%Y-%m-%d %H:%M")
            return (f"| {indent}{path.name} | file | - | {human_size(file_stat.st_size)} | "
                     f"{mtime} | {mtime} | - |")
        s = stats.get(path, {"files": 0, "size": 0, "oldest": None, "newest": None})
        oldest = s["oldest"].strftime("%Y-%m-%d") if s["oldest"] else "-"
        newest = s["newest"].strftime("%Y-%m-%d") if s["newest"] else "-"
        children = ", ".join(sorted(subdirs.get(path, []))) or "-"
        return (f"| {indent}{path.name}/ | dir | {s['files']} | {human_size(s['size'])} | "
                f"{oldest} | {newest} | {children[:80]} |")

    lines = []
    lines.append(f"# Project Overview (depth <= {max_depth}) — `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    root_stats = stats.get(root, {"files": 0, "size": 0, "oldest": None, "newest": None})
    lines.append(f"\nTong so file (toan bo, de quy): **{root_stats['files']}**  |  "
                 f"Tong dung luong: **{human_size(root_stats['size'])}**")
    if root_stats["oldest"]:
        lines.append(f"File cu nhat: {root_stats['oldest'].strftime('%Y-%m-%d %H:%M')}  |  "
                     f"File moi nhat: {root_stats['newest'].strftime('%Y-%m-%d %H:%M')}")

    lines.append("\n## Cay thu muc (gioi han do sau; xem chi tiet tung file o pass 'deep' sau)\n")
    lines.append("| Ten | Loai | Files (de quy) | Dung luong | Cu nhat | Moi nhat | Con truc tiep ben trong |")
    lines.append("|---|---|---|---|---|---|---|")

    def walk_level(d: Path, depth: int):
        if depth > max_depth:
            return
        try:
            entries = sorted(os.scandir(d), key=lambda e: e.name.lower())
        except OSError:
            return
        for entry in entries:
            p = Path(entry.path)
            if entry.is_dir():
                if entry.name in EXCLUDE_DIRS or p.resolve() == audit_dir:
                    continue
                lines.append(fmt_row(p, depth))
                walk_level(p, depth + 1)
            else:
                try:
                    st = entry.stat()
                except OSError:
                    continue
                lines.append(fmt_row(p, depth, is_file=True, file_stat=st))

    walk_level(root, 0)

    out_path = audit_dir / "00_overview.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path, stats


def write_next_steps(root: Path, stats, audit_dir: Path):
    """Rank immediate top-level folders by recursive size and emit
    ready-to-run deep-scan commands, largest first."""
    top_dirs = []
    try:
        for entry in os.scandir(root):
            if entry.is_dir() and entry.name not in EXCLUDE_DIRS:
                p = Path(entry.path)
                if p.resolve() == audit_dir:
                    continue
                s = stats.get(p, {"files": 0, "size": 0})
                top_dirs.append((p, s["files"], s["size"]))
    except OSError:
        pass
    top_dirs.sort(key=lambda t: -t[2])

    lines = []
    lines.append("# Next steps — deep-scan commands (chay lan luot, goi y tu lon den nho)")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append("\nMo `00_overview.md` truoc de xem tong quan. Sau do chay tung lenh ben duoi,")
    lines.append("moi lenh se ghi ket qua chi tiet vao 2 file rieng (`deep_<ten>.md` + `.csv`)")
    lines.append("trong cung thu muc audit nay — khong in tran ra terminal. Voi cac folder chua")
    lines.append("data/model/checkpoint nang, script da tu bo `--peek` de chay nhanh hon va tranh")
    lines.append("doc nham noi dung file nhi phan (ban van co the tu them `--peek` neu muon).\n")
    lines.append("| # | Folder | Files (de quy) | Dung luong | Lenh de chay |")
    lines.append("|---|---|---|---|---|")
    for i, (p, files, size) in enumerate(top_dirs, 1):
        big = size > 200 * 1024 * 1024  # >200MB -> suggest skipping --peek
        peek_flag = "" if big else " --peek"
        cmd = f'python project_inventory.py deep --root "{p}"{peek_flag}'
        lines.append(f"| {i:02d} | {p.name} | {files} | {human_size(size)} | `{cmd}` |")

    lines.append("\n## Cac file nam truc tiep o goc (khong thuoc folder con nao)")
    try:
        root_files = [f for f in os.scandir(root) if f.is_file()]
    except OSError:
        root_files = []
    if root_files:
        lines.append("\n| File | Size | Modified |")
        lines.append("|---|---|---|")
        for f in sorted(root_files, key=lambda e: e.name.lower()):
            st = f.stat()
            mtime = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
            lines.append(f"| {f.name} | {human_size(st.st_size)} | {mtime} |")
    else:
        lines.append("\n_(khong co file nao nam truc tiep o goc)_")

    out_path = audit_dir / "NEXT_STEPS.md"
    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))
    return out_path


# ---------------------------------------------------------------------------
# DEEP MODE (full recursive scan of ONE folder)
# ---------------------------------------------------------------------------
def deep_scan(root: Path, peek: bool, skip_path: Path = None,
              peek_lines: int = 8, peek_max_bytes: int = 200_000):
    rows = []
    for fpath, stat in iter_files(root, skip_path=skip_path):
        rel = fpath.relative_to(root)
        size = stat.st_size
        mtime = datetime.fromtimestamp(stat.st_mtime)
        ext = fpath.suffix.lower()
        lower_name = fpath.name.lower()
        flags = [p for p in SUSPECT_PATTERNS if p in lower_name]

        peek_text = ""
        if peek and ext in TEXT_EXTS and size <= peek_max_bytes:
            try:
                with open(fpath, "r", encoding="utf-8", errors="ignore") as f:
                    lines = []
                    for i, line in enumerate(f):
                        if i >= peek_lines:
                            break
                        lines.append(line.rstrip("\n"))
                    peek_text = " | ".join(lines)
            except Exception:
                peek_text = "<unreadable>"

        folder = str(rel.parent).replace("\\", "/")
        rows.append(
            {
                "path": str(rel).replace("\\", "/"),
                "folder": folder,
                "name": fpath.name,
                "ext": ext,
                "size_bytes": size,
                "size_human": human_size(size),
                "mtime": mtime.strftime("%Y-%m-%d %H:%M"),
                "flags": ",".join(flags),
                "peek": peek_text,
            }
        )
    return rows


def write_deep_csv(rows, out_path: Path):
    fieldnames = ["path", "folder", "name", "ext", "size_bytes", "size_human", "mtime", "flags", "peek"]
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fieldnames)
        w.writeheader()
        for r in rows:
            w.writerow(r)


def write_deep_markdown(rows, out_path: Path, root: Path):
    by_folder = defaultdict(list)
    for r in rows:
        by_folder[r["folder"]].append(r)

    total_size = sum(r["size_bytes"] for r in rows)
    lines = []
    lines.append(f"# Deep scan — `{root}`")
    lines.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    lines.append(f"\nTotal files: **{len(rows)}**  |  Total size: **{human_size(total_size)}**")

    lines.append("\n## Flagged files (ten goi y cu/backup/test/draft/duplicate)\n")
    flagged = [r for r in rows if r["flags"]]
    if flagged:
        lines.append("| Path | Size | Modified | Flags |")
        lines.append("|---|---|---|---|")
        for r in sorted(flagged, key=lambda r: r["path"]):
            lines.append(f"| {r['path']} | {r['size_human']} | {r['mtime']} | {r['flags']} |")
    else:
        lines.append("_(khong co)_")

    lines.append("\n## Danh sach day du theo sub-folder\n")
    for folder in sorted(by_folder):
        label = folder if folder != "." else "(truc tiep trong folder nay)"
        lines.append(f"\n### {label}\n")
        lines.append("| File | Size | Modified | Peek |")
        lines.append("|---|---|---|---|")
        for r in sorted(by_folder[folder], key=lambda r: r["path"]):
            peek = r["peek"][:150].replace("|", "\\|") if r["peek"] else ""
            lines.append(f"| {r['name']} | {r['size_human']} | {r['mtime']} | {peek} |")

    with open(out_path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines))


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="Multi-pass project inventory scanner")
    ap.add_argument("--audit-dir", default="_project_audit",
                     help="Thu muc luu tat ca ket qua audit (tu tao neu chua co)")
    sub = ap.add_subparsers(dest="mode", required=True)

    p_over = sub.add_parser("overview", help="Pass 0: tong quan, gioi han do sau")
    p_over.add_argument("--root", default=".", help="Thu muc goc can quet")
    p_over.add_argument("--max-depth", type=int, default=2,
                        help="Do sau toi da hien trong cay (mac dinh 2)")

    p_deep = sub.add_parser("deep", help="Pass sau: quet day du, cho 1 folder")
    p_deep.add_argument("--root", required=True, help="Folder can quet sau (vd ./src)")
    p_deep.add_argument("--peek", action="store_true",
                        help="Hien vai dong dau cua cac file text nho")

    args = ap.parse_args()
    audit_dir = Path(args.audit_dir).resolve()
    audit_dir.mkdir(parents=True, exist_ok=True)

    if args.mode == "overview":
        root = Path(args.root).resolve()
        if not root.exists():
            raise SystemExit(f"Khong tim thay thu muc: {root}")
        overview_path, stats = write_overview(root, args.max_depth, audit_dir)
        next_steps_path = write_next_steps(root, stats, audit_dir)
        print(f"[overview] Da quet: {root}")
        print(f"[overview] Ghi: {overview_path}")
        print(f"[overview] Ghi: {next_steps_path}")
        print(f"\nMo {overview_path.name} de xem tong quan, roi lam theo {next_steps_path.name}"
              f" de chay tiep cac pass 'deep' cho tung folder.")

    elif args.mode == "deep":
        root = Path(args.root).resolve()
        if not root.exists():
            raise SystemExit(f"Khong tim thay thu muc: {root}")
        rows = deep_scan(root, peek=args.peek, skip_path=audit_dir)
        safe_name = root.name.replace(" ", "_") or "root"
        csv_path = audit_dir / f"deep_{safe_name}.csv"
        md_path = audit_dir / f"deep_{safe_name}.md"
        write_deep_csv(rows, csv_path)
        write_deep_markdown(rows, md_path, root)
        print(f"[deep] Da quet {len(rows)} file trong: {root}")
        print(f"[deep] Ghi: {csv_path}")
        print(f"[deep] Ghi: {md_path}")


if __name__ == "__main__":
    main()
