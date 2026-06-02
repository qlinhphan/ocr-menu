import { startTransition, useEffect, useRef, useState } from "react";
import { OCR_API_URL, cloneDeep, defaultCategory, defaultItem, normalizeMenuData, sampleMenuData } from "../../lib/ocr-store";

const CREATE_MENU_API_URL = "http://localhost:8081/create-menu";
const ADD_HISTORY_API_URL = "http://localhost:8081/add-history";

function FieldBlock({ label, hint, children }) {
  return (
    <label className="field-block">
      <span className="field-label">{label}</span>
      {children}
      <span className="field-hint">{hint}</span>
    </label>
  );
}

function resolveOcrImageUrl(pathImg) {
  if (!pathImg) {
    return "";
  }

  if (typeof pathImg === "string" && /^https?:\/\//i.test(pathImg)) {
    const absoluteImageUrl = new URL(pathImg);
    absoluteImageUrl.searchParams.set("t", Date.now().toString());
    return absoluteImageUrl.toString();
  }

  const normalizedPath = pathImg.startsWith("/") ? pathImg : `/${pathImg}`;
  const imageUrl = new URL(normalizedPath, window.location.origin);
  imageUrl.searchParams.set("t", Date.now().toString());
  return imageUrl.toString();
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

function countMenuItems(menuData) {
  return (menuData?.categories || []).reduce((total, category) => total + (category.items?.length || 0), 0);
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

function OcrPage() {
  const fileInputRef = useRef(null);
  const celebrationTimerRef = useRef(null);
  const [selectedFile, setSelectedFile] = useState(null);
  const [originalImageUrl, setOriginalImageUrl] = useState("");
  const [ocrImageUrl, setOcrImageUrl] = useState("");
  const [ocrImagePath, setOcrImagePath] = useState("");
  const [menuData, setMenuData] = useState(null);
  const [uploadStatus, setUploadStatus] = useState("Chưa có ảnh nào được chọn.");
  const [saveStatus, setSaveStatus] = useState("");
  const [saveSuccessModal, setSaveSuccessModal] = useState({ visible: false, itemCount: 0 });
  const [showDetail, setShowDetail] = useState(false);
  const [isExtracting, setIsExtracting] = useState(false);
  const [isSaving, setIsSaving] = useState(false);
  const [showCelebration, setShowCelebration] = useState(false);

  useEffect(() => {
    return () => {
      if (originalImageUrl) {
        URL.revokeObjectURL(originalImageUrl);
      }

      if (celebrationTimerRef.current) {
        clearTimeout(celebrationTimerRef.current);
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

  function resetWorkspace() {
    setSelectedFile(null);
    setOriginalImageUrl((prev) => {
      if (prev) {
        URL.revokeObjectURL(prev);
      }

      return "";
    });
    setOcrImageUrl("");
    setOcrImagePath("");
    setMenuData(null);
    setUploadStatus("Chưa có ảnh nào được chọn.");
    setSaveStatus("");
    setShowDetail(false);
    setShowCelebration(false);

    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  }

  function handleChooseFile(file) {
    if (!file) {
      return;
    }

    setSelectedFile(file);
    const nextUrl = URL.createObjectURL(file);
    setOriginalImageUrl((prev) => {
      if (prev) {
        URL.revokeObjectURL(prev);
      }

      return nextUrl;
    });
    setOcrImageUrl("");
    setOcrImagePath("");
    setMenuData(null);
    setShowDetail(false);
    setSaveStatus("");
    setSaveSuccessModal({ visible: false, itemCount: 0 });
    setUploadStatus(`Đã chọn ảnh: ${file.name}`);
  }

  async function handleDetect() {
    if (isExtracting) {
      return;
    }

    if (!selectedFile) {
      setUploadStatus("Hãy chọn ảnh trước");
      return;
    }

    setIsExtracting(true);
    setShowCelebration(false);
    setSaveSuccessModal({ visible: false, itemCount: 0 });
    setUploadStatus("Đang đọc ảnh...");

    const formData = new FormData();
    formData.append("file", selectedFile);

    try {
      const response = await fetch(OCR_API_URL, {
        method: "POST",
        body: formData,
      });

      if (!response.ok) {
        let errorMessage = "API lỗi";

        try {
          const errorPayload = await response.json();
          errorMessage = errorPayload?.detail || errorMessage;
        } catch {
          const errorText = await response.text();
          errorMessage = errorText || errorMessage;
        }

        throw new Error(errorMessage);
      }

      const result = await response.json();
      const nextOcrImageUrl = resolveOcrImageUrl(result.path_img);
      const normalizedMenuData = normalizeMenuData(result);
      const extractedItemCount = countMenuItems(normalizedMenuData);

      setOcrImageUrl(nextOcrImageUrl);
      setOcrImagePath(result.path_img || "");
      setMenuData(normalizedMenuData);
      setUploadStatus(`Hoàn tất, đã trích xuất ${extractedItemCount} món. Bạn có thể xem và chỉnh kết quả bên dưới.`);
      setShowCelebration(true);

      if (celebrationTimerRef.current) {
        clearTimeout(celebrationTimerRef.current);
      }

      celebrationTimerRef.current = setTimeout(() => {
        setShowCelebration(false);
      }, 5000);
    } catch (error) {
      setOcrImageUrl("");
      setOcrImagePath("");
      setMenuData(null);
      setUploadStatus(error instanceof Error ? `OCR thất bại: ${error.message}` : "OCR thất bại.");
    } finally {
      setIsExtracting(false);
    }
  }

  async function saveHistory() {
    if (isSaving) {
      return;
    }

    if (!menuData) {
      setSaveStatus("Chưa có dữ liệu để lưu.");
      return;
    }

    const payload = buildObjectSavePayload(menuData);

    if (!payload.length) {
      setSaveStatus("Không có dữ liệu hợp lệ để gửi.");
      return;
    }

    setIsSaving(true);

    try {
      for (let index = 0; index < payload.length; index += 1) {
        await postSingleObjectSave(payload[index], index);
      }
    } catch (error) {
      setIsSaving(false);
      setSaveStatus(error instanceof Error ? `Lưu thất bại: ${error.message}` : "Lưu thất bại.");
      return;
    }

    const historyImageName = extractImageName(ocrImagePath);

    if (historyImageName) {
      try {
        await postImageHistory(historyImageName);
      } catch (error) {
        setIsSaving(false);
        setSaveStatus(
          error instanceof Error
            ? `Đã lưu món ăn nhưng lưu lịch sử ảnh thất bại: ${error.message}`
            : "Đã lưu món ăn nhưng lưu lịch sử ảnh thất bại."
        );
        return;
      }
    }

    const savedItemCount = countMenuItems(menuData);
    setSaveSuccessModal({ visible: true, itemCount: savedItemCount });
    setSaveStatus("");
    setIsSaving(false);
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
      {showCelebration ? (
        <div className="celebration-layer" aria-hidden="true">
          <span className="spark-trail spark-trail-one" />
          <span className="spark-trail spark-trail-two" />
          <span className="firework firework-one" />
          <span className="firework firework-two" />
          <span className="firework firework-three" />
        </div>
      ) : null}

      <section className="panel scroll-grow">
        <div className="section-heading">
          <div>
            <p className="eyebrow">Chức năng OCR</p>
            <h2>Click để upload ảnh</h2>
          </div>
          <button className="ghost-button" type="button" onClick={() => setMenuData(normalizeMenuData(sampleMenuData))}>
            Khu vực OCR
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
              <span className="dropzone-badge">Bấm để chọn ảnh</span>
              <strong>Ảnh gốc</strong>
              <p>Hỗ trợ PNG, JPG, JPEG. Kết quả sẽ hiển thị ngay khi thao tác thành công</p>
            </button>

            <button className="primary-button full-width" type="button" onClick={handleDetect} disabled={isExtracting}>
              {isExtracting ? "Đang đọc ảnh..." : "Đọc ảnh"}
            </button>
            <p className="status-text">{uploadStatus}</p>
          </div>

          <div className="preview-grid">
            <article className="image-stage">
              <div className="stage-header">
                <span className="stage-dot" />
                <h3>Ảnh ban đầu</h3>
              </div>
              <div className={`image-frame ${originalImageUrl ? "has-image" : ""}`}>
                {originalImageUrl ? <img src={originalImageUrl} alt="Ảnh menu gốc" /> : null}
                {!originalImageUrl ? <div className="empty-state">Ảnh gốc sẽ hiện ở đây</div> : null}
              </div>
            </article>

            <article className={`image-stage ocr-stage ${ocrImageUrl ? "active" : ""}`}>
              <div className="stage-header">
                <span className="stage-dot success" />
                <h3>Kết quả</h3>
              </div>
              <div className={`image-frame ${ocrImageUrl ? "has-image" : ""}`}>
                {ocrImageUrl ? <img src={ocrImageUrl} alt="Ảnh đã OCR" /> : null}
                <div className="scan-overlay" />
                {isExtracting ? (
                  <div className="extracting-overlay">
                    <div className="extracting-spinner" />
                    <div className="extracting-copy">
                      <strong>Đang xử lý...</strong>
                      <span>Hệ thống đang trích xuất thông tin từ ảnh của bạn</span>
                    </div>
                  </div>
                ) : null}
                {!ocrImageUrl ? <div className="empty-state">Ảnh kết quả sẽ hiện ở đây</div> : null}
              </div>

              {menuData ? (
                <button className="detail-button" type="button" onClick={() => setShowDetail(true)}>
                  Xem chi tiết JSON
                </button>
              ) : null}
            </article>
          </div>
        </div>

        {menuData ? (
          <div className="editor-panel">
            <div className="editor-header">
              <div>
                <p className="eyebrow">Kết quả</p>
                <h3>Thông tin trích xuất</h3>
              </div>
              <button className="ghost-button" type="button" onClick={addCategory}>
                Thêm nhóm
              </button>
            </div>

            <div className="category-list">
              {menuData.categories.map((category, categoryIndex) => (
                <article key={category.id ?? categoryIndex} className="category-card">
                  <div className="category-top">
                    <FieldBlock label="Tên nhóm món" hint="Ví dụ: Món chính, Đồ uống, Tráng miệng.">
                      <input
                        className="category-name-input"
                        value={category.name ?? ""}
                        onChange={(event) => updateCategoryName(categoryIndex, event.target.value)}
                        placeholder="Tên nhóm món"
                      />
                    </FieldBlock>
                    <button className="danger-button" type="button" onClick={() => removeCategory(categoryIndex)}>
                      Bỏ nhóm
                    </button>
                  </div>

                  {category.items.map((item, itemIndex) => (
                    <div key={item.id ?? itemIndex} className="item-card">
                      <div className="item-top">
                        <FieldBlock label="Tên món" hint="Nhập tên món OCR nhận diện được hoặc tên đã chỉnh sửa.">
                          <input
                            className="item-name-input"
                            value={item.name ?? ""}
                            onChange={(event) => updateItemName(categoryIndex, itemIndex, event.target.value)}
                            placeholder="Tên món"
                          />
                        </FieldBlock>
                        <button className="danger-button" type="button" onClick={() => removeItem(categoryIndex, itemIndex)}>
                          Bỏ món
                        </button>
                      </div>

                      <div className="descriptions-list">
                        {item.descriptions.map((description, descriptionIndex) => (
                          <div key={description.id ?? descriptionIndex} className="description-card">
                            <div className="description-grid">
                              <FieldBlock label="Kích cỡ / Size" hint="Ví dụ: S, M, L, ly vừa, phần nhỏ.">
                                <input
                                  value={description.size ?? ""}
                                  onChange={(event) =>
                                    updateDescriptionField(categoryIndex, itemIndex, descriptionIndex, "size", event.target.value)
                                  }
                                  placeholder="size"
                                />
                              </FieldBlock>
                              <FieldBlock label="Giá" hint="Nhập giá sản phẩm, ví dụ 45000">
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
                              <FieldBlock label="Tùy chọn thêm" hint="Ghi chú như nóng, đá, topping, mức độ cay.">
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
                              <FieldBlock label="Mô tả" hint="Mô tả ngắn gọn để làm rõ thông tin của dòng giá này.">
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
                          </div>
                        ))}
                      </div>
                    </div>
                  ))}

                  <div className="item-actions">
                    <button className="tiny-button" type="button" onClick={() => addItem(categoryIndex)}>
                      Thêm món
                    </button>
                  </div>
                </article>
              ))}
            </div>

            <div className="save-row">
              <button className="primary-button" type="button" onClick={saveHistory} disabled={isSaving}>
                {isSaving ? "Đang lưu..." : `Lưu ${countMenuItems(menuData)} món`}
              </button>
              <p className="status-text">{saveStatus}</p>
            </div>
          </div>
        ) : null}
      </section>

      {saveSuccessModal.visible ? (
        <div className="modal" role="dialog" aria-modal="true">
          <div className="modal-card">
            <div className="modal-header">
              <div>
                <h3>Thêm thành công</h3>
                <p className="status-text">Thêm thành công {saveSuccessModal.itemCount} món</p>
              </div>
            </div>

            <div className="action-cluster" style={{ justifyContent: "flex-end", marginTop: 20 }}>
              <button
                className="primary-button"
                type="button"
                onClick={() => {
                  setSaveSuccessModal({ visible: false, itemCount: 0 });
                  resetWorkspace();
                }}
              >
                OK
              </button>
            </div>
          </div>
        </div>
      ) : null}

      {showDetail ? (
        <div className="modal" role="dialog" aria-modal="true" onClick={() => setShowDetail(false)}>
          <div className="modal-card" onClick={(event) => event.stopPropagation()}>
            <div className="modal-header">
              <h3>Chi tiết JSON OCR</h3>
              <button className="modal-close" type="button" onClick={() => setShowDetail(false)}>
                Đóng
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
