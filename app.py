# ui.py
import streamlit as st
import requests

API_URL = "https://unpernicious-vaccinal-silvia.ngrok-free.dev/chat"

st.set_page_config(page_title="UET Student Assistant", page_icon="🎓")

# Init Session
if "user_info" not in st.session_state:
    st.session_state.user_info = None
if "messages" not in st.session_state:
    st.session_state.messages = []

# --- MÀN HÌNH 1: NHẬP THÔNG TIN ---
if st.session_state.user_info is None:
    st.title("🎓 Trợ lý học vụ UET")
    st.markdown("Chào bạn! Hãy cung cấp thông tin để mình hỗ trợ chính xác hơn nhé.")
    
    with st.form("info_form"):
        c1, c2 = st.columns(2)
        ten_nganh = c1.text_input("Ngành học", placeholder="VD: Công nghệ thông tin")
        nien_khoa = c1.text_input("Niên khóa", placeholder="VD: 2022")
        he_dao_tao = c2.selectbox("Hệ đào tạo", ["Chuẩn", "Chất lượng cao", "Khác"])
        
        if st.form_submit_button("Bắt đầu Chat 🚀"):
            st.session_state.user_info = {
                "ten_nganh": ten_nganh,
                "nien_khoa": nien_khoa,
                "he_dao_tao": he_dao_tao
            }
            st.rerun()

# --- MÀN HÌNH 2: GIAO DIỆN CHAT ---
else:
    # Sidebar
    with st.sidebar:
        st.header("Thông tin của bạn")
        info = st.session_state.user_info
        st.success(f"📚 Ngành: {info.get('ten_nganh')}")
        st.info(f"🎓 Khóa: {info.get('nien_khoa')}")
        st.warning(f"🏫 Hệ: {info.get('he_dao_tao')}")
        
        if st.button("🔄 Đổi thông tin"):
            st.session_state.user_info = None
            st.session_state.messages = []
            st.rerun()

    st.title("💬 Hỏi đáp Học vụ")

    # Hiển thị lịch sử chat
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

    # Xử lý nhập liệu
    if prompt := st.chat_input("Hỏi tôi về môn học, tín chỉ, giảng viên..."):
        # 1. Hiển thị câu hỏi user
        st.session_state.messages.append({"role": "user", "content": prompt})
        with st.chat_message("user"):
            st.markdown(prompt)

        # 2. Gọi API
        with st.chat_message("assistant"):
            with st.spinner("Đang tra cứu dữ liệu..."):
                try:
                    # Lấy lịch sử chat (trừ câu vừa hỏi) gửi lên server để xử lý ngữ cảnh
                    history_to_send = st.session_state.messages[:-1]
                    if len(history_to_send) > 20: 
                        history_to_send = history_to_send[-20:]

                    payload = {
                        "query": prompt,
                        "history": history_to_send,
                        **st.session_state.user_info
                    }
                    
                    res = requests.post(API_URL, json=payload)
                    
                    if res.status_code == 200:
                        data = res.json()
                        bot_reply = data.get("answer", "Lỗi: Không nhận được câu trả lời.")
                        
                        # Chỉ hiển thị câu trả lời (Markdown)
                        st.markdown(bot_reply)
                    else:
                        st.error(f"Lỗi Server: {res.status_code}")
                        bot_reply = "Có lỗi xảy ra khi kết nối server."
                        
                except Exception as e:
                    st.error(f"Lỗi kết nối: {e}")
                    bot_reply = "Không thể kết nối đến hệ thống."
        
        # 3. Lưu câu trả lời vào lịch sử
        st.session_state.messages.append({"role": "assistant", "content": bot_reply})
