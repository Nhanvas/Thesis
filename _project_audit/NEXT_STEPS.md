# Next steps — deep-scan commands (chay lan luot, goi y tu lon den nho)

Generated: 2026-08-13 15:52

Mo `00_overview.md` truoc de xem tong quan. Sau do chay tung lenh ben duoi,
moi lenh se ghi ket qua chi tiet vao 2 file rieng (`deep_<ten>.md` + `.csv`)
trong cung thu muc audit nay — khong in tran ra terminal. Voi cac folder chua
data/model/checkpoint nang, script da tu bo `--peek` de chay nhanh hon va tranh
doc nham noi dung file nhi phan (ban van co the tu them `--peek` neu muon).

| # | Folder | Files (de quy) | Dung luong | Lenh de chay |
|---|---|---|---|---|
| 01 | data | 522 | 32.9GB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\data"` |
| 02 | results | 585 | 179.2MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\results" --peek` |
| 03 | seizure_segments | 229 | 162.0MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\seizure_segments" --peek` |
| 04 | topo_features | 16 | 1.7MB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\topo_features" --peek` |
| 05 | figures | 2 | 754.5KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\figures" --peek` |
| 06 | src | 63 | 648.8KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\src" --peek` |
| 07 | archive | 81 | 542.6KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\archive" --peek` |
| 08 | logs | 4 | 516.8KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\logs" --peek` |
| 09 | docs | 17 | 256.7KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\docs" --peek` |
| 10 | notebooks | 2 | 80.6KB | `python project_inventory.py deep --root "F:\Study\Thesis\Code\notebooks" --peek` |

## Cac file nam truc tiep o goc (khong thuoc folder con nao)

| File | Size | Modified |
|---|---|---|
| .gitignore | 791.0B | 2026-07-31 20:27 |
| attribution_detail.py | 4.3KB | 2026-08-11 09:27 |
| compare_labels_pernode.py | 8.1KB | 2026-08-08 09:28 |
| Dockerfile | 0.0B | 2026-04-04 12:16 |
| dump_components.py | 2.8KB | 2026-08-13 00:49 |
| entry.sh | 0.0B | 2026-04-04 12:16 |
| label_eeg_pilot.py | 15.9KB | 2026-08-11 10:48 |
| Makefile | 0.0B | 2026-04-04 12:16 |
| pip_freeze.txt | 1.8KB | 2026-07-26 00:20 |
| project_inventory.py | 15.8KB | 2026-08-13 15:52 |
| README.md | 8.8KB | 2026-07-31 11:51 |
| requirements.txt | 207.0B | 2026-04-04 12:16 |
| scan_out.txt | 34.0KB | 2026-07-31 19:58 |
| validate_dominant_hitk_FINAL.py | 3.7KB | 2026-08-11 19:35 |