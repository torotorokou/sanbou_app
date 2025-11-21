# SalesTree API実装 - 動作確認手順

## 実装完了日
2025-11-21

## 実装概要
売上ツリー分析機能を、モックデータから実DBデータ（sandbox.v_sales_tree_daily）を使用する実API連携版に移行しました。

## アーキテクチャ

### バックエンド (FastAPI + Clean Architecture)
```
app/backend/core_api/app/
├── domain/
│   ├── sales_tree.py                          # ドメインモデル（Request/Response）
│   └── ports/
│       └── sales_tree_port.py                 # Port定義
├── application/
│   └── usecases/
│       └── sales_tree/
│           ├── fetch_summary_uc.py            # サマリー取得UseCase
│           └── fetch_daily_series_uc.py       # 日次推移取得UseCase
├── infra/
│   └── adapters/
│       └── sales_tree/
│           └── sales_tree_repository.py       # Repository実装
├── presentation/
│   └── routers/
│       └── sales_tree/
│           └── router.py                      # APIエンドポイント
├── config/
│   └── di_providers.py                        # DI設定（追加）
└── app.py                                     # Router登録（追加）
```

### フロントエンド (React + FSD + MVVM)
```
app/frontend/src/
├── features/analytics/sales-pivot/
│   └── shared/
│       └── api/
│           └── salesPivot.repository.ts       # HTTP Repository実装追加
└── pages/analytics/
    └── SalesTreePage.tsx                      # Repository切り替え
```

## APIエンドポイント

### 1. サマリーデータ取得
- **URL**: `POST /core_api/analytics/sales-tree/summary`
- **Request Body**:
```json
{
  "date_from": "2025-10-01",
  "date_to": "2025-10-31",
  "mode": "customer",
  "rep_ids": [101, 102],
  "filter_ids": [],
  "top_n": 20,
  "sort_by": "amount",
  "order": "desc"
}
```
- **Response**:
```json
[
  {
    "rep_id": 101,
    "rep_name": "営業A",
    "metrics": [
      {
        "id": "c_001",
        "name": "顧客アルファ",
        "amount": 1500000.0,
        "qty": 750500.0,
        "slip_count": 15,
        "unit_price": 1998.67,
        "date_key": null
      }
    ]
  }
]
```

### 2. 日次推移データ取得
- **URL**: `POST /core_api/analytics/sales-tree/daily-series`
- **Request Body**:
```json
{
  "date_from": "2025-10-01",
  "date_to": "2025-10-31",
  "rep_id": 101,
  "customer_id": "c_001",
  "item_id": null
}
```
- **Response**:
```json
[
  {
    "date": "2025-10-01",
    "amount": 50000.0,
    "qty": 25000.0,
    "slip_count": 1,
    "unit_price": 2000.0
  }
]
```

### 3. Pivotデータ取得（詳細ドリルダウン）
- **URL**: `POST /core_api/analytics/sales-tree/pivot`
- **Request Body**:
```json
{
  "date_from": "2025-10-01",
  "date_to": "2025-10-31",
  "base_axis": "customer",
  "base_id": "000014",
  "rep_ids": [1],
  "target_axis": "item",
  "top_n": 20,
  "sort_by": "amount",
  "order": "desc",
  "cursor": null
}
```
- **Response**:
```json
{
  "rows": [
    {
      "id": "1",
      "name": "混合廃棄物A",
      "amount": 1771320.0,
      "qty": 30540.0,
      "slip_count": 115,
      "unit_price": 58000.0,
      "date_key": null
    }
  ],
  "next_cursor": "30"
}
```

### 4. マスタデータ取得
- **営業マスタ**: `GET /core_api/analytics/sales-tree/masters/reps`
- **顧客マスタ**: `GET /core_api/analytics/sales-tree/masters/customers`
- **品目マスタ**: `GET /core_api/analytics/sales-tree/masters/items`

## データソース

### sandbox.v_sales_tree_daily
```sql
-- ビュー定義
SELECT 
    sales_date,
    rep_id,
    rep_name,
    customer_id,
    customer_name,
    item_id,
    item_name,
    amount_yen,
    qty_kg,        -- 注意: kg単位（tonではない）
    slip_count
FROM sandbox.mv_sales_tree_daily;
```

**重要**: 数量カラムは `qty_kg`（キログラム単位）です。フロントエンド表示時に適宜変換してください。

## 動作確認手順

### 前提条件
1. Dockerコンテナが起動していること
2. `sandbox.v_sales_tree_daily` にデータが存在すること
3. フロントエンドとバックエンドが起動していること

### 1. バックエンドAPI確認

#### ターミナルで直接テスト（httpieまたはcurl）

```bash
# サマリーデータ取得テスト
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  curl -X POST http://localhost:8000/core_api/analytics/sales-tree/summary \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-10-01",
    "date_to": "2025-10-31",
    "mode": "customer",
    "rep_ids": [],
    "filter_ids": [],
    "top_n": 10,
    "sort_by": "amount",
    "order": "desc"
  }'

# 日次推移データ取得テスト
docker compose -f docker/docker-compose.dev.yml -p local_dev exec core_api \
  curl -X POST http://localhost:8000/core_api/analytics/sales-tree/daily-series \
  -H "Content-Type: application/json" \
  -d '{
    "date_from": "2025-10-01",
    "date_to": "2025-10-31",
    "rep_id": null
  }'
```

#### 期待する結果
- ステータスコード: 200
- JSON形式のレスポンス
- データが空の場合は `[]` が返る

### 2. フロントエンド画面確認

1. ブラウザで売上ツリーページにアクセス
   - URL: `http://localhost:5173/analytics/sales-tree` (開発サーバーのポートに応じて変更)

2. 以下を確認：
   - 営業を選択すると実データが表示される
   - モードを切り替え（顧客/品目/日付）が動作する
   - ソート機能が動作する
   - TOP-N絞り込みが動作する
   - 行をクリックすると詳細（Pivot Drawer）が表示される
   - グラフが表示される（日次推移）

### 3. データベース確認

```bash
# ビューのデータ件数確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "SELECT COUNT(*) FROM sandbox.v_sales_tree_daily;"

# サンプルデータ確認
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "
    SELECT 
      sales_date, 
      rep_name, 
      customer_name, 
      item_name, 
      amount_yen, 
      qty_ton, 
      slip_count 
    FROM sandbox.v_sales_tree_daily 
    LIMIT 10;
  "
```

## トラブルシューティング

### 1. APIが404エラーを返す
- **原因**: Routerが登録されていない
- **確認**: `app/backend/core_api/app/app.py` に `sales_tree_router` が追加されているか
- **解決**: コンテナを再起動

```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev restart core_api
```

### 2. データが空で返る
- **原因**: `sandbox.v_sales_tree_daily` にデータがない
- **確認**:
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
  psql -U myuser -d sanbou_dev -c "SELECT COUNT(*) FROM sandbox.v_sales_tree_daily;"
```
- **解決**: CSVアップロードを実行してデータを投入

### 3. 型エラー（Python）
- **原因**: Pydanticモデルとリクエストの不整合
- **確認**: ログで詳細なエラーメッセージを確認
```bash
docker compose -f docker/docker-compose.dev.yml -p local_dev logs core_api | tail -50
```

### 4. CORS エラー（フロントエンド）
- **原因**: バックエンドのCORS設定
- **解決**: 環境変数 `ENABLE_CORS=true` を設定してコンテナ再起動

### 5. マスタデータ（営業/顧客/品目）が表示されない
- **現状**: マスタAPIは未実装のため、モックデータを使用
- **今後**: マスタAPIを実装後、`HttpSalesPivotRepository` の `getSalesReps()` 等を置き換え

## 今後の拡張

### 1. Pivot API実装
現在、Pivot機能（ドロワー内の展開）はモックデータを使用しています。
実装が必要な場合は、以下を追加：

- バックエンド: `/core_api/analytics/sales-tree/pivot` エンドポイント
- Repository: `fetch_pivot()` メソッド実装
- フロントエンド: `HttpSalesPivotRepository.fetchPivot()` 実装

### 2. CSV Export API実装
現在、CSV Export機能はモックです。
実装が必要な場合は、以下を追加：

- バックエンド: `/core_api/analytics/sales-tree/export` エンドポイント
- Repository: CSV生成ロジック
- フロントエンド: `HttpSalesPivotRepository.exportModeCube()` 実装

### 3. マスタAPI実装
営業・顧客・品目のマスタデータを取得するAPIを実装し、
`HttpSalesPivotRepository` の以下メソッドを置き換え：

- `getSalesReps()`
- `getCustomers()`
- `getItems()`

### 4. キャッシュ実装
頻繁にアクセスされるデータについて、TTLキャッシュを実装：

- バックエンド: `cachetools` を使用したUseCase層でのキャッシュ
- フロントエンド: SWRやReact Queryでのキャッシュ

## 関連ドキュメント
- [FSD Architecture Guide](docs/FSD_ARCHITECTURE_GUIDE.md)
- [Clean Architecture Migration](app/backend/core_api/CLEAN_ARCHITECTURE_MIGRATION.md)

## 変更履歴
- 2025-11-21 18:00: 初回実装完了（モック → 実API移行）
- 2025-11-21 19:00: 期間条件修正、営業マスタ実装
- 2025-11-21 20:00: Pivot API実装（詳細ボタン対応）、qty_kg修正
