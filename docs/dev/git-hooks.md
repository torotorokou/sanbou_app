# Git Hooks & Pre-commit セットアップガイド

## 概要

このプロジェクトでは、コード品質を維持するために **pre-commit** を使用しています。
Git hooks の定義は `.pre-commit-config.yaml` に集約されており、これが「正本」となります。

## 主要な構成要素

```
.
├── .pre-commit-config.yaml      # チェック定義の正本
├── tools/
│   ├── git-hooks/               # Git hooks の入口（薄いラッパー）
│   │   ├── pre-commit           # コミット前チェック
│   │   └── pre-push             # プッシュ前チェック
│   └── precommit/               # カスタムチェックスクリプト
│       ├── README.md
│       ├── check_todos.py       # TODO/FIXME チェック
│       └── noop_example.py      # サンプル
├── mk/
│   └── 98_hooks.mk              # Makefile targets
└── .github/
    └── workflows/
        └── pre-commit.yml       # CI での自動実行
```

## クイックスタート

### 初回セットアップ

```bash
# 1. pre-commit をインストール（まだの場合）
pip install pre-commit

# 2. Git hooks を設定
make hooks-install
```

これで以下が自動的に設定されます：

- `core.hooksPath` を `tools/git-hooks/` に設定
- pre-commit hooks のインストール
- pre-push hooks のインストール

### 日常の使い方

```bash
# 全ファイルでチェック実行（手動）
make hooks-run

# Hooks の自動アップデート
make hooks-update

# 通常のコミット・プッシュ（自動的に hooks が実行される）
git commit -m "feat: 新機能追加"
git push
```

### Hooks をスキップしたい場合

```bash
# コミット時のチェックをスキップ
git commit --no-verify -m "fix: hotfix"

# プッシュ時のチェックをスキップ
git push --no-verify
```

> ⚠️ **注意**: CI では必ず全チェックが実行されるため、スキップしても最終的にはチェックが必要です。

## チェック内容

`.pre-commit-config.yaml` で定義されているチェック：

### 基本チェック

- **ファイル整形**: 行末空白削除、ファイル末尾改行、改行コード統一（LF）
- **構文チェック**: YAML, JSON, TOML, XML の構文検証
- **マージコンフリクト検出**: コンフリクトマーカーの検出
- **大きいファイル検出**: 1000KB 以上のファイルを警告

### セキュリティチェック

- **秘密鍵検出**: 秘密鍵がコミットされないようチェック
- **機密情報検出**: パスワードやAPIキーなどの検出 (detect-secrets)

### Python

- **フォーマット**: black によるコードフォーマット
- **importソート**: isort による import の整理

### Frontend

- **フォーマット**: Prettier による TypeScript/JavaScript/JSON/YAML のフォーマット

### Docker

- **Dockerfile リント**: hadolint による Dockerfile の検証

### Markdown

- **Markdown リント**: markdownlint によるMarkdownの検証

### シェルスクリプト

- **shellcheck**: シェルスクリプトの静的解析

### カスタムチェック

- **パスワードチェック**: docs内のハードコードされたパスワードを検出
- **TODO/FIXMEチェック**: pre-push 時に TODO コメントを検出（情報提供のみ）
- **env/ ファイルチェック**: 実環境ファイルがコミットされないよう警告

## カスタムチェックの追加方法

### 1. スクリプトを作成

`tools/precommit/` にスクリプトを追加：

```python
#!/usr/bin/env python3
"""
my_custom_check.py - カスタムチェックの説明
"""
import sys

def main():
    # チェックロジック
    # 成功: return 0
    # 失敗: return 1
    return 0

if __name__ == '__main__':
    sys.exit(main())
```

### 2. 実行権限を付与

```bash
chmod +x tools/precommit/my_custom_check.py
```

### 3. `.pre-commit-config.yaml` に追加

```yaml
- repo: local
  hooks:
    - id: my-custom-check
      name: 私のカスタムチェック
      entry: tools/precommit/my_custom_check.py
      language: python
      types: [python]
      pass_filenames: true
```

### 4. テスト実行

```bash
make hooks-run
```

## CI での実行

GitHub Actions で自動的に実行されます（`.github/workflows/pre-commit.yml`）：

- すべての push/pull request で実行
- pre-commit cache を使用して高速化
- 失敗時はログとdiffをアーティファクトとして保存

## トラブルシューティング

### pre-commit が見つからない

```bash
pip install pre-commit
# または
pip install --user pre-commit
```

### Hooks が実行されない

```bash
# 設定を確認
git config core.hooksPath

# 再インストール
make hooks-clean
make hooks-install
```

### 特定のチェックを無効化したい

`.pre-commit-config.yaml` で該当する hook を削除またはコメントアウト：

```yaml
# - id: trailing-whitespace  # 無効化
```

### 既存ファイルで大量のエラーが出る場合

```bash
# 段階的に修正
pre-commit run trailing-whitespace --all-files
pre-commit run end-of-file-fixer --all-files
# ... 順番に実行
```

または、一時的に特定の hook をスキップ：

```bash
SKIP=black,isort git commit -m "WIP: 作業中"
```

## ベストプラクティス

### コミット前の習慣

1. **こまめにチェック**: コミット前に `make hooks-run` を実行
2. **段階的なコミット**: 大きな変更は小さく分割してコミット
3. **エラーメッセージを読む**: エラーの内容を理解して修正

### チーム開発での注意点

1. **初回セットアップ**: clone 後は必ず `make hooks-install` を実行
2. **hooks の更新**: 定期的に `make hooks-update` でアップデート
3. **CI を信頼**: ローカルでスキップしても CI が最終チェック

### env/ ファイル管理の注意

- ✅ **追跡する**: `.env.example`, `.env.*.example` などのテンプレート
- ❌ **追跡しない**: `.env.local_dev`, `.env.vm_stg` などの実ファイル

実ファイルがコミットされようとすると、pre-commit が自動的に警告します。

## 参考リンク

- [pre-commit 公式ドキュメント](https://pre-commit.com/)
- [pre-commit hooks カタログ](https://pre-commit.com/hooks.html)
- [プロジェクトの Makefile ガイド](../infrastructure/MAKEFILE_GUIDE.md)

## よくある質問（FAQ）

### Q: `.git` ディレクトリはなぜ .gitignore に？

A: `.git` はGitの内部状態を保持するディレクトリで、自動的に追跡されません。
`.gitignore` に追加するのは Explorer での表示を抑制するためです。

### Q: `core.hooksPath` とは？

A: Git hooks の場所を指定する設定です。デフォルトは `.git/hooks/` ですが、
このプロジェトでは `tools/git-hooks/` を使用し、チーム全体で共有します。

### Q: CI で失敗したが、ローカルでは成功する

A: 以下を確認してください：

- pre-commit のバージョンが最新か（`make hooks-update`）
- `.pre-commit-config.yaml` が最新か（`git pull`）
- キャッシュをクリアして再実行（`pre-commit clean`）

### Q: hooks を一時的に無効化したい

A: 以下のコマンドで設定を解除できます：

```bash
make hooks-clean
```

再度有効化する場合は `make hooks-install` を実行してください。

## 更新履歴

- 2024-12-25: 初版作成
