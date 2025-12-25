/**
 * dataset-submit 型定義
 */

export interface SubmitOptions {
  signal?: AbortSignal;
  onProgress?: (progress: number) => void;
}

export interface SubmitResult {
  success: boolean;
  message?: string;
}
