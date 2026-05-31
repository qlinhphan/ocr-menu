import { useState } from "react";
import { writeHistory } from "../../lib/ocr-store";

function HistoryPage({ historyEntries, setHistoryEntries, onBackToOcr }) {
  const [selectedEntry, setSelectedEntry] = useState(null);

  function clearHistory() {
    writeHistory([]);
    setHistoryEntries([]);
    setSelectedEntry(null);
  }

  return (
    <>
      <section className="panel scroll-grow">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Chuc nang 2</p>
            <h2>Xem lich su OCR</h2>
          </div>
          <div className="action-cluster">
            <button className="ghost-button" type="button" onClick={onBackToOcr}>
              Quay lai OCR
            </button>
            <button className="ghost-button" type="button" onClick={clearHistory}>
              Xoa lich su
            </button>
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
                {entry.imageUrl ? <img src={entry.imageUrl} alt={entry.title} /> : null}
                <div className="history-copy">
                  <p>{entry.createdAt}</p>
                  <h3>{entry.title}</h3>
                  <p>{entry.summary}</p>
                </div>
              </article>
            ))
          ) : (
            <article className="history-card history-empty">
              <div className="history-copy">
                <p>Chua co lich su OCR. Sau khi luu ket qua, danh sach se hien thi tai day.</p>
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
                <h3>{selectedEntry.title}</h3>
                <p className="status-text">{selectedEntry.createdAt}</p>
              </div>
              <button className="modal-close" type="button" onClick={() => setSelectedEntry(null)}>
                Dong
              </button>
            </div>

            {selectedEntry.imageUrl ? (
              <div className="history-preview">
                <img src={selectedEntry.imageUrl} alt={selectedEntry.title} />
              </div>
            ) : null}

            <pre className="modal-json">{JSON.stringify(selectedEntry.data, null, 2)}</pre>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default HistoryPage;
