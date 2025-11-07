/**
 * データセットインポート ViewModel
 * ファイル選択、検証、送信を統括するメインフック
 */

import { useEffect, useMemo, useState } from 'react';
import { useValidateOnPick } from '../../dataset-validate/hooks/useValidateOnPick';
import { useSubmitVM } from '../../dataset-submit/hooks/useSubmitVM';
import { UPLOAD_CSV_DEFINITIONS, UPLOAD_CSV_TYPES } from '../model/constants';
import type { PanelFileItem, DatasetImportVMOptions } from '../model/types';
import type { ValidationStatus } from '../../shared/types/common';

export function useDatasetImportVM(opts?: DatasetImportVMOptions) {
  const activeTypes = useMemo(
    () => opts?.activeTypes ?? (UPLOAD_CSV_TYPES as string[]),
    [opts?.activeTypes]
  );

  const [files, setFiles] = useState<Record<string, File | null>>({});
  const [status, setStatus] = useState<Record<string, ValidationStatus>>({});

  useEffect(() => {
    const initF: Record<string, File | null> = {};
    const initS: Record<string, ValidationStatus> = {};
    activeTypes.forEach(t => {
      initF[t] = null;
      initS[t] = 'unknown';
    });
    setFiles(prev => ({ ...initF, ...prev }));
    setStatus(prev => ({ ...initS, ...prev }));
  }, [activeTypes]);

  const getRequired = (typeKey: string) => UPLOAD_CSV_DEFINITIONS[typeKey]?.requiredHeaders;
  const validateOnPick = useValidateOnPick(getRequired);
  const { uploading, doUpload } = useSubmitVM();

  const onPickFile = async (typeKey: string, file: File) => {
    setFiles(prev => ({ ...prev, [typeKey]: file }));
    const s = await validateOnPick(typeKey, file);
    setStatus(prev => ({ ...prev, [typeKey]: s }));
  };

  const onRemoveFile = (typeKey: string) => {
    setFiles(prev => ({ ...prev, [typeKey]: null }));
    setStatus(prev => ({ ...prev, [typeKey]: 'unknown' }));
  };

  const panelFiles: PanelFileItem[] = useMemo(
    () =>
      activeTypes.map(typeKey => ({
        typeKey,
        label: UPLOAD_CSV_DEFINITIONS[typeKey].label,
        required: !!UPLOAD_CSV_DEFINITIONS[typeKey].required,
        file: files[typeKey] ?? null,
        status: status[typeKey] ?? 'unknown',
      })),
    [files, status, activeTypes]
  );

  const canUpload = useMemo(() => {
    const requiredKeys = activeTypes.filter(
      t => UPLOAD_CSV_DEFINITIONS[t].required !== false
    );
    if (!requiredKeys.length) return false;
    return requiredKeys.every(t => !!files[t] && status[t] === 'valid');
  }, [files, status, activeTypes]);

  const filesForUpload = useMemo(() => {
    const out: Record<string, File> = {};
    for (const t of activeTypes) {
      const f = files[t];
      if (f) out[t] = f;
    }
    return out;
  }, [files, activeTypes]);

  const doUploadActive = () => doUpload(filesForUpload);

  return {
    panelFiles,
    canUpload,
    uploading,
    onPickFile,
    onRemoveFile,
    doUpload: doUploadActive,
  };
}
