import { useEffect, useRef, useState } from "react";
import HistoryPage from "./pages/history/history-page";
import OcrPage from "./pages/ocr/ocr-page";
import { normalizeMenuData } from "./lib/ocr-store";

const HISTORY_LIMIT = 5;
const HISTORY_API_URL = "http://localhost:8081/hist-extract";
const AI_ASSISTANT_API_URL = "/api/rag/invoke";
const CREATE_MENU_API_URL = "http://localhost:8081/create-menu";
const ADD_HISTORY_API_URL = "http://localhost:8081/add-history";

function mapHistoryEntry(entry) {
  return {
    id: entry.id,
    title: entry.name_img || `Phiên OCR #${entry.id}`,
    imageUrl: entry.name_img ? `/${entry.name_img}` : "",
    createdAt: entry.thisMoment || "",
    rawName: entry.name_img || "",
  };
}

function useScrollGrow(pageKey) {
  useEffect(() => {
    const nodes = document.querySelectorAll(".scroll-grow");
    const observer = new IntersectionObserver(
      (entries) => {
        entries.forEach((entry) => {
          if (entry.isIntersecting) {
            entry.target.classList.add("is-visible");
          }
        });
      },
      { threshold: 0.18 }
    );

    nodes.forEach((node) => {
      node.classList.remove("is-visible");
      observer.observe(node);
    });

    return () => observer.disconnect();
  }, [pageKey]);
}

const assistantQuickActions = ["Tôi là ai?", "Ai tạo ra hệ thống này?", "Trích xuất nội dung từ ảnh này"];

function countMenuItems(menuData) {
  return (menuData?.categories || []).reduce((total, category) => total + (category.items?.length || 0), 0);
}

function buildObjectSavePayload(menuData) {
  if (!menuData?.categories?.length) {
    return [];
  }

  return menuData.categories.flatMap((category) =>
    (category.items || []).flatMap((item) =>
      (item.descriptions || []).map((description) => ({
        name_cate: category.name ?? "",
        name_menu: item.name ?? "",
        description_item: description.description ?? "",
        optional_item: description.optional ?? null,
        price_item: Number(description.price ?? 0) || 0,
        size_item: description.size ?? "",
      }))
    )
  );
}

function extractImageName(pathImg) {
  if (!pathImg || typeof pathImg !== "string") {
    return "";
  }

  return pathImg.split("/").filter(Boolean).pop() || "";
}

async function postSingleObjectSave(payloadItem, index) {
  const response = await fetch(CREATE_MENU_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify(payloadItem),
  });

  if (!response.ok) {
    let errorMessage = `Không lưu được object thứ ${index + 1}`;

    try {
      const errorPayload = await response.json();
      errorMessage = errorPayload?.message || errorPayload?.detail || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }

    throw new Error(errorMessage);
  }
}

async function postImageHistory(nameImg) {
  const response = await fetch(ADD_HISTORY_API_URL, {
    method: "POST",
    headers: {
      "Content-Type": "application/json",
    },
    body: JSON.stringify({ name_img: nameImg }),
  });

  if (!response.ok) {
    let errorMessage = "Không lưu được lịch sử ảnh";

    try {
      const errorPayload = await response.json();
      errorMessage = errorPayload?.message || errorPayload?.detail || errorMessage;
    } catch {
      const errorText = await response.text();
      errorMessage = errorText || errorMessage;
    }

    throw new Error(errorMessage);
  }
}

function resolveAssistantOcrMenuData(raw) {
  const candidate = raw?.result ?? raw?.flow?.ocr_rs ?? raw?.flow ?? null;

  if (!candidate) {
    return null;
  }

  if (typeof candidate === "string") {
    try {
      return normalizeMenuData(JSON.parse(candidate));
    } catch {
      return null;
    }
  }

  return normalizeMenuData(candidate);
}

async function saveAssistantOcrToJava(raw) {
  const menuData = resolveAssistantOcrMenuData(raw);
  if (!menuData?.categories?.length) {
    throw new Error("Không có dữ liệu OCR hợp lệ để lưu.");
  }

  const payload = buildObjectSavePayload(menuData);
  if (!payload.length) {
    throw new Error("Không có dữ liệu hợp lệ để gửi.");
  }

  for (let index = 0; index < payload.length; index += 1) {
    await postSingleObjectSave(payload[index], index);
  }

  const historyImageName = extractImageName(raw?.path_img || raw?.result?.path_img || "");
  if (historyImageName) {
    await postImageHistory(historyImageName);
  }

  return countMenuItems(menuData);
}

function formatAssistantResponse(payload) {
  if (!payload) {
    return "Không nhận được dữ liệu từ API.";
  }

  const resultValue = payload.result;

  if (typeof resultValue === "string") {
    const trimmed = resultValue.trim();

    if ((trimmed.startsWith("{") && trimmed.endsWith("}")) || (trimmed.startsWith("[") && trimmed.endsWith("]"))) {
      try {
        return JSON.stringify(JSON.parse(trimmed), null, 2);
      } catch {
        return resultValue;
      }
    }

    return resultValue;
  }

  if (Array.isArray(resultValue) || typeof resultValue === "object") {
    return JSON.stringify(resultValue, null, 2);
  }

  return String(resultValue);
}

function AssistantWidget({ onConfirmOcrSave, onSaveSuccess }) {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [draftFile, setDraftFile] = useState(null);
  const [isSending, setIsSending] = useState(false);
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "Mình là trợ lý AI của Menu OCR Studio. Bạn có thể hỏi câu hỏi hệ thống hoặc gửi ảnh để OCR.",
    },
  ]);
  const fileInputRef = useRef(null);

  async function resolveAddPrompt(message, choice) {
    setMessages((current) =>
      current.map((currentMessage) =>
        currentMessage.id === message.id
          ? {
              ...currentMessage,
              addResolved: true,
              addChoice: choice,
            }
          : currentMessage
      )
    );

    if (choice === "yes") {
      try {
        const savedCount = await onConfirmOcrSave?.(message.raw);
        if (savedCount) {
          onSaveSuccess?.(savedCount);
        }
      } catch (error) {
        setMessages((current) => [
          ...current,
          {
            id: Date.now() + 2,
            role: "assistant",
            content: error instanceof Error ? `Lỗi lưu: ${error.message}` : "Lỗi lưu không xác định.",
          },
        ]);
      }
      return;
    }

    setMessages((current) => [
      ...current,
      {
        id: Date.now() + 2,
        role: "assistant",
        content: "Không sao, mình sẽ không tiếp tục nhắc lưu menu này. Bạn có thể hỏi tiếp hoặc gửi ảnh khác.",
      },
    ]);
  }

  async function sendMessage(rawMessage, file = draftFile) {
    const content = rawMessage.trim();

    if (!content && !file) {
      return;
    }

    const userMessageId = Date.now();
    const assistantMessageId = userMessageId + 1;

    setMessages((current) => [
      ...current,
      { id: userMessageId, role: "user", content: content || "Đã gửi ảnh đính kèm", fileName: file?.name || "" },
    ]);

    setDraftMessage("");
    setDraftFile(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }

    setIsOpen(true);
    setIsSending(true);

    try {
      const formData = new FormData();
      if (content) {
        formData.append("text", content);
      }
      if (file) {
        formData.append("file", file);
      }

      const response = await fetch(AI_ASSISTANT_API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "Gọi API thất bại";

        try {
          const errorPayload = await response.json();
          errorMessage = errorPayload?.detail || errorPayload?.message || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }

        throw new Error(errorMessage);
      }

      const result = await response.json();
      setMessages((current) => [
        ...current,
        {
          id: assistantMessageId,
          role: "assistant",
          content: formatAssistantResponse(result),
          raw: result,
          addPrompt: result?.add || "",
          addResolved: false,
        },
      ]);
    } catch (error) {
      setMessages((current) => [
        ...current,
        {
          id: assistantMessageId,
          role: "assistant",
          content: error instanceof Error ? `Lỗi: ${error.message}` : "Lỗi không xác định.",
        },
      ]);
    } finally {
      setIsSending(false);
    }
  }

  return (
    <>
      <button
        type="button"
        className={`ai-fab ${isOpen ? "ai-fab-hidden" : ""}`}
        onClick={() => setIsOpen(true)}
        aria-label="Mở trợ lý AI"
      >
        <span className="ai-fab-ring" />
        <span className="ai-fab-core">AI</span>
      </button>

      {isOpen ? (
        <section className={`ai-panel ${isExpanded ? "ai-panel-expanded" : ""}`} aria-label="Trợ lý AI">
          <div className="ai-panel-header">
            <div>
              <p className="ai-panel-eyebrow">Trợ lý AI</p>
              <strong>Hỗ trợ RAG / OCR</strong>
            </div>

            <div className="ai-panel-actions">
              <button type="button" className="ai-panel-icon" onClick={() => setIsExpanded((current) => !current)}>
                {isExpanded ? "Thu nhỏ" : "Phóng to"}
              </button>
              <button
                type="button"
                className="ai-panel-icon"
                onClick={() => {
                  setIsExpanded(false);
                  setIsOpen(false);
                }}
              >
                Đóng
              </button>
            </div>
          </div>

          <div className="ai-quick-actions">
            {assistantQuickActions.map((action) => (
              <button key={action} type="button" className="ai-chip" onClick={() => sendMessage(action, null)}>
                {action}
              </button>
            ))}
          </div>

          <div className="ai-thread">
            {messages.map((message) => (
              <article
                key={message.id}
                className={`ai-message ${message.role === "user" ? "ai-message-user" : "ai-message-assistant"}`}
              >
                <span className="ai-message-role">{message.role === "user" ? "Bạn" : "AI"}</span>
                {message.fileName ? <p className="ai-message-file">{message.fileName}</p> : null}
                <pre className="ai-message-content">{message.content}</pre>
                {message.addPrompt ? (
                  <div className={`ai-add-card ${message.addResolved ? "ai-add-card-muted" : ""}`}>
                    <p className="ai-add-label">Gợi ý tiếp theo</p>
                    <strong>{message.addPrompt}</strong>
                    {!message.addResolved ? (
                      <div className="ai-add-actions">
                        <button
                          type="button"
                          className="ai-add-yes"
                          onClick={() => resolveAddPrompt(message, "yes")}
                        >
                          Có
                        </button>
                        <button
                          type="button"
                          className="ai-add-no"
                          onClick={() => resolveAddPrompt(message, "no")}
                        >
                          Không
                        </button>
                      </div>
                    ) : (
                      <span className="ai-add-choice">
                        Bạn đã chọn: {message.addChoice === "yes" ? "Có" : "Không"}
                      </span>
                    )}
                  </div>
                ) : null}
              </article>
            ))}
          </div>

          <form
            className="ai-composer"
            onSubmit={(event) => {
              event.preventDefault();
              sendMessage(draftMessage);
            }}
          >
            <input
              value={draftMessage}
              onChange={(event) => setDraftMessage(event.target.value)}
              placeholder="Hỏi về RAG, OCR hoặc gửi ảnh..."
            />
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              hidden
              onChange={(event) => setDraftFile(event.target.files?.[0] || null)}
            />
            <button type="button" className="ai-panel-icon" onClick={() => fileInputRef.current?.click()}>
              {draftFile?.name || "Chọn ảnh"}
            </button>
            <button type="submit" className="primary-button" disabled={isSending}>
              {isSending ? "Đang gửi..." : "Gửi"}
            </button>
          </form>
        </section>
      ) : null}
    </>
  );
}

function App() {
  const [activePage, setActivePage] = useState("ocr");
  const [historyEntries, setHistoryEntries] = useState([]);
  const [historyMeta, setHistoryMeta] = useState({ sumPage: 0, sumTotal: 0 });
  const [historyLoading, setHistoryLoading] = useState(false);
  const [historyError, setHistoryError] = useState("");
  const [historyPage, setHistoryPage] = useState(1);
  const [saveToast, setSaveToast] = useState(null);
  const saveToastTimerRef = useRef(null);

  useScrollGrow(activePage);

  useEffect(() => {
    return () => {
      if (saveToastTimerRef.current) {
        clearTimeout(saveToastTimerRef.current);
      }
    };
  }, []);

  function showSaveToast(itemCount) {
    setSaveToast({ count: itemCount });

    if (saveToastTimerRef.current) {
      clearTimeout(saveToastTimerRef.current);
    }

    saveToastTimerRef.current = setTimeout(() => {
      setSaveToast(null);
    }, 3200);
  }

  useEffect(() => {
    let isMounted = true;

    async function fetchHistory() {
      setHistoryLoading(true);
      setHistoryError("");

      try {
        const response = await fetch(`${HISTORY_API_URL}?limit=${HISTORY_LIMIT}&page=${historyPage}`);

        if (!response.ok) {
          throw new Error("Không tải được lịch sử OCR.");
        }

        const result = await response.json();

        if (!isMounted) {
          return;
        }

        setHistoryEntries(Array.isArray(result?.hists) ? result.hists.map(mapHistoryEntry) : []);
        setHistoryMeta({
          sumPage: Number(result?.sumPage || 0),
          sumTotal: Number(result?.sumTotal || 0),
        });
      } catch (error) {
        if (!isMounted) {
          return;
        }

        setHistoryEntries([]);
        setHistoryMeta({ sumPage: 0, sumTotal: 0 });
        setHistoryError(error instanceof Error ? error.message : "Không tải được lịch sử OCR.");
      } finally {
        if (isMounted) {
          setHistoryLoading(false);
        }
      }
    }

    fetchHistory();

    return () => {
      isMounted = false;
    };
  }, [historyPage]);

  return (
    <div className="app-shell">
      {saveToast ? (
        <div className="save-toast" role="status" aria-live="polite">
          <span className="save-toast-badge">Thành công</span>
          <strong>Lưu thành công {saveToast.count} món</strong>
        </div>
      ) : null}
      <div className="background-orb orb-one" />
      <div className="background-orb orb-two" />
      <div className="noise-layer" />

      <header className="topbar">
        <div className="brand">
          <div className="brand-mark">DVX</div>
          <div>
            <p className="brand-title">Menu OCR Studio</p>
            <p className="brand-subtitle">Nhận diện ảnh nhanh chóng, giúp tiết kiệm thời gian</p>
          </div>
        </div>

        <nav className="nav-links nav-tabs" aria-label="Điều hướng chức năng">
          <button
            type="button"
            className={`nav-tab ${activePage === "ocr" ? "nav-tab-active" : ""}`}
            onClick={() => setActivePage("ocr")}
          >
            OCR
          </button>
          <button
            type="button"
            className={`nav-tab ${activePage === "history" ? "nav-tab-active" : ""}`}
            onClick={() => setActivePage("history")}
          >
            Lịch sử
          </button>
        </nav>
      </header>

      <main className="page-shell">
        <section className="hero scroll-grow">
          <div>
            <p className="eyebrow">Frontend OCR</p>
            <h1>Đọc hiểu ảnh nhanh chóng.</h1>
            <p className="hero-text">
              Hệ thống dùng để nhập menu món ăn từ ảnh. Bạn có thể chụp ảnh, rồi hệ thống tự động điền dữ liệu cho bạn.
            </p>

            <div className="hero-actions">
              <button className="primary-button" type="button" onClick={() => setActivePage("ocr")}>
                Mở OCR
              </button>
              <button className="ghost-button" type="button" onClick={() => setActivePage("history")}>
                Xem lịch sử
              </button>
            </div>
          </div>

          <div className="hero-stat-panel">
            <article className="stat-card">
              <span>Trang hiện tại</span>
              <strong>{activePage === "ocr" ? "OCR workspace" : "OCR history"}</strong>
            </article>
            <article className="stat-card">
              <span>Bản ghi hiện có</span>
              <strong>{historyMeta.sumTotal || historyEntries.length} phiên</strong>
            </article>
            <article className="stat-card">
              <span>Hiệu năng</span>
              <strong>Nhanh chóng, ổn định, thân thiện và mạnh mẽ</strong>
            </article>
          </div>
        </section>

        {activePage === "ocr" ? (
          <OcrPage />
        ) : (
          <HistoryPage
            historyEntries={historyEntries}
            historyLoading={historyLoading}
            historyError={historyError}
            historyMeta={historyMeta}
            currentPage={historyPage}
            onBackToOcr={() => setActivePage("ocr")}
            onPageChange={setHistoryPage}
          />
        )}
      </main>

      <AssistantWidget
        onConfirmOcrSave={async (raw) => {
          const savedCount = await saveAssistantOcrToJava(raw);
          return savedCount;
        }}
        onSaveSuccess={(itemCount) => showSaveToast(itemCount)}
      />
    </div>
  );
}

export default App;
