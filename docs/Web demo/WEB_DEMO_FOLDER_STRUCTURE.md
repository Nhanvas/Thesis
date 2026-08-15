# WEB_DEMO_FOLDER_STRUCTURE — Cấu trúc thư mục demo/backend + demo/frontend
### Bổ sung cho `WEB_DEMO_API_CONTRACT.md`. DRAFT, chờ xác nhận trước khi tạo thư mục thật.
### Thay thế cấu trúc đề xuất cũ trong `PHASE_C_PLAN.md` (đã lệch: `src/` giờ đã phẳng, có
### `edf_index.py` sẵn — không cần copy lại; và plan cũ chưa có SQLite/export/23-sub).

---

## 0. Monorepo hay repo riêng? — ĐÃ CHỐT: monorepo (`demo/` là subfolder trong repo thesis)

**Không tách repo riêng.** Lý do:
- Demo phụ thuộc trực tiếp vào `src/` (`edf_index.py`, `ensemble_recipe.py`, `cpd_pipeline_v14.py`,
  `attribution_gae_pernode.py`). Tách repo chỉ còn 2 lựa chọn: copy code sang (tạo bản sao rời khỏi
  single-source — đúng loại lỗi stale-cache đã dính nhiều lần, xem `RESULTS_OF_RECORD.md` §13/§14),
  hoặc git submodule (phiền, dễ quên sync, không đáng với deadline đang gấp).
- Không có lý do tổ chức để tách: tách repo hợp lý khi nhiều người/team cần quyền riêng, cần chu kỳ
  release riêng, hoặc deploy public độc lập — cả 3 đều không đúng ở đây (1 người làm, demo
  local-only đã chốt, không public deploy).
- Giữ chung repo là cách tự nhiên nhất để enforce nguyên tắc "1 nguồn sự thật" project đang theo
  (`ensemble_recipe.py`/`cpd_pipeline_v14.py` = nguồn duy nhất) — import thẳng, không cần đồng bộ
  version giữa 2 repo.

**Vệ sinh repo cần làm khi giữ chung:**
- `.gitignore` thêm: `demo/frontend/node_modules/`, `demo/backend/.venv/`, `demo/backend/data/reviews.db`.
- **2 virtual env tách biệt, không dùng chung:**
  - venv chính của thesis (torch, torch_geometric, ruptures, timescoring...) — chỉ cần cho DUY NHẤT
    `scripts/build_timeline_json.py` (gọi thật `cpd_pipeline_v14`/`ensemble_recipe`).
  - venv riêng, nhẹ cho `demo/backend/` (`requirements.txt`: fastapi, uvicorn, pyedflib, fpdf2) —
    server lúc chạy demo chỉ đọc JSON/npy đã có sẵn bằng numpy thuần, KHÔNG cần torch/GPU (đúng
    nguyên tắc `PHASE_C_PLAN.md` gốc: backend không cần GPU để serve demo).
  - Hai `requirements.txt` không đụng nhau, không sợ conflict version.

**Về lâu dài:** nếu sau bảo vệ muốn deploy public làm portfolio, tách repo lúc đó mới thật sự có lợi
— và vì `demo/` đã tự chứa với ranh giới import rõ ràng (chỉ chạm `src/` qua vài module cụ thể), tách
sau này chỉ là copy `demo/` + đóng gói vài module `src/` nó cần, không phải thiết kế lại. Không cần
lo trước bây giờ.

---

## 0.1 Nguyên tắc (tại sao cây thư mục trông như dưới)

- **Import thẳng từ `src/`, không copy code.** `demo/` và `src/` là 2 thư mục ngang hàng ở repo
  root; backend thêm `src/` vào `PYTHONPATH` (hoặc `sys.path.insert`) thay vì tạo bản sao
  `edf_index.py`/`evaluation_protocol.py` bên trong `demo/`.
- **Không copy data/cache vào `demo/`.** Đường dẫn tới dataset CHB-MIT gốc và các cache đã có
  (`data/pernode/`, `data/processed/components/`, ...) được cấu hình qua 1 file (`config.py` +
  `.env`), không hardcode, không duplicate.
- **`demo/backend/data/` chỉ chứa thứ THẬT SỰ mới, sinh riêng cho demo** (không tồn tại nơi khác
  trong repo): `timeline.json` đã precompute cho 23 sub, và file SQLite `reviews.db`.
- Router (HTTP layer) tách khỏi service (business logic) — đúng convention FastAPI, cũng khớp
  cách `PHASE_C_PLAN.md` gốc đã định hướng.

---

## 1. Backend (`demo/backend/`)

```
demo/backend/
├── app/
│   ├── main.py                    # FastAPI app, CORS (chỉ mở cho localhost frontend), mount routers
│   ├── config.py                  # NEW — đường dẫn dataset CHB-MIT gốc, cache dirs, hằng số
│   │                               #   (giới hạn 120s/request EEG, ngưỡng margin §4 = 0.15)
│   ├── db.py                      # NEW — SQLite connection + init schema (từ API_CONTRACT §3)
│   ├── models.py                  # Pydantic schemas — copy nguyên từ API_CONTRACT §1
│   ├── routers/
│   │   ├── subjects.py            # GET /subjects · POST /subjects/resolve
│   │   ├── timeline.py            # GET /subjects/{id}/timeline
│   │   ├── eeg.py                 # GET /subjects/{id}/eeg
│   │   ├── attribution.py         # GET /subjects/{id}/segments/{segment_id}/attribution
│   │   ├── reviews.py             # NEW — GET/PUT/DELETE review
│   │   └── export.py              # NEW — GET export.pdf · export.csv
│   ├── services/
│   │   ├── cpd_service.py         # đọc {subject}_timeline.json đã precompute — KHÔNG gọi
│   │   │                           #   cpd_pipeline_v14 lúc request (xem §0). Đây chính là chỗ
│   │   │                           #   Stage 2 (upload thật) sau này chỉ cần thay nội dung hàm,
│   │   │                           #   giữ nguyên interface load_timeline(subject_id).
│   │   ├── edf_reader.py          # pyedflib: đọc (fname, local_start_s, local_end_s) -> samples
│   │   ├── attribution_service.py # NEW — aggregate pernode.npy theo segment window, tính rank
│   │   │                           #   + confidence_tier/is_diffuse (công thức API_CONTRACT §4)
│   │   ├── subject_resolver.py    # NEW — match tên file upload -> subject_id đã có cache
│   │   ├── review_repo.py         # NEW — CRUD SQLite cho bảng reviews
│   │   └── export_service.py      # NEW — build PDF (fpdf2) + CSV từ timeline+review+attribution
│   └── __init__.py
├── data/                          # CHỈ chứa thứ mới sinh riêng cho demo (xem §0)
│   ├── timeline/                  # {subject}_timeline.json  × 23   — sinh bởi scripts/ bên dưới
│   └── reviews.db                 # SQLite — gitignore (chỉ commit reviews.db.example rỗng nếu cần)
├── scripts/
│   └── build_timeline_json.py     # NEW — precompute: đọc output CPD (qua ensemble_recipe +
│                                   #   cpd_pipeline_v14 thật, chạy 1 lần offline) + ground truth
│                                   #   từ summary.txt -> ghi {subject}_timeline.json cho 23 sub
├── tests/
│   └── test_routes_smoke.py       # NEW — smoke test từng route, theo đúng tinh thần
│                                   #   smoke_test_edf_index.py đã làm (viết khi bắt đầu code)
├── .env.example                   # CHBMIT_DATASET_DIR=... · PERNODE_CACHE_DIR=... (không commit .env thật)
├── requirements.txt                # fastapi, uvicorn, pyedflib, fpdf2, python-dotenv, ...
└── README.md                      # lệnh chạy: uvicorn app.main:app --reload
```

## 2. Frontend (`demo/frontend/`)

```
demo/frontend/
├── src/
│   ├── main.tsx
│   ├── App.tsx                    # top-level: SubjectPicker + 3 layer, bọc trong ViewProvider
│   ├── state/
│   │   └── ViewContext.tsx        # NEW — state dùng chung: {subjectId, windowStart_s, windowEnd_s,
│   │                               #   selectedSegmentId} — đây là cơ chế "linked views" đã chốt
│   │                               #   (chọn 1 điểm trên timeline -> EEG viewer + attribution
│   │                               #   panel nhảy theo cùng lúc)
│   ├── api/
│   │   └── client.ts              # fetch wrapper, kiểu TS khớp models.py (có thể generate tự
│   │                               #   động từ FastAPI's /openapi.json bằng openapi-typescript,
│   │                               #   đỡ phải gõ tay lại — cân nhắc khi có API thật)
│   ├── components/
│   │   ├── SubjectPicker.tsx      # dropzone upload (giả lập) + dropdown 23 sub, badge test/non-test
│   │   ├── SuspicionTimeline.tsx  # Layer 1 — sparkline nền + marker detected/ground-truth
│   │   ├── EegViewer.tsx          # Layer 2 — canvas tự vẽ, 18 kênh xếp chồng, dark clinical mode
│   │   ├── AttributionMap.tsx     # Layer 3 — SVG sơ đồ 10-20, single-hue gradient, blur+badge diffuse
│   │   ├── ReviewPanel.tsx        # 3-state accept/uncertain/reject + custom label + comment
│   │   └── ExportButton.tsx       # trigger tải PDF/CSV
│   ├── hooks/
│   │   ├── useTimeline.ts · useEegSlice.ts · useAttribution.ts · useReviews.ts
│   ├── styles/
│   │   └── theme.ts               # dark clinical mode palette + thang single-hue (đã chốt track UX)
│   ├── utils/
│   │   └── time.ts                # format elapsed seconds -> "HH:MM:SS kể từ đầu bản ghi"
│   └── types.ts                   # interface TS khớp Pydantic models
├── index.html · package.json · tsconfig.json · vite.config.ts
```

---

## 3. Config / .env

Không hardcode đường dẫn tuyệt đối (kiểu `F:/Study/Thesis/Dataset/...`) trong source — để trong
`.env` (không commit), đọc qua `config.py`:

```
CHBMIT_DATASET_DIR=F:/Study/Thesis/Dataset/CHB-MIT/CHB info
PERNODE_CACHE_DIR=../../data/pernode          # trỏ ngược lên data/ gốc của repo, không copy
TIMELINE_JSON_DIR=./data/timeline             # thư mục mới, riêng cho demo
REVIEWS_DB_PATH=./data/reviews.db
MAX_EEG_SLICE_S=120
DIFFUSE_MARGIN_THRESHOLD=0.15
```

## 4. Thư viện PDF export — đề xuất `fpdf2`

Không dùng `weasyprint` (cần cài thêm Cairo/Pango ở tầng hệ điều hành — thường rắc rối trên
Windows). `fpdf2` thuần Python, không cần cài gì thêm ngoài `pip install fpdf2`, đủ cho báo cáo
dạng bảng (timeline + review + attribution tóm tắt) — nếu sau này cần layout đẹp hơn (đồ thị,
nhiều cột phức tạp) thì đổi sang `reportlab`, đổi trong `export_service.py` không ảnh hưởng chỗ khác.

---

## 5. Checklist: cái nào TÁI DÙNG, cái nào MỚI PHẢI VIẾT

| Reuse từ `src/` (không đụng vào) | Mới phải viết |
|---|---|
| `edf_index.py` ✅ đã verify 23/23 subject, 0 FAIL/WARN (`smoke_test_edf_index.py`) | `config.py`, `db.py`, tất cả `routers/*.py` |
| `evaluation_protocol.py` (parser summary) | `cpd_service.py`, `edf_reader.py`, `attribution_service.py`, `subject_resolver.py`, `review_repo.py`, `export_service.py` |
| `ensemble_recipe.py` + `cpd_pipeline_v14.py` — dùng **1 lần** trong `scripts/build_timeline_json.py`, không dùng lúc request | `scripts/build_timeline_json.py` |
| `attribution_gae_pernode.py` — công thức z-score tham chiếu cho `attribution_service.py` | Toàn bộ `demo/frontend/` |

---
*Tiếp theo (khi rebuild xong, không cần bàn lại): chạy `scripts/build_timeline_json.py` cho 23 sub
→ mở rộng export `pernode.npy` lên 23 sub → code backend theo contract → code frontend theo 3 layer.*