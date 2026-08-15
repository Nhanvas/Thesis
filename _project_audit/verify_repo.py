"""
verify_repo.py — one-shot VERIFY dump for REPO_MAP §I. Chay tu REPO ROOT (F:/Study/Thesis/Code).

Muc dich: gom moi thong tin de chan doan KEEP/ARCHIVE/DELETE ma khong phai upload tung file.
  - File TEXT (.csv/.json/.md/.txt/.py): dump noi dung (cap dong).
  - File BINARY (.pt/.npy): size + sha256 (de so trung noi dung, KHONG dump).
  - File ANH (.png/.jpg...): chi dem + liet ke ten (khong dump, khong hash tung cai).
  - Cuoi file: "DUPLICATE HASH GROUPS" — gom moi file da quet theo sha256 =>
    file trung NOI DUNG (khac folder) hien ro => biet cai nao DELETE duoc.

Chay:
    python _project_audit/verify_repo.py
    # hoac chi dinh root khac: python _project_audit/verify_repo.py --root F:/Study/Thesis/Code
Output: _project_audit/verify_report.md
"""
import argparse
import hashlib
from datetime import datetime
from pathlib import Path

TEXT_EXTS = {".csv", ".json", ".md", ".txt", ".py", ".cfg", ".yaml", ".yml"}
IMG_EXTS = {".png", ".jpg", ".jpeg", ".gif", ".webp", ".bmp"}
BIN_EXTS = {".pt", ".npy", ".npz", ".pth", ".pkl", ".zip", ".edf"}

MAX_LINES = 200         # noi len de doc tron thesis_repro_lock.py + CSV
MAX_BYTES = 30000

# --- Muc can VERIFY (REPO_MAP §I). Them/bot path o day neu can. ---
TARGET_DIRS = [
    "results/attribution",
]
TARGET_FILES = [
    "src/thesis_repro_lock.py",
]


def human(n):
    for u in ("B", "KB", "MB", "GB"):
        if n < 1024:
            return f"{n:.1f}{u}"
        n /= 1024
    return f"{n:.1f}TB"


def sha256(path, block=1 << 20):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            b = f.read(block)
            if not b:
                break
            h.update(b)
    return h.hexdigest()


def classify(ext):
    e = ext.lower()
    if e in TEXT_EXTS:
        return "text"
    if e in IMG_EXTS:
        return "image"
    if e in BIN_EXTS:
        return "binary"
    return "other"


def dump_text(path):
    try:
        raw = Path(path).read_text(encoding="utf-8", errors="replace")
    except Exception as e:
        return f"[unreadable: {e}]", False
    lines = raw.splitlines()
    truncated = False
    if len(lines) > MAX_LINES:
        lines = lines[:MAX_LINES]
        truncated = True
    body = "\n".join(lines)
    if len(body) > MAX_BYTES:
        body = body[:MAX_BYTES]
        truncated = True
    return body, truncated


def scan_dir(root, rel, out, hash_index):
    d = root / rel
    out.append(f"\n## DIR `{rel}`")
    if not d.exists():
        out.append("_(khong ton tai)_")
        return
    files = sorted([p for p in d.rglob("*") if p.is_file()])
    if not files:
        out.append("_(rong)_")
        return
    # tom tat
    imgs = [p for p in files if classify(p.suffix) == "image"]
    others = [p for p in files if classify(p.suffix) != "image"]
    tot = sum(p.stat().st_size for p in files)
    out.append(f"**{len(files)} file, {human(tot)}** — text/bin: {len(others)}, anh: {len(imgs)}")

    if imgs:
        names = ", ".join(sorted({p.name for p in imgs})[:20])
        out.append(f"\n_Anh ({len(imgs)}), khong dump. Ten mau:_ {names}{' ...' if len(imgs) > 20 else ''}")

    for p in others:
        st = p.stat()
        relp = p.relative_to(root).as_posix()
        kind = classify(p.suffix)
        mt = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
        h = sha256(p)
        hash_index.setdefault(h, []).append(relp)
        out.append(f"\n### `{relp}`  ({human(st.st_size)}, {mt}, sha `{h[:12]}`)")
        if kind == "text":
            body, tr = dump_text(p)
            out.append(f"```{p.suffix.lstrip('.')}")
            out.append(body)
            out.append("```")
            if tr:
                out.append(f"_... (cat bot; toi da {MAX_LINES} dong / {MAX_BYTES} byte)_")
        else:
            out.append(f"_(binary — chi hash/size)_")


def scan_file(root, rel, out, hash_index):
    p = root / rel
    out.append(f"\n## FILE `{rel}`")
    if not p.exists():
        out.append("_(khong ton tai)_")
        return
    st = p.stat()
    h = sha256(p)
    hash_index.setdefault(h, []).append(rel)
    mt = datetime.fromtimestamp(st.st_mtime).strftime("%Y-%m-%d %H:%M")
    out.append(f"{human(st.st_size)}, {mt}, sha256 `{h}`")
    if classify(p.suffix) == "text":
        body, tr = dump_text(p)
        out.append(f"```{p.suffix.lstrip('.')}")
        out.append(body)
        out.append("```")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--root", default=".")
    ap.add_argument("--out", default="_project_audit/verify_report.md")
    a = ap.parse_args()
    root = Path(a.root).resolve()
    out = [f"# VERIFY REPORT — {datetime.now():%Y-%m-%d %H:%M}",
           f"root = `{root}`", ""]
    hash_index = {}

    for rel in TARGET_DIRS:
        scan_dir(root, rel, out, hash_index)
    for rel in TARGET_FILES:
        scan_file(root, rel, out, hash_index)

    # duplicate hash groups (trung NOI DUNG)
    out.append("\n---\n## DUPLICATE HASH GROUPS (trung NOI DUNG y het)")
    dupes = {h: ps for h, ps in hash_index.items() if len(ps) > 1}
    if not dupes:
        out.append("_(khong co file trung noi dung trong pham vi quet)_")
    else:
        for h, ps in sorted(dupes.items(), key=lambda kv: -len(kv[1])):
            out.append(f"\n**sha `{h[:12]}`** — {len(ps)} ban giong het:")
            for p in ps:
                out.append(f"  - `{p}`")

    outp = root / a.out
    outp.parent.mkdir(parents=True, exist_ok=True)
    outp.write_text("\n".join(out), encoding="utf-8")
    print(f"[done] wrote {outp}  ({human(outp.stat().st_size)})")
    print(f"       scanned dirs={len(TARGET_DIRS)}, files={len(TARGET_FILES)}, "
          f"duplicate-content groups={len(dupes)}")


if __name__ == "__main__":
    main()