-- ==============================================================================
-- 既存DBユーザー（myuser）のパスワード強化SQL
-- ==============================================================================
--
-- 【目的】
-- 現在使用している DB ユーザー 'myuser' のパスワードを強力なものに変更します。
-- これは環境別アプリユーザー（sanbou_app_dev/stg/prod）への移行準備として、
-- 既存ユーザーのセキュリティを一時的に強化するためのものです。
--
-- 【実行タイミング】
-- 環境別アプリユーザーを作成する前に実行してください。
--
-- 【実行前の準備】
-- 1. 強力なパスワードを生成してください：
--    openssl rand -base64 32
--
-- 2. 生成したパスワードで <NEW_STRONG_PASSWORD_FOR_MYUSER> を置き換えてください
--
-- 3. 変更後のパスワードを安全な場所（1Password等）に保管してください
--
-- 【注意事項】
-- ・このファイルはGit管理されます。実際のパスワードは書き込まないでください
-- ・パスワード変更後は、以下のファイルも更新が必要です：
--   - secrets/.env.local_dev.secrets (開発環境)
--   - secrets/.env.local_stg.secrets (ローカルSTG環境)
--   - secrets/.env.vm_stg.secrets (VM STG環境)
--   - secrets/.env.vm_prod.secrets (VM 本番環境)
--
-- 【実行方法】
-- psql -U myuser -d postgres -f 20251204_alter_current_user_password.sql
--
-- または docker compose 経由で：
-- docker compose -f docker/docker-compose.dev.yml -p local_dev exec -T db \
--   psql -U myuser -d postgres < scripts/sql/20251204_alter_current_user_password.sql
--
-- ==============================================================================

-- 現在のユーザー（myuser）のパスワードを強いものに変更
-- 実行前に <NEW_STRONG_PASSWORD_FOR_MYUSER> を実際の強力なパスワードに置き換えてください
ALTER USER myuser WITH PASSWORD '<NEW_STRONG_PASSWORD_FOR_MYUSER>';

-- 実行確認
\echo '✓ パスワード変更完了: myuser'
\echo '重要: secrets/.env.*.secrets ファイルも更新してください'
