import type { UploadProps } from "antd";
import type { ValidationStatus } from "@/shared";

// CsvFileType 型定義（旧 features/database から移行）
// Note: features/database からこの型は削除されました
export interface CsvUploadFileType {
  label: string;
  file: File | null;
  onChange: (file: File | null) => void;
  validationResult?: "ok" | "ng" | "unknown"; // レガシー表記（互換性のため残す）
  required: boolean;
  onRemove?: () => void;
}

// UploadFileConfigと互換性のある型定義（共通のValidationStatusを使用）
export interface CsvFileType {
  label: string;
  file: File | null;
  onChange: (file: File | null) => void;
  validationResult?: ValidationStatus;
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
  /** 半画面以下のコンパクトモード（レイアウト: 左にサンプル+アップロード、右にプレビュー、ボタンは下部） */
  compactMode?: boolean;
}

export interface SampleSectionProps {
  sampleImageUrl?: string;
}

export interface CsvUploadSectionProps {
  uploadFiles: CsvUploadFileType[];
  makeUploadProps: (label: string) => UploadProps;
}
