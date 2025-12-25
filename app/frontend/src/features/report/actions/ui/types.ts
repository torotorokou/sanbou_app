export interface ActionsSectionProps {
  onGenerate: () => void;
  readyToCreate: boolean;
  finalized: boolean;
  onDownloadExcel: () => void;
  onPrintPdf?: () => void;
  pdfUrl: string | null;
  excelReady: boolean;
  pdfReady: boolean;
  compactMode?: boolean;
}
