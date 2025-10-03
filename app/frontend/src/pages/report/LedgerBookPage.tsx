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
                pageGroup="ledger"
            />
            <div style={{ flex: 1, minHeight: 0, overflow: 'hidden' }}>
                <ReportBase {...reportBaseProps} />
            </div>
        </div>
    );
};

export default LedgerBookPage;