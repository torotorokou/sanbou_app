/**
 * 通知設定とコードマッピングの一元化
 * 
 * 目的:
 * - 通知のデフォルト秒数を集中管理
 * - エラーコード→severity/title のマッピングを一元化
 */

export const NOTIFY_DEFAULTS = {
  success: 4000,
  info: 5000,
  warning: 5000,
  error: 6000,
  persistent: null as number | null, // 自動削除しない
  
  // 後方互換性のため
  successMs: 4000,
  infoMs: 5000,
  warningMs: 5000,
  errorMs: 6000,
} as const;

/**
 * エラーコードカタログ
 * 
 * バックエンドの ProblemDetails.code と対応
 * - severity: 通知の種類
 * - title: 通知のタイトル
 * 
 * 運用ルール:
 * - バックエンドで新しいエラーコードを追加したらここにも追加
 * - userMessage はバックエンドから受け取るので、ここでは title のみ
 */
export const codeCatalog: Record<
  string,
  { severity: 'success' | 'info' | 'warning' | 'error'; title: string }
> = {
  // 入力エラー
  INPUT_INVALID: { severity: 'warning', title: '入力エラー' },
  VALIDATION_ERROR: { severity: 'warning', title: '入力値が不正です' },
  MISSING_COLUMNS: { severity: 'error', title: '必須カラムが不足しています' },
  MISSING_DATE_FIELD: { severity: 'error', title: '伝票日付がありません' },
  DATE_MISMATCH: { severity: 'error', title: '伝票日付が一致しません' },
  
  // 認証エラー
  AUTH_REQUIRED: { severity: 'error', title: '認証が必要です' },
  AUTH_FAILED: { severity: 'error', title: '認証に失敗しました' },
  SESSION_EXPIRED: { severity: 'warning', title: 'セッションが切れました' },
  
  // ファイルエラー
  NO_FILES: { severity: 'warning', title: 'ファイルが選択されていません' },
  CSV_READ_ERROR: { severity: 'error', title: 'CSVの読み込みに失敗しました' },
  CSV_VALIDATION_FAILED: { severity: 'error', title: 'CSVの検証に失敗しました' },
  
  // 処理エラー
  PROCESSING_ERROR: { severity: 'error', title: '処理中にエラーが発生しました' },
  INTERNAL_ERROR: { severity: 'error', title: '処理に失敗しました' },
  TIMEOUT: { severity: 'error', title: 'タイムアウトしました' },
  
  // ジョブエラー
  JOB_FAILED: { severity: 'error', title: 'ジョブが失敗しました' },
  JOB_CANCELLED: { severity: 'warning', title: 'ジョブがキャンセルされました' },
  
  // 帳票生成エラー
  REPORT_GENERATION_ERROR: { severity: 'error', title: '帳票生成エラー' },
  REPORT_PROCESSING_ERROR: { severity: 'error', title: '帳票処理エラー' },
  REPORT_FORMAT_ERROR: { severity: 'error', title: 'データ整形エラー' },
  INTERACTIVE_APPLY_FAILED: { severity: 'error', title: '処理エラー' },
  INTERACTIVE_FINALIZE_ERROR: { severity: 'error', title: '最終計算エラー' },
  AUTO_FINALIZE_FAILED: { severity: 'error', title: '自動計算エラー' },
  SESSION_NOT_FOUND: { severity: 'warning', title: 'セッションエラー' },
  
  // 成功
  SUCCESS: { severity: 'success', title: '成功しました' },
  UPLOAD_SUCCESS: { severity: 'success', title: 'アップロードが完了しました' },
  
  // テスト用
  TEST_ERROR: { severity: 'error', title: 'テストエラー' },
};

/**
 * エラーコードから通知設定を取得
 * 
 * @param code エラーコード
 * @returns 通知設定（見つからない場合はデフォルト）
 */
export function getNotificationConfig(code: string) {
  return codeCatalog[code] ?? codeCatalog.INTERNAL_ERROR ?? {
    severity: 'error',
    title: 'エラーが発生しました',
  };
}
