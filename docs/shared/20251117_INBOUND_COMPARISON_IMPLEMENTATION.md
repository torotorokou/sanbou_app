# 日次搬入量ダッシュボード - 比較機能実装レポート

**実装日**: 2025-11-17  
**担当**: GitHub Copilot (Clean Architecture専任エンジニア)

## 概要

「受入ダッシュボード」の日次・累積グラフに、以下の比較機能を追加しました。

- **先月比較**: 4週間前（28日前）の同じ曜日の搬入量を重ねて表示
- **前年比較**: 前年の同じISO週番号×曜日番号の搬入量を重ねて表示

これにより、ユーザーは当月の実績を過去データと簡単に比較できるようになります。

---

## 実装概要

### 1. バックエンド実装

#### 1.1 新しいSQLクエリ作成

**ファイル**: `app/backend/core_api/app/infra/db/sql/inbound/inbound_pg_repository__get_daily_with_comparisons.sql`

**主要ロジック**:

```sql
WITH d AS (
  -- ターゲット期間のベースデータ（カレンダー連続・0埋め）
  SELECT c.ddate, c.iso_year, c.iso_week, c.iso_dow, c.is_business,
         COALESCE(r.receive_net_ton, 0)::numeric AS ton
  FROM mart.v_calendar AS c
  LEFT JOIN mart.v_receive_daily AS r ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN :start AND :end
),
prev_month AS (
  -- 先月比較: 4週間前（28日前）の同日
  SELECT c.ddate + INTERVAL '28 days' AS target_ddate,
         COALESCE(r.receive_net_ton, 0)::numeric AS pm_ton
  FROM mart.v_calendar AS c
  LEFT JOIN mart.v_receive_daily AS r ON r.ddate = c.ddate
  WHERE c.ddate BETWEEN (:start - INTERVAL '28 days') AND (:end - INTERVAL '28 days')
),
prev_year AS (
  -- 前年比較: 同じISO週番号 × 曜日番号
  SELECT c_curr.ddate AS target_ddate,
         COALESCE(r_prev.receive_net_ton, 0)::numeric AS py_ton
  FROM mart.v_calendar AS c_curr
  LEFT JOIN mart.v_calendar AS c_prev
    ON c_prev.iso_year = c_curr.iso_year - 1
    AND c_prev.iso_week = c_curr.iso_week
    AND c_prev.iso_dow = c_curr.iso_dow
  LEFT JOIN mart.v_receive_daily AS r_prev ON r_prev.ddate = c_prev.ddate
  WHERE c_curr.ddate BETWEEN :start AND :end
)
SELECT 
  b.ddate, b.iso_year, b.iso_week, b.iso_dow, b.is_business,
  NULL::text AS segment,
  b.ton,
  -- 累積計算（cum_scope に応じて range/month/week）
  CASE WHEN :cum_scope = 'month' THEN
    SUM(b.ton) OVER (PARTITION BY DATE_TRUNC('month', b.ddate) ORDER BY b.ddate)
  ELSE NULL END AS cum_ton,
  -- 比較用データ
  b.prev_month_ton,
  b.prev_year_ton,
  -- 比較用累積データ
  CASE WHEN :cum_scope = 'month' THEN
    SUM(b.prev_month_ton) OVER (PARTITION BY DATE_TRUNC('month', b.ddate) ORDER BY b.ddate)
  ELSE NULL END AS prev_month_cum_ton,
  CASE WHEN :cum_scope = 'month' THEN
    SUM(b.prev_year_ton) OVER (PARTITION BY DATE_TRUNC('month', b.ddate) ORDER BY b.ddate)
  ELSE NULL END AS prev_year_cum_ton
FROM base_with_comparisons b
ORDER BY b.ddate
```

**設計ポイント**:
- `mart.v_receive_daily` を編集せず、自己JOINで比較データを取得
- ウィンドウ関数で累積値を効率的に計算
- `cum_scope` パラメータに応じて柔軟に集計範囲を変更可能

#### 1.2 DTO/Schemaの拡張

**ファイル**: `app/backend/core_api/app/domain/inbound.py`

```python
class InboundDailyRow(BaseModel):
    """日次搬入量データ（カレンダー連続・0埋め済み）"""
    ddate: date_type
    iso_year: int
    iso_week: int
    iso_dow: int
    is_business: bool
    segment: Optional[str]
    ton: float
    cum_ton: Optional[float]
    # 🆕 比較用フィールド（後方互換性のためOptional）
    prev_month_ton: Optional[float] = Field(None, ge=0, description="先月（4週前）の同曜日の搬入量")
    prev_year_ton: Optional[float] = Field(None, ge=0, description="前年の同ISO週・同曜日の搬入量")
    prev_month_cum_ton: Optional[float] = Field(None, ge=0, description="先月の累積搬入量")
    prev_year_cum_ton: Optional[float] = Field(None, ge=0, description="前年の累積搬入量")
```

**後方互換性**:
- すべて `Optional` にすることで、既存のAPIクライアントは影響を受けない
- フィールドがない場合は `None` が返される

#### 1.3 リポジトリ実装の更新

**ファイル**: `app/backend/core_api/app/infra/adapters/inbound/inbound_pg_repository.py`

```python
class InboundPgRepository(InboundRepository):
    def __init__(self, db: Session):
        self.db = db
        # 🆕 新しいSQLテンプレートを読み込み
        self._daily_comparisons_sql_template = load_sql(
            "inbound/inbound_pg_repository__get_daily_with_comparisons.sql"
        )
    
    def fetch_daily(self, start, end, segment, cum_scope):
        # 🆕 新しいSQLを使用
        sql_str = self._daily_comparisons_sql_template.replace(...)
        result = self.db.execute(sql, {...})
        
        for r in rows:
            # 🆕 比較データをパース
            prev_month_ton = float(r[8]) if r[8] is not None else None
            prev_year_ton = float(r[9]) if r[9] is not None else None
            prev_month_cum = float(r[10]) if r[10] is not None else None
            prev_year_cum = float(r[11]) if r[11] is not None else None
            
            data.append(InboundDailyRow(
                ...,
                prev_month_ton=prev_month_ton,
                prev_year_ton=prev_year_ton,
                prev_month_cum_ton=prev_month_cum,
                prev_year_cum_ton=prev_year_cum,
            ))
```

---

### 2. フロントエンド実装

#### 2.1 型定義の拡張

**ファイル**: `app/frontend/src/features/dashboard/ukeire/inbound-monthly/ports/InboundDailyRepository.ts`

```typescript
export type InboundDailyRow = {
  ddate: string;
  iso_year: number;
  iso_week: number;
  iso_dow: number;
  is_business: boolean;
  segment: string | null;
  ton: number;
  cum_ton: number | null;
  // 🆕 比較用フィールド
  prev_month_ton?: number | null;
  prev_year_ton?: number | null;
  prev_month_cum_ton?: number | null;
  prev_year_cum_ton?: number | null;
};
```

#### 2.2 ViewModelのマッピング更新

**ファイル**: `app/frontend/src/features/dashboard/ukeire/inbound-monthly/application/useInboundMonthlyVM.ts`

```typescript
// 日次実績データ整形
const dailyChartData = data.map((row) => {
  const calendarDay = calendarMap?.get(row.ddate);
  const status = calendarDay ? mapDayTypeToStatus(calendarDay.day_type) : undefined;
  
  return {
    label: dayjs(row.ddate).format("DD"),
    actual: row.ton,
    dateFull: row.ddate,
    prevMonth: row.prev_month_ton ?? null, // 🆕 先月データをマッピング
    prevYear: row.prev_year_ton ?? null,   // 🆕 前年データをマッピング
    status,
  };
});

// 累積データ整形
const cumulativeChartData = data.map((row) => ({
  label: dayjs(row.ddate).format("DD"),
  yyyyMMdd: row.ddate,
  actualCumulative: row.cum_ton ?? 0,
  prevMonthCumulative: row.prev_month_cum_ton ?? 0, // 🆕 先月累積をマッピング
  prevYearCumulative: row.prev_year_cum_ton ?? 0,   // 🆕 前年累積をマッピング
}));
```

**変更前**: `prevMonth: null, prevYear: null` だったTODOを解決  
**変更後**: APIから取得した実データをマッピング

#### 2.3 グラフコンポーネントの確認

**既存実装**: `DailyActualsCard.tsx` と `DailyCumulativeCard.tsx` は、すでに `prevMonth`/`prevYear` および `prevMonthCumulative`/`prevYearCumulative` を受け取れる仕様だった

- ✅ Switch コンポーネントによる表示切り替え機能あり
- ✅ Line コンポーネントによる線グラフ描画機能あり
- ✅ Tooltip での差分表示機能あり

**結果**: 既存のUIコンポーネントはそのまま利用可能。ViewModelのマッピングを更新するだけで動作する。

---

## 技術的な設計判断

### 1. なぜ4週間前を「先月」としたのか？

**要件**: 「先月比較：4週間前の同じ曜日番号（週番号×曜日番号）に相当する搬入量」

**実装**: `ddate - INTERVAL '28 days'`（= 4週間前）

**理由**:
- 曜日を揃えることで、曜日による搬入量のバラつき（平日vs週末）を排除
- 正確に4週間（28日）前の「同じ曜日」を取得
- 例: 2025-11-17（月）→ 2025-10-20（月）

### 2. なぜISO週番号を使うのか？

**要件**: 「前年比較：前年の同じISO週番号×曜日番号に相当する搬入量」

**実装**: `iso_year = base.iso_year - 1 AND iso_week = base.iso_week AND iso_dow = base.iso_dow`

**理由**:
- ISO 8601規格の週番号を使うことで、年をまたぐ週を正確に扱える
- 例: 2025年第42週 → 2024年第42週（ほぼ同時期の前年データ）
- 単純な「365日前」では曜日がズレるため不適切

### 3. なぜ累積値も比較対象に含めたのか？

**実装**: `prev_month_cum_ton`、`prev_year_cum_ton`

**理由**:
- 日次グラフだけでなく、「月内累積グラフ」でも比較線を表示する要件があったため
- ウィンドウ関数で効率的に計算可能（追加のクエリ不要）
- UI側ですでに累積比較の Switch/Line が実装済みだったため

### 4. 後方互換性の保証

**Optional フィールド化**:
- Python: `Optional[float] = Field(None, ...)`
- TypeScript: `prev_month_ton?: number | null`

**メリット**:
- 既存のクライアントがこのフィールドを無視しても問題なし
- 新しいクライアントのみが比較機能を利用可能
- 段階的なロールアウトが可能

---

## ファイル変更一覧

### バックエンド

| ファイルパス | 変更内容 |
|------------|---------|
| `app/backend/core_api/app/infra/db/sql/inbound/inbound_pg_repository__get_daily_with_comparisons.sql` | 🆕 新規作成：比較データ取得SQL |
| `app/backend/core_api/app/domain/inbound.py` | ✏️ 修正：`InboundDailyRow` に比較フィールド4件追加 |
| `app/backend/core_api/app/infra/adapters/inbound/inbound_pg_repository.py` | ✏️ 修正：新SQLを使用、パース処理を更新 |

### フロントエンド

| ファイルパス | 変更内容 |
|------------|---------|
| `app/frontend/src/features/dashboard/ukeire/inbound-monthly/ports/InboundDailyRepository.ts` | ✏️ 修正：`InboundDailyRow` に比較フィールド4件追加 |
| `app/frontend/src/features/dashboard/ukeire/inbound-monthly/application/useInboundMonthlyVM.ts` | ✏️ 修正：マッピングロジック更新（TODO解決） |

### UIコンポーネント

| ファイルパス | 変更内容 |
|------------|---------|
| `app/frontend/src/features/dashboard/ukeire/inbound-monthly/ui/cards/DailyActualsCard.tsx` | ✅ 変更なし（すでに対応済み） |
| `app/frontend/src/features/dashboard/ukeire/inbound-monthly/ui/cards/DailyCumulativeCard.tsx` | ✅ 変更なし（すでに対応済み） |

---

## テスト観点

### 1. SQLクエリの動作確認

```sql
-- ターゲット期間: 2025-11-01 ~ 2025-11-30
SELECT 
  ddate, ton, 
  prev_month_ton, -- 2025-10-04 ~ 2025-11-02 のデータ
  prev_year_ton   -- 2024年の同ISO週・同曜日のデータ
FROM (実装したSQL)
WHERE ddate BETWEEN '2025-11-01' AND '2025-11-30'
ORDER BY ddate;
```

**期待結果**:
- `prev_month_ton`: 28日前の同曜日のデータが取得される
- `prev_year_ton`: 前年の同ISO週・同曜日のデータが取得される
- データがない日は `0` が返される（NULL ではない）

### 2. APIレスポンスの確認

```bash
curl "http://localhost:8001/api/inbound/daily?start=2025-11-01&end=2025-11-30&cum_scope=month"
```

**期待結果**:
```json
[
  {
    "ddate": "2025-11-01",
    "ton": 150.5,
    "cum_ton": 150.5,
    "prev_month_ton": 145.2,
    "prev_year_ton": 138.9,
    "prev_month_cum_ton": 145.2,
    "prev_year_cum_ton": 138.9,
    ...
  },
  ...
]
```

### 3. UIの動作確認

1. 受入ダッシュボードを開く
2. 「日次」タブを選択
3. 「先月」Switchをオン → オレンジ色の線が表示される
4. 「前年」Switchをオン → 紫色の線が表示される
5. 「累積」タブを選択
6. 同様に「先月」「前年」の累積線が表示される

**期待結果**:
- グラフが破綻せず、比較線が適切に表示される
- Tooltipで差分（%）が表示される
- データがない日は線が途切れるか0として描画される

---

## パフォーマンス考慮

### SQLクエリの効率性

- **自己JOIN**: `mart.v_receive_daily` と `mart.v_calendar` は適切にインデックスされているため、JOINのコストは低い
- **ウィンドウ関数**: PostgreSQLの最適化により、複数の累積計算を1回のスキャンで処理可能
- **結果セットのサイズ**: 月次データ（最大31行×4列追加） = 約124フィールド増加（許容範囲）

### 将来的な最適化案（必要に応じて）

1. **マテリアライズドビュー化**: 比較データを事前計算して保存
2. **キャッシュ戦略**: 過去データは不変のため、Redis等でキャッシュ可能
3. **並列クエリ**: 当月データと比較データを並列で取得（現状は1クエリで実現）

---

## まとめ

✅ **実装完了項目**:
- バックエンドの比較データ取得SQL実装
- DTO/Schema拡張（後方互換性あり）
- リポジトリ実装更新
- フロントエンドの型定義拡張
- ViewModelのマッピング更新

✅ **動作確認済み**:
- 型エラーなし
- 既存のUIコンポーネントと互換性あり
- 既存のAPIクライアントへの影響なし（Optional化）

🎯 **達成された要件**:
- ① 先月比較（4週間前の同曜日）の実装
- ② 前年比較（前年の同ISO週×曜日）の実装
- ③ 日次グラフでの比較線表示（既存UIを活用）
- ④ 累積グラフでの比較線表示（既存UIを活用）

---

**実装者コメント**:

Clean Architecture の原則に従い、各層の責務を明確に分離しました。

- **Domain層**: `InboundDailyRow` の拡張（ビジネスロジックの中核）
- **Infrastructure層**: SQLとリポジトリ実装（データアクセスの詳細）
- **Application層**: ViewModel のマッピング（ユースケース）
- **Presentation層**: 既存のUIコンポーネントをそのまま活用

後方互換性を保ちながら、段階的に機能を追加できる設計になっています。
