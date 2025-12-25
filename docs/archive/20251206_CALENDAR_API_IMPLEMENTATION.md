# Calendar API 実装完了レポート

## 概要

`ref.v_calendar_classified`ビューから営業カレンダーデータを取得し、フロントエンドに提供するAPIの実装が完了しました。

## 実装内容

### 1. バックエンドAPI (`core_api`)

**ファイル**: `app/backend/core_api/app/routers/calendar.py`

#### エンドポイント

- **URL**: `GET /api/calendar/month`
- **パラメータ**:
  - `year`: 年 (1900-2100)
  - `month`: 月 (1-12)

#### レスポンス例

```json
[
  {
    "ddate": "2025-10-01",
    "y": 2025,
    "m": 10,
    "iso_year": 2025,
    "iso_week": 40,
    "iso_dow": 3,
    "is_holiday": false,
    "is_second_sunday": false,
    "is_company_closed": false,
    "day_type": "NORMAL",
    "is_business": true
  },
  ...
]
```

#### 主な変更点

1. SQLAlchemyの`text()`関数を使用してSQLクエリを明示的に宣言
2. パラメータバインディングを`:year`、`:month`形式に変更
3. PostgreSQLの`ref.v_calendar_classified`ビューから直接データを取得

### 2. データベース構造

#### 使用ビュー

`ref.v_calendar_classified`

**カラム構成**:

- `ddate`: 日付
- `y`, `m`: 年、月
- `iso_year`, `iso_week`, `iso_dow`: ISO週番号情報
- `is_holiday`: 祝日フラグ
- `is_second_sunday`: 第2日曜日フラグ
- `is_company_closed`: 会社休業日フラグ
- `day_type`: 日タイプ (NORMAL, RESERVATION, CLOSED)
- `is_business`: 営業日フラグ

#### データ範囲

- 現在: 2025年1月 ～ 2026年12月 (730日分)

### 3. フロントエンド連携

**ファイル**: `app/frontend/src/features/dashboard/ukeire/application/adapters/calendar.http.repository.ts`

#### 実装済み機能

- `CalendarRepositoryForUkeire`クラスによるAPI呼び出し
- バックエンドレスポンスをフロントエンド用DTOにマッピング
- `coreApi.get()`を使用した統一的なAPI呼び出し

## テスト結果

### API動作確認

```bash
# 2025年10月のカレンダーデータを取得
curl "http://localhost:8003/api/calendar/month?year=2025&month=10"

# レスポンス: 31日分のカレンダーデータが正常に返却される ✓
```

### データ検証

- ✅ 営業日判定が正しく動作
- ✅ 祝日・休業日の情報が正確
- ✅ ISO週番号が正しく計算
- ✅ day_typeの分類が適切

## 運用上の注意点

### 1. データ範囲の管理

現在のカレンダーデータは2025-2026年の2年分のみです。定期的に以下の対応が必要です：

```sql
-- 新しい年のデータを追加する例
INSERT INTO ref.calendar_day (ddate, y, m, ...)
SELECT ...
FROM generate_series('2027-01-01'::date, '2027-12-31'::date, '1 day');
```

### 2. エラーハンドリング

- データが存在しない年月を指定した場合、空配列`[]`を返す
- SQLエラーの場合、500エラーとエラー詳細を返す

### 3. パフォーマンス

- 月単位でのデータ取得のため、レスポンスは高速（通常31レコード以下）
- インデックスが適切に設定されている（`calendar_day`テーブル）

## 今後の拡張案

1. **年単位取得API**

   ```
   GET /api/calendar/year?year=2025
   ```

2. **日付範囲取得API**

   ```
   GET /api/calendar/range?start=2025-10-01&end=2025-10-31
   ```

3. **営業日カウントAPI**
   ```
   GET /api/calendar/business-days?start=2025-10-01&end=2025-10-31
   ```

## 関連ファイル

### バックエンド

- `app/backend/core_api/app/routers/calendar.py` - APIルーター
- `app/backend/core_api/app/deps.py` - DB依存性注入
- `app/backend/core_api/app/app.py` - ルーター登録

### フロントエンド

- `app/frontend/src/features/dashboard/ukeire/application/adapters/calendar.http.repository.ts` - HTTPリポジトリ
- `app/frontend/src/features/calendar/model/repository.ts` - インターフェース定義
- `app/frontend/src/features/calendar/model/types.ts` - 型定義

### データベース

- `ref.v_calendar_classified` - 営業カレンダービュー
- `ref.calendar_day` - カレンダーマスターテーブル
- `ref.holiday_jp` - 日本の祝日テーブル
- `ref.v_closure_days` - 会社休業日ビュー

## 動作確認環境

- Docker Compose: `docker/docker-compose.dev.yml`
- Database: PostgreSQL 15 (sanbou_dev)
- Backend Port: 8003
- Frontend Port: 5173

---

**実装日**: 2025-10-20  
**ステータス**: ✅ 完了・動作確認済み
