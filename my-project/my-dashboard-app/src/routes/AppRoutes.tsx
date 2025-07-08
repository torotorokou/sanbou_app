import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';

// ✅ 帳票ページのインポート追加
import ReportFactory from '../pages/report/ReportFactory';
import ReportBalance from '../pages/report/ReportBalance';
import ReportAverage from '../pages/report/ReportAverage';
import ReportPrice from '../pages/report/ReportPrice';
import ReportAdminSheet from '../pages/report/ReportAdminSheet';
import ReportPage from '../pages/report/ReportPage'; // ← 追加

// ✅ チャットボットページのインポート
import PdfChatBot from '../pages/navi/PdfChatBot';

// ✅ トークンページのインポート
import TokenPreviewPage from '@/pages/TokenPreviewPage';

const AppRoutes: React.FC = () => (
    <Routes>
        <Route path='/' element={<Navigate to='/dashboard' replace />} />
        <Route path='/dashboard' element={<ManagementDashboard />} />
        <Route path='/factory' element={<FactoryDashboard />} />

        {/* ✅ 帳票ページ群 */}
        <Route path='/report/manage' element={<ReportPage />} />
        {/* <Route path='/report/daily' element={<ReportFactory />} />
        <Route path='/report/balance' element={<ReportBalance />} />
        <Route path='/report/average' element={<ReportAverage />} />
        <Route path='/report/price' element={<ReportPrice />} />
        <Route path='/report/adminsheet' element={<ReportAdminSheet />} /> */}

        {/* ✅ チャットボットページ */}
        <Route path='/navi' element={<PdfChatBot />} />
        {/* ✅ トークンプレビュー */}
        <Route path='/token-preview' element={<TokenPreviewPage />} />
        {/* ✅ 404 */}
        <Route path='*' element={<div>ページが見つかりません</div>} />
    </Routes>
);

export default AppRoutes;
