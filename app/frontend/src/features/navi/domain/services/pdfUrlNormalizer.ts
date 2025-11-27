// features/navi/utils/pdfUrlNormalizer.ts
// PDFのURL正規化ユーティリティ

/**
 * PDFのURLを正規化
 * バックエンドから受け取ったURLをそのまま使用
 * 既に /core_api/rag/pdfs/... の形式で返されている
 */
export function normalizePdfUrl(url: string): string {
  if (!url) return url;

  // 既に正しい形式ならそのまま返す
  if (url.startsWith('/core_api/rag/pdfs/')) {
    return url;
  }

  // 旧形式の場合の互換性対応
  // /rag_api/pdfs/... -> /core_api/rag/pdfs/...
  if (url.startsWith('/rag_api/pdfs/')) {
    return url.replace('/rag_api/pdfs/', '/core_api/rag/pdfs/');
  }

  // /pdfs/... -> /core_api/rag/pdfs/...
  if (url.startsWith('/pdfs/')) {
    return url.replace('/pdfs/', '/core_api/rag/pdfs/');
  }

  // ファイル名だけの場合
  return `/core_api/rag/pdfs/${url.replace(/^\//, '')}`;
}
