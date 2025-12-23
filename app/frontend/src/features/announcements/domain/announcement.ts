/**
 * Announcement Domain - お知らせドメインモデル
 * 
 * お知らせ機能のドメインエンティティと判定関数。
 */

/**
 * 重要度レベル
 */
export type AnnouncementSeverity = 'info' | 'warn' | 'critical';

/**
 * お知らせエンティティ
 */
export interface Announcement {
  /** 一意識別子 */
  id: string;
  /** タイトル */
  title: string;
  /** 本文（Markdown形式） */
  bodyMd: string;
  /** 重要度 */
  severity: AnnouncementSeverity;
  /** ピン留め（トップページバナー対象） */
  pinned: boolean;
  /** 公開開始日時（ISO8601） */
  publishFrom: string;
  /** 公開終了日時（ISO8601、null=無期限） */
  publishTo: string | null;
}

/**
 * お知らせがアクティブ（公開期間内）かどうかを判定
 * 
 * @param announcement - 判定対象のお知らせ
 * @param now - 現在日時（デフォルト: 現在時刻）
 * @returns アクティブならtrue
 */
export function isAnnouncementActive(
  announcement: Announcement,
  now: Date = new Date()
): boolean {
  const publishFrom = new Date(announcement.publishFrom);
  const publishTo = announcement.publishTo
    ? new Date(announcement.publishTo)
    : null;

  return publishFrom <= now && (publishTo === null || now <= publishTo);
}

/**
 * バナー表示対象かどうかを判定
 * 
 * ピン留め かつ 重要度が warn または critical のお知らせがバナー対象
 * 
 * @param announcement - 判定対象のお知らせ
 * @returns バナー対象ならtrue
 */
export function isBannerTarget(announcement: Announcement): boolean {
  return (
    announcement.pinned &&
    (announcement.severity === 'warn' || announcement.severity === 'critical')
  );
}
