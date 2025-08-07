import React from 'react';
import InteractiveReportBase from '../base/InteractiveReportBase';
import BlockUnitPriceWorkflow from '../individual_process/BlockUnitPriceWorkflow';
import { WorkflowProvider } from '../context/WorkflowContext';
import type { ReportBaseProps } from '../../../types/reportBase';
import type { ReportKey } from '../../../constants/reportConfig/managementReportConfig';

/**
 * ブロック単価レポート統合コンポーネント
 * 
 * 🎯 設計目標:
 * - InteractiveReportBaseとBlockUnitPriceWorkflowの統合
 * - WorkflowContextの提供
 * - 保守性の高いアーキテクチャ
 * 
 * 🛡️ 安全性機能:
 * - モーダルの途中閉じ禁止
 * - エラー時の適切な復旧処理
 * - ステップ間の状態整合性保証
 */
const BlockUnitPriceReport: React.FC<ReportBaseProps> = (props) => {
    const debugMode = React.useMemo(() =>
        typeof window !== 'undefined' && window.location.hostname === 'localhost'
        , []);

    // ワークフローコンポーネントのラッパー
    const WorkflowComponent = React.useCallback(({ currentStep, reportKey }: { currentStep: number; reportKey: ReportKey }) => {
        // eslint-disable-next-line react/prop-types
        return (
            <BlockUnitPriceWorkflow
                currentStep={currentStep}
                reportKey={reportKey}
                step={props.step}
                file={props.file}
                preview={props.preview}
                modal={props.modal}
                finalized={props.finalized}
                loading={props.loading}
            />
        );
    }, [props]);

    // 初期化処理
    const handleInitialize = React.useCallback(() => {
        console.log('[BlockUnitPriceReport] Initializing block unit price workflow');
    }, []);

    // 完了処理
    const handleComplete = React.useCallback((result: unknown) => {
        console.log('[BlockUnitPriceReport] Workflow completed successfully', result);
    }, []);

    return (
        <WorkflowProvider>
            <InteractiveReportBase
                {...props}
                WorkflowComponent={WorkflowComponent}
                onInitialize={handleInitialize}
                onComplete={handleComplete}
                debugMode={debugMode}
            />
        </WorkflowProvider>
    );
};

export default BlockUnitPriceReport;
