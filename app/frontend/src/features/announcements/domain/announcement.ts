/**
 * Announcement Domain - お知らせドメインモデル
 *
 * お知らせ機能のドメインエンティティと判定関数。
 *
 * ## 将来のバックエンド連携について（Outbox パターン推奨）
 *
 * 【DB設計】
 * - announcements テーブルに notification_plan を JSON カラムで保存
 * - publish 時に notification_outbox テーブルにレコードを積む
 *   - columns: id, announcement_id, channel, status, sent_at, error_message, created_at
 *
 * 【Worker 処理】
 * - notification_outbox を定期的にポーリング
 * - status='pending' のレコードを処理
 * - email/line を送信し、status='sent'/'failed' に更新
 *
 * 【Clean Architecture】
 * - application: NotificationDispatcherPort（インターフェース）
 * - infra: EmailAdapter / LineAdapter（実装）
 *
 * TODO: バックエンド実装時にこのコメントを参照してください。
 */

/**
 * 重要度レベル
 */
export type AnnouncementSeverity = "info" | "warn" | "critical";

/**
 * 対象オーディエンス
 * - 'all': 全ユーザー
 * - 'internal': 社内ユーザー（今は all と同じ扱い）
 * - 'site:narita': 成田拠点のユーザー
 * - 'site:shinkiba': 新木場拠点のユーザー
 */
export type Audience = "all" | "internal" | "site:narita" | "site:shinkiba";

/**
 * 添付ファイル
 */
export interface Attachment {
  /** 表示ラベル */
  label: string;
  /** URL */
  url: string;
  /** ファイル種別 */
  kind?: "pdf" | "link";
}

/**
 * 通知チャネル
 */
export type NotificationChannel = "inApp" | "email" | "line";

/**
 * 通知設定
 *
 * 将来のメール/LINE連携のための設定情報。
 * 今回は表示のみ（送信は実装しない）。
 */
export interface NotificationPlan {
  /** 配信チャネル */
  channels: NotificationChannel[];
  /** 公開開始時に送信するか（将来実装） */
  sendOnPublish: boolean;
  /** 明示的なスケジュール日時（ISO8601、将来実装） */
  scheduledAt?: string | null;
  /** テンプレートヒント（将来のテンプレート切替用） */
  templateHint?: string | null;
}

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
  /** タグ（任意、最大2〜3個表示推奨） */
  tags?: string[];
  /** 公開開始日時（ISO8601） */
  publishFrom: string;
  /** 公開終了日時（ISO8601、null=無期限） */
  publishTo: string | null;
  /** 対象オーディエンス */
  audience: Audience;
  /** 添付ファイル */
  attachments?: Attachment[];
  /** 通知設定（無ければ inApp のみ相当） */
  notification?: NotificationPlan;
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
  now: Date = new Date(),
): boolean {
  const publishFrom = new Date(announcement.publishFrom);
  const publishTo = announcement.publishTo
    ? new Date(announcement.publishTo)
    : null;

  return publishFrom <= now && (publishTo === null || now <= publishTo);
}

/**
 * お知らせが指定オーディエンスに表示可能かどうかを判定
 *
 * @param announcement - 判定対象のお知らせ
 * @param currentAudience - 現在のユーザーオーディエンス
 * @returns 表示可能ならtrue
 *
 * TODO: 将来的にはユーザープロファイルから currentAudience を取得する
 */
export function isVisibleForAudience(
  announcement: Announcement,
  currentAudience: Audience,
): boolean {
  const { audience } = announcement;

  // 'all' と 'internal' は全員に表示（今は同じ扱い）
  if (audience === "all" || audience === "internal") {
    return true;
  }

  // サイト指定の場合は一致するときのみ表示
  return audience === currentAudience;
}

/**
 * バナー表示対象かどうかを判定
 *
 * 重要度が warn または critical のお知らせがバナー対象
 *
 * @param announcement - 判定対象のお知らせ
 * @returns バナー対象ならtrue
 */
export function isBannerTarget(announcement: Announcement): boolean {
  return (
    announcement.severity === "warn" || announcement.severity === "critical"
  );
}
