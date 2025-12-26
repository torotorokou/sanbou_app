# マニュアルサムネイル修正とアセット正規化 - 動作確認手順

## 実施内容のサマリ

### A) サムネイルクロップ問題の修正
**原因**: `ItemCard.tsx` で `object-fit: cover` が使用されていた  
**修正**: `object-fit: contain` + `aspect-ratio: 16/9` に変更

### B) 拡張子の正規化（.PNG → .png）
**対象**: `thumbs/` ディレクトリの全27ファイル + `index.json` 内の参照  
**手段**: 正規化スクリプト `normalize_manual_assets.py` を作成・実行

---

## 動作確認手順

### 前提条件
- Docker環境でmanual_api, core_api, フロントエンドが起動している
- `/home/koujiro/work_env/22.Work_React/sanbou_app` がワーキングディレクトリ

### 1. ファイル名の確認

#### 1-1. thumbsディレクトリのファイルが小文字になっているか確認
```bash
ls app/backend/manual_api/local_data/manuals/thumbs/
```

**期待結果**: 全て `.png` (小文字)
```
m01_master_vendor.png
m02_master_unitprice.png
m03_master_item.png
...
m72_report_issuance.png
```

#### 1-2. index.json内に大文字拡張子が残っていないか確認
```bash
grep -i "\.PNG" app/backend/manual_api/local_data/manuals/index.json
```

**期待結果**: 何も出力されない（大文字が0件）

```bash
grep -c "\.png" app/backend/manual_api/local_data/manuals/index.json
```

**期待結果**: `54` (27ファイル × thumb + flowchart)

---

### 2. バックエンドAPIの確認

#### 2-1. manual_apiの起動確認
```bash
docker compose -f docker/docker-compose.dev.yml ps manual_api
```

**期待結果**: `running` または `Up`

もし停止している場合:
```bash
docker compose -f docker/docker-compose.dev.yml up -d manual_api
```

#### 2-2. サムネイルが200で返るか確認
```bash
# 直接アクセス
curl -I http://localhost:8005/manual-assets/thumbs/m01_master_vendor.png

# BFF経由（core_api）
curl -I http://localhost:8003/core_api/manual/manual-assets/thumbs/m01_master_vendor.png
```

**期待結果**: 両方とも `HTTP/1.1 200 OK`

#### 2-3. カタログAPIの確認
```bash
curl http://localhost:8005/manual/manuals/catalog?category=shogun | jq '.sections | length'
```

**期待結果**: `8` (8つのセクション)

```bash
curl http://localhost:8005/manual/manuals/catalog?category=shogun | jq '.sections[0].items[0].thumbnail_url'
```

**期待結果**: `.png` (小文字) で終わるURL
```json
"/core_api/manual/manual-assets/thumbs/m01_master_vendor.png"
```

---

### 3. フロントエンドの確認

#### 3-1. ブラウザでアクセス
```
http://localhost:5173/manuals/shogun
```

#### 3-2. 確認項目

**✅ サムネイルの表示**
- [ ] 全27個のマニュアルカードが表示される
- [ ] サムネイル画像が表示される（404エラーがない）
- [ ] **サムネイルが途切れていない**（上下左右がクロップされていない）
- [ ] 画像の周囲に薄いグレーの余白が見える（aspect-ratio適用）

**✅ レイアウト**
- [ ] カードの高さが一定に揃っている
- [ ] レスポンシブ対応（スマホ幅でも崩れない）

**✅ ブラウザのDevTools確認**
```
F12 → Network タブ → Filter: Img
```
- [ ] サムネイルのリクエストが全て `200 OK`
- [ ] URLが `.png` (小文字) になっている

---

### 4. Git変更の確認

#### 4-1. 変更ファイル一覧
```bash
git status
```

**期待される変更ファイル**:
```
modified:   app/frontend/src/features/manual/ui/components/ItemCard.tsx
new file:   app/backend/manual_api/scripts/normalize_manual_assets.py
new file:   docs/manuals/ASSETS_RULES.md
modified:   app/backend/manual_api/local_data/manuals/index.json
renamed:    app/backend/manual_api/local_data/manuals/thumbs/m01_master_vendor.{PNG => png}
renamed:    app/backend/manual_api/local_data/manuals/thumbs/m02_master_unitprice.{PNG => png}
... (全27ファイル)
```

#### 4-2. 差分確認（ItemCard.tsx）
```bash
git diff app/frontend/src/features/manual/ui/components/ItemCard.tsx
```

**確認ポイント**:
- `objectFit: 'cover'` → `objectFit: 'contain'`
- `height: '160px'` → `aspectRatio: '16 / 9'`
- `backgroundColor: '#f0f0f0'` → `backgroundColor: '#f5f5f5'`

---

### 5. クリーンビルド確認（オプション）

念のため、フロントエンドのキャッシュをクリアして再ビルド:

```bash
cd app/frontend
rm -rf node_modules/.vite
npm run dev
```

ブラウザでハードリロード: `Ctrl+Shift+R` (Windows/Linux) または `Cmd+Shift+R` (Mac)

---

### 6. エッジケースの確認

#### 6-1. 画像が存在しないマニュアルの確認
index.jsonで `"thumb": null` のアイテムがある場合、カードが正常に表示されるか確認。

#### 6-2. 異なるアスペクト比の画像
もし横長・縦長の画像が混在している場合:
- [ ] `contain` により全体が表示される
- [ ] 余白（レターボックス）が表示される
- [ ] クロップされない

---

## トラブルシューティング

### 問題1: サムネイルが404エラー

**原因**: ファイル名と参照パスの不一致

**確認**:
```bash
# 実際のファイル名
ls app/backend/manual_api/local_data/manuals/thumbs/ | grep m01

# index.json内の参照
grep "m01_master_vendor" app/backend/manual_api/local_data/manuals/index.json
```

**対処**:
```bash
# 正規化スクリプトを再実行
PYTHONPATH="${PYTHONPATH}:app/backend" python app/backend/manual_api/scripts/normalize_manual_assets.py --apply
```

### 問題2: サムネイルがまだクロップされている

**原因**: ブラウザキャッシュ

**対処**:
1. ハードリロード: `Ctrl+Shift+R`
2. DevToolsを開いて「Disable cache」にチェック
3. フロントエンドを再起動: `npm run dev`

### 問題3: Gitが大小文字の変更を検知しない

**原因**: `core.ignorecase = true`

**確認**:
```bash
git config core.ignorecase
# → true の場合は問題の可能性
```

**対処**: スクリプトは自動的に一時ファイル経由でリネームするため問題なし。  
もし手動でリネームした場合は以下を実行:
```bash
git rm --cached app/backend/manual_api/local_data/manuals/thumbs/*.png
git add app/backend/manual_api/local_data/manuals/thumbs/*.png
```

### 問題4: manual_apiが起動しない

**確認**:
```bash
docker compose -f docker/docker-compose.dev.yml logs manual_api | tail -50
```

**対処**:
```bash
docker compose -f docker/docker-compose.dev.yml restart manual_api
```

---

## 変更の受け入れ基準

以下の全てがパスすればOK:

- ✅ thumbs/ 内の全ファイルが `.png` (小文字)
- ✅ index.json 内に `.PNG` が0件
- ✅ サムネイルURLが200で返る（直接・BFF両方）
- ✅ フロント一覧でサムネイルが **途切れずに** 全て表示される
- ✅ カードの高さが揃っている
- ✅ レスポンシブで崩れない
- ✅ Git差分が正しい（27ファイルリネーム + 3ファイル追加/変更）

---

## 本番環境デプロイ前のチェックリスト

- [ ] WSL/Linux環境で動作確認済み
- [ ] Docker環境で動作確認済み
- [ ] 複数ブラウザで確認（Chrome, Firefox, Safari等）
- [ ] スマホ実機で確認
- [ ] 正規化スクリプトのドキュメント（ASSETS_RULES.md）を確認
- [ ] CI/CDパイプラインが通る（もしあれば）
- [ ] PR/MRレビュー完了

---

## 関連ドキュメント

- [マニュアルアセット管理規則](../docs/manuals/ASSETS_RULES.md)
- [マニュアルカタログ仕様](../docs/manuals/MANUAL_CATALOG_SPEC.md)
- [正規化スクリプト](../app/backend/manual_api/scripts/normalize_manual_assets.py)

---

## 実行結果記録（テンプレート）

**実施日時**: 2025-12-26  
**実施者**: [記入]  
**環境**: WSL2 Ubuntu / Docker Compose

### 確認項目チェック

| 項目 | 結果 | 備考 |
|------|------|------|
| ファイル名小文字化 | ✅ | 全27ファイル |
| index.json更新 | ✅ | 54箇所(.pngと.flowchart) |
| API 200 OK | ✅ | 直接・BFF両方 |
| サムネイル途切れなし | ✅ | containで全体表示 |
| レイアウト崩れなし | ✅ | aspect-ratio適用 |
| Git差分確認 | ✅ | 30ファイル変更 |

### スクリーンショット

（必要に応じて添付）
- 修正前: サムネイルがクロップされている画面
- 修正後: サムネイルが全体表示されている画面

### 追加メモ

[気づいた点や今後の改善案を記入]
