/**
 * منصة مُجاوِب (Mojaweb) — منطق الواجهة المتطور مع دعم كامل للغتين العربية والإنجليزية
 */

document.addEventListener("DOMContentLoaded", () => {
  // الحالة العامة
  let currentLanguage = localStorage.getItem("mojaweb_lang") || "ar";
  let currentSessionId = sessionStorage.getItem("mojaweb_session_id") || null;
  let activeFiles = [];
  let isGenerating = false;
  let currentQuiz = [];
  let userAnswers = {};

  // قاموس اللغتين (i18n Dictionary)
  const i18n = {
    ar: {
      appName: "مُجاوِب",
      ragBadge: "RAG مقيد 100%",
      newSession: "جلسة جديدة",
      uploadTitle: "المستندات والوسائط",
      uploadSubtitle: "اسحب الملفات هنا أو تصفح جهازك",
      uploadFormats: "PDF, Word, PPTX, Excel, Text, MP3, WAV, MP4",
      summarizeBtn: "توليد ملخص",
      quizBtn: "إنشاء اختبار",
      activeFilesTitle: "الملفات المرفوعة",
      emptyFilesText: "لم يتم رفع أي ملفات بعد",
      ephemeralNote: "تخزين مؤقت في الذاكرة: تُمسح البيانات تلقائياً عند إنهاء الجلسة",
      tabChat: "المحادثة",
      tabSummary: "الملخص",
      tabQuiz: "الاختبار الذكي",
      strictBadge: "إجابات موثقة بالسياق",
      welcomeTitle: "مرحباً بك في مُجاوِب 🎓",
      welcomeDesc: "مساعدك الدراسي المتقدم للإجابة الدقيقة عن أسئلتك استناداً إلى ملفاتك وتسجيلاتك المرفوعة فقط.",
      prompt1: "ما هي الفكرة والمحاور الأساسية؟",
      prompt2: "اذكر أهم التعريفات والمصطلحات",
      prompt3: "ما هي النتائج والاستنتاجات؟",
      chatPlaceholder: "اسأل عن أي شيء في ملفاتك... (Enter للإرسال)",
      sendBtn: "إرسال",
      summaryTitle: "الملخص الأكاديمي الشامل",
      copyBtn: "نسخ",
      refreshBtn: "تحديث",
      noSummaryYet: "لم يتم توليد ملخص بعد",
      quizTitle: "مولّد الاختبارات والتقييم الذاتي",
      generateNewQuiz: "إنشاء اختبار جديد",
      quizPromptText: "اختر الإعدادات واضغط 'إنشاء اختبار جديد' لبدء التقييم التفاعلي.",
      devCreditPrefix: "تمت برمجة وتطوير هذا البرنامج بالكامل بواسطة:",
      devName: "محمد تركستاني",
      scoreTitle: "نتيجتك في الاختبار",
      submitQuiz: "إنهاء وتسليم الاختبار",
      retakeQuiz: "إعادة المحاولة",
      newQuizBtn: "اختبار جديد",
      correctText: "إجابة صحيحة ✓",
      wrongText: "إجابة خاطئة ✗",
      explanationLabel: "💡 الشرح والتعليل:",
      sourceLabel: "📌 المصدر:",
      generatingAnswer: "مُجاوِب يراجع المحتوى...",
      generatingSummary: "جارٍ قراءة وتلخيص المستندات...",
      generatingQuiz: "جارٍ إنشاء الاختبار التفاعلي...",
      confirmReset: "هل ترغب في إنهاء الجلسة ومسح كافة الملفات والنصوص من الذاكرة؟",
      confirmDelete: "هل أنت متأكد من حذف هذا الملف من الذاكرة؟",
      noFilesWarning: "يرجى رفع ملفات أو تسجيلات أولاً لطرح الأسئلة أو التلخيص.",
      toastUploaded: "تمت معالجة ورفع الملفات بنجاح",
      toastCleared: "تم مسح الجلسة وتفريغ الذاكرة بنجاح",
      toastCopied: "تم النسخ إلى الحافظة",
      toastQuizCreated: "تم إنشاء الاختبار بنجاح!"
    },
    en: {
      appName: "Mojaweb",
      ragBadge: "100% Strict RAG",
      newSession: "New Session",
      uploadTitle: "Documents & Media",
      uploadSubtitle: "Drag & drop files here or browse",
      uploadFormats: "PDF, Word, PPTX, Excel, Text, MP3, WAV, MP4",
      summarizeBtn: "Smart Summary",
      quizBtn: "Create Quiz",
      activeFilesTitle: "Active Files",
      emptyFilesText: "No files uploaded yet",
      ephemeralNote: "In-memory storage: data is automatically cleared when session ends",
      tabChat: "Chat",
      tabSummary: "Summary",
      tabQuiz: "Smart Quiz",
      strictBadge: "Context-bound answers",
      welcomeTitle: "Welcome to Mojaweb 🎓",
      welcomeDesc: "Your advanced study assistant for precise, source-cited answers strictly based on your uploaded files.",
      prompt1: "What are the main concepts and topics?",
      prompt2: "List the key definitions and terms",
      prompt3: "What are the conclusions and findings?",
      chatPlaceholder: "Ask anything about your files... (Enter to send)",
      sendBtn: "Send",
      summaryTitle: "Comprehensive Academic Summary",
      copyBtn: "Copy",
      refreshBtn: "Refresh",
      noSummaryYet: "No summary generated yet",
      quizTitle: "Self-Assessment & Quiz Generator",
      generateNewQuiz: "Generate New Quiz",
      quizPromptText: "Configure settings and click 'Generate New Quiz' to begin interactive testing.",
      devCreditPrefix: "Designed & Developed by:",
      devName: "Mohammed Turkistani",
      scoreTitle: "Your Quiz Score",
      submitQuiz: "Submit Quiz",
      retakeQuiz: "Retake Quiz",
      newQuizBtn: "New Quiz",
      correctText: "Correct Answer ✓",
      wrongText: "Incorrect Answer ✗",
      explanationLabel: "💡 Explanation:",
      sourceLabel: "📌 Source:",
      generatingAnswer: "Mojaweb is reviewing content...",
      generatingSummary: "Generating academic summary...",
      generatingQuiz: "Creating interactive quiz...",
      confirmReset: "Are you sure you want to end this session and wipe memory?",
      confirmDelete: "Are you sure you want to delete this file?",
      noFilesWarning: "Please upload documents or recordings first.",
      toastUploaded: "Files processed and indexed successfully",
      toastCleared: "Session and memory cleared successfully",
      toastCopied: "Copied to clipboard",
      toastQuizCreated: "Interactive quiz generated successfully!"
    }
  };

  // عناصر واجهة المستخدم
  const htmlRoot = document.getElementById("html-root");
  const btnLangToggle = document.getElementById("btn-lang-toggle");
  const langLabel = document.getElementById("lang-label");

  const dropZone = document.getElementById("drop-zone");
  const fileInput = document.getElementById("file-input");
  const filesListContainer = document.getElementById("files-list-container");
  const activeFilesCount = document.getElementById("active-files-count");
  const storageUsageText = document.getElementById("storage-usage-text");
  const storageProgressBar = document.getElementById("storage-progress-bar");
  const btnResetSession = document.getElementById("btn-reset-session");
  const btnSmartSummary = document.getElementById("btn-smart-summary");
  const btnOpenQuizTab = document.getElementById("btn-open-quiz-tab");

  const tabChatBtn = document.getElementById("tab-chat-btn");
  const tabSummaryBtn = document.getElementById("tab-summary-btn");
  const tabQuizBtn = document.getElementById("tab-quiz-btn");

  const chatViewPanel = document.getElementById("chat-view-panel");
  const summaryViewPanel = document.getElementById("summary-view-panel");
  const quizViewPanel = document.getElementById("quiz-view-panel");

  const chatMessages = document.getElementById("chat-messages");
  const chatForm = document.getElementById("chat-form");
  const chatInput = document.getElementById("chat-input");
  const sendBtn = document.getElementById("send-btn");
  const quickPromptBtns = document.querySelectorAll(".quick-prompt-btn");

  const summaryContentArea = document.getElementById("summary-content-area");
  const btnCopySummary = document.getElementById("btn-copy-summary");
  const btnRefreshSummary = document.getElementById("btn-refresh-summary");

  const quizContentArea = document.getElementById("quiz-content-area");
  const btnGenerateQuiz = document.getElementById("btn-generate-quiz");
  const quizCountSelect = document.getElementById("quiz-count-select");
  const quizTypeSelect = document.getElementById("quiz-type-select");
  const toast = document.getElementById("toast");

  // -------------------------------------------------------------
  // تبديل اللغة (Language Switcher)
  // -------------------------------------------------------------
  function setLanguage(lang) {
    currentLanguage = lang;
    localStorage.setItem("mojaweb_lang", lang);

    if (lang === "ar") {
      htmlRoot.setAttribute("dir", "rtl");
      htmlRoot.setAttribute("lang", "ar");
      langLabel.textContent = "English";
    } else {
      htmlRoot.setAttribute("dir", "ltr");
      htmlRoot.setAttribute("lang", "en");
      langLabel.textContent = "العربية";
    }

    // تحديث كافة النصوص
    const dict = i18n[lang];
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const key = el.getAttribute("data-i18n");
      if (dict[key]) el.textContent = dict[key];
    });

    document.querySelectorAll("[data-i18n-placeholder]").forEach(el => {
      const key = el.getAttribute("data-i18n-placeholder");
      if (dict[key]) el.setAttribute("placeholder", dict[key]);
    });
  }

  btnLangToggle.addEventListener("click", () => {
    setLanguage(currentLanguage === "ar" ? "en" : "ar");
  });

  // -------------------------------------------------------------
  // تهيئة التطبيق والجلسة
  // -------------------------------------------------------------
  async function initApp() {
    setLanguage(currentLanguage);

    if (!currentSessionId) {
      await createNewSession();
    } else {
      await fetchFilesList();
    }
  }

  async function createNewSession() {
    try {
      const res = await fetch("/api/session/new", { method: "POST" });
      if (res.ok) {
        const data = await res.json();
        currentSessionId = data.session_id;
        sessionStorage.setItem("mojaweb_session_id", currentSessionId);
        await fetchFilesList();
      }
    } catch (err) {
      console.error("Session init failed:", err);
    }
  }

  // -------------------------------------------------------------
  // إدارة قائمة الملفات
  // -------------------------------------------------------------
  async function fetchFilesList() {
    if (!currentSessionId) return;

    try {
      const res = await fetch(`/api/files?session_id=${encodeURIComponent(currentSessionId)}`);
      if (res.ok) {
        const data = await res.json();
        activeFiles = data.files || [];
        renderFilesList(activeFiles);
        updateStorageMeter(data.total_size_mb || 0, data.max_size_mb || 50);
      }
    } catch (err) {
      console.error("Fetch files failed:", err);
    }
  }

  function renderFilesList(files) {
    const t = i18n[currentLanguage];
    if (!files || files.length === 0) {
      filesListContainer.innerHTML = `
        <div id="empty-files-placeholder" class="h-full flex flex-col items-center justify-center text-center p-6 text-[var(--text-muted)]">
          <i class="fa-regular fa-file text-2xl mb-1.5 opacity-40"></i>
          <p class="text-xs">${t.emptyFilesText}</p>
        </div>
      `;
      activeFilesCount.textContent = "0";
      return;
    }

    activeFilesCount.textContent = files.length;
    filesListContainer.innerHTML = files.map(file => {
      const iconClass = getFileIcon(file.filename);
      return `
        <div class="flex items-center justify-between p-2 bg-[var(--bg-surface-raised)] hover:bg-[var(--bg-surface-hover)] border border-[var(--border-subtle)] rounded-[var(--radius-sm)] transition-all group">
          <div class="flex items-center gap-2 overflow-hidden">
            <div class="w-7 h-7 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] flex items-center justify-center text-xs flex-shrink-0">
              <i class="${iconClass}"></i>
            </div>
            <div class="overflow-hidden">
              <p class="text-xs font-semibold text-[var(--c-cream)] truncate max-w-[160px]" title="${file.filename}">
                ${file.filename}
              </p>
              <span class="text-[10px] text-[var(--text-muted)]">${file.size_formatted}</span>
            </div>
          </div>
          <button 
            onclick="window.deleteFile('${file.file_id}')"
            title="Delete"
            class="p-1 rounded text-[var(--text-muted)] hover:text-rose-400 hover:bg-rose-500/10 transition-colors"
          >
            <i class="fa-regular fa-trash-can text-xs"></i>
          </button>
        </div>
      `;
    }).join("");
  }

  function getFileIcon(filename) {
    const ext = filename.split('.').pop().toLowerCase();
    switch (ext) {
      case 'pdf': return 'fa-regular fa-file-pdf text-[var(--c-rosewood)]';
      case 'docx': case 'doc': return 'fa-regular fa-file-word text-[var(--c-sky)]';
      case 'pptx': case 'ppt': return 'fa-regular fa-file-powerpoint text-[var(--c-cream)]';
      case 'xlsx': case 'xls': case 'csv': return 'fa-regular fa-file-excel text-emerald-400';
      case 'mp3': case 'wav': case 'm4a': case 'ogg': case 'aac': return 'fa-solid fa-file-audio text-[var(--c-sky)]';
      case 'mp4': case 'mov': case 'webm': case 'm4v': return 'fa-solid fa-file-video text-[var(--c-lavender)]';
      default: return 'fa-regular fa-file-lines text-[var(--text-muted)]';
    }
  }

  function updateStorageMeter(usedMb, maxMb) {
    storageUsageText.textContent = `${usedMb.toFixed(1)} / ${maxMb} MB`;
    const percent = Math.min(100, (usedMb / maxMb) * 100);
    storageProgressBar.style.width = `${percent}%`;

    if (percent > 90) {
      storageProgressBar.className = "bg-rose-500 h-full transition-all duration-300";
    } else if (percent > 70) {
      storageProgressBar.className = "bg-[var(--c-rosewood)] h-full transition-all duration-300";
    } else {
      storageProgressBar.className = "bg-[var(--c-sky)] h-full transition-all duration-300";
    }
  }

  window.deleteFile = async function(fileId) {
    const t = i18n[currentLanguage];
    if (!confirm(t.confirmDelete)) return;

    try {
      const res = await fetch(`/api/files/${fileId}?session_id=${encodeURIComponent(currentSessionId)}`, {
        method: "DELETE"
      });
      if (res.ok) {
        showToast(currentLanguage === 'ar' ? "تم حذف الملف بنجاح" : "File deleted successfully", "success");
        await fetchFilesList();
      }
    } catch (e) {
      showToast("Error deleting file", "error");
    }
  };

  // -------------------------------------------------------------
  // الرفع بالسحب والإفلات
  // -------------------------------------------------------------
  dropZone.addEventListener("click", () => fileInput.click());

  dropZone.addEventListener("dragover", (e) => {
    e.preventDefault();
    dropZone.classList.add("dragover-active");
  });

  dropZone.addEventListener("dragleave", () => {
    dropZone.classList.remove("dragover-active");
  });

  dropZone.addEventListener("drop", (e) => {
    e.preventDefault();
    dropZone.classList.remove("dragover-active");
    if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
      handleFilesUpload(e.dataTransfer.files);
    }
  });

  fileInput.addEventListener("change", (e) => {
    if (e.target.files && e.target.files.length > 0) {
      handleFilesUpload(e.target.files);
    }
  });

  async function handleFilesUpload(filesList) {
    if (!filesList || filesList.length === 0) return;

    const formData = new FormData();
    formData.append("session_id", currentSessionId);

    let totalSize = 0;
    for (let i = 0; i < filesList.length; i++) {
      formData.append("files", filesList[i]);
      totalSize += filesList[i].size;
    }

    if (totalSize > 50 * 1024 * 1024) {
      showToast(currentLanguage === 'ar' ? "الحجم يتجاوز 50MB" : "Bundle exceeds 50MB limit", "error");
      return;
    }

    showToast(currentLanguage === 'ar' ? `جارٍ معالجة ${filesList.length} ملف...` : `Processing ${filesList.length} files...`, "info");

    try {
      const res = await fetch("/api/upload", {
        method: "POST",
        body: formData
      });

      const data = await res.json();
      if (res.ok) {
        showToast(i18n[currentLanguage].toastUploaded, "success");
        await fetchFilesList();
      } else {
        showToast(data.detail || "Upload error", "error");
      }
    } catch (err) {
      showToast("Network upload error", "error");
    } finally {
      fileInput.value = "";
    }
  }

  // -------------------------------------------------------------
  // التلخيص الذكي (Smart Summary)
  // -------------------------------------------------------------
  btnSmartSummary.addEventListener("click", () => triggerSmartSummary());
  btnRefreshSummary.addEventListener("click", () => triggerSmartSummary());

  async function triggerSmartSummary() {
    const t = i18n[currentLanguage];
    if (activeFiles.length === 0) {
      showToast(t.noFilesWarning, "warning");
      return;
    }

    switchTab("summary");
    summaryContentArea.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
        <div class="w-8 h-8 rounded-full border-2 border-[var(--c-lavender)]/30 border-t-[var(--c-lavender)] animate-spin"></div>
        <p class="text-xs font-semibold text-[var(--c-cream)]">${t.generatingSummary}</p>
      </div>
    `;

    try {
      const res = await fetch("/api/summarize", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId })
      });

      const data = await res.json();
      if (res.ok && data.summary) {
        const rendered = marked.parse(data.summary);
        summaryContentArea.innerHTML = `<div class="markdown-content">${DOMPurify.sanitize(rendered)}</div>`;
      } else {
        summaryContentArea.innerHTML = `<p class="text-xs text-rose-300">${data.detail || data.error || "Summary error"}</p>`;
      }
    } catch (e) {
      summaryContentArea.innerHTML = `<p class="text-xs text-rose-300">Connection error</p>`;
    }
  }

  btnCopySummary.addEventListener("click", () => {
    const text = summaryContentArea.innerText;
    if (!text) return;
    navigator.clipboard.writeText(text).then(() => showToast(i18n[currentLanguage].toastCopied, "success"));
  });

  // -------------------------------------------------------------
  // الاختبارات الذكية (Interactive Quiz)
  // -------------------------------------------------------------
  if (btnOpenQuizTab) {
    btnOpenQuizTab.addEventListener("click", () => {
      switchTab("quiz");
      if (activeFiles.length > 0 && currentQuiz.length === 0) {
        triggerQuizGeneration();
      }
    });
  }

  btnGenerateQuiz.addEventListener("click", () => triggerQuizGeneration());

  async function triggerQuizGeneration() {
    const t = i18n[currentLanguage];
    if (activeFiles.length === 0) {
      showToast(t.noFilesWarning, "warning");
      return;
    }

    switchTab("quiz");
    const numQuestions = parseInt(quizCountSelect.value, 10) || 5;
    const quizType = quizTypeSelect.value || "all";

    quizContentArea.innerHTML = `
      <div class="h-full flex flex-col items-center justify-center text-center p-8 space-y-3">
        <div class="w-8 h-8 rounded-full border-2 border-[var(--c-sky)]/30 border-t-[var(--c-sky)] animate-spin"></div>
        <p class="text-xs font-semibold text-[var(--c-cream)]">${t.generatingQuiz}</p>
      </div>
    `;

    try {
      const res = await fetch("/api/quiz/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          session_id: currentSessionId,
          num_questions: numQuestions,
          quiz_type: quizType
        })
      });

      const data = await res.json();
      if (res.ok && data.questions && data.questions.length > 0) {
        currentQuiz = data.questions;
        userAnswers = {};
        renderInteractiveQuiz(currentQuiz);
        showToast(t.toastQuizCreated, "success");
      } else {
        quizContentArea.innerHTML = `<p class="text-xs text-rose-300 text-center p-4">${data.message || data.error || "Quiz generation error"}</p>`;
      }
    } catch (e) {
      quizContentArea.innerHTML = `<p class="text-xs text-rose-300 text-center p-4">Connection error</p>`;
    }
  }

  function renderInteractiveQuiz(questions) {
    const t = i18n[currentLanguage];
    quizContentArea.innerHTML = `
      <div class="max-w-2xl mx-auto space-y-5 pb-6">
        
        <div class="flex items-center justify-between bg-[var(--bg-surface-raised)] p-3 rounded-[var(--radius-md)] border border-[var(--border-subtle)]">
          <span class="text-xs font-bold text-[var(--c-cream)]">${t.quizTitle} (${questions.length})</span>
          <span class="text-[10px] font-mono px-2 py-0.5 rounded bg-[var(--bg-app)] text-[var(--c-sky)] border border-[var(--border-subtle)]">
            Ready
          </span>
        </div>

        <div class="space-y-4">
          ${questions.map((q, idx) => `
            <div class="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-[var(--radius-md)] p-4 space-y-3">
              <div class="flex items-start gap-2">
                <span class="w-5 h-5 rounded bg-[var(--c-lavender)]/20 text-[var(--c-cream)] text-[11px] font-bold flex items-center justify-center flex-shrink-0 mt-0.5">
                  ${idx + 1}
                </span>
                <p class="text-xs font-semibold text-[var(--text-primary)] leading-relaxed">
                  ${escapeHtml(q.question)}
                </p>
              </div>

              <div class="grid grid-cols-1 sm:grid-cols-2 gap-2 pt-1">
                ${q.options.map((opt, optIdx) => `
                  <button 
                    type="button"
                    onclick="window.selectQuizOption(${idx}, ${optIdx})"
                    id="opt-btn-${idx}-${optIdx}"
                    class="quiz-opt text-start flex items-center gap-2"
                  >
                    <span class="w-4 h-4 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] flex items-center justify-center text-[9px] font-mono flex-shrink-0">
                      ${String.fromCharCode(65 + optIdx)}
                    </span>
                    <span class="flex-1">${escapeHtml(opt)}</span>
                  </button>
                `).join("")}
              </div>
            </div>
          `).join("")}
        </div>

        <div class="pt-2 flex justify-end">
          <button 
            onclick="window.submitQuiz()" 
            class="btn-primary px-5 py-2.5 text-xs flex items-center gap-2"
          >
            <i class="fa-solid fa-check"></i>
            <span>${t.submitQuiz}</span>
          </button>
        </div>

      </div>
    `;
  }

  window.selectQuizOption = function(qIndex, optIndex) {
    userAnswers[qIndex] = optIndex;
    const totalOptions = currentQuiz[qIndex].options.length;
    for (let i = 0; i < totalOptions; i++) {
      const btn = document.getElementById(`opt-btn-${qIndex}-${i}`);
      if (btn) {
        if (i === optIndex) btn.classList.add("selected");
        else btn.classList.remove("selected");
      }
    }
  };

  window.submitQuiz = function() {
    const t = i18n[currentLanguage];
    let correctCount = 0;
    currentQuiz.forEach((q, idx) => {
      if (userAnswers[idx] === q.correct_index) correctCount++;
    });

    const percentage = Math.round((correctCount / currentQuiz.length) * 100);

    quizContentArea.innerHTML = `
      <div class="max-w-2xl mx-auto space-y-5 pb-6">
        
        <div class="bg-[var(--bg-surface-raised)] border border-[var(--border-subtle)] rounded-[var(--radius-lg)] p-5 text-center space-y-2">
          <h2 class="text-2xl font-extrabold text-[var(--c-cream)]">${t.scoreTitle}: ${percentage}%</h2>
          <p class="text-xs text-[var(--c-sky)]">${correctCount} / ${currentQuiz.length}</p>

          <div class="pt-2 flex justify-center gap-2">
            <button onclick="window.triggerQuizGeneration()" class="btn-secondary px-3.5 py-1.5 text-xs">
              <i class="fa-solid fa-arrows-rotate ml-1"></i> ${t.newQuizBtn}
            </button>
            <button onclick="window.renderInteractiveQuiz(currentQuiz)" class="btn-ghost px-3.5 py-1.5 text-xs">
              <i class="fa-solid fa-repeat ml-1"></i> ${t.retakeQuiz}
            </button>
          </div>
        </div>

        <div class="space-y-3">
          ${currentQuiz.map((q, idx) => {
            const isCorrect = userAnswers[idx] === q.correct_index;
            return `
              <div class="bg-[var(--bg-surface)] border ${isCorrect ? 'border-emerald-500/30' : 'border-rose-500/30'} rounded-[var(--radius-md)] p-4 space-y-2.5">
                <div class="flex items-start justify-between gap-2">
                  <p class="text-xs font-semibold text-[var(--text-primary)]">${idx + 1}. ${escapeHtml(q.question)}</p>
                  <span class="text-[10px] font-bold px-2 py-0.5 rounded ${isCorrect ? 'bg-emerald-500/20 text-emerald-300' : 'bg-rose-500/20 text-rose-300'}">
                    ${isCorrect ? t.correctText : t.wrongText}
                  </span>
                </div>

                <div class="grid grid-cols-1 sm:grid-cols-2 gap-1.5 pt-1">
                  ${q.options.map((opt, optIdx) => {
                    let optClass = "quiz-opt text-xs opacity-75";
                    if (optIdx === q.correct_index) optClass = "quiz-opt correct";
                    else if (optIdx === userAnswers[idx] && !isCorrect) optClass = "quiz-opt wrong";
                    return `<div class="${optClass}">${escapeHtml(opt)}</div>`;
                  }).join("")}
                </div>

                <div class="pt-2 border-t border-[var(--border-subtle)] text-[11px] text-[var(--text-muted)] space-y-1">
                  <p><strong class="text-[var(--c-cream)]">${t.explanationLabel}</strong> ${escapeHtml(q.explanation || '')}</p>
                  <p><strong class="text-[var(--c-sky)]">${t.sourceLabel}</strong> ${escapeHtml(q.source || '')}</p>
                </div>
              </div>
            `;
          }).join("")}
        </div>

      </div>
    `;
  };

  // -------------------------------------------------------------
  // المحادثة (Chat Form & Messages)
  // -------------------------------------------------------------
  chatForm.addEventListener("submit", (e) => {
    e.preventDefault();
    sendMessage();
  });

  chatInput.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });

  quickPromptBtns.forEach(btn => {
    btn.addEventListener("click", () => {
      chatInput.value = btn.innerText.trim();
      sendMessage();
    });
  });

  async function sendMessage() {
    const query = chatInput.value.trim();
    if (!query || isGenerating) return;

    const t = i18n[currentLanguage];
    if (activeFiles.length === 0) {
      appendMessage("user", query);
      appendMessage("assistant", t.noFilesWarning, [], true);
      chatInput.value = "";
      return;
    }

    appendMessage("user", query);
    chatInput.value = "";
    chatInput.style.height = "auto";

    const typingElement = appendTypingIndicator();
    isGenerating = true;
    sendBtn.disabled = true;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          query: query,
          session_id: currentSessionId
        })
      });

      typingElement.remove();
      const data = await res.json();
      if (res.ok) {
        appendMessage("assistant", data.answer, data.citations || [], data.is_rejected);
      } else {
        appendMessage("assistant", `⚠️ ${data.detail || "Error"}`, [], true);
      }
    } catch (err) {
      typingElement.remove();
      appendMessage("assistant", "Connection error", [], true);
    } finally {
      isGenerating = false;
      sendBtn.disabled = false;
      chatInput.focus();
    }
  }

  function appendMessage(role, text, citations = [], isRejected = false) {
    const messageWrapper = document.createElement("div");
    messageWrapper.className = `flex items-start gap-3 ${role === 'user' ? 'justify-start' : ''}`;

    if (role === "user") {
      messageWrapper.innerHTML = `
        <div class="chat-msg-user max-w-2xl">
          ${escapeHtml(text)}
        </div>
      `;
    } else {
      const renderedHtml = marked.parse(text);
      const sanitizedHtml = DOMPurify.sanitize(renderedHtml);

      let citationsHtml = "";
      if (citations && citations.length > 0 && !isRejected) {
        citationsHtml = `
          <div class="mt-2.5 pt-2 border-t border-[var(--border-subtle)] flex flex-wrap items-center gap-1.5 text-[10px] text-[var(--text-muted)]">
            <span class="font-semibold text-[var(--c-sky)]">Sources:</span>
            ${citations.map(c => `<span class="px-2 py-0.5 rounded bg-[var(--bg-app)] border border-[var(--border-subtle)] text-[var(--c-cream)] font-mono">${c.source_label}</span>`).join("")}
          </div>
        `;
      }

      messageWrapper.innerHTML = `
        <div class="w-8 h-8 rounded-xl bg-[var(--c-cream)] p-1 flex-shrink-0 flex items-center justify-center shadow border border-[var(--border-subtle)]">
          <img src="/static/images/logo.png" alt="Mojaweb" class="h-full w-auto object-contain">
        </div>
        <div class="chat-msg-assistant flex-1 max-w-2xl relative group">
          <div class="markdown-content">
            ${sanitizedHtml}
          </div>
          ${citationsHtml}
        </div>
      `;
    }

    chatMessages.appendChild(messageWrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
  }

  function appendTypingIndicator() {
    const typingWrapper = document.createElement("div");
    typingWrapper.className = "flex items-start gap-3";
    typingWrapper.innerHTML = `
      <div class="w-8 h-8 rounded-xl bg-[var(--c-cream)] p-1 flex-shrink-0 flex items-center justify-center shadow border border-[var(--border-subtle)]">
        <img src="/static/images/logo.png" alt="Mojaweb" class="h-full w-auto object-contain">
      </div>
      <div class="chat-msg-assistant flex items-center gap-1.5 py-3">
        <span class="pulse-dot"></span>
        <span class="pulse-dot"></span>
        <span class="pulse-dot"></span>
      </div>
    `;
    chatMessages.appendChild(typingWrapper);
    chatMessages.scrollTop = chatMessages.scrollHeight;
    return typingWrapper;
  }

  // -------------------------------------------------------------
  // إنهاء الجلسة
  // -------------------------------------------------------------
  btnResetSession.addEventListener("click", async () => {
    const t = i18n[currentLanguage];
    if (!confirm(t.confirmReset)) return;

    try {
      await fetch("/api/session/clear", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ session_id: currentSessionId })
      });

      await createNewSession();
      currentQuiz = [];
      userAnswers = {};
      chatMessages.innerHTML = "";
      summaryContentArea.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-center p-8 text-[var(--text-muted)]"><p class="text-xs">${t.noSummaryYet}</p></div>`;
      quizContentArea.innerHTML = `<div class="h-full flex flex-col items-center justify-center text-center p-8 text-[var(--text-muted)]"><p class="text-xs">${t.quizPromptText}</p></div>`;
      switchTab("chat");
      showToast(t.toastCleared, "success");
    } catch (e) {
      showToast("Reset error", "error");
    }
  });

  // -------------------------------------------------------------
  // التبويبات
  // -------------------------------------------------------------
  tabChatBtn.addEventListener("click", () => switchTab("chat"));
  tabSummaryBtn.addEventListener("click", () => switchTab("summary"));
  tabQuizBtn.addEventListener("click", () => switchTab("quiz"));

  function switchTab(tab) {
    [tabChatBtn, tabSummaryBtn, tabQuizBtn].forEach(b => b.classList.remove("active"));
    [chatViewPanel, summaryViewPanel, quizViewPanel].forEach(p => p.classList.add("hidden"));

    if (tab === "chat") {
      tabChatBtn.classList.add("active");
      chatViewPanel.classList.remove("hidden");
    } else if (tab === "summary") {
      tabSummaryBtn.classList.add("active");
      summaryViewPanel.classList.remove("hidden");
    } else if (tab === "quiz") {
      tabQuizBtn.classList.add("active");
      quizViewPanel.classList.remove("hidden");
    }
  }

  function showToast(message, type = "info") {
    toast.textContent = message;
    let bg = "bg-[var(--bg-surface-raised)] text-[var(--c-cream)] border border-[var(--border-medium)]";
    if (type === "success") bg = "bg-emerald-950 text-emerald-200 border border-emerald-600/40";
    if (type === "error") bg = "bg-rose-950 text-rose-200 border border-rose-600/40";
    if (type === "warning") bg = "bg-amber-950 text-amber-200 border border-amber-600/40";

    toast.className = `fixed bottom-5 left-5 z-50 transition-all duration-200 px-4 py-2.5 rounded-[var(--radius-md)] text-xs font-medium shadow-2xl ${bg} opacity-100 transform translate-y-0`;

    setTimeout(() => {
      toast.className = "fixed bottom-5 left-5 z-50 transform translate-y-10 opacity-0 pointer-events-none transition-all duration-200 px-4 py-2.5 rounded-[var(--radius-md)] text-xs font-medium shadow-2xl";
    }, 3500);
  }

  function escapeHtml(text) {
    if (!text) return "";
    const div = document.createElement("div");
    div.textContent = text;
    return div.innerHTML;
  }

  window.triggerQuizGeneration = triggerQuizGeneration;
  window.renderInteractiveQuiz = renderInteractiveQuiz;

  initApp();
});
