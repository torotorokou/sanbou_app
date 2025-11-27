/**
 * DatasetPreviewRepositoryImpl - Repository 実装
 */

import type { DatasetPreviewRepository } from './DatasetPreviewRepository';
import type { DatasetKey, CsvPreviewData } from '../model/types';
import { PreviewClient } from '../api/client';

export class DatasetPreviewRepositoryImpl implements DatasetPreviewRepository {
  async getPreviewsByUploadId(
    dataset: DatasetKey, 
    uploadId: string, 
    signal?: AbortSignal
  ): Promise<Record<string, CsvPreviewData>> {
    const json = await PreviewClient.get(
      `/core_api/datasets/${dataset}/uploads/${uploadId}/previews`, 
      signal
    );
    return json as Record<string, CsvPreviewData>;
  }
}
