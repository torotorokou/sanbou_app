# 帳簿エラーハンドリング改善レポート

## 概要

帳簿作成処理（ledger_api の各エンドポイント）において、エラーが発生した際にフロントエンドに適切に通知されず、フリーズしたような状態になる問題を修正しました。

## 修正内容

### 1. バックエンド: DomainError への統一

#### 修正ファイル

- `app/backend/ledger_api/app/api/services/report/core/processors/report_processing_service.py`
- `app/backend/ledger_api/app/api/services/report/core/processors/interactive_report_processing_service.py`
- `app/backend/ledger_api/app/api/endpoints/reports/block_unit_price_interactive.py`

#### 変更内容

**report_processing_service.py:**

- すべての例外を `DomainError` に変換し、ProblemDetails形式でレスポンス
- `format()` のエラー → `REPORT_FORMAT_ERROR`
- `main_process()` のエラー → `REPORT_PROCESSING_ERROR`
- 予期しないエラー → `REPORT_GENERATION_ERROR`

```python
# Before (汎用JSONエラー)
return JSONResponse(
    status_code=500,
    content={
        "status": "error",
        "message": "Internal Server Error during report processing.",
        "detail": str(e),
    },
)

# After (DomainErrorでProblemDetails化)
raise DomainError(
    code="REPORT_GENERATION_ERROR",
    status=500,
    user_message=f"帳票の生成中にエラーが発生しました: {str(e)}",
    title="帳票生成エラー"
) from e
```

**interactive_report_processing_service.py:**

- インタラクティブ処理のエラーも `DomainError` に統一
- `apply()` のエラー → `INTERACTIVE_APPLY_FAILED`
- `finalize()` のエラー → `INTERACTIVE_FINALIZE_ERROR`
- `auto_finalize` のエラー → `AUTO_FINALIZE_FAILED`
- セッション未検出 → `SESSION_NOT_FOUND`

**block_unit_price_interactive.py:**

- `HTTPException` から `DomainError` に変更
- すべてのエンドポイント (`/initial`, `/apply`, `/finalize`, `/status/{step}`) で統一

```python
# Before
raise HTTPException(status_code=400, detail="session_id が指定されていません")

# After
raise DomainError(
    code="INPUT_INVALID",
    status=400,
    user_message="session_id が指定されていません",
    title="入力エラー"
)
```

### 2. フロントエンド: エラーコードカタログの拡張

#### 修正ファイル

- `app/frontend/src/features/notification/config.ts`

#### 追加したエラーコード

```typescript
// 帳票生成エラー
REPORT_GENERATION_ERROR: { severity: 'error', title: '帳票生成エラー' },
REPORT_PROCESSING_ERROR: { severity: 'error', title: '帳票処理エラー' },
REPORT_FORMAT_ERROR: { severity: 'error', title: 'データ整形エラー' },
INTERACTIVE_APPLY_FAILED: { severity: 'error', title: '処理エラー' },
INTERACTIVE_FINALIZE_ERROR: { severity: 'error', title: '最終計算エラー' },
AUTO_FINALIZE_FAILED: { severity: 'error', title: '自動計算エラー' },
SESSION_NOT_FOUND: { severity: 'warning', title: 'セッションエラー' },
```

## エラーフロー

### 修正前

```
帳簿処理でエラー発生
  ↓
汎用JSONエラー返却 (status: 500, message: "...")
  ↓
フロントエンドがエラーを適切に処理できない
  ↓
ローディング状態のままフリーズ
```

### 修正後

```
帳簿処理でエラー発生
  ↓
DomainError として raise
  ↓
FastAPI のエラーハンドラが ProblemDetails に変換
  ↓
{
  "status": 500,
  "code": "REPORT_PROCESSING_ERROR",
  "userMessage": "帳票の計算処理中にエラーが発生しました: ...",
  "title": "帳票処理エラー",
  "traceId": "xxx-xxx-xxx"
}
  ↓
axios インターセプターが ApiError に変換
  ↓
notifyApiError() が自動的にエラー通知を表示
  ↓
ユーザーに適切なエラーメッセージが表示される
```

## 影響範囲

### 修正された帳票エンドポイント

- `/ledger_api/reports/factory_report` - 工場日報
- `/ledger_api/reports/balance_sheet` - 工場搬出入収支表
- `/ledger_api/reports/average_sheet` - 工場平均表
- `/ledger_api/reports/management_sheet` - 管理票
- `/ledger_api/reports/block_unit_price/initial` - ブロック単価初期処理
- `/ledger_api/reports/block_unit_price/apply` - 運搬業者選択適用
- `/ledger_api/reports/block_unit_price/finalize` - ブロック単価最終計算
- `/ledger_api/reports/block_unit_price/status/{step}` - ステップ情報取得

### 改善されたユーザー体験

1. **エラーの可視化**: エラーが発生すると即座に通知が表示される
2. **詳細なエラー情報**: traceId とともに、具体的なエラー内容が表示される
3. **一貫したエラーハンドリング**: すべての帳票エンドポイントで統一された方式
4. **フリーズ問題の解消**: エラー時もローディングが適切に終了する

## テスト方法

### 1. CSVエラーのテスト

```bash
# 不正なCSVファイルをアップロードし、エラー通知が表示されることを確認
curl -X POST http://localhost:8001/ledger_api/reports/factory_report \
  -F "shipment=@invalid.csv" \
  -F "yard=@test.csv"
```

### 2. 処理エラーのテスト

```bash
# 必須カラムが欠けたCSVで帳票生成を試み、適切なエラーが返ることを確認
```

### 3. セッションエラーのテスト

```bash
# 無効なsession_idでブロック単価計算を試み、SESSION_NOT_FOUNDエラーが返ることを確認
curl -X POST http://localhost:8001/ledger_api/reports/block_unit_price/finalize \
  -H "Content-Type: application/json" \
  -d '{"session_id": "invalid-session-id"}'
```

## 既存の契約との整合性

### ProblemDetails契約 (RFC 7807準拠)

すべてのエラーは以下のフォーマットで返却されます:

```typescript
interface ProblemDetails {
  status: number; // HTTPステータスコード
  code: string; // エラーコード (例: "REPORT_PROCESSING_ERROR")
  userMessage: string; // ユーザー向けメッセージ
  title?: string; // エラータイトル (例: "帳票処理エラー")
  traceId?: string; // リクエストトレースID
}
```

### 自動エラー通知

すべての帳票APIエラーは自動的に以下のように処理されます:

1. **axios インターセプター** → `ApiError` クラスに変換
2. **notifyApiError()** → code から適切な severity と title を自動選択
3. **通知表示** → エラー内容を6秒間表示（NOTIFY_DEFAULTS.error）

## 今後の改善提案

### 1. より具体的なエラーコード

- `MISSING_REQUIRED_COLUMN` - 必須カラム不足
- `INVALID_DATE_FORMAT` - 日付フォーマット不正
- `CALCULATION_OVERFLOW` - 計算オーバーフロー

### 2. エラー詳細モーダル

- traceId をコピー可能にする
- エラーの技術的詳細を表示
- サポート連絡先を表示

### 3. エラーロギング

- Sentry/DataDog などの監視ツールへの統合
- traceId ベースの分散トレーシング

## まとめ

この修正により、帳簿作成エラーが発生した際に:

- ✅ フロントエンドに適切なエラー通知が表示される
- ✅ フリーズ問題が解消される
- ✅ traceId によるエラー追跡が可能になる
- ✅ すべてのエラーがProblemDetails形式で統一される
- ✅ 既存の通知システム（NL1-NL11）との完全な統合が実現される
