/**
 * Announcement Repository Port - お知らせリポジトリインターフェース
 * 
 * お知らせデータへのアクセスを抽象化。
 * 実装は LocalAnnouncementRepository（ローカル）または
 * HttpAnnouncementRepository（API）に差し替え可能。
 */

import type { Announcement } from '../domain/announcement';

/**
 * ユーザーごとのお知らせ状態マップ
 * key: お知らせID, value: 既読日時（ISO8601）
 */
export interface AnnouncementReadStateMap {
  [announcementId: string]: string | null;
}

/**
 * お知らせ一覧レスポンス（API連携用）
 */
export interface AnnouncementListResponse {
  announcements: Announcement[];
  total: number;
  unreadCount: number;
  /** 既読状態マップ（オプション、APIから取得時に使用） */
  readAtMap?: AnnouncementReadStateMap;
}

/**
 * お知らせリポジトリインターフェース
 */
export interface AnnouncementRepository {
  /**
   * アクティブなお知らせ一覧を取得
   * 
   * @returns お知らせ一覧レスポンス（アクティブなお知らせ、総数、未読数）
   */
  list(): Promise<AnnouncementListResponse>;

  /**
   * 指定IDのお知らせを取得
   * 
   * @param id - お知らせID
   * @returns お知らせ、または見つからない場合はnull
   */
  get(id: string): Promise<Announcement | null>;

  /**
   * お知らせを既読にする
   * 
   * @param id - お知らせID
   */
  markRead(id: string): Promise<void>;

  /**
   * お知らせを確認済みにする（critical用）
   * 
   * @param id - お知らせID
   */
  markAcknowledged(id: string): Promise<void>;

  /**
   * 未読お知らせ数を取得
   * 
   * @returns 未読数
   */
  getUnreadCount(): Promise<number>;
}
