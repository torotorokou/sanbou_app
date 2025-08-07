import React from 'react';
import { BaseWorkflowWrapper, useWorkflowState, type BaseInteractiveWorkflowProps } from '../common/BaseWorkflow';
import CsvUploadService from '../services/CsvUploadService';
import './BlockUnitPriceWorkflow.css';

// ブロック単価ワークフロー専用のプロパティ
interface BlockUnitPriceWorkflowProps extends BaseInteractiveWorkflowProps {
    csvFile?: File;
}

interface TransporterSelectionTableProps {
    transporters: Array<{ id: string; name: string; description: string }>;
    onSelectionChange: (selectedIds: string[]) => void;
    selectedTransporters: string[];
}

const TransporterSelectionTable: React.FC<TransporterSelectionTableProps> = ({
    transporters,
    onSelectionChange,
    selectedTransporters
}) => {
    const handleSelectionChange = (transporterId: string, checked: boolean) => {
        const newSelection = checked
            ? [...selectedTransporters, transporterId]
            : selectedTransporters.filter(id => id !== transporterId);
        onSelectionChange(newSelection);
    };

    return (
        <div className="transporter-selection-table">
            <h3>運搬業者を選択してください</h3>
            <div className="transporters-list">
                {transporters.map(transporter => (
                    <label key={transporter.id} className="transporter-item">
                        <input
                            type="checkbox"
                            checked={selectedTransporters.includes(transporter.id)}
                            onChange={(e) => handleSelectionChange(transporter.id, e.target.checked)}
                        />
                        <span className="transporter-name">{transporter.name}</span>
                        <span className="transporter-description">{transporter.description}</span>
                    </label>
                ))}
            </div>
            <div className="selection-progress">
                選択済み: {selectedTransporters.length} / {transporters.length}
            </div>
        </div>
    );
};

const BlockUnitPriceWorkflowRefactored: React.FC<BlockUnitPriceWorkflowProps> = ({
    visible = false,
    onClose,
    onComplete,
    csvFile,
    config
}) => {
    const { state, nextStep, prevStep, reset, setLoading, setError } = useWorkflowState(0);
    const [selectedTransporters, setSelectedTransporters] = React.useState<string[]>([]);

    // サンプル運搬業者データ
    const transporters = [
        { id: 'transporter1', name: '運搬業者A', description: '地域配送専門' },
        { id: 'transporter2', name: '運搬業者B', description: '長距離輸送対応' },
        { id: 'transporter3', name: '運搬業者C', description: '冷蔵輸送可能' }
    ];

    const maxSteps = 3;
    const isAllSelected = selectedTransporters.length === transporters.length;

    const handleNext = async () => {
        if (state.currentStep === 0 && !isAllSelected) {
            return; // すべて選択されていない場合は進まない
        }

        if (state.currentStep === maxSteps - 1) {
            // 最後のステップで完了処理
            try {
                setLoading(true);
                await CsvUploadService.uploadAndStart(
                    'block_unit_price',
                    csvFile ? { csv: csvFile } : {},
                    {
                        onStart: () => console.log('処理開始'),
                        onSuccess: (data) => {
                            console.log('処理成功:', data);
                            onComplete?.(data);
                        },
                        onError: (error) => {
                            console.error('処理エラー:', error);
                            throw new Error(error);
                        },
                        onComplete: () => console.log('処理完了')
                    }
                );
                onClose?.();
            } catch (error) {
                console.error('処理エラー:', error);
                setError('処理中にエラーが発生しました');
                // エラー時はステップ1に戻る
                reset();
                setSelectedTransporters([]);
            } finally {
                setLoading(false);
            }
        } else {
            nextStep();
        }
    };

    const handleReset = () => {
        reset();
        setSelectedTransporters([]);
    };

    const renderStepContent = () => {
        switch (state.currentStep) {
            case 0:
                return (
                    <TransporterSelectionTable
                        transporters={transporters}
                        onSelectionChange={setSelectedTransporters}
                        selectedTransporters={selectedTransporters}
                    />
                );
            case 1:
                return (
                    <div className="data-confirmation">
                        <h3>選択内容の確認</h3>
                        <p>選択された運搬業者:</p>
                        <ul>
                            {selectedTransporters.map(id => {
                                const transporter = transporters.find(t => t.id === id);
                                return transporter ? <li key={id}>{transporter.name}</li> : null;
                            })}
                        </ul>
                        {csvFile && <p>アップロードファイル: {csvFile.name}</p>}
                    </div>
                );
            case 2:
                return (
                    <div className="completion-step">
                        <h3>処理完了</h3>
                        <p>ブロック単価レポートの処理が完了しました。</p>
                        {state.error && (
                            <div className="error-message">
                                エラー: {state.error}
                            </div>
                        )}
                    </div>
                );
            default:
                return null;
        }
    };

    const defaultConfig = {
        title: 'ブロック単価ワークフロー',
        steps: [
            { title: '運搬業者選択', content: '運搬業者を選択してください' },
            { title: 'データ確認', content: 'データを確認しています' },
            { title: '完了', content: '処理が完了しました' }
        ]
    };

    return (
        <BaseWorkflowWrapper
            visible={visible}
            onClose={onClose}
            config={{ ...defaultConfig, ...config }}
            currentStep={state.currentStep}
            maxSteps={maxSteps}
            onNext={handleNext}
            onPrev={prevStep}
            onReset={handleReset}
            canProceed={state.currentStep !== 0 || isAllSelected}
            isLoading={state.isLoading}
        >
            {renderStepContent()}
        </BaseWorkflowWrapper>
    );
};

export default BlockUnitPriceWorkflowRefactored;
