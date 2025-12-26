import React from 'react';
import { Typography } from 'antd';
import { useResponsive } from '@/shared';
import type { CsvUploadSectionProps } from './types';
import { ReportUploadFileCard } from './ReportUploadFileCard';

/**
 * CSVアップロードセクション - useResponsive(flags)統合版
 *
 * 🔄 リファクタリング内容：
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 4段階レスポンシブ（Mobile/Tablet/Laptop/Desktop）
 * - データ準備に関する機能を集約
 * - uploadFiles と makeUploadProps を使用してアップロード機能を実装
 * - dataset-import のデザインに合わせた見た目（スキップ機能なし）
 */
const CsvUploadSection: React.FC<CsvUploadSectionProps> = ({ uploadFiles, makeUploadProps }) => {
  // responsive: 3段階判定（Mobile/Tablet/Desktop）
  const { flags } = useResponsive();

  // responsive: 3段階ヘルパー
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile; // ≤767px
    if (flags.isTablet) return tablet; // 768-1280px
    return desktop; // ≥1280px
  };

  // responsive: タイトルのレベルとスタイル
  const titleLevel = pickByDevice<5 | 4>(5, 4, 4);
  const marginBottom = pickByDevice(4, 8, 8);
  const fontSize = pickByDevice('14px', '15px', '16px');
  const itemGap = pickByDevice(6, 10, 10);

  return (
    <div style={{ display: 'flex', flexDirection: 'column', minHeight: 0 }}>
      <Typography.Title
        level={titleLevel}
        style={{
          margin: 0,
          marginBottom,
          fontSize,
        }}
      >
        📂 データセット（CSV）の準備
      </Typography.Title>
      <div style={{ flex: 1, minHeight: 0, overflowY: 'auto' }}>
        <div style={{ display: 'flex', flexDirection: 'column', gap: itemGap }}>
          {uploadFiles.map((uploadFile) => {
            // makeUploadPropsは1引数のみを受け取る
            const uploadProps = makeUploadProps(uploadFile.label);

            return (
              <ReportUploadFileCard
                key={uploadFile.label}
                label={uploadFile.label}
                file={uploadFile.file}
                required={uploadFile.required}
                validationResult={uploadFile.validationResult}
                onRemove={uploadFile.onRemove || (() => {})}
                uploadProps={uploadProps}
                size="compact"
              />
            );
          })}
        </div>
      </div>
    </div>
  );
};

export default CsvUploadSection;
