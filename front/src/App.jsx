import { useEffect, useState } from "react";
import HistoryPage from "./pages/history/history-page";
import OcrPage from "./pages/ocr/ocr-page";
import { readHistory } from "./lib/ocr-store";

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

  if (normalizedInput.includes("ocr") || normalizedInput.includes("ảnh") || normalizedInput.includes("trích")) {
    return "Bạn chỉ cần chọn ảnh, bấm 'Đọc ảnh', rồi kiểm tra lại tên nhóm, tên món và từng dòng giá trước khi lưu.";
  }

  if (normalizedInput.includes("sửa") || normalizedInput.includes("mô tả") || normalizedInput.includes("giá")) {
    return "Sau khi OCR xong, bạn có thể sửa trực tiếp từng ô tên món, size, giá, tùy chọn thêm và mô tả ngay trong form kết quả.";
  }

  if (normalizedInput.includes("lưu")) {
    return "Khi dữ liệu đã ổn, bấm nút lưu ở cuối form. Hệ thống sẽ lưu theo số món hiện đang có trên màn hình.";
  }

  if (normalizedInput.includes("lịch sử") || normalizedInput.includes("history")) {
    return "Trang lịch sử sẽ giữ lại các lần OCR đã lưu để bạn mở lại và xem nhanh dữ liệu cũ.";
  }

  return "Mình có thể hỗ trợ bạn ở các bước OCR ảnh, chỉnh dữ liệu món, kiểm tra mô tả hoặc lưu menu. Bạn muốn làm bước nào?";
}

function AssistantWidget() {
  const [isOpen, setIsOpen] = useState(false);
  const [isExpanded, setIsExpanded] = useState(false);
  const [draftMessage, setDraftMessage] = useState("");
  const [messages, setMessages] = useState([
    {
      id: 1,
      role: "assistant",
      content: "Mình là trợ lý AI của Menu OCR Studio. Bạn có thể hỏi cách OCR, sửa dữ liệu món hoặc lưu kết quả.",
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
              placeholder="Hỏi về OCR, chỉnh món hoặc lưu dữ liệu..."
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
  const [historyEntries, setHistoryEntries] = useState(() => readHistory());

  useScrollGrow(activePage);

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
            <p className="brand-subtitle">Nhận diện và ảnh nhanh chóng, giúp tiếp kiệm thời gian</p>
          </div>
        </div>

        <nav className="nav-links nav-tabs" aria-label="Dieu huong chuc nang">
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
            <h1>Đọc hiểu ảnh nhanh chóng & xem lại dễ dàng.</h1>
            <p className="hero-text">
              Hệ thống được xử dụng cho việc thêm menu món ăn. Thay vì phải nhập tay thì giờ đây có thể chụp ảnh sau đó hệ thống tự động điền cho bạn
            </p>

            <div className="hero-actions">
              <button className="primary-button" type="button" onClick={() => setActivePage("ocr")}>
                Mở OCR
              </button>
              <button className="ghost-button" type="button" onClick={() => setActivePage("history")}>
                Mở lịch sử
              </button>
            </div>
          </div>

          <div className="hero-stat-panel">
            <article className="stat-card">
              <span>Trang hiện tại</span>
              <strong>{activePage === "ocr" ? "OCR workspace" : "OCR history"}</strong>
            </article>
            <article className="stat-card">
              <span>Số bản đã lưu</span>
              <strong>{historyEntries.length} Mục lịch sử</strong>
            </article>
            <article className="stat-card">
              <span>Hiệu năng</span>
              <strong>Nhanh chóng, ổn định, thân thiện và mạnh mẽ</strong>
            </article>
          </div>
        </section>

        {activePage === "ocr" ? (
          <OcrPage
            historyEntries={historyEntries}
            setHistoryEntries={setHistoryEntries}
            onOpenHistory={() => setActivePage("history")}
          />
        ) : (
          <HistoryPage
            historyEntries={historyEntries}
            setHistoryEntries={setHistoryEntries}
            onBackToOcr={() => setActivePage("ocr")}
          />
        )}
      </main>

      <AssistantWidget />
    </div>
  );
}

export default App;
