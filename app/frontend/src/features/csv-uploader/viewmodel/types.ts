/**
 * 旧 CsvUploadPanelComponent の互換 props 定義。
 * 初期は互換性重視で緩く受け、段階的に厳格化していく。
 */
export type CsvUploadPanelProps = {
  datasetKey?: string;
  accept?: string;           // default: ".csv"
  maxSizeMB?: number;        // default: 20
  onSuccess?: (payload: unknown) => void;
  onError?: (e: unknown) => void;
  className?: string;
  [key: string]: unknown;    // 既存呼び出し側の暫定互換
};
