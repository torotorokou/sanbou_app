import { useCallback } from "react";

/**
 * レポート関連のアクション処理を管理するフック
 *
 * 🎯 目的：
 * - ボタンアクションのロジックを分離
 * - エラーハンドリングを一元化
 * - UIとビジネスロジックの分離
 */
export const useReportActions = () => {
  /**
   * 印刷処理
   */
  const handlePrint = useCallback((pdfUrl: string | null) => {
    if (pdfUrl) {
      const win = window.open(pdfUrl, "_blank");
      win?.focus();
      win?.print();
    }
  }, []);

  /**
   * プレビュー表示処理
   */
  const handlePreview = useCallback((url: string) => {
    window.open(url, "_blank");
  }, []);

  /**
   * 汎用的なファイルダウンロード処理
   */
  const handleFileDownload = useCallback((url: string, filename: string) => {
    const a = document.createElement("a");
    a.href = url;
    a.download = filename;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
  }, []);

  return {
    handlePrint,
    handlePreview,
    handleFileDownload,
  };
};
