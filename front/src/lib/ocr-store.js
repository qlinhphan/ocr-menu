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

function normalizeDescriptionEntry(rawDescription) {
  return {
    id: rawDescription?.id ?? createId(),
    size: rawDescription?.size ?? rawDescription?.size_item ?? "",
    price: Number(rawDescription?.price ?? rawDescription?.price_item ?? 0) || 0,
    optional: rawDescription?.optional ?? rawDescription?.optional_item ?? null,
    description: rawDescription?.description ?? rawDescription?.description_item ?? "",
  };
}

function normalizeItemEntry(rawItem) {
  const descriptionSource = Array.isArray(rawItem?.descriptions)
    ? rawItem.descriptions
    : rawItem && (
          rawItem.size !== undefined ||
          rawItem.size_item !== undefined ||
          rawItem.price !== undefined ||
          rawItem.price_item !== undefined ||
          rawItem.optional !== undefined ||
          rawItem.optional_item !== undefined ||
          rawItem.description !== undefined ||
          rawItem.description_item !== undefined
        )
      ? [rawItem]
      : [];

  const descriptions = descriptionSource.length
    ? descriptionSource.map(normalizeDescriptionEntry)
    : [defaultDescription()];

  return {
    id: rawItem?.id ?? rawItem?.menu_item_id ?? createId(),
    name: rawItem?.name ?? rawItem?.name_menu ?? "",
    descriptions,
  };
}

function normalizeCategoryEntry(rawCategory) {
  const itemSource = Array.isArray(rawCategory?.items)
    ? rawCategory.items
    : rawCategory && (rawCategory.name_menu !== undefined || rawCategory.name !== undefined)
      ? [rawCategory]
      : [];

  const items = itemSource.length ? itemSource.map(normalizeItemEntry) : [defaultItem()];

  return {
    id: rawCategory?.id ?? rawCategory?.cate_id ?? createId(),
    name: rawCategory?.name ?? rawCategory?.name_cate ?? "",
    items,
  };
}

function normalizeObjectSaveCollection(rawCollection) {
  const groupedCategories = new Map();

  rawCollection.forEach((entry) => {
    const categoryKey = `${entry?.cate_id ?? ""}::${entry?.name_cate ?? ""}`;
    const itemKey = `${entry?.menu_item_id ?? ""}::${entry?.name_menu ?? ""}`;

    if (!groupedCategories.has(categoryKey)) {
      groupedCategories.set(categoryKey, {
        id: entry?.cate_id ?? createId(),
        name: entry?.name_cate ?? "",
        items: [],
        itemMap: new Map(),
      });
    }

    const category = groupedCategories.get(categoryKey);

    if (!category.itemMap.has(itemKey)) {
      const nextItem = {
        id: entry?.menu_item_id ?? createId(),
        name: entry?.name_menu ?? "",
        descriptions: [],
      };
      category.itemMap.set(itemKey, nextItem);
      category.items.push(nextItem);
    }

    category.itemMap.get(itemKey).descriptions.push(
      normalizeDescriptionEntry({
        id: createId(),
        size_item: entry?.size_item,
        price_item: entry?.price_item,
        optional_item: entry?.optional_item,
        description_item: entry?.description_item,
      })
    );
  });

  return {
    categories: Array.from(groupedCategories.values()).map(({ itemMap, ...category }) => ({
      ...category,
      items: category.items.map((item) => ({
        ...item,
        descriptions: item.descriptions.length ? item.descriptions : [defaultDescription()],
      })),
    })),
  };
}

export function normalizeMenuData(raw) {
  if (raw?.categories && Array.isArray(raw.categories)) {
    return {
      categories: raw.categories.map(normalizeCategoryEntry),
    };
  }

  if (raw && raw.name && Array.isArray(raw.items)) {
    return { categories: [normalizeCategoryEntry(raw)] };
  }

  if (Array.isArray(raw) && raw.some((entry) => entry?.name_cate || entry?.name_menu)) {
    return normalizeObjectSaveCollection(raw);
  }

  if (raw && (raw.name_cate || raw.name_menu || raw.description_item || raw.price_item !== undefined)) {
    return normalizeObjectSaveCollection([raw]);
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
