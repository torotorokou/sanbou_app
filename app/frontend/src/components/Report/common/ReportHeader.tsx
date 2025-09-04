import React from 'react';
import { Steps } from 'antd';
import ReportSelector from './ReportSelector';
import type { PageGroupKey } from '@/constants/reportConfig';

type ReportHeaderProps = {
    reportKey: string;
    onChangeReportKey: (val: string) => void;
    currentStep: number;
    /** ページ別帳票グループ指定 */
    pageGroup?: PageGroupKey;
};

const ReportHeader: React.FC<ReportHeaderProps> = ({
    reportKey,
    onChangeReportKey,
    currentStep,
    pageGroup,
}) => {
    return (
        <div
            style={{
                display: 'flex',
                alignItems: 'flex-start',
                gap: 24,
                marginBottom: 24,
            }}
        >
            {/* 📘 セレクトボックスラッパー */}
            <div
                style={{
                    padding: '12px 24px',
                    background: '#fff',
                    borderRadius: 12,
                    boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
                }}
            >
                <ReportSelector
                    reportKey={reportKey}
                    onChange={onChangeReportKey}
                    pageGroup={pageGroup}
                />
            </div>

            {/* ✅ ステップ表示ラッパー */}
            <div
                style={{
                    flex: 1,
                    padding: '12px 24px',
                    background: '#f9f9f9',
                    borderRadius: 12,
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
                        { title: '帳簿作成', description: 'ボタンをクリック' },
                        { title: 'プレビュー確認', description: '帳票を確認' },
                        { title: 'ダウンロード', description: '保存できます' },
                    ]}
                />
            </div>
        </div>
    );
};

export default ReportHeader;
