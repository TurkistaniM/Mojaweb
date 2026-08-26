"""
إدارة الجلسات المؤقتة في الذاكرة (Ephemeral Session Manager)
تخزين غير دائم للبيانات لضمان الخصوصية والتوافق التام مع طبيعة Render المؤقتة
فحص ومراقبة حد الـ 50MB لحزمة الملفات، ومسح الجلسات عند الطلب
"""

import time
import uuid
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, field
from rag_engine import InMemoryRAGEngine
from document_parser import DocumentParser, ExtractedSection


MAX_TOTAL_BUNDLE_BYTES = 50 * 1024 * 1024  # 50 ميجابايت كحد أقصى للحزمة
SESSION_TTL_SECONDS = 7200  # صلاحية الجلسة ساعتان بعد آخر نشاط


@dataclass
class UploadedFileInfo:
    file_id: str
    filename: str
    size_bytes: int
    sections_count: int
    chunks_count: int
    uploaded_at: float = field(default_factory=time.time)

    @property
    def size_formatted(self) -> str:
        if self.size_bytes < 1024:
            return f"{self.size_bytes} B"
        elif self.size_bytes < 1024 * 1024:
            return f"{self.size_bytes / 1024:.1f} KB"
        else:
            return f"{self.size_bytes / (1024 * 1024):.2f} MB"


class EphemeralSession:
    """كائن الجلسة الواحدة المحفوظة في الذاكرة السريعة"""

    def __init__(self, session_id: str):
        self.session_id = session_id
        self.created_at = time.time()
        self.last_active_at = time.time()
        self.files: Dict[str, UploadedFileInfo] = {}
        self.rag_engine = InMemoryRAGEngine()
        self.chat_history: List[Dict[str, str]] = []

    def touch(self) -> None:
        self.last_active_at = time.time()

    @property
    def total_size_bytes(self) -> int:
        return sum(f.size_bytes for f in self.files.values())

    @property
    def total_size_mb(self) -> float:
        return self.total_size_bytes / (1024 * 1024)

    def add_file(self, filename: str, file_bytes: bytes) -> UploadedFileInfo:
        """معالجة ملف واستخراج نصوصه وتخزينه في الجلسة"""
        self.touch()
        file_size = len(file_bytes)

        if self.total_size_bytes + file_size > MAX_TOTAL_BUNDLE_BYTES:
            raise ValueError(
                f"حجم الملفات الإجمالي يتجاوز الحد المسموح (50 ميجابايت). "
                f"الحجم الحالي: {self.total_size_mb:.1f}MB، الملف الإضافي: {file_size / (1024*1024):.1f}MB"
            )

        # استخراج النصوص
        sections = DocumentParser.extract_text(filename, file_bytes)
        
        # إضافة المقاطع إلى محرك RAG
        initial_chunk_count = len(self.rag_engine.chunks)
        self.rag_engine.add_sections(sections)
        new_chunks = len(self.rag_engine.chunks) - initial_chunk_count

        file_id = str(uuid.uuid4())[:8]
        file_info = UploadedFileInfo(
            file_id=file_id,
            filename=filename,
            size_bytes=file_size,
            sections_count=len(sections),
            chunks_count=new_chunks
        )
        self.files[file_id] = file_info
        return file_info

    def remove_file(self, file_id: str) -> Optional[str]:
        """حذف ملف فردي من الجلسة ومن فهرس الذاكرة"""
        self.touch()
        if file_id in self.files:
            file_info = self.files.pop(file_id)
            self.rag_engine.remove_file(file_info.filename)
            return file_info.filename
        return None

    def clear(self) -> None:
        """مسح كامل بيانات الجلسة"""
        self.files.clear()
        self.rag_engine.clear()
        self.chat_history.clear()
        self.touch()


class SessionManager:
    """مدير الجلسات العام للتحكم بالجلسات المؤقتة في الذاكرة"""

    def __init__(self):
        self._sessions: Dict[str, EphemeralSession] = {}

    def get_or_create_session(self, session_id: Optional[str] = None) -> EphemeralSession:
        """جلب الجلسة الحالية أو إنشاء جلسة جديدة تماماً"""
        self._cleanup_expired_sessions()
        
        if not session_id or session_id not in self._sessions:
            new_id = str(uuid.uuid4())
            session = EphemeralSession(new_id)
            self._sessions[new_id] = session
            return session

        session = self._sessions[session_id]
        session.touch()
        return session

    def reset_session(self, session_id: str) -> EphemeralSession:
        """إعادة تعيين ومسح الجلسة أو إنشاء واحدة بديلة"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            return self._sessions[session_id]
        return self.get_or_create_session(session_id)

    def delete_session(self, session_id: str) -> bool:
        """حذف الجلسة بالكامل من الذاكرة"""
        if session_id in self._sessions:
            self._sessions[session_id].clear()
            del self._sessions[session_id]
            return True
        return False

    def _cleanup_expired_sessions(self) -> None:
        """تنظيف دوري للجلسات الخاملة لتفادي تراكم استهلاك الذاكرة على Render"""
        now = time.time()
        expired_ids = [
            sid for sid, s in self._sessions.items()
            if now - s.last_active_at > SESSION_TTL_SECONDS
        ]
        for sid in expired_ids:
            self._sessions[sid].clear()
            del self._sessions[sid]


# كائن مدير الجلسات المركزي
session_manager = SessionManager()
