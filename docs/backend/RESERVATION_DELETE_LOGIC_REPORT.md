# 予約データ削除機能 - ロジック詳細レポート

**作成日**: 2025-12-16  
**対象機能**: 予約履歴カレンダーからの予約データ削除

---

## 📋 目次

1. [削除機能の概要](#削除機能の概要)
2. [アーキテクチャ全体像](#アーキテクチャ全体像)
3. [フロントエンド実装](#フロントエンド実装)
4. [バックエンドAPI](#バックエンドapi)
5. [データベース層](#データベース層)
6. [削除種別の判定](#削除種別の判定-物理削除-vs-論理削除)
7. [データフロー図](#データフロー図)
8. [セキュリティと制約](#セキュリティと制約)
9. [テスト観点](#テスト観点)

---

## 削除機能の概要

### 機能仕様

- **操作対象**: 予約履歴カレンダー上の任意の日付
- **削除可能データ**: データが存在する日付すべて（手入力/顧客集計を問わず）
- **削除方式**: **物理削除**（レコードを完全削除）
- **UI**: クリック → モーダル確認 → 削除実行 → カレンダー再読み込み

---

## アーキテクチャ全体像

```
┌─────────────────────────────────────────────────────────────┐
│ Frontend (React + TypeScript)                               │
│                                                             │
│  ReservationDailyPage                                       │
│    ├─ useReservationCalendarVM (ViewModel)                 │
│    └─ ReservationHistoryCalendar (UI Component)            │
│          └─ onClick → Modal → Delete Button                │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ HTTP DELETE
┌─────────────────────────────────────────────────────────────┐
│ Backend API (FastAPI + Python)                             │
│                                                             │
│  DELETE /core_api/reservation/manual/{reserve_date}        │
│    └─ router.py                                            │
│         └─ ReservationRepositoryImpl.delete_manual()       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼ SQL DELETE
┌─────────────────────────────────────────────────────────────┐
│ Database (PostgreSQL)                                       │
│                                                             │
│  stg.reserve_daily_manual                                  │
│    └─ DELETE FROM ... WHERE reserve_date = ?               │
└─────────────────────────────────────────────────────────────┘
```

---

## フロントエンド実装

### 1. ViewModel (useReservationCalendarVM.ts)

**ファイル**: `app/frontend/src/features/reservation/reservation-calendar/model/useReservationCalendarVM.ts`

```typescript
const onDeleteDate = useCallback(async (date: string) => {
  setIsDeletingDate(date);
  try {
    await repository.deleteManual(date);
    message.success('削除しました');
    // データを再取得
    await fetchHistoryData(historyMonth);
  } catch (err: unknown) {
    console.error('Failed to delete manual data:', err);
    const errorMessage = err instanceof Error ? err.message : '不明なエラー';
    message.error(`削除に失敗しました: ${errorMessage}`);
  } finally {
    setIsDeletingDate(null);
  }
}, [repository, historyMonth, fetchHistoryData]);
```

**責務**:
- 削除APIの呼び出し
- ローディング状態の管理 (`isDeletingDate`)
- エラーハンドリングとユーザーへの通知
- 削除後のカレンダーデータ再取得

---

### 2. HTTPリポジトリ (ReservationDailyHttpRepository.ts)

**ファイル**: `app/frontend/src/features/reservation/shared/infrastructure/ReservationDailyHttpRepository.ts`

```typescript
async deleteManual(date: string): Promise<void> {
  await coreApi.delete(`/core_api/reservation/manual/${date}`);
}
```

**エンドポイント**: `DELETE /core_api/reservation/manual/{date}`  
**パラメータ**: `date` - YYYY-MM-DD形式の日付文字列

---

### 3. UI Component (ReservationHistoryCalendar.tsx)

**ファイル**: `app/frontend/src/features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx`

```typescript
const handleCellClick = () => {
  if (data && onDeleteDate) {
    setSelectedDateForDelete(dateStr);
    setDetailModalOpen(true);
  }
};

const handleDeleteClick = async () => {
  if (onDeleteDate && selectedDateForDelete) {
    await onDeleteDate(selectedDateForDelete);
    setDetailModalOpen(false);
    setSelectedDateForDelete(null);
  }
};
```

**UXフロー**:
1. ユーザーが日付セルをクリック
2. モーダル表示（日付、合計台数、固定客台数を表示）
3. 「削除する」ボタンをクリック
4. 削除確認なし（モーダル自体が確認ステップ）
5. 削除実行 → 成功メッセージ → カレンダー再描画

---

## バックエンドAPI

### 1. APIルーター (router.py)

**ファイル**: `app/backend/core_api/app/api/routers/reservation/router.py`

```python
@router.delete("/manual/{reserve_date}")
def delete_manual_reservation(
    reserve_date: date_type,
    repo: ReservationRepositoryImpl = Depends(get_reservation_repository),
):
    """
    指定日の手入力予約データを削除
    
    Args:
        reserve_date: 予約日 (YYYY-MM-DD)
    
    Returns:
        dict: 削除結果
    """
    success = repo.delete_manual(reserve_date)
    if not success:
        raise HTTPException(status_code=404, detail="Manual reservation not found")
    
    logger.info(f"Deleted manual reservation for {reserve_date}")
    return {"message": "Deleted successfully", "reserve_date": str(reserve_date)}
```

**責務**:
- パスパラメータから日付を受け取る
- リポジトリの `delete_manual()` を呼び出す
- 削除失敗時（データが存在しない）は404エラーを返す
- 成功時は削除完了メッセージを返す

---

### 2. リポジトリ実装 (reservation_repository.py)

**ファイル**: `app/backend/core_api/app/infra/adapters/reservation/reservation_repository.py`

```python
def delete_manual(self, reserve_date: date_type) -> bool:
    """指定日の手入力予約データを削除"""
    try:
        stmt = delete(ReserveDailyManual).where(
            ReserveDailyManual.reserve_date == reserve_date
        )
        result = self.db.execute(stmt)
        self.db.commit()
        return result.rowcount > 0
    except Exception as e:
        self.db.rollback()
        logger.error(f"Failed to delete manual reservation: {e}", exc_info=True)
        raise
```

**実装詳細**:
- SQLAlchemyの `delete()` を使用
- `WHERE reserve_date = ?` で対象レコードを特定
- `result.rowcount` で削除された行数を確認
- トランザクション管理（commit/rollback）
- 例外時はロールバックしてログ出力

---

## データベース層

### 1. テーブル定義

**テーブル名**: `stg.reserve_daily_manual`  
**スキーマ定義**: `20251216_001_add_reserve_daily_manual.py`

```sql
CREATE TABLE stg.reserve_daily_manual (
    reserve_date date PRIMARY KEY,
    total_trucks integer NOT NULL DEFAULT 0,
    fixed_trucks integer NOT NULL DEFAULT 0,
    note text,
    created_by text,
    updated_by text,
    created_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at timestamp with time zone NOT NULL DEFAULT CURRENT_TIMESTAMP,
    
    -- 制約
    CONSTRAINT chk_total_trucks_non_negative CHECK (total_trucks >= 0),
    CONSTRAINT chk_fixed_trucks_non_negative CHECK (fixed_trucks >= 0),
    CONSTRAINT chk_fixed_trucks_not_exceed_total CHECK (fixed_trucks <= total_trucks)
);
```

**主キー**: `reserve_date` (日付ごとに1レコード)

---

### 2. 削除SQL

```sql
DELETE FROM stg.reserve_daily_manual
WHERE reserve_date = '2025-12-10';
```

**実行内容**:
- 指定した日付のレコードを**物理削除**（完全削除）
- カスケード削除なし（単一テーブル操作）
- トリガーなし（シンプルなDELETE）

---

## 削除種別の判定: 物理削除 vs 論理削除

### ✅ **2025-12-16更新: 論理削除に変更**

| 観点 | 物理削除（旧） | 論理削除（現在） |
|------|----------|----------|
| **SQL操作** | `DELETE FROM` | `UPDATE SET deleted_at = NOW()` |
| **データの状態** | レコードが完全に消える | レコードは残る（フラグ付き） |
| **復元可能性** | 不可（バックアップから） | 可（deleted_atをNULLに戻す） |
| **パフォーマンス** | 良好（レコード減少） | 劣化（データ増加） |
| **監査証跡** | 困難 | 容易 |
| **実装複雑度** | 低 | 中（全クエリで除外条件が必要） |

**論理削除に変更した理由（2025-12-16）**:

1. **データ保全**: 誤削除時の復旧を容易にする
2. **監査証跡**: 削除履歴を記録し、誰がいつ削除したかを追跡可能に
3. **運用安全性**: 物理削除によるデータ完全消失のリスクを回避
4. **ビジネス要件**: 削除データの再利用や分析の可能性を残す

---

### ✅ 論理削除の実装（2025-12-16完了）

**1. マイグレーション: テーブルにカラム追加**

マイグレーションファイル: `20251216_004_add_soft_delete_to_reserve_daily_manual.py`

```sql
ALTER TABLE stg.reserve_daily_manual
ADD COLUMN deleted_at timestamp with time zone DEFAULT NULL,
ADD COLUMN deleted_by text DEFAULT NULL;

-- インデックス追加（パフォーマンス対策）
CREATE INDEX idx_reserve_daily_manual_not_deleted 
ON stg.reserve_daily_manual (reserve_date) 
WHERE deleted_at IS NULL;
```

**2. リポジトリ実装: 論理削除**

ファイル: `app/infra/adapters/reservation/reservation_repository.py`

```python
def delete_manual(self, reserve_date: date_type) -> bool:
    """論理削除: deleted_atを設定"""
    from datetime import datetime, timezone
    
    stmt = (
        update(ReserveDailyManual)
        .where(
            ReserveDailyManual.reserve_date == reserve_date,
            ReserveDailyManual.deleted_at == None  # 既に削除済みは除外
        )
        .values(
            deleted_at=datetime.now(timezone.utc),
            deleted_by="system"  # TODO: 認証コンテキストから取得
        )
    )
    result = self.db.execute(stmt)
    self.db.commit()
    return result.rowcount > 0
```

**3. SELECT文に除外条件追加**

```python
def get_manual(self, reserve_date: date_type) -> Optional[ReservationManualRow]:
    stmt = select(ReserveDailyManual).where(
        ReserveDailyManual.reserve_date == reserve_date,
        ReserveDailyManual.deleted_at == None  # 論理削除を除外
    )
    # ...

def upsert_manual(self, data: ReservationManualRow) -> ReservationManualRow:
    # 既存データ検索時も論理削除を除外
    existing = self.db.execute(
        select(ReserveDailyManual).where(
            ReserveDailyManual.reserve_date == data.reserve_date,
            ReserveDailyManual.deleted_at == None
        )
    ).scalar_one_or_none()
    # ...
```

**4. ビュー更新: 論理削除を除外**

```sql
CREATE OR REPLACE VIEW mart.v_reserve_daily_for_forecast AS
WITH manual_data AS (
    SELECT ...
    FROM stg.reserve_daily_manual
    WHERE deleted_at IS NULL  -- 論理削除を除外
)
...
```

---

## データフロー図

### 削除処理のシーケンス

```
User (Browser)
    │
    │ 1. Click cell (2025-12-10)
    ▼
ReservationHistoryCalendar
    │
    │ 2. Open Modal
    │ 3. Click "削除する"
    ▼
useReservationCalendarVM
    │
    │ 4. onDeleteDate('2025-12-10')
    ▼
ReservationDailyHttpRepository
    │
    │ 5. DELETE /core_api/reservation/manual/2025-12-10
    ▼
FastAPI Router
    │
    │ 6. delete_manual_reservation()
    ▼
ReservationRepositoryImpl
    │
    │ 7. delete_manual(date)
    ▼
PostgreSQL
    │
    │ 8. DELETE FROM stg.reserve_daily_manual WHERE reserve_date = '2025-12-10'
    │ 9. COMMIT
    ▼
Response (200 OK)
    │
    │ 10. {"message": "Deleted successfully", ...}
    ▼
useReservationCalendarVM
    │
    │ 11. message.success('削除しました')
    │ 12. fetchHistoryData() (再取得)
    ▼
ReservationHistoryCalendar
    │
    │ 13. カレンダー再描画
    ▼
User (Browser) - Updated Calendar
```

---

## セキュリティと制約

### 1. 認証・認可（現状）

**現在の実装**: 認証なし（TODO）

```python
# router.py (L93)
created_by="system",  # TODO: Get from auth context
```

**将来の実装予定**:
- JWT認証
- ユーザー情報を `created_by`, `deleted_by` に記録
- 削除権限チェック（管理者のみ、など）

---

### 2. データ整合性

**制約チェック**:
- `total_trucks >= 0`
- `fixed_trucks >= 0`
- `fixed_trucks <= total_trucks`

→ 削除時には関係ないが、INSERT/UPDATE時に保証

---

### 3. トランザクション

```python
try:
    result = self.db.execute(stmt)
    self.db.commit()  # 明示的コミット
    return result.rowcount > 0
except Exception as e:
    self.db.rollback()  # エラー時ロールバック
    raise
```

- **ACID特性** を保証
- エラー時は自動ロールバック
- 並行アクセス時の競合も適切に処理

---

## テスト観点

### 1. 単体テスト（リポジトリ層）

```python
def test_delete_manual_success():
    """正常系: データが存在する日付を削除"""
    # Arrange
    repo.upsert_manual(ReservationManualRow(...))
    
    # Act
    result = repo.delete_manual(date(2025, 12, 10))
    
    # Assert
    assert result == True
    assert repo.get_manual(date(2025, 12, 10)) is None

def test_delete_manual_not_found():
    """異常系: 存在しない日付を削除（404）"""
    result = repo.delete_manual(date(2099, 12, 31))
    assert result == False
```

---

### 2. 統合テスト（API層）

```python
def test_delete_api_success(client):
    """正常系: API経由で削除"""
    # Arrange: データ登録
    client.post("/reservation/manual", json={
        "reserve_date": "2025-12-10",
        "total_trucks": 100,
        "fixed_trucks": 50
    })
    
    # Act: 削除
    response = client.delete("/reservation/manual/2025-12-10")
    
    # Assert
    assert response.status_code == 200
    assert response.json()["message"] == "Deleted successfully"
    
    # 再度GETで確認
    get_response = client.get("/reservation/manual/2025-12-10")
    assert get_response.status_code == 404

def test_delete_api_not_found(client):
    """異常系: 存在しない日付を削除（404）"""
    response = client.delete("/reservation/manual/2099-12-31")
    assert response.status_code == 404
```

---

### 3. E2Eテスト（フロントエンド）

```typescript
describe('予約削除機能', () => {
  it('カレンダーから削除できる', async () => {
    // 1. データがある日付をクリック
    await userEvent.click(screen.getByText('10'));
    
    // 2. モーダルが表示される
    expect(screen.getByText('予約データの削除')).toBeInTheDocument();
    
    // 3. 削除ボタンをクリック
    await userEvent.click(screen.getByRole('button', { name: '削除する' }));
    
    // 4. 成功メッセージが表示される
    await waitFor(() => {
      expect(screen.getByText('削除しました')).toBeInTheDocument();
    });
    
    // 5. カレンダーが再描画され、データが消えている
    expect(screen.queryByText('100')).not.toBeInTheDocument();
  });
});
```

---

## まとめ

### 現在の削除ロジック（2025-12-16更新）

1. **論理削除** を採用（物理削除から変更）
2. SQLは `UPDATE stg.reserve_daily_manual SET deleted_at = NOW(), deleted_by = 'system' WHERE reserve_date = ? AND deleted_at IS NULL`
3. レコードは残り、`deleted_at` フラグで管理
4. トランザクション管理あり（ACID保証）
5. 認証は未実装（TODO: `deleted_by` を認証コンテキストから取得）
6. 全SELECT文で `WHERE deleted_at IS NULL` を追加
7. ビューも論理削除を除外するように更新

### 推奨事項

| 項目 | 現状（2025-12-16） | 推奨 |
|------|------|------|
| **削除種別** | 論理削除 | ✅ 完了（2025-12-16実装） |
| **認証** | なし | ⚠️ JWT認証を追加すべき |
| **監査ログ** | deleted_at/deleted_byで記録 | ✅ OK（基本的な監査は可能） |
| **権限管理** | なし | ⚠️ 管理者のみ削除可能にすべき |
| **削除確認** | モーダルのみ | ✅ OK（誤操作防止済み） |
| **復元機能** | 未実装 | △ 必要に応じてUI追加検討 |

---

## 参考ファイル

- フロントエンド
  - `app/frontend/src/features/reservation/reservation-calendar/model/useReservationCalendarVM.ts`
  - `app/frontend/src/features/reservation/shared/infrastructure/ReservationDailyHttpRepository.ts`
  - `app/frontend/src/features/reservation/reservation-calendar/ui/ReservationHistoryCalendar.tsx`

- バックエンド
  - `app/backend/core_api/app/api/routers/reservation/router.py`
  - `app/backend/core_api/app/infra/adapters/reservation/reservation_repository.py`
  - `app/backend/core_api/app/core/ports/reservation_repository_port.py`

- データベース
  - `app/backend/core_api/migrations_v2/alembic/versions/20251216_001_add_reserve_daily_manual.py`

---

**レポート作成者**: GitHub Copilot  
**最終更新**: 2025-12-16
