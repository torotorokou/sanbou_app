# 🚀 モード対応レポートシステム 実装ガイド

## 📋 概要

このドキュメントは、「自動帳簿生成」と「インタラクティブ帳簿生成」に対応したレポートシステムの実装について説明します。SOLID原則とMVC構造に基づいて設計されており、既存システムとの互換性を保ちながら新機能を提供します。

## 🎯 要件と実装概要

### ✅ 実装済み要件

1. **モード判定システム** (`pages/types/reportMode.ts`)
   - 帳簿ごとに「自動」か「インタラクティブ」かを型安全に判定
   - 設定変更により新しいモードを簡単に追加可能

2. **API エンドポイント分岐** (`services/reportModeService.ts`)
   - モードに応じた異なるAPIエンドポイントの自動選択
   - 処理フローの完全分離

3. **共通化設計**
   - CSVアップロード、ファイルダウンロード、PDFプレビューは共通
   - バックエンドAPI通信・モーダル表示のみモード別に分岐

4. **SOLID原則準拠**
   - 単一責任原則：各クラスは特定の責任のみを持つ
   - 開放閉鎖原則：新機能追加時に既存コードを変更しない
   - インターフェース分離：必要最小限のインターフェース

## 🏗️ アーキテクチャ構成

```
src/
├── pages/types/                    # 型定義（新規追加）
│   ├── reportMode.ts              # モード判定システム
│   ├── interactiveMode.ts         # インタラクティブ専用型
│   └── index.ts                   # エクスポート管理
├── services/                      # サービス層（新規追加）
│   └── reportModeService.ts       # モード分岐処理
├── hooks/report/                  # 拡張フック
│   └── useReportModeManager.ts    # モード対応管理フック
├── components/Report/             # UI コンポーネント
│   ├── ReportModeBase.tsx         # モード対応ベース
│   └── interactive/               # インタラクティブ専用UI
│       └── InteractiveReportModal.tsx
└── pages/report/                  # ページコンポーネント
    ├── ReportModeFactory.tsx      # モード対応工場ページ
    └── ReportModeDemo.tsx          # デモンストレーション
```

## 🔧 主要コンポーネント説明

### 1. モード判定システム (`pages/types/reportMode.ts`)

```typescript
// 帳簿ごとのモード設定
export const REPORT_MODE_CONFIG = {
    factory_report: { mode: 'auto' },           // 自動モード
    balance_sheet: { mode: 'interactive' },     // インタラクティブ
    block_unit_price: { mode: 'interactive' },  // インタラクティブ
    // 新しい帳簿を追加する場合はここに設定を追加
} as const;

// モード情報を取得
const modeInfo = getReportModeInfo('balance_sheet');
console.log(modeInfo.isInteractive); // true
```

### 2. サービス層 (`services/reportModeService.ts`)

```typescript
// Factory Pattern でプロセッサーを生成
const processor = ReportProcessorFactory.createProcessor(reportKey);

// モードに応じた処理を自動実行
const result = await ReportModeService.generateReport(
    csvFiles, 
    reportKey, 
    callbacks
);
```

### 3. モード対応フック (`hooks/report/useReportModeManager.ts`)

```typescript
const reportManager = useReportModeManager({
    initialReportKey: 'balance_sheet',
    onModeChange: (mode) => console.log('Mode:', mode),
    onInteractiveStepChange: (step) => console.log('Step:', step),
});

// 統合されたレポート生成
await reportManager.generateReport();

// インタラクティブ処理の継続
await reportManager.continueInteractiveProcess(userInput);
```

## 🎮 使用方法

### 基本的な使用例

```typescript
import { ReportModeFactory } from '@/pages/report/ReportModeFactory';

// モード対応ページの使用
function App() {
    return <ReportModeFactory />;
}
```

### カスタムページの作成

```typescript
import { useReportModeManager } from '@/hooks/report/useReportModeManager';
import { ReportModeBase } from '@/components/Report/ReportModeBase';

function CustomReportPage() {
    const reportManager = useReportModeManager({
        initialReportKey: 'custom_report',
    });

    return (
        <ReportModeBase
            // props...
            onContinueInteractive={reportManager.continueInteractiveProcess}
            onResetInteractive={reportManager.resetInteractiveState}
            interactiveState={reportManager.interactiveState}
        />
    );
}
```

## 🔄 新しいモードの追加方法

### 1. モード設定の追加

```typescript
// pages/types/reportMode.ts
export const REPORT_MODE_CONFIG = {
    // 既存設定...
    new_report: { mode: 'new_mode' }, // 新モード追加
};

export const API_ENDPOINTS = {
    auto: '/ledger_api/report/manage',
    interactive: '/ledger_api/report/interactive',
    new_mode: '/ledger_api/report/new_mode', // 新エンドポイント
};
```

### 2. プロセッサーの実装

```typescript
// services/reportModeService.ts
class NewModeProcessor implements IReportProcessor {
    async processReport(csvFiles, reportKey, callbacks) {
        // 新モードの処理実装
    }
}

// ファクトリーに登録
ReportProcessorFactory.registerProcessor('new_mode', () => new NewModeProcessor());
```

### 3. UI コンポーネントの追加（必要に応じて）

```typescript
// components/Report/newmode/NewModeModal.tsx
const NewModeModal: React.FC = (props) => {
    // 新モード専用UI実装
};
```

## 🧪 デモとテスト

### デモページ

`/pages/report/ReportModeDemo.tsx` で全機能のデモンストレーションが可能です：

- 自動・インタラクティブモードの切り替え確認
- 各帳票タイプの動作確認
- モード判定システムの動作確認

### テスト実行方法

```bash
# TypeScript 型チェック
npm run type-check

# コンポーネントテスト
npm run test

# 統合テスト
npm run test:integration
```

## 📝 開発者向けメモ

### 設計パターン

1. **Factory Pattern**: プロセッサーの生成
2. **Strategy Pattern**: モード別処理の分岐
3. **Observer Pattern**: 状態変更の通知
4. **Facade Pattern**: 複雑な処理の簡潔なインターフェース

### パフォーマンス考慮事項

- 遅延ローディング：モード別コンポーネントは必要時のみロード
- メモ化：重い計算結果のキャッシュ
- 型安全性：実行時エラーの最小化

### 拡張可能性

- 新しいモードの追加は設定ファイルの変更のみで対応
- 既存コードへの影響なし
- バックワード互換性の保持

## 🚨 注意事項

1. **型安全性**: 新しい型を追加する際は `pages/types/index.ts` での適切なエクスポートが必要
2. **API互換性**: 新しいエンドポイントはバックエンドとの調整が必要
3. **テスト**: 新機能追加時は適切なテストの追加が必要

## 🔗 関連ファイル

- `src/pages/types/reportMode.ts` - モード判定システム
- `src/services/reportModeService.ts` - サービス層
- `src/hooks/report/useReportModeManager.ts` - 統合フック
- `src/components/Report/ReportModeBase.tsx` - UI統合
- `src/pages/report/ReportModeDemo.tsx` - デモページ

---

この実装により、既存のレポートシステムを拡張し、自動・インタラクティブ両方のモードに対応した柔軟で保守性の高いシステムが構築されました。
