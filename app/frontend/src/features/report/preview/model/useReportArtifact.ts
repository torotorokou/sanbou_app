import { useState, useCallback, useEffect, useRef } from "react";
import { notifySuccess, notifyError, notifyInfo } from "@features/notification";
import { getApiEndpoint, REPORT_KEYS } from "@features/report/shared/config";
import type { ReportKey } from "@features/report/shared/config";
import type { CsvFiles } from "@features/report/shared/types/report.types";
import { coreApi } from "@features/report/shared/infrastructure/http.adapter";
import { generateJapaneseFilename } from "@features/report/shared/lib/reportKeyTranslation";

// PDFステータスの型定義
export type PdfStatus = "idle" | "pending" | "ready" | "error";

export type ReportArtifactResponse = {
  status?: string;
  report_key?: string;
  report_date?: string;
  artifact?: {
    excel_download_url?: string | null;
    pdf_preview_url?: string | null;
    report_token?: string | null;
  } | null;
  metadata?: {
    pdf_status?: PdfStatus;
    [key: string]: unknown;
  } | null;
  summary?: unknown;
  [key: string]: unknown;
};

// PDFステータスAPIのレスポンス型
type PdfStatusResponse = {
  report_key: string;
  report_token: string;
  status: "pending" | "ready" | "error";
  pdf_url?: string | null;
  message?: string | null;
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
  pdfStatus: PdfStatus;
};

const deriveFileName = (
  reportKey: string | null,
  reportDate: string | null,
  suffix: string,
) => {
  if (reportKey && reportDate) {
    return `${reportKey}_${reportDate}${suffix}`;
  }
  return `report${suffix}`;
};

/**
 * URL 返却方式のレポート生成を扱うフック。
 * 🔄 リファクタリング: Excel同期 + PDF非同期ポーリングに対応
 * - Excel URL は即座に返却
 * - PDFは非同期生成。pdf_status をポーリングして完了を確認
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
    pdfStatus: "idle",
  });
  const [excelFileName, setExcelFileName] = useState<string>(() =>
    deriveFileName(null, null, ".xlsx"),
  );
  const [pdfFileName, setPdfFileName] = useState<string>(() =>
    deriveFileName(null, null, ".pdf"),
  );
  const [isReady, setIsReady] = useState<boolean>(false);

  // ポーリング用のキャンセルフラグ
  const pollingCancelledRef = useRef<boolean>(false);

  // PDFステータスをポーリングで確認（🚀 高速化: 1.5秒間隔）
  // ⚠️ 重要: このポーリングはモーダルに影響しないように設計
  const pollPdfStatus = useCallback(
    async (reportKey: string, reportDate: string, reportToken: string) => {
      pollingCancelledRef.current = false;

      const poll = async () => {
        if (pollingCancelledRef.current) return;

        try {
          const params = new URLSearchParams({
            report_key: reportKey,
            report_date: reportDate,
            report_token: reportToken,
          });

          const response = await coreApi.get<PdfStatusResponse>(
            `/core_api/reports/pdf-status?${params.toString()}`,
          );

          if (pollingCancelledRef.current) return;

          // PDF生成完了
          if (response.status === "ready" && response.pdf_url) {
            console.info("[PDFバックグラウンド] ✅ 生成完了");
            setState((prev) => ({
              ...prev,
              pdfStatus: "ready",
              pdfUrl: response.pdf_url ?? null,
            }));
            notifySuccess(
              "PDF生成完了",
              "PDFプレビューが利用可能になりました。",
            );
            return;
          }

          // PDF生成失敗
          if (response.status === "error") {
            console.error("[PDFバックグラウンド] ❌ 生成失敗");
            setState((prev) => ({
              ...prev,
              pdfStatus: "error",
            }));
            notifyError(
              "PDF生成失敗",
              response.message || "PDFの生成に失敗しました。",
              0,
            );
            return;
          }

          // pending: 1.5秒後に再ポーリング (バックグラウンド処理)
          if (!pollingCancelledRef.current) {
            setTimeout(poll, 1500);
          }
        } catch (error) {
          if (!pollingCancelledRef.current) {
            console.error(
              "[useReportArtifact] PDFステータス確認エラー:",
              error,
            );
            setState((prev) => ({
              ...prev,
              pdfStatus: "error",
            }));
          }
        }
      };

      poll();
    },
    [],
  ); // 依存配列を空にして再生成を防止

  // pdfStatus が pending になったらポーリング開始
  useEffect(() => {
    if (
      state.pdfStatus === "pending" &&
      state.reportToken &&
      state.reportKey &&
      state.reportDate
    ) {
      console.info("[PDFバックグラウンド] ポーリング開始");
      pollPdfStatus(state.reportKey, state.reportDate, state.reportToken);
    }

    return () => {
      pollingCancelledRef.current = true;
    };
  }, [
    state.pdfStatus,
    state.reportToken,
    state.reportKey,
    state.reportDate,
    pollPdfStatus,
  ]);

  const applyArtifactResponse = useCallback(
    (response: ReportArtifactResponse | null) => {
      console.info("[useReportArtifact] APIレスポンス受信:", {
        status: response?.status,
        report_key: response?.report_key,
        has_excel: Boolean(response?.artifact?.excel_download_url),
        pdf_status: response?.metadata?.pdf_status || "none",
      });

      if (!response || typeof response !== "object") {
        setState((prev) => ({
          ...prev,
          excelUrl: null,
          pdfUrl: null,
          reportToken: null,
          lastResponse: response,
          pdfStatus: "idle",
        }));
        setIsReady(false);
        return;
      }

      const artifactBlock = response.artifact ?? {};
      const metadataBlock = response.metadata ?? {};
      const excelUrl =
        typeof artifactBlock?.excel_download_url === "string" &&
        artifactBlock.excel_download_url.length > 0
          ? artifactBlock.excel_download_url
          : null;
      const pdfUrl =
        typeof artifactBlock?.pdf_preview_url === "string" &&
        artifactBlock.pdf_preview_url.length > 0
          ? artifactBlock.pdf_preview_url
          : null;
      const reportKey =
        typeof response.report_key === "string" ? response.report_key : null;
      const reportDate =
        typeof response.report_date === "string" ? response.report_date : null;
      const reportToken =
        typeof artifactBlock?.report_token === "string"
          ? artifactBlock.report_token
          : null;

      // PDFステータスの判定
      // - metadata.pdf_status が "pending" なら pending
      // - pdfUrl があれば ready
      // - それ以外は idle
      let pdfStatus: PdfStatus = "idle";
      if (metadataBlock.pdf_status === "pending") {
        pdfStatus = "pending";
      } else if (pdfUrl) {
        pdfStatus = "ready";
      }

      console.info("[useReportArtifact] アーティファクト:", {
        excel: excelUrl ? "✅ あり" : "❌ なし",
        pdf: pdfUrl
          ? "✅ あり"
          : pdfStatus === "pending"
            ? "⏳ 生成中"
            : "❌ なし",
      });

      setExcelFileName(deriveFileName(reportKey, reportDate, ".xlsx"));
      setPdfFileName(deriveFileName(reportKey, reportDate, ".pdf"));

      setState({
        excelUrl,
        pdfUrl,
        reportToken,
        reportKey,
        reportDate,
        summary: response.summary ?? null,
        metadata: response.metadata ?? null,
        lastResponse: response,
        pdfStatus,
      });

      // Excelがあれば即座にダウンロード開始
      if (excelUrl) {
        setIsReady(true);
      } else {
        setIsReady(Boolean(pdfUrl));
      }
    },
    [],
  );

  const generateReport = useCallback(
    async (
      csvFiles: CsvFiles,
      reportKey: ReportKey,
      onStart: () => void,
      onComplete: () => void,
    ): Promise<boolean> => {
      onStart();
      try {
        const labelToEnglishKey: Record<string, string> = {
          出荷一覧: "shipment",
          受入一覧: "receive",
          ヤード一覧: "yard",
        };

        const formData = new FormData();
        Object.keys(csvFiles).forEach((label) => {
          const fileObj = csvFiles[label];
          if (fileObj) {
            const englishKey = labelToEnglishKey[label] || label;
            formData.append(englishKey, fileObj);
          }
        });
        formData.append("report_key", reportKey);
        // 期間タイプの付与
        type KeysMap = typeof REPORT_KEYS;
        type Entry = KeysMap[keyof KeysMap] & {
          periodType?: "oneday" | "oneweek" | "onemonth";
        };
        const entry = (REPORT_KEYS as KeysMap)[reportKey as keyof KeysMap] as
          | Entry
          | undefined;
        if (entry?.periodType) {
          formData.append("period_type", entry.periodType);
        }

        let apiEndpoint = getApiEndpoint(reportKey);
        if (!apiEndpoint.endsWith("/")) apiEndpoint = `${apiEndpoint}/`;

        const json = await coreApi.uploadForm<ReportArtifactResponse>(
          apiEndpoint,
          formData,
          { timeout: 60000 },
        );
        applyArtifactResponse(json);

        // status フィールドが 'success' または artifact が存在する場合は成功とみなす
        if (
          json.status === "success" ||
          (json.artifact &&
            (json.artifact.excel_download_url || json.artifact.pdf_preview_url))
        ) {
          notifySuccess("レポート作成成功", "帳簿の生成に成功しました。");
        } else if (json.status && json.status !== "success") {
          // status が明示的に success 以外の場合のみ情報通知
          notifyInfo("レポート情報", "レスポンスを確認してください。");
        }
        return true;
      } catch (error) {
        notifyError(
          "レポート作成失敗",
          error instanceof Error
            ? error.message
            : "レポート生成中にエラーが発生しました。",
          0, // 自動削除しない（手動クローズのみ）
        );
        return false;
      } finally {
        onComplete();
      }
    },
    [applyArtifactResponse],
  );

  const downloadExcel = useCallback(async () => {
    if (!state.excelUrl) {
      notifyInfo("ダウンロード不可", "Excel ダウンロード URL がありません。");
      return;
    }

    // デバッグ: ダウンロード時の状態確認
    console.info("[downloadExcel] ダウンロード開始:", {
      reportKey: state.reportKey,
      reportDate: state.reportDate,
      excelUrl: state.excelUrl,
    });

    try {
      // URLからファイルをダウンロード
      const response = await fetch(state.excelUrl);
      if (!response.ok) throw new Error("ダウンロードに失敗しました");

      const blob = await response.blob();

      // report_keyから日本語ファイル名を生成
      let filename = "report.xlsx";
      if (state.reportKey && state.reportDate) {
        filename = generateJapaneseFilename(
          state.reportKey,
          state.reportDate,
          ".xlsx",
        );
        console.info("[downloadExcel] 日本語ファイル名生成成功:", filename);
      } else {
        console.warn(
          "[downloadExcel] reportKey または reportDate が未設定 - デフォルト名を使用:",
          {
            reportKey: state.reportKey,
            reportDate: state.reportDate,
            defaultFilename: filename,
          },
        );
      }

      // Blob URLを作成してダウンロード
      const url = window.URL.createObjectURL(blob);
      const link = document.createElement("a");
      link.href = url;
      link.download = filename;
      document.body.appendChild(link);
      link.click();
      link.remove();
      window.URL.revokeObjectURL(url);

      console.info("[downloadExcel] ダウンロード完了:", filename);
    } catch (error) {
      console.error("[downloadExcel] エラー:", error);
      notifyError(
        "ダウンロード失敗",
        error instanceof Error
          ? error.message
          : "Excelのダウンロードに失敗しました",
      );
    }
  }, [state.excelUrl, state.reportKey, state.reportDate]);

  const getPdfPreviewUrl = useCallback(() => {
    return state.pdfUrl;
  }, [state.pdfUrl]);

  const printPdf = useCallback(() => {
    if (!state.pdfUrl) {
      notifyInfo("印刷不可", "PDF プレビュー URL がありません。");
      return;
    }
    const newWindow = window.open(state.pdfUrl, "_blank", "noopener");
    if (!newWindow) {
      notifyInfo("印刷不可", "ポップアップがブロックされました。");
    }
  }, [state.pdfUrl]);

  const cleanup = useCallback(() => {
    pollingCancelledRef.current = true;
    setState({
      excelUrl: null,
      pdfUrl: null,
      reportToken: null,
      reportKey: null,
      reportDate: null,
      summary: null,
      metadata: null,
      lastResponse: null,
      pdfStatus: "idle",
    });
    setIsReady(false);
  }, []);

  return {
    excelUrl: state.excelUrl,
    pdfUrl: state.pdfUrl,
    pdfStatus: state.pdfStatus,
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
