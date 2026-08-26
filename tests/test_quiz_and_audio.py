"""
اختبارات ميزات الصوت والفيديو والاختبارات التفاعلية (Quiz & Media Tests)
"""

import io
import pytest
from fastapi.testclient import TestClient

from main import app
from document_parser import DocumentParser

client = TestClient(app)


def test_supported_audio_and_video_formats():
    """التحقق من دعم امتدادات الصوت والفيديو"""
    for ext in ["lecture.mp3", "notes.wav", "recording.m4a", "lesson.mp4", "video.webm"]:
        assert DocumentParser.is_supported(ext) is True
        assert DocumentParser.is_audio_or_video(ext) is True


def test_quiz_endpoint_validation():
    """التحقق من استجابة نقطة نهاية توليد الاختبارات عند عدم وجود ملفات"""
    res = client.post("/api/quiz/generate", json={"num_questions": 5, "quiz_type": "all"})
    assert res.status_code == 400


def test_quiz_endpoint_with_uploaded_file():
    """التحقق من دورة العمل لرفع ملف وطلب إنشاء كويز"""
    # إنشاء جلسة
    res_sess = client.post("/api/session/new")
    session_id = res_sess.json()["session_id"]

    # رفع محتوى
    content = "تقنية التعلم العميق (Deep Learning) هي جزء من الذكاء الاصطناعي يعتمد على الشبكات العصبية الاصطناعية متعددة الطبقات.".encode("utf-8")
    files_payload = [
        ("files", ("deep_learning.txt", io.BytesIO(content), "text/plain"))
    ]
    res_upload = client.post(
        "/api/upload",
        data={"session_id": session_id},
        files=files_payload
    )
    assert res_upload.status_code == 200

    # طلب توليد كويز
    res_quiz = client.post(
        "/api/quiz/generate",
        json={"session_id": session_id, "num_questions": 3, "quiz_type": "mcq"}
    )
    assert res_quiz.status_code == 200
    data = res_quiz.json()
    assert "questions" in data
