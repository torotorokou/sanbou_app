/**
 * dataset-submit hooks: useSubmitVM
 * アップロード送信を管理するViewModel
 */

import { useMemo, useState, useRef } from 'react';
import { DatasetImportRepositoryImpl } from '../../dataset-import/repository/DatasetImportRepositoryImpl';

export function useSubmitVM() {
  const repo = useMemo(() => new DatasetImportRepositoryImpl(), []);
  const [uploading, setUploading] = useState(false);
  const [uploadSuccess, setUploadSuccess] = useState(false);
  // 実行中フラグ（useRefで同期的にチェック）
  const isExecutingRef = useRef(false);

  const doUpload = async (filesByType: Record<string, File>, uploadPath: string) => {
    if (!Object.keys(filesByType).length) return;
    
    // useRefで同期的にチェック（React renderingのタイミング問題を回避）
    if (isExecutingRef.current) {
      console.warn('Already executing upload. Ignoring duplicate request.');
      return;
    }
    
    // 既にアップロード中の場合は実行しない（二重送信防止）
    if (uploading) {
      console.warn('Already uploading. Ignoring duplicate upload request.');
      return;
    }
    // 既に成功済みの場合は実行しない
    if (uploadSuccess) {
      console.warn('Upload already succeeded. Please reset before uploading again.');
      return;
    }
    
    // 実行開始
    isExecutingRef.current = true;
    setUploading(true);
    try {
      await repo.upload(filesByType, uploadPath);
      setUploadSuccess(true);
    } catch (error) {
      // エラー時は成功状態をリセット
      setUploadSuccess(false);
      // エラーをログ出力し、rethrowする（呼び出し側でキャッチ）
      console.error('Upload error:', error);
      throw error;
    } finally {
      // 確実にuploadingをfalseにする（モーダルを閉じる）
      isExecutingRef.current = false;
      setUploading(false);
    }
  };

  const resetUploadState = () => {
    setUploadSuccess(false);
    setUploading(false);
    isExecutingRef.current = false;
  };

  return { uploading, uploadSuccess, doUpload, resetUploadState };
}
