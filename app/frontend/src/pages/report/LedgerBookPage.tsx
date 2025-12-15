import React from 'react';
import { ReportBase, ReportHeader } from '@features/report';
import { useReportManager } from '@features/report';
import styles from './ReportPage.module.css';

/**
 * 帳簿専用ページ - 完全な再利用設計
 * 
 * 🎯 設計思想：
 * - 既存のアーキテクチャを100%活用
 * - ゼロからの開発コストを削減
 * - 既存機能（CSV管理、PDF生成、プレビュー等）を継承
 * - インラインスタイルをCSS Modulesに移行
 * 
 * 💡 拡張ポイント：
 * - 帳簿特有のカスタムロジックが必要な場合は、
 *   useReportManagerのラッパーフックを作成可能
 * - 帳簿専用のヘッダーやフッターが必要な場合は、
 *   ReportHeaderを拡張またはカスタムコンポーネント作成
 */

const LedgerBookPage: React.FC = () => {
    // 帳簿専用の初期設定でuseReportManagerを使用
    const reportManager = useReportManager('ledger_book');
    // useMemoでメモ化されたprops（関数ではなくオブジェクト）
    const reportBaseProps = reportManager.getReportBaseProps;

    return (
        <div className={styles.pageContainer}>
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
                areRequiredCsvsUploaded={reportManager.areRequiredCsvsUploaded}
                isFinalized={reportManager.isFinalized}
                pageGroup="ledger"
            />
            <div className={styles.contentArea}>
                <ReportBase {...reportBaseProps} />
            </div>
        </div>
    );
};

export default LedgerBookPage;