# DEMO_BUILD_HANDOFF.md — kế hoạch build SzScan

**Trạng thái: KHÓA để bắt đầu code.** File này gom stack, cấu trúc thư mục, quy trình làm việc và cách xử
lý code cũ. Hấp thu hoàn toàn `WEB_DEMO_CODE_MIGRATION_NOTES.md` (→ `docs/archive/demo_v4/`).

Hành vi/logic: `SZSCAN_SPEC_v5.md`. Thị giác: `SZSCAN_DESIGN_v2.md`. Ảnh chốt: `UI/`.

---

## 1 · Stack — tất cả miễn phí

| Lớp | Chọn | Lý do |
|---|---|---|
| Backend | **Python + FastAPI** | Bắt buộc Python: inference thật dùng torch/torch_geometric, không viết lại bằng JS được. FastAPI nhẹ, ít boilerplate |
| Lưu review | **SQLite** (1 file `.db`) | Có sẵn trong Python, không cần cài gì, đủ cho demo 1 người dùng |
| Frontend | **React + Vite + Tailwind** | Token trong `SZSCAN_DESIGN_v2.md §9` map thẳng sang Tailwind config, gần như copy-paste |
| Vẽ waveform | **Canvas tự viết** | Thư viện chart thông thường (recharts…) giật khi vẽ 18 kênh × hàng nghìn điểm. Phải render tay |
| Font | Inter + IBM Plex Mono | Google Fonts, miễn phí. **Tải về đóng gói cùng app**, không load qua CDN (bảo vệ có thể không có mạng) |
| Chạy lúc bảo vệ | 1 lệnh khởi động, chạy hoàn toàn local, **không cần internet** | Loại rủi ro mạng/deploy |

**Không dùng Figma MCP.** File `.fig` có layer thật, nhưng Dev Mode MCP thuộc gói trả phí và không cần
thiết: toàn bộ hex/spacing đã được đo trực tiếp từ PNG và ghi trong `SZSCAN_DESIGN_v2.md`. Nếu về sau cần
thêm số đo, hai đường miễn phí: đọc pixel từ PNG, hoặc mở Figma bấm Inspect chép tay.

**Máy chạy demo = máy dev.** Không cần đóng gói portable/installer.

---

## 2 · Cấu trúc thư mục

Dùng **chung repo** `F:/Study/Thesis/Code` — vì demo tái sử dụng đúng các module single-source
(`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `edf_index.py`, `edf_order.py`) mà không
được copy/nhân bản. Đây cũng là 1 sản phẩm hoàn chỉnh nên nên nằm cùng chỗ.

```
web_demo/
├── CLAUDE.md                  # rule cho Claude Code (đọc trước khi code)
├── SZSCAN_SPEC_v5.md          # hành vi/logic/ranh giới dữ liệu
├── SZSCAN_DESIGN_v2.md        # token thị giác
├── DEMO_BUILD_HANDOFF.md      # file này
├── PROJECT2_SETUP.md          # cách dựng Claude project #2 + danh sách file upload
├── UI/                        # PNG bản chốt + UI (figma).fig  ← THAM CHIẾU BẮT BUỘC
├── backend/                   # Claude Code tạo
│   ├── main.py                # FastAPI app
│   ├── pipeline_demo.py       # ★ đường label-free liên tục (code MỚI, xem §4)
│   ├── db.py                  # SQLite schema + truy vấn
│   ├── export_txt.py          # sinh file export theo SPEC §7
│   ├── .env.example           # ADMIN_USER / ADMIN_PASS (file .env thật KHÔNG commit)
│   └── tests/
│       └── test_guards.py     # ★ test liêm chính, xem CLAUDE.md
├── frontend/                  # Claude Code tạo
└── cache/                     # output pipeline demo tính sẵn (gitignore)
```

`web_demo/backend/` và `web_demo/frontend/` **không tồn tại** cho tới khi bắt đầu code — Claude Code tạo.

---

## 3 · Xử lý code cũ

| File | Hành động | Lý do |
|---|---|---|
| `src/edf_index.py` | **Giữ nguyên code**, chỉ sửa docstring | `locate_range()` vẫn cần: sau khi PELT chạy trên timeline ghép, nó map event global → đúng file + offset cục bộ. Docstring cũ mô tả sai vai trò ("cắt EEG để hiển thị") — vai trò thật là gán event về file |
| `src/edf_order.py` | **Giữ nguyên hoàn toàn** | Giải quyết vấn đề độc lập: thứ tự **hiển thị** file trên UI (theo giờ thật trong header EDF) khác thứ tự **xử lý** (theo TÊN FILE — quy ước khóa để khớp kết quả thesis). Có case lệch thật như `chb03_24/25` |
| `src/cpd_pipeline_v14.py`, `ensemble_recipe.py`, `szcore_eval.py`, `retrain/gae_joint.py` | **Chỉ đọc, không sửa** | Single-source dùng chung với thesis |
| `src/szcore_eval.build_timeline_masked()` | **CẤM gọi từ demo** | Cần ground-truth — xem `SZSCAN_SPEC_v5.md` §1.2 |

Hai vấn đề độc lập, đừng gộp: `edf_index` = "event này thuộc file nào" (thời gian → file);
`edf_order` = "file này hiện ở vị trí thứ mấy trên UI" (thứ tự hiển thị).

---

## 4 · `pipeline_demo.py` — phần code mới, là lõi của demo

Chưa có module nào trong repo làm việc này. Đây là **anh em song sinh label-free** của đường thesis,
**không được ghi đè** bất kỳ module nào trong `src/`.

```
# giai đoạn 1 — chạy ngay khi 1 file upload xong
def process_file(edf_path) -> np.ndarray:      # ensemble score liên tục theo thời gian
    đọc 18 kênh chuẩn (bỏ EKG/EOG/Ref)
    bandpass 0.5–60 + notch 60
    cắt window 4 s, KHÔNG bỏ window nào        # ⇒ t_giây = idx * 4, ánh xạ 1-1
    z-score per-channel, stats fit trên TOÀN BỘ window của subject
    CAR → wPLI + AEC → top-k 20% → node feat [adj-row 18 | band-power 5]
    GAE seed42 forward → zrecon, Z
    zlatent = Mahalanobis(Z, LedoitWolf fit trên TOÀN BỘ Z)
    zgamma  = gamma-AEC (bản liên tục — xem O5 trong SPEC §8)
    robust-z từng nhánh → ensemble equal 1/3
    return score            # dài đúng bằng số window của file

# giai đoạn 2 — chạy khi bấm "Process"
def process_subject(files) -> dict[file -> list[Event]]:
    files_sorted = sort theo TÊN FILE          # KHÔNG phải thứ tự hiển thị
    global_score = concat([score[f] for f in files_sorted])
    events_global = cpd_pipeline_v14.detect_events(global_score, ...)   # label-free
    op = operating point FP-budget (đọc tham số từ file, xem SPEC §8 O1)
    for ev in events_global:
        file, local_offset = EdfIndex(subject).locate_range(ev.onset_s, ev.offset_s)
        gán ev vào danh sách event của file đó
```

**Bốn chỗ fit khác pipeline thesis** — đã ghi và biện minh trong `SZSCAN_SPEC_v5.md §1.4`. Đọc trước khi
viết, đừng suy luận lại từ đầu.

---

## 5 · Waveform — lưu ý kỹ thuật quan trọng

18 kênh × 256 Hz × 1 giờ = **16.6 triệu điểm/file**. Không gửi thẳng xuống trình duyệt.

- Backend phục vụ waveform theo **cửa sổ thời gian đang xem**, đã **decimate** xuống ~2–4 điểm/pixel
  (min/max envelope, không phải lấy mẫu thưa — lấy mẫu thưa làm mất gai nhọn, mà gai nhọn chính là thứ
  bác sĩ cần thấy).
- Đổi độ dài cửa sổ (`⊲▷ [X] hr`) → gọi lại backend với mức decimate khác.
- Đổi biên độ (`⇕ [X] uV`) → **thuần frontend**, chỉ scale lại, không gọi backend.
- Bật/tắt filter → backend trả **cả 2 chuỗi** (raw + filtered) trong 1 lần gọi, frontend tự chồng lớp.

---

## 6 · Thứ tự build — dựng xong màn nào chốt màn đó

| # | Bước | Xong khi |
|---|---|---|
| 0 | Khung repo, token Tailwind từ `SZSCAN_DESIGN_v2.md §9`, `test_guards.py` chạy PASS | test xanh |
| 1 | `pipeline_demo.py` + CLI chạy 1 file → in ra độ dài score. **Đo thời gian thật** | khớp ước tính ~15 s/giờ |
| 2 | Log in + Database rỗng + footer | so với `UI/A0c`, `A0a` |
| 3 | Create new → upload → Process → subject hiện lên bảng | so với `UI/A1a–A2b`, `A4a` |
| 4 | Analysis: Panel EEG + toolbar + scrub (chưa có event) | so với `UI/B1a`, `B1b`, `B1d` |
| 5 | Mini-timeline + Panel Event + đồng bộ 3 panel | so với `UI/B2a–B2d` |
| 6 | Select Range tạo event thủ công | so với `UI/B3a–B3c` |
| 7 | Panel Attribution | so với `UI/B2a` |
| 8 | Export `.txt` | so với `UI/Annotaiton (format_ ID-summary.txt).png` |
| 9 | Dựng cache 8 subject + chọn subject cho kịch bản upload live | có số đo |

**Bước 1 phải xong trước bước 2.** Nếu pipeline label-free ra kết quả vô lý (vd không có event nào ở mọi
subject), phải phát hiện lúc này — không phải sau khi đã dựng 8 màn giao diện.

---

## 7 · Quy trình làm việc với Claude Code

**Tự chạy trong phạm vi 1 bước, dừng giữa các bước.** Trong 1 bước ở §6, Claude Code tự làm hết các việc
nhỏ (tạo file, sửa, chạy thử, tự sửa lỗi) không hỏi từng dòng. Xong 1 bước thì **dừng**, để Boti mở app
thật so với ảnh mock rồi mới sang bước kế.

Lý do chọn nhịp này: chạy tự do hết cả app rồi mới xem thì 1 hiểu nhầm nhỏ ở đầu sẽ lặp xuyên suốt 9 bước;
hỏi xin phép từng bước nhỏ thì quá chậm, phí sức tự động hóa. Mức tự chủ này chỉnh được nếu thấy chưa hợp.

**Boti giữ quyền quyết định cuối** ở mọi lựa chọn thực chất, đúng như quy ước của cả project.

---

## 8 · Rủi ro đã biết

| Rủi ro | Xử lý |
|---|---|
| Pipeline label-free ra kết quả khác xa thesis (quá nhiều/quá ít event) | Phát hiện ở **bước 1**, trước khi dựng UI. Nếu lệch quá mức, điều chỉnh **operating point** (label-free, hợp lệ) — **không** đụng mô hình, **không** dùng nhãn để chỉnh |
| Bước Process 17 file mất ~6 phút lúc demo trực tiếp | Chọn subject ít file cho kịch bản live; cache sẵn phần còn lại |
| Hội đồng hỏi vì sao số demo khác report | Câu trả lời soạn sẵn trong `SZSCAN_SPEC_v5.md §1.4` |
| Vô tình rò ground-truth vào demo | `test_guards.py` chặn ở CI/local, xem `CLAUDE.md` |
| Thời gian: report 15/10, IELTS 09/10 | **Report là ưu tiên 1.** Nếu phải cắt, cắt theo thứ tự ngược từ bước 8 → 6. Bốn bước 0–5 là bản demo tối thiểu vẫn bảo vệ được |

---

*Hết DEMO_BUILD_HANDOFF.md.*
