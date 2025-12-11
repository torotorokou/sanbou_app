# 優先タスクリスト

**作成日**: 2025年12月11日  
**最終更新**: 2025年12月11日

---

## 🔴 緊急（即時対応が必要）

### 1. ✅ セキュリティインシデント対応（完了）
- [x] docker-compose.dev.ymlからパスワード削除
- [x] Git履歴からの機密情報削除
- [x] インシデントレポート作成

### 2. 🔐 Pre-commitフックの強化（1-2日以内）
**優先度**: 🔴 HIGH  
**理由**: 同様のインシデントの再発防止  
**ファイル**: `scripts/git/hooks/pre-commit-security.py`

**追加すべき検出パターン**:
```python
# PostgreSQL/MySQL DSN内のパスワード
r'postgresql://[^:]+:([^@\s]{8,})@',
r'mysql://[^:]+:([^@\s]{8,})@',

# docker-compose環境変数のDB接続文字列
r'DB_DSN\s*=\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@',
r'DATABASE_URL\s*=\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@',
```

**テスト方法**:
```bash
# 検出されるべきパターン
echo "- DB_DSN=postgresql://user:password123@localhost/db" | python scripts/git/hooks/pre-commit-security.py
```

### 3. 🔑 開発環境DBパスワードのローテーション（1週間以内）
**優先度**: 🟡 MEDIUM  
**理由**: 流出したパスワードの無効化

**手順**:
```bash
# 1. 新しいパスワード生成
openssl rand -base64 32

# 2. secrets/.env.local_dev.secrets を更新
# POSTGRES_PASSWORD=<新しいパスワード>

# 3. DBコンテナを再起動
make down ENV=local_dev
make up ENV=local_dev
```

---

## 🟡 高優先度（1週間以内）

### 4. 📝 セキュリティガイドラインの更新
**優先度**: 🟡 HIGH  
**ファイル**: `docs/conventions/SECURITY_GUIDELINES.md`

追加すべきセクション:
- ❌ データベース接続文字列の直接記述禁止
- ✅ 環境変数を使用した正しい管理方法
- 🔍 コミット前のセルフチェックリスト

### 5. 🎓 チームへのセキュリティ教育
**優先度**: 🟡 HIGH  
**実施内容**:
- インシデントの共有（blamelessな形で）
- ベストプラクティスのレビュー
- Pre-commitフックの使い方の確認

### 6. 🔍 全docker-composeファイルのセキュリティ監査
**優先度**: 🟡 MEDIUM  
**対象ファイル**:
- `docker/docker-compose.dev.yml` ✅（対応済み）
- `docker/docker-compose.local_demo.yml`
- `docker/docker-compose.stg.yml`
- `docker/docker-compose.prod.yml`

**チェック項目**:
- [ ] パスワードが環境変数化されているか
- [ ] APIキーが環境変数化されているか
- [ ] 機密情報がコメントに含まれていないか

---

## 🟢 通常優先度（1ヶ月以内）

### 7. 🔐 GitHub Secret Scanningの有効化
**優先度**: 🟢 MEDIUM  
**実施内容**:
- GitHub Advanced Securityの検討
- Secret scanning alertsの設定
- Push protectionの有効化

### 8. 🔄 定期的なセキュリティ監査の仕組み化
**優先度**: 🟢 MEDIUM  
**実施内容**:
- 月次レビュープロセスの確立
- チェックリストの作成
- 責任者の明確化

### 9. 🔑 シークレット管理の改善
**優先度**: 🟢 LOW（将来的な改善）  
**検討事項**:
- Google Secret Manager / AWS Secrets Managerの利用
- docker-composeからのシークレット完全分離
- 環境変数のテンプレート化とバリデーション自動化

---

## 📋 技術的負債（優先度低、時間があれば対応）

### 10. 📚 ドキュメント整備
- [ ] 環境変数管理のベストプラクティス文書化
- [ ] トラブルシューティングガイド作成
- [ ] オンボーディング資料の更新

### 11. 🧪 テストカバレッジの向上
- [ ] Pre-commitフックのユニットテスト追加
- [ ] セキュリティスキャンのCI/CD統合

---

## 🎯 推奨する作業順序

### 今日中（2025-12-11）
1. ✅ セキュリティインシデント対応（完了）
2. 🔐 Pre-commitフックの強化（パターン追加）

### 今週中（2025-12-13まで）
3. 🔑 開発環境DBパスワードのローテーション
4. 📝 セキュリティガイドラインの更新
5. 🔍 全docker-composeファイルのセキュリティ監査

### 来週（2025-12-18まで）
6. 🎓 チームへのセキュリティ教育
7. 🔐 GitHub Secret Scanningの有効化（検討・実装）

### 1ヶ月以内
8. 🔄 定期的なセキュリティ監査の仕組み化
9. 🔑 シークレット管理の改善（検討開始）

---

## 📊 進捗トラッキング

| タスク | ステータス | 担当 | 期限 |
|--------|-----------|------|------|
| セキュリティインシデント対応 | ✅ 完了 | Copilot | 2025-12-11 |
| Pre-commitフック強化 | 🔄 次のタスク | - | 2025-12-12 |
| DBパスワードローテーション | ⏳ 未着手 | - | 2025-12-18 |
| セキュリティガイドライン更新 | ⏳ 未着手 | - | 2025-12-18 |
| docker-compose監査 | ⏳ 未着手 | - | 2025-12-18 |
| チームセキュリティ教育 | ⏳ 未着手 | - | 2025-12-20 |

---

**次のアクション**: Pre-commitフックの強化（DSNパターン検出の追加）
