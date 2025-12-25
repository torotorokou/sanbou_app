/**
 * PreviewFactory - Fallback プレビューデータ生成
 *
 * CSV未アップロード時に表示するプレビューを生成:
 * - empty: 空テーブル（ヘッダーのみ、行0）
 * - schema: ヘッダー + ダミー行2行
 * - sample: ヘッダー + サンプルデータ3〜5行
 */

import type { CsvPreviewData, FallbackMode } from '../model/types';
import { getHeadersByType } from '../model/schema';

/**
 * Empty モード: ヘッダーのみ、行0
 */
function createEmptyPreview(typeKey: string): CsvPreviewData {
  const columns = getHeadersByType(typeKey);
  return {
    columns,
    rows: [],
  };
}

/**
 * Schema モード: ヘッダー + ダミー行2行
 */
function createSchemaPreview(typeKey: string): CsvPreviewData {
  const columns = getHeadersByType(typeKey);
  const dummyRow = columns.map((col, i) => `${col}_${i + 1}`);

  return {
    columns,
    rows: [dummyRow, dummyRow.map((v) => `${v}_2`)],
  };
}

/**
 * Sample モード: ヘッダー + サンプルデータ
 */
function createSamplePreview(typeKey: string): CsvPreviewData {
  const columns = getHeadersByType(typeKey);

  // typeKey に応じたサンプルデータ
  const samples: Record<string, string[][]> = {
    shogun_flash_ship: [
      ['2025-11-01', 'SH-001', 'ABC商事', 'XYZ物流', '鋼材', '100', 'トン', '至急'],
      ['2025-11-02', 'SH-002', 'DEF工業', 'PQR運輸', 'セメント', '50', '袋', ''],
      ['2025-11-03', 'SH-003', 'GHI建設', 'STU配送', '砂利', '200', 'm³', '通常'],
    ],
    shogun_flash_receive: [
      ['2025-11-01', 'RC-001', 'ABC商事', '鋼材', '100', 'トン', 'A棟1階'],
      ['2025-11-02', 'RC-002', 'DEF工業', 'セメント', '50', '袋', 'B棟2階'],
    ],
    shogun_flash_yard: [
      ['第1ヤード', '鋼材', '500', 'トン', '2025-11-10'],
      ['第2ヤード', 'セメント', '300', '袋', '2025-11-09'],
      ['第3ヤード', '砂利', '1000', 'm³', '2025-11-08'],
    ],
    manifest_primary: [
      ['MF-2025-001', '2025-11-01', 'ABC産廃', '廃プラスチック', '500', 'kg', 'DEF運輸'],
      ['MF-2025-002', '2025-11-02', 'GHI工場', '金属くず', '1000', 'kg', 'JKL運送'],
    ],
    manifest_secondary: [
      ['MF-2025-001', 'MNO処分場', '焼却', '2025-11-05', 'PQR最終処分場'],
      ['MF-2025-002', 'STU再資源化', 'リサイクル', '2025-11-06', 'VWX再生センター'],
    ],
  };

  // 将軍_最終版は速報版と同じサンプル
  const sampleRows = samples[typeKey] ??
    samples[typeKey.replace('final', 'flash')] ?? [columns.map((col, i) => `サンプル${i + 1}`)];

  return {
    columns,
    rows: sampleRows,
  };
}

/**
 * Fallback プレビューデータ生成
 */
export function createFallbackPreview(typeKey: string, mode: FallbackMode): CsvPreviewData {
  switch (mode) {
    case 'empty':
      return createEmptyPreview(typeKey);
    case 'schema':
      return createSchemaPreview(typeKey);
    case 'sample':
      return createSamplePreview(typeKey);
    default:
      return createEmptyPreview(typeKey);
  }
}
