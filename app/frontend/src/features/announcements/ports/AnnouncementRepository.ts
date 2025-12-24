/**
 * Announcement Repository Port - お知らせリポジトリインターフェース
 * 
 * お知らせデータへのアクセスを抽象化。
 * 実装は LocalAnnouncementRepository（ローカル）または
 * HttpAnnouncementRepository（API）に差し替え可能。
 */

import type { Announcement } from '../domain/announcement';

/**
 * お知らせリポジトリインターフェース
 */
export interface AnnouncementRepository {
  /**
   * アクティブなお知らせ一覧を取得
   * 
   * @returns アクティブなお知らせの配列
   */
  list(): Promise<Announcement[]>;

  /**
   * 指定IDのお知らせを取得
   * 
   * @param id - お知らせID
   * @returns お知らせ、または見つからない場合はnull
   */
  get(id: string): Promise<Announcement | null>;
}
