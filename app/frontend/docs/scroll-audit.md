# スクロール/高さ 問題候補 調査レポート

| 種別 | ファイル | 行 | 抜粋 | リスク | 修正方針 |
|---|---|---:|---|---|---|
| 100vh | src/layout/MainLayout.tsx | 18 | `minHeight: '100vh'` | 高 | 骨格(AppShell)に差し替え、100%ベースへ |
| 100vh | src/layout/MainLayout.tsx | 28-29 | `calc(100vh - 64px)` | 高 | 骨格で高さ伝播に統一 |
| 100vh | src/index.css | 137,166 | `min-height: calc(100vh - 64px);` | 中 | 0に修正し骨格側で管理 |
| 100vh | src/layout/Sidebar.tsx | 121 | `height: '100vh'` | 高 | 100%に変更済み |
| 100vh | src/layout/Sidebar.tsx | 163 | `height: 'calc(100vh - 64px)'` | 高 | flex + min-h-0 に変更済み |
| 100dvh | src/pages/portal/PortalPage.tsx | 381 | `minHeight: '100dvh'` | 中 | 骨格適用後、不要なら撤去 |
| 100vh | src/pages/analysis/CustomerListAnalysis.tsx | 102,113 | `height: '100vh'` 等 | 高 | Page内1スクロールへ |
| 100vh | src/pages/navi/PdfChatBot.tsx | 247 | `height: '100vh'` | 高 | Page内1スクロールへ |
| sticky | src/pages/manual/shogunManual.module.css | 11,44 | `position: sticky;` | 注意 | 上位でoverflow:hiddenを避ける |
| overflow | src/index.css | 7 | `overflow: auto` | 中 | root非スクロールへ変更済み |
| overflow | src/shared/styles/base.css | 95 | `overflow: hidden` | 中 | Page/sticky衝突注意、順次是正 |
| Table.y | src/pages/database/RecordListPage.tsx | 274 | `scroll={{..., y: 600}}` | 中 | AutoHeightTable適用済み |
| Table.y | src/pages/CustomerListDashboard.tsx | 260 | `scroll={{ y: MAP_HEIGHT - 90 }}` | 中 | AutoHeightTableへ移行候補 |
| Table.y | src/components/database/CsvPreviewCard.tsx | 104 | `scroll={{ y: tableBodyHeight }}` | 中 | AutoHeightTableへ移行候補 |
| Table.y | src/components/analysis/customer-list-analysis/CustomerComparisonResultCard.tsx | 61 | `scroll={{ y: 400 }}` | 中 | AutoHeightTableへ移行候補 |
