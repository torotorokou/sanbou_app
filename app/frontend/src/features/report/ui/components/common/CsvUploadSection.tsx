import React from 'react';
import { Typography, message } from 'antd';
import { useResponsive } from '@/shared';
import { CsvUploadPanelComponent } from '@/features/csv-uploader';
import type { CsvUploadSectionProps } from './types';

/**
 * CSVアップロードセクション - 互換アダプタ統合版
 * 
 * 🔄 リファクタリング内容：
 * - CsvUploadPanelComponent（互換アダプタ）を使用
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 * - データ準備に関する機能を集約
 * 
 * 📝 TODO: 将来的に SimpleUploadPanel + useDatasetImportVM への直接呼び出しに移行
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({
    uploadFiles,
    // makeUploadProps は現在未使用（互換アダプタが内部で処理）
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

    // 成功/失敗ハンドラ
    const handleSuccess = (payload: unknown) => {
        console.log('CSV upload success:', payload);
        message.success('CSVファイルのアップロードに成功しました');
    };

    const handleError = (error: unknown) => {
        console.error('CSV upload error:', error);
        message.error('CSVファイルのアップロードに失敗しました');
    };

    // activeTypes を uploadFiles から抽出
    const activeTypes = uploadFiles.map(f => f.label);

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
                <CsvUploadPanelComponent
                    datasetKey="report-csv"
                    activeTypes={activeTypes}
                    accept=".csv"
                    maxSizeMB={20}
                    onSuccess={handleSuccess}
                    onError={handleError}
                />
            </div>
        </div>
    );
};

export default CsvUploadSection;
