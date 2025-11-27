# shared/

## 役割
アプリケーション全体で横断的に使用される共通コードを管理するレイヤー

## 配置するもの
- **ui/**: 汎用UIコンポーネント（Button, Input, Modal など）
- **hooks/**: 汎用カスタムフック（useDebounce, useLocalStorage など）
- **utils/**: ユーティリティ関数（日付処理、フォーマット、バリデーションなど）
- **types/**: 共通の型定義（API型、共通型など）
- **lib/**: サードパーティライブラリのラッパー、共通ライブラリ
- **constants/**: 定数定義（環境変数、設定値など）
- **config/**: 設定ファイル（API設定、テーマ設定など）
- **api/**: 共通API通信機能（HTTPクライアント、インターセプターなど）

## 依存関係
- ❌ 他のいかなるレイヤーにも依存しない（最下位レイヤー）
- ✅ すべてのレイヤーから依存される

## 例
```
shared/
├── ui/
│   ├── button/
│   │   ├── Button.tsx
│   │   └── index.ts
│   ├── input/
│   │   ├── Input.tsx
│   │   └── index.ts
│   ├── modal/
│   │   ├── Modal.tsx
│   │   └── index.ts
│   └── index.ts
├── hooks/
│   ├── useDebounce.ts
│   ├── useLocalStorage.ts
│   ├── useResponsive.ts
│   └── index.ts
├── utils/
│   ├── date.ts
│   ├── format.ts
│   ├── validation.ts
│   └── index.ts
├── types/
│   ├── api.ts
│   ├── common.ts
│   └── index.ts
├── lib/
│   ├── httpClient.ts
│   ├── logger.ts
│   └── index.ts
├── constants/
│   ├── env.ts
│   ├── routes.ts
│   └── index.ts
├── config/
│   ├── api.ts
│   ├── theme.ts
│   └── index.ts
└── api/
    ├── client.ts
    ├── interceptors.ts
    └── index.ts
```

## 設計原則
- **再利用性**: どの機能でも使える汎用的なコード
- **ドメイン非依存**: 特定のビジネスロジックに依存しない
- **安定性**: 頻繁に変更されない安定したコード
- **独立性**: 他のレイヤーに依存しない
