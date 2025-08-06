import React from 'react';
import { Typography } from 'antd';
import type { SampleSectionProps } from './types';
import ReportSampleThumbnail from '../viewer/ReportSampleThumbnail';

/**
 * サンプルファイル表示セクション
 * サンプル画像の表示とダウンロードリンクを提供
 */
const SampleSection: React.FC<SampleSectionProps> = ({
    sampleImageUrl = '/factory_report.pdf'
}) => {
    if (!sampleImageUrl) return null;

    return (
        <>
            <Typography.Title level={5}>
                📄 サンプル帳票
            </Typography.Title>
            <div className='sample-thumbnail'>
                <ReportSampleThumbnail
                    url={sampleImageUrl}
                    width='100%'
                    height='160px'
                />
            </div>
        </>
    );
};

export default SampleSection;
