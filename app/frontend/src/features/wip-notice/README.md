# WipNotice - 開発中機能警告バナー

## 概要

開発中（Work In Progress）の機能をユーザーに知らせる汎用警告バナーコンポーネントです。
どのページや機能からも利用可能な共通コンポーネントとして設計されています。

## 使用方法

### 基本的な使い方

```tsx
import { WipNotice } from "@/features/wip-notice";

// 警告を表示
<WipNotice show={true} />

// カスタムメッセージ
<WipNotice
  show={true}
  message="カスタムメッセージ"
  description="詳細な説明文をここに記載します。"
/>
```

### 受入ダッシュボードでの使用例

```tsx
import { ForecastCard } from "@/features/dashboard/ukeire";

<ForecastCard
  {...forecastCardProps}
  showWipNotice={true} // ForecastCard内でWipNoticeを表示
/>;
```

### 直接使用する場合

```tsx
import { WipNotice } from "@/features/wip-notice";

const MyComponent = () => {
  const [showWip, setShowWip] = useState(true);

  return (
    <div>
      <WipNotice
        show={showWip}
        message="開発中の機能です"
        description="搬入量予測（P50 / P10–P90）は現在開発中であり、表示されているデータはダミーデータです。"
      />
      {/* 他のコンテンツ */}
    </div>
  );
};
```

## Props

| Prop          | Type                                          | Default                           | Description              |
| ------------- | --------------------------------------------- | --------------------------------- | ------------------------ |
| `show`        | `boolean`                                     | `false`                           | 警告を表示するかどうか   |
| `message`     | `string`                                      | `"開発中の機能です"`              | 警告のタイトルメッセージ |
| `description` | `string`                                      | `"この機能は現在開発中であり..."` | 詳細説明文               |
| `type`        | `"info" \| "success" \| "warning" \| "error"` | `"warning"`                       | Alertのタイプ            |
| `closable`    | `boolean`                                     | `false`                           | 閉じるボタンの表示有無   |

## 特徴

- ✨ 汎用的で再利用可能
- 🎯 シンプルなAPI
- 🔧 カスタマイズ可能
- 📦 features層に配置され、どこからでもimport可能
- 🎨 Ant DesignのAlertコンポーネントベース

## ディレクトリ構造

```
features/
  wip-notice/
    index.ts        # エクスポート
    README.md       # このファイル
    ui/
      WipNotice.tsx # コンポーネント本体
```
