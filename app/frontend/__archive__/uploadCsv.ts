// アップロード画面専用の必須CSV定義
export const UPLOAD_CSV_TYPES = ['shipment', 'receive', 'yard'] as const;
export type UploadCsvType = (typeof UPLOAD_CSV_TYPES)[number];

export type UploadCsvDefinition = {
    type: UploadCsvType;
    label: string;
    required: boolean; // アップロード画面時のみの必須フラグ
};

// 必要に応じてCSV_DEFINITIONSやonParse、expectedHeadersとの連携も可能
export const UPLOAD_CSV_DEFINITIONS: Record<
    UploadCsvType,
    UploadCsvDefinition
> = {
    shipment: { type: 'shipment', label: '出荷一覧', required: true },
    receive: { type: 'receive', label: '受入一覧', required: false },
    yard: { type: 'yard', label: 'ヤード一覧', required: false },
};
