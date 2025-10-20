import React from 'react';
import { ReportBase, ReportHeader } from '@features/report';
import { useReportManager } from '@features/report';
import styles from './ReportPage.module.css';

/**
 * レポート管理ページ - シンプルで保守しやすい設計
 * 
 * 🔄 リファクタリング内容：
 * - 複雑な状態管理をuseReportManagerフックに分離
 * - propsの手動構築を自動化（getReportBaseProps）
 * - 可読性とメンテナンス性を大幅に向上
 * - インラインスタイルをCSS Modulesに移行
 * 
 * 📝 従来のコード行数：~100行 → 現在：~28行（72%削減）
 * 
 * 🎯 責任：
 * - UIの構造とレイアウトのみ
 * - ビジネスロジックはカスタムフック内で管理
 */

const ManagePage: React.FC = () => {
    const reportManager = useReportManager('factory_report');
    const reportBaseProps = reportManager.getReportBaseProps();

    return (
        <div className={styles.pageContainer}>
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
                areRequiredCsvsUploaded={reportManager.areRequiredCsvsUploaded}
                isFinalized={reportManager.isFinalized}
                pageGroup="manage"
            />
            <div className={styles.contentArea}>
                <ReportBase {...reportBaseProps} />
            </div>
        </div>
    );
};

export default ManagePage;
