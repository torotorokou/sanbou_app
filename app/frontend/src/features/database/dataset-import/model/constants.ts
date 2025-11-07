/**
 * dataset-import モジュールの定数
 * 既存の sampleCsvModel.ts から移設
 */

import type { CsvDefinition } from '../../shared/types/common';

export const UPLOAD_CSV_DEFINITIONS: Record<string, CsvDefinition> = {
  shogun_flash_ship:   { label: '将軍_速報版:出荷一覧',  group: 'shogun_flash', required: true },
  shogun_flash_receive:{ label: '将軍_速報版:受入一覧',  group: 'shogun_flash', required: true },
  shogun_flash_yard:   { label: '将軍_速報版:ヤード一覧', group: 'shogun_flash', required: true },

  shogun_final_ship:   { label: '将軍_最終版:出荷一覧',  group: 'shogun_final', required: true },
  shogun_final_receive:{ label: '将軍_最終版:受入一覧',  group: 'shogun_final', required: true },
  shogun_final_yard:   { label: '将軍_最終版:ヤード一覧', group: 'shogun_final', required: true },

  manifest_primary:    { label: 'マニフェスト:1次マニ', group: 'manifest', required: true },
  manifest_secondary:  { label: 'マニフェスト:2次マニ', group: 'manifest', required: true },
};

export const UPLOAD_CSV_TYPES: string[] = Object.keys(UPLOAD_CSV_DEFINITIONS);

// 互換性のため、色定義も再エクスポート
export { CSV_TYPE_COLORS as csvTypeColors } from '../../shared/ui/colors';
