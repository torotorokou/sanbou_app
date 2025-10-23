// features/navi/utils/pdfUrlNormalizer.ts
// PDFのURL正規化ユーティリティ

/**
 * PDFのURLを正規化（/pdfs/... → /rag_api/pdfs/... に補正）
 */
export function normalizePdfUrl(url: string): string {
  if (!url) return url;

  // すでに rag_api/pdfs ならそのまま
  if (url.startsWith('/rag_api/pdfs/')) return url;

  // バックエンドが返す /pdfs/... を /rag_api/pdfs/... に置換
  if (url.startsWith('/pdfs/')) {
    return url.replace('/pdfs/', '/rag_api/pdfs/');
  }

  // ファイル名だけなら /rag_api/pdfs に寄せる
  return `/rag_api/pdfs/${url.replace(/^\//, '')}`;
}
