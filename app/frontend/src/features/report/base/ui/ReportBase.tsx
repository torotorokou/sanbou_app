import React, { Suspense, useEffect, useState } from 'react';
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
    const { previewUrl, setPreviewUrl } = preview;
    const { setFinalized } = finalized;
    const { setModalOpen } = modal;
    const { setLoading } = loading;

    // インタラクティブ帳簿かどうか判定
    const isInteractive = isInteractiveReport(reportKey);

    const resetInteractiveState = () => {
        setInteractiveInitialResponse(null);
        setInteractiveSessionData(null);
    };

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (pdfPreviewUrl && pdfPreviewUrl !== previewUrl) {
            setPreviewUrl(pdfPreviewUrl);
        }
    }, [pdfPreviewUrl, previewUrl, setPreviewUrl]);

    // 帳簿切り替え時にプレビューや内部状態をリセット
    useEffect(() => {
        cleanup();
        setPreviewUrl(null);
        setInteractiveInitialResponse(null);
        setInteractiveSessionData(null);
        setFinalized(false);
        setModalOpen(false);
        setLoading(false);
    }, [cleanup, reportKey, setFinalized, setLoading, setModalOpen, setPreviewUrl]);

    /**
     * 通常帳簿のレポート生成処理
     */
    const handleNormalGenerate = () => {
        // リジェネレーション時でもモーダルが「帳簿作成中」から始まるように
        // finalized フラグをリセットし、モーダル内部の currentStep を 0 に戻す
        setFinalized(false);
        try {
            step.setCurrentStep(0);
        } catch {
            // step が未定義なケースを保険的に無視
        }

        modal.setModalOpen(true);
        loading.setLoading(true);

        // 非同期処理の完了フラグを外部で管理
        const processState = { completed: false, success: false };
        
        business.handleGenerateReport(
            () => { 
                console.log('[ReportBase] onStart: レポート生成開始');
            },
            () => {   // onComplete（成功・失敗に関わらず実行）
                console.log('[ReportBase] onComplete: 処理完了', { success: processState.success });
                loading.setLoading(false);
                processState.completed = true;
                
                // onSuccessの後に実行されるため、少し遅延させて判定
                setTimeout(() => {
                    if (!processState.success) {
                        console.log('[ReportBase] 失敗のためモーダルを閉じる');
                        // 失敗時: 即座にモーダルを閉じる
                        modal.setModalOpen(false);
                    }
                }, 100);
            },
            () => {   // onSuccess（成功時のみ実行）
                console.log('[ReportBase] onSuccess: 成功 - ステップ1へ進む');
                processState.success = true;
                finalized.setFinalized(true);
                // 成功時のみ「完了」ステップに進める
                step.setCurrentStep(1);
                // 完了メッセージを2秒間表示してからモーダルを閉じる
                setTimeout(() => {
                    console.log('[ReportBase] 2秒後: モーダルを閉じる');
                    modal.setModalOpen(false);
                    step.setCurrentStep(0); // 次回のために初期化
                }, 2000);
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
                onGenerate={handleGenerate}
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
