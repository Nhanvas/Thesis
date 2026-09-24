diff --git a/web_demo/DEMO_BUILD_HANDOFF.md b/web_demo/DEMO_BUILD_HANDOFF.md
index cc58002..1ee08fd 100644
--- a/web_demo/DEMO_BUILD_HANDOFF.md
+++ b/web_demo/DEMO_BUILD_HANDOFF.md
@@ -1,171 +1,178 @@
-# DEMO_BUILD_HANDOFF.md — kế hoạch build SzScan
+# DEMO_BUILD_HANDOFF.md — SzScan build plan
 
-**Trạng thái: KHÓA để bắt đầu code.** File này gom stack, cấu trúc thư mục, quy trình làm việc và cách xử
-lý code cũ. Hấp thu hoàn toàn `WEB_DEMO_CODE_MIGRATION_NOTES.md` (→ `docs/archive/demo_v4/`).
+**Status: LOCKED to start coding.** This file collects the stack, folder structure, working process, and
+how to handle legacy code. Fully absorbs `WEB_DEMO_CODE_MIGRATION_NOTES.md` (→ `docs/archive/demo_v4/`).
 
-Hành vi/logic: `SZSCAN_SPEC_v5.md`. Thị giác: `SZSCAN_DESIGN_v2.md`. Ảnh chốt: `UI/`.
+Behavior/logic: `SZSCAN_SPEC_v5.md`. Visuals: `SZSCAN_DESIGN_v2.md`. Locked mockups: `UI/`.
 
 ---
 
-## 1 · Stack — tất cả miễn phí
+## 1 · Stack — all free
 
-| Lớp | Chọn | Lý do |
+| Layer | Choice | Reason |
 |---|---|---|
-| Backend | **Python + FastAPI** | Bắt buộc Python: inference thật dùng torch/torch_geometric, không viết lại bằng JS được. FastAPI nhẹ, ít boilerplate |
-| Lưu review | **SQLite** (1 file `.db`) | Có sẵn trong Python, không cần cài gì, đủ cho demo 1 người dùng |
-| Frontend | **React + Vite + Tailwind** | Token trong `SZSCAN_DESIGN_v2.md §9` map thẳng sang Tailwind config, gần như copy-paste |
-| Vẽ waveform | **Canvas tự viết** | Thư viện chart thông thường (recharts…) giật khi vẽ 18 kênh × hàng nghìn điểm. Phải render tay |
-| Font | Inter + IBM Plex Mono | Google Fonts, miễn phí. **Tải về đóng gói cùng app**, không load qua CDN (bảo vệ có thể không có mạng) |
-| Chạy lúc bảo vệ | 1 lệnh khởi động, chạy hoàn toàn local, **không cần internet** | Loại rủi ro mạng/deploy |
+| Backend | **Python + FastAPI** | Python is mandatory: real inference uses torch/torch_geometric, can't be rewritten in JS. FastAPI is lightweight, low boilerplate |
+| Review storage | **SQLite** (1 `.db` file) | Built into Python, nothing to install, enough for a single-user demo |
+| Frontend | **React + Vite + Tailwind** | Tokens in `SZSCAN_DESIGN_v2.md §9` map straight onto the Tailwind config, almost copy-paste |
+| Waveform rendering | **Hand-written Canvas** | Ordinary chart libraries (recharts…) stutter when drawing 18 channels × thousands of points. Must render by hand |
+| Font | Inter + IBM Plex Mono | Google Fonts, free. **Downloaded and bundled with the app**, not loaded via CDN (the defense venue may have no internet) |
+| Running at the defense | 1 start command, runs entirely locally, **no internet needed** | Eliminates network/deploy risk |
 
-**Không dùng Figma MCP.** File `.fig` có layer thật, nhưng Dev Mode MCP thuộc gói trả phí và không cần
-thiết: toàn bộ hex/spacing đã được đo trực tiếp từ PNG và ghi trong `SZSCAN_DESIGN_v2.md`. Nếu về sau cần
-thêm số đo, hai đường miễn phí: đọc pixel từ PNG, hoặc mở Figma bấm Inspect chép tay.
+**No Figma MCP.** The `.fig` file has real layers, but Dev Mode MCP is a paid tier and isn't needed: every
+hex/spacing value has already been measured directly from the PNGs and recorded in `SZSCAN_DESIGN_v2.md`.
+If more measurements are needed later, two free routes: read pixels from the PNG, or open Figma and copy
+values by hand via Inspect.
 
-**Máy chạy demo = máy dev.** Không cần đóng gói portable/installer.
+**The demo machine = the dev machine.** No need to package a portable build/installer.
 
 ---
 
-## 2 · Cấu trúc thư mục
+## 2 · Folder structure
 
-Dùng **chung repo** `F:/Study/Thesis/Code` — vì demo tái sử dụng đúng các module single-source
-(`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `edf_index.py`, `edf_order.py`) mà không
-được copy/nhân bản. Đây cũng là 1 sản phẩm hoàn chỉnh nên nên nằm cùng chỗ.
+Uses the **same repo**, `F:/Study/Thesis/Code` — because the demo reuses the exact single-source modules
+(`cpd_pipeline_v14.py`, `ensemble_recipe.py`, `gae_joint.py`, `edf_index.py`, `edf_order.py`), which must
+not be copied/duplicated. This is also a complete product in its own right, so it should live in the same
+place.
 
 ```
 web_demo/
-├── CLAUDE.md                  # rule cho Claude Code (đọc trước khi code)
-├── SZSCAN_SPEC_v5.md          # hành vi/logic/ranh giới dữ liệu
-├── SZSCAN_DESIGN_v2.md        # token thị giác
-├── DEMO_BUILD_HANDOFF.md      # file này
-├── PROJECT2_SETUP.md          # cách dựng Claude project #2 + danh sách file upload
-├── UI/                        # PNG bản chốt + UI (figma).fig  ← THAM CHIẾU BẮT BUỘC
-├── backend/                   # Claude Code tạo
+├── CLAUDE.md                  # rules for Claude Code (read before coding)
+├── SZSCAN_SPEC_v5.md          # behavior/logic/data boundaries
+├── SZSCAN_DESIGN_v2.md        # visual tokens
+├── DEMO_BUILD_HANDOFF.md      # this file
+├── PROJECT2_SETUP.md          # how to set up Claude project #2 + upload file list
+├── UI/                        # locked PNGs + UI (figma).fig  ← MANDATORY REFERENCE
+├── backend/                   # created by Claude Code
 │   ├── main.py                # FastAPI app
-│   ├── pipeline_demo.py       # ★ đường label-free liên tục (code MỚI, xem §4)
-│   ├── db.py                  # SQLite schema + truy vấn
-│   ├── export_txt.py          # sinh file export theo SPEC §7
-│   ├── .env.example           # ADMIN_USER / ADMIN_PASS (file .env thật KHÔNG commit)
+│   ├── pipeline_demo.py       # ★ continuous label-free path (NEW code, see §4)
+│   ├── db.py                  # SQLite schema + queries
+│   ├── export_txt.py          # generates the export file per SPEC §7
+│   ├── .env.example           # ADMIN_USER / ADMIN_PASS (the real .env file is NOT committed)
 │   └── tests/
-│       └── test_guards.py     # ★ test liêm chính, xem CLAUDE.md
-├── frontend/                  # Claude Code tạo
-└── cache/                     # output pipeline demo tính sẵn (gitignore)
+│       └── test_guards.py     # ★ integrity tests, see CLAUDE.md
+├── frontend/                  # created by Claude Code
+└── cache/                     # precomputed demo-pipeline output (gitignored)
 ```
 
-`web_demo/backend/` và `web_demo/frontend/` **không tồn tại** cho tới khi bắt đầu code — Claude Code tạo.
+`web_demo/backend/` and `web_demo/frontend/` **do not exist** until coding starts — Claude Code creates
+them.
 
 ---
 
-## 3 · Xử lý code cũ
+## 3 · Handling legacy code
 
-| File | Hành động | Lý do |
+| File | Action | Reason |
 |---|---|---|
-| `edf_index.py` | **KHÔNG tồn tại, KHÔNG cần viết lại** | Thuộc kiến trúc v3 và đã bị xóa khỏi repo. Kiến trúc v5 suy offset từng file theo cấu tạo — xem `SZSCAN_SPEC_v5.md` §1.5. Tài liệu cũ `WEB_DEMO_CODE_MIGRATION_NOTES.md` mô tả nó như module sẵn có; tài liệu đó đã archive |
-| `web_demo/backend/edf_order.py` | **Giữ nguyên hoàn toàn** | Vấn đề độc lập: thứ tự **hiển thị** file trên UI (theo giờ thật trong header EDF) khác thứ tự **xử lý** (theo TÊN FILE — quy ước khóa để khớp kết quả thesis). Có case lệch thật như `chb03_24/25`. Chuyển từ `docs/demo/` sang đây 2026-09-03; demo-only, không dùng chung với thesis |
-| `src/cpd_pipeline_v14.py`, `ensemble_recipe.py`, `szcore_eval.py`, `retrain/gae_joint.py` | **Chỉ đọc, không sửa** | Single-source dùng chung với thesis |
-| `src/szcore_eval.build_timeline_masked()` | **CẤM gọi từ demo** | Cần ground-truth — xem `SZSCAN_SPEC_v5.md` §1.2 |
+| `edf_index.py` | **Does NOT exist, does NOT need to be rewritten** | Belonged to the v3 architecture and has been deleted from the repo. The v5 architecture derives each file's offset by construction — see `SZSCAN_SPEC_v5.md` §1.5. The old `WEB_DEMO_CODE_MIGRATION_NOTES.md` describes it as an available module; that document has been archived |
+| `web_demo/backend/edf_order.py` | **Keep entirely unchanged** | Independent concern: the **display** order of files in the UI (by the real time in the EDF header) differs from the **processing** order (by FILE NAME — the locked convention needed to match the thesis results). There are real mismatch cases like `chb03_24/25`. Moved from `docs/demo/` to here on 2026-09-03; demo-only, not shared with the thesis |
+| `src/cpd_pipeline_v14.py`, `ensemble_recipe.py`, `szcore_eval.py`, `retrain/gae_joint.py` | **Read-only, do not edit** | Single-source, shared with the thesis |
+| `src/szcore_eval.build_timeline_masked()` | **FORBIDDEN to call from the demo** | Requires ground truth — see `SZSCAN_SPEC_v5.md` §1.2 |
 
-Đừng gộp hai vấn đề: "event này thuộc file nào" (offset tích lũy, `SZSCAN_SPEC_v5.md` §1.5) và
-"file này hiện ở vị trí thứ mấy trên UI" (`edf_order.py`).
+Don't conflate the two concerns: "which file does this event belong to" (cumulative offset,
+`SZSCAN_SPEC_v5.md` §1.5) and "what position does this file show at in the UI" (`edf_order.py`).
 
-⚠️ **Trước khi lấy tham số từ `src/retrain/fp_budget_operating_point.py`**, kiểm tra chuỗi import chạy
-được — `evaluation_protocol.py` và `stat_validation.py` từng bị archive nhầm và mới khôi phục về `src/`
-ngày 2026-09-03 (tag `repo-deps-fixed`, chi tiết `docs/REPO_MAP.md` §7.7).
+⚠️ **Before pulling parameters from `src/retrain/fp_budget_operating_point.py`**, check that the import
+chain actually runs — `evaluation_protocol.py` and `stat_validation.py` were mistakenly archived once and
+were only restored to `src/` on 2026-09-03 (tag `repo-deps-fixed`, details in `docs/REPO_MAP.md` §7.7).
 
 ---
 
-## 4 · `pipeline_demo.py` — phần code mới, là lõi của demo
+## 4 · `pipeline_demo.py` — the new code, the core of the demo
 
-Chưa có module nào trong repo làm việc này. Đây là **anh em song sinh label-free** của đường thesis,
-**không được ghi đè** bất kỳ module nào trong `src/`.
+No module in the repo does this yet. This is the **label-free twin** of the thesis path, and it must
+**never overwrite** any module in `src/`.
 
 ```
-# giai đoạn 1 — chạy ngay khi 1 file upload xong
-def process_file(edf_path) -> np.ndarray:      # ensemble score liên tục theo thời gian
-    đọc 18 kênh chuẩn (bỏ EKG/EOG/Ref)
+# stage 1 — runs as soon as 1 file finishes uploading
+def process_file(edf_path) -> np.ndarray:      # continuous ensemble score over time
+    read the 18 standard channels (drop EKG/EOG/Ref)
     bandpass 0.5–60 + notch 60
-    cắt window 4 s, KHÔNG bỏ window nào        # ⇒ t_giây = idx * 4, ánh xạ 1-1
-    z-score per-channel, stats fit trên TOÀN BỘ window của subject
+    cut into 4 s windows, do NOT drop any window     # ⇒ t_seconds = idx * 4, exact 1-1 mapping
+    z-score per-channel, stats fit on the subject's ENTIRE set of windows
     CAR → wPLI + AEC → top-k 20% → node feat [adj-row 18 | band-power 5]
     GAE seed42 forward → zrecon, Z
-    zlatent = Mahalanobis(Z, LedoitWolf fit trên TOÀN BỘ Z)
-    zgamma  = gamma-AEC (bản liên tục — xem O5 trong SPEC §8)
-    robust-z từng nhánh → ensemble equal 1/3
-    return score            # dài đúng bằng số window của file
+    zlatent = Mahalanobis(Z, LedoitWolf fit on the ENTIRE Z)
+    zgamma  = gamma-AEC (continuous version — see O5 in SPEC §8)
+    robust-z per branch → equal-weight 1/3 ensemble
+    return score            # length exactly equals the file's window count
 
-# giai đoạn 2 — chạy khi bấm "Process"
+# stage 2 — runs when "Process" is clicked
 def process_subject(files) -> dict[file -> list[Event]]:
-    files_sorted = sort theo TÊN FILE          # KHÔNG phải thứ tự hiển thị
+    files_sorted = sort by FILE NAME          # NOT display order
     global_score = concat([score[f] for f in files_sorted])
     events_global = cpd_pipeline_v14.detect_events(global_score, ...)   # label-free
-    op = operating point FP-budget (đọc tham số từ file, xem SPEC §8 O1)
-    offsets = cộng dồn len(score[f]) theo files_sorted     # không cần module tra cứu
+    op = FP-budget operating point (read the parameter from file, see SPEC §8 O1)
+    offsets = cumulative sum of len(score[f]) over files_sorted     # no lookup module needed
     for ev in events_global:
-        file = f sao cho offsets[f] <= ev.onset_win < offsets[f] + len(score[f])
-        gán ev vào danh sách event của file đó, onset cục bộ = ev.onset_win - offsets[file]
+        file = f such that offsets[f] <= ev.onset_win < offsets[f] + len(score[f])
+        assign ev to that file's event list, local onset = ev.onset_win - offsets[file]
 ```
 
-**Bốn chỗ fit khác pipeline thesis** — đã ghi và biện minh trong `SZSCAN_SPEC_v5.md §1.6`. Đọc trước khi
-viết, đừng suy luận lại từ đầu.
+**Four places where fitting differs from the thesis pipeline** — recorded and justified in
+`SZSCAN_SPEC_v5.md §1.6`. Read before writing, don't re-derive it from scratch.
 
 ---
 
-## 5 · Waveform — lưu ý kỹ thuật quan trọng
+## 5 · Waveform — important technical note
 
-18 kênh × 256 Hz × 1 giờ = **16.6 triệu điểm/file**. Không gửi thẳng xuống trình duyệt.
+18 channels × 256 Hz × 1 hour = **16.6 million points/file**. Do not send this straight to the browser.
 
-- Backend phục vụ waveform theo **cửa sổ thời gian đang xem**, đã **decimate** xuống ~2–4 điểm/pixel
-  (min/max envelope, không phải lấy mẫu thưa — lấy mẫu thưa làm mất gai nhọn, mà gai nhọn chính là thứ
-  bác sĩ cần thấy).
-- Đổi độ dài cửa sổ (`⊲▷ [X] hr`) → gọi lại backend với mức decimate khác.
-- Đổi biên độ (`⇕ [X] uV`) → **thuần frontend**, chỉ scale lại, không gọi backend.
-- Bật/tắt filter → backend trả **cả 2 chuỗi** (raw + filtered) trong 1 lần gọi, frontend tự chồng lớp.
+- The backend serves the waveform for the **currently viewed time window**, **decimated** down to
+  ~2–4 points/pixel (min/max envelope, not naive subsampling — subsampling would lose sharp spikes, and
+  spikes are exactly what the clinician needs to see).
+- Changing the window length (`⊲▷ [X] hr`) → calls the backend again with a different decimation level.
+- Changing the amplitude (`⇕ [X] uV`) → **frontend-only**, just rescales, no backend call.
+- Toggling the filter → the backend returns **both series** (raw + filtered) in one call, the frontend
+  layers them itself.
 
 ---
 
-## 6 · Thứ tự build — dựng xong màn nào chốt màn đó
+## 6 · Build order — lock each screen once it's built
 
-| # | Bước | Xong khi |
+| # | Step | Done when |
 |---|---|---|
-| 0 | Khung repo, token Tailwind từ `SZSCAN_DESIGN_v2.md §9`, `test_guards.py` chạy PASS | test xanh |
-| 1 | `pipeline_demo.py` + CLI chạy 1 file → in ra độ dài score. **Đo thời gian thật** | khớp ước tính ~15 s/giờ |
-| 2 | Log in + Database rỗng + footer | so với `UI/A0c`, `A0a` |
-| 3 | Create new → upload → Process → subject hiện lên bảng | so với `UI/A1a–A2b`, `A4a` |
-| 4 | Analysis: Panel EEG + toolbar + scrub (chưa có event) | so với `UI/B1a`, `B1b`, `B1d` |
-| 5 | Mini-timeline + Panel Event + đồng bộ 3 panel | so với `UI/B2a–B2d` |
-| 6 | Select Range tạo event thủ công | so với `UI/B3a–B3c` |
-| 7 | Panel Attribution | so với `UI/B2a` |
-| 8 | Export `.txt` | so với `UI/Annotaiton (format_ ID-summary.txt).png` |
-| 9 | Dựng cache 8 subject + chọn subject cho kịch bản upload live | có số đo |
-
-**Bước 1 phải xong trước bước 2.** Nếu pipeline label-free ra kết quả vô lý (vd không có event nào ở mọi
-subject), phải phát hiện lúc này — không phải sau khi đã dựng 8 màn giao diện.
+| 0 | Repo scaffold, Tailwind tokens from `SZSCAN_DESIGN_v2.md §9`, `test_guards.py` passing | tests green |
+| 1 | `pipeline_demo.py` + CLI runs on 1 file → prints the score length. **Measure real timing** | matches the ~15 s/hour estimate |
+| 2 | Log in + empty Database + footer | compare against `UI/A0c`, `A0a` |
+| 3 | Create new → upload → Process → subject appears in the table | compare against `UI/A1a–A2b`, `A4a` |
+| 4 | Analysis: EEG Panel + toolbar + scrub (no events yet) | compare against `UI/B1a`, `B1b`, `B1d` |
+| 5 | Mini-timeline + Event Panel + 3-panel sync | compare against `UI/B2a–B2d` |
+| 6 | Select Range creates a manual event | compare against `UI/B3a–B3c` |
+| 7 | Attribution Panel | compare against `UI/B2a` |
+| 8 | Export `.txt` | compare against `UI/Annotaiton (format_ ID-summary.txt).png` |
+| 9 | Build cache for 8 subjects + pick the subject for the live-upload scenario | have the measurements |
+
+**Step 1 must finish before step 2.** If the label-free pipeline produces nonsensical results (e.g. zero
+events for every subject), it must be caught now — not after 8 UI screens have already been built.
 
 ---
 
-## 7 · Quy trình làm việc với Claude Code
+## 7 · Working process with Claude Code
 
-**Tự chạy trong phạm vi 1 bước, dừng giữa các bước.** Trong 1 bước ở §6, Claude Code tự làm hết các việc
-nhỏ (tạo file, sửa, chạy thử, tự sửa lỗi) không hỏi từng dòng. Xong 1 bước thì **dừng**, để Boti mở app
-thật so với ảnh mock rồi mới sang bước kế.
+**Run autonomously within one step, stop between steps.** Within one step from §6, Claude Code does all
+the small work itself (creating files, editing, test-running, fixing its own errors) without asking
+line-by-line. Once a step is done, **stop**, so Boti can open the real app and compare it against the
+mockups before moving to the next step.
 
-Lý do chọn nhịp này: chạy tự do hết cả app rồi mới xem thì 1 hiểu nhầm nhỏ ở đầu sẽ lặp xuyên suốt 9 bước;
-hỏi xin phép từng bước nhỏ thì quá chậm, phí sức tự động hóa. Mức tự chủ này chỉnh được nếu thấy chưa hợp.
+Reason for this pace: running the whole app freely and only reviewing it at the end means one small
+early misunderstanding repeats across all 9 steps; asking permission at every small step is too slow and
+wastes the point of automation. This level of autonomy is adjustable if it doesn't feel right.
 
-**Boti giữ quyền quyết định cuối** ở mọi lựa chọn thực chất, đúng như quy ước của cả project.
+**Boti holds final decision-making authority** on every substantive choice, per the project's overall
+convention.
 
 ---
 
-## 8 · Rủi ro đã biết
+## 8 · Known risks
 
-| Rủi ro | Xử lý |
+| Risk | Handling |
 |---|---|
-| Pipeline label-free ra kết quả khác xa thesis (quá nhiều/quá ít event) | Phát hiện ở **bước 1**, trước khi dựng UI. Nếu lệch quá mức, điều chỉnh **operating point** (label-free, hợp lệ) — **không** đụng mô hình, **không** dùng nhãn để chỉnh |
-| Bước Process 17 file mất ~6 phút lúc demo trực tiếp | Chọn subject ít file cho kịch bản live; cache sẵn phần còn lại |
-| Hội đồng hỏi vì sao số demo khác report | Câu trả lời soạn sẵn trong `SZSCAN_SPEC_v5.md §1.6` |
-| Vô tình rò ground-truth vào demo | `test_guards.py` chặn ở CI/local, xem `CLAUDE.md` |
-| Thời gian: report 15/10, IELTS 09/10 | **Report là ưu tiên 1.** Nếu phải cắt, cắt theo thứ tự ngược từ bước 8 → 6. Bốn bước 0–5 là bản demo tối thiểu vẫn bảo vệ được |
+| Label-free pipeline produces results far from the thesis (too many/too few events) | Caught at **step 1**, before building the UI. If the deviation is too large, adjust the **operating point** (label-free, legitimate) — **do not** touch the model, **do not** use labels to adjust |
+| Processing 17 files takes ~6 minutes during a live demo | Pick a subject with few files for the live scenario; pre-cache the rest |
+| Committee asks why the demo's numbers differ from the report | Prepared answer in `SZSCAN_SPEC_v5.md §1.6` |
+| Ground truth accidentally leaks into the demo | `test_guards.py` blocks it in CI/local, see `CLAUDE.md` |
+| Timeline: report due 15 Oct, IELTS 09 Oct | **The report is priority 1.** If something must be cut, cut backward from step 8 → 6. Steps 0–5 are the minimum demo that's still defensible |
 
 ---
 
-*Hết DEMO_BUILD_HANDOFF.md.*
+*End of DEMO_BUILD_HANDOFF.md.*
diff --git a/web_demo/SZSCAN_DESIGN_v2.md b/web_demo/SZSCAN_DESIGN_v2.md
index 4a95af4..75e6cc2 100644
--- a/web_demo/SZSCAN_DESIGN_v2.md
+++ b/web_demo/SZSCAN_DESIGN_v2.md
@@ -1,206 +1,211 @@
-# SZSCAN_DESIGN_v2.md — hệ thống thị giác (bản chốt để build)
+# SZSCAN_DESIGN_v2.md — visual system (locked for build)
 
-**Trạng thái: KHÓA.** Thay thế hoàn toàn `WEB_DEMO_DESIGN_SYSTEM.md` (v1 → `docs/archive/demo_v4/`).
+**Status: LOCKED.** Fully replaces `WEB_DEMO_DESIGN_SYSTEM.md` (v1 → `docs/archive/demo_v4/`).
 
-**Thẩm quyền:** `UI/` (PNG bản chốt) thắng file này về mọi thứ nhìn thấy được. File này ghi lại **giá trị
-đo được** từ chính bộ PNG đó + các quy tắc ngữ nghĩa mà ảnh tĩnh không thể hiện được.
-`SZSCAN_SPEC_v5.md` thắng về hành vi/logic.
+**Authority:** `UI/` (locked PNGs) wins over this file on everything visible. This file records
+**measured values** from those exact PNGs plus semantic rules that a static image can't express.
+`SZSCAN_SPEC_v5.md` wins on behavior/logic.
 
-**Nguồn giá trị:** các hex dưới đây được **đọc trực tiếp bằng pixel sampling từ PNG bản chốt**
-(2026-09-03), không phải đoán bằng mắt và không kế thừa từ v1. Chỗ nào v1 khác với ảnh, **ảnh thắng** và
-được ghi chú rõ.
+**Source of values:** the hex codes below were **read directly by pixel-sampling the locked PNGs**
+(2026-09-03), not eyeballed and not inherited from v1. Wherever v1 differs from the image, **the image
+wins**, and this is clearly noted.
 
 ---
 
-## 0 · Nguyên tắc
+## 0 · Principles
 
-1. **EEG là nội dung trung tâm.** Chrome không cạnh tranh với waveform.
-2. **Ba trục thông tin độc lập, không trộn:** nguồn gốc event (AI/Human) · review status
-   (Accept/Reject/Uncertain/Unseen) · trạng thái tương tác (đang chọn/playhead).
-3. **Không truyền đạt ý nghĩa chỉ bằng màu.** Luôn kèm text/icon — quan trọng cho colorblind và cho máy
-   chiếu (máy chiếu làm lệch màu).
-4. **Không over-claim bằng màu.** Alert chưa review **không** mặc định đỏ. Đỏ chỉ dành cho review status
-   `Reject` và lỗi hệ thống.
-5. **Attribution không dùng thang nhiệt đỏ.** Đó là interpretability, không phải mức độ nguy hiểm/SOZ.
+1. **EEG is the central content.** Chrome never competes with the waveform.
+2. **Three independent information axes, never mixed:** event source (AI/Human) · review status
+   (Accept/Reject/Uncertain/Unseen) · interaction state (selected/playhead).
+3. **Never convey meaning through color alone.** Always paired with text/icon — important for
+   colorblindness and for projectors (projectors shift colors).
+4. **Never over-claim through color.** An unreviewed alert is **not** red by default. Red is reserved
+   for `Reject` review status and system errors.
+5. **Attribution never uses a red heat scale.** It's interpretability, not a danger/SOZ level.
 
 ---
 
-## 1 · Token nền & thương hiệu (đo từ PNG)
+## 1 · Background & brand tokens (measured from the PNGs)
 
-| Vai trò | Hex | Ghi chú |
+| Role | Hex | Note |
 |---|---|---|
-| Header gradient | `#624C8A` → `#10182B` | trái sang phải, dùng ở cả Log in / Database / Analysis |
-| Brand violet (nút primary) | `#776399` | ⚠ **khác v1** — v1 ghi `#7C3AED`, ảnh thật muted hơn hẳn |
-| Nền trang | `#FFFFFF` | ⚠ **khác v1** — v1 ghi `#F8FAFC` |
-| Canvas EEG | `#FEFBEF` | **token mới**, nền kem kiểu máy đọc EEG |
-| Footer bar | `#0F172A` | chữ trắng, disclaimer thường trực |
+| Header gradient | `#624C8A` → `#10182B` | left to right, used on Log in / Database / Analysis alike |
+| Brand violet (primary button) | `#776399` | ⚠ **differs from v1** — v1 recorded `#7C3AED`; the real image is noticeably more muted |
+| Page background | `#FFFFFF` | ⚠ **differs from v1** — v1 recorded `#F8FAFC` |
+| EEG canvas | `#FEFBEF` | **new token**, cream background in the style of an EEG reader |
+| Footer bar | `#0F172A` | white text, persistent disclaimer |
 | Surface (card/panel/table) | `#FFFFFF` | |
-| Border | `#E2E8F0` | viền card, divider |
-| Border strong | `#CBD5E1` | grid chính |
+| Border | `#E2E8F0` | card border, divider |
+| Border strong | `#CBD5E1` | main grid |
 | Text primary | `#0F172A` | |
 | Text secondary | `#475569` | |
 | Text muted | `#64748B` | hint, empty-state |
 
-### Violet có HAI vai trò tách biệt — đọc kỹ
+### Violet has TWO separate roles — read carefully
 
-v1 quy định violet **chỉ** mang nghĩa "đang tương tác". UI thật dùng violet cho cả header và nút primary.
-Chốt: **tách thành 2 vai trò, không nhập nhằng vì chúng không bao giờ xuất hiện cùng ngữ cảnh.**
+v1 specified that violet **only** meant "currently interacting." The real UI uses violet for both the
+header and the primary button. Decision: **split it into 2 roles, with no ambiguity because they never
+appear in the same context.**
 
-| Vai trò | Màu | Xuất hiện ở |
+| Role | Color | Appears in |
 |---|---|---|
-| **Chrome / brand** | `#776399`, header gradient | Ngoài canvas nội dung: header, nút Create new / Save / Log in |
-| **Tương tác** | violet bão hòa hơn, dùng cho playhead + viền "đang chọn" | Trong canvas nội dung: playhead, viền event đang chọn, channel đang hover |
+| **Chrome / brand** | `#776399`, header gradient | Outside the content canvas: header, Create new / Save / Log in buttons |
+| **Interaction** | more saturated violet, used for the playhead + "selected" outline | Inside the content canvas: playhead, selected-event outline, hovered channel on Attribution |
 
-**Blue `#2563EB` giữ độc quyền cho một nghĩa duy nhất: event nguồn Human.** Không dùng blue cho nút.
+**Blue `#2563EB` is reserved exclusively for one meaning: Human-sourced events.** Never used for buttons.
 
 ---
 
-## 2 · Event & review status (3 trục)
+## 2 · Event & review status (3 axes)
 
-### Trục 1 — nguồn gốc
+### Axis 1 — source
 
-| Nguồn | Hex | Icon |
+| Source | Hex | Icon |
 |---|---|---|
-| AI-detected | `#334155` charcoal | icon "AI" |
-| Human-added | `#2563EB` blue | icon người |
+| AI-detected | `#334155` charcoal | "AI" icon |
+| Human-added | `#2563EB` blue | person icon |
 
-### Trục 2 — review status (chỉ áp cho event AI)
+### Axis 2 — review status (applies only to AI events)
 
-| Status | Màu | Nền nhạt |
+| Status | Color | Light background |
 |---|---|---|
 | Accept | `#16A34A` | `#F0FDF4` |
 | Reject | `#DC2626` | `#FEF2F2` |
 | Uncertain | `#D97706` | `#FFFBEB` |
 | Unseen | `#94A3B8` | `#F8FAFC` |
 
-### Trục 3 — tương tác
+### Axis 3 — interaction
 
-Playhead · viền event đang chọn · channel đang hover trên Attribution → **violet bão hòa**.
+Playhead · selected-event outline · hovered channel on Attribution → **saturated violet**.
 
-**Quy tắc kết hợp:** 1 event AI đã Accept = thanh dọc trái xanh lá (status) + icon "AI" (nguồn) + nền card
-xanh lá rất nhạt. Nếu đang được chọn thì **thêm** viền violet, **không thay thế** thanh dọc. Ba trục luôn
-hiển thị đồng thời, không trục nào ghi đè trục nào.
+**Combination rule:** an Accepted AI event = a green left vertical bar (status) + an "AI" icon (source) +
+a very light green card background. If it's currently selected, a violet outline is **added**, **not
+replacing** the vertical bar. All three axes always display simultaneously; no axis overrides another.
 
-**Trên Event Panel:** thanh dọc ~4–5 px cạnh trái mỗi dòng. Nền dòng chỉ tô rất nhạt, tránh "loang lổ".
+**On the Event Panel:** a ~4–5 px vertical bar on the left edge of each row. The row background is only
+tinted very lightly, avoiding a "blotchy" look.
 
-**Trên mini-timeline và hàng Event Time:** AI chưa review = charcoal đặc · Human = blue đặc ·
-Accept = green opacity ~75 % · Reject = red opacity ~55 % + gạch chéo nhẹ (để không chỉ dựa vào màu) ·
-Uncertain = amber opacity ~75 % · đang chọn = thêm viền violet, không đổi màu nền gốc.
+**On the mini-timeline and the Event Time row:** unreviewed AI = solid charcoal · Human = solid blue ·
+Accept = green at ~75% opacity · Reject = red at ~55% opacity + a light diagonal hatch (so it's never
+color-only) · Uncertain = amber at ~75% opacity · selected = adds a violet outline, does not change the
+underlying background color.
 
-**Khi đang xem 1 event:** các event khác giảm còn opacity ~40 % (không đổi màu), event đang chọn giữ
-nguyên độ đậm + viền violet.
+**While one event is being viewed:** other events drop to ~40% opacity (color unchanged); the selected
+event keeps full intensity + the violet outline.
 
 ---
 
 ## 3 · EEG waveform
 
-| Đối tượng | Giá trị |
+| Object | Value |
 |---|---|
-| Nền canvas | `#FEFBEF` |
-| Raw EEG (filter tắt, hoặc làm nền khi filter bật) | `#64748B`, opacity 50 % |
-| Filtered EEG (nổi bật khi bật lff/hff/60) | `#0F172A`, opacity 100 % |
-| Grid phụ | `#E2E8F0` |
-| Grid chính | `#CBD5E1` |
+| Canvas background | `#FEFBEF` |
+| Raw EEG (filter off, or as background when filter is on) | `#64748B`, 50% opacity |
+| Filtered EEG (highlighted when lff/hff/60 is on) | `#0F172A`, 100% opacity |
+| Minor grid | `#E2E8F0` |
+| Major grid | `#CBD5E1` |
 | Playhead | violet |
-| Overlay nền event AI | `#334155`, opacity 8–10 % |
-| Overlay nền event Human | `#2563EB`, opacity 8–10 % |
+| AI event background overlay | `#334155`, 8–10% opacity |
+| Human event background overlay | `#2563EB`, 8–10% opacity |
 
-**Không dùng:** màu đỏ cho waveform bất thường (không có ngưỡng lâm sàng nào biện minh) · màu riêng cho
-từng kênh trong 18 kênh (rainbow gây khó đọc, không thêm thông tin) · gradient mạnh trong waveform ·
-nền đen toàn trang.
+**Not used:** red for an abnormal waveform (no clinical threshold justifies it) · a separate color per
+channel across the 18 channels (a rainbow hurts legibility and adds no information) · strong gradients
+inside the waveform · a full-page black background.
 
 ---
 
-## 4 · Channel Attribution — thang teal
+## 4 · Channel Attribution — teal scale
 
-| Mức | Hex | Ghi chú |
+| Level | Hex | Note |
 |---|---|---|
-| Thấp | `#CBD5E1` | slate trung tính |
-| Trung bình | `#2DD4BF` | teal-400 |
-| Cao | `#0F766E` | teal-700 |
-| Đang hover/chọn | violet | |
-| Channel đã Reject | giữ đường, opacity ~35 % hoặc nét đứt | |
-
-Colorbar trên đầu người: `linear-gradient(to right, #CBD5E1, #2DD4BF, #0F766E)`.
-
-**Vì sao teal, và vì sao chỉ 3 mốc:**
-- Không dùng **đỏ-vàng-xanh lá**: ngụ ý mức độ nguy hiểm/SOZ — sai bản chất, attribution là
-  interpretability (`docs/ATTRIBUTION_SPEC.md`).
-- Không dùng **blue**: chìm trên nền trắng, và blue đã có chủ (event Human).
-- Không dùng **tím**: sẽ đụng trực tiếp với "đang hover" — một channel điểm cao sẽ không phân biệt được
-  với channel đang được hover.
-- Teal là hue duy nhất trong bảng màu hiện tại **chưa bị gán nghĩa nào**.
-- 3 mốc là đủ cho biểu diễn bằng đường mảnh; nhiều mốc hơn thì mắt không phân biệt được.
-
-**Interaction 2 chiều** (hover dòng bảng → sáng đường tương ứng và ngược lại): tăng UX, **không bắt buộc**.
-Bỏ được nếu gấp thời gian.
+| Low | `#CBD5E1` | neutral slate |
+| Medium | `#2DD4BF` | teal-400 |
+| High | `#0F766E` | teal-700 |
+| Hovered/selected | violet | |
+| Rejected channel | keeps its line, ~35% opacity or dashed | |
+
+Colorbar over the head diagram: `linear-gradient(to right, #CBD5E1, #2DD4BF, #0F766E)`.
+
+**Why teal, and why only 3 levels:**
+- Not **red-yellow-green**: implies a danger level/SOZ — wrong nature, attribution is interpretability
+  (`docs/ATTRIBUTION_SPEC.md`).
+- Not **blue**: gets lost on a white background, and blue already has an owner (Human events).
+- Not **purple**: would clash directly with "hovered" — a high-scoring channel would be indistinguishable
+  from a hovered channel.
+- Teal is the only hue in the current palette **not yet assigned a meaning**.
+- 3 levels are enough for a thin-line representation; more levels would be indistinguishable to the eye.
+
+**Two-way interaction** (hovering a table row → highlights the matching line and vice versa): improves
+UX, **not required**. Can be dropped if time is tight.
 
 ---
 
 ## 5 · Database
 
-| Thành phần | Style |
+| Component | Style |
 |---|---|
-| Header bảng | nền `#F1F5F9` |
-| Row mặc định / hover | trắng / `#F8FAFC` |
-| Row đang chọn | nền `#EFF6FF`, viền trái blue |
-| Dòng subject | `font-weight: 600` |
-| Dòng file con | thụt lề nhẹ, text secondary |
+| Table header | `#F1F5F9` background |
+| Default / hover row | white / `#F8FAFC` |
+| Selected row | `#EFF6FF` background, blue left border |
+| Subject row | `font-weight: 600` |
+| Child file row | slightly indented, secondary text |
 
-**Status badge:** `View` → chữ `#475569`, icon vòng tròn rỗng · `Viewing (x/N)` → `#B45309`, icon nửa đầy
-· `Viewed` → `#15803D`, icon check.
+**Status badge:** `View` → text `#475569`, empty-circle icon · `Viewing (x/N)` → `#B45309`, half-filled
+icon · `Viewed` → `#15803D`, check icon.
 
-**Alert:** hiển thị **màu chữ trung tính** (`#0F172A`), không amber, không đỏ.
-⚠ **Khác v1** — v1 quy định amber khi > 0. Ảnh thật để đen trơn; rule cũ sinh ra để cấm **đỏ**, và đen
-trung tính đã thỏa mục đích đó, đồng thời tránh nhiễu khi mọi dòng đều amber.
+**Alert:** shown in **neutral text color** (`#0F172A`), no amber, no red.
+⚠ **Differs from v1** — v1 specified amber when > 0. The real image keeps it plain black; the old rule
+existed to ban **red**, and neutral black already serves that purpose while also avoiding noise from
+every row being amber.
 
 ---
 
 ## 6 · Typography
 
-| Vai trò | Font |
+| Role | Font |
 |---|---|
-| UI chung (label, button, table) | Inter |
-| Dữ liệu kỹ thuật (tên file, tên kênh, timestamp, score) | IBM Plex Mono |
+| General UI (label, button, table) | Inter |
+| Technical data (file name, channel name, timestamp, score) | IBM Plex Mono |
 
-Monospace cho dữ liệu kỹ thuật là **bắt buộc**: bảng số liệu phải thẳng hàng, và `FP1-F7` vs `FP1-F3`
-không được nhìn nhầm. Cả hai font đều miễn phí trên Google Fonts.
+Monospace for technical data is **mandatory**: numeric tables must line up, and `FP1-F7` vs `FP1-F3`
+must never be misread. Both fonts are free on Google Fonts.
 
-**Cỡ chữ:** page title 20–24 · section title 15–16 · body 13–14 · table 12–13 · timestamp 12 ·
+**Font size:** page title 20–24 · section title 15–16 · body 13–14 · table 12–13 · timestamp 12 ·
 button 13–14 · badge 11–12 (px).
 
 ---
 
 ## 7 · Spacing
 
-Bội số 4 px. Page padding 24 · khoảng cách giữa panel 16 · panel padding 16–20 · khoảng cách nhóm toolbar
-12–16 · chiều cao dòng event 48–56 · dòng event đã mở rộng 140–180.
+Multiples of 4 px. Page padding 24 · gap between panels 16 · panel padding 16–20 · toolbar group gap
+12–16 · event row height 48–56 · expanded event row 140–180.
 
-Màn Analysis **được phép dài và cuộn dọc**. Không ép mọi panel vừa 1 viewport; ưu tiên khoảng thở.
+The Analysis screen **is allowed to be long and scroll vertically**. Don't force every panel to fit one
+viewport; prioritize breathing room.
 
 ---
 
-## 8 · Wording — bảng tra nhanh (chống over-claim)
+## 8 · Wording — quick-reference table (anti-overclaiming)
 
-| Tình huống | Dùng | KHÔNG dùng |
+| Situation | Use | Do NOT use |
 |---|---|---|
-| File không có event AI nào | `No detected events in this file. You can still add an event manually with Select Range.` | `No seizure detected` |
-| Event AI chưa review | badge `Unseen`, màu trung tính | màu đỏ |
-| Đang chạy Process | `Processing subject — combining files and detecting change points...` | % giả |
-| Upload file lỗi | `File rejected — unsupported format or channel configuration.` | `Upload failed` |
-| Subject ngoài allowlist | `This demo is restricted to the held-out test subjects.` | im lặng bỏ qua |
-| Tiêu đề panel Attribution | `Channel-level reconstruction anomaly — Event N` | `Channel contribute to ...` |
-| Nhãn block trên hàng Event Time | `Event N` | `seizure N` |
-| Hàng thứ 2 mini-timeline | `Detections` | `Seizure Detections` |
-| Footer mọi màn (trừ Log in) | `SzScan is an AI-assisted tool designed to support clinicians, not replace them.` | — |
+| File has no AI events at all | `No detected events in this file. You can still add an event manually with Select Range.` | `No seizure detected` |
+| Unreviewed AI event | `Unseen` badge, neutral color | red color |
+| Process running | `Processing subject — combining files and detecting change points...` | fake % |
+| Upload file error | `File rejected — unsupported format or channel configuration.` | `Upload failed` |
+| Subject outside the allowlist | `This demo is restricted to the held-out test subjects.` | silently ignore |
+| Attribution panel title | `Channel-level reconstruction anomaly — Event N` | `Channel contribute to ...` |
+| Block label on the Event Time row | `Event N` | `seizure N` |
+| Mini-timeline row 2 | `Detections` | `Seizure Detections` |
+| Footer on every screen (except Log in) | `SzScan is an AI-assisted tool designed to support clinicians, not replace them.` | — |
 
 ---
 
-## 9 · Design tokens — điểm khởi đầu khi code
+## 9 · Design tokens — starting point for code
 
 ```css
 :root {
-  /* nền & chrome */
+  /* background & chrome */
   --color-bg:              #FFFFFF;
   --color-surface:         #FFFFFF;
   --color-eeg-canvas:      #FEFBEF;
@@ -209,16 +214,16 @@ Màn Analysis **được phép dài và cuộn dọc**. Không ép mọi panel v
   --color-border-strong:   #CBD5E1;
 
   --header-gradient:       linear-gradient(90deg, #624C8A 0%, #10182B 100%);
-  --color-brand:           #776399;   /* chrome: header, nút primary */
-  --color-interaction:     #7C3AED;   /* playhead + đang chọn (chỉ trong canvas nội dung) */
+  --color-brand:           #776399;   /* chrome: header, primary button */
+  --color-interaction:     #7C3AED;   /* playhead + selected (content canvas only) */
 
   --color-text:            #0F172A;
   --color-text-secondary:  #475569;
   --color-text-muted:      #64748B;
 
-  /* nguồn gốc event */
+  /* event source */
   --color-ai:              #334155;
-  --color-human:           #2563EB;   /* độc quyền cho event Human, KHÔNG dùng cho nút */
+  --color-human:           #2563EB;   /* exclusive to Human events, NOT used for buttons */
 
   /* review status */
   --color-accept:          #16A34A;  --color-accept-bg:    #F0FDF4;
@@ -249,20 +254,20 @@ Màn Analysis **được phép dài và cuộn dọc**. Không ép mọi panel v
 
 ---
 
-## 10 · Những gì đã đổi so với v1 (để không dùng nhầm)
+## 10 · What changed from v1 (so it's not used by mistake)
 
-| Hạng mục | v1 | v2 (file này) | Vì sao |
+| Item | v1 | v2 (this file) | Why |
 |---|---|---|---|
-| Nền trang | `#F8FAFC` | `#FFFFFF` | đo từ ảnh chốt |
-| Nút primary | blue `#2563EB` | violet `#776399` | đo từ ảnh chốt |
-| Nền canvas EEG | (không có token) | `#FEFBEF` | đo từ ảnh chốt; kem là quy ước máy đọc EEG, tương phản tốt hơn cho nét sẫm |
-| Vai trò violet | chỉ "đang tương tác" | tách chrome / tương tác | ảnh dùng violet làm brand; hai vai trò không cùng ngữ cảnh nên không nhập nhằng |
-| Attribution | blue nhạt → blue đậm | teal 3 mốc | blue chìm trên nền trắng + blue đã có chủ |
-| Alert | amber khi > 0 | trung tính | ảnh chốt; rule cũ chỉ nhằm cấm đỏ |
-| Trục Y Detection Score | auto-scale P1–P99 (có số) | auto-scale P1–P99, **không hiện số**, chỉ zero-line | ô nhỏ, vai trò nhìn nhanh; z-score không có ý nghĩa tuyệt đối để đọc số |
-| Header | (không mô tả) | gradient `#624C8A → #10182B` | đo từ ảnh chốt |
-| Footer | (không có) | bar `#0F172A` thường trực | quyết định minh bạch của tác giả |
+| Page background | `#F8FAFC` | `#FFFFFF` | measured from the locked image |
+| Primary button | blue `#2563EB` | violet `#776399` | measured from the locked image |
+| EEG canvas background | (no token) | `#FEFBEF` | measured from the locked image; cream is the EEG-reader convention, better contrast for dark strokes |
+| Violet's role | only "interacting" | split into chrome / interaction | the image uses violet as the brand color; the two roles never share a context, so no ambiguity |
+| Attribution | light blue → dark blue | 3-level teal | blue gets lost on white + blue already has an owner |
+| Alert | amber when > 0 | neutral | the locked image; the old rule only aimed to ban red |
+| Detection Score Y-axis | auto-scale P1–P99 (with numbers) | auto-scale P1–P99, **no numbers shown**, zero-line only | small box, quick-glance role; a z-score has no absolute meaning worth reading a number for |
+| Header | (not described) | gradient `#624C8A → #10182B` | measured from the locked image |
+| Footer | (none) | persistent `#0F172A` bar | the author's transparency decision |
 
 ---
 
-*Hết SZSCAN_DESIGN_v2.md.*
+*End of SZSCAN_DESIGN_v2.md.*
diff --git a/web_demo/SZSCAN_SPEC_v5.md b/web_demo/SZSCAN_SPEC_v5.md
index 998cdca..8b8552d 100644
--- a/web_demo/SZSCAN_SPEC_v5.md
+++ b/web_demo/SZSCAN_SPEC_v5.md
@@ -1,492 +1,555 @@
-# SZSCAN_SPEC_v5.md — bản chốt để BUILD
+# SZSCAN_SPEC_v5.md — locked for BUILD
 
-**Trạng thái: KHÓA.** File này **thay thế hoàn toàn** `WEB_DEMO_SPEC_v4.md` và
-`WEB_DEMO_CONTEXT_BOUNDARY.md`. Hai file đó chuyển sang `docs/archive/demo_v4/`, **không dùng để code**.
+**Status: LOCKED.** This file **fully replaces** `WEB_DEMO_SPEC_v4.md` and
+`WEB_DEMO_CONTEXT_BOUNDARY.md`. Both files have moved to `docs/archive/demo_v4/`, **do not use them for
+code**.
 
-**Thứ tự thẩm quyền cho mọi việc liên quan web demo:**
-`UI/` (PNG bản chốt — thắng về mọi thứ nhìn thấy được) > file này (hành vi/logic/ranh giới) >
-`SZSCAN_DESIGN_v2.md` (token màu/chữ/khoảng cách) > `DEMO_BUILD_HANDOFF.md` (stack/quy trình).
+**Authority order for everything related to the web demo:**
+`UI/` (locked PNGs — wins on everything visible) > this file (behavior/logic/data boundaries) >
+`SZSCAN_DESIGN_v2.md` (color/type/spacing tokens) > `DEMO_BUILD_HANDOFF.md` (stack/process).
 
-Với các quyết định khoa học (không phải demo), thẩm quyền vẫn là
+For scientific decisions (not demo ones), authority remains
 `docs/RESULTS_OF_RECORD_phaseB.md` > `docs/PROVENANCE.md` > `docs/REPO_MAP.md`.
 
-**Lịch sử:** v5 = v4 + 11 điểm chốt UI (phiên audit 2026-09) + 13 điểm sửa M1–M13 (phiên này) +
-kiến trúc label-free liên tục (mới, dựa trên phép đo — xem §1) + **C17** (2026-09, sau audit report:
-cột Start date đổi từ ngày tuyệt đối sang `Recording N, HH:MM:SS` — xem §5.1).
+**History:** v5 = v4 + 11 UI lock-in points (2026-09 audit session) + 13 fix points M1–M13 (this
+session) + continuous label-free architecture (new, measurement-based — see §1) + **C17** (2026-09,
+after the audit report: the Start date column changed from an absolute date to `Recording N,
+HH:MM:SS` — see §5.1) + **C18** (2026-09-21, after Step 5 fix round 2: the Panel EEG amplitude scale
+extended per real measured data — see §6.4).
 
 ---
 
-## 0 · SCOPE VÀ FRAMING
+## 0 · SCOPE AND FRAMING
 
-Đây là **demo phục vụ bảo vệ thesis**, không phải sản phẩm lâm sàng. Framing bắt buộc:
-**post-hoc EEG review triage** — hỗ trợ bác sĩ rà lại bản ghi đã có, **KHÔNG phải cảnh báo real-time**.
+This is a **thesis-defense demo**, not a clinical product. Mandatory framing: **post-hoc EEG review
+triage** — supports a clinician reviewing a recording they already have, **NOT a real-time alarm**.
 
-Nguyên tắc chống dàn dựng: không thêm bất kỳ thuật toán/bước xử lý nào không có trong pipeline thật.
-Thà thiếu 1 nút còn hơn có 1 nút không phản ánh gì thật.
+Anti-staging principle: never add any algorithm/processing step that isn't in the real pipeline. Better
+to be missing a button than to have a button that reflects nothing real.
 
-**Guardrail chống over-claim — ĐỔI SO VỚI v4:** v4 cấm hiển thị trên UI. **Nay hiển thị thường trực**
-ở footer mọi màn hình (trừ màn Log in, là màn tiền-ứng-dụng):
+**Anti-overclaiming guardrail — CHANGED FROM v4:** v4 banned displaying this on the UI. **Now it's
+shown persistently** in the footer of every screen (except Log in, which is a pre-app screen):
 
 > `SzScan is an AI-assisted tool designed to support clinicians, not replace them.`
 
-Lý do đảo: minh bạch bằng sản phẩm tốt hơn minh bạch bằng lời, và buổi bảo vệ có thể không đủ thời gian
-để nói. (Quyết định của tác giả, 2026-09.)
+Reason for the reversal: transparency through the product beats transparency through spoken words, and
+the defense session may not have enough time to say it out loud. (Author's decision, 2026-09.)
 
-**Đăng nhập — ĐỔI SO VỚI v4:** v4 nói không cần. **Nay có** 1 màn Log in, 1 tài khoản admin cố định.
-Không có đăng ký, không quên/đổi mật khẩu. Lý do: truy cập dữ liệu bệnh nhân nên cần 1 bước chặn; đây là
-bước tượng trưng cho đúng hình hài sản phẩm, **không phải cơ chế bảo mật thật**.
+**Login — CHANGED FROM v4:** v4 said it wasn't needed. **Now there is** 1 Log in screen, 1 fixed admin
+account. No registration, no forgot/change password. Reason: accessing patient data should have 1
+blocking step; this is a symbolic step to match the product's real shape, **not a real security
+mechanism**.
 
 ---
 
-## 1 · KIẾN TRÚC XỬ LÝ — ĐỌC TRƯỚC KHI VIẾT BẤT KỲ DÒNG BACKEND NÀO
+## 1 · PROCESSING ARCHITECTURE — READ BEFORE WRITING ANY BACKEND CODE
 
-### 1.1 Vì sao không thể phát lại kết quả đã khóa của thesis
+### 1.1 Why the thesis's locked results can't be replayed
 
-Đo ngày 2026-09-03, từ chính code trong repo:
+Measured on 2026-09-03, from the actual code in the repo:
 
-| # | Sự thật đo được | Nguồn |
+| # | Measured fact | Source |
 |---|---|---|
-| F1 | `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy` là mảng **theo segment**, không theo thời gian. Không tồn tại index window→giây | liệt kê thư mục |
-| F2 | `szcore_eval.build_timeline_masked()` dựng lại timeline **bằng ground-truth annotation** — đọc `edf['seizures']` rồi đặt score ictal vào đúng vị trí nhãn | `src/szcore_eval.py:98–109` |
-| F3 | Window trong buffer 4h và window interictal thiếu được **lấp bằng bootstrap resample** từ phân phối interictal — giá trị tổng hợp, không phải score thật tại vị trí đó | `src/szcore_eval.py:90, 111–113, 120–123` |
-| F4 | `preprocessing.py` Step 4 **loại** window vượt ±5 SD khỏi `{subj}_interictal.npy`; con trỏ `inter_ptr` chạy tuần tự → score interictal thật **trôi vị trí thời gian** đúng bằng `n_rejected` | `preprocessing.py` Step 4 + `szcore_eval.py:117–119` |
+| F1 | `results/phaseB/tier2/ens_test_tf/rlg/ens_seed42_{subj}_{inter,ictal}.npy` is an array **by segment**, not by time. No window→second index exists | directory listing |
+| F2 | `szcore_eval.build_timeline_masked()` rebuilds the timeline **using ground-truth annotation** — reads `edf['seizures']` then places the ictal score at exactly the label's position | `src/szcore_eval.py:98–109` |
+| F3 | Windows inside the 4h buffer and missing interictal windows are **filled by bootstrap resampling** from the interictal distribution — a synthetic value, not the real score at that position | `src/szcore_eval.py:90, 111–113, 120–123` |
+| F4 | `preprocessing.py` Step 4 **discards** windows beyond ±5 SD from `{subj}_interictal.npy`; the `inter_ptr` pointer runs sequentially → the real interictal score's **time position drifts** by exactly `n_rejected` | `preprocessing.py` Step 4 + `szcore_eval.py:117–119` |
 
-**Hệ quả:** thông tin vị trí thời gian đã mất từ bước preprocessing. Không có cách khôi phục bằng code
-thêm. Mọi phương án "cache kết quả thesis rồi vẽ lên trục thời gian" đều **sai về mặt dữ liệu**.
+**Consequence:** time-position information was already lost at the preprocessing step. There is no way
+to recover it with more code. Every "cache the thesis result then draw it on a time axis" approach is
+**wrong at the data level**.
 
-### 1.2 Điều cấm tuyệt đối
+### 1.2 Absolute prohibitions
 
-**Demo KHÔNG ĐƯỢC:**
-1. gọi `szcore_eval.build_timeline_masked()` hoặc bất kỳ hàm nào dựng timeline từ nhãn;
-2. đọc trường `seizures` / `Seizure Start Time` / `Seizure End Time` từ `chb*-summary.md` lúc runtime;
-3. dùng `{subj}_interictal.npy` / `{subj}_ictal.npy` (hai mảng này được tách **bằng nhãn**);
-4. ghi vào `results/`, `data/models_retrain/`, `docs/`, hay bất kỳ artifact khóa nào của thesis.
+**The demo MUST NOT:**
+1. call `szcore_eval.build_timeline_masked()` or any function that builds a timeline from labels;
+2. read the `seizures` / `Seizure Start Time` / `Seizure End Time` fields from `chb*-summary.md` at
+   runtime;
+3. use `{subj}_interictal.npy` / `{subj}_ictal.npy` (these two arrays were split **using labels**);
+4. write to `results/`, `data/models_retrain/`, `docs/`, or any locked thesis artifact.
 
-Điểm 1–3 không phải quy ước phong cách. Vi phạm = rò ground-truth vào một sản phẩm được giới thiệu là
-label-free. Đó là lỗi liêm chính, và là câu hỏi đầu tiên một hội đồng tinh ý sẽ hỏi.
+Points 1–3 are not a style convention. Violating them = leaking ground truth into a product presented as
+label-free. That's an integrity failure, and it's the first question a sharp committee will ask.
 
-`chb*-summary.md` **vẫn được đọc** cho: danh sách file, `File Start Time`, `File End Time`, duration.
-Chỉ trường seizure là cấm.
+`chb*-summary.md` **is still readable** for: the file list, `File Start Time`, `File End Time`,
+duration. Only the seizure field is forbidden.
 
-### 1.3 Kiến trúc chốt: chạy lại thật, label-free, liên tục
+### 1.3 Locked architecture: a real, label-free, continuous re-run
 
-Demo chạy **cùng mô hình đã khóa** (`data/models_retrain/gae_joint_seed42.pt`) trên **bản ghi liên tục**,
-không tách interictal/ictal, không loại window, không dùng nhãn ở bất kỳ đâu.
+The demo runs the **same locked model** (`data/models_retrain/gae_joint_seed42.pt`) on the **continuous
+recording**, with no interictal/ictal split, no windows dropped, no labels used anywhere.
 
 ```
-file .edf
- → đọc 18 kênh chuẩn (bỏ EKG/EOG/Ref nếu file gốc có)
- → bandpass 0.5–60 Hz + notch 60 Hz          (giống thesis)
- → cắt window 4 s không chồng lấn @256 Hz    (giống thesis, KHÔNG bỏ window nào)
- → z-score per-channel                        (⚠ xem §1.6)
+.edf file
+ → read the 18 standard channels (drop EKG/EOG/Ref if the original file has them)
+ → bandpass 0.5–60 Hz + notch 60 Hz          (same as the thesis)
+ → cut into 4 s non-overlapping windows @256 Hz  (same as the thesis, do NOT drop any window)
+ → z-score per-channel                        (⚠ see §1.6)
  → CAR → wPLI + AEC → top-k 20%
- → band-powers 5 dải → node feat [adj-row 18 | bp 5]
- → Joint GAE seed42 → zrecon + zlatent(⚠ §1.6) ; gamma-AEC → zgamma
- → robust-z từng nhánh (⚠ §1.6) → ensemble equal 1/3
- → [ghép mọi file của subject theo thứ tự TÊN FILE]
- → PELT (cpd_pipeline_v14) chạy MỘT lần trên timeline ghép
- → operating point label-free (FP-budget)
- → gán event global về đúng file bằng offset tích lũy (§1.5)
+ → 5-band band-powers → node feat [adj-row 18 | bp 5]
+ → Joint GAE seed42 → zrecon + zlatent (⚠ §1.6) ; gamma-AEC → zgamma
+ → robust-z per branch (⚠ §1.6) → equal-weight 1/3 ensemble
+ → [concatenate every file of the subject, sorted by FILE NAME]
+ → PELT (cpd_pipeline_v14) runs ONCE on the concatenated timeline
+ → label-free operating point (FP-budget)
+ → assign each global event back to its file via cumulative offset (§1.5)
 ```
 
-**Không có window nào bị bỏ** ⇒ chỉ số window ↔ giây trong file là ánh xạ 1-1 tuyệt đối:
-`t_giây = window_index × 4`. Đây chính là thứ mà đường xử lý của thesis đã đánh mất.
+**No window is ever dropped** ⇒ window index ↔ seconds within a file is an exact 1-1 mapping:
+`t_seconds = window_index × 4`. This is exactly what the thesis's processing path lost.
 
-### 1.5 Gán event về file — không cần module tra cứu
+### 1.5 Assigning events back to files — no lookup module needed
 
-Vì mảng score của mỗi file có độ dài **đúng bằng số window của chính file đó**, offset của từng file
-suy ra được **theo cấu tạo**:
+Because each file's score array has a length **exactly equal to that file's own window count**, each
+file's offset can be derived **by construction**:
 
 ```python
 offsets, cur = {}, 0
 for f in files_sorted_by_name:
     offsets[f] = cur
     cur += len(score[f])
-# event global (on, off) thuộc file f khi  offsets[f] <= on < offsets[f] + len(score[f])
-# offset cục bộ = on - offsets[f]
+# a global event (on, off) belongs to file f when  offsets[f] <= on < offsets[f] + len(score[f])
+# local offset = on - offsets[f]
 ```
 
-Không parse file nào, không đọc summary, không cần module phụ — **và điều này tự động thỏa guard số 2
-ở §1.2**, vì không còn đọc `chb*-summary.md` lúc chạy.
+No file is parsed, no summary is read, no extra module is needed — **and this automatically satisfies
+guard #2 in §1.2**, because it never reads `chb*-summary.md` at runtime.
 
-⚠️ **`edf_index.py` không tồn tại trong repo và không cần viết lại.** Nó thuộc kiến trúc v3 (khi score
-là mảng theo segment nên phải dựng bảng tra `global_offset → file`) và đã bị xóa. Tài liệu cũ
-`WEB_DEMO_CODE_MIGRATION_NOTES.md` mô tả nó như module sẵn có — tài liệu đó đã archive, đừng dùng.
-`edf_order.py` thì **vẫn giữ** (`web_demo/backend/edf_order.py`): vấn đề khác hẳn — thứ tự **hiển thị**
-file trên UI theo giờ thật trong header EDF, khác thứ tự **xử lý** theo tên file. **Lưu ý (2026-09,
-Step 3):** trên thực tế, thứ tự xử lý (§1.5, theo tên file) và thứ tự hiển thị "Recording N" ở §5.1 nay
-đều lấy trực tiếp từ `raw.info['meas_date']` (ngày giờ đầy đủ trong header EDF) thay vì heuristic của
-`edf_order.py` — file đó vẫn còn trong repo, không sửa, nhưng không còn nằm trong luồng gọi thực tế
-nữa, vì `meas_date` giải quyết đúng gốc vấn đề (case chb03_24/25) mà không cần heuristic hoán đổi.
+⚠️ **`edf_index.py` does not exist in the repo and does not need to be rewritten.** It belonged to the
+v3 architecture (when the score was a segment-indexed array, so a `global_offset → file` lookup table
+was required) and has been deleted. The old `WEB_DEMO_CODE_MIGRATION_NOTES.md` describes it as an
+available module — that document has been archived, don't use it.
+`edf_order.py` **is still kept** (`web_demo/backend/edf_order.py`): a completely different concern — the
+**display** order of files in the UI, by the real time in the EDF header, differs from the **processing**
+order, by file name. **Note (2026-09, Step 3):** in practice, both the processing order (§1.5, by file
+name) and the "Recording N" display order in §5.1 now read directly from `raw.info['meas_date']` (the
+full date-time in the EDF header) instead of `edf_order.py`'s heuristic — that file is still in the repo,
+unmodified, but is no longer in the actual call path, because `meas_date` solves the underlying problem
+(the chb03_24/25 case) directly, without needing the swap heuristic.
 
-### 1.6 Divergence có chủ đích khỏi pipeline thesis — ĐÃ ĐƯỢC TÁC GIẢ DUYỆT
+### 1.6 Deliberate divergence from the thesis pipeline — APPROVED BY THE AUTHOR
 
-Có **hai nhóm divergence**, cùng một nguyên nhân gốc: bệnh nhân mới không có nhãn.
+There are **two divergence groups**, sharing the same root cause: a new patient has no labels.
 
-#### (a) Bốn bước fit trên "mảng interictal"
+#### (a) Four steps that fit on the "interictal array"
 
-Bệnh nhân mới không có mảng đó. Demo fit cả bốn trên **toàn bộ window của subject**:
+A new patient has no such array. The demo fits all four on the subject's **entire set of windows**:
 
-| Bước | Thesis fit trên | Demo fit trên |
+| Step | Thesis fits on | Demo fits on |
 |---|---|---|
-| z-score stats (mean/std per channel) | interictal | toàn bộ window |
-| ngưỡng artifact 5 SD | interictal | **bỏ hẳn** (không loại window nào — cần giữ vị trí thời gian) |
-| `LedoitWolf().fit(Zi)` cho `zlatent` | latent của interictal | latent của toàn bộ window |
-| ~~robust-z median/MAD từng nhánh~~ | **toàn bộ window** | **toàn bộ window** — *không phải divergence* |
+| z-score stats (mean/std per channel) | interictal | entire window set |
+| 5 SD artifact threshold | interictal | **dropped entirely** (no window discarded — time position must be preserved) |
+| `LedoitWolf().fit(Zi)` for `zlatent` | interictal's latent | the entire window set's latent |
+| ~~robust-z median/MAD per branch~~ | **entire window set** | **entire window set** — *not a divergence* |
 
-**robust-z không phải divergence.** `retrain_io.robust_z(raw_i, raw_c)` dòng 56–60 đã fit median/MAD
-trên `np.concatenate([raw_i, raw_c])` — tức toàn bộ window. Demo làm y hệt thesis. Bảng trên giữ dòng này
-gạch ngang để phiên sau không đi kiểm tra lại.
+**robust-z is not a divergence.** `retrain_io.robust_z(raw_i, raw_c)` lines 56–60 already fit median/MAD
+on `np.concatenate([raw_i, raw_c])` — i.e. the entire window set. The demo does exactly what the thesis
+does. This row is kept struck through in the table above so a future session doesn't go re-check it.
 
-**Biện minh:** tỷ lệ window ictal cực thấp — đo trên chb06: 45 / (19826 + 45) = **0.23 %**. Không đủ để
-kéo lệch covariance, median hay MAD một cách có ý nghĩa.
+**Justification:** the fraction of ictal windows is extremely low — measured on chb06: 45 / (19826 +
+45) = **0.23%**. Not enough to meaningfully skew the covariance, median, or MAD.
 
-**ĐÃ KIỂM CHỨNG BẰNG PHÉP ĐO — 2026-09-03. Không cần chạy lại.**
+**VERIFIED BY MEASUREMENT — 2026-09-03. No need to rerun.**
 
-Tiêu chí đặt trước khi chạy: PASS nếu Spearman ≥ 0.98 **và** |ΔAUROC| ≤ 0.02 trên cả hai subject.
+Criterion set before running: PASS if Spearman ≥ 0.98 **and** |ΔAUROC| ≤ 0.02 on both subjects.
 
-| subject | AUROC (fit interictal — thesis) | AUROC (fit toàn bộ — demo) | Spearman | n_int / n_ict |
+| subject | AUROC (fit on interictal — thesis) | AUROC (fit on entire set — demo) | Spearman | n_int / n_ict |
 |---|---|---|---|---|
 | chb06 | 0.6066 | 0.6051 | **1.0000** | 19826 / 45 |
 | chb13 | 0.6493 | 0.6408 | **0.9999** | 12452 / 144 |
 
-→ **PASS.** Đổi cách fit LedoitWolf gần như không làm đổi `zlatent` (thứ hạng gần như đồng nhất,
-ΔAUROC 0.0015 / 0.0085). Divergence (a) là vô hại về mặt đo lường.
-
-⚠️ Phép đo này **chỉ** phủ `zlatent`. Ba thứ còn lại — z-score stats, bỏ lọc artifact, và **hậu-cơn (b)**
-— cần tiền xử lý liên tục từ EDF nên chỉ quan sát được ở bước 1 của thứ tự build.
-
-#### (b) Đoạn hậu-cơn không bị loại — nguồn khác biệt LỚN HƠN nhóm (a)
-
-`preprocessing.py` loại **4 giờ sau mỗi cơn** khỏi mảng interictal của thesis (`BUFFER_H`). Demo không
-biết cơn ở đâu nên **không loại được gì** — toàn bộ đoạn hậu-cơn đi thẳng qua PELT.
-
-EEG hậu-cơn bất thường thật (chậm khu trú, suy giảm biên độ, kết nối chức năng thay đổi). Nhiều khả năng
-demo sẽ **gắn cờ các đoạn đó**, trong khi thesis chưa từng chấm điểm chúng.
-
-Về lượng, đây là nguồn khác biệt lớn hơn hẳn nhóm (a): 4 giờ × số cơn, so với 0.23 % window ictal.
-
-**Đây không phải lỗi.** Trong khung post-hoc review triage, đưa đoạn hậu-cơn ra cho bác sĩ xem là hành vi
-hợp lý về lâm sàng — bác sĩ vẫn muốn nhìn đoạn đó. Nhưng nó phải được:
-1. **quan sát ở bước 1** của thứ tự build (chạy 1 subject, xem event rơi vào đâu so với cơn đã biết —
-   *chỉ để mắt người kiểm tra tính hợp lý, tuyệt đối không đưa nhãn vào code*);
-2. **nói ra khi bảo vệ**, không để hội đồng tự phát hiện.
-
-**Hệ quả bắt buộc ghi nhận (cho cả (a) và (b)):**
-- **Số của demo sẽ KHÁC số của thesis.** Không được ép khớp, không được điều chỉnh gì để khớp.
-- Demo **không** hiển thị bất kỳ metric đánh giá nào (sensitivity, FP/day, AUROC, operating point
-  mag_pct/pen_mult). Những con số đó thuộc thesis, không thuộc sản phẩm.
-- Divergence này phải được **báo cô** (Assoc. Prof. Hà Thị Thanh Hương) vì là quyết định phương pháp.
-
-**Câu trả lời chuẩn bị sẵn cho hội đồng** — *"tại sao demo tìm ra event khác bảng trong report?"*:
-> Report đánh giá trên phân đoạn interictal đã lọc nhiễu, đã loại 4 giờ hậu-cơn, và có nhãn, theo giao
-> thức SzCORE. Demo chạy hoàn toàn không nhãn trên bản ghi liên tục nguyên vẹn — kể cả đoạn hậu-cơn —
-> vì đó mới là tình huống của một bệnh nhân mới. Cùng một mô hình, cùng trọng số, hai điều kiện đầu vào
-> khác nhau, nên hai tập kết quả không đồng nhất là đúng như dự kiến, không phải bất thường. Cụ thể,
-> demo có thể gắn cờ đoạn hậu-cơn mà report không hề chấm điểm; trong bối cảnh rà soát hậu kỳ thì đó là
-> hành vi hợp lý, không phải dương tính giả.
-
-### 1.7 Chi phí — đã đo, quyết định chạy live
-
-Đo trên máy dev (Dell Latitude 3590, CPU): `build_adjacency` **13.2 ms/window** + `compute_band_powers`
-**3.7 ms/window** = **16.9 ms/window** → **~15 s cho 1 giờ EEG** (chưa kể đọc EDF, gamma-AEC, GAE
-forward — đều nhỏ hơn nhiều).
-
-**Chốt:**
-- Upload → chạy pipeline **thật**, không giả lập, không replay. Mâu thuẫn "nửa cache / nửa live" của v4
-  biến mất: cả hai nửa đều thật.
-- Vẫn dựng **cache trước cho 8 subject** nhưng chỉ làm **bảo hiểm** lúc bảo vệ (máy trục trặc / hội đồng
-  không muốn chờ). Cache chứa output thật của chính pipeline demo, chỉ là tính sớm.
-- Khớp cache **bằng tên file** (không checksum) — phạm vi 8 subject cố định đã biết trước.
-- Bước "Process" (PELT toàn subject) là chỗ tốn thời gian nhất. Kịch bản demo trực tiếp nên chọn subject
-  **ít file nhất**; con số cụ thể đo lúc dựng cache.
+→ **PASS.** Changing how LedoitWolf is fit barely changes `zlatent` (rank order is nearly identical,
+ΔAUROC 0.0015 / 0.0085). Divergence (a) is measurement-harmless.
+
+⚠️ This measurement **only** covers `zlatent`. The other three — z-score stats, dropping artifact
+filtering, and **the post-ictal segment (b)** — need continuous preprocessing straight from the EDF, so
+they can only be observed at build step 1.
+
+#### (b) The post-ictal segment isn't excluded — a source of divergence LARGER than group (a)
+
+`preprocessing.py` excludes **4 hours after every seizure** from the thesis's interictal array
+(`BUFFER_H`). The demo doesn't know where a seizure is, so it **can't exclude anything** — the entire
+post-ictal segment goes straight through PELT.
+
+Post-ictal EEG is genuinely abnormal (focal slowing, amplitude suppression, altered functional
+connectivity). The demo is quite likely to **flag those segments**, while the thesis never scored them
+at all.
+
+In magnitude, this is a much larger source of difference than group (a): 4 hours × the number of
+seizures, compared with 0.23% of windows for ictal.
+
+**This is not a bug.** Within the post-hoc review triage framing, surfacing the post-ictal segment for a
+clinician to see is clinically reasonable behavior — a clinician would still want to see it. But it must
+be:
+1. **observed at build step 1** (run 1 subject, see where events land relative to known seizures —
+   *purely a human sanity check by eye, absolutely no labels going into the code*);
+2. **stated out loud at the defense**, not left for the committee to discover on its own.
+
+**Mandatory consequences to record (for both (a) and (b)):**
+- **The demo's numbers WILL differ from the thesis's numbers.** They must never be forced to match,
+  never adjusted to match.
+- The demo **does not** display any evaluation metric (sensitivity, FP/day, AUROC, operating-point
+  mag_pct/pen_mult). Those numbers belong to the thesis, not the product.
+- This divergence must be **reported to the advisor** (Assoc. Prof. Hà Thị Thanh Hương) because it's a
+  methodological decision.
+
+**Prepared answer for the committee** — *"why does the demo find different events than the table in the
+report?"*:
+> The report evaluates on an interictal segment that has been noise-filtered, has the 4-hour post-ictal
+> window excluded, and has labels, following the SzCORE protocol. The demo runs completely label-free on
+> the intact continuous recording — including the post-ictal segment — because that's what a new
+> patient's situation actually looks like. Same model, same weights, two different input conditions, so
+> the two result sets not matching is expected, not anomalous. Specifically, the demo may flag the
+> post-ictal segment that the report never scored at all; within a post-hoc review framing, that's
+> reasonable behavior, not a false positive.
+
+### 1.7 Cost — measured, decided to run live
+
+Measured on the dev machine (Dell Latitude 3590, CPU): `build_adjacency` **13.2 ms/window** +
+`compute_band_powers` **3.7 ms/window** = **16.9 ms/window** → **~15 s for 1 hour of EEG** (not counting
+EDF reading, gamma-AEC, GAE forward — all much smaller).
+
+**Decided:**
+- Upload → runs the **real** pipeline, no simulation, no replay. v4's "half cache / half live"
+  contradiction disappears: both halves are now real.
+- Still building **cache in advance for 8 subjects**, but only as **insurance** during the defense
+  (machine trouble / committee doesn't want to wait). The cache holds the real output of the demo's own
+  pipeline, just computed early.
+- Cache is matched **by file name** (not checksum) — the fixed, known-in-advance 8-subject scope makes
+  this safe.
+- The "Process" step (PELT over the whole subject) is the most time-consuming part. The live demo
+  scenario should pick the subject with **the fewest files**; the exact number is measured when building
+  the cache.
 
 ---
 
-## 2 · PHẠM VI DỮ LIỆU
+## 2 · DATA SCOPE
 
-- **Allowlist cứng 8 subject TEST:** `chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18`.
-- File thuộc subject ngoài danh sách → **từ chối**, toast:
+- **Hard allowlist of 8 TEST subjects:** `chb03, chb06, chb13, chb14, chb15, chb16, chb17, chb18`.
+- A file belonging to a subject outside the list → **rejected**, toast:
   `This demo is restricted to the held-out test subjects.`
-- **Lý do (quan trọng, không được nới):** live compute nay chạy được mọi file CHB-MIT. Nếu không chặn,
-  hội đồng upload `chb01` là demo đang chạy trên **dữ liệu huấn luyện** — tự đâm vào câu hỏi khó nhất mà
-  cả thesis đã cẩn thận tránh. Bảng mock trong `UI/A4a` có chb01/02/04… chỉ là **dữ liệu minh họa**.
-- File sai định dạng / thiếu kênh chuẩn → loại khỏi pipeline và Database, toast:
+- **Reason (important, must not be relaxed):** live compute can now run on any CHB-MIT file. Without
+  this block, the committee uploading `chb01` means the demo is running on **training data** — walking
+  straight into the hardest question the whole thesis carefully avoided. The mock table in `UI/A4a`
+  showing chb01/02/04… is **illustrative data only**.
+- A file with the wrong format / missing the standard channels → excluded from the pipeline and the
+  Database, toast:
   `File rejected — unsupported format or channel configuration.`
 
 ---
 
-## 3 · CẤU TRÚC — 3 MÀN
+## 3 · STRUCTURE — 3 SCREENS
 
-1. **Log in** — 1 tài khoản admin cố định.
-2. **Database** (trang chủ) — danh sách subject/file, tạo mới, xóa, mở.
-3. **Analysis** — xem EEG, timeline, review event, channel attribution.
+1. **Log in** — 1 fixed admin account.
+2. **Database** (home page) — subject/file list, create new, delete, open.
+3. **Analysis** — view EEG, timeline, review events, channel attribution.
 
-Không có màn thứ 4. Cả Database và Analysis dùng chung một khung website chuẩn; Analysis dài hơn và cuộn
-dọc bình thường, không phải layout đặc biệt.
+There is no 4th screen. Both Database and Analysis share one standard website shell; Analysis is just
+longer and scrolls vertically normally, not a special layout.
 
 ---
 
-## 4 · MÀN LOG IN
+## 4 · LOG IN SCREEN
 
-- 1 tài khoản duy nhất, **ID và mật khẩu đặt trong `.env` của backend** — không hardcode ở frontend
-  (devtools đọc được). Không đăng ký, không quên/đổi mật khẩu.
-- Ô mật khẩu **phải mask** (`type="password"`). Ảnh mock hiện chữ rõ chỉ để minh họa.
-- Không có footer disclaimer ở màn này (màn tiền-ứng-dụng).
-- Avatar góc phải header sau khi đăng nhập → dropdown **Log out** (xem `UI/A0b`).
-- Đây **không phải** cơ chế bảo mật thật. Không lưu gì nhạy cảm, session đơn giản là đủ.
+- A single account, **ID and password set in the backend's `.env`** — not hardcoded in the frontend
+  (readable via devtools). No registration, no forgot/change password.
+- The password field **must be masked** (`type="password"`). The mockup showing plain text is purely
+  illustrative.
+- No footer disclaimer on this screen (a pre-app screen).
+- Avatar in the header's top-right corner after login → **Log out** dropdown (see `UI/A0b`).
+- This is **not** a real security mechanism. Nothing sensitive is stored; a simple session is enough.
 
 ---
 
-## 5 · MÀN DATABASE
+## 5 · DATABASE SCREEN
 
-### 5.1 Bảng chính (dạng cây, mở rộng được)
+### 5.1 Main table (tree form, expandable)
 
-| Cột | Ý nghĩa |
+| Column | Meaning |
 |---|---|
-| ID | Tên subject (vd `chb06`), bấm ▶ mở rộng ra danh sách file .edf con |
-| No. files | Tổng số file .edf của subject |
-| Start date | **ĐỔI SO VỚI BẢN TRƯỚC — C17, 2026-09.** Hiển thị dạng `Recording N, HH:MM:SS`, **không phải ngày tuyệt đối**. N = vị trí bản ghi trong chuỗi file của subject, sắp theo `meas_date` **tăng dần** (N=1 là bản ghi sớm nhất theo giờ thật trong header EDF — đây cũng là thứ tự mà `edf_order.py`'s heuristic từng nhắm tới, nay đạt được trực tiếp và chính xác hơn nhờ `meas_date` đầy đủ ngày-giờ). HH:MM:SS = giờ trong ngày lúc bắt đầu đúng bản ghi đó, đọc từ `meas_date`. Dòng subject hiển thị **Recording 1** (bản ghi sớm nhất của subject). Dòng file con hiển thị đúng **Recording N** của chính file đó. **Tự suy ra từ header EDF**, không có ô nhập tay, không hiển thị năm/ngày tuyệt đối (xem ghi chú ngay dưới bảng này) |
-| Duration | `HH:MM:SS` nếu < 24 h, `Nd:HH:MM:SS` nếu ≥ 24 h. Subject = tổng duration mọi file; file = end − start của chính nó |
-| Alert | Tổng số event hiện có (xem §5.3) |
-| Status | `View` / `Viewing (x/N)` / `Viewed` (xem §5.2) |
-| Memo | Text tự do do người dùng nhập (giới tính/tuổi/ghi chú). **Không bao giờ được sinh tự động** từ mô hình |
-
-Dòng file con dùng cùng cấu trúc cột, riêng Status không có phân số.
-
-> **Ghi chú ngày tháng (C17):** CHB-MIT (phân phối qua PhysioNet) áp dụng phép dịch chuyển ngày tháng
-> cố định để de-identify bệnh nhân — năm/ngày ghi trong `meas_date` của header EDF **không phải ngày
-> thật**. Phép dịch là **hằng số trong phạm vi một subject**, nên thứ tự các bản ghi, giờ trong ngày mỗi
-> bản ghi bắt đầu, và khoảng cách giữa các bản ghi **vẫn chính xác** — chỉ năm/ngày tuyệt đối là không
-> có ý nghĩa và không nên xuất hiện trên màn hình. Đây là lý do cột này hiển thị `Recording N, HH:MM:SS`
-> thay vì ngày tuyệt đối: giữ đúng ba thứ người xem cần biết, bỏ đúng một thứ bịa. Quyết định này áp
-> dụng đồng nhất cho cả UI Database lẫn mọi nơi khác từng dự định hiển thị ngày tuyệt đối từ `meas_date`
-> — hiện tại không có nơi nào khác làm vậy (§6.2's định dạng thời gian ở màn Analysis vốn đã tương đối,
-> không phải ngày tuyệt đối; §7.3's export cũng chỉ ghi giờ trong ngày, không có năm).
-
-**Trong lúc 1 subject đang xử lý (upload + pipeline + CPD), subject đó KHÔNG xuất hiện trên bảng.** Chỉ
-khi toàn bộ chạy xong, dòng subject + mọi dòng file con mới hiện lên cùng lúc. Subject khác đã có từ
-trước vẫn hiển thị bình thường.
-
-### 5.2 Quy tắc Status
-
-**Cấp file:** `View` (đã xử lý xong, chờ xem) / `Viewing` (đang xem dở, tiến độ tự lưu) / `Viewed` (đã
-bấm nút "Viewed" ở màn Analysis).
-
-**Cấp subject:** `View` nếu TẤT CẢ file đều `View`; `Viewed` nếu TẤT CẢ đều `Viewed`; còn lại là
-`Viewing (x/N)` với **x = số file đã `Viewed`**, N = tổng số file. Phân số chỉ có ở cấp subject — để phân
-biệt rõ với cấp file khi nhìn bảng.
-
-### 5.3 Công thức Alert
+| ID | Subject name (e.g. `chb06`), click ▶ to expand into the list of child .edf files |
+| No. files | The subject's total number of .edf files |
+| Start date | **CHANGED FROM THE PREVIOUS VERSION — C17, 2026-09.** Displayed as `Recording N, HH:MM:SS`, **not an absolute date**. N = the recording's position within the subject's file sequence, sorted by `meas_date` **ascending** (N=1 is the earliest recording by real time in the EDF header — this is also the order `edf_order.py`'s heuristic used to aim for, now achieved directly and more accurately via the full date-time `meas_date`). HH:MM:SS = the time of day that exact recording started, read from `meas_date`. The subject row shows **Recording 1** (the subject's earliest recording). A child file row shows that file's own correct **Recording N**. **Derived automatically from the EDF header**, no manual entry field, no absolute year/date shown (see the note right below this table) |
+| Duration | `HH:MM:SS` if < 24 h, `Nd:HH:MM:SS` if ≥ 24 h. Subject = the sum of every file's duration; file = its own end − start |
+| Alert | The current total event count (see §5.3) |
+| Status | `View` / `Viewing (x/N)` / `Viewed` (see §5.2) |
+| Memo | Free text entered by the user (sex/age/notes). **Never auto-generated** by the model |
+
+A child file row uses the same column structure; only its Status has no fraction.
+
+> **Date note (C17):** CHB-MIT (distributed via PhysioNet) applies a fixed date shift to de-identify
+> patients — the year/date recorded in the EDF header's `meas_date` is **not the real date**. The shift
+> is **constant within a given subject**, so recording order, the time of day each recording starts, and
+> the gap between recordings **remain accurate** — only the absolute year/date is meaningless and
+> shouldn't appear on screen. This is why this column shows `Recording N, HH:MM:SS` instead of an
+> absolute date: it keeps exactly the three things a viewer needs to know and drops exactly the one
+> fabricated thing. This decision applies uniformly to both the Database UI and everywhere else that
+> once intended to show an absolute date from `meas_date` — currently nowhere else does that (§6.2's
+> time format on the Analysis screen is already relative, not an absolute date; §7.3's export also only
+> records the time of day, with no year).
+
+**While a subject is being processed (upload + pipeline + CPD), that subject does NOT appear in the
+table.** Only once everything has finished running does the subject row + every child file row appear
+at once. Any other subject already there beforehand still displays normally.
+
+### 5.2 Status rules
+
+**File level:** `View` (finished processing, waiting to be viewed) / `Viewing` (being viewed, progress
+auto-saved) / `Viewed` (the "Viewed" button has been clicked on the Analysis screen).
+
+**Subject level:** `View` if ALL files are `View`; `Viewed` if ALL are `Viewed`; otherwise
+`Viewing (x/N)` where **x = the number of files that are `Viewed`**, N = total file count. The fraction
+only appears at the subject level — to clearly distinguish it from the file level at a glance.
+
+### 5.3 Alert formula
 
 ```
-Alert = (số event AI-detect CHƯA bị Reject) + (số event User-added)
+Alert = (number of AI-detected events NOT YET Rejected) + (number of User-added events)
 ```
 
-- Reject 1 event AI → Alert giảm 1.
-- `Uncertain` và `Unseen` **vẫn tính** vào Alert.
-- Alert luôn phản ánh trạng thái review mới nhất, không khóa cứng theo số AI gốc.
-- Hiển thị màu trung tính (không amber, không đỏ) — xem `SZSCAN_DESIGN_v2.md`.
+- Rejecting 1 AI event → Alert drops by 1.
+- `Uncertain` and `Unseen` **still count** toward Alert.
+- Alert always reflects the latest review state; it is never locked to the original AI count.
+- Displayed in a neutral color (no amber, no red) — see `SZSCAN_DESIGN_v2.md`.
 
-### 5.4 Ô Search
+### 5.4 Search box
 
-- Lọc theo **tên file hoặc tên subject**. Gõ xong bấm **nút search** — không auto-filter theo từng ký tự.
-- Khớp tên 1 file con → bảng chỉ còn subject chứa file đó, subject **tự expand**, và **chỉ hiện file
-  khớp** (file khác của subject đó tạm ẩn; xóa search thì hiện lại đủ).
-- Khớp tên subject → hiện subject đó với đầy đủ file con, trạng thái collapsed.
-- Không khớp → khối "No data" nhưng đổi chữ thành `No results for '...'`.
-- Không phân biệt hoa/thường, cho phép khớp một phần.
+- Filters by **file name or subject name**. Type, then click the **search button** — no auto-filter per
+  keystroke.
+- Matching a child file's name → the table narrows to the subject containing it, the subject
+  **auto-expands**, and **only the matching file shows** (other files of that subject are temporarily
+  hidden; clearing the search restores all of them).
+- Matching a subject's name → shows that subject with all its child files, collapsed state.
+- No match → the "No data" block, but with the text changed to `No results for '...'`.
+- Case-insensitive, partial match allowed.
 
-### 5.5 Tạo subject mới ("Create new")
+### 5.5 Creating a new subject ("Create new")
 
-Panel overlay bên phải (`UI/A1a`):
+Right-side overlay panel (`UI/A1a`):
 - **Project ID** (text input)
 - **Memo** (text area, optional)
-- Vùng kéo-thả **Browse Files** (nét đứt) — chọn tất cả file .edf của subject cùng lúc
-- **Không có ô "Test date"** — giá trị này tự suy ra từ header EDF và chỉ xuất hiện ở cột `Start date`
-  trên bảng Database *(đổi so với v4, nơi nó còn là 1 ô trong panel)*
-- Danh sách file đã chọn hiện bên dưới, mỗi file 1 icon trạng thái:
-  - vòng tròn xoay = đang tải; **bấm ô vuông giữa vòng tròn để DỪNG** upload file đó
-  - dấu ✕ = đã tải xong (bấm để bỏ khỏi danh sách)
-- Nút đen **Process** + 1 dòng ghi chú nhỏ bên dưới. **Disabled cho tới khi mọi file đã tải xong.**
-
-**Hai giai đoạn xử lý:**
-
-1. **Ngay khi 1 file tải xong** (không đợi bấm Process): backend chạy pipeline §1.3 cho riêng file đó,
-   **dừng trước CPD**, ra 1 mảng ensemble score liên tục theo thời gian của file.
-2. **Bấm Process:** ghép ensemble score của **tất cả file theo đúng thứ tự TÊN FILE** thành 1 timeline
-   liên tục → chạy PELT **một lần duy nhất** trên toàn bộ timeline (thuật toán cần đủ nền để ước lượng
-   ổn định, không tách chạy từng file ngắn) → dùng `edf_index.locate_range()` gán mỗi event global về
-   đúng file theo vị trí thời gian.
-3. Trong lúc chạy: loading full-panel (spinner + progress bar đơn giản, **không** phân biệt 2 giai đoạn
-   con, **không** hiện % giả).
-4. Xong → Database hiện subject mới + mọi file con, Status = `View`.
-
-**Minimize giữa chừng (nút "−"):** không hủy. Thu thành toast góc dưới phải —
-`Create New (draft)` khi đang upload, `Processing...` khi đang chạy Process. Chạy tiếp ngầm, bấm toast để
-quay lại.
-
-**Giới hạn song song:** toàn hệ thống **chỉ đúng 1 subject** được xử lý tại một thời điểm, kể cả đã
-minimize. Bấm "Create new" khi đang có subject chạy → chặn, hiện thông báo yêu cầu chờ (`UI/A1d`).
-
-**Không có chế độ Edit.** Muốn sửa → xóa cả subject rồi tạo lại. Lý do: sửa buộc phải chạy lại CPD trên
-toàn timeline ghép, kéo theo mất mọi review cũ; "sửa = tạo lại" đơn giản hơn nhiều so với thiết kế cơ chế
-bảo toàn review.
-
-### 5.6 Xóa
-
-- **Chỉ xóa được cấp Subject.** Chọn dòng file con rồi bấm Delete → không phản hồi.
-- Có màn xác nhận. **Dùng chung 1 câu cho mọi trường hợp xóa** (đang xử lý dở hay đã hoàn tất) — không
-  tách 2 câu *(chốt của tác giả, khác v4)*.
-
-### 5.7 Nút khác
-
-Chọn 1 dòng → tô đậm. **Open** → sang Analysis đúng subject/file đã chọn. **Cancel** → chỉ bỏ chọn dòng.
+- Dashed drag-and-drop **Browse Files** zone — selects all of the subject's .edf files at once
+- **No "Test date" field** — this value is derived from the EDF header and only appears in the
+  `Start date` column of the Database table *(changed from v4, where it was still a field in the
+  panel)*
+- The list of selected files appears below, each with a status icon:
+  - a spinning circle = uploading; **click the square inside the circle to STOP** that file's upload
+  - an ✕ mark = finished uploading (click to remove it from the list)
+- A black **Process** button + a small note line below it. **Disabled until every file has finished
+  uploading.**
+
+**Two processing stages:**
+
+1. **As soon as 1 file finishes uploading** (not waiting for Process to be clicked): the backend runs
+   the §1.3 pipeline for that file alone, **stopping before CPD**, producing one continuous
+   time-indexed ensemble score array for the file.
+2. **Clicking Process:** concatenates every file's ensemble score, **in exact FILE NAME order**, into
+   one continuous timeline → runs PELT **exactly once** over the whole timeline (the algorithm needs
+   enough background to estimate stably, no splitting into separate short-file runs) → uses
+   `edf_index.locate_range()` to assign each global event back to its correct file by time position.
+3. While running: a full-panel loading state (spinner + a simple progress bar, **not** distinguishing
+   the 2 sub-stages, **no** fake %).
+4. Done → the Database shows the new subject + every child file, Status = `View`.
+
+**Minimizing mid-way (the "−" button):** doesn't cancel anything. Collapses to a bottom-right toast —
+`Create New (draft)` while uploading, `Processing...` while Process is running. Keeps running in the
+background, click the toast to return to it.
+
+**Concurrency limit:** system-wide, **only exactly 1 subject** may be processing at any one time, even
+minimized. Clicking "Create new" while a subject is running → blocked, shows a message asking to wait
+(`UI/A1d`).
+
+**There is no Edit mode.** To make a change → delete the whole subject and re-create it. Reason: editing
+would force CPD to rerun over the whole concatenated timeline, which loses all prior review; "edit =
+re-create" is far simpler than designing a review-preserving mechanism.
+
+### 5.6 Delete
+
+- **Only the Subject level can be deleted.** Selecting a child file row and clicking Delete → no
+  response.
+- A confirmation screen exists. **The same single sentence is used for every delete case**
+  (mid-processing or already complete) — not split into 2 messages *(the author's decision, different
+  from v4)*.
+
+### 5.7 Other buttons
+
+Selecting 1 row → highlights it. **Open** → goes to the Analysis screen for the selected subject/file.
+**Cancel** → just deselects the row.
 
 ---
 
-## 6 · MÀN ANALYSIS
+## 6 · ANALYSIS SCREEN
 
 ### 6.1 Header
 
-| Thành phần | Ý nghĩa |
+| Component | Meaning |
 |---|---|
-| `<ID> (<N> alerts to check)` | N = Alert của **file đang xem**, đồng bộ theo review mới nhất |
-| Previous / Next | Chuyển **file** trước/sau trong cùng subject (không phải chuyển event) |
-| Viewed | Đánh dấu file đang xem là `Viewed` |
-| Export | Xuất báo cáo `.txt` cho **toàn bộ subject**. **Chỉ enable khi mọi file của subject đã `Viewed`** |
-| Dropdown chọn file | Liệt kê mọi file .edf của subject, kèm số event trong ngoặc: `chb06_06.edf (2)` |
-| Progress | `x/N` = số file đã `Viewed` / tổng số file |
+| `<ID> (<N> alerts to check)` | N = the Alert of the **currently viewed file**, synced to the latest review state |
+| Previous / Next | Moves to the previous/next **file** within the same subject (not the next event) |
+| Viewed | Marks the currently viewed file as `Viewed` |
+| Export | Exports a `.txt` report for the **entire subject**. **Only enabled once every file of the subject is `Viewed`** |
+| File-select dropdown | Lists every .edf file of the subject, with the event count in parentheses: `chb06_06.edf (2)` |
+| Progress | `x/N` = number of files `Viewed` / total file count |
 
-### 6.2 Định dạng thời gian — một rule duy nhất
+### 6.2 Time format — a single rule
 
-Áp dụng **đồng bộ cho mọi trục thời gian cấp file** (mini-timeline và trục dưới Panel EEG):
+Applied **consistently to every file-level time axis** (the mini-timeline and the axis below Panel EEG):
 
-- `HH:MM:SS` nếu file < 24 h
-- `dN:HH:MM:SS` nếu ≥ 24 h
+- `HH:MM:SS` if the file is < 24 h
+- `dN:HH:MM:SS` if ≥ 24 h
 
-*(Bỏ ngoại lệ cũ của v4 "mini-timeline không bao giờ dùng dN".)* Ảnh mock hiện `d1 …` chỉ là chọn ví dụ
-minh họa cho trường hợp ≥ 24 h; `UI/B0b` minh họa trường hợp < 24 h.
+*(Removes v4's old exception, "the mini-timeline never uses dN.")* The mockup showing `d1 …` is just an
+illustrative example for the ≥ 24 h case; `UI/B0b` illustrates the < 24 h case.
 
-### 6.3 Panel Timeline (mini, trên cùng)
+### 6.3 Timeline Panel (mini, at the top)
 
-- **Chỉ hiển thị phạm vi file đang xem**, không ghép toàn subject.
-- Mặc định 1 giờ, chia 6 ô × 10 phút.
-- Hai hàng: **Seizure Detection Score** (line chart theo ensemble score) và **Detections** (block chữ
-  nhật dài/ngắn theo duration mỗi event).
-  - Tên hàng thứ nhất **không được** dùng chữ "Probability": ensemble score là robust z-score, có âm có
-    dương, không phải xác suất [0,1].
-  - Trục Y: **không hiện số** ở hai đầu. Chỉ vẽ **đường zero** + chiều cao tương đối, auto-scale theo
-    percentile P1–P99 của **chính file đang xem** (tránh 1 outlier kéo giãn trục). Lý do bỏ số: ô này
-    nhỏ, vai trò là nhìn nhanh; và z-score không có ý nghĩa lâm sàng tuyệt đối để đọc số.
-- Có playhead (▼) đồng bộ với Panel EEG.
-- **Chỉ để xem, không tương tác.** Click chỉ hoạt động trên Panel EEG.
+- **Only shows the range of the currently viewed file**, never the whole subject concatenated.
+- Default 1 hour, split into 6 cells × 10 min each.
+- Two rows: **Seizure Detection Score** (a line chart of the ensemble score) and **Detections**
+  (rectangular blocks, long/short per each event's duration).
+  - Row 1's name **must not** use the word "Probability": the ensemble score is a robust z-score, which
+    can be negative or positive, not a [0,1] probability.
+  - Y-axis: **shows no numbers** at either end. Only draws a **zero line** + relative height,
+    auto-scaled to the P1–P99 percentile of **the currently viewed file itself** (avoids one outlier
+    stretching the axis). Reason for dropping numbers: this box is small, a quick-glance role; and a
+    z-score has no absolute clinical meaning worth reading as a number.
+- Has a playhead (▼) synced with Panel EEG.
+- **View-only, no interaction.** Clicks only work on Panel EEG.
 
-### 6.4 Panel EEG
+### 6.4 EEG Panel
 
-- **Cố định đúng 18 kênh chuẩn** của pipeline. Lọc bỏ mọi kênh phụ (EKG/EOG/Ref) nếu file gốc có —
-  vd chb13/14 có thêm EKG, chb15 có thêm 8 kênh FC/CP-Ref. Lý do: mọi thứ hiển thị phải là dữ liệu thật
-  sự đi vào tính toán.
+- **Fixed at exactly the 18 standard channels** of the pipeline. Filters out every extra channel
+  (EKG/EOG/Ref) if the original file has them — e.g. chb13/14 have an extra EKG, chb15 has 8 extra
+  FC/CP-Ref channels. Reason: everything shown must be data that genuinely went into the computation.
 
-**Toolbar** (trái → phải, xem `UI/B1a`):
+**Toolbar** (left → right, see `UI/B1a`):
 
-| Nút | Chức năng |
+| Button | Function |
 |---|---|
-| `⊲▷ [X] hr` | Độ dài cửa sổ hiển thị trên Panel EEG, **độc lập** với zoom 1 giờ của mini-timeline. Bấm số → popover trượt dọc 24hr → 1min (`UI/B1b`) |
-| `⇕ [X] uV` | Thang biên độ, dropdown mức cố định 5/7/10/15/20/30 µV. Thuần frontend, không đụng backend |
-| `⏮⏭ Select Range` | Bật chế độ tạo event thủ công (§6.6) |
-| `lff 0.5 Hz` · `hff 60 Hz` · `60` | 3 filter khớp đúng bước preprocessing thật |
-
-**Đã bỏ khỏi toolbar** (so với Persyst/wireframe gốc): nút **All** (kênh đã cố định, không cho chọn) và
-nút **ar** (Artifact Reduction — pipeline không có bước tương ứng; giữ chỉ để "giống Persyst" là tính năng
-không phản ánh gì thật). Cũng bỏ nút **Comment** trên toolbar vì đã có Comment gắn theo từng event.
-
-**Toggle filter:** khi bật, sóng đã lọc nổi bật, sóng raw lùi làm nền mờ — **không ẩn hẳn raw**.
-
-**Playhead:** chỉ click được trên Panel EEG. Click 1 điểm → playhead nhảy tới đó, mini-timeline đồng bộ.
-
-**Thanh scrub dưới cùng:** có dropdown tốc độ phát `1x / 2x / 4x / 8x`, mặc định **1x**
-*(mới so với v4, nơi tốc độ bị cố định)*. Dừng ở 8x vì cao hơn thì mắt không đọc được waveform nữa.
-
-**Hàng "Event Time"** dưới cùng Panel EEG: block của các event trong tầm nhìn, nhãn ghi `Event N`
-(**không** ghi `seizure N` — xem §7.2).
-
-### 6.5 Panel Event
-
-- **Filter 2 tầng lồng nhau:** tầng 1 `All / Human / AI`; tầng 2 chỉ xuất hiện khi chọn AI —
-  `Accept / Reject / Uncertain / Unseen`. (Event Human tự confirm khi tạo nên không cần review.)
-- **Số đếm:** dạng `x` khi filter là All hoặc Human; dạng `x/y` khi filter là nhãn con của AI
-  (x = số khớp nhãn, y = tổng event AI trong file). "All" cộng gộp Human + AI.
-- Mỗi dòng: `Event` (tên) / `Onset` / `Type` (icon AI hoặc icon người) / `▼` mở rộng tại chỗ.
-- **Event AI mở rộng:** Onset / Offset / Duration (chỉ đọc) + 3 lựa chọn `Accept / Reject / Uncertain`
-  + ô Comment + nút Save. **Không sửa được onset/offset của event AI** — muốn sửa thì Reject rồi tự tạo
-  event mới bằng Select Range.
-- **Event User-added mở rộng:** Onset / Offset / Duration + **Delete / Edit** + Comment + Save. Không có
+| `⊲▷ [X] hr` | The length of the window shown on Panel EEG, **independent** of the mini-timeline's 1-hour zoom. Click the number → a vertical-slider popover from 24hr → 1min (`UI/B1b`) |
+| `⇕ [X] uV` | Amplitude scale, a dropdown of fixed steps **5/7/10/15/20/30/50/75/100/150/250/500 µV** (⚠ **CHANGED — C18, 2026-09-21**, see the note right below this table). Frontend-only, doesn't touch the backend |
+| `⏮⏭ Select Range` | Enables manual event-creation mode (§6.6) |
+| `lff 0.5 Hz` · `hff 60 Hz` · `60` | 3 filters matching the real preprocessing steps exactly |
+
+> **Amplitude-scale note (C18, 2026-09-21):** the original 5/7/10/15/20/30 µV list was chosen before
+> real data existed to check it against — reasonable at the time, but "locked" in this document has
+> never meant "can't be revised once real build data shows a different picture"; it means once revised,
+> it's re-locked, not never revised. Measured directly on real data during the build (`chb13_03.edf`,
+> `chb06_01.edf` — Step 5 fix round 2, method: `max_uv − min_uv` per displayed bucket, the exact
+> quantity `drawSeries` draws and `amplitudeUv` scales against) gives a per-channel amplitude of
+> **median ~106–111 µV, peaks up to ~1200–1800 µV** on both subjects — far beyond the old range, which
+> kept the waveform looking dense/busy at every old level, including the largest (30 µV). Extended with
+> 50/75/100/150/250/500 µV to cover the median range and most of the peak range, **keeping the 6 old
+> small levels unchanged** for flat (interictal) signal segments. The dropdown isn't stretched all the
+> way to the absolute peak (~1800 µV) because amplitude that large is rare and would needlessly
+> lengthen the list; 500 µV is already enough to stop clipping most channels. (`chb15` gives a notably
+> lower median — ~26 µV — but that was measured on 1 short, 500 s test file, not representative of a
+> full recording; not used to lower the range's floor, the 6 old small levels stay unchanged.)
+
+**Removed from the toolbar** (compared to the original Persyst/wireframe): the **All** button (channels
+are fixed, not selectable) and the **ar** button (Artifact Reduction — the pipeline has no corresponding
+step; keeping it just to "look like Persyst" would be a feature reflecting nothing real). Also removed
+the toolbar's **Comment** button since Comment is already attached to each event.
+
+**Filter toggle:** when on, the filtered wave is highlighted, the raw wave recedes into a dim background
+— **raw is never fully hidden**.
+
+**Playhead:** only clickable on Panel EEG. Clicking a point → the playhead jumps there, the mini-timeline
+syncs.
+
+**Bottom scrub bar:** has a playback-speed dropdown `1x / 2x / 4x / 8x`, default **1x** *(new compared to
+v4, where the speed was fixed)*. Capped at 8x because beyond that the eye can no longer read the
+waveform.
+
+**The "Event Time" row** at the bottom of Panel EEG: blocks for the events in view, labeled `Event N`
+(**never** `seizure N` — see §7.2).
+
+### 6.5 Event Panel
+
+- **Two nested filter tiers:** tier 1 `All / Human / AI`; tier 2 only appears when `AI` is selected —
+  `Accept / Reject / Uncertain / Unseen`. (A Human event self-confirms when created, so it needs no
+  review.)
+- **Count format:** bare `x` when the filter is All or Human; `x/y` when the filter is an AI sub-label
+  (x = matches, y = total AI events in the file). "All" combines Human + AI.
+- Each row: `Event` (name) / `Onset` / `Type` (AI icon or person icon) / `▼` expand in place.
+- **An expanded AI event:** read-only Onset / Offset / Duration + 3 choices `Accept / Reject /
+  Uncertain` + a Comment field + a Save button. **An AI event's onset/offset cannot be edited** — to
+  change it, Reject it and create a new event manually with Select Range.
+- **An expanded User-added event:** Onset / Offset / Duration + **Delete / Edit** + Comment + Save. No
   Accept/Reject/Uncertain.
-- **Click 1 dòng event** → đồng bộ tức thì cả 3 panel còn lại: Panel EEG nhảy tới onset→offset,
-  mini-timeline cập nhật playhead, Panel Attribution hiện dữ liệu của event đó.
-  **Panel Event là nguồn điều khiển chính.**
-- **Trạng thái rỗng:** file không có event AI nào → panel trống, vẫn thêm được event thủ công
-  (`UI/B0a`). Wording: `No detected events in this file. You can still add an event manually with Select
-  Range.` — **không** dùng `No seizure detected` (ngụ ý kết luận y khoa).
-
-### 6.6 Tạo event thủ công (Select Range)
-
-1. Bấm **Select Range** → bật chế độ đánh dấu.
-2. Click điểm 1 trên grid EEG → đặt **onset**, hiện đường mốc dọc.
-3. Di chuột sang phải → ô chữ nhật kéo dài theo con trỏ trong hàng "Event Time" (`UI/B3a`).
-4. Click điểm 2 → chốt **offset** (`UI/B3b`).
-5. Event mới **tự chèn đúng vị trí thời gian** trong danh sách (không phải thêm vào cuối), kèm icon
-   người, Onset/Offset/Duration tự tính, không có Accept/Reject/Uncertain.
-6. Mini-timeline thêm block mới tại vị trí tương ứng, màu khác block AI.
-7. Alert ở header + Database tự động **+1**.
-
-*Lưu ý đọc ảnh:* màu xám trong `UI/B3a` là nhãn **Unseen**, không phải hiệu ứng làm mờ khi đang tạo event.
-
-### 6.7 Panel Channel Attribution
-
-**Framing bắt buộc — đây là ràng buộc khoa học, không phải lựa chọn UI.** Theo
-`docs/ATTRIBUTION_SPEC.md`, đây là **XAI cho nhánh reconstruction của GAE**. Nó **KHÔNG phải** localization
-và **KHÔNG phải** SOZ. Kết quả đối chiếu nhãn hiện ở trạng thái **PROVISIONAL**.
-
-- **Tiêu đề panel:** `Channel-level reconstruction anomaly — Event N`
-  *(sửa từ "Channel contribute to ..." trong mock — cách nói cũ ngụ ý quan hệ nhân quả/định vị.)*
-- **Hiển thị:** hình đầu đơn giản (vòng tròn + 18 vị trí điện cực hệ 10-20) làm nền, vẽ đè **18 đường
-  thẳng nối 2 điện cực của mỗi kênh bipolar** (vd FP1↔F7 cho kênh `FP1-F7`), tô theo Score.
-  - **Bắt buộc dùng đường nối, không dùng chấm tròn**: CHB-MIT là dữ liệu **bipolar**, mỗi kênh là hiệu
-    điện thế giữa 2 điện cực, không phải giá trị tại 1 điểm. Chấm tròn sai bản chất dữ liệu.
-  - Thang màu **teal**, không đỏ/vàng/xanh-lá — xem `SZSCAN_DESIGN_v2.md` §4.
-- **Bảng dưới:** `Rank / Channel / Score / Status`. Rank cố định theo Score, không cho user sắp xếp lại.
-  Status là segmented control `Accept | Reject` (loại trừ nhau như radio).
-- Nút **Save** + **Clear all** ở cuối bảng.
-- Đồng bộ theo event đang chọn, **kể cả event do user tự tạo** — attribution là số per-window tính từ mô
-  hình, tổng hợp trên bất kỳ khoảng thời gian nào, không phụ thuộc event đó do AI hay người tạo.
-- **Trạng thái rỗng:** chưa chọn event nào → placeholder `Select an event to view attribution`, không tự
-  động hiện event đầu tiên.
-- **Không** hiển thị metric đánh giá attribution (AUROC, khoảng tin cậy, p-value) trên UI.
+- **Clicking 1 event row** → instantly syncs the other 3 panels: Panel EEG jumps to onset→offset, the
+  mini-timeline updates its playhead, the Attribution Panel shows that event's data.
+  **The Event Panel is the primary control source.**
+- **Empty state:** a file with no AI events at all → an empty panel, still allows adding an event
+  manually (`UI/B0a`). Wording: `No detected events in this file. You can still add an event manually
+  with Select Range.` — **never** `No seizure detected` (implies a medical conclusion).
+
+### 6.6 Creating a manual event (Select Range)
+
+1. Click **Select Range** → enables marking mode.
+2. Click point 1 on the EEG grid → sets the **onset**, shows a vertical marker line.
+3. Move the mouse right → a rectangle stretches following the cursor in the "Event Time" row (`UI/B3a`).
+4. Click point 2 → locks in the **offset** (`UI/B3b`).
+5. The new event **inserts itself at the correct time position** in the list (not appended at the end),
+   with a person icon, auto-computed Onset/Offset/Duration, no Accept/Reject/Uncertain.
+6. The mini-timeline adds a new block at the matching position, colored differently from an AI block.
+7. The header's Alert + the Database **auto-increment by 1**.
+
+*Note when reading the mockup:* the gray in `UI/B3a` is the **Unseen** label, not a dimming effect from
+being in event-creation mode.
+
+### 6.7 Channel Attribution Panel
+
+**Mandatory framing — this is a scientific constraint, not a UI choice.** Per
+`docs/ATTRIBUTION_SPEC.md`, this is **XAI for the GAE's reconstruction branch**. It is **NOT**
+localization and **NOT** SOZ. The label-scored result is currently **PROVISIONAL**.
+
+- **Panel title:** `Channel-level reconstruction anomaly — Event N`
+  *(revised from "Channel contribute to ..." in the mockup — the old phrasing implies a causal/
+  localizing relationship.)*
+- **Display:** a simple head diagram (circle + the 18 electrode positions of the 10-20 system) as the
+  background, with **18 straight lines connecting the 2 electrodes of each bipolar channel** drawn over
+  it (e.g. FP1↔F7 for channel `FP1-F7`), colored by Score.
+  - **Connecting lines are mandatory, dots are not allowed**: CHB-MIT is **bipolar** data — each
+    channel is the potential difference between 2 electrodes, not a value at 1 point. A dot
+    misrepresents the nature of the data.
+  - **Teal** color scale, never red/yellow/green — see `SZSCAN_DESIGN_v2.md` §4.
+- **Table below:** `Rank / Channel / Score / Status`. Rank is fixed by Score, the user cannot reorder
+  it. Status is a segmented control `Accept | Reject` (mutually exclusive, like a radio button).
+- **Save** + **Clear all** buttons at the bottom of the table.
+- Syncs to the currently selected event, **including a user-created event** — attribution is a
+  per-window number computed by the model, aggregated over any time range, independent of whether that
+  event was AI- or human-created.
+- **Empty state:** no event selected yet → placeholder `Select an event to view attribution`, never
+  auto-shows the first event.
+- **Never** shows an attribution evaluation metric (AUROC, confidence interval, p-value) on the UI.
 
 ---
 
 ## 7 · EXPORT
 
-### 7.1 Phạm vi
+### 7.1 Scope
 
-**1 file `.txt` duy nhất cho toàn bộ subject**, gộp mọi file .edf con — giống hệt cấu trúc gốc
-`chbXX-summary.txt` của CHB-MIT (vốn cũng gộp nhiều file trong 1 file text).
+**A single `.txt` file for the entire subject**, combining every child .edf file — exactly matching the
+original structure of CHB-MIT's `chbXX-summary.txt` (which itself combines multiple files in 1 text
+file).
 
-### 7.2 Quy tắc chữ "Event" vs "Seizure"
+### 7.2 The "Event" vs "Seizure" wording rule
 
-- **Trên UI khi đang review:** mọi thứ AI phát hiện gọi là **Event** / **Alert**. Không bao giờ gọi một
-  phát hiện đơn lẻ là "seizure".
-- **Hai nhãn được phép chứa chữ "Seizure" trên UI:** `Seizure Detection Score` và tiêu đề panel EEG —
-  vì chúng chỉ **đầu ra của hệ thống nói chung**, không gán nhãn y khoa cho một mục cụ thể.
-- **Trong file export:** giữ dòng `Number of Seizures in File: N` đúng quy ước CHB-MIT gốc (để đối chiếu
-  máy), nhưng các mục con vẫn đánh số `Event 1`, `Event 2`… khớp đúng số hiệu bác sĩ đã thấy trên UI.
-  Hai cách gọi cùng tồn tại là **có chủ đích**, không phải lỗi.
+- **On the UI during review:** everything AI-detected is called an **Event** / **Alert**. A single
+  detection is never called a "seizure".
+- **Two labels are allowed to contain the word "Seizure" on the UI:** `Seizure Detection Score` and the
+  EEG panel's title — because they are only the **system's output in general**, not a medical label
+  assigned to one specific item.
+- **In the export file:** the line `Number of Seizures in File: N` is kept exactly per the original
+  CHB-MIT convention (for machine cross-referencing), but sub-entries are still numbered `Event 1`,
+  `Event 2`… matching exactly the numbering the clinician already saw on the UI. Both naming schemes
+  coexisting is **deliberate**, not a bug.
 
-### 7.3 Cấu trúc
+### 7.3 Structure
 
-Giữ khung gốc CHB-MIT, chèn thông tin mới ngay sau mỗi event (xem `UI/Annotaiton (format_ ID-summary.txt).png`):
+Keeps the original CHB-MIT frame, inserting new information right after each event (see
+`UI/Annotaiton (format_ ID-summary.txt).png`):
 
 ```
 Data Sampling Rate: 256 Hz
@@ -506,7 +569,7 @@ Event 1
     Start Time: 1230 seconds
     End Time: 1265 seconds
     Duration: 35 seconds
-    Comment: (nội dung nếu có)
+    Comment: (content if any)
     Channel Attribution (rank/channel/score/status):
       1  FP1-F7  3.5  Accept
       2  F7-T7   3.4  Reject
@@ -517,26 +580,27 @@ Event 2
     Start Time: ...
 ```
 
-**Thời gian trong export dùng giây tính từ đầu FILE** (giống annotation gốc CHB-MIT), **không** dùng
-`HH:MM:SS` như trên UI — đây là file kỹ thuật để xử lý tiếp, không tối ưu cho đọc bằng mắt.
+**Time in the export uses seconds from the start of the FILE** (like the original CHB-MIT annotation),
+**not** `HH:MM:SS` like the UI — this is a technical file meant for further processing, not optimized
+for human reading.
 
 ---
 
-## 8 · VIỆC CÒN TREO — phải xử lý lúc build, không được đoán
+## 8 · OPEN ITEMS — must be handled during the build, never guessed
 
-| # | Việc | Cách xử lý |
+| # | Item | How to handle |
 |---|---|---|
-| O1 | **Operating point của demo** (ngưỡng phát hiện event). Thủ tục FP-budget là label-free nên dùng được, nhưng **giá trị budget cụ thể** phải **đọc từ file** (`src/retrain/fp_budget_operating_point.py` + `docs/RESULTS_OF_RECORD_phaseB.md`) lúc build — **tuyệt đối không gõ lại từ trí nhớ** | đọc file |
-| O2 | **Tham số PELT** (penalty, model, min_size) — lấy đúng từ `src/cpd_pipeline_v14.py`, không tự chọn lại | đọc file |
-| ~~O3~~ | ~~robust-z của demo fit trên gì~~ — **ĐÓNG 2026-09-03**: `retrain_io.robust_z` đã fit trên toàn bộ window (dòng 56–60). Không phải divergence, không cần xử lý | đã đóng |
-| O4 | **Subject nào dùng cho kịch bản upload live** — chọn theo số file thật, đo lúc dựng cache | đo |
-| O4b | **Mức độ gắn cờ đoạn hậu-cơn** (§1.6b) — quan sát ở bước 1, quyết định có nói riêng trong slide bảo vệ hay không. Không chỉnh mô hình, không chỉnh ngưỡng để "sửa" | quan sát |
-| O5 | **Gamma-AEC trong đường liên tục** — `dataprep/compute_gamma_aec.py` hiện chạy trên mảng đã tách; cần bản liên tục | viết mới trong `pipeline_demo.py` |
+| O1 | **The demo's operating point** (the event-detection threshold). The FP-budget procedure is label-free so it's usable, but the **specific budget value** must be **read from a file** (`src/retrain/fp_budget_operating_point.py` + `docs/RESULTS_OF_RECORD_phaseB.md`) at build time — **absolutely never type it from memory** | read the file |
+| O2 | **PELT parameters** (penalty, model, min_size) — take them exactly from `src/cpd_pipeline_v14.py`, don't re-choose them | read the file |
+| ~~O3~~ | ~~what the demo's robust-z fits on~~ — **CLOSED 2026-09-03**: `retrain_io.robust_z` already fits on the entire window set (lines 56–60). Not a divergence, nothing to handle | closed |
+| O4 | **Which subject to use for the live-upload scenario** — chosen by real file count, measured while building the cache | measure |
+| O4b | **The extent of post-ictal flagging** (§1.6b) — observed at step 1, decide whether to call it out separately in the defense slides. No adjusting the model, no adjusting the threshold to "fix" it | observe |
+| O5 | **Gamma-AEC in the continuous path** — `dataprep/compute_gamma_aec.py` currently runs on the already-split array; a continuous version is needed | write new code in `pipeline_demo.py` |
 
-| O6 | **`evaluation_protocol.py` và `stat_validation.py` vừa được khôi phục về `src/`** (2026-09-03, tag `repo-deps-fixed`) sau khi bị archive nhầm dù vẫn đang được import. `fp_budget_operating_point.py` phụ thuộc chuỗi này — kiểm tra `import` chạy được trước khi lấy tham số cho O1 | 1 lệnh |
+| O6 | **`evaluation_protocol.py` and `stat_validation.py` were just restored to `src/`** (2026-09-03, tag `repo-deps-fixed`) after being mistakenly archived while still being imported. `fp_budget_operating_point.py` depends on this chain — verify the `import` runs before pulling parameters for O1 | 1 command |
 
-Không mục nào chặn việc bắt đầu dựng frontend.
+None of these items block starting to build the frontend.
 
 ---
 
-*Hết SZSCAN_SPEC_v5.md. Thay thế hoàn toàn `WEB_DEMO_SPEC_v4.md` và `WEB_DEMO_CONTEXT_BOUNDARY.md`.*
+*End of SZSCAN_SPEC_v5.md. Fully replaces `WEB_DEMO_SPEC_v4.md` and `WEB_DEMO_CONTEXT_BOUNDARY.md`.*
