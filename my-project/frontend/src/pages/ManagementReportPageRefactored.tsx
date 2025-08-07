// /app/src/pages/ManagementReportPageRefactored.tsx
import React from 'react';
import { GenericReportPage } from './report/GenericReportPage';
import { managementReportConfigPackage } from '../constants/reportConfig/managementReportConfigSet';

/**
 * 管理系帳票ページ（リファクタリング後）
 * 
 * 汎用化されたGenericReportPageを使用して、
 * 管理系帳票専用の設定パッケージを注入
 */
const ManagementReportPageRefactored: React.FC = () => {
    return (
        <GenericReportPage
            config={managementReportConfigPackage}
            title="管理系帳票作成システム"
            description="工場日報、収支表、管理票など、管理部門向けの各種帳票を生成できます。"
        />
    );
};

export default ManagementReportPageRefactored;
