# メンテナンスページ 運用マニュアル

## 🎯 現在の状態

✅ **すべて設定完了！**

- Cloud Run デプロイ済み
- LB 設定完了
- IAP 有効化済み（domain:honest-recycle.co.jp）
- 現在: **メンテナンスモード ON** 🔧

**アクセス**: https://honest.sanbou-app.jp/  
（@honest-recycle.co.jp のアカウントで Google ログイン後に 503 ページが表示されます）

---

## � 次回以降のメンテナンス作業手順

### 計画メンテナンスの流れ

1. **メンテナンス開始**
   ```bash
   cd ops/maintenance
   make maintenance-on
   ```

2. **メンテナンス作業実施**
   - DB マイグレーション
   - アプリケーション更新
   - 動作確認

3. **メンテナンス終了**
   ```bash
   cd ops/maintenance
   make maintenance-off
   ```

4. **本番動作確認**
   ```bash
   # ブラウザで https://honest.sanbou-app.jp/ にアクセス
   # アプリケーションが正常に動作することを確認
   ```

### 緊急メンテナンスの流れ

```bash
# 即座にメンテナンスモードに切り替え
cd ops/maintenance
make maintenance-on

# 問題対応...

# 復旧
make maintenance-off
```

---

## 🔄 メンテナンスモード切替コマンド

### メンテナンス開始

```bash
# ルートディレクトリから実行可能
make maintenance-on PROJECT_ID=honest-sanbou-app-prod

# または ops/maintenance/ から
cd ops/maintenance
make maintenance-on PROJECT_ID=honest-sanbou-app-prod
```

または手動で：

```bash
gcloud compute url-maps set-default-service sanbou-prod-lb \
  --default-service maintenance-page-backend \
  --global \
  --project=honest-sanbou-app-prod
```

### メンテナンス終了（本番復帰）

```bash
# ルートディレクトリから実行可能
make maintenance-off PROJECT_ID=honest-sanbou-app-prod

# または ops/maintenance/ から
cd ops/maintenance
make maintenance-off PROJECT_ID=honest-sanbou-app-prod
```

または手動で：

```bash
gcloud compute url-maps set-default-service sanbou-prod-lb \
  --default-service sanbou-prod-backend \
  --global \
  --project=honest-sanbou-app-prod
```

### 現在の状態確認

```bash
# ルートディレクトリから実行可能
make maintenance-status PROJECT_ID=honest-sanbou-app-prod

# または ops/maintenance/ から
cd ops/maintenance
make maintenance-status PROJECT_ID=honest-sanbou-app-prod
```

**反映時間**: 数秒〜1分程度

---

## 🔧 メンテナンスページの更新

HTML やメッセージを変更した場合：

```bash
cd ops/maintenance
# main.py を編集
vim cloudrun/main.py

# デプロイ
make deploy-local

# 確認（メンテナンスモード中の場合）
# https://honest.sanbou-app.jp/ にアクセス
```

---

## 📋 よく使うコマンド

```bash
cd ops/maintenance

# メンテナンスモード ON
make maintenance-on

# メンテナンスモード OFF
make maintenance-off

# 現在の状態確認
make maintenance-status

# Cloud Run サービス状態確認
make check

# デプロイ（更新時）
make deploy-local
```

---

## ⚠️ 注意事項

- メンテナンスモード中は @honest-recycle.co.jp でログイン後に HTTP 503 を返します
- IAP により他のドメインのユーザーはアクセスできません
- **必ず `make maintenance-off` で本番に復帰してください**
- 切り替え前に `make maintenance-status` で現在の状態を確認することを推奨
