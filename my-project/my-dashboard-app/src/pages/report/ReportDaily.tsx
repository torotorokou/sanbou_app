import React, { useState } from 'react';
import {
    Calendar,
    Table,
    Typography,
    Card,
    Upload,
    Button,
    message,
    ConfigProvider,
    Modal,
    Steps,
    Spin,
} from 'antd';
import {
    UploadOutlined,
    DownloadOutlined,
    PlayCircleOutlined,
} from '@ant-design/icons';
import type { UploadProps, CalendarProps } from 'antd';
import jaJP from 'antd/locale/ja_JP';
import dayjs, { Dayjs } from 'dayjs';
import 'dayjs/locale/ja';
import { customTokens } from '@/theme/tokens';

dayjs.locale('ja');

const { Step } = Steps;

type ReportRow = {
    key: string;
    工場: string;
    搬入量: number;
    搬出量: number;
};

const columns = [
    { title: '工場', dataIndex: '工場', key: '工場' },
    { title: '搬入量', dataIndex: '搬入量', key: '搬入量' },
    { title: '搬出量', dataIndex: '搬出量', key: '搬出量' },
];

const ReportDaily: React.FC = () => {
    const [selectedDate, setSelectedDate] = useState<Dayjs | null>(null);
    const [shipFile, setShipFile] = useState<File | null>(null);
    const [yardFile, setYardFile] = useState<File | null>(null);
    const [receiveFile, setReceiveFile] = useState<File | null>(null);
    const [csvData, setCsvData] = useState<ReportRow[]>([]);
    const [finalized, setFinalized] = useState(false);
    const [modalOpen, setModalOpen] = useState(false);
    const [currentStep, setCurrentStep] = useState(0);
    const [loading, setLoading] = useState(false);

    const handleSelect: CalendarProps<Dayjs>['onSelect'] = (date) => {
        setSelectedDate(date);
        setCsvData([]);
        setFinalized(false);
        setShipFile(null);
        setYardFile(null);
        setReceiveFile(null);
    };

    const makeUploadProps = (
        label: string,
        setter: (file: File) => void
    ): UploadProps => ({
        accept: '.csv',
        showUploadList: false,
        beforeUpload: (file) => {
            setter(file);
            message.success(`${label} をアップロードしました`);
            return false;
        },
    });

    const readyToCreate = selectedDate || shipFile || yardFile || receiveFile;

    const handleStepNext = () => {
        if (currentStep === 0) {
            setCurrentStep(1);
        } else if (currentStep === 1) {
            setLoading(true);
            setTimeout(() => {
                const dummyData: ReportRow[] = [
                    { key: '1', 工場: 'A工場', 搬入量: 100, 搬出量: 80 },
                    { key: '2', 工場: 'B工場', 搬入量: 200, 搬出量: 150 },
                ];
                setCsvData(dummyData);
                setFinalized(true);
                setLoading(false);
                setCurrentStep(2);
            }, 1500);
        } else {
            setModalOpen(false);
            setCurrentStep(0);
        }
    };

    const handleOpenModal = () => {
        setModalOpen(true);
        setCurrentStep(0);
    };

    return (
        <ConfigProvider locale={jaJP}>
            <Modal
                open={modalOpen}
                footer={null}
                closable={false}
                width={700}
                centered
            >
                <Steps current={currentStep} style={{ marginBottom: 24 }}>
                    <Step title="データ選択" />
                    <Step title="プレビュー確認" />
                    <Step title="完了" />
                </Steps>

                {currentStep === 0 && (
                    <Typography.Text>
                        帳簿を作成する準備が整いました。次へ進んでください。
                    </Typography.Text>
                )}

                {currentStep === 1 &&
                    (loading ? (
                        <Spin tip="帳簿を作成中です..." />
                    ) : (
                        <Table
                            columns={columns}
                            dataSource={csvData}
                            pagination={false}
                            bordered
                            size="small"
                        />
                    ))}

                {currentStep === 2 && (
                    <Typography.Text type="success">
                        ✅ 帳簿が作成されました。ダウンロードしてください。
                    </Typography.Text>
                )}

                <div style={{ marginTop: 24, textAlign: 'right' }}>
                    <Button type="primary" onClick={handleStepNext}>
                        {currentStep < 2 ? '次へ' : '閉じる'}
                    </Button>
                </div>
            </Modal>

            <div style={{ padding: 24 }}>
                <Typography.Title level={3}>📅 工場日報 作成</Typography.Title>
                <div
                    style={{
                        display: 'flex',
                        gap: 24,
                        alignItems: 'stretch',
                        height: 'calc(100vh - 120px)',
                        marginTop: 16,
                    }}
                >
                    <Card
                        size="small"
                        title={
                            <Typography.Title level={5} style={{ margin: 0 }}>
                                🗂 データセットの準備
                            </Typography.Title>
                        }
                        style={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 16,
                            width: 320,
                        }}
                        bodyStyle={{
                            display: 'flex',
                            flexDirection: 'column',
                            gap: 16,
                        }}
                    >
                        <Card
                            size="small"
                            bodyStyle={{ padding: 8 }}
                            style={{
                                backgroundColor: customTokens.colorBgLayout,
                            }}
                        >
                            <Calendar
                                fullscreen={false}
                                onSelect={handleSelect}
                                value={selectedDate || undefined}
                            />
                        </Card>

                        <Typography.Paragraph
                            style={{
                                margin: 0,
                                padding: '0 8px',
                                fontSize: 12,
                                color: '#666',
                            }}
                        >
                            📅 カレンダーまたは 📂 CSV を選択してください
                        </Typography.Paragraph>

                        <Card
                            size="small"
                            title={
                                <Typography.Title
                                    level={5}
                                    style={{ margin: 0 }}
                                >
                                    📂 CSVアップロード
                                </Typography.Title>
                            }
                            style={{
                                borderRadius: 12,
                                backgroundColor: customTokens.colorBgBase,
                            }}
                        >
                            <div
                                style={{
                                    display: 'flex',
                                    flexDirection: 'column',
                                    gap: 16,
                                }}
                            >
                                {[
                                    {
                                        label: '出荷CSV',
                                        setter: setShipFile,
                                        file: shipFile,
                                    },
                                    {
                                        label: 'ヤードCSV',
                                        setter: setYardFile,
                                        file: yardFile,
                                    },
                                    {
                                        label: '受入CSV',
                                        setter: setReceiveFile,
                                        file: receiveFile,
                                    },
                                ].map(({ label, setter, file }) => (
                                    <div
                                        key={label}
                                        style={{
                                            display: 'flex',
                                            flexDirection: 'column',
                                            gap: 4,
                                        }}
                                    >
                                        <div
                                            style={{
                                                display: 'flex',
                                                alignItems: 'center',
                                                gap: 12,
                                            }}
                                        >
                                            <Typography.Text
                                                style={{ width: 80 }}
                                            >
                                                {label}
                                            </Typography.Text>
                                            <Upload
                                                {...makeUploadProps(
                                                    label,
                                                    setter
                                                )}
                                            >
                                                <Button
                                                    icon={<UploadOutlined />}
                                                    type="default"
                                                    size="middle"
                                                >
                                                    アップロード
                                                </Button>
                                            </Upload>
                                        </div>
                                        <div
                                            style={{
                                                minHeight: 22,
                                                marginLeft: 92,
                                                background: file
                                                    ? '#f0fdf4'
                                                    : undefined,
                                                border: file
                                                    ? '1px solid #86efac'
                                                    : undefined,
                                                borderRadius: file
                                                    ? 6
                                                    : undefined,
                                                padding: file
                                                    ? '2px 8px'
                                                    : undefined,
                                                fontSize: 12,
                                                color: '#166534',
                                            }}
                                        >
                                            {file?.name || '　'}
                                        </div>
                                    </div>
                                ))}
                            </div>
                        </Card>
                    </Card>

                    <div
                        style={{
                            display: 'flex',
                            justifyContent: 'center',
                            alignItems: 'center',
                            width: 120,
                        }}
                    >
                        <Button
                            icon={<PlayCircleOutlined />}
                            type="primary"
                            size="large"
                            shape="round"
                            disabled={!readyToCreate}
                            onClick={handleOpenModal}
                            style={{
                                writingMode: 'vertical-rl',
                                textOrientation: 'mixed',
                                height: 160,
                                fontSize: '1.2rem',
                            }}
                        >
                            帳簿作成
                        </Button>
                    </div>

                    <div style={{ flex: 1 }}>
                        <Typography.Title level={4}>
                            📄 {selectedDate?.format('YYYY年M月D日')} の帳簿
                        </Typography.Title>
                        {finalized ? (
                            <Table
                                columns={columns}
                                dataSource={csvData}
                                pagination={false}
                                bordered
                            />
                        ) : (
                            <Typography.Text type="secondary">
                                帳簿を作成するとここに表示されます。
                            </Typography.Text>
                        )}
                    </div>

                    <div>
                        {finalized && (
                            <Button icon={<DownloadOutlined />}>
                                帳票ダウンロード
                            </Button>
                        )}
                    </div>
                </div>
            </div>
        </ConfigProvider>
    );
};

export default ReportDaily;
