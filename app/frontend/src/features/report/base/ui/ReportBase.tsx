import React, { Suspense, useEffect, useState, useRef } from "react";
import { logger } from "@/shared";
import ReportManagePageLayout from "@features/report/manage/ui/ReportManagePageLayout";
import ReportStepperModal from "@features/report/modal/ui/ReportStepperModal";
import BlockUnitPriceInteractiveModal from "@features/report/interactive/ui/BlockUnitPriceInteractiveModal";
import type {
  InitialApiResponse,
  SessionData,
} from "@features/report/shared/types/interactive.types";
import type { TransportCandidateRow } from "@features/report/shared/types/interactive.types";
import {
  normalizeRow,
  isRecord,
} from "@features/report/shared/lib/transportNormalization";
import {
  notifyWarning,
  notifySuccess,
  notifyError,
  notifyInfo,
} from "@features/notification";
const PDFViewer = React.lazy(
  () => import("@features/report/viewer/ui/PDFViewer"),
);
import {
  pdfPreviewMap,
  modalStepsMap,
  isInteractiveReport,
  getApiEndpoint,
} from "@features/report/shared/config";
import { useReportBaseBusiness } from "../model/useReportBaseBusiness";
import type { ReportBaseProps } from "@features/report/shared/types/report.types";
import type { ReportArtifactResponse } from "@features/report/preview/model/useReportArtifact";
import { coreApi } from "@features/report/shared/infrastructure/http.adapter";

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
  preview: _preview, // eslint-disable-line @typescript-eslint/no-unused-vars -- 将来の拡張用に保持
  modal,
  finalized,
  loading,
  reportKey,
}) => {
  // ビジネスロジックとZIP処理フック
  const business = useReportBaseBusiness(
    file.csvConfigs,
    file.files,
    file.onUploadFile,
    reportKey,
  );
  const [interactiveInitialResponse, setInteractiveInitialResponse] =
    useState<InitialApiResponse | null>(null);
  const [interactiveSessionData, setInteractiveSessionData] =
    useState<SessionData | null>(null);
  const { cleanup, pdfPreviewUrl, pdfStatus } = business;

  // モーダル表示タイマーの管理（Excel生成完了後のモーダル表示時間）
  const modalTimerRef = useRef<NodeJS.Timeout | null>(null);
  const { setFinalized } = finalized;
  const { setModalOpen } = modal;

  // インタラクティブ帳簿かどうか判定
  const isInteractive = isInteractiveReport(reportKey);

  const resetInteractiveState = () => {
    logger.log("[ReportBase] resetInteractiveState 呼び出し");
    // モーダルタイマークリア
    if (modalTimerRef.current) {
      logger.log("[ReportBase] モーダルタイマークリア");
      clearTimeout(modalTimerRef.current);
      modalTimerRef.current = null;
    }
    setInteractiveInitialResponse(null);
    setInteractiveSessionData(null);
  };

  // 📄 PDFプレビューはモーダルとは完全に独立
  // business.pdfPreviewUrl が変更されても、モーダルには影響しない
  // PDFはバックグラウンドで生成され、PDFViewerが直接参照する

  // 📑 帳簿切り替え時にプレビューや内部状態をリセット（タブ遷移時のPDFクリア）
  useEffect(() => {
    logger.log("[ReportBase] 帳簿切り替え検知:", reportKey);
    // モーダルタイマークリア
    if (modalTimerRef.current) {
      logger.log("[ReportBase] モーダルタイマークリア (reportKey変更)");
      clearTimeout(modalTimerRef.current);
      modalTimerRef.current = null;
    }
    // プレビューと状態をリセット
    cleanup();
    setFinalized(false);
    setModalOpen(false);

    return () => {
      logger.log("[ReportBase] アンマウント/クリーンアップ");
      // モーダルタイマークリア
      if (modalTimerRef.current) {
        logger.log("[ReportBase] モーダルタイマークリア (アンマウント)");
        clearTimeout(modalTimerRef.current);
        modalTimerRef.current = null;
      }
      cleanup();
      setFinalized(false);
      setModalOpen(false);
    };
  }, [reportKey]); // ⚠️ reportKeyのみに依存させる

  /**
   * 📊 通常帳簿のレポート生成処理 - Excel完了ベースのシンプルフロー
   *
   * 🎯 フロー:
   * 1. モーダル表示 (作成中)
   * 2. API呼び出し (CSVアップロード)
   * 3. Excel生成完了 → 完了ステップ表示
   * 4. 1.2秒後にモーダル自動クローズ
   *
   * ⚠️ PDFはバックグラウンドで生成され、モーダルの動作には一切関与しません
   */
  const handleNormalGenerate = () => {
    logger.log("[ReportBase] === Excel生成フロー開始 ===");

    // タイマークリア
    if (modalTimerRef.current) {
      logger.log("[ReportBase] 既存タイマーをクリア");
      clearTimeout(modalTimerRef.current);
      modalTimerRef.current = null;
    }

    // 初期状態設定
    logger.log("[ReportBase] モーダル表示: 作成中ステップ");
    setFinalized(false);
    step.setCurrentStep(0);
    modal.setModalOpen(true);
    loading.setLoading(true);

    business.handleGenerateReport(
      () => {}, // onStart
      () => {
        // onComplete: API呼び出し完了
        logger.log("[ReportBase] API呼び出し完了");
        loading.setLoading(false);
      },
      () => {
        // onSuccess: Excel生成完了 (モーダルの核心イベント)
        logger.log("[ReportBase] ✅ Excel生成完了");

        // 完了ステップへ移行
        finalized.setFinalized(true);
        step.setCurrentStep(1);
        notifySuccess("生成完了", "帳簿生成が完了しました");

        // 1.2秒後にモーダルを自動クローズ
        logger.log("[ReportBase] 1.2秒後にモーダルをクローズするタイマー設定");
        modalTimerRef.current = setTimeout(() => {
          logger.log("[ReportBase] 🚪 モーダルをクローズ");
          modal.setModalOpen(false);
          step.setCurrentStep(0);
          logger.log("[ReportBase] === Excel生成フロー完了 ===");
        }, 1200);
      },
    );
  };

  /**
   * インタラクティブ帳簿のレポート生成処理
   */
  const handleInteractiveGenerate = async () => {
    if (!business.isReadyToCreate) {
      notifyWarning("確認", "必要なCSVファイルをアップロードしてください。");
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
        出荷一覧: "shipment",
        受入一覧: "receive",
        ヤード一覧: "yard",
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
          formDataSummary[key] = [
            ...(formDataSummary[key] ?? []),
            displayValue,
          ];
        });
        logger.log("[BlockUnitPrice] initial request payload:", {
          reportKey,
          endpoint: getApiEndpoint(reportKey),
          formData: formDataSummary,
        });
      } catch (logError) {
        logger.warn("Failed to log initial request payload:", logError);
      }

      const apiEndpoint = getApiEndpoint(reportKey);
      const data = await coreApi.uploadForm<unknown>(apiEndpoint, formData, {
        timeout: 60000,
      });
      // 生データをまず全部出す（インスペクト用）
      logger.log("[BlockUnitPrice] initial response - raw:", data);

      if (!isRecord(data)) {
        throw new Error("初期レスポンス形式が不正です。");
      }

      const sessionIdRaw = data["session_id"];
      const session_id = typeof sessionIdRaw === "string" ? sessionIdRaw : "";

      if (!session_id) {
        throw new Error("セッションIDが取得できませんでした。");
      }

      const rowsSourceRaw = data["rows"];
      const rowsSource = Array.isArray(rowsSourceRaw) ? rowsSourceRaw : [];
      const normalizedRows: TransportCandidateRow[] = rowsSource.reduce<
        TransportCandidateRow[]
      >((acc, row, idx) => {
        const normalizedRow = normalizeRow(row);
        if (normalizedRow) {
          acc.push(normalizedRow);
        } else {
          try {
            logger.warn(
              `Skipped invalid transport row at index ${idx}:`,
              row,
              "serialized:",
              JSON.stringify(row),
            );
          } catch {
            logger.warn(
              `Skipped invalid transport row at index ${idx}: (unserializable)`,
              row,
            );
          }
        }
        return acc;
      }, []);

      logger.log("[BlockUnitPrice] initial response payload (normalized):", {
        session_id,
        rowsCount: normalizedRows.length,
        rowsSample: normalizedRows.length > 0 ? normalizedRows.slice(0, 3) : [],
      });

      const sessionData: SessionData = { session_id };

      const normalized: InitialApiResponse = {
        session_id,
        rows: normalizedRows,
      };

      setInteractiveInitialResponse(normalized);
      setInteractiveSessionData(sessionData);

      modal.setModalOpen(true);
      notifySuccess("取得成功", "初期データを取得しました。");
    } catch (error) {
      console.error("Interactive initial API failed:", error);
      notifyError(
        "エラー",
        error instanceof Error
          ? error.message
          : "初期データの取得に失敗しました。",
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
      // PDFプレビューはapplyArtifactResponse内で処理される
      business.applyArtifactResponse(response);

      if (response?.status === "success") {
        finalized.setFinalized(true);
        setTimeout(() => {
          modal.setModalOpen(false);
          resetInteractiveState();
        }, 1500);
      } else {
        notifyInfo("情報", "帳簿レスポンスを確認してください。");
      }
    } catch (error) {
      console.error("Interactive success handling failed:", error);
    }
  };

  const handleInteractiveModalClose = () => {
    modal.setModalOpen(false);
    resetInteractiveState();
  };

  // レポート生成処理を帳簿タイプに応じて選択
  const handleGenerate = isInteractive
    ? handleInteractiveGenerate
    : handleNormalGenerate;

  // ラップして呼び出し元をログ
  const handleGenerateWithLog = () => {
    logger.log(">>> [ReportBase] handleGenerate 呼び出し <<<");
    logger.log("[ReportBase] isInteractive:", isInteractive);
    logger.log("[ReportBase] reportKey:", reportKey);
    logger.debug("[ReportBase] 呼び出しスタック");
    handleGenerate();
  };

  // モーダル設定
  const steps = modalStepsMap[reportKey].map((step) => step.label);
  const contents = modalStepsMap[reportKey].map((step) => step.content);
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
      {isInteractive && reportKey === "block_unit_price" && (
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
        pdfUrl={pdfPreviewUrl}
        excelReady={business.hasExcel}
        pdfReady={business.hasPdf}
        header={undefined}
      >
        <Suspense fallback={null}>
          {/* PDFViewerはbusiness.pdfPreviewUrlを直接参照（親に影響しない） */}
          <PDFViewer pdfUrl={pdfPreviewUrl} pdfStatus={pdfStatus} />
        </Suspense>
      </ReportManagePageLayout>
    </>
  );
};

// PDFViewerをメモ化してパフォーマンス最適化
export default React.memo(ReportBase);
