import React from 'react';
import { Routes, Route, Navigate } from 'react-router-dom';
import ManagementDashboard from '../pages/ManagementDashboard';
import FactoryDashboard from '../pages/FactoryDashboard';

const AppRoutes: React.FC = () => (
    <Routes>
        <Route path="/" element={<Navigate to="/dashboard" replace />} />
        <Route path="/dashboard" element={<ManagementDashboard />} />
        <Route path="/factory" element={<FactoryDashboard />} />
        {/* 他ページも同様に */}
        <Route path="*" element={<div>ページが見つかりません</div>} />
    </Routes>
);

export default AppRoutes;
