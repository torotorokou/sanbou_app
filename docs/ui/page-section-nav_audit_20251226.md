# ページ内セクションナビゲーション対応監査レポート

**作成日**: 2025-12-26  
**対象**: 将軍マニュアルページのモバイルレスポンシブ対応

## 概要

将軍マニュアルページ（`/manuals/shogun`）にモバイル対応のページ内ナビゲーションを実装しました。PC/タブレットでは既存のサイドバー表示を維持し、モバイルでは目次ボタン→BottomSheet方式に切り替えることで、すべてのデバイスでページ内セクションへの移動が可能になりました。

## 実装内容

### 1. アーキテクチャ（FSD + MVVM + Repository）

以下のディレクトリ構成で実装しました：

```
features/manual/
├── domain/
│   └── types/
│       └── sectionNav.types.ts          # Section定義（型、ValueObject）
├── model/
│   └── useSectionNavViewModel.ts        # ViewModel（状態管理・操作）
└── ui/
    └── components/
        ├── BottomSheet.tsx              # BottomSheet UI
        ├── BottomSheet.module.css
        ├── SectionList.tsx              # セクション項目リスト
        └── SectionList.module.css
```

### 2. 実装詳細

#### 2.1 Section定義（domain/types/sectionNav.types.ts）

```typescript
export type SectionNavKind = 'scroll' | 'route';

export interface SectionNavItem {
  id: string;
  label: string;
  kind: SectionNavKind;      // scroll: ページ内スクロール, route: ページ遷移
  target: string;            // scroll: "#vendor", route: "/masters/vendor"
  icon?: ReactNode;
  count?: number;
}
```

#### 2.2 ViewModel（model/useSectionNavViewModel.ts）

- `isOpen` state管理
- `open()`/`close()` 操作
- `onSelect(item)`: セクション選択時の処理
  - `kind="scroll"`: `scrollIntoView({ behavior: 'smooth' })`
  - `kind="route"`: `navigate(target)`
  - 移動後に自動的に`close()`

#### 2.3 UI Components

##### BottomSheet

- Portal を使用して body 直下に描画
- Backdrop クリック/ESC キーで閉じる
- Body scroll lock（モーダル開閉時）
- 画面下部から60-70%の高さでスライドイン
- アニメーション（fadeIn/slideUp）

##### SectionList

- セクション項目をリスト表示
- アイコン・バッジカウント表示
- ホバー/アクティブ時のスタイル
- aria-label によるアクセシビリティ対応

### 3. ページへの適用（pages/manual/shogun/index.tsx）

#### PC/タブレット（≥768px）
- 既存のサイドバー（`Anchor`）表示を維持
- セクション項目は共通定義（`sectionNavItems`）から生成

#### モバイル（≤767px）
- サイドバーは非表示
- 右下に目次FABボタンを表示
- BottomSheet で目次を表示
- 項目タップでスクロール→自動で閉じる

### 4. レスポンシブ対応

- `useResponsive()` フック使用
  - `isMobile: ≤767px`
  - `isTablet: 768-1280px`
  - `isDesktop: ≥1281px`
- `showSider = !flags.isMobile` でサイドバー表示制御

## タイトル修正

### 要件0・1対応

- タイトル「環境将軍マニュアル」が2行にならないよう `white-space: nowrap` を追加
- モバイル時はフォントサイズを16pxに縮小
- タイトルのみ表示、説明文は表示しない（元々存在せず）

## 既存機能の保護

以下の既存機能は変更なし：

- ✅ 検索機能（ヘッダー/コンテンツ内）
- ✅ セクションブロック表示
- ✅ マニュアルモーダル表示
- ✅ フィルタリング機能
- ✅ PC/タブレットのサイドバー

## アクセシビリティ

- ✅ FABボタンに `aria-label="目次を開く"`
- ✅ BottomSheet に `role="dialog"` と `aria-modal="true"`
- ✅ ESCキーでBottomSheetを閉じる
- ✅ Body scroll lock（モーダル時）

## デザイン

- ✅ 既存デザインを破壊しない
- ✅ FABボタンは右下固定（z-index: 999）
- ✅ BottomSheetは画面下から70%の高さでスライドイン
- ✅ 背面クリックで閉じる
- ✅ スクロール可能

## パフォーマンス

- `useMemo` で `sectionNavItems` を計算（filtered変更時のみ再計算）
- `useCallback` でViewModel内の関数をメモ化

## テスト項目（手動確認）

### モバイル幅（≤767px）
- [ ] サイドバーが非表示
- [ ] 目次FABボタンが右下に表示
- [ ] FABボタンクリックでBottomSheet表示
- [ ] BottomSheet内のセクション項目をタップ
- [ ] セクションへスクロール移動
- [ ] BottomSheetが自動で閉じる
- [ ] 背面クリックでBottomSheetが閉じる
- [ ] ESCキーでBottomSheetが閉じる
- [ ] タイトルが1行に収まる

### タブレット/PC幅（≥768px）
- [ ] サイドバーが表示される
- [ ] 既存のAnchorナビゲーションが動作
- [ ] 目次FABボタンが非表示
- [ ] 既存機能（検索/フィルタ/モーダル）が正常動作

## 変更ファイル一覧

### 新規作成
- `features/manual/domain/types/sectionNav.types.ts`
- `features/manual/model/useSectionNavViewModel.ts`
- `features/manual/ui/components/BottomSheet.tsx`
- `features/manual/ui/components/BottomSheet.module.css`
- `features/manual/ui/components/SectionList.tsx`
- `features/manual/ui/components/SectionList.module.css`

### 変更
- `features/manual/index.ts` - 新規コンポーネントのexport追加
- `pages/manual/shogun/index.tsx` - モバイル対応の適用
- `pages/manual/shogun/ShogunList.module.css` - タイトル修正、FABボタンスタイル追加

## 将来の拡張可能性

### 他のページへの適用

現在、将軍マニュアルページのみに実装していますが、以下のページにも同様の実装が可能です：

- マスター作成ページ
- 契約書ページ
- 見積書ページ
- マニフェストページ

各ページで以下の手順で適用できます：

1. セクション項目定義（`SectionNavItem[]`）を作成
2. `useSectionNavViewModel` を使用
3. PC: 既存サイドバー、モバイル: FAB + BottomSheet

### 拡張機能アイデア

- セクションのネスト（親子関係）対応
- セクション進捗表示（訪問済み/未訪問）
- セクション検索機能
- お気に入りセクション
- セクション履歴

## まとめ

将軍マニュアルページにおいて、FSD + MVVM + Repositoryアーキテクチャに準拠した形で、モバイル対応のページ内ナビゲーション機能を実装しました。既存機能を破壊せず、PC/タブレットでは従来通りのサイドバー、モバイルでは目次ボタン→BottomSheet方式を採用することで、すべてのデバイスで快適なナビゲーションを実現しています。
