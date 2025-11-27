# Phase 3 簡略版 - 実用的アプローチ

## 方針転換の理由
- Phase 2完了時点で、すでに主要な横断的機能は `@shared` に集約済み
- 残りの機能別コンポーネントは、現状の配置でも十分に保守可能
- 完全なFSD移行は段階的に進め、まずは**公開API**と**README**で構造を明確化

## Phase 3-Simplified: 最小限の整理

### 実施内容

#### 1. Features層の README 作成 ✅
各feature配下にREADME.mdを配置し、責務を明確化:
- `features/notification/README.md` - 既存
- `features/report/README.md` - 新規
- `features/database/README.md` - 新規  
- `features/manual/README.md` - 新規
- `features/chat/README.md` - 新規

#### 2. 公開API (index.ts) の整備
各featureの公開インターフェースを定義:
- `features/report/index.ts`
- `features/database/index.ts`
- `features/manual/index.ts`
- `features/chat/index.ts`

#### 3. 型定義の整理
- Report関連型を `@/types/reportBase.ts` から `@/constants/reportConfig.ts` に統合 (already inline)
- Manual関連型を維持 (`@/types/manuals.ts`)
- 新しい移行は不要、既存の配置を文書化

---

## 現状の構造 (変更なし)

### Components層
```
src/components/
├── Report/          # Report UI components
├── chat/            # Chat UI components  
├── database/        # Database UI components
├── manual/          # Manual UI components
├── common/          # 共通UIコンポーネント
└── ui/              # 汎用UIコンポーネント
```

### Hooks層
```
src/hooks/
├── report/          # Report business logic
├── database/        # Database operations
├── data/            # Data fetching
└── ui/              → @shared/hooks/ui (Phase 2完了)
```

### Pages層
```
src/pages/
├── report/          # Report pages
├── manual/          # Manual pages
├── database/        # Database pages
├── navi/            # Navigation (Chat含む)
└── dashboard/       # Dashboard pages
```

---

## Phase 3-Simplified 実施ステップ

### ステップ1: README作成 (各feature配下)
各featureの責務、構造、使用方法を文書化

### ステップ2: 公開API整備
将来の移行を見据え、各featureで何をexportすべきかを定義

### ステップ3: Path Alias追加
必要に応じて新しいエイリアスを追加:
- `@features/report` → `src/features/report` (将来用)
- `@components/Report` → `src/components/Report` (現状維持)
- `@hooks/report` → `src/hooks/report` (現状維持)

### ステップ4: ドキュメント更新
- `MIGRATION_STATUS.md` - 現状の構造を文書化
- `ARCHITECTURE.md` - FSD原則と現在の適用状況
- `FUTURE_ROADMAP.md` - 将来の完全移行計画

---

## 完了基準

- ✅ 各主要機能にREADME.md
- ✅ features/配下の構造が明確
- ✅ 公開APIが定義されている
- ✅ ドキュメントが最新
- ✅ ビルドエラーなし
- ✅ 既存機能が正常動作

---

## メリット

1. **段階的な移行**: 大規模な破壊的変更を避ける
2. **継続的な改善**: 必要な機能から順次移行
3. **ビジネス継続性**: 開発を止めずに改善
4. **リスク軽減**: 各ステップで検証可能
5. **文書化優先**: チーム全体の理解を促進

---

## 次のステップ (Phase 4以降)

### Phase 4: 段階的Feature移行
新規開発や大規模修正時に、該当featureを完全移行:
1. Report機能の完全移行 (レポート生成ロジック改修時)
2. Database機能の完全移行 (CSV処理改善時)
3. Manual機能の完全移行 (マニュアル検索機能追加時)

### Phase 5: Pages層の整理
- ページコンポーネントをWidgets/Featuresに分解
- ルーティング定義の最適化

### Phase 6: 完全なFSD達成
- 全featureがFSD構造に準拠
- 循環依存の完全排除
- 完全なレイヤー分離

---

**開始日**: 2025年10月3日  
**完了予定**: Phase 3-Simplified (本日中)
