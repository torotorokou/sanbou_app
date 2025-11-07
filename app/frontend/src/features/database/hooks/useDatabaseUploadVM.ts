/**
 * データベースアップロード ViewModel
 * 
 * 責務:
 * - ファイル選択・削除の状態管理（typeKeyで管理）
 * - 即時バリデーション（必須ヘッダチェック）
 * - アップロード可否判定
 * - アップロード実行
 * - データセット切替対応
 */

import { useEffect, useMemo, useState } from 'react';
import { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES } from '../model/sampleCsvModel';
import type { PanelFileItem, ValidationStatus } from '../model/types';
import { DatabaseUploadRepositoryImpl } from '../repository/DatabaseUploadRepositoryImpl';
import { collectTypesForDataset, requiredTypesForDataset, type DatasetKey } from '../model/dataset';

export interface UseDatabaseUploadVMOptions {
  datasetKey?: DatasetKey;
}

export function useDatabaseUploadVM(opts?: UseDatabaseUploadVMOptions) {
  const datasetKey = opts?.datasetKey ?? 'shogun_flash';
  const repo = useMemo(() => new DatabaseUploadRepositoryImpl(), []);
  
  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [status, setStatus] = useState<Record<string, ValidationStatus>>({});
  const [uploading, setUploading] = useState(false);

  // active type keys for current dataset
  const activeTypes = useMemo(
    () => collectTypesForDataset(datasetKey),
    [datasetKey]
  );

  // 初期キー生成（typeKeyベース）
  useEffect(() => {
    const initFiles: Record<string, File | null> = {};
    const initStatus: Record<string, ValidationStatus> = {};
    for (const t of UPLOAD_CSV_TYPES as string[]) {
      initFiles[t] = null;
      initStatus[t] = 'unknown';
    }
    setFiles(initFiles);
    setStatus(initStatus);
  }, []);

  /**
   * 必須ヘッダの簡易検証（先頭行のみチェック）
   */
  const validateHeaders = async (typeKey: string, file: File): Promise<ValidationStatus> => {
    try {
      const text = await file.text();
      const firstLine = text.split(/\r?\n/)[0] ?? '';
      const headers = firstLine.split(',').map(s => s.trim());
      
      const def = UPLOAD_CSV_DEFINITIONS[typeKey];
      const req = def?.requiredHeaders ?? [];
      
      // 必須ヘッダが定義されていない場合は valid とする
      if (req.length === 0) return 'valid';
      
      const ok = req.every((h: string) => headers.includes(h));
      return ok ? 'valid' : 'invalid';
    } catch {
      return 'invalid';
    }
  };

  /**
   * ファイル選択時のハンドラ（必ずtypeKeyで保存）
   */
  const onPickFile = async (typeKey: string, file: File) => {
    // 1) 保存（必ず typeKey で）
    setFiles(prev => ({ ...prev, [typeKey]: file }));
    
    // 2) 即時検証
    const s = await validateHeaders(typeKey, file);
    setStatus(prev => ({ ...prev, [typeKey]: s }));
  };

  /**
   * ファイル削除時のハンドラ
   */
  const onRemoveFile = (typeKey: string) => {
    setFiles(prev => ({ ...prev, [typeKey]: null }));
    setStatus(prev => ({ ...prev, [typeKey]: 'unknown' }));
  };

  /**
   * Viewに渡す一覧（PanelFileItem[]）
   * activeTypes のみに限定
   */
  const panelFiles: PanelFileItem[] = useMemo(() => {
    return activeTypes.map(typeKey => {
      const def = UPLOAD_CSV_DEFINITIONS[typeKey];
      return {
        typeKey,
        label: def?.label ?? typeKey,
        required: def?.required !== false, // デフォルトはtrue
        file: files[typeKey] ?? null,
        status: (status[typeKey] ?? 'unknown') as ValidationStatus,
      };
    });
  }, [files, status, activeTypes]);

  /**
   * アップロード可否（必須がすべてvalid & file存在）
   * datasetの必須タイプのみをチェック
   */
  const canUpload = useMemo(() => {
    const requiredKeys = requiredTypesForDataset(datasetKey, activeTypes);
    
    if (requiredKeys.length === 0) return false;
    
    return requiredKeys.every(t => {
      const f = files[t];
      const s = status[t];
      return !!f && s === 'valid';
    });
  }, [files, status, datasetKey, activeTypes]);

  /**
   * アップロード実行
   * activeTypes に限定してファイルを送信
   */
  const doUpload = async () => {
    const filesByType: Record<string, File> = {};
    for (const k of activeTypes) {
      const v = files[k];
      if (v) filesByType[k] = v;
    }
    
    if (Object.keys(filesByType).length === 0) return;
    
    setUploading(true);
    try {
      await repo.upload(filesByType);
    } catch (error) {
      // エラーは Repository 側で通知済み
      console.error('Upload failed:', error);
    } finally {
      setUploading(false);
    }
  };

  return {
    panelFiles,
    canUpload,
    uploading,
    onPickFile,    // (typeKey, file)
    onRemoveFile,  // (typeKey)
    doUpload,
  };
}
