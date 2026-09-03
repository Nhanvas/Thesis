"""
edf_order.py — sắp xếp thứ tự file EDF THEO HEADER TIME, dành riêng cho backend web demo (SzScan).

TẠI SAO FILE NÀY TỒN TẠI (khác evaluation_protocol.parse_summary_edf_list)
----------------------------------------------------------------------------
evaluation_protocol.parse_summary_edf_list() sort file theo TÊN FILE
(`edfs.sort(key=lambda x: x['fname'])`) — quy ước ĐÃ KHÓA cho pipeline evaluation
sinh ra số liệu §0, KHÔNG được sửa file đó.

Web demo đã chốt (WEB_DEMO_CONTEXT_BOUNDARY.md, quyết định #4): thứ tự HIỂN THỊ
trên UI sort theo `File Start Time` trong header EDF, không theo tên file — vì
có mâu thuẫn thật trong CHB-MIT (vd chb03_24.edf tên đứng trước nhưng giờ ghi
16:39 muộn hơn chb03_25.edf ghi lúc 15:38).

GIỚI HẠN THẬT SỰ CỦA CÁCH LÀM NÀY (nói thẳng, không giấu)
-----------------------------------------------------------
Header EDF chỉ ghi "HH:MM:SS" — KHÔNG có ngày tháng. Với 1 subject ghi trải dài
nhiều ngày, giờ trong ngày sẽ "quay vòng" (vd 23:50 rồi lại 00:10 của ngày kế
tiếp) nhiều lần suốt bản ghi. Sort thuần theo giá trị giờ trong ngày SẼ SAI khi
có quay vòng như vậy — 00:10 sẽ bị coi là "sớm hơn" 23:50 dù thực ra muộn hơn
1 ngày.

Cách xử lý ĐÚNG cần biết thêm NGÀY của mỗi file — thông tin này KHÔNG có trong
`chb*-summary.txt`. Không có cách nào suy ra ngày tuyệt đối chỉ từ giờ-trong-
ngày một cách chắc chắn 100% khi dữ liệu vốn không cung cấp.

QUYẾT ĐỊNH THỰC DỤNG (chấp nhận, không giả vờ hoàn hảo)
----------------------------------------------------------
1. Sort CHÍNH theo thứ tự tên file (đáng tin cho việc phân biệt các phiên ghi
   CÁCH XA nhau — số thứ tự trong tên tăng dần theo từng phiên ghi mới).
2. CHỈ hoán đổi 2 file LIỀN KỀ NHAU (theo tên) nếu giờ header của chúng chênh
   lệch NGƯỢC nhưng trong phạm vi NHỎ (< SWAP_THRESHOLD_S, mặc định 2 giờ) —
   đây là dấu hiệu lỗi đồng hồ cục bộ kiểu chb03_24/25 (cùng buổi, đồng hồ ghi
   lộn), KHÔNG PHẢI dấu hiệu qua ngày mới (qua ngày mới sẽ chênh lệch có thể
   rất lớn theo hướng khác, hoặc lặp lại mỗi ~24h một cách có quy luật).
3. Bất kỳ trường hợp nào NGOÀI phạm vi này (chênh lệch lớn, nhiều file liền kề
   cùng bất thường) → GIỮ NGUYÊN thứ tự theo tên file, KHÔNG cố tự động sửa —
   an toàn hơn là đoán sai.

Đây là 1 heuristic có giới hạn rõ ràng, xử lý đúng trường hợp ĐÃ QUAN SÁT ĐƯỢC
(chb03_24/25) nhưng KHÔNG đảm bảo đúng cho mọi subject/mọi lỗi đồng hồ có thể
xảy ra. Nếu phát hiện thứ tự hiển thị sai với 1 subject cụ thể khi test thật,
cần xem lại thủ công — không tin tưởng mù quáng heuristic này.

QUAN HỆ VỚI edf_index.EdfIndex
-------------------------------
EdfIndex vẫn dùng parse_summary_edf_list gốc (sort theo tên) để xây global
timeline cho việc CHẠY CPD (đúng logic evaluation, khớp §0). File này chỉ đổi
THỨ TỰ HIỂN THỊ trên UI — 2 việc tách biệt:
    1. edf_index.EdfIndex          -> global timeline (backend chạy PELT)
    2. edf_order.sorted_by_header  -> thứ tự file hiển thị (frontend duyệt)
Sau khi PELT chạy xong, dùng EdfIndex.locate_range(start_s, end_s) để map mỗi
detected_event về (filename, local_start_s, local_end_s), rồi tra order_index
tương ứng ở đây để biết hiển thị ở vị trí thứ mấy trên UI.
"""
import re
from dataclasses import dataclass
from pathlib import Path
from typing import List

SWAP_THRESHOLD_S = 2 * 3600   # chỉ hoán đổi nếu chênh lệch < 2 giờ (heuristic, xem docstring)


@dataclass
class OrderedFile:
    filename: str
    start_time_header: str
    order_index: int          # dùng cho Previous/Next + progress dots
    duration_s: float


def _hms_to_seconds(t: str) -> int:
    p = t.strip().split(":")
    return int(p[0]) * 3600 + int(p[1]) * 60 + int(p[2])


def parse_summary_sorted_by_header(summary_path: str) -> List[OrderedFile]:
    """Đọc {subj}-summary.txt, trả về danh sách file cho THỨ TỰ HIỂN THỊ web demo.
    Mặc định giữ thứ tự theo tên file; chỉ hoán đổi 2 file liền kề nếu phát hiện
    mâu thuẫn giờ trong phạm vi nhỏ (xem giới hạn ở docstring module)."""
    text = Path(summary_path).read_text()
    pat = re.compile(
        r'File Name:\s*(\S+\.edf)\s+File Start Time:\s*(\S+)\s+'
        r'File End Time:\s*(\S+)\s+Number of Seizures in File:\s*(\d+)',
        re.DOTALL)
    raw = []
    for m in pat.finditer(text):
        fname, t0, t1, _ = m.groups()
        dur = _hms_to_seconds(t1) - _hms_to_seconds(t0)
        if dur <= 0:
            dur += 86400
        raw.append({'fname': fname, 'start_raw': t0, 'dur': dur})

    raw.sort(key=lambda x: x['fname'])   # thứ tự gốc, đáng tin cho phiên ghi cách xa nhau

    i = 0
    while i < len(raw) - 1:
        a, b = raw[i], raw[i + 1]
        ta, tb = _hms_to_seconds(a['start_raw']), _hms_to_seconds(b['start_raw'])
        if tb < ta and (ta - tb) < SWAP_THRESHOLD_S:
            raw[i], raw[i + 1] = raw[i + 1], raw[i]
            i = max(0, i - 1)   # lùi lại 1 bước phòng chuỗi hoán đổi liên tiếp
        else:
            i += 1

    return [OrderedFile(filename=r['fname'], start_time_header=r['start_raw'],
                        order_index=idx, duration_s=float(r['dur']))
            for idx, r in enumerate(raw)]
