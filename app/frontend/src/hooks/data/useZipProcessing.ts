import { useState, useCallback } from 'react';
import * as JSZip from 'jszip';
import { notifySuccess, notifyError } from '../../utils/notify';

/**
 * ZIP受信後の共通処理フック
 *
 * 🎯 目的：
 * - インタラクティブ・通常帳簿共通のZIP処理
 * - ExcelとPDFの分離・管理
 * - ダウンロード・プレビュー機能の統一
 */
export const useZipProcessing = () => {
    const [zipUrl, setZipUrl] = useState<string | null>(null);
    const [zipFileName, setZipFileName] = useState<string>('');
    const [excelBlob, setExcelBlob] = useState<Blob | null>(null);
    const [pdfBlob, setPdfBlob] = useState<Blob | null>(null);
    const [excelFileName, setExcelFileName] = useState<string>('');
    const [pdfFileName, setPdfFileName] = useState<string>('');
    const [pdfPreviewUrl, setPdfPreviewUrl] = useState<string | null>(null);

    /**
     * ZIPファイルを処理してExcelとPDFを分離
     */
    const processZipFile = useCallback(
        async (zipBlob: Blob, fileName: string) => {
            try {
                // ZIPファイルのオブジェクトURLを作成
                const zipObjectUrl = window.URL.createObjectURL(zipBlob);
                setZipUrl(zipObjectUrl);
                setZipFileName(fileName);

                // ZIPファイルを解凍
                const zip = await JSZip.loadAsync(zipBlob);

                // Excelファイルを探す
                const excelFile = Object.keys(zip.files).find(
                    (name) => name.endsWith('.xlsx') || name.endsWith('.xls')
                );

                // PDFファイルを探す
                const pdfFile = Object.keys(zip.files).find((name) =>
                    name.endsWith('.pdf')
                );

                if (excelFile) {
                    const excelBlob = await zip.files[excelFile].async('blob');
                    setExcelBlob(excelBlob);
                    setExcelFileName(excelFile);
                }

                if (pdfFile) {
                    const pdfBlob = await zip.files[pdfFile].async('blob');
                    setPdfBlob(pdfBlob);
                    setPdfFileName(pdfFile);

                    // PDFプレビューURL作成
                    const pdfObjectUrl = window.URL.createObjectURL(pdfBlob);
                    setPdfPreviewUrl(pdfObjectUrl);
                }

                notifySuccess('ZIP処理完了', 'ファイルが正常に処理されました');
                return true;
            } catch (error) {
                console.error('ZIP processing error:', error);
                notifyError(
                    'ZIP処理エラー',
                    'ファイル処理中にエラーが発生しました'
                );
                return false;
            }
        },
        []
    );

    /**
     * Excelファイルをダウンロード
     */
    const downloadExcel = useCallback(() => {
        if (!excelBlob || !excelFileName) {
            notifyError('ダウンロードエラー', 'Excelファイルが見つかりません');
            return;
        }

        const url = window.URL.createObjectURL(excelBlob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = excelFileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        notifySuccess(
            'ダウンロード開始',
            `${excelFileName} のダウンロードを開始しました`
        );
    }, [excelBlob, excelFileName]);

    /**
     * PDFファイルをダウンロード
     */
    const downloadPdf = useCallback(() => {
        if (!pdfBlob || !pdfFileName) {
            notifyError('ダウンロードエラー', 'PDFファイルが見つかりません');
            return;
        }

        const url = window.URL.createObjectURL(pdfBlob);
        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = url;
        a.download = pdfFileName;
        document.body.appendChild(a);
        a.click();
        window.URL.revokeObjectURL(url);
        document.body.removeChild(a);

        notifySuccess(
            'ダウンロード開始',
            `${pdfFileName} のダウンロードを開始しました`
        );
    }, [pdfBlob, pdfFileName]);

    /**
     * ZIPファイルをダウンロード
     */
    const downloadZip = useCallback(() => {
        if (!zipUrl || !zipFileName) {
            notifyError('ダウンロードエラー', 'ZIPファイルが見つかりません');
            return;
        }

        const a = document.createElement('a');
        a.style.display = 'none';
        a.href = zipUrl;
        a.download = zipFileName;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);

        notifySuccess(
            'ダウンロード開始',
            `${zipFileName} のダウンロードを開始しました`
        );
    }, [zipUrl, zipFileName]);

    /**
     * PDF印刷
     */
    const printPdf = useCallback(() => {
        if (!pdfPreviewUrl) {
            notifyError('印刷エラー', 'PDFが見つかりません');
            return;
        }

        const printWindow = window.open(pdfPreviewUrl);
        if (printWindow) {
            printWindow.addEventListener('load', () => {
                printWindow.print();
            });
        }
    }, [pdfPreviewUrl]);

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
        setZipFileName('');
        setExcelBlob(null);
        setPdfBlob(null);
        setExcelFileName('');
        setPdfFileName('');
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

        // 計算されたプロパティ
        hasExcel: !!excelBlob,
        hasPdf: !!pdfBlob,
        hasZip: !!zipUrl,

        // アクション
        processZipFile,
        downloadExcel,
        downloadPdf,
        downloadZip,
        printPdf,
        cleanup,
    };
};
