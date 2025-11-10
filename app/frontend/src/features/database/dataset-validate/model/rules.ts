/**
 * バリデーションルール定義
 */

export interface ValidationRule {
  field: string;
  required?: boolean;
  pattern?: RegExp;
  minLength?: number;
  maxLength?: number;
}

export const VALIDATION_RULES: Record<string, ValidationRule[]> = {
  // 将来的な拡張用
  // shogun_flash_ship: [
  //   { field: '伝票日付', required: true },
  //   { field: '荷主', required: true },
  // ],
};

/**
 * データセット別の必須CSV定義（UploadGuide 用）
 */
export interface RequiredCsvSpec {
  typeKey: string;
  label: string;
  required: boolean;
  headers?: string[];
  filenameHints?: string[];
  sampleUrl?: string;
}

export interface DatasetRule {
  datasetKey: string;
  requiredCsv: RequiredCsvSpec[];
  globalNotes?: string[];
}

export const DATASET_RULES: Record<string, DatasetRule> = {
  shogun_flash: {
    datasetKey: 'shogun_flash',
    requiredCsv: [
      {
        typeKey: 'shogun_flash_ship',
        label: '将軍_速報版:出荷一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['出荷一覧.csv', 'shipment.csv'],
      },
      {
        typeKey: 'shogun_flash_receive',
        label: '将軍_速報版:受入一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['受入一覧.csv', 'receive.csv'],
      },
      {
        typeKey: 'shogun_flash_yard',
        label: '将軍_速報版:ヤード一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['ヤード一覧.csv', 'yard.csv'],
      },
    ],
    globalNotes: [
      '⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。',
      '自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。',
    ],
  },
  shogun_final: {
    datasetKey: 'shogun_final',
    requiredCsv: [
      {
        typeKey: 'shogun_final_ship',
        label: '将軍_最終版:出荷一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['出荷一覧.csv', 'shipment.csv'],
      },
      {
        typeKey: 'shogun_final_receive',
        label: '将軍_最終版:受入一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['受入一覧.csv', 'receive.csv'],
      },
      {
        typeKey: 'shogun_final_yard',
        label: '将軍_最終版:ヤード一覧',
        required: true,
        headers: ['伝票日付', '荷主', '品名'],
        filenameHints: ['ヤード一覧.csv', 'yard.csv'],
      },
    ],
    globalNotes: [
      '⚠️ ファイルは「将軍ソフトからダウンロードしたままの状態」でアップロードしてください。',
      '自分で編集・加工・列の並び替え・名前変更をしたファイルは使用できません。',
    ],
  },
  manifest: {
    datasetKey: 'manifest',
    requiredCsv: [
      {
        typeKey: 'manifest_primary',
        label: 'マニフェスト:1次マニ',
        required: true,
        headers: ['交付日', '排出事業者', '廃棄物種類'],
        filenameHints: ['1次マニフェスト.csv', 'primary.csv'],
      },
      {
        typeKey: 'manifest_secondary',
        label: 'マニフェスト:2次マニ',
        required: true,
        headers: ['交付日', '排出事業者', '廃棄物種類'],
        filenameHints: ['2次マニフェスト.csv', 'secondary.csv'],
      },
    ],
    globalNotes: [
      '⚠️ マニフェストデータは正確性が求められます。',
      '公的書類からの情報を正確に入力してください。',
    ],
  },
} as const;
