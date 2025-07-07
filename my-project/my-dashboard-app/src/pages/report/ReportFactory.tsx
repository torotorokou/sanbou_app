import React, { useState } from 'react';
import { ConfigProvider, Typography, Spin, Table } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import dayjs from 'dayjs';
import 'dayjs/locale/ja';
import ReportManagePageLayout from '@/components/Report/common/ReportManagePageLayout';
import ReportStepperModal from '@/components/Report/common/ReportStepperModal';
import ReportStepIndicator from '@/components/Report/common/ReportStepIndicator';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';

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

    const readyToCreate = shipFile !== null;

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

                if (label === '出荷CSV') {
                    const parsed: ShipmentRow[] = body.map((cols, i) => ({
                        key: i.toString(),
                        商品名: cols[0],
                        出荷先: cols[1],
                        数量: parseInt(cols[2]),
                    }));
                    setShipmentData(parsed);
                } else if (label === 'ヤードCSV') {
                    const parsed: WorkerRow[] = body.map((cols, i) => ({
                        key: i.toString(),
                        氏名: cols[0],
                        所属: cols[1],
                        出勤区分: cols[2],
                    }));
                    setWorkerData(parsed);
                } else if (label === '受入CSV') {
                    const parsed: ValuableRow[] = body.map((cols, i) => ({
                        key: i.toString(),
                        品目: cols[0],
                        重量: parseFloat(cols[1]),
                        単価: parseFloat(cols[2]),
                    }));
                    setValuableData(parsed);
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
            <ReportStepIndicator currentStep={currentStep} />

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
                uploadFiles={[
                    { label: '出荷CSV', file: shipFile, onChange: setShipFile },
                    {
                        label: 'ヤードCSV',
                        file: yardFile,
                        onChange: setYardFile,
                    },
                    {
                        label: '受入CSV',
                        file: receiveFile,
                        onChange: setReceiveFile,
                    },
                ]}
                makeUploadProps={makeUploadProps}
                finalized={finalized}
                readyToCreate={readyToCreate}
                pdfUrl={pdfUrl}
            >
                {pdfUrl ? (
                    <div>
                        <iframe
                            src={pdfUrl}
                            style={{
                                width: '100%',
                                height: '80vh',
                                border: '1px solid #ccc',
                            }}
                        />
                    </div>
                ) : (
                    <Typography.Text type='secondary'>
                        帳簿を作成するとここにPDFが表示されます。
                    </Typography.Text>
                )}
            </ReportManagePageLayout>
        </ConfigProvider>
    );
};

export default ReportFactory;
