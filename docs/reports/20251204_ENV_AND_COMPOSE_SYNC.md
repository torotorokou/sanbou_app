# 環境変数と Docker Compose ファイルの同期・整理作業

**作業日**: 2024年12月4日  
**ブランチ**: `refactor/env-and-compose-sync`  
**目的**: 複数の .env ファイルと docker-compose.yml を整理・同期し、環境間の一貫性を確保

---

## 実施内容サマリ

### 1. .env ファイルの同期と整理

#### 基準ファイルの確立

- **`env/.env.local_dev`** を「環境変数スキーマの基準（Source of Truth）」として確立
- 全ての環境変数定義はこのファイルを参照して同期

#### 各 .env ファイルの更新

**env/.env.local_dev**

- ヘッダーコメントに「環境変数スキーマの基準」であることを明記
- 他の環境のテンプレートとなる完全なキー定義を維持

**env/.env.local_demo**

- キー構成を .env.local_dev と統一
- `VITE_API_BASE_URL` の設定を `/core_api` に統一（local_dev と同様）
- ポート設定を明確化（5174, 8011-8015, 5433）
- `sanbou_app_demo` ユーザー使用を推奨する注釈を追加

**env/.env.local_stg**

- RAG_GCS_URI の設定を追加
- GCS_LEDGER_BUCKET_DEV キーを追加（他環境との整合性のため）
- セクション構成を .env.local_dev と統一

**env/.env.vm_stg**

- GCS_LEDGER_BUCKET_DEV キーを追加
- RAG_GCS_URI のコメントを追加
- Forecast Worker 設定のコメントを整理

**env/.env.vm_prod**

- GCS_LEDGER_BUCKET_DEV キーを追加（全環境で同じキーセットを維持）
- RAG_GCS_URI のコメントを追加
- セクション構成を統一

**env/.env.common**

- ヘッダーコメントを更新し、読み込み順序を明記
- 既存の共通設定を維持（十分に整理されていたため大きな変更なし）

**env/.env.example**

- 完全なテンプレートとして再構築
- 全ての必要なキーを .env.local_dev を基準に記載
- CHANGEME プレフィックスを使用してダミー値を明示
- 各環境のサンプル設定をコメントアウトして記載
- API キーやシークレットの生成方法をコメントで説明

---

### 2. docker-compose ファイルの整理

#### 環境コメントの追加

各 docker-compose.\*.yml ファイルに以下を追加：

- 対応する ENV 値
- 使用する .env ファイルの組み合わせ
- 環境の特徴・用途

**docker/docker-compose.dev.yml**

```yaml
## docker-compose.dev.yml (ローカル開発環境 - ENV=local_dev 用)
## - Makefile 経由で起動: make up ENV=local_dev
## - 使用する env ファイル: env/.env.common + env/.env.local_dev + secrets/.env.local_dev.secrets
## - 特徴: ホットリロード有効、開発用ポート使用、ボリュームマウント
```

**docker/docker-compose.local_demo.yml**

```yaml
## docker-compose.local_demo.yml (ローカルデモ環境 - ENV=local_demo 用)
## - Makefile 経由で起動: make up ENV=local_demo
## - 使用する env ファイル: env/.env.common + env/.env.local_demo + secrets/.env.local_demo.secrets
## - 特徴: local_dev と完全分離、独立したポート・DB・データディレクトリ
```

**docker/docker-compose.stg.yml**

```yaml
## docker-compose.stg.yml (ステージング環境 - ENV=local_stg / ENV=vm_stg 用)
## - Makefile 経由で起動:
##   * ローカルSTG: make up ENV=local_stg (env/.env.local_stg 使用)
##   * GCP VM STG: make up ENV=vm_stg (env/.env.vm_stg 使用)
```

**docker/docker-compose.prod.yml**

```yaml
## docker-compose.prod.yml (本番環境 - ENV=vm_prod 用)
## - Makefile 経由で起動: make up ENV=vm_prod
## - 使用する env ファイル: env/.env.common + env/.env.vm_prod + secrets/.env.vm_prod.secrets
```

#### secrets ファイル参照の追加

**stg.yml と prod.yml の全サービスに secrets ファイル参照を追加**:

```yaml
env_file:
  - ../env/.env.common
  - ../env/.env.${STG_ENV_FILE} # または ../env/.env.vm_prod
  - ../secrets/.env.${STG_ENV_FILE}.secrets # 追加
```

影響を受けたサービス：

- core_api
- plan_worker
- ai_api
- ledger_api
- rag_api
- manual_api

#### ハードコード値の env 参照化

**docker-compose.local_demo.yml**

- DB healthcheck の `pg_isready` コマンドを環境変数参照に変更
  - 変更前: `pg_isready -U myuser -d sanbou_demo`
  - 変更後: `pg_isready -U $${POSTGRES_USER} -d $${POSTGRES_DB}`

#### TZ 環境変数の統一

- docker-compose.local_demo.yml の全サービスに `TZ=Asia/Tokyo` を追加
- 他の compose ファイルと設定を統一

---

### 3. Makefile の更新

#### 環境マッピングドキュメントの追加

```makefile
## =============================================================
## 環境マッピング (Environment Mapping)
## =============================================================
## ENV 値と対応する .env ファイル・docker-compose.yml の関係:
##
## ENV=local_dev  → docker/docker-compose.dev.yml
##                → env/.env.common + env/.env.local_dev + secrets/.env.local_dev.secrets
##                → ローカル開発環境（ホットリロード有効）
##
## ENV=local_demo → docker/docker-compose.local_demo.yml
##                → env/.env.common + env/.env.local_demo + secrets/.env.local_demo.secrets
##                → ローカルデモ環境（local_dev と完全分離）
##
## ENV=local_stg  → docker/docker-compose.stg.yml (STG_ENV_FILE=local_stg)
##                → env/.env.common + env/.env.local_stg + secrets/.env.local_stg.secrets
##                → ローカルSTG検証環境（本番近似構成、nginx 経由）
##
## ENV=vm_stg     → docker/docker-compose.stg.yml (STG_ENV_FILE=vm_stg)
##                → env/.env.common + env/.env.vm_stg + secrets/.env.vm_stg.secrets
##                → GCP VM ステージング環境
##
## ENV=vm_prod    → docker/docker-compose.prod.yml
##                → env/.env.common + env/.env.vm_prod + secrets/.env.vm_prod.secrets
##                → GCP VM 本番環境
##
## 注意: 環境変数スキーマの基準（Source of Truth）は env/.env.local_dev です
## =============================================================
```

---

## 変更されたファイル一覧

```
M docker/docker-compose.dev.yml       - 環境コメント追加
M docker/docker-compose.local_demo.yml - 環境コメント追加、TZ統一、ハードコード値修正
M docker/docker-compose.prod.yml      - 環境コメント追加、secrets参照追加
M docker/docker-compose.stg.yml       - 環境コメント追加、secrets参照追加
M env/.env.common                      - ヘッダーコメント改善
M env/.env.example                     - 完全なテンプレートとして再構築
M env/.env.local_dev                   - Source of Truth として明記
M env/.env.local_demo                  - キー構成統一、コメント改善
M env/.env.local_stg                   - キー追加、セクション構成統一
M env/.env.vm_prod                     - キー追加、コメント改善
M env/.env.vm_stg                      - キー追加、コメント改善
M makefile                             - 環境マッピングドキュメント追加
```

---

## 整合性チェック結果

### Docker Compose 構文検証

すべての docker-compose.yml ファイルが構文的に正しいことを確認：

```
✓ docker-compose.dev.yml is valid
✓ docker-compose.local_demo.yml is valid
✓ docker-compose.stg.yml (local_stg) is valid
✓ docker-compose.stg.yml (vm_stg) is valid
✓ docker-compose.prod.yml is valid
```

### 環境変数キーの整合性

- .env.local_dev を基準として、全環境で同じキーセットを維持
- 環境ごとに値は異なるが、キー名とフォーマットは統一
- deprecated な変数（VITE_API_BASE_URL など）は明示的にコメントで注記

---

## 主要な改善点

### 1. 一貫性の向上

- 全ての環境で同じキーセットを使用
- コメントの形式とセクション構成を統一
- docker-compose.yml の env_file セクションを標準化

### 2. ドキュメント化の充実

- 各ファイルの役割と用途を明確化
- 環境マッピングを Makefile に記載
- .env.example を完全なテンプレートとして整備

### 3. セキュリティの強化

- secrets ファイル参照を stg/prod の全サービスに追加
- .env.example にダミー値を使用し、実際の値の記載を防止
- パスワード・API キーは必ず secrets/ ファイルで管理することを明記

### 4. 保守性の向上

- .env.local_dev を基準とすることで、キー追加時の同期が容易に
- 環境ごとの差分が明確化
- deprecated な変数を明示的にマーク

---

## 今後の運用方針

### 新しい環境変数の追加手順

1. `env/.env.local_dev` に新しいキーを追加（適切なコメント付き）
2. 他の全ての .env ファイルに同じキーを追加（環境に応じた値を設定）
3. `.env.example` にもダミー値で追加
4. 必要に応じて docker-compose.yml で環境変数参照を追加

### 環境変数の削除手順

1. コード・compose ファイルでの参照を全て削除
2. 各 .env ファイルから該当キーを削除（または deprecated としてコメントアウト）
3. `.env.example` からも削除

### 定期的なメンテナンス

- 未使用の環境変数を定期的に検索・削除
- .env.local_dev と他環境の同期状態を確認
- deprecated とマークされた変数の参照が残っていないか確認

---

## 注意事項

### secrets ファイルの管理

- `secrets/.env.*.secrets` ファイルは Git 管理対象外
- 本番環境のパスワードや API キーは必ず secrets/ で管理
- secrets ファイルのテンプレートは `secrets/.env.secrets.template` を参照

### 既存運用への影響

- 既存の値や設定は変更していない（キーの追加とコメントの改善のみ）
- 既に稼働中の環境には影響なし
- 新規デプロイ時には .env ファイルの再確認を推奨

### バックアップ

- 変更前のファイルは `docker/archive/` に保管済み
- 問題が発生した場合は Git で revert 可能

---

## 関連ドキュメント

- `env/.env.example` - 環境変数設定の完全なテンプレート
- `secrets/.env.secrets.template` - シークレット設定のテンプレート
- `docs/db/20251204_db_user_design.md` - DB ユーザー設計
- `makefile` - 環境マッピングと make コマンド一覧
