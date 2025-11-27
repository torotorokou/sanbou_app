import React from 'react';
import { Steps } from 'antd';
import { useResponsive, bp } from '@/shared';
import ReportSelector from '@features/report/selector/ui/ReportSelector';
import type { PageGroupKey } from '@features/report/shared/config';

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

/**
 * レポートヘッダーコンポーネント - useResponsive(flags)統合版
 * 
 * 🔄 リファクタリング内容：
 * - window.innerWidth、isTabletOrHalf、ANT直参照を全廃
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 * - 値の決定はコンポーネント先頭で一元管理
 */

const ReportHeader: React.FC<ReportHeaderProps> = ({
    reportKey,
    onChangeReportKey,
    currentStep,
    areRequiredCsvsUploaded,
    isFinalized,
    pageGroup,
}) => {
    // responsive: flagsベースの段階スイッチ
    const { flags } = useResponsive();

    // responsive: 段階的な値決定（Mobile→Tablet→Laptop→Desktop）
    const pickByDevice = <T,>(mobile: T, tablet: T, laptop: T, desktop: T): T => {
        if (flags.isMobile) return mobile;
        if (flags.isTablet) return tablet;
        if (flags.isLaptop) return laptop;
        return desktop; // isDesktop
    };

    // responsive: 各種スタイル値を4段階で定義
    const gap = pickByDevice(12, 16, 20, 24);
    const marginBottom = pickByDevice(12, 16, 20, 24);
    const padding = pickByDevice('8px 12px', '10px 16px', '12px 20px', '12px 24px');
    const selectorWidth = pickByDevice<string | number>('auto', 'auto', 260, 300);
    const borderRadius = 12;
    const minimizeSteps = pickByDevice(true, true, false, false); // Mobile/TabletはSteps最小化
    const stepsMinWidth = pickByDevice(0, 0, bp.xs, bp.sm);

    // responsive: レイアウト方向（Mobile/Tablet=縦、Laptop/Desktop=横）
    const flexDirection = pickByDevice<'column' | 'row'>('column', 'column', 'row', 'row');
    const alignItems = pickByDevice<'stretch' | 'flex-start'>('stretch', 'stretch', 'flex-start', 'flex-start');

    // responsive: セレクター表示制御（Tablet以下は中央寄せ、Laptop以上は左寄せ）
    const selectorDisplay = pickByDevice<'flex' | undefined>('flex', 'flex', undefined, undefined);
    const selectorJustify = pickByDevice<'center' | undefined>('center', 'center', undefined, undefined);

    // responsive: セレクターのタイトル風スタイル（Tablet以下）
    const selectorTitleStyle = pickByDevice<React.CSSProperties | undefined>(
        { fontSize: 16, fontWeight: 700, width: 'auto', minWidth: 180, textAlign: 'center' },
        { fontSize: 17, fontWeight: 700, width: 'auto', minWidth: 200, textAlign: 'center' },
        undefined,
        undefined
    );

    const containerStyle: React.CSSProperties = {
        display: 'flex',
        alignItems,
        gap,
        marginBottom,
        flexDirection,
    };

    const selectorWrapperStyle: React.CSSProperties = {
        padding,
        background: '#fff',
        borderRadius,
        boxShadow: '0 2px 6px rgba(0,0,0,0.06)',
        width: selectorWidth,
        flex: flags.isMobile || flags.isTablet ? undefined : '0 0 auto',
        display: selectorDisplay,
        justifyContent: selectorJustify,
    };

    const stepsWrapperStyle: React.CSSProperties = {
        flex: 1,
        padding,
        background: '#f9f9f9',
        borderRadius,
        boxShadow: '0 2px 6px rgba(0,0,0,0.04)',
        overflowX: 'auto',
        minWidth: stepsMinWidth,
        // responsive: 狭い画面でも横並びを維持
        WebkitOverflowScrolling: 'touch', // iOS用スムーズスクロール
    };

    // responsive: ステップアイテムの説明文（Mobile=非表示、それ以外で段階的表示）
    const showDescription = !flags.isMobile && !minimizeSteps;
    const stepItems = [
        { title: 'データセットの準備', description: showDescription ? 'CSVアップロード' : undefined },
        { title: '帳簿作成', description: showDescription ? 'ボタンをクリック' : undefined },
        { title: 'ダウンロード', description: showDescription ? '保存できます' : undefined },
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

    return (
        <div style={containerStyle}>
            {/* 📘 セレクトボックスラッパー */}
            <div style={selectorWrapperStyle}>
                {/* responsive: セレクター内部も中央寄せ（Laptop以下） */}
                <div style={selectorDisplay === 'flex' ? { display: 'flex', alignItems: 'center', justifyContent: 'center' } : undefined}>
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
                <div style={{ minWidth: flags.isXs ? 480 : flags.isSm ? 540 : 'auto' }}>
                    <Steps
                        current={headerIndex}
                        responsive={false}
                        size={minimizeSteps ? 'small' : flags.isMobile ? 'small' : undefined}
                        items={stepItems}
                    />
                </div>
            </div>
        </div>
    );
};

export default ReportHeader;
