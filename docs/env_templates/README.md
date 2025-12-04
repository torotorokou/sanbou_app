# 環境変数ファイル テンプレート

このディレクトリには、各環境の .env ファイルのテンプレートが保存されています。

## ⚠️ 重要な注意事項

**これらのファイルはドキュメント/参考用です。実際の環境ファイルは Git 管理されていません。**

- 実際の環境ファイルは `env/` ディレクトリにあります
- 環境ファイルは `.gitignore` で除外されており、Git で追跡されません
- 新しい環境をセットアップする際は、`env/.env.example` をベースに作成してください

## ファイル一覧

### env/.env.common
全環境共通の設定。すべての環境で最初に読み込まれます。

### env/.env.local_dev
ローカル開発環境用。環境変数スキーマの基準（Source of Truth）です。

### env/.env.local_stg
ローカルステージング検証環境用。nginx + 本番近似構成。

### env/.env.vm_stg
GCP VM ステージング環境用。

### env/.env.vm_prod
GCP VM 本番環境用。

## 新しい環境のセットアップ手順

1. `env/.env.example` を参照して、必要な環境ファイルを作成
2. このディレクトリのテンプレートも参考にする
3. `secrets/` ディレクトリに対応する secrets ファイルを作成
4. パスワードや API キーは必ず secrets ファイルで管理

## 関連ドキュメント

- `env/.env.example` - 環境変数設定の完全なテンプレート
- `secrets/.env.secrets.template` - シークレット設定のテンプレート
- `docs/20251204_ENV_AND_COMPOSE_SYNC.md` - 環境変数と Docker Compose の同期作業記録
- `makefile` - 環境マッピングと make コマンド一覧
