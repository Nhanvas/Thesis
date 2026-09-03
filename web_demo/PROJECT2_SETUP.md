# PROJECT2_SETUP.md — dựng Claude project #2 cho việc build SzScan

**Rev. 2026-09-03 (b).** Thay thế bản trước: danh sách upload viết lại đầy đủ (path + mục đích + bẫy),
instruction tách ra file riêng `PROJECT2_INSTRUCTIONS.md`, thêm `THESIS_CONTEXT_FOR_DEMO.md`.

**Vì sao tách project:** project nghiên cứu mang toàn bộ ràng buộc khoa học — số đã khóa, cấm đụng TEST
set, pre-registration, provenance checkpoint. Những thứ đó không liên quan tới việc code UI/backend và
làm loãng ngữ cảnh. Ngược lại, build demo cần ngữ cảnh UI/stack mà project nghiên cứu không cần.

**Phân vai sau khi tách:**

| Nơi | Làm gì |
|---|---|
| **Project #2 (Claude.ai)** | Bàn spec, wording, xử lý mâu thuẫn, hướng dẫn từng bước build, chuẩn bị demo cho bảo vệ |
| **Claude Code (local)** | Viết code thật, chạy server, sửa lỗi. Đọc `web_demo/CLAUDE.md` |
| **Project hiện tại** | Report, attribution, mọi việc khoa học. Giữ `PROJECT2_SETUP.md` làm điểm neo để biết project #2 tồn tại |

---

## 1 · DANH SÁCH UPLOAD — nhóm A: bắt buộc, tài liệu demo

Không có nhóm này thì project #2 không làm việc được.

| File | Path trong repo | Mục đích |
|---|---|---|
| `SZSCAN_SPEC_v5.md` | `web_demo/` | **Thắng mọi xung đột về hành vi/logic.** §1 chứa chứng minh bằng phép đo cho kiến trúc — đọc trọn §1 trước khi lý luận về backend |
| `SZSCAN_DESIGN_v2.md` | `web_demo/` | Token màu/chữ/khoảng cách, **đo bằng pixel-sampling từ PNG chốt**, không phải đoán |
| `DEMO_BUILD_HANDOFF.md` | `web_demo/` | Stack, cấu trúc thư mục, thứ tự 9 bước build, rủi ro đã biết |
| `THESIS_CONTEXT_FOR_DEMO.md` | `web_demo/` | **File mới.** Toàn bộ những gì demo cần biết về thesis, và không hơn. Thay cho việc phải upload cả bộ tài liệu khoa học |
| `CLAUDE.md` | `web_demo/` | Rule của Claude Code. Project #2 cần biết Claude Code đang bị ràng buộc gì để không hướng dẫn ngược |
| `PROJECT2_SETUP.md` | `web_demo/` | File này |
| **29 file PNG** | `web_demo/UI/*.png` | **Thắng về mọi thứ nhìn thấy được.** Tác giả thiết kế và đã đóng băng |

Không upload `UI (figma).fig` — Claude không đọc được định dạng kiwi-encoded, chỉ tốn dung lượng.

## 2 · Nhóm B: code phải đọc để không phải đoán logic

Toàn bộ là **chỉ đọc**. `pipeline_demo.py` tái hiện logic này ở dạng label-free liên tục, **không được
sửa** bất kỳ file nào dưới đây.

| File | Path | Mục đích với demo |
|---|---|---|
| `preprocessing.py` | `src/dataprep/` | 6 bước tiền xử lý. **Nguồn của divergence §1.6** — Step 4 loại window ±5 SD, và buffer 4 giờ hậu-cơn bị loại khỏi mảng interictal |
| `graph_construction.py` | `src/dataprep/` | wPLI + AEC + CAR + top-k 20 %. `build_adjacency()` là entry point |
| `feature_extraction.py` | `src/dataprep/` | 5 band powers/kênh → `[N, 18, 5]` |
| `compute_gamma_aec.py` | `src/dataprep/` | Nhánh `zgamma`. ⚠️ Bản hiện tại chạy trên mảng đã tách; demo cần bản liên tục (O5) |
| `gae_joint.py` | `src/retrain/` | `GAEModel`, `load_checkpoint`, `score_windows`. Mọi thứ downstream import file này |
| `latent_anomaly.py` | `src/phaseB/` | `latent_pool` → nhánh `zlatent`. Chỗ có `LedoitWolf().fit(Zi)` sinh ra divergence (a) |
| `retrain_io.py` | `src/retrain/` | `robust_z`. **Đã xác minh fit trên toàn bộ window** (dòng 56–60) — không phải divergence |
| `ensemble_recipe.py` | `src/` | Công thức ensemble, trọng số bằng nhau 1/3 |
| `cpd_pipeline_v14.py` | `src/` | **LOCKED.** `detect_events()` là entry point. Lấy tham số PELT từ đây, không tự chọn |
| `fp_budget_operating_point.py` | `src/retrain/` | Operating point label-free. Phụ thuộc `final_eval` → `stat_validation` |
| `edf_order.py` | `web_demo/backend/` | Thứ tự **hiển thị** file trên UI theo header time, khác thứ tự **xử lý** theo tên file |

## 3 · Nhóm C: upload để BIẾT LÀ CẤM, không phải để dùng

| File | Path | Vì sao vẫn upload |
|---|---|---|
| `szcore_eval.py` | `src/` | Chứa `build_timeline_masked()` — **guard #1 cấm gọi**. Đọc dòng 90, 98–109, 111–113, 120–123 mới hiểu vì sao mảng score của thesis không phát lại được lên trục thời gian. Không đọc thì sẽ có phiên đề xuất lại cache-replay |

## 4 · KHÔNG upload — và lý do

| Nhóm | Vì sao không |
|---|---|
| `RESULTS_OF_RECORD_phaseB.md`, `PROVENANCE.md`, `RUBRIC_TRACKING.md`, `PHASE_C_*`, `PHASE_D_HANDOFF.md`, `PROPOSED_SOLUTION.md`, mọi `PREREG_*` | Demo **không hiển thị metric nào** và **không được ép khớp** số thesis. Mang vào chỉ tạo cám dỗ trộn hai bộ quy tắc. `THESIS_CONTEXT_FOR_DEMO.md` đã thay thế phần cần thiết |
| `ATTRIBUTION_SPEC.md` | Chỉ §9 liên quan, và §5 của `THESIS_CONTEXT_FOR_DEMO.md` đã tóm đủ ràng buộc |
| `THESIS_REPORT_WRITING_GUIDE.md`, `ATTRIBUTION_REPORT_PACK.md`, `Report_format.md` | Tài liệu viết report, thuộc project hiện tại |
| 23 file `chbNN-summary.md` | Guard #2 cấm đọc trường seizure lúc runtime. Upload cả bộ chỉ tăng khả năng một phiên nào đó tiện tay dùng chúng làm nhãn |
| `create_splits.py` | Trap §7.1 — sinh split E_main 15/8 **sai**. Không có lý do gì để demo thấy nó |
| 5 file LSTM trong `src/retrain/` | Nhánh đã bị drop. Sự tồn tại của chúng chỉ gây nhầm |
| `Lit_review.txt`, `2024__SzCORE.pdf`, `Thesis_Registration_Form.md` | Không liên quan build |
| `UI (figma).fig` | Claude không đọc được |

## 5 · Bẫy đã biết — nói trước để không mất thời gian tìm lại

| Bẫy | Thực tế |
|---|---|
| `edf_index.py` | **Không tồn tại.** Thuộc kiến trúc v3, đã xóa. Kiến trúc v5 suy offset từng file theo cấu tạo (`SZSCAN_SPEC_v5.md` §1.5). Tài liệu cũ mô tả nó như module sẵn có — tài liệu đó đã archive |
| `docs/archive/demo_v4/` | 4 file demo cũ. **DO NOT CITE.** v4 mô tả nhánh LSTM và kiến trúc cache-replay, cả hai đều sai |
| File summary | Đuôi **`.md`**, không phải `.txt`. Docstring cũ ghi `.txt` |
| Checkpoint | Nhận diện bằng **sha256**, không bằng tên file. Model `archive/pre_rebuild_s0/` tương quan 0.987–0.999 với bản canonical — đủ để qua mặt một lần kiểm tra hời hợt |
| Nhánh temporal/LSTM | **Đã drop.** Mọi tài liệu mô tả nó là tài liệu cũ |
| `data/processed/{subj}_{interictal,ictal}.npy` | Tách **bằng nhãn** → guard #3 cấm dùng. Nhìn tên tưởng là dữ liệu thô, không phải |
| Mảng `ens_seed42_*` | Theo **segment**, không theo thời gian. Không phát lại được lên trục thời gian thật |

## 6 · Instruction

Toàn văn ở `PROJECT2_INSTRUCTIONS.md` (tiếng Anh). Dán nguyên file đó vào ô Instructions của project #2.

## 7 · Sau khi dựng xong

1. **Kiểm tra ngữ cảnh đã nạp đúng** — hỏi project #2: *"tóm tắt ranh giới dữ liệu của demo"*. Trả lời
   đúng phải nhắc đủ **ba guard** ở `SZSCAN_SPEC_v5.md` §1.2. Nếu thiếu, ngữ cảnh chưa vào.
2. **Kiểm tra bẫy** — hỏi: *"dùng edf_index thế nào?"*. Trả lời đúng là "module đó không tồn tại và
   không cần". Nếu nó hướng dẫn cách dùng, tức là đang bịa.
3. Mở Claude Code tại `F:/Study/Thesis/Code`, xác nhận đọc được `web_demo/CLAUDE.md`.
4. Bắt đầu từ **bước 0** trong `DEMO_BUILD_HANDOFF.md` §6 — khung repo + `test_guards.py`. Không nhảy
   thẳng vào giao diện.

## 8 · Project hiện tại giữ lại gì

Sau khi project #2 hoạt động, gỡ khỏi project hiện tại: `SZSCAN_SPEC_v5.md`, `SZSCAN_DESIGN_v2.md`,
`DEMO_BUILD_HANDOFF.md`, `CLAUDE.md`, `THESIS_CONTEXT_FOR_DEMO.md`.

**Giữ lại `PROJECT2_SETUP.md`** làm điểm neo — để mọi phiên sau của project hiện tại biết project #2 tồn
tại, làm gì, và ranh giới ở đâu. Hai nơi cùng giữ thẩm quyền về demo là công thức cho việc hai bên trôi
lệch nhau.

---

## 9 · Hai project làm việc với nhau qua Boti — quy tắc sở hữu

File này tồn tại ở **cả hai** project, nên nó là mặt tiếp xúc. Không tạo thêm file cầu nối nào khác:
thêm một file nữa là thêm một thứ có thể trôi lệch.

### 9.1 Ai sở hữu file nào

| Nhóm file | Chủ sở hữu | Bên kia được làm gì |
|---|---|---|
| `web_demo/*` (spec, design, handoff, CLAUDE.md, THESIS_CONTEXT, UI/) | **Project #2** | Project hiện tại **không sửa**, kể cả khi thấy chỗ sai — báo qua Boti |
| `docs/*` (RESULTS_OF_RECORD, PROVENANCE, REPO_MAP, PROJECT_STATUS, ATTRIBUTION_SPEC, PREREG…) | **Project hiện tại** | Project #2 **không sửa**, chỉ đọc `THESIS_CONTEXT_FOR_DEMO.md` |
| `src/*` | **Project hiện tại** | Project #2 **chỉ đọc**, code mới chỉ nằm trong `web_demo/backend/` |
| `PROJECT2_SETUP.md` (file này) | **Chung** | Sửa khi cả hai bên đã thống nhất; Boti mang bản mới sang bên còn lại |

Nguyên tắc: **một quyết định chỉ có một nơi làm chủ.** Hai nơi cùng giữ thẩm quyền về cùng một thứ là
công thức chắc chắn cho việc trôi lệch.

### 9.2 Ba tình huống phải chuyển thông tin qua lại

**(A) Project #2 phát hiện lỗi ở phía thesis.** Ví dụ: một module khóa import hỏng, một tham số trong
`cpd_pipeline_v14.py` không như tài liệu mô tả, một phép đo mới mâu thuẫn với `THESIS_CONTEXT_FOR_DEMO.md`.

→ Project #2 **không tự sửa** file thesis. Nó viết ra: *phát hiện gì, bằng lệnh nào, output ra sao.*
Boti mang sang project hiện tại. Project hiện tại xác minh lại rồi mới cập nhật `docs/`.

*Tiền lệ:* đúng cách này đã lộ ra `evaluation_protocol.py` và `stat_validation.py` bị archive nhầm dù
vẫn đang được import — tìm ra trong lúc bàn demo, sửa ở phía thesis.

**(B) Project hiện tại thay đổi thứ demo phụ thuộc.** Ba thứ demo thật sự phụ thuộc:
checkpoint canonical · giới hạn diễn giải attribution · danh sách 8 subject TEST.

→ Nếu một trong ba đổi, Boti mang bản `THESIS_CONTEXT_FOR_DEMO.md` mới sang project #2. Ngoài ba thứ
này, thay đổi phía thesis **không** ảnh hưởng demo — vì demo không hiển thị metric nào.

*Trường hợp cụ thể sắp tới:* nếu cô freeze nhãn attribution, số attribution sẽ đổi. Demo **không** bị
ảnh hưởng (không hiển thị số), nhưng nếu trạng thái PROVISIONAL được gỡ thì §5 của
`THESIS_CONTEXT_FOR_DEMO.md` cần cập nhật.

**(C) Divergence mới của demo cần báo cô.** Mọi chỗ demo làm khác pipeline thesis đều là quyết định
phương pháp, không phải chi tiết kỹ thuật.

→ Project #2 ghi vào `SZSCAN_SPEC_v5.md` §1.6. Boti mang sang project hiện tại để đưa vào phần
Limitations của report và vào tài liệu trình cô. Hai divergence đã biết: (a) bốn bước fit trên toàn bộ
window, (b) đoạn hậu-cơn không bị loại.

**(D) Project #2 sinh vật liệu cho report.** Web demo là một **sản phẩm hoàn chỉnh**, nên bản thân quá
trình thiết kế và xây dựng nó là nội dung phải báo cáo — độc lập với việc rubric có dòng riêng cho demo
hay không (rà `RUBRIC_TRACKING.md`: **không có**; demo ăn điểm gián tiếp qua tiêu chí #4 *Design
considers impacts* và #7 *Significance + applicability*).

Phân biệt hai loại "demo", đừng lẫn:

| Loại | Là gì | Cần gì |
|---|---|---|
| **Demo lúc bảo vệ** | Web đã hoàn chỉnh, trình bày end-to-end trước hội đồng | Bước 0–8 xong, kịch bản, subject ít file, cache dự phòng |
| **Báo cáo quá trình build** | Chương/mục trong report mô tả kiến trúc và lập luận thiết kế | Chủ yếu **viết được ngay**, không chờ code |

Phần lớn vật liệu cho loại thứ hai đã sẵn sàng, vì nó là **lập luận thiết kế có bằng chứng**, không phải
kết quả thí nghiệm:

- F1–F4 (`SZSCAN_SPEC_v5.md` §1.1) — vì sao không thể phát lại mảng score đã khóa lên trục thời gian.
  Đây là dạng vật liệu tiêu chí #4 tìm kiếm: một quyết định kiến trúc ra bằng phép đo.
- Kiến trúc label-free liên tục và ba guard (§1.2–§1.3).
- Divergence (a) — **đã đo, PASS** (§1.6a).
- Divergence (b) hậu-cơn — sự **tồn tại** là tất yếu logic; **mức độ** thì chờ bước 1.
- Lựa chọn stack, phạm vi 8 subject, ràng buộc wording attribution.

**Bốn chỗ phải chờ bước 1 mới điền được:** thời gian chạy thật đầu-cuối (hiện chỉ có 16.9 ms/window ở
mức thành phần) · mức độ gắn cờ đoạn hậu-cơn (O4b) · operating point của demo (O1) · ảnh chụp app thật.

→ Viết phần report về demo **ngay bây giờ** với bốn chỗ trống đó, đừng đợi build xong. Project #2 cung
cấp nội dung kỹ thuật; project hiện tại quyết định cách viết vào report và đặt vào tiêu chí nào.

### 9.3 Câu hỏi nên hỏi đúng project nào

| Câu hỏi | Hỏi ở |
|---|---|
| "màn này nên hiện gì", "sửa lỗi backend", "bước tiếp theo build gì" | Project #2 |
| "số này lấy ở đâu", "viết chương này thế nào", "trả lời hội đồng ra sao về Phase C" | Project hiện tại |
| "demo khác thesis chỗ nào" | Cả hai đều trả lời được; project #2 cho chi tiết kỹ thuật, project hiện tại cho cách viết vào report |
| "checkpoint nào đúng" | Project hiện tại — chỉ nó có `PROVENANCE.md` |

### 9.4 Điều dễ quên nhất

Project #2 **không có** `RESULTS_OF_RECORD_phaseB.md`. Nếu nó nêu một con số hiệu năng, con số đó **được
bịa ra**, vì nó không có nguồn nào để đọc. Đúng thiết kế: demo không hiển thị metric nào, nên project #2
không có lý do chính đáng nào để nêu số.
