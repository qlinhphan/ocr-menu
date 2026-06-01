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
    </div>
  );
}

export default App;
