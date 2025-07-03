import React, { useState } from 'react';
import { ConfigProvider, Typography, Spin, Table } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/ja';
import ReportManagePageLayout from '@/components/Report/common/ReportManagePageLayout';
import ReportStepperModal from '@/components/Report/common/ReportStepperModal';
import type { UploadProps } from 'antd';
import type { ColumnsType } from 'antd/es/table';

dayjs.locale('ja');

type ReportRow = {
    key: string;
    工場: string;
    搬入量: number;
    搬出量: number;
};

const columns: ColumnsType<ReportRow> = [
    { title: '工場', dataIndex: '工場', key: '工場' },
    { title: '搬入量', dataIndex: '搬入量', key: '搬入量' },
    { title: '搬出量', dataIndex: '搬出量', key: '搬出量' },
];

const ReportFactory: React.FC = () => {
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [shipFile, setShipFile] = useState<File | null>(null);
    const [yardFile, setYardFile] = useState<File | null>(null);
    const [receiveFile, setReceiveFile] = useState<File | null>(null);
    const [csvData, setCsvData] = useState<ReportRow[]>([]);
    const [finalized, setFinalized] = useState(false);

    const [modalOpen, setModalOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);

    const readyToCreate = selectedDate !== null || shipFile !== null;

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
                const data: ReportRow[] = rows
                    .slice(1)
                    .filter((r) => r.length >= 3)
                    .map((cols, i) => ({
                        key: i.toString(),
                        工場: cols[0],
                        搬入量: parseFloat(cols[1]),
                        搬出量: parseFloat(cols[2]),
                    }));
                setCsvData(data);
            };
            reader.readAsText(file);
            return false;
        },
    });

    const handleGenerate = () => {
        setModalOpen(true);
        setCurrentStep(1);
        setLoading(true);

        setTimeout(() => {
            setLoading(false);
            setFinalized(true);
            setCurrentStep(2);

            setTimeout(() => {
                setModalOpen(false);
                setCurrentStep(0);
            }, 1000);
        }, 2000);
    };

    return (
        <ConfigProvider locale={jaJP}>
            <ReportStepperModal
                open={modalOpen}
                steps={['データ選択', 'プレビュー確認', '完了']}
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
                        帳簿を作成する準備が整いました。次へ進んでください。
                    </Typography.Text>
                )}
                {currentStep === 1 &&
                    (loading ? (
                        <Spin tip='帳簿を作成中です...' />
                    ) : (
                        <Table
                            columns={columns}
                            dataSource={csvData}
                            pagination={false}
                            bordered
                            size='small'
                        />
                    ))}
                {currentStep === 2 && (
                    <Typography.Text type='success'>
                        ✅ 帳簿が作成されました。ダウンロードしてください。
                    </Typography.Text>
                )}
            </ReportStepperModal>

            <ReportManagePageLayout
                title='📅 工場日報'
                onGenerate={handleGenerate}
                calendarDate={selectedDate}
                onDateChange={setSelectedDate}
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
                readyToCreate={readyToCreate} // ✅ これを渡す
            >
                <div>
                    <Typography.Title level={5}>👷 出勤者一覧</Typography.Title>
                    <Table
                        columns={columns}
                        dataSource={csvData}
                        pagination={false}
                        bordered
                        size='small'
                    />

                    <Typography.Title level={5} style={{ marginTop: 24 }}>
                        💰 有価物一覧
                    </Typography.Title>
                    <Table
                        columns={columns}
                        dataSource={csvData}
                        pagination={false}
                        bordered
                        size='small'
                    />

                    <Typography.Title level={5} style={{ marginTop: 24 }}>
                        📦 出荷情報
                    </Typography.Title>
                    <Table
                        columns={columns}
                        dataSource={csvData}
                        pagination={false}
                        bordered
                        size='small'
                    />
                </div>
            </ReportManagePageLayout>
        </ConfigProvider>
    );
};

export default ReportFactory;
