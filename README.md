# Trợ lý học vụ UET (Chatbot RAG)

Hệ thống Trợ lý học vụ dành cho sinh viên trường Đại học Công nghệ (UET) ứng dụng công nghệ Retrieval-Augmented Generation (RAG) với mô hình ngôn ngữ lớn (LLM). Hệ thống giúp sinh viên tra cứu thông tin về môn học, tín chỉ, khung chương trình đào tạo và các quy chế học vụ một cách chính xác dựa trên thông tin định danh (Ngành, Khóa, Hệ đào tạo).

## Yêu cầu hệ thống 

Do hệ thống sử dụng các mô hình Deep Learning nặng (Llama-3.1-8B, BGE-M3, Jina-embeddings), kiến trúc triển khai được chia làm 2 phần độc lập:

* **Backend (Google Colab):** Cần tài khoản Google để sử dụng Google Colab (Khuyến nghị bật Runtime T4 GPU để chạy vLLM).
* **Ngrok:** Cần một tài khoản Ngrok (miễn phí) và `Authtoken` để mở port nội bộ của Colab ra Internet.
* **Frontend (Streamlit Cloud):** Cần tài khoản GitHub và Streamlit Community Cloud.

---

## Hướng dẫn cài đặt và triển khai (Deployment)

Việc triển khai hệ thống phải tuân thủ đúng thứ tự: **Bật Backend (Colab) trước -> Lấy Link API -> Cập nhật Frontend -> Deploy UI.**

### Bước 1: Khởi chạy Backend trên Google Colab
Backend chịu trách nhiệm load LLM vào VRAM và giao tiếp với Elasticsearch.

1. Tạo một sổ tay (Notebook) mới trên Google Colab và bật GPU (`Runtime` > `Change runtime type` > `T4 GPU`).
2. Tải toàn bộ các file `.py` trong thư mục `src` (**ngoại trừ `ui.py`**) lên môi trường của Colab.
3. Cài đặt các thư viện cần thiết bằng cách chạy cell sau:
   ```bash
   !pip install fastapi uvicorn pyngrok nest-asyncio langchain_openai elasticsearch sentence_transformers FlagEmbedding vllm
   
```
4. Mở file `api.py` (hoặc file chứa code API tương ứng), tìm đến dòng `ngrok.set_auth_token("...")` và đảm bảo bạn đã điền Authtoken Ngrok của mình.
5. Khởi chạy Backend bằng lệnh:
   ```bash
   !python api.py
   
```
6. Chờ vài phút để hệ thống tải trọng số các mô hình vào GPU. Khi thành công, terminal sẽ in ra dòng:
   `API ENDPOINT CỦA BẠN: https://<chuoi-ngau-nhien>.ngrok-free.dev/chat`
   *(Hãy COPY đường link này).*

### Bước 2: Cập nhật cấu hình Frontend (Local)
1. Mở file `src/ui.py` trên máy tính cục bộ của bạn.
2. Tìm biến `API_URL` ở đầu file và dán đường link API vừa copy từ Bước 1 vào.
   ```python
   # Ví dụ:
   API_URL = "[https://1234abcd.ngrok-free.dev/chat](https://1234abcd.ngrok-free.dev/chat)"
   
```
3. Lưu file `ui.py`.
4. Đảm bảo bạn đã có file `requirements.txt` trong thư mục `src/` (hoặc thư mục root) với nội dung sau để Streamlit nhận diện thư viện:
   ```text
   requests
   
```
5. Thực hiện commit và đẩy code mới nhất lên GitHub:
   ```bash
   git add .
   git commit -m "Update API URL and requirements"
   git push origin main
   
```

### Bước 3: Deploy Giao diện lên Streamlit Community Cloud
1. Truy cập [share.streamlit.io](https://share.streamlit.io/) và đăng nhập bằng tài khoản GitHub của bạn.
2. Bấm **"New app"** (hoặc "Create app").
3. Chọn Repository KLTN của bạn, chọn nhánh `main` (hoặc `master`).
4. Tại mục **Main file path**, điền đường dẫn tới file UI: `src/ui.py`.
5. Bấm **"Deploy!"**. Quá trình khởi tạo giao diện sẽ mất khoảng 1-2 phút.

---

##  Chạy thử phần mềm và Demo

Sau khi Streamlit deploy thành công, bạn sẽ nhận được một đường link public cho giao diện người dùng.

1. **Màn hình khởi tạo:** Nhập thông tin định danh sinh viên (Ngành học, Niên khóa, Hệ đào tạo) và bấm "Bắt đầu Chat".

2. **Màn hình Chat:** Giao diện có Sidebar lưu thông tin cá nhân. Tại khung chat, hãy đặt các câu hỏi đa dạng, ví dụ:
   * *"Môn Giải tích 1 có bao nhiêu tín chỉ?"* 
   * *"Thầy cô nào dạy môn Cơ sở dữ liệu?"*
   * *"Ngành Công nghệ thông tin khóa 2022 có những môn tự chọn nào?"* (Truy xuất Khung chương trình đào tạo).
