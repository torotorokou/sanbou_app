import React from 'react';
import { VerticalActionButton } from '@shared/ui';
import { PlayCircleOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { useReportActions } from '../../hooks/useReportActions';
import { useWindowSize } from '@shared/hooks/ui';
import type { ActionsSectionProps } from './types';
import { actionButtonColors } from '@shared/theme';

/**
 * レスポンシブル対応レポート関連のアクションボタンセクション
 * 生成・ダウンロード・印刷機能を集約
 * 
 * 📱 モバイル・タブレット：横並びレイアウト
 * 💻 デスクトップ：縦並びレイアウト
 */
const ActionsSection: React.FC<ActionsSectionProps> = ({
    onGenerate,
    readyToCreate,
    finalized,
    onDownloadExcel,
    onPrintPdf,
    pdfUrl,
    excelReady,
    pdfReady,
    compactMode = false,
}) => {
    const actions = useReportActions();
    const { isMobile, isTablet } = useWindowSize();
    const isMobileOrTablet = isMobile || isTablet;

    // compactMode: 半画面用の下部横並び表示にする
    if (compactMode) {
        return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 8, width: '100%', justifyContent: 'flex-end' }}>
                {/* 生成ボタン：生成前のみ表示（生成後は再生成が表示されるため非表示） */}
                {!finalized && (
                    <div style={{ width: '100%' }}>
                        <VerticalActionButton
                            icon={<PlayCircleOutlined />}
                            text='レポート生成'
                            onClick={onGenerate}
                            disabled={!readyToCreate}
                        />
                    </div>
                )}

                {/* 生成後は1行で表示：再生成・エクセルDL・印刷 */}
                {finalized && (
                    <div style={{ display: 'flex', gap: 12, width: '100%', justifyContent: 'flex-start' }}>
                        <VerticalActionButton
                            icon={<PlayCircleOutlined />}
                            text='再生成'
                            onClick={onGenerate}
                            disabled={!readyToCreate}
                        />
                        <VerticalActionButton
                            icon={<DownloadOutlined />}
                            text='エクセルDL'
                            onClick={onDownloadExcel}
                            disabled={!excelReady}
                            backgroundColor={actionButtonColors.generate}
                        />
                        <VerticalActionButton
                            icon={<PrinterOutlined />}
                            text='印刷'
                            onClick={onPrintPdf || (() => actions.handlePrint(pdfUrl || null))}
                            backgroundColor={actionButtonColors.download}
                            disabled={!pdfReady}
                        />
                    </div>
                )}
            </div>
        );
    }

    return (
        <div style={{
            display: 'flex',
            flexDirection: isMobileOrTablet ? 'row' : 'column',
            alignItems: 'center',
            justifyContent: 'center',
            width: isMobileOrTablet ? '100%' : 'auto', // デスクトップでは自動サイズ
            height: isMobileOrTablet ? 'auto' : 'auto', // 高さは内容に合わせる
            flexWrap: isMobileOrTablet ? 'wrap' : 'nowrap',
            gap: isMobileOrTablet ? 12 : 24, // ボタン間のスペース
        }}>
            {/* 生成前: レポート生成ボタンを表示 */}
            {!finalized && (
                <VerticalActionButton
                    icon={<PlayCircleOutlined />}
                    text='レポート生成'
                    onClick={onGenerate}
                    disabled={!readyToCreate}
                />
            )}

            {/* 生成後: 再生成・エクセルDL・印刷の3つを表示 */}
            {finalized && (
                <div style={{
                    display: 'flex',
                    flexDirection: isMobileOrTablet ? 'row' : 'column',
                    gap: isMobileOrTablet ? 12 : 8,
                    alignItems: 'center',
                }}>
                    <VerticalActionButton
                        icon={<PlayCircleOutlined />}
                        text='再生成'
                        onClick={onGenerate}
                        disabled={!readyToCreate}
                    />
                    <VerticalActionButton
                        icon={<DownloadOutlined />}
                        text='エクセルDL'
                        onClick={onDownloadExcel}
                        disabled={!excelReady}
                        backgroundColor={actionButtonColors.generate}
                    />
                    <VerticalActionButton
                        icon={<PrinterOutlined />}
                        text='印刷'
                        onClick={onPrintPdf || (() => actions.handlePrint(pdfUrl || null))}
                        backgroundColor={actionButtonColors.download}
                        disabled={!pdfReady}
                    />
                </div>
            )}
        </div>
    );
};

export default ActionsSection;
