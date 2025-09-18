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
import ManualModal from '@/pages/manual/ManualModal';
import ManualPage from '@/pages/manual/ManualPage';
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
import Page from '@/layouts/Page';

const AppRoutes: React.FC = () => {
    const location = useLocation();
    const state = location.state as { backgroundLocation?: Location } | undefined;

    return (
    <>
    <Routes location={state?.backgroundLocation || location}>
        {/* テスト用ルート */}
        <Route path='/test' element={<Page><TestPage /></Page>} />

    {/* ポータル(トップ) */}
    <Route path={ROUTER_PATHS.PORTAL} element={<Page><PortalPage /></Page>} />

        {/* ダッシュボード */}
        <Route
            path={ROUTER_PATHS.DASHBOARD}
            element={<Page><ManagementDashboard /></Page>}
        />
        <Route path={ROUTER_PATHS.FACTORY} element={<Page><FactoryDashboard /></Page>} />
        <Route path={ROUTER_PATHS.PRICING} element={<Page><PricingDashboard /></Page>} />
        <Route
            path={ROUTER_PATHS.CUSTOMER_LIST}
            element={<Page><CustomerListDashboard /></Page>}
        />

        {/* 帳票ページ */}
    {/* /report 直アクセス時は管理ページへ */}
    <Route path='/report' element={<Navigate to={ROUTER_PATHS.REPORT_MANAGE} replace />} />
        <Route path={ROUTER_PATHS.REPORT_MANAGE} element={<Page><ReportManagePage /></Page>} />
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<Page><ReportFactory /></Page>} />
        <Route path={ROUTER_PATHS.LEDGER_BOOK} element={<Page><LedgerBookPage /></Page>} />

        {/* データ分析 */}
        <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<Page><CustomerListAnalysis /></Page>}
        />

        {/* チャットボット */}
    <Route path={ROUTER_PATHS.NAVI} element={<Page><PdfChatBot /></Page>} />

    {/* マニュアル（新） */}
    <Route path='/manuals' element={<Page><GlobalManualSearch /></Page>} />
    <Route path='/manuals/syogun' element={<Page><ShogunManualList /></Page>} />
        {/* 単独ページ（正ルート） */}
        <Route path='/manuals/syogun/:id' element={<Page><ManualPage /></Page>} />


        {/* データベース関連 */}
    <Route path={ROUTER_PATHS.UPLOAD_PAGE} element={<Page><UploadPage /></Page>} />
    <Route path={ROUTER_PATHS.RECORD_LIST} element={<Page><RecordListPage /></Page>} />

        {/* トークンプレビュー */}
        <Route
            path={ROUTER_PATHS.TOKEN_PREVIEW}
            element={<Page><TokenPreviewPage /></Page>}
        />

    {/* お知らせ */}
    <Route path={ROUTER_PATHS.NEWS} element={<Page><NewsPage /></Page>} />
        {/* その他/404 */}
                <Route path='*' element={<Page><div>ページが見つかりません</div></Page>} />
        </Routes>

        {/* 背景ロケーションがある場合のみ、モーダルルートをオーバーレイ表示 */}
            {state?.backgroundLocation && (
            <Routes>
                <Route path='/manuals/syogun/:id' element={<Page><ManualModal /></Page>} />
            </Routes>
        )}
        </>
)};

export default AppRoutes;
