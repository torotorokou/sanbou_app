import { useCallback, useEffect } from 'react';
import type { UploadProps } from 'antd/es/upload';
import { useCsvFileValidator } from '@features/csv-validation';
import { useReportArtifact } from '@features/report/preview/model/useReportArtifact';
import type {
  CsvFiles,
  CsvConfigEntry,
  UploadFileConfig,
  MakeUploadPropsFn,
} from '@features/report/shared/types/report.types';
import type { ReportKey } from '@features/report/shared/config';

/**
 * ReportBaseのビジネスロジックを統合管理するフック
 *
 * 🔄 更新: 共通のcsv-validationを使用するように変更
 *
 * 🎯 目的：
 * - CSV検証、Excel生成の複雑なロジックを統合
 * - ReportBaseコンポーネントをシンプルに保つ
 * - 関連する機能を一元化して保守性向上
 */

export const useReportBaseBusiness = (
  csvConfigs: CsvConfigEntry[],
  csvFiles: CsvFiles,
  onUploadFile: (label: string, file: File | null) => void,
  reportKey: ReportKey
) => {
  // 共通のCSV検証フックを使用
  const csvValidation = useCsvFileValidator({
    getRequiredHeaders: (label: string) => {
      const entry = csvConfigs.find((c) => c.config.label === label);
      return entry?.config.expectedHeaders;
    },
  });

  const artifact = useReportArtifact();

  useEffect(() => {
    artifact.cleanup();
  }, [artifact.cleanup, reportKey]);

  /**
   * ファイル削除処理
   */
  const handleRemoveFile = useCallback(
    (label: string) => {
      onUploadFile(label, null);
      csvValidation.resetValidation(label);
    },
    [onUploadFile, csvValidation]
  );

  /**
   * アップロード用props生成
   */
  const makeUploadProps = useCallback(
    (label: string, parser: (csvText: string) => void): UploadProps => ({
      accept: '.csv',
      showUploadList: false,
      beforeUpload: async (fileObj) => {
        onUploadFile(label, fileObj);

        if (!fileObj) {
          csvValidation.resetValidation(label);
          return false;
        }

        // 共通の検証フックを使用（ヘッダー検証 + カスタムパーサー検証）
        await csvValidation.validateFile(label, fileObj);

        // パーサーも実行（データ構造の検証）
        try {
          const text = await fileObj.text();
          parser(text);
        } catch (parseError) {
          console.error(`CSV parsing failed for ${label}:`, parseError);
          // パース失敗は検証結果に反映済み
        }

        return false;
      },
    }),
    [onUploadFile, csvValidation]
  );

  /**
   * レポート生成準備チェック
   */
  const isReadyToCreate = useCallback((): boolean => {
    return csvConfigs.every((entry) => {
      const label = entry.config.label;
      const fileObj = csvFiles[label];
      const validation = csvValidation.getValidationResult(label);

      if (fileObj) {
        return validation === 'valid';
      } else {
        return !entry.required;
      }
    });
  }, [csvConfigs, csvFiles, csvValidation]);

  /**
   * アップロードファイル設定を生成
   */
  const getUploadFileConfigs = useCallback((): UploadFileConfig[] => {
    return csvConfigs.map((entry: CsvConfigEntry): UploadFileConfig => {
      const label = entry.config.label;
      return {
        label,
        file: csvFiles[label] ?? null,
        onChange: (f: File | null) => {
          onUploadFile(label, f);
          if (f === null) {
            csvValidation.resetValidation(label);
          }
        },
        required: entry.required,
        validationResult: csvValidation.getValidationResult(label),
        onRemove: () => handleRemoveFile(label),
      };
    });
  }, [csvConfigs, csvFiles, onUploadFile, csvValidation, handleRemoveFile]);

  /**
   * MakeUploadProps関数を生成
   */
  const createMakeUploadProps = useCallback((): MakeUploadPropsFn => {
    return (label: string): UploadProps => {
      // ラベルに対応するcsvConfigエントリを検索
      let entry = null;
      for (let i = 0; i < csvConfigs.length; i++) {
        if (csvConfigs[i].config.label === label) {
          entry = csvConfigs[i];
          break;
        }
      }

      if (!entry) {
        console.warn(`CSV config not found for label: ${label}`);
        return {};
      }

      // parserを取得してmakeUploadPropsに渡す
      return makeUploadProps(label, entry.config.onParse);
    };
  }, [csvConfigs, makeUploadProps]);

  /**
   * レポート生成処理（ZIP形式）
   */
  const handleGenerateReport = useCallback(
    async (onStart: () => void, onComplete: () => void, onSuccess: () => void) => {
      const success = await artifact.generateReport(csvFiles, reportKey, onStart, onComplete);

      if (success) {
        onSuccess();
      }
    },
    [artifact, csvFiles, reportKey]
  );

  return {
    // 状態
    validationResults: csvValidation.validationResults,

    // Excel/PDF関連
    excelUrl: artifact.excelUrl,
    pdfUrl: artifact.pdfUrl,
    pdfStatus: artifact.pdfStatus, // 🔄 PDF非同期生成ステータス
    excelFileName: artifact.excelFileName,
    pdfFileName: artifact.pdfFileName,
    hasExcel: Boolean(artifact.excelUrl),
    hasPdf: Boolean(artifact.pdfUrl),
    pdfPreviewUrl: artifact.pdfUrl,
    reportToken: artifact.reportToken,
    reportDate: artifact.reportDate,
    reportKey: artifact.reportKey,
    summary: artifact.summary,
    metadata: artifact.metadata,
    lastResponse: artifact.lastResponse,

    // 計算されたプロパティ
    isReadyToCreate: isReadyToCreate(),
    uploadFileConfigs: getUploadFileConfigs(),
    makeUploadPropsFn: createMakeUploadProps(),
    isReportReady: artifact.isReady,

    // アクション
    handleRemoveFile,
    handleGenerateReport,
    downloadExcel: artifact.downloadExcel,
    printPdf: artifact.printPdf,
    getPdfPreviewUrl: artifact.getPdfPreviewUrl,
    cleanup: artifact.cleanup,
    applyArtifactResponse: artifact.applyArtifactResponse,
  };
};
