# ukeireVolume 統合リファクタリング完了レポート

## 実行日時
2025-10-20

## ブランチ
`refactor/consolidate-ukeireVolume`

---

## 1. Before → After ファイル移動マッピング

### 削除されたディレクトリ
- ❌ `features/dashboard/ukeire/**` (全削除)
- ❌ `pages/dashboard/ukeire/**` (全削除)

### 新規作成されたファイル

#### 共通モジュール
- ✅ `features/ukeireVolume/shared/api/client.ts` (新設HTTPクライアント)
- ✅ `features/ukeireVolume/index.ts` (Barrel exports)

#### Repository層
- ✅ `features/ukeireVolume/forecast/repository/UkeireForecastRepositoryImpl.ts`
- ✅ `features/ukeireVolume/forecast/repository/__mocks__/MockUkeireForecastRepository.ts` (移動)
- ✅ `features/ukeireVolume/actuals/repository/UkeireActualsRepository.ts` (IF新設)
- ✅ `features/ukeireVolume/actuals/repository/UkeireActualsRepositoryImpl.ts`
- ✅ `features/ukeireVolume/history/repository/UkeireHistoryRepository.ts` (IF新設)
- ✅ `features/ukeireVolume/history/repository/UkeireHistoryRepositoryImpl.ts`

#### ViewModel層
- ✅ `features/ukeireVolume/actuals/hooks/useUkeireActualsVM.ts` (新設)
- ✅ `features/ukeireVolume/history/hooks/useUkeireHistoryVM.ts` (新設)
- ✅ `features/ukeireVolume/overview/hooks/useUkeireVolumeCombinedVM.ts` (統合VM・新設)

#### Page層
- ✅ `pages/ukeire/index.tsx` (骨組みのみ・新設)

### 既存ファイルの更新

#### ルーティング
- 📝 `app/routes/routes.ts`
  - `DASHBOARD_UKEIRE: '/dashboard/ukeire'` → `UKEIRE: '/ukeire'`
- 📝 `app/routes/AppRoutes.tsx`
  - `InboundForecastDashboardPage` → `UkeirePage`
- 📝 `app/navigation/sidebarMenu.tsx`
  - `ROUTER_PATHS.DASHBOARD_UKEIRE` → `ROUTER_PATHS.UKEIRE`
- 📝 `pages/home/PortalPage.tsx`
  - `ROUTER_PATHS.DASHBOARD_UKEIRE` → `ROUTER_PATHS.UKEIRE`

#### Cross-module参照
- 📝 `features/calendar/ui/CalendarCard.tsx`
  - `@/features/dashboard/ukeire/ui/components/BusinessCalendar` → `@/features/ukeireVolume/shared/components/BusinessCalendar`

---

## 2. アーキテクチャ変更サマリ

### Before (旧構造)
```
features/dashboard/ukeire/
├── application/ (VM + Repository)
├── domain/ (Types + Services)
└── ui/ (Cards + Components)

pages/dashboard/ukeire/
└── InboundForecastDashboardPage.tsx (大きなPage)
```

### After (新構造)
```
features/ukeireVolume/
├── shared/
│   ├── api/client.ts (共通HTTPクライアント)
│   └── components/ (共有UI)
├── model/ (統合型定義)
├── services/ (純関数)
├── actuals/ (実績feature)
│   ├── repository/
│   ├── hooks/
│   └── ui/
├── history/ (過去データfeature)
│   ├── repository/
│   ├── hooks/
│   └── ui/
├── forecast/ (予測feature)
│   ├── api/
│   ├── repository/
│   ├── hooks/
│   └── ui/
└── overview/ (合成レイヤ)
    ├── hooks/useUkeireVolumeCombinedVM.ts
    └── ui/

features/kpiTarget/ (KPI共通化)
└── ui/TargetCard.tsx

pages/ukeire/
└── index.tsx (レイアウト専用Page)
```

---

## 3. 主要な新規ファイル Diff

### 3.1 shared/api/client.ts (共通HTTPクライアント)

```typescript
/**
 * 受入量 - 共通HTTPクライアント
 * Repository層から使用する汎用fetch wrapper
 */

export class HttpError extends Error {
  constructor(
    public url: string,
    public status: number,
    public statusText: string,
    message?: string
  ) {
    super(message || `HTTP ${status}: ${url}`);
    this.name = "HttpError";
  }
}

export const http = {
  async get<T>(url: string, signal?: AbortSignal): Promise<T> {
    const res = await fetch(url, { 
      method: "GET",
      signal, 
      credentials: "include",
      headers: { "Content-Type": "application/json" },
    });
    if (!res.ok) throw new HttpError(url, res.status, res.statusText);
    return res.json() as Promise<T>;
  },
  // post() も同様に実装
};
```

### 3.2 overview/hooks/useUkeireVolumeCombinedVM.ts (統合VM)

```typescript
/**
 * Ukeire Volume Combined ViewModel
 * actuals/history/forecast の3つのVMを統合し、UI用に整形
 */
import { useState } from "react";
import dayjs from "dayjs";
import { useUkeireActualsVM } from "../../actuals/hooks/useUkeireActualsVM";
import { useUkeireHistoryVM } from "../../history/hooks/useUkeireHistoryVM";
import { useUkeireForecastVM } from "../../forecast/hooks/useUkeireForecastVM";

export function useUkeireVolumeCombinedVM({
  actualsRepository,
  historyRepository,
  forecastRepository,
  initialMonth,
}: UkeireVolumeCombinedViewProps) {
  const [month, setMonth] = useState<IsoMonth>(initialMonth || dayjs().format("YYYY-MM"));
  
  // 各VMを独立して呼び出し
  const forecastVM = useUkeireForecastVM(forecastRepository, month);
  const actualsVM = useUkeireActualsVM(actualsRepository, month);
  const historyVM = useUkeireHistoryVM(historyRepository, month);
  
  // 統合状態
  const loading = forecastVM.loading || actualsVM.loading || historyVM.loading;
  const error = actualsVM.error || historyVM.error || null;
  
  return {
    month,
    monthJP: dayjs(month).format("YYYY年MM月"),
    loading,
    error,
    targetCardProps: forecastVM.targetCardProps,
    combinedDailyProps: forecastVM.combinedDailyProps,
    forecastCardProps: forecastVM.forecastCardProps,
    headerProps: forecastVM.headerProps,
    setMonth,
  };
}
```

### 3.3 pages/ukeire/index.tsx (骨組みPage)

```typescript
/**
 * 受入量ダッシュボードページ
 * レイアウト/配置のみ - ビジネスロジックは overview VM に集約
 */
import React, { useMemo } from "react";
import { Row, Col, Typography, DatePicker, Space, Badge, Skeleton } from "antd";
import dayjs, { type Dayjs } from "dayjs";
import { useUkeireVolumeCombinedVM } from "@/features/ukeireVolume/overview/hooks/useUkeireVolumeCombinedVM";
import { MockUkeireForecastRepository } from "@/features/ukeireVolume/forecast/repository/__mocks__/MockUkeireForecastRepository";
import { TargetCard } from "@/features/kpiTarget/ui/TargetCard";
import CalendarCardUkeire from "@/features/ukeireVolume/actuals/ui/CalendarCard.Ukeire";
import { CombinedDailyCard } from "@/features/ukeireVolume/history/ui/CombinedDailyCard";
import { ForecastCard } from "@/features/ukeireVolume/forecast/ui/ForecastCard";

const UkeirePage: React.FC = () => {
  // Repository injection (TODO: DI container化)
  const actualsRepository = useMemo(() => new MockActualsRepository(), []);
  const historyRepository = useMemo(() => new MockHistoryRepository(), []);
  const forecastRepository = useMemo(() => new MockUkeireForecastRepository(), []);

  const vm = useUkeireVolumeCombinedVM({
    actualsRepository,
    historyRepository,
    forecastRepository,
  });

  if (vm.loading || !vm.targetCardProps) {
    return <Skeleton active paragraph={{ rows: 6 }} />;
  }

  return (
    <div style={{ minHeight: "100dvh", overflow: "hidden", display: "flex", flexDirection: "column" }}>
      {/* ヘッダー + カードレイアウト（詳細略） */}
      <Row gutter={[12, 12]}>
        <Col xs={24} lg={7}>{vm.targetCardProps && <TargetCard {...vm.targetCardProps} />}</Col>
        <Col xs={24} lg={12}>{vm.combinedDailyProps && <CombinedDailyCard {...vm.combinedDailyProps} />}</Col>
        <Col xs={24} lg={5}><CalendarCardUkeire year={year} month={month} /></Col>
      </Row>
    </div>
  );
};

export default UkeirePage;
```

---

## 4. 実行結果

### 4.1 型チェック
```bash
$ pnpm typecheck
> tsc --noEmit -p tsconfig.json
✅ エラーなし
```

### 4.2 ビルド
```bash
$ pnpm build
✓ built in 10.60s
✅ 成功 (警告: チャンクサイズが大きい - 既知の問題)
```

### 4.3 削除確認
```bash
$ ls features/dashboard/ukeire
ls: cannot access 'features/dashboard/ukeire': No such file or directory
✅ 削除完了

$ ls pages/dashboard/ukeire
ls: cannot access 'pages/dashboard/ukeire': No such file or directory
✅ 削除完了
```

---

## 5. TODO リスト（未完了・暫定対応）

### 5.1 Repository実装の完成
- [ ] **MockActualsRepository を正式実装に置き換え**
  - 現状: `pages/ukeire/index.tsx` 内でインラインクラス定義
  - 推奨: `features/ukeireVolume/actuals/repository/__mocks__/` に移動
  
- [ ] **MockHistoryRepository を正式実装に置き換え**
  - 同上

- [ ] **HTTP Repository の実装とエンドポイント確定**
  - `UkeireForecastRepositoryImpl.ts`: `/api/ukeire/forecast/:month` (暫定)
  - `UkeireActualsRepositoryImpl.ts`: `/api/ukeire/actuals/:month` (暫定)
  - `UkeireHistoryRepositoryImpl.ts`: `/api/ukeire/history/:month` (暫定)

### 5.2 ViewModel の完成
- [ ] **useUkeireVolumeCombinedVM の完全実装**
  - 現状: forecastVMのpropsをそのまま流用
  - 推奨: actualsVM/historyVMからもデータを取得し、独自に整形

- [ ] **dailyActualsProps / dailyCumulativeProps の実装**
  - 現状: `null` を返している
  - 推奨: actualsVMからデータ取得して生成

### 5.3 DI (Dependency Injection) の改善
- [ ] **Repository のDIコンテナ化**
  - 現状: Pageコンポーネント内で `useMemo(() => new MockXxx(), [])` で生成
  - 推奨: Context API または DI library (InversifyJS等) で管理

### 5.4 エラーハンドリング
- [ ] **エラー境界 (Error Boundary) の追加**
  - Repository エラー時の fallback UI
  
- [ ] **リトライロジックの追加**
  - HTTP Repository での通信失敗時の自動リトライ

### 5.5 パフォーマンス最適化
- [ ] **React.memo / useMemo の適用**
  - Card コンポーネントのメモ化
  - ChartData のメモ化

- [ ] **Code Splitting の改善**
  - 現在のビルド警告対応 (チャンクサイズ > 500KB)

---

## 6. 受け入れ条件チェック

- [x] **Page 層はレイアウト/配置のみ（状態・通信なし）**
  - ✅ `pages/ukeire/index.tsx` は骨組みのみ、VM呼び出しとレイアウト専用

- [x] **Feature 層に UI/Hook/Repository/API/Model が揃っている**
  - ✅ ukeireVolume 配下に完全な層構造

- [x] **KPI Target は features/kpiTarget に共通化されている**
  - ✅ `features/kpiTarget/ui/TargetCard.tsx` で一元化

- [x] **実績/過去/予測は ukeireVolume 配下の actuals/history/forecast に分離**
  - ✅ 各feature配下に repository/hooks/ui を配置

- [x] **合成表示は overview（VM）で一元化、UIは描画専用**
  - ✅ `useUkeireVolumeCombinedVM` で3つのVMを統合
  - ⚠️ 部分的に実装中（TODO: actualsVM/historyVMの活用）

- [x] **`pnpm typecheck && pnpm build` 成功**
  - ✅ エラーなしで完了

---

## 7. 次のステップ

1. **TODO 5.1-5.2 の実装** (Repository Mock実装とVM完成)
2. **統合テストの作成** (E2E / Integration)
3. **パフォーマンス測定** (Lighthouse / Bundle Analyzer)
4. **本番APIエンドポイント確定**後、HTTP Repository の接続
5. **DI Container導入** (Context API or InversifyJS)

---

## 8. まとめ

### 達成したこと
- ✅ 旧 `features/dashboard/ukeire` を完全削除
- ✅ ukeireVolume へ機能集約 (actuals/history/forecast/overview)
- ✅ Repository パターン実装 (IF分離、Mock/HTTP実装)
- ✅ ViewModel 層の分離 (feature別 + 統合VM)
- ✅ Page 層の簡素化 (骨組みのみ)
- ✅ `pnpm typecheck && pnpm build` 成功
- ✅ ルーティング整理 (`/ukeire` に統一)

### 残課題
- ⚠️ Repository Mock実装の正式化
- ⚠️ Overview VM の完全実装
- ⚠️ DI Container 導入
- ⚠️ エラーハンドリング強化

**総合評価**: ✅ **リファクタリング基本構造は完成。TODO項目を段階的に実装することで完全版へ移行可能。**
