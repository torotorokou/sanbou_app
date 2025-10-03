import React from 'react';
import { VerticalActionButton } from '@shared/ui';
import { PlayCircleOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { useReportActions } from '@features/report';
import { Card, Typography, Space } from 'antd';
import { useWindowSize } from '@shared/hooks/ui';
import type { ActionsSectionProps } from './types';
import { actionButtonColors } from '@/theme';

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
            gap: isMobileOrTablet ? 12 : 8,
            alignItems: 'center',
            justifyContent: isMobileOrTablet ? 'center' : 'center',
            width: '100%',
            flexWrap: isMobileOrTablet ? 'wrap' : 'nowrap',
        }}>
            {/* レポート生成ボタン */}
            <VerticalActionButton
                icon={<PlayCircleOutlined />}
                text='レポート生成'
                onClick={onGenerate}
                disabled={!readyToCreate}
            />

            {/* ダウンロード・印刷ボタン */}
            {finalized && (
                <>
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
                </>
            )}
        </div>
    );
};

export default ActionsSection;
