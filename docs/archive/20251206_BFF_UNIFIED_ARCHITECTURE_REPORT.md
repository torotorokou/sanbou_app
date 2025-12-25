# BFF統一アーキテクチャ リファクタリング完了レポート

## 📋 概要

FSD構成 + MVVM（Hooks=ViewModel）+ Repositoryパターン + SOLID原則に従い、
**core_api（BFF）経由の統一通信アーキテクチャ**を実装しました。

## 🎯 アーキテクチャ原則の適用

### ✅ BFF（Backend for Frontend）パターン

- フロントエンドは**唯一のエントリーポイント `/core_api/...`** のみに通信
- core_api が他のバックエンド（rag_api, ledger_api など）へ内部フォワード
- マイクロサービス間の複雑さをフロントエンドから隠蔽

### ✅ SOLID原則

- **S (Single Responsibility)**: API Client層、Repository層、ViewModel層が明確に分離
- **O (Open/Closed)**: Repositoryインターフェースで拡張に開放、変更に閉鎖
- **L (Liskov Substitution)**: モックRepositoryで置換可能（テスト容易）
- **I (Interface Segregation)**: 小さな責務ごとのインターフェース
- **D (Dependency Inversion)**: UIは抽象（coreApi）に依存、具体実装は下層

### ✅ FSD構成

```
features/navi/
  api/client.ts       ← coreApi経由のHTTP通信のみ
  repository/         ← API→Domain変換
  hooks/              ← ViewModel（状態管理・副作用）
  ui/                 ← View（純粋UI）
  model/              ← Domain型・DTO
```

## 🔨 実施した変更

### 1. フロントエンド: 統一HTTPクライアントの作成

#### 新規作成: `src/shared/infrastructure/http/coreApiClient.ts`

```typescript
export const coreApi = {
  get: <T>(path, opts?) => ...,
  post: <T>(path, body?, opts?) => ...,
  put: <T>(path, body?, opts?) => ...,
  patch: <T>(path, body?, opts?) => ...,
  delete: <T>(path, opts?) => ...,
};
```

**特徴:**

- ✅ fetch ベース（軽量、標準API）
- ✅ タイムアウト制御（デフォルト15秒）
- ✅ AbortController によるキャンセル対応
- ✅ JSON自動パース・エラーハンドリング

#### 更新: `src/shared/infrastructure/http/index.ts`

```typescript
// 🆕 推奨
export { coreApi } from './coreApiClient';

// レガシー（既存コード互換）
export { apiGet, apiPost, ... } from './httpClient';
```

### 2. Navi機能のAPI層を更新

#### 更新: `features/navi/api/client.ts`

**Before:**

```typescript
import { apiGet, apiPost } from '@shared/infrastructure/http';

async getQuestionOptions() {
  return await apiGet('/rag_api/api/question-options');
}
```

**After:**

```typescript
import { coreApi } from '@shared/infrastructure/http';

async getQuestionOptions() {
  return await coreApi.get('/core_api/rag/question-options');
}
```

**変更点:**

- ❌ `apiGet/apiPost` (axios) → ✅ `coreApi` (fetch)
- ❌ `/rag_api/...` (直接通信) → ✅ `/core_api/rag/...` (BFF経由)

### 3. バックエンド: core_api にBFFエンドポイントを追加

#### 更新: `app/backend/core_api/app/routers/chat.py`

**prefix変更:** `/chat` → `/rag`

**新規エンドポイント:**

```python
@router.get("/question-options")
async def proxy_question_options():
    # rag_api の /api/question-options にフォワード
    url = f"{RAG_API_BASE}/api/question-options"
    ...

@router.post("/generate-answer")
async def proxy_generate_answer(request: Request):
    # rag_api の /api/generate-answer にフォワード
    url = f"{RAG_API_BASE}/api/generate-answer"
    ...
```

**フォワーディング仕様:**

- `/core_api/rag/question-options` → `rag_api:8003/api/question-options`
- `/core_api/rag/generate-answer` → `rag_api:8003/api/generate-answer`

### 4. Vite設定の確認

#### `vite.config.ts` (既存)

```typescript
proxy: {
  '/core_api': {
    target: 'http://core_api:8000',
    changeOrigin: true,
    rewrite: (p) => p.replace(/^\/core_api/, ''),
  },
}
```

✅ 既に適切に設定済み（変更不要）

## 📊 通信フロー

### Before (直接通信)

```
Frontend → /rag_api/api/question-options → rag_api:8003
          (複数のエンドポイント、proxy複雑)
```

### After (BFF統一)

```
Frontend → /core_api/rag/question-options
           ↓ (Vite proxy)
         core_api:8000/rag/question-options
           ↓ (内部フォワード)
         rag_api:8003/api/question-options
```

## ✅ チェックリスト

✅ HTTPはすべて `coreApi` 経由  
✅ `/core_api/...` 以外の直fetch・axios呼び出しが存在しない (navi機能)  
✅ core_api が他サービス（rag_api）へ内部フォワード  
✅ UI・Hook・Repository の責務が明確  
✅ SOLID原則を満たす（単一責任・依存逆転）  
✅ `pnpm typecheck` → **エラー0**  
✅ `pnpm build` → **成功** (9.96s)

## 🎯 アーキテクチャの利点

### 1. 統一されたエントリーポイント

- フロントエンドは `/core_api/...` のみを意識
- マイクロサービスの変更がフロントエンドに影響しない
- proxy設定が1箇所で完結

### 2. テスタビリティの向上

- coreApi をモック化してテスト可能
- Repositoryレベルでのテスト容易
- ViewModelの単体テストが独立

### 3. 保守性の向上

- 通信ロジックが統一（coreApiClient.ts）
- エラーハンドリングが一元化
- タイムアウト制御が統一

### 4. スケーラビリティ

- 新しいバックエンドサービス追加時はcore_apiにルート追加のみ
- フロントエンドの変更不要
- BFFパターンでマイクロサービス化に対応

## 📈 Before/After 比較

| 項目              | Before                | After                  |
| ----------------- | --------------------- | ---------------------- |
| HTTP クライアント | axios + fetch 混在    | coreApi 統一           |
| エンドポイント    | `/rag_api/...`        | `/core_api/rag/...`    |
| 通信方式          | 直接通信（複数proxy） | BFF経由（統一proxy）   |
| 依存関係          | フロント→複数サービス | フロント→core_api のみ |
| 型エラー          | なし                  | **0**                  |
| ビルド            | 成功                  | **成功**               |

## 🔧 今後の拡張

### 簡単にできること

1. **新しいバックエンドサービスの追加**

   - core_api に新しいルーター追加
   - フロントエンドは coreApi.get/post を使うだけ

2. **認証・認可の一元化**

   - core_api で JWT検証
   - すべてのリクエストで統一チェック

3. **キャッシング・レート制限**

   - core_api でミドルウェア追加
   - すべてのエンドポイントに適用

4. **モニタリング・ログ**
   - core_api で統一ロギング
   - すべての通信を追跡可能

## 🚀 次のステップ

### 他の機能への適用

同じパターンを以下の機能に適用可能:

- `features/manual` → `/core_api/manual/...`
- `features/report` → `/core_api/reports/...`
- `features/forecast` → `/core_api/forecast/...`

### 段階的な移行

1. 新機能は coreApi を使用（推奨）
2. 既存機能は順次移行（apiGet/apiPost → coreApi）
3. 最終的にレガシーHTTPクライアントを廃止

---

## ✨ まとめ

**FSD + MVVM + Repository + SOLID + BFF** により、以下を達成:

✅ **統一HTTPクライアント** (coreApi)  
✅ **BFF経由の通信** (/core_api/...)  
✅ **マイクロサービスの隠蔽**  
✅ **型エラー0**  
✅ **ビルド成功**  
✅ **テスタビリティ向上**  
✅ **保守性向上**  
✅ **スケーラビリティ確保**

---

**リファクタリング完了日**: 2025年10月17日
