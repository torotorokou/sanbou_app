# Legacy DB Scripts

**目的**: 歴史的に使用されていたデータベース権限関連スクリプトの保存

---

## 📌 このディレクトリについて

このディレクトリには、過去に使用されていたデータベース権限・ロール管理スクリプトが格納されています。
現在は `ops/db/sql/` の新しい統合スクリプトに置き換えられています。

**参照用として保持していますが、新規実行は推奨しません。**

---

## 📁 ファイル一覧

| ファイル名 | 旧用途 | 代替スクリプト |
|-----------|--------|--------------|
| `bootstrap_roles.sql` | app_readonly ロール作成 | `01_roles.sql` |
| `db_permissions.sql` | core_api_user / forecast_user 作成 | `01_roles.sql` + `03_grants.sql` |
| `fix_schema_permissions.sql` | 権限修正 | `03_grants.sql` + `04_default_privileges.sql` |
| `grant_schema_permissions.sql` | 権限付与 | `03_grants.sql` |
| `20251204_create_app_db_users.sql` | 環境別ユーザー作成 | `01_roles.sql` |

---

## ⚠️ 注意事項

### なぜ legacy に移動したか

1. **統合管理**: 権限管理が複数ファイルに分散していた → `01_roles.sql` ~ `04_default_privileges.sql` に統合
2. **実行順序の明確化**: 番号付きファイル名で実行順序を明示
3. **ベストプラクティスの適用**: DEFAULT PRIVILEGES の追加、所有者の分離など
4. **保守性向上**: 体系的なドキュメント化（`ops/db/README.md`）

### 移行パス

既存環境で古いスクリプトを使用している場合：

```bash
# 新しいスクリプトを使用した移行
cd /path/to/sanbou_app

# 1. 現在の状態を確認
make db-verify-roles ENV=local_dev

# 2. 新しいロール設計を適用
make db-apply-all ENV=local_dev

# 3. 検証
make db-verify-roles ENV=local_dev
```

詳細は `ops/db/README.md` を参照してください。

---

## 🔗 関連リソース

- **現行の権限管理**: [ops/db/README.md](../README.md)
- **開発ツール**: [scripts/db/](../../../scripts/db/)
- **Makefile コマンド**: [mk/50_db_roles.mk](../../../mk/50_db_roles.mk)

---

**最終更新日**: 2025-12-24
