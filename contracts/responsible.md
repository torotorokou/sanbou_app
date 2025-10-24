# 📘 Responsive Design ルール（最終版 / A4簡易まとめ）

---

## 🎯 目的
Ant Design の `lg=992px` とプロジェクト独自の `bp.lg=1024px` のズレを解消。  
**`md(768px)` と `xl(1280px)` の2段構成** に統一して、レスポンシブをシンプル化。

---

## 🧩 Grid（Col）置換ルール

| 旧 | 新 | 意味 |
|----|----|------|
| `lg={8}` | `md={12} xl={8}` | 2列 → 3列 |
| `lg={10}` | `md={12} xl={10}` | 均等2列 |
| `lg={12}` | `md={12} xl={12}` | 同幅 |
| `lg={14}` | `md={12} xl={14}` | 広め |
| `lg={16}` | `md={24} xl={16}` | 1列→2列 |

✅ すべての `lg=` を削除し、`md` と `xl` のみ使用。  
768〜1279px帯（tablet）は安定した2列レイアウトに統一。  
（最新SSOT: bp.xl = 1280）

---

## 🎨 CSSルール

**共通定義ファイル：** `/shared/styles/custom-media.css`

```css
@custom-media --lt-md (width < 768px);
@custom-media --ge-md (width >= 768px);
@custom-media --ge-xl (width >= 1280px);
