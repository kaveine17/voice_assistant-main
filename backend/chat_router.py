from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel, Field
from typing import List, Literal, Optional
import os
import ssl
from sqlalchemy.orm import Session

from database import get_db

# Workaround для SSL UNEXPECTED_EOF_WHILE_READING при работе с GigaChat API
# (сервер может закрывать соединение без close_notify, OpenSSL 3.0 строже это проверяет)
if hasattr(ssl, "OP_IGNORE_UNEXPECTED_EOF"):
    _orig_create_default = ssl.create_default_context

    def _patched_create_default(purpose=ssl.Purpose.SERVER_AUTH, cafile=None, capath=None, cadata=None):
        ctx = _orig_create_default(purpose, cafile, capath, cadata)
        ctx.options |= ssl.OP_IGNORE_UNEXPECTED_EOF
        return ctx

    ssl.create_default_context = _patched_create_default
from models import Conversation, Message as DBMessage, User
from schemas import ConversationCreate, ConversationOut, ConversationUpdate, MessageCreate, MessageOut
from auth_router import get_current_user

router = APIRouter(prefix="/api", tags=["api"])


# ---------------- PUNCTUATION VIA GIGACHAT ----------------
class PunctuateIn(BaseModel):
    text: str = Field(min_length=1)


class PunctuateOut(BaseModel):
    text: str


@router.post("/punctuate", response_model=PunctuateOut)
def punctuate(req: PunctuateIn):
    """
    Восстановление пунктуации через LLM (GigaChat).
    На входе "сырой" текст распознавания, на выходе — тот же текст
    с расставленными запятыми, вопросительными/восклицательными знаками и т.п.
    """
    text = req.text.strip()
    if not text:
        raise HTTPException(status_code=400, detail="Текст пустой")

    messages = [
        {
            "role": "system",
            "content": (
                "Ты помощник, который расставляет знаки препинания в русском тексте. "
                "Ничего не переводишь и не переписываешь, только: "
                "1) расставляешь запятые, точки, вопросительные, восклицательные знаки и тире; "
                "2) при необходимости ставишь заглавную букву в начале предложения; "
                "3) возвращаешь ТОЛЬКО исправленный текст, без пояснений и кавычек."
            ),
        },
        {
            "role": "user",
            "content": text,
        },
    ]

    try:
        punctuated = ask_gigachat(messages=messages, temperature=0.1)
    except HTTPException:
        # пробрасываем HTTP-ошибки наверх (например, проблемы с GigaChat)
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

    # небольшой safety: если LLM вдруг вернёт мусор, подстрахуемся исходным текстом
    if not isinstance(punctuated, str) or not punctuated.strip():
        punctuated = text

    return PunctuateOut(text=punctuated.strip())


# ---------------- EXISTING CHAT REQUEST TO GIGACHAT ----------------
class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant"]
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatMessage]
    model: Optional[str] = None
    temperature: Optional[float] = 0.7


class SendMessageRequest(BaseModel):
    content: str = Field(min_length=1)


class SendMessageResponse(BaseModel):
    reply: str
    user_message_id: int
    assistant_message_id: int
    conversation_title: str


def ask_gigachat(messages: List[dict], temperature: float = 0.7) -> str:
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

    try:
        with GigaChat(credentials=creds, verify_ssl_certs=False) as gc:
            resp = gc.chat({"messages": messages, "temperature": temperature})
            return resp.choices[0].message.content
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


def generate_conversation_title(first_user_message: str) -> str:
    """
    Генерация короткого названия чата по первому сообщению пользователя.
    Пытаемся использовать GigaChat, при ошибке — простой fallback.
    """
    text = first_user_message.strip()
    if not text:
        return "Новый чат"

    system_prompt = (
        "Ты придумываешь КОРОТКИЕ, ёмкие названия для чатов на русском языке. "
        "Используй не больше 5–6 слов. "
        "Не добавляй кавычки и лишние комментарии, возвращай только название."
    )

    try:
        title = ask_gigachat(
            messages=[
                {"role": "system", "content": system_prompt},
                {
                    "role": "user",
                    "content": f"Придумай название для чата по этому сообщению: {text}",
                },
            ],
            temperature=0.3,
        )
        title = (title or "").strip()
        if not title:
            raise ValueError("empty title")
        return title[:255]
    except Exception:
        # Fallback: усечённое первое сообщение
        short = text[:60].strip()
        return short or "Новый чат"


@router.post("/chat")
def chat(req: ChatRequest):
    messages = [{"role": m.role, "content": m.content} for m in req.messages]
    answer = ask_gigachat(messages=messages, temperature=req.temperature or 0.7)
    return {"reply": answer}


# ---------------- CONVERSATIONS ----------------
@router.post("/conversations", response_model=ConversationOut, status_code=201)
def create_conversation(
    data: ConversationCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    title = (data.title or "").strip()
    conversation = Conversation(
        user_id=user.id,
        title=title or "Новый чат",
    )
    db.add(conversation)
    db.commit()
    db.refresh(conversation)
    return conversation


@router.get("/conversations", response_model=list[ConversationOut])
def get_conversations(
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversations = (
        db.query(Conversation)
        .filter(Conversation.user_id == user.id)
        .order_by(Conversation.created_at.desc())
        .all()
    )
    return conversations


@router.delete("/conversations/{conversation_id}", status_code=204)
def delete_conversation(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )
    if not conversation:
        raise HTTPException(status_code=404, detail="Чат не найден")
    db.delete(conversation)
    db.commit()
    return None


@router.patch("/conversations/{conversation_id}", response_model=ConversationOut)
def rename_conversation(
    conversation_id: int,
    data: ConversationUpdate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Чат не найден")

    new_title = data.title.strip()
    if not new_title:
        raise HTTPException(status_code=400, detail="Название чата не может быть пустым")

    conversation.title = new_title[:255]
    db.add(conversation)
    db.commit()
    db.refresh(conversation)

    return conversation


@router.get("/conversations/{conversation_id}/messages", response_model=list[MessageOut])
def get_messages(
    conversation_id: int,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Чат не найден")

    messages = (
        db.query(DBMessage)
        .filter(DBMessage.conversation_id == conversation_id)
        .order_by(DBMessage.created_at.asc())
        .all()
    )
    return messages


@router.post("/conversations/{conversation_id}/messages", response_model=MessageOut, status_code=201)
def create_message(
    conversation_id: int,
    data: MessageCreate,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Чат не найден")

    message = DBMessage(
        conversation_id=conversation_id,
        role="user",
        content=data.content.strip(),
    )
    db.add(message)
    db.commit()
    db.refresh(message)

    return message


# ---------------- SEND MESSAGE + SAVE AI REPLY ----------------
@router.post("/conversations/{conversation_id}/send", response_model=SendMessageResponse)
def send_message(
    conversation_id: int,
    data: SendMessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    conversation = (
        db.query(Conversation)
        .filter(Conversation.id == conversation_id, Conversation.user_id == user.id)
        .first()
    )

    if not conversation:
        raise HTTPException(status_code=404, detail="Чат не найден")

    content = data.content.strip()
    if not content:
        raise HTTPException(status_code=400, detail="Сообщение не может быть пустым")

    # 1. сохраняем сообщение пользователя
    user_message = DBMessage(
        conversation_id=conversation_id,
        role="user",
        content=content,
    )
    db.add(user_message)
    db.commit()
    db.refresh(user_message)

    # 2. получаем всю историю чата
    db_messages = (
        db.query(DBMessage)
        .filter(DBMessage.conversation_id == conversation_id)
        .order_by(DBMessage.created_at.asc())
        .all()
    )

    # 3. преобразуем историю в формат GigaChat
    giga_messages = [
        {"role": msg.role, "content": msg.content}
        for msg in db_messages
    ]

    # 4. получаем ответ ассистента
    assistant_reply = ask_gigachat(messages=giga_messages, temperature=0.7)

    # 5. сохраняем ответ ассистента
    assistant_message = DBMessage(
        conversation_id=conversation_id,
        role="assistant",
        content=assistant_reply,
    )
    db.add(assistant_message)
    db.commit()
    db.refresh(assistant_message)

    # 6. автоназвание чата по первому сообщению, если ещё не переименован
    if conversation.title in ("Новый чат", "", None):
        try:
            auto_title = generate_conversation_title(first_user_message=content)
            conversation.title = auto_title
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        except Exception:
            # Не критично, если автоназвание не удалось — просто оставляем старый title
            pass

    return SendMessageResponse(
        reply=assistant_reply,
        user_message_id=user_message.id,
        assistant_message_id=assistant_message.id,
        conversation_title=conversation.title,
    )