# Step-by-Step Formatting Guide

## 📋 目次

- [概要](#概要)
- [なぜステップ実行するのか](#なぜステップ実行するのか)
- [実行方法](#実行方法)
- [実行順序](#実行順序)
- [途中で止めた場合](#途中で止めた場合)
- [トラブルシューティング](#トラブルシューティング)
- [FAQ](#faq)

---

## 概要

このガイドは、WSL/VSCode環境で **CPU張り付きや再接続ループを起こしやすい `pre-commit run --all-files` を避け**、各ツールを **1つずつ順番に** 安全に実行するための手順書です。

### 🎯 対象

- 初回の全ファイル整形
- 設定変更後の再整形
- WSL環境でのCPU負荷を抑えた整形

### ⚡ 基本方針

- **`pre-commit run --all-files` は使わない**（CPU張り付き回避）
- **各ツールを1つずつ順番に実行**（同時実行禁止）
- **nice -n 10 でCPU優先度を下げる**（WSL負荷軽減）
- **対象外ディレクトリを明示的に除外**（node_modules, .venv等）

---

## なぜステップ実行するのか

### 🚨 問題：pre-commit --all-files の課題

`pre-commit run --all-files` を実行すると、以下の問題が発生する可能性があります：

1. **WSLでCPUが100%に張り付く**
   - メモリ4GB以下の環境で顕著
   - 複数のツールが同時に全ファイルをスキャン
   - I/O集中により応答不能になる

2. **VSCodeの再接続ループ**
   - WSL側の高負荷によりSSH接続が切れる
   - 自動再接続→再度高負荷→切断のループ
   - 作業が中断される

3. **巨大ディレクトリの巻き込み**
   - node_modules/, .venv/ などをスキャン
   - 除外設定が効かない場合がある
   - 処理時間が異常に長くなる

### ✅ 解決策：1ツールずつ順番に実行

このスクリプトは以下のように動作します：

- **直列実行**：1つのツールが完了してから次に進む
- **CPU優先度低下**：nice -n 10 で実行
- **対象明示**：frontendは `app/frontend/` 配下のみ
- **中断可能**：途中で止めても次から再開できる

---

## 実行方法

### 前提条件

以下がインストールされていることを確認してください：

```bash
# pre-commit（Python ツール用）
pre-commit --version

# Node.js & npm（Frontend ツール用）
cd app/frontend && npm --version
```

### 基本コマンド

```bash
# スクリプトの場所
cd /path/to/sanbou_app

# ヘルプ表示
bash scripts/format_step_by_step.sh help

# 個別実行
bash scripts/format_step_by_step.sh python-fix
bash scripts/format_step_by_step.sh python-format
bash scripts/format_step_by_step.sh frontend-format
bash scripts/format_step_by_step.sh frontend-fix

# 全処理を順番に実行
bash scripts/format_step_by_step.sh all

# チェックのみ（修正なし）
bash scripts/format_step_by_step.sh check
```

---

## 実行順序

### 固定の実行順序（推奨）

以下の順序で実行することを推奨します：

#### 1️⃣ Python: ruff --fix
```bash
bash scripts/format_step_by_step.sh python-fix
```

**目的**: import整形 & lint自動修正

- import文の並び替え
- 未使用import削除
- 自動修正可能なlintエラー修正

**対象**:
- `app/backend/` 配下のPythonファイル
- 除外: `migrations/`, `alembic/`, `.venv/`, `__pycache__/`

#### 2️⃣ Python: black format
```bash
bash scripts/format_step_by_step.sh python-format
```

**目的**: コード整形

- インデント統一
- 改行位置調整
- クォート統一

**注意**: blackはruffの後に実行（ruffのimport整形を上書きしないため）

#### 3️⃣ Frontend: prettier --write
```bash
bash scripts/format_step_by_step.sh frontend-format
```

**目的**: コード整形

- インデント統一（2スペース）
- 改行位置調整
- セミコロン統一

**対象**:
- `app/frontend/src/` 配下の `.ts`, `.tsx`, `.js`, `.jsx`, `.json`, `.css`
- 除外: `node_modules/`, `dist/`, `build/`

#### 4️⃣ Frontend: eslint --fix
```bash
bash scripts/format_step_by_step.sh frontend-fix
```

**目的**: lint自動修正

- 未使用変数削除
- 型エラー修正（一部）
- コーディング規約違反修正

**注意**: eslintはprettierの後に実行（prettierの整形を上書きしないため）

#### 5️⃣ 最終チェック
```bash
bash scripts/format_step_by_step.sh check
```

**目的**: すべてのツールでエラーがないか確認

- 修正は行わない（check only）
- 残っているエラーを報告

---

## 途中で止めた場合

### 中断しても問題ない

各ステップは **冪等性**（何度実行しても結果が同じ）を持つため、途中で止めても問題ありません。

### 再開方法

止まったステップから再開できます：

```bash
# 例: Step 2（black）で止まった場合
# → Step 2 から再開
bash scripts/format_step_by_step.sh python-format

# その後、残りを実行
bash scripts/format_step_by_step.sh frontend-format
bash scripts/format_step_by_step.sh frontend-fix
```

### 全体を再実行する場合

```bash
# 全処理を最初から
bash scripts/format_step_by_step.sh all
```

すでに整形済みのファイルは変更されないため、安全です。

---

## トラブルシューティング

### 問題1: CPU使用率が高い

**症状**: nice -n 10 を使っているのに CPU 100%

**原因**: WSLのメモリ制限やI/O負荷

**解決策**:
```bash
# 処理を一時停止（Ctrl+Z）
# プロセスを再開（CPU負荷が下がってから）
fg

# または、ステップを分けて実行
bash scripts/format_step_by_step.sh python-fix
# （CPUが落ち着くまで待つ）
bash scripts/format_step_by_step.sh python-format
```

### 問題2: VSCode再接続ループ

**症状**: スクリプト実行中にVSCodeが切断される

**解決策**:
```bash
# VSCodeを閉じる
# ターミナルから直接実行
cd /path/to/sanbou_app
bash scripts/format_step_by_step.sh all

# 完了後、VSCodeを再接続
```

### 問題3: "command not found: pre-commit"

**原因**: pre-commitがインストールされていない

**解決策**:
```bash
# pre-commitのインストール
pip install pre-commit

# または
pip install --user pre-commit

# インストール確認
pre-commit --version
```

### 問題4: Frontend で "npm ERR!"

**原因**: node_modules がインストールされていない

**解決策**:
```bash
cd app/frontend
npm install
cd ../..

# 再実行
bash scripts/format_step_by_step.sh frontend-format
```

### 問題5: 大量のエラーが表示される

**症状**: ruff や eslint で数百のエラー

**原因**: 既存コードに多数のlintエラーがある

**解決策**:
```bash
# エラーは表示されるが、自動修正可能なものは修正される
# 手動修正が必要なエラーは、後で対応する

# エラー内容を確認
bash scripts/format_step_by_step.sh check
```

---

## FAQ

### Q1: pre-commit run --all-files と何が違うのですか？

**A**: 主な違いは以下の通りです：

| 項目 | pre-commit --all-files | このスクリプト |
|------|------------------------|----------------|
| 実行方式 | 複数ツール同時実行 | 1ツールずつ順番 |
| CPU負荷 | 高い（100%張り付き） | 低い（nice -n 10） |
| 中断時の再開 | 困難 | 簡単（ステップ指定） |
| ログ | 混在して見づらい | ステップごとに明確 |
| WSL安定性 | 不安定 | 安定 |

### Q2: 毎回このスクリプトを使う必要がありますか？

**A**: いいえ。通常のコミット時は `pre-commit` を使用してください。

- **初回整形時のみ**: このスクリプト使用
- **通常のコミット**: `git commit` で pre-commit が自動実行（staged ファイルのみ）

### Q3: 処理時間はどのくらいかかりますか？

**A**: プロジェクトのサイズによりますが、目安は以下の通りです：

- Python ruff: 1-2分
- Python black: 30秒-1分
- Frontend prettier: 30秒-1分
- Frontend eslint: 1-2分
- **合計**: 約5-10分

WSL環境では、さらに時間がかかる場合があります。

### Q4: エラーがあっても続行できますか？

**A**: はい。以下のエラーは続行可能です：

- **ruff**: 自動修正できないエラーは警告として表示されるが、処理は続行
- **eslint**: 自動修正できないエラーは警告として表示されるが、処理は続行
- **black**: エラーがあると停止（構文エラーの可能性）
- **prettier**: エラーがあると停止（構文エラーの可能性）

### Q5: 変更が多すぎて怖いです。段階的に実行できますか？

**A**: はい。以下のように分割実行できます：

```bash
# 1. Python のみ
bash scripts/format_step_by_step.sh python-fix
git add app/backend/
git commit -m "style: apply ruff fix"

bash scripts/format_step_by_step.sh python-format
git add app/backend/
git commit -m "style: apply black format"

# 2. Frontend のみ
bash scripts/format_step_by_step.sh frontend-format
git add app/frontend/
git commit -m "style: apply prettier format"

bash scripts/format_step_by_step.sh frontend-fix
git add app/frontend/
git commit -m "style: apply eslint fix"
```

### Q6: CI/CDでも使えますか？

**A**: 使えますが、CI/CDでは **チェックのみ** を推奨します：

```yaml
# GitHub Actions の例
- name: Check formatting
  run: bash scripts/format_step_by_step.sh check
```

CI/CDでの自動修正は、コミット権限の問題があるため避けてください。

---

## 推奨ワークフロー

### 初回整形時

```bash
# 1. 専用ブランチを作成
git checkout -b chore/initial-formatting

# 2. 全処理を実行
bash scripts/format_step_by_step.sh all

# 3. 変更を確認
git status
git diff --stat

# 4. コミット
git add -A
git commit -m "chore: apply initial formatting (ruff, black, prettier, eslint)"

# 5. プッシュ
git push origin chore/initial-formatting
```

### 設定変更後の再整形

```bash
# 1. 設定ファイルを変更
# （例: pyproject.toml, .prettierrc.json 等）

# 2. 該当ツールのみ再実行
bash scripts/format_step_by_step.sh python-format
# または
bash scripts/format_step_by_step.sh frontend-format

# 3. コミット
git add -A
git commit -m "style: reformat after config change"
```

---

## 関連ドキュメント

- [INITIAL_FORMATTING.md](./INITIAL_FORMATTING.md) - 初回整形ガイド（Makefile版）
- [code-style.md](./code-style.md) - コーディングスタイルガイド
- [git-hooks.md](./git-hooks.md) - Git Hooks（pre-commit）の詳細

---

## サポート

問題が解決しない場合は、以下を確認してください：

1. pre-commit と npm がインストールされているか
2. `.gitignore` と `pyproject.toml` の除外設定が正しいか
3. `node_modules` がインストールされているか
4. WSLのメモリ制限を確認（`.wslconfig`）

それでも解決しない場合は、チーム内で相談してください。
