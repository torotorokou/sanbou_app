// src/components/database/types.ts

export type CsvFileType = {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean;
    validationResult?: 'ok' | 'ng' | 'unknown';
    onRemove?: () => void;
};

export type CsvUploadCardEntry = CsvFileType;
