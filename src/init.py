# init.py
import os
os.environ["USE_TF"] = "0"
os.environ["USE_TORCH"] = "1"
os.environ["TF_CPP_MIN_LOG_LEVEL"] = "3"
os.environ["PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION"] = "python"

from langchain_openai import ChatOpenAI
from elasticsearch import Elasticsearch

# --- CẤU HÌNH API KEY ---
os.environ["OPENAI_API_KEY"] = "sk-SSme5jNJVdhGlfBfwKKXZghoOknQ0a1asIDWYYw271BFJgtK"
os.environ["OPENAI_BASE_URL"] = "https://gpt2.shupremium.com/v1"

BASIC_AUTH = ("elastic", "jCIzg963pq6qBMNzU5n1iFEs")
CLOUD_ID = "a436a8f89eed43f1a274176a33838755:dXMtY2VudHJhbDEuZ2NwLmNsb3VkLmVzLmlvOjQ0MyQwODZhM2VlYmE3NDM0MGU4OWUyMjgzN2U2M2I2NTg5MyRhZDI2Nzc0MWRkYjA0ODVkOGU4MzYxMzM5MjY0MjNlMw==" # Copy từ Elastic Cloud
INDEX_MAPPING = {
    "course": "idx_jina_2_course",
    "program": "idx_jina_2_program"
}

COURSE_FIELD_MAP = {
    "ask_ve_giang_vien": "thong_tin_ve_giang_vien",
    "ask_ve_thong_tin_chung": "thong_tin_chung_mon_hoc",
    "ask_ve_muc_tieu": "muc_tieu_mon_hoc",
    "ask_ve_chuan_dau_ra": "chuan_dau_ra",
    "ask_ve_tom_tat_noi_dung": "tom_tat_noi_dung_mon_hoc",
    "ask_ve_noi_dung_chi_tiet": "noi_dung_chi_tiet_mon_hoc",
    "ask_ve_tai_lieu": "tai_lieu_tham_khao",
    "ask_ve_hinh_thuc_to_chuc": "hinh_thuc_to_chuc_mon_hoc",
    "ask_ve_chinh_sach": "chinh_sach_hoc_tap",
    "ask_ve_danh_gia": "phuong_thuc_danh_gia"
}

PROGRAM_FIELD_MAP = {
    "ask_ve_gioi_thieu_chung": "gioi_thieu_chung",
    "ask_ve_chuan_dau_ra": "chuan_dau_ra",
    "ask_ve_tom_tat_ctdt": "tom_tat_chuong_trinh_dao_tao",
    "ask_ve_khoi_kien_thuc_chung": "ly_luan_chinh_tri_va_giao_duc_dai_cuong",
    "ask_ve_khoi_co_ban": "toan_khoa_hoc_co_ban",
    "ask_ve_khoi_co_so_nganh": "co_so_nganh_hoc",
    "ask_ve_khoi_chuyen_nganh": "chuyen_nganh_tot_nghiep"
}

# --- KHỞI TẠO CÁC CLIENT NHẸ TẠI GLOBAL ---
llm = ChatOpenAI(model="gpt-4o-mini", temperature=0, max_retries=2)
es_client = Elasticsearch(cloud_id=CLOUD_ID, basic_auth=BASIC_AUTH, request_timeout=120)

# --- BIẾN TOÀN CỤC CHO LOCAL MODELS (Ban đầu là None) ---
embed_model = None
reranker = None
llm_engine = None
tokenizer = None

# --- HÀM LAZY LOAD: Chỉ gọi 1 lần khi FastAPI chạy ---
def load_local_models():
    global embed_model, reranker, llm_engine, tokenizer
    if llm_engine is not None:
        return

    from sentence_transformers import SentenceTransformer
    from FlagEmbedding import FlagReranker
    from vllm import LLM

    print("\n⏳ Đang tải Jina Embeddings...")
    embed_model = SentenceTransformer("jinaai/jina-embeddings-v3", trust_remote_code=True)
    embed_model.max_seq_length = 1024

    print("⏳ Đang tải BGE-M3 Reranker...")
    reranker = FlagReranker("nguyen10001/bge-m3-reranker-vnu-courses", use_fp16=True)

    print("⏳ Đang tải Llama 3.1 INT4 (vLLM)...")
    llm_engine = LLM(
        model="hugging-quants/Meta-Llama-3.1-8B-Instruct-AWQ-INT4",
        quantization="awq",
        dtype="float16",
        gpu_memory_utilization=0.55,
        max_model_len=2048,
        enforce_eager=True
    )
    tokenizer = llm_engine.get_tokenizer()
    print("✅ ĐÃ LOAD XONG TOÀN BỘ MÔ HÌNH!\n")