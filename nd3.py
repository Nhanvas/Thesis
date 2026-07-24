# -*- coding: utf-8 -*-
"""Sinh sơ đồ tổng thể đề tài (SVG) - lưới 5 làn x 6 tầng + dải nền dùng chung."""
from PIL import ImageFont
from xml.sax.saxutils import escape

FD = "/usr/share/fonts/truetype/dejavu/"
_cache = {}
def F(size, style="r"):
    k = (size, style)
    if k not in _cache:
        fn = {"r": "DejaVuSans.ttf", "b": "DejaVuSans-Bold.ttf", "i": "DejaVuSans-Oblique.ttf"}[style]
        _cache[k] = ImageFont.truetype(FD + fn, size)
    return _cache[k]

def tw(text, size, style="r"):
    return F(size, style).getlength(text)

def wrap(text, maxw, size, style="r"):
    out = []
    for para in text.split("\n"):
        words = para.split(" ")
        cur = ""
        for w in words:
            t = (cur + " " + w).strip()
            if tw(t, size, style) <= maxw or not cur:
                cur = t
            else:
                out.append(cur); cur = w
        out.append(cur)
    return out

# ---------------------------------------------------------------- palette
INK      = "#16202B"
INK2     = "#33414F"
MUTED    = "#5C6B7A"
NOTE     = "#4A5A69"
WARN     = "#9C3412"
OK       = "#136A3A"
STARC    = "#8A4B00"
PAGE     = "#FFFFFF"

VOICE_D  = "#8A4B12"; VOICE_M = "#C57A2E"; VOICE_L = "#FDF3E7"; VOICE_B = "#E5C49B"
EEG_D    = "#123E5C"; EEG_M   = "#2E6D96"; EEG_L   = "#EAF2F8"; EEG_B   = "#A9C7DC"
TIER_A   = "#FBFBF9"; TIER_B  = "#F3F5F2"
GREY_B   = "#C9D2D9"
BAND1_F  = "#F4F1E8"; BAND1_B = "#C9BE9E"; BAND1_D = "#6B5A2E"
BAND2_F  = "#F2F4F6"; BAND2_B = "#C2CBD3"; BAND2_D = "#2E3D4B"

# ---------------------------------------------------------------- geometry
W        = 3060
MARG     = 26
GUT      = 196          # left label gutter
NCOL     = 5
CGAP     = 14
CW       = (W - 2*MARG - GUT - (NCOL-1)*CGAP) // NCOL
CX       = [MARG + GUT + i*(CW+CGAP) for i in range(NCOL)]
PAD      = 11
TXTW     = CW - 2*PAD

S_H, S_P, S_N = 12.8, 11.4, 11.1
LH_H, LH_P    = 16.4, 14.9

# ---------------------------------------------------------------- content dsl
def h(t):  return ("h", t)
def p(t):  return ("p", t)
def b(t):  return ("b", t)
def n(t):  return ("n", "\u25b8 " + t)
def wn(t): return ("w", "\u26a0 " + t)
def ok(t): return ("o", "\u2714 " + t)
def st(t): return ("s", "\u2605 " + t)
def row(items, title=None): return ("row", items, title)   # items = list of (label, blocks)
def branch(items, title=None): return ("branch", items, title)

def block_lines(kind, text, width):
    if kind == "h":  return wrap(text, width, S_H, "b"), S_H, LH_H, "b"
    if kind == "b":  return wrap(text, width, S_P, "b"), S_P, LH_P, "b"
    if kind in ("n",): return wrap(text, width, S_N, "i"), S_N, LH_P, "i"
    return wrap(text, width, S_P, "r"), S_P, LH_P, "r"

def elem_height(el, width):
    if el[0] == "row":
        _, items, title = el
        k = len(items)
        sw = (width - (k-1)*8) / k
        hh = 0
        for lab, blocks in items:
            hh = max(hh, 8 + LH_H + 2 + blocks_height(blocks, sw-16) + 8)
        return hh + (LH_H + 3 if title else 0)
    if el[0] == "branch":
        _, items, title = el
        hh = (LH_H + 3) if title else 0
        for lab, blocks in items:
            hh += 8 + LH_H + 2 + blocks_height(blocks, width - 30 - 16) + 8 + 9
        return hh
    lines, size, lh, sty = block_lines(el[0], el[1], width)
    return len(lines)*lh + 4

def blocks_height(blocks, width):
    return sum(elem_height(e, width) for e in blocks)

# ================================================================ CONTENT
COLS = [
 dict(tag="NỘI DUNG 1", sub="Giọng nói tiếng Việt \u2192 Sàng lọc sớm bệnh Alzheimer",
      meta="Đối tác: BV Quân y 175 + ĐH Bách Khoa \u00b7 Nhân sự: Đức + team thầy Thơ",
      core="SẢN PHẨM LÕI \u2013 có phần mềm & tác nhân ảo", mod="voice", dis="ALZHEIMER"),
 dict(tag="NỘI DUNG 4", sub="Giọng nói tiếng Việt \u2192 Sàng lọc trầm cảm + khám phá kiểu hình",
      meta="Đối tác: BV Nguyễn Tri Phương \u00b7 Nhân sự: Thanh Nhật",
      core=None, mod="voice", dis="TRẦM CẢM"),
 dict(tag="NỘI DUNG 3", sub="EEG dài hạn \u2192 Phát hiện, khu trú & theo dõi cơn động kinh",
      meta="Đối tác: BV Quân y 175 + BV Nguyễn Tri Phương + ĐH Bách Khoa \u00b7 Nhân sự: Trung Nhân + Minh + team thầy Thơ",
      core="SẢN PHẨM LÕI \u2013 có phần mềm \u00b7 ĐÃ CÓ KẾT QUẢ SƠ BỘ", mod="eeg", dis="ĐỘNG KINH"),
 dict(tag="NỘI DUNG 2", sub="EEG / TMS-EEG \u2192 Dự đoán đáp ứng điều trị TMS ở Alzheimer",
      meta="Đối tác: BV Quân y 175 \u00b7 Nhân sự: SV + cô Lụa",
      core=None, mod="eeg", dis="ALZHEIMER"),
 dict(tag="NỘI DUNG 5", sub="EEG \u2192 Dự đoán đáp ứng điều trị rTMS ở trầm cảm",
      meta="Đối tác: BV Quân y 175 \u00b7 Nhân sự: SV + cô Lụa",
      core=None, mod="eeg", dis="TRẦM CẢM"),
]

TIERS = [
 ("\u2460", "ĐỐI TƯỢNG &\nTHIẾT KẾ\nNGHIÊN CỨU", [
  # ND1
  [h("Cắt ngang \u00b7 kết hợp nghiên cứu lâm sàng và phát triển sản phẩm, 5 giai đoạn kế thừa nhau"),
   p("GĐ1 tổng quan y văn + khảo sát nhu cầu bác sĩ \u2192 GĐ2 xây quy trình chuẩn & hạ tầng kỹ thuật \u2192 GĐ3 thu dữ liệu \u2192 GĐ4 mô hình AI \u2192 GĐ5 tích hợp & đánh giá trong môi trường lâm sàng"),
   b("GĐ3: n \u2248 60 (30 bệnh nhân Alzheimer / 30 người khỏe mạnh)"),
   b("GĐ5: n \u2248 20 \u2013 so sánh 2 hình thức hướng dẫn thu dữ liệu: bác sĩ trực tiếp vs tác nhân ảo"),
   n("Tuổi, giới và TRÌNH ĐỘ HỌC VẤN được đưa vào mô hình như biến hiệu chỉnh: ở Việt Nam học vấn ảnh hưởng điểm test nhận thức một cách độc lập với bệnh lý, nếu không kiểm soát mô hình sẽ học đặc điểm nhân khẩu thay vì dấu hiệu bệnh")],
  # ND4
  [h("Quan sát cắt ngang \u00b7 TIẾN CỨU \u00b7 bệnh \u2013 chứng"),
   b("n \u2248 100 người có dữ liệu đạt yêu cầu: 60 trầm cảm / 40 chứng khỏe mạnh"),
   p("Pilot 8\u201312 người trước khi thu chính thức (kiểm tra độ dễ hiểu của hướng dẫn, thời lượng nhiệm vụ, chất lượng âm thanh); tuyển dư 5\u201310% dự phòng rút lui / bản ghi hỏng"),
   p("Ghép tương đối 2 nhóm theo tuổi, giới, học vấn; nếu không ghép được thì đưa vào mô hình như đồng biến"),
   n("Ưu tiên số lượng ở nhóm bệnh vì cần đủ mẫu cho cả bài toán phân loại lẫn bài toán khám phá kiểu hình"),
   n("Thiết kế tiến cứu cho phép kiểm soát đồng nhất thiết bị, không gian, khoảng cách micro, nội dung và trình tự nhiệm vụ \u2192 hạn chế mô hình khai thác khác biệt kỹ thuật thay vì khác biệt bệnh lý")],
  # ND3
  [h("HỒI CỨU \u00b7 ĐA TRUNG TÂM \u2013 khai thác bản ghi đã thực hiện theo chỉ định lâm sàng"),
   n("Ưu thế tiến độ: có sẵn dữ liệu để xây mô hình ngay từ đầu, không phụ thuộc tốc độ tuyển bệnh; kho dữ liệu tiếp tục lớn lên theo hoạt động ghi thường quy"),
   b("BV Quân y 175 \u2013 bản ghi dài hạn > 24 giờ là nguồn chính (tỷ lệ bản ghi bắt được cơn 67\u201370%, phần lớn thuộc thể cục bộ)."),
   p("Bản ghi giấc ngủ ngắn và thường quy tuy ít bắt được cơn nhưng đóng vai trò DỮ LIỆU NỀN quy mô lớn để đo và tối ưu tỷ lệ báo động giả"),
   b("BV Nguyễn Tri Phương \u2013 50\u201360 ca có cơn, toàn bộ thuộc nhóm > 24 giờ, nhiều ca có hơn 1 cơn nên số sự kiện lớn hơn số ca. Giá trị đặc thù: CÓ SẴN nhãn kênh liên quan và nhãn thể cơn cục bộ / toàn thể"),
   wn("Cỡ mẫu tính theo HAI đơn vị khác nhau: bệnh nhân = đơn vị phân tách dữ liệu; SỰ KIỆN CƠN = đơn vị đánh giá hiệu năng. Với độ nhạy kỳ vọng \u2248 80%, cần \u2248 60 sự kiện để nửa khoảng tin cậy 95% \u2264 \u00b110% (hoặc \u2248 43 sự kiện nếu chấp nhận \u00b112%)")],
  # ND2
  [h("Quan sát DỌC trên bệnh nhân suy giảm nhận thức nhẹ / Alzheimer có chỉ định điều trị TMS"),
   b("Giai đoạn thí điểm \u2265 10 bệnh nhân, mở rộng khi nguồn bệnh cho phép"),
   b("3 mốc đo: T0 (bắt đầu liệu trình) \u2013 T2 (giữa liệu trình) \u2013 T4 (kết thúc liệu trình)"),
   p("Tiêu chuẩn lựa chọn/loại trừ dựa trên chẩn đoán, mức độ bệnh, khả năng thực hiện bài đánh giá nhận thức, thuốc đang dùng và yêu cầu an toàn của TMS"),
   p("Ghi nhận đầy đủ thông số điều trị: vị trí kích thích, số buổi, tần số, cường độ, số xung, mức độ hoàn thành liệu trình"),
   n("Các mốc đánh giá có thể điều chỉnh theo phác đồ thực tế nhưng phải xác định TRƯỚC và áp dụng thống nhất trong từng nhóm dữ liệu"),
   wn("Cỡ mẫu nhỏ \u2192 mọi kết quả bắt buộc báo cáo kèm mức biến thiên hoặc khoảng tin cậy và diễn giải thận trọng")],
  # ND5
  [h("Quan sát DỌC trên bệnh nhân rối loạn trầm cảm chủ yếu (MDD) điều trị rTMS"),
   b("3 mốc đo: T0 \u2013 T2 \u2013 T4, tương ứng liệu trình chuẩn 4\u20136 tuần (20\u201330 buổi kích thích)"),
   p("Biến nền thu song song với EEG: tuổi, giới, trình độ học vấn, số đợt trầm cảm, mức độ kháng trị, thuốc đang dùng, điểm triệu chứng và thông số TMS"),
   wn("BỐI CẢNH TẠO RA GIÁ TRỊ CỦA ĐỀ TÀI: rTMS chỉ đạt đáp ứng ở khoảng 45\u201355% bệnh nhân, tỷ lệ thuyên giảm còn thấp hơn, trong khi liệu trình kéo dài nhiều tuần và tốn kém"),
   n("Y văn cho thấy mô hình EEG dự báo NHÓM KHÔNG ĐÁP ỨNG chính xác hơn nhóm đáp ứng \u2192 công cụ được định vị như bộ lọc LOẠI TRỪ SỚM, giúp bệnh nhân tránh một liệu trình dài ít triển vọng và sớm cân nhắc phương án thay thế")],
 ]),

 ("\u2461", "QUY TRÌNH\nTHU NHẬN &\nNHÃN THAM\nCHIẾU", [
  [h("BỘ TÁC VỤ KHAI THÁC LỜI NÓI"),
   p("Đọc văn bản \u00b7 Mô tả tranh \u00b7 Kể lại câu chuyện \u00b7 Trả lời câu hỏi & hội thoại tự nhiên"),
   b("Sàng lọc tác vụ và đặc trưng theo 5 tiêu chí: (i) mức phụ thuộc ngôn ngữ \u2013 văn hóa; (ii) khả năng khái quát giữa các tác vụ; (iii) chi phí tính toán; (iv) độ ổn định giữa các thiết bị ghi âm; (v) tính khả thi trong môi trường lâm sàng"),
   wn("Hình Cookie Theft KHÔNG dùng nguyên trạng \u2013 nếu sử dụng phải điều chỉnh theo bối cảnh văn hóa và người nói tiếng Việt"),
   h("NHÃN THAM CHIẾU"),
   p("Chẩn đoán của bác sĩ + kết quả bộ test đánh giá nhận thức + thông tin nhân khẩu học"),
   n("Ghi kèm mỗi bản thu: thiết bị sử dụng, tần số lấy mẫu, mức nhiễu môi trường, kỹ thuật viên thực hiện, chất lượng bản ghi \u2013 để phân tích ảnh hưởng của điều kiện thu tới hiệu năng")],

  [h("PHIÊN THU 20\u201330 PHÚT, 7 BƯỚC CHUẨN HÓA"),
   p("\u2460 Giới thiệu & ký chấp thuận  \u2461 Nhân khẩu học và thông tin nền  \u2462 Đánh giá lâm sàng  \u2463 Đọc văn bản trung tính 150\u2013250 từ (1\u20132 phút)  \u2464 Mô tả tranh (2\u20133 phút)  \u2465 Nói tự do chủ đề trung tính (2\u20133 phút)  \u2466 PHỎNG VẤN BÁN CẤU TRÚC thích nghi từ DAIC-WOZ (10\u201315 phút, 11 nhóm chủ đề: khí sắc, hứng thú, năng lượng, giấc ngủ, tập trung, công việc, quan hệ, sự kiện tích cực, căng thẳng, cách đối phó, kỳ vọng tương lai)"),
   h("NHÃN THAM CHIẾU"),
   p("Chẩn đoán của bác sĩ chuyên khoa tâm thần (hỗ trợ bằng MINI hoặc công cụ tương đương) \u00b7 PHQ-9 phiên bản tiếng Việt dùng như BIẾN LIÊN TỤC \u00b7 HAMD-17 do người đã tập huấn thực hiện"),
   h("ĐIỀU KIỆN THU ÂM"),
   p("WAV không nén \u00b7 fs \u2265 16 kHz (ưu tiên 44,1 / 48 kHz) \u00b7 \u2265 16-bit \u00b7 micro cách miệng 15\u201320 cm \u00b7 ghi đoạn thử kiểm tra clipping và nhiễu nền trước mỗi phiên"),
   n("Thu 2 kênh riêng cho người phỏng vấn nếu điều kiện cho phép; chỉ giọng người tham gia được đưa vào mô hình để mô hình không khai thác nội dung câu hỏi"),
   wn("KHÔNG áp dụng khử nhiễu làm thay đổi đáng kể cao độ, năng lượng, khoảng dừng hay chất lượng giọng \u2013 đây chính là những thông tin mang dấu hiệu bệnh"),
   wn("Quy trình riêng cho nguy cơ tự sát: chuyển ngay bác sĩ chuyên khoa xử trí. Đầu ra của mô hình AI KHÔNG được dùng để đánh giá hoặc loại trừ nguy cơ tự sát")],

  [h("NGUỒN DỮ LIỆU"),
   p("EEG đa kênh theo hệ điện cực quốc tế 10-20 (19\u201321 kênh) + tín hiệu video đồng bộ + thông tin cấu hình ghi, thu trong quá trình khám chữa bệnh thường quy tại 2 bệnh viện"),
   h("QUY TRÌNH GÁN NHÃN"),
   p("Công cụ phần mềm gán nhãn do chính nhóm nghiên cứu phát triển \u2192 bác sĩ đánh dấu cơn \u2192 KIỂM TRA CHÉO giữa nhiều bác sĩ \u2192 đối chiếu nhãn theo quy ước DUNG SAI CHỒNG LẤN THỜI GIAN của khung SzCORE"),
   n("Lý do phải có dung sai: kết quả đọc EEG khác nhau giữa những người đọc, ngay cả ở việc xác định thời điểm khởi phát của cùng một cơn \u2013 nên không thể đòi hỏi trùng khớp tuyệt đối"),
   wn("VIDEO KHÔNG THAM GIA HUẤN LUYỆN. Video chỉ dùng ngoại tuyến làm nguồn đối chiếu độc lập để xác nhận cơn đã gán nhãn và kiểm chứng cách mô hình hoạt động \u2013 nhờ đó sản phẩm vẫn vận hành được trên bản ghi không kèm video"),
   n("Toàn bộ dữ liệu mã hóa, loại bỏ định danh, lưu trên máy chủ bảo mật, phân quyền theo vai trò; chỉ dùng sau khi Hội đồng Đạo đức phê duyệt")],

  [h("TÍN HIỆU THU NHẬN"),
   p("EEG trạng thái nghỉ + TMS-EEG (ghi đồng thời, khóa thời gian với xung TMS) tại T0 / T2 / T4"),
   p("Lưu đầy đủ thông số kỹ thuật phục vụ chuẩn hóa và kiểm soát chất lượng: hệ điện cực, cấu hình kênh, tần số lấy mẫu, thời lượng và điều kiện ghi, phương pháp tham chiếu ban đầu, dấu thời gian"),
   h("ĐẦU RA LÂM SÀNG (biến phụ thuộc)"),
   b("Δ điểm nhận thức trên MoCA / MMSE / ADAS-Cog / CDR-SB, giữ ở dạng BIẾN LIÊN TỤC làm kết quả chính (bảo toàn thông tin, phù hợp giai đoạn thí điểm)"),
   p("Phân nhóm đáp ứng / không đáp ứng chỉ là phân tích BỔ SUNG khi cỡ mẫu cho phép; tiêu chí phân nhóm xác định trước dựa trên thang đo chính, mức thay đổi có ý nghĩa lâm sàng và ý kiến bác sĩ chuyên khoa"),
   n("Nếu có thay đổi thiết bị hoặc cấu hình thu nhận, khác biệt kỹ thuật phải được ghi nhận và xử lý bằng chuẩn hóa hoặc phân tích độ nhạy")],

  [h("TÍN HIỆU THU NHẬN"),
   p("EEG trạng thái nghỉ tại T0 / T2 / T4, chuẩn hóa về số kênh, tần số lấy mẫu, thời gian ghi, điều kiện ghi (mắt nhắm hay mắt mở) và sơ đồ điện cực tham chiếu"),
   n("Cấu hình rút gọn 8 ĐIỆN CỰC đã được ghi nhận cho độ chính xác tương đương \u2013 thậm chí nhỉnh hơn \u2013 cấu hình 30 điện cực, mở triển vọng ứng dụng chi phí thấp trong thực hành"),
   wn("YÊU CẦU KIỂM SOÁT THEN CHỐT: chất lượng tín hiệu phải tương đồng giữa T0, T2 và T4, để khác biệt EEG quan sát được phản ánh thay đổi SINH HỌC thật sự chứ không phải chênh lệch kỹ thuật giữa các lần đo"),
   h("ĐẦU RA LÂM SÀNG (biến phụ thuộc)"),
   b("Δ điểm thang trầm cảm sau liệu trình (bài toán hồi quy) + phân loại đáp ứng / thuyên giảm / không đáp ứng (bài toán phân loại)")],
 ]),

 ("\u2462", "TIỀN XỬ LÝ\nTÍN HIỆU", [
  [h("CHUỖI XỬ LÝ ÂM THANH"),
   p("Phát hiện vùng có lời nói (VAD) \u2192 phân tách người nói \u2192 chuẩn hóa kênh ghi âm \u2192 chuẩn hóa âm lượng \u2192 khử nhiễu \u2192 kiểm tra chất lượng thủ công với các bản ghi có dấu hiệu bất thường"),
   h("PHIÊN ÂM (speech-to-text)"),
   p("PhoWhisper \u2013 phát triển từ Whisper, tinh chỉnh trên \u2248 844 giờ tiếng Việt (VIVOS, VLSP 2020 và dữ liệu riêng) \u2013 kết hợp hiệu chỉnh thủ công làm chuẩn tham chiếu"),
   wn("Bắt buộc ĐO LẠI tỷ lệ lỗi từ (WER) trực tiếp trên dữ liệu người cao tuổi và bệnh nhân Alzheimer: chỉ số công bố của PhoWhisper được đo trên giọng người khỏe mạnh, không đại diện cho quần thể nghiên cứu")],

  [h("CHUỖI XỬ LÝ ÂM THANH"),
   p("Kiểm tra định dạng tệp \u2192 chuẩn hóa tần số lấy mẫu \u2192 VAD \u2192 PHÂN TÁCH NGƯỜI NÓI (tách giọng bệnh nhân khỏi giọng người phỏng vấn) \u2192 loại hoặc gắn cờ đoạn chồng tiếng và nhiễu nặng \u2192 phân đoạn theo nhiệm vụ và theo lượt nói \u2192 ghi chỉ số chất lượng cho từng đoạn"),
   h("PHIÊN ÂM"),
   p("Whisper hoặc mô hình ASR tiếng Việt tương đương; 10\u201315% dữ liệu được kiểm tra / hiệu chỉnh thủ công để đo WER"),
   n("Đoạn có chất lượng phiên âm thấp bị LOẠI khỏi phân tích ngôn ngữ nhưng vẫn GIỮ LẠI cho phân tích âm học nếu tín hiệu đạt yêu cầu"),
   n("Toàn bộ triển khai bằng một pipeline thống nhất; tham số chính xác định trên dữ liệu huấn luyện hoặc dữ liệu thí điểm và cố định trước khi đánh giá tập kết quả cuối cùng")],

  [h("CHUỖI XỬ LÝ EEG"),
   p("Kiểm tra cấu hình điện cực, tần số lấy mẫu, thời lượng, tính liên tục \u2192 lọc thông dải + lọc notch nhiễu điện lưới \u2192 phát hiện kênh xấu và đoạn có tín hiệu phẳng, biên độ bất thường, chuyển động mạnh, bão hòa, nhiễu cơ (loại bỏ hoặc nội suy) \u2192 ICA kết hợp ICLabel và kiểm tra trực quan để khử nhiễu mắt, cơ, tim, điện cực \u2192 chuẩn hóa"),
   h("PHÂN ĐOẠN"),
   b("Cửa sổ trượt có chồng lấn, ưu tiên độ dài ngắn 4\u20135 giây; độ dài cửa sổ và bước trượt được chọn trên tập kiểm định. Nhãn mỗi cửa sổ suy ra từ khoảng thời gian cơn do bác sĩ đánh dấu"),
   n("Lý do chọn cửa sổ ngắn: bảo toàn độ phân giải thời gian cần thiết cho chức năng xác định điện cực khởi phát"),
   wn("CHIA DỮ LIỆU THEO BỆNH NHÂN TRƯỚC, CẮT CỬA SỔ SAU. Các cửa sổ chồng lấn có tương quan rất cao; nếu cắt trước rồi mới chia, chúng sẽ phân tán giữa tập huấn luyện và tập kiểm thử và làm hiệu năng bị thổi phồng")],

  [h("CHUỖI XỬ LÝ EEG"),
   p("Lọc thông dải \u2248 0,5\u201345 Hz + lọc notch \u2192 phát hiện kênh xấu và đoạn xấu (loại bỏ hoặc nội suy) \u2192 phân tích thành phần độc lập (ICA, EEGLAB + ICLabel) khử nhiễu mắt, cơ, tim, điện cực và môi trường"),
   h("RIÊNG TMS-EEG"),
   b("Loại bỏ hoặc nội suy khoảng tín hiệu bị ảnh hưởng trực tiếp bởi xung TMS và hiện tượng BÃO HÒA BỘ KHUẾCH ĐẠI \u2013 phải thực hiện TRƯỚC bước lọc \u2192 phân đoạn quanh từng xung \u2192 hiệu chỉnh đường nền \u2192 loại các trial không đạt chất lượng"),
   n("Tham chiếu quy trình chuẩn quốc tế: PREP pipeline \u00b7 DISCOVER-EEG \u00b7 TESA \u00b7 khuyến cáo thu nhận và phân tích TMS-EEG"),
   n("Chỉ những bản ghi đáp ứng tiêu chuẩn chất lượng xác định trước mới được đưa vào các bước phân tích tiếp theo")],

  [h("CHUỖI XỬ LÝ EEG"),
   p("Lọc thông dải + lọc nhiễu điện lưới \u2192 phát hiện và xử lý kênh xấu \u2192 ICA khử nhiễu mắt, cơ và chuyển động \u2192 chia thành các đoạn (epoch) ngắn \u2192 loại bỏ đoạn không đạt chất lượng \u2192 chuẩn hóa"),
   n("ICA ở đây có VAI TRÒ KÉP: ngoài khử nhiễu, các thành phần độc lập còn được dùng để TÁCH NGUỒN HOẠT ĐỘNG VÙNG DLPFC \u2013 vùng đích của rTMS \u2013 phục vụ trực tiếp bước trích xuất đặc trưng phi tuyến")],
 ]),

 ("\u2463", "TRÍCH XUẤT\nĐẶC TRƯNG\n(ứng viên dấu\nấn sinh học số)", [
  [h("NHÓM ÂM HỌC"),
   p("Thời lượng và nhịp điệu lời nói \u00b7 tốc độ nói \u00b7 tốc độ phát âm \u00b7 tỷ lệ và thời lượng khoảng lặng \u00b7 các tham số của tần số cơ bản F0 \u00b7 jitter \u00b7 shimmer \u00b7 tỷ số hài trên nhiễu (HNR) \u00b7 hệ số MFCC \u00b7 tham số formant \u00b7 chất lượng giọng và cấu âm"),
   wn("XỬ LÝ ĐẶC THÙ TIẾNG VIỆT \u2013 tiếng Việt là ngôn ngữ THANH ĐIỆU, F0 không chỉ mang ngữ điệu mà còn tham gia phân biệt NGHĨA của từ. Quy trình: phân đoạn âm tiết \u2192 xác định thanh điệu và ngữ cảnh âm vị \u2192 chuẩn hóa F0 theo từng người nói \u2192 chỉ so sánh sai lệch âm học trong CÙNG điều kiện thanh điệu. Mục đích: không diễn giải nhầm khác biệt ngữ âm bình thường thành dấu hiệu bệnh lý"),
   h("NHÓM NGÔN NGỮ"),
   p("Độ phong phú từ vựng \u00b7 tỷ lệ loại trên thẻ (type-token ratio) \u00b7 mật độ ý tưởng \u00b7 độ mạch lạc \u00b7 số đơn vị thông tin được đề cập \u00b7 cấu trúc cú pháp \u00b7 quan hệ ngữ nghĩa"),
   wn("Tiếng Việt không phân tách từ bằng khoảng trắng ở cấp độ từ \u2192 mọi chỉ số từ vựng và cú pháp phụ thuộc trực tiếp vào bước tách từ. Bắt buộc dùng THỐNG NHẤT MỘT công cụ tách từ cho toàn bộ dữ liệu để các mẫu so sánh được với nhau")],

  [h("\u2460 ÂM HỌC & NGỮ ĐIỆU"),
   p("MFCC \u00b7 cao độ trung bình và độ biến thiên cao độ \u00b7 cường độ \u00b7 năng lượng \u00b7 jitter \u00b7 shimmer \u00b7 HNR \u00b7 tốc độ nói và tốc độ phát âm \u00b7 số lượng và thời lượng khoảng dừng \u00b7 tỷ lệ thời gian im lặng \u00b7 độ dài lượt nói \u00b7 bộ mô tả chuẩn eGeMAPS"),
   h("\u2461 BIỂU DIỄN TỪ MÔ HÌNH TIỀN HUẤN LUYỆN"),
   p("wav2vec 2.0 \u00b7 HuBERT \u00b7 WavLM \u00b7 Whisper dùng như bộ mã hóa"),
   n("Do quy mô dữ liệu giai đoạn đầu còn nhỏ, các mô hình này được dùng ở chế độ TRÍCH XUẤT ĐẶC TRƯNG CỐ ĐỊNH hoặc tinh chỉnh giới hạn, KHÔNG huấn luyện mạng sâu end-to-end trực tiếp từ tín hiệu thô"),
   p("Embedding cấp đoạn \u2192 tổng hợp bằng trung bình, độ lệch chuẩn, trung vị, percentile hoặc pooling phù hợp \u2192 biểu diễn CẤP NGƯỜI THAM GIA"),
   h("\u2462 NGÔN NGỮ (trích từ bản phiên âm)"),
   p("Tổng số từ \u00b7 độ dài câu \u00b7 độ đa dạng từ vựng \u00b7 tần suất từ phủ định \u00b7 đại từ ngôi thứ nhất \u00b7 từ biểu thị cảm xúc \u00b7 từ ngập ngừng \u00b7 tỷ lệ lặp lại \u00b7 chỉ số mạch lạc ngữ nghĩa \u00b7 sentence / document embedding"),
   n("Ba nguồn thông tin được đánh giá RIÊNG trước khi kết hợp, nhằm tách bạch giá trị độc lập và giá trị bổ sung của từng nguồn")],

  [h("KHẢO SÁT TRÊN 4 MIỀN"),
   p("Miền thời gian (hình thái sóng) \u00b7 miền tần số (công suất phổ, năng lượng theo dải) \u00b7 miền thời gian\u2013tần số kết hợp \u00b7 miền không gian (quan hệ giữa các kênh)"),
   st("NEUROMARKER CỐT LÕI \u2013 QUÁ TRÌNH TIẾN TRIỂN THEO THỜI GIAN của tần số, biên độ, hình thái và phân bố không gian"),
   n("Vì sao đây là đặc trưng quan trọng nhất: khởi phát cơn trên EEG da đầu KHÔNG có một hình thái duy nhất và không tương ứng cố định với hình thái ghi bằng điện cực nội sọ. Do đó thứ phân biệt cơn thật với hoạt động nhịp điệu do nhiễu vận động và nhiễu điện cực không phải hình thái tại một thời điểm, mà là quá trình tiến triển CÓ HỆ THỐNG theo thời gian"),
   h("DẤU ẤN ĐỊNH KHU (phục vụ chức năng khu trú)"),
   p("Hoạt động nhanh kịch phát \u00b7 nhóm dao động tần số cao (HFO) \u2013 có độ đặc hiệu cao với vùng sinh động kinh và giữ được giá trị định bên bán cầu ngay ở tần số lấy mẫu dưới 512 Hz thường dùng trong lâm sàng"),
   h("ĐỘNG HỌC LAN TRUYỀN (phục vụ chức năng mô tả lan truyền)"),
   p("Độ trễ huy động giữa các điện cực \u00b7 hướng lan \u00b7 tốc độ lan \u00b7 các chỉ số kết nối và đồng bộ chức năng"),
   n("Song song, tín hiệu sau tiền xử lý được đưa TRỰC TIẾP vào mạng học sâu để tự học biểu diễn, rồi so sánh với nhóm mô hình dùng đặc trưng thủ công trên CÙNG một quy trình kiểm thử")],

  [h("MIỀN PHỔ"),
   p("Công suất tuyệt đối và tương đối các dải delta, theta, alpha, beta \u00b7 tần số alpha đỉnh (PAF) \u00b7 các tỷ số phổ phản ánh MỨC ĐỘ CHẬM HÓA của hoạt động điện não"),
   h("HÌNH THÁI & ĐỘNG HỌC MẠNG"),
   p("Đặc trưng hình thái \u00b7 độ biến thiên \u00b7 kết nối chức năng \u00b7 tính đồng bộ \u00b7 entropy \u00b7 độ phức tạp tín hiệu"),
   h("RIÊNG TMS-EEG"),
   p("Điện thế gợi bởi TMS (TEP): biên độ và độ trễ của các thành phần đáp ứng \u00b7 công suất gợi \u00b7 mức độ lan truyền hoạt động giữa các vùng não \u2013 cho phép khảo sát trực tiếp tính phản ứng, tính kích thích và khả năng lan truyền của vỏ não"),
   wn("Việc lựa chọn tập đặc trưng ĐƯỢC ĐỊNH HƯỚNG BỞI GIẢ THUYẾT SINH LÝ THẦN KINH và bằng chứng về biến đổi điện sinh lý trong Alzheimer, không quét mù toàn bộ không gian đặc trưng \u2013 vì số chiều lớn trên cỡ mẫu nhỏ làm tăng mạnh nguy cơ quá khớp")],

  [h("MIỀN PHỔ"),
   p("Công suất tuyệt đối và tương đối delta \u2013 theta \u2013 alpha \u2013 beta và các tỷ số phổ. Nhóm dự báo được trích dẫn nhiều nhất là CÔNG SUẤT VÙNG TRÁN ở dải alpha và theta"),
   h("IAF \u2013 tần số alpha cá thể"),
   b("Thuộc nhóm dấu ấn ổn định nhất. Điểm đặc biệt: KHOẢNG CÁCH giữa IAF và tần số kích thích 10 Hz có liên hệ với mức cải thiện lâm sàng \u2013 bệnh nhân có IAF gần 10 Hz thường đáp ứng tốt hơn với rTMS 10 Hz"),
   h("FAA \u2013 bất đối xứng alpha vùng trán"),
   p("Phản ánh mất cân bằng hoạt hóa giữa trán trái và trán phải trong trầm cảm"),
   wn("Diễn giải thận trọng: nhiều bằng chứng cho thấy FAA thiên về \u201cdấu ấn đặc điểm\u201d tương đối ổn định và không phải lúc nào cũng phân biệt được người đáp ứng với người không đáp ứng"),
   h("THETA CORDANCE VÙNG TRƯỚC TRÁN"),
   p("Chỉ số kết hợp công suất tuyệt đối và tương đối, tương quan với tưới máu não vùng tương ứng. Mức giảm sớm trong tuần đầu được xem là chỉ báo tiên lượng đáp ứng với cả rTMS lẫn thuốc chống trầm cảm"),
   wn("Chiều biến đổi giữa các nghiên cứu chưa hoàn toàn nhất quán \u2013 có công trình ghi nhận cordance TĂNG ở người đáp ứng"),
   h("KẾT NỐI CHỨC NĂNG mạng trán và trán\u2013đai"),
   p("Kết nối dựa trên tương quan phổ trong dải IAF (từng dự báo đáp ứng với độ chính xác \u2248 69%) \u00b7 đồng bộ pha PLV / PLI \u00b7 kết nối định hướng mô hình hóa dạng đồ thị \u2192 chỉ số lý thuyết đồ thị, điển hình betweenness centrality tại điện cực Fp2 dải delta (AUC \u2248 0,85)"),
   h("PHI TUYẾN & ĐỘ PHỨC TẠP"),
   p("Permutation entropy \u00b7 fractal dimension \u00b7 Lempel\u2013Ziv complexity \u00b7 correlation dimension \u00b7 đặc trưng bispectrum \u2013 trích từ chuỗi thời gian của các thành phần liên quan vùng trán"),
   n("Hướng khám phá bổ sung: tách thành phần phổ PHI CHU KỲ 1/f (aperiodic) khỏi thành phần dao động thật nhằm nâng cao khả năng tái lập của dấu ấn")],
 ]),

 ("\u2464", "MÔ HÌNH AI &\nGIAO THỨC\nĐÁNH GIÁ", [
  [h("LỰA CHỌN ĐẶC TRƯNG THEO 3 MỨC"),
   p("\u2460 Sàng lọc theo bằng chứng lâm sàng, tính ổn định của phép đo và khả năng diễn giải \u2192 \u2461 thuật toán lựa chọn đặc trưng đa biến, tối ưu đồng thời mức liên quan với bệnh và giảm tính dư thừa \u2192 \u2462 kiểm tra mức đóng góp trên dữ liệu KHÔNG dùng trong huấn luyện để xác nhận khả năng khái quát hóa"),
   b("Độ ổn định tập đặc trưng đánh giá bằng bootstrap resampling: tần suất được lựa chọn, sự ổn định của thứ hạng, khoảng biến thiên của mức độ quan trọng"),
   n("Đặc trưng âm học và ngôn ngữ thường tương quan cao \u2192 không chỉ báo cáo ma trận tương quan mà PHÂN CỤM các đặc trưng tương quan rồi đánh giá mức quan trọng THEO TỪNG NHÓM"),
   h("MÔ HÌNH & CHỈ SỐ"),
   p("Logistic Regression \u00b7 Support Vector Machine \u00b7 Random Forest và các mô hình có giám sát khác. Chỉ số: Accuracy \u00b7 Sensitivity \u00b7 Specificity \u00b7 F1-score \u00b7 AUC-ROC"),
   b("MỐC THAM CHIẾU QUỐC TẾ: ADReSS \u00b7 ADReSSo (đường cơ sở 78,87% khi kết hợp đặc trưng âm học và ngôn ngữ) \u00b7 TAUKADIAL (thiết lập đa ngôn ngữ)"),
   h("KHẢ NĂNG DIỄN GIẢI"),
   p("SHAP và LIME phân tích mức đóng góp của từng đặc trưng ở cả cấp toàn mô hình và cấp từng trường hợp cụ thể")],

  [branch([
     ("NHÁNH A \u2013 HỌC CÓ GIÁM SÁT (bài toán sàng lọc bệnh \u2013 chứng)", [
        b("6 cấu hình được xây dựng và so sánh: (1) đặc trưng âm học & ngữ điệu \u00b7 (2) embedding từ mô hình giọng nói tiền huấn luyện \u00b7 (3) đặc trưng ngôn ngữ \u00b7 (4) kết hợp âm thanh + ngôn ngữ \u00b7 (5) từng nhiệm vụ nói riêng \u00b7 (6) kết hợp toàn bộ nhiệm vụ nói"),
        p("Thuật toán: Logistic Regression có điều chuẩn \u00b7 Elastic Net \u00b7 SVM \u00b7 Random Forest \u00b7 XGBoost"),
        p("Chỉ số: ROC-AUC \u00b7 balanced accuracy \u00b7 F1 \u00b7 sensitivity \u00b7 specificity \u00b7 precision, kèm BRIER SCORE và CALIBRATION CURVE để đánh giá mức khớp giữa xác suất dự đoán và kết quả thực tế"),
        p("Khoảng tin cậy 95% bằng bootstrap CẤP NGƯỜI THAM GIA \u00b7 permutation test để xác nhận hiệu năng cao hơn mức ngẫu nhiên \u00b7 phân tích ABLATION theo nhóm đặc trưng và theo nhiệm vụ nói \u00b7 phân tích độ nhạy theo tuổi, giới, học vấn, thời lượng phát ngôn, thuốc, chất lượng âm thanh và thiết bị thu"),
        n("Các đoạn ghi âm KHÔNG được xem là quan sát độc lập; dự đoán cuối cùng tổng hợp ở CẤP NGƯỜI THAM GIA cho đúng mục tiêu sàng lọc"),
     ]),
     ("NHÁNH B \u2013 HỌC KHÔNG GIÁM SÁT (khám phá kiểu hình trầm cảm)", [
        p("Chỉ thực hiện trên nhóm bệnh nhân trầm cảm có dữ liệu đạt chuẩn chất lượng"),
        wn("PHQ-9, HAMD-17, tuổi, giới và nhãn lâm sàng KHÔNG được dùng để hình thành cụm \u2013 chỉ dùng SAU khi phân cụm để mô tả và đánh giá ý nghĩa của các nhóm, nhằm tránh lập luận vòng tròn"),
        b("PCA (giảm nhiễu, xử lý tương quan, hạ số chiều) \u2192 UMAP (khảo sát cấu trúc lân cận) \u2192 HDBSCAN (phát hiện vùng mật độ cao, không cần định trước số cụm)"),
        n("Phân cụm chính thực hiện trên không gian PCA hoặc UMAP có SỐ CHIỀU LỚN HƠN HAI; biểu diễn UMAP 2 chiều chỉ dùng để trực quan hóa, tránh diễn giải cụm chỉ dựa trên hình ảnh"),
        n("Trường hợp bị HDBSCAN gán là \u201cnoise\u201d KHÔNG bị tự động loại khỏi nghiên cứu \u2013 đây có thể là bệnh nhân có biểu hiện giọng nói không điển hình và được mô tả riêng"),
        p("ĐỘ ỔN ĐỊNH: lặp UMAP với nhiều random seed \u00b7 bootstrap / subsampling người tham gia \u00b7 thay đổi có kiểm soát tham số \u00b7 Adjusted Rand Index \u00b7 Jaccard similarity \u00b7 cluster persistence \u00b7 tỷ lệ giữ nguyên cụm qua các lần phân tích \u00b7 đối chiếu với Gaussian Mixture Model và hierarchical clustering"),
        p("ĐẶC TRƯNG HÓA: ANOVA / Kruskal\u2013Wallis, kiểm định hậu nghiệm, chi bình phương / Fisher, hiệu chỉnh đa kiểm định, báo cáo kích thước hiệu ứng và khoảng tin cậy"),
        n("Tên kiểu hình mang tính MÔ TẢ (ví dụ: \u201cgiảm tốc độ nói và kéo dài khoảng dừng\u201d, \u201cgiảm biến thiên ngữ điệu\u201d, \u201cthay đổi chủ yếu ở miền ngôn ngữ\u201d), không phải phân loại lâm sàng chính thức"),
     ]),
   ], "HAI NHÁNH SONG SONG, HỘI TỤ Ở BƯỚC ĐÁNH GIÁ"),
   ("j", "ĐIỂM NỐI A \u2194 B: chiếu phân bố ĐIỂM NGUY CƠ và hiệu năng của mô hình sàng lọc lên TỪNG kiểu hình \u2192 xác định kiểu hình nào được mô hình nhận diện tốt nhất, kiểu hình nào có tỷ lệ ÂM TÍNH GIẢ cao, mức tự tin của mô hình khác nhau ra sao giữa các nhóm, và những ca có triệu chứng lâm sàng đáng kể nhưng biểu hiện giọng nói gần với nhóm chứng. Đây là cơ sở xác định PHẠM VI HOẠT ĐỘNG và GIỚI HẠN của công cụ, thay vì chỉ báo cáo một con số hiệu năng trung bình.")],

  [("j", "4 CHỨC NĂNG MÔ HÌNH:  \u2460 Phát hiện cơn kèm xác định thời điểm khởi phát và kết thúc  \u2461 Khu trú các điện cực có hoạt động bất thường xuất hiện SỚM và MẠNH nhất  \u2462 Mô tả trình tự huy động điện cực theo thời gian (lan truyền)  \u2463 (thăm dò) Phân loại thể cơn cục bộ / toàn thể \u2013 nếu số ca thể toàn thể không đủ, báo cáo dưới dạng phân tích khả thi kèm khuyến nghị quy mô dữ liệu"),
   h("MÔ HÌNH"),
   p("Nền so sánh: Linear Discriminant Analysis \u00b7 Logistic Regression \u00b7 Random Forest \u00b7 SVM \u00b7 XGBoost  \u2016  Học sâu: EEGNet \u00b7 CNN và các biến thể CNN chuyên xử lý EEG (khai thác quan hệ không gian \u2013 thời gian giữa các kênh mà không cần thiết kế đặc trưng thủ công)"),
   h("XỬ LÝ MẤT CÂN BẰNG LỚP CỰC ĐOAN"),
   p("Cơn chỉ chiếm tỷ lệ rất nhỏ trong bản ghi dài hạn \u2192 kỹ thuật lấy mẫu, hàm mất mát có trọng số, ưu tiên đưa vào các đoạn tín hiệu nền DỄ GÂY NHẦM, tăng cường dữ liệu, học chuyển giao, tối ưu siêu tham số"),
   wn("Ở bước ĐÁNH GIÁ, mô hình chạy trên TOÀN BỘ bản ghi liên tục và KHÔNG áp dụng cân bằng dữ liệu \u2013 để phản ánh đúng điều kiện vận hành thực tế"),
   h("HẬU XỬ LÝ THEO SzCORE (bắt buộc trước khi chấm điểm)"),
   b("Gộp các cửa sổ dương liền kề \u2192 nối các đoạn cách nhau dưới một khoảng thời gian ngắn \u2192 loại bỏ sự kiện quá ngắn \u2192 DANH SÁCH SỰ KIỆN CƠN \u2192 chỉ danh sách này mới được đối chiếu với nhãn tham chiếu"),
   h("CHỈ SỐ ĐÁNH GIÁ Ở MỨC SỰ KIỆN"),
   p("Sensitivity \u00b7 Precision \u00b7 F1-score \u00b7 SỐ BÁO ĐỘNG GIẢ TRÊN 24 GIỜ \u2013 chỉ số quyết định khả năng chấp nhận sản phẩm \u00b7 độ trễ phát hiện cơn"),
   wn("KHÔNG dùng Accuracy và Specificity làm chỉ số chính: các đoạn không phải cơn chiếm áp đảo nên hai chỉ số này cao ngay cả với mô hình kém"),
   h("KIỂM ĐỊNH NGOẠI VI"),
   b("Huấn luyện trên dữ liệu MỘT bệnh viện \u2192 kiểm thử trên bệnh viện CÒN LẠI, đánh giá khả năng tổng quát hóa qua khác biệt thiết bị và quần thể bệnh nhân. Ngoài giá trị trung bình, báo cáo PHÂN BỐ HIỆU NĂNG THEO TỪNG BỆNH NHÂN để bộc lộ các ca mô hình hoạt động kém"),
   h("XAI \u2013 YÊU CẦU BẮT BUỘC vì sản phẩm là thiết bị hỗ trợ quyết định lâm sàng"),
   p("Grad-CAM \u00b7 Integrated Gradients \u00b7 SHAP \u00b7 Attention Visualization (tùy kiến trúc) để trực quan hóa khoảng thời gian và điện cực đóng góp nhiều nhất vào quyết định \u2192 đối chiếu với nhận định của bác sĩ chuyên khoa"),
   ("j", "MỐC HIỆU NĂNG THAM CHIẾU (phần mềm thương mại đã được cấp phép):  Persyst 14 \u2013 phát hiện 67,3\u201371,1% với 2\u20134 báo động giả/ngày  \u2016  Encevis 2.0 \u2013 phát hiện 80,7\u201389,1% với 12\u201322 báo động giả/ngày  \u2016  SCORE-AI \u2013 đạt hiệu năng ngang chuyên gia và đã được kiểm định ngoại vi độc lập. Dải này minh họa rõ sự ĐÁNH ĐỔI giữa độ nhạy và số báo động giả, và được dùng làm mốc định vị mục tiêu của sản phẩm.")],

  [row([("\u2460 CHỈ LÂM SÀNG", [p("Dữ liệu lâm sàng + nhân khẩu học")]),
        ("\u2461 CHỈ ĐIỆN SINH LÝ", [p("Đặc trưng EEG / TMS-EEG")]),
        ("\u2462 KẾT HỢP", [p("EEG/TMS-EEG + lâm sàng")])],
       "3 NHÓM MÔ HÌNH XÂY DỰNG SONG SONG ĐỂ TÁCH BẠCH GIÁ TRỊ BỔ SUNG THẬT SỰ CỦA DỮ LIỆU ĐIỆN SINH LÝ"),
   h("BÀI TOÁN"),
   p("Ưu tiên HỒI QUY dự đoán mức thay đổi điểm nhận thức sau điều trị (bảo toàn thông tin). Bài toán phân loại đáp ứng / không đáp ứng chỉ thực hiện bổ sung khi cỡ mẫu và phân bố giữa các nhóm cho phép"),
   h("KIỂM SOÁT SỐ CHIỀU & THUẬT TOÁN"),
   p("Lựa chọn đặc trưng: LASSO \u00b7 Mutual Information \u00b7 Recursive Feature Elimination \u00b7 kỹ thuật giảm chiều phù hợp. Thuật toán khảo sát: Elastic Net \u00b7 SVM / SVR \u00b7 Random Forest \u00b7 XGBoost"),
   n("Ưu tiên mô hình TUYẾN TÍNH CÓ ĐIỀU CHUẨN khi dữ liệu hạn chế; mô hình phi tuyến chỉ được chọn khi cho thấy giá trị dự báo bổ sung rõ ràng và ổn định"),
   wn("MỖI BỆNH NHÂN ĐƯỢC ĐO LẶP TẠI NHIỀU THỜI ĐIỂM \u2192 phân chia dữ liệu ở CẤP BỆNH NHÂN: toàn bộ bản ghi EEG, trial TMS-EEG và mọi mốc đánh giá của một bệnh nhân chỉ nằm trong MỘT tập. Sử dụng GroupKFold, Leave-One-Subject-Out hoặc kiểm định chéo lồng nhau"),
   h("CHỈ SỐ"),
   p("Hồi quy: MAE \u00b7 RMSE \u00b7 R\u00b2 \u00b7 hệ số tương quan giữa giá trị dự đoán và giá trị quan sát.  Phân loại: balanced accuracy \u00b7 AUC \u00b7 sensitivity \u00b7 specificity \u00b7 precision \u00b7 F1 \u00b7 ma trận nhầm lẫn"),
   n("Mô hình cuối được chọn theo CÂN BẰNG giữa hiệu suất ngoài mẫu, độ ổn định, khả năng tổng quát hóa, mức độ phức tạp và khả năng diễn giải \u2013 không chọn theo hiệu năng cao nhất tại một lần thử nghiệm"),
   p("XAI: SHAP phân tích mức đóng góp của từng đặc trưng vào kết quả dự đoán")],

  [row([("\u2460 CHỈ LÂM SÀNG", [p("Biến nền + điểm triệu chứng")]),
        ("\u2461 CHỈ EEG", [p("EEG nền T0 + biến đổi sớm")]),
        ("\u2462 KẾT HỢP", [p("EEG + lâm sàng")])],
       "3 NHÓM MÔ HÌNH SO SÁNH \u2013 vì tuổi và mức độ nặng ban đầu vốn đã có giá trị tiên lượng độc lập, EEG chỉ thực sự hữu ích nếu bổ sung được năng lực dự báo VƯỢT TRÊN các biến lâm sàng sẵn có"),
   h("HAI NHÓM ĐẦU VÀO"),
   b("(a) Đặc trưng EEG NỀN tại T0  \u2016  (b) Đặc trưng BIẾN ĐỔI SỚM T0 \u2192 T2, phản ánh tính dẻo thần kinh sớm"),
   n("Cơ sở: thay đổi theta cordance vùng trước trán trong tuần đầu có khả năng dự báo kết quả cuối liệu trình; rộng hơn, chính mức cải thiện triệu chứng sớm trong tuần đầu cũng đã có giá trị tiên lượng ở cả phác đồ 10 Hz lẫn iTBS"),
   h("BÀI TOÁN"),
   p("Hồi quy dự đoán mức thay đổi điểm trầm cảm  \u2016  Phân loại đáp ứng / không đáp ứng (mở rộng: phân loại thuyên giảm nếu dữ liệu cho phép)"),
   h("THUẬT TOÁN & LỰA CHỌN ĐẶC TRƯNG"),
   p("Elastic Net \u00b7 SVM \u00b7 Random Forest \u00b7 XGBoost. Lựa chọn đặc trưng bằng LASSO \u00b7 Mutual Information \u00b7 Recursive Feature Elimination \u00b7 thuật toán di truyền (do số đặc trưng lớn trong khi cỡ mẫu hạn chế)"),
   n("Tham chiếu kết quả đã công bố để định hướng: mạng nơ-ron trên QEEG cordance đạt độ nhạy \u2248 93% và độ chính xác \u2248 89%; SVM / KNN / MLP trên đặc trưng phi tuyến vùng trán đạt \u2248 94%; mô hình đồ thị dựa trên kết nối định hướng cho hiệu năng tốt; LDA tỏ ra ổn định trên dữ liệu nhỏ với cấu hình ít điện cực"),
   h("CHỈ SỐ"),
   p("Hồi quy: MAE \u00b7 RMSE \u00b7 R\u00b2.  Phân loại: AUC \u00b7 sensitivity \u00b7 specificity \u00b7 F1"),
   st("Đặc biệt chú trọng NPV \u2013 giá trị dự báo âm tính: đây là chỉ số phản ánh trực tiếp khả năng LOẠI TRỪ người không đáp ứng, đúng với vai trò sàng lọc mà công cụ hướng tới"),
   p("Cross-validation / nested CV chia theo bệnh nhân \u00b7 SHAP để diễn giải sinh học \u00b7 kiểm định trên tập dữ liệu độc lập"),
   wn("Báo cáo cả KẾT QUẢ ÂM TÍNH và không tái lập được \u2013 đã có nghiên cứu ghi nhận biến đổi QEEG cordance KHÔNG dự báo được đáp ứng. Nhiều mô hình trước đây dựa trên cỡ mẫu nhỏ và đánh giá thiếu tách biệt giữa tập huấn luyện và kiểm thử nên hiệu năng bị thổi phồng")],
 ]),

 ("\u2465", "SẢN PHẨM\nĐẦU RA", [
  [p("\u25ad  QUY TRÌNH CHUẨN thu thập \u2013 kiểm tra chất lượng \u2013 phiên âm \u2013 trích xuất đặc trưng giọng nói tiếng Việt, phù hợp điều kiện bệnh viện"),
   p("\u25a4  CƠ SỞ DỮ LIỆU có cấu trúc: đặc trưng trích xuất, thông tin nhân khẩu học, kết quả đánh giá lâm sàng, đầu ra mô hình, nhật ký hệ thống"),
   p("\u2b21  MÔ HÌNH AI hỗ trợ sàng lọc Alzheimer có khả năng diễn giải + bộ đặc trưng ứng viên dấu ấn âm học và ngôn ngữ tiếng Việt"),
   st("\u2b22  PHẦN MỀM HỖ TRỢ SÀNG LỌC + thành phần trực quan hóa: đặc trưng ngôn ngữ và âm học bất thường, biểu đồ theo dõi thay đổi theo thời gian đối chiếu điểm lâm sàng, MỨC ĐỘ KHÔNG CHẮC CHẮN của dự đoán, chất lượng bản ghi âm, bản tóm tắt mức đóng góp của đặc trưng"),
   st("\u2b22  TÁC NHÂN ẢO hướng dẫn người bệnh thực hiện tác vụ nói: tổng hợp giọng nói tiếng Việt + nhận dạng giọng nói + hoạt hình khuôn mặt + quản lý hội thoại + giám sát trạng thái nhiệm vụ"),
   n("Mục tiêu của tác nhân ảo: chuẩn hóa quy trình thu, giảm biến thiên do người hướng dẫn gây ra giữa các lần khảo sát và giữa các cơ sở, đồng thời giảm cảm giác bị đánh giá khi giao tiếp"),
   p("Đánh giá: tỷ lệ hoàn thành nhiệm vụ \u00b7 đặc điểm dữ liệu lời nói trong hai điều kiện hướng dẫn \u00b7 hiệu suất hệ thống \u00b7 mức độ chấp nhận. Trải nghiệm người dùng khảo sát bằng phỏng vấn bán cấu trúc và phân tích chủ đề (thematic analysis): mức tin tưởng, tính dễ hiểu, khả năng tích hợp quy trình, quyền riêng tư, rào cản triển khai")],

  [p("\u25ad  QUY TRÌNH THU NHẬN & ĐÁNH GIÁ dữ liệu giọng nói phục vụ sàng lọc trầm cảm \u2013 xây trên nguyên tắc DAIC-WOZ, thích nghi ngôn ngữ, văn hóa và bối cảnh lâm sàng Việt Nam; gồm bộ nhiệm vụ nói, hướng dẫn thu âm, tiêu chuẩn kiểm soát chất lượng và bộ công cụ đánh giá triệu chứng"),
   p("\u25ad  QUY TRÌNH XỬ LÝ & PHÂN TÍCH tín hiệu giọng nói: tiền xử lý, VAD, phân tách người nói, phiên âm tự động, kiểm soát chất lượng, trích xuất đặc trưng âm học \u2013 ngữ điệu \u2013 khoảng dừng \u2013 ngôn ngữ \u2013 biểu diễn tiền huấn luyện"),
   p("\u2b21  MÔ HÌNH AI cho ĐIỂM NGUY CƠ TRẦM CẢM ở cấp người tham gia, đã tối ưu và kiểm định nội bộ theo phân tách cấp người, kèm đánh giá hiệu năng, độ ổn định và khả năng diễn giải"),
   p("\u2b21  BẢN ĐỒ KIỂU HÌNH TRẦM CẢM theo biểu hiện giọng nói kèm bằng chứng về độ ổn định của từng cụm và mô tả nhóm ngoại lệ"),
   p("\u2b22  MÔ-ĐUN PHÂN TÍCH THỬ NGHIỆM: tiếp nhận tệp ghi âm \u2192 tiền xử lý \u2192 trích xuất đặc trưng \u2192 suy luận \u2192 xuất điểm nguy cơ tham khảo"),
   n("Định vị sản phẩm: công cụ hỗ trợ sàng lọc và nghiên cứu, không thay thế chẩn đoán hoặc quyết định điều trị của bác sĩ chuyên khoa"),
   n("Kết quả không đạt ý nghĩa thống kê hoặc cấu trúc cụm không ổn định vẫn được báo cáo như một phần của đánh giá tính khả thi")],

  [p("\u25ad  QUY TRÌNH CHUẨN HÓA thu nhận \u2013 tiền xử lý EEG dài hạn + CÔNG CỤ PHẦN MỀM GÁN NHÃN có kiểm tra chéo giữa các bác sĩ"),
   p("\u2b21  BỘ ĐẶC TRƯNG / NEUROMARKER + 3 mô hình lõi (phát hiện \u2013 khu trú \u2013 lan truyền) + mô hình thăm dò phân loại thể cơn"),
   st("\u2b22  PHẦN MỀM HỖ TRỢ ĐỌC EEG DÀI HẠN \u2013 kiến trúc 3 lớp:"),
   p("\u2022 LỚP QUẢN LÝ DỮ LIỆU: nhập bản ghi EEG từ các định dạng chuẩn, quản lý cơ sở dữ liệu, đồng bộ EEG với video"),
   p("\u2022 LỚP XỬ LÝ AI: toàn bộ tiền xử lý tín hiệu \u2192 chạy mô hình phát hiện cơn \u2192 khu trú vùng khởi phát \u2192 mô tả lan truyền \u2192 sinh kết quả diễn giải từ mô-đun Explainable AI"),
   p("\u2022 LỚP GIAO DIỆN: trực quan hóa EEG nhiều kênh, xem video đồng bộ, hiển thị danh sách sự kiện AI phát hiện theo trình tự thời gian kèm MỨC ĐỘ TIN CẬY, trực quan hóa điện cực liên quan đến quyết định của mô hình, cho phép bác sĩ XÁC NHẬN / CHỈNH SỬA / LOẠI BỎ cảnh báo trước khi lưu kết quả cuối cùng"),
   b("THỬ NGHIỆM TẠI BỆNH VIỆN 2 GIAI ĐOẠN, trên tập dữ liệu ĐỘC LẬP VỀ THỜI GIAN (lấy từ phần dữ liệu tích lũy sau thời điểm chốt dữ liệu phát triển, không tham gia bất kỳ giai đoạn phát triển mô hình nào):"),
   p("\u2460 Quy mô nhỏ 20\u201325 bản ghi \u2013 phát hiện lỗi chức năng và hiệu chỉnh ngưỡng cảnh báo   \u2461 Mở rộng 50\u201360 bản ghi \u2013 đánh giá hiệu năng và MỨC GIẢM THỜI GIAN ĐỌC trong quy trình thực tế"),
   p("ĐÁNH GIÁ THEO 3 NHÓM TIÊU CHÍ \u2013 hiệu năng kỹ thuật (thời gian xử lý toàn bản ghi 24 giờ, tốc độ phản hồi khi thao tác, khả năng tải và hiển thị đồng thời nhiều kênh, mức sử dụng tài nguyên, tính ổn định khi vận hành liên tục, khả năng tích hợp mà không làm thay đổi quy trình chuyên môn) \u00b7 khả năng sử dụng (System Usability Scale) \u00b7 trải nghiệm người dùng (User Experience Questionnaire), theo phương pháp Thiết kế lấy người dùng làm trọng tâm"),
   wn("RÀNG BUỘC BẮT BUỘC CỦA SẢN PHẨM: không được làm tăng nguy cơ bỏ sót cơn có ý nghĩa lâm sàng"),
   ("j", "\u2714 KẾT QUẢ SƠ BỘ ĐÃ ĐẠT \u2013 bộ dữ liệu công khai CHB-MIT, montage lưỡng cực 18 kênh, 256 Hz, tập kiểm thử 8 bệnh nhân độc lập với 76 cơn.  Kiến trúc: đồ thị kết nối chức năng (wPLI, AEC) \u2192 Graph Autoencoder kết hợp nhánh thời gian LSTM và đặc trưng gamma \u2192 phát hiện điểm thay đổi PELT xác định thời điểm khởi phát và kết thúc \u2192 chấm điểm ở mức sự kiện theo SzCORE.  \u2016  Điểm vận hành cân bằng: độ nhạy 75,0% (CI95% 64,2\u201383,4) với 39,77 báo động giả/24 giờ.  \u2016  Điểm ưu tiên độ nhạy: 82,9% (CI95% 72,9\u201389,7) với 71,25 báo động giả/24 giờ, độ trễ phát hiện \u2248 0\u20137 giây.  \u2016  Mức mẫu: AUROC trung bình 0,791.  Kết quả đạt được HOÀN TOÀN KHÔNG GIÁM SÁT và ĐỘC LẬP BỆNH NHÂN, nằm trong dải 67,6\u201381% của phần mềm thương mại đã cấp phép \u2013 củng cố tính khả thi của hướng tiếp cận.")],

  [p("\u25ad  QUY TRÌNH CHUẨN thu nhận, tiền xử lý và phân tích dữ liệu EEG / TMS-EEG ở bệnh nhân Alzheimer điều trị TMS"),
   p("\u2b21  BỘ ĐẶC TRƯNG ĐIỆN SINH LÝ có giá trị liên quan đến mức độ bệnh và sự thay đổi chức năng nhận thức sau điều trị"),
   p("\u2b21  MÔ HÌNH AI THỬ NGHIỆM dự đoán và theo dõi đáp ứng điều trị TMS trên cơ sở kết hợp dữ liệu EEG / TMS-EEG với dữ liệu lâm sàng"),
   p("Tiêu chí nghiệm thu: mức độ hoàn thiện của quy trình \u00b7 mối liên quan giữa đặc trưng EEG với chỉ số lâm sàng \u00b7 các chỉ số hiệu suất phù hợp của mô hình"),
   n("Định vị đúng giai đoạn: đây là nghiên cứu THÍ ĐIỂM \u2013 mục tiêu là xác lập tính khả thi của quy trình thu nhận EEG/TMS-EEG và nhận diện đặc trưng tiềm năng, chưa phải mô hình sẵn sàng triển khai")],

  [p("\u25ad  QUY TRÌNH CHUẨN HÓA tiền xử lý và phân tích EEG ở bệnh nhân trầm cảm điều trị rTMS"),
   p("\u2b21  BỘ ĐẶC TRƯNG EEG liên quan đáp ứng điều trị: đặc trưng phổ \u00b7 IAF \u00b7 FAA \u00b7 theta cordance \u00b7 kết nối chức năng \u00b7 đặc trưng phi tuyến"),
   p("\u2b21  MÔ HÌNH HỒI QUY dự đoán mức cải thiện triệu chứng + MÔ HÌNH PHÂN LOẠI đáp ứng / không đáp ứng (kèm phân loại thuyên giảm nếu dữ liệu cho phép), đều được kiểm chứng độ ổn định và kiểm định ngoài mẫu khi khả thi"),
   b("TRẢ LỜI 2 CÂU HỎI PHƯƠNG PHÁP: (i) mô hình kết hợp EEG + lâm sàng có thực sự vượt trội mô hình chỉ dùng dữ liệu lâm sàng hay không; (ii) đặc trưng BIẾN ĐỔI SỚM đóng góp thêm bao nhiêu so với đặc trưng nền"),
   p("\u2b22  Mã nguồn / phần mềm thử nghiệm + báo cáo khoa học + bài báo quốc tế"),
   n("Hướng mở rộng: phân tầng điều trị \u2013 một số công trình gợi ý dấu ấn EEG có thể hỗ trợ lựa chọn giữa rTMS và thuốc, qua đó nâng tỷ lệ thuyên giảm trong các mô phỏng phân tầng")],
 ]),
]

BAND1_ITEMS = [
 ("PHÂN TÁCH DỮ LIỆU Ở CẤP CÁ THỂ",
  "Toàn bộ bản ghi, đoạn tín hiệu, cửa sổ trượt, lượt phát ngôn, trial TMS-EEG và mọi mốc thời gian của MỘT bệnh nhân / người tham gia chỉ được nằm trong MỘT tập dữ liệu hoặc MỘT fold. Ở ND3 còn phải chia theo bệnh nhân TRƯỚC khi cắt cửa sổ."),
 ("CHỐNG RÒ RỈ DỮ LIỆU",
  "Chuẩn hóa, điền giá trị thiếu, lựa chọn đặc trưng, giảm chiều và tối ưu siêu tham số CHỈ được ước lượng trên tập huấn luyện của TỪNG vòng kiểm định rồi mới áp dụng cho tập kiểm thử. Nested cross-validation tách quá trình lựa chọn mô hình khỏi quá trình ước lượng hiệu năng."),
 ("BÁO CÁO TRUNG THỰC, KHÔNG CHỌN CON SỐ ĐẸP",
  "Kèm khoảng tin cậy và độ dao động giữa các lần chia dữ liệu; báo cáo phân bố hiệu năng theo từng cá thể để bộc lộ trường hợp mô hình hoạt động kém; kết quả âm tính và không tái lập được vẫn được công bố."),
 ("AI CÓ THỂ DIỄN GIẢI LÀ BẮT BUỘC",
  "SHAP \u00b7 LIME \u00b7 Grad-CAM \u00b7 Integrated Gradients \u00b7 Attention Visualization \u00b7 permutation importance, đối chiếu với nhận định chuyên môn. \u26a0 Kết quả diễn giải KHÔNG phải bằng chứng về quan hệ nhân quả giữa đặc trưng và bệnh."),
 ("KIỂM ĐỊNH ĐỘC LẬP TRƯỚC KHI TIN",
  "ND3 kiểm định ngoại vi chéo bệnh viện và thử nghiệm trên dữ liệu độc lập về thời gian \u00b7 ND1 & ND4 giữ tập kiểm thử theo thời gian \u00b7 ND2 & ND5 đánh giá trên bệnh nhân chưa từng xuất hiện trong huấn luyện."),
 ("ĐỊNH VỊ SẢN PHẨM",
  "Mọi sản phẩm của nhiệm vụ là CÔNG CỤ HỖ TRỢ ra quyết định lâm sàng: kết quả do mô hình sinh ra phải được bác sĩ xem xét, xác nhận và diễn giải; không thay thế chẩn đoán và phán đoán chuyên môn."),
]

BAND2_PANELS = [
 ("QUẢN TRỊ DỮ LIỆU & TUÂN THỦ PHÁP LÝ", [
   "Mã giả hóa và TÁCH BIỆT thông tin định danh khỏi dữ liệu nghiên cứu \u00b7 mã hóa khi lưu trữ và truyền tải \u00b7 phân quyền truy cập theo vai trò \u00b7 ghi nhật ký kiểm toán mọi hoạt động truy cập \u00b7 cơ chế sao lưu.",
   "\u26a0 Bản ghi giọng nói được xem là DỮ LIỆU SINH TRẮC HỌC có nguy cơ tái định danh cao \u2192 áp dụng bảo vệ dữ liệu ngay từ giai đoạn thiết kế hệ thống.",
   "Tuân thủ Nghị định 13/2023/NĐ-CP và Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15 \u00b7 Toàn bộ nghiên cứu chỉ triển khai sau khi được Hội đồng Đạo đức trong nghiên cứu y sinh học phê duyệt.",
 ]),
 ("MẠNG LƯỚI PHỐI HỢP LIÊN NGÀNH", [
   "BV QUÂN Y 175 \u2013 đối tác lâm sàng chủ lực (hệ thống EEG + TMS, không gian thu âm, nguồn bệnh): ND1 \u00b7 ND2 \u00b7 ND3 \u00b7 ND5",
   "BV NGUYỄN TRI PHƯƠNG \u2013 kho dữ liệu EEG động kinh có sẵn nhãn kênh và nhãn thể cơn; chuyên môn sức khỏe tâm thần: ND3 \u00b7 ND4",
   "ĐH BÁCH KHOA \u2013 ĐHQG-HCM \u2013 đối tác kỹ thuật: thiết kế, huấn luyện, tối ưu mô hình AI; phát triển phần mềm, nền tảng ứng dụng và tích hợp hệ thống: ND1 \u00b7 ND3",
   "TƯ VẤN QUỐC TẾ: H. Christensen, M. Roantree, Ngô Thanh Hoàn \u2192 ND1, ND4  \u2016  T. Kishimoto \u2192 ND1, ND5  \u2016  M. Miyakoshi \u2192 ND2, ND3, ND5",
 ]),
 ("RỦI RO TRỌNG YẾU & BIỆN PHÁP KIỂM SOÁT", [
   "\u26a0 Tuyển chọn đối tượng không đạt kế hoạch, tỷ lệ bỏ theo dõi cao \u2192 mở rộng mạng lưới bệnh viện, kéo dài thời gian tuyển, dự phòng 15\u201320% cỡ mẫu, theo dõi tiến độ hằng tháng.",
   "\u26a0 Dữ liệu EEG / giọng nói / lâm sàng không đồng nhất giữa các cơ sở \u2192 ban hành quy trình chuẩn SOP, đào tạo nhân sự, kiểm tra chất lượng định kỳ, tiền xử lý và kiểm soát chất lượng tự động.",
   "\u26a0 Hiệu năng mô hình không đạt yêu cầu \u2192 đánh giá đa chỉ số, tối ưu siêu tham số, tăng dữ liệu, học chuyển giao, mô hình ensemble, kiểm định trên tập độc lập.",
   "\u26a0 Mất an toàn thông tin và dữ liệu cá nhân \u2192 mã hóa, phân quyền, ẩn danh, máy chủ bảo mật, tuân thủ quy định bảo vệ dữ liệu và đạo đức nghiên cứu y sinh.",
 ]),
]

# ================================================================ svg build
out = []
def add(s): out.append(s)
def esc(s): return escape(s)

def rect(x, y, w, h, fill, stroke=None, rx=4, sw=1, dash=None, op=None):
    a = f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" rx="{rx}" fill="{fill}"'
    if stroke: a += f' stroke="{stroke}" stroke-width="{sw}"'
    if dash: a += f' stroke-dasharray="{dash}"'
    if op: a += f' opacity="{op}"'
    add(a + '/>')

def text(x, y, s, size, style="r", fill=INK, anchor="start", ls=0):
    fam = "DejaVu Sans, Arial, Helvetica, sans-serif"
    w = "700" if style == "b" else "400"
    it = ' font-style="italic"' if style == "i" else ""
    extra = f' letter-spacing="{ls}"' if ls else ""
    add(f'<text x="{x:.1f}" y="{y:.1f}" font-family="{fam}" font-size="{size}" font-weight="{w}"{it} fill="{fill}" text-anchor="{anchor}"{extra}>{esc(s)}</text>')

def draw_blocks(blocks, x, y, width, accent):
    cy = y
    for el in blocks:
        cy = draw_elem(el, x, cy, width, accent)
    return cy

def draw_elem(el, x, y, width, accent):
    k = el[0]
    if k == "row":
        _, items, title = el
        cy = y
        if title:
            for ln in wrap(title, width, S_H, "b"):
                cy += LH_H; text(x, cy - 4, ln, S_H, "b", accent)
            cy += 3
        n_ = len(items)
        sw = (width - (n_-1)*8) / n_
        hmax = 0
        for lab, blocks in items:
            hmax = max(hmax, 8 + LH_H + 2 + blocks_height(blocks, sw-16) + 8)
        for i, (lab, blocks) in enumerate(items):
            bx = x + i*(sw+8)
            rect(bx, cy, sw, hmax, "#FFFFFF", accent, rx=5, sw=1.3)
            ty = cy + 8 + LH_H - 4
            text(bx+8, ty, lab, S_H, "b", accent)
            draw_blocks(blocks, bx+8, cy+8+LH_H+2, sw-16, accent)
        # converging arrows
        cxm = x + width/2
        add(f'<path d="M {x+sw/2:.1f} {cy+hmax:.1f} L {cxm:.1f} {cy+hmax+9:.1f} L {x+width-sw/2:.1f} {cy+hmax:.1f}" fill="none" stroke="{accent}" stroke-width="1.2" opacity="0.65"/>')
        return cy + hmax + 12
    if k == "branch":
        _, items, title = el
        cy = y
        if title:
            for ln in wrap(title, width, S_H, "b"):
                cy += LH_H; text(x, cy - 4, ln, S_H, "b", accent)
            cy += 3
        rail = x + 9
        top = cy
        for lab, blocks in items:
            bw = width - 30
            bh = 8 + LH_H + 2 + blocks_height(blocks, bw-16) + 8
            rect(x+30, cy, bw, bh, "#FFFFFF", accent, rx=5, sw=1.3)
            text(x+38, cy+8+LH_H-4, lab, S_H, "b", accent)
            draw_blocks(blocks, x+38, cy+8+LH_H+2, bw-16, accent)
            add(f'<path d="M {rail:.1f} {cy+bh/2:.1f} L {x+30:.1f} {cy+bh/2:.1f}" stroke="{accent}" stroke-width="1.6" fill="none"/>')
            add(f'<circle cx="{x+30:.1f}" cy="{cy+bh/2:.1f}" r="2.6" fill="{accent}"/>')
            cy += bh + 9
        add(f'<path d="M {rail:.1f} {top+10:.1f} L {rail:.1f} {cy-19:.1f}" stroke="{accent}" stroke-width="1.6" fill="none"/>')
        return cy
    if k == "j":  # joint / callout box
        txt = el[1]
        lines = wrap(txt, width - 22, S_P, "b")
        bh = len(lines)*LH_P + 14
        rect(x, y+2, width, bh, "#FFF9EC", "#C9A24A", rx=5, sw=1.4)
        add(f'<rect x="{x:.1f}" y="{y+2:.1f}" width="4.5" height="{bh:.1f}" rx="2" fill="#C9A24A"/>')
        cy = y + 2 + 7
        for ln in lines:
            cy += LH_P; text(x+13, cy-4, ln, S_P, "b", "#5B4A16")
        return y + bh + 9
    # simple text blocks
    lines, size, lh, sty = block_lines(k, el[1], width)
    fill = {"h": accent, "b": INK, "p": INK2, "n": NOTE, "w": WARN, "o": OK, "s": STARC}.get(k, INK2)
    styl = {"h": "b", "b": "b", "n": "i", "w": "r", "o": "b", "s": "b"}.get(k, "r")
    if k == "w":
        lines = wrap(el[1], width, S_P, "r"); size, lh = S_P, LH_P
    if k in ("o", "s"):
        lines = wrap(el[1], width, S_P, "b"); size, lh = S_P, LH_P
    cy = y
    for ln in lines:
        cy += lh
        text(x, cy - 4, ln, size, styl, fill)
    return cy + 4

# ---- measure everything
hdr_h = 214
grp_h = 40
colhdr_h = 0
for c in COLS:
    hh = 12 + 21 + 4 + len(wrap(c["sub"], CW-2*PAD, 13.4, "b"))*17 + 3 + len(wrap(c["meta"], CW-2*PAD, 11, "r"))*14 + 6
    if c["core"]: hh += 20
    colhdr_h = max(colhdr_h, hh + 10)
link_h = 62
tier_h = []
for tid, tname, cells in TIERS:
    hh = 0
    for cell in cells:
        hh = max(hh, blocks_height(cell, TXTW) + 2*PAD + 6)
    tier_h.append(hh)
band1_h = 0
b1w = (W - 2*MARG - 20 - 5*10) / 6
for t, d in BAND1_ITEMS:
    band1_h = max(band1_h, len(wrap(t, b1w-18, 12, "b"))*15.5 + len(wrap(d, b1w-18, 10.9, "r"))*14.2 + 24)
band1_h += 44
band2_h = 0
b2w = (W - 2*MARG - 20 - 2*12) / 3
for t, items in BAND2_PANELS:
    hh = 26
    for it in items:
        hh += len(wrap(it, b2w-20, 11.2, "r"))*14.5 + 5
    band2_h = max(band2_h, hh + 16)
band2_h += 34
foot_h = 62

TIER_GAP = 13
H = int(hdr_h + grp_h + colhdr_h + link_h + sum(tier_h) + len(tier_h)*TIER_GAP
        + band1_h + 16 + band2_h + 14 + foot_h + MARG)

add(f'<svg xmlns="http://www.w3.org/2000/svg" width="{W}" height="{H}" viewBox="0 0 {W} {H}">')
add(f'<rect width="{W}" height="{H}" fill="{PAGE}"/>')

# ---------------- header
y = MARG
rect(MARG, y, W-2*MARG, hdr_h-10, "#0E2233", None, rx=7)
add(f'<rect x="{MARG}" y="{y}" width="{W-2*MARG}" height="6" rx="3" fill="{VOICE_M}"/>')
add(f'<rect x="{MARG+(W-2*MARG)/2}" y="{y}" width="{(W-2*MARG)/2}" height="6" rx="3" fill="{EEG_M}"/>')
tx = MARG + 26
text(tx, y+52, "NÂNG CAO NĂNG LỰC CHẨN ĐOÁN, SÀNG LỌC VÀ QUẢN LÝ BỆNH LÝ TÂM THẦN KINH", 31, "b", "#FFFFFF")
text(tx, y+86, "(ĐỘNG KINH \u2013 ALZHEIMER \u2013 TRẦM CẢM) TRONG BỐI CẢNH GIÀ HÓA DÂN SỐ", 31, "b", "#FFFFFF")
text(tx, y+112, "Nhiệm vụ phát triển công nghệ  \u00b7  Thời gian thực hiện 30 tháng  \u00b7  SƠ ĐỒ TỔNG THỂ 5 NỘI DUNG NGHIÊN CỨU", 14.5, "b", "#8FC0DE")
mg = wrap("MỤC TIÊU CHUNG: phát hiện các dấu ấn sinh học số (digital biomarkers) từ tín hiệu giọng nói và điện não đồ trên dữ liệu người Việt Nam; xây dựng các mô hình học máy \u2013 học sâu có khả năng diễn giải để hỗ trợ sàng lọc, chẩn đoán và dự đoán đáp ứng điều trị; đóng gói thành phần mềm hỗ trợ quyết định lâm sàng và kiểm thử trên dữ liệu thực tế tại bệnh viện đối tác.", 1500, 13.2, "r")
yy = y+140
for ln in mg:
    yy += 17.5; text(tx, yy, ln, 13.2, "r", "#D3E3EE")

# mini matrix
mx, my, mcw, mch = W - MARG - 780, y + 26, 176, 34
text(mx, my-8, "BẢN ĐỒ ĐỊNH VỊ 5 NỘI DUNG", 12.5, "b", "#8FC0DE")
heads = ["", "ALZHEIMER", "ĐỘNG KINH", "TRẦM CẢM"]
for j, hh_ in enumerate(heads):
    if j: text(mx + j*mcw + mcw/2, my+20, hh_, 11.6, "b", "#CBDDE9", "middle")
rows = [("GIỌNG NÓI", VOICE_M, ["NỘI DUNG 1", "\u2014", "NỘI DUNG 4"]),
        ("EEG / TMS-EEG", EEG_M, ["NỘI DUNG 2", "NỘI DUNG 3", "NỘI DUNG 5"])]
for i, (lab, col, cells3) in enumerate(rows):
    ry = my + 28 + i*(mch+6)
    rect(mx, ry, mcw-6, mch, col, None, rx=4)
    text(mx + (mcw-6)/2, ry+22, lab, 11.6, "b", "#FFFFFF", "middle")
    for j, cc in enumerate(cells3):
        cx0 = mx + (j+1)*mcw
        f = "#1B3B52" if cc != "\u2014" else "#16293A"
        rect(cx0, ry, mcw-6, mch, f, "#3E6C8B", rx=4)
        text(cx0 + (mcw-6)/2, ry+22, cc, 12, "b", "#FFFFFF" if cc != "\u2014" else "#4E6A80", "middle")

# legend
lx = W - MARG - 300
text(lx, my-8, "KÝ HIỆU", 12.5, "b", "#8FC0DE")
leg = [("\u25ad", "Quy trình / SOP"), ("\u2b21", "Mô hình AI, bộ đặc trưng"),
       ("\u25a4", "Cơ sở dữ liệu"), ("\u2b22", "Phần mềm / mô-đun"),
       ("\u2605", "Sản phẩm lõi, điểm nhấn"), ("\u26a0", "Điểm kiểm soát then chốt"),
       ("\u25b8", "Ghi chú lý do phương pháp")]
for i, (sym, lab) in enumerate(leg):
    ly = my + 14 + i*20
    text(lx, ly, sym, 13, "b", "#E3B36A")
    text(lx+22, ly, lab, 11.5, "r", "#CBDDE9")

y += hdr_h

# ---------------- group band
gA0, gA1 = CX[0], CX[2]+CW
gB0, gB1 = CX[3], CX[4]+CW
rect(gA0, y, gA1-gA0, grp_h-8, "#F6EDE1", VOICE_B, rx=5, sw=1.4)
rect(gB0, y, gB1-gB0, grp_h-8, "#E9F1F7", EEG_B, rx=5, sw=1.4)
text((gA0+gA1)/2, y+21, "NHÓM A \u2013 SÀNG LỌC, PHÁT HIỆN VÀ THEO DÕI BỆNH BẰNG DẤU ẤN SINH HỌC SỐ   (đầu ra: điểm nguy cơ / danh sách sự kiện có thời điểm)", 13.6, "b", "#6E4415", "middle")
text((gB0+gB1)/2, y+21, "NHÓM B \u2013 DỰ ĐOÁN ĐÁP ỨNG ĐIỀU TRỊ TMS, HƯỚNG TỚI CÁ THỂ HÓA   (đầu ra: Δ điểm lâm sàng / phân loại đáp ứng)", 13.6, "b", "#123E5C", "middle")
text(MARG+8, y+21, "TRỤC CÂU HỎI\nLÂM SÀNG", 11.4, "b", MUTED)
y += grp_h

# ---------------- column headers
for i, c in enumerate(COLS):
    D, M, L, B = (VOICE_D, VOICE_M, VOICE_L, VOICE_B) if c["mod"] == "voice" else (EEG_D, EEG_M, EEG_L, EEG_B)
    rect(CX[i], y, CW, colhdr_h-6, L, B, rx=6, sw=1.5)
    add(f'<rect x="{CX[i]}" y="{y}" width="{CW}" height="7" rx="3" fill="{M}"/>')
    cy = y + 12
    text(CX[i]+PAD, cy+18, c["tag"], 20, "b", D)
    badge = c["dis"]; bw2 = tw(badge, 11.2, "b") + 18
    rect(CX[i]+CW-PAD-bw2, cy+4, bw2, 20, M, None, rx=10)
    text(CX[i]+CW-PAD-bw2/2, cy+18, badge, 11.2, "b", "#FFFFFF", "middle")
    cy += 21 + 4
    for ln in wrap(c["sub"], CW-2*PAD, 13.4, "b"):
        cy += 17; text(CX[i]+PAD, cy, ln, 13.4, "b", INK)
    cy += 3
    for ln in wrap(c["meta"], CW-2*PAD, 11, "r"):
        cy += 14; text(CX[i]+PAD, cy, ln, 11, "r", MUTED)
    if c["core"]:
        cy += 6
        rect(CX[i]+PAD, cy, CW-2*PAD, 18, "#FFF4DC", "#C9A24A", rx=4, sw=1.2)
        text(CX[i]+PAD+7, cy+13, "\u2605 " + c["core"], 10.9, "b", "#7A5A12")
text(MARG+8, y+26, "NỘI DUNG\nNGHIÊN CỨU", 12.2, "b", INK2)
y += colhdr_h

# ---------------- link row
def pill(x0, x1, yy, txt, col, fill):
    w_ = x1-x0
    rect(x0, yy, w_, 34, fill, col, rx=17, sw=1.4, dash="6 4")
    text((x0+x1)/2, yy+21, txt, 11.5, "b", col, "middle")
    add(f'<path d="M {x0-9:.1f} {yy+17:.1f} l 9 -6 v 12 z" fill="{col}"/>')
    add(f'<path d="M {x1+9:.1f} {yy+17:.1f} l -9 -6 v 12 z" fill="{col}"/>')
pill(CX[0]+CW*0.30, CX[1]+CW*0.70, y+8,
     "\u2261 CHUNG PIPELINE GIỌNG NÓI: VAD \u00b7 phân tách người nói \u00b7 ASR tiếng Việt \u00b7 eGeMAPS \u00b7 embedding tự giám sát \u2013 khác nhau ở bộ tác vụ nói và nhãn tham chiếu lâm sàng",
     VOICE_D, "#FBF2E6")
pill(CX[3]+CW*0.22, CX[4]+CW*0.78, y+8,
     "\u2261 CHUNG KHUNG NGHIÊN CỨU DỌC T0 \u2013 T2 \u2013 T4 và phép so sánh 3 nhóm mô hình (lâm sàng | EEG | kết hợp)",
     EEG_D, "#E9F1F7")
rect(CX[2]+CW*0.06, y+8, CW*0.88, 34, "#EFF3F0", "#9AA9A0", rx=17, sw=1.3, dash="6 4")
text(CX[2]+CW/2, y+29, "\u25c6 NGUỒN DỮ LIỆU HỒI CỨU \u2013 không phụ thuộc tiến độ tuyển bệnh", 11.5, "b", "#3E5148", "middle")
y += link_h

# ---------------- tiers
for ti, (tid, tname, cells) in enumerate(TIERS):
    th = tier_h[ti]
    band = TIER_A if ti % 2 == 0 else TIER_B
    rect(MARG, y, W-2*MARG, th, band, "#E2E6E2", rx=6, sw=1)
    # gutter label
    add(f'<circle cx="{MARG+34}" cy="{y+34}" r="17" fill="{INK}"/>')
    text(MARG+34, y+41, tid, 20, "b", "#FFFFFF", "middle")
    ly = y + 66
    for ln in tname.split("\n"):
        ly += 17; text(MARG+14, ly, ln, 13.4, "b", INK)
    for i, cell in enumerate(cells):
        c = COLS[i]
        D, M, L, B = (VOICE_D, VOICE_M, VOICE_L, VOICE_B) if c["mod"] == "voice" else (EEG_D, EEG_M, EEG_L, EEG_B)
        ch = blocks_height(cell, TXTW) + 2*PAD
        rect(CX[i], y+4, CW, ch, "#FFFFFF", B, rx=5, sw=1.2)
        add(f'<rect x="{CX[i]}" y="{y+4:.1f}" width="3.5" height="{ch:.1f}" rx="1.8" fill="{M}"/>')
        draw_blocks(cell, CX[i]+PAD, y+4+PAD-4, TXTW, D)
        if ti < len(TIERS)-1:
            ax = CX[i] + CW/2
            ay = y + th + 1
            add(f'<path d="M {ax-8:.1f} {ay:.1f} l 8 9 l 8 -9 z" fill="{M}" opacity="0.8"/>')
    y += th + TIER_GAP
    if ti == 4:  # after tier 5 -> band1
        pass

# ---------------- band 1 (methodology)
rect(MARG, y, W-2*MARG, band1_h, BAND1_F, BAND1_B, rx=6, sw=1.6)
add(f'<rect x="{MARG}" y="{y}" width="{W-2*MARG}" height="5" rx="2.5" fill="{BAND1_B}"/>')
text(MARG+16, y+29, "NGUYÊN TẮC PHƯƠNG PHÁP LUẬN BẮT BUỘC \u2013 ÁP DỤNG THỐNG NHẤT CHO CẢ 5 NỘI DUNG", 15.5, "b", BAND1_D)
text(MARG+16, y+29+18, "Đây là điều kiện để kết quả có giá trị chuyển giao, không phải phần phụ lục kỹ thuật: phần lớn mô hình EEG/giọng nói công bố trước đây bị thổi phồng hiệu năng do vi phạm chính các nguyên tắc này.", 11.6, "i", "#7A6A3E")
by = y + 62
for i, (t, d) in enumerate(BAND1_ITEMS):
    bx = MARG + 10 + i*(b1w+10)
    rect(bx, by, b1w, band1_h-72, "#FFFFFF", BAND1_B, rx=5, sw=1.1)
    cy = by + 8
    for ln in wrap(t, b1w-18, 12, "b"):
        cy += 15.5; text(bx+9, cy-3, ln, 12, "b", BAND1_D)
    cy += 3
    for ln in wrap(d, b1w-18, 10.9, "r"):
        cy += 14.2; text(bx+9, cy-3, ln, 10.9, "r", INK2)
y += band1_h + 16

# ---------------- band 2
rect(MARG, y, W-2*MARG, band2_h, BAND2_F, BAND2_B, rx=6, sw=1.4)
text(MARG+16, y+26, "NỀN TẢNG TRIỂN KHAI CHUNG", 15, "b", BAND2_D)
py = y + 40
for i, (t, items) in enumerate(BAND2_PANELS):
    bx = MARG + 10 + i*(b2w+12)
    rect(bx, py, b2w, band2_h-52, "#FFFFFF", BAND2_B, rx=5, sw=1.1)
    add(f'<rect x="{bx}" y="{py}" width="{b2w}" height="4" rx="2" fill="{BAND2_D}"/>')
    cy = py + 12
    cy += 16; text(bx+10, cy-3, t, 12.4, "b", BAND2_D)
    cy += 4
    for it in items:
        for ln in wrap(it, b2w-20, 11.2, "r"):
            cy += 14.5; text(bx+10, cy-3, ln, 11.2, "r", INK2)
        cy += 5
y += band2_h + 14

# ---------------- footer
rect(MARG, y, W-2*MARG, foot_h-8, "#0E2233", None, rx=6)
text(MARG+18, y+24, "ĐẦU RA TỔNG HỢP CỦA NHIỆM VỤ:  02 phần mềm lõi (ND1 sàng lọc giọng nói + tác nhân ảo  \u2016  ND3 hỗ trợ đọc EEG dài hạn)  \u00b7  05 quy trình chuẩn thu nhận \u2013 xử lý \u2013 phân tích  \u00b7  05 bộ đặc trưng / dấu ấn sinh học số trên dữ liệu người Việt  \u00b7  05 nhóm mô hình AI có khả năng diễn giải  \u00b7  cơ sở dữ liệu lâm sàng đa phương thức", 12.4, "b", "#FFFFFF")
text(MARG+18, y+45, "Công bố khoa học quốc tế  \u00b7  Tài sản trí tuệ (02 sáng chế trong nước)  \u00b7  Đào tạo NCS và học viên cao học  \u00b7  Địa chỉ ứng dụng và chuyển giao trước mắt: Bệnh viện Quân y 175 và Bệnh viện Nguyễn Tri Phương  \u00b7  Lộ trình: kiểm thử kỹ thuật \u2192 đánh giá trên dữ liệu độc lập \u2192 thử nghiệm lâm sàng có giám sát \u2192 hoàn thiện và mở rộng", 12.4, "r", "#A9C7DC")

add('</svg>')

svg = "\n".join(out)
open("/home/claude/sodo.svg", "w", encoding="utf-8").write(svg)
print("W,H =", W, H)