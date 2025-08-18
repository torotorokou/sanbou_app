import React, { useState, useCallback } from 'react';
import { Modal, Button, Steps, Spin, message, Space, Card, Select } from 'antd';
import { CheckCircleOutlined } from '@ant-design/icons';
import { getApiEndpoint } from '../../../constants/reportConfig';
import type { ReportKey } from '../../../constants/reportConfig';

// 型定義（要件に合わせて整備）
interface TransportVendor {
    code: string;
    name: string;
    fee?: number;
    unit_price?: number;
}

interface InteractiveItem {
    id: string; // 対象ID
    processor_name: string; // 処理業者名
    product_name: string; // 商品名
    note?: string; // 備考
    transport_options: TransportVendor[]; // 選択肢
}

interface InitialApiResponse {
    status: string;
    data: {
        session_id: string;
        items: InteractiveItem[];
    };
}

// id => 選択された運搬業者
type SelectionMap = Record<string, TransportVendor>;

interface BlockUnitPriceInteractiveModalProps {
    open: boolean;
    onClose: () => void;
    csvFiles: { [label: string]: File | null };
    reportKey: ReportKey;
    onSuccess: (zipUrl: string, fileName: string) => void;
}

/**
 * 選択UI：処理業者ごとに運搬業者を選択
 */
const TransportSelectionList: React.FC<{
    items: InteractiveItem[];
    selections: SelectionMap;
    onChange: (id: string, vendor: TransportVendor) => void;
}> = ({ items, selections, onChange }) => {
    return (
        <div>
            {items.map((item) => (
                <Card key={item.id} style={{ marginBottom: 12 }}>
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                        <div>
                            <div><strong>ID:</strong> {item.id}</div>
                            <div><strong>処理業者:</strong> {item.processor_name}</div>
                            <div><strong>商品名:</strong> {item.product_name}</div>
                            {item.note && <div><strong>備考:</strong> {item.note}</div>}
                        </div>
                        <div style={{ minWidth: 260 }}>
                            <div style={{ marginBottom: 6 }}>運搬業者を選択</div>
                            <Select
                                style={{ width: 240 }}
                                placeholder="選択してください"
                                value={selections[item.id]?.code}
                                onChange={(code) => {
                                    const vendor = item.transport_options.find(v => v.code === code);
                                    if (vendor) onChange(item.id, vendor);
                                }}
                                options={item.transport_options.map(v => ({ value: v.code, label: v.name }))}
                            />
                        </div>
                    </div>
                </Card>
            ))}
        </div>
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
    const [selections, setSelections] = useState<SelectionMap>({});

    // ステップ定義
    const steps = [
        { title: '準備', description: '初期データを取得中' },
        { title: '選択', description: '処理業者ごとに運搬業者を選択' },
        { title: '確認', description: '選択内容を確認' },
        { title: '生成', description: '帳簿を生成中' },
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
            // すべて未選択で初期化
            setSelections({});
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
            // 送信する形：[{ id, vendor_code }...]
            const selectionPayload = Object.keys(selections).map((id) => ({
                id,
                vendor_code: selections[id].code,
            }));
            formData.append('user_selections', JSON.stringify(selectionPayload));

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

            setCurrentStep(4);
            message.success('帳簿生成が完了しました');

            // 成功コールバック実行
            onSuccess(zipUrl, fileName);

            // 2秒後に完了ステップへ
            // 完了画面は短時間表示してクローズ（親がZIP共通処理へ）
            setTimeout(() => {
                onClose();
            }, 1200);

        } catch (error) {
            console.error('Final API call failed:', error);
            message.error('帳簿生成に失敗しました');
        } finally {
            setProcessing(false);
        }
    }, [csvFiles, reportKey, selections, onSuccess, onClose]);

    /**
     * ユーザー選択の更新
     */
    const handleSelectionChange = useCallback((id: string, vendor: TransportVendor) => {
        setSelections((prev) => ({ ...prev, [id]: vendor }));
    }, []);

    /**
     * 次のステップへ進む
     */
    const handleNext = useCallback(() => {
        if (currentStep === 0) {
            handleInitialApiCall();
        } else if (currentStep === 1) {
            // 選択 -> 確認へ
            setCurrentStep(2);
        } else if (currentStep === 2) {
            // 確認 -> 生成へ
            setCurrentStep(3);
            handleFinalApiCall();
        }
    }, [currentStep, handleInitialApiCall, handleFinalApiCall]);

    /**
     * モーダルクローズ時のリセット
     */
    const handleClose = useCallback(() => {
        setCurrentStep(0);
        setInitialData(null);
        setSelections({});
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

                <div style={{ minHeight: 240 }}>
                    {(currentStep === 0 || (processing && currentStep !== 4)) && (
                        <div style={{ textAlign: 'center', padding: 40 }}>
                            <Spin size="large" />
                            <p style={{ marginTop: 16 }}>
                                {currentStep === 0 ? '初期データを取得しています...' :
                                    currentStep === 3 ? '帳簿を生成しています...' : '処理中です...'}
                            </p>
                        </div>
                    )}

                    {currentStep === 1 && !processing && initialData?.data?.items && (
                        <div>
                            <h4>処理業者ごとに運搬業者を選択してください</h4>
                            <TransportSelectionList
                                items={initialData.data.items}
                                selections={selections}
                                onChange={handleSelectionChange}
                            />
                        </div>
                    )}

                    {currentStep === 2 && !processing && initialData?.data?.items && (
                        <div>
                            <h4>選択内容の確認</h4>
                            {initialData.data.items.map((item) => (
                                <Card key={item.id} size="small" style={{ marginBottom: 8 }}>
                                    <Space>
                                        <span><strong>ID:</strong> {item.id}</span>
                                        <span><strong>処理業者:</strong> {item.processor_name}</span>
                                        <span><strong>商品名:</strong> {item.product_name}</span>
                                        <span><strong>選択:</strong> {selections[item.id]?.name || '未選択'}</span>
                                    </Space>
                                </Card>
                            ))}
                        </div>
                    )}

                    {currentStep === 4 && (
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
                            {currentStep >= 3 ? '閉じる' : 'キャンセル'}
                        </Button>

                        {currentStep === 1 && !processing && initialData?.data?.items && (
                            <Button
                                type="primary"
                                onClick={handleNext}
                                disabled={initialData.data.items.some(item => !selections[item.id])}
                            >
                                確認へ
                            </Button>
                        )}

                        {currentStep === 2 && !processing && (
                            <>
                                <Button onClick={() => setCurrentStep(1)}>戻る</Button>
                                <Button type="primary" onClick={handleNext}>進む</Button>
                            </>
                        )}
                    </Space>
                </div>
            </div>
        </Modal>
    );
};

export default BlockUnitPriceInteractiveModal;
