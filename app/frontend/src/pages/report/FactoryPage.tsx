import React from 'react';
import { ReportBase, ReportHeader } from '@features/report';
import { useReportManager } from '@features/report';
import styles from './ReportPage.module.css';

/**
 * 工場帳簿ページ - 新しい分割アーキテクチャ対応
 * 
 * 🔄 リファクタリング内容：
 * - 古い手動実装（~216行）から新しいアーキテクチャに移行
 * - 複雑な状態管理をuseReportManagerフックに分離
 * - 工場関連の帳票のみを表示するよう設定
 * - インラインスタイルをCSS Modulesに移行
 * 
 * 📝 コード行数：~216行 → ~28行（87%削減）
 * 
 * 🎯 責任：
 * - 工場帳票に特化したUIレイアウト
 * - ビジネスロジックはカスタムフック内で管理
 */

const FactoryPage: React.FC = () => {
    const reportManager = useReportManager('factory_report2');
    const reportBaseProps = reportManager.getReportBaseProps();

    return (
        <div className={styles.pageContainer}>
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
                areRequiredCsvsUploaded={reportManager.areRequiredCsvsUploaded}
                isFinalized={reportManager.isFinalized}
                pageGroup="factory"
            />
            <div className={styles.contentArea}>
                <ReportBase {...reportBaseProps} />
            </div>
        </div>
    );
};

export default FactoryPage;
