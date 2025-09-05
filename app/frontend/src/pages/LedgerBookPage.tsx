// src/pages/LedgerBookPage.tsx

import React from 'react';
import ReportBase from '../components/Report/ReportBase';
import ReportHeader from '../components/Report/common/ReportHeader';
import { useReportManager } from '../hooks/report';

/**
 * 帳簿ページ - 既存のコンポーネントを完全再利用
 * 
 * 🔄 再利用設計の利点：
 * - 既存のReportBaseとuseReportManagerを100%再利用
 * - 新機能追加時のコード重複を完全に排除
 * - 一貫したUX/UIを自動的に継承
 * - メンテナンス性とコード品質を保持
 * 
 * 📝 実装コード量：わずか~30行（95%のコードを再利用）
 * 
 * 🎯 責任：
 * - 帳簿に特化したレポートタイプの指定のみ
 * - その他すべての機能は既存コンポーネントに委譲
 */

const LedgerBookPage: React.FC = () => {
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
