import React from 'react';
import { Steps } from 'antd';
import { useWindowSize } from '../../../hooks/ui';
import { BREAKPOINTS as BP } from '@/shared/constants/breakpoints';
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
    const { isMobile, isTablet, width } = useWindowSize();
    const isMobileOrTablet = isMobile || isTablet;
    // 幅が autoCollapse 未満ならステップは最小表示にする
    const minimizeSteps = typeof width === 'number' ? width < BP.autoCollapse : false;

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
        // デスクトップでは左側に固定幅で配置
        width: isMobileOrTablet ? 'auto' : width < BP.autoCollapse ? 260 : 300,
        flex: isMobileOrTablet ? undefined : '0 0 auto',
        // 半画面以下ではラッパーをフレックスにして中央寄せ
        display: width < BP.autoCollapse ? 'flex' : undefined,
        justifyContent: width < BP.autoCollapse ? 'center' : undefined,
    };

    const stepsWrapperStyle: React.CSSProperties = {
        flex: 1,
        padding: isMobile ? '8px 12px' : isTablet ? '10px 16px' : '12px 24px',
        background: '#f9f9f9',
        borderRadius: 12,
        boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
        overflowX: 'auto',
        minWidth: isMobile ? 0 : 480,
    };

    const stepItems = [
        { title: 'データセットの準備', description: minimizeSteps ? undefined : isMobile ? undefined : 'CSVアップロード' },
        { title: '帳簿作成', description: minimizeSteps ? undefined : isMobile ? undefined : 'ボタンをクリック' },
        { title: 'プレビュー確認', description: minimizeSteps ? undefined : isMobile ? undefined : '帳票を確認' },
        { title: 'ダウンロード', description: minimizeSteps ? undefined : isMobile ? undefined : '保存できます' },
    ];

    // タイトル風スタイル（半画面以下）を selector に渡すための inline style
    const selectorTitleStyle: React.CSSProperties | undefined = width < BP.autoCollapse ? {
        fontSize: 18,
        fontWeight: 700,
        width: 'auto',
        minWidth: 200,
        textAlign: 'center'
    } : undefined;

    return (
        <div style={containerStyle}>
            {/* 📘 セレクトボックスラッパー */}
            <div style={selectorWrapperStyle}>
                {/* ReportSelector は内部で style を受け付けないため、ラッパーで直接見た目を調整 */}
                <div style={width < BP.autoCollapse ? { display: 'flex', alignItems: 'center', justifyContent: 'center' } : undefined}>
                    <ReportSelector
                        reportKey={reportKey}
                        onChange={onChangeReportKey}
                        pageGroup={pageGroup}
                        customOptions={undefined}
                        style={selectorTitleStyle}
                    />
                </div>
            </div>

            {/* ✅ ステップ表示ラッパー */}
            <div style={stepsWrapperStyle}>
                <Steps
                    current={currentStep}
                    responsive={true}
                    size={minimizeSteps ? 'small' : isMobile ? 'small' : undefined}
                    items={stepItems}
                />
            </div>
        </div>
    );
};

export default ReportHeader;
