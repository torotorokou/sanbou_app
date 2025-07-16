import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';

// ルート定数
import { ROUTER_PATHS } from '@/constants/router';

// ページコンポーネント
// ダッシュボード
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';
import PricingDashboard from '../pages/PricingDashboard';

// 帳票ページ
import ReportFactory from '../pages/report/ReportFactory';
import ReportPage from '../pages/report/ReportPage';

// データ分析
import CustomerListAnalysis from '../pages/analysis/CustomerListAnalysis.tsx';

// チャットボット
import PdfChatBot from '../pages/navi/PdfChatBot';

// マニュアル検索
import ManualSearch from '../pages/ManualSearch';

// データベース関連
import UploadPage from '../pages/database/UploadPage';
import RecordListPage from '../pages/database/RecordListPage';

// トークンプレビュー
import TokenPreviewPage from '@/pages/TokenPreviewPage';

const AppRoutes: React.FC = () => (
    <Routes>
        {/* ルートリダイレクト */}
        <Route
            path='/'
            element={<Navigate to={ROUTER_PATHS.DASHBOARD} replace />}
        />

        {/* ダッシュボード */}
        <Route
            path={ROUTER_PATHS.DASHBOARD}
            element={<ManagementDashboard />}
        />
        <Route path={ROUTER_PATHS.FACTORY} element={<FactoryDashboard />} />
        <Route path={ROUTER_PATHS.PRICING} element={<PricingDashboard />} />

        {/* 帳票ページ */}
        <Route path={ROUTER_PATHS.REPORT_MANAGE} element={<ReportPage />} />
        <Route path={ROUTER_PATHS.REPORT_FACTORY} element={<ReportFactory />} />

        {/* データ分析 */}
        <Route
            path={ROUTER_PATHS.ANALYSIS_CUSTOMERLIST}
            element={<CustomerListAnalysis />}
        />

        {/* チャットボット */}
        <Route path={ROUTER_PATHS.NAVI} element={<PdfChatBot />} />

        {/* マニュアル検索 */}
        <Route path={ROUTER_PATHS.MANUAL_SEARCH} element={<ManualSearch />} />

        {/* データベース関連 */}
        <Route path={ROUTER_PATHS.UPLOAD_PAGE} element={<UploadPage />} />
        <Route path={ROUTER_PATHS.RECORD_LIST} element={<RecordListPage />} />

        {/* トークンプレビュー */}
        <Route
            path={ROUTER_PATHS.TOKEN_PREVIEW}
            element={<TokenPreviewPage />}
        />

        {/* その他/404 */}
        <Route path='*' element={<div>ページが見つかりません</div>} />
    </Routes>
);

export default AppRoutes;
