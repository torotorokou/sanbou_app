# FSD Refactoring - Architecture Guide

**作成日**: 2025-11-20  
**対象**: sanbou_app フロントエンド

---

## 📐 アーキテクチャの基本方針

このプロジェクトは **FSD (Feature-Sliced Design)** を採用しています。

### レイヤー構造

```
src/
├── app/          # アプリケーション初期化・ルーティング
├── pages/        # ページコンポーネント
├── widgets/      # 複合的なUIブロック
├── features/     # ビジネス機能（ドメインロジック）
├── entities/     # ビジネスエンティティ
└── shared/       # 汎用的な再利用可能コード
```

---

## 🎯 Shared層の原則

### ✅ Shared層に含めるべきもの

**ドメインに依存しない汎用的な機能のみ**

- **UI Components**: 汎用的なボタン、カード、バッジなど
- **Hooks**: レスポンシブ、スクロールトラッキングなど
- **Infrastructure**: HTTP client、API utilities
- **Theme**: デザイントークン、カラーマップ
- **Utils**: 日付処理、文字列処理、ロガーなど
- **Types**: APIレスポンス型、ValidationStatus など

### ❌ Shared層に含めてはいけないもの

**特定のドメイン・ビジネスロジックを含むもの**

- CSV検証ロジック → `features/csv-validation`
- 将軍CSV型定義 → `features/database`
- ジョブポーリング → `features/notification`
- レポート関連の型 → `features/report`

---

## 🔄 今回のリファクタリング内容

### 1. CSV検証機能の統合

**Before:**
```
shared/lib/csv-validation/
  ├── csvHeaderValidator.ts
  ├── useCsvFileValidator.ts
  └── types.ts
```

**After:**
```
features/csv-validation/
  ├── core/
  │   ├── csvHeaderValidator.ts      ← 統合
  │   └── csvRowValidator.ts
  └── hooks/
      └── useCsvFileValidator.ts      ← 統合
```

**理由**: CSV検証はビジネスロジックを含むため、feature層で管理

---

### 2. CsvKind型の移動

**Before:**
```
shared/types/csvKind.ts
```

**After:**
```
features/database/shared/types/csvKind.ts
```

**理由**: 「将軍CSV」という特定ドメインの概念

---

### 3. Job Serviceの再配置

**Before:**
```
shared/infrastructure/job/jobService.ts
```

**After:**
```
features/notification/infrastructure/jobService.ts
```

**理由**: `pollJob`は通知機能に強く依存しており、汎用化が不十分

---

### 4. 循環参照の解消

**Before:**
```
features/csv-validation/adapters/     ← 削除
features/csv-validation/model/rules.ts ← 移動
```

**After:**
```
features/database/config/rules.ts
```

**理由**: 
- `csv-validation` → `database` の循環依存を解消
- `rules.ts` は実質的にdatabase設定の一部

---

## 📦 依存関係ルール

### レイヤー間の依存方向

```
app
 ↓
pages
 ↓
widgets
 ↓
features  ←─── 相互依存は避ける
 ↓
entities
 ↓
shared    ←─── 下位層は上位層に依存しない
```

### Feature間の依存

**原則**: Feature間の直接的な依存は最小限に

**許可される依存**:
```typescript
// OK: notification は汎用的
import { notifyError } from '@features/notification';

// NG: 特定feature間の相互依存
import { SomeComponent } from '@features/report';  // csv-validation から
```

**推奨パターン**:
- 共通ロジック → `shared` に配置
- Feature固有だが再利用 → `feature/shared` サブディレクトリ
- どうしても必要 → Dependency Injection パターン

---

## 🗂️ ディレクトリ構造ガイド

### Feature内の構造 (MVVM + Repository)

```
features/[feature-name]/
├── ui/                    # View層
│   └── components/
├── model/                 # ViewModel層
│   └── use[Name]VM.ts
├── domain/                # ドメインロジック
│   └── types/
├── infrastructure/        # 外部API通信
│   └── repository.ts
├── application/           # アプリケーションサービス
├── shared/                # Feature内共通
│   ├── types/
│   └── utils/
└── index.ts               # 公開API
```

### Shared層の構造

```
shared/
├── constants/             # 定数定義
├── hooks/                 # 汎用Hooks
│   └── ui/               # UI関連Hooks
├── infrastructure/        # インフラ層
│   └── http/             # HTTP client
├── theme/                 # デザイン設定
├── types/                 # 共通型定義
├── ui/                    # 汎用UIコンポーネント
├── utils/                 # ユーティリティ関数
└── styles/                # グローバルスタイル
```

---

## 📝 Import規約

### 推奨されるImportパターン

```typescript
// ✅ Good: barrel export経由
import { useCsvFileValidator } from '@features/csv-validation';
import { apiGet } from '@/shared';

// ❌ Bad: 内部実装を直接参照
import { useCsvFileValidator } from '@features/csv-validation/hooks/useCsvFileValidator';
```

### Alias設定

```typescript
@/            → src/
@shared       → src/shared
@features     → src/features
@pages        → src/pages
```

---

## 🔍 コードレビューチェックリスト

### Shared層への追加時

- [ ] ドメイン固有の概念を含んでいないか？
- [ ] 3つ以上のfeatureで使用される汎用的なコードか？
- [ ] Feature層への依存がないか？

### Feature層への追加時

- [ ] 他のFeatureへの依存は最小限か？
- [ ] `shared` に移動すべき汎用ロジックはないか？
- [ ] 循環依存を引き起こしていないか？

### Import追加時

- [ ] 適切なalias (`@/shared`, `@features`) を使用しているか？
- [ ] Barrel export経由でimportしているか？
- [ ] 依存方向はレイヤールールに従っているか？

---

## 🚀 今後の改善提案

1. **Entity層の導入検討**
   - `database/shared/types/csvKind.ts` → `entities/csv-kind`
   - 複数featureで使用されるエンティティの抽出

2. **Dependency Injection強化**
   - Feature間の依存をインターフェース経由に
   - テスタビリティの向上

3. **型定義の集約**
   - API型定義の一元管理
   - OpenAPI schemaからの自動生成検討

---

## 📚 参考資料

- [Feature-Sliced Design 公式ドキュメント](https://feature-sliced.design/)
- [SOLID原則](https://en.wikipedia.org/wiki/SOLID)
- [Clean Architecture](https://blog.cleancoder.com/uncle-bob/2012/08/13/the-clean-architecture.html)

---

**Last Updated**: 2025-11-20  
**Maintained by**: Development Team
