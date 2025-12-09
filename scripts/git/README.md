# Git セキュリティツール

Git フックとセキュリティチェックツールの説明とリファクタリング履歴

## 📁 ディレクトリ構成

```
scripts/git/
├── lib/
│   ├── security_patterns.sh   # 機密情報パターン定義（共通ライブラリ）
│   └── output_utils.sh         # 出力ユーティリティ（共通ライブラリ）
├── verify_gitignore.sh         # .gitignore 整合性チェッカー
├── cleanup_git_history.sh      # Git 履歴クリーンアップ
└── setup_git_hooks.sh          # Git フックのセットアップ

.git/hooks/
├── pre-commit                  # コミット前チェック
└── pre-push                    # プッシュ前チェック
```

## 🎯 各ツールの役割

### 1. **pre-commit** (Git フック)
コミット前に以下をチェック:
- ✅ 機密ファイルのパターンマッチング
- ✅ ファイル内容の機密情報検出
- ✅ ユーザーへの警告と確認

### 2. **pre-push** (Git フック)
プッシュ前に以下をチェック:
- ✅ Git 履歴内の機密ファイル
- ✅ コミット履歴の機密情報パターン
- ✅ Git 追跡状態の確認
- ✅ .gitignore の整合性

### 3. **verify_gitignore.sh**
.gitignore の設定状態を検証:
```bash
bash scripts/git/verify_gitignore.sh
```

### 4. **security_patterns.sh** (共通ライブラリ)
機密情報の検出パターンを一元管理:
- 禁止ファイルパターン
- 機密情報の内容パターン
- 除外パターン（誤検知防止）

### 5. **output_utils.sh** (共通ライブラリ)
統一された出力形式:
- 色付きログ出力
- プログレスバー
- エラー詳細表示
- ユーザー確認ダイアログ

## 🔧 リファクタリングの改善点

### Before (旧実装)
❌ パターンが各ファイルに分散
❌ 重複したチェックロジック
❌ 不統一なエラーメッセージ
❌ 除外ルールが複雑で読みにくい

### After (新実装)
✅ パターンを共通ライブラリに集約
✅ 段階的チェックで早期検出
✅ 統一されたユーザーフレンドリーな出力
✅ 関数化による再利用性向上
✅ プログレス表示で処理状況が明確

## 📋 検出対象の機密情報

### ファイルパターン
- `env/.env.*` (テンプレート以外)
- `secrets/*.secrets`
- `secrets/gcp-sa*.json`
- `*.pem`, `*.key` (秘密鍵)
- `*.dump` (データベースダンプ)

### 内容パターン
- データベースパスワード
- GCP 秘密鍵 (`BEGIN PRIVATE KEY`)
- API キー
- JWT シークレット
- AWS アクセスキー

### 除外パターン（誤検知防止）
- 環境変数参照 (`os.getenv`, `$VAR`)
- コメント行
- コード例・ドキュメント内のバッククォート
- 空の値

## 🚀 使用方法

### 通常の Git 操作
```bash
# コミット時に自動チェック
git add .
git commit -m "message"

# プッシュ時に自動チェック
git push origin branch
```

### 手動チェック
```bash
# .gitignore の整合性確認
bash scripts/git/verify_gitignore.sh

# Git 履歴のクリーンアップ
bash scripts/git/cleanup_git_history.sh
```

### フック再セットアップ
```bash
bash scripts/git/setup_git_hooks.sh
```

## 📝 .gitignore の必須パターン

以下のパターンが含まれているか自動チェックされます:

```gitignore
# 環境変数ディレクトリ
/env/
!env/.env.example
!env/*.template

# 機密情報ディレクトリ
/secrets/
!secrets/*.template

# 個別ファイルパターン
.env
.env.*
*.pem
*.key
gcp-sa*.json
gcs-key*.json
```

## ⚠️ トラブルシューティング

### エラー: "セキュリティパターンライブラリが見つかりません"
```bash
# ライブラリの存在確認
ls -la scripts/git/lib/

# 実行権限の付与
chmod +x scripts/git/lib/*.sh
```

### エラー: "機密ファイルがプッシュに含まれています"
```bash
# ファイルを unstage
git restore --staged <ファイル名>

# Git 追跡から削除（ファイルは保持）
git rm --cached <ファイル名>

# 履歴から完全削除
bash scripts/git/cleanup_git_history.sh
```

### 警告を無視してコミット/プッシュする場合
```bash
# pre-commit をスキップ（非推奨）
git commit --no-verify -m "message"

# pre-push をスキップ（非推奨）
git push --no-verify origin branch
```

## 🔍 検証コマンド

```bash
# 追跡されている機密ファイルの確認
git ls-files | grep -E '^(env/\.env\.|secrets/.*\.secrets$)'

# .gitignore が機能しているか確認
git check-ignore -v env/.env.local_dev

# 特定パターンの Git 履歴検索
git log -S "POSTGRES_PASSWORD" --all

# コミット内容の詳細確認
git show <commit-hash>
```

## 📚 参考資料

- [Git Hooks 公式ドキュメント](https://git-scm.com/book/en/v2/Customizing-Git-Git-Hooks)
- [.gitignore パターン](https://git-scm.com/docs/gitignore)
- [git-filter-repo](https://github.com/newren/git-filter-repo)

## 🎓 ベストプラクティス

1. **テンプレートファイルのみコミット**
   - `.env.example`, `*.template` を使用

2. **定期的な整合性チェック**
   ```bash
   bash scripts/git/verify_gitignore.sh
   ```

3. **CI/CD でのチェック統合**
   - GitHub Actions で pre-push 相当のチェック実施

4. **チーム内での共有**
   - 全メンバーが同じフックを使用
   - `scripts/git/setup_git_hooks.sh` で統一

5. **機密情報は環境変数で管理**
   - ハードコーディングを避ける
   - `os.getenv()` を使用
