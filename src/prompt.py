# prompt.py
from lib import ChatPromptTemplate, StrOutputParser
from init import llm
from schema import IntentResult, CourseExtraction, ProgramExtraction
# ======================================================
# 0. REPHRASE CHAIN (Viết lại câu hỏi dựa trên lịch sử)
# ======================================================
rephrase_system = """
Bạn là chuyên gia ngôn ngữ giúp làm rõ câu hỏi của sinh viên.
Nhiệm vụ: Dựa vào LỊCH SỬ HỘI THOẠI, hãy viết lại câu hỏi mới nhất của người dùng thành một câu hỏi ĐỘC LẬP (Standalone Question) đầy đủ ngữ nghĩa.
Thông tin của sinh viên là: {user_info}
Quy tắc:
1. Nếu câu hỏi mới chứa các từ thay thế (như "môn đó", "nó", "ngành này", "ở trên"...), hãy thay thế chúng bằng danh từ cụ thể được nhắc đến trong lịch sử chat.
2. Giữ nguyên ý định của câu hỏi. KHÔNG trả lời câu hỏi, chỉ viết lại thôi.
3. Nếu câu hỏi đã rõ ràng và không liên quan đến lịch sử, hãy giữ nguyên câu hỏi đó.

Ví dụ:
- Lịch sử: User: "Môn AI có mấy tín chỉ?" -> AI: "3 tín chỉ"
- Câu mới: "Thế còn môn Toán rời rạc?"
- Viết lại: "Môn Toán rời rạc có mấy tín chỉ?"

Ví dụ 2:
- Lịch sử: User: "Cho tôi hỏi về môn Trí tuệ nhân tạo"
- Câu mới: "Nội dung môn đó là gì?"
- Viết lại: "Nội dung môn Trí tuệ nhân tạo là gì?"
"""

rephrase_prompt = ChatPromptTemplate.from_messages([
    ("system", rephrase_system),
    ("human", "LỊCH SỬ HỘI THOẠI:\n{chat_history}\n\nCÂU HỎI MỚI: {query}")
])

rephrase_chain = rephrase_prompt | llm | StrOutputParser()
# ======================================================
# 1. CLASSIFIER CHAIN (Phân loại Intent)
# ======================================================
classifier_system = """
Bạn là bộ phân loại intent (course/program) cho sinh viên UET.
Dưới đây là thông tin sinh viên đang hỏi: {user_info}

### ĐỊNH NGHĨA INTENT:
1. **course (Môn học)**: 
   - Hỏi chi tiết VỀ NỘI DUNG môn học: tín chỉ, giảng viên, đề cương, tài liệu, cách thi, điểm số...
   - Ví dụ: "Môn Toán rời rạc bao nhiêu tín chỉ?", "Ai dạy môn Giải tích?"

2. **program (Chương trình đào tạo/Ngành)**:
   - Hỏi về TÊN NGÀNH, KHÓA HỌC (K65...), lộ trình học.
   - Hỏi về **CẤU TRÚC CHƯƠNG TRÌNH**: môn này có bắt buộc không, môn này thuộc nhóm nào, cần học bao nhiêu tín chỉ để ra trường...

### QUY TẮC ƯU TIÊN (QUAN TRỌNG - Áp dụng theo thứ tự):
1. **Ngoại lệ "Bắt buộc/Tự chọn"**: Nếu câu hỏi chứa tên môn học NHƯNG lại hỏi về tính chất **"bắt buộc"**, **"tự chọn"**, **"có phải học không"**, **"điều kiện tốt nghiệp"** -> Hãy chọn **program** (vì cần tra cứu Khung chương trình đào tạo của ngành).
2. Nếu câu hỏi chỉ nhắc tên môn học để hỏi thông tin chi tiết (tín chỉ, thầy cô...) -> Chọn **course**.
3. Nếu câu hỏi mơ hồ KHÔNG có tên môn học -> Dựa vào `user_info` để chọn **program**.
"""

classifier_prompt = ChatPromptTemplate.from_messages([
    ("system", classifier_system),
    ("human", "{query}")
])

classifier_chain = classifier_prompt | llm.with_structured_output(IntentResult)


# ======================================================
# 2. COURSE EXTRACT CHAIN (Trích xuất Môn học)
# ======================================================
course_system_prompt = """
Bạn là chuyên gia trích xuất thông tin Môn học (Course) tại UET.
Thông tin sinh viên: {user_info}

### NHIỆM VỤ:
Trích xuất thông tin từ câu hỏi dựa trên định nghĩa sau. 
Nếu câu hỏi thiếu thông tin (ví dụ niên khóa), hãy tham khảo `Thông tin sinh viên` ở trên để bổ sung nếu hợp lý.

### BẢNG ĐỊNH NGHĨA DỮ LIỆU:
{{
    "metadata": {{
        "ten_mon_hoc": "tên môn học (Chuẩn hóa về tiếng Việt)",
        "ma_mon_hoc": "mã môn học (VD: INT3401)",
        "so_tin_chi": "số tín chỉ",
        "hoc_phan_tien_quyet": "môn tiên quyết"
    }},
    "detail_subject": {{
        "thong_tin_ve_giang_vien": "giảng viên, email, văn phòng",
        "thong_tin_chung_mon_hoc": "giới thiệu chung",
        "muc_tieu_mon_hoc": "mục tiêu môn học",
        "chuan_dau_ra": "chuẩn đầu ra môn học",
        "tom_tat_noi_dung_mon_hoc": "tóm tắt nội dung",
        "noi_dung_chi_tiet_mon_hoc": "đề cương chi tiết",
        "tai_lieu_tham_khao": "sách, giáo trình",
        "hinh_thuc_to_chuc_mon_hoc": "giờ học lý thuyết/thực hành",
        "chinh_sach_hoc_tap": "điểm danh, quy định lớp",
        "phuong_thuc_danh_gia": "cách tính điểm, thi giữa kỳ/cuối kỳ"
    }}
}}

### HƯỚNG DẪN:
- Đánh dấu `True` vào các trường `detail_subject` nếu người dùng hỏi về khía cạnh đó.
"""

course_chain = (
    ChatPromptTemplate.from_messages([
        ("system", course_system_prompt),
        ("human", "{query}")
    ]) 
    | llm.with_structured_output(CourseExtraction)
)


# ======================================================
# 3. PROGRAM EXTRACT CHAIN (Trích xuất Ngành học)
# ======================================================
program_system_prompt = """
Bạn là chuyên gia trích xuất thông tin Chương trình đào tạo (Program) tại UET.
Thông tin sinh viên: {user_info}

### NHIỆM VỤ (QUAN TRỌNG):
Trích xuất thông tin ngành học. 
**LƯU Ý ĐẶC BIỆT**: Nếu người dùng không nói rõ tên ngành hay khóa học trong câu hỏi, HÃY SỬ DỤNG `Thông tin sinh viên` để điền vào các trường `ten_nganh`, `nien_khoa`, `he_dao_tao`.

### BẢNG ĐỊNH NGHĨA DỮ LIỆU:
{{
    "metadata":{{
        "ten_nganh": "tên ngành (VD: Công nghệ thông tin)",
        "nien_khoa": "Năm bắt đầu khóa (VD: K67 -> 2022)",
        "he_dao_tao": "hệ chuẩn / chất lượng cao"
    }},
    "detail_program":{{
        "gioi_thieu_chung": "giới thiệu ngành",
        "chuan_dau_ra": "chuẩn đầu ra của ngành",
        "tom_tat_chuong_trinh_dao_tao": "khung chương trình tổng quát",
        "ly_luan_chinh_tri_va_giao_duc_dai_cuong": "Môn chung (Triết, Pháp luật...)",
        "toan_khoa_hoc_co_ban": "Môn nền tảng (Toán, Lý...)",
        "co_so_nganh_hoc": "Môn cơ sở cốt lõi",
        "chuyen_nganh_tot_nghiep": "Môn chuyên sâu, thực tập, đồ án"
    }}
}}

### HƯỚNG DẪN:
- Đánh dấu `True` vào các trường `detail_program` tương ứng với câu hỏi.
"""

program_chain = (
    ChatPromptTemplate.from_messages([
        ("system", program_system_prompt),
        ("human", "{query}")
    ]) 
    | llm.with_structured_output(ProgramExtraction)
)


# ======================================================
# 4. ANSWER GENERATION CHAIN (Trả lời cuối cùng)
# ======================================================
answer_system_prompt = """
Bạn là Trợ lý ảo tư vấn học vụ UET.
Thông tin sinh viên đang hỏi: {user_info}

Nhiệm vụ: Trả lời câu hỏi dựa trên CONTEXT được cung cấp.

### CONTEXT:
{context}

### YÊU CẦU:
1. Trả lời chính xác dựa trên Context.
2. Nếu Context rỗng, hãy nói "Hiện chưa có dữ liệu chi tiết".
3. Tùy chỉnh xưng hô phù hợp với sinh viên (ví dụ: "Với sinh viên khóa {user_info}...").
"""

answer_prompt = ChatPromptTemplate.from_messages([
    ("system", answer_system_prompt),
    ("human", "{query}")
])

answer_chain = answer_prompt | llm | StrOutputParser()