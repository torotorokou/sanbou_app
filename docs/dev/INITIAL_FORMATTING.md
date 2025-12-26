# 初回一括整形ガイド（Initial Formatting Guide）

## 📋 目次

- [概要](#概要)
- [なぜ初回だけ直叩きするのか](#なぜ初回だけ直叩きするのか)
- [実行前の準備](#実行前の準備)
- [実行手順](#実行手順)
- [トラブルシューティング](#トラブルシューティング)
- [以降の運用](#以降の運用)

---

## 概要

このガイドは、**プロジェクトに初めてコード整形ツールを導入する際**、または **既存コード全体を一括で整形する必要がある場合** に使用します。

### 🎯 目的

- 全ファイルに対して整形・自動修正を安全に実行する
- WSL環境でのCPU張り付き問題を回避する
- 大量の変更を1つのコミットにまとめる

### ⚡ 重要な前提

- **初回のみ**：通常のコミット時は `pre-commit`（staged ファイルのみ）を使用
- **専用ブランチ推奨**：大量の変更が発生するため、専用ブランチで作業することを強く推奨
- **CPU負荷軽減**：ツールを順番に実行し、同時多発スキャンを避ける

---

## なぜ初回だけ直叩きするのか

### 🚨 問題：pre-commit の全体スキャンはCPU負荷が高い

`pre-commit run --all-files` を実行すると、以下の問題が発生する可能性があります：

- **WSL環境でCPUが張り付く**（特にメモリが限られた環境）
- **複数のツールが同時に全ファイルをスキャン**するため、I/Oが集中する
- **node_modules や .venv などの大容量ディレクトリ**を巻き込む可能性がある

### ✅ 解決策：ツールを順番に直叩きする

このガイドで提供する `make bootstrap-format` は以下のように動作します：

1. **Python ruff fix**（import整形 & lint自動修正）
2. **Python black format**（コード整形）
3. **Frontend prettier write**（コード整形）
4. **Frontend eslint fix**（lint自動修正）

各ツールは順番に実行され、`nice -n 10` でCPU優先度を下げて実行されます。

---

## 実行前の準備

### 1. 前提条件の確認

以下がインストールされていることを確認してください：

```bash
# Python ツール
python -m black --version    # black: formatter
python -m ruff --version     # ruff: linter + import sorter

# Frontend ツール（app/frontend で実行）
cd app/frontend
npm run format --version     # prettier: formatter
npm run lint --version       # eslint: linter
cd ../..
```

### 2. ブランチの作成

**必須**: 専用のブランチで作業してください。

```bash
git checkout -b chore/initial-formatting
```

### 3. 現在の状態を確認

変更前の状態をバックアップしておくことを推奨します。

```bash
# 現在のブランチを確認
git branch

# 未コミットの変更がないことを確認
git status

# （オプション）念のためバックアップ
git stash
```

---

## 実行手順

### ステップ1: 初回一括整形の実行

ルートディレクトリから以下を実行します：

```bash
make bootstrap-format
```

#### 実行内容の確認

コマンドを実行すると、以下のような確認プロンプトが表示されます：

```
============================================================
🚀 初回一括整形を開始します
============================================================
⚠️  注意: この処理は時間がかかり、大量の変更が発生します
   - 専用のブランチで作業することを推奨します
   - 途中で止めた場合は、同じコマンドで再開できます

📂 対象:
   - Python: app/backend/ (migrations除外)
   - Frontend: app/frontend/src/

🔧 実行順序:
   1. Python: ruff fix (import整形 & lint自動修正)
   2. Python: black format (コード整形)
   3. Frontend: prettier write (コード整形)
   4. Frontend: eslint fix (lint自動修正)

続行しますか？ [y/N]
```

`y` を入力してEnterキーを押すと実行が開始されます。

### ステップ2: 実行ログの確認

各ステップの実行状況が表示されます：

```
============================================================
▶️  Step 1/4: Python ruff fix
============================================================
🔧 Python ruff fix を実行中...
✅ ruff fix 完了

============================================================
▶️  Step 2/4: Python black format
============================================================
🎨 Python black format を実行中...
✅ black format 完了

...（以下続く）
```

### ステップ3: 変更の確認

実行完了後、変更内容を確認します：

```bash
# 変更されたファイル数を確認
git status

# 変更の詳細を確認（オプション）
git diff --stat
```

### ステップ4: コミット

変更をコミットします：

```bash
# 全変更をステージング
git add -A

# コミット
git commit -m "chore: apply initial formatting (ruff, black, prettier, eslint)"
```

### ステップ5: 整形の検証

整形が正しく適用されたか確認します：

```bash
make check-format
```

すべてのチェックが通れば、整形は成功です。

### ステップ6: プッシュ

リモートにプッシュします：

```bash
git push origin chore/initial-formatting
```

---

## トラブルシューティング

### 問題1: 途中でCPUが張り付いて止まった

**解決策**: プロセスを終了（Ctrl+C）し、個別のステップを実行します。

```bash
# 個別実行の例
make fmt-python-ruff      # Python ruff fix のみ
make fmt-python-black     # Python black format のみ
make fmt-frontend-prettier # Frontend prettier write のみ
make fmt-frontend-eslint   # Frontend eslint fix のみ
```

### 問題2: 大量のエラーが出る

**原因**: 既存コードに多数のlintエラーがある可能性があります。

**解決策**: `|| true` により、エラーがあっても処理は継続されます。以下で詳細を確認できます：

```bash
# Python のエラーを確認
python -m ruff check app/backend/core_api

# Frontend のエラーを確認
cd app/frontend && npm run lint
```

### 問題3: node_modules や .venv が除外されていない

**確認**: `.gitignore` と `pyproject.toml` の設定を確認してください。

```bash
# .gitignore の確認
cat .gitignore | grep -E "node_modules|\.venv"

# pyproject.toml の除外設定を確認
grep -A 10 "extend-exclude" pyproject.toml
```

### 問題4: Frontend の prettier/eslint が動かない

**原因**: npm パッケージがインストールされていない可能性があります。

**解決策**:

```bash
cd app/frontend
npm install
npm run format --version  # prettier の確認
npm run lint --version    # eslint の確認
cd ../..
```

### 問題5: 変更が多すぎて git diff が見づらい

**解決策**: ファイル別に変更を確認します。

```bash
# 変更されたファイル一覧
git diff --name-only

# 特定のファイルの変更を確認
git diff app/backend/core_api/app/main.py
```

---

## 以降の運用

### 日常のコミット時

初回整形完了後は、通常の `pre-commit` を使用します：

```bash
# pre-commit のインストール（初回のみ）
pre-commit install

# コミット時に自動実行される（staged ファイルのみ）
git add <file>
git commit -m "feat: add new feature"
```

### 再度全体整形が必要な場合

設定変更後など、再度全体整形が必要な場合は、再度 `make bootstrap-format` を実行できます。

```bash
# 再度全体整形
make bootstrap-format
```

### チェックのみ実行したい場合

整形せず、チェックだけしたい場合：

```bash
# 全体チェック
make check-format

# Python のみ
make check-python

# Frontend のみ
make check-frontend
```

---

## よくある質問（FAQ）

### Q1: なぜ `pre-commit run --all-files` を使わないのですか？

**A**: WSL環境でCPU張り付きが発生するため、初回は直叩きで順番に実行します。通常のコミット時（staged ファイルのみ）は `pre-commit` を使用します。

### Q2: 変更が多すぎて怖いです。段階的に実行できますか？

**A**: はい、可能です。以下のように個別実行できます：

```bash
make fmt-python           # Python のみ
make fmt-frontend         # Frontend のみ
```

さらに細かく：

```bash
make fmt-python-ruff      # Python ruff のみ
make fmt-python-black     # Python black のみ
make fmt-frontend-prettier # Frontend prettier のみ
make fmt-frontend-eslint   # Frontend eslint のみ
```

### Q3: CI/CDでも同じコマンドを使えますか？

**A**: CI/CDでは `make check-format` を使用することを推奨します。これはチェックのみ行い、修正はしません。

```yaml
# GitHub Actions の例
- name: Check formatting
  run: make check-format
```

### Q4: migrations や node_modules も整形されますか？

**A**: いいえ。`pyproject.toml` と `.gitignore` で除外されているディレクトリは対象外です。

- Python: `migrations`, `alembic`, `.venv`, `__pycache__` など
- Frontend: `node_modules`, `dist`, `build` など

### Q5: ruff と black は競合しませんか？

**A**: 競合しません。役割が明確に分かれています：

- **ruff**: linter + import sorter（`--fix` で自動修正）
- **black**: formatter（コード整形）

`pyproject.toml` で競合を回避する設定が入っています。

---

## 関連ドキュメント

- [code-style.md](./code-style.md) - コーディングスタイルガイド
- [git-hooks.md](./git-hooks.md) - Git Hooks（pre-commit）の詳細
- [MAKEFILE_QUICKREF.md](../../MAKEFILE_QUICKREF.md) - Makefile クイックリファレンス

---

## サポート

問題が解決しない場合は、以下を確認してください：

1. ツールのバージョンが最新か
2. `.gitignore` と `pyproject.toml` の除外設定が正しいか
3. `node_modules` がインストールされているか

それでも解決しない場合は、チーム内で相談してください。
