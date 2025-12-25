# フロントエンド開発者向けAPI仕様書

## 概要

AI回答生成とPDF結合機能を提供するRESTful APIです。
開発用と本番用の2つのエンドポイントがあり、同じレスポンス形式で統一されています。

## ベースURL

```
http://localhost:8000/rag_api/api
```

## エンドポイント

### 1. テスト用ダミーAPI (開発・テスト用)

```http
POST /test-answer
```

**用途**: フロントエンド開発時のモックAPI
**処理時間**: 即座 (< 100ms)

#### リクエスト

```json
{
  "query": "売上を教えて",
  "category": "financial",
  "tags": ["sales", "report"]
}
```

#### レスポンス (成功時)

```json
{
  "status": "success",
  "code": "S200",
  "detail": "ダミーAI回答生成成功",
  "result": {
    "answer": "ダミー回答: 売上を教えて（カテゴリ: financial）",
    "sources": [
      ["document1.pdf", 3],
      ["document2.pdf", 4],
      ["document3.pdf", 5]
    ],
    "pdf_url": "http://localhost:8000/static/pdfs/merged_response_20250819_114538.pdf"
  }
}
```

### 2. AI回答生成API (本番用)

```http
POST /generate-answer
```

**用途**: 実際のAI回答生成
**処理時間**: 2-5秒

#### リクエスト

```json
{
  "query": "今月の売上実績を教えて",
  "category": "financial",
  "tags": ["monthly", "sales"]
}
```

#### レスポンス (成功時)

```json
{
  "status": "success",
  "code": "S200",
  "detail": "AI回答生成成功",
  "result": {
    "answer": "今月の売上実績は前年同月比15%増の1,200万円でした。主な要因は...",
    "sources": [
      ["sales_report_2025_08.pdf", 12],
      ["financial_summary.pdf", 8]
    ],
    "pdf_url": "http://localhost:8000/static/pdfs/merged_response_20250819_114538.pdf"
  }
}
```

## エラーレスポンス

```json
{
  "status": "error",
  "code": "E500",
  "detail": "Internal Server Error: connection timeout",
  "hint": "サーバー側で予期せぬエラーが発生しました。管理者に連絡してください。"
}
```

## フロントエンド実装ガイド

### 1. 開発時の推奨フロー

```javascript
// 開発時は test-answer を使用
const API_BASE = "http://localhost:8000/rag_api/api";
const endpoint =
  process.env.NODE_ENV === "development"
    ? "/test-answer" // 開発時: 高速ダミーAPI
    : "/generate-answer"; // 本番時: 実際のAI API

const response = await fetch(`${API_BASE}${endpoint}`, {
  method: "POST",
  headers: { "Content-Type": "application/json" },
  body: JSON.stringify({
    query: userQuestion,
    category: selectedCategory,
    tags: selectedTags,
  }),
});
```

### 2. ローディング処理

```javascript
// AI APIは処理時間があるためローディング表示推奨
const [loading, setLoading] = useState(false);

const handleSubmit = async () => {
  setLoading(true);
  try {
    const response = await callAPI();
    // 結果表示処理
  } catch (error) {
    // エラーハンドリング
  } finally {
    setLoading(false);
  }
};
```

### 3. PDF表示

```javascript
// PDFダウンロード/表示
const openPDF = (pdfUrl) => {
  // 新しいタブで開く
  window.open(pdfUrl, "_blank");

  // またはダウンロード
  const link = document.createElement("a");
  link.href = pdfUrl;
  link.download = "ai_response.pdf";
  link.click();
};
```

### 4. TypeScript型定義

```typescript
interface APIRequest {
  query: string;
  category: string;
  tags: string[];
}

interface APIResponse {
  status: "success" | "error";
  code: string;
  detail: string;
  result?: {
    answer: string;
    sources: [string, number][];
    pdf_url: string;
  };
  hint?: string;
}
```

## 注意事項

### PDF管理

- ユーザー向け: `/static/pdfs/merged_response_*.pdf` (公開)
- 開発者向け: `/static/pdfs/debug/` (内部用、個別ページ)
- `pdf_url`は常に結合されたPDFを指します

### 開発・本番切り替え

- 両APIは同じレスポンス形式
- エンドポイントURL変更のみで切り替え可能
- 環境変数での制御を推奨

### エラーハンドリング

- ネットワークエラー
- AI API タイムアウト (30秒)
- 不正なリクエスト形式
- サーバー内部エラー

### パフォーマンス

- `test-answer`: < 100ms (ダミーデータ)
- `generate-answer`: 2-5秒 (AI処理)
- PDF生成: 追加で1-2秒
