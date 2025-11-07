import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';

// ルート定数
import { ROUTER_PATHS } from './routes';

// Dashboard pages (not yet refactored)
const ManagementDashboard = lazy(() => import('../../pages/dashboard/ManagementDashboard'));
// const FactoryDashboard = lazy(() => import('../../pages/dashboard/ukeire/FactoryDashboard'));
const InboundForecastDashboardPage = lazy(() => import('../../pages/dashboard/ukeire/InboundForecastDashboardPage'));
const PricingDashboard = lazy(() => import('../../pages/dashboard/PricingDashboard'));
const CustomerListDashboard = lazy(() => import('../../pages/dashboard/CustomerListDashboard'));
const SalesTreePage = lazy(() => import('../../pages/dashboard/SalesTreePage'));

// Report pages - using public API
const ReportManagePage = lazy(() => import('@/pages/report').then(m => ({ default: m.ReportManagePage })));
const ReportFactoryPage = lazy(() => import('@/pages/report').then(m => ({ default: m.ReportFactoryPage })));
const LedgerBookPage = lazy(() => import('@/pages/report').then(m => ({ default: m.LedgerBookPage })));

// Database pages - using public API
const UploadDatabasePage = lazy(() => import('@/pages/database').then(m => ({ default: m.UploadDatabasePage })));
const RecordListPage = lazy(() => import('@/pages/database').then(m => ({ default: m.RecordListPage })));
const DatasetImportPage = lazy(() => import('@/pages/database').then(m => ({ default: m.DatasetImportPage })));
const RecordManagerPage = lazy(() => import('@/pages/database').then(m => ({ default: m.RecordManagerPage })));

// Manual pages - using public API
const GlobalManualSearchPage = lazy(() => import('@/pages/manual').then(m => ({ default: m.GlobalManualSearchPage })));
const ShogunManualListPage = lazy(() => import('@/pages/manual').then(m => ({ default: m.ShogunManualListPage })));
const ManualDetailPage = lazy(() => import('@/pages/manual').then(m => ({ default: m.ManualDetailPage })));
const ManualDetailRouteComponent = lazy(() => import('@/features/manual').then(m => ({ default: m.ManualDetailRoute })));

// Analysis pages - using public API
const CustomerListAnalysisPage = lazy(() => import('@/pages/analysis').then(m => ({ default: m.CustomerListAnalysisPage })));

// Chat pages - using public API
const SolvestNaviPage = lazy(() => import('@/pages/navi').then(m => ({ default: m.SolvestNaviPage })));

// Home pages - using public API
const PortalPage = lazy(() => import('@/pages/home').then(m => ({ default: m.PortalPage })));
const NewsPage = lazy(() => import('@/pages/home').then(m => ({ default: m.NewsPage })));

// Utility pages - using public API
const TokenPreviewPage = lazy(() => import('@/pages/utils').then(m => ({ default: m.TokenPreviewPage })));
const TestPage = lazy(() => import('@/pages/utils').then(m => ({ default: m.TestPage })));

const AppRoutes: React.FC = () => {
    const location = useLocation();
    const state = location.state as { backgroundLocation?: Location } | undefined;

    return (
    <>
    <Suspense fallback={<div style={{padding:16}}><Spin /></div>}>
    <Routes location={state?.backgroundLocation || location}>
        {/* テスト用ルート */}
        <Route path='/test' element={<TestPage />} />

    {/* ポータル(トップ) */}
    <Route path={ROUTER_PATHS.PORTAL} element={<PortalPage />} />

        {/* ダッシュボード */}
        <Route path={ROUTER_PATHS.DASHBOARD_UKEIRE} element={<InboundForecastDashboardPage />} />
        <Route path={ROUTER_PATHS.PRICING} element={<PricingDashboard />} />
        <Route path={ROUTER_PATHS.SALES_TREE} element={<SalesTreePage />} />
        <Route
            path={ROUTER_PATHS.CUSTOMER_LIST}
            element={<CustomerListDashboard />}
        />

        {/* 帳票ページ */}
    {/* /report 直アクセス時は管理ページへ */}
    <Route path='/report' element={<Navigate to={ROUTER_PATHS.REPORT_MANAGE} replace />} />
        <Route path={ROUTER_PATHS.REPORT_MANAGE} element={<ReportManagePage />} />
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactoryPage />} />
        <Route path={ROUTER_PATHS.LEDGER_BOOK} element={<LedgerBookPage />} />

        {/* データ分析 */}
        <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<CustomerListAnalysisPage />}
        />

    {/* チャットボット */}
    <Route path={ROUTER_PATHS.NAVI} element={<SolvestNaviPage />} />

    {/* マニュアル（新） */}
    <Route path='/manuals' element={<GlobalManualSearchPage />} />
    <Route path='/manuals/syogun' element={<ShogunManualListPage />} />
        {/* 単独ページ（正ルート） */}
        <Route path='/manuals/syogun/:id' element={<ManualDetailPage />} />


    {/* データベース関連 */}
        <Route path={ROUTER_PATHS.UPLOAD_PAGE} element={<UploadDatabasePage />} />
        <Route path={ROUTER_PATHS.RECORD_LIST} element={<RecordListPage />} />
        <Route path={ROUTER_PATHS.DATASET_IMPORT} element={<DatasetImportPage />} />
        <Route path={ROUTER_PATHS.RECORD_MANAGER} element={<RecordManagerPage />} />

        {/* トークンプレビュー */}
        <Route
            path={ROUTER_PATHS.TOKEN_PREVIEW}
            element={<TokenPreviewPage />}
        />

    {/* お知らせ */}
    <Route path={ROUTER_PATHS.NEWS} element={<NewsPage />} />
        {/* その他/404 */}
                <Route path='*' element={<div>ページが見つかりません</div>} />
        </Routes>
    </Suspense>

        {/* 背景ロケーションがある場合のみ、モーダルルートをオーバーレイ表示 */}
            {state?.backgroundLocation && (
                <Suspense fallback={null}>
                    <Routes>
                        <Route path='/manuals/syogun/:id' element={<ManualDetailRouteComponent />} />
                    </Routes>
                </Suspense>
            )}
        </>
)};

export default AppRoutes;
