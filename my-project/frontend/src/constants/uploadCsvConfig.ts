// src/constants/uploadCsvConfig.ts

export const UPLOAD_CSV_TYPES = ['shipment', 'receive', 'yard'] as const;
export type UploadCsvType = (typeof UPLOAD_CSV_TYPES)[number];

export type UploadCsvDefinition = {
    type: UploadCsvType;
    label: string;
    required: boolean;
};

export const UPLOAD_CSV_DEFINITIONS: Record<
    UploadCsvType,
    UploadCsvDefinition
> = {
    shipment: { type: 'shipment', label: '出荷一覧', required: true },
    receive: { type: 'receive', label: '受入一覧', required: true },
    yard: { type: 'yard', label: 'ヤード一覧', required: true },
};
