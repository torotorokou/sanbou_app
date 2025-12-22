# レスポンシブデザイン実装ガイド

**作成日**: 2025-12-22  
**対象**: フロントエンド開発者（次回実装時の参照用）  
**目的**: レスポンシブ実装時に迷わずコピペできるパターン集

---

## 📌 このドキュメントの使い方

### いつ読むか

- 新規ページ/コンポーネントを作成する時
- 既存コンポーネントのレスポンシブ対応を追加する時
- レスポンシブ実装のコードレビュー時

### 読み方

1. **A. 3段階の考え方** - 全員必読（設計思想）
2. **B. 基本パターン** - 実装時にコピペ
3. **C. 禁止パターン** - レビュー前に確認
4. **D. FSD設計** - コンポーネント責務の置き場
5. **E. 実装テンプレ** - コピペ用コード集

---

## A. 3段階の考え方

### A-1. 運用定義（2025-12-22更新）

```
Mobile:  ≤ 767px    スマホ、極小ウィンドウ
Tablet:  768-1280px タブレット、小〜中型ノートPC（★1280含む）
Desktop: ≥ 1281px   フルHD以上のデスクトップ（★1280含まない）
```

### A-2. いつ isMobile/isTablet/isDesktop を使うか

#### 主要分岐（必須）

以下の場合は必ず3段階で分岐：

- **ページ全体の構造**（1列/2列/3列）
- **ナビゲーション**（Drawer/固定サイドバー閉じ/固定サイドバー開き）
- **モーダル/ダイアログの幅**
- **テーブルのカラム数**
- **フォームのレイアウト**

#### 詳細調整（任意）

以下の場合は詳細5段階（isXs/isSm/isMd/isLg/isXl）も使用可：

- **フォントサイズの微調整**
- **余白の段階的変更**
- **アイコンサイズ**

ただし、**基本は3段階で十分**。迷ったら3段階にする。

### A-3. なぜ1280px を Tablet に含めるのか

**理由1**: 1280x800は一般的なノートPC解像度  
**理由2**: サイドバーのデフォルト閉じ動作を1280pxまで適用  
**理由3**: Desktopは「十分に広い画面」のみを指す（フルHD 1920x1080以上を想定）

---

## B. 基本パターン（推奨）

### B-1. ページ構造の3段階分岐

#### パターン1: if/else チェーン

```typescript
import { useResponsive } from '@/shared';

const MyPage: React.FC = () => {
  const { flags } = useResponsive();
  
  // 3段階分岐
  if (flags.isMobile) {
    // Mobile (≤767px): 1列縦並び
    return <MobileLayout />;
  }
  
  if (flags.isTablet) {
    // Tablet (768-1280px): 2列レイアウト
    return <TabletLayout />;
  }
  
  // Desktop (≥1281px): 3列フルレイアウト
  return <DesktopLayout />;
};
```

#### パターン2: pickByDevice ヘルパー

```typescript
const MyComponent: React.FC = () => {
  const { flags } = useResponsive();
  
  // 値を3段階で決定
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile;      // ≤767
    if (flags.isTablet) return tablet;      // 768-1280
    return desktop;                         // ≥1281
  };
  
  const columns = pickByDevice(1, 2, 3);
  const gap = pickByDevice(8, 16, 24);
  const padding = pickByDevice('8px', '16px', '24px');
  
  return (
    <div style={{
      display: 'grid',
      gridTemplateColumns: `repeat(${columns}, 1fr)`,
      gap,
      padding,
    }}>
      {/* ... */}
    </div>
  );
};
```

### B-2. SidebarMode の使い方

**useSidebar は3段階運用で自動駆動**される：

```typescript
import { useSidebar } from '@/shared';

const MyLayout: React.FC = () => {
  const { state, actions } = useSidebar();
  
  // state.drawerMode は自動で決まる
  // - Mobile (≤767):        drawerMode=true, defaultCollapsed=true
  // - Tablet (768-1280):    drawerMode=false, defaultCollapsed=true
  // - Desktop (≥1281):      drawerMode=false, defaultCollapsed=false
  
  return (
    <Layout>
      {state.drawerMode ? (
        <Drawer
          open={state.isOpen}
          onClose={actions.close}
        >
          <SidebarContent />
        </Drawer>
      ) : (
        <Sider
          collapsed={state.isCollapsed}
          onCollapse={actions.toggle}
        >
          <SidebarContent />
        </Sider>
      )}
      <Content>{children}</Content>
    </Layout>
  );
};
```

### B-3. モーダル幅の決定

```typescript
const MyModal: React.FC<Props> = ({ visible, onClose }) => {
  const { flags } = useResponsive();
  
  // モーダル幅を3段階で決定
  const modalWidth = flags.isMobile ? '90%'      // ≤767
                   : flags.isTablet ? 640        // 768-1280
                   : 800;                        // ≥1281
  
  return (
    <Modal
      open={visible}
      onCancel={onClose}
      width={modalWidth}
    >
      {/* ... */}
    </Modal>
  );
};
```

### B-4. テーブル表示の切り替え

```typescript
const MyTable: React.FC = () => {
  const { flags } = useResponsive();
  
  // Mobile: カード表示、Tablet以上: テーブル表示
  if (flags.isMobile) {
    return <CardList data={data} />;
  }
  
  // Tablet/Desktop: テーブル表示（カラム数は同じでOK）
  return (
    <Table
      dataSource={data}
      columns={columns}
      scroll={{ x: flags.isTablet ? 800 : undefined }}
    />
  );
};
```

### B-5. フォーム配置

```typescript
const MyForm: React.FC = () => {
  const { flags } = useResponsive();
  
  // フォーム列数を3段階で決定
  const colSpan = flags.isMobile ? 24      // 1列（全幅）
                : flags.isTablet ? 12      // 2列（半幅）
                : 8;                       // 3列（1/3幅）
  
  return (
    <Form>
      <Row gutter={16}>
        <Col span={colSpan}>
          <Form.Item name="name" label="名前">
            <Input />
          </Form.Item>
        </Col>
        <Col span={colSpan}>
          <Form.Item name="email" label="メール">
            <Input />
          </Form.Item>
        </Col>
        {/* ... */}
      </Row>
    </Form>
  );
};
```

---

## C. 禁止パターン（アンチパターン）

### C-1. ❌ window.innerWidth 直参照

```typescript
// ❌ 禁止
const isMobile = window.innerWidth <= 767;
if (window.innerWidth < 1280) { ... }

// ✅ 正解
const { flags } = useResponsive();
if (flags.isMobile) { ... }
if (!flags.isDesktop) { ... }  // = Mobile or Tablet
```

**理由**:
- SSRで window が存在しない
- テストが困難
- 境界値変更時に複数ファイル修正が必要

### C-2. ❌ 数値ハードコード

```typescript
// ❌ 禁止
const tabletMax = 1279;
if (width < 1280) { ... }
const modalWidth = width < 768 ? 320 : 640;

// ✅ 正解
import { BP } from '@/shared';
if (width <= BP.tabletMax) { ... }
const modalWidth = flags.isMobile ? 320 : 640;
```

**理由**:
- 境界値変更時に修正箇所が散在
- typoリスク（1279 vs 1280 など）

### C-3. ❌ isLaptop を運用分岐に使用

```typescript
// ❌ 禁止（4段階になり混乱）
if (flags.isMobile) { ... }
else if (flags.isTablet) { ... }
else if (flags.isLaptop) { ... }  // ← これは禁止
else { ... }

// ✅ 正解（3段階統一）
if (flags.isMobile) { ... }
else if (flags.isTablet) { ... }  // 768-1280 を含む
else { ... }  // Desktop (≥1281)
```

**理由**:
- 4段階にすると Tablet/Laptop の境界（1024px）で混乱
- **isTablet が 768-1280 を含むため、isLaptop は不要**

### C-4. ❌ 独自の境界値定義

```typescript
// ❌ 禁止
const MOBILE_MAX = 799;  // 独自定義
const TABLET_MIN = 800;

// ✅ 正解
import { BP } from '@/shared';
// BP.mobileMax, BP.tabletMin, BP.tabletMax, BP.desktopMin を使用
```

---

## D. コンポーネント設計の置き場（FSD/MVVM）

### D-1. FSD層の責務

#### pages/

- **役割**: ページ全体の骨組みのみ
- **レスポンシブ**: 最小限の構造分岐（1列/2列/3列など）
- **例**:
  ```typescript
  // pages/report/ManagePage.tsx
  const ManagePage = () => {
    const { flags } = useResponsive();
    return flags.isMobile ? <MobileView /> : <DesktopView />;
  };
  ```

#### features/*/ui/

- **役割**: 表示コンポーネント（できるだけ状態レス）
- **レスポンシブ**: variant prop で受け取る（推奨）
- **例**:
  ```typescript
  // features/report/upload/ui/CsvUploadSection.tsx
  type Props = {
    variant?: 'mobile' | 'tablet' | 'desktop';
  };
  
  const CsvUploadSection: React.FC<Props> = ({ variant = 'desktop' }) => {
    const fontSize = variant === 'mobile' ? '14px' : '16px';
    // ...
  };
  ```

#### features/*/model/

- **役割**: 画面状態・ユースケース・レスポンシブロジック集約
- **レスポンシブ**: useResponsive() を呼び、計算結果をuiに渡す
- **例**:
  ```typescript
  // features/report/selector/model/useReportLayoutStyles.ts
  export const useReportLayoutStyles = () => {
    const { flags } = useResponsive();
    
    const padding = flags.isMobile ? 8
                  : flags.isTablet ? 16
                  : 24;
    
    return { padding, gap, ... };
  };
  ```

#### shared/hooks/ui/

- **役割**: レスポンシブ基盤（useResponsive, useSidebar）
- **レスポンシブ**: 唯一の真実の源
- **変更**: 慎重に（全体影響大）

### D-2. レスポンシブロジックの配置指針

| ロジック種類 | 推奨配置 | 理由 |
|------------|---------|------|
| 画面構造分岐（1列/2列/3列） | pages/ | ページ全体の骨組み |
| モーダル幅・余白・フォント | features/*/model/ | 再利用可能なロジック |
| variant受け取り | features/*/ui/ | テスト容易性 |
| レスポンシブ基盤 | shared/hooks/ui/ | 唯一の真実 |

---

## E. 実装テンプレ（コピペ用）

### E-1. useResponsive の基本

```typescript
import { useResponsive } from '@/shared';

const MyComponent: React.FC = () => {
  const { flags, tier, width } = useResponsive();
  
  // flags.isMobile   : boolean (≤767)
  // flags.isTablet   : boolean (768-1280) ★1280含む
  // flags.isDesktop  : boolean (≥1281)
  // tier             : 'mobile' | 'tablet' | 'desktop'
  // width            : number (画面幅、SSR時は768)
  
  // 使用例
  const layout = flags.isMobile ? 'stack' : 'grid';
  
  return <div>{/* ... */}</div>;
};
```

### E-2. pickByDevice ヘルパー（推奨パターン）

```typescript
const MyComponent: React.FC = () => {
  const { flags } = useResponsive();
  
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile;
    if (flags.isTablet) return tablet;
    return desktop;
  };
  
  // 使用例
  const columns = pickByDevice(1, 2, 3);
  const fontSize = pickByDevice(14, 15, 16);
  const padding = pickByDevice('8px 12px', '12px 16px', '16px 24px');
  
  return <div style={{ padding, fontSize }}>{/* ... */}</div>;
};
```

### E-3. ResponsiveVariant props パターン

#### コンポーネント定義

```typescript
// features/myfeature/ui/MyComponent.tsx
export type ResponsiveVariant = 'mobile' | 'tablet' | 'desktop';

type Props = {
  variant?: ResponsiveVariant;
  // ...
};

export const MyComponent: React.FC<Props> = ({ 
  variant = 'desktop',
  ...props 
}) => {
  const size = variant === 'mobile' ? 'small'
             : variant === 'tablet' ? 'middle'
             : 'large';
  
  return <Button size={size}>{/* ... */}</Button>;
};
```

#### 使用側

```typescript
// pages/MyPage.tsx
const MyPage: React.FC = () => {
  const { tier } = useResponsive();
  
  return <MyComponent variant={tier} />;
};
```

### E-4. CSS-in-JS レスポンシブスタイル

```typescript
const MyComponent: React.FC = () => {
  const { flags } = useResponsive();
  
  const styles = {
    container: {
      display: 'flex',
      flexDirection: flags.isMobile ? 'column' : 'row',
      gap: flags.isMobile ? 8 : flags.isTablet ? 16 : 24,
      padding: flags.isMobile ? '8px 12px' : '16px 24px',
    } as React.CSSProperties,
  };
  
  return <div style={styles.container}>{/* ... */}</div>;
};
```

### E-5. 境界値を使う場合（稀）

```typescript
import { BP } from '@/shared';

const MyComponent: React.FC = () => {
  const [containerWidth, setContainerWidth] = useState(0);
  
  useEffect(() => {
    // コンテナ幅を取得して判定（window.innerWidthは使わない）
    const updateWidth = () => {
      if (ref.current) {
        const w = ref.current.offsetWidth;
        setContainerWidth(w);
      }
    };
    // ...
  }, []);
  
  // BP定数を使って判定
  const isMobileContainer = containerWidth <= BP.mobileMax;
  const isTabletContainer = containerWidth >= BP.tabletMin 
                         && containerWidth <= BP.tabletMax;
  
  return <div ref={ref}>{/* ... */}</div>;
};
```

---

## F. 例外ルール

### F-1. 許容される例外

以下の場合のみ、3段階運用の例外を認める：

#### 1. 特殊なUI調整（詳細5段階）

```typescript
// 例: フォントサイズの微調整
const fontSize = flags.isXs ? 12
               : flags.isSm ? 14
               : flags.isMd ? 14
               : flags.isLg ? 15
               : 16;

// ただし、基本は3段階で十分
// 迷ったら3段階にする
```

#### 2. shared層の内部実装

```typescript
// shared/hooks/ui/useResponsive.ts
const width = window.innerWidth;  // OK（内部実装）
```

#### 3. テスト・デバッグ

```typescript
// shared/utils/responsiveTest.ts
if (window.innerWidth > 1920) { ... }  // OK（テストツール）
```

### F-2. 例外申請プロセス

原則禁止だが、どうしても必要な場合：

1. `docs/audits/RESPONSIVE_EXCEPTIONS.md` に記録
2. 理由・代替案がないことを証明
3. レビューで承認を得る

**目標**: 例外ゼロを維持

---

## G. トラブルシューティング

### G-1. サイドバーが1280pxで開いてしまう

**症状**: 1280px幅でサイドバーがデフォルトで開く  
**原因**: 1280px が Desktop 扱いになっている（旧定義）

**修正**:
- `breakpoints.ts` で `BP.desktopMin: 1281` を確認
- `useResponsive.ts` で `isDesktop: width >= 1281` を確認

### G-2. Tablet判定が 768-1023 になっている

**症状**: 1024-1280px が Desktop 扱いになる  
**原因**: `isTablet: isMd` のみ（`isMd || isLg` でない）

**修正**:
```typescript
// ❌ 誤り
isTablet: isMd,  // 768-1023のみ

// ✅ 正解
isTablet: isMd || isLg,  // 768-1280（★1280含む）
```

### G-3. テストで境界値が不安定

**症状**: 767/768/1280/1281 でテスト失敗  
**原因**: 浮動小数点演算、境界値のズレ

**修正**:
```typescript
// テストは整数で明示的に
expect(makeFlags(767).isMobile).toBe(true);
expect(makeFlags(768).isTablet).toBe(true);
expect(makeFlags(1280).isTablet).toBe(true);   // ★重要
expect(makeFlags(1281).isDesktop).toBe(true);  // ★重要
```

---

## H. チェックリスト

### 実装時（開発者）

- [ ] useResponsive() を使用している
- [ ] isMobile/isTablet/isDesktop で3段階分岐
- [ ] window.innerWidth 直参照なし
- [ ] 数値ハードコード（767/768/1280/1281）なし
- [ ] isLaptop を運用分岐に使用していない
- [ ] pickByDevice は3引数（mobile, tablet, desktop）
- [ ] コメントに境界値を記載する場合は "768-1280" を明記

### レビュー時（レビュアー）

- [ ] RESPONSIVE_BREAKPOINT_POLICY.md に準拠
- [ ] 禁止パターンが含まれていない
- [ ] 境界値テスト（767/768/1280/1281）追加されている
- [ ] FSD責務が適切（pagesは構造のみ、modelにロジック集約）
- [ ] 例外がある場合は RESPONSIVE_EXCEPTIONS.md に記録

---

## I. 参考リンク

- [RESPONSIVE_BREAKPOINT_POLICY.md](./RESPONSIVE_BREAKPOINT_POLICY.md) - 運用ポリシー
- [RESPONSIVE_AUDIT_BEFORE.md](../audits/RESPONSIVE_AUDIT_BEFORE.md) - 変更前監査
- [RESPONSIVE_AUDIT_AFTER.md](../audits/RESPONSIVE_AUDIT_AFTER.md) - 変更後監査
- [shared/constants/breakpoints.ts](../../src/shared/constants/breakpoints.ts) - 境界値定義
- [shared/hooks/ui/useResponsive.ts](../../src/shared/hooks/ui/useResponsive.ts) - レスポンシブフック

---

**作成者**: GitHub Copilot  
**更新日**: 2025-12-22  
**次回更新**: 境界値変更時、または新パターン追加時
