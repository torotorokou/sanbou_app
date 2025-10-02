import { useState, useCallback } from 'react';
import { notifySuccess, notifyError, notifyInfo } from '../../utils/notify';
import type { ReportKey } from '@/constants/reportConfig';
import { getApiEndpoint } from '@/constants/reportConfig';
import type { ReportArtifactResponse } from './useReportArtifact';

type CsvFiles = { [csvLabel: string]: File | null };

/**
 * Excel生成とダウンロード機能を管理するフック
 *
 * 🎯 目的：
 * - API呼び出しと結果処理を分離
 * - ファイルダウンロードの複雑性を隠蔽
 * - エラーハンドリングを一元化
 */
export const useExcelGeneration = () => {
    const [excelUrl, setExcelUrl] = useState<string | null>(null);
    const [excelFileName, setExcelFileName] = useState<string>('output.xlsx');

    /**
     * レポートを生成してExcelファイルを作成
     */
    const generateExcel = useCallback(
        async (
            csvFiles: CsvFiles,
            reportKey: ReportKey,
            onStart: () => void,
            onComplete: () => void
        ) => {
            onStart();

            try {
                // 日本語ラベルを英語キーにマッピング
                const labelToEnglishKey: Record<string, string> = {
                    出荷一覧: 'shipment',
                    受入一覧: 'receive',
                    ヤード一覧: 'yard',
                };

                const formData = new FormData();
                Object.keys(csvFiles).forEach((label) => {
                    const fileObj = csvFiles[label];
                    if (fileObj) {
                        const englishKey = labelToEnglishKey[label] || label;
                        formData.append(englishKey, fileObj);
                    }
                });
                formData.append('report_key', reportKey);

                // デバッグログ
                console.log('FormData contents:');
                Object.keys(csvFiles).forEach((label) => {
                    const fileObj = csvFiles[label];
                    if (fileObj) {
                        const englishKey = labelToEnglishKey[label] || label;
                        console.log(
                            `FormData key: ${englishKey}, file name: ${fileObj.name}`
                        );
                    }
                });
                console.log(`FormData key: report_key, value: ${reportKey}`);

                let apiEndpoint = getApiEndpoint(reportKey);
                if (!apiEndpoint.endsWith('/')) apiEndpoint = `${apiEndpoint}/`;
                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    await handleApiError(response);
                    return false;
                }

                // 新APIは JSON で署名付きURLを返す
                const json = (await response.json().catch(() => null)) as ReportArtifactResponse | null;
                const excelUrl = json?.artifact?.excel_download_url ?? null;
                const reportKeyResp: string | null = typeof json?.report_key === 'string' ? json.report_key : null;
                const reportDate: string | null = typeof json?.report_date === 'string' ? json.report_date : null;
                const fileName = reportKeyResp && reportDate ? `${reportKeyResp}_${reportDate}.xlsx` : 'output.xlsx';

                if (typeof excelUrl === 'string' && excelUrl) {
                    setExcelUrl(excelUrl);
                    setExcelFileName(fileName);
                    notifySuccess('帳簿作成成功', `${fileName} をダウンロードできます。`);
                } else {
                    notifyInfo('帳簿作成', 'Excel ダウンロードURLが取得できませんでした。');
                }
                return true;
            } catch (err) {
                console.error('帳簿作成失敗エラー:', err);
                notifyError(
                    '帳簿作成失敗',
                    err instanceof Error ? err.message : String(err)
                );
                return false;
            } finally {
                onComplete();
            }
        },
        []
    );

    /**
     * Excelファイルをダウンロード
     */
    const downloadExcel = useCallback(() => {
        if (excelUrl) {
            window.open(excelUrl, '_blank', 'noopener');
        } else {
            notifyInfo('ダウンロード不可', 'Excelファイルがありません。');
        }
    }, [excelUrl, excelFileName]);

    return {
        excelUrl,
        excelFileName,
        generateExcel,
        downloadExcel,
    };
};

/**
 * APIエラーを処理する
 */
async function handleApiError(response: Response, rawBody?: string | null) {
    let errorMsg = '帳簿作成失敗';
    try {
        const clonedText = rawBody ?? (await response.clone().text().catch(() => ''));
        try {
            const errorJson = JSON.parse(clonedText || '{}');
            errorMsg = errorJson?.detail || errorMsg;
            if (errorJson?.hint) {
                notifyInfo('ヒント', errorJson.hint);
            }
        } catch {
            if (clonedText && clonedText.trim()) {
                errorMsg = `${errorMsg}: ${clonedText.substring(0, 200)}`;
            }
        }
    } catch {
        // best-effort only
    }

    console.error('[Report] API error:', response.status, response.statusText, rawBody);
    throw new Error(errorMsg);
}

// 署名付きURL運用のため、レスポンスヘッダーからのファイル名抽出は不要
