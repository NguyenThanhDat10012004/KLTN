# schema.py
from lib import BaseModel, Field, Optional, Literal

# --- 1. SCHEMA CHO PHÂN LOẠI (CLASSIFICATION) ---
class IntentResult(BaseModel):
    intent_type: Literal["course", "program", "unknown"] = Field(
        ..., 
        description="Phân loại câu hỏi: 'course' (môn học), 'program' (ngành/CTĐT), hoặc 'unknown' nếu không rõ."
    )

# --- 2. SCHEMA CHO INTENT COURSE ---
class CourseExtraction(BaseModel):
    # Metadata
    ten_mon_hoc: Optional[str] = Field(None, description="Tên môn học")
    ma_mon_hoc: Optional[str] = Field(None, description="Mã môn học")
    so_tin_chi: Optional[int] = Field(None, description="Số tín chỉ")
    hoc_phan_tien_quyet: Optional[str] = Field(None, description="Môn tiên quyết")
    
    # Details Flags
    ask_ve_giang_vien: bool = Field(False, description="Hỏi về giảng viên")
    ask_ve_thong_tin_chung: bool = Field(False, description="Hỏi thông tin chung")
    ask_ve_muc_tieu: bool = Field(False, description="Hỏi mục tiêu")
    ask_ve_chuan_dau_ra: bool = Field(False, description="Hỏi chuẩn đầu ra")
    ask_ve_tom_tat_noi_dung: bool = Field(False, description="Hỏi tóm tắt nội dung")
    ask_ve_noi_dung_chi_tiet: bool = Field(False, description="Hỏi đề cương chi tiết")
    ask_ve_tai_lieu: bool = Field(False, description="Hỏi tài liệu/giáo trình")
    ask_ve_hinh_thuc_to_chuc: bool = Field(False, description="Hỏi hình thức tổ chức")
    ask_ve_chinh_sach: bool = Field(False, description="Hỏi chính sách/điểm danh")
    ask_ve_danh_gia: bool = Field(False, description="Hỏi cách thi/đánh giá điểm")

# --- 3. SCHEMA CHO INTENT PROGRAM ---
class ProgramExtraction(BaseModel):
    # Metadata
    ten_nganh: Optional[str] = Field(None, description="Tên ngành")
    nien_khoa: Optional[int] = Field(None, description="Năm khóa (VD: 2022)")
    he_dao_tao: Optional[str] = Field(None, description="Hệ đào tạo")
    
    # Details Flags
    ask_ve_gioi_thieu_chung: bool = Field(False, description="Hỏi giới thiệu chung")
    ask_ve_chuan_dau_ra: bool = Field(False, description="Hỏi chuẩn đầu ra")
    ask_ve_tom_tat_ctdt: bool = Field(False, description="Hỏi tóm tắt chương trình")
    ask_ve_khoi_kien_thuc_chung: bool = Field(False, description="Hỏi khối kiến thức chung")
    ask_ve_khoi_co_ban: bool = Field(False, description="Hỏi khối cơ bản")
    ask_ve_khoi_co_so_nganh: bool = Field(False, description="Hỏi khối cơ sở ngành")
    ask_ve_khoi_chuyen_nganh: bool = Field(False, description="Hỏi khối chuyên ngành")