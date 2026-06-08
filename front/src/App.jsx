import { useEffect, useState } from "react";
import HistoryPage from "./pages/history/history-page";
import OcrPage from "./pages/ocr/ocr-page";

const HISTORY_LIMIT = 5;
const HISTORY_API_URL = "http://localhost:8081/hist-extract";

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

const assistantQuickActions = [
  "Hướng dẫn OCR ảnh",
  "Cách sửa món sau khi trích xuất",
  "Lưu menu như thế nào",
];

function buildAssistantReply(input) {
  const normalizedInput = input.trim().toLowerCase();

  if (!normalizedInput) {
    return "Mình đang ở đây để hỗ trợ OCR menu, chỉnh dữ liệu món và lưu kết quả. Bạn cứ hỏi ngắn gọn là được.";
  }

  if (normalizedInput.includes("ocr") || normalizedInput.includes("ảnh") || normalizedInput.includes("anh") || normalizedInput.includes("trích")) {
    return "Bạn chỉ cần chọn ảnh, bấm 'Đọc ảnh', rồi kiểm tra lại tên nhóm, tên món và từng dòng giá trước khi lưu.";
  }

  if (normalizedInput.includes("sửa") || normalizedInput.includes("sua") || normalizedInput.includes("mô tả") || normalizedInput.includes("mo ta") || normalizedInput.includes("giá") || normalizedInput.includes("gia")) {
    return "Sau khi OCR xong, bạn có thể sửa trực tiếp từng ô tên món, size, giá, tùy chọn thêm và mô tả ngay trong form kết quả.";
  }

  if (normalizedInput.includes("lưu") || normalizedInput.includes("luu")) {
    return "Khi dữ liệu đã ổn, bấm nút lưu ở cuối form. Hệ thống sẽ lưu theo số món hiện đang có trên màn hình.";
  }

  if (normalizedInput.includes("lịch sử") || normalizedInput.includes("lich su")) {
    return "Bạn có thể mở tab Lịch sử để xem lại các phiên OCR đã lưu và kiểm tra nhanh dữ liệu chi tiết.";
  }

  return "Mình có thể hỗ trợ bạn ở các bước OCR ảnh, chỉnh dữ liệu món, kiểm tra mô tả hoặc xem lịch sử. Bạn muốn làm bước nào?";
}

function AssistantWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "Mình là trợ lý AI của Menu OCR Studio. Bạn có thể hỏi cách OCR, sửa dữ liệu món, lưu kết quả hoặc xem lịch sử.",
    },
  ]);

  function sendMessage(rawMessage) {
    const content = rawMessage.trim();

    if (!content) {
      return;
    }

    setMessages((current) => [
      ...current,
      { id: Date.now(), role: "user", content },
      { id: Date.now() + 1, role: "assistant", content: buildAssistantReply(content) },
    ]);
    setDraftMessage("");
    setIsOpen(true);
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
              <strong>Hỗ trợ nhanh cho người dùng</strong>
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
              <button key={action} type="button" className="ai-chip" onClick={() => sendMessage(action)}>
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
                <p>{message.content}</p>
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
              placeholder="Hỏi về OCR, chỉnh món, lưu dữ liệu hoặc xem lịch sử..."
            />
            <button type="submit" className="primary-button">
              Gửi
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

  useScrollGrow(activePage);

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
              Hệ thống được sử dụng cho việc thêm menu món ăn. Thay vì phải nhập tay thì giờ đây có thể chụp ảnh, sau
              đó hệ thống tự động điền dữ liệu cho bạn.
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

      <AssistantWidget />
    </div>
  );
}

export default App;
