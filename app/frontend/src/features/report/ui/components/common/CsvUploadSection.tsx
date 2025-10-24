import React from 'react';
import { Typography } from 'antd';
import { CsvUploadPanelComponent as CsvUploadPanel } from '@features/database/ui';
import { useResponsive } from '@/shared';
import type { CsvUploadSectionProps } from './types';

/**
 * CSVアップロードセクション - useResponsive(flags)統合版
 * 
 * 🔄 リファクタリング内容：
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 * - データ準備に関する機能を集約
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
    uploadFiles,
    makeUploadProps
}) => {
    // responsive: flagsベースの段階スイッチ
    const { flags } = useResponsive();

    // responsive: 段階的な値決定（Mobile→Tablet→Laptop→Desktop）
    const pickByDevice = <T,>(mobile: T, tablet: T, laptop: T, desktop: T): T => {
        if (flags.isMobile) return mobile;
        if (flags.isTablet) return tablet;
        if (flags.isLaptop) return laptop;
        return desktop; // isDesktop
    };

    // responsive: タイトルのレベルとスタイル
    const titleLevel = pickByDevice<5 | 4>(5, 4, 4, 4);
    const marginBottom = pickByDevice(4, 6, 8, 8);
    const fontSize = pickByDevice('14px', '15px', '16px', '16px');

    return (
        <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
            <Typography.Title
                level={titleLevel}
                style={{
                    margin: 0,
                    marginBottom,
                    fontSize
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
