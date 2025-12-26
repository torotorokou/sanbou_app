import React from 'react';
import type { ReactNode } from 'react';
import { useReportLayoutStyles } from '@features/report/selector/model/useReportLayoutStyles';
import { useResponsive } from '@/shared';
import SampleSection from '@features/report/base/ui/SampleSection';
import CsvUploadSection from '@features/report/upload/ui/CsvUploadSection';
import ActionsSection from '@features/report/actions/ui/ActionsSection';
import PreviewSection from '@features/report/preview/ui/PreviewSection';
import type { UploadProps } from 'antd';
import type { UploadFileConfig } from '@features/report/shared/types/report.types';
import type { CsvUploadFileType as CsvFileType } from './types';

/**
 * レポート管理ページレイアウト - useResponsive(flags)統合版
 *
 * 🔄 リファクタリング内容：
 * - isTabletOrHalf、window.innerWidth直参照を全廃
 * - useResponsive(flags)のpickByDevice方式に統一
 * - 3段階レスポンシブ（Mobile/Tablet/Desktop）
 */

// Convert UploadFileConfig validation result to CsvFileType format
const mapValidationResult = (
  result?: 'valid' | 'invalid' | 'unknown'
): 'ok' | 'ng' | 'unknown' | undefined => {
  if (!result) return undefined;
  if (result === 'valid') return 'ok';
  if (result === 'invalid') return 'ng';
  return 'unknown';
};

const convertToCsvFileType = (files: UploadFileConfig[]): CsvFileType[] => {
  return files.map((f) => ({
    ...f,
    validationResult: mapValidationResult(
      f.validationResult as 'valid' | 'invalid' | 'unknown' | undefined
    ),
  }));
};

type Props = {
  header?: ReactNode;
  sampleImageUrl?: string;
  uploadFiles?: UploadFileConfig[];
  // MakeUploadPropsFn と同等: ラベルから UploadProps を生成
  makeUploadProps?: (label: string) => UploadProps;
  onGenerate?: () => void;
  readyToCreate?: boolean;
  finalized?: boolean;
  onDownloadExcel?: () => void;
  onPrintPdf?: () => void;
  pdfUrl?: string | null;
  excelReady?: boolean;
  pdfReady?: boolean;
  children?: ReactNode;
};

const ReportManagePageLayout: React.FC<Props> = ({
  header,
  sampleImageUrl,
  uploadFiles: mappedUploadFiles,
  makeUploadProps,
  onGenerate,
  readyToCreate,
  finalized,
  onDownloadExcel,
  onPrintPdf,
  pdfUrl,
  excelReady,
  pdfReady,
  children,
}) => {
  const styles = useReportLayoutStyles();

  // responsive: flagsベースの3段階スイッチ（統一体系）
  const { flags } = useResponsive();

  // responsive: 3段階の値決定（Mobile→Tablet→Desktop）
  const pickByDevice = <T,>(mobile: T, tablet: T, desktop: T): T => {
    if (flags.isMobile) return mobile; // ≤767px
    if (flags.isTablet) return tablet; // 768-1280px
    return desktop; // ≥1281px
  };

  // responsive: レイアウト切り替え
  // - isXs: 1列（データセット上、プレビュー下）
  // - isSm/isTablet: 2列簡易レイアウト
  // - Desktop: フルレイアウト
  const isExtraSmallLayout = flags.isXs; // < 640px: 1列縦並び
  const isCompactLayout = flags.isSm || flags.isTablet; // 640-1279px: 2列横並び
  const gap = pickByDevice(8, 16, 16);
  const headerJustify = pickByDevice<'center' | 'flex-start'>('center', 'center', 'flex-start');

  return (
    <div style={styles.container}>
      {header && (
        <div
          style={{
            marginBottom: 8,
            display: 'flex',
            justifyContent: headerJustify,
            width: '100%',
          }}
        >
          {header}
        </div>
      )}

      <div style={styles.mainLayout}>
        {/* responsive: isXs (< 640px) - 1列縦並びレイアウト */}
        {isExtraSmallLayout ? (
          <>
            <div
              style={{
                display: 'flex',
                flexDirection: 'column',
                gap: 12,
                width: '100%',
                minHeight: 0,
                flexGrow: 1,
                flexShrink: 1,
                flexBasis: 0,
              }}
            >
              {/* 1. データセット（上） */}
              <div style={{ flexGrow: 0, flexShrink: 0, flexBasis: 'auto' }}>
                <CsvUploadSection
                  uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                  makeUploadProps={(label: string) =>
                    makeUploadProps ? makeUploadProps(label) : ({} as UploadProps)
                  }
                />
              </div>

              {/* 2. レポート生成ボタン（中） */}
              <div style={{ flexGrow: 0, flexShrink: 0, flexBasis: 'auto' }}>
                <ActionsSection
                  onGenerate={onGenerate ?? (() => {})}
                  readyToCreate={!!readyToCreate}
                  finalized={!!finalized}
                  onDownloadExcel={onDownloadExcel ?? (() => {})}
                  onPrintPdf={onPrintPdf}
                  pdfUrl={pdfUrl ?? null}
                  excelReady={!!excelReady}
                  pdfReady={!!pdfReady}
                  compactMode={true}
                />
              </div>

              {/* 3. プレビュー（下・スクロール可能） */}
              <div
                style={{
                  flexGrow: 1,
                  flexShrink: 1,
                  flexBasis: 'auto',
                  minHeight: 300,
                  overflow: 'auto',
                }}
              >
                <div style={styles.previewContainer}>
                  <PreviewSection>{children}</PreviewSection>
                </div>
              </div>
            </div>
          </>
        ) : isCompactLayout ? (
          <>
            {/* isSm/Tablet (640-1023px) - 2列横並びレイアウト */}
            <div
              style={{
                display: 'flex',
                gap,
                width: '100%',
                minHeight: 0,
                flexGrow: 1,
                flexShrink: 1,
                flexBasis: 0,
              }}
            >
              <div
                style={{
                  flexGrow: 1,
                  flexShrink: 1,
                  flexBasis: '40%',
                  display: 'flex',
                  flexDirection: 'column',
                  gap: 12,
                  minHeight: 0,
                }}
              >
                <div style={{ display: 'none' }}>
                  <SampleSection sampleImageUrl={sampleImageUrl} />
                </div>
                <CsvUploadSection
                  uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                  makeUploadProps={(label: string) =>
                    makeUploadProps ? makeUploadProps(label) : ({} as UploadProps)
                  }
                />
              </div>

              <div
                style={{
                  flexGrow: 1,
                  flexShrink: 1,
                  flexBasis: '60%',
                  display: 'flex',
                  minHeight: 0,
                }}
              >
                <div style={styles.previewContainer}>
                  <PreviewSection>{children}</PreviewSection>
                </div>
              </div>
            </div>

            <div style={{ width: '100%', marginTop: 12 }}>
              <ActionsSection
                onGenerate={onGenerate ?? (() => {})}
                readyToCreate={!!readyToCreate}
                finalized={!!finalized}
                onDownloadExcel={onDownloadExcel ?? (() => {})}
                onPrintPdf={onPrintPdf}
                pdfUrl={pdfUrl ?? null}
                excelReady={!!excelReady}
                pdfReady={!!pdfReady}
                compactMode={true}
              />
            </div>
          </>
        ) : (
          <>
            {/* Laptop/Desktop (≥1024px) - フルレイアウト */}
            <div style={styles.leftPanel}>
              <SampleSection sampleImageUrl={sampleImageUrl} />
              <CsvUploadSection
                uploadFiles={convertToCsvFileType(mappedUploadFiles ?? [])}
                makeUploadProps={(label: string) =>
                  makeUploadProps ? makeUploadProps(label) : ({} as UploadProps)
                }
              />
            </div>

            <div style={styles.centerPanel as React.CSSProperties}>
              <ActionsSection
                onGenerate={onGenerate ?? (() => {})}
                readyToCreate={!!readyToCreate}
                finalized={!!finalized}
                onDownloadExcel={onDownloadExcel ?? (() => {})}
                onPrintPdf={onPrintPdf}
                pdfUrl={pdfUrl ?? null}
                excelReady={!!excelReady}
                pdfReady={!!pdfReady}
              />
            </div>

            <div style={styles.rightPanel}>
              <div style={styles.previewContainer}>
                <PreviewSection>{children}</PreviewSection>
              </div>
            </div>
          </>
        )}
      </div>
    </div>
  );
};

export default ReportManagePageLayout;
