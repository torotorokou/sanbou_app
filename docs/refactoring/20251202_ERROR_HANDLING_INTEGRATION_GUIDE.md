# エラーハンドリング統合ガイド

**作成日**: 2024-12-02  
**対象**: `app/frontend/src/shared/utils/errorHandling.ts`

## 概要

このガイドは、フロントエンドアプリケーションにおけるエラーハンドリングの標準パターンを定義します。
`shared/utils/errorHandling.ts` で提供される関数群を活用することで、エラーハンドリングの一貫性を保ち、
ユーザーへの通知を自動化できます。

## 提供される関数

### 1. `handleApiCall<T>`

標準的なAPI呼び出しのエラーハンドリングをラップします。

**使用例（Repository層）**:

```typescript
import { handleApiCall } from "@shared/utils";
import { coreApi } from "@shared";
import type { User } from "../domain/types";

export class UserRepository {
  async getUser(id: string): Promise<User | null> {
    return await handleApiCall(
      () => coreApi.get<User>(`/api/users/${id}`),
      "ユーザー取得",
    );
  }

  async createUser(data: CreateUserParams): Promise<User | null> {
    return await handleApiCall(
      () => coreApi.post<User>("/api/users", data),
      "ユーザー作成",
    );
  }
}
```

**使用例（ViewModel/hooks）**:

```typescript
import { handleApiCall } from "@shared/utils";
import { userRepository } from "../infrastructure/user.repository";

export const useUserData = (userId: string) => {
  const [user, setUser] = useState<User | null>(null);
  const [loading, setLoading] = useState(false);

  const fetchUser = async () => {
    setLoading(true);
    const result = await handleApiCall(
      () => userRepository.getUser(userId),
      "ユーザーデータ取得",
    );
    if (result) {
      setUser(result);
    }
    setLoading(false);
  };

  useEffect(() => {
    fetchUser();
  }, [userId]);

  return { user, loading, refetch: fetchUser };
};
```

### 2. `handleApiCallWithRetry<T>`

ネットワークエラーや一時的な障害に対して、自動リトライを行います。

**使用例（アップロード処理）**:

```typescript
import { handleApiCallWithRetry } from "@shared/utils";
import { coreApi } from "@shared";

export const uploadFile = async (file: File): Promise<UploadResult | null> => {
  const formData = new FormData();
  formData.append("file", file);

  // 最大3回リトライ（デフォルト）
  return await handleApiCallWithRetry(
    () => coreApi.post<UploadResult>("/api/upload", formData),
    "ファイルアップロード",
    3,
  );
};
```

**リトライ間隔**:

- 1回目: 失敗後 1秒待機
- 2回目: 失敗後 2秒待機
- 3回目: 失敗後 3秒待機

### 3. `handleOperation<T>`

API以外の処理（ファイル操作、計算処理など）のエラーハンドリングに使用します。

**使用例（ファイル処理）**:

```typescript
import { handleOperation } from "@shared/utils";

export const processCSV = async (file: File): Promise<ParsedData | null> => {
  return await handleOperation(async () => {
    const text = await file.text();
    return parseCSV(text);
  }, "CSVファイル処理");
};
```

## エラーコード規約

新しいエラーコードを追加する際は、以下の規約に従ってください。

### 命名規則

- **形式**: `UPPER_SNAKE_CASE`
- **カテゴリプレフィックス**: エラーの種類を示す接頭辞を使用

### カテゴリ一覧

| カテゴリ       | 説明                                   | 例                                        |
| -------------- | -------------------------------------- | ----------------------------------------- |
| `INPUT_*`      | 入力エラー（フォーム、パラメータなど） | `INPUT_INVALID`, `INPUT_MISSING`          |
| `VALIDATION_*` | バリデーションエラー                   | `VALIDATION_ERROR`, `VALIDATION_FAILED`   |
| `AUTH_*`       | 認証・認可エラー                       | `AUTH_REQUIRED`, `AUTH_FAILED`            |
| `*_NOT_FOUND`  | リソース未発見                         | `USER_NOT_FOUND`, `FILE_NOT_FOUND`        |
| `PROCESSING_*` | 処理エラー（計算、変換など）           | `PROCESSING_TIMEOUT`, `PROCESSING_FAILED` |
| `TIMEOUT`      | タイムアウト                           | `TIMEOUT`, `CONNECTION_TIMEOUT`           |
| `JOB_*`        | ジョブエラー（バックグラウンド処理）   | `JOB_FAILED`, `JOB_CANCELLED`             |
| `NETWORK_*`    | ネットワークエラー                     | `NETWORK_ERROR`, `NETWORK_UNREACHABLE`    |
| `DATABASE_*`   | データベースエラー                     | `DATABASE_CONNECTION_FAILED`              |

### 良い例

```typescript
const GOOD_EXAMPLES = [
  "INPUT_INVALID",
  "VALIDATION_ERROR",
  "USER_NOT_FOUND",
  "PROCESSING_TIMEOUT",
  "JOB_FAILED",
  "AUTH_REQUIRED",
  "NETWORK_ERROR",
  "DATABASE_CONNECTION_FAILED",
];
```

### 悪い例

```typescript
const BAD_EXAMPLES = [
  "error", // 小文字
  "Error", // PascalCase
  "validation-error", // kebab-case
  "userNotFound", // camelCase
  "err", // 省略形
  "failed", // 抽象的すぎる
];
```

### エラーコード追加チェックリスト

新しいエラーコードを追加する際は、以下を確認してください：

- [ ] `UPPER_SNAKE_CASE` で命名されている
- [ ] カテゴリプレフィックスを使用している
- [ ] 既存のエラーコードと重複していない
- [ ] エラーの原因と種類が明確に分かる
- [ ] ドキュメント（`features/notification/domain/config.ts`）に追加済み

### エラーコードの検証

開発時に `validateErrorCode` 関数でエラーコードが規約に準拠しているか確認できます：

```typescript
import { validateErrorCode } from "@shared/utils/errorHandling";

// ✅ 正しいコード
validateErrorCode("USER_NOT_FOUND"); // true

// ❌ 間違ったコード
validateErrorCode("userNotFound"); // false（警告がコンソールに表示される）
```

## 移行パターン

### Before（旧パターン）

```typescript
// ❌ 各所で個別にエラーハンドリング
export const fetchData = async () => {
  try {
    const response = await coreApi.get("/api/data");
    return response;
  } catch (error) {
    notifyApiError(error, "データ取得に失敗しました");
    console.error("Error:", error);
    return null;
  }
};
```

### After（新パターン）

```typescript
// ✅ handleApiCallを使用
import { handleApiCall } from "@shared/utils";

export const fetchData = async () => {
  return await handleApiCall(() => coreApi.get("/api/data"), "データ取得");
};
```

## ベストプラクティス

### 1. Repository層での使用

Repository層では常に `handleApiCall` を使用し、エラーハンドリングをラップします。

```typescript
export class ReportRepository {
  async getReport(id: string): Promise<Report | null> {
    return await handleApiCall(
      () => coreApi.get<Report>(`/api/reports/${id}`),
      "レポート取得",
    );
  }
}
```

### 2. ViewModel層での使用

ViewModel層では、Repository呼び出しの結果をnullチェックして処理します。

```typescript
export const useReportData = (reportId: string) => {
  const [report, setReport] = useState<Report | null>(null);

  useEffect(() => {
    const loadReport = async () => {
      const result = await repository.getReport(reportId);
      if (result) {
        setReport(result);
      }
    };
    loadReport();
  }, [reportId]);

  return { report };
};
```

### 3. 重要な処理にはリトライを使用

アップロードやデータ送信など、失敗が許されない処理には `handleApiCallWithRetry` を使用します。

```typescript
const handleSubmit = async (data: FormData) => {
  const result = await handleApiCallWithRetry(
    () => coreApi.post("/api/submit", data),
    "データ送信",
    3, // 最大3回リトライ
  );

  if (result) {
    // 成功処理
    navigate("/success");
  }
};
```

## 関連ドキュメント

- [通知機構の設計](../features/notification/README.md)
- [Repository パターン](../shared/infrastructure/README.md)
- [FSD アーキテクチャ](../docs/conventions/FSD_ARCHITECTURE.md)

## 今後の拡張

- [ ] エラー率のモニタリング機能
- [ ] エラーコードの自動カタログ生成
- [ ] SSE通知との統合強化
- [ ] GraphQLエラーハンドリングのサポート
