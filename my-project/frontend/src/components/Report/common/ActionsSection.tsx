import React from 'react';
import VerticalActionButton from '../../ui/VerticalActionButton';
import { PlayCircleOutlined, DownloadOutlined, PrinterOutlined } from '@ant-design/icons';
import { useReportActions } from '../../../hooks/report';
import type { ActionsSectionProps } from './types';
import { actionButtonColors } from '../../../theme';

/**
 * レポート関連のアクションボタンセクション
 * 生成・ダウンロード・印刷機能を集約
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

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            alignItems: 'center'
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
