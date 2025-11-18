/**
 * ファイル選択時の検証フック
 * 共通のcsvHeaderValidatorを使用
 */

import { useCallback } from 'react';
import { validateHeaders } from '@shared';

export function useValidateOnPick(
  getRequired: (typeKey: string) => string[] | undefined
) {
  return useCallback(
    async (typeKey: string, file: File) => {
      const req = getRequired(typeKey) ?? [];
      if (req.length === 0) {
        // 必須ヘッダーが定義されていない場合は検証スキップ
        return 'unknown' as const;
      }
      return await validateHeaders(file, req);
    },
    [getRequired]
  );
}
