# Chat Feature

## 概要

AI質問応答機能 (Solvest Navi) を提供します。

## ディレクトリ構造

```
chat/
├── domain/
│   └── types.ts                    # 型定義 (ChatMessage, ChatAnswerRequest, ChatAnswerResult)
├── ports/
│   └── repository.ts               # IChatRepository インターフェース
├── application/
│   └── useChatVM.ts                # ViewModel（将来実装）/ postChatAnswer 再エクスポート
├── infrastructure/
│   └── chat.repository.ts          # ChatRepository 実装
├── ui/
│   ├── cards/
│   │   ├── ChatAnswerSection.tsx
│   │   ├── ChatQuestionSection.tsx
│   │   └── ChatSendButtonSection.tsx
│   └── components/
│       ├── AnswerViewer.tsx
│       ├── ChatMessageCard.tsx
│       ├── PdfCardList.tsx
│       ├── PdfPreviewModal.tsx
│       ├── QuestionPanel.tsx
│       └── References.tsx
├── styles/
│   └── QuestionPanel.css
├── index.ts                        # Public API
└── README.md
```

## 主要なエクスポート

### Domain

- `ChatMessage`: チャットメッセージ型
- `ChatAnswerRequest`: チャット質問リクエスト型
- `ChatAnswerResult`: チャット回答レスポンス型

### Application

- `postChatAnswer`: チャット質問API関数
- `ChatRepository`: リポジトリクラス

### UI Components

#### Cards

- `ChatAnswerSection`: AI応答表示エリア
- `ChatQuestionSection`: 質問入力エリア
- `ChatSendButtonSection`: 送信ボタンセクション

#### Components

- `AnswerViewer`: マークダウン形式の応答表示
- `ChatMessageCard`: チャットメッセージカード
- `PdfCardList`: PDF参照リスト
- `PdfPreviewModal`: PDFプレビューモーダル
- `QuestionPanel`: 質問パネル (カテゴリ/テンプレート選択)
- `References`: 参照リスト

## 使用例

```typescript
import {
  postChatAnswer,
  ChatAnswerSection,
  ChatQuestionSection,
} from "@features/chat";

const result = await postChatAnswer({
  question: "AIへの質問",
  category: "general",
});
```

- **役割**: 送信ボタン
- **パス**: `@/components/chat/ChatSendButtonSection.tsx`
- **機能**:
  - 送信処理
  - ローディング状態

#### PdfPreviewModal

- **役割**: PDFプレビューモーダル
- **パス**: `@/components/chat/PdfPreviewModal.tsx`
- **機能**:
  - PDF.jsによるプレビュー
  - レスポンシブ対応

### API Client

#### chatService

- **パス**: `@/services/chatService.ts`
- **メソッド**:
  - `sendQuestion()`: 質問送信
  - `getQuestionTemplates()`: テンプレート取得 (将来)

### Pages

#### SolvestNavi

- **パス**: `@/pages/navi/SolvestNavi.tsx`
- **役割**: チャットページのメインコンポーネント
- **機能**:
  - 質問・回答フロー管理
  - ステップインジケーター
  - PDF関連資料の表示

## 使用例

### 基本的なチャットフロー

```typescript
import { useState } from 'react';
import { apiPost } from '@shared/infrastructure/http';
import ChatQuestionSection from '@/components/chat/ChatQuestionSection';
import ChatAnswerSection from '@/components/chat/ChatAnswerSection';

function ChatPage() {
  const [question, setQuestion] = useState('');
  const [answer, setAnswer] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSend = async () => {
    setLoading(true);
    try {
      const res = await apiPost('/rag_api/chat', { question });
      setAnswer(res.answer);
    } finally {
      setLoading(false);
    }
  };

  return (
    <>
      <ChatQuestionSection
        question={question}
        onChange={setQuestion}
      />
      <button onClick={handleSend} disabled={loading}>
        送信
      </button>
      {answer && <ChatAnswerSection answer={answer} />}
    </>
  );
}
```

## 質問テンプレート

### カテゴリ別テンプレート

- **取得API**: `/rag_api/api/question-options`
- **形式**:
  ```typescript
  {
    "category1": [
      { "title": "質問例1", "tag": ["tag1", "tag2"] },
      { "title": "質問例2", "tag": ["tag3"] }
    ]
  }
  ```

### テンプレート選択

ユーザーが質問テンプレートを選択すると、質問入力欄に自動入力

## チャットフロー

### ステップ

1. **質問入力** - ユーザーが質問を入力/選択
2. **送信** - バックエンドAI APIに送信
3. **AI処理** - RAG (Retrieval-Augmented Generation) で回答生成
4. **応答表示** - マークダウン形式で表示
5. **関連資料** - 必要に応じてPDF表示

### ローディング状態

- **Spin コンポーネント**: "AIが回答中です..." 表示
- **全画面オーバーレイ**: ユーザー操作をブロック

## 依存関係

### 内部依存

- `@shared/infrastructure/http` - API通信
- `@shared/utils/pdfWorkerLoader` - PDF.js初期化
- `@shared/hooks/ui` - レスポンシブ対応
- `@features/notification` - 通知表示

### 外部依存

- `antd` - UIコンポーネント (Spin, Button, Modal)
- `react-markdown` - マークダウンレンダリング (将来)
- `pdfjs-dist` - PDF表示

## API仕様

### 質問送信API

```
POST /rag_api/chat
Content-Type: application/json

Body:
{
  "question": "質問内容",
  "context": { ... }  // optional
}

Response:
{
  "answer": "AI応答テキスト",
  "sources": [...]  // 参照資料 (optional)
}
```

### 質問テンプレート取得

```
GET /rag_api/api/question-options

Response:
{
  "基本操作": [
    { "title": "環境将軍の使い方は?", "tag": ["基本"] }
  ],
  "詳細設定": [
    { "title": "詳細設定の方法は?", "tag": ["設定"] }
  ]
}
```

## PDFプレビュー

### PDF.js 統合

- **ワーカー読み込み**: `ensurePdfJsWorkerLoaded()`
- **遅延初期化**: 初回使用時のみロード
- **レスポンシブ**: 画面サイズに応じてスケール調整

### モーダル制御

```typescript
const [pdfVisible, setPdfVisible] = useState(false);
const [pdfUrl, setPdfUrl] = useState('');

// PDF表示
setPdfUrl('/api/pdf/document.pdf');
setPdfVisible(true);

// モーダル
<PdfPreviewModal
  visible={pdfVisible}
  onClose={() => setPdfVisible(false)}
  pdfUrl={pdfUrl}
/>
```

## エラーハンドリング

### エラー種別

1. **ネットワークエラー**: API通信失敗
2. **AIエラー**: AI応答生成失敗
3. **タイムアウト**: 長時間応答なし

### 通知方法

- エラー時: `notifyError()` で詳細メッセージ表示
- 成功時: `notifySuccess()` で完了通知

## 今後の改善点

### Phase 4 (将来)

- [ ] `features/chat/` 配下への完全移行
- [ ] チャット履歴保存
- [ ] マルチターン会話対応
- [ ] ファイルアップロード対応

### 機能追加

- [ ] 音声入力
- [ ] 応答のコピー機能
- [ ] 質問の履歴検索
- [ ] お気に入り質問

### 技術的負債

- [ ] WebSocket対応 (リアルタイム応答)
- [ ] ストリーミング応答
- [ ] オフライン対応
- [ ] 応答品質のフィードバック

## セキュリティ

### 入力検証

- 質問文字数制限 (例: 500文字)
- SQLインジェクション対策
- XSS対策 (応答のサニタイズ)

### アクセス制御

- 認証済みユーザーのみアクセス
- レート制限 (過度なAPI呼び出し防止)

## パフォーマンス

### 最適化

- PDF.jsの遅延読み込み
- 応答のキャッシング (将来)
- 画像の遅延読み込み

## 関連ドキュメント

- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `@shared/utils/pdfWorkerLoader.ts` - PDF初期化
- `/rag_api` - RAG API仕様

---

**最終更新**: 2025年10月3日  
**メンテナ**: Sanbou App Team
