# レスポンシブ実装ガイド

目的: リロード不要・即時追従し、保守性の高いレスポンシブ基盤を統一する。

## 基本ルール

- レイアウトのみ: CSS media queries を使用（`src/shared/constants/breakpoints.ts` を参照）。
- ウィンドウ幅ベース: `useWindowSize()` を使用。
- コンポーネント幅ベース: `useContainerSize()`（ResizeObserver ベース）を使用。
- AntD の `Grid.useBreakpoint()` は補助的に利用可能。閾値は breakpoints.ts に合わせる。

## 標準フック

- `useWindowSize()`: `{ width, height, isMobile, isTablet, isDesktop }`
- `useContainerSize<T extends HTMLElement>()`: `{ ref, size: { width, height } }`
- `useDeviceType()`: 互換のため残置。内部では `useWindowSize` を使用。

## マイグレーション

- 旧: `useDeviceType`, `matchMedia` → 新: `useWindowSize`, CSS media queries。
- DOM の差し替えは最小限に。スタイルは CSS へ移行。
- リサイズ即時追従が必要な分岐には `useWindowSize().width` を依存に含める。

## 例

- ページのレイアウト切替: `const { isMobile } = useWindowSize();`
- コンポーネント内で自身の幅で切替: `const { ref, size } = useContainerSize<HTMLDivElement>();`

## テスト

- 単体: `useWindowSize` をモックして分岐レンダリングを検証。
- E2E: Cypress で `cy.viewport()` を使いリサイズシナリオ。
