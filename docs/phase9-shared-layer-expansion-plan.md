# Phase 9: Shared Layer Expansion - Execution Plan

**Status:** 🚀 In Progress  
**Branch:** `phase9/shared-layer-expansion`  
**Date:** 2025-10-03

---

## 🎯 Goals

Phase 9では、srcルートに散在しているファイルを`shared/`層に統合し、FSD構造を完成させます。

### Primary Objectives
1. ✅ `utils/` → `shared/lib/` に移行
2. ✅ `types/` → `shared/types/` に統合
3. ✅ `config/` → `shared/config/` に統合
4. ✅ `services/` → `shared/api/` に統合
5. ✅ 他の散在ディレクトリの整理
6. ✅ Import pathの更新

---

## 📋 Migration Steps

### Step 1: Utils → Shared/Lib Migration

**Target Directory:** `src/utils/` (7 files)

**Files to Migrate:**
```
src/utils/
├── anchors.ts                  → shared/lib/anchors.ts
├── csvPreview.ts              → shared/lib/csvPreview.ts
├── notify.ts                  → shared/lib/notify.ts (deprecated - use features/notification)
├── notify.test.ts             → shared/lib/notify.test.ts (keep for reference)
├── pdfWorkerLoader.ts         → shared/lib/pdfWorkerLoader.ts
├── responsiveTest.ts          → shared/lib/responsiveTest.ts (review if needed)
└── validators/
    └── csvValidator.ts        → shared/lib/validators/csvValidator.ts
```

**Action:**
1. Create `shared/lib/` directory
2. Move all utils files to `shared/lib/`
3. Create `shared/lib/index.ts` for Public API
4. Update all imports from `@/utils/*` to `@shared/lib/*`
5. Delete `src/utils/` directory

---

### Step 2: Types → Shared/Types Migration

**Target Directory:** `src/types/` (6 files)

**Files to Migrate:**
```
src/types/
├── api.ts                     → shared/types/api.ts
├── manuals.ts                 → shared/types/manuals.ts (or features/manual/types?)
├── navi.ts                    → shared/types/navi.ts
├── report.ts                  → shared/types/report.ts (or features/report/types?)
├── reportBase.ts              → shared/types/reportBase.ts
└── yaml.d.ts                  → shared/types/yaml.d.ts
```

**Current State:**
- `shared/types/` already exists
- Need to consolidate duplicate type definitions

**Action:**
1. Review existing `shared/types/` contents
2. Move `src/types/*` to `shared/types/`
3. Merge duplicate definitions
4. Update `shared/types/index.ts` for Public API
5. Update all imports from `@/types/*` to `@shared/types/*`
6. Delete `src/types/` directory

**Note:** Consider if `manuals.ts` and `report.ts` should be in feature-specific types instead.

---

### Step 3: Config → Shared/Config Migration

**Target Directory:** `src/config/` (1 file)

**Files to Migrate:**
```
src/config/
└── notification.ts            → shared/config/notification.ts (or features/notification/config?)
```

**Action:**
1. Review if this belongs in `shared/config/` or `features/notification/config/`
2. Move to appropriate location
3. Update imports
4. Delete `src/config/` directory if empty

---

### Step 4: Services → Shared/API Migration

**Target Directory:** `src/services/` (3 files)

**Files to Migrate:**
```
src/services/
├── httpClient.ts              → shared/infrastructure/http/httpClient.ts (already exists?)
├── httpClient_impl.ts         → shared/infrastructure/http/httpClient_impl.ts (check duplicate)
└── api/
    └── manualsApi.ts          → features/manual/api/manualsApi.ts (feature-specific!)
```

**Current State:**
- `shared/infrastructure/http/` already exists
- May have duplicate httpClient implementations

**Action:**
1. Check if `shared/infrastructure/http/` has httpClient
2. Consolidate duplicate implementations
3. Move `manualsApi.ts` to `features/manual/api/`
4. Update all imports
5. Delete `src/services/` directory

---

### Step 5: Other Root Directories Review

**Directories to Review:**

1. **src/constants/** → Already exists in `shared/constants/`
   - Check for duplicates
   - Consolidate if needed

2. **src/data/** → Should be empty (deleted in Phase 8)
   - Verify deletion

3. **src/layout/** → Legacy layout components
   - Move to `shared/ui/layout/` or delete if unused

4. **src/local_config/** → Local configuration files
   - Keep in root (not part of shared layer)

5. **src/parsers/** → Parser utilities
   - Move to `shared/lib/parsers/` or feature-specific

6. **src/routes/** → Route configuration
   - Keep in `app/routes/` (application layer)

7. **src/stores/** → State management stores
   - Review and move to appropriate features or shared

8. **src/theme/** → Theme configuration
   - Keep in root or move to `shared/theme/`

---

## 📊 Expected Changes

### Directory Structure After Phase 9

```
src/
├── app/                        # Application Layer (unchanged)
├── pages/                      # Pages Layer (unchanged)
├── widgets/                    # Widgets Layer (unchanged)
├── features/                   # Features Layer (unchanged + manualsApi)
├── entities/                   # Entities Layer (unchanged)
│
├── shared/                     # Shared Layer (EXPANDED)
│   ├── api/                    # Consolidated API clients
│   ├── components/             # Shared UI components (existing)
│   ├── config/                 # Shared configuration
│   ├── constants/              # Shared constants (existing)
│   ├── hooks/                  # Shared hooks (existing)
│   ├── infrastructure/         # Infrastructure (existing)
│   ├── lib/                    # ✨ NEW: Utility functions
│   │   ├── anchors.ts
│   │   ├── csvPreview.ts
│   │   ├── pdfWorkerLoader.ts
│   │   ├── validators/
│   │   └── index.ts
│   ├── styles/                 # Shared styles (existing)
│   ├── types/                  # ✨ EXPANDED: All shared types
│   │   ├── api.ts
│   │   ├── manuals.ts
│   │   ├── navi.ts
│   │   ├── report.ts
│   │   ├── reportBase.ts
│   │   └── index.ts
│   ├── ui/                     # Shared UI utilities (existing)
│   └── utils/                  # Legacy (might be duplicate of lib/)
│
├── theme/                      # Theme configuration (keep in root)
├── routes/                     # Route configuration (keep in root)
└── main.tsx                    # Entry point (unchanged)
```

### Directories to Delete
- ❌ `src/utils/` (after migration to `shared/lib/`)
- ❌ `src/types/` (after migration to `shared/types/`)
- ❌ `src/config/` (after migration to `shared/config/`)
- ❌ `src/services/` (after migration to `shared/` or `features/`)

---

## 🔧 Import Path Updates

### Pattern Changes

| Old Pattern | New Pattern | Scope |
|------------|-------------|-------|
| `@/utils/*` | `@shared/lib/*` | All utility functions |
| `@/types/*` | `@shared/types/*` | All type definitions |
| `@/config/*` | `@shared/config/*` | Shared config |
| `@/services/httpClient` | `@shared/infrastructure/http` | HTTP client |
| `@/services/api/manualsApi` | `@features/manual/api` | Feature-specific API |

### TypeScript Path Aliases (tsconfig.json)

Check if these need updates:
```json
{
  "compilerOptions": {
    "paths": {
      "@/*": ["./src/*"],
      "@shared/*": ["./src/shared/*"],
      "@features/*": ["./src/features/*"],
      "@pages/*": ["./src/pages/*"],
      "@widgets/*": ["./src/widgets/*"]
    }
  }
}
```

---

## ✅ Validation Steps

After each step:
1. Run `npm run build` - ensure 0 errors
2. Check for broken imports
3. Run tests if available
4. Commit changes

Final validation:
1. Full build verification
2. All import paths use FSD-compliant aliases
3. No duplicate files
4. All legacy directories deleted

---

## 📝 Notes

### Decisions Needed
- [ ] Should `manuals.ts` types go to `features/manual/types/`?
- [ ] Should `report.ts` types go to `features/report/types/`?
- [ ] Is `notify.ts` deprecated in favor of `features/notification`?
- [ ] What to do with `parsers/` and `stores/` directories?
- [ ] Should `theme/` stay in root or move to `shared/theme/`?

### Empty Files Review
During migration, check for empty or unused files and delete them.

---

## 🎯 Success Criteria

Phase 9 is complete when:
- ✅ All `utils/` migrated to `shared/lib/`
- ✅ All `types/` migrated to `shared/types/`
- ✅ All `config/` migrated appropriately
- ✅ All `services/` migrated appropriately
- ✅ All import paths updated
- ✅ Build passes with 0 errors
- ✅ Legacy directories deleted
- ✅ Documentation updated

---

**Next:** Begin Step 1 - Utils → Shared/Lib Migration
