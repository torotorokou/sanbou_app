// shared/utils/pdf/workerLoader.ts
// Lazily load pdf.js worker using Vite ?worker dynamic import
// This ensures the ~1MB worker is not included in initial bundle.

type PDFJSLite = {
  GlobalWorkerOptions?: {
    workerSrc?: string;
    // Not in types but supported at runtime
    workerPort?: Worker | null;
  };
};

export async function ensurePdfJsWorkerLoaded(): Promise<void> {
  const mod = await import("react-pdf");
  const pdfjs = (mod as unknown as { pdfjs: PDFJSLite }).pdfjs;

  if (!pdfjs.GlobalWorkerOptions) return;

  // If already configured, exit
  const alreadySet = Boolean(
    pdfjs.GlobalWorkerOptions.workerSrc &&
    typeof pdfjs.GlobalWorkerOptions.workerSrc === "string",
  );
  if (alreadySet) return;

  // Use env override if provided; else point to CDN to avoid bundling
  const CDN_WORKER_URL =
    "https://cdn.jsdelivr.net/npm/pdfjs-dist@5.3.93/build/pdf.worker.min.mjs";
  const WORKER_URL =
    (import.meta as ImportMeta & { env: Record<string, string | undefined> })
      .env.VITE_PDFJS_WORKER_URL || CDN_WORKER_URL;

  pdfjs.GlobalWorkerOptions.workerSrc = WORKER_URL;
  // Ensure workerPort is not set so pdf.js will use workerSrc
  (
    pdfjs.GlobalWorkerOptions as unknown as { workerPort?: Worker | null }
  ).workerPort = null;
}
