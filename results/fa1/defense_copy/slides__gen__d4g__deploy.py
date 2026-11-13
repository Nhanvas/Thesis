import sys, os, json
sys.path.insert(0, os.path.dirname(__file__))
import render
ROOT = render.ROOT
S = render.collect(["slides_main", "slides_refs", "slides_app1", "slides_app2", "slides_app3"])
ORDER = ["p02_toc", "p04_eeg", "p06_goals", "p25_conc", "r26",
         "aA1", "aA2", "aA3", "aA4", "aB1", "aB2", "aB3", "aB4", "aC1", "aC3", "aC4", "aC6", "aC7",
         "aD1", "aD3", "aE1", "aE3", "aE6", "aE10", "aF1", "aF3", "aF4", "aG1", "aG2", "aH1", "aH2"]
assert set(ORDER) == set(S), set(S) ^ set(ORDER)
out = os.path.join(ROOT, "deck/project/slides"); os.makedirs(out, exist_ok=True)
for k in ORDER:
    h = render.fill(S[k], False)
    assert "{{" not in h and "file://" not in h
    open(os.path.join(out, k + ".html"), "w").write(h)
print(json.dumps(ORDER))
