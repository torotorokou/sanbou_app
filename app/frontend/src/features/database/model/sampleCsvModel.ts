// サンプルのCSV定義（開発・プレゼン用）
// 実運用では @features/database/model の定義に置き換えてください。

export type UploadCsvDefinition = {
  label: string;
  group: string;
  required?: boolean;
  requiredHeaders?: string[];
};

export const UPLOAD_CSV_DEFINITIONS: Record<string, UploadCsvDefinition> = {
  shogun_flash_ship:   { label: '将軍_速報版：出荷一覧',  group: 'shogun_flash', required: true },
  shogun_flash_receive:{ label: '将軍_速報版：受入一覧',  group: 'shogun_flash', required: true },
  shogun_flash_yard:   { label: '将軍_速報版：ヤード一覧', group: 'shogun_flash', required: true },

  shogun_final_ship:   { label: '将軍_最終版：出荷一覧',  group: 'shogun_final', required: true },
  shogun_final_receive:{ label: '将軍_最終版：受入一覧',  group: 'shogun_final', required: true },
  shogun_final_yard:   { label: '将軍_最終版：ヤード一覧', group: 'shogun_final', required: true },

  manifest_primary:    { label: 'マニフェスト：1次マニ', group: 'manifest', required: true },
  manifest_secondary:  { label: 'マニフェスト：2次マニ', group: 'manifest', required: true },
};

export const UPLOAD_CSV_TYPES: string[] = Object.keys(UPLOAD_CSV_DEFINITIONS);

export const csvTypeColors: Record<string, string> = {
  shogun_flash_ship: '#3B82F6',
  shogun_flash_receive: '#0EA5E9',
  shogun_flash_yard: '#06B6D4',
  shogun_final_ship: '#10B981',
  shogun_final_receive: '#059669',
  shogun_final_yard: '#34D399',
  manifest_primary: '#F59E0B',
  manifest_secondary: '#F97316',
};
