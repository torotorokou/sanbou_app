// /app/src/components/Report/services/LegacyReportService.ts
import {
    identifyCsvType,
    isCsvMatch,
} from '../../../utils/validators/csvValidator';
import type {
    WorkerRow,
    ValuableRow,
    ShipmentRow,
} from '../../../types/report';

/**
 * 既存ReportFactory.tsx用のレガシーサービス
 *
 * 既存のバリデーションロジックとデータ処理ロジックを
 * 新しいシステム形式でラップ
 */

export interface LegacyValidationResult {
    shipFileValid: 'valid' | 'invalid' | 'unknown';
    yardFileValid: 'valid' | 'invalid' | 'unknown';
    receiveFileValid: 'valid' | 'invalid' | 'unknown';
}

export interface LegacyParsedData {
    workerData: WorkerRow[];
    valuableData: ValuableRow[];
    shipmentData: ShipmentRow[];
}

export class LegacyReportService {
    /**
     * CSVファイルをバリデーションして解析
     */
    static validateAndParseCSV(
        file: File,
        label: string
    ): Promise<{
        isValid: boolean;
        data: WorkerRow[] | ValuableRow[] | ShipmentRow[] | null;
    }> {
        return new Promise((resolve) => {
            const reader = new FileReader();
            reader.onload = (e) => {
                const text = e.target?.result as string;
                const rows = text.split('\n').map((row) => row.split(','));
                const body = rows.slice(1);

                // ファイルの厳密なCSVバリデーション
                const csvValidationResult = identifyCsvType(text);
                let isValid = false;
                let data: WorkerRow[] | ValuableRow[] | ShipmentRow[] | null =
                    null;

                if (label === '出荷一覧') {
                    isValid = isCsvMatch(csvValidationResult, '出荷一覧');

                    if (isValid) {
                        data = body.map((cols, i) => ({
                            key: i.toString(),
                            商品名: cols[0] || '',
                            出荷先: cols[1] || '',
                            数量: parseInt(cols[2]) || 0,
                        })) as ShipmentRow[];
                    }
                } else if (label === 'ヤード一覧') {
                    isValid = isCsvMatch(csvValidationResult, 'ヤード一覧');

                    if (isValid) {
                        data = body.map((cols, i) => ({
                            key: i.toString(),
                            氏名: cols[0] || '',
                            所属: cols[1] || '',
                            出勤区分: cols[2] || '',
                        })) as WorkerRow[];
                    }
                } else if (label === '受入一覧') {
                    isValid = isCsvMatch(csvValidationResult, '受入一覧');

                    if (isValid) {
                        data = body.map((cols, i) => ({
                            key: i.toString(),
                            品目: cols[0] || '',
                            重量: parseFloat(cols[1]) || 0,
                            単価: parseFloat(cols[2]) || 0,
                        })) as ValuableRow[];
                    }
                }

                resolve({ isValid, data });
            };
            reader.readAsText(file);
        });
    }

    /**
     * レガシーAPI形式でレポート生成をシミュレーション
     */
    static async generateLegacyReport(csvFiles: File[]): Promise<{
        success: boolean;
        pdfUrl?: string;
        excelFile?: Uint8Array;
        pdfFile?: Uint8Array;
    }> {
        // 既存のロジックをシミュレーション
        console.log(
            `Processing ${csvFiles.length} CSV files for legacy report generation`
        );

        return new Promise((resolve) => {
            setTimeout(() => {
                const dummyPdfUrl = '/factory_report.pdf';

                // シミュレートされたPDFバイナリデータ（実際の実装では本物のPDFバイナリ）
                const dummyPdfContent = new TextEncoder().encode(
                    'PDF content placeholder'
                );

                resolve({
                    success: true,
                    pdfUrl: dummyPdfUrl,
                    pdfFile: dummyPdfContent,
                });
            }, 2000); // 2秒のシミュレーション
        });
    }

    /**
     * 読み込み可能状態の判定（既存ロジック）
     */
    static isReadyToCreate(
        shipFile: File | null,
        shipFileValid: 'valid' | 'invalid' | 'unknown'
    ): boolean {
        return shipFile !== null && shipFileValid === 'valid';
    }
}
