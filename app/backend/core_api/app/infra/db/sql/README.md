# SQL Files Directory

このディレクトリには、Pythonコードから分離された複雑なSQLクエリが格納されています。

## 目的

- **保守性の向上**: 長大なSQLをPythonコードから分離し、可読性と保守性を向上
- **再利用性**: SQLファイルは他のツール(psql, DBeaver, BIツール等)からも利用可能
- **SOLID原則**: 単一責務原則に沿った設計。SQLはデータアクセスロジックとして独立
- **バージョン管理**: SQLの変更履歴を明確に追跡可能

## ディレクトリ構造

```
sql/
├── dashboard/          # ダッシュボード関連SQL
├── inbound/           # 入荷データ関連SQL
├── forecast/          # 予測ジョブ関連SQL
└── README.md          # このファイル
```

## 命名規則

SQLファイルは以下の規則で命名されています:

```
<クラス名のスネークケース>__<メソッド名>.sql
```

例:

- `dashboard_target_repo__get_by_date_optimized.sql`
  - クラス: `DashboardTargetRepository`
  - メソッド: `get_by_date_optimized`

## 使用方法

### Pythonコードからの読み込み

```python
from app.infra.db.sql_loader import load_sql
from sqlalchemy import text

# SQLファイルを読み込み
sql_str = load_sql("dashboard/dashboard_target_repo__get_by_date_optimized.sql")
query = text(sql_str)

# パラメータバインディングで実行
result = session.execute(query, {"req": date(2025, 1, 1), "mode": "daily"})
```

### パフォーマンス最適化

SQLを事前にコンパイルしてキャッシュすることで、繰り返し実行時のパフォーマンスを向上できます:

```python
class MyRepository:
    def __init__(self, db: Session):
        self.db = db
        # __init__で事前にコンパイル
        self._my_query_sql = text(load_sql("path/to/query.sql"))

    def my_method(self, param):
        # 事前にコンパイルしたクエリを使用
        return self.db.execute(self._my_query_sql, {"param": param})
```

## SQLファイルのガイドライン

### 含めるべきSQL

以下の条件を満たすSQLは`.sql`ファイルに切り出すべきです:

- ✅ 15行以上の複雑なSELECT文
- ✅ WITH句を使った共通テーブル式(CTE)
- ✅ 複数テーブルのJOINと集計を伴うロジック
- ✅ BI ツールやバッチ処理で再利用しそうなロジック

### Pythonに残すべきSQL

以下のSQLはPython内にインラインで残してOKです:

- ✅ 10行未満のシンプルなSELECT/INSERT/UPDATE/DELETE
- ✅ 単一テーブルに対する単純な条件検索
- ✅ if文でWHERE条件を動的に組み替える「テンプレート性の高い」クエリ

## パラメータバインディング

SQLファイル内では、SQLAlchemyのパラメータバインディング構文を使用します:

```sql
-- 名前付きパラメータ(:param_name)
SELECT * FROM users WHERE id = :user_id AND status = :status

-- Pythonから実行
result = session.execute(query, {"user_id": 123, "status": "active"})
```

**注意**:

- テーブル名や列名などの識別子は、パラメータバインディングでは渡せません
- 動的な識別子が必要な場合は、Python側で文字列置換を行ってから`text()`に渡します

## 各SQLファイルの説明

### dashboard/dashboard_target_repo\_\_get_by_date_optimized.sql

- **目的**: 月次/週次/日次の目標と実績データを最適化された単一クエリで取得
- **特徴**:
  - 190行の超長大SQL
  - 複数のCTEでアンカー日の解決、累積計算、NULLマスキングを実行
  - Materialized View(mv_target_card_per_day)を参照してパフォーマンス最適化
- **パラメータ**:
  - `:req` - 対象日付(通常は月初)
  - `:mode` - 'daily' または 'monthly'

### inbound/inbound_pg_repository\_\_get_daily_with_cumulative.sql

- **目的**: 日次入荷データをカレンダーと結合し、累積値を計算
- **特徴**:
  - CTEとウィンドウ関数を使用
  - カレンダーとのLEFT JOINで欠損日を0埋め
  - 累積スコープ(range/month/week)に応じた累積計算
- **パラメータ**:
  - `:start` - 開始日(含む)
  - `:end` - 終了日(含む)
  - `:cum_scope` - 累積スコープ('range', 'month', 'week', 'none')
- **注意**: テーブル名はPython側で動的に差し込むため、SQL内では`mart.v_calendar`のままですが、実行時に置換されます

### forecast/job_repo\_\_claim_job.sql

- **目的**: 待機中の予測ジョブを1つクレームし、実行中状態に更新
- **特徴**:
  - `FOR UPDATE SKIP LOCKED`で複数ワーカーの競合を回避
  - CTEで対象ジョブを選択し、UPDATEで原子的に更新
  - attemptsカウンタをインクリメント
- **パラメータ**: なし
- **戻り値**: クレームしたジョブのID、または利用可能なジョブがない場合はNULL

## メンテナンス

### SQLファイルの追加

1. 適切なサブディレクトリを選択(または作成)
2. 命名規則に従ってファイルを作成
3. SQLファイルの先頭にコメントで以下を記載:
   - 目的の説明
   - パラメータの説明
   - 戻り値の説明
   - 注意事項(あれば)

### SQLファイルの修正

- SQLファイルを直接編集
- 変更履歴はGitで管理
- 大きな変更の場合は、マイグレーションスクリプトも更新すること

## トラブルシューティング

### FileNotFoundError

```python
FileNotFoundError: SQL file not found: .../sql/path/to/file.sql
```

**原因**: SQLファイルが存在しないか、パスが間違っています

**解決策**:

1. ファイルが存在するか確認
2. パスの区切り文字は `/` を使用(Windows/Linux両対応)
3. ファイル名の大文字/小文字が正確か確認

### テーブル名が見つからない

```
relation "mart.v_calendar" does not exist
```

**原因**: SQL内のテーブル名が環境に合っていません

**解決策**:

- Python側で`sql_names.py`の定数を使用してテーブル名を動的に差し込む
- 例: `sql_str.replace("mart.v_calendar", V_CALENDAR)`

## 参考資料

- [SQLAlchemy Text SQL](https://docs.sqlalchemy.org/en/20/core/sqlelement.html#sqlalchemy.sql.expression.text)
- [PostgreSQL CTE Documentation](https://www.postgresql.org/docs/current/queries-with.html)
- [FOR UPDATE SKIP LOCKED](https://www.postgresql.org/docs/current/sql-select.html#SQL-FOR-UPDATE-SHARE)
