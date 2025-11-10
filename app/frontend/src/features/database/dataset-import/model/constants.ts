/**
 * dataset-import モジュールの定数
 * 
 * @deprecated このファイルは config レジストリに移行済みです。
 * 新規コードでは @features/database/config を直接使用してください。
 */

import type { CsvDefinition } from '../../shared/types/common';
import { DATASETS } from '../../config';

/**
 * @deprecated config/datasets.ts を使用してください
 */
export const UPLOAD_CSV_DEFINITIONS: Record<string, CsvDefinition> = (() => {
  const result: Record<string, CsvDefinition> = {};
  for (const dataset of Object.values(DATASETS)) {
    for (const csv of dataset.csv) {
      result[csv.typeKey] = {
        label: csv.label,
        group: dataset.key,
        required: csv.required,
      };
    }
  }
  return result;
})();

/**
 * @deprecated config/selectors.getCsvTypeKeys() を使用してください
 */
export const UPLOAD_CSV_TYPES: string[] = Object.keys(UPLOAD_CSV_DEFINITIONS);

/**
 * @deprecated config/selectors.getCsvColor() を使用してください
 */
export { CSV_TYPE_COLORS as csvTypeColors } from '../../shared/ui/colors';
