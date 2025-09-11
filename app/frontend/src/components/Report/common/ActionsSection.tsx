import React from 'react';
import VerticalActionButton from '../../ui/VerticalActionButton';
import { PlayCircleOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { useReportActions } from '../../../hooks/report';
import { useWindowSize } from '../../../hooks/ui';
import type { ActionsSectionProps } from './types';
import { actionButtonColors } from '../../../theme';

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
}) => {
    const actions = useReportActions();
    const { isMobile, isTablet } = useWindowSize();
    const isMobileOrTablet = isMobile || isTablet;

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
            {/* レポート生成ボタン */}
            <VerticalActionButton
                icon={<PlayCircleOutlined />}
                text='レポート生成'
                onClick={onGenerate}
                disabled={!readyToCreate}
            />

            {/* スペーサー - 帳簿作成ボタンと他のボタンを離すため */}
            {finalized && (
                <div style={{
                    height: isMobileOrTablet ? 0 : 50,
                    width: isMobileOrTablet ? 24 : 0
                }} />
            )}

            {/* ダウンロード・印刷ボタン */}
            {finalized && (
                <div style={{
                    display: 'flex',
                    flexDirection: isMobileOrTablet ? 'row' : 'column',
                    gap: isMobileOrTablet ? 12 : 8,
                    alignItems: 'center',
                }}>
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
