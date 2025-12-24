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
import type { AnnouncementRepository, AnnouncementListResponse } from '../ports/AnnouncementRepository';
import { ANNOUNCEMENT_SEEDS } from './seed';
import { markAsRead, markAsAcknowledged, getUnreadCount } from './announcementUserStateStorage';

/** デフォルトのユーザーキー（ローカル環境用） */
const DEFAULT_USER_KEY = 'local';

/**
 * ローカル（シードデータ）リポジトリ実装
 */
export class LocalAnnouncementRepository implements AnnouncementRepository {
  private userKey: string;

  constructor(userKey: string = DEFAULT_USER_KEY) {
    this.userKey = userKey;
  }

  /**
   * アクティブなお知らせ一覧を取得
   * 
   * 注意: audience フィルタは適用しない（ViewModel で行う）
   */
  async list(): Promise<AnnouncementListResponse> {
    const now = new Date();
    const activeAnnouncements = ANNOUNCEMENT_SEEDS.filter((ann) => isAnnouncementActive(ann, now));
    
    // ローカルストレージから未読数を計算
    const ids = activeAnnouncements.map((ann) => ann.id);
    const unreadCount = getUnreadCount(this.userKey, ids);
    
    return {
      announcements: activeAnnouncements,
      total: activeAnnouncements.length,
      unreadCount,
    };
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

  /**
   * お知らせを既読にする（ローカルストレージに保存）
   */
  async markRead(id: string): Promise<void> {
    markAsRead(this.userKey, id);
  }

  /**
   * お知らせを確認済みにする（ローカルストレージに保存）
   */
  async markAcknowledged(id: string): Promise<void> {
    markAsAcknowledged(this.userKey, id);
  }

  /**
   * 未読お知らせ数を取得
   */
  async getUnreadCount(): Promise<number> {
    const result = await this.list();
    return result.unreadCount;
  }
}

/**
 * デフォルトのリポジトリインスタンス
 */
export const announcementRepository = new LocalAnnouncementRepository();
