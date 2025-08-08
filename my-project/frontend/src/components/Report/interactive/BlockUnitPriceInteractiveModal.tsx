import React, { useState, useCallback } from 'react';
import { Modal, Button, Steps, Spin, message, Space, Form, InputNumber, Card } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { getApiEndpoint } from '../../../constants/reportConfig';
import type { ReportKey } from '../../../constants/reportConfig';

// 型定義
interface TransportOption {
    vendor_code: string;
    vendor_name: string;
    transport_fee: number;
    weight_unit_price: number;
}

interface InitialApiResponse {
    status: string;
    data: {
        transport_options: TransportOption[];
        session_id: string;
    };
}

interface UserSelections {
    transportSelections: Record<string, string>;
    [key: string]: unknown;
}

interface BlockUnitPriceInteractiveModalProps {
    open: boolean;
    onClose: () => void;
    csvFiles: { [label: string]: File | null };
    reportKey: ReportKey;
    onSuccess: (zipUrl: string, fileName: string) => void;
}

/**
 * 運搬業者選択コンポーネント
 */
const TransportSelectionForm: React.FC<{
    transportOptions: TransportOption[];
    onSelectionsChange: (selections: UserSelections) => void;
}> = ({ transportOptions, onSelectionsChange }) => {
    const [form] = Form.useForm();

    const handleFormChange = () => {
        const values = form.getFieldsValue();
        onSelectionsChange({
            transportSelections: values,
        });
    };

    return (
        <Card title="運搬業者選択" style={{ marginBottom: 16 }}>
            <Form form={form} layout="vertical" onValuesChange={handleFormChange}>
                {transportOptions.map((option) => (
                    <div key={option.vendor_code} style={{ marginBottom: 16 }}>
                        <h4>{option.vendor_name}</h4>
                        <Space>
                            <Form.Item
                                name={`${option.vendor_code}_transport_fee`}
                                label="運搬費"
                                style={{ marginBottom: 0 }}
                            >
                                <InputNumber
                                    placeholder={`${option.transport_fee}円`}
                                    style={{ width: 120 }}
                                    min={0}
                                />
                            </Form.Item>
                            <Form.Item
                                name={`${option.vendor_code}_weight_unit_price`}
                                label="重量単価"
                                style={{ marginBottom: 0 }}
                            >
                                <InputNumber
                                    placeholder={`${option.weight_unit_price}円/kg`}
                                    style={{ width: 120 }}
                                    min={0}
                                />
                            </Form.Item>
                        </Space>
                    </div>
                ))}
            </Form>
        </Card>
    );
};

/**
 * ブロック単価表専用インタラクティブモーダル
 * 
 * 🎯 目的：
 * - ブロック単価表専用の複数ステップフロー管理
 * - ユーザー入力を含むAPI複数回やり取り
 * - 共通モーダルと分離したカスタマイズ可能UI
 * 
 * 🔄 フロー：
 * 1. CSVアップロード（完了済み前提）
 * 2. 基本情報API送信 → 選択肢受信
 * 3. ユーザー選択入力
 * 4. 最終API送信 → ZIP受信
 */
const BlockUnitPriceInteractiveModal: React.FC<BlockUnitPriceInteractiveModalProps> = ({
    open,
    onClose,
    csvFiles,
    reportKey,
    onSuccess,
}) => {
    const [currentStep, setCurrentStep] = useState(0);
    const [processing, setProcessing] = useState(false);
    const [initialData, setInitialData] = useState<InitialApiResponse | null>(null);
    const [userSelections, setUserSelections] = useState<UserSelections>({ transportSelections: {} });

    // ステップ定義
    const steps = [
        { title: '基本処理', description: '初期データを取得中' },
        { title: 'ユーザー選択', description: '必要な選択を行ってください' },
        { title: '最終処理', description: '帳簿を生成中' },
        { title: '完了', description: '処理が完了しました' },
    ];

    /**
     * Step 1: 初期API呼び出し
     */
    const handleInitialApiCall = useCallback(async () => {
        setProcessing(true);
        try {
            const formData = new FormData();

            // CSVファイルを追加
            const labelToEnglishKey: Record<string, string> = {
                出荷一覧: 'shipment',
                受入一覧: 'receive',
                ヤード一覧: 'yard',
            };

            Object.keys(csvFiles).forEach((label) => {
                const fileObj = csvFiles[label];
                if (fileObj) {
                    const englishKey = labelToEnglishKey[label] || label;
                    formData.append(englishKey, fileObj);
                }
            });

            formData.append('report_key', reportKey);
            formData.append('step', 'initial');

            const apiEndpoint = getApiEndpoint(reportKey);
            const response = await fetch(`${apiEndpoint}/initial`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('初期処理でエラーが発生しました');
            }

            const data: InitialApiResponse = await response.json();
            setInitialData(data);
            setCurrentStep(1);
            message.success('初期処理が完了しました');
        } catch (error) {
            console.error('Initial API call failed:', error);
            message.error('初期処理に失敗しました');
        } finally {
            setProcessing(false);
        }
    }, [csvFiles, reportKey]);

    /**
     * Step 3: 最終API呼び出し（ZIP生成）
     */
    const handleFinalApiCall = useCallback(async () => {
        setProcessing(true);
        try {
            const formData = new FormData();

            // CSVファイルを追加
            const labelToEnglishKey: Record<string, string> = {
                出荷一覧: 'shipment',
                受入一覧: 'receive',
                ヤード一覧: 'yard',
            };

            Object.keys(csvFiles).forEach((label) => {
                const fileObj = csvFiles[label];
                if (fileObj) {
                    const englishKey = labelToEnglishKey[label] || label;
                    formData.append(englishKey, fileObj);
                }
            });

            formData.append('report_key', reportKey);
            formData.append('step', 'final');
            formData.append('user_selections', JSON.stringify(userSelections));

            const apiEndpoint = getApiEndpoint(reportKey);
            const response = await fetch(`${apiEndpoint}/final`, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                throw new Error('最終処理でエラーが発生しました');
            }

            const zipBlob = await response.blob();
            const zipUrl = window.URL.createObjectURL(zipBlob);
            const fileName = response.headers.get('Content-Disposition')?.split('filename=')[1] || 'report.zip';

            setCurrentStep(3);
            message.success('帳簿生成が完了しました');

            // 成功コールバック実行
            onSuccess(zipUrl, fileName);

            // 2秒後に完了ステップへ
            setTimeout(() => {
                setCurrentStep(3);
            }, 2000);

        } catch (error) {
            console.error('Final API call failed:', error);
            message.error('帳簿生成に失敗しました');
        } finally {
            setProcessing(false);
        }
    }, [csvFiles, reportKey, userSelections, onSuccess]);

    /**
     * ユーザー選択の更新
     */
    const handleUserSelectionsChange = useCallback((selections: UserSelections) => {
        setUserSelections(selections);
    }, []);

    /**
     * 次のステップへ進む
     */
    const handleNext = useCallback(() => {
        if (currentStep === 0) {
            handleInitialApiCall();
        } else if (currentStep === 1) {
            setCurrentStep(2);
            handleFinalApiCall();
        } else if (currentStep === 2) {
            setCurrentStep(3);
        }
    }, [currentStep, handleInitialApiCall, handleFinalApiCall]);

    /**
     * モーダルクローズ時のリセット
     */
    const handleClose = useCallback(() => {
        setCurrentStep(0);
        setInitialData(null);
        setUserSelections({ transportSelections: {} });
        setProcessing(false);
        onClose();
    }, [onClose]);

    // モーダルが開いた時に自動的に初期処理開始
    React.useEffect(() => {
        if (open && currentStep === 0) {
            // 少し遅延して開始（UIが安定してから）
            const timer = setTimeout(() => {
                handleInitialApiCall();
            }, 500);
            return () => clearTimeout(timer);
        }
    }, [open, currentStep, handleInitialApiCall]);

    return (
        <Modal
            title="ブロック単価表作成"
            open={open}
            onCancel={handleClose}
            width={800}
            footer={null}
        >
            <div style={{ padding: '20px 0' }}>
                <Steps current={currentStep} style={{ marginBottom: 24 }}>
                    {steps.map((step) => (
                        <Steps.Step key={step.title} title={step.title} description={step.description} />
                    ))}
                </Steps>

                <div style={{ minHeight: 200 }}>
                    {(currentStep === 0 || processing) && currentStep !== 3 && (
                        <div style={{ textAlign: 'center', padding: 40 }}>
                            <Spin size="large" />
                            <p style={{ marginTop: 16 }}>
                                {currentStep === 0 ? '初期データを取得しています...' :
                                    currentStep === 2 ? '帳簿を生成しています...' :
                                        '処理中です...'}
                            </p>
                        </div>
                    )}

                    {currentStep === 1 && !processing && (
                        <div>
                            <h4>運搬業者と単価設定を選択してください</h4>
                            {initialData?.data?.transport_options ? (
                                <TransportSelectionForm
                                    transportOptions={initialData.data.transport_options}
                                    onSelectionsChange={handleUserSelectionsChange}
                                />
                            ) : (
                                <div>運搬業者データを読み込んでいます...</div>
                            )}
                        </div>
                    )}

                    {currentStep === 3 && (
                        <div style={{ textAlign: 'center', padding: 40 }}>
                            <CheckCircleOutlined style={{ fontSize: 48, color: '#52c41a' }} />
                            <h3 style={{ marginTop: 16 }}>完了しました！</h3>
                            <p>ブロック単価表が正常に生成されました。</p>
                        </div>
                    )}
                </div>

                <div style={{ textAlign: 'right', marginTop: 24 }}>
                    <Space>
                        <Button onClick={handleClose}>
                            {currentStep === 3 ? '閉じる' : 'キャンセル'}
                        </Button>

                        {currentStep === 1 && !processing && (
                            <Button
                                type="primary"
                                onClick={handleNext}
                                disabled={!userSelections || Object.keys(userSelections.transportSelections || {}).length === 0}
                            >
                                次へ
                            </Button>
                        )}
                    </Space>
                </div>
            </div>
        </Modal>
    );
};

export default BlockUnitPriceInteractiveModal;
