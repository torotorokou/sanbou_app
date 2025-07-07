import React from 'react';
import { Steps, Typography } from 'antd';

const { Step } = Steps;

type ReportStepIndicatorProps = {
    currentStep: number;
};

const ReportStepIndicator: React.FC<ReportStepIndicatorProps> = ({
    currentStep,
}) => {
    return (
        <div
            style={{
                display: 'flex',
                justifyContent: 'space-between',
                alignItems: 'center',
                padding: '16px 24px',
                background: '#fff',
                borderRadius: 32,
                maxWidth: 1200,
                margin: '0 auto 24px auto',
            }}
        >
            {/* 左：タイトル */}
            <Typography.Title level={3} style={{ margin: 0 }}>
                📘　工場日報
            </Typography.Title>

            {/* 右：ステップ */}
            <Steps
                current={currentStep}
                responsive={false}
                style={{ flex: 1, marginLeft: 40 }}
                items={[
                    {
                        title: 'データセットの準備',
                        description: 'CSVアップロード',
                    },
                    {
                        title: '帳簿作成',
                        description: 'ボタンをクリック',
                    },
                    {
                        title: 'プレビュー確認',
                        description: '帳票を確認',
                    },
                    {
                        title: 'ダウンロード',
                        description: '保存できます',
                    },
                ]}
            />
        </div>
    );
};

export default ReportStepIndicator;
