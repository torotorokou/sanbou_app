/**
 * データセットインポート ViewModel
 * ファイル選択、検証、送信を統括するメインフック
 */

import { useEffect, useMemo, useState } from 'react';
import { useValidateOnPick } from '../../dataset-validate/hooks/useValidateOnPick';
import { useSubmitVM } from '../../dataset-submit/hooks/useSubmitVM';
import { findCsv, getDatasetConfig } from '../../config';
import type { PanelFileItem, DatasetImportVMOptions } from '../model/types';
import type { ValidationStatus } from '../../shared/types/common';
import type { CsvPreviewData } from '../../dataset-preview/model/types';
import { parseCsvPreview } from '../../shared/csv/parseCsv';
import type { DatasetKey, CsvTypeKey } from '../../config';

export function useDatasetImportVM(opts?: DatasetImportVMOptions) {
  const activeTypes = useMemo(
    () => opts?.activeTypes ?? [],
    [opts?.activeTypes]
  );
  
  const datasetKey = opts?.datasetKey;

  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [status, setStatus] = useState<Record<string, ValidationStatus>>({});
  const [previews, setPreviews] = useState<Record<string, CsvPreviewData | null>>({});
  const [skipped, setSkipped] = useState<Record<string, boolean>>({});

  useEffect(() => {
    setFiles(prev => {
      const newFiles = { ...prev };
      let changed = false;
      activeTypes.forEach(t => {
        if (!(t in newFiles)) {
          newFiles[t] = null;
          changed = true;
        }
      });
      return changed ? newFiles : prev;
    });
    
    setStatus(prev => {
      const newStatus = { ...prev };
      let changed = false;
      activeTypes.forEach(t => {
        if (!(t in newStatus)) {
          newStatus[t] = 'unknown';
          changed = true;
        }
      });
      return changed ? newStatus : prev;
    });
    
    setPreviews(prev => {
      const newPreviews = { ...prev };
      let changed = false;
      activeTypes.forEach(t => {
        if (!(t in newPreviews)) {
          newPreviews[t] = null;
          changed = true;
        }
      });
      return changed ? newPreviews : prev;
    });
    
    setSkipped(prev => {
      const newSkipped = { ...prev };
      let changed = false;
      activeTypes.forEach(t => {
        if (!(t in newSkipped)) {
          newSkipped[t] = false;
          changed = true;
        }
      });
      return changed ? newSkipped : prev;
    });
  }, [activeTypes]);

  const getRequired = (typeKey: string) => {
    if (!datasetKey) return undefined;
    const csv = findCsv(datasetKey as DatasetKey, typeKey as CsvTypeKey);
    return csv?.validate.requiredHeaders;
  };
  
  const validateOnPick = useValidateOnPick(getRequired);
  const { uploading, uploadSuccess, doUpload, resetUploadState } = useSubmitVM();

  const onPickFile = async (typeKey: string, file: File) => {
    // 新しいファイルを選択したら成功状態をリセット
    if (uploadSuccess) {
      resetUploadState();
    }
    setFiles(prev => ({ ...prev, [typeKey]: file }));
    
    // CSVファイルを読み込んでプレビューを生成
    try {
      const text = await file.text();
      const preview = parseCsvPreview(text, 100);
      setPreviews(prev => ({ ...prev, [typeKey]: preview }));
    } catch (error) {
      console.error('CSVプレビュー生成エラー:', error);
      setPreviews(prev => ({ ...prev, [typeKey]: null }));
    }
    
    const s = await validateOnPick(typeKey, file);
    setStatus(prev => ({ ...prev, [typeKey]: s }));
  };

  const onRemoveFile = (typeKey: string) => {
    // ファイル削除時に成功状態をリセット（再アップロードを可能に）
    if (uploadSuccess) {
      resetUploadState();
    }
    setFiles(prev => ({ ...prev, [typeKey]: null }));
    setStatus(prev => ({ ...prev, [typeKey]: 'unknown' }));
    setPreviews(prev => ({ ...prev, [typeKey]: null }));
    setSkipped(prev => ({ ...prev, [typeKey]: false }));
  };

  const onToggleSkip = (typeKey: string) => {
    // スキップ切り替え時に成功状態をリセット（アップロード対象が変わるため）
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

  const canUpload = useMemo(() => {
    const requiredKeys = activeTypes.filter(t => {
      if (!datasetKey) return false;
      const csv = findCsv(datasetKey as DatasetKey, t as CsvTypeKey);
      return csv?.required !== false;
    });
    if (!requiredKeys.length) return false;

    // 必須ファイルは「スキップされている」または「ファイルが選択されていてvalid」である必要がある
    const requiredOkay = requiredKeys.every(t => skipped[t] || (!!files[t] && status[t] === 'valid'));

    // さらに、実際にアップロードするファイルが1つ以上あること（全てスキップは不可）
    const hasUploadTargets = activeTypes.some(t => !skipped[t] && !!files[t] && status[t] === 'valid');

    return requiredOkay && hasUploadTargets;
  }, [files, status, skipped, activeTypes, datasetKey]);

  const filesForUpload = useMemo(() => {
    const out: Record<string, File> = {};
    for (const t of activeTypes) {
      // スキップされていないファイルのみを含める
      if (!skipped[t]) {
        const f = files[t];
        if (f) out[t] = f;
      }
    }
    return out;
  }, [files, skipped, activeTypes]);

  const doUploadActive = async () => {
    // アップロード中は実行しない（二重送信防止）
    if (uploading) {
      console.warn('Already uploading. Ignoring duplicate upload request.');
      return;
    }
    // 既に成功済みの場合は実行しない
    if (uploadSuccess) {
      console.warn('Upload already succeeded.');
      return;
    }
    // datasetKey からアップロード先のパスを取得
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
      await doUpload(filesForUpload, dataset.upload.path);
      // 成功したら全ファイルをクリア
      setFiles({});
      setStatus({});
      setPreviews({});
      setSkipped({});
    } catch (error) {
      // エラー時は状態を確実にリセット（再アップロードを可能に）
      resetUploadState();
      console.error('Upload failed:', error);
      // ファイルは保持（ユーザーが削除できる）
    }
  };

  return {
    panelFiles,
    canUpload,
    uploading,
    uploadSuccess,
    onPickFile,
    onRemoveFile,
    onToggleSkip,
    doUpload: doUploadActive,
  };
}
