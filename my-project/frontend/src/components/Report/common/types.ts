import type { UploadProps } from 'antd';
import type { CsvFileType as CsvUploadFileType } from '../../common/csv-upload/types';

// UploadFileConfigと互換性のある型定義
export interface CsvFileType {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    validationResult?: 'valid' | 'invalid' | 'unknown';
    required: boolean;
    onRemove?: () => void;
}

export interface ActionsSectionProps {
    onGenerate: () => void;
    readyToCreate: boolean;
    finalized: boolean;
    onDownloadExcel: () => void;
    onPrintPdf?: () => void;
    excelUrl?: string | null;
    pdfUrl?: string | null;
    excelReady?: boolean;
    pdfReady?: boolean;
}

export interface SampleSectionProps {
    sampleImageUrl?: string;
}

export interface CsvUploadSectionProps {
    uploadFiles: CsvUploadFileType[];
    makeUploadProps: (
        label: string,
        setter: (file: File) => void
    ) => UploadProps;
}
