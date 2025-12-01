/**
 * DatasetPreviewVM - プレビュータブ構築ロジック
 */

import { useMemo } from 'react';
import type { PreviewSource, TabDef } from '../model/types';
import { getCsvListSorted, findCsv } from '../../config';
import { createFallbackPreview } from '../factory/previewFactory';
import { getHeadersByType } from '../model/schema';
import type { CsvTypeKey } from '../../config';

const DEFAULT_CSV_COLOR = '#777777';

export function useDatasetPreviewVM(source: PreviewSource) {
  const tabs: TabDef[] = useMemo(() => {
    // kind: 'fallback' - datasetKey のみでタブ生成
    if (source.kind === 'fallback') {
      const csvList = getCsvListSorted(source.datasetKey);
      
      return csvList.map(csv => {
        return {
          key: csv.typeKey,
          label: csv.label.split(':')[1] ?? csv.label, // "将軍_速報版:出荷一覧" → "出荷一覧"
          color: csv.color ?? DEFAULT_CSV_COLOR,
          preview: createFallbackPreview(csv.typeKey, source.mode),
          required: csv.required,
          status: 'unknown' as const,
          fallbackColumns: getHeadersByType(csv.typeKey), // schema.ts からヘッダーを取得
        };
      });
    }
    
    // kind: 'previews' - 既存データから構築
    if (source.kind === 'previews') {
      const keys = Object.keys(source.data) as CsvTypeKey[];
      const csvList = getCsvListSorted(source.datasetKey);
      
      // config の順序に従ってソート
      const sorted = keys.sort((a, b) => {
        const csvA = csvList.find(c => c.typeKey === a);
        const csvB = csvList.find(c => c.typeKey === b);
        if (!csvA || !csvB) return 0;
        return csvA.order - csvB.order;
      });
      
      return sorted.map(k => {
        const csv = findCsv(source.datasetKey, k);
        return {
          key: k,
          label: csv?.label.split(':')[1] ?? k,
          color: csv?.color ?? DEFAULT_CSV_COLOR,
          preview: source.data[k],
          required: csv?.required ?? true,
          status: 'unknown' as const,
        };
      });
    }
    
    // TODO: files / uploadId の分岐は Repository 経由でプレビューを構築
    return [];
  }, [source]);

  return { tabs };
}
