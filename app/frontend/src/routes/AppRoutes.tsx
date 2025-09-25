import React, { Suspense, lazy } from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { Spin } from 'antd';

// ルート定数
import { ROUTER_PATHS } from '@/constants/router';

// 軽量/コアはそのまま、重いページを lazy 化
const ManagementDashboard = lazy(() => import('../pages/dashboard/ManagementDashboard'));
const FactoryDashboard = lazy(() => import('../pages/dashboard/FactoryDashboard'));
const PricingDashboard = lazy(() => import('../pages/dashboard/PricingDashboard'));
const CustomerListDashboard = lazy(() => import('../pages/dashboard/CustomerListDashboard'));
const SalesTreePage = lazy(() => import('../pages/dashboard/SalesTreePage'));

const ReportFactory = lazy(() => import('../pages/report/ReportFactory'));
const ReportManagePage = lazy(() => import('../pages/report/ReportManagePage'));
const LedgerBookPage = lazy(() => import('../pages/report/LedgerBookPage'));

const CustomerListAnalysis = lazy(() => import('../pages/analysis/CustomerListAnalysis'));

const SolvestNavi = lazy(() => import('../pages/navi/SolvestNavi'));

const ManualModal = lazy(() => import('@/pages/manual/ManualModal'));
const ManualPage = lazy(() => import('@/pages/manual/ManualPage'));
const GlobalManualSearch = lazy(() => import('@/pages/manual/GlobalManualSearch'));
const ShogunManualList = lazy(() => import('@/pages/manual/ShogunManualList'));

const UploadPage = lazy(() => import('../pages/database/UploadDatabasePage'));
const RecordListPage = lazy(() => import('../pages/database/RecordListPage'));

const TokenPreviewPage = lazy(() => import('@/pages/utils/TokenPreviewPage'));
const TestPage = lazy(() => import('@/pages/utils/TestPage'));
const PortalPage = lazy(() => import('@/pages/home/PortalPage'));
const NewsPage = lazy(() => import('@/pages/home/NewsPage'));

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
        <Route
            path={ROUTER_PATHS.DASHBOARD}
            element={<ManagementDashboard />}
        />
        <Route path={ROUTER_PATHS.FACTORY} element={<FactoryDashboard />} />
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
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactory />} />
        <Route path={ROUTER_PATHS.LEDGER_BOOK} element={<LedgerBookPage />} />

        {/* データ分析 */}
        <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<CustomerListAnalysis />}
        />

    {/* チャットボット */}
    <Route path={ROUTER_PATHS.NAVI} element={<SolvestNavi />} />

    {/* マニュアル（新） */}
    <Route path='/manuals' element={<GlobalManualSearch />} />
    <Route path='/manuals/syogun' element={<ShogunManualList />} />
        {/* 単独ページ（正ルート） */}
        <Route path='/manuals/syogun/:id' element={<ManualPage />} />


        {/* データベース関連 */}
        <Route path={ROUTER_PATHS.UPLOAD_PAGE} element={<UploadPage />} />
        <Route path={ROUTER_PATHS.RECORD_LIST} element={<RecordListPage />} />

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
                        <Route path='/manuals/syogun/:id' element={<ManualModal />} />
                    </Routes>
                </Suspense>
            )}
        </>
)};

export default AppRoutes;
