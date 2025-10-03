import React from 'react';
import { Steps } from 'antd';
import { useWindowSize } from '@shared/hooks/ui';
import { isTabletOrHalf, ANT } from '@/shared/constants/breakpoints';
import ReportSelector from './ReportSelector';
import type { PageGroupKey } from '@features/report';

type ReportHeaderProps = {
    reportKey: string;
    onChangeReportKey: (val: string) => void;
    currentStep: number;
    // New flags used to derive header step index
    areRequiredCsvsUploaded?: boolean;
    isFinalized?: boolean;
    /** ページ別帳票グループ指定 */
    pageGroup?: PageGroupKey;
};

const ReportHeader: React.FC<ReportHeaderProps> = ({
    reportKey,
    onChangeReportKey,
    currentStep,
    areRequiredCsvsUploaded,
    isFinalized,
    pageGroup,
}) => {
    const { isMobile, isTablet, width } = useWindowSize();
    const isMobileOrTablet = isMobile || isTablet;
    // 幅が autoCollapse 未満ならステップは最小表示にする
    const minimizeSteps = typeof width === 'number' ? isTabletOrHalf(width) : false;

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
            width: isMobileOrTablet ? 'auto' : (typeof width === 'number' && width < ANT.xl ? 260 : 300),
        flex: isMobileOrTablet ? undefined : '0 0 auto',
        // 半画面以下ではラッパーをフレックスにして中央寄せ
            display: (typeof width === 'number' && isTabletOrHalf(width)) ? 'flex' : undefined,
            justifyContent: (typeof width === 'number' && isTabletOrHalf(width)) ? 'center' : undefined,
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
        { title: 'ダウンロード', description: minimizeSteps ? undefined : isMobile ? undefined : '保存できます' },
    ];

    // Derive header index from upload/finish flags when available. Falls back to passed currentStep.
    const deriveHeaderIndex = () => {
        if (typeof areRequiredCsvsUploaded === 'boolean' && typeof isFinalized === 'boolean') {
            if (!areRequiredCsvsUploaded) return 0; // データセットの準備
            if (areRequiredCsvsUploaded && !isFinalized) return 1; // 帳簿作成
            if (isFinalized) return 2; // ダウンロード
        }
        return Math.min(Math.max(currentStep, 0), stepItems.length - 1);
    };
    const headerIndex = deriveHeaderIndex();

    // タイトル風スタイル（半画面以下）を selector に渡すための inline style
    const selectorTitleStyle: React.CSSProperties | undefined = (typeof width === 'number' && width < ANT.xl) ? {
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
                    <div style={(typeof width === 'number' && isTabletOrHalf(width)) ? { display: 'flex', alignItems: 'center', justifyContent: 'center' } : undefined}>
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
                    current={headerIndex}
                    responsive={true}
                    size={minimizeSteps ? 'small' : isMobile ? 'small' : undefined}
                    items={stepItems}
                />
            </div>
        </div>
    );
};

export default ReportHeader;
