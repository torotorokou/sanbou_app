/**
 * shared/model/useExportOptions.ts
 * エクスポートオプション状態管理用カスタムフック
 */

import { useState, useEffect } from "react";
import type { ExportOptions } from "./types";
import { DEFAULT_EXPORT_OPTIONS } from "../lib/utils";

const STORAGE_KEY = "exportOptions_v1";

/**
 * エクスポートオプション状態管理の戻り値
 */
export interface ExportOptionsState {
  exportOptions: ExportOptions;
  setExportOptions: (
    options: ExportOptions | ((prev: ExportOptions) => ExportOptions),
  ) => void;
}

/**
 * エクスポートオプションの状態を管理するカスタムフック
 *
 * @description
 * - localStorageと自動連携
 * - 初期値はlocalStorageから取得、なければデフォルト値
 * - 変更時に自動でlocalStorageに保存
 *
 * @returns {ExportOptionsState} エクスポートオプション状態とセッター関数
 */
export function useExportOptions(): ExportOptionsState {
  const [exportOptions, setExportOptions] = useState<ExportOptions>(() => {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      return raw ? (JSON.parse(raw) as ExportOptions) : DEFAULT_EXPORT_OPTIONS;
    } catch {
      return DEFAULT_EXPORT_OPTIONS;
    }
  });

  useEffect(() => {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(exportOptions));
  }, [exportOptions]);

  return {
    exportOptions,
    setExportOptions,
  };
}
