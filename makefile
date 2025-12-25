## ============================================================
## Sanbou App - Makefile
## ============================================================
##
## 📚 ドキュメント
##    MAKEFILE_QUICKREF.md           - クイックリファレンス
##    docs/infrastructure/MAKEFILE_GUIDE.md - 詳細ガイド
##
## 🚀 よく使うコマンド
##    make help                      - 全コマンド一覧
##    make up ENV=local_dev          - 環境起動
##    make down ENV=local_dev        - 環境停止
##    make logs ENV=local_dev S=xxx  - ログ確認
##    make al-up-env ENV=local_dev   - DBマイグレーション（新規環境は自動でbaseline適用）
##    make backup ENV=local_dev      - バックアップ
##
## 🆕 新規環境構築（baseline→roles→alembic を自動実行）
##    make al-up-env ENV=vm_stg      - ステージング環境（初回でも自動で器作成）
##    make al-up-env ENV=vm_prod FORCE=1  - 本番環境（初回のみFORCE=1必須）
##
## 🌍 環境 (ENV)
##    local_dev  - ローカル開発（自動ビルド）
##    local_demo - ローカルデモ
##    vm_stg     - GCP VM ステージング（Artifact Registry）
##    vm_prod    - GCP VM 本番（Artifact Registry）
##
## ⚠️ VM環境での注意
##    - vm_stg と vm_prod は同時起動不可（ポート80競合）
##    - VM環境ではローカルでイメージビルド後 pull して使用
##    - 本番マイグレーション前に必ずバックアップ取得
##
## ============================================================
## モジュール構成:
##   - mk/00_core.mk      : help system
##   - mk/10_env.mk       : environment mapping
##   - mk/20_docker.mk    : docker operations
##   - mk/30_backup.mk    : backup/restore
##   - mk/40_db_baseline.mk : baseline schema
##   - mk/50_db_roles.mk  : bootstrap roles
##   - mk/60_alembic.mk   : migrations
##   - mk/70_db_ownership.mk : ownership refactoring
##   - mk/80_registry.mk  : Artifact Registry
##   - mk/90_maintenance.mk : maintenance operations
##   - mk/95_security.mk  : security scanning
##   - mk/96_format.mk    : formatting & linting
## ============================================================

MK_DIR := mk

include $(MK_DIR)/00_core.mk
include $(MK_DIR)/10_env.mk
include $(MK_DIR)/20_docker.mk
include $(MK_DIR)/30_backup.mk
include $(MK_DIR)/40_db_baseline.mk
include $(MK_DIR)/50_db_roles.mk
include $(MK_DIR)/60_alembic.mk
include $(MK_DIR)/70_db_ownership.mk
include $(MK_DIR)/80_registry.mk
include $(MK_DIR)/90_maintenance.mk
include $(MK_DIR)/95_security.mk
include $(MK_DIR)/96_format.mk
include $(MK_DIR)/30_backup.mk
include $(MK_DIR)/40_db_baseline.mk
include $(MK_DIR)/50_db_roles.mk
include $(MK_DIR)/60_alembic.mk
include $(MK_DIR)/70_db_ownership.mk
include $(MK_DIR)/80_registry.mk
include $(MK_DIR)/90_maintenance.mk
include $(MK_DIR)/95_security.mk
include $(MK_DIR)/98_hooks.mk
