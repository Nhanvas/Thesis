# TIÊU CHÍ ĐÁNH NHÃN — "DOMINANT / INVOLVED CHANNEL" (v2)
### Dùng cho: GVHD (Assoc. Prof. Hà Thị Thanh Hương) đánh nhãn CHÍNH THỨC trên CHB-MIT
### Thesis: Unsupervised Seizure Temporal Localization (GAE + CPD) — phần Channel Attribution
### Ghi chú: bản nhãn của cô là REFERENCE authoritative. Có một bản AI-draft riêng (chỉ để tham khảo,
###          không đáng tin bằng cô); cô nên đọc độc lập từ raw EEG trước, so sau nếu muốn.

---

## 0. Nhiệm vụ (đọc trước khi đánh)

- Với **mỗi cơn**, chỉ ra **kênh mang phóng điện ictal MẠNH và KÉO DÀI nhất** = *dominant channel*.
- **KHÔNG** đánh onset (kênh khởi phát sớm nhất). **KHÔNG** suy ra SOZ (vùng phẫu thuật).
- Đây là *involvement trên scalp* — một phán đoán thị giác của người đọc, không phải ground truth SOZ.
  Ta chấp nhận giới hạn này một cách minh bạch.

---

## 1. Đơn vị đánh nhãn — 18 kênh bipolar (chọn theo TÊN)

| # | Kênh | Vùng | Bán cầu |
|---|------|------|--------|
| 1 | FP1-F7 | Thái dương–trán trước T | **Trái** |
| 2 | F7-T7  | Thái dương trước T | **Trái** |
| 3 | T7-P7  | Thái dương giữa–sau T | **Trái** |
| 4 | P7-O1  | Thái dương–chẩm T | **Trái** |
| 5 | FP1-F3 | Trán T | **Trái** |
| 6 | F3-C3  | Trán–trung tâm T | **Trái** |
| 7 | C3-P3  | Trung tâm–đỉnh T | **Trái** |
| 8 | P3-O1  | Đỉnh–chẩm T | **Trái** |
| 9 | FP2-F4 | Trán P | **Phải** |
| 10 | F4-C4 | Trán–trung tâm P | **Phải** |
| 11 | C4-P4 | Trung tâm–đỉnh P | **Phải** |
| 12 | P4-O2 | Đỉnh–chẩm P | **Phải** |
| 13 | FP2-F8 | Thái dương–trán trước P | **Phải** |
| 14 | F8-T8 | Thái dương trước P | **Phải** |
| 15 | T8-P8 | Thái dương giữa–sau P | **Phải** |
| 16 | P8-O2 | Thái dương–chẩm P | **Phải** |
| 17 | FZ-CZ | Đường giữa trước | Giữa |
| 18 | CZ-PZ | Đường giữa sau | Giữa |

> Tên kênh trong nhãn phải khớp đúng danh sách này. (T8-P8: nếu file có lặp, dùng T8-P8-0.)

---

## 2. "Dominant channel" — bốn dấu hiệu để NHÌN

So sánh **đoạn cơn** với **đoạn nền (baseline)**. Kênh dominant là kênh có mẫu ictal rõ nhất theo
**cả bốn** dấu hiệu:

1. **Biên độ tăng** — đường sóng to hẳn so với nền và so với các kênh khác.
2. **Nhịp đều (rhythmicity)** — sóng lặp lại đều đặn như một dao động rõ ràng.
3. **Tiến triển (evolution)** — nhịp/biên độ đổi theo thời gian (phân biệt cơn thật với artifact).
4. **Kéo dài (sustained)** — duy trì nhiều giây liên tục, không phải một gai đơn lẻ.

---

## 3. NGUYÊN TẮC THEN CHỐT — ba cái bẫy phải tránh (quan trọng nhất)

Đây là chỗ dễ sai nhất; nắm ba điều này thì nhãn mới chắc:

- **(a) Phải "đen LÊN so với baseline", không chỉ "đen".** Kênh dominant là kênh **chuyển từ yên
  ở nền → mạnh lúc cơn**. Một dòng đen dày *cả ở baseline lẫn lúc cơn* thì độ đen đó **không** do cơn.
  → Luôn liếc panel baseline của đúng kênh đó trước khi kết luận.
- **(b) Chuỗi thái dương phải (F8-T8, T8-P8, P8-O2) và đường giữa hay dính artifact cơ/điện cực.**
  Chúng có thể đen dày *do nhiễu nền*, không phải phóng điện. → Cảnh giác đặc biệt với các kênh này;
  chỉ tính là dominant nếu chúng **thật sự bùng lên đúng lúc cơn** (qua test (a)).
- **(c) Soi HAI bán cầu cân xứng, đừng để định kiến dẫn dắt.** Nếu đã "biết" bệnh nhân này ổ bên trái,
  rất dễ vô thức chỉ nhìn bên trái và bỏ qua bên phải cũng đang đen ngang ngửa. → Bắt buộc so **dòng trái
  vs dòng phải tương ứng** (vd T7-P7 vs T8-P8). Nếu **cả hai đen như nhau** → đây là **diffuse/bilateral**,
  KHÔNG phải "trái trội".

---

## 4. Đánh BAO NHIÊU kênh mỗi cơn

- **Mặc định: 1 kênh** — kênh trội rõ nhất.
- **Cho phép 2** — chỉ khi hai kênh **trội ngang nhau** (thường kề nhau chung một điện cực, vd F7-T7 và
  T7-P7 chung T7). Ghi cả hai, phân tách bằng dấu phẩy.
- **Tối đa 2.** Cần ≥3 kênh trội ngang nhau → đây là dấu hiệu **diffuse** (§5), không ghi 3.

---

## 5. Khi nào đánh DIFFUSE (để trống kênh)

- Phóng điện nổi lên **gần như đồng thời khắp/nhiều kênh, HAI bán cầu tương đương, không kênh nào trội** →
  **để TRỐNG cột dominant**, và ghi lý do ngắn ở cột note (vd "phủ hai bên, không kênh trội").
- Cơn diffuse **không** được chấm điểm (không có đích), nhưng **được đếm** và báo cáo riêng (tỉ lệ diffuse
  là một kết quả thật về giới hạn của scalp).
- **Ranh giới:** có 1–2 kênh trội **hơn hẳn** phần còn lại (qua test §3a) → đánh kênh. Không kênh nào trội,
  hai bên như nhau → diffuse. Khi lưỡng lự, ghi rõ ở note để đối chiếu sau.

---

## 6. MULTIFOCAL (nhiều ổ)

- **Khác ổ giữa các cơn** (cơn này trái, cơn khác phải): cứ đánh **theo từng cơn** bình thường. Gộp lại
  thấy không dồn về một bên là **phát hiện thật** (đa ổ/song phương), không cần làm gì đặc biệt khi đánh.
- **Hai vùng đồng trội trong CÙNG một cơn:** ghi **tối đa 2 kênh**; nếu không tách được → **diffuse**.

---

## 7. Quy trình đọc

Mỗi cơn có 3 panel raw-EEG:
1. **BASELINE** (đoạn trước cơn) — mốc so sánh; **luôn xem trước** (phục vụ test §3a).
2. **ONSET ZOOM** — chỉ để tham khảo *thời điểm* khởi phát (KHÔNG phải nhãn).
3. **FULL SEIZURE** — panel chính để đọc **dominant**.

Chỉ dùng **raw EEG** + lọc hiển thị (band-pass ~1–70 Hz, notch 60 Hz). **KHÔNG** dùng line-length /
band-power / spectrogram / bất kỳ đặc trưng nào của model. Có thể mở mne để cuộn/zoom thêm khi cần chốt.

---

## 8. Chống thiên lệch (bắt buộc)

- Đánh **chỉ từ raw EEG**, **không** xem output/attribution của model (giữ nhãn độc lập với thứ đang được kiểm định).
- **Không để kiến thức trước về ổ của bệnh nhân dẫn dắt** — soi cả hai bán cầu cân xứng (§3c).
- Giữ tiêu chí **nhất quán** giữa các cơn và bệnh nhân.
- Lưỡng lự thì ghi rõ ở note, **không đoán bừa**.

---

## 9. Định dạng file — `labels_{subject}.csv`

Các cột `subject, seizure_idx, fname, onset_s, offset_s` **đã điền sẵn**. Cô chỉ điền **2 cột**:

| cột | cô điền |
|-----|---------|
| `dominant_ch` | 1–2 tên kênh (đúng §1), phân tách bằng dấu phẩy. **Để TRỐNG nếu diffuse.** |
| `note` | ghi chú ngắn — bắt buộc ghi **lý do** khi để trống (diffuse); tùy chọn khi có kênh. |

*(Đã bỏ cột `confidence` và `diffuse` — trống = diffuse, lý do ghi ở note.)*

> **Lưu ý (gộp file):** mỗi subject là một file `labels_{subject}.csv`; sau khi cô đánh xong, các file per-subject sẽ được gộp thành `labels_ALL_FINAL.csv` để chấm MAP@K (theo ATTRIBUTION_SPEC §6). Cô **không cần** tự tạo file gộp.

Ví dụ:
```
subject,seizure_idx,fname,onset_s,offset_s,dominant_ch,note
chb15,1,chb15_10.edf,1082,1113,"T7-P7","thái dương trái sau, nhịp đều kéo dài"
chb15,2,chb15_15.edf,1591,1748,"F7-T7, T7-P7","hai kênh kề trội ngang nhau"
chb13,0,chb13_19.edf,2077,2121,"","phủ hai bán cầu, không kênh trội"
```

---

## 10. Tóm tắt một dòng

> Mỗi cơn: so với nền, chọn **1** (đôi khi **2**) kênh **to nhất + đều nhất + kéo dài nhất** VÀ
> **mới đen lên đúng lúc cơn**. Soi **cả hai bên** — hai bên như nhau thì **để trống (diffuse)**.
> Chỉ dùng raw EEG, không nhìn model, không để định kiến ổ dẫn dắt.