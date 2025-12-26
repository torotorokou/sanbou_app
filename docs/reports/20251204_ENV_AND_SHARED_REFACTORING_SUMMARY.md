# 環境変数化とbackend_shared集約の調査レポート

作成日: 2024-12-04  
ブランチ: feature/env-and-shared-refactoring  
担当: GitHub Copilot

---

## 📋 エグゼクティブサマリー

バックエンド全体のセキュリティ、保守性、コード品質を向上させるため、以下2つの観点から包括的な調査とリファクタリング計画を策定しました:

1. **環境変数化**: ハードコード値を `.env` ファイルに移行
2. **backend_shared 集約**: 重複する共通処理を統一ライブラリに集約

### 主要な成果物

| ドキュメント                                                                              | 内容                                 | ページ数 |
| ----------------------------------------------------------------------------------------- | ------------------------------------ | -------- |
| [ENV_HARDCODE_AUDIT.md](./20251204_ENV_HARDCODE_AUDIT.md)                                 | ハードコード値の監査と環境変数化計画 | 15+      |
| [BACKEND_SHARED_CONSOLIDATION_PLAN.md](./20251204_BACKEND_SHARED_CONSOLIDATION_PLAN.md)   | 共通処理集約の詳細計画               | 20+      |
| [RAG_API_DATETIME_REFACTORING.md](./refactoring/20251204_RAG_API_DATETIME_REFACTORING.md) | リファクタリング実例                 | 10+      |

### 新規実装コード

| モジュール     | ファイル                                         | 行数      |
| -------------- | ------------------------------------------------ | --------- |
| datetime_utils | `backend_shared/utils/datetime_utils.py`         | 225行     |
| cors_config    | `backend_shared/infra/frameworks/cors_config.py` | 145行     |
| base_settings  | `backend_shared/config/base_settings.py`         | 180行     |
| **合計**       |                                                  | **550行** |

### 期待される効果

- **コード削減**: 約850行の重複コード削減
- **セキュリティ向上**: 機密情報の環境変数化
- **保守性向上**: 共通処理の一元管理
- **開発効率向上**: 新規サービス開発の初期設定が簡単に

---

## 🔍 調査概要

### 調査範囲

全6つのバックエンドサービスを対象に調査:

1. **core_api** - BFF（Backend for Frontend）
2. **ledger_api** - 帳票生成サービス
3. **ai_api** - Gemini API ラッパー
4. **rag_api** - RAG（検索拡張生成）サービス
5. **manual_api** - マニュアル管理サービス
6. **plan_worker** - 予測計算ワーカー

### 調査項目

#### 3-1. 環境変数化すべきハードコード値

以下のカテゴリで洗い出し:

- ✅ APIキー / トークン / シークレット
- ✅ DB接続文字列 / ユーザー名 / パスワード
- ✅ GCPプロジェクトID / バケット名 / リージョン
- ✅ IAP関連のURL / Client ID
- ✅ 外部サービスのURL / エンドポイント
- ✅ 許可ドメインなど認証・認可の条件

#### 3-2. backend_shared に集約すべき共通処理

以下のカテゴリで洗い出し:

- ✅ ロギングの初期化処理
- ✅ エラーハンドリング / レスポンス形式
- ✅ IAP認証・JWT検証・メールドメインチェック
- ✅ GCSクライアント生成とダウンロード/アップロード処理
- ✅ 日付/時刻変換ユーティリティ（JST変換など）
- ✅ CORSミドルウェア
- ✅ 環境変数読み込みパターン

---

## 📊 調査結果サマリー

### 環境変数化候補

#### 🔴 高優先度（セキュリティ/必須）

| 項目                 | 現在の値                                          | 推奨環境変数名           | 影響範囲   |
| -------------------- | ------------------------------------------------- | ------------------------ | ---------- |
| 許可ドメイン         | `"honest-recycle.co.jp"`                          | `ALLOWED_EMAIL_DOMAIN`   | core_api   |
| IAP公開鍵URL         | `"https://www.gstatic.com/iap/verify/public_key"` | `IAP_PUBLIC_KEY_URL`     | core_api   |
| レポートシークレット | `"change-me-in-production"`                       | `REPORT_ARTIFACT_SECRET` | ledger_api |

#### 🟡 中優先度（デプロイ柔軟性）

| 項目           | 現在の値                                          | 推奨環境変数名   | 影響範囲            |
| -------------- | ------------------------------------------------- | ---------------- | ------------------- |
| Gemini API URL | `"https://generativelanguage.googleapis.com/..."` | `GEMINI_API_URL` | ai_api              |
| CORS Origins   | `"http://localhost:5173,..."`                     | `CORS_ORIGINS`   | 全サービス          |
| タイムゾーン   | `"Asia/Tokyo"`                                    | `APP_TIMEZONE`   | rag_api, ledger_api |

### 共通処理の重複状況

#### ✅ 既に統一済み

- **ロギング初期化**: 全サービスで `backend_shared.application.logging` を使用

#### ⚠️ 部分的に重複

| 項目               | 重複サービス                          | 削減可能コード量 | 優先度 |
| ------------------ | ------------------------------------- | ---------------- | ------ |
| エラーハンドリング | core_api, manual_api, ai_api, rag_api | ~500行           | 🔥 高  |
| 環境変数読み込み   | 全サービス                            | ~200行           | 🟡 中  |
| CORS設定           | 全サービス                            | ~100行           | 🟡 中  |

#### 🔴 完全に重複

| 項目          | 重複サービス        | 削減可能コード量 | 優先度 |
| ------------- | ------------------- | ---------------- | ------ |
| 日付/時刻変換 | rag_api, ledger_api | ~50行            | 🔥 高  |

#### 🟡 特殊ケース

- **IAP認証**: core_api のみ実装（他は内部API）→ 将来的に検討
- **GCS操作**: 削除済み → 対応不要

---

## 🎯 実装した解決策

### 1. datetime_utils モジュール

**目的**: タイムゾーン処理の統一とパフォーマンス最適化

**主な機能**:

- `get_app_timezone()`: アプリケーションタイムゾーンの取得（キャッシュ済み）
- `now_in_app_timezone()`: 現在時刻の取得
- `to_app_timezone()`: タイムゾーン変換
- `format_datetime_jp()`: 日本語形式フォーマット
- `format_date_jp()`: 日付フォーマット

**使用例**:

```python
from backend_shared.utils.datetime_utils import now_in_app_timezone, format_datetime_jp

timestamp = format_datetime_jp(now_in_app_timezone())
# '2024年12月04日 15:30'
```

### 2. cors_config モジュール

**目的**: CORS設定の統一とセキュリティ強化

**主な機能**:

- `get_cors_origins()`: 環境変数からオリジンリスト取得
- `setup_cors()`: FastAPIへのCORSミドルウェア設定

**使用例**:

```python
from backend_shared.infra.frameworks.cors_config import setup_cors

app = FastAPI()
setup_cors(app)  # 環境変数から自動取得
```

### 3. base_settings モジュール

**目的**: 設定クラスの共通化と型安全性の確保

**主な機能**:

- `BaseAppSettings`: 全サービス共通の基底設定クラス
- ステージ設定、デバッグモード、API基本情報、CORS設定

**使用例**:

```python
from backend_shared.config.base_settings import BaseAppSettings

class AiApiSettings(BaseAppSettings):
    API_TITLE: str = "AI_API"
    GEMINI_API_KEY: str = ""
```

---

## 📝 推奨する実装手順

### Phase 1: backend_shared に新規モジュール追加（完了✅）

- ✅ `datetime_utils.py` を作成
- ✅ `cors_config.py` を作成
- ✅ `base_settings.py` を作成
- ✅ `backend_shared/utils/__init__.py` を更新

### Phase 2: 環境変数の追加（次のステップ）

`.env.common` に追加:

```bash
# === Security / Authentication ===
ALLOWED_EMAIL_DOMAIN=honest-recycle.co.jp
IAP_PUBLIC_KEY_URL=https://www.gstatic.com/iap/verify/public_key

# === Application Settings ===
APP_TIMEZONE=Asia/Tokyo

# === API URLs (External Services) ===
GEMINI_API_URL=https://generativelanguage.googleapis.com/v1beta/models/gemini-1.5-flash:generateContent
```

`secrets/.env.*.secrets` に追加:

```bash
# === ledger_api Report Artifact Secret ===
REPORT_ARTIFACT_SECRET=<strong-random-secret>
```

### Phase 3: 1サービスで試験導入（rag_api）

1. rag_api で `datetime_utils` を使用
   - `dummy_response_service.py` をリファクタリング
   - `ai_response_service.py` をリファクタリング
2. rag_api で `cors_config` を使用
   - `main.py` のCORS設定を変更
3. 動作確認とテスト

### Phase 4: 全サービスへの展開

1. エラーハンドリング統一
   - core_api の独自実装を削除
   - manual_api, ai_api, rag_api で統一版使用
2. 日付処理統一
   - ledger_api で `datetime_utils` 使用
3. CORS設定統一
   - 全サービスで `cors_config` 使用

---

## 📈 期待される効果

### コスト削減

| 項目       | Before            | After           | 削減量  |
| ---------- | ----------------- | --------------- | ------- |
| コード量   | ~850行の重複      | 統一実装        | 約850行 |
| 保守コスト | 6サービス個別管理 | 1箇所で統一管理 | 約80%   |

### 品質向上

- ✅ エラーハンドリングの統一 → ユーザー体験向上
- ✅ ログ出力の統一 → 運用性向上
- ✅ タイムゾーン処理の一貫性 → バグ削減

### セキュリティ向上

- ✅ 機密情報の環境変数化 → Git漏洩リスク低減
- ✅ CORS設定の厳格化 → XSS/CSRF対策強化
- ✅ IAP認証の一元管理 → セキュリティポリシー統一

### 開発効率向上

- ✅ 新規サービス開発時の初期設定が簡単に
- ✅ 共通機能の再利用による開発速度向上
- ✅ バグ修正が全サービスに即座に反映

---

## ⚠️ 注意事項とリスク

### 後方互換性

- ✅ すべての新規機能にはデフォルト値を設定
- ✅ 既存の動作を変更しない
- ✅ 段階的に移行し、各フェーズで動作確認

### デプロイ時の注意

#### ステージング環境

1. 新しい環境変数を設定
2. backend_shared の更新をデプロイ
3. 各サービスの更新をデプロイ
4. 動作確認とテスト

#### 本番環境

1. ステージング環境で十分にテスト
2. 本番環境で環境変数を事前準備
3. ダウンタイムなしのローリングアップデート
4. ロールバック計画の準備

### セキュリティチェックリスト

- [ ] `ALLOWED_EMAIL_DOMAIN` が正しく設定されているか
- [ ] `REPORT_ARTIFACT_SECRET` が強力なランダム文字列か
- [ ] `CORS_ORIGINS` が本番環境で適切に制限されているか
- [ ] シークレット系の値が `secrets/` ディレクトリにあるか
- [ ] `.gitignore` で `secrets/` が除外されているか

---

## 🔗 関連ドキュメント

### 新規作成ドキュメント

1. [ENV_HARDCODE_AUDIT.md](./20251204_ENV_HARDCODE_AUDIT.md)

   - ハードコード値の詳細な監査レポート
   - 環境変数化の推奨リスト
   - BaseSettings 設計案

2. [BACKEND_SHARED_CONSOLIDATION_PLAN.md](./20251204_BACKEND_SHARED_CONSOLIDATION_PLAN.md)

   - 共通処理の重複分析
   - backend_shared への集約計画
   - 4フェーズの実装手順

3. [RAG_API_DATETIME_REFACTORING.md](./refactoring/20251204_RAG_API_DATETIME_REFACTORING.md)
   - rag_api リファクタリングの実例
   - Before/After のコード比較
   - 実装手順の詳細

### 既存ドキュメント

- [ENV_CONSOLIDATION.md](./20251203_ENV_CONSOLIDATION.md) - 環境変数統合の設計方針
- [SECURITY_AUDIT_REPORT.md](./20251203_SECURITY_AUDIT_REPORT.md) - セキュリティ監査レポート
- [backend_shared README](../app/backend/backend_shared/README.md) - 共通ライブラリの使用方法

### 新規実装コード

- `backend_shared/src/backend_shared/utils/datetime_utils.py` (225行)
- `backend_shared/src/backend_shared/infra/frameworks/cors_config.py` (145行)
- `backend_shared/src/backend_shared/config/base_settings.py` (180行)

---

## 🚀 次のステップ

### 短期（今回のPR）

1. ✅ backend_shared に新規モジュールを追加
2. ✅ ドキュメント作成
3. ⬜ PR作成とレビュー
4. ⬜ ステージング環境でテスト

### 中期（次回以降のPR）

1. 環境変数の追加（.env.common、secrets/）
2. rag_api でリファクタリング（datetime_utils、cors_config）
3. 他サービスでエラーハンドリング統一
4. 全サービスでCORS設定統一

### 長期（今後の継続的改善）

1. 新規サービス作成時のテンプレート整備
2. CI/CDでの環境変数検証
3. アーキテクチャドキュメントの継続的更新
4. ベストプラクティス集の作成

---

## 📞 サポートとフィードバック

このリファクタリング計画に関する質問、提案、フィードバックは以下まで:

- **ブランチ**: `feature/env-and-shared-refactoring`
- **ドキュメント**: `docs/` ディレクトリ
- **実装コード**: `app/backend/backend_shared/`

---

**作成者**: GitHub Copilot  
**レビュー**: 必要に応じてチームメンバーによるレビュー  
**最終更新**: 2024-12-04
