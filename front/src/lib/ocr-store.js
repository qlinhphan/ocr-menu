export const OCR_API_URL = "http://localhost:8000/extract-menu";
export const HISTORY_KEY = "dvx_ocr_history";

export const sampleMenuData = {
  categories: [
    {
      id: 1,
      name: "Banh Mi",
      items: [
        {
          id: 10,
          name: "Banh mi Bamboo dac biet",
          descriptions: [
            {
              id: 100,
              size: "min",
              price: 50000,
              optional: null,
              description: "Gia thap nhat theo set",
            },
            {
              id: 101,
              size: "max",
              price: 70000,
              optional: null,
              description: "Gia cao nhat theo set",
            },
          ],
        },
        {
          id: 11,
          name: "Banh mi Hoi An dac biet",
          descriptions: [
            {
              id: 102,
              size: "min",
              price: 40000,
              optional: null,
              description: "Gia thap nhat theo set",
            },
            {
              id: 103,
              size: "max",
              price: 60000,
              optional: null,
              description: "Gia cao nhat theo set",
            },
          ],
        },
      ],
    },
  ],
};

export function cloneDeep(data) {
  return JSON.parse(JSON.stringify(data));
}

export function createId() {
  return Date.now() + Math.floor(Math.random() * 1000);
}

export function normalizeMenuData(raw) {
  if (raw?.categories && Array.isArray(raw.categories)) {
    return cloneDeep(raw);
  }

  if (raw && raw.name && Array.isArray(raw.items)) {
    return { categories: [cloneDeep(raw)] };
  }

  return cloneDeep(sampleMenuData);
}

export function defaultDescription() {
  return {
    id: createId(),
    size: "",
    price: 0,
    optional: null,
    description: "",
  };
}

export function defaultItem() {
  return {
    id: createId(),
    name: "",
    descriptions: [defaultDescription()],
  };
}

export function defaultCategory() {
  return {
    id: createId(),
    name: "",
    items: [defaultItem()],
  };
}

export function readHistory() {
  try {
    return JSON.parse(localStorage.getItem(HISTORY_KEY) || "[]");
  } catch {
    return [];
  }
}

export function writeHistory(entries) {
  localStorage.setItem(HISTORY_KEY, JSON.stringify(entries));
}
