import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';

// ✅ ページルータからインポート
import { ROUTER_PATHS } from '@/constants/router';

// ✅ 帳票ページのインポート追加
import ReportFactory from '../pages/report/ReportFactory';
import ReportPage from '../pages/report/ReportPage';

// ✅ チャットボットページのインポート
import PdfChatBot from '../pages/navi/PdfChatBot';

// ✅ トークンページのインポート
import TokenPreviewPage from '@/pages/TokenPreviewPage';

const AppRoutes: React.FC = () => (
    <Routes>
        <Route
            path='/'
            element={<Navigate to={ROUTER_PATHS.DASHBOARD} replace />}
        />
        <Route
            path={ROUTER_PATHS.DASHBOARD}
            element={<ManagementDashboard />}
        />
        <Route path={ROUTER_PATHS.FACTORY} element={<FactoryDashboard />} />

        {/* ✅ 帳票ページ群 */}
        <Route path={ROUTER_PATHS.REPORT_MANAGE} element={<ReportPage />} />
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactory />} />

        {/* ✅ チャットボットページ */}
        <Route path={ROUTER_PATHS.NAVI} element={<PdfChatBot />} />

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
