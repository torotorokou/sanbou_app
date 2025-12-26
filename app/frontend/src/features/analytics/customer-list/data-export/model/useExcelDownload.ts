/**
 * Excel Download Hook
 *
 * Excelダウンロードの状態管理とロジック
 */

import { useState } from 'react';
import { notifySuccess, notifyError } from '@features/notification';
import type { Dayjs } from 'dayjs';

export interface ExcelDownloadViewModel {
  isDownloading: boolean;
  handleDownload: (
    currentStart: Dayjs | null,
    currentEnd: Dayjs | null,
    previousStart: Dayjs | null,
    previousEnd: Dayjs | null
  ) => Promise<void>;
}

/**
 * Excelダウンロード機能のHook
 *
 * @param apiPostBlob - API呼び出し関数（DI）
 */
export function useExcelDownload(
  apiPostBlob: <T>(url: string, data: T) => Promise<Blob>
): ExcelDownloadViewModel {
  const [isDownloading, setIsDownloading] = useState(false);

  const handleDownload = async (
    currentStart: Dayjs | null,
    currentEnd: Dayjs | null,
    previousStart: Dayjs | null,
    previousEnd: Dayjs | null
  ) => {
    setIsDownloading(true);
    try {
      const blob = await apiPostBlob<Record<string, string | undefined>>(
        '/core_api/customer-comparison/excel',
        {
          targetStart: currentStart?.format('YYYY-MM'),
          targetEnd: currentEnd?.format('YYYY-MM'),
          compareStart: previousStart?.format('YYYY-MM'),
          compareEnd: previousEnd?.format('YYYY-MM'),
        }
      );

      const url = window.URL.createObjectURL(blob);
      const link = document.createElement('a');
      link.href = url;
      link.setAttribute('download', '顧客比較リスト.xlsx');
      document.body.appendChild(link);
      link.click();
      link.parentNode?.removeChild(link);
      window.URL.revokeObjectURL(url);

      notifySuccess('ダウンロード完了', 'エクセルをダウンロードしました');
    } catch {
      notifyError('エラー', 'ダウンロードに失敗しました');
    } finally {
      setIsDownloading(false);
    }
  };

  return {
    isDownloading,
    handleDownload,
  };
}
