# GCP URL公開前セキュリティ課題レポート

**作成日**: 2025-12-03  
**対象**: sanbou_app - GCP URL公開前のセキュリティ監査レポート

---

## 概要

既存のWebアプリケーション（sanbou_app）をGCPでURL公開することを想定し、セキュリティ面における修正すべき課題を優先度順に分析・整理しました。本レポートは、コードベースの調査結果に基づき、Critical/High/Mediumの3段階で分類しています。

---

## GCP URL公開前に修正すべきセキュリティ課題（優先度順）

### 🔴 **最優先（Critical）**

#### 1. **CORS設定の過度な許可**
**現状の問題:**
- 全APIサービスで `allow_origins=["*"]` が設定されている
- 本番環境でも全オリジンからのアクセスを許可

**影響:**
- クロスサイトリクエストフォージェリ(CSRF)攻撃のリスク
- 意図しないドメインからのAPIアクセスが可能

**修正箇所:**
- `app/backend/core_api/app/app.py` (87行目)
- `app/backend/ai_api/app/main.py` (65行目)
- `app/backend/ledger_api/app/main.py` (68行目)
- `app/backend/rag_api/app/main.py` (128行目)
- `app/backend/manual_api/app/main.py` (115行目)

**推奨対応:**
```python
# 環境変数で許可するオリジンを制限
allowed_origins = os.getenv("CORS_ALLOWED_ORIGINS", "").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,  # 本番では特定ドメインのみ
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE"],  # 必要なメソッドのみ
    allow_headers=["*"],
)
```

#### 2. **GCPサービスアカウントキーの直接マウント**
**現状の問題:**
- `secrets/dev_key.json`, `secrets/stg_key.json` をコンテナに直接マウント
- 鍵ファイルがGitリポジトリに存在する可能性

**影響:**
- 鍵の漏洩リスク
- 鍵のローテーション管理が困難

**推奨対応:**
- GCP Workload Identity を使用（推奨）
- または Google Secret Manager に移行
- 環境変数経由でのクレデンシャル注入

#### 3. **データベースパスワードの平文保存**
**現状の問題:**
- `env/.env.common` に `POSTGRES_PASSWORD (実際の値は隠蔽)`
- 簡単なパスワードが使用されている

**推奨対応:**
```bash
# 強力なパスワードを生成
openssl rand -base64 32

# Cloud SQL の場合は IAM 認証を使用
# Secret Manager に保存して起動時に取得
```

---

### 🟠 **高優先度（High）**

#### 4. **HTTPS/TLS設定の強化**
**現状の問題:**
- nginx の TLS 設定はあるが、証明書管理が手動
- HTTP から HTTPS へのリダイレクトが条件付き

**推奨対応:**
```nginx
# app/nginx/conf.d/app.conf
server {
    listen 80;
    server_name _;
    # 全てのHTTPリクエストをHTTPSにリダイレクト（本番環境）
    return 301 https://$host$request_uri;
}

server {
    listen 443 ssl http2;
    
    # 強力な TLS 設定
    ssl_protocols TLSv1.3;  # TLSv1.2 は非推奨
    ssl_prefer_server_ciphers off;
    ssl_ciphers 'TLS_AES_128_GCM_SHA256:TLS_AES_256_GCM_SHA384:TLS_CHACHA20_POLY1305_SHA256';
    
    # HSTS の強化
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains; preload" always;
    
    # セキュリティヘッダーの追加
    add_header Content-Security-Policy "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline';" always;
    add_header Permissions-Policy "geolocation=(), microphone=(), camera=()" always;
}
```

#### 5. **認証・認可の実装不足**
**現状の問題:**
- 認証基盤は実装されているが、実際のエンドポイント保護が不十分
- `deps.py` にJWT認証の雛形はあるが未使用

**推奨対応:**
- Google Cloud IAP (Identity-Aware Proxy) を有効化
- または JWT認証を全エンドポイントに適用
- ロール・権限ベースのアクセス制御を実装

#### 6. **レート制限の未実装**
**現状:**
- API呼び出しにレート制限が設定されていない

**推奨対応:**
```python
# slowapi または fastapi-limiter の導入
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded

limiter = Limiter(key_func=get_remote_address)
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)

@app.get("/api/endpoint")
@limiter.limit("10/minute")  # 1分間に10リクエストまで
async def endpoint():
    pass
```

---

### 🟡 **中優先度（Medium）**

#### 7. **環境変数とシークレットの分離**
**現状:**
- APIキーが環境変数ファイルに平文で記載される可能性

**推奨対応:**
```bash
# GCP Secret Manager を使用
gcloud secrets create openai-api-key --data-file=-
gcloud secrets add-iam-policy-binding openai-api-key \
  --member="serviceAccount:PROJECT_ID@appspot.gserviceaccount.com" \
  --role="roles/secretmanager.secretAccessor"
```

#### 8. **ログの機密情報マスキング**
**推奨対応:**
```python
# backend_shared でのロギング設定にフィルター追加
import re

class SensitiveDataFilter(logging.Filter):
    def filter(self, record):
        # パスワード、トークン、APIキーをマスキング
        if hasattr(record, 'msg'):
            record.msg = re.sub(r'(password|token|api[_-]?key)[\s:=]+\S+', r'\1=***', str(record.msg), flags=re.IGNORECASE)
        return True
```

#### 9. **Content Security Policy (CSP) の設定**
**推奨対応:**
フロントエンドの `index.html` にメタタグを追加:
```html
<meta http-equiv="Content-Security-Policy" 
      content="default-src 'self'; 
               script-src 'self' 'unsafe-inline' 'unsafe-eval'; 
               style-src 'self' 'unsafe-inline'; 
               img-src 'self' data: https:; 
               connect-src 'self' https://your-api-domain.com;">
```

#### 10. **Dockerコンテナのセキュリティ**
**現状:**
- 一部のサービスで `user: "0:0"` (root実行)

**推奨対応:**
```yaml
# ledger_api の user: "0:0" を削除
# 全コンテナを非rootで実行（既に core_api などは対応済み）
```

---

## 実装優先順位のまとめ

| 優先度 | 項目 | 実装難易度 | 影響度 | 推定工数 |
|--------|------|-----------|--------|----------|
| 🔴 Critical | CORS設定修正 | 低 | 高 | 1-2時間 |
| 🔴 Critical | GCP鍵管理の改善 | 中 | 高 | 2-4時間 |
| 🔴 Critical | DBパスワード強化 | 低 | 高 | 30分-1時間 |
| 🟠 High | TLS設定強化 | 中 | 高 | 2-3時間 |
| 🟠 High | 認証・認可の完全実装 | 高 | 高 | 4-8時間 |
| 🟠 High | レート制限実装 | 中 | 中 | 2-3時間 |
| 🟡 Medium | Secret Manager移行 | 中 | 中 | 2-4時間 |
| 🟡 Medium | ログマスキング | 低 | 中 | 1-2時間 |
| 🟡 Medium | CSP設定 | 低 | 中 | 1時間 |
| 🟡 Medium | Root実行の削除 | 低 | 中 | 30分 |

---

## 推奨実施順序

1. **即時対応（Critical項目）**: CORS設定とDBパスワードの修正
2. **GCP移行前**: GCP鍵管理とTLS設定の強化
3. **公開後**: 認証・認可とレート制限の実装
4. **継続改善**: 残りのMedium項目の対応

---

## 補足事項

- 本レポートはコードベースの静的分析に基づくものであり、動的テストによる検証が必要です
- GCP固有のセキュリティ要件（Cloud Armor、VPC Service Controlsなど）を追加で検討してください
- 定期的なセキュリティ監査と依存関係の更新を推奨します

---

## 参考資料

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Google Cloud Security Best Practices](https://cloud.google.com/security/best-practices)
- [FastAPI Security](https://fastapi.tiangolo.com/tutorial/security/)</content>
<parameter name="filePath">/home/koujiro/work_env/22.Work_React/sanbou_app/docs/20251203_SECURITY_AUDIT_REPORT.md