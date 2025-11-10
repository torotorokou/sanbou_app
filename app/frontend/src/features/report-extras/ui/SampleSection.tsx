import React from 'react';
import { Typography } from 'antd';
import type { SampleSectionProps } from '../types/report.types';
import ReportSampleThumbnail from '@features/report-viewer/ui/ReportSampleThumbnail';

/**
 * サンプルファイル表示セクション
 * サンプル画像の表示とダウンロードリンクを提供
 */
const SampleSection: React.FC<SampleSectionProps> = ({
    sampleImageUrl = '/factory_report.pdf'
}) => {
    if (!sampleImageUrl) return null;

    return (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
            <Typography.Title level={5} style={{ margin: 0 }}>
                📄 サンプル帳票
            </Typography.Title>
            <div className='sample-thumbnail'>
                <ReportSampleThumbnail
                    url={sampleImageUrl}
                    width='100%'
                    height='140px'
                />
            </div>
        </div>
    );
};

export default SampleSection;
