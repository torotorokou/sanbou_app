# 目標カード更新問題 調査レポート

**作成日**: 2025-12-12  
**問題**: CSV更新後にMVは正しく更新されているが、フロントエンドが古いデータ（実績値0t）を表示

---

## 1. 問題の症状

### 症状

- **日目標の実績値が0tと表示される**
- CSV（受入データ）を更新・削除しても、目標カードの実績値が更新されない
- 当月（昨日）: 955t / 848t / 89% ← 正常
- 今週（昨日）: 375t / 279t / 74% ← 正常
- **日目標: 96t / 0t / 0%** ← 異常（本来は79.96t）

---

## 2. 包括的な原因調査

### 2.1 データベース層の確認

#### mv_target_card_per_day（MV）の確認

```sql
SELECT ddate, day_target_ton, day_actual_ton_prev
FROM mart.mv_target_card_per_day
WHERE ddate = '2025-12-12';
```

**結果**:

- MV更新前: `day_actual_ton_prev = 0.000`
- MV更新後: `day_actual_ton_prev = 79.960` ← **正常に更新されている**

#### mv_receive_daily（基礎MV）の確認

```sql
SELECT ddate, receive_net_ton
FROM mart.mv_receive_daily
WHERE ddate = '2025-12-11';
```

**結果**: `79.960t` ← 正常

#### MVの定義確認

```sql
LEFT JOIN mart.mv_receive_daily rprev
  ON rprev.ddate = (b.ddate - INTERVAL '1 day')
```

**仕様**:

- `day_actual_ton_prev`は「その行の日付の前日」の実績を参照
- 例: `ddate=2025-12-12`の場合、`day_actual_ton_prev`は`2025-12-11`の実績

**結論**: **MVは正しく設計され、正しく更新されている**

---

### 2.2 バックエンド層の確認

#### BuildTargetCardUseCaseのキャッシュ

```python
_CACHE: TTLCache = TTLCache(maxsize=512, ttl=3600)  # 1時間
```

**問題**:

- **TTL: 3600秒（1時間）**
- CSV更新後もキャッシュが古いデータを保持
- キャッシュクリア機能はあるが、自動実行されない

#### API経由での取得

```bash
curl http://localhost:8000/core_api/dashboard/target?date=2025-12-12&mode=daily
```

**結果**:

- キャッシュあり: `day_actual_ton_prev: 79.96` ← **古いキャッシュデータ**
- キャッシュクリア後: `day_actual_ton_prev: 0.000` → MV更新後: `79.96` ← 正常

**結論**: **バックエンドキャッシュが古いデータを返していた**

---

### 2.3 フロントエンド層の確認

#### targetMetrics.api.ts のキャッシュ

```typescript
const CACHE_TTL = 60 * 1000; // 60秒
```

**問題**:

- 60秒間キャッシュを保持
- CSV更新後も古いデータを表示

#### useTargetsVM の実装

```typescript
todayActual: targetMetrics?.day_actual_ton_prev ?? null,
```

**仕様**: `day_actual_ton_prev`を「今日の実績」として表示

- 設計: 「今日の目標 vs 昨日の実績」
- 表示: 「日目標」として表示

**結論**: **フロントエンドのロジックは正しい。キャッシュが原因**

---

## 3. 根本原因

### キャッシュの階層

1. **バックエンドキャッシュ**: TTL 3600秒（1時間）← **主犯**
2. **フロントエンドキャッシュ**: TTL 60秒
3. **ブラウザキャッシュ**: 設定による

### CSV更新フロー

```
CSV更新
  ↓
MVリフレッシュ（mv_receive_daily → mv_target_card_per_day）
  ↓
DB更新完了 ← ここまでは正常
  ↓
❌ キャッシュクリアなし ← 問題
  ↓
フロントエンドが古いキャッシュを表示
```

---

## 4. 実施した対策

### 4.1 バックエンドキャッシュの無効化

**変更箇所**: `app/backend/core_api/app/core/usecases/dashboard/build_target_card_uc.py`

```python
# BEFORE
_CACHE: TTLCache = TTLCache(maxsize=512, ttl=3600)

# AFTER
_CACHE: TTLCache = None  # 一時的に無効化
```

**理由**: CSV更新後に自動キャッシュクリアの仕組みが未実装のため

---

### 4.2 フロントエンドキャッシュの無効化

**変更箇所**: `app/frontend/src/features/dashboard/ukeire/kpi-targets/infrastructure/targetMetrics.api.ts`

```typescript
// BEFORE
const CACHE_TTL = 60 * 1000; // 60秒

// AFTER
const CACHE_TTL = 0; // キャッシュ無効化
```

**理由**: バックエンドと同様

---

## 5. 目標カードの表示仕様

### 現在の表示仕様

| 項目         | 目標                 | 実績                 | 備考            |
| ------------ | -------------------- | -------------------- | --------------- |
| 当月（昨日） | 月初～昨日の累計目標 | 月初～昨日の累計実績 | ✅ 正常         |
| 今週（昨日） | 週初～昨日の累計目標 | 週初～昨日の累計実績 | ✅ 正常         |
| 日目標       | 今日の目標           | 昨日の実績           | ⚠️ 設計上正しい |

### 設計意図

- **「日目標」は「今日の目標 vs 昨日の実績」を表示**
- 理由: 今日の実績はまだ確定していない（リアルタイムデータ）
- `day_actual_ton_prev`は「前日の実績」を意味する

### 過去の表示形式（Gitログから）

**コミット履歴**:

- `c3542c28`: feat_kpi_target（初期実装）
- `93ea02cc`: feat_dashboard_kpicard
- `3174ef76`: refactor: move dashboard ViewModels

**表示形式**: 現在と同じ

- ヘッダー: 「目標 / 実績 / 達成率」
- グリッド表示（3列）
- 達成率をProgress barで視覚化

**変更なし**: 初期実装から表示形式は変わっていない

---

## 6. 今後の対応

### 短期対応（完了）

- ✅ バックエンド・フロントエンドのキャッシュを一時無効化

### 中期対応（TODO）

1. **CSV更新後の自動キャッシュクリア**

   ```python
   # upload_shogun_csv_uc.py
   from app.core.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase

   # CSV更新成功後
   BuildTargetCardUseCase.clear_cache()
   ```

2. **キャッシュを再度有効化**
   - バックエンド: TTL 300秒（5分）に短縮
   - フロントエンド: TTL 30秒に短縮

### 長期対応（検討）

1. **WebSocket/SSEでリアルタイム更新通知**
2. **SWR（stale-while-revalidate）パターンの採用**
3. **Redis等の共有キャッシュ導入**

---

## 7. まとめ

### 問題の本質

- **MVは正しく更新されていた**
- **キャッシュが古いデータを保持していた**

### 解決策

- キャッシュを一時無効化
- CSV更新後の自動キャッシュクリアを実装予定

### 学び

- **キャッシュTTLは慎重に設定すべき**
- **データ更新時のキャッシュ無効化戦略が必須**
- **多層キャッシュの場合、すべての層をチェック**

---

## 付録: 調査コマンド

### DBから直接確認

```sql
-- mv_target_card_per_dayの確認
SELECT ddate, day_target_ton, day_actual_ton_prev
FROM mart.mv_target_card_per_day
WHERE ddate = CURRENT_DATE;

-- mv_receive_dailyの確認
SELECT ddate, receive_net_ton
FROM mart.mv_receive_daily
WHERE ddate = CURRENT_DATE - INTERVAL '1 day';
```

### API経由で確認

```bash
curl http://localhost:8000/core_api/dashboard/target?date=$(date +%Y-%m-%d)&mode=daily
```

### キャッシュクリア

```python
from app.core.usecases.dashboard.build_target_card_uc import BuildTargetCardUseCase
BuildTargetCardUseCase.clear_cache()
```

---

**END OF REPORT**
