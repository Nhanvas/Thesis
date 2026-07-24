import glob, os
SUBJ = "chb03"   # một test subject là đủ — naming đồng nhất across subjects
roots = ["data/processed", "results/cpd/scores", "results/cpd", "."]
seen, hits = set(), []
for r in roots:
    for p in glob.glob(os.path.join(r, "**", f"*{SUBJ}*.npy"), recursive=True):
        rp = os.path.relpath(p)
        if rp not in seen:
            seen.add(rp); hits.append(rp)
for h in sorted(hits):
    print(h)
print(f"\n[{len(hits)} files matching {SUBJ}]")