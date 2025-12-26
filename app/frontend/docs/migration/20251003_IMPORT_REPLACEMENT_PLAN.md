# Phase 2: Import パス置換計画

## 📋 置換が必要なファイル一覧

### 1. HTTPクライアント（5ファイル）

#### `@/services/httpClient` → `@shared/infrastructure/http`

1. ✅ `src/components/Report/interactive/BlockUnitPriceInteractive.tsx`

   ```typescript
   - import { apiPost } from '@/services/httpClient';
   + import { apiPost } from '@shared/infrastructure/http';
   ```

2. ✅ `src/pages/analysis/CustomerListAnalysis.tsx`

   ```typescript
   - import { apiPostBlob } from '@/services/httpClient';
   + import { apiPostBlob } from '@shared/infrastructure/http';
   ```

3. ✅ `src/pages/navi/SolvestNavi.tsx`

   ```typescript
   - import { apiGet, apiPost } from '@/services/httpClient';
   + import { apiGet, apiPost } from '@shared/infrastructure/http';
   ```

4. ✅ `src/services/chatService.ts`

   ```typescript
   - import { apiPost } from '@/services/httpClient';
   + import { apiPost } from '@shared/infrastructure/http';
   ```

5. ✅ `src/services/api/manualsApi.ts`
   ```typescript
   - import { apiGet } from '@/services/httpClient';
   + import { apiGet } from '@shared/infrastructure/http';
   ```

### 2. ユーティリティ（6ファイル）

#### anchors（2ファイル）

6. ✅ `src/pages/manual/ManualPage.tsx`

   ```typescript
   - import { ensureSectionAnchors, smoothScrollToAnchor } from '@/utils/anchors';
   + import { ensureSectionAnchors, smoothScrollToAnchor } from '@shared/utils';
   ```

7. ✅ `src/pages/manual/ManualModal.tsx`
   ```typescript
   - import { ensureSectionAnchors, smoothScrollToAnchor } from '@/utils/anchors';
   + import { ensureSectionAnchors, smoothScrollToAnchor } from '@shared/utils';
   ```

#### csvPreview（1ファイル）

8. ✅ `src/hooks/database/useCsvUploadArea.ts`
   ```typescript
   - import { parseCsvPreview } from '@/utils/csvPreview';
   + import { parseCsvPreview } from '@shared/utils/csv/csvPreview';
   ```

#### pdfWorkerLoader（2ファイル）

9. ✅ `src/components/chat/PdfPreviewModal.tsx`

   ```typescript
   - import { ensurePdfJsWorkerLoaded } from '@/utils/pdfWorkerLoader';
   + import { ensurePdfJsWorkerLoaded } from '@shared/utils';
   ```

10. ✅ `src/components/Report/viewer/PDFViewer.tsx`
    ```typescript
    - import { ensurePdfJsWorkerLoaded } from '@/utils/pdfWorkerLoader';
    + import { ensurePdfJsWorkerLoaded } from '@shared/utils';
    ```

#### validators（1ファイル）

11. ✅ `src/hooks/database/useCsvUploadArea.ts`
    ```typescript
    - import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';
    + import { identifyCsvType, isCsvMatch } from '@shared/utils/validators/csvValidator';
    ```

### 3. 型定義（2ファイル）

#### api.ts（2ファイル）

12. ✅ `src/services/httpClient_impl.ts`

    ```typescript
    - import type { ApiResponse } from '@/types/api';
    + import type { ApiResponse } from '@shared/types';
    ```

13. ✅ `src/shared/infrastructure/http/httpClient_impl.ts`
    ```typescript
    - import type { ApiResponse } from '@/types/api';
    + import type { ApiResponse } from '@shared/types';
    ```

### 4. UIフック（27ファイル）

#### `@/hooks/ui` → `@shared/hooks/ui`

14-28. ✅ 以下15ファイル
`typescript
    - import { useWindowSize } from '@/hooks/ui';
    + import { useWindowSize } from '@shared/hooks/ui';
    `

    - `src/theme/ThemeProvider.tsx`
    - `src/layout/Sidebar.tsx` (2箇所)
    - `src/pages/home/PortalPage.tsx`
    - `src/shared/ui/ReportStepIndicator.tsx`
    - `src/pages/manual/ShogunManualList.tsx`
    - `src/pages/manual/ManualPage.tsx`
    - `src/pages/navi/SolvestNavi.tsx`
    - `src/components/ui/ReportStepIndicator.tsx`
    - `src/components/common/csv-upload/CsvUploadPanel.tsx`
    - `src/components/Report/common/ReportStepperModal.tsx`
    - `src/components/Report/common/ReportStepIndicator.tsx`
    - `src/components/chat/PdfPreviewModal.tsx`
    - `src/components/chat/ChatQuestionSection.tsx`

29. ✅ `src/shared/hooks/useBreakpoint.ts`
    ```typescript
    - import { useWindowSize } from "@/hooks/ui/useWindowSize";
    + import { useWindowSize } from "@shared/hooks/ui";
    ```

#### 相対パス → `@shared/hooks/ui`

30-41. ✅ 以下12ファイル（相対パス）
`typescript
    - import { useWindowSize } from '../../hooks/ui';
    - import { useWindowSize } from '../../../hooks/ui';
    - import { useWindowSize } from '../hooks/ui';
    + import { useWindowSize } from '@shared/hooks/ui';
    `

    - `src/shared/ui/VerticalActionButton.tsx`
    - `src/components/debug/ResponsiveDebugInfo.tsx`
    - `src/components/ui/VerticalActionButton.tsx`
    - `src/components/Report/common/CsvUploadSection.tsx`
    - `src/components/Report/common/ActionsSection_new.tsx`
    - `src/components/Report/common/ReportHeader.tsx`
    - `src/components/Report/common/PreviewSection.tsx`
    - `src/components/Report/viewer/PDFViewer.tsx`
    - `src/components/common/csv-upload/CsvUploadCard.tsx`
    - `src/components/Report/common/ActionsSection.tsx`
    - `src/components/Report/common/ReportManagePageLayout.tsx`
    - `src/layout/MainLayout.tsx`

---

## 📊 置換サマリー

| カテゴリ         | ファイル数 | 対象パス                |
| ---------------- | ---------- | ----------------------- |
| HTTPクライアント | 5          | `@/services/httpClient` |
| ユーティリティ   | 6          | `@/utils/*`             |
| 型定義           | 2          | `@/types/api`           |
| UIフック         | 27         | `@/hooks/ui` + 相対パス |
| **合計**         | **40**     | -                       |

---

## ✅ 実行順序

1. HTTPクライアント（影響範囲が大きい）
2. 型定義（HTTPクライアントが依存）
3. ユーティリティ
4. UIフック

実行しますか？
