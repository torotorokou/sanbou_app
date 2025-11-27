# 日次搬入量（棒）＋日次累積（線）カード実装 - 動作確認ガイド

## 概要

SOLID原則とMVCパターンに基づいて、日次搬入量と累積データを表示するカード機能を実装しました。

## 実装内容

### Backend（FastAPI / core_api）

#### 1. Domain/DTO
- `app/domain/inbound.py`
  - `InboundDailyRow`: 日次搬入量データのDTO（pydantic）
  - `CumScope`: 累積計算スコープのLiteral型

#### 2. Port
- `app/ports/inbound_repository.py`
  - `InboundRepository`: 抽象インターフェース
  - `fetch_daily()`: 日次データ取得メソッド定義

#### 3. Infrastructure
- `app/repositories/inbound_pg_repo.py`
  - `InboundPgRepository`: PostgreSQL実装
  - CTE + ウィンドウ関数で連続日・0埋め・累積計算を実現

#### 4. Router
- `app/routers/inbound.py`
  - `GET /api/inbound/daily`: 日次搬入量データ取得エンドポイント
- `app/app.py`: ルータ登録

#### 5. Tests
- `tests/test_inbound_daily.py`
  - cum_scope各モード（none/range/month/week）のテスト
  - バリデーション（範囲逆転、範囲超過）のテスト

### Frontend（React + TypeScript）

#### 1. Port/Repository
- `inbound-monthly/ports/InboundDailyRepository.ts`: インターフェース定義
- `inbound-monthly/infrastructure/HttpInboundDailyRepository.ts`: HTTP実装

#### 2. Application/VM
- `inbound-monthly/application/useInboundMonthlyVM.ts`
  - 月変更時の自動データ取得
  - 日次実績・累積データの整形

#### 3. UI統合
- `InboundForecastDashboardPage.tsx`
  - `HttpInboundDailyRepository`を使用してAPI経由でデータ取得
  - `useInboundMonthlyVM`でデータ整形
  - `CombinedDailyCard`に日次・累積データを渡して表示

#### 4. Export
- `inbound-monthly/index.ts`: 機能のエクスポート
- `features/dashboard/ukeire/index.ts`: 親レベルのエクスポート

## 動作確認チェックリスト

### Backend API確認

#### 1. 基本動作（cum_scope=none）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-10-01&end=2025-10-05&cum_scope=none"
```
**期待結果:**
- ステータス: 200 OK
- レスポンス: 5日分の連続データ（欠損日は0埋め）
- `cum_ton`フィールドはすべて`null`

#### 2. 累積計算（cum_scope=range）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-10-01&end=2025-10-05&cum_scope=range"
```
**期待結果:**
- `cum_ton`が単調増加（または同値）
- 全期間での累積値が計算される

#### 3. 月ごと累積（cum_scope=month）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-09-28&end=2025-10-03&cum_scope=month"
```
**期待結果:**
- 月が変わるタイミングで`cum_ton`がリセット
- 9月末の累積 > 10月初日の累積（リセットされるため）

#### 4. 週ごと累積（cum_scope=week）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-10-05&end=2025-10-13&cum_scope=week"
```
**期待結果:**
- `iso_week`が変わるタイミングで`cum_ton`がリセット
- 週の最初の日から累積が再スタート

#### 5. セグメント指定
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-10-01&end=2025-10-05&segment=A&cum_scope=none"
```
**期待結果:**
- `segment`フィールドがすべて`"A"`
- 指定セグメントのデータのみ取得

#### 6. バリデーションエラー（範囲逆転）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-10-10&end=2025-10-05&cum_scope=none"
```
**期待結果:**
- ステータス: 400 Bad Request
- エラーメッセージ: "start must be <= end"

#### 7. バリデーションエラー（範囲超過）
```bash
curl "http://localhost:8003/api/inbound/daily?start=2025-01-01&end=2026-01-05&cum_scope=none"
```
**期待結果:**
- ステータス: 400 Bad Request
- エラーメッセージ: "Date range exceeds 366 days"

### Frontend UI確認

#### 1. 初期表示
- ブラウザで`http://localhost:5173`にアクセス
- 受入ダッシュボードを開く
- **期待結果:**
  - 当月の日次搬入量カード（棒グラフ）が表示される
  - 累積搬入量カード（折れ線グラフ）が表示される
  - データがローディング中はSkeletonが表示される

#### 2. 月変更による再取得
- 月ナビゲーション（前月/次月ボタン）で月を変更
- **期待結果:**
  - 選択月のデータが自動再取得される
  - 日次・累積カードのデータが更新される
  - 欠損日は0トンの棒として表示される

#### 3. タブ切り替え
- CombinedDailyCard内の「日次」「累積」タブを切り替え
- **期待結果:**
  - タブ切り替えがスムーズに動作
  - それぞれのチャートが正しく表示される

#### 4. レスポンシブ表示
- ブラウザウィンドウをリサイズ（Desktop / Laptop / Mobile）
- **期待結果:**
  - 各画面サイズでレイアウトが適切に変化
  - モバイル時は縦積み、デスクトップ時は横並び

#### 5. エラーハンドリング
- APIサーバーを停止して再読み込み
- **期待結果:**
  - エラーメッセージが表示される
  - アプリケーションがクラッシュしない

#### 6. 前月・前年比較（オプション）
- 日次カードの「先月」「前年」トグルスイッチを操作
- **期待結果:**
  - 現時点では前月・前年データは未実装（TODO）
  - トグルは動作するが比較データは表示されない（今後の拡張ポイント）

## データフロー

```
1. User: 月変更操作
   ↓
2. useInboundMonthlyVM: month変更を検知
   ↓
3. HttpInboundDailyRepository: GET /api/inbound/daily (start, end, cum_scope=month)
   ↓
4. core_api Router: リクエスト受信
   ↓
5. InboundPgRepository: CTE + ウィンドウ関数でSQL実行
   ↓
6. PostgreSQL: mart.receive_daily + ref.v_calendar_classified からデータ取得
   ↓
7. Repository: InboundDailyRowのリストを返却
   ↓
8. VM: データ整形（日次・累積用に分離）
   ↓
9. CombinedDailyCard: Rechartsで棒グラフ・折れ線グラフ描画
```

## トラブルシューティング

### Backend

**問題: テーブル/ビューが存在しない**
- 原因: `mart.receive_daily`または`ref.v_calendar_classified`が未作成
- 対処: マイグレーションを実行してスキーマを最新化

**問題: "column r.segment does not exist" エラー**
- 原因: `mart.receive_daily`テーブルに`segment`カラムが存在しない
- 対処: ✅ 修正済み - SQLから`segment`機能を削除し、常に`NULL`を返すように変更
- 注意: 将来的に`segment`カラムが追加される場合は、SQLのCTE部分を再度有効化すること

**問題: 累積計算が正しくない**
- 原因: ウィンドウ関数のPARTITION BY / ORDER BYが不適切
- 対処: SQLのCTEロジックを確認、cum_scopeの条件分岐を検証

### Frontend

**問題: データが表示されない**
- 原因: APIプロキシ設定が不正、またはAPIサーバーが起動していない
- 対処: 
  - Viteプロキシ設定（`/api` → core_api）を確認
  - `docker-compose`でcore_apiコンテナが起動しているか確認

**問題: 型エラー**
- 原因: DTO型定義が不一致
- 対処: Backend（pydantic）とFrontend（TypeScript）の型定義を同期

## 今後の拡張

### 優先度: 高
1. **前月・前年データ対応**
   - 現在は当月のみ取得
   - 前月・前年のデータを並行取得して比較表示

### 優先度: 中
2. **セグメント機能の追加**
   - ⚠️ 現在は`mart.receive_daily`に`segment`カラムが存在しないため、機能を無効化
   - テーブルスキーマに`segment`カラム追加後、以下を実施：
     - SQLのCTE部分で`segment`フィルタリングを再有効化
     - UI上でSegmentedコンポーネント追加（全体/セグメントA/Bなど選択可能に）

3. **累積スコープの動的切り替え**
   - UI上で「全期間/月ごと/週ごと」を選択可能に

4. **パフォーマンス最適化**
   - `mart.receive_daily`にインデックス追加（ddate, segment）
   - 頻繁に使用する場合はdense（連続日・0埋め）ビューを永続化

### 優先度: 低
5. **エクスポート機能**
   - CSV/Excelでデータエクスポート

6. **リアルタイム更新**
   - WebSocketまたはポーリングで最新データを自動取得

## 技術的なポイント

### SOLID原則の適用
- **Single Responsibility**: 各レイヤー（Domain/Port/Infrastructure/Application/UI）が明確な責務を持つ
- **Open/Closed**: Portを通じて拡張可能（MockRepository↔HttpRepository切り替え可能）
- **Liskov Substitution**: InboundRepositoryインターフェースを満たす実装は互換性あり
- **Interface Segregation**: 必要最小限のメソッドのみ定義
- **Dependency Inversion**: 上位層（Application）は下位層（Infrastructure）に依存せず、Portに依存

### MVCパターン
- **Model**: Domain/DTO（InboundDailyRow）
- **View**: UI Components（DailyActualsCard, DailyCumulativeCard, CombinedDailyCard）
- **Controller**: ViewModel（useInboundMonthlyVM）

### その他
- **CTE（Common Table Expression）**: 複雑なSQLを段階的に構築
- **ウィンドウ関数**: 累積計算を効率的に実行（ROW_NUMBER不要）
- **TypeScript型安全性**: pydanticとTypeScriptの型定義を一致させてランタイムエラーを防止

## まとめ

本実装により、以下を達成しました：

✅ Backend: CTE+ウィンドウ関数で連続日・0埋め・累積計算を実現  
✅ Frontend: SOLID原則に基づいたレイヤー分離  
✅ UI: Rechartsで日次棒グラフ・累積折れ線グラフを表示  
✅ テスト: 各累積モードとバリデーションのカバレッジ  
✅ ドキュメント: 動作確認チェックリストとトラブルシューティング

初心者にも追いやすいコード設計と、明確な責務分離により、今後の拡張・保守が容易になっています。
