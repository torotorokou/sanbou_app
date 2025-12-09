# 顧客比較分析機能のリファクタリング完了レポート

**実施日**: 2025年11月21日  
**対象機能**: 顧客離脱分析（来なくなった顧客）  
**アーキテクチャ**: FSD + MVVM + Repository + SOLID原則

---

## 📋 実施した主な変更

### 1. 命名規則の統一（target/compare → current/previous）

#### Before → After
- `targetStart` → `currentStart`（今期の開始月）
- `targetEnd` → `currentEnd`（今期の終了月）
- `targetMonths` → `currentMonths`（今期の月リスト）
- `targetCustomers` → `currentCustomers`（今期の顧客）
- `compareStart` → `previousStart`（前期の開始月）
- `compareEnd` → `previousEnd`（前期の終了月）
- `compareMonths` → `previousMonths`（前期の月リスト）
- `compareCustomers` → `previousCustomers`（前期の顧客）
- `onlyCompare` → `lostCustomers`（離脱顧客）

#### UI文言の変更
- 「対象月グループ」 → 「今期（分析対象期間）」
- 「比較月グループ」 → 「前期（比較期間）」
- 「来なくなった顧客」 → 「来なくなった顧客（離脱）」
- カードタイトルに件数表示を追加（例: `今期の顧客（対象期間）: 15 件`）

**改善効果**: 時間軸が明確になり、「どちらが過去でどちらが現在か」が一目で理解可能に。

---

### 2. ViewModel（useCustomerComparison）の型安全性向上

#### 新規追加した型定義

```typescript
export interface CustomerChurnViewModel {
    /** 今期（分析対象期間）の顧客リスト */
    currentCustomers: CustomerData[];
    /** 前期（比較期間）の顧客リスト */
    previousCustomers: CustomerData[];
    /** 離脱顧客（前期 - 今期） */
    lostCustomers: CustomerData[];
}
```

#### 改善内容
- **明確なインターフェイス定義**: 返り値の型を厳密に定義
- **JSDoc完備**: 各プロパティの意味を日本語で明記
- **ビジネスロジックの明示化**: `lostCustomers = previous - current` の関係性を明確化
- **useMemoによるパフォーマンス最適化**: 不要な再計算を防止

**改善効果**: 型推論が効き、IDEの補完が強化され、バグの混入リスクが低減。

---

### 3. CSV生成ユーティリティの実装

#### 新規ファイル
`features/analytics/customer-list/model/utils/buildLostCustomersCsv.ts`

#### 実装した純粋関数

```typescript
// CSV生成（純粋関数）
export function buildLostCustomersCsv(customers: CustomerData[]): string

// CSVダウンロード（副作用関数）
export function downloadCsv(csvContent: string, filename: string): void
```

#### 特徴
- **純粋関数として実装**: I/Oに依存せず、テストが容易
- **CSVエスケープ処理**: ダブルクォート・カンマ・改行を適切にエスケープ
- **UTF-8 BOM付き**: Excelで文字化けしないよう配慮
- **再利用可能**: 他のfeatureからもimportして利用可能

**改善効果**: 単一責任原則（SRP）に準拠し、テスタビリティが向上。

---

### 4. Pageコンポーネントの責務明確化

#### Before（混在していた責務）
- 期間選択のstate管理
- 分析実行のロジック
- ダウンロードのロジック
- UIレイアウト
- データ加工（useMemoの呼び出し）

#### After（分離された責務）
- **State管理のみ**: 期間選択とUI状態（analysisStarted, isAnalyzing）
- **イベントハンドリング**: ボタンクリック時の処理をシンプルに記述
- **ViewModelへの委譲**: データ加工は`useCustomerComparison`に完全委譲
- **UIレイアウト**: Antd ComponentsとCSSの配置に集中

#### 改善されたハンドラ

```typescript
// Excel全データダウンロード
const handleDownloadExcel = async () => { /* API経由 */ }

// CSV離脱顧客ダウンロード（NEW!）
const handleDownloadLostCustomersCsv = () => {
    if (!analysisStarted) {
        message.warning('先に分析を実行してください');
        return;
    }
    if (lostCustomers.length === 0) {
        message.warning('離脱顧客が存在しません');
        return;
    }
    const csv = buildLostCustomersCsv(lostCustomers);
    downloadCsv(csv, '来なくなった顧客.csv');
    message.success(`離脱顧客 ${lostCustomers.length} 件をCSVダウンロードしました`);
}
```

**改善効果**: Pageコンポーネントが軽量化され、テストとメンテナンスが容易に。

---

### 5. 新機能: 離脱顧客CSV個別ダウンロード

#### 追加したUI要素
- **ボタン**: 「離脱顧客のみCSVダウンロード」
- **アイコン**: `DownloadOutlined`（直感的なUI）
- **色分け**: 赤系（#f43f5e）で離脱顧客に注意を促すデザイン

#### 動作フロー
1. ユーザーが「分析する」を実行
2. 離脱顧客が0件の場合 → warning表示
3. 離脱顧客が存在する場合 → CSV生成 → ダウンロード → 成功メッセージ（件数表示付き）

**改善効果**: ユーザーが欲しいデータだけを迅速に取得でき、UX向上。

---

### 6. Feature公開APIの更新

#### `features/analytics/customer-list/index.ts`

```typescript
// 新規エクスポート
export type { CustomerChurnViewModel } from './domain/services/analysisService';
export { buildLostCustomersCsv, downloadCsv } from './model/utils/buildLostCustomersCsv';
```

**改善効果**: 必要な型・関数が明示的にエクスポートされ、他機能からの利用が容易。

---

## 🏗️ SOLID / FSD原則への適合状況

### ✅ SRP（単一責任原則）
- **Page**: UIレイアウトとイベント配線のみ
- **ViewModel**: データ取得と集計ロジックのみ
- **CSV Utility**: CSV生成とダウンロードのみ
- **Form Component**: 期間入力UIのみ
- **Card Component**: データ表示のみ

### ✅ OCP（開放閉鎖原則）
- CSV生成関数は、新しいフォーマットが必要になっても既存コードを変更せず拡張可能
- ViewModelは、新しい比較パターン（例: 3期間比較）も追加可能

### ✅ LSP（リスコフの置換原則）
- `CustomerData`型を持つ配列であれば、CSV生成関数に渡すことが可能
- 抽象化されたインターフェイスで実装されており、テストダブルへの置き換えが容易

### ✅ ISP（インターフェイス分離原則）
- `CustomerChurnViewModel`は必要最小限のプロパティのみ公開
- 各UIコンポーネントは必要なpropsのみを受け取る

### ✅ DIP（依存関係逆転原則）
- ViewModelは抽象（`IAnalysisRepository`）に依存（現状はモックデータ）
- 将来API実装に切り替えても、ViewModelの変更は不要

---

## 📊 想定ユースケース

### ユースケース1: 月次の離脱顧客分析
**シナリオ**: 営業マネージャーが、先月まで取引があったのに今月は来ていない顧客をリストアップしたい

**操作フロー**:
1. 今期を「2024-11」、前期を「2024-10」に設定
2. 「分析する」ボタンをクリック
3. 「来なくなった顧客（離脱）」カードに表示される顧客を確認
4. 「離脱顧客のみCSVダウンロード」で営業チームに共有

**リファクタリングの効果**:
- 命名が明確なため、設定ミスが減少
- CSV出力で迅速にデータ共有可能
- 件数表示により、即座に状況を把握可能

---

### ユースケース2: 四半期比較での傾向分析
**シナリオ**: 経営層が、Q3とQ2の顧客動向を比較し、離脱率を確認したい

**操作フロー**:
1. 今期を「2024-07～2024-09（Q3）」、前期を「2024-04～2024-06（Q2）」に設定
2. 分析実行
3. 3つのカードで現在顧客・過去顧客・離脱顧客を視覚的に比較
4. 必要に応じてExcelで全データをダウンロード

**リファクタリングの効果**:
- `currentMonths` / `previousMonths`という命名で、複数月の比較が直感的に理解可能
- ViewModelのuseMemoにより、大量データでもパフォーマンスが安定
- カード表示により、データの内訳が一目瞭然

---

### ユースケース3: 開発者がCSV機能を別機能へ再利用
**シナリオ**: 他のfeatureで顧客データをCSV出力したい

**操作フロー**:
```typescript
import { buildLostCustomersCsv, downloadCsv } from '@features/analytics/customer-list';

const handleExport = () => {
    const csv = buildLostCustomersCsv(myCustomerData);
    downloadCsv(csv, 'export.csv');
};
```

**リファクタリングの効果**:
- 純粋関数として実装されているため、どこからでも安全に呼び出せる
- FSDのbarrel exportにより、importパスが明確
- TypeScript型定義により、誤った型のデータを渡すとコンパイルエラー

---

## 🎯 開発者目線での改善ポイント

### 1. 可読性の向上
- **Before**: `targetMonths` と `compareMonths` のどちらが「今」なのか分かりにくかった
- **After**: `currentMonths` と `previousMonths` で時間軸が明確

### 2. 保守性の向上
- **Before**: Page内にCSV生成ロジックを直書きする必要があった
- **After**: 純粋関数として分離され、単体テストが容易

### 3. 拡張性の向上
- **Before**: 新しい出力形式（例: JSON）を追加する際、既存コードを改変する必要があった
- **After**: 新しいutilを追加するだけで、既存機能に影響なし

### 4. 型安全性の向上
- **Before**: ViewModelの返り値が暗黙的な`any`型になっていた
- **After**: `CustomerChurnViewModel`で厳密に型定義され、TypeScriptの恩恵を最大化

### 5. テスタビリティの向上
- **Before**: Page全体をマウントしないとロジックをテストできなかった
- **After**: 純粋関数・ViewModelを個別にユニットテスト可能

---

## 🔍 今後の改善余地

1. **Repository層の実装**: 現在はモックデータ。API実装時に`IAnalysisRepository`を実装
2. **エラーハンドリングの強化**: ViewModelに`error`プロパティを追加し、Pageで表示
3. **ローディング状態の管理**: ViewModelに`isLoading`を追加し、より細かい制御
4. **E2Eテストの追加**: Playwright/Cypressでユーザー操作フローをテスト
5. **パフォーマンス計測**: 大量データ（10,000件以上）でのuseMemo効果を検証

---

## ✅ 結論

このリファクタリングにより、以下が達成されました。

- ✅ **命名の一貫性**: 時間軸ベースの明確な命名（current/previous/lost）
- ✅ **MVVM構成の徹底**: Page（View）とViewModel（Hook）の責務分離
- ✅ **CSV機能の追加**: 離脱顧客の個別エクスポート機能
- ✅ **SOLID原則への準拠**: 各モジュールが単一責任で疎結合
- ✅ **FSD構成の遵守**: features配下の適切な階層化
- ✅ **型安全性の向上**: TypeScriptの型システムを最大活用
- ✅ **再利用性の確保**: CSV utilityが他機能でも利用可能

**開発者体験**: コードの意図が明確になり、新規開発者がコードを読んだ際の理解コストが大幅に削減されました。また、機能追加時の影響範囲が限定され、安全な拡張が可能になりました。

---

**実施者**: GitHub Copilot (Claude Sonnet 4.5)  
**レビュー推奨**: コードレビューにて、命名規則とアーキテクチャの妥当性を再確認
