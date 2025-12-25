# ログ設計・運用方針（sanbou_app 想定）

- 作成日: 2025-11-28
- 対象プロジェクト: sanbou_app
- 対象環境: `local_dev` / `vm_stg` / `vm_prod` など
- 対象: Docker コンテナで動作する各サービス（frontend / core_api / ledger_api / rag_api / job_runner / db など）

---

## 1. ログの役割と種類

ログは「何のために使うか」で 3 つに分けて考える。

### 1.1 アプリケーションログ（技術者向け）

- 対象
  - FastAPI / バッチ / ワーカー / ジョブランナー などのアプリケーションコード
- 目的
  - バグ調査・性能調査・処理フローのトレース
- 代表的な内容の例
  - リクエスト開始・終了
  - 外部 API / DB 呼び出しの結果・所要時間
  - 例外発生時のスタックトレース

### 1.2 アクセス / インフラログ（運用向け）

- 対象
  - nginx / リバースプロキシ
  - DB（PostgreSQL）
  - Docker / OS
- 目的
  - 負荷状況、障害の検知、外形監視
- 代表的な内容の例
  - HTTP アクセスログ（ステータスコード / レイテンシ / パス等）
  - DB 接続エラー、スロークエリ
  - コンテナの再起動ログ

### 1.3 業務ログ（ビジネス向け）

- 対象
  - CSV 取込み、マテビュー更新、月次締め処理などの「業務イベント」
- 目的
  - 「この処理は実行されたか」「成功 / 失敗は？」「誰がいつ実行したか」を後から追跡する
- 保存先
  - DB の `log` スキーマ等に専用テーブルを持つ（例：`log.upload_file`, `log.mv_refresh` など）
- 代表的な内容の例
  - ファイル名・サイズ・取込開始/終了時刻・成功/失敗・エラーメッセージ
  - マテビュー名・実行時刻・処理件数・実行時間・ステータス

---

## 2. 全体構成イメージ

Docker コンテナが多くなっても、ログの流れは基本的に次のように統一する。

```text
[React] [core_api] [ledger_api] [rag_api] [job_runner] ...
       ↓        ↓           ↓           ↓
    stdout   stdout      stdout      stdout      ← 各コンテナは標準出力にログを書くだけ
       ↓        ↓           ↓           ↓
            Docker (コンテナ毎のログを保持)
                       ↓
        [ログ集約コンテナ]（promtail / fluent-bit 等）
                       ↓
           [中央ストレージ]（Loki / Cloud Logging 等）
                       ↓
           [ビューア]（Grafana / GCP コンソール 等）
```

### 2.1 基本方針

1. **アプリケーションは原則「標準出力（stdout）」にのみログを書き出す。**
   - ファイルへの直接出力は行わない（ローテーションや集約が複雑になるため）。
2. **コンテナ外でログを集約・保存・検索できる仕組みを用意する。**
   - 開発環境: `docker compose logs` で十分
   - stg / 本番: Loki + Promtail + Grafana や GCP Cloud Logging などを利用
3. **業務ログは DB テーブル（`log` スキーマ等）に保存し、アプリログとは目的を分離する。**

---

## 3. ログ 1 行のフォーマット方針

ツールよりも重要なのは「ログ 1 行の中身を決めておくこと」。  
最低限、次のフィールドを含める。

```json
{
  "ts": "2025-11-28T11:23:45+09:00", // 日時（ISO8601）
  "level": "INFO", // ログレベル（DEBUG / INFO / WARN / ERROR）
  "service": "ledger_api", // サービス名（コンテナ名に対応）
  "env": "vm_stg", // 環境名（local_dev / vm_stg / vm_prod 等）
  "trace_id": "af31c...", // リクエストやジョブを一意に識別するID
  "user_id": "sales_001", // （あれば）ユーザーID
  "message": "GET /api/sales/tree completed",
  "duration_ms": 43, // 処理時間
  "rows": 120 // 処理件数など、関心のあるメトリクス
}
```

### 3.1 JSON 形式を採用する理由

- 検索・集計がしやすい（フィールド単位で絞り込み可能）
- Loki / Cloud Logging / Elasticsearch 等、多くのツールと相性が良い
- 既存のテキストログも、「最低限のキー:値」を JSON ライクに揃えておくと後処理が楽になる

### 3.2 ログレベル運用

- 開発環境（local_dev）
  - `DEBUG` まで出してよい
- stg / 本番
  - 基本は `INFO` 以上
  - 詳細なデバッグ情報は必要な箇所に絞る
- `ERROR` レベルには必ずスタックトレースまたは原因を記録する

---

## 4. 環境別の運用方針

### 4.1 local_dev（開発環境）

**目的**: 実装中に何が起きているかをすぐ確認できるようにする。

- アプリケーション
  - 各 FastAPI サービスに共通の logging 設定を導入する
  - すべて標準出力に JSON でログを出す
  - `service` / `env` / `trace_id` などのフィールドを含める
- 確認方法
  - 全体ログ
    - `docker compose -f docker/docker-compose.dev.yml logs -f`
  - サービスを絞る
    - `docker compose -f docker/docker-compose.dev.yml logs -f core_api ledger_api`
- ポイント
  - この段階では「ログ基盤」よりも「フォーマットを揃えること」を優先する

### 4.2 vm_stg / vm_prod（ステージング・本番）

**目的**: 障害対応や性能調査のために、すべてのサービスからのログを 1 か所で検索 / 可視化できるようにする。

- アプリケーション側
  - local_dev と同様に stdout に JSON ログを出すだけ
- インフラ側（例: Loki スタックを利用）
  - `loki` コンテナ：ログの保存と検索を担う
  - `promtail` コンテナ：ホストの Docker ログを読み取り、Loki に送信
  - `grafana` コンテナ：Web UI からログを検索・可視化
- ラベリング例（promtail設定）
  - `compose_project` : local_dev / vm_stg / vm_prod
  - `service` : core_api / ledger_api / rag_api / frontend / db 等
  - `env` : dev / stg / prod
- 将来的な GCP 移行
  - GCE VM 上の Docker でも Cloud Logging に転送可能
  - Cloud Run / GKE の場合は stdout に JSON を出すだけで自動取り込み

---

## 5. 業務ログ（DB log スキーマ）との役割分担

### 5.1 アプリケーションログ（stdout 側）の役割

- 技術的詳細（例外・エラー原因・スタックトレース・SQL エラー等）を記録
- しばらく期間が経ったものは削除・圧縮してもよい（運用ポリシー次第）

### 5.2 業務ログ（DB 側）の役割

- 「業務イベント」の履歴として長期保管する
- 例
  - `log.upload_file`
    - ファイル名 / サイズ / 取込開始・終了時刻 / 実行者 / 成否 / エラーメッセージ
  - `log.mv_refresh`
    - ビュー名 / 実行時刻 / 実行時間 / 処理件数 / 成否 / エラーメッセージ
- これらは監査・説明責任のために長期保存する前提

### 5.3 具体的な使い分けイメージ

- アプリログを見たい時
  - 「なぜこの時 500 エラーが出たのか？」
  - → Loki / Cloud Logging などで、`service="core_api" AND trace_id="..."` を検索
- 業務ログを見たい時
  - 「この CSV ファイルは本当に取り込み済みか？」
  - 「このマテビューは最近いつ成功したか？」
  - → DB で `SELECT * FROM log.upload_file WHERE file_name = ...` など

---

## 6. アプリケーション実装側のルール

### 6.1 共通フィールドの付与

- 環境変数から `SERVICE_NAME` / `ENV` を取得し、ログに自動付与する
  - 例: `SERVICE_NAME=ledger_api`, `ENV=vm_stg`

### 6.2 リクエスト ID（trace_id）の導入

- FastAPI の Middleware で以下を実施
  - リクエストヘッダ `X-Request-ID` を参照し、なければUUIDを新規発行
  - `trace_id` として ContextVar に格納
  - ログ出力時に必ず `trace_id` を含める
- 複数サービス間の連携（core_api → ledger_api → rag_api 等）でも同じ `trace_id` を引き回すことで、1つのリクエストの流れを横断的に追跡可能

### 6.3 ログレベルの目安

- `DEBUG`：詳細な変数値や分岐の様子（開発専用）
- `INFO`：正常系の重要なイベント（リクエスト完了、バッチ完了など）
- `WARN`：想定はしているが望ましくない状態（リトライで復旧した等）
- `ERROR`：処理が失敗しユーザー影響が懸念される状態（例外発生）

---

## 7. 初心者向けのまとめ

- **何を書くか**
  - 技術ログ（アプリ＆インフラ）と業務ログ（DB）を分ける
- **どこに貯めるか**
  - アプリは「標準出力（stdout）」 → Docker → ログ集約ツールへ
  - 業務ログは DB の `log` スキーマのテーブルへ
- **どう見つけるか**
  - 開発中: `docker compose logs` で確認
  - stg/prod: Loki + Grafana や Cloud Logging で検索
- **ログ1行には何を入れるか**
  - 日時・レベル・サービス名・環境名・trace_id・メッセージ・処理時間など

この方針に沿って実装すれば、コンテナが増えてもログの管理と調査がしやすくなります。
