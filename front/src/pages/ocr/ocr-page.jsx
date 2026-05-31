import { startTransition, useEffect, useRef, useState } from "react";
import {
  OCR_API_URL,
  cloneDeep,
  createId,
  defaultCategory,
  defaultDescription,
  defaultItem,
  normalizeMenuData,
  sampleMenuData,
  writeHistory,
} from "../../lib/ocr-store";

function FieldBlock({ label, hint, children }) {
  return (
    <label className="field-block">
      <span className="field-label">{label}</span>
      {children}
      <span className="field-hint">{hint}</span>
    </label>
  );
}

function OcrPage({ historyEntries, setHistoryEntries, onOpenHistory }) {
  const fileInputRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [originalImageUrl, setOriginalImageUrl] = useState("");
  const [ocrImageUrl, setOcrImageUrl] = useState("");
  const [menuData, setMenuData] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("Chua co anh nao duoc chon.");
  const [saveStatus, setSaveStatus] = useState("");
  const [showDetail, setShowDetail] = useState(false);

  useEffect(() => {
    return () => {
      if (originalImageUrl) {
        URL.revokeObjectURL(originalImageUrl);
      }
    };
  }, [originalImageUrl]);

  function updateMenuData(updater) {
    startTransition(() => {
      setMenuData((current) => {
        const base = cloneDeep(current || { categories: [] });
        updater(base);
        return base;
      });
    });
  }

  function handleChooseFile(file) {
    if (!file) return;

    setSelectedFile(file);
    const nextUrl = URL.createObjectURL(file);
    setOriginalImageUrl((prev) => {
      if (prev) URL.revokeObjectURL(prev);
      return nextUrl;
    });
    setOcrImageUrl("");
    setMenuData(null);
    setShowDetail(false);
    setSaveStatus("");
    setUploadStatus(`Da chon anh: ${file.name}`);
  }

  async function handleDetect() {
    if (!selectedFile) {
      setUploadStatus("Hay chon anh menu truoc khi detect OCR.");
      return;
    }

    setUploadStatus("Dang gui anh den OCR service...");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(OCR_API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        throw new Error("OCR API tra ve loi");
      }

      const result = await response.json();
      setOcrImageUrl(originalImageUrl);
      setMenuData(normalizeMenuData(result));
      setUploadStatus("OCR thanh cong. Ban co the xem va chinh sua ket qua ben duoi.");
    } catch {
      setOcrImageUrl(originalImageUrl);
      setMenuData(normalizeMenuData(sampleMenuData));
      setUploadStatus("Khong goi duoc API. Giao dien da nap du lieu mau de ban tiep tuc thao tac.");
    }
  }

  function saveHistory() {
    if (!menuData) {
      setSaveStatus("Chua co du lieu de luu.");
      return;
    }

    const firstCategory = menuData.categories?.[0];
    const nextEntry = {
      id: createId(),
      imageUrl: originalImageUrl,
      createdAt: new Date().toLocaleString("vi-VN"),
      title: firstCategory?.name || "OCR Menu",
      summary: `${menuData.categories?.length || 0} nhom mon duoc luu`,
      data: menuData,
    };

    const nextHistory = [nextEntry, ...historyEntries].slice(0, 12);
    writeHistory(nextHistory);
    setHistoryEntries(nextHistory);
    setSaveStatus("Da luu ket qua OCR vao lich su.");
  }

  function addCategory() {
    updateMenuData((draft) => {
      draft.categories.push(defaultCategory());
    });
  }

  function removeCategory(categoryIndex) {
    updateMenuData((draft) => {
      draft.categories.splice(categoryIndex, 1);
    });
  }

  function addItem(categoryIndex) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items.push(defaultItem());
    });
  }

  function removeItem(categoryIndex, itemIndex) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items.splice(itemIndex, 1);
    });
  }

  function addDescription(categoryIndex, itemIndex) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items[itemIndex].descriptions.push(defaultDescription());
    });
  }

  function removeDescription(categoryIndex, itemIndex, descriptionIndex) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items[itemIndex].descriptions.splice(descriptionIndex, 1);
    });
  }

  function updateCategoryName(categoryIndex, value) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].name = value;
    });
  }

  function updateItemName(categoryIndex, itemIndex, value) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items[itemIndex].name = value;
    });
  }

  function updateDescriptionField(categoryIndex, itemIndex, descriptionIndex, field, value) {
    updateMenuData((draft) => {
      draft.categories[categoryIndex].items[itemIndex].descriptions[descriptionIndex][field] = value;
    });
  }

  return (
    <>
      <section className="panel scroll-grow">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Chuc nang 1</p>
            <h2>Upload anh menu de detect OCR</h2>
          </div>
          <button className="ghost-button" type="button" onClick={() => setMenuData(normalizeMenuData(sampleMenuData))}>
            Nap du lieu mau
          </button>
        </div>

        <div className="upload-layout">
          <div className="upload-card">
            <button
              type="button"
              className="dropzone"
              onClick={() => fileInputRef.current?.click()}
              onDragOver={(event) => event.preventDefault()}
              onDrop={(event) => {
                event.preventDefault();
                handleChooseFile(event.dataTransfer.files?.[0]);
              }}
            >
              <input
                ref={fileInputRef}
                type="file"
                hidden
                accept="image/*"
                onChange={(event) => handleChooseFile(event.target.files?.[0])}
              />
              <span className="dropzone-badge">Keo tha hoac bam de chon anh</span>
              <strong>Anh menu goc</strong>
              <p>Ho tro PNG, JPG, JPEG. Sau khi chon, anh se hien ngay ben phai.</p>
            </button>

            <button className="primary-button full-width" type="button" onClick={handleDetect}>
              Detect OCR
            </button>
            <p className="status-text">{uploadStatus}</p>

            <div className="mini-action-row">
              <button className="ghost-button full-width" type="button" onClick={onOpenHistory}>
                Mo trang lich su
              </button>
            </div>
          </div>

          <div className="preview-grid">
            <article className="image-stage">
              <div className="stage-header">
                <span className="stage-dot" />
                <h3>Anh ban dau</h3>
              </div>
              <div className={`image-frame ${originalImageUrl ? "has-image" : ""}`}>
                {originalImageUrl ? <img src={originalImageUrl} alt="Anh menu goc" /> : null}
                {!originalImageUrl ? <div className="empty-state">Anh goc se hien thi o day</div> : null}
              </div>
            </article>

            <article className={`image-stage ocr-stage ${ocrImageUrl ? "active" : ""}`}>
              <div className="stage-header">
                <span className="stage-dot success" />
                <h3>Anh da OCR</h3>
              </div>
              <div className={`image-frame ${ocrImageUrl ? "has-image" : ""}`}>
                {ocrImageUrl ? <img src={ocrImageUrl} alt="Anh da OCR" /> : null}
                <div className="scan-overlay" />
                {!ocrImageUrl ? <div className="empty-state">Anh OCR se hien thi o day sau khi detect</div> : null}
              </div>

              {menuData ? (
                <button className="detail-button" type="button" onClick={() => setShowDetail(true)}>
                  Xem chi tiet JSON
                </button>
              ) : null}
            </article>
          </div>
        </div>

        {menuData ? (
          <div className="editor-panel">
            <div className="editor-header">
              <div>
                <p className="eyebrow">Ket qua OCR</p>
                <h3>Thong tin menu sau OCR</h3>
              </div>
              <button className="ghost-button" type="button" onClick={addCategory}>
                Them nhom
              </button>
            </div>

            <div className="category-list">
              {menuData.categories.map((category, categoryIndex) => (
                <article key={category.id ?? categoryIndex} className="category-card">
                  <div className="category-top">
                    <FieldBlock label="Ten nhom mon" hint="Vi du: Mon chinh, Do uong, Trang mieng.">
                      <input
                        className="category-name-input"
                        value={category.name ?? ""}
                        onChange={(event) => updateCategoryName(categoryIndex, event.target.value)}
                        placeholder="Ten nhom mon"
                      />
                    </FieldBlock>
                    <button className="danger-button" type="button" onClick={() => removeCategory(categoryIndex)}>
                      Bo nhom
                    </button>
                  </div>

                  {category.items.map((item, itemIndex) => (
                    <div key={item.id ?? itemIndex} className="item-card">
                      <div className="item-top">
                        <FieldBlock label="Ten mon" hint="Nhap ten mon OCR nhan dien duoc hoac ten da chinh sua.">
                          <input
                            className="item-name-input"
                            value={item.name ?? ""}
                            onChange={(event) => updateItemName(categoryIndex, itemIndex, event.target.value)}
                            placeholder="Ten mon"
                          />
                        </FieldBlock>
                        <button className="danger-button" type="button" onClick={() => removeItem(categoryIndex, itemIndex)}>
                          Bo mon
                        </button>
                      </div>

                      <div className="descriptions-list">
                        {item.descriptions.map((description, descriptionIndex) => (
                          <div key={description.id ?? descriptionIndex} className="description-card">
                            <div className="description-grid">
                              <FieldBlock label="Kich co / size" hint="Vi du: S, M, L, ly vua, phan nho.">
                                <input
                                  value={description.size ?? ""}
                                  onChange={(event) =>
                                    updateDescriptionField(categoryIndex, itemIndex, descriptionIndex, "size", event.target.value)
                                  }
                                  placeholder="size"
                                />
                              </FieldBlock>
                              <FieldBlock label="Gia" hint="Nhap gia tri so, vi du 45000.">
                                <input
                                  type="number"
                                  value={description.price ?? 0}
                                  onChange={(event) =>
                                    updateDescriptionField(
                                      categoryIndex,
                                      itemIndex,
                                      descriptionIndex,
                                      "price",
                                      Number(event.target.value || 0)
                                    )
                                  }
                                  placeholder="price"
                                />
                              </FieldBlock>
                              <FieldBlock label="Tuy chon them" hint="Ghi chu nhu nong, da, topping, muc do cay.">
                                <input
                                  value={description.optional ?? ""}
                                  onChange={(event) =>
                                    updateDescriptionField(
                                      categoryIndex,
                                      itemIndex,
                                      descriptionIndex,
                                      "optional",
                                      event.target.value || null
                                    )
                                  }
                                  placeholder="optional"
                                />
                              </FieldBlock>
                              <FieldBlock label="Mo ta" hint="Mo ta ngan gon de lam ro thong tin cua dong gia nay.">
                                <input
                                  value={description.description ?? ""}
                                  onChange={(event) =>
                                    updateDescriptionField(
                                      categoryIndex,
                                      itemIndex,
                                      descriptionIndex,
                                      "description",
                                      event.target.value
                                    )
                                  }
                                  placeholder="description"
                                />
                              </FieldBlock>
                            </div>
                            <button
                              className="danger-button slim-button"
                              type="button"
                              onClick={() => removeDescription(categoryIndex, itemIndex, descriptionIndex)}
                            >
                              Bo dong
                            </button>
                          </div>
                        ))}
                      </div>

                      <div className="item-actions">
                        <button className="tiny-button" type="button" onClick={() => addDescription(categoryIndex, itemIndex)}>
                          Them mo ta gia
                        </button>
                      </div>
                    </div>
                  ))}

                  <div className="item-actions">
                    <button className="tiny-button" type="button" onClick={() => addItem(categoryIndex)}>
                      Them mon
                    </button>
                  </div>
                </article>
              ))}
            </div>

            <div className="save-row">
              <button className="primary-button" type="button" onClick={saveHistory}>
                Luu vao lich su
              </button>
              <p className="status-text">{saveStatus}</p>
            </div>
          </div>
        ) : null}
      </section>

      {showDetail ? (
        <div className="modal" role="dialog" aria-modal="true" onClick={() => setShowDetail(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Chi tiet JSON OCR</h3>
              <button className="modal-close" type="button" onClick={() => setShowDetail(false)}>
                Dong
              </button>
            </div>
            <pre className="modal-json">{JSON.stringify(menuData, null, 2)}</pre>
          </div>
        </div>
      ) : null}
    </>
  );
}

export default OcrPage;
