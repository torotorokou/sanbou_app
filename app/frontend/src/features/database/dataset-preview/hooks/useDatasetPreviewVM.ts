/**
 * DatasetPreviewVM - プレビュータブ構築ロジック
 */

import { useMemo } from 'react';
import type { PreviewSource, TabDef, DatasetKey } from '../model/types';
import { CSV_TYPE_COLORS, DEFAULT_CSV_COLOR } from '../../shared/ui/colors';
import { collectTypesForDataset } from '../../shared/dataset/dataset';
import { UPLOAD_CSV_DEFINITIONS } from '../../dataset-import/model/constants';
import { createFallbackPreview } from '../factory/previewFactory';
import { getHeadersByType } from '../model/schema';

const TYPE_ORDER: Record<DatasetKey, string[]> = {
  shogun_flash: ['shogun_flash_ship', 'shogun_flash_receive', 'shogun_flash_yard'],
  shogun_final: ['shogun_final_ship', 'shogun_final_receive', 'shogun_final_yard'],
  manifest: ['manifest_primary', 'manifest_secondary'],
};

const TYPE_LABELS: Record<string, string> = {
  shogun_flash_ship: '出荷',
  shogun_flash_receive: '受入',
  shogun_flash_yard: 'ヤード',
  shogun_final_ship: '出荷',
  shogun_final_receive: '受入',
  shogun_final_yard: 'ヤード',
  manifest_primary: '1次',
  manifest_secondary: '2次',
};

export function useDatasetPreviewVM(source: PreviewSource) {
  const tabs: TabDef[] = useMemo(() => {
    // kind: 'fallback' - datasetKey のみでタブ生成
    if (source.kind === 'fallback') {
      const types = collectTypesForDataset(source.datasetKey);
      const order = TYPE_ORDER[source.datasetKey] ?? types;
      
      return types
        .sort((a, b) => {
          const ia = order.indexOf(a);
          const ib = order.indexOf(b);
          if (ia === -1 && ib === -1) return 0;
          if (ia === -1) return 1;
          if (ib === -1) return -1;
          return ia - ib;
        })
        .map(k => {
          const def = UPLOAD_CSV_DEFINITIONS[k];
          return {
            key: k,
            label: TYPE_LABELS[k] ?? def?.label ?? k,
            color: CSV_TYPE_COLORS[k] ?? DEFAULT_CSV_COLOR,
            preview: createFallbackPreview(k, source.mode),
            required: def?.required !== false,
            status: 'unknown' as const,
            fallbackColumns: getHeadersByType(k), // schema.ts からヘッダーを取得
          };
        });
    }
    
    // kind: 'previews' - 既存データから構築
    if (source.kind === 'previews') {
      const keys = Object.keys(source.data);
      const order = TYPE_ORDER[source.datasetKey] ?? keys;
      
      return keys
        .sort((a, b) => {
          const ia = order.indexOf(a);
          const ib = order.indexOf(b);
          if (ia === -1 && ib === -1) return 0;
          if (ia === -1) return 1;
          if (ib === -1) return -1;
          return ia - ib;
        })
        .map(k => ({
          key: k,
          label: TYPE_LABELS[k] ?? k,
          color: CSV_TYPE_COLORS[k] ?? DEFAULT_CSV_COLOR,
          preview: source.data[k],
          required: true,
          status: 'unknown' as const,
        }));
    }
    
    // TODO: files / uploadId の分岐は Repository 経由でプレビューを構築
    return [];
  }, [source]);

  return { tabs };
}
