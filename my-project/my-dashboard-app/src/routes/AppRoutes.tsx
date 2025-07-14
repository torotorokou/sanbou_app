import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';

// ✅ ページルータからインポート
import { ROUTER_PATHS } from '@/constants/router';

// ✅ 帳票ページのインポート追加
import ReportFactory from '../pages/report/ReportFactory';
import ReportPage from '../pages/report/ReportPage';
import PricingDashboard from '../pages/PricingDashboard';

// ✅ データ分析ページのインポート
import CustomerListAnalysis from '../pages/analysis/CustomerListAnalysis';

// ✅ チャットボットページのインポート
import PdfChatBot from '../pages/navi/PdfChatBot';

// ✅ マニュアル検索ページのインポート
import ManualSearch from '../pages/ManualSearch';

// ✅ トークンページのインポート
import TokenPreviewPage from '@/pages/TokenPreviewPage';

const AppRoutes: React.FC = () => (
    <Routes>
        <Route
            path='/'
            element={<Navigate to={ROUTER_PATHS.DASHBOARD} replace />}
        />
        {/* ✅ ダッシュボード */}
        <Route
            path={ROUTER_PATHS.DASHBOARD}
            element={<ManagementDashboard />}
        />
        <Route path={ROUTER_PATHS.FACTORY} element={<FactoryDashboard />} />
        <Route path={ROUTER_PATHS.PRICING} element={<PricingDashboard />} />

        {/* ✅ 帳票ページ群 */}
        <Route path={ROUTER_PATHS.REPORT_MANAGE} element={<ReportPage />} />
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactory />} />

        {/* ✅ データ分析ページ */}
        <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<CustomerListAnalysis />}
        />

        {/* ✅ チャットボットページ */}
        <Route path={ROUTER_PATHS.NAVI} element={<PdfChatBot />} />

        {/* マニュアル検索 */}
        <Route path={ROUTER_PATHS.MANUAL_SEARCH} element={<ManualSearch />} />

        {/* ✅ トークンプレビュー */}
        <Route
            path={ROUTER_PATHS.TOKEN_PREVIEW}
            element={<TokenPreviewPage />}
        />

        {/* ✅ その他の帳票ページ */}
        {/* ✅ 404 */}
        <Route path='*' element={<div>ページが見つかりません</div>} />
    </Routes>
);

export default AppRoutes;
