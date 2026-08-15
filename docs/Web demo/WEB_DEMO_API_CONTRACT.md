# WEB_DEMO_API_CONTRACT — API contract cho Phase C backend
### Trạng thái: DRAFT, chờ xác nhận trước khi code. Bổ sung cho `WEB_DEMO_SPEC.md` (bài toán/UX)
### và `PHASE_C_PLAN.md` (kiến trúc gốc) — file này là bản đặc tả kỹ thuật cụ thể để code thẳng vào.

---

## 0. Quy ước chung

- Base URL (local): `http://localhost:8000/api`
- Không auth (single-user, chạy local cho GVHD/hội đồng, không public deploy)
- **Toàn bộ thời gian trong API = elapsed seconds tính từ đầu recording của subject đó**
  (không phải giờ đồng hồ thật) — tránh đúng quirk chb03_24/25 đã phát hiện, nhất quán với
  cách `edf_index.py` và `evaluation_protocol.build_timeline*` đánh index.
- Lỗi chuẩn FastAPI: `{"detail": "..."}`. 404 khi subject/segment không tồn tại trong cache,
  400 khi range không hợp lệ (map thẳng từ `ValueError` mà `EdfIndex.locate()/locate_range()`
  đã raise sẵn — không cần viết lại logic validate).
- CORS: mở cho origin của frontend dev server (localhost) — không cần cấu hình production.

---

## 1. Data models (Pydantic — dùng thẳng cho `models.py`)

```python
from pydantic import BaseModel
from typing import Literal, Optional


class SubjectSummary(BaseModel):
    subject_id: str                    # "chb03"
    is_test_subject: bool              # True cho 8 sub có số liệu đã khóa (RESULTS_OF_RECORD)
    duration_h: float
    n_files: int
    n_detected_events: int
    n_ground_truth_seizures: int


class DetectedEvent(BaseModel):
    segment_id: str                    # "chb03_evt00" — sinh ổn định lúc precompute, không đổi giữa các lần chạy
    start_s: float
    end_s: float
    pen_mult: float                    # operating point (mag/pen) đã dùng để sinh event này
    confidence_tier: Literal["high", "low"]   # công thức ở §4


class GroundTruthSeizure(BaseModel):
    seizure_idx: int
    start_s: float
    end_s: float


class TimelineResponse(BaseModel):
    subject_id: str
    duration_s: float
    window_sec: int = 4
    score_series: list[float]          # downsampled ensemble score, ~1 điểm/phút, vẽ sparkline nền
    score_series_step_s: float
    detected_events: list[DetectedEvent]
    ground_truth: list[GroundTruthSeizure]   # để so sánh trực quan model bắt đúng/sai/miss


class EegSliceResponse(BaseModel):
    subject_id: str
    channels: list[str]                # 18 tên kênh bipolar, đúng thứ tự chuẩn CHB-MIT
    fs: int                            # 256
    start_s: float
    end_s: float
    data: list[list[float]]            # shape [18][n_samples]


class ChannelAttribution(BaseModel):
    channel: str
    z_score: float
    rank: int


class AttributionResponse(BaseModel):
    subject_id: str
    segment_id: str
    channels: list[ChannelAttribution]     # sắp theo rank tăng dần
    confidence_tier: Literal["high", "low"]
    is_diffuse: bool                       # công thức §4
    method_note: str = ("per-node GAE reconstruction z-score, ictal window; "
                         "PROVISIONAL — chờ nhãn blind của GVHD")


class ReviewIn(BaseModel):
    review_status: Literal["accept", "uncertain", "reject"]
    custom_label: Optional[str] = None
    comment: Optional[str] = None


class ReviewOut(ReviewIn):
    subject_id: str
    segment_id: str
    reviewed_at: str                   # ISO timestamp
```

---

## 2. Routes

### 2.1 Subjects

**`GET /api/subjects`** → `list[SubjectSummary]`
Đọc thẳng từ metadata đã precompute — KHÔNG đọc EDF ở route này, phải nhanh (danh sách 23 sub).

**`POST /api/subjects/resolve`**
Body: `{"filenames": ["chb03_01.edf", "chb03_02.edf", ...]}`
Response: `{"subject_id": "chb03", "matched": true}` hoặc `{"subject_id": null, "matched": false, "message": "Chưa có dữ liệu tiền xử lý cho case này"}`
Logic: match tiền tố `chbXX` từ tên file → có cache tương ứng thì `matched=true`. Đây là bước
"giả lập nhận diện" đã chốt (giữ cảm giác upload, không chạy pipeline thật).

### 2.2 Layer 1 — Timeline

**`GET /api/subjects/{subject_id}/timeline`** → `TimelineResponse`
404 nếu `subject_id` không có trong cache.

### 2.3 Layer 2 — Raw EEG

**`GET /api/subjects/{subject_id}/eeg?start_s=&end_s=`** → `EegSliceResponse`
- 400 nếu `end_s <= start_s`, hoặc nếu `end_s - start_s` vượt giới hạn tối đa 1 lần request
  (đề xuất **120s** — đủ cho window rộng nhất một bác sĩ cần xem, tránh frontend lỡ xin nguyên
  bản ghi nhiều giờ).
- Gọi `EdfIndex.locate_range(start_s, end_s)` → có thể trả nhiều segment nếu bắc qua ranh giới
  file (đã verify hoạt động đúng ở smoke test) → đọc từng đoạn bằng `pyedflib`, ghép lại đúng
  thứ tự thời gian trước khi trả response.

### 2.4 Layer 3 — Attribution

**`GET /api/subjects/{subject_id}/segments/{segment_id}/attribution`** → `AttributionResponse`
- Tra `segment_id` → `(start_s, end_s)` từ timeline đã precompute.
- Đọc `{subject}_{split}_pernode.npy` đúng đoạn window đó, tính z-score trung bình mỗi kênh
  (cùng công thức `attribution_gae_pernode.py`), rank giảm dần.
- Tính `confidence_tier` + `is_diffuse` theo §4.

### 2.5 Review (SQLite)

**`GET /api/subjects/{subject_id}/reviews`** → `list[ReviewOut]`
**`PUT /api/subjects/{subject_id}/segments/{segment_id}/review`** body `ReviewIn` → `ReviewOut`
(upsert: tạo mới nếu chưa có, ghi đè nếu đã có)
**`DELETE /api/subjects/{subject_id}/segments/{segment_id}/review`** → xóa (undo review)

### 2.6 Export

**`GET /api/subjects/{subject_id}/export.pdf`** → file PDF (timeline + review + tóm tắt attribution của subject)
**`GET /api/subjects/{subject_id}/export.csv`** → file CSV (mỗi dòng = 1 segment đã review, đủ cột)

---

## 3. SQLite schema (bản chốt)

```sql
CREATE TABLE reviews (
    subject_id     TEXT NOT NULL,
    segment_id     TEXT NOT NULL,
    review_status  TEXT CHECK(review_status IN ('accept','uncertain','reject')),
    custom_label   TEXT,
    comment        TEXT,
    reviewed_at    TEXT NOT NULL,
    PRIMARY KEY (subject_id, segment_id)
);
```
**Khác bản nháp trong chat trước:** dùng `segment_id` (đoạn model **detect được**) thay vì
`seizure_idx` (cơn ground-truth) — vì bác sĩ có thể cần review/reject cả những đoạn model báo
sai (false positive), không chỉ những cơn thật.

---

## 4. Công thức `confidence_tier` / `is_diffuse` — ⚠️ CẦN NHÂN XÁC NHẬN

Đây là chỗ mình phải tự đề xuất vì `ATTRIBUTION_SPEC.md` chưa có công thức tính confidence
tự động — tiêu chí "diffuse" hiện tại chỉ tồn tại dưới dạng **quy trình đọc mắt của GVHD**
(`TIEU_CHI_LABEL_dominant_channel_v2.md`), không phải công thức từ z-score. Đề xuất heuristic
riêng cho demo:

```
margin = (z[rank1] - z[rank2]) / (abs(z[rank1]) + 1e-9)
is_diffuse = margin < 0.15          # ngưỡng tạm, có thể chỉnh sau khi xem UI thực tế
confidence_tier = "low" if is_diffuse else "high"
```

Ý tưởng: nếu kênh hạng 1 không tách biệt rõ khỏi kênh hạng 2 thì coi như không có kênh trội
thật sự — khớp tinh thần "diffuse" nhưng đo bằng z-score thay vì mắt người.

**Phải ghi rõ trong UI/tooltip đây là suy luận tự động (demo heuristic), KHÔNG phải nhãn đã
qua kiểm định của GVHD** — tránh hiểu nhầm "model tự học được diffuse", đúng tinh thần chống
overclaim đã nói ở `WEB_DEMO_SPEC.md` §5.

---

## 5. Precompute cần có trước khi backend chạy được (checklist, làm sau rebuild)

- [ ] `{subject}_timeline.json` cho cả 23 sub — sinh 1 lần từ output CPD + ground truth summary
- [ ] `{subject}_{split}_pernode.npy` cho cả 23 sub (hiện chỉ có 8 sub test)
- [x] `edf_index.py` — đã verify 23/23 subject, 0 FAIL/WARN
- [x] Danh sách 18 tên kênh chuẩn — đã có sẵn trong summary parser

---
*Tiếp theo: cấu trúc thư mục `demo/backend` + `demo/frontend` cụ thể, dựa trên contract này.*
