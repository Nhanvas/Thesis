# Chạy trong Python shell để verify count
from src.cpd_pipeline_v2 import parse_summary_edf_list
from pathlib import Path

SUMMARY_DIR = Path(r"F:\Study\Thesis\Dataset\CHB-MIT\CHB info\summary")

for subj in ["chb03","chb06","chb13","chb14","chb15","chb16","chb17","chb18"]:
    edfs = parse_summary_edf_list(SUMMARY_DIR / f"{subj}-summary.txt")
    n_sz = sum(len(e['seizures']) for e in edfs)
    print(f"{subj}: {n_sz} seizures in summary")