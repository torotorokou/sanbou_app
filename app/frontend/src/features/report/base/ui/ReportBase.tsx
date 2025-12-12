import React, { Suspense, useEffect, useState, useRef } from 'react';
import ReportManagePageLayout from '@features/report/manage/ui/ReportManagePageLayout';
import ReportStepperModal from '@features/report/modal/ui/ReportStepperModal';
import BlockUnitPriceInteractiveModal from '@features/report/interactive/ui/BlockUnitPriceInteractiveModal';
import type { InitialApiResponse, SessionData } from '@features/report/shared/types/interactive.types';
import type { TransportCandidateRow } from '@features/report/shared/types/interactive.types';
import { normalizeRow, isRecord } from '@features/report/shared/lib/transportNormalization';
import { notifyWarning, notifySuccess, notifyError, notifyInfo } from '@features/notification';
const PDFViewer = React.lazy(() => import('@features/report/viewer/ui/PDFViewer'));
import { pdfPreviewMap, modalStepsMap, isInteractiveReport, getApiEndpoint } from '@features/report/shared/config';
import { useReportBaseBusiness } from '../model/useReportBaseBusiness';
import type { ReportBaseProps } from '@features/report/shared/types/report.types';
import type { ReportArtifactResponse } from '@features/report/preview/model/useReportArtifact';
import { coreApi } from '@features/report/shared/infrastructure/http.adapter';

// normalizeRow is now provided by ./interactive/transportNormalization

/**
 * レポートベースコンポーネント - インタラクティブモーダル対応版
 * 
 * 🔄 改善内容：
 * - インタラクティブ帳簿専用モーダル分岐を追加
 * - 共通ZIP処理フックの統合
 * - 通常帳簿とインタラクティブ帳簿の統一的な体験
 * - 複雑なビジネスロジックをカスタムフックに分離
 * 
 * 📝 新機能：
 * - 帳簿タイプ別モーダル分岐
 * - インタラクティブフローサポート
 * - 統一されたZIP処理
 */
const ReportBase: React.FC<ReportBaseProps> = ({
    step,
    file,
    preview,
    modal,
    finalized,
    loading,
    reportKey
}) => {
    // ビジネスロジックとZIP処理フック
    const business = useReportBaseBusiness(
        file.csvConfigs,
        file.files,
        file.onUploadFile,
        reportKey
    );
    const [interactiveInitialResponse, setInteractiveInitialResponse] = useState<InitialApiResponse | null>(null);
    const [interactiveSessionData, setInteractiveSessionData] = useState<SessionData | null>(null);
    const { cleanup, pdfPreviewUrl, pdfStatus } = business;
    
    // モーダル表示タイマーの管理（Excel生成完了後のモーダル表示時間）
    const modalTimerRef = useRef<NodeJS.Timeout | null>(null);
    const { previewUrl, setPreviewUrl } = preview;
    const { setFinalized } = finalized;
    const { setModalOpen } = modal;
    const { setLoading } = loading;

    // インタラクティブ帳簿かどうか判定
    const isInteractive = isInteractiveReport(reportKey);

    const resetInteractiveState = () => {
        // タイマークリア
        if (modalTimerRef.current) {
            clearTimeout(modalTimerRef.current);
            modalTimerRef.current = null;
        }
        setInteractiveInitialResponse(null);
        setInteractiveSessionData(null);
    };

    // 📄 PDFプレビューURLが生成されたら設定（モーダルとは独立）
    useEffect(() => {
        if (pdfPreviewUrl && pdfPreviewUrl !== previewUrl) {
            setPreviewUrl(pdfPreviewUrl);
        }
    }, [pdfPreviewUrl, previewUrl, setPreviewUrl]);

    // 📑 帳簿切り替え時にプレビューや内部状態をリセット（タブ遷移時のPDFクリア）
    useEffect(() => {
        // タイマークリア
        if (modalTimerRef.current) {
            clearTimeout(modalTimerRef.current);
            modalTimerRef.current = null;
        }
        // プレビューと状態をリセット
        cleanup();
        setPreviewUrl(null);
        setFinalized(false);
        setModalOpen(false);
        
        return () => {
            // アンマウント時のクリーンアップ
            if (modalTimerRef.current) {
                clearTimeout(modalTimerRef.current);
                modalTimerRef.current = null;
            }
            cleanup();
            setPreviewUrl(null);
            setFinalized(false);
            setModalOpen(false);
        };
    }, [reportKey, cleanup, setFinalized, setModalOpen, setPreviewUrl]);

    /**
     * 📊 通常帳簿のレポート生成処理（Excel生成完了でモーダル表示）
     * PDF生成は非同期でバックグラウンド処理され、モーダルには影響しない
     */
    const handleNormalGenerate = () => {
        // 状態リセットとタイマークリア
        if (modalTimerRef.current) {
            clearTimeout(modalTimerRef.current);
            modalTimerRef.current = null;
        }
        setFinalized(false);
        step.setCurrentStep(0);
        modal.setModalOpen(true);
        loading.setLoading(true);

        business.handleGenerateReport(
            () => {},  // onStart
            () => {    // onComplete（API呼び出し完了）
                loading.setLoading(false);
            },
            () => {    // onSuccess（Excel生成成功）
                // Excel生成完了を表示（PDFは非同期でバックグラウンド生成中）
                finalized.setFinalized(true);
                step.setCurrentStep(1);
                
                // 2.5秒後にモーダルを閉じる（Excel生成完了の視認性確保）
                modalTimerRef.current = setTimeout(() => {
                    modal.setModalOpen(false);
                    step.setCurrentStep(0);
                }, 2500);
            }
        );
    };

    /**
     * インタラクティブ帳簿のレポート生成処理
     */
    const handleInteractiveGenerate = async () => {
        if (!business.isReadyToCreate) {
            notifyWarning('確認', '必要なCSVファイルをアップロードしてください。');
            return;
        }

        resetInteractiveState();
        // 再生成時にヘッダ／モーダルが完了ステップにならないようリセット
        setFinalized(false);
        try {
            step.setCurrentStep(0);
        } catch {
            // noop
        }

        loading.setLoading(true);

        try {
            const formData = new FormData();
            const labelToKey: Record<string, string> = {
                出荷一覧: 'shipment',
                受入一覧: 'receive',
                ヤード一覧: 'yard',
            };

            Object.entries(file.files).forEach(([label, fileObj]) => {
                if (fileObj) {
                    const key = labelToKey[label] || label;
                    formData.append(key, fileObj);
                }
            });

            try {
                const formDataSummary: Record<string, string[]> = {};
                formData.forEach((value, key) => {
                    const displayValue =
                        value instanceof File
                            ? `${value.name} (${value.size} bytes)`
                            : String(value);
                    formDataSummary[key] = [...(formDataSummary[key] ?? []), displayValue];
                });
                console.groupCollapsed('[BlockUnitPrice] initial request payload');
                console.log('reportKey:', reportKey);
                console.log('endpoint:', getApiEndpoint(reportKey));
                console.log('FormData:', formDataSummary);
                console.groupEnd();
            } catch (logError) {
                console.warn('Failed to log initial request payload:', logError);
            }

            const apiEndpoint = getApiEndpoint(reportKey);
            const data = await coreApi.uploadForm<unknown>(apiEndpoint, formData, { timeout: 60000 });
            // 生データをまず全部出す（インスペクト用）
            console.groupCollapsed('[BlockUnitPrice] initial response - raw');
            console.log(data);
            console.groupEnd();

            if (!isRecord(data)) {
                throw new Error('初期レスポンス形式が不正です。');
            }

            const sessionIdRaw = data['session_id'];
            const session_id = typeof sessionIdRaw === 'string' ? sessionIdRaw : '';

            if (!session_id) {
                throw new Error('セッションIDが取得できませんでした。');
            }

            const rowsSourceRaw = data['rows'];
            const rowsSource = Array.isArray(rowsSourceRaw) ? rowsSourceRaw : [];
            const normalizedRows: TransportCandidateRow[] = rowsSource.reduce<TransportCandidateRow[]>((acc, row, idx) => {
                const normalizedRow = normalizeRow(row);
                if (normalizedRow) {
                    acc.push(normalizedRow);
                } else {
                    try {
                        console.warn(`Skipped invalid transport row at index ${idx}:`, row, 'serialized:', JSON.stringify(row));
                    } catch {
                        console.warn(`Skipped invalid transport row at index ${idx}: (unserializable)`, row);
                    }
                }
                return acc;
            }, []);

            console.groupCollapsed('[BlockUnitPrice] initial response payload (normalized)');
            console.log('session_id:', session_id);
            console.log('rows count:', normalizedRows.length);
            if (normalizedRows.length > 0) {
                console.log('rows sample:', normalizedRows.slice(0, 3));
            }
            console.groupEnd();

            const sessionData: SessionData = { session_id };

            const normalized: InitialApiResponse = {
                session_id,
                rows: normalizedRows,
            };

            setInteractiveInitialResponse(normalized);
            setInteractiveSessionData(sessionData);

            modal.setModalOpen(true);
            notifySuccess('取得成功', '初期データを取得しました。');
        } catch (error) {
            console.error('Interactive initial API failed:', error);
            notifyError(
                'エラー',
                error instanceof Error
                    ? error.message
                    : '初期データの取得に失敗しました。'
            );
            resetInteractiveState();
        } finally {
            loading.setLoading(false);
        }
    };

    /**
     * インタラクティブモーダルのZIP成功時処理（共通化）
     */
    const handleInteractiveSuccess = (response: ReportArtifactResponse) => {
        try {
            business.applyArtifactResponse(response);
            if (response?.artifact?.pdf_preview_url) {
                setPreviewUrl(response.artifact.pdf_preview_url);
            }

            if (response?.status === 'success') {
                finalized.setFinalized(true);
                setTimeout(() => {
                    modal.setModalOpen(false);
                    resetInteractiveState();
                }, 1500);
            } else {
                notifyInfo('情報', '帳簿レスポンスを確認してください。');
            }
        } catch (error) {
            console.error('Interactive success handling failed:', error);
        }
    };

    const handleInteractiveModalClose = () => {
        modal.setModalOpen(false);
        resetInteractiveState();
    };

    // レポート生成処理を帳簿タイプに応じて選択
    const handleGenerate = isInteractive ? handleInteractiveGenerate : handleNormalGenerate;
    
    // ラップして呼び出し元をログ
    const handleGenerateWithLog = () => {
        console.log('>>> [ReportBase] handleGenerate 呼び出し <<<');
        console.log('[ReportBase] isInteractive:', isInteractive);
        console.log('[ReportBase] reportKey:', reportKey);
        console.trace('[ReportBase] 呼び出しスタック');
        handleGenerate();
    };

    // モーダル設定
    const steps = modalStepsMap[reportKey].map(step => step.label);
    const contents = modalStepsMap[reportKey].map(step => step.content);
    const stepConfigs = modalStepsMap[reportKey];
    return (
        <>
            {/* 通常帳簿用モーダル */}
            {!isInteractive && (
                <ReportStepperModal
                    open={modal.modalOpen}
                    steps={steps}
                    currentStep={step.currentStep}
                    onNext={() => {
                        if (step.currentStep === step.steps.length - 1) {
                            modal.setModalOpen(false);
                            step.setCurrentStep(0);
                        }
                    }}
                    stepConfigs={stepConfigs}
                >
                    {contents[step.currentStep]}
                </ReportStepperModal>
            )}

            {/* インタラクティブ帳簿用モーダル */}
            {isInteractive && reportKey === 'block_unit_price' && (
                <BlockUnitPriceInteractiveModal
                    open={modal.modalOpen}
                    onClose={handleInteractiveModalClose}
                    csvFiles={file.files}
                    reportKey={reportKey}
                    onSuccess={handleInteractiveSuccess}
                    initialApiResponse={interactiveInitialResponse ?? undefined}
                    initialSessionData={interactiveSessionData ?? undefined}
                />
            )}

            {/* メインレイアウト */}
            <ReportManagePageLayout
                onGenerate={handleGenerateWithLog}
                onDownloadExcel={business.downloadExcel}
                onPrintPdf={business.printPdf}
                uploadFiles={business.uploadFileConfigs}
                makeUploadProps={business.makeUploadPropsFn}
                finalized={finalized.finalized}
                readyToCreate={business.isReadyToCreate}
                sampleImageUrl={pdfPreviewMap[reportKey]}
                pdfUrl={previewUrl}
                excelReady={business.hasExcel}
                pdfReady={business.hasPdf}
                header={undefined}
            >
                <Suspense fallback={null}>
            <PDFViewer pdfUrl={previewUrl} pdfStatus={pdfStatus} />
                </Suspense>
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
