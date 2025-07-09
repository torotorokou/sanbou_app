import React from 'react';
import { Modal, Steps, Typography, Spin, Table, Button } from 'antd';
import type { ColumnsType } from 'antd/es/table';

const { Step } = Steps;

export type ReportRow = {
    key: string;
    工場: string;
    搬入量: number;
    搬出量: number;
};

type DailyReportStepperProps = {
    open: boolean;
    currentStep: number;
    loading: boolean;
    data: ReportRow[];
    onNext: () => void;
};

const columns: ColumnsType<ReportRow> = [
    { title: '工場', dataIndex: '工場', key: '工場' },
    { title: '搬入量', dataIndex: '搬入量', key: '搬入量' },
    { title: '搬出量', dataIndex: '搬出量', key: '搬出量' },
];

const DailyReportStepper: React.FC<DailyReportStepperProps> = ({
    open,
    currentStep,
    loading,
    data,
    onNext,
}) => {
    return (
        <Modal open={open} footer={null} closable={false} width={700} centered>
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
                        dataSource={data}
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
                <Button type="primary" onClick={onNext}>
                    {currentStep < 2 ? '次へ' : '閉じる'}
                </Button>
            </div>
        </Modal>
    );
};

export default DailyReportStepper;
