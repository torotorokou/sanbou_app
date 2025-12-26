# § 1 現状棚卸し：Single Source of Truth 確立のための資産分析

## 1.1 重複・競合マップ（TSV形式）

```tsv
分類	現在のパス	役割	状態	統合方針	移動先	理由
constants	src/shared/constants/breakpoints.ts	ブレークポイント定義（ANT, BP, 述語）	✅ 主要	保持・強化	同じ	唯一の正として確立
hooks	src/shared/hooks/ui/useWindowSize.ts	window幅検知Hook	✅ 主要	保持	同じ	内部実装として維持
hooks	src/shared/hooks/ui/useResponsive.ts	公開レスポンシブHook	⚠️ 非推奨実装	上書き	同じ	useWindowSize依存の薄いラッパーに変更
hooks	src/shared/hooks/useBreakpoint.ts	useWindowSizeの薄いラッパー	⚠️ 重複	削除候補	-	useResponsiveに統合して削除
theme	src/shared/theme/responsive.css	レスポンシブCSS（カスタムメディア利用）	✅ 主要	保持・強化	同じ	カスタムメディア統合後の主軸
theme	src/styles/custom-media.css	カスタムメディア定義（自動生成）	⚠️ 分散	統合後削除	src/shared/theme/responsive.css	生成ロジックを変更して統合
theme	src/shared/theme/tokens.ts	カラートークン	✅ 主要	保持	同じ	変更不要
theme	src/shared/theme/cssVars.ts	CSS変数生成	✅ 主要	保持	同じ	変更不要
theme	src/shared/theme/colorMaps.ts	カラーマップ	✅ 主要	保持	同じ	変更不要
styles	src/shared/styles/base.css	グローバルCSS	✅ 主要	保持	同じ	変更不要
styles	src/styles/tabsTight.module.css	Tabs固有のモジュールCSS	🔵 機能特化	移動	src/shared/styles/tabsTight.module.css	共有CSSとして整理
plugin	src/plugins/vite-plugin-custom-media.ts	カスタムメディア自動生成	⚠️ 出力先変更	修正	同じ	出力先をresponsive.cssに変更
infrastructure	src/shared/infrastructure/**	HTTP/Job等	✅ 主要	保持	同じ	変更不要
ui	src/shared/ui/**	再利用UI	✅ 主要	保持	同じ	変更不要
utils	src/shared/utils/**	ユーティリティ	✅ 主要	保持	同じ	変更不要
types	src/shared/types/**	型定義	✅ 主要	保持	同じ	変更不要
```

## 1.2 ブレークポイント定義の不一致検出

### 現在の定義値の比較

| ソース               | xs  | sm  | md                 | lg   | xl        | xxl  |
| -------------------- | --- | --- | ------------------ | ---- | --------- | ---- |
| breakpoints.ts (ANT) | 480 | 576 | 768                | 992  | 1200      | 1600 |
| breakpoints.ts (BP)  | -   | -   | 767(max)           | -    | 1200(min) | -    |
| custom-media.css     | -   | -   | 767(max), 768(min) | -    | 1200(min) | -    |
| 目標値（新bp）       | 0   | 640 | 768                | 1024 | 1280      | -    |

**⚠️ 重大な不一致**：

- 現在の実装は `ANT.md=768, ANT.xl=1200` の2軸
- 提案の `bp` は `sm:640, md:768, lg:1024, xl:1280` の4軸
- **既存UIは ANT.md/xl に最適化されているため、完全置換は破壊的**

### 推奨方針：段階的移行

1. **フェーズ1（本PR）**: `bp` を ANT互換で導入（`bp.sm=576, bp.md=768, bp.lg=992, bp.xl=1200`）
2. **フェーズ2（別PR）**: 新しい値体系への移行検討（UI検証必要）

## 1.3 インポート依存グラフ

### styles/ への依存（11箇所）

```
main.tsx                                    → @shared/styles/base.css
shared/theme/responsive.css                 → @/styles/custom-media.css ⚠️
pages/home/PortalPage.css                   → @/styles/custom-media.css ⚠️
pages/dashboard/ManagementDashboard.css     → @/styles/custom-media.css ⚠️
pages/manual/shogun/ShogunList.module.css   → @/styles/custom-media.css ⚠️
features/.../CombinedDailyCard.tsx          → @/styles/tabsTight.module.css ⚠️
features/chat/.../QuestionPanel.tsx         → ../../styles/QuestionPanel.css
features/calendar/.../CalendarCore.tsx      → ../../styles/calendar.module.css
```

**⚠️ マーク**: 統合対象（custom-media.css 4箇所、tabsTight 1箇所）

### useWindowSize への依存（30箇所超）

主要な利用箇所：

- `app/layout/*`: Sidebar, MainLayout
- `pages/*`: PortalPage, ShogunList
- `shared/hooks/ui/*`: useResponsive, useSidebarResponsive
- `shared/ui/*`: VerticalActionButton, ResponsiveDebugInfo

**✅ 評価**: useWindowSize は内部実装として適切に機能中

### ANT/BP の直接参照（30箇所超）

主要なパターン：

- CSS内の固定値: `@media (max-width: 1024px)` など（1箇所のみ検出）
- TypeScript内: `ANT.md`, `ANT.xl`, `BP.mobileMax`, `BP.desktopMin` など
- Viteプラグイン: `ANT.md`, `ANT.xl` の読み取り

**✅ 評価**: 既にbreakpoints.tsを中心に統一されているが、直値が1箇所残存

## 1.4 インポート置換の影響件数（概算）

| 対象                            | 件数 | 置換内容                               | 優先度 |
| ------------------------------- | ---- | -------------------------------------- | ------ |
| `@/styles/custom-media.css`     | 4    | `@/shared/theme/responsive.css`        | 🔴 高  |
| `@/styles/tabsTight.module.css` | 1    | `@/shared/styles/tabsTight.module.css` | 🟡 中  |
| features内の相対styles import   | 2    | 要調査・個別判断                       | 🟢 低  |
| 固定値メディアクエリ            | 1    | `mq.up()` or カスタムメディア          | 🟡 中  |
| useBreakpoint                   | 少数 | useResponsive                          | 🟡 中  |

**合計影響ファイル数**: 約8-12ファイル（安全に置換可能）

## 1.5 統合後の目標構成

```
src/
  shared/
    constants/
      breakpoints.ts        ← 唯一の正（ANT互換bp + mq + match）
      index.ts
    hooks/
      ui/
        useResponsive.ts    ← 公開Hook（簡潔版）
        useWindowSize.ts    ← 内部実装（維持）
        useSidebarResponsive.ts
        useSidebarDefault.ts
        useContainerSize.ts
        useScrollTracker.ts
        index.ts
      useBreakpoint.ts      ← 🗑️ 削除候補（useResponsiveに統合）
      index.ts
    theme/
      tokens.ts
      cssVars.ts
      colorMaps.ts
      responsive.css        ← カスタムメディア統合後の主軸
      index.ts
    styles/
      base.css
      tabsTight.module.css  ← styles/から移動
      index.ts
    ui/
      ...（変更なし）
    infrastructure/
      ...（変更なし）
    utils/
      ...（変更なし）
    types/
      ...（変更なし）
    index.ts                ← バレル公開窓口

  styles/                   ← 🗑️ 廃止予定
    custom-media.css        ← responsive.cssに統合後削除
    tabsTight.module.css    ← shared/stylesへ移動

  plugins/
    vite-plugin-custom-media.ts  ← 出力先をresponsive.cssに変更
```

## 1.6 コミット分割案

### Commit 1: `chore(shared): add unified breakpoints with ANT compatibility`

- breakpoints.ts の上書き（ANT互換値で bp, mq, match を追加）
- useResponsive.ts の上書き（簡潔版）
- 既存機能に影響なし（互換性維持）

### Commit 2: `refactor(styles): consolidate custom-media into responsive.css`

- vite-plugin-custom-media.ts の出力先を responsive.css に変更
- responsive.css にカスタムメディア定義を統合
- @import の置換（4箇所）

### Commit 3: `refactor(styles): move tabsTight to shared/styles`

- git mv src/styles/tabsTight.module.css → src/shared/styles/
- import の置換（1箇所）

### Commit 4: `refactor(hooks): consolidate useBreakpoint into useResponsive`

- useBreakpoint.ts の削除
- useResponsive への置換（該当箇所のみ）

### Commit 5: `refactor(shared): enforce barrel exports for @/shared`

- shared/index.ts の充実化
- 深いimportの置換（必要に応じて）

### Commit 6: `cleanup: remove deprecated styles/ directory`

- src/styles/ の削除（custom-media.css含む）
- 最終動作確認

### Commit 7: `chore(eslint): add rules for shared deep imports`

- ESLintルール追加
- docs/fsd-linting-rules.md の更新

## 1.7 リスク分析

### 🔴 高リスク

- **ブレークポイント値の変更**: 新bp値（sm:640, lg:1024, xl:1280）は既存UIを破壊
  - **対策**: ANT互換値で導入し、新値への移行は別PRで慎重に

### 🟡 中リスク

- **カスタムメディアの統合**: @import先の変更で一時的にスタイル崩れの可能性
  - **対策**: ビルド後に各ページを目視確認

### 🟢 低リスク

- **Hook名の変更**: useBreakpoint → useResponsive は利用箇所が少ない
- **バレル化**: 段階的に進めるため影響範囲を制御可能

## 1.8 フォローアップTODO（別PR）

1. ⚠️ features内のstylesディレクトリの整理（QuestionPanel.css, calendar.module.css等）
2. ⚠️ 固定値メディアクエリの完全排除（SearchPage.module.css: 1024px）
3. ⚠️ 新bp値体系への移行検討（UI影響の全面検証必要）
4. ⚠️ ESLintルールの強化テスト

---

## 次のステップ

この分析に基づき、以下を実施します：

1. ✅ **合意確認**: 上記の統合方針とコミット分割案をレビュー
2. → **実装開始**: Commit 1から順次実施
3. → **テスト**: 各コミット後に `npm run typecheck` + `npm run build`
4. → **サマリ出力**: 最終的な変更サマリとフォローアップTODOを提示

**承認いただければ、Commit 1の実装を開始します。**
