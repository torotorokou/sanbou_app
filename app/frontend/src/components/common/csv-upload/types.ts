// src/components/common/csv-upload/types.ts

export type CsvFileType = {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean;
    validationResult?: 'valid' | 'invalid' | 'unknown';
    onRemove?: () => void;
};
