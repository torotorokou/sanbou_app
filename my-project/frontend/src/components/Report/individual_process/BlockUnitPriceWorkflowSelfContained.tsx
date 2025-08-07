import React from 'react';
import { Modal, Button, Steps } from 'antd';
import CsvUploadService from '../services/CsvUploadService';
import './BlockUnitPriceWorkflow.css';

// 自己完結型インタラクティブワークフローのprops
interface SelfContainedWorkflowProps {
    visible?: boolean;
    onClose?: () => void;
    onComplete?: (result: unknown) => void;
    csvFile?: File;
    config?: {
        title?: string;
        steps?: Array<{ title: string; content: string }>;
    };
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

const BlockUnitPriceWorkflowSelfContained: React.FC<SelfContainedWorkflowProps> = ({
    visible = false,
    onClose,
    onComplete,
    csvFile,
    config
}) => {
    const [currentStep, setCurrentStep] = React.useState(0);
    const [selectedTransporters, setSelectedTransporters] = React.useState<string[]>([]);
    const [isLoading, setIsLoading] = React.useState(false);

    // サンプル運搬業者データ
    const transporters = [
        { id: 'transporter1', name: '運搬業者A', description: '地域配送専門' },
        { id: 'transporter2', name: '運搬業者B', description: '長距離輸送対応' },
        { id: 'transporter3', name: '運搬業者C', description: '冷蔵輸送可能' }
    ];

    const steps = config?.steps || [
        { title: '運搬業者選択', content: '運搬業者を選択してください' },
        { title: 'データ確認', content: 'データを確認しています' },
        { title: '完了', content: '処理が完了しました' }
    ];

    const isAllSelected = selectedTransporters.length === transporters.length;

    const handleNext = async () => {
        if (currentStep === 0 && !isAllSelected) {
            return; // すべて選択されていない場合は進まない
        }

        if (currentStep === steps.length - 1) {
            // 最後のステップで完了処理
            try {
                setIsLoading(true);
                // CsvUploadServiceの適切なメソッドを使用
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
                // エラー時はステップ1に戻る
                setCurrentStep(0);
                setSelectedTransporters([]);
            } finally {
                setIsLoading(false);
            }
        } else {
            setCurrentStep(prev => prev + 1);
        }
    };

    const handlePrev = () => {
        setCurrentStep(prev => Math.max(0, prev - 1));
    };

    const handleReset = () => {
        setCurrentStep(0);
        setSelectedTransporters([]);
        setIsLoading(false);
    };

    const renderStepContent = () => {
        switch (currentStep) {
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
                    </div>
                );
            default:
                return null;
        }
    };

    return (
        <Modal
            title={config?.title || 'ブロック単価ワークフロー'}
            open={visible}
            onCancel={onClose}
            footer={null}
            width={800}
            destroyOnClose
        >
            <Steps current={currentStep} items={steps} className="workflow-steps" />

            <div className="step-content">
                {renderStepContent()}
            </div>

            <div className="workflow-actions">
                {currentStep > 0 && (
                    <Button onClick={handlePrev} disabled={isLoading}>
                        前へ
                    </Button>
                )}
                {currentStep > 0 && (
                    <Button onClick={handleReset} disabled={isLoading}>
                        最初から
                    </Button>
                )}
                <Button
                    type="primary"
                    onClick={handleNext}
                    disabled={currentStep === 0 && !isAllSelected}
                    loading={isLoading}
                >
                    {currentStep === steps.length - 1 ? '完了' : '次へ'}
                </Button>
            </div>
        </Modal>
    );
};

export default BlockUnitPriceWorkflowSelfContained;
