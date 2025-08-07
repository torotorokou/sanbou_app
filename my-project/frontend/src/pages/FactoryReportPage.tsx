// /app/src/pages/FactoryReportPage.tsx
import React from 'react';
import { GenericReportPage } from './report/GenericReportPage';
import { factoryReportConfigPackage } from '../constants/reportConfig/factoryReportConfigSet';

/**
 * 工場系帳票ページ（新規作成例）
 * 
 * 汎用化されたシステムを使用して、
 * 新しい帳票タイプを簡単に追加した例
 */
const FactoryReportPage: React.FC = () => {
    return (
        <GenericReportPage
            config={factoryReportConfigPackage}
            title="工場系帳票作成システム"
            description="生産実績、品質管理、設備保守など、工場運営に必要な各種帳票を生成できます。"
        />
    );
};

export default FactoryReportPage;
