# Manual Feature

## 概要
環境将軍マニュアルの表示・検索機能を提供

## 責務
- マニュアルの一覧表示
- マニュアル検索
- マニュアル詳細表示
- 目次ナビゲーション
- モーダル/ページ両モード対応

## 構造

### 現在の配置
```
src/
├── components/manual/         # Manual UI Components
│   └── (manual related components)
├── services/api/              # API Client
│   └── manualsApi.ts
├── types/                     # 型定義
│   └── manuals.ts
└── pages/manual/              # ページコンポーネント
    ├── ManualPage.tsx        # フルページモード
    ├── ManualModal.tsx       # モーダルモード
    └── ShogunManualList.tsx  # マニュアル一覧
```

## 主要コンポーネント

### Pages

#### ShogunManualList
- **役割**: マニュアル一覧・検索ページ
- **パス**: `@/pages/manual/ShogunManualList.tsx`
- **機能**:
  - カテゴリ別表示
  - 検索フィルタ
  - モーダル開閉

#### ManualPage
- **役割**: マニュアル詳細フルページ
- **パス**: `@/pages/manual/ManualPage.tsx`
- **機能**:
  - マニュアル本文表示
  - 目次ナビゲーション
  - アンカーリンク

#### ManualModal
- **役割**: マニュアル詳細モーダル
- **パス**: `@/pages/manual/ManualModal.tsx`
- **機能**:
  - モーダル内でマニュアル表示
  - 前後ナビゲーション
  - フルページ展開

### API Client

#### manualsApi
- **パス**: `@/services/api/manualsApi.ts`
- **メソッド**:
  - `list()`: マニュアル一覧取得
  - `get(id)`: マニュアル詳細取得
  - `catalog()`: カタログ (カテゴリ別) 取得

## 型定義

### ManualSummary (一覧用)
```typescript
type ManualSummary = {
  id: string;
  title: string;
  description?: string;
  category: string;
  tags?: string[];
};
```

### ManualDetail (詳細用)
```typescript
type ManualDetail = {
  id: string;
  title: string;
  content: string;        // HTML形式
  category: string;
  sections?: Section[];   // 目次
};
```

### ManualSection (カタログ用)
```typescript
type ManualSection = {
  title: string;
  description?: string;
  icon: React.ReactNode;
  items: ManualItem[];
};
```

## 使用例

### マニュアル一覧の取得
```typescript
import manualsApi from '@/services/api/manualsApi';

async function loadManuals() {
  const manuals = await manualsApi.list({ category: 'syogun' });
  console.log(manuals);
}
```

### マニュアル詳細の表示
```typescript
import { useState, useEffect } from 'react';
import manualsApi from '@/services/api/manualsApi';

function ManualViewer({ manualId }: { manualId: string }) {
  const [data, setData] = useState(null);

  useEffect(() => {
    manualsApi.get(manualId).then(setData);
  }, [manualId]);

  if (!data) return <div>Loading...</div>;

  return (
    <div dangerouslySetInnerHTML={{ __html: data.content }} />
  );
}
```

### モーダル/ページ切り替え
```typescript
// ページモード
<Link to={`/manuals/syogun/${id}?full=1`}>フルページで開く</Link>

// モーダルモード
<Link to={`/manuals/syogun/${id}`} state={{ backgroundLocation: location }}>
  モーダルで開く
</Link>
```

## 目次ナビゲーション

### アンカー生成
- **関数**: `ensureSectionAnchors()`
- **パス**: `@shared/utils/anchors.ts`
- **機能**: H2, H3タグに自動的にIDを付与

### スムーススクロール
- **関数**: `smoothScrollToAnchor()`
- **パス**: `@shared/utils/anchors.ts`
- **機能**: アンカーリンククリック時にスムーススクロール

## 依存関係

### 内部依存
- `@shared/utils/anchors` - 目次ナビゲーション
- `@shared/hooks/ui` - レスポンシブ対応

### 外部依存
- `antd` - UIコンポーネント (Modal, Anchor, Breadcrumb)
- `react-router-dom` - ルーティング

## API仕様

### マニュアル一覧取得
```
GET /manual_api/manuals?category=syogun

Response:
{
  "manuals": [
    {
      "id": "manual_001",
      "title": "環境将軍の使い方",
      "category": "syogun"
    }
  ]
}
```

### マニュアル詳細取得
```
GET /manual_api/manuals/:id

Response:
{
  "id": "manual_001",
  "title": "環境将軍の使い方",
  "content": "<h2>概要</h2><p>...</p>",
  "sections": [
    { "level": 2, "title": "概要", "anchor": "概要" }
  ]
}
```

### カタログ取得
```
GET /manual_api/catalog?category=syogun

Response:
{
  "sections": [
    {
      "title": "基本操作",
      "items": [
        { "id": "manual_001", "title": "環境将軍の使い方" }
      ]
    }
  ]
}
```

## ルーティング

### パス定義
- `/manuals` - マニュアル一覧
- `/manuals/syogun/:id` - マニュアル詳細 (モーダル)
- `/manuals/syogun/:id?full=1` - マニュアル詳細 (フルページ)

### モーダルルーティング
React Routerの`state.backgroundLocation`を使用してモーダル実装

## 今後の改善点

### Phase 4 (将来)
- [ ] `features/manual/` 配下への完全移行
- [ ] 全文検索機能の追加
- [ ] ブックマーク機能
- [ ] 閲覧履歴

### 技術的負債
- [ ] HTML sanitization (XSS対策)
- [ ] 画像の遅延読み込み
- [ ] 目次の自動生成改善
- [ ] オフライン対応

## セキュリティ

### XSS対策
- サーバー側でHTMLサニタイズ
- `dangerouslySetInnerHTML`使用時は信頼できるコンテンツのみ

### アクセス制御
- 認証済みユーザーのみアクセス可能
- ロールベースのマニュアル表示制御 (将来)

## 関連ドキュメント
- `PHASE2_COMPLETION_REPORT.md` - Phase 2完了レポート
- `@/types/manuals.ts` - 型定義詳細
- `@shared/utils/anchors.ts` - アンカーユーティリティ

---

**最終更新**: 2025年10月3日  
**メンテナ**: Sanbou App Team
