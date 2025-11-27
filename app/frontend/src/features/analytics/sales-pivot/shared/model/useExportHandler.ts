/**
 * features/analytics/sales-pivot/shared/model/useExportHandler.ts
 * CSV出力ハンドラー
 */

import { useCallback } from 'react';
import type { SummaryQuery, ExportOptions, Mode } from './types';
import type { HttpSalesPivotRepository } from '../api/salesPivot.repository';
import { axisLabel } from './metrics';
import { downloadBlob } from '../lib/utils';

interface ExportHandlerParams {
  repository: HttpSalesPivotRepository;
  query: SummaryQuery;
  exportOptions: ExportOptions;
  repIds: string[];
  baseAx: Mode;
  periodLabel: string;
  message?: { success?: (msg: string) => void; error?: (msg: string) => void };
}

export function useExportHandler(params: ExportHandlerParams) {
  const { repository, query, exportOptions, repIds, baseAx, periodLabel, message } = params;

  const handleExport = useCallback(async () => {
    if (repIds.length === 0) return;
    try {
      const blob = await repository.exportModeCube({
        ...query,
        options: exportOptions,
        targetRepIds: repIds,
      });
      downloadBlob(blob, `csv_${axisLabel(baseAx)}_${periodLabel}.csv`);
      message?.success?.('CSVを出力しました。');
    } catch (e) {
      console.error(e);
      message?.error?.('CSV出力でエラーが発生しました。');
    }
  }, [repository, query, exportOptions, repIds, baseAx, periodLabel, message]);

  return { handleExport };
}
