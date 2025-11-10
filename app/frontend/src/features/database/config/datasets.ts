/**
 * データセット設定レジストリ
 * 
 * 既存の分散定義（constants.ts, colors.ts, rules.ts など）から集約した実体定義。
 * すべてのデータセット（将軍_速報版、将軍_最終版、マニフェスト）の
 * CSV種別、ラベル、色、順序、必須ヘッダ、ファイル名ヒント、
 * プレビュー設定、アップロード先を一元管理する。
 */

import type { DatasetConfig } from './types';

export const DATASETS: Readonly<Record<string, DatasetConfig>> = {
  shogun_flash: {
    key: 'shogun_flash',
    label: '将軍_速報版',
    schemaVersion: 1,
    notes: [
      '⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。',
      '自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。',
    ],
    upload: {
      path: '/core_api/database/upload/syogun_csv',
      payloadShape: 'formData',
    },
    csv: [
      {
        typeKey: 'shogun_flash_receive',
        label: '将軍_速報版:受入一覧',
        required: true,
        order: 1,
        color: '#0EA5E9',
        filenameHints: ['受入', 'ukeire', 'receive'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '売上日付', '支払日付', '業者CD', '業者名'],
          rowSchemaName: 'row_shogun_receive_v1',
        },
      },
      {
        typeKey: 'shogun_flash_ship',
        label: '将軍_速報版:出荷一覧',
        required: true,
        order: 2,
        color: '#3B82F6',
        filenameHints: ['出荷', 'shukka', 'shipment', 'ship'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '出荷番号', '取引先名', '業者CD', '業者名'],
          rowSchemaName: 'row_shogun_shipment_v1',
        },
      },
      {
        typeKey: 'shogun_flash_yard',
        label: '将軍_速報版:ヤード一覧',
        required: true,
        order: 3,
        color: '#06B6D4',
        filenameHints: ['ヤード', 'yard'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '取引先名', '品名', '正味重量', '数量'],
          rowSchemaName: 'row_shogun_yard_v1',
        },
      },
    ],
  },
  shogun_final: {
    key: 'shogun_final',
    label: '将軍_最終版',
    schemaVersion: 1,
    notes: [
      '⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。',
      '自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。',
      '速報版と混在させないこと。',
    ],
    upload: {
      path: '/core_api/database/upload/syogun_csv',
      payloadShape: 'formData',
    },
    csv: [
      {
        typeKey: 'shogun_final_receive',
        label: '将軍_最終版:受入一覧',
        required: true,
        order: 1,
        color: '#059669',
        filenameHints: ['受入', 'ukeire', 'receive'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '売上日付', '支払日付', '業者CD', '業者名'],
          rowSchemaName: 'row_shogun_receive_v1',
        },
      },
      {
        typeKey: 'shogun_final_ship',
        label: '将軍_最終版:出荷一覧',
        required: true,
        order: 2,
        color: '#10B981',
        filenameHints: ['出荷', 'shukka', 'shipment', 'ship'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '出荷番号', '取引先名', '業者CD', '業者名'],
          rowSchemaName: 'row_shogun_shipment_v1',
        },
      },
      {
        typeKey: 'shogun_final_yard',
        label: '将軍_最終版:ヤード一覧',
        required: true,
        order: 3,
        color: '#34D399',
        filenameHints: ['ヤード', 'yard'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['伝票日付', '取引先名', '品名', '正味重量', '数量'],
          rowSchemaName: 'row_shogun_yard_v1',
        },
      },
    ],
  },
  manifest: {
    key: 'manifest',
    label: 'マニフェスト（1次・2次）',
    schemaVersion: 1,
    notes: [
      '⚠️ マニフェストデータは正確性が求められます。',
      '公的書類からの情報を正確に入力してください。',
      '一次/二次を間違えないこと。',
    ],
    upload: {
      path: '/core_api/database/upload/syogun_csv',
      payloadShape: 'formData',
    },
    csv: [
      {
        typeKey: 'manifest_primary',
        label: 'マニフェスト:1次マニ',
        required: true,
        order: 1,
        color: '#F59E0B',
        filenameHints: ['1次', 'primary', 'プライマリ', '一次'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['マニフェスト番号', '処分方法'],
          rowSchemaName: 'row_manifest_primary_v1',
        },
      },
      {
        typeKey: 'manifest_secondary',
        label: 'マニフェスト:2次マニ',
        required: true,
        order: 2,
        color: '#F97316',
        filenameHints: ['2次', 'secondary', 'セカンダリ', '二次'],
        parse: { encoding: 'sjis', delimiter: ',' },
        preview: { columnWidth: 120, stickyHeader: true },
        validate: {
          requiredHeaders: ['マニフェスト番号', '処分方法'],
          rowSchemaName: 'row_manifest_secondary_v1',
        },
      },
    ],
  },
} as const;

/**
 * typeKey から必須ヘッダーを取得するヘルパー関数
 * adapters などから使用して、ヘッダー定義を一元化する
 */
export function getRequiredHeaders(typeKey: string): string[] | undefined {
  for (const dataset of Object.values(DATASETS)) {
    const csv = dataset.csv.find((c) => c.typeKey === typeKey);
    if (csv) {
      return csv.validate.requiredHeaders;
    }
  }
  return undefined;
}
