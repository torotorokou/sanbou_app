import React, { useState } from 'react';
import { ConfigProvider, Typography, Spin } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import dayjs from 'dayjs';
import 'dayjs/locale/ja';
import ReportManagePageLayout from '@/components/Report/common/ReportManagePageLayout';
import ReportStepperModal from '@/components/Report/common/ReportStepperModal';
import ReportStepIndicator from '@/components/Report/common/ReportStepIndicator';
import type { UploadProps } from 'antd';
import PDFViewer from '@/components/Report/viewer/PDFViewer';
import type { WorkerRow, ValuableRow, ShipmentRow } from '@/types/report';
import { identifyCsvType, isCsvMatch } from '@/utils/validators/csvValidator';

dayjs.locale('ja');

const ReportFactory: React.FC = () => {
    const [shipFile, setShipFile] = useState<File | null>(null);
    const [yardFile, setYardFile] = useState<File | null>(null);
    const [receiveFile, setReceiveFile] = useState<File | null>(null);

    const [workerData, setWorkerData] = useState<WorkerRow[]>([]);
    const [valuableData, setValuableData] = useState<ValuableRow[]>([]);
    const [shipmentData, setShipmentData] = useState<ShipmentRow[]>([]);

    const [finalized, setFinalized] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);
    const [pdfUrl, setPdfUrl] = useState<string | null>(null);

    // ファイルのバリデーション状態を管理
    const [shipFileValid, setShipFileValid] = useState<'valid' | 'invalid' | 'unknown'>('unknown');
    const [yardFileValid, setYardFileValid] = useState<'valid' | 'invalid' | 'unknown'>('unknown');
    const [receiveFileValid, setReceiveFileValid] = useState<'valid' | 'invalid' | 'unknown'>('unknown');

    // 帳簿作成の準備状態を判定
    const readyToCreate = shipFile !== null && shipFileValid === 'valid';

    const makeUploadProps = (
        label: string,
        setter: (file: File) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file) => {
            setter(file);
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const rows = text.split('\n').map((row) => row.split(','));
                const body = rows.slice(1);

                // ファイルの厳密なCSVバリデーション
                const csvValidationResult = identifyCsvType(text);
                let isValid = false;

                if (label === '出荷一覧') {
                    isValid = isCsvMatch(csvValidationResult, '出荷一覧');
                    setShipFileValid(isValid ? 'valid' : 'invalid');

                    if (isValid) {
                        const parsed: ShipmentRow[] = body.map((cols, i) => ({
                            key: i.toString(),
                            商品名: cols[0] || '',
                            出荷先: cols[1] || '',
                            数量: parseInt(cols[2]) || 0,
                        }));
                        setShipmentData(parsed);
                    }
                } else if (label === 'ヤード一覧') {
                    isValid = isCsvMatch(csvValidationResult, 'ヤード一覧');
                    setYardFileValid(isValid ? 'valid' : 'invalid');

                    if (isValid) {
                        const parsed: WorkerRow[] = body.map((cols, i) => ({
                            key: i.toString(),
                            氏名: cols[0] || '',
                            所属: cols[1] || '',
                            出勤区分: cols[2] || '',
                        }));
                        setWorkerData(parsed);
                    }
                } else if (label === '受入一覧') {
                    isValid = isCsvMatch(csvValidationResult, '受入一覧');
                    setReceiveFileValid(isValid ? 'valid' : 'invalid');

                    if (isValid) {
                        const parsed: ValuableRow[] = body.map((cols, i) => ({
                            key: i.toString(),
                            品目: cols[0] || '',
                            重量: parseFloat(cols[1]) || 0,
                            単価: parseFloat(cols[2]) || 0,
                        }));
                        setValuableData(parsed);
                    }
                }
            };
            reader.readAsText(file);
            return false;
        },
    });

    const handleGenerate = async () => {
        setModalOpen(true);
        setCurrentStep(1);
        setLoading(true);

        const dummyUrl = '/factory_report.pdf';
        setPdfUrl(dummyUrl);

        setLoading(false);
        setFinalized(true);
        setCurrentStep(2);

        setTimeout(() => {
            setModalOpen(false);
            setCurrentStep(0);
        }, 1000);
    };

    return (
        <ConfigProvider locale={jaJP}>
            <ReportStepIndicator
                currentStep={currentStep}
                items={[
                    { title: 'データ準備' },
                    { title: 'PDF生成' },
                    { title: '完了' }
                ]}
            />

            <ReportStepperModal
                open={modalOpen}
                steps={['データ選択', 'PDF生成中', '完了']}
                currentStep={currentStep}
                onNext={() => {
                    if (currentStep === 2) {
                        setModalOpen(false);
                        setCurrentStep(0);
                    }
                }}
            >
                {currentStep === 0 && (
                    <Typography.Text>
                        帳簿を作成する準備が整いました。
                    </Typography.Text>
                )}
                {currentStep === 1 && loading && (
                    <Spin tip='帳簿をPDFに変換中です...' />
                )}
                {currentStep === 2 && (
                    <Typography.Text type='success'>
                        ✅ PDF帳簿が作成されました。
                    </Typography.Text>
                )}
            </ReportStepperModal>

            <ReportManagePageLayout
                onGenerate={handleGenerate}
                onDownloadExcel={() => {
                    // Excel download logic here
                    console.log('Excel download requested');
                }}
                uploadFiles={[
                    {
                        label: '出荷一覧',
                        file: shipFile,
                        onChange: setShipFile,
                        required: true,
                        validationResult: shipFileValid,
                        onRemove: () => {
                            setShipFile(null);
                            setShipFileValid('unknown');
                            setShipmentData([]);
                        },
                    },
                    {
                        label: 'ヤード一覧',
                        file: yardFile,
                        onChange: setYardFile,
                        required: false,
                        validationResult: yardFileValid,
                        onRemove: () => {
                            setYardFile(null);
                            setYardFileValid('unknown');
                            setWorkerData([]);
                        },
                    },
                    {
                        label: '受入一覧',
                        file: receiveFile,
                        onChange: setReceiveFile,
                        required: false,
                        validationResult: receiveFileValid,
                        onRemove: () => {
                            setReceiveFile(null);
                            setReceiveFileValid('unknown');
                            setValuableData([]);
                        },
                    },
                ]}
                makeUploadProps={makeUploadProps}
                finalized={finalized}
                readyToCreate={readyToCreate}
                pdfUrl={pdfUrl}
                excelUrl={null}
            >
                {/* PDFの表示場所 */}
                <PDFViewer pdfUrl={pdfUrl} />
            </ReportManagePageLayout>
        </ConfigProvider>
    );
};

export default ReportFactory;
