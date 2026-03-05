from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Literal, Optional
import os

router = APIRouter(prefix="/api", tags=["api"])

class Message(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str

class ChatRequest(BaseModel):
    messages: List[Message]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7

@router.post("/chat")
def chat(req: ChatRequest):
    provider = os.getenv("LLM_PROVIDER", "gigachat")
    if provider != "gigachat":
        raise HTTPException(status_code=400, detail="Only gigachat is configured")

    creds = os.getenv("GIGACHAT_CREDENTIALS")
    if not creds:
        raise HTTPException(status_code=500, detail="GIGACHAT_CREDENTIALS is empty in .env")

    try:
        from gigachat import GigaChat
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"gigachat package not installed: {e}")

    # ВАЖНО: verify_ssl_certs может упасть без сертификата.
    # Если словишь SSL ошибку — скажи мне, я дам правильный вариант с CA.
    try:
        with GigaChat(credentials=creds, verify_ssl_certs=False) as gc:
            messages = [{"role": m.role, "content": m.content} for m in req.messages]
            resp = gc.chat({"messages": messages, "temperature": req.temperature})
            answer = resp.choices[0].message.content
            return {"reply": answer}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))