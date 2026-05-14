# api.py
import uvicorn
import nest_asyncio
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, List, Dict
from pyngrok import ngrok
from contextlib import asynccontextmanager

import init # Import init module
from backend_service import get_answer_from_llm

# Dùng lifespan để ép hệ thống tải model một cách an toàn
@asynccontextmanager
async def lifespan(app: FastAPI):
    init.load_local_models()
    yield
    # Có thể thêm code dọn dẹp bộ nhớ ở đây nếu cần

app = FastAPI(lifespan=lifespan)

class ChatRequest(BaseModel):
    query: str
    history: List[Dict[str, str]] = Field(default=[], description="Lịch sử chat")
    ten_nganh: Optional[str] = None
    nien_khoa: Optional[str] = None
    he_dao_tao: Optional[str] = None

@app.post("/chat")
async def chat_endpoint(request: ChatRequest):
    try:
        user_context = {
            "ten_nganh": request.ten_nganh,
            "nien_khoa": request.nien_khoa,
            "he_dao_tao": request.he_dao_tao
        }
        result = get_answer_from_llm(request.query, request.history, user_context)
        return result 
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    nest_asyncio.apply()
    
    # Nhớ điền token ngrok nếu chưa có
    # ngrok.set_auth_token("TOKEN_CỦA_BẠN")
    ngrok.set_auth_token("3B749o8q3M7uXwxXbDhGDMuFpwz_7cYVYeGJdQK7K34xPkVpf")
    public_url = ngrok.connect(8000).public_url
    print("\n" + "="*50)
    print(f"🚀 API ENDPOINT CỦA BẠN: {public_url}/chat")
    print("="*50 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)