import {
    reportApiUrlMap,
    getReportType,
} from '../../../constants/reportConfig/managementReportConfig';
import type { ReportKey } from '../../../constants/reportConfig/managementReportConfig';
import * as JSZip from 'jszip';

// CSVアップロード共通処理の型定義
interface CsvUploadResponse {
    success: boolean;
    data?: unknown;
    error?: string;
}

interface CsvUploadCallbacks {
    onStart: () => void;
    onSuccess: (data: unknown) => void;
    onError: (error: string) => void;
    onComplete: () => void;
}

// ZIP処理結果の型定義
export interface ZipProcessResult {
    success: boolean;
    zipUrl?: string;
    zipFileName?: string;
    excelBlob?: Blob;
    pdfBlob?: Blob;
    excelFileName?: string;
    pdfFileName?: string;
    pdfPreviewUrl?: string;
    hasExcel: boolean;
    hasPdf: boolean;
    type: 'zip';
}

// APIリクエスト設定の型定義
interface ApiRequestConfig {
    url: string;
    method: string;
    body: FormData;
}

/**
 * CSV処理共通ユーティリティ
 * シンプルレポートとインタラクティブレポート共通のCSVアップロード処理
 */
export class CsvUploadService {
    /**
     * レポートタイプに応じたAPIエンドポイントを取得
     * @param reportKey レポートキー
     * @returns APIエンドポイントURL
     */
    private static getApiEndpoint(reportKey: ReportKey): string {
        const reportType = getReportType(reportKey);

        if (reportType === 'interactive') {
            return `/ledger_api/${reportKey}/upload-and-start`;
        } else {
            return reportApiUrlMap[reportKey];
        }
    }

    /**
     * FormDataを構築（レポートタイプに応じた形式）
     * @param reportKey レポートキー
     * @param files アップロードするファイル群
     * @returns 構築されたFormData
     */
    private static buildFormData(
        reportKey: ReportKey,
        files: Record<string, File>
    ): FormData {
        const formData = new FormData();
        const reportType = getReportType(reportKey);

        // シンプルレポート（auto）の場合はreport_keyが必要
        if (reportType === 'auto') {
            formData.append('report_key', reportKey);
        }

        // ファイルの追加（共通）
        if (files['出荷一覧']) {
            formData.append('shipment', files['出荷一覧']);
        }
        if (files['ヤード一覧']) {
            formData.append('yard', files['ヤード一覧']);
        }
        if (files['受入一覧']) {
            formData.append('receive', files['受入一覧']);
        }

        return formData;
    }

    /**
     * APIリクエスト設定を構築
     * @param reportKey レポートキー
     * @param files アップロードするファイル群
     * @returns APIリクエスト設定
     */
    private static buildApiRequest(
        reportKey: ReportKey,
        files: Record<string, File>
    ): ApiRequestConfig {
        return {
            url: this.getApiEndpoint(reportKey),
            method: 'POST',
            body: this.buildFormData(reportKey, files),
        };
    }

    /**
     * APIレスポンスエラーハンドリング
     * @param response Fetchレスポンス
     * @param callbacks コールバック関数群
     * @returns エラーレスポンス
     */
    private static async handleApiError(
        response: Response,
        callbacks: CsvUploadCallbacks
    ): Promise<CsvUploadResponse> {
        const errorText = await response.text();
        const error = `APIエラー: ${response.status} - ${errorText}`;
        callbacks.onError(error);
        return { success: false, error };
    }

    /**
     * ZIPファイルからExcelとPDFを抽出して処理
     * @param zipBlob ZIP形式のBlob
     * @returns 処理結果
     */
    private static async processZipFile(
        zipBlob: Blob
    ): Promise<ZipProcessResult> {
        try {
            // JSZipでZIPを解凍
            const zipContent = await JSZip.loadAsync(zipBlob);

            // Excelファイルを検索
            const excelFile = Object.keys(zipContent.files).find(
                (name) => name.endsWith('.xlsx') || name.endsWith('.xls')
            );

            // PDFファイルを検索
            const pdfFile = Object.keys(zipContent.files).find((name) =>
                name.endsWith('.pdf')
            );

            let excelBlob: Blob | undefined;
            let pdfBlob: Blob | undefined;
            let pdfPreviewUrl: string | undefined;

            // Excelファイルの処理
            if (excelFile) {
                excelBlob = await zipContent.files[excelFile].async('blob');
                console.log(`[CsvUploadService] Excel extracted: ${excelFile}`);
            }

            // PDFファイルの処理
            if (pdfFile) {
                const pdfArrayBuffer = await zipContent.files[pdfFile].async(
                    'arraybuffer'
                );
                pdfBlob = new Blob([pdfArrayBuffer], {
                    type: 'application/pdf',
                });
                pdfPreviewUrl = URL.createObjectURL(pdfBlob);
                console.log(`[CsvUploadService] PDF extracted: ${pdfFile}`);
            }

            // ZIPファイル全体のURL生成
            const zipUrl = URL.createObjectURL(zipBlob);

            return {
                success: true,
                zipUrl,
                zipFileName: 'report.zip',
                excelBlob,
                pdfBlob,
                excelFileName: excelFile || '',
                pdfFileName: pdfFile || '',
                pdfPreviewUrl,
                hasExcel: !!excelBlob,
                hasPdf: !!pdfBlob,
                type: 'zip',
            };
        } catch (error) {
            console.error('[CsvUploadService] ZIP processing failed:', error);
            return {
                success: false,
                hasExcel: false,
                hasPdf: false,
                type: 'zip',
            };
        }
    }

    /**
     * APIレスポンスを処理（レポートタイプに応じた形式）
     * @param response Fetchレスポンス
     * @param reportKey レポートキー
     * @returns 処理済みデータ
     */
    private static async processApiResponse(
        response: Response,
        reportKey: ReportKey
    ): Promise<unknown> {
        const reportType = getReportType(reportKey);
        const contentType = response.headers.get('content-type') || '';

        console.log(`[CsvUploadService] Response content-type: ${contentType}`);

        // 両方のレポートタイプで最終的にはZIPファイルが返される
        if (contentType.includes('application/json')) {
            // JSONが返された場合（エラーまたは中間ステップ）
            const jsonData = await response.json();

            if (reportType === 'interactive') {
                // インタラクティブレポート：ワークフロー用のJSONデータ
                return jsonData;
            } else {
                // シンプルレポート：JSONが返されるのは通常エラー
                console.warn(
                    '[CsvUploadService] Unexpected JSON response for simple report'
                );
                return jsonData;
            }
        } else {
            // ファイルが返された場合（ZIP形式）
            const fileBlob = await response.blob();
            console.log(
                `[CsvUploadService] Received file blob, size: ${fileBlob.size} bytes`
            );

            // ZIPファイルとして処理
            const zipResult = await this.processZipFile(fileBlob);
            return zipResult;
        }
    }

    /**
     * CSVファイルをバックエンドにアップロードして処理開始
     * @param reportKey レポートキー
     * @param files アップロードするファイル群
     * @param callbacks 処理状況のコールバック
     * @returns レスポンスデータ
     */
    static async uploadAndStart(
        reportKey: ReportKey,
        files: Record<string, File>,
        callbacks: CsvUploadCallbacks
    ): Promise<CsvUploadResponse> {
        const reportType = getReportType(reportKey);
        console.log(
            `[CsvUploadService] Starting upload for ${reportKey} (type: ${reportType})`
        );

        // 処理開始通知
        callbacks.onStart();

        try {
            // APIリクエスト設定を構築
            const apiConfig = this.buildApiRequest(reportKey, files);
            console.log(`[CsvUploadService] API URL: ${apiConfig.url}`);

            // FormDataの内容をデバッグ出力
            const formDataEntries = Array.from(apiConfig.body.entries());
            console.log(
                '[CsvUploadService] FormData entries:',
                formDataEntries.map(([key, value]) => [
                    key,
                    value instanceof File ? `File: ${value.name}` : value,
                ])
            );

            // バックエンドAPIコール
            const response = await fetch(apiConfig.url, {
                method: apiConfig.method,
                body: apiConfig.body,
            });

            if (!response.ok) {
                return await this.handleApiError(response, callbacks);
            }

            // レポートタイプに応じたレスポンス処理
            const result = await this.processApiResponse(response, reportKey);

            // 成功通知
            callbacks.onSuccess(result);
            console.log('[CsvUploadService] Upload successful:', result);

            return { success: true, data: result };
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : 'Unknown error';
            console.error('[CsvUploadService] Upload failed:', error);
            callbacks.onError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            // 処理完了通知
            callbacks.onComplete();
        }
    }

    /**
     * 最終データをバックエンドに送信してPDF生成
     * @param reportKey レポートキー
     * @param finalData 最終的なユーザー入力データ
     * @param callbacks 処理状況のコールバック
     * @returns レスポンスデータ
     */
    static async submitFinalData(
        reportKey: string,
        finalData: unknown,
        callbacks: CsvUploadCallbacks
    ): Promise<CsvUploadResponse> {
        console.log(
            `[CsvUploadService] Submitting final data for ${reportKey}`
        );

        callbacks.onStart();

        try {
            const response = await fetch(
                `/ledger_api/${reportKey}/generate-final`,
                {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(finalData),
                }
            );

            if (!response.ok) {
                const errorText = await response.text();
                const error = `APIエラー: ${response.status} - ${errorText}`;
                callbacks.onError(error);
                return { success: false, error };
            }

            const result = await response.json();
            callbacks.onSuccess(result);

            return { success: true, data: result };
        } catch (error) {
            const errorMessage =
                error instanceof Error ? error.message : 'Unknown error';
            callbacks.onError(errorMessage);
            return { success: false, error: errorMessage };
        } finally {
            callbacks.onComplete();
        }
    }
}

export default CsvUploadService;
