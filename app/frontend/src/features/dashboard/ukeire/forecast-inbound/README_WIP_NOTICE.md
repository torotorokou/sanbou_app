# WipNotice - 未完成機能警告バナー

## 概要
搬入量予測（P50 / P10-P90）が未完成であることをユーザーに知らせる警告バナーコンポーネントです。

## 使用方法

### 基本的な使い方
ForecastCardコンポーネントに`showWipNotice`プロパティを追加することで、警告バナーを表示できます。

```tsx
import { ForecastCard } from "@/features/dashboard/ukeire";

// 警告を表示する場合
<ForecastCard 
  {...forecastCardProps} 
  showWipNotice={true}  // <- これを追加
/>

// 警告を表示しない場合（デフォルト）
<ForecastCard 
  {...forecastCardProps} 
  showWipNotice={false}  // または省略
/>
```

### ページ側での実装例
InboundForecastDashboardPage.tsx で使用する場合：

```tsx
// 定数で管理する場合
const SHOW_FORECAST_WIP_NOTICE = true;  // 開発中はtrue、完成したらfalse

return (
  <div>
    {/* 予測カード */}
    {vm.forecastCardProps && (
      <ForecastCard 
        {...vm.forecastCardProps} 
        isGeMd={true}
        showWipNotice={SHOW_FORECAST_WIP_NOTICE}  // <- 追加
      />
    )}
  </div>
);
```

## カスタマイズ
WipNoticeコンポーネントを直接使用してメッセージをカスタマイズすることも可能です：

```tsx
import { WipNotice } from "@/features/dashboard/ukeire";

<WipNotice 
  show={true}
  message="カスタムメッセージ"
  description="カスタム説明文"
/>
```

## 注意事項
- デフォルトでは警告は非表示（`showWipNotice={false}`）です
- 他のコンポーネントには影響を与えません
- ForecastCardコンポーネント内でのみ表示されます
