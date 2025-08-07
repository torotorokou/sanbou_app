import React, { useState, useCallback, useEffect } from 'react';
import type { ReportBaseProps } from '../../types/reportBase';
import { interactiveModalStepsMap } from '../../constants/reportConfig/managementReportConfig';
import InteractiveWorkflowFactory, { registerDefaultWorkflows } from './individual_process/InteractiveWorkflowFactory';

// 拡張されたprops型（getValidationResultを含む）
interface ExtendedReportBaseProps extends ReportBaseProps {
    getValidationResult?: (label: string) => 'valid' | 'invalid' | 'unknown';
}

/**
 * インタラクティブレポートベースコンポーネント
 * ユーザーとの対話が必要なレポート生成のための汎用ベース
 * 
 * 🎯 責任：
 * - インタラクティブワークフローの基本構造提供
 * - ファクトリーパターンによる各レポートタイプ専用コンポーネントへの委譲
 * - 共通的なエラーハンドリングと状態管理
 */
const InteractiveReportBase: React.FC<ExtendedReportBaseProps> = (props) => {
    const { reportKey } = props;

    // 基本状態
    const [error, setError] = useState<string | null>(null);
    const [workflowStarted, setWorkflowStarted] = useState<boolean>(false);
    const [WorkflowComponent, setWorkflowComponent] = useState<React.ComponentType<any> | null>(null);
    const [loading, setLoading] = useState(true);

    // ステップ設定を取得
    const stepConfigs = interactiveModalStepsMap[reportKey] || [];

    console.log('[InteractiveReportBase] reportKey:', reportKey, 'workflowStarted:', workflowStarted);

    // ワークフローファクトリーを初期化
    useEffect(() => {
        const initializeWorkflow = () => {
            try {
                // デフォルトワークフローを登録
                registerDefaultWorkflows();

                // 対応するワークフローコンポーネントを取得
                const component = InteractiveWorkflowFactory.getWorkflowComponent(reportKey);

                if (!component) {
                    throw new Error(`Workflow component not found for report: ${reportKey}`);
                }

                setWorkflowComponent(() => component);
                setLoading(false);
            } catch (err) {
                console.error(`Failed to initialize workflow for ${reportKey}:`, err);
                setError(`ワークフローの初期化に失敗しました: ${reportKey}`);
                setLoading(false);
            }
        };

        initializeWorkflow();
    }, [reportKey]);

    // ワークフロー開始
    const handleStartWorkflow = useCallback(() => {
        setWorkflowStarted(true);
        setError(null);
    }, []);

    // エラーリセット
    const handleErrorReset = useCallback(() => {
        setError(null);
        setWorkflowStarted(false);
    }, []);

    // レポートタイプ別のワークフローコンポーネントをレンダリング
    const renderWorkflowComponent = useCallback(() => {
        if (loading) {
            return <div>ワークフローを読み込み中...</div>;
        }

        if (!WorkflowComponent) {
            return (
                <div className="unsupported-report">
                    <h3>サポートされていないレポートタイプ</h3>
                    <p>レポートタイプ「{reportKey}」はインタラクティブワークフローに対応していません。</p>
                    <p>設定ファイルでレポートタイプを「auto」に変更するか、専用ワークフローを実装してください。</p>
                </div>
            );
        }

        return <WorkflowComponent {...props} />;
    }, [loading, WorkflowComponent, reportKey, props]);

    // ファイルアップロード後、自動的にワークフロー開始
    useEffect(() => {
        const hasRequiredFiles = Object.keys(props.file.files).length > 0;
        if (hasRequiredFiles && !workflowStarted && !error) {
            handleStartWorkflow();
        }
    }, [props.file.files, workflowStarted, error, handleStartWorkflow]);

    // エラー表示
    if (error) {
        return (
            <div className="interactive-report-error">
                <div className="error-container">
                    <h3>エラーが発生しました</h3>
                    <p>{error}</p>
                    <button onClick={handleErrorReset} className="btn-secondary">
                        やり直す
                    </button>
                </div>
            </div>
        );
    }

    // ワークフロー開始前
    if (!workflowStarted) {
        return (
            <div className="interactive-report-waiting">
                <div className="waiting-container">
                    <h3>インタラクティブレポート準備中</h3>
                    <p>必要なファイルがアップロードされるまでお待ちください。</p>
                    {Object.keys(props.file.files).length > 0 && (
                        <button onClick={handleStartWorkflow} className="btn-primary">
                            ワークフローを開始
                        </button>
                    )}
                </div>
            </div>
        );
    }

    return (
        <div className="interactive-report-base">
            {/* 共通ヘッダー */}
            <div className="report-header">
                <h1>インタラクティブレポート生成</h1>
                <div className="report-info">
                    <span className="report-type">{reportKey}</span>
                    {stepConfigs.length > 0 && (
                        <span className="step-count">{stepConfigs.length} ステップ</span>
                    )}
                </div>
            </div>

            {/* ワークフロー固有のコンテンツ */}
            <div className="workflow-container">
                {renderWorkflowComponent()}
            </div>
        </div>
    );
};

export default InteractiveReportBase;
