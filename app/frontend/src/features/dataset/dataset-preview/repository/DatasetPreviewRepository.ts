/**
 * DatasetPreviewRepository - インターフェース
 */

import type { DatasetKey, CsvPreviewData } from "../model/types";

export interface DatasetPreviewRepository {
  getPreviewsByUploadId(
    dataset: DatasetKey,
    uploadId: string,
    signal?: AbortSignal,
  ): Promise<Record<string, CsvPreviewData>>;
}
