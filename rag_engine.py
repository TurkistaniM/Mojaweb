"""
محرك RAG دلالي ومعجمي في الذاكرة (In-Memory RAG Engine)
يعمل بالكامل داخل الذاكرة المؤقتة (Ephemeral In-Memory)
يدعم تطبيع اللغة العربية وتجزئة النصوص والبحث الدقيق BM25/TF-IDF
"""

import re
import math
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, field
from document_parser import ExtractedSection


@dataclass
class TextChunk:
    chunk_id: str
    filename: str
    section_number: int
    section_type: str
    source_label: str
    text: str
    tokens: List[str] = field(default_factory=list)


def normalize_arabic(text: str) -> str:
    """
    تطبيع النصوص العربية لتوحيد أشكال الحروف وإزالة التشكيل والتطويل
    لضمان أفضل دقة في البحث واسترجاع المعلومات
    """
    if not text:
        return ""
    
    text = text.lower()
    
    # إزالة التشكيل (الحركات)
    text = re.sub(r'[\u064B-\u0652\u0670\u0640]', '', text)
    
    # توحيد الألفات
    text = re.sub(r'[إأآا]', 'ا', text)
    
    # توحيد التاء المربوطة والهاء
    text = re.sub(r'ة', 'ه', text)
    
    # توحيد الياء والألف المقصورة
    text = re.sub(r'[ىي]', 'ي', text)
    
    # توحيد الواو المهموزة
    text = re.sub(r'ؤ', 'و', text)
    
    # توحيد الهمزة على نبرة
    text = re.sub(r'ئ', 'ي', text)
    
    return text


def tokenize(text: str) -> List[str]:
    """تقسيم النص إلى رموز وكلمات مطبعة مع دعم العربية والإنجليزية والأرقام"""
    normalized = normalize_arabic(text)
    # استخراج الكلمات والرموز الأبجدية الرقمية
    tokens = re.findall(r'[\w\d]+', normalized, re.UNICODE)
    # استبعاد الكلمات ذات الحرف الواحد إذا لم تكن رقماً
    return [t for t in tokens if len(t) > 1 or t.isdigit()]


class InMemoryRAGEngine:
    """
    محرك بحث واسترجاع فوري داخل الذاكرة
    يعتمد على خوارزمية BM25 المعززة بالبحث المطابق للعبارات (Phrase & N-Gram Matching)
    """

    def __init__(self, chunk_size: int = 750, chunk_overlap: int = 150):
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.chunks: List[TextChunk] = []
        
        # إحصائيات BM25
        self.doc_lengths: List[int] = []
        self.avg_doc_len: float = 0.0
        self.doc_freqs: Dict[str, int] = {}
        self.total_docs: int = 0
        self.k1: float = 1.5
        self.b: float = 0.75

    def add_sections(self, sections: List[ExtractedSection]) -> None:
        """تجزئة المقاطع وإضافتها لفهرس الذاكرة"""
        for sec in sections:
            self._chunk_section(sec)
        self._rebuild_index()

    def remove_file(self, filename: str) -> None:
        """حذف ملف من فهرس الذاكرة وإعادة بناء الفهرس"""
        self.chunks = [c for c in self.chunks if c.filename != filename]
        self._rebuild_index()

    def clear(self) -> None:
        """مسح كامل الفهرس من الذاكرة"""
        self.chunks = []
        self.doc_lengths = []
        self.avg_doc_len = 0.0
        self.doc_freqs = {}
        self.total_docs = 0

    def _chunk_section(self, section: ExtractedSection) -> None:
        """تقسيم المقطع الواحد إلى أجزاء صغيرة مترابطة"""
        text = section.text.strip()
        if not text:
            return

        if len(text) <= self.chunk_size:
            chunk = TextChunk(
                chunk_id=f"{section.filename}_{section.section_number}_{len(self.chunks)}",
                filename=section.filename,
                section_number=section.section_number,
                section_type=section.section_type,
                source_label=section.source_label,
                text=text,
                tokens=tokenize(text)
            )
            self.chunks.append(chunk)
            return

        # تقسيم على فواصل الفقرات أو الأسطر
        paragraphs = text.split("\n")
        current_text = ""
        chunk_sub_id = 0

        for para in paragraphs:
            para = para.strip()
            if not para:
                continue

            if len(current_text) + len(para) <= self.chunk_size:
                current_text += ("\n" if current_text else "") + para
            else:
                if current_text:
                    chunk = TextChunk(
                        chunk_id=f"{section.filename}_{section.section_number}_{chunk_sub_id}",
                        filename=section.filename,
                        section_number=section.section_number,
                        section_type=section.section_type,
                        source_label=section.source_label,
                        text=current_text,
                        tokens=tokenize(current_text)
                    )
                    self.chunks.append(chunk)
                    chunk_sub_id += 1
                    
                    # استبقاء جزء من التداخل
                    words = current_text.split()
                    overlap_words = words[-max(1, len(words) // 5):]
                    current_text = " ".join(overlap_words) + "\n" + para
                else:
                    # في حال كانت الفقرة الواحدة أطول من حجم المقطع
                    for i in range(0, len(para), self.chunk_size - self.chunk_overlap):
                        sub_str = para[i:i + self.chunk_size]
                        chunk = TextChunk(
                            chunk_id=f"{section.filename}_{section.section_number}_{chunk_sub_id}",
                            filename=section.filename,
                            section_number=section.section_number,
                            section_type=section.section_type,
                            source_label=section.source_label,
                            text=sub_str,
                            tokens=tokenize(sub_str)
                        )
                        self.chunks.append(chunk)
                        chunk_sub_id += 1
                    current_text = ""

        if current_text:
            chunk = TextChunk(
                chunk_id=f"{section.filename}_{section.section_number}_{chunk_sub_id}",
                filename=section.filename,
                section_number=section.section_number,
                section_type=section.section_type,
                source_label=section.source_label,
                text=current_text,
                tokens=tokenize(current_text)
            )
            self.chunks.append(chunk)

    def _rebuild_index(self) -> None:
        """إعادة بناء فهرس BM25 وإحصائيات تكرار الكلمات"""
        self.total_docs = len(self.chunks)
        if self.total_docs == 0:
            self.doc_lengths = []
            self.avg_doc_len = 0.0
            self.doc_freqs = {}
            return

        self.doc_lengths = [len(c.tokens) for c in self.chunks]
        self.avg_doc_len = sum(self.doc_lengths) / max(1, self.total_docs)
        self.doc_freqs = {}

        for chunk in self.chunks:
            seen_tokens = set(chunk.tokens)
            for token in seen_tokens:
                self.doc_freqs[token] = self.doc_freqs.get(token, 0) + 1

    def search(self, query: str, top_k: int = 4) -> List[Tuple[TextChunk, float]]:
        """
        البحث عن المقاطع الأكثر ملاءمة للسؤال باستخدام BM25 + مطابقة العبارات
        """
        if not self.chunks or not query.strip():
            return []

        query_tokens = tokenize(query)
        if not query_tokens:
            return []

        normalized_query = normalize_arabic(query)
        scores: List[float] = [0.0] * len(self.chunks)

        for i, chunk in enumerate(self.chunks):
            doc_len = self.doc_lengths[i]
            token_counts: Dict[str, int] = {}
            for t in chunk.tokens:
                token_counts[t] = token_counts.get(t, 0) + 1

            chunk_score = 0.0
            for qt in query_tokens:
                if qt not in token_counts:
                    continue

                freq = token_counts[qt]
                df = self.doc_freqs.get(qt, 0)
                
                # حساب IDF مع التنعيم
                idf = math.log(1 + (self.total_docs - df + 0.5) / (df + 0.5))
                
                # حساب وزن التكرار
                numerator = freq * (self.k1 + 1)
                denominator = freq + self.k1 * (1 - self.b + self.b * (doc_len / max(1.0, self.avg_doc_len)))
                chunk_score += idf * (numerator / denominator)

            # تعزيز إضافي في حال وجود تطابق لعبارة كاملة أو تسلسل كلمات
            normalized_chunk_text = normalize_arabic(chunk.text)
            if normalized_query in normalized_chunk_text:
                chunk_score += 5.0
            else:
                # فحص تطابق الكلمات المتجاورة (Bigrams)
                if len(query_tokens) >= 2:
                    for j in range(len(query_tokens) - 1):
                        bi = f"{query_tokens[j]} {query_tokens[j+1]}"
                        if bi in normalized_chunk_text:
                            chunk_score += 1.5

            scores[i] = chunk_score

        # ترتيب النتائج واستخراج أفضل k مقاطع
        ranked_indices = sorted(range(len(scores)), key=lambda idx: scores[idx], reverse=True)
        results = []
        for idx in ranked_indices[:top_k]:
            if scores[idx] > 0.05:  # حد أدنى للأهمية
                results.append((self.chunks[idx], scores[idx]))

        return results

    def build_context(self, query: str, top_k: int = 4) -> Tuple[str, List[Dict[str, Any]]]:
        """
        بناء السياق المنسق المرفق مع السؤال للنموذج وقائمة المصادر المستشهد بها
        """
        search_results = self.search(query, top_k=top_k)
        if not search_results:
            return "", []

        context_parts = []
        citations = []

        for chunk, score in search_results:
            context_parts.append(
                f"--- [المصدر: {chunk.source_label}] ---\n{chunk.text.strip()}\n"
            )
            citations.append({
                "filename": chunk.filename,
                "section_number": chunk.section_number,
                "section_type": chunk.section_type,
                "source_label": chunk.source_label,
                "score": round(score, 3),
                "snippet": chunk.text[:150] + ("..." if len(chunk.text) > 150 else "")
            })

        return "\n".join(context_parts), citations

    def get_all_content_for_summary(self, max_chars: int = 35000) -> str:
        """
        استخراج محتوى شامل ومنظم من جميع الملفات المرفوعة لاستخدامه في التلخيص
        """
        if not self.chunks:
            return ""

        file_grouped: Dict[str, List[str]] = {}
        for chunk in self.chunks:
            if chunk.filename not in file_grouped:
                file_grouped[chunk.filename] = []
            file_grouped[chunk.filename].append(
                f"[{chunk.source_label}]\n{chunk.text}"
            )

        summary_text_parts = []
        total_len = 0

        for filename, parts in file_grouped.items():
            header = f"=== ملف: {filename} ===\n"
            content = "\n\n".join(parts)
            part_str = header + content + "\n\n"
            
            if total_len + len(part_str) > max_chars:
                allowed = max(0, max_chars - total_len - len(header))
                summary_text_parts.append(header + content[:allowed] + "\n...[تم اقتطاع باقي المحتوى لتجاوز الحد الأقصى]")
                break
            else:
                summary_text_parts.append(part_str)
                total_len += len(part_str)

        return "".join(summary_text_parts)
