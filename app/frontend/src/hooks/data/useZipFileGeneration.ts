import { useState, useCallback } from 'react';
import * as JSZip from 'jszip';
import { notifySuccess, notifyError, notifyInfo } from '../../utils/notify';
import { getApiEndpoint, REPORT_KEYS } from '@/constants/reportConfig';
import type { ReportKey } from '@/constants/reportConfig';

type CsvFiles = { [csvLabel: string]: File | null };

/**
 * ZIP生成とダウンロード機能を管理するフック
 *
 * 🎯 目的：
 * - バックエンドからZIPファイルを受け取る
 * - ZIPからExcelとPDFを分離して個別に管理
 * - エクセルダウンロード、PDF印刷・プレビュー機能を提供
 */
export const useZipFileGeneration = () => {
    const [zipUrl, setZipUrl] = useState<string | null>(null);
    const [zipFileName, setZipFileName] = useState<string>('output.zip');
    const [excelBlob, setExcelBlob] = useState<Blob | null>(null);
    const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);
    const [excelFileName, setExcelFileName] = useState<string>('');
    const [pdfFileName, setPdfFileName] = useState<string>('');
    const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);

    /**
     * レポートを生成してZIPファイルを作成・処理
     */
    const generateZipReport = useCallback(
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
                // コンフィグから periodType を解決
                type KeysMap = typeof REPORT_KEYS;
                type Entry = KeysMap[keyof KeysMap] & { periodType?: 'oneday' | 'oneweek' | 'onemonth' };
                const entry = (REPORT_KEYS as KeysMap)[reportKey as keyof KeysMap] as Entry | undefined;
                const periodTypeFromConfig = entry?.periodType;
                if (periodTypeFromConfig) {
                    formData.append('period_type', periodTypeFromConfig);
                }

                // デバッグログ（送信内容）
                try {
                    console.groupCollapsed('[Report] Request Payload');
                    console.log('Endpoint:', getApiEndpoint(reportKey));
                    console.log('Report Key:', reportKey);
                    console.log('Derived period_type from config:', periodTypeFromConfig || '(none)');
                    console.log('Files:');
                    Object.keys(csvFiles).forEach((label) => {
                        const fileObj = csvFiles[label];
                        if (fileObj) {
                            const englishKey = labelToEnglishKey[label] || label;
                            console.log(` - ${englishKey}: name=${fileObj.name}, size=${fileObj.size}, type=${fileObj.type}`);
                        }
                    });
                    // FormData 内容の確認
                    const fdSummary: Record<string, string[]> = {};
                    formData.forEach((value, key) => {
                        const v = value instanceof File ? `${value.name} (${value.size} bytes)` : String(value);
                        fdSummary[key] = [...(fdSummary[key] || []), v];
                    });
                    console.log('FormData Summary:', fdSummary);
                    console.groupEnd();
                } catch {}

                // 帳簿タイプに応じてAPIエンドポイントを選択
                const apiEndpoint = getApiEndpoint(reportKey);
                try {
                    const fullUrl = new URL(apiEndpoint, window.location.origin).toString();
                    console.log(`API endpoint for ${reportKey}: ${apiEndpoint}`);
                    console.log(`Full request URL: ${fullUrl}`);
                } catch {
                    console.log(`API endpoint for ${reportKey}: ${apiEndpoint}`);
                }

                // Note: Do NOT set Content-Type header for FormData; browser will set boundary
                const response = await fetch(apiEndpoint, {
                    method: 'POST',
                    body: formData,
                });

                // デバッグログ（レスポンス概要）
                try {
                    console.groupCollapsed('[Report] Response Meta');
                    console.log('Status:', response.status, response.statusText);
                    const interestingHeaders = ['content-type', 'content-length', 'content-disposition'];
                    interestingHeaders.forEach((h) => {
                        console.log(`${h}:`, response.headers.get(h) || '(missing)');
                    });
                    console.groupEnd();
                } catch {}

                if (!response.ok) {
                    // Attempt to read response text for better debugging (covers HTML 500 pages)
                    let respText: string | null = null;
                    try {
                        respText = await response.text();
                    } catch {
                        // ignore
                    }

                    console.error('[Report] API Error Response Body:', respText);
                    await handleApiError(response, respText);
                    return false;
                }

                const zipBlob = await response.blob();
                const fileName = extractFileName(response);

                // デバッグログ（受信Blob情報）
                try {
                    console.groupCollapsed('[Report] Received Blob');
                    console.log('filename:', fileName);
                    console.log('blob.type:', zipBlob.type || '(unknown)');
                    console.log('blob.size:', zipBlob.size, 'bytes');
                    console.groupEnd();
                } catch {}

                // ZIPファイルのオブジェクトURLを作成
                const zipObjectUrl = window.URL.createObjectURL(zipBlob);
                setZipUrl(zipObjectUrl);
                setZipFileName(fileName);

                // ZIPファイルからExcelとPDFを抽出
                await extractFilesFromZip(zipBlob);

                notifySuccess(
                    'レポート作成成功',
                    `${fileName} が生成されました。`
                );
                return true;
            } catch (err) {
                console.error('レポート作成失敗エラー:', err);
                notifyError(
                    'レポート作成失敗',
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
     * ZIPファイルからExcelとPDFを抽出
     */
    const extractFilesFromZip = useCallback(async (zipBlob: Blob) => {
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

            if (excelFile) {
                const excelBlob = await zipContent.files[excelFile].async(
                    'blob'
                );
                setExcelBlob(excelBlob);
                setExcelFileName(excelFile);
            }

            if (pdfFile) {
                console.log('PDFファイル発見:', pdfFile);
                // PDFファイルはバイナリデータなので、適切なMIMEタイプでBlobを作成
                const pdfArrayBuffer = await zipContent.files[pdfFile].async(
                    'arraybuffer'
                );
                console.log(
                    'PDF ArrayBuffer サイズ:',
                    pdfArrayBuffer.byteLength
                );

                // PDFファイルの基本検証
                const pdfUint8Array = new Uint8Array(pdfArrayBuffer);
                const pdfHeader = String.fromCharCode(
                    ...pdfUint8Array.slice(0, 4)
                );

                if (pdfHeader !== '%PDF') {
                    console.warn(
                        '警告: PDFファイルのヘッダーが不正です:',
                        pdfHeader
                    );
                    notifyError(
                        'PDF検証エラー',
                        'PDFファイルが破損している可能性があります。'
                    );
                } else {
                    console.log('PDF検証成功: 正常なPDFファイルです');
                }

                const pdfBlob = new Blob([pdfArrayBuffer], {
                    type: 'application/pdf',
                });
                console.log('PDF Blob作成完了 - サイズ:', pdfBlob.size);
                setPdfBlob(pdfBlob);
                setPdfFileName(pdfFile);

                // PDFプレビューURLを即座に生成
                try {
                    const url = window.URL.createObjectURL(pdfBlob);
                    setPdfPreviewUrl(url);
                    console.log('PDFプレビューURL生成完了:', url);
                } catch (error) {
                    console.error('PDFプレビューURL生成エラー:', error);
                }
            }

            console.groupCollapsed('[Report] ZIP Extract Summary');
            console.log(`Excel File:`, excelFile || '(none)');
            console.log(`PDF File:`, pdfFile || '(none)');
            console.log('All ZIP entries:', Object.keys(zipContent.files));
            console.groupEnd();

            // 状態確認ログ
            console.log('ZIP解凍完了 - 現在の状態:', {
                hasExcel: !!excelFile,
                hasPdf: !!pdfFile,
                excelBlobSize: excelBlob?.size || 0,
                pdfBlobSize: pdfBlob?.size || 0,
            });
        } catch (error) {
            console.error('ZIP解凍エラー:', error);
            notifyError('ZIP解凍失敗', 'ZIPファイルの解凍に失敗しました。');
        }
    }, []);

    /**
     * Excelファイルをダウンロード
     */
    const downloadExcel = useCallback(() => {
        if (excelBlob && excelFileName) {
            const url = window.URL.createObjectURL(excelBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = excelFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            notifySuccess(
                'ダウンロード開始',
                `${excelFileName} をダウンロードしています。`
            );
        } else {
            notifyInfo('ダウンロード不可', 'Excelファイルがありません。');
        }
    }, [excelBlob, excelFileName]);

    /**
     * PDFファイルを印刷
     */
    const printPdf = useCallback(() => {
        if (pdfBlob) {
            try {
                // 既存のプレビューURLを使用するか、新規作成
                const url =
                    pdfPreviewUrl || window.URL.createObjectURL(pdfBlob);

                // まず新しいタブでPDFを開く
                const printWindow = window.open(url, '_blank');

                if (printWindow) {
                    // PDFの読み込みを確実に待つ
                    const attemptPrint = () => {
                        try {
                            // ウィンドウがフォーカスされた後に印刷を実行
                            printWindow.focus();
                            setTimeout(() => {
                                printWindow.print();
                            }, 500);
                        } catch (error) {
                            console.warn('自動印刷に失敗:', error);
                        }
                    };

                    // 複数の方法でPDF読み込み完了を検知
                    printWindow.addEventListener('load', attemptPrint);
                    setTimeout(attemptPrint, 2000); // フォールバック

                    notifySuccess(
                        '印刷準備完了',
                        'PDFが新しいタブで開かれました。印刷ダイアログが表示されない場合は、Ctrl+P（またはCmd+P）で手動印刷してください。'
                    );
                } else {
                    notifyError(
                        '印刷失敗',
                        'ポップアップがブロックされました。ブラウザのポップアップ設定を確認してください。'
                    );
                }

                // プレビューURLが無かった場合のみURLを解放
                if (!pdfPreviewUrl) {
                    setTimeout(() => window.URL.revokeObjectURL(url), 15000);
                }
            } catch (error) {
                console.error('PDF印刷エラー:', error);
                notifyError('印刷失敗', 'PDFの印刷に失敗しました。');
            }
        } else {
            notifyInfo('印刷不可', 'PDFファイルがありません。');
        }
    }, [pdfBlob, pdfPreviewUrl]);

    /**
     * PDFプレビューURLを取得
     */
    const getPdfPreviewUrl = useCallback((): string | null => {
        if (pdfBlob && !pdfPreviewUrl) {
            try {
                // 適切なMIMEタイプでオブジェクトURLを作成（一度だけ）
                const url = window.URL.createObjectURL(
                    new Blob([pdfBlob], { type: 'application/pdf' })
                );
                setPdfPreviewUrl(url);
                return url;
            } catch (error) {
                console.error('PDFプレビューURL生成エラー:', error);
                return null;
            }
        }
        return pdfPreviewUrl;
    }, [pdfBlob, pdfPreviewUrl]);

    /**
     * PDFファイルをダウンロード（デバッグ用）
     */
    const downloadPdf = useCallback(() => {
        if (pdfBlob && pdfFileName) {
            const url = window.URL.createObjectURL(pdfBlob);
            const a = document.createElement('a');
            a.href = url;
            a.download = pdfFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);
            window.URL.revokeObjectURL(url);

            notifySuccess(
                'PDFダウンロード開始',
                `${pdfFileName} をダウンロードしています。`
            );
        } else {
            notifyInfo('ダウンロード不可', 'PDFファイルがありません。');
        }
    }, [pdfBlob, pdfFileName]);

    /**
     * ZIPファイル全体をダウンロード（オプション）
     */
    const downloadZip = useCallback(() => {
        if (zipUrl) {
            const a = document.createElement('a');
            a.href = zipUrl;
            a.download = zipFileName;
            document.body.appendChild(a);
            a.click();
            document.body.removeChild(a);

            notifySuccess(
                'ZIPダウンロード',
                `${zipFileName} をダウンロードしました。`
            );
        } else {
            notifyInfo('ダウンロード不可', 'ZIPファイルがありません。');
        }
    }, [zipUrl, zipFileName]);

    /**
     * リソースをクリーンアップ
     */
    const cleanup = useCallback(() => {
        if (zipUrl) {
            window.URL.revokeObjectURL(zipUrl);
            setZipUrl(null);
        }
        if (pdfPreviewUrl) {
            window.URL.revokeObjectURL(pdfPreviewUrl);
            setPdfPreviewUrl(null);
        }
        setExcelBlob(null);
        setPdfBlob(null);
        setExcelFileName('');
        setPdfFileName('');
        setZipFileName('output.zip');
    }, [zipUrl, pdfPreviewUrl]);

    return {
        // 状態
        zipUrl,
        zipFileName,
        excelBlob,
        pdfBlob,
        excelFileName,
        pdfFileName,
        pdfPreviewUrl,

        // アクション
        generateZipReport,
        downloadExcel,
        downloadPdf,
        printPdf,
        getPdfPreviewUrl,
        downloadZip,
        cleanup,

        // 計算されたプロパティ
        hasExcel: !!excelBlob,
        hasPdf: !!pdfBlob,
        isReady: !!(excelBlob && pdfBlob),
    };
};

/**
 * APIエラーを処理する
 */
async function handleApiError(response: Response, rawBody?: string | null) {
    let errorMsg = 'レポート作成失敗';
    try {
        const clonedText = rawBody ?? (await response.clone().text().catch(() => ''));
        // Try parse JSON first
        try {
            const errorJson = JSON.parse(clonedText || '{}');
            errorMsg = errorJson?.detail || errorMsg;
            if (errorJson?.hint) {
                notifyInfo('ヒント', errorJson.hint);
            }
        } catch {
            // not JSON, fall back to using raw text
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

/**
 * レスポンスヘッダーからファイル名を抽出
 */
function extractFileName(response: Response): string {
    const disposition = response.headers.get('Content-Disposition');
    let fileName = 'output.zip';

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
