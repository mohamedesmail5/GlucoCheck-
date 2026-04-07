"""
DiabetesAI — AI Agent Layer (LangChain + OpenAI/Anthropic)
Handles: Chat, Streaming, Image Analysis, Grade Classification
"""
import os
import json
import base64
from typing import AsyncGenerator
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
from langchain_openai import ChatOpenAI
from langchain.memory import ConversationBufferWindowMemory
from langchain.schema import SystemMessage, HumanMessage, AIMessage
from database import supabase
from auth import get_current_user
import numpy as np

chat_router = APIRouter(tags=["Chat"])

# ─── System Prompt ─────────────────────────────────────────────────────────────
MEDICAL_SYSTEM_PROMPT = """أنت DiabetesAI — مساعد طبي ذكي متخصص في تشخيص ومتابعة مرض السكري.

## هويتك:
- مساعد طبي مدرّب على أحدث الإرشادات الطبية (ADA, WHO, IDF)
- متخصص في: تشخيص السكري، تحليل نتائج الفحوصات، خطط الرعاية الذاتية
- **لستَ طبيبًا مرخصًا** — دورك الدعم والتثقيف وليس التشخيص الطبي الرسمي

## درجات تصنيف السكري:
| الدرجة | التصنيف | السكر الصائم | الإجراء |
|--------|---------|--------------|---------|
| Grade 0 | طبيعي / ما قبل السكري | < 125 mg/dL | وقاية + نمط حياة صحي |
| Grade 1 | سكري خفيف | 126-180 mg/dL | نظام غذائي + متابعة دورية |
| Grade 2 | سكري متوسط | 181-300 mg/dL | علاج دوائي + خطة مكثفة |
| Grade 3 | سكري حاد | > 300 mg/dL | **إحالة طبية فورية** |

## تعليمات الرد:
1. استخدم اللغة العربية بشكل افتراضي، وأجب بالإنجليزية إذا سألك المريض بها
2. اسأل عن: السكر الصائم، HbA1c، العمر، الوزن، الأعراض، التاريخ العائلي
3. بعد جمع المعلومات، حدد الدرجة وقدم خطة واضحة
4. كن دافئًا ومطمئنًا لكن صريحًا في الحالات الحرجة
5. أنهِ كل تشخيص بـ: **[GRADE: X]** حيث X هو رقم الدرجة (0-3)
6. للحالات الحرجة (Grade 3): أضف **[URGENT: TRUE]**

## تنسيق الردود:
- استخدم عناوين واضحة مع **bold**
- قوائم منظمة للتوصيات
- لا تستخدم emoji — استخدم نص فقط
"""

# In-memory session memories (production: use Redis)
session_memories: dict = {}


def get_memory(session_id: str) -> ConversationBufferWindowMemory:
    if session_id not in session_memories:
        session_memories[session_id] = ConversationBufferWindowMemory(
            k=20, return_messages=True
        )
    return session_memories[session_id]


def classify_grade_from_response(text: str) -> int | None:
    import re
    m = re.search(r'\[GRADE:\s*([0-3])\]', text)
    return int(m.group(1)) if m else None


# ─── Pydantic Models ───────────────────────────────────────────────────────────
class ChatRequest(BaseModel):
    session_id: str
    message:    str
    image_url:  str | None = None


# ─── Streaming Chat Endpoint ───────────────────────────────────────────────────
@chat_router.post("/chat")
async def chat_stream(req: ChatRequest, current_user=Depends(get_current_user)):
    """Stream AI response token by token via Server-Sent Events."""

    llm = ChatOpenAI(
        model       = "gpt-4o-mini",
        temperature = 0.3,
        streaming   = True,
        openai_api_key = os.environ.get("OPENAI_API_KEY", "")
    )

    memory = get_memory(req.session_id)
    history = memory.chat_memory.messages

    messages = [SystemMessage(content=MEDICAL_SYSTEM_PROMPT)] + history
    if req.image_url:
        messages.append(HumanMessage(content=[
            {"type": "text",      "text": req.message},
            {"type": "image_url", "image_url": {"url": req.image_url}}
        ]))
    else:
        messages.append(HumanMessage(content=req.message))

    async def token_generator() -> AsyncGenerator[str, None]:
        full_response = ""
        async for chunk in llm.astream(messages):
            token = chunk.content
            full_response += token
            yield f"data: {json.dumps({'token': token})}\n\n"

        # Save to DB
        grade = classify_grade_from_response(full_response)
        supabase.table("messages").insert([
            {"session_id": req.session_id, "role": "user",  "content": req.message},
            {"session_id": req.session_id, "role": "agent", "content": full_response}
        ]).execute()

        if grade is not None:
            supabase.table("diagnoses").insert({
                "session_id": req.session_id,
                "user_id":    current_user["id"],
                "grade":      grade,
                "source":     "text"
            }).execute()
            supabase.table("sessions").update({
                "grade": grade, "updated_at": "now()"
            }).eq("id", req.session_id).execute()

        memory.chat_memory.add_user_message(req.message)
        memory.chat_memory.add_ai_message(full_response)

        yield f"data: {json.dumps({'done': True, 'grade': grade})}\n\n"

    return StreamingResponse(
        token_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"}
    )


@chat_router.get("/messages/{session_id}")
async def get_messages(session_id: str, current_user=Depends(get_current_user)):
    res = supabase.table("messages")\
        .select("*")\
        .eq("session_id", session_id)\
        .order("created_at")\
        .execute()
    return res.data


@chat_router.get("/diagnoses")
async def get_diagnoses(current_user=Depends(get_current_user)):
    res = supabase.table("diagnoses")\
        .select("*, sessions(title)")\
        .eq("user_id", current_user["id"])\
        .order("created_at", desc=True)\
        .execute()
    return res.data
