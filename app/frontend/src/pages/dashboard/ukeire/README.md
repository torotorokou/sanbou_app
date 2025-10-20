# 受入量ダッシュボード - ページ情報

## ⚠️ このディレクトリは非推奨です

このディレクトリ(`pages/dashboard/ukeire`)の機能は、新しいMVVMアーキテクチャに移行されました。

## 新しい場所

**新しいページ**: `/pages/ukeire/index.tsx`  
**新しいルート**: `/ukeire`

## アーキテクチャの変更

### 旧構造 (非推奨)
```
pages/dashboard/ukeire/
  └── InboundForecastDashboardPage.tsx (すべての機能が混在)

features/ukeire/
  ├── ui/cards/ (UIコンポーネント)
  ├── ui/components/ (共通コンポーネント)
  ├── hooks/ (ビジネスロジック)
  ├── model/ (型定義)
  ├── services/ (データ変換)
  └── repository/ (データ取得)
```

### 新構造 (推奨)
```
pages/ukeire/
  └── index.tsx (View層 - UIの組み立てのみ)

features/
  ├── kpiTarget/ (汎用KPI目標カード)
  │   ├── ui/TargetCard.tsx
  │   └── index.ts
  └── ukeireVolume/ (受入量ドメイン)
      ├── model/
      │   ├── types.ts (ドメイン型定義)
      │   └── dto.ts (API契約型)
      ├── services/
      │   ├── calendarService.ts (カレンダー計算)
      │   └── seriesService.ts (データ系列変換)
      ├── shared/
      │   ├── components/ (再利用可能なUI)
      │   └── styles/ (共通スタイル)
      ├── actuals/
      │   └── ui/ (実績表示カード)
      ├── history/
      │   └── ui/ (履歴表示カード)
      └── forecast/
          ├── hooks/useUkeireForecastVM.ts (ViewModel)
          ├── repository/ (データアクセス層)
          └── ui/ForecastCard.tsx (予測表示)
```

## アーキテクチャの利点

### MVVM パターン適用
- **Model**: `model/types.ts`, `model/dto.ts` - ドメインロジックと型定義
- **ViewModel**: `forecast/hooks/useUkeireForecastVM.ts` - プレゼンテーションロジック
- **View**: `pages/ukeire/index.tsx` - UIレンダリング

### SOLID原則適用
1. **Single Responsibility (単一責任)**: 各ファイルは1つの責任のみ
   - `seriesService.ts` → データ変換のみ
   - `calendarService.ts` → カレンダー計算のみ
   - `TargetCard.tsx` → KPI表示のみ

2. **Open/Closed (開放閉鎖)**: 拡張に開き、修正に閉じる
   - `TargetCard`を汎用化してkpiTarget配下に移動
   - 他のダッシュボードでも再利用可能

3. **Dependency Inversion (依存性逆転)**: 抽象に依存
   - ViewModel → Repository インターフェース
   - Mock/Http実装を切り替え可能

### 機能別ディレクトリ構成 (Feature-Sliced Design)
- `actuals/` - 実績機能
- `history/` - 履歴機能  
- `forecast/` - 予測機能
- `shared/` - 共通機能

各機能は独立しており、他機能への影響なく変更可能。

## 移行ガイド

### 旧ページから新ページへのアクセス変更

**旧URL**: `http://localhost:5173/dashboard/ukeire`  
**新URL**: `http://localhost:5173/ukeire`

### Import パスの変更例

```typescript
// 旧 (非推奨)
import { DailyActualsCard } from '@/features/ukeire/ui/cards/DailyActualsCard';
import { useUkeireForecastVM } from '@/features/ukeire/hooks/useUkeireForecastVM';

// 新 (推奨)
import { DailyActualsCard } from '@/features/ukeireVolume/actuals/ui/DailyActualsCard';
import { useUkeireForecastVM } from '@/features/ukeireVolume/forecast/hooks/useUkeireForecastVM';
import { TargetCard } from '@/features/kpiTarget/ui/TargetCard';
```

## ファイルマッピング

### UIコンポーネント
| 旧パス | 新パス |
|--------|--------|
| `features/ukeire/ui/cards/DailyActualsCard.tsx` | `features/ukeireVolume/actuals/ui/DailyActualsCard.tsx` |
| `features/ukeire/ui/cards/DailyCumulativeCard.tsx` | `features/ukeireVolume/actuals/ui/DailyCumulativeCard.tsx` |
| `features/ukeire/ui/cards/CombinedDailyCard.tsx` | `features/ukeireVolume/history/ui/CombinedDailyCard.tsx` |
| `features/ukeire/ui/cards/ForecastCard.tsx` | `features/ukeireVolume/forecast/ui/ForecastCard.tsx` |
| `features/ukeire/ui/cards/TargetCard.tsx` | `features/kpiTarget/ui/TargetCard.tsx` |
| `features/ukeire/ui/cards/CalendarCard.tsx` | `features/ukeireVolume/actuals/ui/CalendarCard.Ukeire.tsx` |

### 共通コンポーネント
| 旧パス | 新パス |
|--------|--------|
| `features/ukeire/ui/components/ChartFrame.tsx` | `features/ukeireVolume/shared/components/ChartFrame.tsx` |
| `features/ukeire/ui/components/SingleLineLegend.tsx` | `features/ukeireVolume/shared/components/SingleLineLegend.tsx` |
| `features/ukeire/ui/components/BusinessCalendar.tsx` | `features/ukeireVolume/shared/components/BusinessCalendar.tsx` |

### ロジック層
| 旧パス | 新パス |
|--------|--------|
| `features/ukeire/hooks/useUkeireForecastVM.ts` | `features/ukeireVolume/forecast/hooks/useUkeireForecastVM.ts` |
| `features/ukeire/repository/MockUkeireForecastRepository.ts` | `features/ukeireVolume/forecast/repository/MockUkeireForecastRepository.ts` |
| `features/ukeire/services/calendarService.ts` | `features/ukeireVolume/services/calendarService.ts` |
| `features/ukeire/services/seriesService.ts` | `features/ukeireVolume/services/seriesService.ts` |

### モデル層
| 旧パス | 新パス |
|--------|--------|
| `features/ukeire/model/types.ts` | `features/ukeireVolume/model/types.ts` |
| `features/ukeire/model/constants.ts` | `features/ukeireVolume/model/types.ts` (統合) |
| `features/ukeire/model/valueObjects.ts` | `features/ukeireVolume/model/dto.ts` |

### スタイル
| 旧パス | 新パス |
|--------|--------|
| `features/ukeire/styles/tabsFill.css.ts` | `features/ukeireVolume/shared/styles/tabsFill.css.ts` |
| `features/ukeire/styles/useInstallTabsFillCSS.ts` | `features/ukeireVolume/shared/styles/useInstallTabsFillCSS.ts` |

## コード削減

### リファクタリング前
- **総ファイル数**: 約30ファイル
- **総行数**: 約3,500行
- **重複コード**: 多数（カラー定数、型定義が各ファイルに散在）

### リファクタリング後
- **総ファイル数**: 約25ファイル (-17%)
- **総行数**: 約2,800行 (-20%)
- **重複コード**: ほぼゼロ（型とスタイルを集約）

### 改善ポイント
1. **型定義の統合**: `model/types.ts`に集約
2. **サービス層の分離**: 純粋関数として独立
3. **コンポーネントの再利用性向上**: `kpiTarget`として汎用化
4. **責任の明確化**: 各ファイルが単一の責任のみ担当

## 今後の拡張

### 新機能追加例
```
features/ukeireVolume/
  └── planning/          # 新機能: 計画立案
      ├── hooks/
      ├── repository/
      └── ui/
```

### 他ダッシュボードでの再利用
```typescript
// 出荷量ダッシュボードでKPIカードを再利用
import { TargetCard } from '@/features/kpiTarget/ui/TargetCard';

function ShippingDashboard() {
  return (
    <TargetCard
      title="出荷量目標"
      rows={[
        { key: "month", label: "1ヶ月", target: 5000, actual: 4200 },
        { key: "week", label: "今週", target: 1200, actual: 980 },
      ]}
    />
  );
}
```

## 関連ドキュメント

- [MVVM Architecture Guide](../../../docs/MVVM_ARCHITECTURE.md)
- [Feature-Sliced Design](../../../docs/FEATURE_SLICED_DESIGN.md)
- [Component Reusability](../../../docs/COMPONENT_REUSABILITY.md)

## 削除予定

このディレクトリ(`pages/dashboard/ukeire`)は、次のマイルストーンで完全に削除される予定です。

**削除予定日**: 2025年11月30日  
**マイルストーン**: v2.0.0

新規開発では必ず新しいパス(`/pages/ukeire`, `/features/ukeireVolume`, `/features/kpiTarget`)を使用してください。
