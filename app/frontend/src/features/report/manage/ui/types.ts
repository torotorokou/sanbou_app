export interface CsvUploadFileType {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean;
    validationResult?: 'ok' | 'ng' | 'unknown';
}
