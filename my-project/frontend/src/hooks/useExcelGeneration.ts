import { useState, useCallback } from 'react';
import { notifySuccess, notifyError, notifyInfo } from '../utils/notify';
import type { ReportKey } from '../constants/reportConfig';

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

                const response = await fetch('/ledger_api/report/manage', {
                    method: 'POST',
                    body: formData,
                });

                if (!response.ok) {
                    await handleApiError(response);
                    return false;
                }

                const blob = await response.blob();
                const fileName = extractFileName(response);

                const excelObjectUrl = window.URL.createObjectURL(blob);
                setExcelUrl(excelObjectUrl);
                setExcelFileName(fileName);

                notifySuccess(
                    '帳簿作成成功',
                    `${fileName} をダウンロードできます。`
                );
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
            const a = document.createElement('a');
            a.href = excelUrl;
            a.download = excelFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(excelUrl);
            setExcelUrl(null);
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
async function handleApiError(response: Response) {
    let errorMsg = '帳簿作成失敗';
    try {
        const errorJson = await response.json();
        errorMsg = errorJson?.detail || errorMsg;
        if (errorJson?.hint) {
            notifyInfo('ヒント', errorJson.hint);
        }
    } catch {
        // JSONでなければスルー
    }
    throw new Error(errorMsg);
}

/**
 * レスポンスヘッダーからファイル名を抽出
 */
function extractFileName(response: Response): string {
    const disposition = response.headers.get('Content-Disposition');
    let fileName = 'output.xlsx';

    if (disposition) {
        const matchStar = disposition.match(/filename\*=UTF-8''([^;]+)/);
        if (matchStar) {
            fileName = decodeURIComponent(matchStar[1]);
        } else {
            const match = disposition.match(/filename="?([^"]+)"?/);
            if (match && match[1]) {
                fileName = decodeURIComponent(match[1]);
            }
        }
    }

    return fileName;
}
