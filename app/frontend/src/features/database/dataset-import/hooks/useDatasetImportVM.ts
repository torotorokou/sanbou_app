/**
 * データセットインポート ViewModel
 * ファイル選択、検証、送信を統括するメインフック
 * 
 * 最適化:
 * - CSVプレビュー生成処理を削除（UI フリーズ防止）
 * - 軽量なバリデーションのみ実施
 */

import { useEffect, useMemo, useState, useCallback, useRef } from 'react';
import { useValidateOnPick } from '../../dataset-validate/hooks/useValidateOnPick';
import { useSubmitVM } from '../../dataset-submit/hooks/useSubmitVM';
import { globalUploadPollingManager } from '../services/globalUploadPollingManager';
import { findCsv, getDatasetConfig } from '../../config';
import type { PanelFileItem, DatasetImportVMOptions } from '../model/types';
import type { ValidationStatus } from '../../shared/types/common';
import type { CsvPreviewData } from '../../dataset-preview/model/types';
import type { DatasetKey, CsvTypeKey } from '../../config';

export function useDatasetImportVM(opts?: DatasetImportVMOptions) {
  const datasetKey = opts?.datasetKey;
  const activeTypes = opts?.activeTypes ?? [];

  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [status, setStatus] = useState<Record<string, ValidationStatus>>({});
  const [previews, setPreviews] = useState<Record<string, CsvPreviewData | null>>({});
  const [skipped, setSkipped] = useState<Record<string, boolean>>({});
  const [uploadFileIds, setUploadFileIds] = useState<Record<string, number> | undefined>();
  const uploadFileIdsRef = useRef<Record<string, number> | undefined>();
  const isProcessingRef = useRef(false);
  const resetUploadStateRef = useRef<(() => void) | null>(null);

  // datasetKeyが変更されたら状態を初期化
  useEffect(() => {
    const newFiles: Record<string, File | null> = {};
    const newStatus: Record<string, ValidationStatus> = {};
    const newPreviews: Record<string, CsvPreviewData | null> = {};
    const newSkipped: Record<string, boolean> = {};
    
    activeTypes.forEach(t => {
      newFiles[t] = null;
      newStatus[t] = 'unknown';
      newPreviews[t] = null;
      newSkipped[t] = false;
    });
    
    setFiles(newFiles);
    setStatus(newStatus);
    setPreviews(newPreviews);
    setSkipped(newSkipped);
  }, [datasetKey]); // activeTypesではなくdatasetKeyに依存

  const getRequired = (typeKey: string) => {
    if (!datasetKey) return undefined;
    const csv = findCsv(datasetKey as DatasetKey, typeKey as CsvTypeKey);
    return csv?.validate.requiredHeaders;
  };
  const validateOnPick = useValidateOnPick(getRequired);
  const { uploading, uploadSuccess, doUpload, resetUploadState } = useSubmitVM();

  // resetUploadStateをrefに保存（最新の関数を保持）
  useEffect(() => {
    resetUploadStateRef.current = resetUploadState;
  }, [resetUploadState]);

  const onPickFile = async (typeKey: string, file: File) => {
    if (uploadSuccess) {
      resetUploadState();
    }
    setFiles(prev => ({ ...prev, [typeKey]: file }));
    
    // CSVプレビュー生成は重い処理なのでスキップ（UI フリーズ防止）
    // サーバー側で処理するため、フロントでは不要
    setPreviews(prev => ({ ...prev, [typeKey]: null }));
    
    const s = await validateOnPick(typeKey, file);
    setStatus(prev => ({ ...prev, [typeKey]: s }));
  };

  const onRemoveFile = (typeKey: string) => {
    if (uploadSuccess) {
      resetUploadState();
    }
    setFiles(prev => ({ ...prev, [typeKey]: null }));
    setStatus(prev => ({ ...prev, [typeKey]: 'unknown' }));
    setPreviews(prev => ({ ...prev, [typeKey]: null }));
    setSkipped(prev => ({ ...prev, [typeKey]: false }));
  };

  const onToggleSkip = (typeKey: string) => {
    if (uploadSuccess) {
      resetUploadState();
    }
    setSkipped(prev => ({ ...prev, [typeKey]: !prev[typeKey] }));
  };

  const panelFiles: PanelFileItem[] = useMemo(
    () =>
      activeTypes.map(typeKey => {
        const csv = datasetKey ? findCsv(datasetKey as DatasetKey, typeKey as CsvTypeKey) : undefined;
        return {
          typeKey,
          label: csv?.label ?? typeKey,
          required: csv?.required ?? false,
          file: files[typeKey] ?? null,
          status: status[typeKey] ?? 'unknown',
          preview: previews[typeKey] ?? null,
          skipped: skipped[typeKey] ?? false,
        };
      }),
    [files, status, previews, skipped, activeTypes, datasetKey]
  );

  // uploadFileIdsをrefに同期
  useEffect(() => {
    uploadFileIdsRef.current = uploadFileIds;
    isProcessingRef.current = !!uploadFileIds && Object.keys(uploadFileIds).length > 0;
  }, [uploadFileIds]);

  // バックグラウンド処理中かどうか（状態に基づいて計算）
  const isProcessing = useMemo(() => {
    return !!uploadFileIds && Object.keys(uploadFileIds).length > 0;
  }, [uploadFileIds]);

  // グローバルポーリングマネージャーの完了を監視（マウント時に1度だけ登録）
  useEffect(() => {
    // 完了コールバックを登録
    const unsubscribe = globalUploadPollingManager.onCompletion((completedFileIds, allSuccess) => {
      console.log('[useDatasetImportVM] Processing complete:', { completedFileIds, allSuccess });
      
      // 現在のuploadFileIdsのいずれかが完了した場合（refから取得）
      const currentUploadFileIds = uploadFileIdsRef.current;
      if (!currentUploadFileIds) return;
      
      const currentFileIds = Object.values(currentUploadFileIds);
      const isOurBatch = completedFileIds.some(id => currentFileIds.includes(id));
      
      if (isOurBatch) {
        console.log('[useDatasetImportVM] Our batch completed. Resetting state...');
        
        // 即座にref更新
        uploadFileIdsRef.current = undefined;
        isProcessingRef.current = false;
        
        // 状態更新
        setUploadFileIds(undefined);
        
        // uploadSuccessもリセット（refから取得して実行）
        if (resetUploadStateRef.current) {
          resetUploadStateRef.current();
        }
        
        if (allSuccess) {
          // すべて成功した場合のみファイルをクリア
          setFiles({});
          setStatus({});
          setPreviews({});
          setSkipped({});
        }
      }
    });

    // クリーンアップ（アンマウント時のみ）
    return () => {
      unsubscribe();
    };
  }, []); // 依存配列を空にして、マウント時のみ実行

  const canUpload = useMemo(() => {
    // ポーリング中はアップロード不可
    if (isProcessing) return false;

    const requiredKeys = activeTypes.filter(t => {
      if (!datasetKey) return false;
      const csv = findCsv(datasetKey as DatasetKey, t as CsvTypeKey);
      return csv?.required !== false;
    });
    if (!requiredKeys.length) return false;

    const requiredOkay = requiredKeys.every(t => skipped[t] || (!!files[t] && status[t] === 'valid'));
    const hasUploadTargets = activeTypes.some(t => !skipped[t] && !!files[t] && status[t] === 'valid');

    return requiredOkay && hasUploadTargets;
  }, [files, status, skipped, activeTypes, datasetKey, isProcessing]);

  const filesForUpload = useMemo(() => {
    const out: Record<string, File> = {};
    for (const t of activeTypes) {
      if (!skipped[t] && files[t]) {
        out[t] = files[t]!;
      }
    }
    return out;
  }, [files, skipped, activeTypes]);

  const handleUpload = useCallback(async () => {
    if (!datasetKey) {
      console.error('datasetKey が指定されていません');
      return;
    }
    
    const dataset = getDatasetConfig(datasetKey as DatasetKey);
    if (!dataset) {
      console.error(`Dataset not found: ${datasetKey}`);
      return;
    }
    
    try {
      const result = await doUpload(filesForUpload, dataset.upload.path);
      
      if (result.success) {
        console.log('Upload accepted. Starting global status polling...', result.uploadFileIds);
        
        // グローバルポーリングマネージャーに登録
        if (result.uploadFileIds && Object.keys(result.uploadFileIds).length > 0) {
          setUploadFileIds(result.uploadFileIds);
          globalUploadPollingManager.addJobs(result.uploadFileIds);
        } else {
          // upload_file_idsがない場合は即座にクリア（旧API対応）
          console.warn('No upload_file_ids returned. Clearing files immediately.');
          setFiles({});
          setStatus({});
          setPreviews({});
          setSkipped({});
        }
      }
    } catch (error) {
      console.error('[handleUpload] Upload failed:', error);
      // エラーが発生してもUIをブロックしない
      // エラー通知はuseSubmitVMで既に表示されている
    }
  }, [datasetKey, filesForUpload, doUpload]);

  const onResetAll = useCallback(() => {
    console.log('[onResetAll] Clearing all files.');
    if (uploadSuccess) {
      resetUploadState();
    }
    setFiles({});
    setStatus({});
    setPreviews({});
    setSkipped({});
  }, [uploadSuccess, resetUploadState]);

  return {
    panelFiles,
    canUpload,
    uploading,
    uploadSuccess,
    isProcessing,
    onPickFile,
    onRemoveFile,
    onToggleSkip,
    onResetAll,
    doUpload: handleUpload,
    resetUploadState,
  };
}
