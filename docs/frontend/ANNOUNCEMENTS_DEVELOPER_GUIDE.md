# お知らせ機能 - 開発者ガイド

**最終更新**: 2025年12月23日

---

## 📖 このガイドについて

このドキュメントは、お知らせ機能の開発者向けガイドです。  
新規機能追加、バグ修正、次フェーズ開発（HTTP/DB対応）を行う際の参考にしてください。

---

## 🏗️ ディレクトリ構造

```
app/frontend/src/features/announcements/
├── domain/                   # ドメインロジック（ビジネスルール）
│   └── announcement.ts
├── ports/                    # 抽象化（インターフェース）
│   └── AnnouncementRepository.ts
├── infrastructure/           # 具体実装（データ取得・永続化）
│   ├── seed.ts
│   ├── LocalAnnouncementRepository.ts
│   └── announcementUserStateStorage.ts
├── model/                    # ViewModel（状態管理・ロジック）
│   ├── useAnnouncementBannerViewModel.ts
│   ├── useAnnouncementsListViewModel.ts
│   └── useUnreadAnnouncementCountViewModel.ts
├── ui/                       # UIコンポーネント（状態レス）
│   ├── AnnouncementBanner.tsx
│   ├── AnnouncementList.tsx
│   ├── AnnouncementDetailModal.tsx
│   └── NewsMenuLabel.tsx
└── index.ts                  # 公開API（エクスポート）
```

---

## 🔧 コーディング規約

### 1. 責務分離

| 層                 | 責務                         | 禁止事項                                    |
| ------------------ | ---------------------------- | ------------------------------------------- |
| **domain**         | ビジネスルール、型定義       | 外部依存（API、DB、localStorage）を持たない |
| **ports**          | 抽象化（インターフェース）   | 実装を含まない                              |
| **infrastructure** | データ取得・永続化の具体実装 | ビジネスロジックを含まない                  |
| **model**          | 状態管理、ViewModel          | UIレンダリングを含まない                    |
| **ui**             | UIレンダリング               | 状態管理、API呼び出しを含まない             |

### 2. 型安全性

```typescript
// ✅ Good: 型を明示
interface UseAnnouncementBannerViewModelResult {
  announcement: Announcement | null;
  isLoading: boolean;
  onAcknowledge: () => void;
}

export function useAnnouncementBannerViewModel(
  userKey: string = "local",
): UseAnnouncementBannerViewModelResult {
  // ...
}

// ❌ Bad: any 使用
export function useAnnouncementBannerViewModel(userKey: any): any {
  // ...
}
```

### 3. 命名規則

| 種類                 | 規則             | 例                                       |
| -------------------- | ---------------- | ---------------------------------------- |
| 型・インターフェース | PascalCase       | `Announcement`, `AnnouncementRepository` |
| 関数・変数           | camelCase        | `isAnnouncementActive`, `userKey`        |
| Hooks                | `use` 接頭辞     | `useAnnouncementBannerViewModel`         |
| UIコンポーネント     | PascalCase       | `AnnouncementBanner`                     |
| 定数                 | UPPER_SNAKE_CASE | `ANNOUNCEMENT_SEEDS`                     |

---

## 🧩 主要コンポーネントの使用例

### ViewModel の使用

```typescript
import { useAnnouncementsListViewModel } from '@features/announcements';

const MyPage: React.FC = () => {
  const { user } = useAuth();
  const userKey = user?.userId ?? 'local';

  const {
    announcements,
    isLoading,
    openDetail,
    isUnread,
  } = useAnnouncementsListViewModel(userKey);

  if (isLoading) {
    return <Spin />;
  }

  return (
    <AnnouncementList
      items={announcements}
      onOpen={openDetail}
      isUnread={isUnread}
    />
  );
};
```

### Repository の差し替え

```typescript
// 現在（MVP）: LocalAnnouncementRepository
import { announcementRepository } from "@features/announcements/infrastructure/LocalAnnouncementRepository";

// 将来（HTTP対応）: HttpAnnouncementRepository
import { announcementRepository } from "@features/announcements/infrastructure/HttpAnnouncementRepository";

// ViewModel内での使用（どちらも同じインターフェース）
const announcements = await announcementRepository.list();
const announcement = await announcementRepository.get(id);
```

---

## 🔄 データフロー

### 一覧ページのデータフロー

```
[ユーザー操作]
    ↓
[AnnouncementList (UI)]
    ↓ onOpen(id)
[useAnnouncementsListViewModel (ViewModel)]
    ↓ markAsRead(userKey, id)
[announcementUserStateStorage (Infrastructure)]
    ↓ localStorage.setItem(...)
[localStorage]
```

### バナー表示のデータフロー

```
[ページレンダリング]
    ↓
[useAnnouncementBannerViewModel (ViewModel)]
    ↓ repository.list()
[LocalAnnouncementRepository (Infrastructure)]
    ↓ filter(isAnnouncementActive)
[ANNOUNCEMENT_SEEDS (Seed Data)]
    ↓ filter(isBannerTarget && !isAcknowledged)
[ViewModel]
    ↓ announcement
[AnnouncementBanner (UI)]
```

---

## 🧪 テストの書き方

### ViewModel のユニットテスト（例）

```typescript
import { renderHook, act } from "@testing-library/react";
import { useAnnouncementBannerViewModel } from "@features/announcements";

describe("useAnnouncementBannerViewModel", () => {
  beforeEach(() => {
    localStorage.clear();
  });

  it("should return banner announcement", async () => {
    const { result } = renderHook(() =>
      useAnnouncementBannerViewModel("test-user"),
    );

    // 初期状態はローディング
    expect(result.current.isLoading).toBe(true);

    // 非同期処理を待つ
    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    // バナー対象が取得される
    expect(result.current.announcement).not.toBeNull();
    expect(result.current.announcement?.pinned).toBe(true);
  });

  it("should acknowledge announcement", async () => {
    const { result } = renderHook(() =>
      useAnnouncementBannerViewModel("test-user"),
    );

    await act(async () => {
      await new Promise((resolve) => setTimeout(resolve, 0));
    });

    const announcementId = result.current.announcement?.id;

    // 確認済みにする
    act(() => {
      result.current.onAcknowledge();
    });

    // アナウンスメントが消える
    expect(result.current.announcement).toBeNull();

    // localStorageに保存される
    const state = JSON.parse(
      localStorage.getItem("announcements.v1.test-user") || "{}",
    );
    expect(state.ackAtById[announcementId!]).toBeDefined();
  });
});
```

### UIコンポーネントのテスト（例）

```typescript
import { render, screen, fireEvent } from '@testing-library/react';
import { AnnouncementBanner } from '@features/announcements';

describe('AnnouncementBanner', () => {
  const mockAnnouncement = {
    id: 'test-001',
    title: 'テストお知らせ',
    bodyMd: 'これはテストです。',
    severity: 'warn' as const,
    pinned: true,
    publishFrom: '2025-01-01T00:00:00Z',
    publishTo: null,
  };

  it('should render announcement', () => {
    const onClose = jest.fn();
    const onAcknowledge = jest.fn();

    render(
      <AnnouncementBanner
        announcement={mockAnnouncement}
        onClose={onClose}
        onAcknowledge={onAcknowledge}
      />
    );

    expect(screen.getByText('テストお知らせ')).toBeInTheDocument();
  });

  it('should call onAcknowledge when button clicked', () => {
    const onClose = jest.fn();
    const onAcknowledge = jest.fn();

    render(
      <AnnouncementBanner
        announcement={mockAnnouncement}
        onClose={onClose}
        onAcknowledge={onAcknowledge}
      />
    );

    fireEvent.click(screen.getByText('理解しました'));
    expect(onAcknowledge).toHaveBeenCalledTimes(1);
  });
});
```

---

## 🐛 デバッグのヒント

### localStorage の確認

開発者ツール（F12）→ Application → Local Storage で確認：

```json
{
  "announcements.v1.local": {
    "readAtById": {
      "ann-001": "2025-12-23T10:30:00.000Z"
    },
    "ackAtById": {
      "ann-003": "2025-12-23T10:35:00.000Z"
    }
  }
}
```

### ViewModel のログ出力

```typescript
export function useAnnouncementsListViewModel(userKey: string = "local") {
  const [announcements, setAnnouncements] = useState<Announcement[]>([]);

  useEffect(() => {
    const fetchAnnouncements = async () => {
      const all = await announcementRepository.list();
      console.log("[ViewModel] Fetched announcements:", all); // ← デバッグログ
      setAnnouncements(all);
    };
    fetchAnnouncements();
  }, []);

  // ...
}
```

### React DevTools でステート確認

1. React DevTools をインストール
2. Components タブで該当コンポーネントを選択
3. Hooks セクションでステート値を確認

---

## 🚀 次フェーズ開発ガイド

### HTTP/DB 対応の実装手順

#### 1. バックエンドAPI作成

```python
# app/backend/core_api/app/api/routers/announcements.py

from fastapi import APIRouter, Depends
from app.core.usecases.announcement_usecases import AnnouncementUseCases

router = APIRouter(prefix="/api/announcements", tags=["announcements"])

@router.get("/")
async def list_announcements(
    usecases: AnnouncementUseCases = Depends()
):
    """アクティブなお知らせ一覧を取得"""
    return await usecases.list_active_announcements()

@router.get("/{announcement_id}")
async def get_announcement(
    announcement_id: str,
    usecases: AnnouncementUseCases = Depends()
):
    """指定IDのお知らせを取得"""
    return await usecases.get_announcement(announcement_id)

@router.post("/{announcement_id}/read")
async def mark_as_read(
    announcement_id: str,
    user_id: str = Depends(get_current_user_id),
    usecases: AnnouncementUseCases = Depends()
):
    """既読にする"""
    await usecases.mark_as_read(user_id, announcement_id)
    return {"status": "ok"}
```

#### 2. HttpAnnouncementRepository 作成

```typescript
// app/frontend/src/features/announcements/infrastructure/HttpAnnouncementRepository.ts

import type { Announcement } from "../domain/announcement";
import type { AnnouncementRepository } from "../ports/AnnouncementRepository";
import { httpClient } from "@/shared/infrastructure/http";

export class HttpAnnouncementRepository implements AnnouncementRepository {
  async list(): Promise<Announcement[]> {
    const response = await httpClient.get<Announcement[]>("/api/announcements");
    return response.data;
  }

  async get(id: string): Promise<Announcement | null> {
    try {
      const response = await httpClient.get<Announcement>(
        `/api/announcements/${id}`,
      );
      return response.data;
    } catch {
      return null;
    }
  }
}

export const announcementRepository = new HttpAnnouncementRepository();
```

#### 3. ユーザー状態をサーバー管理に変更

```typescript
// app/frontend/src/features/announcements/infrastructure/announcementUserStateApi.ts

import { httpClient } from "@/shared/infrastructure/http";

export async function markAsRead(announcementId: string): Promise<void> {
  await httpClient.post(`/api/announcements/${announcementId}/read`);
}

export async function markAsAcknowledged(
  announcementId: string,
): Promise<void> {
  await httpClient.post(`/api/announcements/${announcementId}/acknowledge`);
}

export async function getUnreadCount(): Promise<number> {
  const response = await httpClient.get<{ count: number }>(
    "/api/announcements/unread-count",
  );
  return response.data.count;
}
```

#### 4. ViewModel の更新

```typescript
// model/useAnnouncementsListViewModel.ts の変更例

import { markAsRead as markAsReadApi } from "../infrastructure/announcementUserStateApi";

const openDetail = useCallback(
  async (id: string) => {
    const ann = announcements.find((a) => a.id === id);
    if (ann) {
      // localStorage → API呼び出しに変更
      await markAsReadApi(id);
      setStateVersion((v) => v + 1);
      setSelectedAnnouncement(ann);
      setIsDetailOpen(true);
    }
  },
  [announcements],
);
```

---

## 📦 パフォーマンス最適化

### 1. メモ化

```typescript
// ✅ Good: 重い計算は useMemo で
const unreadCount = useMemo(() => {
  const state = loadUserState(userKey);
  return announcements.filter((ann) => !state.readAtById[ann.id]).length;
}, [announcements, userKey]);

// ❌ Bad: 毎回計算
const unreadCount = announcements.filter(
  (ann) => !isRead(userKey, ann.id),
).length;
```

### 2. コンポーネントの分割

```typescript
// ✅ Good: 細かく分割して再レンダリング範囲を限定
<AnnouncementList items={announcements} onOpen={openDetail} isUnread={isUnread} />

// ❌ Bad: 巨大なコンポーネントで全体が再レンダリング
<AllInOneAnnouncementComponent />
```

### 3. 遅延ローディング

```typescript
// pages/home/index.ts
export const NewsPage = lazy(() => import("./NewsPage"));
```

---

## 🔒 セキュリティ考慮事項

### XSS 対策

```typescript
// ✅ Good: エスケープ処理
<Typography.Text>{announcement.title}</Typography.Text>

// ❌ Bad: dangerouslySetInnerHTML を安易に使わない
<div dangerouslySetInnerHTML={{ __html: announcement.bodyMd }} />
```

### 認証・認可

```typescript
// 将来的にユーザーロールに応じた表示制御
const { user } = useAuth();
const isAdmin = user?.role === 'admin';

{isAdmin && <AdminAnnouncementEditor />}
```

---

## 📚 参考リンク

- [React Hooks 公式ドキュメント](https://react.dev/reference/react)
- [TypeScript Handbook](https://www.typescriptlang.org/docs/handbook/intro.html)
- [Ant Design Components](https://ant.design/components/overview/)
- [Feature-Sliced Design](https://feature-sliced.design/)

---

**更新履歴**

| 日付       | 変更内容 | 担当    |
| ---------- | -------- | ------- |
| 2025-12-23 | 初版作成 | Copilot |
