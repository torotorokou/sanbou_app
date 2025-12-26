# stg ブランチマージ競合レポート

**作成日**: 2025-12-26  
**対象ブランチ**: dev/forecast ← stg  
**競合ファイル数**: 23件

## 概要

`dev/forecast` ブランチへ `stg` ブランチをマージしようとした際に、23ファイルで競合が発生しました。
主な競合要因は以下の通りです：

1. **Makefile の大規模リファクタリング** (mk/*.mk への分割)
2. **データベース権限周りの変更** (myuser → sanbou_app_dev への移行)
3. **予約機能 (reservation) の同時開発**
4. **backend_shared の共通化と DB関連の変更**

## ブランチの関係

```
dev/forecast (HEAD): c2a07cae - Merge remote-tracking branch 'origin/stg' into dev/forecast
  ↑ 競合発生
stg: 8be8d6dd - Merge pull request #99 from torotorokou/feature/sidebar-drawer-auto-close
```

## 競合ファイル一覧

### 1. ビルド・インフラ関連 (2件)

| ファイル | 競合の内容 |
|---------|-----------|
| `makefile` | stgでmk/*.mkへの分割実施、dev/forecastで独自のENV管理改善 |
| `docker/docker-compose.dev.yml` | サービス定義の変更が競合 |

### 2. データベース・権限関連 (2件)

| ファイル | 競合の内容 |
|---------|-----------|
| `ops/db/legacy/20251204_create_app_db_users.sql` | DB権限管理の変更 |
| `app/backend/backend_shared/tests/test_db_url_builder.py` | DB URL構築テストの変更 |

### 3. backend_shared 共通モジュール (6件)

| ファイル | 競合の内容 |
|---------|-----------|
| `app/backend/backend_shared/src/backend_shared/config/di_providers.py` | 依存性注入の変更 |
| `app/backend/backend_shared/src/backend_shared/config/env_utils.py` | 環境変数ユーティリティの変更 |
| `app/backend/backend_shared/src/backend_shared/db/__init__.py` | DB初期化の変更 |
| `app/backend/backend_shared/src/backend_shared/infra/db/__init__.py` | DB インフラ層の変更 |
| `app/backend/backend_shared/src/backend_shared/infra/frameworks/database.py` | データベースフレームワークの変更 |
| `app/backend/backend_shared/src/backend_shared/utils/dataframe_utils_optimized.py` | DataFrame ユーティリティの最適化 |

### 4. core_api - 予約機能 (6件)

| ファイル | 競合の内容 |
|---------|-----------|
| `app/backend/core_api/app/api/routers/forecast/router.py` | 予測APIルーターの変更 |
| `app/backend/core_api/app/api/routers/reservation/router.py` | 予約APIルーターの変更 |
| `app/backend/core_api/app/api/schemas/reservation.py` | 予約スキーマの変更 |
| `app/backend/core_api/app/config/settings.py` | 設定ファイルの変更 |
| `app/backend/core_api/app/core/domain/reservation.py` | 予約ドメインモデルの変更 |
| `app/backend/core_api/app/infra/adapters/reservation/reservation_repository.py` | 予約リポジトリの変更 |

### 5. core_api - データベース (1件)

| ファイル | 競合の内容 |
|---------|-----------|
| `app/backend/core_api/app/infra/db/db.py` | DB接続管理の変更 |

### 6. plan_worker (1件)

| ファイル | 競合の内容 |
|---------|-----------|
| `app/backend/plan_worker/app/test/common.py` | テスト共通処理の変更 |

### 7. frontend - 予約機能 (5件)

| ファイル | 競合の内容 |
|---------|-----------|
| `app/frontend/src/features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx` | 予約カレンダーUI |
| `app/frontend/src/features/reservation/reservation-calendar/ui/ReservationMonthlyStats.tsx` | 月次統計UI |
| `app/frontend/src/features/reservation/reservation-input/model/useReservationInputVM.ts` | 予約入力VM |
| `app/frontend/src/features/reservation/reservation-input/ui/ReservationInputForm.tsx` | 予約入力フォーム |
| `app/frontend/src/pages/database/ReservationDailyPage.tsx` | 予約ページ |

## 主な変更点の比較

### stg ブランチの主な変更

1. **レスポンシブデザイン改善**
   - サイドバードロワーの自動クローズ機能
   - モバイル対応の強化 (SalesTree, CustomerList, Manual)
   
2. **コード品質改善**
   - print → logger 統一
   - console.log → logger 統一
   - CSS の module.css への変換
   - グローバル CSS の統合
   
3. **機能追加**
   - Feature flags 追加
   - マニュアル動画のローカル配信
   - バンドルサイズ最適化
   
4. **インフラ改善**
   - pre-commit hooks 導入
   - typecheck workflow 追加
   - security check 強化

### dev/forecast ブランチの主な変更

1. **予約機能の実装・拡張**
   - ReservationDailyPage の実装
   - 予約カレンダー・統計機能
   - 予約入力フォームの改善
   
2. **Makefile の改善**
   - ENV 管理の強化
   - nginx 動作確認手順の追加
   - ヘルスチェック URL の統一

## 競合解決の推奨アプローチ

### 優先度 高: ビルド・インフラ

**makefile**
- stg の mk/*.mk 分割を採用（モジュール化のメリット大）
- dev/forecast の ENV 改善部分はマイグレーション後に mk/10_env.mk へ反映

**docker-compose.dev.yml**
- 両方の変更をマージ
- サービス定義の追加は両立可能

### 優先度 高: 予約機能

**backend (6ファイル)**
- 機能的な変更が含まれるため、慎重にマージ
- APIスキーマの互換性を確認
- テストを実行して動作確認

**frontend (5ファイル)**
- UIコンポーネントの変更をマージ
- TypeScript型定義の整合性を確認
- 手動テスト必須

### 優先度 中: backend_shared

**DB関連 (6ファイル)**
- stg の共通化・リファクタリングを優先
- dev/forecast の機能追加は再実装の可能性
- テストでカバレッジ確認

### 優先度 低: その他

**ops/db/legacy/20251204_create_app_db_users.sql**
- stg の myuser 削除を採用
- dev/forecast の変更は不要の可能性

## 競合解決の手順

### ステップ1: 準備
```bash
# 現在の状態を保存
git stash save "WIP before conflict resolution"

# 競合ファイルをバックアップ
mkdir -p tmp/conflict_backup_$(date +%Y%m%d_%H%M%S)
git diff --name-only --diff-filter=U | xargs -I {} cp {} tmp/conflict_backup_$(date +%Y%m%d_%H%M%S)/
```

### ステップ2: Makefile の解決
```bash
# stg の mk/*.mk 分割を採用
git checkout stg -- makefile mk/

# dev/forecast の ENV 改善を mk/10_env.mk に反映（手動）
# → 別途対応
```

### ステップ3: backend_shared の解決
```bash
# stg のリファクタリングを優先採用
git checkout stg -- app/backend/backend_shared/

# dev/forecast の機能追加があれば手動マージ
# → テスト実行で確認
```

### ステップ4: 予約機能の解決
```bash
# 各ファイルを個別に確認しながらマージ
git mergetool app/backend/core_api/app/api/routers/reservation/router.py
# ... 以下同様に全23ファイルを処理
```

### ステップ5: 検証
```bash
# ビルドテスト
make build ENV=local_dev

# 型チェック
cd app/frontend && npm run typecheck

# ユニットテスト
cd app/backend/core_api && pytest

# 手動動作確認
# - 予約機能
# - マニュアル機能
# - ダッシュボード
```

### ステップ6: コミット
```bash
git add .
git commit -m "resolve: stg merge conflicts - adopt stg refactoring + preserve dev/forecast features"
```

## リスク評価

### 高リスク
- **予約機能**: API スキーマ変更による互換性問題の可能性
- **backend_shared**: 共通モジュールの変更が複数サービスに影響

### 中リスク
- **Makefile**: mk/*.mk 分割後の動作確認が必要
- **docker-compose**: サービス起動の確認が必要

### 低リスク
- **CSS/UI**: ビジュアルの確認のみ
- **ログ出力**: 機能への影響は最小限

## 推奨事項

1. **段階的なマージ**
   - まず stg の大規模リファクタリングを採用
   - 次に dev/forecast の機能追加を再実装
   
2. **テスト強化**
   - 予約機能の E2E テスト追加
   - backend_shared の統合テスト実施
   
3. **ドキュメント更新**
   - マージ後の動作確認手順を文書化
   - 新しい Makefile 構造のドキュメント更新

4. **レビュー体制**
   - 予約機能の変更は重点的にレビュー
   - backend_shared の変更は影響範囲を確認

## 参考情報

### 関連ドキュメント
- `docs/backend/20251216_RESERVE_TABLES_MIGRATION.md` - 予約テーブルのマイグレーション
- `docs/database/20251224_myuser_removal_implementation_report.md` - myuser 削除
- `mk/README.md` - 新しい Makefile 構造（作成予定）

### 関連 PR
- #99: Feature/sidebar drawer auto close (stg へマージ済み)
- #94: feature/add-git-ref-build-targets (dev/forecast へマージ済み)

---

**作成者**: GitHub Copilot  
**最終更新**: 2025-12-26
