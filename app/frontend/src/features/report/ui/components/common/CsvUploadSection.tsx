import React from 'react';
import { Typography } from 'antd';
import { CsvUploadPanelComponent as CsvUploadPanel } from '@features/database/ui';
import { useResponsive } from '@/shared';
import type { CsvUploadSectionProps } from './types';

/**
 * CSVアップロードセクション
 * データ準備に関する機能を集約
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
    uploadFiles,
    makeUploadProps
}) => {
    const { isMobile, isTablet } = useResponsive();

    return (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Typography.Title
                level={isMobile ? 5 : 4}
                style={{
                    margin: 0,
                    marginBottom: isMobile ? 4 : isTablet ? 6 : 8,
                    fontSize: isMobile ? '14px' : isTablet ? '15px' : '16px'
                }}
            >
                📂 データセット（CSV）の準備
            </Typography.Title>
            <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
                <CsvUploadPanel
                    upload={{ files: uploadFiles, makeUploadProps }}
                />
            </div>
        </div>
    );
};

export default CsvUploadSection;
