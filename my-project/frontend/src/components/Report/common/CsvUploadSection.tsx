import React from 'react';
import { Typography } from 'antd';
import CsvUploadPanel from '../../common/csv-upload/CsvUploadPanel';
import type { CsvUploadSectionProps } from './types';

/**
 * CSVアップロードセクション
 * データ準備に関する機能を集約
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
    uploadFiles,
    makeUploadProps
}) => {
    return (
        <>
            <Typography.Title level={5}>
                📂 データセットの準備
            </Typography.Title>
            <CsvUploadPanel
                upload={{ files: uploadFiles, makeUploadProps }}
            />
        </>
    );
};

export default CsvUploadSection;
