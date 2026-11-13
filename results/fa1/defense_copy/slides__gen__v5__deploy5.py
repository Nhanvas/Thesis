import sys, os, json, importlib
sys.path.insert(0, os.path.dirname(__file__))
import render5 as render
ROOT = render.ROOT
S = render.collect(["v5_main", "v5_app"])
ORDER = [f"s{i:02d}" for i in range(1, 28)] + ["aA1", "aA2", "aB1", "aB2", "aB3", "aB4", "aC1", "aC2", "aC3", "aC4", "aC5", "aC6", "aC7",
         "aD1", "aD2", "aD3", "aD4", "aE1", "aE2", "aE3", "aE4", "aE5", "aE6", "aE7", "aE8", "aE9", "aF1", "aF2", "aF3",
         "aG1", "aG2", "aG3", "aH1", "aH2"]
assert set(ORDER) == set(S) and len(ORDER) == 61
out = os.path.join(ROOT, "deck/project/slides"); os.makedirs(out, exist_ok=True)
for f in os.listdir(out):
    os.remove(os.path.join(out, f))
for k in ORDER:
    h = render.fill(S[k], False)
    assert "{{" not in h and "file://" not in h
    open(os.path.join(out, k + ".html"), "w").write(h)
json.dump(ORDER, open(os.path.join(ROOT, "order.json"), "w"))
print(len(ORDER))
