# BFF-プロキシ アーキテクチャ

## 概要

本システムは **BFF (Backend For Frontend)** パターンを採用し、フロントエンドと帳票生成API間の疎結合を実現しています。

## アーキテクチャ図

```
フロントエンド (React + Vite)
    ↓ /core_api/reports/*
Vite Dev Server (開発) / Caddy (本番)
    ↓ proxy: /core_api → http://core_api:8000
core_api (BFF Layer)
    ↓ /reports/*
ledger_api (Business Logic)
```

## レイヤー責務

### 1. フロントエンド

- **URL**: `/core_api/reports/...`, `/core_api/block_unit_price_interactive/...`
- **責務**: ユーザーインターフェース、入力検証、レポート表示
- **特徴**: 常に `/core_api` プレフィックスでAPIを呼び出す

### 2. Vite Dev Server / Caddy

- **責務**: プロキシ設定
- **開発環境 (Vite)**:
  ```ts
  server: {
    proxy: {
      '/core_api': {
        target: 'http://core_api:8000',
        changeOrigin: true,
        rewrite: (p) => p.replace(/^\/core_api/, ''),
      },
    },
  }
  ```
- **本番環境 (Caddy)**:
  ```
  handle /core_api* {
    reverse_proxy core_api:8000
  }
  ```

### 3. core_api (BFF)

- **URL**: `/reports/*`, `/block_unit_price_interactive/*`
- **責務**:
  - リクエストの転送（HTTP proxy）
  - URL rewriting（内部パス → 外部パス）
  - 認証・認可（将来実装）
  - ヘッダー透過
  - ストリーミング
- **特徴**:
  - ビジネスロジックを持たない薄い窓口
  - ledger_apiへのHTTPクライアント
  - `rewrite_artifact_urls_to_bff()` で `/reports/artifacts/...` → `/core_api/reports/artifacts/...`

**主要ファイル**:

- `app/backend/core_api/app/routers/reports.py`
- `app/backend/core_api/app/routers/block_unit_price.py`

**エンドポイント例**:

```python
# 工場日報
@router.post("/factory_report/")
async def proxy_factory_report(request: Request):
    # FormDataをledger_apiに転送
    url = f"{LEDGER_API_BASE}/reports/factory_report/"
    r = await client.post(url, data=data, files=files)
    return rewrite_artifact_urls_to_bff(r.json())
```

### 4. ledger_api (Business Logic)

- **URL**: `/reports/*`, `/block_unit_price_interactive/*`（内部論理パス）
- **責務**:
  - 帳票生成（Excel/PDF）
  - データ処理
  - ファイルアップロード処理
  - 署名付きURL生成
- **特徴**:
  - `/core_api` の存在を知らない（DIP: 依存関係逆転の原則）
  - 内部論理パスのみで動作
  - `REPORT_ARTIFACT_URL_PREFIX=/reports/artifacts` を返す

**主要ファイル**:

- `app/backend/ledger_api/app/main.py`
- `app/backend/ledger_api/app/api/endpoints/reports/*.py`

**エンドポイント例**:

```python
# ルーター登録（内部論理パス）
app.include_router(reports_router, prefix="/reports")
app.include_router(block_unit_price_router, prefix="/block_unit_price_interactive")
```

## URL変換フロー

### 帳票生成リクエスト

1. **フロントエンド**: `POST /core_api/reports/factory_report/`
2. **Viteプロキシ**: → `http://core_api:8000/reports/factory_report/`
3. **core_api BFF**: → `http://ledger_api:8000/reports/factory_report/`
4. **ledger_api**: 帳票生成 → レスポンス返却

### アーティファクトURLの変換

**ledger_apiからのレスポンス**:

```json
{
  "artifact": {
    "excel_download_url": "/reports/artifacts/factory_report/2025-10-17/token123/report.xlsx",
    "pdf_preview_url": "/reports/artifacts/factory_report/2025-10-17/token123/report.pdf"
  }
}
```

**core_api BFFでの変換** (`rewrite_artifact_urls_to_bff()`):

```json
{
  "artifact": {
    "excel_download_url": "/core_api/reports/artifacts/factory_report/2025-10-17/token123/report.xlsx",
    "pdf_preview_url": "/core_api/reports/artifacts/factory_report/2025-10-17/token123/report.pdf"
  }
}
```

**フロントエンド**: `/core_api/reports/artifacts/...` でファイル取得

## DIP (依存関係逆転の原則)

### 原則

- **上位レイヤー（core_api）が下位レイヤー（ledger_api）を知る**: ✅ OK
- **下位レイヤー（ledger_api）が上位レイヤー（core_api）を知る**: ❌ NG

### 実装

- ledger_apiは `/core_api` プレフィックスの存在を知らない
- ledger_apiは内部論理パス（`/reports/...`）のみを返す
- core_apiがプレフィックスを付与する責務を持つ

## 環境変数

### core_api

```bash
LEDGER_API_BASE=http://ledger_api:8000  # ledger_apiのベースURL
```

### ledger_api

```bash
REPORT_ARTIFACT_URL_PREFIX=/reports/artifacts  # 内部論理パス
REPORT_ARTIFACT_ROOT_DIR=/tmp/reports          # ファイル保存先
REPORT_ARTIFACT_URL_TTL=900                    # URL有効期限（秒）
```

## メリット

1. **疎結合**: フロントエンドとledger_apiが独立して変更可能
2. **単一責任**: 各レイヤーが明確な責務を持つ
3. **テスト容易性**: 各レイヤーを独立してテスト可能
4. **スケーラビリティ**: core_apiとledger_apiを独立してスケール可能
5. **セキュリティ**: core_apiで認証・認可を一元管理（将来）

## 今後の拡張

- [ ] core_apiでJWT認証を実装
- [ ] レート制限（Rate Limiting）
- [ ] リクエストロギング・監査
- [ ] キャッシュレイヤー
- [ ] A/Bテスト用のルーティング

## トラブルシューティング

### 404エラー（Artifact not found）

- **原因**: URLに `/core_api` プレフィックスが付いていない
- **確認**: `rewrite_artifact_urls_to_bff()` が呼ばれているか
- **修正**: BFFエンドポイントで `return rewrite_artifact_urls_to_bff(r.json())`

### 500エラー（ECONNREFUSED）

- **原因**: core_apiがledger_apiに接続できない
- **確認**: `LEDGER_API_BASE` 環境変数の値
- **修正**: `http://ledger_api:8000` に設定（Dockerサービス名を使用）

### 422エラー（Validation Error）

- **原因**: CSVファイルの形式が不正
- **確認**: 必須カラムが含まれているか
- **対処**: エラーメッセージを確認して必要なカラムを追加

## 参考資料

- [BFF Pattern - Microsoft](https://docs.microsoft.com/en-us/azure/architecture/patterns/backends-for-frontends)
- [Dependency Inversion Principle (DIP)](https://en.wikipedia.org/wiki/Dependency_inversion_principle)
- [FastAPI Proxy Pattern](https://fastapi.tiangolo.com/advanced/custom-request-and-route/)
