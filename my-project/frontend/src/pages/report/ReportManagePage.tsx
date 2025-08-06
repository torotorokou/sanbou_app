// src/pages/report/ReportPage.tsx

import React from 'react';
import ReportBase from '../../components/Report/ReportBase';
import ReportHeader from '../../components/Report/common/ReportHeader';
// import ResponsiveDebugInfo from '../../components/debug/ResponsiveDebugInfo';
import { useReportManager } from '../../hooks/report';

/**
 * レポートページ - シンプルで保守しやすい設計
 * 
 * 🔄 リファクタリング内容：
 * - 複雑な状態管理をuseReportManagerフックに分離
 * - propsの手動構築を自動化（getReportBaseProps）
 * - 可読性とメンテナンス性を大幅に向上
 * 
 * 📝 従来のコード行数：~100行 → 現在：~25行（75%削減）
 * 
 * 🎯 責任：
 * - UIの構造とレイアウトのみ
 * - ビジネスロジックはカスタムフック内で管理
 */

const ReportManagePage: React.FC = () => {
    const reportManager = useReportManager('factory_report');
    const reportBaseProps = reportManager.getReportBaseProps();

    return (
        <>
            {/* <ResponsiveDebugInfo /> */}
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
            />
            <ReportBase {...reportBaseProps} />
        </>
    );
};

export default ReportManagePage;
