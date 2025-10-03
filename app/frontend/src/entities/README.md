# entities/

## 役割
ビジネスドメインの中心となるエンティティ（ドメインオブジェクト）を管理するレイヤー

## 配置するもの
- **ドメインモデル**: User, Ledger, Report, Manual などのエンティティ
- **エンティティ固有のロジック**: バリデーション、計算、変換処理
- **エンティティの型定義**: TypeScript interface/type
- **エンティティのスキーマ**: Zod などのバリデーションスキーマ
- **エンティティのストア**: グローバルなエンティティ状態管理

## 依存関係
- ✅ shared に依存可能
- ❌ app, pages, widgets, features に依存不可
- ⚠️ 複数の features から参照される共通のドメインオブジェクト

## 例
```
entities/
├── user/
│   ├── model/
│   │   ├── User.ts
│   │   ├── userSchema.ts
│   │   └── userStore.ts
│   ├── api/
│   │   └── userApi.ts
│   ├── lib/
│   │   └── userValidation.ts
│   └── index.ts
├── ledger/
│   ├── model/
│   │   ├── Ledger.ts
│   │   ├── ledgerSchema.ts
│   │   └── ledgerStore.ts
│   ├── api/
│   │   └── ledgerApi.ts
│   └── index.ts
├── report/
│   ├── model/
│   │   ├── Report.ts
│   │   └── reportSchema.ts
│   └── index.ts
└── manual/
    ├── model/
    │   ├── Manual.ts
    │   └── manualSchema.ts
    └── index.ts
```

## entities と features の違い
- **entities**: ビジネスドメインの「データ構造」と「ドメインロジック」
- **features**: ビジネスの「ユースケース」と「機能実装」
- entities は複数の features から参照される共通の概念
