# Hướng dẫn annotate menu (Schema v1)

Tài liệu này mô tả cách gán nhãn ảnh menu theo [`schema_v1.json`](./schema_v1.json). Mỗi ảnh tương ứng **một file JSON** cùng tên (ví dụ `images/menu_001.png` → `annotations/menu_001.json`).

---

## 1. Mục tiêu annotate

- **Chuyển nội dung menu trên ảnh thành cấu trúc JSON** có thể dùng cho huấn luyện/đánh giá mô hình đọc menu (OCR + structuring).
- **Bám sát những gì người đọc thấy trên ảnh**, không suy diễn món không có trên menu, không bổ sung giá/size không hiển thị.
- **Phân cấp đúng**: danh mục (category) → món (item) → các biến thể giá (descriptions: size, giá, mô tả, tuỳ chọn).
- **Giá luôn là số nguyên VND** (bỏ dấu chấm/phẩy, đơn vị `k`/`K` quy đổi đúng).
- **Nhất quán giữa các ảnh**: cùng quy tắc đặt tên, cùng cách xử lý combo/size/OCR sai.

---

## 2. Định nghĩa từng field

Cấu trúc gốc:

```json
{
  "categories": [ ... ]
}
```

### 2.1. `categories` (bắt buộc)

Mảng các **nhóm món** trên menu (thường là tiêu đề in đậm/lớn: *Khai vị*, *Món chính*, *Đồ uống*, *APPETIZERS*, …).

| Field | Kiểu | Mô tả |
|-------|------|--------|
| `categories` | `array` | Toàn bộ menu; thứ tự phần tử = thứ tự **từ trên xuống dưới, trái sang phải** trên ảnh (theo layout đọc tự nhiên). |

### 2.2. Trong mỗi category: `name`, `items`

| Field | Kiểu | Mô tả |
|-------|------|--------|
| `name` | `string` | Tên danh mục **đúng như trên ảnh** (giữ nguyên ngôn ngữ, hoa/thường nếu menu in vậy). |
| `items` | `array` | Danh sách món thuộc danh mục đó. |

### 2.3. Trong mỗi item: `name`, `descriptions`

| Field | Kiểu | Mô tả |
|-------|------|--------|
| `name` | `string` | **Tên món** (không gồm size, giá, mô tả dài). Một dòng/tên chính trên menu. |
| `descriptions` | `array` | Một hoặc nhiều **dòng giá/biến thể** của cùng một món. Luôn có ít nhất 1 phần tử nếu món có giá hiển thị. |

### 2.4. Trong mỗi phần tử `descriptions`

| Field | Kiểu | Bắt buộc | Mô tả |
|-------|------|----------|--------|
| `price` | `integer` (≥ 0) | **Có** | Giá **VND**, số nguyên. Ví dụ: `45.000đ` → `45000`; `120k` → `120000`. |
| `size` | `string` \| `null` | Không | Nhãn size nếu có: `S`, `M`, `L`, `Nhỏ`, `Vừa`, `Lớn`, `Ly`, `Chai`, `0.5L`, … `null` nếu menu **không** tách size. |
| `description` | `string` \| `null` | Không | Mô tả ngắn **gắn với món** (thành phần, cách chế biến, ghi chú in dưới tên). Không nhét tên món hoặc giá vào đây. |
| `optional` | `string` \| `null` | Không | Tuỳ chọn in trên menu: topping, độ cay, thay đổi món trong combo, “chọn 1 trong 3”, … `null` nếu không có. |

**Lưu ý schema:** Chỉ được các field trên; không thêm field khác (`additionalProperties: false`).

---

## 3. Text nào phải bỏ (không đưa vào JSON)

Không annotate các nội dung **không phải món + giá + mô tả món** của menu:

| Loại | Ví dụ | Xử lý |
|------|--------|--------|
| Thông tin quán | Tên nhà hàng, slogan, logo chữ | Bỏ |
| Liên hệ / địa chỉ | SĐT, Zalo, Facebook, website, QR caption | Bỏ |
| Khuyến mãi chung | “Giảm 20%”, “Happy hour 17h–19h” (không gắn 1 món cụ thể) | Bỏ |
| Ghi chú phục vụ chung | “Giá đã gồm VAT”, “Giá có thể thay đổi”, “+10% service charge” | Bỏ |
| Số trang / watermark | “Trang 1/2”, “Photo by …”, app watermark | Bỏ |
| Trang trí / không đọc được | Hoa văn, icon không có chữ, chữ mờ không đoán được | Bỏ |
| Chỉ mục / số thứ tự trang trí | “01”, “•” đứng một mình không phải size | Bỏ (trừ khi menu dùng làm **size** rõ ràng) |
| Ngôn ngữ trùng không thêm thông tin | Nếu menu song ngữ **cùng một món một dòng**, giữ **một** bản (ưu tiên ngôn ngữ chính của menu; nếu hai dòng tách biệt cho hai món → annotate hai item) | Bỏ bản trùng |

**Vẫn giữ** nếu menu in chung với món: ghi chú “cay”, “chay”, “best seller” **dưới tên món** → đưa vào `description` hoặc `optional` tùy ngữ cảnh.

---

## 4. Quy tắc trường hợp đặc biệt

### 4.1. Một món nhiều size (nhiều giá)

- **Một** `item` với `name` = tên món.
- **Nhiều** phần tử trong `descriptions`, mỗi phần tử một `size` + `price` tương ứng.

Ví dụ trên ảnh: *Cà phê sữa — S 25.000 / M 30.000 / L 35.000*

```json
{
  "name": "Cà phê sữa",
  "descriptions": [
    { "size": "S", "price": 25000, "optional": null, "description": null },
    { "size": "M", "price": 30000, "optional": null, "description": null },
    { "size": "L", "price": 35000, "optional": null, "description": null }
  ]
}
```

Size lấy **đúng nhãn trên ảnh** (không tự đổi `S` → `Nhỏ` nếu menu ghi `S`).

---

### 4.2. Không có size (một giá)

- Một phần tử `descriptions` với `size: null`.
- `price` bắt buộc.

```json
{
  "name": "Phở bò tái",
  "descriptions": [
    {
      "size": null,
      "price": 65000,
      "optional": null,
      "description": "Ăn kèm rau, chanh, ớt"
    }
  ]
}
```

Nếu menu in **hai cột giá** nhưng **không** ghi size (ví dụ “Mang về” / “Tại chỗ”): dùng `size` = nhãn trên ảnh (`"Mang về"`, `"Tại chỗ"`) — coi là biến thể giá, không phải S/M/L.

---

### 4.3. Combo / set / meal

**Nguyên tắc:** Combo là **một item** nếu menu bán như **một dòng một giá** (tên combo + giá tổng).

- `name`: tên combo (vd. *Combo A*, *Set lunch 1*).
- `description`: liệt kê thành phần **như in trên menu** (có thể nhiều dòng gộp một string, giữ xuống dòng bằng `\n` nếu menu xuống dòng rõ).
- `optional`: phần “chọn”, “thay”, “kèm” — vd. *Chọn nước: Coca / Sprite / Trà đá*.

**Combo nhiều mức giá** (vd. 2 người / 4 người): nhiều `descriptions`, `size` = nhãn mức (`"2 người"`, `"4 người"`) hoặc `null` nếu menu chỉ in hai giá cạnh nhau không có nhãn — khi đó ghi nhãn suy ra **chỉ khi** menu có chữ phân biệt (vd. cột “Nhỏ” / “Lớn”); nếu không có nhãn, dùng `description` để phân biệt và `size: null` cho từng giá **theo thứ tự trên ảnh**.

**Không** tách từng món con thành item riêng **trừ khi** menu in **từng dòng có giá riêng** (khi đó là món lẻ, không phải combo).

---

### 4.4. OCR bị sai / chữ khó đọc

| Tình huống | Quy tắc |
|------------|---------|
| Đọc được **chắc chắn** | Ghi đúng chữ trên ảnh (kể cả lỗi chính tả của menu: *Phở bò* menu in *Phở bò đặc biệt* → ghi y nguyên). |
| Đọc **không chắc** một phần | Ghi phần chắc; phần không chắc dùng `?` cho **ký tự/dòng** đó (vd. `"Bún ch?a"`). Không đoán món phổ biến. |
| **Giá** mờ nhưng đọc được vài chữ số | Ghi số đọc được; nếu thiếu chữ số cuối → `?` **không** dùng cho `price` (price phải là integer). Nếu không đủ chắc để ra số nguyên hợp lệ → **bỏ hẳn** dòng giá đó; nếu món không còn giá nào hợp lệ → **không** tạo item đó. |
| Cả dòng **không đọc được** | Không tạo item cho dòng đó. |
| Lỗi rõ do ảnh (nhầm O/0) | Sửa **chỉ khi** ngữ cảnh menu (các giá khác, format) cho thấy rõ là lỗi ảnh; ghi trong `description` item: `"[note] giá đọc từ ảnh mờ, đã chuẩn hóa 45000"` nếu team cho phép note — nếu không có field note, ưu tiên giá đúng format và **không** thêm field ngoài schema. |

**Không** sửa tên món cho “đúng chính tả” nếu menu in sai — dataset phản ánh **menu thật trên ảnh**.

---

## 5. Quy ước giá và format

- Đơn vị: **VND**, kiểu **integer**.
- `45.000` / `45,000` / `45.000đ` → `45000`.
- `120k` / `120K` → `120000`.
- Hai giá cùng dòng: tách thành hai object `descriptions`.
- Menu in “++” / “+15.000” topping: giá topping **chỉ** annotate nếu menu có **giá số**; phần “+ topping” không có số → `optional`, không tạo `price` riêng trừ khi có giá cụ thể.

---

## 6. Ví dụ hoàn chỉnh

Ảnh giả định có cấu trúc:

- Header: *Nhà hàng ABC – 0901234567* (bỏ)
- **Khai vị**: *Gỏi cuốn* 40.000 — *Chả giò (4 pcs)* 55.000, ghi *kèm tương ớt*
- **Đồ uống**: *Trà đào* — Ly 35.000 / Chai 60.000
- **Combo**: *Combo Lunch* 99.000 — *Cơm + canh + trà*; *Chọn món: Gà rán hoặc Cá kho*
- Footer: *Giá chưa bao gồm VAT* (bỏ)

File `menu_099.json`:

```json
{
  "categories": [
    {
      "name": "Khai vị",
      "items": [
        {
          "name": "Gỏi cuốn",
          "descriptions": [
            {
              "size": null,
              "price": 40000,
              "optional": null,
              "description": null
            }
          ]
        },
        {
          "name": "Chả giò (4 pcs)",
          "descriptions": [
            {
              "size": null,
              "price": 55000,
              "optional": null,
              "description": "kèm tương ớt"
            }
          ]
        }
      ]
    },
    {
      "name": "Đồ uống",
      "items": [
        {
          "name": "Trà đào",
          "descriptions": [
            {
              "size": "Ly",
              "price": 35000,
              "optional": null,
              "description": null
            },
            {
              "size": "Chai",
              "price": 60000,
              "optional": null,
              "description": null
            }
          ]
        }
      ]
    },
    {
      "name": "Combo",
      "items": [
        {
          "name": "Combo Lunch",
          "descriptions": [
            {
              "size": null,
              "price": 99000,
              "optional": "Chọn món: Gà rán hoặc Cá kho",
              "description": "Cơm + canh + trà"
            }
          ]
        }
      ]
    }
  ]
}
```

---

## 7. Checklist trước khi nộp

- [ ] JSON hợp lệ `schema_v1.json`, chỉ có field cho phép.
- [ ] Mọi `descriptions[]` đều có `price` (integer ≥ 0).
- [ ] Không còn text menu (món/giá) bị sót; không có text “phải bỏ” (mục 3).
- [ ] Nhiều size → nhiều `descriptions`; một giá → một phần tử, `size: null`.
- [ ] Combo = một item nếu một giá combo; thành phần / lựa chọn trong `description` / `optional`.
- [ ] Tên file JSON khớp tên ảnh (`menu_001.png` → `menu_001.json`).

Tham chiếu schema: [`schema_v1.json`](./schema_v1.json).
