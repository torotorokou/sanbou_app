# Pre-commit フック強化 - DSN パターン検出

**作成日**: 2024年12月24日  
**優先度**: 🔴 HIGH  
**理由**: セキュリティインシデント再発防止

---

## 📋 概要

2024年12月11日のセキュリティインシデント（docker-compose.dev.yml内のDB接続文字列流出）を受けて、Pre-commitフックにDSN（Data Source Name）パターンの検出機能を追加します。

---

## 🎯 目的

以下のようなデータベース接続文字列がコミットされることを防止：

```yaml
# 🚫 検出すべき危険なパターン
DB_DSN: postgresql://user:password123@localhost/db
DATABASE_URL: mysql://root:secretpass@db:3306/mydb
REDIS_URL: redis://:mypassword@localhost:6379
```

---

## 🔍 追加する検出パターン

### 1. PostgreSQL DSN
```python
r'postgresql://[^:]+:([^@\s]{8,})@'
r'postgres://[^:]+:([^@\s]{8,})@'
```

**マッチ例**:
- `postgresql://user:password123@localhost/db`
- `postgres://myuser:secretpass@db.example.com:5432/production`

### 2. MySQL DSN
```python
r'mysql://[^:]+:([^@\s]{8,})@'
```

**マッチ例**:
- `mysql://root:mysqlpassword@localhost:3306/mydb`
- `mysql://app_user:app_pass_2024@mysql-server/app_db`

### 3. Redis DSN
```python
r'redis://:[^@\s]{8,}@'
```

**マッチ例**:
- `redis://:myredispassword@localhost:6379`
- `redis://:secretkey123@redis.example.com:6379/0`

### 4. docker-compose 環境変数内のDSN
```python
r'DB_DSN\s*[:=]\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@'
r'DATABASE_URL\s*[:=]\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@'
```

**マッチ例**:
```yaml
DB_DSN: postgresql://user:password@localhost/db
DATABASE_URL="mysql://root:pass123@mysql/db"
```

---

## ⚙️ 実装方針

### 1. 既存の pre-commit-security.py を拡張
- 既存の SECRET_PATTERNS リストにDSNパターンを追加
- パターン名を明確化（例: `postgresql_dsn`, `mysql_dsn`）

### 2. 誤検知の削減
- パスワード部分が8文字以上のケースのみ検出
- プレースホルダー（例: `${PASSWORD}`, `<password>`）は除外
- .env.example や ドキュメント内の例示は除外

### 3. テストケースの追加
- 検出されるべきパターン
- 検出されないべきパターン（誤検知防止）

---

## 🧪 テスト計画

### 検出されるべきケース（True Positive）
```bash
# 1. PostgreSQL DSN
echo "DB_DSN: postgresql://user:password123@localhost/db" > test.yml
git add test.yml  # → ブロックされるべき

# 2. MySQL DSN in docker-compose
echo "DATABASE_URL=mysql://root:secretpass@mysql:3306/db" > test.yml
git add test.yml  # → ブロックされるべき

# 3. Redis DSN
echo "REDIS_URL: redis://:mypassword123@redis:6379" > test.yml
git add test.yml  # → ブロックされるべき
```

### 検出されないケース（False Negative回避）
```bash
# 1. 環境変数参照（許可）
echo "DB_DSN: postgresql://user:\${DB_PASSWORD}@localhost/db" > test.yml
git add test.yml  # → OK

# 2. プレースホルダー（許可）
echo "DATABASE_URL: mysql://user:<password>@localhost/db" > test.yml
git add test.yml  # → OK

# 3. ドキュメント内の例示（許可）
echo "Example: postgresql://user:example_pass@host/db" > README.md
git add README.md  # → OK（.mdファイルは除外対象に追加）

# 4. 短いパスワード（7文字以下は除外）
echo "DB_DSN: postgresql://user:pass@localhost/db" > test.yml
git add test.yml  # → OK（8文字未満は開発用と判断）
```

---

## 📝 実装手順

### Step 1: 現在のpre-commit-security.pyを確認
```bash
cat scripts/git/hooks/pre-commit-security.py
```

### Step 2: DSNパターンを追加
```python
SECRET_PATTERNS = [
    # 既存のパターン...
    
    # Database DSN patterns (password >= 8 chars)
    (r'postgresql://[^:]+:([^@\s]{8,})@', 'postgresql_dsn'),
    (r'postgres://[^:]+:([^@\s]{8,})@', 'postgres_dsn'),
    (r'mysql://[^:]+:([^@\s]{8,})@', 'mysql_dsn'),
    (r'redis://:[^@\s]{8,}@', 'redis_dsn'),
    
    # docker-compose environment variables with DSN
    (r'DB_DSN\s*[:=]\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@', 'db_dsn_env'),
    (r'DATABASE_URL\s*[:=]\s*["\']?[^"\'\s]*://[^:]+:[^@\s]{8,}@', 'database_url_env'),
]
```

### Step 3: プレースホルダー除外ロジックを追加
```python
def is_placeholder(password_part: str) -> bool:
    """パスワード部分がプレースホルダーかどうか判定"""
    placeholders = [
        r'\$\{[^}]+\}',  # ${VAR}
        r'\$\([^)]+\)',  # $(VAR)
        r'<[^>]+>',      # <password>
        r'\*+',          # ****
        r'example',      # example_pass
        r'your_',        # your_password
    ]
    return any(re.search(pattern, password_part, re.IGNORECASE) 
               for pattern in placeholders)
```

### Step 4: テストを追加
```bash
python tests/test_pre_commit_security.py
```

### Step 5: 動作確認
```bash
# 実際のファイルでテスト
echo "DB_DSN: postgresql://user:realpassword@localhost/db" > /tmp/test.yml
python scripts/git/hooks/pre-commit-security.py /tmp/test.yml
# → エラーが出るべき
```

---

## 🔒 セキュリティ上の考慮事項

### 検出レベルのバランス
- **厳しすぎる**: 開発を妨げる（誤検知が多い）
- **緩すぎる**: インシデントを防げない
- **最適解**: 8文字以上のパスワードを検出、プレースホルダーは除外

### 除外ファイル
以下のファイルは検査対象外にすることを検討：
- `.env.example`（テンプレートファイル）
- `*.md`（ドキュメント内の例示）
- `docs/examples/**`（サンプルコード）

---

## 📈 成功基準

- ✅ PostgreSQL/MySQL/Redis DSNが検出できる
- ✅ docker-compose内の環境変数も検出できる
- ✅ プレースホルダーは誤検知しない
- ✅ テストケースがすべてパスする
- ✅ 実際のコミットで動作確認済み

---

## 🔄 継続的改善

### 今後の追加候補
- MongoDB DSN: `mongodb://user:pass@host/db`
- AWS RDS接続文字列
- Azure SQL接続文字列
- SQLite with password（あまり使われないが）

### メンテナンス
- 月次でパターンの有効性を確認
- 誤検知レポートの収集と対応
- 新しいデータベースタイプへの対応

---

## 📚 関連ドキュメント

- [セキュリティインシデントレポート](../security/INCIDENT_REPORT_20241211.md)
- [セキュリティガイドライン](../conventions/SECURITY_GUIDELINES.md)
- [Pre-commitフック利用ガイド](../development/PRE_COMMIT_GUIDE.md)

---

**次のアクション**: 実装開始（scripts/git/hooks/pre-commit-security.py の更新）
