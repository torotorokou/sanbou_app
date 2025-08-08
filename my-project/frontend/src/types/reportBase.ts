import type { UploadProps } from 'antd/es/upload';
import type { ReportKey } from '../constants/reportConfig/managementReportConfig.tsx';

/**
 * ReportBase関連の型定義を整理
 * 型の複雑性を下げ、再利用性を向上
 */

export type CsvConfig = {
    config: {
        label: string;
        onParse: (csvText: string) => void;
    };
    required: boolean;
};

export type CsvConfigEntry = CsvConfig;

export type CsvFiles = { [csvLabel: string]: File | null };

export type ValidationResult = 'valid' | 'invalid' | 'unknown';

export type StepProps = {
    steps: string[];
    currentStep: number;
    setCurrentStep: (step: number) => void;
};

export type FileProps = {
    csvConfigs: CsvConfig[];
    files: CsvFiles;
    onUploadFile: (label: string, file: File | null) => void;
};

export type PreviewProps = {
    previewUrl: string | null;
    setPreviewUrl: (url: string | null) => void;
};

export type ModalProps = {
    modalOpen: boolean;
    setModalOpen: (b: boolean) => void;
};

export type FinalizedProps = {
    finalized: boolean;
    setFinalized: (b: boolean) => void;
};

export type LoadingProps = {
    loading: boolean;
    setLoading: (b: boolean) => void;
};

export type ReportBaseProps = {
    step: StepProps;
    file: FileProps;
    preview: PreviewProps;
    modal: ModalProps;
    finalized: FinalizedProps;
    loading: LoadingProps;
    reportKey: ReportKey;
};

export type UploadFileConfig = {
    label: string;
    file: File | null;
    onChange: (file: File | null) => void;
    required: boolean;
    validationResult: ValidationResult;
    onRemove: () => void;
};

export type MakeUploadPropsFn = (label: string) => UploadProps;
