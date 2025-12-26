# tools/precommit/

このディレクトリには、pre-commit で使用するカスタムチェックスクリプトを配置します。

## 概要

`.pre-commit-config.yaml` で `repo: local` として定義されたカスタムフックの実体をここに配置することで、
リポジトリ内で「見える化」し、チームメンバーが容易にカスタマイズできるようにします。

## 使い方

1. **新しいチェックを追加する場合:**

   - このディレクトリに Python スクリプトを作成
   - `.pre-commit-config.yaml` の `repo: local` セクションに hook を追加
   - `chmod +x` で実行権限を付与

2. **既存のチェックを修正する場合:**
   - このディレクトリのスクリプトを直接編集
   - `make hooks-run` でテスト実行

## サンプルスクリプト

- `check_todos.py` - TODO/FIXME コメントをチェック（pre-push時）
- `noop_example.py` - 何もしないダミー（構造のサンプル）

## 注意事項

- スクリプトは必ず shebang (`#!/usr/bin/env python3`) を付けてください
- 実行権限を付与してください: `chmod +x <script_name>.py`
- エラーメッセージはわかりやすく日本語で出力してください
- 終了コード 0 = 成功、非ゼロ = 失敗
