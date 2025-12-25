/**
 * データセット設定レジストリ - barrel export
 *
 * config レジストリのすべての公開APIをエクスポート
 */

// Types
export type { DatasetKey, CsvTypeKey, CsvConfig, DatasetConfig } from "./types";

// Dataset Registry
export { DATASETS } from "./datasets";

// Selectors (Query Functions)
export {
  getDatasetConfig,
  getCsvListSorted,
  findCsv,
  guessCsvTypeByFilename,
  getUploadEndpoint,
  getRequiredCsvTypes,
  getCsvTypeKeys,
  collectTypesForDataset,
  getCsvLabel,
  getCsvColor,
  getAllDatasets,
  getDatasetLabel,
} from "./selectors";
