/**
 * Logger Utility
 *
 * 本番環境では console.log を抑制し、開発環境でのみ出力するロガー
 *
 * 使用方法:
 * ```typescript
 * import { logger } from '@shared/utils/logger';
 *
 * logger.log('Debug message', data);
 * logger.warn('Warning message');
 * logger.error('Error message', error);
 * ```
 *
 * 環境判定:
 * - import.meta.env.MODE === 'production' の場合: console.log/info/debug を抑制
 * - import.meta.env.MODE === 'development' の場合: すべて出力
 *
 * 注意: error/warn は本番環境でも出力（重要なエラー情報を失わないため）
 */

const isDevelopment = import.meta.env.MODE === 'development';

/**
 * Application Logger
 *
 * 本番環境では console.log/info/debug を抑制
 * error/warn は常に出力
 */
export const logger = {
  /**
   * デバッグログ（開発環境のみ）
   */
  log: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.log(...args);
    }
  },

  /**
   * 情報ログ（開発環境のみ）
   */
  info: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.info(...args);
    }
  },

  /**
   * デバッグログ（開発環境のみ）
   */
  debug: (...args: unknown[]): void => {
    if (isDevelopment) {
      console.debug(...args);
    }
  },

  /**
   * 警告ログ（常に出力）
   */
  warn: (...args: unknown[]): void => {
    console.warn(...args);
  },

  /**
   * エラーログ（常に出力）
   */
  error: (...args: unknown[]): void => {
    console.error(...args);
  },

  /**
   * グループ化ログ（開発環境のみ）
   */
  group: (label: string): void => {
    if (isDevelopment) {
      console.group(label);
    }
  },

  /**
   * グループ終了（開発環境のみ）
   */
  groupEnd: (): void => {
    if (isDevelopment) {
      console.groupEnd();
    }
  },

  /**
   * テーブル表示（開発環境のみ）
   */
  table: (data: unknown): void => {
    if (isDevelopment) {
      console.table(data);
    }
  },
};
