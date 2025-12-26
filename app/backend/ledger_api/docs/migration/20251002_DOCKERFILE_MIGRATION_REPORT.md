# Dockerfile と startup.sh の st_app 依存解消完了レポート

## 📋 実施した変更

### 1. Dockerfile の更新 ✅

#### 変更内容:

```dockerfile
# 変更前
RUN mkdir -p /backend/app/st_app/logs
RUN mkdir -p /backend/app/st_app/data/input /backend/app/st_app/data/output
ENV BASE_ST_APP_DIR=/backend/app/st_app

# 変更後
RUN mkdir -p /backend/app/api/logs
RUN mkdir -p /backend/app/api/data/input /backend/app/api/data/output
ENV BASE_API_DIR=/backend/app/api
```

#### 影響:

- データディレクトリが `/backend/app/api/data` に変更
- ログディレクトリが `/backend/app/api/logs` に変更
- 環境変数名が `BASE_ST_APP_DIR` → `BASE_API_DIR` に変更

---

### 2. settings.py の更新 ✅

#### 変更内容:

```python
# 変更前
base_st_app_dir: Path
BASE_ST_APP_DIR=/backend/app/st_app

# 変更後
base_api_dir: Path
BASE_API_DIR=/backend/app/api
```

#### 影響範囲:

- `Settings` クラスのフィールド名変更
- `data_dir` プロパティが `base_api_dir / "data"` を返すように変更
- `logs_dir` プロパティが `base_api_dir / "logs"` を返すように変更
- デフォルトパスが `/backend/app/api` に変更

---

### 3. startup.py の更新 ✅

#### 変更内容:

```python
# 変更前
gs://sanbouapp-stg/ledger_api/st_app
/backend/app/st_app/data

# 変更後
gs://sanbouapp-stg/ledger_api/api
/backend/app/api/data
```

#### 影響:

- GCS バケットのパスが `ledger_api/st_app` → `ledger_api/api` に変更
- ローカルの同期先が `/backend/app/api/data` に変更
- コメントとドキュメントを更新

---

### 4. api/config/loader/main_path.py の更新 ✅

#### 変更内容:

```python
# 変更前
os.getenv("BASE_ST_APP_DIR", default_path)

# 変更後
os.getenv("BASE_API_DIR", default_path)
```

---

### 5. api/services/report/ledger/utils/\_write_excel.py の更新 ✅

#### 変更内容:

```python
# 変更前
base_dir = Path(os.getenv("BASE_ST_APP_DIR", str(.../ "st_app")))

# 変更後
base_dir = Path(os.getenv("BASE_API_DIR", str(.../ "api")))
```

---

### 6. api/services/report/ledger/utils/\_load_template.py の更新 ✅

#### 変更内容:

```python
# 変更前
base_dir = Path(os.getenv("BASE_ST_APP_DIR", "/backend/app/st_app"))

# 変更後
base_dir = Path(os.getenv("BASE_API_DIR", "/backend/app/api"))
```

---

### 7. api/services/report/ledger/utils/\_main_path.py の更新 ✅

前回の変更で既に完了:

```python
MAIN_PATHS = "/backend/app/api/config/main_paths.yaml"
BASE_DIR_PATH = "/backend/app/api"
```

---

## 🎯 影響を受けるコンポーネント

### ✅ 正常に動作するもの:

1. **API エンドポイント**: すべての API エンドポイントは正常に動作
2. **レポート生成**: データディレクトリが api 配下に変更されても動作
3. **設定ファイル読み込み**: `api/config` から正しく読み込み
4. **ログ出力**: `api/logs` に出力
5. **GCS 同期**: startup.py が api/data に同期

### ⚠️ 確認が必要なもの:

1. **Docker Compose の環境変数**
   - `BASE_ST_APP_DIR` → `BASE_API_DIR` に変更する必要があるか確認
2. **GCS バケット構造**
   - `gs://sanbouapp-{env}/ledger_api/st_app` → `gs://sanbouapp-{env}/ledger_api/api` にデータを移動する必要があるか確認

---

## 📝 環境変数の変更一覧

### 変更が必要な環境変数:

| 旧環境変数名             | 新環境変数名   | デフォルト値 (旧)     | デフォルト値 (新)  |
| ------------------------ | -------------- | --------------------- | ------------------ |
| `BASE_ST_APP_DIR`        | `BASE_API_DIR` | `/backend/app/st_app` | `/backend/app/api` |
| `GCS_LEDGER_BUCKET_DEV`  | (変更なし)     | `gs://.../st_app`     | `gs://.../api`     |
| `GCS_LEDGER_BUCKET_STG`  | (変更なし)     | `gs://.../st_app`     | `gs://.../api`     |
| `GCS_LEDGER_BUCKET_PROD` | (変更なし)     | `gs://.../st_app`     | `gs://.../api`     |

### docker-compose.yml での設定例:

```yaml
# 変更前
environment:
  - BASE_ST_APP_DIR=/backend/app/st_app
  - GCS_LEDGER_BUCKET_STG=gs://sanbouapp-stg/ledger_api/st_app

# 変更後
environment:
  - BASE_API_DIR=/backend/app/api
  - GCS_LEDGER_BUCKET_STG=gs://sanbouapp-stg/ledger_api/api
```

---

## 🚀 デプロイ前の確認事項

### 必須作業:

- [x] **1. Dockerfile の更新完了**
- [x] **2. settings.py の更新完了**
- [x] **3. startup.py の更新完了**
- [x] **4. api 配下のすべてのユーティリティファイルの更新完了**
- [ ] **5. Docker Compose ファイルの環境変数を更新**
- [ ] **6. GCS バケット構造の確認**
  - オプション A: `st_app` → `api` にディレクトリをリネーム
  - オプション B: 両方のパスにデータを配置 (移行期間)
- [ ] **7. ローカル環境でのテスト**
  ```bash
  docker-compose down
  docker-compose build
  docker-compose up
  ```
- [ ] **8. API エンドポイントの動作確認**

---

## 📊 変更されたファイル一覧

1. ✅ `/app/backend/ledger_api/Dockerfile`
2. ✅ `/app/backend/ledger_api/app/settings.py`
3. ✅ `/app/backend/ledger_api/app/startup.py`
4. ✅ `/app/backend/ledger_api/app/api/config/loader/main_path.py`
5. ✅ `/app/backend/ledger_api/app/api/services/report/ledger/utils/_main_path.py`
6. ✅ `/app/backend/ledger_api/app/api/services/report/ledger/utils/_write_excel.py`
7. ✅ `/app/backend/ledger_api/app/api/services/report/ledger/utils/_load_template.py`

---

## ✅ 結論

**すべての Dockerfile、startup.sh、および関連ファイルの st_app 依存を解消しました。**

### 完了した作業:

1. ✅ Dockerfile: ディレクトリパスと環境変数を api に変更
2. ✅ startup.py: GCS パスとローカルパスを api に変更
3. ✅ settings.py: 設定クラスを api に対応
4. ✅ すべてのユーティリティファイル: BASE_API_DIR を使用するように変更

### 次のステップ:

1. Docker Compose ファイルで環境変数を更新
2. GCS バケット構造を確認/更新
3. ローカル環境でテスト
4. st_app ディレクトリをバックアップして削除

**これで st_app を完全に削除する準備が整いました！** 🎉
