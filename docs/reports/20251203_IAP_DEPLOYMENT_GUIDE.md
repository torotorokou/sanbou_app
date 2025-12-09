# IAP（Identity-Aware Proxy）導入ガイド

**作成日：** 2024年12月3日  
**対象：** sanbou_app 本番環境・ステージング環境  
**目的：** Google Cloud IAP による認証基盤の導入手順

---

## 概要

このガイドでは、sanbou_app に Google Cloud の Identity-Aware Proxy (IAP) を導入する手順をまとめています。

### IAP とは

Google Cloud の IAP は、アプリケーションへのアクセスを Google アカウントで認証・認可する仕組みです。
HTTPS Load Balancer の背後に配置され、許可されたユーザーのみがアプリケーションにアクセスできるようになります。

### 導入フェーズ

- **第1フェーズ：** GCP 側の設定のみで、許可された Google アカウント以外はアプリに一切アクセスできない状態にする
- **第2フェーズ：** `/auth/me` エンドポイントで認証済みユーザー情報を取得し、フロントエンドに表示する

---

## 前提条件

- GCP プロジェクトが作成済み
- HTTPS Load Balancer が構築済み
- アプリケーションが Cloud Run または Compute Engine VM で稼働中
- ドメイン名が設定済み（例：`https://sanbou-app.jp`, `https://stg.sanbou-app.jp`）

---

## 第1フェーズ：IAP によるアクセス制御

### 1. GCP Console での IAP 有効化

#### 1-1. IAP を有効にする

1. GCP Console → **セキュリティ** → **Identity-Aware Proxy** に移動
2. 対象の Backend Service を選択（HTTPS Load Balancer に紐付いているもの）
3. 右上の **IAP を有効にする** をクリック

#### 1-2. OAuth 同意画面の設定

初回のみ、OAuth 同意画面の設定が必要です：

1. **アプリケーション名：** sanbou_app（任意）
2. **サポートメール：** 管理者のメールアドレス
3. **承認済みドメイン：** `sanbou-app.jp`
4. **スコープ：** デフォルト（openid, email, profile）

#### 1-3. アクセス権限の設定

1. IAP 画面で対象の Backend Service の **アクセス権限** をクリック
2. **プリンシパルを追加** をクリック
3. **新しいプリンシパル** に以下を追加：
   - 個別ユーザー：`user@honest-recycle.co.jp`
   - グループ全体：`group:dev-team@honest-recycle.co.jp`
4. **ロール** に `IAP-secured Web App User` を選択
5. **保存**

### 2. IAP_AUDIENCE の取得

IAP が有効になると、JWT 検証用の `audience` 値が発行されます。

#### 2-1. gcloud コマンドで取得

```bash
# Backend Service の audience を取得
gcloud compute backend-services describe <BACKEND_SERVICE_NAME> \
  --global \
  --format="value(iap.oauth2ClientId)"
```

出力例：
```
/projects/123456789/global/backendServices/987654321
```

この値を次のステップで環境変数に設定します。

#### 2-2. または GCP Console から取得

1. **セキュリティ** → **Identity-Aware Proxy**
2. 対象の Backend Service をクリック
3. **詳細を表示** から `audience` 値をコピー

### 3. 環境変数の設定

#### 3-1. ステージング環境（`env/.env.vm_stg`）

```bash
# env/.env.vm_stg
IAP_ENABLED=true
# IAP_AUDIENCE=/projects/123456789/global/backendServices/987654321  # 例
```

#### 3-2. 本番環境（`env/.env.vm_prod`）

```bash
# env/.env.vm_prod
IAP_ENABLED=true
# IAP_AUDIENCE=/projects/123456789/global/backendServices/987654321  # 例
```

**注意：** `IAP_AUDIENCE` は環境ごとに異なる可能性があります。必ず各環境の値を確認してください。

### 4. アプリケーションのデプロイ

環境変数を更新したら、アプリケーションを再デプロイします：

```bash
# docker-compose を使用している場合
docker-compose -f docker/docker-compose.prod.yml down
docker-compose -f docker/docker-compose.prod.yml up -d

# または Cloud Run の場合
gcloud run deploy core-api --set-env-vars IAP_ENABLED=true,IAP_AUDIENCE_VAR=<AUDIENCE>
```

### 5. 動作確認

#### 5-1. アクセス制御の確認

1. ブラウザで `https://sanbou-app.jp` にアクセス
2. IAP のログイン画面が表示されることを確認
3. 許可された Google アカウントでログイン
4. アプリケーションが正常に表示されることを確認

#### 5-2. 未承認ユーザーの確認

1. 許可されていない Google アカウントでログインを試みる
2. **アクセス拒否** のエラーが表示されることを確認

---

## 第2フェーズ：/auth/me による ユーザー情報表示

第1フェーズが完了していれば、**追加のコード変更なし**で第2フェーズも動作します。

### 1. バックエンドの動作確認

#### 1-1. /auth/me エンドポイントのテスト

```bash
# ブラウザまたは curl でアクセス
curl -H "Authorization: Bearer $(gcloud auth print-identity-token)" \
  https://sanbou-app.jp/core_api/auth/me
```

**期待されるレスポンス：**
```json
{
  "email": "user@honest-recycle.co.jp",
  "display_name": "user",
  "user_id": "iap_user",
  "role": "user"
}
```

#### 1-2. ログの確認

```bash
# Cloud Run の場合
gcloud logging read "resource.type=cloud_run_revision AND textPayload:\"IAP JWT authentication successful\"" --limit 10

# または docker-compose の場合
docker logs core_api | grep "IAP JWT authentication successful"
```

### 2. フロントエンドの動作確認

#### 2-1. Sidebar のユーザー情報表示

1. アプリケーションにログイン
2. 左サイドバー上部・下部に **「ログイン中：{メールアドレス}」** が表示されることを確認

#### 2-2. ブラウザ DevTools での確認

1. DevTools の **Network** タブを開く
2. `/core_api/auth/me` のリクエストを確認
3. レスポンスに正しいユーザー情報が含まれることを確認

---

## トラブルシューティング

### JWT 検証エラー（401 Unauthorized）

**症状：** `/auth/me` にアクセスすると 401 エラーが返る

**原因と対策：**
1. `IAP_AUDIENCE` が正しく設定されているか確認
2. IAP が正しく有効化されているか GCP Console で確認
3. `IAP_ENABLED=true` が設定されているか確認

**ログの確認：**
```bash
docker logs core_api | grep "IAP JWT verification failed"
```

### ドメインエラー（403 Forbidden）

**症状：** ログインはできるが、アプリケーションにアクセスできない

**原因と対策：**
1. ユーザーのメールドメインが `@honest-recycle.co.jp` であることを確認
2. 他のドメインを許可する場合は `iap_auth_provider.py` の `allowed_domain` を修正

### ヘルスチェックの除外

**症状：** Load Balancer のヘルスチェックが失敗する

**原因と対策：**
1. `/health` と `/healthz` が IAP 除外パスに含まれているか確認
2. `auth_middleware.py` の `excluded_paths` を確認
3. GCP Console で Backend Service のヘルスチェックパスが `/health` になっているか確認

---

## セキュリティ上の注意事項

### 1. DEBUG モードの無効化

本番環境では必ず `DEBUG=false` を設定してください。
`DEBUG=true` の場合、`/docs` と `/redoc` が公開され、API 仕様が誰でも閲覧可能になります。

```bash
# env/.env.vm_prod
DEBUG=false
```

### 2. 許可ドメインの制限

デフォルトでは `@honest-recycle.co.jp` のみが許可されています。
外部パートナーのアクセスが必要な場合は、慎重に検討してください。

### 3. IAP のバイパスに注意

- Load Balancer を経由しない直接アクセス（VM の IP アドレス直叩き）は IAP で保護されません
- Firewall ルールで Load Balancer からのアクセスのみを許可してください

### 4. ログの監視

IAP 認証の失敗ログを定期的に監視し、不正アクセスの試みを検出してください：

```bash
gcloud logging read "textPayload:\"IAP JWT verification failed\"" --limit 100
```

---

## 参考資料

- [Google Cloud IAP 公式ドキュメント](https://cloud.google.com/iap/docs)
- [IAP による認証のベストプラクティス](https://cloud.google.com/iap/docs/concepts-best-practices)
- sanbou_app 認証アーキテクチャドキュメント：`docs/20251203_IAP_AUTHENTICATION_IMPLEMENTATION.md`

---

## 変更履歴

| 日付 | 変更内容 | 担当者 |
|------|---------|--------|
| 2024-12-03 | 初版作成 | - |

