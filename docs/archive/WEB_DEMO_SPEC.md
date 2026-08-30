# WEB_DEMO_SPEC — **SzScan** (bản chốt cuối)
### Gộp WEB_DEMO_SPEC + WEB_DEMO_API_CONTRACT + WEB_DEMO_FOLDER_STRUCTURE. Thay thế toàn bộ 3 file đó + PHASE_C_PLAN*.
### Trạng thái: SPEC KHÓA để code. Phụ thuộc: baseline v3.1 đã khóa (RESULTS_OF_RECORD §0); attribution method khóa (nhãn groundtruth chờ cô).

**Sản phẩm:** **SzScan** (Sz = seizure · scan = hậu-kiểm long-term EEG). Logo đã chốt.
**Một dòng:** web hỗ trợ bác sĩ/KTV **review post-hoc** bản ghi long-term EEG — tăng tốc đọc, giảm gánh nặng — dựng trên 2 lõi đã có: (1) seizure detection + CPD, (2) channel attribution (XAI).

---

## 1. Phạm vi & guardrail trung thực (đọc trước khi code)

- **Phạm vi = 8 test subject** (chb03,06,13,14,15,16,17,18) — đúng 8 case held-out sinh ra số §0. Demo gắn thẳng vào kết quả báo cáo. **KHÔNG** dùng 23 sub (12 train + 3 val không có số locked, và cần GPU pass thừa).
- **Không real-time.** Kết quả **PRE-COMPUTE** offline; backend chỉ serve JSON/npy. Upload là **giả lập** (resolve tên file → case đã cache); interface `load_timeline()` để Stage-2 (upload thật) swap sau mà không đổi frontend.
- **Số hiển thị = §0:** balanced **0.632 @ 38.6 FP/day**, high-sens **0.776 @ 72.7**. **KHÔNG BAO GIỜ** hiện 0.750/0.829 (retired, test-tuned).
- **Chống over-claim (bắt buộc có panel "cách đọc"):** proof-of-concept trên CHB-MIT, **chưa validate lâm sàng**; **hậu-kiểm, không chẩn đoán**; latency ~0–7s (**không "pre-ictal"**); attribution **PROVISIONAL** (chờ nhãn cô).
- **Attribution:** method đã KHÓA (per-node GAE recon-z, MAP@K). Demo **hiển thị được ngay** (ranking = output model thật); **con số accuracy (MAP@K) chờ groundtruth cô** → test sau, gắn nhãn PROVISIONAL ở UI.

---

## 2. User flow & 3 lớp UX

1. Trang chủ → chọn subject (8 test, badge "held-out test set"). Upload giả lập: kéo file `chbXX_*.edf` → resolve tiền tố → matched.
2. Màn kết quả, **linked views** (chọn 1 điểm timeline → EEG viewer + attribution nhảy theo cùng lúc):
   - **Layer 1 — Suspicion Timeline:** sparkline điểm ensemble (nền) + marker **detected event** + marker **ground-truth seizure** (so trực quan hit/miss/FP).
   - **Layer 2 — Raw EEG:** canvas 18 kênh xếp chồng, dark clinical mode; chỉnh cửa sổ/biên độ/filter; cuộn theo timeline.
   - **Layer 3 — Attribution:** sơ đồ 10–20 (SVG), single-hue gradient theo recon-z; cơn **diffuse** → blur + badge "diffuse (no dominant channel)".
3. **Review** mỗi detected event: accept / uncertain / reject + custom label + comment (lưu SQLite).
4. **Export** PDF/CSV (timeline + review + tóm tắt attribution).

**Thời gian:** MỌI mốc = **elapsed seconds từ đầu bản ghi của subject** (không phải giờ đồng hồ) — tránh quirk chb03_24/25, nhất quán `edf_index.py` / `evaluation_protocol.build_timeline*`.

---

## 3. Kiến trúc (đã chốt)

- **Monorepo:** `demo/` là subfolder trong repo thesis. Import thẳng `src/` (thêm `src/` vào PYTHONPATH), **KHÔNG copy code** → giữ single-source (`ensemble_recipe`, `cpd_pipeline_v14`, `edf_index`, `attribution_gae_pernode`).
- **2 venv tách:** venv thesis (torch...) chỉ cho `scripts/build_timeline_json.py` (chạy 1 lần offline); venv demo nhẹ (`fastapi, uvicorn, pyedflib, fpdf2, python-dotenv`) cho backend serve — **không torch/GPU lúc request**.
- **Không hardcode path** → `.env` + `config.py`.
- `.gitignore` thêm: `demo/frontend/node_modules/`, `demo/backend/.venv/`, `demo/backend/data/reviews.db`.

---

## 4. Backend `demo/backend/`

```
app/
  main.py           FastAPI, CORS localhost, mount routers
  config.py         path dataset/cache + hằng (MAX_EEG_SLICE_S=120)
  db.py             SQLite connect + init schema (§6)
  models.py         Pydantic schemas (§5)
  routers/          subjects · timeline · eeg · attribution · reviews · export
  services/
    cpd_service.py         load {subject}_timeline.json precomputed (interface load_timeline(subject_id) — Stage-2 swap point)
    edf_reader.py          pyedflib: (fname, local_start_s, local_end_s) -> samples
    attribution_service.py aggregate pernode.npy theo segment window -> rank + diffuse (§7)
    subject_resolver.py    tên file upload -> subject_id đã cache (8 test)
    review_repo.py         CRUD SQLite
    export_service.py      PDF (fpdf2) + CSV
data/
  timeline/{subject}_timeline.json   × 8    (sinh bởi scripts/)
  reviews.db                                (gitignored)
scripts/
  build_timeline_json.py   OFFLINE precompute (xem §8 — bind v3.1)
tests/test_routes_smoke.py
.env.example · requirements.txt · README.md (uvicorn app.main:app --reload)
```

---

## 5. Data models (Pydantic → `models.py`)

```python
class SubjectSummary(BaseModel):
    subject_id: str; is_test_subject: bool; duration_h: float
    n_files: int; n_detected_events: int; n_ground_truth_seizures: int

class DetectedEvent(BaseModel):
    segment_id: str            # "chb03_evt00" — ổn định giữa các lần chạy
    start_s: float; end_s: float
    pen_mult: float            # operating point (mag/pen) đã dùng
    confidence_tier: Literal["high","low"]

class GroundTruthSeizure(BaseModel):
    seizure_idx: int; start_s: float; end_s: float

class TimelineResponse(BaseModel):
    subject_id: str; duration_s: float; window_sec: int = 4
    score_series: list[float]; score_series_step_s: float     # ~1 điểm/phút
    detected_events: list[DetectedEvent]; ground_truth: list[GroundTruthSeizure]

class EegSliceResponse(BaseModel):
    subject_id: str; channels: list[str]; fs: int = 256
    start_s: float; end_s: float; data: list[list[float]]     # [18][n_samples]

class ChannelAttribution(BaseModel):
    channel: str; z_score: float; rank: int

class AttributionResponse(BaseModel):
    subject_id: str; segment_id: str
    channels: list[ChannelAttribution]                        # rank tăng dần
    confidence_tier: Literal["high","low"]; is_diffuse: bool
    label_source: Literal["v5_expert_draft","no_expert_label"]  # §7
    method_note: str = "per-node GAE recon z-score, ictal window; PROVISIONAL — chờ nhãn blind của GVHD"

class ReviewIn(BaseModel):
    review_status: Literal["accept","uncertain","reject"]
    custom_label: Optional[str] = None; comment: Optional[str] = None

class ReviewOut(ReviewIn):
    subject_id: str; segment_id: str; reviewed_at: str        # ISO
```

**Routes** (base `http://localhost:8000/api`, no auth, elapsed-seconds everywhere, lỗi FastAPI `{"detail":...}`):
- `GET /subjects` → `list[SubjectSummary]` (đọc metadata precompute, không đọc EDF).
- `POST /subjects/resolve` `{filenames:[...]}` → `{subject_id, matched}` (match tiền tố `chbXX`; 8 test → matched=true, còn lại message "chưa có tiền xử lý").
- `GET /subjects/{id}/timeline` → `TimelineResponse` (404 nếu ngoài cache).
- `GET /subjects/{id}/eeg?start_s=&end_s=` → `EegSliceResponse` (400 nếu `end<=start` hoặc `>120s`; `EdfIndex.locate_range` ghép qua ranh giới file).
- `GET /subjects/{id}/segments/{segment_id}/attribution` → `AttributionResponse`.
- `GET/PUT/DELETE /subjects/{id}/segments/{segment_id}/review` (upsert/undo).
- `GET /subjects/{id}/export.{pdf,csv}`.

---

## 6. SQLite

```sql
CREATE TABLE reviews (
  subject_id TEXT NOT NULL, segment_id TEXT NOT NULL,
  review_status TEXT CHECK(review_status IN ('accept','uncertain','reject')),
  custom_label TEXT, comment TEXT, reviewed_at TEXT NOT NULL,
  PRIMARY KEY (subject_id, segment_id)
);
```
Khóa theo `segment_id` (đoạn model detect) — review được cả false-positive, không chỉ cơn thật.

---

## 7. `is_diffuse` / `confidence_tier` — dùng output THẬT của method (không heuristic bịa)

- **Event là true-positive** (trùng ground-truth seizure có nhãn): lấy cột **`diffuse` trong `results/attribution_v5/rank_per_seizure.csv`** → `is_diffuse` + `label_source="v5_expert_draft"`. `confidence_tier="low"` nếu diffuse, else `"high"`.
- **Event là false-positive** (không có nhãn): `label_source="no_expert_label"`; `is_diffuse` = fallback heuristic `margin=(z[r1]-z[r2])/(|z[r1]|+1e-9) < 0.15` (chỉ để hiển thị), `confidence_tier="low"`.
- **UI/tooltip bắt buộc:** ghi rõ "nhãn diffuse là bản nháp phương pháp, CHƯA qua kiểm định GVHD" — chống hiểu nhầm "model tự học diffuse".

---

## 8. Precompute — bind BASELINE v3.1 (⚠️ điểm dễ sai nhất)

`scripts/build_timeline_json.py` chạy 1 lần offline, cho 8 test subject, **dùng đúng cấu hình §0**:
- Ensemble: `ensemble_recipe.build_ensemble` với `ENS_WEIGHTS=(0.3334,0.3333,0.3333)` (equal — đã đúng trên disk).
- Component: **seed42** ens arrays `results/retrain_v3p1/ens/ens_seed42_{subj}_{split}.npy` (canonical; KHÔNG deep-mean).
- CPD: `cpd_pipeline_v14`. **Operating point §0:** mặc định **balanced mag70/pen0.5**; cho toggle **high-sens mag55/pen0.3** (ghi `pen_mult` vào mỗi `DetectedEvent`).
- Ground-truth: parse `chb*-summary.txt` (external `CHBMIT_DATASET_DIR`).
- `pernode.npy`: phải từ **GAE seed42 v3.1** — nếu bản cache cũ từ GAE khác thì regenerate bằng `attribution_gae_pernode.py` trước (8 test đủ, không cần 23).

Checklist precompute: `[ ] timeline.json ×8` · `[ ] pernode.npy ×8 (từ GAE v3.1)` · `[x] edf_index verify 23/23` · `[x] 18 tên kênh chuẩn`.

---

## 9. Frontend `demo/frontend/` (React + TS + Vite)

```
src/
  App.tsx                 SubjectPicker + 3 layer, bọc ViewProvider
  state/ViewContext.tsx   linked views: {subjectId, windowStart_s, windowEnd_s, selectedSegmentId}
  api/client.ts           fetch wrapper (generate từ /openapi.json bằng openapi-typescript)
  components/
    SubjectPicker.tsx      dropzone (giả lập) + 8 test sub, badge test/held-out
    SuspicionTimeline.tsx  Layer 1
    EegViewer.tsx          Layer 2 (canvas, dark clinical)
    AttributionMap.tsx     Layer 3 (SVG 10-20, single-hue, blur+badge diffuse)
    ReviewPanel.tsx        accept/uncertain/reject + label + comment
    ExportButton.tsx
  hooks/ useTimeline · useEegSlice · useAttribution · useReviews
  styles/theme.ts          dark clinical palette + single-hue scale
  utils/time.ts            elapsed-seconds -> "HH:MM:SS kể từ đầu bản ghi"
index.html · package.json · tsconfig.json · vite.config.ts
```

## 10. Config / export
`.env` (không commit): `CHBMIT_DATASET_DIR`, `PERNODE_CACHE_DIR=../../data/pernode`, `TIMELINE_JSON_DIR=./data/timeline`, `REVIEWS_DB_PATH=./data/reviews.db`, `MAX_EEG_SLICE_S=120`, `DIFFUSE_MARGIN_THRESHOLD=0.15`. PDF = **fpdf2** (thuần Python, không cần Cairo/Pango; đổi `reportlab` trong `export_service.py` sau nếu cần).

## 11. Reuse vs viết mới
| Reuse `src/` (không đụng) | Viết mới |
|---|---|
| `edf_index.py`, `evaluation_protocol.py` (parser), `ensemble_recipe.py`+`cpd_pipeline_v14.py` (dùng 1 lần trong build_timeline_json), `attribution_gae_pernode.py` (công thức z tham chiếu) | `config.py`, `db.py`, mọi `routers/*`, `cpd_service`, `edf_reader`, `attribution_service`, `subject_resolver`, `review_repo`, `export_service`, `build_timeline_json.py`, toàn bộ `demo/frontend/` |

## 12. Thứ tự build (item CUỐI — không ăn vào thời gian viết report)
UX/UI + khung frontend (làm trước được) → `build_timeline_json.py` (8 sub) + mở rộng `pernode.npy` (8 sub, GAE v3.1) → backend theo contract → frontend 3 layer → smoke test → export. Nếu runway ép: **demo cắt trước report**; demo phục vụ defense (điểm nhấn), không nằm trên critical path báo cáo.
