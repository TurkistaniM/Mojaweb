"""
تطبيق وخادم منصة "مُجاوِب" (Mojaweb)
خادم ويب عالي الأداء مبني بـ FastAPI ومصمم للنشر المباشر على منصة Render
يدعم تحليل المستندات والصوتيات ومقاطع الفيديو والدردشة المقيدة والتلخيص والاختبارات
"""

import os
import sys
from typing import List, Optional
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env إن وجد (للتطوير المحلي)
load_dotenv()

from fastapi import FastAPI, UploadFile, File, Form, Header, HTTPException, Request, status
from fastapi.responses import HTMLResponse, JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from session_manager import session_manager, EphemeralSession, MAX_TOTAL_BUNDLE_BYTES
from openrouter_client import openrouter_client
from document_parser import DocumentParser

# قراءة مفاتيح وإعدادات البيئة
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
PORT = int(os.environ.get("PORT", 8000))
HOST = os.environ.get("HOST", "0.0.0.0")

app = FastAPI(
    title="مُجاوِب (Mojaweb) - المساعد الدراسي الذكي",
    description="منصة دراسية تفاعلية تعتمد على RAG الصارم لملفات وصوتيات وفيديوهات الطلاب 100%",
    version="1.1.0"
)

# تمكين CORS لمرونة الاستخدام
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATES_DIR = BASE_DIR / "templates"
STATIC_DIR = BASE_DIR / "static"

# تجهيز الملفات الثابتة
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")


# نماذج البيانات لطلبات الـ API (Pydantic Models)
class ChatRequest(BaseModel):
    query: str
    session_id: Optional[str] = None


class SummarizeRequest(BaseModel):
    session_id: Optional[str] = None


class QuizRequest(BaseModel):
    session_id: Optional[str] = None
    num_questions: int = 5
    quiz_type: str = "all"  # "all", "mcq", "boolean"


class ClearSessionRequest(BaseModel):
    session_id: Optional[str] = None


def get_current_session(session_id: Optional[str] = None, x_session_id: Optional[str] = None) -> EphemeralSession:
    """استرجاع الجلسة المؤقتة الحالية بناءً على المعرف الممرر"""
    sid = session_id or x_session_id
    return session_manager.get_or_create_session(sid)


# -------------------------------------------------------------
# نقاط النهاية (API Endpoints)
# -------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def serve_home():
    """تقديم الواجهة الرئيسية للتطبيق"""
    index_file = TEMPLATES_DIR / "index.html"
    if index_file.exists():
        return FileResponse(str(index_file))
    return HTMLResponse("<h1>منصة مُجاوِب (Mojaweb) تعمل بنجاح</h1>")


@app.get("/api/health")
async def health_check():
    """فحص صحة الخدمة والإعدادات وحالة مفتاح الذكاء الاصطناعي"""
    api_key_configured = bool(os.environ.get("OPENROUTER_API_KEY", "").strip())
    model_name = openrouter_client.get_model()
    return {
        "status": "online",
        "app_name": "Mojaweb (مُجاوِب)",
        "version": "1.1.0",
        "author": "محمد تركستاني",
        "openrouter_configured": api_key_configured,
        "model": model_name,
        "supported_formats": list(DocumentParser.SUPPORTED_EXTENSIONS),
        "max_bundle_size_mb": 50
    }


@app.post("/api/session/new")
async def create_new_session():
    """إنشاء جلسة ضيف جديدة وتزويد الواجهة بمعرف الجلسة"""
    session = session_manager.get_or_create_session()
    return {
        "session_id": session.session_id,
        "created_at": session.created_at,
        "message": "تم إنشاء جلسة مؤقتة جديدة بنجاح"
    }


@app.get("/api/files")
async def list_files(
    session_id: Optional[str] = None,
    x_session_id: Optional[str] = Header(None)
):
    """عرض قائمة الملفات النشطة في الجلسة وحجمها الإجمالي"""
    session = get_current_session(session_id, x_session_id)
    files_list = [
        {
            "file_id": f.file_id,
            "filename": f.filename,
            "size_bytes": f.size_bytes,
            "size_formatted": f.size_formatted,
            "sections_count": f.sections_count,
            "chunks_count": f.chunks_count,
            "uploaded_at": f.uploaded_at
        }
        for f in session.files.values()
    ]
    return {
        "session_id": session.session_id,
        "files": files_list,
        "total_files": len(files_list),
        "total_size_bytes": session.total_size_bytes,
        "total_size_mb": round(session.total_size_mb, 2),
        "max_size_mb": 50,
        "total_chunks": len(session.rag_engine.chunks)
    }


@app.post("/api/upload")
async def upload_files(
    files: List[UploadFile] = File(...),
    session_id: Optional[str] = Form(None),
    x_session_id: Optional[str] = Header(None)
):
    """
    رفع ومعالجة حزمة ملفات ومقاطع صوت وفيديو متعددة في وقت واحد (Multi-File Ingestion)
    مع التحقق من التنسيقات والحد الإجمالي (50MB) والتجزئة في الذاكرة
    """
    session = get_current_session(session_id, x_session_id)
    
    if not files:
        raise HTTPException(status_code=400, detail="لم يتم إرسال أي ملفات للرفع.")

    uploaded_results = []
    errors = []

    for file in files:
        filename = file.filename or "unknown_file"
        
        # فحص التنسيق
        if not DocumentParser.is_supported(filename):
            errors.append({
                "filename": filename,
                "error": f"امتداد غير مدعوم. الامتدادات المدعومة تشمل: مستندات (PDF, Word, PPTX, Excel, CSV, TXT) وصوتيات وفيديوهات (MP3, WAV, MP4, WebM)"
            })
            continue

        try:
            content = await file.read()
            if len(content) == 0:
                errors.append({
                    "filename": filename,
                    "error": "الملف فارغ (0 بايت)"
                })
                continue

            file_info = session.add_file(filename, content)
            uploaded_results.append({
                "file_id": file_info.file_id,
                "filename": file_info.filename,
                "size_formatted": file_info.size_formatted,
                "sections_count": file_info.sections_count,
                "chunks_count": file_info.chunks_count
            })

        except ValueError as ve:
            errors.append({
                "filename": filename,
                "error": str(ve)
            })
        except Exception as e:
            errors.append({
                "filename": filename,
                "error": f"فشل استخراج النصوص: {str(e)}"
            })

    return {
        "session_id": session.session_id,
        "uploaded_count": len(uploaded_results),
        "uploaded_files": uploaded_results,
        "errors": errors,
        "total_files": len(session.files),
        "total_size_mb": round(session.total_size_mb, 2),
        "total_chunks": len(session.rag_engine.chunks)
    }


@app.delete("/api/files/{file_id}")
async def delete_file(
    file_id: str,
    session_id: Optional[str] = None,
    x_session_id: Optional[str] = Header(None)
):
    """حذف ملف فردي من الجلسة وفهرس الذاكرة"""
    session = get_current_session(session_id, x_session_id)
    removed_name = session.remove_file(file_id)

    if not removed_name:
        raise HTTPException(status_code=404, detail="الملف غير موجود في هذه الجلسة.")

    return {
        "session_id": session.session_id,
        "message": f"تم حذف الملف '{removed_name}' بنجاح",
        "remaining_files": len(session.files),
        "total_size_mb": round(session.total_size_mb, 2),
        "total_chunks": len(session.rag_engine.chunks)
    }


@app.post("/api/chat")
async def chat_endpoint(
    payload: ChatRequest,
    x_session_id: Optional[str] = Header(None)
):
    """
    نقطة النهاية للمحادثة المقيدة (Strict RAG Chatbot)
    تبحث عن المقاطع الأكثر صلة وتمررها مع التوجيه الصارم إلى OpenRouter
    """
    session = get_current_session(payload.session_id, x_session_id)
    query = payload.query.strip()

    if not query:
        raise HTTPException(status_code=400, detail="لا يمكن إرسال سؤال فارغ.")

    if not session.files:
        return {
            "session_id": session.session_id,
            "answer": "عذراً، لم تقم برفع أي ملفات دراسية أو تسجيلات بعد. يرجى رفع ملفاتك أولاً لطرح الأسئلة حولها.",
            "citations": [],
            "is_rejected": True
        }

    # البحث في الذاكرة عن المقاطع الأكثر صلة بالسؤال
    context, citations = session.rag_engine.build_context(query, top_k=4)

    # استدعاء OpenRouter
    result = await openrouter_client.generate_chat_response(
        query=query,
        context=context,
        chat_history=session.chat_history
    )

    answer = result.get("answer", "")
    is_rejected = result.get("is_rejected", False)

    # حفظ جزء من المحادثة في الجلسة المؤقتة
    session.chat_history.append({"role": "user", "content": query})
    session.chat_history.append({"role": "assistant", "content": answer})
    session.touch()

    return {
        "session_id": session.session_id,
        "answer": answer,
        "citations": citations if not is_rejected else [],
        "is_rejected": is_rejected,
        "error": result.get("error")
    }


@app.post("/api/summarize")
async def summarize_endpoint(
    payload: SummarizeRequest,
    x_session_id: Optional[str] = Header(None)
):
    """
    توليد ملخص أكاديمي لأهم النقاط بنقرة واحدة (Smart Summary)
    """
    session = get_current_session(payload.session_id, x_session_id)

    if not session.files:
        raise HTTPException(status_code=400, detail="يرجى رفع ملف أو تسجيل واحد على الأقل لتوليد الملخص.")

    all_content = session.rag_engine.get_all_content_for_summary()
    result = await openrouter_client.generate_summary(all_content)

    return {
        "session_id": session.session_id,
        "summary": result.get("summary", ""),
        "error": result.get("error")
    }


@app.post("/api/quiz/generate")
async def generate_quiz_endpoint(
    payload: QuizRequest,
    x_session_id: Optional[str] = Header(None)
):
    """
    توليد اختبار تجريبي تفاعلي (Interactive Quiz) من محتوى الملفات المرفوعة
    """
    session = get_current_session(payload.session_id, x_session_id)

    if not session.files:
        raise HTTPException(status_code=400, detail="يرجى رفع ملفات دراسية أولاً لتوليد الاختبار التقييمي.")

    all_content = session.rag_engine.get_all_content_for_summary()
    result = await openrouter_client.generate_quiz(
        all_content=all_content,
        num_questions=payload.num_questions,
        quiz_type=payload.quiz_type
    )

    return {
        "session_id": session.session_id,
        "questions": result.get("questions", []),
        "total": result.get("total", 0),
        "error": result.get("error"),
        "message": result.get("message")
    }


@app.post("/api/session/clear")
async def clear_session_endpoint(
    payload: ClearSessionRequest,
    x_session_id: Optional[str] = Header(None)
):
    """مسح الجلسة وكافة الملفات والنصوص من الذاكرة بالكامل"""
    session = get_current_session(payload.session_id, x_session_id)
    session.clear()

    return {
        "session_id": session.session_id,
        "message": "تم مسح كافة البيانات والجلسة من الذاكرة بنجاح.",
        "files_count": 0,
        "total_size_mb": 0
    }


# -------------------------------------------------------------
# تشغيل الخادم
# -------------------------------------------------------------
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("main:app", host=HOST, port=PORT, reload=True)
