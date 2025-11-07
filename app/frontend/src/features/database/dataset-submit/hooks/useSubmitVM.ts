/**
 * dataset-submit hooks: useSubmitVM
 * アップロード送信を管理するViewModel
 */

import { useMemo, useState } from 'react';
import { DatasetImportRepositoryImpl } from '../../dataset-import/repository/DatasetImportRepositoryImpl';

export function useSubmitVM() {
  const repo = useMemo(() => new DatasetImportRepositoryImpl(), []);
  const [uploading, setUploading] = useState(false);

  const doUpload = async (filesByType: Record<string, File>) => {
    if (!Object.keys(filesByType).length) return;
    setUploading(true);
    try {
      await repo.upload(filesByType);
    } finally {
      setUploading(false);
    }
  };

  return { uploading, doUpload };
}
