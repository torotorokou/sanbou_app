/**
 * Infrastructure exports - リポジトリインスタンス切り替え
 *
 * 環境に応じてLocalまたはHTTPリポジトリを選択。
 * ViewModel はこのファイルから announcementRepository をインポートすることで、
 * 実装の切り替えが容易になる。
 *
 * 切り替え方法:
 * - 本番環境: USE_LOCAL_ANNOUNCEMENT_REPOSITORY = false (デフォルト)
 * - 開発時にシードデータを使う場合: USE_LOCAL_ANNOUNCEMENT_REPOSITORY = true
 */

import type { AnnouncementRepository } from '../ports/AnnouncementRepository';
import { LocalAnnouncementRepository } from './LocalAnnouncementRepository';
import { HttpAnnouncementRepository } from './HttpAnnouncementRepository';

/**
 * ローカルリポジトリを使用するかどうかのフラグ
 *
 * true: シードデータ + localStorage（開発用）
 * false: バックエンドAPI経由（本番用）
 *
 * 将来的には環境変数 (import.meta.env.VITE_USE_LOCAL_ANNOUNCEMENTS) で制御可能
 */
const USE_LOCAL_ANNOUNCEMENT_REPOSITORY = false;

/**
 * お知らせリポジトリインスタンス
 *
 * ViewModelからはこのインスタンスをインポートして使用する。
 */
export const announcementRepository: AnnouncementRepository = USE_LOCAL_ANNOUNCEMENT_REPOSITORY
  ? new LocalAnnouncementRepository()
  : new HttpAnnouncementRepository();

/**
 * 開発モードかどうか
 * localStorage変更検知などのローカル専用機能を有効にするかどうかの判定に使用
 */
export const isLocalMode = USE_LOCAL_ANNOUNCEMENT_REPOSITORY;
