"""
عميل التواصل مع OpenRouter API (OpenRouter Client)
مزود بنظام التبديل التلقائي للنماذج البديلة (Auto-Fallback) لتفادي أخطاء 429 Rate Limit
"""

import os
import json
import re
import httpx
import logging
from typing import List, Dict, Any, Optional

logger = logging.getLogger("openrouter_client")

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"
DEFAULT_MODEL = "google/gemma-4-26b-a4b-it:free"

# قائمة النماذج المجانية عالية الكفاءة للتبديل التلقائي عند انشغال النموذج الأساسي
FALLBACK_FREE_MODELS = [
    "google/gemma-4-26b-a4b-it:free",
    "meta-llama/llama-3.3-70b-instruct:free",
    "deepseek/deepseek-chat:free",
    "google/gemini-2.0-flash-exp:free",
    "qwen/qwen-2.5-72b-instruct:free",
    "mistralai/mistral-small-24b-instruct-2501:free",
    "microsoft/phi-3-medium-128k-instruct:free",
    "google/gemma-2-9b-it:free"
]

STANDARD_REJECTION_MESSAGE = "عذراً، هذا السؤال خارج سياق الملفات المرفوعة، ولا يمكنني الإجابة إلا بناءً على محتواها."

SYSTEM_INSTRUCTION_QA = """أنت "مُجاوِب"، مساعد دراسي وأكاديمي وظيفته الحصرية هي الإجابة عن أسئلة المستخدم بالاعتماد فقط وبشكل صارم على سياق الملفات المرفوعة والمقدمة لك أدناه.

القواعد الصارمة التي يجب اتباعها بدقة:
1. لا تستخدم أي معلومات عامة أو معرفة مسبقة خارج هذا السياق إطلاقاً.
2. إذا لم تجد الإجابة مذكورة بوضوح في سياق الملفات، أو إذا كان السؤال عن موضوع خارجي لا علاقة له بها، يجب عليك الرد حرفياً بالعبارة التالية فقط دون أي شرح إضافي:
"عذراً، هذا السؤال خارج سياق الملفات المرفوعة، ولا يمكنني الإجابة إلا بناءً على محتواها."
3. عند الإجابة، اذكر اسم الملف ورقم المقطع/الصفحة لتوثيق المصدر كلما كان ذلك متاحاً.
4. التزم بلغة واضحة، دقيقة، ومهنية."""

SUMMARY_PROMPT_SYSTEM = """قم بتحليل محتوى الملفات المرفقة واستخرج ملخصاً شاملاً ومنظماً لأهم المفاهيم والنقاط الرئيسية بصيغة نقاط مرتبة وعناوين فرعية واضحة، مع الاقتصار التام على ما ورد في الملف دون إضافات خارجية."""

QUIZ_PROMPT_SYSTEM = """أنت خبير اختبارات وتقييم أكاديمي في منصة "مُجاوِب".
وظيفتك توليد اختبار تقييمي تفاعلي عالي الجودة للطلاب استناداً فقط وبشكل صارم إلى محتوى المستندات والملفات المرفقة أدناه.

يجب أن تكون مخرجاتك حصراً مصفوفة JSON صالحة (Valid JSON Array) بدون أي نص تمهيدي أو ختامي خارج كود الـ JSON.

كل عنصر في المصفوفة يمثل سؤالاً ويحتوي الحقول التالية:
- "id": رقم تسلسلي (1, 2, ...)
- "question": نص السؤال بدقة ووضوح
- "type": "mcq" (اختيار من متعدد 4 خيارات) أو "boolean" (صح أو خطأ خياران)
- "options": مصفوفة النصوص للخيارات (مثال: ["الخيار 1", "الخيار 2", "الخيار 3", "الخيار 4"] أو ["صح", "خطأ"])
- "correct_index": رقم المؤشر (0-indexed) للإجابة الصحيحة ضمن مصفوفة options
- "explanation": تعليل وشرح موجز ودقيق لسبب صحة الإجابة استناداً للملف
- "source": اسم الملف ورقم الصفحة أو الشريحة التي وردت فيها المعلومة

التزم التزاماً تاماً بما ورد في المستندات فقط."""


class OpenRouterClient:
    """عميل الاتصال بـ OpenRouter مع التبديل الذكي بين النماذج لتفادي انقطاع الخدمة"""

    def __init__(self):
        self.api_key = os.environ.get("OPENROUTER_API_KEY", "").strip()
        self.primary_model = os.environ.get("OPENROUTER_MODEL", DEFAULT_MODEL).strip()

    def get_api_key(self) -> str:
        return os.environ.get("OPENROUTER_API_KEY", self.api_key).strip()

    def get_candidate_models(self) -> List[str]:
        """تجهيز قائمة النماذج المرشحة مع وضع النموذج المفضل أولاً"""
        primary = os.environ.get("OPENROUTER_MODEL", self.primary_model).strip() or DEFAULT_MODEL
        models = [primary]
        for m in FALLBACK_FREE_MODELS:
            if m not in models:
                models.append(m)
        return models

    def get_model(self) -> str:
        return os.environ.get("OPENROUTER_MODEL", self.primary_model).strip() or DEFAULT_MODEL

    def is_configured(self) -> bool:
        return bool(self.get_api_key())

    async def _execute_with_fallback(
        self,
        messages: List[Dict[str, str]],
        temperature: float = 0.1,
        max_tokens: int = 2048,
        timeout_sec: float = 60.0
    ) -> Dict[str, Any]:
        """
        تنفيذ الطلب مع التبديل التلقائي للنموذج التالي في حال حدوث 429 Rate Limit
        """
        api_key = self.get_api_key()
        if not api_key:
            return {
                "content": "",
                "error": "API_KEY_NOT_CONFIGURED",
                "message": "⚠️ تنبيه: لم يتم ضبط مفتاح `OPENROUTER_API_KEY` في متغيرات البيئة لخادم Backend."
            }

        headers = {
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://render.com",
            "X-Title": "Mojaweb Chatbot",
            "Content-Type": "application/json"
        }

        candidate_models = self.get_candidate_models()
        last_error = ""

        async with httpx.AsyncClient(timeout=timeout_sec) as client:
            for model_name in candidate_models:
                payload = {
                    "model": model_name,
                    "messages": messages,
                    "temperature": temperature,
                    "max_tokens": max_tokens
                }

                try:
                    response = await client.post(OPENROUTER_URL, headers=headers, json=payload)
                    
                    # في حال النجاح
                    if response.status_code == 200:
                        data = response.json()
                        content = data.get("choices", [{}])[0].get("message", {}).get("content", "").strip()
                        return {
                            "content": content,
                            "model_used": model_name,
                            "usage": data.get("usage", {})
                        }

                    # في حال كان الخطأ 429 (معدل الاستخدام مضغوط للنموذج)، ننتقل فوراً للنموذج البديل
                    if response.status_code in (429, 503, 502, 500):
                        last_error = f"Model {model_name} returned status {response.status_code}"
                        continue
                    else:
                        # خطأ آخر (مثل مفتاح غير صالح)
                        err_text = response.text
                        try:
                            err_json = response.json()
                            err_text = err_json.get("error", {}).get("message", err_text)
                        except Exception:
                            pass
                        last_error = f"HTTP {response.status_code}: {err_text}"
                        # إذا كان الخطأ متعلق بالمصادقة (401)، لا داعي لتجربة باقي النماذج
                        if response.status_code == 401:
                            break

                except (httpx.TimeoutException, httpx.NetworkError) as net_err:
                    last_error = f"Network timeout on {model_name}: {str(net_err)}"
                    continue
                except Exception as e:
                    last_error = str(e)
                    continue

        return {
            "content": "",
            "error": "ALL_MODELS_FAILED",
            "message": f"عذراً، تعذر الوصول للنماذج مؤقتاً بسبب ضغط المزود: {last_error}"
        }

    async def generate_chat_response(
        self,
        query: str,
        context: str,
        chat_history: Optional[List[Dict[str, str]]] = None
    ) -> Dict[str, Any]:
        """توليد إجابة على سؤال المستخدم بناءً على السياق المرفوع فقط"""
        if not self.is_configured():
            return {
                "answer": "⚠️ تنبيه: لم يتم ضبط مفتاح `OPENROUTER_API_KEY` في متغيرات البيئة لخادم Backend.",
                "error": "API_KEY_NOT_CONFIGURED"
            }

        if not context.strip():
            return {
                "answer": STANDARD_REJECTION_MESSAGE,
                "is_rejected": True
            }

        user_content = (
            f"سياق الملفات المرفوعة المتاح لك:\n\n"
            f"{context}\n\n"
            f"سؤال المستخدم:\n{query}\n\n"
            f"أجب بناءً على السياق أعلاه فقط واذكر اسم الملف ورقم الصفحة/المقطع كمرجع، "
            f"وإذا لم تجد الإجابة في السياق فالتزم بالرد بعبارة الرفض المحددة فقط."
        )

        messages = [
            {"role": "system", "content": SYSTEM_INSTRUCTION_QA}
        ]

        if chat_history:
            for msg in chat_history[-2:]:
                messages.append({"role": msg["role"], "content": msg["content"]})

        messages.append({"role": "user", "content": user_content})

        result = await self._execute_with_fallback(messages, temperature=0.1, max_tokens=2048, timeout_sec=60.0)

        if result.get("error"):
            return {
                "answer": result.get("message", "حدث خطأ أثناء التواصل مع النموذج."),
                "error": result.get("error")
            }

        answer = result.get("content", "").strip() or STANDARD_REJECTION_MESSAGE
        return {
            "answer": answer,
            "model_used": result.get("model_used"),
            "usage": result.get("usage", {})
        }

    async def generate_summary(self, all_content: str) -> Dict[str, Any]:
        """توليد ملخص أكاديمي لأهم النقاط والمفاهيم الواردة في الملفات"""
        if not self.is_configured():
            return {
                "summary": "⚠️ تنبيه: لم يتم ضبط مفتاح `OPENROUTER_API_KEY` في متغيرات البيئة للخادم.",
                "error": "API_KEY_NOT_CONFIGURED"
            }

        if not all_content.strip():
            return {
                "summary": "لا توجد ملفات مرفوعة أو نصوص متاحة لتلخيصها. يرجى رفع ملف أولاً.",
                "error": "NO_CONTENT"
            }

        messages = [
            {"role": "system", "content": SUMMARY_PROMPT_SYSTEM},
            {"role": "user", "content": f"محتوى المستندات المرفوعة:\n\n{all_content}\n\nيرجى استخراج وتلخيص أهم النقاط والمفاهيم الرئيسية فقط كما ورد في الملفات."}
        ]

        result = await self._execute_with_fallback(messages, temperature=0.1, max_tokens=2500, timeout_sec=90.0)

        if result.get("error"):
            return {
                "summary": result.get("message", "حدث خطأ أثناء توليد الملخص."),
                "error": result.get("error")
            }

        summary_text = result.get("content", "").strip() or "لم يتم استخراج أي نقاط ملخصة."
        return {
            "summary": summary_text,
            "model_used": result.get("model_used"),
            "usage": result.get("usage", {})
        }

    async def generate_quiz(self, all_content: str, num_questions: int = 5, quiz_type: str = "all") -> Dict[str, Any]:
        """توليد اختبار تجريبي تفاعلي (Quiz Generator) بناءً على الملفات المرفوعة"""
        if not self.is_configured():
            return {
                "questions": [],
                "error": "API_KEY_NOT_CONFIGURED",
                "message": "⚠️ لم يتم ضبط مفتاح `OPENROUTER_API_KEY`."
            }

        if not all_content.strip():
            return {
                "questions": [],
                "error": "NO_CONTENT",
                "message": "لا توجد ملفات كافية لتوليد الاختبار."
            }

        type_instructions = "نوع الأسئلة: مزيج من أسئلة اختيار من متعدد (MCQ) وأسئلة صح وخطأ."
        if quiz_type == "mcq":
            type_instructions = "نوع الأسئلة: جميع الأسئلة اختيار من متعدد (MCQ) فقط (4 خيارات لكل سؤال)."
        elif quiz_type == "boolean":
            type_instructions = "نوع الأسئلة: جميع الأسئلة صح أو خطأ فقط (خيارات: ['صح', 'خطأ'])."

        prompt = (
            f"قم بإنشاء اختبار أكاديمي مكون من {num_questions} أسئلة دقيقة استناداً إلى المحتوى التالي فقط:\n\n"
            f"{all_content}\n\n"
            f"{type_instructions}\n"
            f"تأكد من إرجاع مصفوفة JSON نقية فقط تحتوي على الأسئلة والخيارات والمؤشر الصحيح والشرح والمصدر."
        )

        messages = [
            {"role": "system", "content": QUIZ_PROMPT_SYSTEM},
            {"role": "user", "content": prompt}
        ]

        result = await self._execute_with_fallback(messages, temperature=0.2, max_tokens=3000, timeout_sec=90.0)

        if result.get("error"):
            return {
                "questions": [],
                "error": result.get("error"),
                "message": result.get("message", "حدث خطأ أثناء توليد الاختبار.")
            }

        raw_text = result.get("content", "").strip()

        # استخراج مصفوفة الـ JSON
        json_match = re.search(r'\[\s*\{.*\}\s*\]', raw_text, re.DOTALL)
        if json_match:
            clean_json = json_match.group(0)
        else:
            clean_json = raw_text.strip("`").replace("json", "").strip()

        try:
            questions_list = json.loads(clean_json)
            return {
                "questions": questions_list,
                "total": len(questions_list),
                "model_used": result.get("model_used")
            }
        except Exception as e:
            return {
                "questions": [],
                "error": "JSON_PARSE_ERROR",
                "message": f"تعذر استخراج بنية الأسئلة بشكل سليم: {str(e)}"
            }


# كائن عميل OpenRouter العام
openrouter_client = OpenRouterClient()
