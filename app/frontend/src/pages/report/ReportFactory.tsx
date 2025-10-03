// src/pages/report/ReportFactory.tsx

import React from 'react';
import ReportBase from '../../components/Report/ReportBase';
import ReportHeader from '../../components/Report/common/ReportHeader';
import { useReportManager } from '../../hooks/report';

/**
 * 工場帳簿ページ - 新しい分割アーキテクチャ対応
 * 
 * 🔄 リファクタリング内容：
 * - 古い手動実装（~216行）から新しいアーキテクチャに移行
 * - 複雑な状態管理をuseReportManagerフックに分離
 * - 工場関連の帳票のみを表示するよう設定
 * 
 * 📝 コード行数：~216行 → ~35行（84%削減）
 * 
 * 🎯 責任：
 * - 工場帳票に特化したUIレイアウト
 * - ビジネスロジックはカスタムフック内で管理
 */

const ReportFactory: React.FC = () => {
    const reportManager = useReportManager('factory_report2');
    const reportBaseProps = reportManager.getReportBaseProps();

    return (
        <div
            style={{
                height: 'calc(100dvh - (var(--page-padding, 0px) * 2))',
                padding: 'var(--page-padding, 16px)',
                display: 'flex',
                flexDirection: 'column',
                overflow: 'hidden',
                boxSizing: 'border-box',
                scrollbarGutter: 'stable both-edges'
            }}
        >
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
                pageGroup="factory"
            />
            <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                <ReportBase {...reportBaseProps} />
            </div>
        </div>
    );
};

export default ReportFactory;
