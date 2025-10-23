import { useState, useCallback } from 'react';
import { notifySuccess, notifyError, notifyInfo } from '@features/notification';
import { getApiEndpoint, REPORT_KEYS } from '../model/config';
import type { ReportKey } from '../model/config';
import type { CsvFiles } from '../domain/types/report.types';
import { coreApi } from '@shared/infrastructure/http/coreApi';

export type ReportArtifactResponse = {
    status?: string;
    report_key?: string;
    report_date?: string;
    artifact?: {
        excel_download_url?: string | null;
        pdf_preview_url?: string | null;
        report_token?: string | null;
    } | null;
    summary?: unknown;
    metadata?: unknown;
    [key: string]: unknown;
};

export type ReportArtifactState = {
    excelUrl: string | null;
    pdfUrl: string | null;
    reportToken: string | null;
    reportKey: string | null;
    reportDate: string | null;
    summary: unknown;
    metadata: unknown;
    lastResponse: ReportArtifactResponse | null;
};

const deriveFileName = (reportKey: string | null, reportDate: string | null, suffix: string) => {
    if (reportKey && reportDate) {
        return `${reportKey}_${reportDate}${suffix}`;
    }
    return `report${suffix}`;
};

/**
 * URL 返却方式のレポート生成を扱うフック。
 * 以前の ZIP 解凍ロジックを廃止し、Excel/PDF の署名付き URL をそのまま扱います。
 */
export const useReportArtifact = () => {
    const [state, setState] = useState<ReportArtifactState>({
        excelUrl: null,
        pdfUrl: null,
        reportToken: null,
        reportKey: null,
        reportDate: null,
        summary: null,
        metadata: null,
        lastResponse: null,
    });
    const [excelFileName, setExcelFileName] = useState<string>(() => deriveFileName(null, null, '.xlsx'));
    const [pdfFileName, setPdfFileName] = useState<string>(() => deriveFileName(null, null, '.pdf'));
    const [isReady, setIsReady] = useState<boolean>(false);

    const applyArtifactResponse = useCallback((response: ReportArtifactResponse | null) => {
        if (!response || typeof response !== 'object') {
            setState((prev) => ({
                ...prev,
                excelUrl: null,
                pdfUrl: null,
                reportToken: null,
                lastResponse: response,
            }));
            setIsReady(false);
            return;
        }

        const artifactBlock = response.artifact ?? {};
        const excelUrl = typeof artifactBlock?.excel_download_url === 'string' && artifactBlock.excel_download_url.length > 0
            ? artifactBlock.excel_download_url
            : null;
        const pdfUrl = typeof artifactBlock?.pdf_preview_url === 'string' && artifactBlock.pdf_preview_url.length > 0
            ? artifactBlock.pdf_preview_url
            : null;
        const reportKey = typeof response.report_key === 'string' ? response.report_key : null;
        const reportDate = typeof response.report_date === 'string' ? response.report_date : null;

        setExcelFileName(deriveFileName(reportKey, reportDate, '.xlsx'));
        setPdfFileName(deriveFileName(reportKey, reportDate, '.pdf'));

        setState({
            excelUrl,
            pdfUrl,
            reportToken: typeof artifactBlock?.report_token === 'string' ? artifactBlock.report_token : null,
            reportKey,
            reportDate,
            summary: response.summary ?? null,
            metadata: response.metadata ?? null,
            lastResponse: response,
        });
        setIsReady(Boolean(excelUrl || pdfUrl));
        // 開発者向けログ: 受信したアーティファクト URL を表示
        try {
            console.info('[useReportArtifact] applyArtifactResponse: excelUrl=', excelUrl, 'pdfUrl=', pdfUrl, 'reportToken=', artifactBlock?.report_token);
            // full response for debugging
            console.debug('[useReportArtifact] full response:', response);
        } catch {
            // ログ失敗は致命的ではないので無視
        }
    }, []);

    const generateReport = useCallback(
        async (
            csvFiles: CsvFiles,
            reportKey: ReportKey,
            onStart: () => void,
            onComplete: () => void
        ): Promise<boolean> => {
            onStart();
            try {
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
                // 期間タイプの付与
                type KeysMap = typeof REPORT_KEYS;
                type Entry = KeysMap[keyof KeysMap] & { periodType?: 'oneday' | 'oneweek' | 'onemonth' };
                const entry = (REPORT_KEYS as KeysMap)[reportKey as keyof KeysMap] as Entry | undefined;
                if (entry?.periodType) {
                    formData.append('period_type', entry.periodType);
                }

                let apiEndpoint = getApiEndpoint(reportKey);
                if (!apiEndpoint.endsWith('/')) apiEndpoint = `${apiEndpoint}/`;
                
                const json = await coreApi.uploadForm<ReportArtifactResponse>(
                    apiEndpoint, 
                    formData, 
                    { timeout: 60000 }
                );
                applyArtifactResponse(json);
                // 開発者向けログ: API レスポンス確認
                try {
                    console.info('[useReportArtifact] generateReport response status=', json.status);
                    console.debug('[useReportArtifact] generateReport artifact block=', json.artifact);
                } catch {
                    // ignore logging errors
                }

                if (json.status === 'success') {
                    notifySuccess('レポート作成成功', 'Excel/PDF の URL を取得しました。');
                } else {
                    notifyInfo('レポート情報', 'レスポンスを確認してください。');
                }
                return true;
            } catch (error) {
                notifyError(
                    'レポート作成失敗',
                    error instanceof Error ? error.message : 'レポート生成中にエラーが発生しました。'
                );
                return false;
            } finally {
                onComplete();
            }
        },
        [applyArtifactResponse]
    );

    const downloadExcel = useCallback(() => {
        if (state.excelUrl) {
            window.open(state.excelUrl, '_blank', 'noopener');
        } else {
            notifyInfo('ダウンロード不可', 'Excel ダウンロード URL がありません。');
        }
    }, [state.excelUrl]);

    const getPdfPreviewUrl = useCallback(() => {
        return state.pdfUrl;
    }, [state.pdfUrl]);

    const printPdf = useCallback(() => {
        if (!state.pdfUrl) {
            notifyInfo('印刷不可', 'PDF プレビュー URL がありません。');
            return;
        }
        const newWindow = window.open(state.pdfUrl, '_blank', 'noopener');
        if (!newWindow) {
            notifyInfo('印刷不可', 'ポップアップがブロックされました。');
        }
    }, [state.pdfUrl]);

    const cleanup = useCallback(() => {
        setState({
            excelUrl: null,
            pdfUrl: null,
            reportToken: null,
            reportKey: null,
            reportDate: null,
            summary: null,
            metadata: null,
            lastResponse: null,
        });
        setIsReady(false);
    }, []);

    return {
        excelUrl: state.excelUrl,
        pdfUrl: state.pdfUrl,
        excelFileName,
        pdfFileName,
        summary: state.summary,
        metadata: state.metadata,
        reportToken: state.reportToken,
        reportKey: state.reportKey,
        reportDate: state.reportDate,
        lastResponse: state.lastResponse,
        isReady,
        generateReport,
        applyArtifactResponse,
        downloadExcel,
        printPdf,
        getPdfPreviewUrl,
        cleanup,
    };
};
