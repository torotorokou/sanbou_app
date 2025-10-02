import React, { Suspense, useEffect, useState } from 'react';
import ReportManagePageLayout from './common/ReportManagePageLayout';
import ReportStepperModal from './common/ReportStepperModal';
import BlockUnitPriceInteractiveModal, { type InitialApiResponse, type SessionData, type TransportCandidateRow } from './interactive/BlockUnitPriceInteractiveModal';
import { message } from 'antd';
const PDFViewer = React.lazy(() => import('./viewer/PDFViewer'));
import { pdfPreviewMap, modalStepsMap, isInteractiveReport, getApiEndpoint } from '@/constants/reportConfig';
import { useReportBaseBusiness } from '../../hooks/report';
import type { ReportBaseProps } from '../../types/reportBase';
import type { ReportArtifactResponse } from '../../hooks/data/useReportArtifact';

const isRecord = (value: unknown): value is Record<string, unknown> =>
    typeof value === 'object' && value !== null;

const normalizeRow = (value: unknown): TransportCandidateRow | null => {
    if (!isRecord(value)) return null;

    const rawOptions = Array.isArray(value['options']) ? value['options'] : [];
    const options = rawOptions
        .map((opt) => (typeof opt === 'string' ? opt.trim() : String(opt ?? '')).trim())
        .filter((label) => label.length > 0);

    const initialIndexRaw = value['initial_index'];
    let initial_index = 0;
    if (typeof initialIndexRaw === 'number' && Number.isFinite(initialIndexRaw)) {
        initial_index = initialIndexRaw;
    } else if (typeof initialIndexRaw === 'string') {
        const parsed = Number.parseInt(initialIndexRaw, 10);
        if (Number.isFinite(parsed)) {
            initial_index = parsed;
        }
    }
    initial_index = Math.max(0, Math.trunc(initial_index));

    const detailValue = value['detail'];
    let detail: string | undefined;
    if (typeof detailValue === 'string') {
        detail = detailValue;
    } else if (detailValue != null) {
        detail = String(detailValue);
    }

    const entryIdCandidate = value['entry_id'];
    const vendorCodeCandidate = value['vendor_code'] ?? value['vendorId'];
    const vendorNameCandidate = value['vendor_name'] ?? value['processor_name'];
    const itemNameCandidate = value['item_name'] ?? value['product_name'];

    // 変更: entry_id が number の場合も許容して文字列化する
    if (typeof entryIdCandidate !== 'string' && typeof entryIdCandidate !== 'number') {
        console.warn('normalizeRow: invalid entry_id type, skipping row:', typeof entryIdCandidate, entryIdCandidate);
        return null;
    }
    const entry_id = String(entryIdCandidate);

    return {
        entry_id,
        vendor_code: typeof vendorCodeCandidate === 'number' || typeof vendorCodeCandidate === 'string'
            ? vendorCodeCandidate
            : '',
        vendor_name: typeof vendorNameCandidate === 'string' ? vendorNameCandidate : String(vendorNameCandidate ?? ''),
        item_name: typeof itemNameCandidate === 'string' ? itemNameCandidate : String(itemNameCandidate ?? ''),
        detail,
        options,
        initial_index,
    } satisfies TransportCandidateRow;
};

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

    // インタラクティブ帳簿かどうか判定
    const isInteractive = isInteractiveReport(reportKey);

    const resetInteractiveState = () => {
        setInteractiveInitialResponse(null);
        setInteractiveSessionData(null);
    };

    // PDFプレビューURLが生成されたら設定
    useEffect(() => {
        if (business.pdfPreviewUrl && business.pdfPreviewUrl !== preview.previewUrl) {
            preview.setPreviewUrl(business.pdfPreviewUrl);
        }
    }, [business.pdfPreviewUrl, preview]);

    /**
     * 通常帳簿のレポート生成処理
     */
    const handleNormalGenerate = () => {
        modal.setModalOpen(true);
        loading.setLoading(true);

        business.handleGenerateReport(
            () => { }, // onStart
            () => {   // onComplete
                loading.setLoading(false);
                setTimeout(() => {
                    modal.setModalOpen(false);
                }, 1000);
            },
            () => {   // onSuccess  
                finalized.setFinalized(true);
            }
        );
    };

    /**
     * インタラクティブ帳簿のレポート生成処理
     */
    const handleInteractiveGenerate = async () => {
        if (!business.isReadyToCreate) {
            message.warning('必要なCSVファイルをアップロードしてください。');
            return;
        }

        resetInteractiveState();
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
            const response = await fetch(apiEndpoint, {
                method: 'POST',
                body: formData,
            });

            if (!response.ok) {
                let errorMessage = '初期データの取得に失敗しました。';
                try {
                    const errorBody = await response.json();
                    if (errorBody?.detail) {
                        errorMessage = String(errorBody.detail);
                    }
                } catch {
                    try {
                        const text = await response.text();
                        if (text) {
                            errorMessage = text;
                        }
                    } catch {
                        // ignore parsing errors
                    }
                }
                throw new Error(errorMessage);
            }

            const data = (await response.json()) as unknown;
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
            message.success('初期データを取得しました。');
        } catch (error) {
            console.error('Interactive initial API failed:', error);
            message.error(
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
                preview.setPreviewUrl(response.artifact.pdf_preview_url);
            }

            if (response?.status === 'success') {
                finalized.setFinalized(true);
                setTimeout(() => {
                    modal.setModalOpen(false);
                    resetInteractiveState();
                }, 1500);
            } else {
                message.info('帳簿レスポンスを確認してください。');
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
                pdfUrl={preview.previewUrl}
                excelUrl={business.excelUrl}
                excelReady={business.hasExcel}
                pdfReady={business.hasPdf}
                header={undefined}
            >
                <Suspense fallback={null}>
                    <PDFViewer pdfUrl={preview.previewUrl} />
                </Suspense>
            </ReportManagePageLayout>
        </>
    );
};

export default ReportBase;
