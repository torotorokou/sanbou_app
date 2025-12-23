/**
 * Local Announcement Repository - ローカル実装
 * 
 * シードデータからお知らせを取得するローカル実装。
 * 後で HttpAnnouncementRepository に差し替え可能。
 * 
 * 【Repository の責務】
 * - アクティブ（公開期間内）なお知らせのみを返す
 * - 対象（audience）フィルタは ViewModel 側で行う
 *   （将来 API 化の際はサーバー側でユーザー属性に基づきフィルタ）
 */

import type { Announcement } from '../domain/announcement';
import { isAnnouncementActive } from '../domain/announcement';
import type { AnnouncementRepository } from '../ports/AnnouncementRepository';
import { ANNOUNCEMENT_SEEDS } from './seed';

/**
 * ローカル（シードデータ）リポジトリ実装
 */
export class LocalAnnouncementRepository implements AnnouncementRepository {
  /**
   * アクティブなお知らせ一覧を取得
   * 
   * 注意: audience フィルタは適用しない（ViewModel で行う）
   */
  async list(): Promise<Announcement[]> {
    const now = new Date();
    return ANNOUNCEMENT_SEEDS.filter((ann) => isAnnouncementActive(ann, now));
  }

  /**
   * 指定IDのお知らせを取得
   */
  async get(id: string): Promise<Announcement | null> {
    const announcement = ANNOUNCEMENT_SEEDS.find((ann) => ann.id === id);
    if (!announcement) return null;

    // アクティブでない場合も返す（詳細表示用）
    return announcement;
  }
}

/**
 * デフォルトのリポジトリインスタンス
 */
export const announcementRepository = new LocalAnnouncementRepository();
