# PROJECT2_SETUP.md — dựng và duy trì Claude project #2 (build SzScan)

**Rev. 2026-10-03.** Thay thế bản 2026-09-03 (b). Thay đổi: danh sách upload viết lại theo trạng thái
thật của project (đã build xong 9 bước), bỏ các file đã hết giá trị, thêm file code backend hiện hành,
cập nhật quy tắc chuyển thông tin giữa hai project, bỏ các câu đã cũ.

**Vì sao tách project:** project nghiên cứu mang toàn bộ ràng buộc khoa học — số đã khóa,
pre-registration, provenance checkpoint. Những thứ đó không liên quan tới việc code UI/backend và làm
loãng ngữ cảnh. Ngược lại, build demo cần ngữ cảnh UI/stack mà project nghiên cứu không cần.

**Phân vai:**

| Nơi | Làm gì |
|---|---|
| **Project #2 (Claude.ai)** | Spec, wording, xử lý mâu thuẫn, hướng dẫn từng bước, soạn prompt cho Claude Code, chuẩn bị demo cho bảo vệ |
| **Claude Code (local)** | Viết code thật, chạy server, sửa lỗi. Đọc `web_demo/CLAUDE.md` |
| **Project #1** | Report, đánh giá, attribution, mọi việc khoa học. Giữ `PROJECT2_SETUP.md` làm điểm neo |

---

## 1 · Nhóm A — tài liệu demo (bắt buộc)

Phải luôn là bản mới nhất của repo. Khi sửa file nào trong repo thì thay luôn file đó trong project.

| File | Path trong repo | Mục đích |
|---|---|---|
| `SZSCAN_SPEC_v5.md` | `web_demo/` | **Thắng mọi xung đột về hành vi/logic.** §1 chứa chứng minh bằng phép đo cho kiến trúc — đọc trọn §1 trước khi lý luận về backend |
| `SZSCAN_DESIGN_v2.md` | `web_demo/` | Token màu/chữ/khoảng cách đo bằng pixel-sampling |
| `DEMO_BUILD_HANDOFF.md` | `web_demo/` | Stack, cấu trúc thư mục, trạng thái 9 bước, quy trình freeze, số đo |
| `THESIS_CONTEXT_FOR_DEMO.md` | `web_demo/` | Những gì demo cần biết về thesis, và không hơn |
| `CLAUDE.md` | `web_demo/` | Rule của Claude Code |
| `BUILD_PROGRESS.md` | `web_demo/` | Nhật ký lịch sử, chỉ nối thêm. **Đọc đầu tiên ở phiên mới.** Chỉ mang tính thông tin, không ghi đè các file trên |
| `PROJECT2_SETUP.md` | `web_demo/` | File này (dùng chung) |
| `UI 29 screen.pdf` | `web_demo/UI/` (bản gộp) | Gộp 29 PNG đã chốt. **Thắng về mọi thứ nhìn thấy được** |

Instructions của project: toàn văn ở `PROJECT2_INSTRUCTIONS.md` (tiếng Anh), dán vào ô Instructions.
File này **không** cần upload vào Project files.

Không upload `UI (figma).fig` — Claude không đọc được.

## 2 · Nhóm B — code thesis, chỉ đọc

`pipeline_demo.py` tái hiện logic này ở dạng label-free liên tục. **Không được sửa** các file dưới đây.

`preprocessing.py`, `graph_construction.py`, `feature_extraction.py`, `compute_gamma_aec.py`,
`gae_joint.py`, `latent_anomaly.py`, `retrain_io.py`, `ensemble_recipe.py`, `cpd_pipeline_v14.py`,
`fp_budget_operating_point.py`, `edf_order.py`.

Ghi chú theo trạng thái hiện tại:

- `fp_budget_operating_point.py` chỉ còn là nguồn tham khảo. Đường chạy thật dùng **một operating point cố
  định** đặt ở hằng số trong `pipeline_demo.py`.
- `preprocessing.py` là nguồn của divergence §1.6 (loại window ±5 SD, buffer hậu-cơn).
- `retrain_io.py`: `robust_z` đã xác minh fit trên toàn bộ window.

## 3 · Nhóm C — upload để BIẾT LÀ CẤM

`szcore_eval.py` (chứa `build_timeline_masked()` — guard #1 cấm gọi). Đọc để hiểu vì sao mảng score của
thesis không phát lại được lên trục thời gian; không đọc thì sẽ có phiên đề xuất lại cache-replay.

## 4 · Nhóm D — bản sao code backend/frontend của demo

Đây là code **của demo**, project #2 sở hữu. Bản sao trong project **dễ cũ nhất**: mỗi lần Claude Code
sửa các file này, phải thay bản trong project, nếu không phiên sau sẽ lý luận trên code đã lỗi thời (đã
xảy ra: bản `pipeline_demo.py` còn per-subject calibration, `upload_manager.py` chưa có cap 2).

| File | Path |
|---|---|
| `pipeline_demo.py`, `pipeline_worker.py`, `upload_manager.py`, `db.py`, `attribution.py`, `main.py`, `waveform_serving.py` | `web_demo/backend/` |
| `test_signal_loss_v3.py` | `web_demo/backend/tests/` |
| `AnalysisScreen.jsx`, `EegPanel.jsx`, `MiniTimeline.jsx` | `web_demo/frontend/src/` (đúng path theo repo) |

Quy tắc: khi nghi ngờ bản sao trong project, đối chiếu với `BUILD_PROGRESS.md` §17–§18 trước, rồi xin
bản hiện hành.

## 5 · KHÔNG upload — và lý do

| Nhóm | Vì sao không |
|---|---|
| `RESULTS_OF_RECORD_*`, `PROVENANCE.md`, `RUBRIC_TRACKING.md`, `PHASE_*`, `PROPOSED_SOLUTION.md`, mọi `PREREG_*`, `ATTRIBUTION_SPEC.md` | Demo không hiển thị metric nào và không được ép khớp số thesis. `THESIS_CONTEXT_FOR_DEMO.md` thay cho phần cần thiết |
| Tài liệu viết report | Thuộc project #1 |
| 23 file `chbNN-summary.md` | Guard #2 cấm đọc trường seizure lúc runtime |
| `create_splits.py` | Sinh split sai — không có lý do để demo thấy |
| 5 file LSTM trong `src/retrain/` | Nhánh đã drop |
| `UI (figma).fig` | Claude không đọc được |
| **`STEP8_9_PREDEFENSE_CHECKLIST.md`** | Danh sách việc của giai đoạn trước; mọi mục đã xong hoặc đã nằm trong `BUILD_PROGRESS.md` §14/§18. Giữ lại chỉ tạo hai nguồn trạng thái |
| **5 báo cáo `CC_*`** (`CC_CHB13_REUPLOAD`, `CC_STAGE_TIMING`, `CC_FIX_FILTER_SINGLE_TOGGLE`, `CC_FILECOUNT_AUDIT`, `CC_FIX_DELETE_CONCURRENCY`) | Kết luận của chúng đã được ghi vào `BUILD_PROGRESS.md`; số trong các báo cáo cũ (timing) đã bị thay. Giữ lại là giữ số lỗi thời. Bản gốc vẫn còn trong repo nếu cần tra |

## 6 · Bẫy đã biết

| Bẫy | Thực tế |
|---|---|
| `edf_index.py` | **Không tồn tại**; thuộc kiến trúc v3 đã xóa. Offset từng file suy ra theo cấu tạo (SPEC §1.5) |
| `docs/archive/demo_v4/` | **DO NOT CITE.** Mô tả nhánh LSTM và cache-replay, đều sai |
| File summary | Đuôi **`.md`**, không phải `.txt` |
| Checkpoint | Nhận diện bằng **sha256**, không bằng tên file |
| Nhánh temporal/LSTM | Đã drop. Tài liệu nào mô tả nó là tài liệu cũ |
| `data/processed/{subj}_{interictal,ictal}.npy` | Tách bằng nhãn → guard #3 cấm |
| Mảng `ens_seed42_*` | Theo segment, không phát lại được lên trục thời gian |
| Hai con số thời gian | **21.9 s/h** (chỉ xử lý) và **≈12.3 s/h** (cả lượt chạy, gồm upload) — không dùng thay cho nhau. 9.76 / 10.83 / "~15 s/h" đã bị thay |
| Code trong project knowledge | Có thể cũ (xem §4) |
| Bản tải về | Trình duyệt đặt tên `NAME (1).md`; sau mỗi lần nhận file chạy `ls web_demo/*\(*\)*` |

## 7 · Kiểm tra sau khi cập nhật project

1. Hỏi project #2: *"tóm tắt ranh giới dữ liệu của demo"* — trả lời đúng phải đủ **ba guard** + write
   guard (SPEC §1.2).
2. Hỏi: *"operating point của demo là gì?"* — trả lời đúng: **một điểm cố định cho mọi bệnh nhân, đọc từ
   hằng số trong `pipeline_demo.py`**, không calibrate theo subject, không nêu số nếu chưa đọc file.
3. Hỏi: *"dùng edf_index thế nào?"* — đúng là "không tồn tại, không cần".
4. Hỏi: *"tốc độ xử lý bao nhiêu s/giờ?"* — đúng là nêu **cả hai** số và phân biệt chúng.

## 8 · Project #1 giữ lại gì

Project #1 không giữ các file tài liệu demo. **Giữ `PROJECT2_SETUP.md`** làm điểm neo để biết project #2
tồn tại, làm gì, ranh giới ở đâu. Hai nơi cùng giữ thẩm quyền về demo là công thức cho trôi lệch.

---

## 9 · Hai project làm việc với nhau qua Boti — quy tắc sở hữu

File này tồn tại ở **cả hai** project nên là mặt tiếp xúc. Không tạo thêm file cầu nối nào khác.

### 9.1 Ai sở hữu file nào

| Nhóm file | Chủ sở hữu | Bên kia được làm gì |
|---|---|---|
| `web_demo/*` (spec, design, handoff, CLAUDE.md, BUILD_PROGRESS, UI/) | **Project #2** | Project #1 **không sửa**, kể cả khi thấy chỗ sai — báo qua Boti |
| `THESIS_CONTEXT_FOR_DEMO.md` | **Chia đôi**: chỉ project #1 sửa §1–§3 và §5; project #2 sửa phần còn lại | Mọi thay đổi §1–§3, §5 đi theo đường (B) bên dưới |
| `docs/*` | **Project #1** | Project #2 không sửa |
| `src/*` | **Project #1** | Project #2 chỉ đọc; code mới chỉ nằm trong `web_demo/backend/` |
| `PROJECT2_SETUP.md` | **Chung** | Sửa khi cả hai bên đã thống nhất; Boti mang bản mới sang bên kia |

Nguyên tắc: **một quyết định chỉ có một nơi làm chủ.**

### 9.2 Các tình huống phải chuyển thông tin qua lại

**(A) Project #2 phát hiện lỗi ở phía thesis.** Project #2 không tự sửa file thesis. Nó viết ra: phát
hiện gì, bằng lệnh nào, output ra sao. Boti mang sang project #1; project #1 xác minh rồi mới cập nhật
`docs/`.

**(B) Project #1 thay đổi thứ demo phụ thuộc.** Chỉ có ba thứ chảy được vào demo, mỗi thứ dưới dạng một
bản `THESIS_CONTEXT_FOR_DEMO.md` mới do Boti mang sang:

1. **checkpoint** (đường dẫn + sha256 mới);
2. **operating point cố định và merge window** — project #1 chọn trên dữ liệu VAL; project #2 chỉ đặt
   hằng số, chạy guards, tag và chạy lại;
3. **giới hạn diễn giải attribution.**

Ngoài ba thứ này, thay đổi phía thesis không ảnh hưởng demo, vì demo không hiển thị metric nào. Nhãn
attribution đã freeze với kết quả **âm tính** (2026-09-25); wording panel đã khớp.

Trạng thái chờ (2026-10-03): một ứng viên operating point từ phía thesis đã được nêu nhưng **chưa áp
dụng** vào demo, chờ tác giả và cô quyết định (xem `BUILD_PROGRESS.md` §18). Áp dụng nó là một thay đổi
code thuộc quy trình freeze: guards → tag mới → chạy lại cả 8 subject từ DB rỗng.

**(C) Divergence mới của demo cần báo cô.** Mọi chỗ demo làm khác pipeline thesis đều là quyết định
phương pháp. Project #2 ghi vào `SZSCAN_SPEC_v5.md` §1.6; Boti mang sang project #1 để đưa vào
Limitations và tài liệu trình cô. Đã biết: (a) bốn bước fit trên toàn bộ window; (b) đoạn hậu-cơn không
bị loại; (c) quy tắc signal-loss (cửa sổ phẳng bị loại khỏi mọi phép fit, điểm 0); (d) một operating
point cố định thay vì calibrate theo subject.

**(D) Project #2 sinh vật liệu cho report.** Web demo là một sản phẩm hoàn chỉnh nên quá trình thiết kế và
xây dựng nó là nội dung phải báo cáo. Vật liệu sẵn: F1–F4 (SPEC §1.1) — vì sao không phát lại được mảng
score đã khóa; kiến trúc label-free liên tục và ba guard; divergence (a) đã đo, PASS; lựa chọn stack,
phạm vi 8 subject, wording attribution; số đo thời gian và bộ nhớ của bản đã freeze (hai con số thời
gian, §6 ở trên). Project #2 cung cấp nội dung kỹ thuật; project #1 quyết định cách viết vào report.
Phần handback nằm ở `web_demo/report_handback/`.

**Quy tắc trình bày (Boti, 2026-09-28):** không thứ gì hội đồng nhìn thấy — report, slide, chú thích ảnh,
câu trả lời khi bảo vệ — được nhắc tên gọi nội bộ (step, phase, tên prompt, `CC_*`, "fix round"…). Chỉ
nói hệ thống làm gì và cho ra output gì. Khi lấy nội dung từ `BUILD_PROGRESS.md` vào report, diễn đạt lại
theo bản chất việc.

### 9.3 Câu hỏi nên hỏi đúng project nào

| Câu hỏi | Hỏi ở |
|---|---|
| "màn này nên hiện gì", "sửa lỗi backend", "bước tiếp theo", "chuẩn bị demo bảo vệ" | Project #2 |
| "số này lấy ở đâu", "viết chương này thế nào", "đánh giá/kết quả thesis", "chọn operating point" | Project #1 |
| "demo khác thesis chỗ nào" | Cả hai — #2 cho chi tiết kỹ thuật, #1 cho cách viết vào report |
| "checkpoint nào đúng" | Project #1 — chỉ nó có `PROVENANCE.md` |

### 9.4 Điều dễ quên nhất

Project #2 không có kết quả đánh giá của thesis. Nếu nó nêu một con số hiệu năng, con số đó **được bịa
ra**. Demo không hiển thị metric nào, nên project #2 không có lý do chính đáng để nêu số.
