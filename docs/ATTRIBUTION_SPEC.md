# ATTRIBUTION_SPEC — Channel Attribution (đã chốt)
### Nguồn DUY NHẤT cho phần attribution. Thay thế: PREREG_05, ATTRIBUTION_PREREGISTRATION_v3_1,
### và bộ attribution_c1/c2/c3 (Gini/AUC/consistency — đã bị bác bỏ, xóa khỏi project).
### Trạng thái: bài toán/method/metric ĐÃ KHÓA; kết quả PROVISIONAL (chờ nhãn cứng của GVHD).

---

## 1. BÀI TOÁN (đã khóa)
Với mỗi cơn pipeline phát hiện đúng, xếp hạng 18 kênh scalp theo **mức độ THAM GIA cơn**
(*dominant/involved channel*), và kiểm tra top-hạng có trùng kênh chuyên gia đánh dấu không.
- Là **interpretability/XAI** cho nhánh GAE. KHÔNG phải onset, KHÔNG phải SOZ.
- Framing: hỗ trợ đọc bản ghi hậu kỳ (định bên/vùng), không phải định vị phẫu thuật.

## 2. METHOD (đã khóa — không train lại)
- Per-node GAE reconstruction error, gộp trên cửa sổ ictal của cơn.
- Robust-z vs interictal: `z_i = (mean_ictal_i − median_inter_i) / (MAD_inter_i)`.
- Sắp z giảm dần → hạng mỗi kênh (rank 1 = bất thường nhất).
- Timing hiện tại = **groundtruth (Q-method)**: cô lập chất lượng attribution khỏi lỗi detection.
  Biến thể PELT-timing (Q-system) để dành phụ lục.
- Script: `attribution_gae_pernode.py` (per-node) + `validate_dominant_hitk_FINAL.py` (chấm điểm).

## 3. LABEL (reference standard)
- GVHD đánh **1 kênh dominant/cơn (tối đa 2 nếu 2 kênh kề trội ngang nhau)**, blind từ raw EEG.
- Cơn lan tỏa hai bên không có kênh trội → **để trống = diffuse**, ghi lý do; loại khỏi chấm điểm, đếm riêng.
- Tiêu chí đầy đủ: `TIEU_CHI_LABEL_dominant_channel_v2.md` (4 dấu hiệu + nguyên tắc "đen-lên-so-baseline",
  soi 2 bán cầu, cảnh giác artifact chuỗi thái dương phải, chống anchoring).
- Schema: `subject, seizure_idx, fname, onset_s, offset_s, dominant_ch, note` (đã bỏ confidence/diffuse).

## 4. METRIC (đã khóa)
- **Primary: MAP@K** (mean average precision at K), K = 3 và 5 — metric field dùng (Grattarola 2022).
  - AP@K (1 cơn) = (1/số kênh đúng) · Σ_{i≤K} precision@i · rel(i). Với |T|=1: AP@K = 1/hạng (nếu hạng ≤ K, không thì 0).
  - MAP@K = trung bình AP@K qua các cơn focal.
- **Chance (baseline ngẫu nhiên, bắt buộc):** MAP@K khi rank ngẫu nhiên.
- **KHÔNG dùng:** AUC (nhãn thưa 1–2/18). hit@k & median rank đã BỎ khỏi bảng chính (chỉ là bản thô của MAP@K).
- **Caveat so sánh:** MAP@K của ta KHÔNG so trực tiếp giá trị với Grattarola (họ iEEG+SOZ; ta scalp+reader).
  Chỉ so về phương pháp đánh giá.

## 5. KẾT QUẢ (PROVISIONAL — nhãn AI-draft, chờ cô)
- 76 cơn: 36 focal + 40 diffuse (~53%).
- Pooled: **MAP@3 = 0.262, MAP@5 = 0.303** (chance: 0.102 / 0.128) → trên ngẫu nhiên ~2.6×, khiêm tốn.
- Mạnh ở unifocal (chb03, chb15); ≈ ngẫu nhiên ở broad/đa-ổ/cơn-ngắn (chb14/16/18).
- **Đóng khung honest:** recover kênh trên ngẫu nhiên nhưng vừa phải; mạnh nhất ở **lateralization** cho
  sub unifocal; 53% diffuse = giới hạn nội tại của scalp (kết quả, không phải model kém).

## 6. VIỆC CÒN LẠI
1. GVHD label cứng (blind) trên `labels_ALL_FINAL.csv` theo tiêu chí v2 → freeze.
2. Chạy lại `validate_dominant_hitk_FINAL.py` → số CHÍNH THỨC (thay số provisional §5).
3. (Nên) thêm **lateralization accuracy** — điểm mạnh nhất. (Tùy chọn) Q-system PELT-timing = phụ lục.

## 7. ĐIỂM YẾU ĐÃ TỰ PHÁT HIỆN (ghi để không bị bắt lỗi)
- AI-draft có xu hướng **over-call bán cầu trái ở sub nền-bận (vd chb03)** — chuỗi phải nhiều khi cũng trội.
  → nhãn cứng của cô sẽ điều chỉnh; nếu chb03 chuyển bilateral/diffuse thì MAP@K pooled có thể tụt.
- Nhãn AI không blind tuyệt đối (đã thấy model output) → chỉ là draft; cô là authoritative.
