import React from 'react';
import { Steps } from 'antd';
import { useWindowSize } from '../../../hooks/ui';
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
    const { isMobile, isTablet } = useWindowSize();
    const isMobileOrTablet = isMobile || isTablet;

    const containerStyle: React.CSSProperties = {
        display: 'flex',
        alignItems: isMobileOrTablet ? 'stretch' : 'flex-start',
        gap: isMobile ? 12 : isTablet ? 16 : 24,
        marginBottom: isMobile ? 12 : isTablet ? 16 : 24,
        flexDirection: (isMobileOrTablet ? 'column' : 'row') as 'row' | 'column',
    };

    const selectorWrapperStyle: React.CSSProperties = {
        padding: isMobile ? '8px 12px' : isTablet ? '10px 16px' : '12px 24px',
        background: '#fff',
        borderRadius: 12,
        boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
    };

    const stepsWrapperStyle: React.CSSProperties = {
        flex: 1,
        padding: isMobile ? '8px 12px' : isTablet ? '10px 16px' : '12px 24px',
        background: '#f9f9f9',
        borderRadius: 12,
        boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
        overflowX: 'auto',
    };

    const stepItems = [
        { title: 'データセットの準備', description: isMobile ? undefined : 'CSVアップロード' },
        { title: '帳簿作成', description: isMobile ? undefined : 'ボタンをクリック' },
        { title: 'プレビュー確認', description: isMobile ? undefined : '帳票を確認' },
        { title: 'ダウンロード', description: isMobile ? undefined : '保存できます' },
    ];

    return (
        <div style={containerStyle}>
            {/* 📘 セレクトボックスラッパー */}
            <div style={selectorWrapperStyle}>
                <ReportSelector
                    reportKey={reportKey}
                    onChange={onChangeReportKey}
                    pageGroup={pageGroup}
                />
            </div>

            {/* ✅ ステップ表示ラッパー */}
            <div style={stepsWrapperStyle}>
                <Steps
                    current={currentStep}
                    responsive={true}
                    size={isMobile ? 'small' : undefined}
                    items={stepItems}
                    style={{ minWidth: isMobile ? 0 : 480 }}
                />
            </div>
        </div>
    );
};

export default ReportHeader;
