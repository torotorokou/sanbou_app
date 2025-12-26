# マニュアルアセット管理規則

## ファイル命名規則

### 拡張子は必ず小文字
✅ **正しい**: `m01_master_vendor.png`  
❌ **間違い**: `m01_master_vendor.PNG`

**理由**:
- Windowsでは大小文字を区別しないが、Linux/Docker/Cloud Runでは区別される
- `.PNG` で保存すると、コードが `.png` を期待している場合に404エラーが発生
- チーム開発での混乱を防ぐため、小文字に統一

### 対象拡張子
- 画像: `.png`, `.jpg`, `.jpeg`, `.webp`, `.gif`, `.svg`
- 動画: `.mp4`, `.webm`
- ドキュメント: `.md`, `.pdf`

## ディレクトリ構成

```
local_data/manuals/
├── index.json          # マニュアルカタログ（正本）
├── thumbs/             # サムネイル画像
│   ├── m01_master_vendor.png
│   ├── m02_master_unitprice.png
│   └── ...
├── videos/             # 操作動画
│   ├── m01_master_vendor.mp4
│   └── ...
├── flowcharts/         # フローチャート図
│   ├── m01_master_vendor.png
│   └── ...
└── contents/           # Markdownコンテンツ
    ├── m01_master_vendor.md
    └── ...
```

## アセット追加時の手順

### 1. ファイル名の命名
形式: `m{no}_{category}_{name}.{ext}`
- `no`: 2桁のマニュアル番号（01, 02, 11, 21...）
- `category`: カテゴリ（master, contract, manifest等）
- `name`: 具体的な名前（vendor, customer等）
- `ext`: **小文字の拡張子**

例:
```
m01_master_vendor.png     # マスター作成-業者
m11_contract_business.png # 契約書-事業系
m31_manifest_honest_out.png # マニフェスト-オネスト運搬
```

### 2. ファイル配置
該当ディレクトリに配置:
- サムネイル → `thumbs/`
- 動画 → `videos/`
- フローチャート → `flowcharts/`

### 3. index.json への登録
```json
{
  "id": "m01_master_vendor",
  "no": 1,
  "title": "業者",
  "assets": {
    "thumb": "thumbs/m01_master_vendor.png",
    "video": "videos/m01_master_vendor.mp4",
    "flowchart": "flowcharts/m01_master_vendor.png"
  }
}
```

## PowerPointからの書き出し時の注意

PowerPointは画像を `.PNG` (大文字) で保存することがあります。

### 対処方法

#### 方法1: 正規化スクリプトの使用（推奨）
```bash
# まず変更内容を確認
python -m manual_api.scripts.normalize_manual_assets --dry-run

# 問題なければ適用
python -m manual_api.scripts.normalize_manual_assets --apply
```

#### 方法2: 手動リネーム（少量の場合）
```bash
cd app/backend/manual_api/local_data/manuals/thumbs
for file in *.PNG; do mv "$file" "${file%.PNG}.png"; done
```

## 正規化スクリプトの使い方

### 基本的な使用法

#### Dry Run（変更内容の確認）
```bash
cd /path/to/sanbou_app
python -m manual_api.scripts.normalize_manual_assets --dry-run
```

出力例:
```
📁 対象ディレクトリ: /path/to/local_data/manuals
🎯 モード: Dry Run（変更なし）
📂 対象: thumbs, videos, flowcharts, contents

🔄 thumbs/ を処理中...
  📝 thumbs/m01_master_vendor.PNG → m01_master_vendor.png
  📝 thumbs/m02_master_unitprice.PNG → m02_master_unitprice.png
  ...
  27件のファイルを処理

🔄 index.json を処理中...
📝 index.json の更新予定:
  .PNG → .png (27件)

============================================================
🔍 Dry Run 結果
============================================================
リネーム対象ファイル: 27件
index.json 更新箇所: 27件
```

#### Apply（実際に変更）
```bash
python -m manual_api.scripts.normalize_manual_assets --apply
```

### オプション

#### 特定ディレクトリのみ処理
```bash
# thumbs のみ
python -m manual_api.scripts.normalize_manual_assets --apply --target thumbs

# thumbs と videos のみ
python -m manual_api.scripts.normalize_manual_assets --apply --target thumbs videos
```

#### カスタムパス指定
```bash
python -m manual_api.scripts.normalize_manual_assets --apply \
  --base-dir /custom/path/to/manuals
```

### 実行後の確認手順

1. **Gitで変更を確認**
   ```bash
   git status
   git diff app/backend/manual_api/local_data/manuals/
   ```

2. **APIで確認**
   ```bash
   # manual_api起動
   docker compose -f docker/docker-compose.dev.yml up -d manual_api
   
   # サムネイルにアクセス
   curl -I http://localhost:8005/manual-assets/thumbs/m01_master_vendor.png
   # HTTP/1.1 200 OK が返ればOK
   ```

3. **フロントエンドで確認**
   ```bash
   # ブラウザで一覧ページを開く
   http://localhost:5173/manuals/shogun
   # サムネイルが全て表示されることを確認
   ```

4. **変更をコミット**
   ```bash
   git add .
   git commit -m "normalize: マニュアルアセット拡張子を小文字に統一"
   ```

## トラブルシューティング

### Gitが大小文字の変更を検知しない

**原因**: Gitの設定によっては大小文字のみの変更を無視することがある

**対処法**:
```bash
# core.ignorecaseの確認
git config core.ignorecase
# → true の場合は検知しない可能性がある

# スクリプトは自動的に一時ファイル経由でリネームするため問題なし
# もし手動でリネームする場合:
mv file.PNG _temp_file.png
mv _temp_file.png file.png
```

### 404エラーが解消しない

1. **コンテナの再起動**
   ```bash
   docker compose -f docker/docker-compose.dev.yml restart manual_api
   ```

2. **ファイル名の確認**
   ```bash
   ls app/backend/manual_api/local_data/manuals/thumbs/
   # 拡張子が .png (小文字) になっているか確認
   ```

3. **index.json の確認**
   ```bash
   grep -i "\.PNG" app/backend/manual_api/local_data/manuals/index.json
   # 何も出力されなければOK
   ```

### スクリプト実行時のエラー

#### `ModuleNotFoundError: No module named 'manual_api'`
**原因**: Pythonパスが正しく設定されていない

**対処法**:
```bash
# リポジトリルートから実行
cd /path/to/sanbou_app

# または PYTHONPATH を設定
export PYTHONPATH="${PYTHONPATH}:app/backend"
python -m manual_api.scripts.normalize_manual_assets --dry-run
```

#### `PermissionError: [Errno 13] Permission denied`
**原因**: ファイルが読み取り専用または権限不足

**対処法**:
```bash
# 権限確認
ls -la app/backend/manual_api/local_data/manuals/thumbs/

# 必要に応じて権限変更
chmod 644 app/backend/manual_api/local_data/manuals/thumbs/*.PNG
```

## 定期メンテナンス

### 月次チェック
```bash
# 大文字拡張子が混入していないか確認
find app/backend/manual_api/local_data/manuals -name "*.PNG" -o -name "*.JPG"

# 混入していた場合は正規化
python -m manual_api.scripts.normalize_manual_assets --apply
```

### CI/CDでの自動チェック（将来的に）
```yaml
# .github/workflows/check-assets.yml
name: Check Asset Naming
on: [pull_request]
jobs:
  check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      - name: Check for uppercase extensions
        run: |
          if find app/backend/manual_api/local_data/manuals -regex ".*\.\(PNG\|JPG\|JPEG\)" | grep -q .; then
            echo "Error: Uppercase extensions found. Run normalize script."
            exit 1
          fi
```

## GCS移行時の注意事項

将来GCSに移行する際も、この命名規則は維持してください：
- GCSのオブジェクト名も大小文字を区別
- URL生成時に拡張子を小文字前提で処理するため
- 移行スクリプトでも正規化を実施すること

## 関連ドキュメント

- [マニュアルカタログ仕様](./MANUAL_CATALOG_SPEC.md)
- [マニュアルAPI監査](./MANUAL_API_AUDIT_20251226.md)
- [GCS移行計画](./MANUAL_ASSETS_MIGRATION_PLAN.md)
