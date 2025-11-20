/**
 * header/model/useHeaderViewModel.ts
 * ヘッダー機能のViewModel（CSV出力管理）
 */

import { useState, useEffect, useCallback } from 'react';
import type { ExportOptions, SummaryQuery, ID } from '../../shared/model/types';
import { DEFAULT_EXPORT_OPTIONS } from '../../shared/model/types';
import type { SalesPivotRepository } from '../../shared/api/salesPivot.repository';

export interface UseHeaderViewModelParams {
  repository: SalesPivotRepository;
  query: SummaryQuery;
  repIds: ID[];
  periodLabel: string;
}

export interface UseHeaderViewModelResult {
  exportOptions: ExportOptions;
  setExportOptions: (options: ExportOptions | ((prev: ExportOptions) => ExportOptions)) => void;
  handleExport: () => Promise<Blob>;
  canExport: boolean;
}

/**
 * ヘッダーViewModel Hook
 * - Export options の永続化
 * - CSV出力処理
 */
export function useHeaderViewModel(params: UseHeaderViewModelParams): UseHeaderViewModelResult {
  const { repository, query, repIds, periodLabel } = params;

  // Export options（localStorage永続化）
  const [exportOptions, setExportOptions] = useState<ExportOptions>(() => {
    try {
      const raw = localStorage.getItem('exportOptions_v1');
      return raw ? (JSON.parse(raw) as ExportOptions) : DEFAULT_EXPORT_OPTIONS;
    } catch {
      return DEFAULT_EXPORT_OPTIONS;
    }
  });

  useEffect(() => {
    localStorage.setItem('exportOptions_v1', JSON.stringify(exportOptions));
  }, [exportOptions]);

  // CSV出力処理
  const handleExport = useCallback(async (): Promise<Blob> => {
    const blob = await repository.exportModeCube({
      ...query,
      options: exportOptions,
      targetRepIds: repIds,
    });
    return blob;
  }, [repository, query, exportOptions, repIds]);

  const canExport = repIds.length > 0;

  return {
    exportOptions,
    setExportOptions,
    handleExport,
    canExport,
  };
}
