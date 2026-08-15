# Next steps — cac lenh de chay tiep (lon -> nho)

Generated: 2026-08-15 10:54

1. Mo `00_overview.md` de xem toan bo cay thu muc + mtime/created.
2. Chay tung lenh `deep` ben duoi de xem NOI DUNG DAY DU cua file trong tung folder lon (ghi ra `deep_<ten>.md` + `.csv`).
3. Chay lenh `audit` (o cuoi) MOT LAN cho toan repo de tim file trung ten va so lieu loi thoi.

| # | Folder | Files (de quy) | Dung luong | Lenh de chay |
|---|---|---|---|---|
| 01 | data | 527 | 32.9GB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\data" --no-content` |
| 02 | results | 728 | 182.6MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\results"` |
| 03 | seizure_segments | 229 | 162.0MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\seizure_segments"` |
| 04 | topo_features | 16 | 1.7MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\topo_features"` |
| 05 | figures | 2 | 754.5KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\figures"` |
| 06 | src | 63 | 649.3KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\src"` |
| 07 | archive | 81 | 542.6KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\archive"` |
| 08 | logs | 4 | 516.8KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\logs"` |
| 09 | docs | 21 | 312.3KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\docs"` |
| 10 | notebooks | 2 | 80.6KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\notebooks"` |

## File nam truc tiep o goc repo

| File | Size | Modified |
|---|---|---|
| .gitignore | 791.0B | 2026-07-31 20:27:14 |
| attribution_detail.py | 4.3KB | 2026-08-11 09:27:05 |
| compare_labels_pernode.py | 8.1KB | 2026-08-08 09:28:13 |
| Dockerfile | 0.0B | 2026-04-04 12:16:10 |
| dump_components.py | 2.8KB | 2026-08-13 00:49:59 |
| entry.sh | 0.0B | 2026-04-04 12:16:12 |
| label_eeg_pilot.py | 15.9KB | 2026-08-11 10:48:47 |
| Makefile | 0.0B | 2026-04-04 12:16:12 |
| pip_freeze.txt | 1.8KB | 2026-07-26 00:20:09 |
| project_inventory.py | 27.4KB | 2026-08-15 10:53:52 |
| README.md | 8.8KB | 2026-07-31 11:51:45 |
| requirements.txt | 207.0B | 2026-04-04 12:16:11 |
| scan_out.txt | 34.0KB | 2026-07-31 19:58:05 |
| validate_dominant_hitk_FINAL.py | 3.7KB | 2026-08-11 19:35:11 |

## Lenh audit toan repo (chay rieng, sau khi da xem overview)

```
python project_inventory.py audit --root "F:\Study\Thesis\Code"
```