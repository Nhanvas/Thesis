# ATTRIBUTION_SPEC — Channel Attribution (v2, đã chốt hướng mới)

> **Nguồn DUY NHẤT cho phần channel attribution.** Thay thế hoàn toàn spec cũ
> (dominant-channel + MAP@K + loại "diffuse") và `TIEU_CHI_LABEL_dominant_channel_v2.md`.
> Trạng thái: **bài toán / method / label-schema / metric ĐÃ KHÓA**; kết quả PROVISIONAL
> (chờ nhãn cứng của cô). File này tự chứa đủ để một chat sau THỰC THI mà không cần context lại.
>
> **Cập nhật:** 2026-08 · lý do đổi hướng: nhãn mới của cô là **một TẬP kênh ictal / cơn**
> (không còn 1–2 kênh dominant, không loại diffuse). Bài toán vì thế chuyển thành
> **phân loại nhị phân per-channel** — đúng khung đã được publish (EEG-CGS, AAAI 2023),
> map 1:1 với per-node recon-error của GAE.

---

## 0. TL;DR (đọc 30 giây)

- **Bài toán:** với mỗi cơn, GAE cho ra 18 điểm bất thường (per-node recon-z); hỏi *các kênh
  chuyên gia đánh là ictal có điểm cao hơn các kênh không-ictal không?* → **per-channel binary
  classification**, XAI cho nhánh GAE. **KHÔNG phải SOZ, KHÔNG phải onset.**
- **Score (từ pipeline, không train lại):** per-node GAE reconstruction error → robust-z vs
  interictal → 1 vector `s ∈ ℝ^18` / cơn.
- **Ground-truth (từ cô):** tập kênh ictal / cơn, 3 tầng `definite / uncertain / non-ictal`
  + cờ artifact + tag `focal/generalized`. (Bản AI-draft 76 cơn = phần "LABEL" bên dưới.)
- **Metric chính:** macro-**AUROC** + **AUPRC** (threshold-free) qua các cơn; kèm operating-point
  **Precision / Sensitivity / Specificity / F1** để so trực tiếp SOTA (EEG-CGS: 0.70/0.55/0.43/0.78).
- **Stratify focal vs generalized như một ĐẶC TÍNH, không phải bug:** cơn focal → attribution khu
  trú (đo localization); cơn generalized → attribution lan (báo "diffuse-đúng"), không ép localization.
- **Sanity check tổng hợp:** tiêm anomaly kênh nhân tạo (GT chính xác) → AUROC cao chứng minh máy chạy.
- **Honesty:** đồng thuận chuyên gia về định vị onset vốn thấp (ICC ~0.15–0.26) → "plausibility, not
  accuracy"; nhãn AI-draft không blind → cô là authoritative; CHB-MIT không có nhãn kênh sẵn → ta tự dựng.

---

## 1. BÀI TOÁN (đã khóa)

Với **mỗi cơn mà detector bắt đúng**, xếp/điểm 18 kênh scalp theo **mức bất thường của GAE**, và kiểm
tra điểm đó có **phân biệt được kênh ictal vs không-ictal** (theo nhãn chuyên gia) hay không.

- Đây là **interpretability / XAI** của nhánh GAE reconstruction. Framing = **hỗ trợ đọc bản ghi hậu
  kỳ** (khoanh vùng/bên các kênh có kiểu hình ictal để bác sĩ review nhanh), **không** phải định vị
  phẫu thuật (SOZ), **không** phải onset channel.
- Khung bài toán và cách chấm theo **EEG-CGS (Ho & Armanfard, AAAI 2023)** — "unsupervised seizure /
  anomalous **channel** detection", node = kênh EEG, anomaly-score từ GNN autoencoder recon +
  contrastive, chấm bằng per-channel Precision/F1/Sensitivity/Specificity so với nhãn kênh của dataset.
  Ta khác họ ở: (a) score = **recon-z thuần của GAE detector temporal của ta** (không thêm contrastive
  head), (b) dataset = **CHB-MIT** (vốn KHÔNG có nhãn kênh → ta tự dựng nhãn), (c) nhãn = **tập kênh
  ictal do chuyên gia review**, không phải nhãn TUSZ có sẵn.

**Đóng góp khoa học (để viết report / trả lời reviewer):**
CHB-MIT chỉ có onset/offset TIME, **không** có nhãn kênh/SOZ. Phần lớn nghiên cứu interpretability trên
CHB-MIT validate **định tính** (saliency "trông giống ổ đã biết"). Ta cung cấp **(i) một tập nhãn kênh
ictal do chuyên gia review trên CHB-MIT + (ii) đánh giá ĐỊNH LƯỢNG attribution per-channel** trên
dataset vốn thiếu nhãn kênh — đây là phần mới, đặt cạnh EEG-CGS (làm định lượng nhưng trên TUSZ có nhãn
sẵn) và SZTrack/DeepSOZ (localization có giám sát bằng SOZ lâm sàng).

---

## 2. SCORE — cái pipeline THỰC SỰ cho ra (không train lại)

**Input (đã có sẵn từ GAE inference):**
`{subj}_{interictal|ictal}_pernode.npy`, shape `[n_win, 18]` = per-window, per-node **GAE
reconstruction error** (`r_i(w)`). (Script dump hiện có: xem `attribution_gae_pernode.py` header;
files nằm dưới `data/processed/` hoặc theo `--pernode_root`.)

**Chuẩn hoá per-channel (robust-z vs baseline interictal của chính subject):**
```
med_i = median_w r_i(w)   trên interictal
mad_i = median_w |r_i(w) − med_i|  + 1e-9   trên interictal
zwin_i(w) = (r_i(w) − med_i) / mad_i          # per-window robust-z, dấu giữ nguyên
```

**Gộp về 1 điểm / kênh / cơn** (aggregation qua các window của cơn đó):
- **PRIMARY (pre-register): `s_i = p95_w( |zwin_i(w)| )`** trên các window thuộc cơn — "ictal
  involvement = ĐỈNH bất thường", robust hơn mean, khớp trực giác một kênh chỉ cần ictal một đoạn.
- **Sensitivity (báo phụ): `s_i = mean_w( |zwin_i(w)| )`** = đúng công thức `z_channels()` hiện có
  trong `attribution_gae_pernode.py` (để bắc cầu với code cũ).
- Kết quả mỗi cơn: **vector `s ∈ ℝ^18`** (chỉ số kênh theo `CH_NAMES` bên dưới).

**18 kênh (thứ tự cố định — index 0..17):**
```
0 FP1-F7  1 F7-T7  2 T7-P7  3 P7-O1   (L-temp,  Trái)
4 FP1-F3  5 F3-C3  6 C3-P3  7 P3-O1   (L-cent,  Trái)
8 FP2-F4  9 F4-C4 10 C4-P4 11 P4-O2   (R-cent,  Phải)
12 FP2-F8 13 F8-T8 14 T8-P8 15 P8-O2  (R-temp,  Phải)
16 FZ-CZ  17 CZ-PZ                     (Mid)
HEMI = L×8, R×8, M×2
```

**Lưu ý test-set discipline:** score dùng recon-error của GAE canonical seed 42 (đã khóa ở baseline
§0). **Không** chọn ngưỡng/aggregation trên 8 sub test; nếu cần ngưỡng cho operating point, chốt trên
VAL hoặc bằng quy tắc cố định (mục 4). Aggregation (p95) là pre-registered, không tune trên test.

---

## 3. LABEL — ground-truth từ cô (schema + convention)

### 3.1 Convention (đã chốt với ChatGPT double-check)
Với **mỗi cơn**, liệt kê **mọi kênh có phóng điện ictal RÕ / MẠNH** (rhythmic evolving, sharp-and-slow,
low-voltage fast tiến triển) trong diễn tiến cơn. Cụ thể (strict-ictal):
- **TÍNH (definite):** kênh có ictal rhythmic evolution thật (dù vào muộn), là *thành phần mạnh* của
  trường ictal.
- **KHÔNG tự động tính:** kênh chỉ *attenuation/suppression*, *artifact*, hay *một transient trùng
  thời điểm* — xếp `uncertain` hoặc bỏ.
- **Không còn "diffuse-loại":** cơn lan rộng vẫn liệt kê kênh mạnh; nhưng đã **lược bớt lan yếu-muộn**
  (thường mid-central F3-C3/C3-P3/F4-C4/C4-P4 và đỉnh FZ-CZ/CZ-PZ) nên **không cơn nào = 18/18** → mọi
  cơn đều có cả kênh 1 và 0 (điều kiện cần để AUROC/AP có nghĩa).
- **`early_ictal` (metadata phụ):** kênh ictal sớm/rõ nhất — KHÔNG phải SOZ, chỉ để mô tả bên hóa và
  (tùy chọn) làm target localization hẹp hơn. Không bắt buộc cho metric chính.

### 3.2 Schema CSV (`ictal_channels_FINAL.csv` — cô edit trên đây)
```
subject, seizure_idx, onset_s, ictal_channels, uncertain_channels, flags, focal_generalized
```
- `ictal_channels`  : list tên kênh, ngăn bằng `;`  (vd `T7-P7;P7-O1;FP2-F8;F8-T8`)
- `uncertain_channels` : list (có thể rỗng) — kênh nghi ngờ, sẽ **loại khỏi chấm** (không tính +/−)
- `flags`           : `artifact:P7-O1;P3-O1` / `electrodecrement` / `noisy` / rỗng
- `focal_generalized`: `focal` | `generalized`  (dựa `|ictal_channels|` + hình; xem 3.4)

### 3.3 Bản AI-DRAFT 76 cơn (đầu vào cho cô review — đã chốt trong phiên này)
> Đây là **draft**, cô đọc blind từ raw EEG rồi sửa. "M18-trừ" nghĩa liệt kê tên cụ thể như dưới.
> (Nếu chat sau cần: bản đầy đủ từng cơn nằm trong lịch sử; ở đây tóm nguyên tắc + các cơn khu trú
> quan trọng nhất để không phải chép lại 76 dòng.)

- **chb03 (trái ổn định):** 7 cơn, mỗi cơn ~13 kênh trái-trội + phải-trước
  `FP1-F7;F7-T7;T7-P7;P7-O1;FP1-F3;F3-C3;P3-O1;FP2-F4;P4-O2;FP2-F8;F8-T8;T8-P8;P8-O2`.
- **chb06 (không ổ, conf THẤP):** cả 10 cơn = `F3-C3;C3-P3;P3-O1;F4-C4;C4-P4;P4-O2;FZ-CZ;CZ-PZ`.
- **chb13 (trái-predominant; sz4/sz10 lan 2 bên):** ~12 kênh/cơn quanh
  `FP1-F7;F7-T7;T7-P7;P7-O1;FP1-F3;F3-C3;P3-O1;FP2-F4;FP2-F8;F8-T8;T8-P8;P4-O2` (sz4/sz10 thêm phải-central).
- **chb14 (trán 2 bên, Fp-max, cơn ngắn):** core `FP1-F7;FP1-F3;FP2-F4;FP2-F8` + temporal 2 bên;
  sz3/sz7 lan rộng hơn (~14), sz6 hẹp nhất (~6: `FP1-F7;FP1-F3;FP2-F4;FP2-F8;F8-T8;T8-P8`).
- **chb15 (trục T7-P7 trái + đa dạng):** khu trú rõ ở sz0 `FP1-F7;F7-T7;T7-P7;P7-O1;P3-O1`,
  sz8 `T7-P7;P7-O1;P3-O1`, sz15 `T7-P7;P7-O1;P3-O1;FP2-F4;F4-C4`, sz17 `T7-P7;P7-O1;P3-O1;FP2-F4;F4-C4;FZ-CZ`.
- **chb16 (2 bên lan rộng, bên hóa yếu):** ~11–13 kênh fronto-central-temporal-midline 2 bên;
  sz2 (giàu thông tin) `FP1-F3;F3-C3;FP2-F4;F4-C4;FP2-F8;F8-T8;T8-P8;P8-O2;T7-P7;P7-O1;FZ-CZ;CZ-PZ`.
- **chb17 (bitemporal, phải-trội):** 3 cơn ~11–12 kênh bitemporal + P4-O2 (sz2 phải-trội).
- **chb18 (phải + đường giữa; sz1 khu trú):** sz1 = `T7-P7;P7-O1;FP2-F4;P4-O2;FP2-F8;F8-T8;T8-P8;P8-O2`;
  sz4 = M18-trừ `P7-O1;P3-O1` (2 kênh này `flags: artifact`); còn lại ~14 kênh phải+giữa.

### 3.4 focal vs generalized (gán tự động, cô chỉnh nếu cần)
- `generalized` nếu `|ictal_channels| ≥ 12` **hoặc** cô ghi rõ; ngược lại `focal`.
- Ngưỡng 12 là pre-registered; báo cả phân tích với ngưỡng 10 và 14 làm sensitivity.

---

## 4. METRIC (đã khóa)

Cho mỗi cơn: `y ∈ {0,1}^18` (1 = `ictal_channels`), `s ∈ ℝ^18` (mục 2).
**Masking trước khi chấm:** loại khỏi cả `y` và `s` các kênh trong `uncertain_channels` và `flags:
artifact:*`. (→ mỗi cơn chấm trên ≤18 kênh còn lại.)

### 4.1 PRIMARY — per-channel binary, threshold-free (headline)
- **AUROC/cơn** = P(s(kênh ictal) > s(kênh non-ictal)); **macro-average qua cơn** (không pool kênh×cơn
  — tránh lệch thang z giữa cơn). Chance = 0.5.
- **AUPRC/cơn** (average precision) — nhạy hơn khi tập ictal lớn; macro-average. Chance = prevalence.
- Báo mean ± bootstrap-CI (resample qua cơn, 1000 lần).

### 4.2 Operating-point (để so SOTA EEG-CGS) — báo phụ
- Chọn ngưỡng `τ` trên score z bằng **quy tắc cố định pre-registered** (KHÔNG tune trên test):
  `τ` = giá trị z cho **Specificity = 0.90** trên "pseudo-seizure" interictal blocks (đã có cơ chế
  pseudo-block trong `attribution_gae_pernode.py`), tính trên **VAL subjects**, rồi khóa và áp lên test.
- Tại `τ`: gộp toàn bộ kênh×cơn (test) → **Precision / Sensitivity / Specificity / F1**.
- **Comparator bar (EEG-CGS Table 4, TUSZ, unsupervised):** Pre 0.70 · F1 0.55 · Sen 0.43 · Spec 0.78.
  *Chỉ so về mức độ/khung, không so tuyệt đối* (họ TUSZ+nhãn sẵn; ta CHB-MIT+reader).

### 4.3 Ranking (dễ hiểu khi bảo vệ) — báo phụ
- **Recall@|S|/cơn:** lấy top-`|S|` kênh theo s (|S| = số kênh ictal của cơn), đếm trúng. Chance = |S|/M.
- **MAP** với relevance = `ictal_channels` (giữ liên tục với spec cũ, nhưng relevance giờ là TẬP, không
  phải dominant): `AP = (1/|S|)·Σ_i prec@i·rel(i)` trên ranking 18 kênh; mean qua cơn.

### 4.4 Null (bắt buộc, thay cho chỉ so 0.5)
- **Permutation:** hoán vị s giữa các kênh trong từng cơn (giữ y), tính lại AUROC/AP macro; lặp 1000×
  → phân phối null, p-value + effect size (Δ so null-mean). Đây là bằng chứng "trên ngẫu nhiên", mạnh
  hơn so 0.5 đơn thuần.

### 4.5 Stratification (BẮT BUỘC — nếu không headline bị pha loãng)
- **Theo focal/generalized:**
  - *focal*: báo AUROC/AUPRC/Recall@|S| — đây là nơi câu chuyện **localization** đứng.
  - *generalized*: **không ép localization**; thay vào đó báo **"diffuse-correctness"** = mức lan của
    anomaly mass, vd `spread = 1 − (mass ở top-k)/(tổng mass)` hoặc entropy chuẩn hoá của s. Kỳ vọng:
    generalized có spread cao (đúng), focal có spread thấp. So sánh spread(focal) < spread(generalized)
    bằng test rank. → tái hiện đúng EEG-CGS Fig.3 (focal khu trú, generalized lan) như một **kết quả
    dương**, biến "18/18 làm metric vô nghĩa" thành phát hiện có kiểm soát.
- **Theo subject:** báo per-subject; **tách riêng chb06** (không ổ, conf thấp) khỏi headline, để ở
  limitation. chb14 (trán) / chb18_sz1 / chb15 khu trú / chb13 sz2,sz3,sz9 = nơi kỳ vọng AUROC cao nhất.
- **Theo |S|:** scatter AUROC vs |S| — dự kiến |S| nhỏ ⇒ AUROC cao (khu trú), |S| lớn ⇒ trần thấp.

### 4.6 Synthetic sanity check (upper-bound, làm trước khi chấm nhãn thật)
- Tiêm anomaly kênh nhân tạo vào interictal (đẩy recon-error 1 kênh chọn trước lên) → GT chính xác →
  AUROC/F1. Kỳ vọng cao (EEG-CGS synthetic F1 ~0.88). Chứng minh **máy attribution chạy đúng** độc lập
  với độ nhiễu của nhãn thật. (Có thể mô phỏng bằng cách scale `r_i` của 1 kênh trong pernode-inter.)

### 4.7 Secondary internal-validity (giữ từ code cũ, KHÔNG headline)
Từ `attribution_gae_pernode.py` (đã chạy được): **C1** consistency (top-k tái diễn qua cơn vs random
null), **C2** seizure-specificity (vs pseudo-seizure null), **C3** faithfulness (mass + occlusion AUROC
drop vs random-drop null), và **lateralization index** `LI=(ΣL−ΣR)/(ΣL+ΣR)`. Đây là *internal* (không
cần nhãn ngoài) → dùng như supporting evidence + so với `early_ictal` bên hóa của cô. Bỏ phần
**convergent-vs-eigencentrality** (khung C1/C2/C3 eigencentrality cũ đã archive).

---

## 5. WEB DEMO (SzScan) — tie-in

Analog CDSS đã được cấp phép (Persyst-style): highlight **KHI** (temporal — task đăng ký, PELT/CPD) +
**Ở ĐÂU** (kênh có recon-z cao — attribution này) để **triage review hậu kỳ**. Hiển thị per-seizure:
timeline + heat 18 kênh theo `s`. Guardrails (đã có trong `WEB_DEMO_SPEC.md`): PROVISIONAL, không
real-time, không SOZ; nhãn kênh là "vùng có kiểu hình ictal", ngôn ngữ = **hỗ trợ-quyết-định bổ trợ,
dùng sau khi chuyên gia đánh dấu onset**. Chỉ phục vụ 8 sub test, precomputed.

---

## 6. COMPARATORS / TRÍCH DẪN (cho report)

- **EEG-CGS** — Ho & Armanfard, AAAI 2023. Unsupervised GNN-autoencoder + contrastive, anomalous
  **channel** detection, per-channel Pre/F1/Sen/Spec vs nhãn kênh TUSZ; focal→khu trú, generalized→lan.
  *Khung + metric của ta theo bài này.* (SOTA bar: 0.70/0.55/0.43/0.78.)
- **SZTrack** — Craley et al., PLOS One 2022. Channel-wise CNN+BLSTM, seizure tracking + SOZ
  localization từ scalp; GT = coarse zone + SOZ lâm sàng; cắt −15s..+30s quanh onset.
- **DeepSOZ** — MICCAI 2023. Transformer + attention-MIL cho SOZ localization scalp (có giám sát).
- **Wong et al.** — BSPC 2025. Channel-annotated DL + DeepSHAP, chấm channel-highlight vs GT (Sen 0.59).
- **Grattarola et al.** — ESWA 2022. Attention-GNN iEEG, AP@K vs SOZ (comparator cho ranking metric).
- **Tang et al.** — ICLR 2022. Self-supervised DCRNN TUSZ, occlusion-based localization.
- **AR2 (Le et al.)** — đồng thuận reader về định vị/bên hóa onset THẤP (ICC 0.15–0.26) → cơ sở cho
  "plausibility not accuracy" + tầng uncertain.
- **CHB-MIT** chỉ có onset/offset time, **không** SOZ/nhãn kênh (Shoeb thesis; BIDS release) → lý do ta
  phải tự dựng nhãn.

---

## 7. HONESTY / LIMITATIONS (ghi để không bị bắt lỗi)

1. Nhãn AI-draft **không blind tuyệt đối**; cô là authoritative. AI-draft có xu hướng over-call bán cầu
   trái ở sub nền-bận (chb03/chb13) — cô sửa có thể làm AUROC đổi.
2. **Đồng thuận chuyên gia thấp** về định vị onset (AR2) → nhãn vốn nhiễu; dùng tầng `uncertain` +
   confidence, đóng khung concordance/plausibility, không "accuracy".
3. **CHB-MIT không có nhãn kênh/SOZ** → nhãn là *chú thích scalp involvement*, không phải SOZ; validate
   là proxy, không phải localization accuracy tuyệt đối.
4. **chb06 (và một phần chb16) signal-limited:** nền nhiễu + cơn lan đối xứng → attribution kém định vị;
   báo riêng, không kéo vào headline. Đây khớp lâm sàng: extratemporal/broad khó bên hóa trên scalp.
5. **Aggregation p95 & ngưỡng τ** là lựa chọn pre-registered; báo sensitivity với mean & τ khác.

---

## 8. EXECUTION PLAN (cho chat sau — làm thật, không cần context lại)

**Tiền đề:** đã có `{subj}_{inter|ictal}_pernode.npy [n_win,18]`; `chb*-summary.txt`;
`evaluation_protocol.py` importable (cung cấp `WIN_SEC`, `parse_summary_edf_list`).

**Bước 1 — Freeze nhãn (cô).**
Cô sửa `results/attribution_v6/labels/ictal_channels_FINAL.csv` (schema §3.2) từ AI-draft §3.3 → freeze.

**Bước 2 — Viết scorer self-contained `src/validate_channel_attribution.py`.** Nó phải:
1. Đọc pernode npy (inter+ictal) + summary → dựng **per-seizure window blocks** (tái dùng logic
   `seizure_window_blocks()` trong `attribution_gae_pernode.py`).
2. Tính `zwin` (robust-z vs interictal med/MAD) rồi **`s_i = p95_w|zwin_i(w)|` / cơn** (primary);
   thêm biến thể `mean` (sensitivity).
3. Đọc `ictal_channels_FINAL.csv` → `y`/cơn; **mask** `uncertain` + `flags:artifact`.
4. Tính per-seizure: `auroc(y,s)`, `average_precision(y,s)`, `recall@|S|`, `spread`, `|S|`,
   `focal_generalized`. Dùng `auroc()` có sẵn trong code cũ hoặc `sklearn`.
5. Macro-average (toàn bộ / focal / generalized / per-subject); bootstrap-CI qua cơn.
6. **Permutation null** (§4.4) + **operating-point τ** chốt trên VAL (§4.2) → Pre/Sen/Spec/F1 test.
7. **Synthetic check** (§4.6): hàm tiêm anomaly 1 kênh vào pernode-inter, chấm AUROC.
8. Ghi ra `results/attribution_v6/`:
   - `channel_attr_perseizure.csv` (subject, seizure_idx, |S|, focal_gen, auroc, ap, recall_at_S, spread)
   - `channel_attr_summary.csv` (macro AUROC/AUPRC/Pre/Sen/Spec/F1 + strata focal/gen + per-subject + CI)
   - `channel_attr_null.csv` (null-mean, p-value, effect size)
   - `channel_attr_synthetic.csv`
   - `channel_attr_figure.png` (bar |z| 18 kênh/subject như hàm figure cũ, + scatter AUROC-vs-|S|)
9. **Smoke-test trên synthetic trước** (mục 4 rule "test before delivering"): dựng pernode giả có
   1 kênh anomaly → AUROC≈1 mới chạy nhãn thật.

**Bước 3 — Báo cáo.** Điền số vào bảng: macro-AUROC/AUPRC (headline) · Pre/Sen/Spec/F1 vs bar 0.55 ·
focal vs generalized (localization vs diffuse-correct) · per-subject (chb06 tách) · null p-value.

**Bước 4 — Số PROVISIONAL → CHÍNH THỨC** sau khi cô freeze nhãn: chạy lại Bước 2, thay §9 kết quả.

---

## 9. KẾT QUẢ (PROVISIONAL — chờ cô)
*(chưa chạy với nhãn ictal-set mới; số dominant/MAP@K cũ (0.262/0.303) ĐÃ BỊ RETIRE — khác bài toán.)*
Điền sau Bước 2/4.

---

## 10. FILE OPERATIONS (áp vào repo — archive, đừng xóa cứng)

**SUPERSEDE (thêm banner + git mv vào `archive/attribution_superseded/`):**
- `TIEU_CHI_LABEL_dominant_channel_v2.md` → banner "SUPERSEDED bởi ATTRIBUTION_SPEC §3"; convention nhãn
  giờ = ictal-set 3-tầng (không dominant, không diffuse-loại).
- `validate_dominant_hitk_FINAL.py` → archive (MAP@K/hit@k dominant); thay bằng
  `src/validate_channel_attribution.py` (Bước 2).
- `results/attribution_v5/labels/labels_*_FINAL.csv` (+ `rank_per_seizure.csv` nếu là dominant) →
  archive; thay bằng `results/attribution_v6/labels/ictal_channels_FINAL.csv`.

**KEEP (còn dùng):**
- `attribution_gae_pernode.py` — **giữ** (nguồn per-node z + C1/C2/C3 internal + figure). Chỉ **hạ**
  phần "dominant"/eigencentrality-convergence xuống secondary; per-seizure z là input cho scorer mới.
- `attribution_detail.py`, `compare_labels_pernode.py`, `label_eeg_pilot.py` — giữ (hỗ trợ).
- `Spatial_Localization__...md` — giữ làm **field survey**; cập nhật banner trỏ về spec v2 này.

**DELETE:** không xóa cứng gì (rule "archive, don't delete"). Mọi thứ cũ → `archive/` kèm banner
provenance.

## 11. AMENDMENT A2 (2026-09-01) — pre-registered BEFORE any number was seen

Lý do: rlg là pipeline-of-record (RoR §1); mọi kết quả attribution phải truy vết được về
checkpoint canonical, và các dump cũ không có manifest provenance.

- **D1 — Regenerate, không tin dump cũ.** Mọi `*_pernode.npy` phát sinh trước amendment này
  bị coi là provenance-unknown. Per-node recon error được dump lại bằng
  `src/dump_pernode_recon.py` từ `data/models_retrain/gae_joint_seed42.pt`
  (`gae_joint.score_windows(per_node=True)`), kèm manifest SHA-256. Dump legacy đã được xác minh
  (2026-09-01) là sinh từ joint model §0 tiền-rebuild, nay cách ly ở `archive/pre_rebuild_s0/pernode/`
  — KHÔNG dùng, kể cả để đối chiếu số. Checkpoint canonical: `docs/PROVENANCE.md`.
- **D2 — Label source.** Kết quả chạy với nhãn AI-draft mang banner PROVISIONAL; số chính
  thức chỉ phát sinh sau khi cô freeze `ictal_channels_FINAL.csv` (§3.2). Nhãn AI-draft
  không được tái tạo từ trí nhớ/transcript — phải là file trên đĩa có provenance.
- **D3 — Scope cơn (sửa §1).** PRIMARY = **toàn bộ 76 cơn TEST**, không điều kiện theo kết quả
  CPD (attribution là XAI của nhánh GAE, độc lập detector → tránh selection bias).
  SECONDARY = phân tầng detected vs missed. Điều này thay câu "mỗi cơn detector bắt đúng" ở §1.
- **D4 — Multi-seed.** Macro-AUROC/AUPRC báo cho seed 42 (primary) và seed {1,2,3} (robustness),
  theo tiền lệ RoR §7. SD qua seed là noise floor của attribution.
- **Scope subject:** 8 TEST (chấm) + 3 VAL chb10/11/22 (CHỈ để chốt τ theo §4.2, không chấm).
- Falsification: macro-AUROC không vượt phân phối permutation-null (§4.4, p ≥ 0.05) ⇒ báo
  attribution là negative result, không reframe.

- **D5 — min_windows (chốt trước khi thấy bất kỳ AUROC nào).** PRIMARY = toàn bộ 76 cơn TEST,
  **không loại trừ theo số cửa sổ**; p95 trên 2 cửa sổ vẫn xác định được, và loại cơn sau khi thấy
  số là selection bias. SECONDARY = sensitivity analysis loại 3 cơn có `n_windows < 3`. Báo cả hai.
  Nếu chênh lệch > 1 SD-seed thì báo cáo phải nêu rõ kết luận phụ thuộc cơn ngắn.
  Phân bố TEST (đo từ `results/attribution_v6/seizure_blocks.csv`): min 2, p25 5, median 12, max 52.

- **Provenance nền (2026-09-01).** Toàn bộ attribution chạy trên
  `data/models_retrain/gae_joint_seed42.pt`, sha256 `dea06cb5…`, bias fingerprint **1.1597**,
  chb13 recon AUROC **0.8319**, xác minh corr = 1.0000000 trên 16/16 mảng zrecon đã commit.
  Row→seizure map: `results/attribution_v6/{seizure_blocks.csv, ictal_row_to_seizure.csv}`,
  76/76 cơn TEST khớp tuyệt đối. Gate mở phiên: `python src/verify_provenance.py`.