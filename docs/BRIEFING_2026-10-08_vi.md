# Báo cáo giải thích cho buổi gặp cô (08/10/2026)

> Bản sửa 08/10 chiều: look #6 seed 42 subject-mean là 0.508 (0.498 là trung bình 4 seed, theo `e22 SUMMARY`); chb24 21.3 h (x1 SUMMARY). Tài liệu viết trước attribution của hệ cuối (A5) và trước khi xây lại demo.

**Hệ thống phát hiện và định vị cơn co giật trên EEG da đầu: từ kết quả cũ đến hệ thống đã chốt**

Tài liệu này viết để Nhân đọc lại toàn bộ câu chuyện trong một lần, hiểu được vì sao kết quả thay đổi,
và trình bày lại cho cô. Mọi con số đều lấy từ các file kết quả đã lưu. Con số nào do tính tay từ các số
trong file thì có ghi "(tính từ số liệu)".

---

## 0. Tóm tắt trong một trang

1. **Kết quả cũ trong báo cáo (độ nhạy 0.618, 27.4 báo động giả/ngày trên 8 bệnh nhân kiểm tra) bị lạc quan.**
   Con số đó đúng với cách đánh giá đã dùng, nhưng cách đánh giá đó dựng lại dòng thời gian từ nhãn cơn
   co giật và lấp khoảng trống bằng những đoạn EEG "sạch" đã loại bỏ hết các đoạn biên độ cao. Mà chính
   các đoạn biên độ cao lại là thứ gây ra phần lớn báo động giả ngoài thực tế.
2. **Khi chạy lại hệ thống cũ trên bản ghi liên tục** (giữ mọi đoạn, đúng thứ tự thời gian, như khi dùng thật),
   nó chỉ bắt được 23/76 cơn với 73.3 báo động giả/ngày, hoặc 2/76 cơn nếu giữ báo động giả quanh 24/ngày.
3. **Ba nguyên nhân gốc đã được đo:** (a) đặc trưng đầu vào của mô hình GAE cũ xóa mất thông tin biên độ;
   (b) mô hình học "thế nào là bình thường" từ bệnh nhân khác, nên các trạng thái biên độ cao (không phải co
   giật) của chính bệnh nhân mới bị chấm điểm cao hơn cả cơn co giật; (c) điểm bất thường bị "trôi" theo
   từng file ghi.
4. **Đã sửa:** huấn luyện lại GAE với 7 đặc trưng có giữ biên độ; đo bất thường **theo từng kênh, so với chính
   bệnh nhân đó** (không dùng nhãn); trừ trôi nền bằng trung vị trượt ±15 phút; ngưỡng cảnh báo riêng cho
   từng bệnh nhân (tính từ điểm số, không dùng nhãn); dùng phát hiện điểm thay đổi phi tham số (kernel CPD)
   để định vị thời điểm bắt đầu và kết thúc cơn.
5. **Kết quả hiện tại (đánh giá trên bản ghi liên tục, bộ chấm chính thức SzCORE):**

| | Độ nhạy (gộp) | Độ nhạy (trung bình theo bệnh nhân, cách tính chính thức) | Báo động giả/ngày |
|---|---|---|---|
| Hệ thống cũ, chạy trên bản ghi liên tục | 2/76 đến 23/76 | — | 24.2 đến 73.3 |
| Kiểm tra lần "sạch" (thiết kế hoàn toàn không dùng tập kiểm tra) | 26/76 = **0.342** | **0.508** (4 lần huấn luyện: 0.498) | 22.2 |
| Hệ thống cuối (thiết kế có dùng thông tin từ tập kiểm tra, đã công khai) | 37/76 = **0.487** | **0.577** | 27.5 |
| **Dữ liệu hoàn toàn mới, chưa từng dùng:** chb24 | 14/16 = **0.875** | — | 29.5 |
| **Dữ liệu hoàn toàn mới, chưa từng dùng:** Siena (14 bệnh nhân người lớn, 4 lần huấn luyện) | 0.617 | **0.633** | 41.0 |
| Phương pháp không giám sát duy nhất trong bảng xếp hạng SzCORE (DynaSD), cùng dữ liệu Siena | — | 0.664 | 77.7 |

6. **Vì sao trên 8 bệnh nhân kiểm tra vẫn chưa cao:** 3 bệnh nhân (chb06, chb13, chb16) giữ 32/76 cơn mà
   hệ thống chỉ bắt được 5. chb06 và chb16 gần như toàn cơn rất ngắn (6–20 giây), chb13 có cơn bị các
   trạng thái biên độ cao của chính bệnh nhân lấn át. Tập kiểm tra khó hơn rõ rệt so với các bệnh nhân
   dùng để thiết kế (đo được: 20–50 % đoạn bình thường có điểm cao hơn đỉnh cơn, so với khoảng 4 %).
7. **Vì sao vẫn bảo vệ được:** hệ thống đáp ứng đủ mục tiêu đăng ký (không dùng nhãn, GAE là trung tâm,
   CPD phi tham số có vai trò đo được: giảm sai số thời điểm bắt đầu cơn từ 32 xuống 12 giây trên tập
   kiểm tra); đánh giá bằng giao thức trung thực nhất hiện có; có kiểm định ngoài trên dữ liệu chưa từng
   thấy cho kết quả ngang phương pháp không giám sát tốt nhất với khoảng một nửa số báo động giả; và
   mọi chỗ yếu đều có nguyên nhân đo được, được công khai.

---

## 1. Vài khái niệm cần nắm trước

| Thuật ngữ | Nghĩa đơn giản |
|---|---|
| **Cửa sổ** | Một đoạn EEG dài 4 giây, 18 kênh. Mọi điểm số đều tính trên từng cửa sổ. |
| **Sự kiện (event)** | Một khoảng thời gian liên tục mà hệ thống cho là có cơn. Đánh giá theo sự kiện, không theo cửa sổ. |
| **Độ nhạy** | Tỉ lệ cơn co giật thật được hệ thống bắt trúng (có sự kiện chồng lên cơn). |
| **Báo động giả/ngày (FP/day)** | Số sự kiện không trùng cơn nào, quy về 24 giờ ghi. Đây là chi phí của hệ thống. |
| **Độ chính xác (precision)** | Trong các sự kiện hệ thống đưa ra, bao nhiêu phần là cơn thật. |
| **F1** | Trung bình điều hòa của độ nhạy và độ chính xác. |
| **SzCORE** | Khung đánh giá chuẩn (Dan và cộng sự, Epilepsia 2024): bắt trúng nếu sự kiện nằm trong dung sai 30 s trước bắt đầu và 60 s sau kết thúc; sự kiện cách nhau dưới 90 s được gộp; cơn dài hơn 300 s bị cắt thành nhiều mảnh. Ta đã đọc mã nguồn gốc của bộ chấm để chắc chắn dùng đúng. |
| **Gộp (pooled)** | Cộng tất cả cơn của mọi bệnh nhân rồi chia: bệnh nhân nhiều cơn (chb15 có 20 cơn) nặng ký hơn bệnh nhân ít cơn (chb17 có 3). |
| **Trung bình theo bệnh nhân (subject-mean)** | Tính độ nhạy cho từng bệnh nhân rồi lấy trung bình: mỗi bệnh nhân một phiếu. **Đây là con số chính thức của SzCORE.** Ta báo cáo cả hai. |
| **Tập huấn luyện / kiểm định / kiểm tra** | 12 / 3 / 8 bệnh nhân CHB-MIT, chia cố định từ đầu. Mọi lựa chọn thiết kế chỉ được làm trên 15 bệnh nhân huấn luyện + kiểm định. 8 bệnh nhân kiểm tra (76 cơn) chỉ được chấm sau khi chốt. |
| **Lần huấn luyện (seed)** | Huấn luyện GAE 4 lần với khởi tạo ngẫu nhiên khác nhau. Số chính là lần đầu (seed 42); báo kèm trung bình 4 lần để thấy độ ổn định. |
| **GAE** | Graph Autoencoder: mỗi cửa sổ được biến thành một đồ thị 18 nút (18 kênh), cạnh là mức đồng bộ giữa các kênh. GAE nén mỗi nút thành 16 con số (gọi là "biểu diễn ẩn"). |
| **CPD (phát hiện điểm thay đổi)** | Tìm thời điểm mà tính chất của chuỗi điểm số thay đổi. Kernel CPD là phương pháp phi tham số (không giả định phân bố). |
| **Đoạn "biên độ cao"** | Cửa sổ có ít nhất một mẫu vượt ±5 độ lệch chuẩn trên một kênh. Trước đây ta tưởng đó là nhiễu; thực ra 46 % cửa sổ bình thường và khoảng 90 % cửa sổ co giật thuộc loại này. Nó nghĩa là "biên độ cao", không phải "nhiễu". |

---

## 2. Vấn đề của kết quả cũ: vì sao bị lạc quan

### 2.1 Hệ thống cũ làm gì

EEG → đồ thị mỗi cửa sổ → GAE → ba điểm bất thường (sai số tái tạo, khoảng cách của biểu diễn ẩn trung
bình, và một chỉ số đồng bộ biên độ dải gamma) → chuẩn hóa → cộng đều ba điểm → PELT (một thuật toán CPD)
cắt chuỗi điểm thành các đoạn → đoạn nào đủ cao thì là cơn.

### 2.2 Cách đánh giá cũ ("offline") và lỗ hổng của nó

Do mảng điểm số của hệ thống cũ được lưu theo đoạn (không có chỉ số cửa sổ → giây), việc chấm điểm phải
**dựng lại dòng thời gian từ nhãn cơn**, rồi lấp các khoảng giữa các cơn bằng điểm của các cửa sổ bình
thường được lấy mẫu lại. Các cửa sổ này đến từ tập đã **loại bỏ đoạn biên độ cao**.

Hệ quả: chính những đoạn gây báo động giả ngoài đời thật bị loại ra ngay từ khi dựng dòng thời gian. Số
liệu đúng với giao thức đó, nhưng **không phải ước lượng hiệu năng trên một bản ghi thật**.

Số cũ trên 8 bệnh nhân kiểm tra (76 cơn, 278.2 giờ bình thường):

| Điểm vận hành | Độ nhạy | Độ chính xác | F1 | Báo động giả/ngày |
|---|---|---|---|---|
| Điểm chốt trên tập kiểm định (số chính của báo cáo cũ) | 0.618 (47/76) | 0.129 | 0.213 | 27.4 |
| Điểm độ nhạy cao | 0.711 | 0.068 | 0.123 | 64.4 |
| Đỉnh F1 trên đường cong (tìm bằng cách quét trên tập kiểm tra, không bao giờ được là kết quả) | 0.474 | 0.387 | 0.426 | 4.9 |

Mức phân biệt theo cửa sổ (AUROC trung bình 8 bệnh nhân) khi đó là 0.805.

### 2.3 Đánh giá lại trên bản ghi liên tục: con số thật

Ta chạy lại mọi cửa sổ của mọi file, đúng thứ tự thời gian, không loại bỏ gì, không dùng nhãn:

| Cách chạy hệ thống cũ | Kết quả trên 8 bệnh nhân kiểm tra |
|---|---|
| Cùng cài đặt với số chính cũ, trên bản ghi liên tục | 23/76 cơn (0.303, tính từ số liệu) @ 73.3 báo động giả/ngày |
| Cài đặt giữ báo động giả thấp hơn | 0.079 @ 19.2 |
| Ứng dụng web SzScan (đã xây xong, vẫn chạy hệ thống cũ) | 0.211 @ 52.4 |
| Hệ thống cũ với bộ phát hiện ngưỡng mới | 2/76 @ 24.2 |

AUROC theo cửa sổ trên bản ghi liên tục: 0.640 (so với 0.805 ở giao thức cũ).

**Đây là lý do cô thấy "căng" khi xem số thật ngày 05/10, và là điểm xuất phát của toàn bộ công việc cải
thiện hiệu năng.**

### 2.4 Ba lỗi phụ đã phát hiện trong quá trình kiểm tra lại

1. **PELT báo cả điểm thay đổi đi xuống.** Mỗi lần điểm số giảm cũng tạo một điểm thay đổi, nên dùng PELT làm
   bộ phát hiện sinh nhiều báo động thừa. Khi so trên cùng nhóm bệnh nhân thiết kế, PELT làm bộ phát hiện cho
   độ nhạy 0.213 trong khi một bộ ngưỡng đơn giản cho 0.479.
2. **Một công thức độ chính xác tự viết bị sai** (có lúc ra số âm). Từ đó mọi độ chính xác, F1 và báo động
   giả/ngày đều lấy từ chính đầu ra của bộ chấm SzCORE, không tự tính.
3. **Cách gộp số chính thức của SzCORE là trung bình theo bệnh nhân**, không phải cộng gộp. Từ đó ta luôn báo
   cả hai.

---

## 3. Tìm nguyên nhân: đã làm gì để xác định

Nguyên tắc làm việc: hiểu EEG thô và cơ chế lỗi trước, rồi mới đề xuất; mỗi thử nghiệm ghi trước giả thuyết
và tiêu chí đạt/không đạt; chỉ thiết kế trên 15 bệnh nhân không thuộc tập kiểm tra.

| Câu hỏi | Cách kiểm tra | Kết quả | Kết luận |
|---|---|---|---|
| Báo động giả đến từ đâu? | Thử bỏ (bằng nhãn, chỉ để chẩn đoán) các cửa sổ biên độ cao không phải co giật trên tập kiểm định | Báo động giả giảm khoảng 85–90 % (633 → 68), vẫn giữ 11/15 cơn | Báo động giả chủ yếu đến từ đoạn biên độ cao không phải co giật |
| Đoạn "biên độ cao" có phải nhiễu? | Xem EEG thô và đếm | Quy tắc ±5 độ lệch chuẩn đánh dấu 46 % cửa sổ bình thường (chỉ cần một mẫu trên một kênh) và khoảng 90 % cửa sổ co giật | Không phải nhiễu; là "biên độ cao". Không thể dùng nó làm nhãn nhiễu |
| Định nghĩa lại "bình thường" chung cho mọi bệnh nhân có giúp? | Mô hình mật độ trên đặc trưng, học từ nhiều bệnh nhân | Không đạt (0.340 so với 0.372); tăng độ phức tạp mô hình không đổi gì | "Bình thường" chung không giải quyết được |
| Nếu có nhãn thì đạt bao nhiêu? (chỉ để tham chiếu, không bao giờ thuộc hệ thống) | Mô hình có giám sát, kiểm tra chéo bỏ một bệnh nhân | 0.702 @ 20.5 | Mức tham chiếu của việc có nhãn |
| Dùng đánh dấu biên độ cao làm nhãn nhiễu? | Huấn luyện mô hình nhận diện nhiễu | 81.5 % cửa sổ co giật bị gọi là nhiễu | Sai từ thiết kế (đoán trước được từ con số 90 % ở trên) |
| "Bình thường" học từ **chính bệnh nhân** thì sao? | Mô hình mật độ trên đặc trưng, học trên toàn bộ bản ghi của từng bệnh nhân, không nhãn | 0.340 → **0.596** | **Bình thường riêng từng bệnh nhân tách được cơn khỏi trạng thái biên độ cao của bệnh nhân đó** — nếu đầu vào còn giữ biên độ |
| Làm vậy trên đầu ra GAE cũ được không? | Cùng cách, trên đầu ra GAE cũ | Không đạt | Đầu ra GAE cũ thiếu thông tin |
| Vì sao GAE cũ thiếu thông tin? | Đọc mã | Năng lượng dải tần được chuẩn hóa trong từng cửa sổ, rồi co giãn min–max theo kênh trong từng cửa sổ | **Đặc trưng nút của GAE cũ xóa mất biên độ và hình dạng phổ của cửa sổ. Đây là nguyên nhân gốc** |

---

## 4. Sửa mô hình: GAE phiên bản 2

**Thay đổi:** thêm 7 đặc trưng giữ thông tin biên độ cho mỗi nút (log năng lượng 5 dải tần, log độ dài
đường cong tín hiệu, độ nhọn phân bố có dấu); chuẩn hóa theo tập huấn luyện. Đầu vào mỗi nút từ 23 lên 30;
mô hình có 3,964 tham số; huấn luyện trên cửa sổ không biên độ cao của tập huấn luyện; 4 lần huấn luyện
(Kaggle, mỗi lần khoảng 3.3–3.8 giờ).

**Kết quả trên 15 bệnh nhân thiết kế:** 0.330 @ 23.7 → **0.489 @ 19.8**. Điểm của cửa sổ co giật tăng (trung vị
1.40 → 2.31), nhưng điểm của đoạn biên độ cao không phải co giật **không giảm** (1.02 → 1.02).

**Chấm trên tập kiểm tra (một lần):** 3/76 cơn @ 24.1. AUROC theo cửa sổ tăng 0.640 → 0.680 (6/8 bệnh nhân
tăng), nhưng **cải thiện không chuyển thành cơn bắt được.** Cơn ngắn bắt được 0/18.

**Thử dùng kernel CPD trực tiếp làm bộ phát hiện:** không đạt (0.250 @ 5.8 so với 0.489 @ 19.8).

**Chẩn đoán cuối giai đoạn này:**
- Muốn bắt cơn khi chỉ cho phép khoảng 2 % thời gian vượt ngưỡng, đỉnh cơn phải nằm trong 2 % điểm cao nhất
  của chính bệnh nhân đó. AUROC 0.65–0.87 còn xa mức đó.
- Thứ chiếm phần đuôi cao của điểm số trên tập kiểm tra là **hoạt động biên độ cao không phải co giật của
  chính bệnh nhân**: 20–50 % đoạn bình thường có điểm vượt đỉnh cơn (trên tập kiểm định chỉ 4 %); bỏ các
  đoạn biên độ cao thì tỉ lệ này còn 0.1–1 %.
- GAE v2 sửa được đầu vào, nhưng "bình thường" vẫn học từ người khác. Bài học từ thí nghiệm mô hình mật độ:
  cần "bình thường" của chính bệnh nhân.

---

## 5. Thích nghi theo từng bệnh nhân, không dùng nhãn

Ý tưởng: giống cách phương pháp DynaSD (phương pháp không giám sát duy nhất trong bảng xếp hạng SzCORE)
học đường nền từ chính bản ghi của bệnh nhân. Vì cơn co giật chỉ chiếm phần rất nhỏ thời gian ghi, học
"bình thường" trên toàn bộ bản ghi của bệnh nhân vẫn không cần nhãn.

| Bước | Kết quả trên 15 bệnh nhân thiết kế | Điều rút ra |
|---|---|---|
| Phân tích phần đuôi cao của điểm số cũ | 95–96 % cửa sổ ở đuôi là biên độ cao; điểm gamma chiếm đuôi ở 12/15 bệnh nhân. Khả năng tách cơn khỏi đoạn biên độ cao: biểu diễn ẩn 0.966, gamma 0.762, sai số tái tạo khoảng 0.53 (gần ngẫu nhiên) | Trong ba điểm, **biểu diễn ẩn của GAE v2 là thứ tách được**; sai số tái tạo gần như không |
| Đo bất thường **theo từng kênh**: với mỗi bệnh nhân và mỗi kênh, học vùng bình thường của 16 con số ẩn, đo khoảng cách (Mahalanobis); lấy kênh bất thường thứ 9 trong 18 | 0.622 @ 24.6; 12/15 bệnh nhân không kém hơn | Mô hình hóa theo kênh mang lại cải thiện |
| Tinh chỉnh (fine-tune) GAE trên toàn bộ bản ghi từng bệnh nhân, không nhãn | 0.628 so với 0.622 | Không chọn: không thấy cơ chế (đoạn biên độ cao không giảm điểm) |
| Đo hiện tượng **trôi theo file** | 84.5 % cửa sổ bình thường có điểm cao nhất nằm trong 1/4 số file có điểm cao nhất của bệnh nhân; các file đó không giàu co giật hơn | Trôi theo file là thật và chiếm phần lớn báo động giả |
| Trừ trung vị trượt ±15 phút trong mỗi file (khử trôi chậm) | 0.681 @ 24.25; mọi lần huấn luyện đều tăng; 13/15 bệnh nhân | Được chọn |
| Cộng thêm điểm tái tạo, gamma, biểu diễn ẩn toàn đồ thị | Đều kém hơn chỉ dùng biểu diễn ẩn theo kênh | **Bỏ** điểm tái tạo và gamma khỏi điểm cuối |
| Ghép các mức lan rộng: kênh thứ 6, 9, 12 và trung bình 18 kênh, mỗi cái đã khử trôi, chuyển thành phân vị của bệnh nhân rồi lấy trung bình đều | 0.668 @ 19.98; trung bình theo bệnh nhân 0.828; kiểm định 0.983 | **Điểm bất thường tổng hợp cuối cùng** (một chuỗi số duy nhất) |
| Kernel CPD làm bộ định vị bắt đầu/kết thúc | Sai số bắt đầu 16 → 8 s; kết thúc 20 → 16 s; độ nhạy 0.668 → 0.662 | Được chọn. Nhưng: với thời điểm kết thúc, một quy tắc đơn giản (lấy đoạn liên tục vượt ngưỡng) cho 12 s, tốt hơn CPD |
| Một nhánh riêng cho cơn ngắn | Không thêm được cơn nào trong giới hạn báo động giả | Không chọn |
| Kiểm tra độ tin cậy: lấy mẫu lại theo bệnh nhân (10,000 lần), so với hệ thống GAE v2 trước đó ở cùng mức báo động giả | Độ nhạy gộp +0.173 [+0.075, +0.287]; trung bình theo bệnh nhân +0.171 [+0.055, +0.303] | Cải thiện không phải do một bệnh nhân, không phải do tiêu thêm báo động giả |

**Chấm trên tập kiểm tra lần này là lần "sạch"** (mọi thiết kế chỉ dùng 15 bệnh nhân thiết kế):

| | Seed 42 | 4 lần huấn luyện |
|---|---|---|
| Độ nhạy gộp | 26/76 = **0.342** | 0.336 ± 0.008 |
| Báo động giả/ngày | 22.2 | 23.9 ± 1.2 |
| Độ chính xác / F1 | 0.092 / 0.145 | |
| Trung bình theo bệnh nhân | **0.508** | 0.498 ± 0.010 |
| Sai số bắt đầu / kết thúc (CPD) | 8 s / 20 s (bộ phát hiện thô: 28 s / 16 s) | |

Báo động giả/ngày khớp đúng mức đã dự đoán trước (23.5). Độ nhạy tăng 8.7 lần so với GAE v2 trước đó
(3/76 → 26/76), nhưng bằng khoảng một nửa so với 15 bệnh nhân thiết kế (0.662 → 0.336), đúng như đã cảnh báo
từ trước rằng tập thiết kế dễ hơn.

Theo từng bệnh nhân (seed 42): chb03 7/7, chb06 2/10, chb13 1/12, chb14 6/8, **chb15 0/20**, chb16 2/10,
chb17 3/3, chb18 5/6.

Nhân không duyệt kết quả này và mở thêm một vòng, mục tiêu độ nhạy gộp ≥ 0.50.

---

## 6. Vòng cuối: phân tích từng cơn bị bỏ sót

**Chính sách công khai:** vòng này có đọc thông tin từ tập kiểm tra, chia làm hai loại, đều được ghi lại:
(1) không dùng nhãn: EEG và đầu ra mô hình của bệnh nhân kiểm tra (hệ thống vốn đã dùng toàn bộ bản ghi của
bệnh nhân, nên đây là thông tin hệ thống tự thấy); (2) có dùng nhãn: ghép thời điểm cơn với điểm số để xem
từng cơn bị sót vì sao. Vì có loại (2), kết quả lần chấm tiếp theo phải ghi là **"có dùng thông tin từ tập
kiểm tra"**, và lần chấm sạch ở Mục 5 vẫn là kết quả kiểm tra độc lập chính.

**Câu hỏi cho từng cơn:** ngưỡng phải nới đến mức nào (bao nhiêu phần trăm thời gian của bệnh nhân) thì mới
chạm tới đỉnh của cơn đó?

| Số cơn chạm được nếu ngưỡng cho phép ≤ | 0.5 % | 1 % | 2 % | 5 % | 10 % |
|---|---|---|---|---|---|
| Tập kiểm tra (76 cơn) | 25.75 | 27.5 | 45.5 | 62.25 | 71.25 |
| 15 bệnh nhân thiết kế (93 cơn) | 60.5 | 66.5 | 74.25 | 85.25 | 90.0 |

(Trung bình 4 lần huấn luyện. Đây là giới hạn trên, chưa tính báo động giả.)

**Đọc bảng:**
- **chb15 là "suýt trúng":** 0/20 cơn ở mức 1 %, nhưng 10.5/20 ở mức 2 % (trung vị 1.9 %). Cơn của chb15 nằm
  ngay dưới ngưỡng.
- **chb06, chb13, chb16 nằm sâu hơn (2–10 %):** cần thay đổi lớn hơn một ngưỡng.

**Các giả thuyết đã kiểm tra và không được ủng hộ:** dùng ít kênh hơn cho cơn khu trú (cơn chb15 thực ra kích
hoạt khoảng 8 kênh ở đỉnh); bỏ bước khử trôi (làm tệ đi rõ: 25.75 → 13.0 cơn); học vùng bình thường sau khi
bỏ 5 % cửa sổ xa nhất; đầu vào của bệnh nhân kiểm tra lệch khỏi phân bố huấn luyện (không thấy lệch đáng kể);
đổi mức làm mượt. Một ngưỡng chung 2 % cho mọi bệnh nhân tốn 95.1 báo động giả/ngày trên tập thiết kế, nên
chỉ có ngưỡng **riêng từng bệnh nhân** là chi trả được.

**Thay đổi được chọn: ngưỡng riêng cho từng bệnh nhân, không dùng nhãn.** Với mỗi bệnh nhân, tính tỉ lệ thời
gian mà điểm trung bình vượt một mức k cố định (k = 4.0677, hiệu chỉnh một lần trên 15 bệnh nhân thiết kế);
kẹp tỉ lệ này trong khoảng 0.5 %–2 %; đó là phần thời gian cho phép cảnh báo của bệnh nhân. Trên 15 bệnh
nhân thiết kế: 0.670 @ 23.25 sau CPD, trung bình theo bệnh nhân 0.832, không bệnh nhân nào giảm.

**Kết quả lần chấm cuối trên tập kiểm tra (có dùng thông tin từ tập kiểm tra):**

| | Seed 42 | 4 lần huấn luyện |
|---|---|---|
| Độ nhạy gộp | 37/76 = **0.487** | 0.477 ± 0.022 |
| Báo động giả/ngày | 27.5 | 29.2 ± 1.3 |
| Độ chính xác / F1 | 0.104 / 0.172 | |
| Trung bình theo bệnh nhân | **0.577** | 0.567 ± 0.019 |
| Trước bước định vị CPD | 38/76 = 0.500 @ 28.4 | |
| Sai số bắt đầu (bộ phát hiện → CPD) | 32 s → **12 s** | |
| Sai số kết thúc (bộ phát hiện / CPD / quy tắc đoạn liên tục) | 20 s / 24 s / 16 s | |

**Phải nói thẳng:**
- Mục tiêu 0.50 **chưa đạt** (thiếu 1 cơn ở seed 42, tính sau bước định vị).
- **Toàn bộ phần tăng đến từ chb15 (0 → 11/20)**; mọi bệnh nhân khác giữ nguyên kết quả.
- Mức kẹp trên 2 % chỉ có tác dụng với chb15 trên tập kiểm tra, không có tác dụng với bệnh nhân nào trong
  tập thiết kế (cao nhất 1.1 %). Mức này được đặt sau khi đã thấy kết quả lần chấm sạch.
- Lấy mẫu lại theo bệnh nhân, so với lần chấm sạch: độ nhạy gộp +0.141 [0.000, 0.333], báo động giả
  +5.27/ngày [+0.37, +13.60].

Sau lần này, công việc hiệu năng đóng lại. Tập kiểm tra CHB-MIT đã dùng hết: mọi thử nghiệm mới cần dữ liệu mới.

---

## 7. Hệ thống đã chốt, mô tả từng bước

1. **Tiền xử lý (không đổi):** CHB-MIT, 18 kênh lưỡng cực, lọc 0.5–60 Hz và lọc khấc 60 Hz, cửa sổ 4 s không
   chồng lấn, chuẩn hóa theo bệnh nhân.
2. **Đồ thị mỗi cửa sổ (không đổi):** 18 nút, cạnh là mức đồng bộ pha (wPLI) và đồng bộ đường bao biên độ (AEC),
   giữ 20 % cạnh mạnh nhất.
3. **GAE v2:** mỗi nút có 30 đặc trưng (hàng kề 18, năng lượng 5 dải, và 7 đặc trưng giữ biên độ); nén mỗi nút
   thành 16 số.
4. **Điểm bất thường theo kênh (không nhãn):** với mỗi bệnh nhân và mỗi kênh, học vùng bình thường của 16 số
   ẩn trên toàn bộ bản ghi của bệnh nhân; điểm = khoảng cách Mahalanobis đến vùng đó; chuẩn hóa bền vững.
5. **Mức lan rộng trong không gian:** lấy kênh bất thường thứ 6, 9, 12 trong 18 và trung bình 18 kênh. Ý nghĩa:
   "có ít nhất 6 / 9 / 12 kênh cùng bất thường" — đặc trưng không gian.
6. **Khử trôi theo thời gian:** trừ trung vị trượt ±15 phút trong cùng file. Vì dùng cả 15 phút sau, bước này
   hợp với **xem lại EEG sau khi ghi** (đúng định vị đề tài), không phải báo động thời gian thực.
7. **Điểm bất thường tổng hợp:** đổi mỗi thành phần thành phân vị trong bệnh nhân, lấy trung bình đều → một
   chuỗi điểm duy nhất ("ensemble anomaly score" trong đơn đăng ký).
8. **Phát hiện:** làm mượt 5 cửa sổ (20 s); ngưỡng = phần thời gian cho phép của bệnh nhân (0.5–2 %, tính từ
   điểm số, không nhãn); đoạn liên tục vượt ngưỡng là một sự kiện; gộp sự kiện cách nhau dưới 90 s.
9. **Định vị bằng kernel CPD (phi tham số):** quanh mỗi sự kiện ±60 s, tìm đúng 2 điểm thay đổi trên điểm chưa
   làm mượt = thời điểm bắt đầu và kết thúc. Nếu không tìm được một "cái bướu" hợp lệ thì giữ ranh giới của
   bộ phát hiện.

Những gì đã bỏ so với hệ thống cũ: điểm tái tạo và điểm gamma không còn trong điểm cuối; PELT không còn làm
bộ phát hiện. Không có bước nào dùng nhãn cơn.

---

## 8. Kiểm định ngoài: dữ liệu chưa từng dùng

Để có bằng chứng sạch cho hệ thống cuối, ta chạy **nguyên hệ thống đã chốt, không chỉnh gì, một lần duy nhất**,
trên hai bộ dữ liệu chưa từng dùng ở bất kỳ bước thiết kế nào. Cấu hình chạy được ghi trước khi xử lý bất kỳ
bản ghi nào.

- **chb24:** bệnh nhân CHB-MIT nằm ngoài cả 23 bệnh nhân đã chia; 16 cơn, 21.3 giờ.
- **Siena Scalp EEG:** 14 bệnh nhân **người lớn** (GAE được huấn luyện trên trẻ em), 47 cơn, 140 giờ. Điều chỉnh
  bắt buộc, không dùng nhãn: dựng 18 kênh lưỡng cực từ cách ghi gốc, hạ tần số mẫu 512 → 256 Hz, lọc khấc
  50 Hz. Nhãn lấy từ chính bộ chuyển đổi của bảng xếp hạng SzCORE.
- Trước khi chấm, có hai bước kiểm tra tái tạo: dựng lại một file của chb03 trên máy khác ra đúng đặc trưng,
  và tái tạo đúng kết quả cũ của chb03.

| Bộ dữ liệu | Seed 42 | 4 lần huấn luyện | Sai số bắt đầu / kết thúc (CPD) |
|---|---|---|---|
| chb24 | 14/16 = **0.875** @ 29.5; độ chính xác 0.350, F1 0.500 | 0.828 ± 0.060 @ 28.4 | 4 s / 4 s |
| Siena, gộp | 33/47 = **0.702** @ 44.0 | 0.617 ± 0.060 @ 43.8 | 20 s / 28 s |
| Siena, trung bình theo bệnh nhân (chính thức) | 0.748 @ 41.5 | **0.633** ± 0.079; độ chính xác 0.160; F1 0.226; **41.0** báo động giả/ngày | |

Khoảng tin cậy (lấy mẫu lại theo bệnh nhân) của Siena, trung bình theo bệnh nhân: [0.477, 0.777].

**So sánh trên cùng dữ liệu Siena** (kết quả công bố trong bảng xếp hạng SzCORE, trung bình theo bệnh nhân):

| Phương pháp | Loại | Độ nhạy | Độ chính xác | F1 | Báo động giả/ngày |
|---|---|---|---|---|---|
| DynaSD | Không giám sát (duy nhất) | 0.664 | 0.126 | 0.170 | 77.7 |
| **Hệ thống của ta** (4 lần) | Không giám sát | 0.633 | 0.160 | 0.226 | 41.0 |
| Zhu 2023 | Có giám sát | 0.674 | | | 15.3 |
| SeizureTransformer | Có giám sát, huấn luyện trên dữ liệu khác | 0.685 | | | 1.0 |

Đọc: độ nhạy tương đương phương pháp không giám sát tốt nhất, với **khoảng một nửa số báo động giả** và F1
cao hơn. Các phương pháp có giám sát vẫn tốt hơn về báo động giả, điều này là bình thường vì chúng dùng nhãn.

**Giới hạn phải nói:** cùng nhãn và cùng định nghĩa chấm, nhưng ta dùng bộ chấm và đường xử lý tín hiệu của
mình, không chạy bên trong hệ thống của bảng xếp hạng. Trên Siena, báo động giả 41–44/ngày cao hơn mức 40 ta
tự đặt là chấp nhận được; 3 bệnh nhân (PN06, PN07, PN16) có trên 70 báo động giả/ngày; PN05 bắt 0/3.

Để tham khảo thêm (khác bệnh nhân, không so trực tiếp được): DynaSD trên toàn bộ CHB-MIT đạt 0.608 (độ chính
xác 0.199, F1 0.218) @ 23.2 báo động giả/ngày, trung bình theo bệnh nhân.

---

## 9. Vì sao hiệu năng trên 8 bệnh nhân kiểm tra vẫn chưa cao

### 9.1 Kết quả bị chi phối bởi vài bệnh nhân

| Bệnh nhân | Số cơn | Bắt được (hệ thống cuối, seed 42) | Đặc điểm |
|---|---|---|---|
| chb03 | 7 | 7 | |
| chb06 | 10 | 2 | 10 cơn toàn thể, dài 12–20 s; điểm số **đảo ngược** (cơn có điểm thấp hơn nền) dưới mọi mô hình từng thử, AUROC 0.25–0.38 |
| chb13 | 12 | 1 | Cơn nằm ở mức 2–5 %, bị các trạng thái biên độ cao của chính bệnh nhân lấn át (89 % phần đuôi là đoạn biên độ cao) |
| chb14 | 8 | 6 | |
| chb15 | 20 | 11 | Cơn "suýt trúng", ngay dưới ngưỡng 2 % |
| chb16 | 10 | 2 | 10 cơn dài 6–14 s, ngắn hơn cả mức làm mượt 20 s |
| chb17 | 3 | 3 | |
| chb18 | 6 | 5 | |
| **Tổng** | **76** | **37** | |

- **Ba bệnh nhân chb06, chb13, chb16 giữ 32/76 cơn và hệ thống chỉ bắt được 5.** Năm bệnh nhân còn lại:
  32/44 cơn (tính từ số liệu: 37 − 5 = 32; 76 − 32 = 44).
- chb15 (20 cơn) và chb13 (12 cơn) chiếm 42 % số cơn của tập kiểm tra. Vì vậy độ nhạy **gộp** thực chất là
  câu chuyện của hai bệnh nhân. Đây là lý do SzCORE dùng **trung bình theo bệnh nhân** làm số chính thức
  (seed 42: 0.577 ở hệ thống cuối, 0.508 ở lần chấm sạch).

### 9.2 Cơn ngắn

23/76 cơn kiểm tra ngắn hơn 20 giây theo nhãn (chb06 8, chb13 2, chb14 3, chb16 10). Tập thiết kế chỉ có 3 cơn
ngắn, nên không thể thiết kế và kiểm chứng giải pháp cho cơn ngắn mà không chạm vào tập kiểm tra. Với cửa sổ
4 giây và làm mượt 20 giây, cơn 6–14 giây gần như bị pha loãng.

### 9.3 Tập kiểm tra khó hơn tập thiết kế, đo được

- Trên tập kiểm tra, 20–50 % đoạn bình thường có điểm cao hơn đỉnh cơn; trên tập kiểm định chỉ khoảng 4 %.
- 12 trong 15 bệnh nhân thiết kế đã được dùng để huấn luyện GAE.
- Ở mức ngưỡng của hệ thống (0.5 %), chạm được 60.5/93 cơn thiết kế nhưng chỉ 25.75/76 cơn kiểm tra.
- Kết quả: từ tập thiết kế sang tập kiểm tra, độ nhạy giảm khoảng một nửa. Điều này đã được ghi và cảnh báo
  trước khi chấm, không phải giải thích sau.

### 9.4 Với 8 bệnh nhân, khoảng tin cậy rất rộng

Lần chấm sạch: độ nhạy gộp 0.336 [0.133, 0.670], trung bình theo bệnh nhân 0.498 [0.226, 0.770]. Khoảng
tin cậy đã chứa mức 0.50. Bỏ riêng chb15 thì độ nhạy gộp là 0.464. Nói cách khác, với 8 bệnh nhân, một hai
bệnh nhân khó quyết định con số.

### 9.5 Bản chất bài toán không giám sát

Hệ thống chỉ biết "điều gì khác thường so với chính bệnh nhân này". Một cơn co giật nhỏ hơn, ngắn hơn hoặc
đều đặn hơn các trạng thái biên độ cao bình thường của bệnh nhân (ngủ, cử động, nhai...) thì không thể được
xếp lên trên chỉ bằng mức "khác thường". Mô hình có giám sát làm được (0.702 @ 20.5 trên tập thiết kế) vì
nó học từ nhãn cơn. Đề tài đăng ký là không giám sát nên không dùng hướng đó.

### 9.6 Độ chính xác thấp là đặc điểm chung của lĩnh vực

Với khoảng 25–30 báo động giả/ngày và chỉ vài cơn mỗi ngày, độ chính xác tất yếu thấp (khoảng 0.1). Phương
pháp không giám sát duy nhất của bảng xếp hạng cũng chỉ đạt 0.199 trên CHB-MIT và 0.126 trên Siena. Với mục
đích xem lại EEG sau khi ghi, điều quan trọng là phần thời gian bác sĩ phải xem: trên 15 bệnh nhân thiết kế,
các sự kiện của hệ thống chiếm 1.62 % thời gian ghi (tức là thay vì đọc toàn bộ, bác sĩ đọc khoảng 1.6 %).

---

## 10. Những gì đã thử mà không giúp (vẫn là kết quả có giá trị)

| Hướng | Kết quả | Ý nghĩa |
|---|---|---|
| Định nghĩa "bình thường" chung cho mọi bệnh nhân | Không cải thiện | Phải là bình thường của từng bệnh nhân |
| Tăng kích thước mô hình | Không đổi | Vấn đề ở đầu vào, không ở kích thước |
| Coi đoạn biên độ cao là nhiễu | Gọi 81.5 % cửa sổ co giật là nhiễu | Biên độ cao ≠ nhiễu |
| Tinh chỉnh GAE trên từng bệnh nhân | Không cải thiện đáng kể | Việc học vùng bình thường theo từng bệnh nhân ở đầu ra có lẽ đã làm điều tương tự |
| Đường nền ngắn (10–30 phút đầu mỗi file) | Tệ hơn rõ rệt | Đường nền ngắn chỉ chứa một trạng thái, mọi thứ khác trông bất thường |
| Ghép thêm điểm tái tạo / gamma | Kém hơn | Sai số tái tạo gần như không tách được cơn khỏi đoạn biên độ cao |
| Kernel CPD hoặc PELT làm bộ phát hiện | Kém hơn bộ ngưỡng | CPD hợp với vai trò định vị, không hợp vai trò phát hiện |
| Nhánh riêng cho cơn ngắn | Không thêm cơn nào trong giới hạn báo động giả | Đỉnh cơn ngắn nằm dưới mọi ngưỡng chi trả được |
| CPD đa kênh (18 kênh) làm bộ định vị | Kết thúc tốt nhất (8 s) nhưng mất độ nhạy | Không chọn theo quy tắc ghi trước; là hướng mở rộng |

Kết quả nghiên cứu trước đó về giải thích theo kênh (kênh nào mô hình cho là bất thường có trùng kênh bác sĩ
thấy cơn hay không) vẫn là một kết quả âm đã ghi trước, làm trên hệ thống cũ, và được báo cáo như vậy.

---

## 11. Vì sao luận văn đủ để bảo vệ

**1. Đáp ứng đúng đơn đăng ký (không đổi đề tài, không đổi mục tiêu).**

| Yêu cầu trong đơn | Hệ thống hiện tại |
|---|---|
| Khung không giám sát | Không bước nào dùng nhãn cơn; mọi thống kê theo bệnh nhân đều học trên toàn bộ bản ghi, không nhãn |
| Mục tiêu 1: chấm điểm bất thường không giám sát với đặc trưng không gian–thời gian | GAE trên đồ thị 18 kênh (không gian), bất thường theo từng kênh và mức lan rộng nhiều kênh (không gian), khử trôi theo thời gian |
| Mục tiêu 2: định vị thời gian bằng CPD phi tham số trên điểm bất thường tổng hợp | Kernel CPD (phi tham số) trên một chuỗi điểm tổng hợp; vai trò đo được: sai số bắt đầu cơn 32 → 12 s (tập kiểm tra, hệ thống cuối), 28 → 8 s (lần chấm sạch), 4 s trên chb24 |
| Trọng tâm tài liệu: hiệu chỉnh ngưỡng và trôi nền | Hai đóng góp chính của giai đoạn này đúng là hai chủ đề đó: ngưỡng riêng từng bệnh nhân không nhãn, và khử trôi theo file |
| Đánh giá mức sự kiện trên CHB-MIT | SzCORE chính thức, bản ghi liên tục, cả gộp và trung bình theo bệnh nhân |

**2. Đánh giá trung thực nhất có thể.** Ta tự phát hiện và sửa chỗ lạc quan của giao thức cũ, chuyển sang bản
ghi liên tục và bộ chấm chuẩn, đọc mã nguồn bộ chấm, công khai mọi lần nhìn vào tập kiểm tra.

**3. Có bằng chứng sạch rằng phương pháp tổng quát hóa.** Trên dữ liệu chưa từng thấy (chb24 và 14 bệnh nhân
người lớn của Siena), không chỉnh gì: 83–88 % cơn của chb24, 62–70 % cơn của Siena; ngang phương pháp không
giám sát duy nhất của bảng xếp hạng với khoảng một nửa báo động giả.

**4. Cải thiện so với điểm xuất phát là thật và có khoảng tin cậy.** Trên cùng 8 bệnh nhân kiểm tra, trên bản
ghi liên tục: từ 2–3/76 lên 26/76 (lần sạch) và 37/76 (hệ thống cuối). Trên tập thiết kế, cải thiện so với
GAE v2 ban đầu có khoảng tin cậy không chứa 0.

**5. Chỗ yếu có nguyên nhân đo được.** Không phải "mô hình không hoạt động" mà là: ba bệnh nhân cụ thể, với cơ
chế cụ thể (cơn rất ngắn; điểm số đảo ngược; bị trạng thái biên độ cao của chính bệnh nhân lấn át), và các
hướng giải quyết cụ thể cho nghiên cứu tiếp theo (cửa sổ ngắn hơn hoặc chồng lấn cho cơn ngắn; điểm bất
thường hai phía cho cơn đều hơn nền; biểu diễn tách cơn khỏi trạng thái biên độ cao của bệnh nhân).

**6. Định vị đúng ứng dụng.** Hệ thống là công cụ hỗ trợ **xem lại EEG sau khi ghi**, không phải báo động thời
gian thực. Ở vai trò này, chỉ ra khoảng 1.6 % thời gian ghi để bác sĩ xem trước, bắt được khoảng một nửa đến
hai phần ba số cơn, và định vị thời điểm bắt đầu trong khoảng 10 giây, là một nguyên mẫu có ích.

---

## 12. Những điều phải công khai trong báo cáo

1. Số lần đã nhìn vào tập kiểm tra: 7 lần (đánh giá cũ; đánh giá lại hệ thống cũ trên bản ghi liên tục; ứng
   dụng web; một lần thử bộ lọc cảnh báo; lần chấm GAE v2 ban đầu; hai lần chấm hệ thống mới), cộng một lần
   đọc thông tin tập kiểm tra để phân tích cơn bị sót. Kiểm định ngoài là riêng, không tính vào đó.
2. Lần chấm sạch (0.342, trung bình theo bệnh nhân 0.508; 4 lần huấn luyện 0.336 / 0.498) là kết quả kiểm tra độc lập; hệ thống cuối (0.487,
   0.577) được báo cáo bên cạnh, ghi rõ "có dùng thông tin từ tập kiểm tra", và phần tăng là của chb15 tại
   một mức kẹp chỉ có tác dụng trên tập kiểm tra.
3. Khoảng 40 quyết định thiết kế đã được đưa ra trên 15 bệnh nhân thiết kế, nên số trên tập thiết kế lạc quan;
   từ thiết kế sang kiểm tra giảm khoảng 2 lần.
4. Số theo giao thức cũ và số trên bản ghi liên tục không bao giờ gộp thành một con số.
5. Không loại bệnh nhân khó khỏi kết quả chính. (Một số công trình loại chb06, chb13, chb14, chb16 và dùng
   nhãn để chỉnh ngưỡng từng bệnh nhân; nếu cần so sánh thì chỉ đặt cạnh, không thay thế.)
6. Ứng dụng web hiện vẫn chạy hệ thống cũ (0.211 @ 52.4); muốn chạy hệ thống mới cần xây lại.

---

## 13. Những điểm cần cô quyết định

1. **Báo cáo trình bày giao thức cũ thế nào?** Đề xuất: số chính là bản ghi liên tục; giao thức cũ hoặc bỏ,
   hoặc nêu ngắn như một giao thức có điều kiện thuận lợi, kèm giải thích vì sao lạc quan.
2. **Học "bình thường" trên toàn bộ bản ghi của bệnh nhân (không nhãn) có được coi là "không giám sát" không?**
   Hệ thống không dùng nhãn, nhưng đổi từ "một mô hình chung cho mọi bệnh nhân" sang "thích nghi với từng
   bệnh nhân mới mà không cần nhãn". DynaSD làm cùng kiểu.
3. **Vai trò của CPD:** từ "bộ phát hiện" (PELT ở hệ thống cũ) sang "bộ định vị thời điểm bắt đầu/kết thúc"
   (kernel CPD). Điểm mạnh đo được ở thời điểm bắt đầu; thời điểm kết thúc chưa tốt hơn quy tắc đơn giản.
4. **Cách công khai các lần nhìn tập kiểm tra** và việc đặt kết quả sạch và kết quả cuối cạnh nhau.
5. **Số chính dùng gộp hay trung bình theo bệnh nhân?** Đề xuất: báo cả hai, coi trung bình theo bệnh nhân là
   số chính thức như SzCORE.
6. **Có xây lại ứng dụng web cho hệ thống mới trước hạn nộp 15/10 hay không.**

---

## 14. Câu hỏi cô có thể hỏi và cách trả lời

**"Trước báo 0.618, giờ chỉ 0.34–0.49. Mô hình tệ đi à?"**
Không. Cùng 8 bệnh nhân, nhưng cách đo khác. Đo theo cách cũ thì loại bỏ trước những đoạn gây báo động giả.
Đo trên bản ghi liên tục thì hệ thống cũ chỉ được 2/76 đến 23/76 cơn. Hệ thống mới, đo cùng cách trung thực
đó, được 26/76 (sạch) và 37/76 (cuối).

**"Tại sao không đạt 0.5?"**
Ba bệnh nhân (32 cơn) có cơ chế mà một hệ thống không giám sát khó xử lý: cơn rất ngắn, điểm số đảo ngược,
hoặc cơn yếu hơn trạng thái bình thường biên độ cao của chính bệnh nhân. Theo cách tính chính thức (trung
bình theo bệnh nhân) thì đạt 0.577. Trên dữ liệu mới chưa từng thấy thì đạt 0.63–0.88.

**"Có phải chỉnh cho vừa tập kiểm tra không?"**
Lần chấm sạch được thiết kế hoàn toàn không dùng tập kiểm tra và là kết quả độc lập chính. Lần cuối có dùng
thông tin từ tập kiểm tra, được ghi rõ. Để có bằng chứng sạch cho hệ thống cuối, ta chạy nó một lần trên
chb24 và Siena, không chỉnh gì.

**"So với các nghiên cứu khác?"**
Trên cùng dữ liệu Siena, phương pháp không giám sát duy nhất trong bảng xếp hạng chuẩn đạt độ nhạy 0.664 với
77.7 báo động giả/ngày; ta đạt 0.633 với 41.0. Các phương pháp có giám sát tốt hơn vì dùng nhãn.

**"Còn dùng CPD không, nó làm gì?"**
Có. Kernel CPD (phi tham số) chạy trên điểm bất thường tổng hợp để xác định thời điểm bắt đầu và kết thúc
của mỗi sự kiện. Nó giảm sai số thời điểm bắt đầu từ 2 đến 3.5 lần so với ranh giới của bộ phát hiện
(16 → 8 s trên tập thiết kế, 28 → 8 s ở lần chấm sạch, 32 → 12 s ở hệ thống cuối). Thời điểm kết thúc thì
chưa tốt hơn một quy tắc đơn giản, và ta nói rõ điều đó.

**"Sao báo động giả nhiều vậy?"**
Mục đích là xem lại EEG sau khi ghi. Các sự kiện chiếm khoảng 1.6 % thời gian ghi (trên tập thiết kế); bác sĩ
xem phần đó trước thay vì đọc toàn bộ. Mức báo động giả của ta tương đương hoặc thấp hơn phương pháp không
giám sát được công bố.

**"Sao không bỏ các bệnh nhân khó?"**
Bỏ đi thì số đẹp hơn nhưng là chọn lọc kết quả. Ta giữ cả 8 và giải thích từng bệnh nhân.

---

*Nguồn số liệu: hồ sơ giai đoạn hiệu năng (bản ngày 07/10/2026), kết quả kiểm định ngoài, bảng kết quả
của hệ thống cũ. Các số "tính từ số liệu" được ghi rõ tại chỗ.*
