import React from 'react';
import { Typography } from 'antd';
import CsvUploadPanel from '../../common/csv-upload/CsvUploadPanel';
import { useWindowSize } from '../../../hooks/ui';
import type { CsvUploadSectionProps } from './types';

/**
 * CSVアップロードセクション
 * データ準備に関する機能を集約
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
    uploadFiles,
    makeUploadProps
}) => {
    const { isMobile, isTablet } = useWindowSize();

    return (
        <>
            <Typography.Title
                level={isMobile ? 5 : 4}
                style={{
                    marginBottom: isMobile ? 6 : isTablet ? 8 : 10, // マージンを縮小してスペース効率化
                    fontSize: isMobile ? '14px' : isTablet ? '15px' : '16px'
                }}
            >
                📂 データセット（CSV）の準備
            </Typography.Title>
            <CsvUploadPanel
                upload={{ files: uploadFiles, makeUploadProps }}
            />
        </>
    );
};

export default CsvUploadSection;
