import React from 'react';
import { Steps } from 'antd';

type ReportStepIndicatorProps = {
    currentStep: number;
};

const ReportStepIndicator: React.FC<ReportStepIndicatorProps> = ({
    currentStep,
}) => {
    return (
        <div
            style={{
                background: '#fff',
                borderRadius: 32,
                padding: '16px 24px',
                boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
            }}
        >
            <Steps
                current={currentStep}
                responsive={false}
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
