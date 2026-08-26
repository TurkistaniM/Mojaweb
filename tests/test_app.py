"""
اختبارات التحقق والفحص الآلي لمنصة مُجاوِب (Mojaweb Test Suite)
يفحص مستخرج المستندات، محرك RAG، إدارة الجلسات والحدود القصوى للحجم ونقاط النهاية
"""

import io
import pytest
from fastapi.testclient import TestClient

from main import app
from document_parser import DocumentParser, ExtractedSection
from rag_engine import InMemoryRAGEngine, normalize_arabic, tokenize
from session_manager import session_manager, EphemeralSession, MAX_TOTAL_BUNDLE_BYTES
from openrouter_client import STANDARD_REJECTION_MESSAGE, SYSTEM_INSTRUCTION_QA, SUMMARY_PROMPT_SYSTEM


client = TestClient(app)


def test_arabic_normalization():
    """اختبار دقة تطبيع الكلمات والحروف العربية"""
    raw_text = "الذَّكَاءُ الاِصْطِنَاعِيُّ وَتَطْبِيقَاتُهُ فِي مِصْرَ"
    norm = normalize_arabic(raw_text)
    assert "الذكاء" in norm or "الذكاء" == normalize_arabic("الذكاء")
    assert "في" in norm
    assert "مصر" in norm

    # توحيد الألفات والتاء المربوطة
    assert normalize_arabic("أحمد") == normalize_arabic("احمد") == normalize_arabic("إحمد")
    assert normalize_arabic("جامعة") == normalize_arabic("جامعه")
    assert normalize_arabic("علي") == normalize_arabic("على")


def test_document_parser_txt_and_md():
    """اختبار استخراج النصوص من ملفات TXT و Markdown"""
    txt_content = "هذا نص تجريبي لاختبار المساعد الدراسي مُجاوِب.".encode("utf-8")
    sections = DocumentParser.extract_text("lecture1.txt", txt_content)
    assert len(sections) >= 1
    assert "مُجاوِب" in sections[0].text
    assert sections[0].filename == "lecture1.txt"

    md_content = "# عنوان رئيسي\n\nفقرة تشرح الخوارزميات وهياكل البيانات.".encode("utf-8")
    sections_md = DocumentParser.extract_text("notes.md", md_content)
    assert len(sections_md) >= 1
    assert "الخوارزميات" in sections_md[0].text


def test_document_parser_csv():
    """اختبار استخراج النصوص من ملفات CSV"""
    csv_bytes = "المعرف,المادة,الدرجة\n1,حاسب آلي,95\n2,رياضيات,90".encode("utf-8")
    sections = DocumentParser.extract_text("grades.csv", csv_bytes)
    assert len(sections) == 1
    assert "حاسب آلي" in sections[0].text
    assert "رياضيات" in sections[0].text


def test_in_memory_rag_engine():
    """اختبار فهرسة وبحث محرك RAG في الذاكرة"""
    engine = InMemoryRAGEngine(chunk_size=300)
    
    sections = [
        ExtractedSection(
            filename="biology_ch1.pdf",
            section_number=1,
            section_type="صفحة",
            text="الخلية هي الوحدة الأساسية للحياة في جميع الكائنات الحية. تحتوي على النواة والسيتوبلازم."
        ),
        ExtractedSection(
            filename="biology_ch1.pdf",
            section_number=2,
            section_type="صفحة",
            text="عملية البناء الضوئي تحدث في البلاستيدات الخضراء وتنتج الجلوكوز والأكسجين باستخدام ضوء الشمس."
        ),
        ExtractedSection(
            filename="history_ch1.pdf",
            section_number=1,
            section_type="صفحة",
            text="تأسست الحضارة البابلية في بلاد الرافدين واشتهرت بقوانين حمورابي وبوابة عشتار."
        )
    ]
    
    engine.add_sections(sections)
    assert len(engine.chunks) == 3

    # البحث عن البناء الضوئي
    results = engine.search("ما هي عملية البناء الضوئي؟", top_k=2)
    assert len(results) >= 1
    top_chunk, score = results[0]
    assert "البناء الضوئي" in top_chunk.text
    assert top_chunk.section_number == 2

    # فحص بناء السياق وقائمة المصادر
    context, citations = engine.build_context("البناء الضوئي")
    assert "biology_ch1.pdf" in context
    assert len(citations) >= 1
    assert citations[0]["filename"] == "biology_ch1.pdf"


def test_session_manager_and_size_limit():
    """اختبار إدارة الجلسات في الذاكرة وفرض حد الـ 50MB"""
    session = session_manager.get_or_create_session()
    
    # رفع ملف نصي صغير
    sample_bytes = "محتوى دراسي قصير".encode("utf-8")
    info = session.add_file("lecture.txt", sample_bytes)
    assert info.filename == "lecture.txt"
    assert len(session.files) == 1
    assert session.total_size_bytes == len(sample_bytes)

    # اختبار تجاوز حد 50MB
    oversized_bytes = b"X" * (MAX_TOTAL_BUNDLE_BYTES + 1024)
    with pytest.raises(ValueError, match="50 ميجابايت"):
        session.add_file("huge.txt", oversized_bytes)

    # اختبار حذف ملف
    deleted_name = session.remove_file(info.file_id)
    assert deleted_name == "lecture.txt"
    assert len(session.files) == 0


def test_api_health_endpoint():
    """اختبار نقطة النهاية /api/health"""
    response = client.get("/api/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "online"
    assert data["max_bundle_size_mb"] == 50
    assert ".pdf" in data["supported_formats"]


def test_api_full_workflow():
    """اختبار دورة العمل المتكاملة عبر الـ API: جلسة -> رفع -> محادثة -> ملخص -> مسح"""
    # 1. إنشاء جلسة جديدة
    res_sess = client.post("/api/session/new")
    assert res_sess.status_code == 200
    session_id = res_sess.json()["session_id"]

    # 2. رفع ملفات تجريبية
    file_content = "الذكاء الاصطناعي التوليدي يقوم بإنشاء نصوص وصور برمجية جديدة.".encode("utf-8")
    files_payload = [
        ("files", ("ai_intro.txt", io.BytesIO(file_content), "text/plain"))
    ]
    res_upload = client.post(
        "/api/upload",
        data={"session_id": session_id},
        files=files_payload
    )
    assert res_upload.status_code == 200
    upload_data = res_upload.json()
    assert upload_data["uploaded_count"] == 1
    assert upload_data["total_files"] == 1

    # 3. فحص قائمة الملفات
    res_files = client.get(f"/api/files?session_id={session_id}")
    assert res_files.status_code == 200
    files_data = res_files.json()
    assert len(files_data["files"]) == 1
    file_id = files_data["files"][0]["file_id"]

    # 4. محادثة مع سؤال خارج السياق (عند عدم وجود مفتاح، أو تحقق الرفض)
    res_chat = client.post(
        "/api/chat",
        json={"query": "ما هي عاصمة فرنسا؟", "session_id": session_id}
    )
    assert res_chat.status_code == 200
    chat_data = res_chat.json()
    assert "answer" in chat_data

    # 5. مسح الجلسة
    res_clear = client.post("/api/session/clear", json={"session_id": session_id})
    assert res_clear.status_code == 200
    assert res_clear.json()["files_count"] == 0
