// src/pages/report/LedgerBookPage.tsx

import React from 'react';
import ReportBase from '../../components/Report/ReportBase';
import ReportHeader from '../../components/Report/common/ReportHeader';
import { useReportManager } from '../../hooks/report';

/**
 * 帳簿専用ページ - 完全な再利用設計
 * 
 * 🎯 設計思想：
 * - 既存のアーキテクチャを100%活用
 * - ゼロからの開発コストを削減
 * - 既存機能（CSV管理、PDF生成、プレビュー等）を継承
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
    const reportBaseProps = reportManager.getReportBaseProps();

    return (
        <>
            <ReportHeader
                reportKey={reportManager.selectedReport}
                onChangeReportKey={reportManager.changeReport}
                currentStep={reportManager.currentStep}
                pageGroup="ledger"
            />
            <ReportBase {...reportBaseProps} />
        </>
    );
};

export default LedgerBookPage;