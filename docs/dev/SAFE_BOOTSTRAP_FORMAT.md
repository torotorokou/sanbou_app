# 安全な初回整形ガイド（WSL2 フリーズ防止）

## 📖 概要

このドキュメントは、**WSL2 + VSCode Remote-WSL 環境**で、リポジトリ全体の整形を**フリーズさせずに**実行する方法を説明します。

## ⚠️ 問題：なぜフリーズするのか？

### フリーズの原因

1. **巨大ディレクトリの監視**
   - `app/frontend/node_modules/`: 564MB（約24万ファイル）
   - `data/`: 451MB
   - `.venv/`: 318MB
   - → VSCode のファイル監視で CPU 張り付き

2. **全体スキャン系コマンド**
   - `pre-commit run --all-files` → すべてのファイルをスキャン
   - `eslint .` → node_modules も検索対象
   - `prettier .` → 全ファイルを走査
   - → CPU 100% → VSCode 再接続ループ

3. **並列実行の負荷**
   - pre-commit は複数のツールを並列実行
   - ruff + black + prettier + eslint が同時に動く
   - → メモリ不足・CPU 張り付き

### 根拠

- リポジトリ調査結果：
  ```bash
  $ du -sh app/frontend/node_modules app/frontend/dist data .venv
  564M    app/frontend/node_modules
  7.9M    app/frontend/dist
  451M    data
  318MB   .venv
  ```

- VSCode のファイル監視対象：
  - デフォルトでは上記ディレクトリもすべて監視
  - `.vscode/settings.json` で除外設定が必須

---

## ✅ 解決策：直列・対象限定の実行

### 方針

1. **pre-commit は使わない**（初回整形時）
2. **各ツールを直列に実行**（並列負荷を避ける）
3. **対象ディレクトリを限定**（node_modules/data を除外）
4. **nice コマンドで優先度を下げる**（CPU 負荷軽減）

### 実行順序（固定）

```
1. Python: ruff --fix（import整形 & lint自動修正）
2. Python: black（コード整形）
3. Frontend: prettier --write（コード整形）
4. Frontend: eslint --fix（lint自動修正）
```

---

## 🚀 実行方法

### 方法1：Makefile（推奨）

```bash
# 全体整形（直列・対象限定）
make fmt-step-all
```

このコマンドは以下を順次実行します：

```bash
make fmt-step-py-fix   # Python ruff --fix
make fmt-step-py       # Python black
make fmt-step-fe       # Frontend prettier
make fmt-step-fe-fix   # Frontend eslint --fix
```

### 方法2：スクリプト直接実行

```bash
bash scripts/format_step_by_step.sh all
```

### 方法3：個別ステップ実行

途中で止まった場合や、特定の処理だけ実行したい場合：

```bash
# Python のみ
make fmt-step-py-fix   # ruff --fix
make fmt-step-py       # black

# Frontend のみ
make fmt-step-fe       # prettier
make fmt-step-fe-fix   # eslint --fix
```

---

## 📋 実行前の準備

### 1. VSCode 設定の確認

`.vscode/settings.json` が最新であることを確認：

```bash
git pull origin main
```

以下の設定が含まれているはずです：
- `files.watcherExclude`: 巨大ディレクトリの監視除外
- `search.exclude`: 検索対象の除外
- `typescript.tsserver.maxTsServerMemory`: 4096

### 2. Docker コンテナの起動

Python の整形には Docker コンテナが必要です：

```bash
make up ENV=local_dev
```

### 3. ブランチの作成（推奨）

大量の差分が出るため、専用ブランチで作業：

```bash
git checkout -b chore/initial-format
```

---

## ⚙️ 実行の流れ（詳細）

### Step 1: Python ruff --fix

```bash
make fmt-step-py-fix
```

**内容**：
- import の整形
- lint エラーの自動修正
- 対象：`app/backend/` （migrations 除外）

**所要時間**：約30秒〜1分

**注意**：
- 一部のエラーは自動修正できない（手動修正が必要）
- エラーが出ても次のステップに進む

### Step 2: Python black

```bash
make fmt-step-py
```

**内容**：
- コードの整形
- 対象：`app/backend/` （migrations 除外）

**所要時間**：約20秒〜40秒

**注意**：
- black は常に成功する（エラーなし）

### Step 3: Frontend prettier

```bash
make fmt-step-fe
```

**内容**：
- コードの整形
- 対象：`app/frontend/src/**/*.{ts,tsx,js,jsx,json,css}`

**所要時間**：約30秒〜1分

**注意**：
- node_modules は自動的に除外される

### Step 4: Frontend eslint --fix

```bash
make fmt-step-fe-fix
```

**内容**：
- lint エラーの自動修正
- 対象：`app/frontend/src/**/*.{ts,tsx,js,jsx}`

**所要時間**：約1分〜2分

**注意**：
- 一部のエラーは自動修正できない（警告として表示）

---

## 🔄 途中で止めた場合の再開方法

### 状況1：Step 2 で止まった

```bash
# Step 2 から再開
make fmt-step-py        # black
make fmt-step-fe        # prettier
make fmt-step-fe-fix    # eslint
```

### 状況2：Step 3 で止まった

```bash
# Step 3 から再開
make fmt-step-fe        # prettier
make fmt-step-fe-fix    # eslint
```

### 状況3：エラーで止まった

1. エラーメッセージを確認
2. 手動で修正が必要なファイルがある場合は修正
3. 次のステップから再開

---

## 📊 実行結果の確認

### 成功の確認

全ステップが完了したら、以下のコマンドで確認：

```bash
make fmt-step-check
```

**期待される結果**：
- Python ruff: ✅ Passed
- Python black: ✅ Passed
- Frontend prettier: ✅ Passed
- Frontend eslint: ⚠️ 警告のみ（エラー0件）

### 差分の確認

```bash
git status
git diff --stat
```

**想定される差分**：
- Python: 50〜200ファイル
- Frontend: 50〜100ファイル

---

## 💾 コミット方法

### 推奨：1コミットにまとめる

```bash
git add -A
git commit -m "chore: initial code formatting

- Run ruff --fix on Python code
- Run black on Python code
- Run prettier on Frontend code
- Run eslint --fix on Frontend code

Executed using make fmt-step-all (serial, target-limited)
Safe for WSL2 environment (no freeze)"
```

### 注意事項

- pre-commit hook は自動で走る（staged のみ）
- 全体整形は**pre-commit では実行しない**
- CI で全体チェックが実行される

---

## ❌ やってはいけないこと

### 1. `pre-commit run --all-files` を実行

**理由**：
- すべてのファイルをスキャン
- 並列実行で CPU 100%
- VSCode 再接続ループ

**代替**：
```bash
make fmt-step-all  # 直列・対象限定
```

### 2. リポジトリルートで `eslint .`

**理由**：
- node_modules も検索対象
- 564MB をスキャン
- フリーズの原因

**代替**：
```bash
cd app/frontend
npm run lint:fix  # src/ のみ対象
```

### 3. リポジトリルートで `prettier .`

**理由**：
- 全ファイルをスキャン
- data/, backups/ も対象
- CPU 張り付き

**代替**：
```bash
cd app/frontend
npm run format  # src/ のみ対象
```

### 4. VSCode の "Format All Files"

**理由**：
- VSCode が全ファイルを走査
- TypeScript Server がメモリ不足
- フリーズの原因

**代替**：
```bash
make fmt-step-all  # コマンドラインで実行
```

---

## 🔧 トラブルシューティング

### 問題1：VSCode がフリーズした

**症状**：
- VSCode が応答しない
- 「再接続しています...」のループ

**対処**：
1. VSCode を強制終了（タスクマネージャー）
2. WSL を再起動：`wsl --shutdown`
3. VSCode を再起動
4. `.vscode/settings.json` が最新か確認
5. 個別ステップで再実行

### 問題2：Docker コンテナが起動しない

**症状**：
- `make fmt-step-py` でエラー

**対処**：
```bash
make up ENV=local_dev
make ps ENV=local_dev  # 起動確認
```

### 問題3：大量のエラーが出る

**症状**：
- ruff で333エラー
- eslint で30警告

**対処**：
- **正常です**（既に ignore 設定済み）
- エラーは報告されるが、コミットはブロックされない
- 段階的に修正していく方針

### 問題4：途中で止まった

**対処**：
1. どのステップで止まったか確認
2. エラーメッセージを読む
3. 手動修正が必要なら修正
4. 次のステップから再開

---

## 📚 関連ドキュメント

- [型チェック（mypy）](./TYPECHECK.md)
- [ステップ実行フォーマット](./STEP_BY_STEP_FORMAT.md)
- [Makefile ガイド](../infrastructure/MAKEFILE_GUIDE.md)

---

## 🎯 次のステップ

初回整形が完了したら：

1. **コミット・プッシュ**
   ```bash
   git push origin chore/initial-format
   ```

2. **PR 作成**
   - タイトル：`chore: initial code formatting`
   - 説明：初回整形の理由と内容

3. **CI の確認**
   - GitHub Actions が自動実行
   - 全体チェックが通ることを確認

4. **マージ**
   - レビュー承認後にマージ

5. **日常の運用**
   - コミット時は pre-commit が自動実行（staged のみ）
   - 全体チェックは CI に任せる
   - ローカルでは `make fmt-step-check` で確認

---

## 💡 ベストプラクティス

### ✅ やるべきこと

1. **定期的な整形**
   - 週1回程度、`make fmt-step-all` を実行
   - ブランチマージ前に実行

2. **CI の結果を確認**
   - PR 作成後、CI の結果を待つ
   - エラーがあれば修正

3. **VSCode 設定の更新**
   - `.vscode/settings.json` が更新されたら `git pull`
   - チーム全体で設定を共有

### ❌ やらないこと

1. **全体スキャン系コマンド**
   - `pre-commit run --all-files`
   - `eslint .`
   - `prettier .`

2. **VSCode の自動整形**
   - `editor.formatOnSave: true`
   - `editor.codeActionsOnSave`

3. **巨大ディレクトリの監視**
   - `.vscode/settings.json` の除外設定を削除しない

---

## 📝 更新履歴

- 2025-12-25: 初版作成
