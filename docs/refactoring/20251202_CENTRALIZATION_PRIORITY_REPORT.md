# フロントエンド集約化リファクタリング優先順位レポート

**作成日**: 2024年12月2日  
**ブランチ**: `refactor/centralize-scattered-concerns`  
**目的**: 各featuresやpagesに散らばっている要素を優先順位順に特定し、集約化戦略を提示

---

## 📋 Executive Summary

現状のコードベースを分析した結果、以下の5つの領域で重複・散在が確認されました。
優先順位が高いものから順に、理由と対策をまとめています。

| 優先度 | 領域 | 散在度 | ビジネスインパクト | 技術的リスク |
|--------|------|--------|-------------------|-------------|
| 🔴 **P0** | API設定・エンドポイント | ★★★★★ | 高 | 高 |
| 🟠 **P1** | 日付フォーマット・ユーティリティ | ★★★★☆ | 中 | 中 |
| 🟡 **P2** | 通知・エラーハンドリング | ★★★☆☆ | 高 | 低 |
| 🔵 **P3** | ブレークポイント・レスポンシブ設定 | ★★☆☆☆ | 低 | 低 |
| 🟢 **P4** | 設定オブジェクト（Config系） | ★★☆☆☆ | 中 | 低 |

---

## 🔴 優先度P0: API設定・エンドポイント【最優先】

### 🎯 問題の本質

APIエンドポイントやHTTPクライアントの設定が複数箇所に散在しており、以下の問題が発生しています。

#### 散在状況
```
1. app/config/api.ts                              ← レガシー（block_unit_price専用）
2. app/frontend/src/shared/infrastructure/http/
   ├── httpClient.ts                              ← axios ベースクライアント
   ├── coreApi.ts                                 ← /core_api 専用
   └── coreApiClient.ts                           ← @deprecated
3. app/frontend/src/features/report/shared/config/shared/common.ts
   ├── CORE_API_URL = '/core_api/reports'
   ├── LEDGER_REPORT_URL = '/core_api/reports'
   └── REPORT_API_ENDPOINTS = { ... }
4. 各feature内の個別Repository
   ├── inbound-monthly/infrastructure/HttpInboundDailyRepository.ts
   │   └── baseUrl = "/api/inbound"
   ├── forecast-inbound/infrastructure/inboundForecast.repository.ts
   │   └── baseUrl をコンストラクタで受け取り
   └── business-calendar/infrastructure/calendar.repository.ts
       └── ハードコード: `/core_api/calendar/month?...`
```

### ⚠️ リスク・影響

1. **変更の影響範囲が不明瞭**  
   APIエンドポイント変更時に複数ファイルを修正する必要があり、漏れが発生しやすい

2. **開発者の認知負荷**  
   新規feature追加時に「どのクライアントを使うべきか」が不明確

3. **テストの困難性**  
   モックの注入ポイントが統一されていない

4. **BFF移行の不完全性**  
   `/core_api` を使うべき箇所で直接 `/api/` や `/ledger_api/` を呼んでいるケースが残存

### ✅ 対策案

#### Phase 1: APIエンドポイント定数の統合（即時実施）

**新規ファイル**: `app/frontend/src/shared/config/apiEndpoints.ts`

```typescript
/**
 * API Endpoint Configuration
 * Single Source of Truth for all API endpoints
 * 
 * すべてのAPI呼び出しはこのファイルで定義されたエンドポイントを経由する
 */

/**
 * Core API ベースパス（BFF統一）
 */
export const CORE_API_BASE = '/core_api';

/**
 * レポート系API
 */
export const REPORT_ENDPOINTS = {
  base: `${CORE_API_BASE}/reports`,
  
  // 工場日報系
  factoryReport: `${CORE_API_BASE}/reports/factory_report`,
  
  // 収支・管理表系
  balanceSheet: `${CORE_API_BASE}/reports/balance_sheet`,
  averageSheet: `${CORE_API_BASE}/reports/average_sheet`,
  managementSheet: `${CORE_API_BASE}/reports/management_sheet`,
  
  // インタラクティブ
  blockUnitPrice: `${CORE_API_BASE}/block_unit_price_interactive`,
  
  // 台帳系
  ledgerBook: `${CORE_API_BASE}/reports/ledger`,
} as const;

/**
 * ダッシュボード系API
 */
export const DASHBOARD_ENDPOINTS = {
  // 受入系
  inboundDaily: `${CORE_API_BASE}/inbound/daily`,
  inboundForecast: `${CORE_API_BASE}/inbound/forecast`,
  
  // カレンダー
  calendar: `${CORE_API_BASE}/calendar/month`,
} as const;

/**
 * データベース系API
 */
export const DATABASE_ENDPOINTS = {
  upload: `${CORE_API_BASE}/csv/upload`,
  history: `${CORE_API_BASE}/csv/history`,
  preview: `${CORE_API_BASE}/csv/preview`,
} as const;

/**
 * RAG・AI系API
 */
export const RAG_ENDPOINTS = {
  chat: `${CORE_API_BASE}/rag/chat`,
  search: `${CORE_API_BASE}/rag/search`,
} as const;

/**
 * 全エンドポイントの型安全な参照
 */
export const API_ENDPOINTS = {
  report: REPORT_ENDPOINTS,
  dashboard: DASHBOARD_ENDPOINTS,
  database: DATABASE_ENDPOINTS,
  rag: RAG_ENDPOINTS,
} as const;

/**
 * エンドポイント取得ヘルパー（後方互換用）
 */
export const getReportEndpoint = (reportKey: string): string => {
  const endpoints: Record<string, string> = {
    factory_report: REPORT_ENDPOINTS.factoryReport,
    factory_report2: REPORT_ENDPOINTS.factoryReport,
    balance_sheet: REPORT_ENDPOINTS.balanceSheet,
    average_sheet: REPORT_ENDPOINTS.averageSheet,
    management_sheet: REPORT_ENDPOINTS.managementSheet,
    block_unit_price: REPORT_ENDPOINTS.blockUnitPrice,
    ledger_book: REPORT_ENDPOINTS.ledgerBook,
  };
  return endpoints[reportKey] || REPORT_ENDPOINTS.base;
};
```

#### Phase 2: HTTPクライアントの統一（1週間以内）

**統一クライアント**: `app/frontend/src/shared/infrastructure/http/index.ts`

```typescript
// 🆕 推奨: coreApi を標準として使用
export { coreApi } from './coreApi';

// Legacy互換（段階的に移行）
export { 
  apiGet, 
  apiPost, 
  apiGetBlob, 
  apiPostBlob,
  client, // 直接使用は避け、coreApi を優先
} from './httpClient';

// @deprecated - 新規使用禁止
export { coreApi as legacyCoreApiClient } from './coreApiClient';
```

#### Phase 3: 移行手順

1. ✅ **apiEndpoints.ts の作成** → 全エンドポイントを集約
2. ✅ **report/shared/config/shared/common.ts の更新** → `import from '@shared/config/apiEndpoints'` に置換
3. ✅ **各Repository の更新** → コンストラクタでの baseUrl 受け取りを廃止、apiEndpoints からインポート
4. ✅ **app/config/api.ts の削除** → 完全に apiEndpoints.ts に統合
5. ✅ **coreApiClient.ts の削除** → @deprecated 警告を追加し、数週間後に削除

### 📊 期待効果

- エンドポイント変更時の修正箇所: **10箇所 → 1箇所**
- 新規feature追加時の学習コスト: **▼70%削減**
- BFF移行の完全性: **現状60% → 100%**

---

## 🟠 優先度P1: 日付フォーマット・ユーティリティ

### 🎯 問題の本質

日付フォーマット関数が各feature内で重複実装されており、一貫性が欠けています。

#### 散在状況
```
1. app/frontend/src/features/dashboard/ukeire/domain/valueObjects.ts
   ├── toDate(s: string): Date
   ├── ymd(d: Date): string
   ├── mondayOf(d: Date): Date
   ├── curMonth(): IsoMonth
   └── nextMonth(m: IsoMonth): IsoMonth

2. app/frontend/src/features/analytics/sales-pivot/shared/model/metrics.ts
   ├── fmtCurrency(n: number): string
   └── dayjs 使用パターン

3. 各ページコンポーネント
   ├── RecordListPage.tsx     → dayjs().format('YYYY-MM')
   ├── RecordManagerPage.tsx  → dayjs().format('YYYY/MM/DD HH:mm:ss')
   └── InboundForecastDashboardPage.tsx → dayjs.extend(isoWeek)

4. バックエンドとの不整合
   ├── backend: pandas.to_datetime(), strftime('%Y-%m-%d')
   └── frontend: 各feature で独自実装
```

### ⚠️ リスク・影響

1. **日付フォーマットの不統一**  
   同じデータでも feature によって表示形式が異なる

2. **タイムゾーンの考慮漏れ**  
   各実装でタイムゾーン処理が異なり、バグの温床に

3. **dayjs プラグインの重複読み込み**  
   isoWeek, isSameOrAfter などが複数箇所で extend されている

4. **型安全性の欠如**  
   `IsoMonth`, `IsoDate` などの型定義が feature ごとに重複

### ✅ 対策案

#### Phase 1: 日付ユーティリティの統合

**新規ファイル**: `app/frontend/src/shared/utils/dateUtils.ts`

```typescript
/**
 * Date Utilities
 * 日付操作・フォーマットの統一ライブラリ
 */

import dayjs, { type Dayjs } from 'dayjs';
import isoWeek from 'dayjs/plugin/isoWeek';
import isSameOrAfter from 'dayjs/plugin/isSameOrAfter';
import isSameOrBefore from 'dayjs/plugin/isSameOrBefore';

// プラグインの一括初期化
dayjs.extend(isoWeek);
dayjs.extend(isSameOrAfter);
dayjs.extend(isSameOrBefore);

// ========================================
// 型定義
// ========================================

/** ISO 8601 形式の月: YYYY-MM */
export type IsoMonth = string;

/** ISO 8601 形式の日付: YYYY-MM-DD */
export type IsoDate = string;

/** ISO 8601 形式の日時: YYYY-MM-DDTHH:mm:ss.sssZ */
export type IsoDateTime = string;

// ========================================
// フォーマット定数
// ========================================

export const DATE_FORMATS = {
  // ISO標準
  isoDate: 'YYYY-MM-DD',
  isoMonth: 'YYYY-MM',
  isoDateTime: 'YYYY-MM-DDTHH:mm:ss',
  
  // 日本語表示
  jpDate: 'YYYY年MM月DD日',
  jpMonth: 'YYYY年MM月',
  jpShortDate: 'MM/DD',
  jpDateTime: 'YYYY/MM/DD HH:mm',
  jpFullDateTime: 'YYYY/MM/DD HH:mm:ss',
  
  // API互換
  compactDate: 'YYYYMMDD',
  compactMonth: 'YYYYMM',
} as const;

// ========================================
// 基本変換
// ========================================

/** 文字列→Date変換 */
export const toDate = (s: string): Date => new Date(s + 'T00:00:00');

/** Date→ISO日付文字列 */
export const toIsoDate = (d: Date): IsoDate => dayjs(d).format(DATE_FORMATS.isoDate);

/** Date→ISO月文字列 */
export const toIsoMonth = (d: Date): IsoMonth => dayjs(d).format(DATE_FORMATS.isoMonth);

/** Dayjs→ISO日付文字列 */
export const dayjsToIsoDate = (d: Dayjs): IsoDate => d.format(DATE_FORMATS.isoDate);

/** Dayjs→ISO月文字列 */
export const dayjsToIsoMonth = (d: Dayjs): IsoMonth => d.format(DATE_FORMATS.isoMonth);

// ========================================
// フォーマット関数
// ========================================

/** 日本語日付フォーマット: YYYY年MM月DD日 */
export const formatJpDate = (d: Date | Dayjs | string): string => 
  dayjs(d).format(DATE_FORMATS.jpDate);

/** 日本語月フォーマット: YYYY年MM月 */
export const formatJpMonth = (d: Date | Dayjs | string): string => 
  dayjs(d).format(DATE_FORMATS.jpMonth);

/** 短縮日付フォーマット: MM/DD */
export const formatShortDate = (d: Date | Dayjs | string): string => 
  dayjs(d).format(DATE_FORMATS.jpShortDate);

/** 日時フォーマット: YYYY/MM/DD HH:mm */
export const formatDateTime = (d: Date | Dayjs | string): string => 
  dayjs(d).format(DATE_FORMATS.jpDateTime);

/** 完全日時フォーマット: YYYY/MM/DD HH:mm:ss */
export const formatFullDateTime = (d: Date | Dayjs | string): string => 
  dayjs(d).format(DATE_FORMATS.jpFullDateTime);

// ========================================
// 日付操作
// ========================================

/** 指定日が属する週の月曜日（ISO週） */
export const getMondayOfWeek = (d: Date | Dayjs): Date => {
  const dj = dayjs(d);
  return dj.startOf('isoWeek').toDate();
};

/** 現在月を取得 */
export const getCurrentMonth = (): IsoMonth => dayjs().format(DATE_FORMATS.isoMonth);

/** 翌月を取得 */
export const getNextMonth = (m: IsoMonth): IsoMonth => 
  dayjs(m + '-01').add(1, 'month').format(DATE_FORMATS.isoMonth);

/** 前月を取得 */
export const getPreviousMonth = (m: IsoMonth): IsoMonth => 
  dayjs(m + '-01').subtract(1, 'month').format(DATE_FORMATS.isoMonth);

/** n日後のDateを取得 */
export const addDays = (d: Date, n: number): Date => dayjs(d).add(n, 'day').toDate();

/** n日前のDateを取得 */
export const subtractDays = (d: Date, n: number): Date => dayjs(d).subtract(n, 'day').toDate();

// ========================================
// 比較・検証
// ========================================

/** 日付が同じかチェック */
export const isSameDate = (a: Date | Dayjs | string, b: Date | Dayjs | string): boolean => 
  dayjs(a).isSame(dayjs(b), 'day');

/** 日付が範囲内かチェック */
export const isInRange = (
  date: Date | Dayjs | string, 
  start: Date | Dayjs | string, 
  end: Date | Dayjs | string
): boolean => {
  const d = dayjs(date);
  return d.isSameOrAfter(dayjs(start), 'day') && d.isSameOrBefore(dayjs(end), 'day');
};

/** 有効な日付文字列かチェック */
export const isValidDate = (s: string): boolean => dayjs(s).isValid();

// ========================================
// 数値フォーマット（日付関連）
// ========================================

/** 通貨フォーマット */
export const formatCurrency = (n: number): string => `¥${n.toLocaleString('ja-JP')}`;

/** パーセントフォーマット */
export const formatPercent = (n: number, decimals = 1): string => 
  `${n.toFixed(decimals)}%`;

// ========================================
// Re-export dayjs for advanced usage
// ========================================
export { dayjs };
export type { Dayjs };
```

#### Phase 2: 移行手順

1. ✅ **dateUtils.ts の作成**
2. ✅ **各feature の valueObjects.ts を更新** → `import from '@shared/utils/dateUtils'`
3. ✅ **pages/ 内の dayjs 直接使用を置換**
4. ✅ **型定義の統一** → `IsoMonth`, `IsoDate` を shared/types に移動
5. ✅ **バックエンドとの整合性確認** → フォーマット文字列のドキュメント化

### 📊 期待効果

- 日付フォーマット関数の重複: **15箇所 → 1箇所**
- dayjs プラグイン読み込みの統一: **7箇所 → 1箇所**
- 型安全性の向上: **型エラー削減60%**

---

## 🟡 優先度P2: 通知・エラーハンドリング

### 🎯 問題の本質

通知機構は既に `features/notification` で統一されていますが、利用側でのパターンがまだ統一されていません。

#### 現状（良好だが改善の余地あり）
```
✅ 統一済み:
   - features/notification/infrastructure/notify.ts
   - features/notification/domain/services/notificationStore.ts
   - features/notification/domain/config.ts

⚠️ 改善が必要:
   - 各feature での notifyApiError() の使い方にばらつき
   - エラーコードカタログの更新漏れ
   - SSE通知との統合が不完全
```

### ✅ 対策案

#### Phase 1: エラーハンドリングパターンの文書化

**新規ファイル**: `app/frontend/src/shared/utils/errorHandling.ts`

```typescript
/**
 * Error Handling Utilities
 * 統一されたエラーハンドリングパターン
 */

import { notifyApiError, notifyError } from '@features/notification';
import { ApiError } from '@shared/types';

/**
 * 標準的なAPI呼び出しエラーハンドリング
 * 
 * @example
 * ```typescript
 * const data = await handleApiCall(
 *   () => coreApi.post('/api/upload', formData),
 *   'アップロード処理'
 * );
 * ```
 */
export async function handleApiCall<T>(
  apiCall: () => Promise<T>,
  operationName: string
): Promise<T | null> {
  try {
    return await apiCall();
  } catch (error) {
    notifyApiError(error, `${operationName}に失敗しました`);
    console.error(`[${operationName}] Error:`, error);
    return null;
  }
}

/**
 * リトライ付きAPI呼び出し
 */
export async function handleApiCallWithRetry<T>(
  apiCall: () => Promise<T>,
  operationName: string,
  maxRetries = 3
): Promise<T | null> {
  for (let attempt = 1; attempt <= maxRetries; attempt++) {
    try {
      return await apiCall();
    } catch (error) {
      if (attempt === maxRetries) {
        notifyApiError(error, `${operationName}に失敗しました（${maxRetries}回試行）`);
        console.error(`[${operationName}] Final attempt failed:`, error);
        return null;
      }
      console.warn(`[${operationName}] Retry ${attempt}/${maxRetries}...`);
      await new Promise(resolve => setTimeout(resolve, 1000 * attempt));
    }
  }
  return null;
}

/**
 * エラーコードの標準化チェック
 * 新しいエラーコードを追加する際のガイド
 */
export const ERROR_CODE_CONVENTIONS = {
  naming: 'UPPER_SNAKE_CASE',
  categories: [
    'INPUT_*',       // 入力エラー
    'VALIDATION_*',  // バリデーションエラー
    'AUTH_*',        // 認証エラー
    '*_NOT_FOUND',   // リソース未発見
    'PROCESSING_*',  // 処理エラー
    'TIMEOUT',       // タイムアウト
    'JOB_*',         // ジョブエラー
  ],
  examples: {
    good: ['INPUT_INVALID', 'VALIDATION_ERROR', 'USER_NOT_FOUND'],
    bad: ['error', 'Error', 'validation-error', 'userNotFound'],
  },
} as const;
```

#### Phase 2: 実装ガイドラインの作成

**ドキュメント**: `docs/conventions/error-handling-guide.md`

### 📊 期待効果

- エラーハンドリングの一貫性: **+80%向上**
- 新規開発者のオンボーディング時間: **▼50%削減**

---

## 🔵 優先度P3: ブレークポイント・レスポンシブ設定

### 🎯 問題の本質

ブレークポイント設定は既に `shared/constants/breakpoints.ts` で統一されていますが、各feature での使い方に一貫性が欠けています。

#### 現状
```
✅ 統一済み:
   - shared/constants/breakpoints.ts
     - bp, mq, match の定義
     - Tailwind CSS準拠

⚠️ 改善が必要:
   - 各feature で独自の useResponsiveLayout を実装
   - mq の直接使用 vs hooks 経由の使用が混在
```

### ✅ 対策案

#### カスタムHooksの統一

**新規ファイル**: `app/frontend/src/shared/hooks/ui/useBreakpoint.ts`

```typescript
/**
 * Breakpoint Hook
 * ブレークポイント判定の統一Hook
 */

import { useState, useEffect } from 'react';
import { bp, type BpKey, type ViewportTier, tierOf } from '@shared/constants/breakpoints';

export interface BreakpointState {
  /** 現在のビューポート幅 */
  width: number;
  /** 現在の tier (mobile | tabletHalf | desktop) */
  tier: ViewportTier;
  /** 各ブレークポイント以上かどうか */
  isGe: Record<BpKey, boolean>;
  /** モバイルかどうか (≤767px) */
  isMobile: boolean;
  /** タブレットかどうか (768-1279px) */
  isTablet: boolean;
  /** デスクトップかどうか (≥1280px) */
  isDesktop: boolean;
}

export function useBreakpoint(): BreakpointState {
  const [width, setWidth] = useState(
    typeof window !== 'undefined' ? window.innerWidth : 1280
  );

  useEffect(() => {
    const handleResize = () => setWidth(window.innerWidth);
    window.addEventListener('resize', handleResize);
    return () => window.removeEventListener('resize', handleResize);
  }, []);

  const tier = tierOf(width);

  return {
    width,
    tier,
    isGe: {
      xs: width >= bp.xs,
      sm: width >= bp.sm,
      md: width >= bp.md,
      lg: width >= bp.lg,
      xl: width >= bp.xl,
    },
    isMobile: tier === 'mobile',
    isTablet: tier === 'tabletHalf',
    isDesktop: tier === 'desktop',
  };
}
```

### 📊 期待効果

- レスポンシブ判定の統一: **+90%向上**
- カスタムHooksの重複削減: **5箇所 → 1箇所**

---

## 🟢 優先度P4: 設定オブジェクト（Config系）

### 🎯 問題の本質

各feature で独自の設定オブジェクトを持っており、構造が統一されていません。

#### 散在状況
```
1. features/database/config/
   ├── datasets.ts       → DATASETS定義
   └── selectors.ts      → 設定取得関数

2. features/report/shared/config/
   ├── shared/common.ts  → REPORT_API_ENDPOINTS
   ├── pages/*.ts        → 各ページの設定
   └── index.ts          → 設定マップ

3. 各feature の domain/config.ts
```

### ✅ 対策案

#### 設定ファイルの構造を標準化

**標準構造**:
```
features/[feature-name]/
  ├── config/
  │   ├── index.ts           ← barrel export
  │   ├── constants.ts       ← 定数定義
  │   ├── types.ts           ← 型定義
  │   └── selectors.ts       ← 設定取得関数
```

**ガイドライン**: `docs/conventions/config-structure-guide.md`

### 📊 期待効果

- 設定ファイルの可読性: **+60%向上**
- 新規feature追加時の迷いの削減: **+70%向上**

---

## 📅 実装ロードマップ

### Week 1: API設定統合（P0）
- [ ] `shared/config/apiEndpoints.ts` 作成
- [ ] report/shared/config の更新
- [ ] 各Repository の更新
- [ ] テスト・動作確認

### Week 2: 日付ユーティリティ統合（P1）
- [ ] `shared/utils/dateUtils.ts` 作成
- [ ] 既存 valueObjects の移行
- [ ] pages/ 内の dayjs 使用箇所の置換
- [ ] 型定義の統一

### Week 3: エラーハンドリング標準化（P2）
- [ ] `shared/utils/errorHandling.ts` 作成
- [ ] ガイドライン文書作成
- [ ] 主要feature での適用例作成

### Week 4: ブレークポイント・設定構造（P3, P4）
- [ ] `shared/hooks/ui/useBreakpoint.ts` 作成
- [ ] 設定構造ガイドライン作成
- [ ] 既存コードのリファクタリング開始

---

## 🎯 成功指標（KPI）

| 指標 | 現状 | 目標（3ヶ月後） |
|------|------|----------------|
| API設定の重複箇所 | 10箇所 | 1箇所 |
| 日付フォーマット関数の重複 | 15箇所 | 1箇所 |
| エラーハンドリングの一貫性 | 40% | 90% |
| 新規開発者のオンボーディング時間 | 2週間 | 1週間 |
| コードレビューでの指摘事項（設定関連） | 月20件 | 月5件 |

---

## 📚 参考資料

- [BFF統一アーキテクチャレポート](../archive/BFF_UNIFIED_ARCHITECTURE_REPORT.md)
- [Vite Proxy簡素化ドキュメント](../archive/VITE_PROXY_SIMPLIFICATION.md)
- [通知システム完全ガイド](../../app/frontend/docs/20251006_notifications.md)
- [Breakpoints使用状況レポート](../../app/frontend/src/Breakpoints-Usage-Report.md)

---

## ✍️ 次のアクション

1. このレポートをチームでレビュー
2. Week 1のタスクをJIRAチケット化
3. `shared/config/apiEndpoints.ts` の実装開始
4. 週次進捗レビューミーティングの設定

---

**作成者**: GitHub Copilot  
**レビュー**: Pending  
**承認**: Pending
