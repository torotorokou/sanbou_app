import React from 'react';
import { Routes, Route, Navigate, useLocation } from 'react-router-dom';

// ルート定数
import { ROUTER_PATHS } from '@/constants/router';

// ページコンポーネント
// ダッシュボード
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';
import PricingDashboard from '../pages/PricingDashboard';
import CustomerListDashboard from '../pages/CustomerListDashboard.tsx';

// 帳票ページ
import ReportFactory from '../pages/report/ReportFactory';
import ReportManagePage from '../pages/report/ReportManagePage.tsx';
import LedgerBookPage from '../pages/LedgerBookPage';

// データ分析
import CustomerListAnalysis from '../pages/analysis/CustomerListAnalysis.tsx';

// チャットボット
import PdfChatBot from '../pages/navi/PdfChatBot';

// マニュアル検索
import ManualModal from '@/pages/manuals/ManualModal';
import ManualPage from '@/pages/manuals/ManualPage';
import GlobalManualSearch from '@/pages/manual/GlobalManualSearch';
import ShogunManualList from '@/pages/manual/ShogunManualList';

// データベース関連
import UploadPage from '../pages/database/UploadDatabasePage';
import RecordListPage from '../pages/database/RecordListPage';

// トークンプレビュー
import TokenPreviewPage from '@/pages/TokenPreviewPage';
import TestPage from '@/pages/TestPage';
import PortalPage from '@/pages/portal/PortalPage';
import NewsPage from '@/pages/NewsPage';

const AppRoutes: React.FC = () => {
    const location = useLocation();
    const state = location.state as { backgroundLocation?: Location } | undefined;

    return (
    <>
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
        <Route path={ROUTER_PATHS.NAVI} element={<PdfChatBot />} />

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

        {/* 背景ロケーションがある場合のみ、モーダルルートをオーバーレイ表示 */}
            {state?.backgroundLocation && (
            <Routes>
                <Route path='/manuals/syogun/:id' element={<ManualModal />} />
            </Routes>
        )}
        </>
)};

export default AppRoutes;
