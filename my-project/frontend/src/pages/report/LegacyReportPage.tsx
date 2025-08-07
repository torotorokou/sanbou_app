// /app/src/pages/report/LegacyReportPage.tsx
import React from 'react';
import { GenericReportPage } from './GenericReportPage';
import { legacyReportConfigPackage } from '../../constants/reportConfig/legacyReportConfigSet';

/**
 * 既存ReportFactory.tsx統合ページ
 * 
 * 汎用化されたシステムを使用して、
 * 既存のReportFactory.tsxロジックを統合した例
 */
const LegacyReportPage: React.FC = () => {
    return (
        <GenericReportPage
            config={legacyReportConfigPackage}
            title="レガシーレポートシステム（統合版）"
            description="既存のReportFactory.tsxの処理ロジックを新しい汎用システムに統合した例です。出荷一覧、ヤード一覧、受入一覧のCSVファイルから工場レポートを生成できます。"
        />
    );
};

export default LegacyReportPage;
