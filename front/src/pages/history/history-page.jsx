import { useMemo, useState } from "react";

function countItemsFromEntry(entry) {
  return (entry?.data?.categories || []).reduce((total, category) => total + (category.items?.length || 0), 0);
}

function countCategoriesFromEntry(entry) {
  return entry?.data?.categories?.length || 0;
}

function formatEntrySummary(entry) {
  const itemCount = countItemsFromEntry(entry);

  if (entry?.summary) {
    return entry.summary;
  }

  if (itemCount > 0) {
    return `${itemCount} món đã được nhận diện và lưu trong phiên này.`;
  }

  return "Bản ghi OCR đã được lưu để bạn xem lại khi cần.";
}

function buildHistoryStats(historyEntries) {
  const totalSessions = historyEntries.length;
  const totalItems = historyEntries.reduce((sum, entry) => sum + countItemsFromEntry(entry), 0);
  const totalCategories = historyEntries.reduce((sum, entry) => sum + countCategoriesFromEntry(entry), 0);

  return { totalSessions, totalItems, totalCategories };
}

function HistoryPage({ historyEntries = [], onBackToOcr, onClearHistory }) {
  const [selectedEntry, setSelectedEntry] = useState(null);
  const stats = useMemo(() => buildHistoryStats(historyEntries), [historyEntries]);
  const latestEntry = historyEntries[0] || null;

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
              Trang này giúp người dùng mở lại nhanh những lần OCR trước đó, đối chiếu ảnh và xem dữ liệu JSON đã lưu.
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
              <span>Tổng số món</span>
              <strong>{stats.totalItems}</strong>
            </article>
            <article className="history-kpi">
              <span>Tổng nhóm món</span>
              <strong>{stats.totalCategories}</strong>
            </article>
          </div>
        </div>

        <div className="history-grid">
          {historyEntries.length ? (
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
                  <p>{entry.createdAt || "Không rõ thời gian"}</p>
                  <h3>{entry.title || "Phiên OCR đã lưu"}</h3>
                  <p>{formatEntrySummary(entry)}</p>

                  <div className="history-meta-row">
                    <span>{countCategoriesFromEntry(entry)} nhóm</span>
                    <span>{countItemsFromEntry(entry)} món</span>
                    <span>Xem chi tiết</span>
                  </div>
                </div>
              </article>
            ))
          ) : (
            <article className="history-card history-empty">
              <div className="history-copy history-empty-copy">
                <p className="eyebrow">Chưa có dữ liệu</p>
                <h3>Chưa có lịch sử OCR nào để hiển thị</h3>
                <p>
                  Sau khi người dùng hoàn tất OCR và lưu kết quả, các bản ghi sẽ xuất hiện ở đây để mở lại, kiểm tra và
                  đối chiếu nhanh.
                </p>
                {onBackToOcr ? (
                  <button className="ghost-button slim-button" type="button" onClick={onBackToOcr}>
                    Đi tới màn hình OCR
                  </button>
                ) : null}
              </div>
            </article>
          )}
        </div>
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
                <span>Nhóm món</span>
                <strong>{countCategoriesFromEntry(selectedEntry)}</strong>
              </article>
              <article className="history-detail-card">
                <span>Số món</span>
                <strong>{countItemsFromEntry(selectedEntry)}</strong>
              </article>
              <article className="history-detail-card">
                <span>Mô tả</span>
                <strong>{selectedEntry.summary || "Bản ghi OCR đã lưu"}</strong>
              </article>
            </div>

            {selectedEntry.imageUrl ? (
              <div className="history-preview">
                <img src={selectedEntry.imageUrl} alt={selectedEntry.title || "Ảnh xem trước lịch sử"} />
              </div>
            ) : null}

            <p className="history-json-caption">Dữ liệu chi tiết của phiên OCR</p>
            <pre className="modal-json">{JSON.stringify(selectedEntry.data, null, 2)}</pre>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default HistoryPage;
