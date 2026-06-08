import { useMemo, useState } from "react";

function formatEntrySummary(entry) {
  if (entry?.rawName) {
    // return `Ảnh OCR đã lưu với tên ${entry.rawName}.`;
    return ""
  }

  return "Bản ghi OCR đã được lưu để bạn xem lại khi cần.";
}

function buildHistoryStats(historyEntries, historyMeta) {
  const totalSessions = historyMeta?.sumTotal || historyEntries.length;
  const totalPages = historyMeta?.sumPage || 0;
  const currentItems = historyEntries.length;

  return { totalSessions, totalPages, currentItems };
}

function buildPageWindow(currentPage, totalPages) {
  if (!totalPages) {
    return [];
  }

  const pages = new Set([1, totalPages, currentPage - 1, currentPage, currentPage + 1]);

  return Array.from(pages)
    .filter((page) => page >= 1 && page <= totalPages)
    .sort((a, b) => a - b);
}

function HistoryPage({
  historyEntries = [],
  historyLoading = false,
  historyError = "",
  historyMeta,
  currentPage = 1,
  onBackToOcr,
  onClearHistory,
  onPageChange,
}) {
  const [selectedEntry, setSelectedEntry] = useState(null);
  const stats = useMemo(() => buildHistoryStats(historyEntries, historyMeta), [historyEntries, historyMeta]);
  const latestEntry = historyEntries[0] || null;
  const pageButtons = useMemo(() => buildPageWindow(currentPage, stats.totalPages), [currentPage, stats.totalPages]);

  return (
    <>
      <section className="panel scroll-grow">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Lịch sử OCR</p>
            <h2>Xem lại các lần xử lý đã lưu</h2>
          </div>

          <div className="action-cluster">
            {onBackToOcr ? (
              <button className="ghost-button" type="button" onClick={onBackToOcr}>
                Quay lại OCR
              </button>
            ) : null}

            {onClearHistory ? (
              <button className="ghost-button" type="button" onClick={onClearHistory} disabled={!historyEntries.length}>
                Xóa toàn bộ
              </button>
            ) : null}
          </div>
        </div>

        <div className="history-overview">
          <div className="history-overview-copy">
            <p className="status-text">
              Trang này lấy dữ liệu trực tiếp từ API lịch sử OCR và hiển thị ảnh đã lưu trong thư mục public cùng thời gian xử lý.
            </p>

            {latestEntry ? (
              <div className="history-badge">
                Lần lưu gần nhất: <strong>{latestEntry.createdAt || "Không rõ thời gian"}</strong>
              </div>
            ) : (
              <div className="history-badge">Chưa có bản ghi nào được lưu.</div>
            )}
          </div>

          <div className="history-stat-strip">
            <article className="history-kpi">
              <span>Phiên đã lưu</span>
              <strong>{stats.totalSessions}</strong>
            </article>
            <article className="history-kpi">
              <span>Tổng số trang</span>
              <strong>{stats.totalPages}</strong>
            </article>
            <article className="history-kpi">
              <span>Bản ghi đang hiển thị</span>
              <strong>{stats.currentItems}</strong>
            </article>
          </div>
        </div>

        {historyLoading ? <p className="status-text">Đang tải lịch sử OCR...</p> : null}
        {historyError ? <p className="status-text">{historyError}</p> : null}

        <div className="history-grid">
          {!historyLoading && historyEntries.length ? (
            historyEntries.map((entry) => (
              <article
                key={entry.id}
                className="history-card history-card-clickable"
                onClick={() => setSelectedEntry(entry)}
                onKeyDown={(event) => {
                  if (event.key === "Enter" || event.key === " ") {
                    event.preventDefault();
                    setSelectedEntry(entry);
                  }
                }}
                role="button"
                tabIndex={0}
              >
                {entry.imageUrl ? <img src={entry.imageUrl} alt={entry.title || "Ảnh lịch sử OCR"} /> : null}

                <div className="history-copy">
                  <p className="history-card-time">{entry.createdAt || "Không rõ thời gian"}</p>
                  <h3 className="history-card-title">{entry.title || `Ảnh #${entry.id}`}</h3>
                  <p className="history-card-summary">{formatEntrySummary(entry)}</p>

                  <div className="history-meta-row">
                    <span className="history-meta-chip history-meta-chip-name">{entry.rawName || "Không rõ tên ảnh"}</span>
                    <span className="history-meta-chip">{entry.createdAt || "Không rõ thời gian"}</span>
                    <span>Xem chi tiết</span>
                  </div>
                </div>
              </article>
            ))
          ) : !historyLoading ? (
            <article className="history-card history-empty">
              <div className="history-copy history-empty-copy">
                <p className="eyebrow">Chưa có dữ liệu</p>
                <h3>Chưa có lịch sử OCR nào để hiển thị</h3>
                <p>
                  Sau khi người dùng hoàn tất OCR và lưu lịch sử ảnh, các bản ghi sẽ xuất hiện ở đây để mở lại và đối chiếu nhanh.
                </p>
                {onBackToOcr ? (
                  <button className="ghost-button slim-button" type="button" onClick={onBackToOcr}>
                    Đi tới màn hình OCR
                  </button>
                ) : null}
              </div>
            </article>
          ) : null}
        </div>

        {stats.totalPages > 1 ? (
          <div className="history-pagination" aria-label="Phân trang lịch sử OCR">
            <button
              type="button"
              className="pagination-button"
              onClick={() => onPageChange?.(Math.max(1, currentPage - 1))}
              disabled={historyLoading || currentPage <= 1}
            >
              Trước
            </button>

            {pageButtons.map((page) => (
              <button
                key={page}
                type="button"
                className={`pagination-button ${page === currentPage ? "pagination-button-active" : ""}`}
                onClick={() => onPageChange?.(page)}
                disabled={historyLoading}
                aria-current={page === currentPage ? "page" : undefined}
              >
                {page}
              </button>
            ))}

            <button
              type="button"
              className="pagination-button"
              onClick={() => onPageChange?.(Math.min(stats.totalPages, currentPage + 1))}
              disabled={historyLoading || currentPage >= stats.totalPages}
            >
              Sau
            </button>
          </div>
        ) : null}
      </section>

      {selectedEntry ? (
        <div className="modal" role="dialog" aria-modal="true" onClick={() => setSelectedEntry(null)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <div>
                <h3>{selectedEntry.title || "Chi tiết lịch sử OCR"}</h3>
                <p className="status-text">{selectedEntry.createdAt || "Không rõ thời gian lưu"}</p>
              </div>

              <button className="modal-close" type="button" onClick={() => setSelectedEntry(null)}>
                Đóng
              </button>
            </div>

            <div className="history-detail-grid">
              <article className="history-detail-card">
                <span>Mã lịch sử</span>
                <strong>{selectedEntry.id}</strong>
              </article>
              <article className="history-detail-card">
                <span>Thời gian</span>
                <strong>{selectedEntry.createdAt || "Không rõ"}</strong>
              </article>
              <article className="history-detail-card">
                <span>Tên ảnh</span>
                <strong>{selectedEntry.rawName || "Không rõ"}</strong>
              </article>
            </div>

            {selectedEntry.imageUrl ? (
              <div className="history-preview">
                <img src={selectedEntry.imageUrl} alt={selectedEntry.title || "Ảnh xem trước lịch sử"} />
              </div>
            ) : null}

            <p className="history-json-caption">Dữ liệu trả về từ API lịch sử OCR</p>
            <pre className="modal-json">{JSON.stringify(selectedEntry, null, 2)}</pre>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default HistoryPage;
