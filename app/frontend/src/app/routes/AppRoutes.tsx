import React, { Suspense, lazy } from "react";
import { Routes, Route, Navigate, useLocation } from "react-router-dom";
import { Spin } from "antd";

// ルート定数
import { ROUTER_PATHS } from "./routes";

// Feature Flags (途中機能の制御)
import { isFeatureEnabled } from "@/shared";

// Dashboard pages (not yet refactored)
// const FactoryDashboard = lazy(() => import('../../pages/dashboard/ukeire/FactoryDashboard'));
const InboundForecastDashboardPage = lazy(
  () => import("../../pages/dashboard/ukeire/InboundForecastDashboardPage"),
);
const PricingDashboard = lazy(
  () => import("../../pages/dashboard/PricingDashboard"),
);
const CustomerListDashboard = lazy(
  () => import("../../pages/dashboard/CustomerListDashboard"),
);

// Analytics pages - using public API
const SalesTreePage = lazy(() =>
  import("@/pages/analytics").then((m) => ({ default: m.SalesTreePage })),
);
const CustomerListAnalysisPage = lazy(() =>
  import("@/pages/analytics").then((m) => ({
    default: m.CustomerListAnalysisPage,
  })),
);

// Report pages - using public API
const ReportManagePage = lazy(() =>
  import("@/pages/report").then((m) => ({ default: m.ReportManagePage })),
);
const ReportFactoryPage = lazy(() =>
  import("@/pages/report").then((m) => ({ default: m.ReportFactoryPage })),
);
const LedgerBookPage = lazy(() =>
  import("@/pages/report").then((m) => ({ default: m.LedgerBookPage })),
);

// Database pages - using public API
const RecordListPage = lazy(() =>
  import("@/pages/database").then((m) => ({ default: m.RecordListPage })),
);
const DatasetImportPage = lazy(() =>
  import("@/pages/database").then((m) => ({ default: m.DatasetImportPage })),
);
const RecordManagerPage = lazy(() =>
  import("@/pages/database").then((m) => ({ default: m.RecordManagerPage })),
);
const ReservationDailyPage = lazy(() =>
  import("@/pages/database").then((m) => ({ default: m.ReservationDailyPage })),
);

// Manual pages - using public API
const GlobalManualSearchPage = lazy(() =>
  import("@/pages/manual").then((m) => ({ default: m.GlobalManualSearchPage })),
);
const ShogunManualListPage = lazy(() =>
  import("@/pages/manual").then((m) => ({ default: m.ShogunManualListPage })),
);
const ManualDetailPage = lazy(() =>
  import("@/pages/manual").then((m) => ({ default: m.ManualDetailPage })),
);
const ManualDetailRouteComponent = lazy(() =>
  import("@/features/manual").then((m) => ({ default: m.ManualDetailRoute })),
);
const VendorMasterPage = lazy(() =>
  import("@/pages/manual").then((m) => ({ default: m.VendorMasterPage })),
);

// Chat pages - using public API
const SolvestNaviPage = lazy(() =>
  import("@/pages/navi").then((m) => ({ default: m.SolvestNaviPage })),
);

// Home pages - using public API
const PortalPage = lazy(() =>
  import("@/pages/home").then((m) => ({ default: m.PortalPage })),
);
const NewsPage = lazy(() =>
  import("@/pages/home").then((m) => ({ default: m.NewsPage })),
);
const AnnouncementDetailPage = lazy(() =>
  import("@/pages/home").then((m) => ({ default: m.AnnouncementDetailPage })),
);

// Utility pages - using public API
const TokenPreviewPage = lazy(() =>
  import("@/pages/utils").then((m) => ({ default: m.TokenPreviewPage })),
);
const TestPage = lazy(() =>
  import("@/pages/utils").then((m) => ({ default: m.TestPage })),
);

// Settings pages - using public API
const SettingsPage = lazy(() =>
  import("@/pages/settings").then((m) => ({ default: m.SettingsPage })),
);

// Error pages
const NotFoundPage = lazy(() => import("@/pages/error/NotFoundPage"));

// ===========================================================
// Experimental pages (Feature Flag で制御)
// フラグ OFF の環境ではルート未接続となり、URL直打ちでも 404 になる
// ===========================================================
const NewReportPage = lazy(() =>
  import("@/pages/experimental").then((m) => ({ default: m.NewReportPage })),
);

const AppRoutes: React.FC = () => {
  const location = useLocation();
  const state = location.state as { backgroundLocation?: Location } | undefined;

  // 本番環境ではテストページへのアクセスを404に
  const isProduction = import.meta.env.MODE === "production";

  return (
    <>
      <Suspense
        fallback={
          <div style={{ padding: 16 }}>
            <Spin />
          </div>
        }
      >
        <Routes location={state?.backgroundLocation || location}>
          {/* ポータル(トップ) - 最初に定義して優先度を高める */}
          <Route path={ROUTER_PATHS.PORTAL} element={<PortalPage />} />

          {/* テスト用ルート - 開発環境のみ */}
          {!isProduction && <Route path="/test" element={<TestPage />} />}

          {/* ダッシュボード */}
          <Route
            path={ROUTER_PATHS.DASHBOARD_UKEIRE}
            element={<InboundForecastDashboardPage />}
          />
          <Route path={ROUTER_PATHS.PRICING} element={<PricingDashboard />} />
          <Route path={ROUTER_PATHS.SALES_TREE} element={<SalesTreePage />} />
          <Route
            path={ROUTER_PATHS.CUSTOMER_LIST}
            element={<CustomerListDashboard />}
          />

          {/* 帳票ページ */}
          {/* /report 直アクセス時は管理ページへ */}
          <Route
            path="/report"
            element={<Navigate to={ROUTER_PATHS.REPORT_MANAGE} replace />}
          />
          <Route
            path={ROUTER_PATHS.REPORT_MANAGE}
            element={<ReportManagePage />}
          />
          {/* 工場帳簿 - Feature Flag で制御 */}
          {isFeatureEnabled("FACTORY_REPORT") && (
            <Route
              path={ROUTER_PATHS.REPORT_FACTORY}
              element={<ReportFactoryPage />}
            />
          )}
          <Route path={ROUTER_PATHS.LEDGER_BOOK} element={<LedgerBookPage />} />

          {/* データ分析 */}
          <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<CustomerListAnalysisPage />}
          />

          {/* チャットボット */}
          <Route path={ROUTER_PATHS.NAVI} element={<SolvestNaviPage />} />

          {/* マニュアル（新） */}
          <Route path="/manuals" element={<GlobalManualSearchPage />} />
          <Route path="/manuals/shogun" element={<ShogunManualListPage />} />
          {/* 単独ページ（正ルート） */}
          <Route path="/manuals/shogun/:id" element={<ManualDetailPage />} />
          {/* マスター - 業者ページ */}
          <Route path="/manual/master/vendor" element={<VendorMasterPage />} />

          {/* データベース関連 */}
          <Route path={ROUTER_PATHS.RECORD_LIST} element={<RecordListPage />} />
          <Route
            path={ROUTER_PATHS.DATASET_IMPORT}
            element={<DatasetImportPage />}
          />
          <Route
            path={ROUTER_PATHS.RECORD_MANAGER}
            element={<RecordManagerPage />}
          />
          {/* 予約表 - Feature Flag で制御 */}
          {isFeatureEnabled("RESERVATION_DAILY") && (
            <Route
              path={ROUTER_PATHS.RESERVATION_DAILY}
              element={<ReservationDailyPage />}
            />
          )}

          {/* トークンプレビュー */}
          <Route
            path={ROUTER_PATHS.TOKEN_PREVIEW}
            element={<TokenPreviewPage />}
          />

          {/* 設定 */}
          <Route path={ROUTER_PATHS.SETTINGS} element={<SettingsPage />} />

          {/* お知らせ */}
          <Route path={ROUTER_PATHS.NEWS} element={<NewsPage />} />
          <Route
            path={ROUTER_PATHS.NEWS_DETAIL}
            element={<AnnouncementDetailPage />}
          />

          {/* ===========================================================
           * 実験的機能 (Feature Flag で制御)
           * フラグ OFF の環境ではルートが存在しないため 404 になる
           * これにより URL 直打ちでもアクセス不能となる
           * =========================================================== */}
          {isFeatureEnabled("NEW_REPORT") && (
            <Route
              path={ROUTER_PATHS.EXPERIMENTAL_NEW_REPORT}
              element={<NewReportPage />}
            />
          )}

          {/* その他/404 */}
          <Route path="*" element={<NotFoundPage />} />
        </Routes>
      </Suspense>

      {/* 背景ロケーションがある場合のみ、モーダルルートをオーバーレイ表示 */}
      {state?.backgroundLocation && (
        <Suspense fallback={null}>
          <Routes>
            <Route
              path="/manuals/shogun/:id"
              element={<ManualDetailRouteComponent />}
            />
          </Routes>
        </Suspense>
      )}
    </>
  );
};

export default AppRoutes;
