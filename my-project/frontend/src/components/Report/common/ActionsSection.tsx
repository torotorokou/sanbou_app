import React from 'react';
import VerticalActionButton from '../../ui/VerticalActionButton';
import { PlayCircleOutlined, DownloadOutlined } from '@ant-design/icons';
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
    excelUrl,
    pdfUrl,
}) => {
    const actions = useReportActions();

    return (
        <div style={{
            display: 'flex',
            flexDirection: 'column',
            gap: 8,
            alignItems: 'center'
        }}>
            {/* 帳簿作成ボタン */}
            <VerticalActionButton
                icon={<PlayCircleOutlined />}
                text='帳簿作成'
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
                        disabled={!excelUrl}
                        backgroundColor={actionButtonColors.generate}
                    />
                    <VerticalActionButton
                        icon={<PlayCircleOutlined />}
                        text='印刷'
                        onClick={() => actions.handlePrint(pdfUrl || null)}
                        backgroundColor={actionButtonColors.download}
                        disabled={!pdfUrl}
                    />
                </>
            )}
        </div>
    );
};

export default ActionsSection;
